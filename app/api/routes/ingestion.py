import asyncio
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Header, Query, BackgroundTasks
from pydantic import BaseModel, Field

from app.config import settings
from app.database import DatabaseManager
from app.services.ingestion_service import IngestionService
from app.models.ingestion import IngestionRun, IngestionStats

router = APIRouter(prefix="/api/ingestion", tags=["Ingestion"])


class TriggerIngestionRequest(BaseModel):
    max_pages: int = Field(default=50, ge=1, le=100)


@router.get("/status", response_model=IngestionStats)
async def get_ingestion_status():
    db = DatabaseManager.get_database()
    try:
        total_sources = await db.sources.count_documents({})
        total_chunks = await db.content_chunks.count_documents({})

        pipeline = [
            {"$group": {"_id": "$domain", "count": {"$sum": 1}}}
        ]
        cursor = db.sources.aggregate(pipeline)
        breakdown: Dict[str, int] = {}
        async for doc in cursor:
            if doc["_id"]:
                breakdown[doc["_id"]] = doc["count"]

        last_run = await db.ingestion_runs.find_one(
            {"status": "completed"},
            sort=[("completed_at", -1)]
        )

        return IngestionStats(
            total_sources=total_sources,
            total_chunks=total_chunks,
            domain_breakdown=breakdown,
            last_ingested_at=last_run.get("completed_at") if last_run else None,
            is_running=IngestionService.is_running()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to query ingestion status: {str(e)}")


@router.post("/run", response_model=Dict[str, Any])
async def trigger_ingestion(
    background_tasks: BackgroundTasks,
    body: Optional[TriggerIngestionRequest] = None,
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key")
):
    """
    Authenticated administrative endpoint to trigger controlled data ingestion.
    Requires X-Admin-Key matching server configuration.
    """
    if x_admin_key != settings.ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Unauthorized: Invalid administrative credentials.")

    if IngestionService.is_running():
        raise HTTPException(status_code=409, detail="An ingestion run is already in progress.")

    max_pages = body.max_pages if body else 50

    async def _run_task():
        try:
            await IngestionService.run_ingestion(trigger="admin_api", max_pages=max_pages)
        except Exception:
            pass

    asyncio.create_task(_run_task())

    return {
        "status": "started",
        "message": "Data ingestion pipeline started in background.",
        "max_pages": max_pages
    }


@router.get("/sources")
async def list_sources(
    domain: Optional[str] = Query(None),
    status: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0)
):
    """
    Returns indexed sources with fetch status and metadata.
    """
    db = DatabaseManager.get_database()
    query: Dict[str, Any] = {}
    if domain:
        query["domain"] = domain
    if status is not None:
        query["fetch_status"] = status

    cursor = db.sources.find(query).skip(skip).limit(limit).sort("updated_at", -1)
    sources = []
    async for s in cursor:
        s["_id"] = str(s["_id"])
        sources.append(s)

    total = await db.sources.count_documents(query)

    return {
        "total": total,
        "items": sources,
        "limit": limit,
        "skip": skip
    }
