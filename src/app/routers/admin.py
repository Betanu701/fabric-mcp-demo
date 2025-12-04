"""
Data source discovery and management router.
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..config import Settings, get_settings
from ..dependencies import get_tenant_config, get_tenant_id, require_admin
from ..models.agent import DataSource, DiscoveryResult, SourceListResponse
from ..models.tenant import TenantConfig
from ..startup.discovery import DiscoveryService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/sources", tags=["admin", "sources"])


@router.get(
    "",
    response_model=SourceListResponse,
    summary="List data sources",
    description="Get list of discovered data sources"
)
async def list_sources(
    enabled_only: bool = Query(default=False, description="Show only enabled sources"),
    tenant_id: str = Depends(get_tenant_id),
    tenant_config: TenantConfig = Depends(get_tenant_config),
    settings: Settings = Depends(get_settings)
) -> SourceListResponse:
    """List all discovered data sources."""
    # TODO: Load sources from persistent storage
    # For now, run discovery
    
    discovery_service = DiscoveryService(settings)
    result = await discovery_service.discover_all_sources()
    
    sources = result.sources
    
    # Filter by enabled status
    if enabled_only:
        sources = [s for s in sources if s.enabled]
    
    # Filter by tenant's allowed sources if configured
    if tenant_config.allowed_sources:
        sources = [s for s in sources if s.id in tenant_config.allowed_sources]
    
    return SourceListResponse(
        sources=sources,
        total=len(sources),
        tenant_id=tenant_id
    )


@router.post(
    "/sync",
    response_model=DiscoveryResult,
    summary="Sync data sources",
    description="Trigger auto-discovery scan for data sources"
)
async def sync_sources(
    _: bool = Depends(require_admin),
    settings: Settings = Depends(get_settings)
) -> DiscoveryResult:
    """Trigger data source discovery scan."""
    logger.info("Starting manual source discovery sync")
    
    discovery_service = DiscoveryService(settings)
    result = await discovery_service.discover_all_sources()
    
    logger.info(f"Discovery completed: {result.sources_found} sources found")
    
    return result


@router.put(
    "/{source_id}",
    response_model=DataSource,
    summary="Update data source",
    description="Update data source configuration (e.g., description, enabled status)"
)
async def update_source(
    source_id: str,
    source: DataSource,
    _: bool = Depends(require_admin)
) -> DataSource:
    """Update data source configuration."""
    # Ensure ID matches
    if source.id != source_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Source ID in path must match ID in body"
        )
    
    # TODO: Save to persistent storage
    logger.info(f"Updated source: {source_id}")
    
    return source


@router.post(
    "/{source_id}/test",
    summary="Test source connection",
    description="Test connectivity to a data source"
)
async def test_source(
    source_id: str,
    _: bool = Depends(require_admin),
    settings: Settings = Depends(get_settings)
):
    """Test connection to a data source."""
    # TODO: Load source from storage
    # For now, create mock source for testing
    
    from ..models.agent import SourceType
    mock_source = DataSource(
        id=source_id,
        name=f"Source {source_id}",
        type=SourceType.FABRIC_DATA_AGENT,
        description="Test source",
        enabled=True
    )
    
    discovery_service = DiscoveryService(settings)
    is_connected = await discovery_service.test_source_connection(mock_source)
    
    return {
        "source_id": source_id,
        "connected": is_connected,
        "message": "Connection successful" if is_connected else "Connection failed"
    }
