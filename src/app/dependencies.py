"""
FastAPI dependency injection providers.
"""
from functools import lru_cache
from typing import Optional

from fastapi import Depends, Header, HTTPException, Request, status

from .config import Settings, get_settings
from .models.tenant import TenantConfig
from .services.tenant_manager import TenantManager


# Cached instances
_tenant_manager: Optional[TenantManager] = None


def get_tenant_manager(settings: Settings = Depends(get_settings)) -> TenantManager:
    """Get tenant manager instance (singleton)."""
    global _tenant_manager
    if _tenant_manager is None:
        _tenant_manager = TenantManager(settings)
    return _tenant_manager


async def get_tenant_id(
    request: Request,
    x_tenant_id: Optional[str] = Header(default=None, alias="x-tenant-id")
) -> str:
    """
    Extract tenant ID from request.
    Falls back to request state if header not provided.
    """
    # Try request state first (set by middleware)
    if hasattr(request.state, "tenant_id") and request.state.tenant_id:
        return request.state.tenant_id
    
    # Fall back to header
    if x_tenant_id:
        return x_tenant_id
    
    # Default tenant
    return "default"


async def get_tenant_config(
    request: Request,
    tenant_manager: TenantManager = Depends(get_tenant_manager)
) -> TenantConfig:
    """
    Get tenant configuration from request state.
    Raises 403 if tenant is invalid or disabled.
    """
    # Check request state first (set by middleware)
    if hasattr(request.state, "tenant_config") and request.state.tenant_config:
        return request.state.tenant_config
    
    # Try loading from tenant manager
    tenant_id = await get_tenant_id(request)
    tenant_config = await tenant_manager.get_tenant(tenant_id)
    
    if not tenant_config:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Tenant '{tenant_id}' not found or disabled"
        )
    
    if not tenant_config.enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Tenant '{tenant_id}' is disabled"
        )
    
    return tenant_config


async def require_admin(
    request: Request,
    # TODO: Add actual authentication check
) -> bool:
    """
    Require admin access for endpoint.
    Currently placeholder - will integrate with Entra ID.
    """
    # TODO: Implement actual admin role check
    # For now, allow all requests to admin endpoints
    return True
