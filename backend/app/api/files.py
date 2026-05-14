import os
import asyncio
import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form

logger = logging.getLogger(__name__)
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.uploaded_file import UploadedFile, FileChunk
from app.schemas.file import FileResponse, FileQARequest, FileQAResponse
from app.services.file_processor import extract_text
from app.services.vector_store import store_embeddings, retrieve_relevant_chunks
from app.services.ai_service import get_ai_provider
from app.utils.embeddings import chunk_text
from app.config import get_settings

settings = get_settings()
router = APIRouter()

ALLOWED_EXTENSIONS = {"pdf", "txt", "png", "jpg", "jpeg", "doc", "docx", "xls", "xlsx"}


def _get_extension(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


@router.post("/upload", response_model=FileResponse, status_code=201)
async def upload_file(
    file: UploadFile = File(...),
    chat_id: int = Form(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ext = _get_extension(file.filename)
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type .{ext} not allowed")

    file_bytes = await file.read()
    if len(file_bytes) > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large")

    # Save file to disk
    user_dir = os.path.join(settings.UPLOAD_DIR, str(current_user.id))
    os.makedirs(user_dir, exist_ok=True)

    safe_filename = os.path.basename(file.filename)
    file_path = os.path.join(user_dir, safe_filename)
    with open(file_path, "wb") as f:
        f.write(file_bytes)

    # Create DB record
    db_file = UploadedFile(
        user_id=current_user.id,
        chat_id=chat_id,
        filename=safe_filename,
        file_type=ext,
        file_path=file_path,
        file_size=len(file_bytes),
        processing_status="processing",
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)

    # Process in background
    asyncio.create_task(_process_file(db_file.id, file_path, ext))
    return db_file


async def _process_file(file_id: int, file_path: str, file_type: str):
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        db_file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
        if not db_file:
            return

        # Extract text
        loop = asyncio.get_event_loop()
        extracted = await loop.run_in_executor(None, extract_text, file_path, file_type)
        db_file.extracted_text = extracted

        # Chunk
        chunks = chunk_text(extracted)

        # Store chunks in DB
        for i, chunk in enumerate(chunks):
            db_chunk = FileChunk(
                file_id=file_id,
                chunk_index=i,
                chunk_text=chunk,
                tokens=len(chunk.split()),
            )
            db.add(db_chunk)

        # Embed and store in vector DB
        if chunks:
            await loop.run_in_executor(None, store_embeddings, file_id, chunks)

        db_file.processing_status = "completed"
        db.commit()
    except Exception as e:
        logger.exception(f"File {file_id} processing failed: {e}")
        db_file.processing_status = "failed"
        db.commit()
    finally:
        db.close()


@router.get("/", response_model=list[FileResponse])
def list_files(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    files = (
        db.query(UploadedFile)
        .filter(UploadedFile.user_id == current_user.id)
        .order_by(UploadedFile.created_at.desc())
        .all()
    )
    return files


@router.get("/{file_id}", response_model=FileResponse)
def get_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    file = (
        db.query(UploadedFile)
        .filter(UploadedFile.id == file_id, UploadedFile.user_id == current_user.id)
        .first()
    )
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    return file


@router.delete("/{file_id}", status_code=204)
def delete_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    file = (
        db.query(UploadedFile)
        .filter(UploadedFile.id == file_id, UploadedFile.user_id == current_user.id)
        .first()
    )
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    # Remove physical file
    if file.file_path and os.path.exists(file.file_path):
        os.remove(file.file_path)

    db.delete(file)
    db.commit()


@router.post("/{file_id}/qa", response_model=FileQAResponse)
async def file_qa(
    file_id: int,
    data: FileQARequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    file = (
        db.query(UploadedFile)
        .filter(UploadedFile.id == file_id, UploadedFile.user_id == current_user.id)
        .first()
    )
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    if file.processing_status != "completed":
        raise HTTPException(status_code=400, detail="File is still being processed")

    # Use the chat's model if file is linked to a chat, otherwise use defaults
    from app.models.chat import Chat

    model_provider = "openai"
    model_name = "gpt-3.5-turbo"
    if file.chat_id:
        chat = db.query(Chat).filter(Chat.id == file.chat_id).first()
        if chat:
            model_provider = chat.model_provider
            model_name = chat.model_name

    # Retrieve relevant chunks
    loop = asyncio.get_event_loop()
    relevant_chunks = await loop.run_in_executor(
        None, retrieve_relevant_chunks, file_id, data.question, 5
    )

    if not relevant_chunks:
        return FileQAResponse(answer="No relevant content found in this file.", sources=[])

    # Build context-aware prompt
    context = "\n\n---\n\n".join(relevant_chunks)
    system_prompt = (
        "You are a helpful assistant answering questions about a document.\n\n"
        f"Context from the document:\n{context}\n\n"
        "Answer the user's question based ONLY on the provided context. "
        "If the answer is not in the context, say so."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": data.question},
    ]

    provider = get_ai_provider(model_provider)
    answer = await provider.generate(messages=messages, model=model_name, stream=False)

    return FileQAResponse(answer=answer, sources=relevant_chunks[:3])
