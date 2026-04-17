from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class FileResponse(BaseModel):
    id: int
    filename: str
    file_type: Optional[str]
    file_size: Optional[int]
    processing_status: str
    is_knowledge: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class FileQARequest(BaseModel):
    question: str


class FileQAResponse(BaseModel):
    answer: str
    sources: list[str] = []
