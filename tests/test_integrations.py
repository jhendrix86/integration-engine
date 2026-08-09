"""
integrations.py is currently 100% mock (every endpoint has a "# In
production, this would ... For now, return a mock response" comment and
never touches the database) - real DB persistence for this router is a
bigger, separate task, not in scope here. These tests cover what's actually
true today: routing/response-shape regressions, request validation, and the
one piece of genuinely computed logic - next_sync_at's math.
"""

from datetime import datetime

import pytest


async def test_create_integration_returns_the_submitted_fields(client):
    r = await client.post("/integrations/create", json={
        "name": "HubSpot CRM", "integration_type": "crm", "provider": "hubspot",
        "credentials": {"api_key": "x"}, "config": {"sync_contacts": True},
    })

    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "HubSpot CRM"
    assert body["provider"] == "hubspot"
    assert body["status"] == "active"


async def test_create_integration_requires_declared_fields(client):
    r = await client.post("/integrations/create", json={"name": "x"})
    assert r.status_code == 422


async def test_next_sync_at_matches_sync_interval_hours(client):
    r = await client.post("/integrations/create", json={
        "name": "Mailchimp", "integration_type": "marketing", "provider": "mailchimp",
        "credentials": {}, "config": {}, "sync_interval_hours": 6,
    })
    body = r.json()
    created = datetime.fromisoformat(body["created_at"])
    next_sync = datetime.fromisoformat(body["next_sync_at"])
    assert (next_sync - created).total_seconds() == pytest.approx(6 * 3600, abs=1)


async def test_next_sync_at_defaults_to_24_hours(client):
    r = await client.post("/integrations/create", json={
        "name": "Salesforce", "integration_type": "crm", "provider": "salesforce",
        "credentials": {}, "config": {},
    })
    body = r.json()
    created = datetime.fromisoformat(body["created_at"])
    next_sync = datetime.fromisoformat(body["next_sync_at"])
    assert (next_sync - created).total_seconds() == pytest.approx(24 * 3600, abs=1)


async def test_trigger_sync(client):
    r = await client.post("/integrations/integration_123/sync")
    assert r.status_code == 200
    assert r.json()["status"] == "running"


async def test_get_integration(client):
    r = await client.get("/integrations/integration_123")
    assert r.status_code == 200
    assert r.json()["id"] == "integration_123"


async def test_list_integrations(client):
    r = await client.get("/integrations/")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == len(body["integrations"])


async def test_list_integrations_echoes_filters(client):
    r = await client.get("/integrations/", params={"status": "active", "integration_type": "crm"})
    assert r.status_code == 200
    assert r.json()["filters"] == {"status": "active", "integration_type": "crm"}
