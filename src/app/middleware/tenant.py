"""
Tenant context middleware for extracting and validating X-Tenant-ID header.
"""
import logging
from typing import Optional

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ..services.tenant_manager import TenantManager

logger = logging.getLogger(__name__)


class TenantContextMiddleware(BaseHTTPMiddleware):
    """Middleware to extract and validate tenant context from request headers."""
    
    TENANT_HEADER = "x-tenant-id"
    DEFAULT_TENANT = "default"
    
    def __init__(self, app, tenant_manager: TenantManager):
        """Initialize middleware."""
        super().__init__(app)
        self.tenant_manager = tenant_manager
    
    async def dispatch(self, request: Request, call_next):
        """Process request and inject tenant context."""
        # Extract tenant ID from header
        tenant_id = request.headers.get(self.TENANT_HEADER, self.DEFAULT_TENANT)
        
        # Skip validation for health/docs endpoints
        if self._is_public_endpoint(request.url.path):
            request.state.tenant_id = None
            request.state.tenant_config = None
            return await call_next(request)
        
        # Validate tenant
        is_valid = await self.tenant_manager.validate_tenant(tenant_id)
        
        if not is_valid:
            logger.warning(f"Invalid or disabled tenant: {tenant_id}")
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "error": "invalid_tenant",
                    "message": f"Tenant '{tenant_id}' is not valid or disabled",
                    "tenant_id": tenant_id
                }
            )
        
        # Load tenant configuration
        tenant_config = await self.tenant_manager.get_tenant(tenant_id)
        
        # Inject into request state
        request.state.tenant_id = tenant_id
        request.state.tenant_config = tenant_config
        
        logger.debug(f"Request from tenant: {tenant_id}")
        
        # Continue processing
        response = await call_next(request)
        
        # Add tenant ID to response headers for debugging
        response.headers["X-Tenant-ID"] = tenant_id
        
        return response
    
    def _is_public_endpoint(self, path: str) -> bool:
        """Check if endpoint is public (no tenant validation required)."""
        public_paths = [
            "/health",
            "/ready",
            "/docs",
            "/openapi.json",
            "/redoc"
        ]
        return any(path.startswith(p) for p in public_paths)
