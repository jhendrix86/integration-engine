"""
Templates router - real DB-backed catalog (app/models/integration_template.py,
seeded on boot by app/seed_templates.py) instead of a hand-written list
literal in the router. /install now actually creates a real Integration
row from the template.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from pydantic import BaseModel
from loguru import logger

from app.database import get_db
from app.models.integration import Integration, IntegrationStatus, IntegrationType
from app.models.integration_template import IntegrationTemplate
from app.models.tenant_base import apply_tenant_context

router = APIRouter()


class InstallTemplateRequest(BaseModel):
    """Optional overrides when installing a template as a real integration"""
    name: Optional[str] = None
    config: Optional[dict] = None


def _serialize(template: IntegrationTemplate) -> dict:
    return {
        "id": str(template.id),
        "name": template.name,
        "integration_type": template.integration_type.value,
        "provider": template.provider,
        "description": template.description,
        "features": template.features,
        "is_popular": template.is_popular,
    }


async def _get_template_or_404(db: AsyncSession, template_id: str) -> IntegrationTemplate:
    try:
        template_uuid = uuid.UUID(template_id)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found")

    template = await db.get(IntegrationTemplate, template_uuid)
    if template is None:
        raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found")
    return template


@router.get("/")
async def list_templates(integration_type: Optional[IntegrationType] = None, db: AsyncSession = Depends(get_db)):
    """List integration templates, real query against the seeded catalog"""
    try:
        query = select(IntegrationTemplate)
        if integration_type is not None:
            query = query.where(IntegrationTemplate.integration_type == integration_type)

        result = await db.execute(query.order_by(IntegrationTemplate.name))
        templates = result.scalars().all()

        return {
            "total": len(templates),
            "templates": [_serialize(t) for t in templates],
            "filters": {"integration_type": integration_type.value if integration_type else None},
        }

    except Exception as e:
        logger.error(f"Failed to list templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{template_id}")
async def get_template(template_id: str, db: AsyncSession = Depends(get_db)):
    """Get template details"""
    try:
        template = await _get_template_or_404(db, template_id)
        return _serialize(template)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{template_id}/install")
async def install_template(template_id: str, request: InstallTemplateRequest = InstallTemplateRequest(), db: AsyncSession = Depends(get_db)):
    """Install an integration template - creates a real Integration row"""
    try:
        template = await _get_template_or_404(db, template_id)
        logger.info(f"Installing template {template_id}")

        integration = Integration(
            name=request.name or template.name,
            integration_type=template.integration_type,
            provider=template.provider,
            status=IntegrationStatus.INACTIVE,  # needs real credentials before it can go active
            config={**(template.default_config or {}), **(request.config or {})},
        )
        apply_tenant_context(integration)
        db.add(integration)
        await db.commit()
        await db.refresh(integration)

        logger.info(f"Template installed: {template_id} -> integration {integration.id}")
        return {
            "id": str(integration.id),
            "template_id": template_id,
            "name": integration.name,
            "status": integration.status.value,
            "installed_at": integration.created_at.isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to install template: {e}")
        raise HTTPException(status_code=500, detail=str(e))
