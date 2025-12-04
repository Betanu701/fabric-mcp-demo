"""
Telemetry middleware for distributed tracing and metrics.
Uses OpenTelemetry for Application Insights integration.
"""
import logging
import time
from typing import Callable, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

try:
    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode
    TELEMETRY_AVAILABLE = True
except ImportError:
    TELEMETRY_AVAILABLE = False

logger = logging.getLogger(__name__)


class TelemetryMiddleware(BaseHTTPMiddleware):
    """Middleware for distributed tracing and request metrics."""
    
    def __init__(self, app, tracer_provider=None):
        """Initialize telemetry middleware."""
        super().__init__(app)
        if TELEMETRY_AVAILABLE:
            self.tracer = trace.get_tracer(__name__, tracer_provider=tracer_provider)
        else:
            self.tracer = None
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with tracing."""
        if not TELEMETRY_AVAILABLE or self.tracer is None:
            # Tracing disabled, just call next
            return await call_next(request)
        
        # Start span for this request
        with self.tracer.start_as_current_span(
            f"{request.method} {request.url.path}",
            kind=trace.SpanKind.SERVER
        ) as span:
            # Record request attributes
            span.set_attribute("http.method", request.method)
            span.set_attribute("http.url", str(request.url))
            span.set_attribute("http.scheme", request.url.scheme)
            span.set_attribute("http.host", request.url.hostname or "")
            span.set_attribute("http.target", request.url.path)
            
            # Add tenant context if available
            if hasattr(request.state, "tenant_id") and request.state.tenant_id:
                span.set_attribute("tenant.id", request.state.tenant_id)
            
            # Add client IP
            client_ip = request.client.host if request.client else "unknown"
            span.set_attribute("http.client_ip", client_ip)
            
            # Record start time
            start_time = time.time()
            
            try:
                # Process request
                response = await call_next(request)
                
                # Record response attributes
                span.set_attribute("http.status_code", response.status_code)
                
                # Set span status based on response
                if response.status_code >= 500:
                    span.set_status(Status(StatusCode.ERROR))
                elif response.status_code >= 400:
                    span.set_status(Status(StatusCode.ERROR))
                else:
                    span.set_status(Status(StatusCode.OK))
                
                # Calculate duration
                duration_ms = (time.time() - start_time) * 1000
                span.set_attribute("http.duration_ms", duration_ms)
                
                # Add custom response headers for tracing
                trace_id = span.get_span_context().trace_id
                if trace_id:
                    response.headers["X-Trace-ID"] = format(trace_id, "032x")
                
                return response
                
            except Exception as e:
                # Record exception
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                logger.error(f"Request failed: {e}", exc_info=True)
                raise
