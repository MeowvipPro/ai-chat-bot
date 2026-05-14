import json
import chromadb
from app.config import get_settings

settings = get_settings()

_client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
_embedder = None


def _is_bedrock_model() -> bool:
    return settings.EMBEDDING_MODEL.startswith("amazon.")


def _get_embedder():
    global _embedder
    if _embedder is not None:
        return _embedder

    if _is_bedrock_model():
        import boto3
        session = boto3.Session(
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            aws_session_token=settings.AWS_SESSION_TOKEN,
            region_name=settings.AWS_REGION,
        )
        _embedder = session.client("bedrock-runtime")
    else:
        import os, requests as _req
        _orig = _req.Session.request
        _req.Session.request = lambda self, *a, **kw: _orig(self, *a, **{**kw, "verify": False})
        os.environ.setdefault("HF_HUB_DISABLE_SSL_VERIFY", "1")
        os.environ.setdefault("REQUESTS_CA_BUNDLE", "")
        from sentence_transformers import SentenceTransformer
        _embedder = SentenceTransformer(settings.EMBEDDING_MODEL)
        _req.Session.request = _orig
    return _embedder


def _encode(texts: list[str]) -> list[list[float]]:
    embedder = _get_embedder()
    if _is_bedrock_model():
        embeddings = []
        for text in texts:
            body = json.dumps({"inputText": text})
            response = embedder.invoke_model(
                modelId=settings.EMBEDDING_MODEL,
                contentType="application/json",
                accept="application/json",
                body=body,
            )
            result = json.loads(response["body"].read())
            embeddings.append(result["embedding"])
        return embeddings
    else:
        return embedder.encode(texts).tolist()


def store_embeddings(file_id: int, chunks: list[str]):
    embeddings = _encode(chunks)
    collection = _client.get_or_create_collection(name=f"file_{file_id}")
    collection.add(
        ids=[f"chunk_{i}" for i in range(len(chunks))],
        embeddings=embeddings,
        documents=chunks,
        metadatas=[{"file_id": file_id, "chunk_index": i} for i in range(len(chunks))],
    )


def retrieve_relevant_chunks(file_id: int, query: str, top_k: int = 5) -> list[str]:
    query_embedding = _encode([query])
    collection = _client.get_collection(name=f"file_{file_id}")
    results = collection.query(query_embeddings=query_embedding, n_results=top_k)
    return results["documents"][0] if results["documents"] else []


# ---- Knowledge Base (user-level) ----

def store_knowledge_embeddings(user_id: int, file_id: int, chunks: list[str]):
    embeddings = _encode(chunks)
    collection = _client.get_or_create_collection(name=f"knowledge_user_{user_id}")
    collection.add(
        ids=[f"file_{file_id}_chunk_{i}" for i in range(len(chunks))],
        embeddings=embeddings,
        documents=chunks,
        metadatas=[{"file_id": file_id, "chunk_index": i} for i in range(len(chunks))],
    )


def retrieve_knowledge_chunks(user_id: int, query: str, top_k: int = 5) -> list[str]:
    query_embedding = _encode([query])
    try:
        collection = _client.get_collection(name=f"knowledge_user_{user_id}")
    except Exception:
        return []
    count = collection.count()
    if count == 0:
        return []
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=min(top_k, count),
    )
    return results["documents"][0] if results["documents"] else []


def delete_knowledge_embeddings(user_id: int, file_id: int):
    try:
        collection = _client.get_collection(name=f"knowledge_user_{user_id}")
        results = collection.get(where={"file_id": file_id})
        if results["ids"]:
            collection.delete(ids=results["ids"])
    except Exception:
        pass
