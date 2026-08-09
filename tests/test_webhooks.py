"""webhooks.py is 100% mock - see tests/test_integrations.py's module docstring."""


async def test_receive_webhook_echoes_payload_and_event_type(client):
    r = await client.post(
        "/webhooks/integration_123",
        json={"contact_id": "c1", "email": "a@example.com"},
        headers={"X-Event-Type": "contact.created"},
    )

    assert r.status_code == 200
    body = r.json()
    assert body["integration_id"] == "integration_123"
    assert body["event_type"] == "contact.created"
    assert body["payload"] == {"contact_id": "c1", "email": "a@example.com"}
    assert body["status"] == "processed"


async def test_receive_webhook_defaults_event_type_when_header_missing(client):
    r = await client.post("/webhooks/integration_123", json={})
    assert r.status_code == 200
    assert r.json()["event_type"] == "unknown"


async def test_get_webhook(client):
    r = await client.get("/webhooks/webhook_123")
    assert r.status_code == 200
    assert r.json()["id"] == "webhook_123"


async def test_list_webhooks(client):
    r = await client.get("/webhooks/")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == len(body["webhooks"])


async def test_list_webhooks_echoes_filters(client):
    r = await client.get("/webhooks/", params={"integration_id": "integration_123", "status": "processed"})
    assert r.status_code == 200
    assert r.json()["filters"] == {"integration_id": "integration_123", "status": "processed"}
