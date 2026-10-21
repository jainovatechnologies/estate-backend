from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Source(BaseModel):
    canonical_url: str = Field(..., description="Normalized unique canonical URL")
    original_url: str = Field(..., description="Original requested URL")
    title: str = Field(default="Untitled Page")
    domain: str = Field(..., description="Domain name (e.g. darglobal.co.uk or wasalt.sa)")
    description: Optional[str] = None
    fetch_status: int = Field(default=200, description="HTTP status code or error code")
    status_message: str = Field(default="OK")
    content_hash: str = Field(..., description="SHA-256 hash of extracted clean text")
    raw_length: int = Field(default=0)
    word_count: int = Field(default=0)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class ContentChunk(BaseModel):
    chunk_id: str = Field(..., description="Unique chunk identifier")
    source_url: str = Field(..., description="Source canonical URL")
    domain: str = Field(...)
    title: str = Field(default="")
    chunk_index: int = Field(..., ge=0)
    total_chunks: int = Field(..., ge=1)
    content: str = Field(..., min_length=1)
    token_estimate: int = Field(default=0)
    created_at: datetime = Field(default_factory=utc_now)
