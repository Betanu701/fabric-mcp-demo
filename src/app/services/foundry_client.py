"""
FoundryIQ client for multi-agent orchestration.
Integrates with Microsoft Foundry to route queries to specialized agents.
"""
import logging
from typing import Optional, List, Dict, Any
import httpx
from datetime import datetime

from ..config import Settings

logger = logging.getLogger(__name__)


class FoundryIQClient:
    """Client for Microsoft FoundryIQ multi-agent orchestration."""
    
    def __init__(self, settings: Settings):
        """Initialize FoundryIQ client."""
        self.settings = settings
        self.http_client: Optional[httpx.AsyncClient] = None
        self._mock_mode = settings.local_mock_services
    
    async def initialize(self) -> None:
        """Initialize HTTP client."""
        if self._mock_mode:
            logger.warning("FoundryIQ client running in mock mode")
            return
        
        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(60.0),
            headers={
                "Content-Type": "application/json",
                "User-Agent": f"{self.settings.app_name}/{self.settings.app_version}"
            }
        )
        logger.info("FoundryIQ client initialized")
    
    async def send_query(
        self,
        endpoint: str,
        agent_id: str,
        message: str,
        conversation_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send a query to a FoundryIQ agent.
        
        Args:
            endpoint: FoundryIQ endpoint URL
            agent_id: Agent identifier in FoundryIQ
            message: User message
            conversation_id: Optional conversation ID for context
            context: Optional additional context
        
        Returns:
            Response dictionary with message, sources, and metadata
        """
        if self._mock_mode or not self.http_client:
            return self._get_mock_response(agent_id, message, conversation_id)
        
        try:
            # Construct FoundryIQ API request
            request_payload = {
                "agent_id": agent_id,
                "message": message,
                "conversation_id": conversation_id,
                "context": context or {},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Send request to FoundryIQ
            response = await self.http_client.post(
                f"{endpoint}/v1/agents/query",
                json=request_payload
            )
            response.raise_for_status()
            
            data = response.json()
            
            logger.info(f"FoundryIQ query successful - Agent: {agent_id}, ConvID: {conversation_id}")
            
            return {
                "message": data.get("response", ""),
                "agent_id": agent_id,
                "conversation_id": data.get("conversation_id", conversation_id),
                "sources_used": data.get("sources", []),
                "tokens_used": data.get("usage", {}).get("total_tokens", 0),
                "latency_ms": data.get("latency_ms", 0),
                "model": data.get("model", "unknown"),
                "confidence": data.get("confidence", 1.0),
                "metadata": data.get("metadata", {})
            }
            
        except httpx.HTTPError as e:
            logger.error(f"FoundryIQ request failed: {e}")
            return self._get_error_response(agent_id, str(e))
        except Exception as e:
            logger.error(f"Unexpected error in FoundryIQ query: {e}")
            return self._get_error_response(agent_id, str(e))
    
    async def discover_agents(self, endpoint: str) -> List[Dict[str, Any]]:
        """
        Discover available agents from FoundryIQ.
        
        Args:
            endpoint: FoundryIQ endpoint URL
        
        Returns:
            List of agent definitions
        """
        if self._mock_mode or not self.http_client:
            return self._get_mock_agents()
        
        try:
            response = await self.http_client.get(f"{endpoint}/v1/agents")
            response.raise_for_status()
            
            data = response.json()
            agents = data.get("agents", [])
            
            logger.info(f"Discovered {len(agents)} agents from FoundryIQ")
            return agents
            
        except Exception as e:
            logger.error(f"Failed to discover agents: {e}")
            return []
    
    async def get_agent_capabilities(
        self,
        endpoint: str,
        agent_id: str
    ) -> Dict[str, Any]:
        """
        Get detailed capabilities for a specific agent.
        
        Args:
            endpoint: FoundryIQ endpoint URL
            agent_id: Agent identifier
        
        Returns:
            Agent capabilities dictionary
        """
        if self._mock_mode or not self.http_client:
            return {
                "agent_id": agent_id,
                "capabilities": ["query", "summarize", "analyze"],
                "data_sources": ["fabric", "sharepoint", "onelake"],
                "max_context_length": 4096,
                "supported_languages": ["en"]
            }
        
        try:
            response = await self.http_client.get(
                f"{endpoint}/v1/agents/{agent_id}/capabilities"
            )
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Failed to get agent capabilities: {e}")
            return {}
    
    async def route_query(
        self,
        endpoint: str,
        message: str,
        available_agents: List[str],
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Use FoundryIQ routing to select the best agent for a query.
        
        Args:
            endpoint: FoundryIQ endpoint URL
            message: User message
            available_agents: List of available agent IDs
            context: Optional routing context
        
        Returns:
            Selected agent ID
        """
        if self._mock_mode or not self.http_client:
            # Simple keyword-based routing for mock mode
            message_lower = message.lower()
            if any(word in message_lower for word in ["sale", "revenue", "customer", "order"]):
                return "foundry-sales-001"
            elif any(word in message_lower for word in ["inventory", "stock", "warehouse"]):
                return "foundry-inventory-001"
            else:
                return "foundry-general-001"
        
        try:
            request_payload = {
                "message": message,
                "available_agents": available_agents,
                "context": context or {}
            }
            
            response = await self.http_client.post(
                f"{endpoint}/v1/routing/select",
                json=request_payload
            )
            response.raise_for_status()
            
            data = response.json()
            selected_agent = data.get("selected_agent", available_agents[0] if available_agents else None)
            
            logger.info(f"FoundryIQ routed query to agent: {selected_agent}")
            return selected_agent
            
        except Exception as e:
            logger.error(f"Failed to route query: {e}")
            # Fallback to first available agent
            return available_agents[0] if available_agents else "foundry-general-001"
    
    def _get_mock_response(
        self,
        agent_id: str,
        message: str,
        conversation_id: Optional[str]
    ) -> Dict[str, Any]:
        """Generate mock response for testing."""
        agent_name_map = {
            "foundry-sales-001": "Sales Agent",
            "foundry-inventory-001": "Inventory Agent",
            "foundry-general-001": "General Knowledge Agent"
        }
        
        agent_name = agent_name_map.get(agent_id, "Unknown Agent")
        
        return {
            "message": f"[Mock FoundryIQ Response from {agent_name}] I understand you're asking: '{message}'. In production, this will connect to FoundryIQ and retrieve data from Microsoft Fabric DataAgents.",
            "agent_id": agent_id,
            "conversation_id": conversation_id or f"conv-{datetime.utcnow().timestamp()}",
            "sources_used": [f"mock-source-{agent_id}"],
            "tokens_used": len(message.split()) * 2,
            "latency_ms": 0,
            "model": "gpt-4-turbo",
            "confidence": 0.95,
            "metadata": {
                "mock": True,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    def _get_mock_agents(self) -> List[Dict[str, Any]]:
        """Get mock agent list for testing."""
        return [
            {
                "id": "foundry-sales-001",
                "name": "Sales Agent",
                "description": "Specialized in sales data and customer analytics",
                "capabilities": ["query", "summarize", "analyze"],
                "data_sources": ["fabric-sales", "dynamics-crm"]
            },
            {
                "id": "foundry-inventory-001",
                "name": "Inventory Agent",
                "description": "Manages inventory and supply chain queries",
                "capabilities": ["query", "forecast", "alert"],
                "data_sources": ["fabric-inventory", "warehouse-system"]
            },
            {
                "id": "foundry-general-001",
                "name": "General Knowledge Agent",
                "description": "Handles general queries and routing",
                "capabilities": ["query", "route", "summarize"],
                "data_sources": ["sharepoint", "onelake"]
            }
        ]
    
    def _get_error_response(self, agent_id: str, error_msg: str) -> Dict[str, Any]:
        """Generate error response."""
        return {
            "message": f"I encountered an error while processing your request: {error_msg}",
            "agent_id": agent_id,
            "conversation_id": None,
            "sources_used": [],
            "tokens_used": 0,
            "latency_ms": 0,
            "model": "error",
            "confidence": 0.0,
            "metadata": {
                "error": True,
                "error_message": error_msg
            }
        }
    
    async def close(self) -> None:
        """Close HTTP client."""
        if self.http_client:
            await self.http_client.aclose()
            logger.info("FoundryIQ client closed")
