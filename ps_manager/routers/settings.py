from fastapi import APIRouter
from ps_manager.config import get_settings

router = APIRouter(prefix="/api/settings", tags=["settings"])

@router.get("/")
def get_settings_handler():
    s = get_settings()
    return {
        "storage_path": str(s.storage_path.resolve()),
        "host": s.host,
        "port": s.port,
    }
