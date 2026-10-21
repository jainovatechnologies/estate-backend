from datetime import datetime, timezone
from fastapi import APIRouter
from app.database import DatabaseManager
from app.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    db_ok = await DatabaseManager.is_healthy()
    llm_configured = bool(settings.OPENROUTER_API_KEY and settings.OPENROUTER_API_KEY != "your_openrouter_api_key_here")

    return {
        "status": "healthy" if db_ok else "degraded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": {
            "status": "connected" if db_ok else "disconnected",
            "name": settings.MONGODB_DATABASE
        },
        "llm_provider": {
            "configured": llm_configured,
            "model": settings.OPENROUTER_MODEL,
            "provider": "OpenRouter"
        },
        "environment": settings.ENVIRONMENT
    }
