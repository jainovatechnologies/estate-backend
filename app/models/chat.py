from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Citation(BaseModel):
    title: str = Field(..., description="Title of the cited source page")
    domain: str = Field(..., description="Originating domain")
    url: str = Field(..., description="Clickable canonical URL")
    excerpt: Optional[str] = Field(default=None, description="Short relevant snippet")


class HighchartsSeries(BaseModel):
    name: str
    data: List[Any]
    type: Optional[str] = "column"
    color: Optional[str] = None


class HighchartsConfig(BaseModel):
    title: str
    subtitle: Optional[str] = None
    xAxisCategories: Optional[List[str]] = None
    yAxisTitle: Optional[str] = None
    series: List[HighchartsSeries]
    chartType: str = "column"
    sourceDescription: str


class ChatMessage(BaseModel):
    message_id: str = Field(..., description="Unique message UUID")
    session_id: str = Field(..., description="Session identifier")
    role: MessageRole = Field(...)
    content: str = Field(..., description="Raw text / markdown content")
    citations: List[Citation] = Field(default_factory=list)
    chart_data: Optional[HighchartsConfig] = None
    created_at: datetime = Field(default_factory=utc_now)


class ChatSession(BaseModel):
    session_id: str = Field(...)
    title: str = Field(default="New Conversation")
    message_count: int = Field(default=0)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000, description="User question")
    session_id: Optional[str] = Field(default=None, description="Optional existing session ID")


class ChatResponse(BaseModel):
    message_id: str
    session_id: str
    role: MessageRole = MessageRole.ASSISTANT
    content: str
    citations: List[Citation] = Field(default_factory=list)
    chart_data: Optional[HighchartsConfig] = None
    created_at: datetime
