"""
Sync router - real DB-backed CRUD against the sync_jobs table.
/configure creates a pending job; /{sync_id}/trigger actually runs it
(app/services/sync_engine.py) rather than always returning "running".
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from loguru import logger

from app.database import get_db
from app.models.integration import Integration
from app.models.sync import SyncJob, SyncStatus
from app.models.tenant_base import apply_tenant_context
from app.services.sync_engine import run_sync_job

router = APIRouter()


class ConfigureSyncRequest(BaseModel):
    """Request to configure sync"""
    integration_id: str
    sync_type: str
    direction: str
    config: dict = {}


def _serialize(sync_job: SyncJob) -> dict:
    total = sync_job.total_records or 0
    progress = round(100 * (sync_job.processed_records or 0) / total, 1) if total else None

    return {
        "id": str(sync_job.id),
        "integration_id": str(sync_job.integration_id),
        "sync_type": sync_job.sync_type,
        "direction": sync_job.direction,
        "status": sync_job.status.value,
        "total_records": sync_job.total_records,
        "processed_records": sync_job.processed_records,
        "failed_records": sync_job.failed_records,
        "records_created": sync_job.records_created,
        "records_updated": sync_job.records_updated,
        "records_deleted": sync_job.records_deleted,
        "started_at": sync_job.started_at.isoformat() if sync_job.started_at else None,
        "completed_at": sync_job.completed_at.isoformat() if sync_job.completed_at else None,
        "duration_seconds": sync_job.duration_seconds,
        "error_message": sync_job.error_message,
        "progress_percentage": progress,
        "created_at": sync_job.created_at.isoformat(),
    }


async def _get_sync_job_or_404(db: AsyncSession, sync_id: str) -> SyncJob:
    try:
        sync_uuid = uuid.UUID(sync_id)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Sync job '{sync_id}' not found")

    sync_job = await db.get(SyncJob, sync_uuid)
    if sync_job is None:
        raise HTTPException(status_code=404, detail=f"Sync job '{sync_id}' not found")
    return sync_job


@router.post("/configure")
async def configure_sync(request: ConfigureSyncRequest, db: AsyncSession = Depends(get_db)):
    """Create a pending sync job for an integration"""
    try:
        try:
            integration_uuid = uuid.UUID(request.integration_id)
        except ValueError:
            raise HTTPException(status_code=404, detail=f"Integration '{request.integration_id}' not found")

        integration = await db.get(Integration, integration_uuid)
        if integration is None:
            raise HTTPException(status_code=404, detail=f"Integration '{request.integration_id}' not found")

        logger.info(f"Configuring sync for integration {request.integration_id}")

        sync_job = SyncJob(
            integration_id=integration.id,
            sync_type=request.sync_type,
            direction=request.direction,
            status=SyncStatus.PENDING,
            extra_metadata=request.config or None,
        )
        apply_tenant_context(sync_job)
        db.add(sync_job)
        await db.commit()
        await db.refresh(sync_job)

        logger.info(f"Sync configured: {sync_job.id}")
        return _serialize(sync_job)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to configure sync: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{sync_id}/status")
async def get_sync_status(sync_id: str, db: AsyncSession = Depends(get_db)):
    """Get sync job status"""
    try:
        sync_job = await _get_sync_job_or_404(db, sync_id)
        return _serialize(sync_job)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get sync status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{sync_id}/trigger")
async def trigger_sync(sync_id: str, db: AsyncSession = Depends(get_db)):
    """Actually run a previously-configured (pending) sync job"""
    try:
        sync_job = await _get_sync_job_or_404(db, sync_id)

        if sync_job.status not in (SyncStatus.PENDING, SyncStatus.FAILED):
            raise HTTPException(status_code=409, detail=f"Sync job '{sync_id}' is already {sync_job.status.value}")

        integration = await db.get(Integration, sync_job.integration_id)
        if integration is None:
            raise HTTPException(status_code=404, detail=f"Integration '{sync_job.integration_id}' not found")

        logger.info(f"Triggering manual sync {sync_id}")

        await run_sync_job(db, integration, sync_job)

        await db.commit()
        await db.refresh(sync_job)

        logger.info(f"Manual sync {sync_job.status.value}: {sync_id}")
        return _serialize(sync_job)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger sync: {e}")
        raise HTTPException(status_code=500, detail=str(e))
