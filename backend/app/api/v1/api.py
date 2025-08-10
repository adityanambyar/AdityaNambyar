from fastapi import APIRouter
from app.api.v1.endpoints import upload, transcribe, summarize, minutes

api_router = APIRouter()

api_router.include_router(upload.router, prefix="/upload", tags=["upload"])
api_router.include_router(transcribe.router, prefix="/transcribe", tags=["transcribe"])
api_router.include_router(summarize.router, prefix="/summarize", tags=["summarize"])
api_router.include_router(minutes.router, prefix="/minutes", tags=["minutes"])