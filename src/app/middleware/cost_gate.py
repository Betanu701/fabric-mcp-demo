"""
Cost gate middleware for budget enforcement.
Checks tenant budget status and enforces policies.
"""
import logging
from typing import Callable, Optional

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ..services.budget_enforcer import BudgetEnforcer

logger = logging.getLogger(__name__)


class CostGateMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce budget policies."""
    
    def __init__(self, app):
        """Initialize cost gate middleware."""
        super().__init__(app)
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
        
        # Get budget enforcer from app state
        budget_enforcer: Optional[BudgetEnforcer] = None
        if hasattr(request.app.state, "budget_enforcer"):
            budget_enforcer = request.app.state.budget_enforcer
        
        if budget_enforcer:
            try:
                # Check budget
                allowed, reason, alert = await budget_enforcer.check_budget(tenant_config)
                
                if not allowed:
                    logger.warning(f"Request blocked for tenant {tenant_id}: {reason}")
                    
                    # Send notification if alert exists
                    if alert and hasattr(request.app.state, "notification_service"):
                        notification_service = request.app.state.notification_service
                        # Send budget alert (async, don't wait)
                        # TODO: Get admin email from tenant config
                        pass
                    
                    return JSONResponse(
                        status_code=status.HTTP_402_PAYMENT_REQUIRED,
                        content={
                            "error": "budget_exceeded",
                            "message": "Tenant has exceeded budget limit",
                            "reason": reason,
                            "tenant_id": tenant_id,
                            "enforcement": tenant_config.budget_enforcement.value,
                            "current_cost": float(alert.current_cost) if alert else None,
                            "budget_limit": float(alert.budget_limit) if alert else None
                        }
                    )
                
                # If there's a warning, add it to response headers
                if reason:
                    response = await call_next(request)
                    response.headers["X-Budget-Warning"] = reason
                    return response
                    
            except Exception as e:
                logger.error(f"Budget check failed for {tenant_id}: {e}")
                # Fail open - allow request if check fails
        
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
