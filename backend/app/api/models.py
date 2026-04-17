from fastapi import APIRouter, Depends
from app.services.ai_service import get_all_available_models

router = APIRouter()


@router.get("/available")
async def list_available_models():
    models = await get_all_available_models()
    return {"models": models}
