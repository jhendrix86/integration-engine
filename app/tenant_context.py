"""
Tenant context management for multi-tenancy support
"""

from contextvars import ContextVar
from typing import Optional
from uuid import UUID

tenant_context: ContextVar[Optional[UUID]] = ContextVar("tenant_context", default=None)


def set_tenant_context(tenant_id: UUID) -> None:
    """Set the tenant context for the current request."""
    tenant_context.set(tenant_id)


def get_tenant_context() -> Optional[UUID]:
    """Get the current tenant context."""
    return tenant_context.get()


def clear_tenant_context() -> None:
    """Clear the tenant context."""
    tenant_context.set(None)
