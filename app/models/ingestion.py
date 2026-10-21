from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class IngestionRun(BaseModel):
    run_id: str = Field(..., description="Unique run ID")
    trigger: str = Field(default="manual", description="Trigger source: manual, cron, admin")
    started_at: datetime = Field(default_factory=utc_now)
    completed_at: Optional[datetime] = None
    status: str = Field(default="running", description="running, completed, failed")
    pages_discovered: int = Field(default=0)
    pages_ingested: int = Field(default=0)
    pages_failed: int = Field(default=0)
    chunks_created: int = Field(default=0)
    errors: List[str] = Field(default_factory=list)
    summary: Dict[str, Any] = Field(default_factory=dict)


class IngestionStats(BaseModel):
    total_sources: int = 0
    total_chunks: int = 0
    domain_breakdown: Dict[str, int] = Field(default_factory=dict)
    last_ingested_at: Optional[datetime] = None
    is_running: bool = False
