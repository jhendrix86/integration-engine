"""
Webhook router
"""

from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime
from loguru import logger

from app.database import get_db

router = APIRouter()


@router.post("/{integration_id}")
async def receive_webhook(
    integration_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Receive webhook from external service"""
    try:
        logger.info(f"Received webhook for integration {integration_id}")
        
        # Get webhook payload
        payload = await request.json()
        event_type = request.headers.get("X-Event-Type", "unknown")
        
        # In production, this would process webhook and trigger actions
        # For now, return a mock response
        webhook = {
            "id": "webhook_123",
            "integration_id": integration_id,
            "event_type": event_type,
            "payload": payload,
            "status": "processed",
            "received_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Webhook processed for integration {integration_id}")
        return webhook
        
    except Exception as e:
        logger.error(f"Failed to process webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{webhook_id}")
async def get_webhook(
    webhook_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get webhook details"""
    try:
        logger.info(f"Getting webhook details for {webhook_id}")
        
        # In production, this would query from database
        # For now, return a mock response
        webhook = {
            "id": webhook_id,
            "integration_id": "integration_123",
            "event_type": "contact.created",
            "status": "processed",
            "received_at": datetime.utcnow().isoformat()
        }
        
        return webhook
        
    except Exception as e:
        logger.error(f"Failed to get webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_webhooks(
    integration_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """List webhooks"""
    try:
        logger.info("Listing webhooks")
        
        # In production, this would query from database with filters
        # For now, return a mock response
        webhooks = [
            {
                "id": "webhook_001",
                "integration_id": "integration_123",
                "event_type": "contact.created",
                "status": "processed",
                "received_at": datetime.utcnow().isoformat()
            }
        ]
        
        return {
            "total": len(webhooks),
            "webhooks": webhooks,
            "filters": {
                "integration_id": integration_id,
                "status": status
            },
            "pagination": {
                "limit": limit,
                "offset": offset
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to list webhooks: {e}")
        raise HTTPException(status_code=500, detail=str(e))
