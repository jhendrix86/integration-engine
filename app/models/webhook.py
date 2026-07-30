"""
Webhook models
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, Enum, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base


class WebhookStatus(str, enum.Enum):
    """Webhook status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"


class Webhook(Base):
    """Webhook model"""
    __tablename__ = "webhooks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    integration_id = Column(UUID(as_uuid=True), ForeignKey("integrations.id"), nullable=False)
    
    # Webhook details
    webhook_url = Column(String(500), nullable=False)
    event_type = Column(String(100), nullable=False)
    
    # Status
    status = Column(Enum(WebhookStatus), default=WebhookStatus.ACTIVE)
    
    # Security
    secret = Column(String(255), nullable=True)
    
    # Processing
    last_received_at = Column(DateTime, nullable=True)
    total_received = Column(Integer, default=0)
    total_processed = Column(Integer, default=0)
    total_failed = Column(Integer, default=0)
    
    # Error handling
    last_error = Column(String(500), nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    integration = relationship("Integration", back_populates="webhooks")
    
    def __repr__(self):
        return f"<Webhook {self.event_type} - {self.status}>"
