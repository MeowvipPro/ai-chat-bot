import os
import logging
import asyncio
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.database import get_db, SessionLocal
from app.dependencies import get_current_user
from app.models.user import User
from app.models.uploaded_file import UploadedFile, FileChunk
from app.schemas.file import FileResponse
from app.services.file_processor import extract_text
from app.services.vector_store import store_knowledge_embeddings, delete_knowledge_embeddings
from app.utils.embeddings import chunk_text
from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()
router = APIRouter()

ALLOWED_EXTENSIONS = {"pdf", "txt", "png", "jpg", "jpeg", "doc", "docx", "xls", "xlsx"}


def _get_extension(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


@router.post("/upload", response_model=FileResponse, status_code=201)
async def upload_knowledge_doc(
    file: UploadFile = File(...),
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
    user_dir = os.path.join(settings.UPLOAD_DIR, "knowledge", str(current_user.id))
    os.makedirs(user_dir, exist_ok=True)

    safe_filename = os.path.basename(file.filename)
    file_path = os.path.join(user_dir, safe_filename)
    with open(file_path, "wb") as f:
        f.write(file_bytes)

    db_file = UploadedFile(
        user_id=current_user.id,
        chat_id=None,
        filename=safe_filename,
        file_type=ext,
        file_path=file_path,
        file_size=len(file_bytes),
        processing_status="processing",
        is_knowledge=True,
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)

    # Process in background
    asyncio.create_task(_process_knowledge_doc(db_file.id, file_path, ext, current_user.id))
    return db_file


async def _process_knowledge_doc(file_id: int, file_path: str, file_type: str, user_id: int):
    db = SessionLocal()
    db_file = None
    try:
        db_file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
        if not db_file:
            logger.error(f"Knowledge doc {file_id} not found in DB")
            return

        logger.info(f"Processing knowledge doc {file_id}: {file_path}")

        loop = asyncio.get_event_loop()
        extracted = await loop.run_in_executor(None, extract_text, file_path, file_type)
        db_file.extracted_text = extracted

        chunks = chunk_text(extracted)
        logger.info(f"Knowledge doc {file_id}: extracted {len(chunks)} chunks")

        for i, chunk in enumerate(chunks):
            db_chunk = FileChunk(
                file_id=file_id,
                chunk_index=i,
                chunk_text=chunk,
                tokens=len(chunk.split()),
            )
            db.add(db_chunk)

        # Store in user-level knowledge collection
        if chunks:
            await loop.run_in_executor(None, store_knowledge_embeddings, user_id, file_id, chunks)

        db_file.processing_status = "completed"
        db.commit()
        logger.info(f"Knowledge doc {file_id}: processing completed")
    except Exception as e:
        logger.exception(f"Knowledge doc {file_id} processing failed: {e}")
        if db_file:
            db_file.processing_status = "failed"
            db.commit()
    finally:
        db.close()


@router.get("/", response_model=list[FileResponse])
def list_knowledge_docs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    files = (
        db.query(UploadedFile)
        .filter(
            UploadedFile.user_id == current_user.id,
            UploadedFile.is_knowledge == True,
        )
        .order_by(UploadedFile.created_at.desc())
        .all()
    )
    return files


@router.delete("/{file_id}", status_code=204)
def delete_knowledge_doc(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    file = (
        db.query(UploadedFile)
        .filter(
            UploadedFile.id == file_id,
            UploadedFile.user_id == current_user.id,
            UploadedFile.is_knowledge == True,
        )
        .first()
    )
    if not file:
        raise HTTPException(status_code=404, detail="Knowledge document not found")

    # Remove from ChromaDB
    delete_knowledge_embeddings(current_user.id, file_id)

    # Remove physical file
    if file.file_path and os.path.exists(file.file_path):
        os.remove(file.file_path)

    db.delete(file)
    db.commit()
