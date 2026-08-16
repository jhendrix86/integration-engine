"""
Verifies tenant context assignment for integration-engine endpoints.
Tests that apply_tenant_context() correctly assigns tenant_id on create.
Note: Automatic query filtering is not yet implemented - this test validates
create-time tenant assignment only.
"""

# Use fixed UUIDs that match what we create in conftest
TENANT_A = "3e2a7c54-a950-48f3-9eb9-d1eb6b2d1be2"
TENANT_B = "00000000-0000-0000-0000-000000000001"


async def test_apply_tenant_context_on_integration_create(client, db_session):
    """Verify that apply_tenant_context assigns tenant_id on integration creation."""
    from sqlalchemy import select
    from app.models.integration import Integration
    import uuid
    
    # Create integration for tenant A
    result = await client.post(
        "/integrations/create",
        json={
            "name": "Test Integration",
            "integration_type": "crm",
            "provider": "hubspot",
            "credentials": {"api_key": "test-key"},
            "config": {"sync_contacts": True},
        },
        headers={"X-Tenant-ID": TENANT_A}
    )
    assert result.status_code == 200
    integration_id = result.json()["id"]
    
    # Verify tenant_id was correctly assigned
    integration = await db_session.get(Integration, uuid.UUID(integration_id))
    assert integration is not None
    assert str(integration.tenant_id) == TENANT_A


async def test_apply_tenant_context_on_credential_create(client, db_session):
    """Verify that apply_tenant_context assigns tenant_id on credential creation."""
    from sqlalchemy import select
    from app.models.credential import Credential
    import uuid
    
    # Create integration with credentials for tenant A
    result = await client.post(
        "/integrations/create",
        json={
            "name": "Test Integration",
            "integration_type": "crm",
            "provider": "hubspot",
            "credentials": {"api_key": "test-key"},
            "config": {"sync_contacts": True},
        },
        headers={"X-Tenant-ID": TENANT_A}
    )
    assert result.status_code == 200
    integration_id = result.json()["id"]
    
    # Verify credential tenant_id was correctly assigned
    result = await db_session.execute(select(Credential).where(Credential.integration_id == uuid.UUID(integration_id)))
    credential = result.scalars().first()
    assert credential is not None
    assert str(credential.tenant_id) == TENANT_A


async def test_apply_tenant_context_on_sync_job_create(client, db_session):
    """Verify that apply_tenant_context assigns tenant_id on sync job creation."""
    from sqlalchemy import select
    from app.models.sync import SyncJob
    import uuid
    
    # Create integration for tenant A
    result = await client.post(
        "/integrations/create",
        json={
            "name": "Test Integration",
            "integration_type": "crm",
            "provider": "hubspot",
            "credentials": {"api_key": "test-key"},
            "config": {"sync_contacts": True},
        },
        headers={"X-Tenant-ID": TENANT_A}
    )
    assert result.status_code == 200
    integration_id = result.json()["id"]
    
    # Trigger sync job
    sync_result = await client.post(
        f"/integrations/{integration_id}/sync",
        headers={"X-Tenant-ID": TENANT_A}
    )
    assert sync_result.status_code == 200
    sync_job_id = sync_result.json()["id"]
    
    # Verify sync job tenant_id was correctly assigned
    sync_job = await db_session.get(SyncJob, uuid.UUID(sync_job_id))
    assert sync_job is not None
    assert str(sync_job.tenant_id) == TENANT_A


async def test_apply_tenant_context_on_webhook_create(client, db_session):
    """Verify that apply_tenant_context assigns tenant_id on webhook creation."""
    from sqlalchemy import select
    from app.models.webhook import Webhook
    import uuid
    
    # Create integration for tenant A
    result = await client.post(
        "/integrations/create",
        json={
            "name": "Test Integration",
            "integration_type": "crm",
            "provider": "hubspot",
            "credentials": {"api_key": "test-key"},
            "config": {"sync_contacts": True},
        },
        headers={"X-Tenant-ID": TENANT_A}
    )
    assert result.status_code == 200
    integration_id = result.json()["id"]
    
    # Register webhook
    webhook_result = await client.post(
        "/webhooks/",
        json={
            "integration_id": integration_id,
            "webhook_url": "https://example.com/webhook",
            "event_type": "contact.created",
            "secret": "test-secret"
        },
        headers={"X-Tenant-ID": TENANT_A}
    )
    assert webhook_result.status_code == 200
    webhook_id = webhook_result.json()["id"]
    
    # Verify webhook tenant_id was correctly assigned
    webhook = await db_session.get(Webhook, uuid.UUID(webhook_id))
    assert webhook is not None
    assert str(webhook.tenant_id) == TENANT_A
