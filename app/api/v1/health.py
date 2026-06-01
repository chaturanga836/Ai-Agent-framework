from fastapi import APIRouter

from app.core.config import get_settings
from app.workflows.llamaindex_bridge import workflow_status

router = APIRouter()


@router.get("/health")
def health():
    settings = get_settings()
    return {
        "status": "ok",
        "service": settings.app_name,
        "llamaindex": workflow_status(),
    }
