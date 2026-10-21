from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Path
from pydantic import BaseModel, Field

from app.models.chat import ChatSession, ChatMessage, ChatRequest, ChatResponse
from app.services.chat_service import ChatService

router = APIRouter(prefix="/api/chat", tags=["Chat"])


class CreateSessionRequest(BaseModel):
    title: Optional[str] = Field(default=None, description="Initial conversation title")


@router.get("/sessions", response_model=List[ChatSession])
async def list_sessions(limit: int = Query(default=20, ge=1, le=100)):
    try:
        return await ChatService.list_sessions(limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch sessions: {str(e)}")


@router.post("/sessions", response_model=ChatSession)
async def create_session(body: Optional[CreateSessionRequest] = None):
    try:
        session = await ChatService.get_or_create_session()
        return session
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")


@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessage])
async def get_session_messages(
    session_id: str = Path(..., description="Conversation session ID"),
    limit: int = Query(default=50, ge=1, le=100)
):
    try:
        return await ChatService.get_session_messages(session_id=session_id, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch messages: {str(e)}")


@router.post("/completions", response_model=ChatResponse)
async def chat_completion(request: ChatRequest):
    """
    REST fallback for conversational completion.
    Clients can use this if WebSocket/Socket.IO connections are blocked by enterprise proxies.
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    try:
        session = await ChatService.get_or_create_session(request.session_id)
        response = await ChatService.process_user_message(
            session_id=session.session_id,
            message_text=request.message
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Completion failed: {str(e)}")
