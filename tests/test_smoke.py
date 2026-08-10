"""
Integration Engine smoke tests
"""
import pytest


@pytest.mark.asyncio
async def test_app_instantiation():
    """Verify FastAPI app instantiates without error"""
    from app.main import app
    assert app is not None
    assert app.title == "Integration Engine"


@pytest.mark.asyncio
async def test_models_import():
    """Verify core models import without error"""
    from app.models import Webhook, Integration, Event
    assert Webhook is not None
    assert Integration is not None
    assert Event is not None
