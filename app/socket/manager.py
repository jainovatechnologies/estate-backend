import logging
from typing import Dict
import socketio
from app.config import settings

logger = logging.getLogger(__name__)

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=settings.cors_origins if settings.cors_origins != ["*"] else "*",
    logger=False,
    engineio_logger=False,
    ping_timeout=30,
    ping_interval=15
)


class SocketManager:
    active_connections: Dict[str, str] = {}

    @classmethod
    def register_client(cls, sid: str, session_id: str) -> None:
        cls.active_connections[sid] = session_id
        logger.info(f"Client {sid} registered for session {session_id}")

    @classmethod
    def unregister_client(cls, sid: str) -> None:
        if sid in cls.active_connections:
            session_id = cls.active_connections.pop(sid)
            logger.info(f"Client {sid} disconnected from session {session_id}")

    @classmethod
    def get_session(cls, sid: str) -> str:
        return cls.active_connections.get(sid, "")

    @classmethod
    async def emit_status(cls, sid: str, status_text: str, step: str = "processing") -> None:
        try:
            await sio.emit("chat:status", {"status": status_text, "step": step}, to=sid)
        except Exception as e:
            logger.warning(f"Failed to emit status to {sid}: {e}")

    @classmethod
    async def emit_response(cls, sid: str, payload: dict) -> None:
        try:
            await sio.emit("chat:response", payload, to=sid)
        except Exception as e:
            logger.error(f"Failed to emit response to {sid}: {e}")

    @classmethod
    async def emit_error(cls, sid: str, error_message: str) -> None:
        try:
            await sio.emit("chat:error", {"error": error_message}, to=sid)
        except Exception as e:
            logger.error(f"Failed to emit error to {sid}: {e}")
