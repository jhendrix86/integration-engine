"""
Webhook router - real DB-backed CRUD against the webhooks table.

The old mock version had no way to ever register a webhook subscription
at all (only receive/get/list existed) - added POST / for that, since
without it there's nothing for the receiver to look up against.
"""

import uuid

from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, field_validator
from loguru import logger

from app.database import get_db
from app.models.integration import Integration
from app.models.tenant_base import apply_tenant_context
from app.models.webhook import Webhook, WebhookStatus
from app.services.webhook_signature import verify_signature

router = APIRouter()


class RegisterWebhookRequest(BaseModel):
    """Request to register a webhook subscription for an integration"""
    integration_id: str
    webhook_url: str
    event_type: str
    secret: str

    @field_validator("secret")
    @classmethod
    def _secret_must_be_real(cls, v: str) -> str:
        # SECURITY_REVIEW.md finding #6: verify_signature() honestly skips
        # verification when a webhook has no secret - that's the right
        # behavior for an existing no-secret registration, but nothing
        # should be able to create a NEW one that way, since it means any
        # unsigned payload from anyone is accepted forever.
        if not v or not v.strip():
            raise ValueError("secret must be a non-empty string - unsigned webhooks accept any payload from anyone")
        return v


def _serialize(webhook: Webhook) -> dict:
    return {
        "id": str(webhook.id),
        "integration_id": str(webhook.integration_id),
        "webhook_url": webhook.webhook_url,
        "event_type": webhook.event_type,
        "status": webhook.status.value,
        "last_received_at": webhook.last_received_at.isoformat() if webhook.last_received_at else None,
        "total_received": webhook.total_received,
        "total_processed": webhook.total_processed,
        "total_failed": webhook.total_failed,
        "last_error": webhook.last_error,
        "created_at": webhook.created_at.isoformat(),
    }


async def _get_webhook_or_404(db: AsyncSession, webhook_id: str) -> Webhook:
    try:
        webhook_uuid = uuid.UUID(webhook_id)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Webhook '{webhook_id}' not found")

    webhook = await db.get(Webhook, webhook_uuid)
    if webhook is None:
        raise HTTPException(status_code=404, detail=f"Webhook '{webhook_id}' not found")
    return webhook


@router.post("/")
async def register_webhook(request: RegisterWebhookRequest, db: AsyncSession = Depends(get_db)):
    """Register a webhook subscription for an integration"""
    try:
        try:
            integration_uuid = uuid.UUID(request.integration_id)
        except ValueError:
            raise HTTPException(status_code=404, detail=f"Integration '{request.integration_id}' not found")

        integration = await db.get(Integration, integration_uuid)
        if integration is None:
            raise HTTPException(status_code=404, detail=f"Integration '{request.integration_id}' not found")

        webhook = Webhook(
            integration_id=integration.id,
            webhook_url=request.webhook_url,
            event_type=request.event_type,
            secret=request.secret,
            status=WebhookStatus.ACTIVE,
        )
        apply_tenant_context(webhook)
        db.add(webhook)
        await db.commit()
        await db.refresh(webhook)

        logger.info(f"Webhook registered: {webhook.id} for integration {integration.id}")
        return _serialize(webhook)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to register webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{integration_id}")
async def receive_webhook(integration_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    """Receive a webhook from an external service - real signature verification and persistence"""
    try:
        event_type = request.headers.get("X-Event-Type", "unknown")
        logger.info(f"Received webhook for integration {integration_id} (event_type={event_type})")

        try:
            integration_uuid = uuid.UUID(integration_id)
        except ValueError:
            raise HTTPException(status_code=404, detail=f"Integration '{integration_id}' not found")

        query = select(Webhook).where(Webhook.integration_id == integration_uuid, Webhook.event_type == event_type)
        result = await db.execute(query)
        webhook = result.scalars().first()

        if webhook is None:
            # Fall back to any webhook registered for this integration, regardless of event_type
            result = await db.execute(select(Webhook).where(Webhook.integration_id == integration_uuid))
            webhook = result.scalars().first()

        if webhook is None:
            raise HTTPException(status_code=404, detail=f"No webhook registered for integration '{integration_id}'")

        raw_body = await request.body()
        signature = request.headers.get("X-Webhook-Signature")

        webhook.total_received = (webhook.total_received or 0) + 1
        webhook.last_received_at = datetime.utcnow()

        if not verify_signature(webhook.secret, raw_body, signature):
            webhook.total_failed = (webhook.total_failed or 0) + 1
            webhook.last_error = "Signature verification failed"
            await db.commit()
            raise HTTPException(status_code=401, detail="Webhook signature verification failed")

        webhook.total_processed = (webhook.total_processed or 0) + 1
        webhook.last_error = None
        await db.commit()
        await db.refresh(webhook)

        logger.info(f"Webhook processed for integration {integration_id}: {webhook.id}")
        return {
            "id": str(webhook.id),
            "integration_id": integration_id,
            "event_type": event_type,
            "status": "processed",
            "received_at": webhook.last_received_at.isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{webhook_id}")
async def get_webhook(webhook_id: str, db: AsyncSession = Depends(get_db)):
    """Get webhook details"""
    try:
        webhook = await _get_webhook_or_404(db, webhook_id)
        return _serialize(webhook)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_webhooks(
    integration_id: Optional[str] = None,
    status: Optional[WebhookStatus] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """List webhooks, real filters applied against the database"""
    try:
        query = select(Webhook)
        if integration_id is not None:
            try:
                query = query.where(Webhook.integration_id == uuid.UUID(integration_id))
            except ValueError:
                return {"total": 0, "webhooks": [], "filters": {"integration_id": integration_id, "status": None}, "pagination": {"limit": limit, "offset": offset}}
        if status is not None:
            query = query.where(Webhook.status == status)

        query = query.order_by(Webhook.created_at.desc()).offset(offset).limit(limit)

        result = await db.execute(query)
        webhooks = result.scalars().all()

        return {
            "total": len(webhooks),
            "webhooks": [_serialize(w) for w in webhooks],
            "filters": {"integration_id": integration_id, "status": status.value if status else None},
            "pagination": {"limit": limit, "offset": offset},
        }

    except Exception as e:
        logger.error(f"Failed to list webhooks: {e}")
        raise HTTPException(status_code=500, detail=str(e))
