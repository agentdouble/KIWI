from fastapi import APIRouter
from app.api import (
    auth,
    sessions,
    agents,
    chats,
    messages,
    documents,
    documents_processing,
    powerpoint,
    search,
    admin,
    alert,
    feature_updates,
)
import logging

logger = logging.getLogger(__name__)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth")
logger.info("Auth router loaded successfully")
api_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(chats.router, prefix="/chats", tags=["chats"])
api_router.include_router(messages.router, prefix="/messages", tags=["messages"])
api_router.include_router(documents.router, tags=["documents"])
api_router.include_router(documents_processing.router, tags=["document-processing"])
api_router.include_router(powerpoint.router, tags=["powerpoint"])
api_router.include_router(search.router, tags=["search"])
api_router.include_router(admin.router, prefix="/admin")
api_router.include_router(alert.router)
api_router.include_router(feature_updates.router)
