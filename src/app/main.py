"""
FastAPI main application entry point.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    TELEMETRY_AVAILABLE = True
except ImportError:
    TELEMETRY_AVAILABLE = False
    import logging
    logging.warning("OpenTelemetry not available - telemetry disabled")

from .config import get_settings
from .dependencies import get_tenant_manager
from .middleware import (
    CostGateMiddleware,
    SetupGuardMiddleware,
    TelemetryMiddleware,
    TenantContextMiddleware,
)
from .routers import admin, agents, chat, health, tenant, costs, budgets, branding, notifications
from .startup.discovery import run_discovery
from .startup.init_tenants import init_tenants_from_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown."""
    # Startup
    logger.info("Starting Enterprise MCP Server")
    settings = get_settings()
    
    # Initialize tenant manager
    from .services import (
        TenantManager, RateLimiter, CostTracker, BudgetEnforcer,
        FoundryIQClient, NotificationService, BrandingService
    )
    
    tenant_manager = get_tenant_manager(settings)
    await tenant_manager.initialize()
    
    # Initialize all services
    logger.info("Initializing services")
    
    rate_limiter = RateLimiter(settings)
    await rate_limiter.initialize()
    app.state.rate_limiter = rate_limiter
    
    cost_tracker = CostTracker(settings)
    await cost_tracker.initialize()
    app.state.cost_tracker = cost_tracker
    
    budget_enforcer = BudgetEnforcer(settings, cost_tracker)
    app.state.budget_enforcer = budget_enforcer
    
    foundry_client = FoundryIQClient(settings)
    await foundry_client.initialize()
    app.state.foundry_client = foundry_client
    
    notification_service = NotificationService(settings)
    await notification_service.initialize()
    app.state.notification_service = notification_service
    
    branding_service = BrandingService(settings)
    await branding_service.initialize()
    app.state.branding_service = branding_service
    
    logger.info("All services initialized")
    
    # Initialize tenants from config
    logger.info("Initializing tenants from configuration")
    init_result = await init_tenants_from_config(settings)
    logger.info(f"Tenant initialization: {init_result.get('status')}")
    
    # Run auto-discovery if enabled
    if settings.feature_auto_discovery:
        logger.info("Running data source auto-discovery")
        discovery_result = await run_discovery(settings)
        logger.info(f"Discovery found {discovery_result.sources_found} sources")
    
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Enterprise MCP Server")
    
    # Close all services
    await rate_limiter.close()
    await foundry_client.close()
    logger.info("All services closed")


# Create FastAPI application
settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Enterprise Multi-Tenant MCP Server with FoundryIQ Integration",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
tenant_manager = get_tenant_manager(settings)
app.add_middleware(TenantContextMiddleware, tenant_manager=tenant_manager)
app.add_middleware(TelemetryMiddleware)
app.add_middleware(CostGateMiddleware)
app.add_middleware(SetupGuardMiddleware, setup_completed=False)

# Instrument with OpenTelemetry
if settings.application_insights_enabled and TELEMETRY_AVAILABLE:
    FastAPIInstrumentor.instrument_app(app)
elif settings.application_insights_enabled and not TELEMETRY_AVAILABLE:
    logger.warning("OpenTelemetry instrumentation requested but not available")

# Include routers
app.include_router(health.router)
app.include_router(chat.router)
app.include_router(agents.router)
app.include_router(tenant.router)
app.include_router(admin.router)
app.include_router(costs.router)
app.include_router(budgets.router)
app.include_router(branding.router)
app.include_router(notifications.router)

# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        log_level=settings.log_level.lower()
    )
