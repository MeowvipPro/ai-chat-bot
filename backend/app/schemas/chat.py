from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class ChatCreate(BaseModel):
    title: Optional[str] = "New Chat"
    model_provider: Optional[str] = "openai"
    model_name: Optional[str] = "gpt-3.5-turbo"


class ChatUpdate(BaseModel):
    title: Optional[str] = None
    model_provider: Optional[str] = None
    model_name: Optional[str] = None


class ChatResponse(BaseModel):
    id: int
    title: str
    model_provider: str
    model_name: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ChatDetailResponse(ChatResponse):
    messages: list["MessageResponse"] = []


class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1)
    stream: bool = True
    use_knowledge: bool = False


class MessageResponse(BaseModel):
    id: int
    chat_id: int
    role: str
    content: str
    tokens_used: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}
