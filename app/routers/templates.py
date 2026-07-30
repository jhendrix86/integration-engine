"""
Templates router
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from loguru import logger

from app.database import get_db

router = APIRouter()


@router.get("/")
async def list_templates(
    integration_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List integration templates"""
    try:
        logger.info("Listing integration templates")
        
        # In production, this would query from database
        # For now, return a mock response
        templates = [
            {
                "id": "template_001",
                "name": "HubSpot CRM",
                "integration_type": "crm",
                "provider": "hubspot",
                "description": "Full HubSpot CRM integration with contacts, deals, and companies sync",
                "features": ["contacts", "deals", "companies", "activities"],
                "is_popular": True
            },
            {
                "id": "template_002",
                "name": "Salesforce",
                "integration_type": "crm",
                "provider": "salesforce",
                "description": "Enterprise Salesforce integration with full object sync",
                "features": ["accounts", "contacts", "opportunities", "leads"],
                "is_popular": True
            },
            {
                "id": "template_003",
                "name": "Mailchimp",
                "integration_type": "marketing",
                "provider": "mailchimp",
                "description": "Email marketing integration with list and campaign sync",
                "features": ["lists", "campaigns", "subscribers", "reports"],
                "is_popular": False
            }
        ]
        
        return {
            "total": len(templates),
            "templates": templates,
            "filters": {
                "integration_type": integration_type
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to list templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{template_id}/install")
async def install_template(
    template_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Install integration template"""
    try:
        logger.info(f"Installing template {template_id}")
        
        # In production, this would create integration from template
        # For now, return a mock response
        integration = {
            "id": "integration_123",
            "template_id": template_id,
            "name": "HubSpot CRM",
            "status": "active",
            "installed_at": logger.info("Template installed")
        }
        
        logger.info(f"Template installed: {template_id}")
        return integration
        
    except Exception as e:
        logger.error(f"Failed to install template: {e}")
        raise HTTPException(status_code=500, detail=str(e))
