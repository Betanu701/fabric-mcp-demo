"""
Pydantic models for agents and data sources.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    """Agent status options."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"


class SourceType(str, Enum):
    """Data source type options."""
    FABRIC_DATA_AGENT = "fabric-data-agent"
    SHAREPOINT = "sharepoint"
    ONELAKE = "onelake"
    WEB = "web"
    CUSTOM = "custom"


class DataSource(BaseModel):
    """Data source configuration."""
    id: str = Field(..., description="Unique source identifier")
    name: str = Field(..., description="Source display name")
    type: SourceType = Field(..., description="Source type")
    description: str = Field(..., description="Source description for routing")
    enabled: bool = Field(default=True, description="Whether source is active")
    
    # Source-specific configuration
    endpoint: Optional[str] = Field(default=None, description="Source API endpoint")
    connection_string: Optional[str] = Field(default=None, description="Connection string")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    # Discovery info
    discovered_at: Optional[datetime] = Field(default=None, description="Auto-discovery time")
    last_tested: Optional[datetime] = Field(default=None, description="Last health check")
    
    class Config:
        use_enum_values = True


class Agent(BaseModel):
    """FoundryIQ agent configuration."""
    id: str = Field(..., description="Unique agent identifier")
    name: str = Field(..., description="Agent display name")
    description: str = Field(..., description="Agent capabilities description")
    status: AgentStatus = Field(default=AgentStatus.ACTIVE, description="Agent status")
    
    # FoundryIQ configuration
    foundry_agent_id: str = Field(..., description="FoundryIQ agent ID")
    model_endpoint: Optional[str] = Field(default=None, description="Model API endpoint")
    
    # Associated data sources
    knowledge_sources: List[str] = Field(
        default_factory=list,
        description="Connected DataAgent source IDs"
    )
    
    # Routing hints
    keywords: List[str] = Field(
        default_factory=list,
        description="Keywords for agent selection"
    )
    priority: int = Field(default=0, description="Routing priority (higher = preferred)")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True


class AgentListResponse(BaseModel):
    """Response for listing agents."""
    agents: List[Agent]
    total: int
    tenant_id: Optional[str] = None


class SourceListResponse(BaseModel):
    """Response for listing data sources."""
    sources: List[DataSource]
    total: int
    tenant_id: Optional[str] = None


class DiscoveryResult(BaseModel):
    """Result of auto-discovery scan."""
    sources_found: int
    sources_added: int
    sources_updated: int
    sources: List[DataSource]
    scan_time: datetime = Field(default_factory=datetime.utcnow)
    errors: List[str] = Field(default_factory=list)
