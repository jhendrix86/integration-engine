"""sync.py is 100% mock - see tests/test_integrations.py's module docstring."""


async def test_configure_sync_returns_the_submitted_fields(client):
    r = await client.post("/sync/configure", json={
        "integration_id": "integration_123", "sync_type": "full", "direction": "pull", "config": {"batch_size": 100},
    })
    assert r.status_code == 200
    body = r.json()
    assert body["integration_id"] == "integration_123"
    assert body["sync_type"] == "full"


async def test_configure_sync_requires_declared_fields(client):
    r = await client.post("/sync/configure", json={"integration_id": "x"})
    assert r.status_code == 422


async def test_get_sync_status(client):
    """Regression test: this endpoint used `timedelta` without importing it -
    a real NameError that only import-checking app.main wouldn't have caught,
    since it only surfaces when the endpoint actually runs."""
    r = await client.get("/sync/sync_job_123/status")
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == "sync_job_123"
    assert 0 <= body["progress_percentage"] <= 100


async def test_trigger_sync(client):
    r = await client.post("/sync/sync_job_123/trigger")
    assert r.status_code == 200
    assert r.json()["status"] == "running"
