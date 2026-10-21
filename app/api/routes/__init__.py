from app.api.routes.health import router as health_router
from app.api.routes.chat import router as chat_router
from app.api.routes.ingestion import router as ingestion_router

__all__ = ["health_router", "chat_router", "ingestion_router"]
