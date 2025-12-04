"""
Cost gate middleware for budget enforcement.
Checks tenant budget status and enforces policies.
"""
import logging
from typing import Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class CostGateMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce budget policies."""
    
    def __init__(self, app):
        """Initialize cost gate middleware."""
        super().__init__(app)
        # TODO: Inject budget enforcer service
        self._enforcement_enabled = True
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check budget status before processing request."""
        # Skip for public endpoints
        if self._is_public_endpoint(request.url.path):
            return await call_next(request)
        
        # Skip if no tenant context
        if not hasattr(request.state, "tenant_id") or not request.state.tenant_id:
            return await call_next(request)
        
        tenant_id = request.state.tenant_id
        tenant_config = request.state.tenant_config
        
        # Check budget status
        if not self._enforcement_enabled or not tenant_config:
            return await call_next(request)
        
        # TODO: Implement actual budget check via budget_enforcer service
        # For now, allow all requests
        is_blocked = False
        block_reason = None
        
        if is_blocked:
            logger.warning(f"Request blocked for tenant {tenant_id}: {block_reason}")
            return JSONResponse(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                content={
                    "error": "budget_exceeded",
                    "message": "Tenant has exceeded budget limit",
                    "reason": block_reason,
                    "tenant_id": tenant_id,
                    "enforcement": tenant_config.budget_enforcement.value
                }
            )
        
        # Process request
        return await call_next(request)
    
    def _is_public_endpoint(self, path: str) -> bool:
        """Check if endpoint should skip budget enforcement."""
        public_paths = [
            "/health",
            "/ready",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/api/admin/costs",  # Allow cost checking
            "/api/admin/budgets"  # Allow budget management
        ]
        return any(path.startswith(p) for p in public_paths)
