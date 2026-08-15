"""
Seeds the integration_templates catalog on first boot. This is reference
data (a picklist of known providers this engine can install a starting
Integration for), not a fabricated live API response - same category as
a real app shipping default roles/permissions rows. Idempotent: only
inserts if the table is empty.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.integration import IntegrationType
from app.models.integration_template import IntegrationTemplate

_CATALOG = [
    {
        "name": "HubSpot CRM", "integration_type": IntegrationType.CRM, "provider": "hubspot",
        "description": "Full HubSpot CRM integration with contacts, deals, and companies sync",
        "features": ["contacts", "deals", "companies", "activities"], "is_popular": True,
        "default_config": {},
    },
    {
        "name": "Salesforce", "integration_type": IntegrationType.CRM, "provider": "salesforce",
        "description": "Enterprise Salesforce integration with full object sync",
        "features": ["accounts", "contacts", "opportunities", "leads"], "is_popular": True,
        "default_config": {},
    },
    {
        "name": "Pipedrive", "integration_type": IntegrationType.CRM, "provider": "pipedrive",
        "description": "Pipedrive CRM integration with deals and pipeline sync",
        "features": ["deals", "persons", "organizations"], "is_popular": False,
        "default_config": {},
    },
    {
        "name": "Mailchimp", "integration_type": IntegrationType.MARKETING, "provider": "mailchimp",
        "description": "Email marketing integration with list and campaign sync",
        "features": ["lists", "campaigns", "subscribers", "reports"], "is_popular": False,
        "default_config": {},
    },
    {
        "name": "SendGrid", "integration_type": IntegrationType.MARKETING, "provider": "sendgrid",
        "description": "Transactional and marketing email delivery integration",
        "features": ["email_send", "templates", "stats"], "is_popular": False,
        "default_config": {},
    },
    {
        "name": "Google Analytics", "integration_type": IntegrationType.ANALYTICS, "provider": "google_analytics",
        "description": "Website analytics and traffic reporting integration",
        "features": ["pageviews", "sessions", "conversions"], "is_popular": True,
        "default_config": {},
    },
    {
        "name": "Slack", "integration_type": IntegrationType.PRODUCTIVITY, "provider": "slack",
        "description": "Team messaging and notification integration",
        "features": ["messages", "channels"], "is_popular": True,
        "default_config": {},
    },
    {
        "name": "Notion", "integration_type": IntegrationType.PRODUCTIVITY, "provider": "notion",
        "description": "Workspace and database sync integration",
        "features": ["pages", "databases"], "is_popular": False,
        "default_config": {},
    },
]


async def seed_default_templates(session: AsyncSession) -> None:
    existing = await session.execute(select(IntegrationTemplate.id).limit(1))
    if existing.scalar_one_or_none() is not None:
        return  # already seeded

    for entry in _CATALOG:
        session.add(IntegrationTemplate(**entry))
    await session.commit()
