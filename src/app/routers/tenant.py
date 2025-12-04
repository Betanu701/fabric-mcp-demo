"""
Tenant management admin router.
"""
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from ..dependencies import get_tenant_manager, require_admin
from ..models.tenant import TenantConfig
from ..services.tenant_manager import TenantManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/tenants", tags=["admin", "tenants"])


@router.get(
    "",
    response_model=List[TenantConfig],
    summary="List all tenants",
    description="Get list of all tenant configurations (admin only)"
)
async def list_tenants(
    _: bool = Depends(require_admin),
    tenant_manager: TenantManager = Depends(get_tenant_manager)
) -> List[TenantConfig]:
    """List all tenant configurations."""
    tenants = await tenant_manager.list_tenants()
    return tenants


@router.get(
    "/{tenant_id}",
    response_model=TenantConfig,
    summary="Get tenant details",
    description="Get detailed configuration for a specific tenant"
)
async def get_tenant(
    tenant_id: str,
    _: bool = Depends(require_admin),
    tenant_manager: TenantManager = Depends(get_tenant_manager)
) -> TenantConfig:
    """Get tenant configuration by ID."""
    tenant = await tenant_manager.get_tenant(tenant_id)
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant '{tenant_id}' not found"
        )
    
    return tenant


@router.post(
    "",
    response_model=TenantConfig,
    status_code=status.HTTP_201_CREATED,
    summary="Create new tenant",
    description="Create a new tenant configuration"
)
async def create_tenant(
    tenant_config: TenantConfig,
    _: bool = Depends(require_admin),
    tenant_manager: TenantManager = Depends(get_tenant_manager)
) -> TenantConfig:
    """Create new tenant."""
    try:
        created_tenant = await tenant_manager.create_tenant(tenant_config)
        logger.info(f"Created tenant: {created_tenant.id}")
        return created_tenant
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to create tenant: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create tenant"
        )


@router.put(
    "/{tenant_id}",
    response_model=TenantConfig,
    summary="Update tenant",
    description="Update an existing tenant configuration"
)
async def update_tenant(
    tenant_id: str,
    tenant_config: TenantConfig,
    _: bool = Depends(require_admin),
    tenant_manager: TenantManager = Depends(get_tenant_manager)
) -> TenantConfig:
    """Update tenant configuration."""
    # Ensure ID matches
    if tenant_config.id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant ID in path must match ID in body"
        )
    
    try:
        updated_tenant = await tenant_manager.update_tenant(tenant_config)
        logger.info(f"Updated tenant: {updated_tenant.id}")
        return updated_tenant
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to update tenant: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update tenant"
        )


@router.delete(
    "/{tenant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete tenant",
    description="Delete a tenant configuration (soft delete with recovery option)"
)
async def delete_tenant(
    tenant_id: str,
    _: bool = Depends(require_admin),
    tenant_manager: TenantManager = Depends(get_tenant_manager)
):
    """Delete tenant configuration."""
    try:
        await tenant_manager.delete_tenant(tenant_id)
        logger.info(f"Deleted tenant: {tenant_id}")
        return None
    except Exception as e:
        logger.error(f"Failed to delete tenant: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete tenant"
        )


@router.get(
    "/{tenant_id}/usage",
    summary="Get tenant usage metrics",
    description="Get usage statistics for a specific tenant"
)
async def get_tenant_usage(
    tenant_id: str,
    _: bool = Depends(require_admin),
    tenant_manager: TenantManager = Depends(get_tenant_manager)
):
    """Get tenant usage metrics."""
    # Verify tenant exists
    tenant = await tenant_manager.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant '{tenant_id}' not found"
        )
    
    # TODO: Integrate with usage tracking service
    return {
        "tenant_id": tenant_id,
        "message": "Usage metrics not yet implemented"
    }
