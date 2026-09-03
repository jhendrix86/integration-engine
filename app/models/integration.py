"""
Integration models
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, Enum, ForeignKey, JSON
from sqlalchemy import Uuid
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base
from app.models.tenant_base import TenantBase


class IntegrationStatus(str, enum.Enum):
    """Integration status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    SYNCING = "syncing"


class IntegrationType(str, enum.Enum):
    """Integration type enumeration"""
    CRM = "crm"
    MARKETING = "marketing"
    ANALYTICS = "analytics"
    PRODUCTIVITY = "productivity"
    CUSTOM = "custom"


class Integration(TenantBase, Base):
    """Integration model"""
    __tablename__ = "integrations"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Integration details
    name = Column(String(255), nullable=False)
    integration_type = Column(Enum(IntegrationType), nullable=False)
    provider = Column(String(100), nullable=False)  # hubspot, salesforce, etc.
    
    # Status
    status = Column(Enum(IntegrationStatus), default=IntegrationStatus.INACTIVE)
    
    # Configuration
    config = Column(JSON, nullable=False)
    
    # Sync settings
    auto_sync_enabled = Column(Boolean, default=False)
    sync_interval_hours = Column(Integer, default=24)
    last_sync_at = Column(DateTime, nullable=True)
    next_sync_at = Column(DateTime, nullable=True)
    
    # Error handling
    last_error = Column(String(500), nullable=True)
    error_count = Column(Integer, default=0)
    
    # Metadata
    extra_metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    webhooks = relationship("Webhook", back_populates="integration")
    sync_jobs = relationship("SyncJob", back_populates="integration")
    credentials = relationship("Credential", back_populates="integration")
    
    def __repr__(self):
        return f"<Integration {self.name} - {self.provider} - {self.status}>"
