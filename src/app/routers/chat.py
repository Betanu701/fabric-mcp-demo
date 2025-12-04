"""
Chat router for conversations with agents.
"""
import logging
import time
import uuid
from typing import Optional
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status, Request

from ..dependencies import get_tenant_config, get_tenant_id, get_settings
from ..models.chat import ChatRequest, ChatResponse
from ..models.tenant import TenantConfig
from ..config import Settings
from ..services.foundry_client import FoundryIQClient
from ..services.rate_limiter import RateLimiter
from ..services.cost_tracker import CostTracker

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])

# Initialize services (will be set in lifespan)
foundry_client: Optional[FoundryIQClient] = None
rate_limiter: Optional[RateLimiter] = None
cost_tracker: Optional[CostTracker] = None


def get_foundry_client(request: Request) -> FoundryIQClient:
    """Get FoundryIQ client from app state."""
    if hasattr(request.app.state, "foundry_client"):
        return request.app.state.foundry_client
    raise HTTPException(status_code=500, detail="FoundryIQ client not initialized")


def get_rate_limiter(request: Request) -> RateLimiter:
    """Get rate limiter from app state."""
    if hasattr(request.app.state, "rate_limiter"):
        return request.app.state.rate_limiter
    raise HTTPException(status_code=500, detail="Rate limiter not initialized")


def get_cost_tracker(request: Request) -> CostTracker:
    """Get cost tracker from app state."""
    if hasattr(request.app.state, "cost_tracker"):
        return request.app.state.cost_tracker
    raise HTTPException(status_code=500, detail="Cost tracker not initialized")


@router.post(
    "",
    response_model=ChatResponse,
    summary="Send chat message",
    description="Send a message to an agent and receive a response"
)
async def send_chat_message(
    request: ChatRequest,
    tenant_id: str = Depends(get_tenant_id),
    tenant_config: TenantConfig = Depends(get_tenant_config),
    foundry: FoundryIQClient = Depends(get_foundry_client),
    limiter: RateLimiter = Depends(get_rate_limiter),
    tracker: CostTracker = Depends(get_cost_tracker)
) -> ChatResponse:
    """
    Send a chat message to an agent.
    Routes to specific agent or uses intelligent routing if no agent specified.
    """
    start_time = time.time()
    
    # Check rate limits
    allowed, reason = await limiter.check_rate_limit(
        tenant_id=tenant_id,
        rpm_limit=tenant_config.rate_limit_rpm,
        rpd_limit=tenant_config.rate_limit_rpd,
        monthly_limit=tenant_config.quota_monthly_requests if hasattr(tenant_config, 'quota_monthly_requests') else None
    )
    
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=reason
        )
    
    # Record the request
    await limiter.record_request(
        tenant_id=tenant_id,
        rpm_limit=tenant_config.rate_limit_rpm,
        rpd_limit=tenant_config.rate_limit_rpd,
        monthly_limit=tenant_config.quota_monthly_requests if hasattr(tenant_config, 'quota_monthly_requests') else None
    )
    
    # Generate conversation ID if not provided
    conversation_id = request.conversation_id or str(uuid.uuid4())
    
    # Select agent - route intelligently if not specified
    if request.agent_id:
        agent_id = request.agent_id
        # Map to FoundryIQ agent ID
        foundry_agent_id = f"foundry-{agent_id}"
    else:
        # Use intelligent routing
        available_agents = ["foundry-sales-001", "foundry-inventory-001", "foundry-general-001"]
        foundry_agent_id = await foundry.route_query(
            endpoint=tenant_config.foundry_endpoint,
            message=request.message,
            available_agents=available_agents,
            context=request.context
        )
        agent_id = foundry_agent_id.replace("foundry-", "")
    
    # Send query to FoundryIQ
    try:
        foundry_response = await foundry.send_query(
            endpoint=tenant_config.foundry_endpoint,
            agent_id=foundry_agent_id,
            message=request.message,
            conversation_id=conversation_id,
            context=request.context
        )
        
        # Calculate cost (estimate based on tokens)
        tokens = foundry_response.get("tokens_used", 0)
        estimated_cost = Decimal(str(tokens)) * Decimal("0.00002")  # $0.00002 per token
        
        # Track cost
        await tracker.track_request_cost(
            tenant_id=tenant_id,
            service="FoundryIQ",
            cost=estimated_cost
        )
        
        # Calculate latency
        latency_ms = int((time.time() - start_time) * 1000)
        
        response = ChatResponse(
            message=foundry_response.get("message", ""),
            agent_id=agent_id,
            conversation_id=foundry_response.get("conversation_id", conversation_id),
            sources_used=foundry_response.get("sources_used", []),
            tokens_used=tokens,
            latency_ms=latency_ms,
            metadata={
                "tenant_id": tenant_id,
                "model": foundry_response.get("model", "unknown"),
                "context": request.context,
                "confidence": foundry_response.get("confidence", 1.0),
                "foundry_agent_id": foundry_agent_id
            }
        )
        
        logger.info(
            f"Chat message processed: tenant={tenant_id}, agent={agent_id}, "
            f"latency={latency_ms}ms, tokens={tokens}, cost=${estimated_cost:.4f}"
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to process chat message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process message: {str(e)}"
        )


@router.get(
    "/history",
    summary="Get conversation history",
    description="Retrieve conversation history for the tenant"
)
async def get_conversation_history(
    conversation_id: Optional[str] = None,
    limit: int = 50,
    tenant_id: str = Depends(get_tenant_id),
    tenant_config: TenantConfig = Depends(get_tenant_config)
):
    """
    Get conversation history.
    If conversation_id provided, returns that conversation.
    Otherwise returns recent conversations for the tenant.
    """
    # TODO: Implement conversation history storage and retrieval
    # For now, return empty result
    
    return {
        "conversations": [],
        "total": 0,
        "tenant_id": tenant_id,
        "message": "Conversation history not yet implemented"
    }
