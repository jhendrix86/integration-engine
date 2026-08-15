"""integrations.py is now real: every endpoint reads/writes the integrations table."""

from datetime import datetime

import pytest


async def _create_integration(client, **overrides):
    payload = {
        "name": "HubSpot CRM", "integration_type": "crm", "provider": "hubspot",
        "credentials": {"api_key": "x"}, "config": {"sync_contacts": True},
    }
    payload.update(overrides)
    r = await client.post("/integrations/create", json=payload)
    assert r.status_code == 200
    return r.json()


async def test_create_integration_persists_a_real_row(client):
    body = await _create_integration(client)
    assert body["name"] == "HubSpot CRM"
    assert body["provider"] == "hubspot"
    assert body["status"] == "active"
    assert body["id"]  # a real generated UUID, not "integration_123"


async def test_create_integration_requires_declared_fields(client):
    r = await client.post("/integrations/create", json={"name": "x"})
    assert r.status_code == 422


async def test_create_integration_rejects_invalid_type(client):
    r = await client.post("/integrations/create", json={
        "name": "x", "integration_type": "not_a_real_type", "provider": "y", "credentials": {}, "config": {},
    })
    assert r.status_code == 422


async def test_create_integration_persists_credentials_as_a_real_credential_row(client, db_session):
    from sqlalchemy import select
    from app.models.credential import Credential

    created = await _create_integration(client, credentials={"api_key": "secret-123"})

    result = await db_session.execute(select(Credential))
    credentials = result.scalars().all()
    assert len(credentials) == 1
    assert str(credentials[0].integration_id) == created["id"]
    # Unconfigured ENCRYPTION_KEY in tests - stored honestly as unencrypted, not silently faked.
    assert credentials[0].encrypted_data["encrypted"] is False
    assert credentials[0].encrypted_data["data"] == {"api_key": "secret-123"}


async def test_next_sync_at_matches_sync_interval_hours_when_auto_sync_enabled(client):
    body = await _create_integration(client, name="Mailchimp", sync_interval_hours=6, auto_sync_enabled=True)
    created = datetime.fromisoformat(body["created_at"])
    next_sync = datetime.fromisoformat(body["next_sync_at"])
    assert (next_sync - created).total_seconds() == pytest.approx(6 * 3600, abs=1)


async def test_next_sync_at_is_unset_without_auto_sync(client):
    body = await _create_integration(client, auto_sync_enabled=False)
    assert body["next_sync_at"] is None


async def test_trigger_sync_without_sync_url_configured_reports_honest_failure(client):
    created = await _create_integration(client)
    r = await client.post(f"/integrations/{created['id']}/sync")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "failed"
    assert "sync_url" in body["error_message"]


async def test_trigger_sync_for_unknown_integration_is_a_real_404(client):
    r = await client.post("/integrations/00000000-0000-0000-0000-000000000000/sync")
    assert r.status_code == 404


async def test_get_integration_returns_the_real_row(client):
    created = await _create_integration(client)
    r = await client.get(f"/integrations/{created['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == created["id"]


async def test_get_unknown_integration_is_a_real_404(client):
    r = await client.get("/integrations/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404


async def test_list_integrations_reflects_real_created_rows(client):
    await _create_integration(client, name="one", provider="hubspot")
    await _create_integration(client, name="two", provider="mailchimp", integration_type="marketing")

    r = await client.get("/integrations/")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 2
    assert {i["name"] for i in body["integrations"]} == {"one", "two"}


async def test_list_integrations_filters_by_type_for_real(client):
    await _create_integration(client, name="crm-one", integration_type="crm")
    await _create_integration(client, name="marketing-one", integration_type="marketing")

    r = await client.get("/integrations/", params={"integration_type": "crm"})
    body = r.json()
    assert body["total"] == 1
    assert body["integrations"][0]["name"] == "crm-one"
