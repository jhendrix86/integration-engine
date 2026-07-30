"""
Credential models
"""

from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base


class CredentialType(str, enum.Enum):
    """Credential type enumeration"""
    API_KEY = "api_key"
    OAUTH = "oauth"
    BASIC_AUTH = "basic_auth"
    TOKEN = "token"


class Credential(Base):
    """Credential model"""
    __tablename__ = "credentials"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    integration_id = Column(UUID(as_uuid=True), ForeignKey("integrations.id"), nullable=False)
    
    # Credential details
    credential_type = Column(Enum(CredentialType), nullable=False)
    name = Column(String(255), nullable=False)
    
    # Encrypted credentials
    encrypted_data = Column(JSON, nullable=False)
    
    # OAuth specific
    oauth_token = Column(String(500), nullable=True)
    oauth_refresh_token = Column(String(500), nullable=True)
    oauth_expires_at = Column(DateTime, nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    integration = relationship("Integration", back_populates="credentials")
    
    def __repr__(self):
        return f"<Credential {self.name} - {self.credential_type}>"
