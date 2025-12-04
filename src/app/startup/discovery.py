"""
Auto-discovery service for DataAgents and knowledge sources.
Scans FoundryIQ, Fabric, SharePoint, OneLake for available sources.
"""
import logging
from datetime import datetime
from typing import Dict, List

from ..config import Settings
from ..models.agent import DataSource, DiscoveryResult, SourceType

logger = logging.getLogger(__name__)


class DiscoveryService:
    """Auto-discovers DataAgents and knowledge sources."""
    
    def __init__(self, settings: Settings):
        """Initialize discovery service."""
        self.settings = settings
        self._discovered_sources: List[DataSource] = []
    
    async def discover_all_sources(self) -> DiscoveryResult:
        """
        Discover all available data sources.
        Returns discovery results with found sources.
        """
        logger.info("Starting auto-discovery of data sources")
        
        sources_found = []
        errors = []
        
        try:
            # Discover Fabric Data Agents
            fabric_sources = await self._discover_fabric_data_agents()
            sources_found.extend(fabric_sources)
            logger.info(f"Discovered {len(fabric_sources)} Fabric Data Agents")
        except Exception as e:
            error_msg = f"Failed to discover Fabric Data Agents: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
        
        try:
            # Discover SharePoint sites
            sharepoint_sources = await self._discover_sharepoint_sites()
            sources_found.extend(sharepoint_sources)
            logger.info(f"Discovered {len(sharepoint_sources)} SharePoint sites")
        except Exception as e:
            error_msg = f"Failed to discover SharePoint sites: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
        
        try:
            # Discover OneLake sources
            onelake_sources = await self._discover_onelake_sources()
            sources_found.extend(onelake_sources)
            logger.info(f"Discovered {len(onelake_sources)} OneLake sources")
        except Exception as e:
            error_msg = f"Failed to discover OneLake sources: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
        
        # Store discovered sources
        self._discovered_sources = sources_found
        
        result = DiscoveryResult(
            sources_found=len(sources_found),
            sources_added=len(sources_found),  # All are new in discovery
            sources_updated=0,
            sources=sources_found,
            errors=errors
        )
        
        logger.info(
            f"Discovery complete: {result.sources_found} sources found, "
            f"{len(errors)} errors"
        )
        
        return result
    
    async def _discover_fabric_data_agents(self) -> List[DataSource]:
        """Discover Fabric Data Agents."""
        # TODO: Implement actual Fabric API discovery
        # For now, return mock data for development
        
        if self.settings.local_mock_services:
            return [
                DataSource(
                    id="fabric-data-agent-sales",
                    name="Sales Data Agent",
                    type=SourceType.FABRIC_DATA_AGENT,
                    description="Access to sales database with revenue, orders, and customer data",
                    endpoint=f"{self.settings.foundry_api_base}/agents/sales",
                    discovered_at=datetime.utcnow(),
                    enabled=True,
                    metadata={
                        "tables": ["orders", "customers", "products"],
                        "schema": "sales"
                    }
                ),
                DataSource(
                    id="fabric-data-agent-inventory",
                    name="Inventory Data Agent",
                    type=SourceType.FABRIC_DATA_AGENT,
                    description="Access to inventory database with stock levels, warehouses, and SKUs",
                    endpoint=f"{self.settings.foundry_api_base}/agents/inventory",
                    discovered_at=datetime.utcnow(),
                    enabled=True,
                    metadata={
                        "tables": ["inventory", "warehouses", "products"],
                        "schema": "inventory"
                    }
                )
            ]
        
        # Placeholder for actual implementation
        logger.warning("Fabric Data Agent discovery not yet implemented")
        return []
    
    async def _discover_sharepoint_sites(self) -> List[DataSource]:
        """Discover SharePoint sites."""
        # TODO: Implement actual SharePoint API discovery via Microsoft Graph
        
        if self.settings.local_mock_services:
            return [
                DataSource(
                    id="sharepoint-site-marketing",
                    name="Marketing SharePoint Site",
                    type=SourceType.SHAREPOINT,
                    description="Marketing documents, campaigns, and presentations",
                    endpoint="https://contoso.sharepoint.com/sites/marketing",
                    discovered_at=datetime.utcnow(),
                    enabled=True,
                    metadata={
                        "site_url": "https://contoso.sharepoint.com/sites/marketing",
                        "document_libraries": ["Documents", "Campaigns"]
                    }
                )
            ]
        
        logger.warning("SharePoint discovery not yet implemented")
        return []
    
    async def _discover_onelake_sources(self) -> List[DataSource]:
        """Discover OneLake sources."""
        # TODO: Implement actual OneLake API discovery
        
        if self.settings.local_mock_services:
            return [
                DataSource(
                    id="onelake-analytics",
                    name="Analytics OneLake",
                    type=SourceType.ONELAKE,
                    description="Analytics data lake with aggregated business metrics",
                    endpoint=f"{self.settings.foundry_api_base}/onelake/analytics",
                    discovered_at=datetime.utcnow(),
                    enabled=True,
                    metadata={
                        "workspace": "analytics",
                        "lakehouse": "business-metrics"
                    }
                )
            ]
        
        logger.warning("OneLake discovery not yet implemented")
        return []
    
    def get_discovered_sources(self) -> List[DataSource]:
        """Get list of discovered sources."""
        return self._discovered_sources.copy()
    
    async def test_source_connection(self, source: DataSource) -> bool:
        """Test connection to a data source."""
        # TODO: Implement actual connection testing
        logger.info(f"Testing connection to source: {source.id}")
        
        try:
            # Placeholder for actual connection test
            # Would make actual API call to verify source is accessible
            return True
        except Exception as e:
            logger.error(f"Connection test failed for {source.id}: {e}")
            return False


async def run_discovery(settings: Settings) -> DiscoveryResult:
    """
    Convenience function to run discovery.
    Called during application startup if feature flag is enabled.
    """
    if not settings.feature_auto_discovery:
        logger.info("Auto-discovery disabled via feature flag")
        return DiscoveryResult(
            sources_found=0,
            sources_added=0,
            sources_updated=0,
            sources=[],
            errors=[]
        )
    
    service = DiscoveryService(settings)
    return await service.discover_all_sources()
