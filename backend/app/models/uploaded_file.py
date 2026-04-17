from sqlalchemy import Column, Integer, String, Text, BigInteger, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base


class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id", ondelete="SET NULL"), nullable=True, index=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50))
    file_path = Column(String(500))
    file_size = Column(BigInteger)
    extracted_text = Column(Text, nullable=True)
    processing_status = Column(String(20), default="pending")  # pending, processing, completed, failed
    is_knowledge = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="uploaded_files")
    chat = relationship("Chat", back_populates="uploaded_files")
    chunks = relationship("FileChunk", back_populates="file", cascade="all, delete-orphan")


class FileChunk(Base):
    __tablename__ = "file_chunks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(Integer, ForeignKey("uploaded_files.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer)
    chunk_text = Column(Text, nullable=False)
    tokens = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    file = relationship("UploadedFile", back_populates="chunks")
