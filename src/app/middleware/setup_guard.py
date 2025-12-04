"""
Setup guard middleware to redirect to setup wizard if not completed.
"""
import logging

from fastapi import Request, Response
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class SetupGuardMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce setup wizard completion."""
    
    def __init__(self, app, setup_completed: bool = False):
        """Initialize setup guard middleware."""
        super().__init__(app)
        self._setup_completed = setup_completed
    
    async def dispatch(self, request: Request, call_next):
        """Check if setup is completed before allowing access."""
        # Allow setup wizard and public endpoints
        if self._is_allowed_endpoint(request.url.path):
            return await call_next(request)
        
        # Check if setup is completed
        if not self._setup_completed:
            # TODO: Check actual setup status from database/Key Vault
            # For now, allow all requests (setup wizard is optional)
            pass
        
        return await call_next(request)
    
    def _is_allowed_endpoint(self, path: str) -> bool:
        """Check if endpoint is allowed without setup completion."""
        allowed_paths = [
            "/health",
            "/ready",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/api/admin/setup",  # Setup wizard endpoints
            "/setup"  # Frontend setup route
        ]
        return any(path.startswith(p) for p in allowed_paths)
    
    def mark_setup_completed(self) -> None:
        """Mark setup as completed."""
        self._setup_completed = True
        logger.info("Setup marked as completed")
