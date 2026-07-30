"""
Sync router
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from loguru import logger

from app.database import get_db

router = APIRouter()


class ConfigureSyncRequest(BaseModel):
    """Request to configure sync"""
    integration_id: str
    sync_type: str
    direction: str
    config: dict


@router.post("/configure")
async def configure_sync(
    request: ConfigureSyncRequest,
    db: AsyncSession = Depends(get_db)
):
    """Configure data sync"""
    try:
        logger.info(f"Configuring sync for integration {request.integration_id}")
        
        # In production, this would save sync configuration
        # For now, return a mock response
        sync_config = {
            "id": "sync_config_123",
            "integration_id": request.integration_id,
            "sync_type": request.sync_type,
            "direction": request.direction,
            "config": request.config,
            "created_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Sync configured for integration {request.integration_id}")
        return sync_config
        
    except Exception as e:
        logger.error(f"Failed to configure sync: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{sync_id}/status")
async def get_sync_status(
    sync_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get sync job status"""
    try:
        logger.info(f"Getting sync status for {sync_id}")
        
        # In production, this would query from database
        # For now, return a mock response
        sync_status = {
            "id": sync_id,
            "status": "running",
            "total_records": 1000,
            "processed_records": 650,
            "failed_records": 5,
            "started_at": (datetime.utcnow() - timedelta(minutes=5)).isoformat(),
            "progress_percentage": 65.0
        }
        
        return sync_status
        
    except Exception as e:
        logger.error(f"Failed to get sync status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{sync_id}/trigger")
async def trigger_sync(
    sync_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Trigger manual sync"""
    try:
        logger.info(f"Triggering manual sync {sync_id}")
        
        # In production, this would trigger sync job
        # For now, return a mock response
        sync_job = {
            "id": sync_id,
            "status": "running",
            "triggered_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Manual sync triggered: {sync_id}")
        return sync_job
        
    except Exception as e:
        logger.error(f"Failed to trigger sync: {e}")
        raise HTTPException(status_code=500, detail=str(e))
