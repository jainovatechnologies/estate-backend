import logging
from app.socket.manager import sio, SocketManager
from app.services.chat_service import ChatService

logger = logging.getLogger(__name__)


@sio.event
async def connect(sid: str, environ: dict):
    logger.info(f"Socket.IO client connected: {sid}")


@sio.event
async def disconnect(sid: str):
    logger.info(f"Socket.IO client disconnected: {sid}")
    SocketManager.unregister_client(sid)


@sio.event
async def chat_join(sid: str, data: dict):
    session_id = data.get("session_id") if isinstance(data, dict) else None
    session = await ChatService.get_or_create_session(session_id)
    SocketManager.register_client(sid, session.session_id)
    await sio.enter_room(sid, session.session_id)

    history = await ChatService.get_session_messages(session.session_id, limit=50)
    history_payload = [
        {
            "message_id": m.message_id,
            "session_id": m.session_id,
            "role": m.role.value,
            "content": m.content,
            "citations": [c.model_dump() for c in m.citations],
            "chart_data": m.chart_data.model_dump() if m.chart_data else None,
            "created_at": m.created_at.isoformat()
        }
        for m in history
    ]

    await sio.emit("chat:history", {
        "session_id": session.session_id,
        "title": session.title,
        "messages": history_payload
    }, to=sid)


@sio.event
async def chat_message(sid: str, data: dict):
    if not isinstance(data, dict):
        await SocketManager.emit_error(sid, "Invalid message payload format.")
        return

    session_id = data.get("session_id")
    message_text = data.get("message", "").strip()

    if not message_text:
        await SocketManager.emit_error(sid, "Message text cannot be empty.")
        return

    if len(message_text) > 4000:
        await SocketManager.emit_error(sid, "Message exceeds 4000 characters limit.")
        return

    try:
        await SocketManager.emit_status(sid, "Searching grounded context from Dar Global and Wasalt...", "retrieving")
        await SocketManager.emit_status(sid, "Synthesizing answer from verified sources...", "synthesizing")

        response = await ChatService.process_user_message(session_id=session_id, message_text=message_text)

        response_payload = {
            "message_id": response.message_id,
            "session_id": response.session_id,
            "role": response.role.value,
            "content": response.content,
            "citations": [c.model_dump() for c in response.citations],
            "chart_data": response.chart_data.model_dump() if response.chart_data else None,
            "created_at": response.created_at.isoformat()
        }

        await SocketManager.emit_response(sid, response_payload)
        await SocketManager.emit_status(sid, "Complete", "done")

    except Exception as e:
        logger.error(f"Error handling chat_message for sid {sid}: {e}", exc_info=True)
        await SocketManager.emit_error(sid, f"Failed to process message: {str(e)}")
