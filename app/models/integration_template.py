"""
Integration template models

Unlike every other model in this engine, IntegrationTemplate does NOT
inherit TenantBase - it's a shared, read-only catalog (which providers
this engine knows how to install as a starting-point Integration), not
per-tenant data. This is the opposite call from notification-engine's
Digest fix last session (which DID need TenantBase, because it held real
per-tenant recipient data) - the two aren't the same shape of problem.
"""

from sqlalchemy import Column, String, DateTime, Boolean, Enum, JSON
from sqlalchemy import Uuid
from datetime import datetime
import uuid

from app.database import Base
from app.models.integration import IntegrationType


class IntegrationTemplate(Base):
    """A reusable starting-point config for a known provider"""
    __tablename__ = "integration_templates"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)

    name = Column(String(255), unique=True, nullable=False)
    integration_type = Column(Enum(IntegrationType), nullable=False)
    provider = Column(String(100), nullable=False)
    description = Column(String(1000), nullable=True)
    features = Column(JSON, nullable=True)  # list of strings
    default_config = Column(JSON, nullable=True)
    is_popular = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<IntegrationTemplate {self.name} - {self.provider}>"
