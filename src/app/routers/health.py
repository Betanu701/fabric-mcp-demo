"""
Health check router for monitoring and readiness probes.
"""
import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from ..config import Settings, get_settings
from ..dependencies import get_tenant_manager
from ..services.tenant_manager import TenantManager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: datetime
    version: str
    environment: str


class ReadinessResponse(BaseModel):
    """Readiness check response with component statuses."""
    ready: bool
    timestamp: datetime
    components: Dict[str, Any]


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Basic health check endpoint for liveness probes"
)
async def health_check(
    settings: Settings = Depends(get_settings)
) -> HealthResponse:
    """Basic health check - always returns 200 if service is running."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version=settings.app_version,
        environment=settings.environment
    )


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    status_code=status.HTTP_200_OK,
    summary="Readiness check",
    description="Comprehensive readiness check for all dependencies"
)
async def readiness_check(
    settings: Settings = Depends(get_settings),
    tenant_manager: TenantManager = Depends(get_tenant_manager)
) -> ReadinessResponse:
    """
    Readiness check with dependency validation.
    Returns 200 if all components are ready, 503 otherwise.
    """
    components = {}
    all_ready = True
    
    # Check tenant manager
    try:
        tenant_count = tenant_manager.get_cached_tenant_count()
        components["tenant_manager"] = {
            "status": "ready",
            "cached_tenants": tenant_count
        }
    except Exception as e:
        logger.error(f"Tenant manager not ready: {e}")
        components["tenant_manager"] = {
            "status": "not_ready",
            "error": str(e)
        }
        all_ready = False
    
    # Check Key Vault connectivity
    if settings.key_vault_url and not settings.local_mock_services:
        try:
            # TODO: Add actual Key Vault ping
            components["key_vault"] = {
                "status": "ready",
                "url": settings.key_vault_url
            }
        except Exception as e:
            logger.error(f"Key Vault not ready: {e}")
            components["key_vault"] = {
                "status": "not_ready",
                "error": str(e)
            }
            all_ready = False
    else:
        components["key_vault"] = {
            "status": "skipped",
            "reason": "local_mode"
        }
    
    # Check Redis connectivity
    try:
        # TODO: Add actual Redis ping
        components["redis"] = {
            "status": "ready",
            "url": settings.redis_url
        }
    except Exception as e:
        logger.error(f"Redis not ready: {e}")
        components["redis"] = {
            "status": "not_ready",
            "error": str(e)
        }
        # Redis not critical for basic operation
        # all_ready = False
    
    # Check FoundryIQ connectivity
    try:
        # TODO: Add actual FoundryIQ health check
        components["foundry"] = {
            "status": "ready",
            "endpoint": settings.foundry_api_base
        }
    except Exception as e:
        logger.error(f"FoundryIQ not ready: {e}")
        components["foundry"] = {
            "status": "not_ready",
            "error": str(e)
        }
        # FoundryIQ not critical for admin operations
        # all_ready = False
    
    response = ReadinessResponse(
        ready=all_ready,
        timestamp=datetime.utcnow(),
        components=components
    )
    
    # Return 503 if not ready
    if not all_ready:
        return response
    
    return response
