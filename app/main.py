import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import socketio

from app.config import settings
from app.database import DatabaseManager
from app.api.routes import health_router, chat_router, ingestion_router
from app.socket.manager import sio
import app.socket.events  # noqa: F401

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("estate_intelligence")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Estate Intelligence backend...")
    await DatabaseManager.connect()

    try:
        from app.services.ingestion_service import IngestionService
        db = DatabaseManager.get_database()
        count = await db.sources.count_documents({"fetch_status": 200})
        if count == 0:
            logger.info("Database has 0 sources. Running initial dataset seeding...")
            await IngestionService.run_ingestion(trigger="startup", max_pages=15)
    except Exception as e:
        logger.warning(f"Startup ingestion/seed notice: {e}")

    yield

    logger.info("Shutting down Estate Intelligence backend...")
    await DatabaseManager.close()


fastapi_app = FastAPI(
    title="Estate Intelligence API",
    description="Real Estate Intelligence Chatbot grounded in Dar Global and Wasalt verified data.",
    version="1.0.0",
    lifespan=lifespan
)

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins if settings.cors_origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@fastapi_app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please try again later."}
    )


fastapi_app.include_router(health_router)
fastapi_app.include_router(chat_router)
fastapi_app.include_router(ingestion_router)

app = socketio.ASGIApp(
    socketio_server=sio,
    other_asgi_app=fastapi_app,
    socketio_path="socket.io"
)

