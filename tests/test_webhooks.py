"""
webhooks.py is now real: registration/get/list hit the webhooks table,
and the receiver does real HMAC-SHA256 signature verification
(app/services/webhook_signature.py) against the webhook's own secret,
plus real persistence of receipt counters.
"""

import hashlib
import hmac
import json


async def _create_integration(client, **overrides):
    payload = {"name": "HubSpot CRM", "integration_type": "crm", "provider": "hubspot", "credentials": {}, "config": {}}
    payload.update(overrides)
    r = await client.post("/integrations/create", json=payload)
    return r.json()


async def _register_webhook(client, integration_id, **overrides):
    payload = {
        "integration_id": integration_id, "webhook_url": "https://us.example.com/hooks/x",
        "event_type": "contact.created", "secret": "a-real-secret",
    }
    payload.update(overrides)
    r = await client.post("/webhooks/", json=payload)
    assert r.status_code == 200
    return r.json()


async def test_register_webhook_persists_a_real_row(client):
    integration = await _create_integration(client)
    webhook = await _register_webhook(client, integration["id"])

    assert webhook["integration_id"] == integration["id"]
    assert webhook["event_type"] == "contact.created"
    assert webhook["status"] == "active"
    assert webhook["total_received"] == 0
    assert webhook["id"]  # a real generated UUID


async def test_register_webhook_for_unknown_integration_is_a_real_404(client):
    r = await client.post("/webhooks/", json={
        "integration_id": "00000000-0000-0000-0000-000000000000",
        "webhook_url": "https://x.example.com", "event_type": "contact.created", "secret": "shh",
    })
    assert r.status_code == 404


async def test_register_webhook_rejects_empty_secret(client):
    # SECURITY_REVIEW.md finding #6: verify_signature() honestly skips
    # verification when a webhook has no secret, so nothing should be able
    # to create one that way - a webhook without a secret accepts any
    # unsigned payload from anyone, forever.
    integration = await _create_integration(client)

    r = await client.post("/webhooks/", json={
        "integration_id": integration["id"], "webhook_url": "https://x.example.com",
        "event_type": "contact.created", "secret": "",
    })
    assert r.status_code == 422


async def test_register_webhook_requires_a_secret_field_at_all(client):
    integration = await _create_integration(client)

    r = await client.post("/webhooks/", json={
        "integration_id": integration["id"], "webhook_url": "https://x.example.com",
        "event_type": "contact.created",
    })
    assert r.status_code == 422


async def test_receive_webhook_with_a_real_secret_accepts_a_correctly_signed_payload(client):
    integration = await _create_integration(client)
    await _register_webhook(client, integration["id"], secret="shh")

    body = json.dumps({"contact_id": "c1", "email": "a@example.com"}).encode()
    signature = hmac.new(b"shh", body, hashlib.sha256).hexdigest()

    r = await client.post(
        f"/webhooks/{integration['id']}",
        content=body,
        headers={
            "X-Event-Type": "contact.created",
            "X-Webhook-Signature": f"sha256={signature}",
            "Content-Type": "application/json",
        },
    )

    assert r.status_code == 200
    body = r.json()
    assert body["integration_id"] == integration["id"]
    assert body["event_type"] == "contact.created"
    assert body["status"] == "processed"


async def test_receive_webhook_increments_real_counters(client, db_session):
    import uuid

    from sqlalchemy import select
    from app.models.webhook import Webhook

    integration = await _create_integration(client)
    registered = await _register_webhook(client, integration["id"])  # default secret: "a-real-secret"

    body = b"{}"
    signature = hmac.new(b"a-real-secret", body, hashlib.sha256).hexdigest()
    await client.post(
        f"/webhooks/{integration['id']}", content=body,
        headers={"X-Event-Type": "contact.created", "X-Webhook-Signature": f"sha256={signature}", "Content-Type": "application/json"},
    )

    result = await db_session.execute(select(Webhook).where(Webhook.id == uuid.UUID(registered["id"])))
    webhook = result.scalar_one()
    assert webhook.total_received == 1
    assert webhook.total_processed == 1
    assert webhook.last_received_at is not None


async def test_receive_webhook_for_unregistered_integration_is_a_real_404(client):
    integration = await _create_integration(client)  # no webhook registered for it
    r = await client.post(f"/webhooks/{integration['id']}", json={}, headers={"X-Event-Type": "contact.created"})
    assert r.status_code == 404


async def test_receive_webhook_rejects_bad_signature_when_secret_configured(client):
    integration = await _create_integration(client)
    await _register_webhook(client, integration["id"], secret="shh")

    r = await client.post(
        f"/webhooks/{integration['id']}", json={"a": 1}, headers={"X-Event-Type": "contact.created", "X-Webhook-Signature": "sha256=wrong"},
    )
    assert r.status_code == 401


async def test_receive_webhook_accepts_a_real_valid_signature(client):
    integration = await _create_integration(client)
    await _register_webhook(client, integration["id"], secret="shh")

    body = json.dumps({"a": 1}).encode()
    signature = hmac.new(b"shh", body, hashlib.sha256).hexdigest()

    r = await client.post(
        f"/webhooks/{integration['id']}",
        content=body,
        headers={
            "X-Event-Type": "contact.created",
            "X-Webhook-Signature": f"sha256={signature}",
            "Content-Type": "application/json",
        },
    )
    assert r.status_code == 200
    assert r.json()["status"] == "processed"


async def test_get_webhook_returns_the_real_row(client):
    integration = await _create_integration(client)
    registered = await _register_webhook(client, integration["id"])

    r = await client.get(f"/webhooks/{registered['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == registered["id"]


async def test_get_unknown_webhook_is_a_real_404(client):
    r = await client.get("/webhooks/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404


async def test_list_webhooks_filters_by_integration_id_for_real(client):
    integration_a = await _create_integration(client, name="a")
    integration_b = await _create_integration(client, name="b")
    await _register_webhook(client, integration_a["id"])
    await _register_webhook(client, integration_b["id"])

    r = await client.get("/webhooks/", params={"integration_id": integration_a["id"]})
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1
    assert body["webhooks"][0]["integration_id"] == integration_a["id"]
