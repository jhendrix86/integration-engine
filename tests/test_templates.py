"""templates.py is 100% mock - see tests/test_integrations.py's module docstring."""


async def test_list_templates(client):
    r = await client.get("/templates/")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == len(body["templates"])


async def test_list_templates_echoes_filter(client):
    r = await client.get("/templates/", params={"integration_type": "crm"})
    assert r.status_code == 200
    assert r.json()["filters"] == {"integration_type": "crm"}


async def test_install_template(client):
    """Regression test: installed_at used to be `logger.info(...)` (which
    returns None), the same bug fixed at /health - now real timestamps."""
    r = await client.post("/templates/template_001/install")
    assert r.status_code == 200
    body = r.json()
    assert body["template_id"] == "template_001"
    assert body["installed_at"] is not None
