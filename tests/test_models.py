"""
Real tests for the SQLAlchemy models - previously completely untested
despite being the only real (non-mock) part of this engine.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.integration import Integration, IntegrationStatus, IntegrationType
from app.models.credential import Credential, CredentialType
from app.models.sync import SyncJob, SyncStatus
from app.models.webhook import Webhook, WebhookStatus


async def test_integration_webhook_relationship_round_trips(db_session):
    integration = Integration(
        name="HubSpot CRM", integration_type=IntegrationType.CRM, provider="hubspot",
        status=IntegrationStatus.ACTIVE, config={"sync_contacts": True},
    )
    db_session.add(integration)
    await db_session.flush()

    webhook = Webhook(integration_id=integration.id, webhook_url="https://example.com/hook", event_type="contact.created")
    db_session.add(webhook)
    await db_session.commit()

    result = await db_session.execute(select(Integration).where(Integration.id == integration.id))
    fetched = result.scalar_one()
    await db_session.refresh(fetched, attribute_names=["webhooks"])

    assert len(fetched.webhooks) == 1
    assert fetched.webhooks[0].event_type == "contact.created"
    assert fetched.webhooks[0].status == WebhookStatus.ACTIVE


async def test_integration_sync_job_relationship_round_trips(db_session):
    integration = Integration(
        name="Mailchimp", integration_type=IntegrationType.MARKETING, provider="mailchimp", config={},
    )
    db_session.add(integration)
    await db_session.flush()

    sync_job = SyncJob(integration_id=integration.id, sync_type="full", direction="pull", status=SyncStatus.PENDING)
    db_session.add(sync_job)
    await db_session.commit()

    result = await db_session.execute(select(Integration).where(Integration.id == integration.id))
    fetched = result.scalar_one()
    await db_session.refresh(fetched, attribute_names=["sync_jobs"])

    assert len(fetched.sync_jobs) == 1
    assert fetched.sync_jobs[0].sync_type == "full"


async def test_integration_credential_relationship_round_trips(db_session):
    integration = Integration(name="Salesforce", integration_type=IntegrationType.CRM, provider="salesforce", config={})
    db_session.add(integration)
    await db_session.flush()

    credential = Credential(
        integration_id=integration.id, credential_type=CredentialType.OAUTH,
        name="prod-oauth", encrypted_data={"ciphertext": "..."},
    )
    db_session.add(credential)
    await db_session.commit()

    result = await db_session.execute(select(Integration).where(Integration.id == integration.id))
    fetched = result.scalar_one()
    await db_session.refresh(fetched, attribute_names=["credentials"])

    assert len(fetched.credentials) == 1
    assert fetched.credentials[0].credential_type == CredentialType.OAUTH


async def test_webhook_requires_an_integration(db_session):
    """integration_id is a NOT NULL FK - a webhook can't exist without an integration."""
    webhook = Webhook(integration_id=uuid.uuid4(), webhook_url="https://example.com/hook", event_type="x")
    db_session.add(webhook)
    try:
        await db_session.commit()
        assert False, "expected an IntegrityError for a nonexistent integration_id"
    except IntegrityError:
        await db_session.rollback()


async def test_integration_defaults(db_session):
    integration = Integration(name="Custom API", integration_type=IntegrationType.CUSTOM, provider="internal", config={})
    db_session.add(integration)
    await db_session.commit()
    await db_session.refresh(integration)

    assert integration.status == IntegrationStatus.INACTIVE
    assert integration.auto_sync_enabled is False
    assert integration.sync_interval_hours == 24
    assert integration.error_count == 0
