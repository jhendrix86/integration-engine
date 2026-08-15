"""
Integration router - real DB-backed CRUD against the integrations table.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from loguru import logger

from app.database import get_db
from app.models.credential import Credential, CredentialType
from app.models.integration import Integration, IntegrationStatus, IntegrationType
from app.models.sync import SyncJob
from app.models.tenant_base import apply_tenant_context
from app.services.encryption import encrypt_credentials
from app.services.sync_engine import run_sync_job

router = APIRouter()


class CreateIntegrationRequest(BaseModel):
    """Request to create integration"""
    name: str
    integration_type: IntegrationType
    provider: str
    credentials: dict
    config: dict
    auto_sync_enabled: bool = False
    sync_interval_hours: int = 24


def _serialize(integration: Integration) -> dict:
    return {
        "id": str(integration.id),
        "name": integration.name,
        "integration_type": integration.integration_type.value,
        "provider": integration.provider,
        "status": integration.status.value,
        "config": integration.config,
        "auto_sync_enabled": integration.auto_sync_enabled,
        "sync_interval_hours": integration.sync_interval_hours,
        "last_sync_at": integration.last_sync_at.isoformat() if integration.last_sync_at else None,
        "next_sync_at": integration.next_sync_at.isoformat() if integration.next_sync_at else None,
        "last_error": integration.last_error,
        "error_count": integration.error_count,
        "created_at": integration.created_at.isoformat(),
    }


async def _get_integration_or_404(db: AsyncSession, integration_id: str) -> Integration:
    try:
        integration_uuid = uuid.UUID(integration_id)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Integration '{integration_id}' not found")

    integration = await db.get(Integration, integration_uuid)
    if integration is None:
        raise HTTPException(status_code=404, detail=f"Integration '{integration_id}' not found")
    return integration


@router.post("/create")
async def create_integration(request: CreateIntegrationRequest, db: AsyncSession = Depends(get_db)):
    """Create a new integration"""
    try:
        logger.info(f"Creating integration: {request.name}")

        next_sync = datetime.utcnow() + timedelta(hours=request.sync_interval_hours) if request.auto_sync_enabled else None

        integration = Integration(
            name=request.name,
            integration_type=request.integration_type,
            provider=request.provider,
            status=IntegrationStatus.ACTIVE,
            config=request.config,
            auto_sync_enabled=request.auto_sync_enabled,
            sync_interval_hours=request.sync_interval_hours,
            next_sync_at=next_sync,
        )
        apply_tenant_context(integration)
        db.add(integration)
        await db.flush()

        if request.credentials:
            credential = Credential(
                integration_id=integration.id,
                credential_type=CredentialType.API_KEY,
                name=f"{request.provider} credentials",
                encrypted_data=encrypt_credentials(request.credentials),
            )
            apply_tenant_context(credential)
            db.add(credential)

        await db.commit()
        await db.refresh(integration)

        logger.info(f"Integration created: {integration.id}")
        return _serialize(integration)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create integration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{integration_id}/sync")
async def trigger_sync(integration_id: str, db: AsyncSession = Depends(get_db)):
    """Create and immediately run a sync job for this integration"""
    try:
        integration = await _get_integration_or_404(db, integration_id)
        logger.info(f"Triggering sync for integration {integration_id}")

        sync_job = SyncJob(integration_id=integration.id, sync_type="manual", direction="pull")
        apply_tenant_context(sync_job)
        db.add(sync_job)
        await db.flush()

        await run_sync_job(db, integration, sync_job)

        await db.commit()
        await db.refresh(sync_job)

        logger.info(f"Sync {sync_job.status.value} for integration {integration_id}")
        return {
            "id": str(sync_job.id),
            "integration_id": str(integration.id),
            "status": sync_job.status.value,
            "started_at": sync_job.started_at.isoformat() if sync_job.started_at else None,
            "error_message": sync_job.error_message,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger sync: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{integration_id}")
async def get_integration(integration_id: str, db: AsyncSession = Depends(get_db)):
    """Get integration details"""
    try:
        integration = await _get_integration_or_404(db, integration_id)
        return _serialize(integration)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get integration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_integrations(
    status: Optional[IntegrationStatus] = None,
    integration_type: Optional[IntegrationType] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """List integrations, real filters applied against the database"""
    try:
        query = select(Integration)
        if status is not None:
            query = query.where(Integration.status == status)
        if integration_type is not None:
            query = query.where(Integration.integration_type == integration_type)

        query = query.order_by(Integration.created_at.desc()).offset(offset).limit(limit)

        result = await db.execute(query)
        integrations = result.scalars().all()

        return {
            "total": len(integrations),
            "integrations": [_serialize(i) for i in integrations],
            "filters": {
                "status": status.value if status else None,
                "integration_type": integration_type.value if integration_type else None,
            },
            "pagination": {"limit": limit, "offset": offset},
        }

    except Exception as e:
        logger.error(f"Failed to list integrations: {e}")
        raise HTTPException(status_code=500, detail=str(e))
