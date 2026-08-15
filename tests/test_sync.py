"""
sync.py is now real: /configure persists a pending sync_jobs row,
/{id}/trigger actually runs it (app/services/sync_engine.py - a real
httpx call against the integration's own config['sync_url'], mocked here
via respx), /{id}/status reads the real row.
"""

import httpx
import respx


async def _create_integration(client, sync_url=None, **overrides):
    payload = {
        "name": "HubSpot CRM", "integration_type": "crm", "provider": "hubspot",
        "credentials": {}, "config": {"sync_url": sync_url} if sync_url else {},
    }
    payload.update(overrides)
    r = await client.post("/integrations/create", json=payload)
    assert r.status_code == 200
    return r.json()


async def test_configure_sync_persists_a_real_pending_row(client):
    integration = await _create_integration(client)

    r = await client.post("/sync/configure", json={
        "integration_id": integration["id"], "sync_type": "full", "direction": "pull", "config": {"batch_size": 100},
    })
    assert r.status_code == 200
    body = r.json()
    assert body["integration_id"] == integration["id"]
    assert body["sync_type"] == "full"
    assert body["status"] == "pending"
    assert body["id"]  # a real generated UUID, not "sync_config_123"


async def test_configure_sync_requires_declared_fields(client):
    r = await client.post("/sync/configure", json={"integration_id": "x"})
    assert r.status_code == 422


async def test_configure_sync_for_unknown_integration_is_a_real_404(client):
    r = await client.post("/sync/configure", json={
        "integration_id": "00000000-0000-0000-0000-000000000000", "sync_type": "full", "direction": "pull",
    })
    assert r.status_code == 404


async def test_get_sync_status_returns_the_real_row(client):
    integration = await _create_integration(client)
    configured = (await client.post("/sync/configure", json={
        "integration_id": integration["id"], "sync_type": "full", "direction": "pull",
    })).json()

    r = await client.get(f"/sync/{configured['id']}/status")
    assert r.status_code == 200
    assert r.json()["id"] == configured["id"]
    assert r.json()["status"] == "pending"


async def test_get_sync_status_for_unknown_job_is_a_real_404(client):
    r = await client.get("/sync/00000000-0000-0000-0000-000000000000/status")
    assert r.status_code == 404


async def test_trigger_sync_without_sync_url_reports_honest_failure(client):
    integration = await _create_integration(client)  # no sync_url configured
    configured = (await client.post("/sync/configure", json={
        "integration_id": integration["id"], "sync_type": "full", "direction": "pull",
    })).json()

    r = await client.post(f"/sync/{configured['id']}/trigger")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "failed"
    assert "sync_url" in body["error_message"]


@respx.mock
async def test_trigger_sync_pulls_real_records_from_the_configured_endpoint(client):
    respx.get("https://api.example.com/contacts").mock(
        return_value=httpx.Response(200, json={"records": [{"id": 1}, {"id": 2}, {"id": 3}]})
    )

    integration = await _create_integration(client, sync_url="https://api.example.com/contacts")
    configured = (await client.post("/sync/configure", json={
        "integration_id": integration["id"], "sync_type": "full", "direction": "pull",
    })).json()

    r = await client.post(f"/sync/{configured['id']}/trigger")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "completed"
    assert body["processed_records"] == 3
    assert body["records_created"] == 3
    assert body["progress_percentage"] == 100.0

    integration_after = (await client.get(f"/integrations/{integration['id']}")).json()
    assert integration_after["status"] == "active"
    assert integration_after["last_sync_at"] is not None


@respx.mock
async def test_trigger_sync_reports_honest_failure_on_error_response(client):
    respx.get("https://api.example.com/contacts").mock(return_value=httpx.Response(500, text="server error"))

    integration = await _create_integration(client, sync_url="https://api.example.com/contacts")
    configured = (await client.post("/sync/configure", json={
        "integration_id": integration["id"], "sync_type": "full", "direction": "pull",
    })).json()

    r = await client.post(f"/sync/{configured['id']}/trigger")
    body = r.json()
    assert body["status"] == "failed"
    assert "500" in body["error_message"]

    integration_after = (await client.get(f"/integrations/{integration['id']}")).json()
    assert integration_after["status"] == "error"
    assert integration_after["error_count"] == 1


async def test_trigger_sync_for_unknown_job_is_a_real_404(client):
    r = await client.post("/sync/00000000-0000-0000-0000-000000000000/trigger")
    assert r.status_code == 404


@respx.mock
async def test_trigger_already_completed_sync_is_rejected(client):
    respx.get("https://api.example.com/contacts").mock(return_value=httpx.Response(200, json={"records": []}))

    integration = await _create_integration(client, sync_url="https://api.example.com/contacts")
    configured = (await client.post("/sync/configure", json={
        "integration_id": integration["id"], "sync_type": "full", "direction": "pull",
    })).json()

    await client.post(f"/sync/{configured['id']}/trigger")
    r = await client.post(f"/sync/{configured['id']}/trigger")
    assert r.status_code == 409
