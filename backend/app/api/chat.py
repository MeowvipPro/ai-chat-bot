import json
import asyncio
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.chat import Chat
from app.models.message import Message
from app.schemas.chat import (
    ChatCreate,
    ChatUpdate,
    ChatResponse,
    ChatDetailResponse,
    MessageCreate,
    MessageResponse,
)
from app.services.ai_service import get_ai_provider
from app.services.vector_store import retrieve_knowledge_chunks

router = APIRouter()


@router.get("/", response_model=list[ChatResponse])
def list_chats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    chats = (
        db.query(Chat)
        .filter(Chat.user_id == current_user.id)
        .order_by(Chat.updated_at.desc())
        .all()
    )
    return chats


@router.post("/", response_model=ChatResponse, status_code=status.HTTP_201_CREATED)
def create_chat(
    data: ChatCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    chat = Chat(
        user_id=current_user.id,
        title=data.title,
        model_provider=data.model_provider,
        model_name=data.model_name,
    )
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return chat


@router.get("/{chat_id}", response_model=ChatDetailResponse)
def get_chat(
    chat_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == current_user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat


@router.put("/{chat_id}", response_model=ChatResponse)
def update_chat(
    chat_id: int,
    data: ChatUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == current_user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    if data.title is not None:
        chat.title = data.title
    if data.model_provider is not None:
        chat.model_provider = data.model_provider
    if data.model_name is not None:
        chat.model_name = data.model_name

    db.commit()
    db.refresh(chat)
    return chat


@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chat(
    chat_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == current_user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    db.delete(chat)
    db.commit()


@router.get("/{chat_id}/messages", response_model=list[MessageResponse])
def get_messages(
    chat_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == current_user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat.messages


@router.post("/{chat_id}/messages")
async def send_message(
    chat_id: int,
    data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == current_user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    # Save user message
    user_msg = Message(chat_id=chat.id, role="user", content=data.content)
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    # Build conversation history
    messages_history = [{"role": m.role, "content": m.content} for m in chat.messages]

    # RAG: inject knowledge context if toggled on
    if data.use_knowledge:
        loop = asyncio.get_event_loop()
        relevant_chunks = await loop.run_in_executor(
            None, retrieve_knowledge_chunks, current_user.id, data.content, 5
        )
        if relevant_chunks:
            context = "\n\n---\n\n".join(relevant_chunks)
            rag_system = (
                "Use the following knowledge base context to help answer the user's question. "
                "If the context is relevant, incorporate it into your answer. "
                "If it's not relevant, answer normally.\n\n"
                f"Knowledge Base Context:\n{context}"
            )
            # Insert RAG system message right before the last user message
            messages_history.insert(-1, {"role": "system", "content": rag_system})

    provider = get_ai_provider(chat.model_provider)

    if data.stream:
        return StreamingResponse(
            _stream_response(provider, messages_history, chat, db),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    else:
        response_text = await provider.generate(
            messages=messages_history,
            model=chat.model_name,
            stream=False,
        )
        assistant_msg = Message(chat_id=chat.id, role="assistant", content=response_text)
        db.add(assistant_msg)
        db.commit()
        db.refresh(assistant_msg)
        return MessageResponse.model_validate(assistant_msg)


async def _stream_response(provider, messages_history, chat, db):
    full_response = ""
    try:
        stream = await provider.generate(
            messages=messages_history,
            model=chat.model_name,
            stream=True,
        )
        async for token in stream:
            full_response += token
            yield f"data: {json.dumps({'token': token})}\n\n"

        # Save completed assistant message
        assistant_msg = Message(chat_id=chat.id, role="assistant", content=full_response)
        db.add(assistant_msg)
        db.commit()

        yield f"data: {json.dumps({'done': True})}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"
