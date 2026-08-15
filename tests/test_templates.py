"""
templates.py is now real: the catalog is a real, seeded
integration_templates table (app/seed_templates.py) instead of a literal
list in the router, and /install creates a real Integration row.
"""


async def test_list_templates_reflects_the_real_seeded_catalog(client):
    r = await client.get("/templates/")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == len(body["templates"])
    assert body["total"] > 0
    assert any(t["provider"] == "hubspot" for t in body["templates"])


async def test_list_templates_filters_by_type_for_real(client):
    r = await client.get("/templates/", params={"integration_type": "crm"})
    assert r.status_code == 200
    body = r.json()
    assert body["total"] > 0
    assert all(t["integration_type"] == "crm" for t in body["templates"])


async def test_get_unknown_template_is_a_real_404(client):
    r = await client.get("/templates/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404


async def test_install_template_creates_a_real_integration(client):
    templates = (await client.get("/templates/", params={"integration_type": "crm"})).json()["templates"]
    hubspot = next(t for t in templates if t["provider"] == "hubspot")

    r = await client.post(f"/templates/{hubspot['id']}/install")
    assert r.status_code == 200
    body = r.json()
    assert body["template_id"] == hubspot["id"]
    assert body["name"] == "HubSpot CRM"
    assert body["installed_at"] is not None

    integration = (await client.get(f"/integrations/{body['id']}")).json()
    assert integration["provider"] == "hubspot"
    assert integration["integration_type"] == "crm"


async def test_install_template_accepts_a_custom_name(client):
    templates = (await client.get("/templates/")).json()["templates"]
    template = templates[0]

    r = await client.post(f"/templates/{template['id']}/install", json={"name": "My Custom HubSpot"})
    assert r.status_code == 200
    assert r.json()["name"] == "My Custom HubSpot"


async def test_install_unknown_template_is_a_real_404(client):
    r = await client.post("/templates/00000000-0000-0000-0000-000000000000/install")
    assert r.status_code == 404
