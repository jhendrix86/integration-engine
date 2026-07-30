"""
Integration router
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from loguru import logger

from app.database import get_db
from app.models.integration import Integration, IntegrationStatus, IntegrationType

router = APIRouter()


class CreateIntegrationRequest(BaseModel):
    """Request to create integration"""
    name: str
    integration_type: str
    provider: str
    credentials: dict
    config: dict
    auto_sync_enabled: bool = False
    sync_interval_hours: int = 24


@router.post("/create")
async def create_integration(
    request: CreateIntegrationRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create a new integration"""
    try:
        logger.info(f"Creating integration: {request.name}")
        
        # Calculate next sync time
        next_sync = datetime.utcnow() + timedelta(hours=request.sync_interval_hours)
        
        # In production, this would save to database
        # For now, return a mock response
        integration = {
            "id": "integration_123",
            "name": request.name,
            "integration_type": request.integration_type,
            "provider": request.provider,
            "status": "active",
            "config": request.config,
            "auto_sync_enabled": request.auto_sync_enabled,
            "sync_interval_hours": request.sync_interval_hours,
            "next_sync_at": next_sync.isoformat(),
            "created_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Integration created: {integration['id']}")
        return integration
        
    except Exception as e:
        logger.error(f"Failed to create integration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{integration_id}/sync")
async def trigger_sync(
    integration_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Trigger manual sync for integration"""
    try:
        logger.info(f"Triggering sync for integration {integration_id}")
        
        # In production, this would trigger sync job
        # For now, return a mock response
        sync_job = {
            "id": "sync_job_123",
            "integration_id": integration_id,
            "status": "running",
            "started_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Sync triggered for integration {integration_id}")
        return sync_job
        
    except Exception as e:
        logger.error(f"Failed to trigger sync: {e}")
        raise HTTPException(status_code=500, detail(str(e))


@router.get("/{integration_id}")
async def get_integration(
    integration_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get integration details"""
    try:
        logger.info(f"Getting integration details for {integration_id}")
        
        # In production, this would query from database
        # For now, return a mock response
        integration = {
            "id": integration_id,
            "name": "HubSpot CRM",
            "integration_type": "crm",
            "provider": "hubspot",
            "status": "active",
            "config": {
                "sync_contacts": True,
                "sync_deals": True
            },
            "last_sync_at": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
            "next_sync_at": (datetime.utcnow() + timedelta(hours=22)).isoformat()
        }
        
        return integration
        
    except Exception as e:
        logger.error(f"Failed to get integration: {e}")
        raise HTTPException(status_code=500, detail(str(e))


@router.get("/")
async def list_integrations(
    status: Optional[str] = None,
    integration_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """List integrations"""
    try:
        logger.info("Listing integrations")
        
        # In production, this would query from database with filters
        # For now, return a mock response
        integrations = [
            {
                "id": "integration_001",
                "name": "HubSpot CRM",
                "integration_type": "crm",
                "provider": "hubspot",
                "status": "active",
                "last_sync_at": (datetime.utcnow() - timedelta(hours=2)).isoformat()
            },
            {
                "id": "integration_002",
                "name": "Mailchimp",
                "integration_type": "marketing",
                "provider": "mailchimp",
                "status": "active",
                "last_sync_at": (datetime.utcnow() - timedelta(hours=1)).isoformat()
            }
        ]
        
        return {
            "total": len(integrations),
            "integrations": integrations,
            "filters": {
                "status": status,
                "integration_type": integration_type
            },
            "pagination": {
                "limit": limit,
                "offset": offset
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to list integrations: {e}")
        raise HTTPException(status_code=500, detail(str(e))
