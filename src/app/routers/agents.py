"""
Agent management router.
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..dependencies import get_tenant_config, get_tenant_id
from ..models.agent import Agent, AgentListResponse, AgentStatus
from ..models.tenant import TenantConfig

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agents", tags=["agents"])


@router.get(
    "",
    response_model=AgentListResponse,
    summary="List available agents",
    description="Get list of agents available for the tenant"
)
async def list_agents(
    enabled_only: bool = Query(default=True, description="Show only enabled agents"),
    tenant_id: str = Depends(get_tenant_id),
    tenant_config: TenantConfig = Depends(get_tenant_config)
) -> AgentListResponse:
    """
    List all available agents for the tenant.
    Filtered by tenant's allowed sources if configured.
    """
    # TODO: Integrate with FoundryIQ to get actual agents
    # For now, return mock data
    
    mock_agents = [
        Agent(
            id="sales-agent",
            name="Sales Agent",
            description="Answers questions about sales data, revenue, and customer information",
            status=AgentStatus.ACTIVE,
            foundry_agent_id="foundry-sales-001",
            knowledge_sources=["fabric-data-agent-sales"],
            keywords=["sales", "revenue", "customers", "orders"],
            priority=10
        ),
        Agent(
            id="inventory-agent",
            name="Inventory Agent",
            description="Provides information about inventory levels, stock, and warehouse data",
            status=AgentStatus.ACTIVE,
            foundry_agent_id="foundry-inventory-001",
            knowledge_sources=["fabric-data-agent-inventory"],
            keywords=["inventory", "stock", "warehouse", "products"],
            priority=10
        ),
        Agent(
            id="general-agent",
            name="General Knowledge Agent",
            description="Handles general queries and routes to specialized agents",
            status=AgentStatus.ACTIVE,
            foundry_agent_id="foundry-general-001",
            knowledge_sources=["sharepoint-site-marketing", "onelake-analytics"],
            keywords=["general", "help", "information"],
            priority=1
        )
    ]
    
    # Filter by enabled status
    if enabled_only:
        mock_agents = [a for a in mock_agents if a.status == AgentStatus.ACTIVE]
    
    # Filter by tenant's allowed sources if configured
    if tenant_config.allowed_sources:
        mock_agents = [
            a for a in mock_agents
            if any(src in tenant_config.allowed_sources for src in a.knowledge_sources)
        ]
    
    return AgentListResponse(
        agents=mock_agents,
        total=len(mock_agents),
        tenant_id=tenant_id
    )


@router.get(
    "/{agent_id}",
    response_model=Agent,
    summary="Get agent details",
    description="Get detailed information about a specific agent"
)
async def get_agent(
    agent_id: str,
    tenant_id: str = Depends(get_tenant_id),
    tenant_config: TenantConfig = Depends(get_tenant_config)
) -> Agent:
    """Get details for a specific agent."""
    # TODO: Integrate with FoundryIQ to get actual agent
    
    # Mock implementation
    agents_response = await list_agents(
        enabled_only=False,
        tenant_id=tenant_id,
        tenant_config=tenant_config
    )
    
    for agent in agents_response.agents:
        if agent.id == agent_id:
            return agent
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Agent '{agent_id}' not found"
    )
