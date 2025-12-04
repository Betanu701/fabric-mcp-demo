"""
Budget management router for setting and monitoring budgets.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Body
from pydantic import BaseModel, Field

from ..dependencies import get_tenant_config, get_tenant_id
from ..models.tenant import TenantConfig, BudgetEnforcement
from ..services.budget_enforcer import BudgetEnforcer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/budgets", tags=["budgets"])


class BudgetUpdateRequest(BaseModel):
    """Request to update budget settings."""
    budget_limit: Optional[float] = Field(None, description="Budget limit in USD")
    threshold: Optional[int] = Field(None, ge=0, le=100, description="Alert threshold percentage")
    enforcement: Optional[BudgetEnforcement] = Field(None, description="Enforcement policy")


def get_budget_enforcer(request: Request) -> BudgetEnforcer:
    """Get budget enforcer from app state."""
    if hasattr(request.app.state, "budget_enforcer"):
        return request.app.state.budget_enforcer
    raise HTTPException(status_code=500, detail="Budget enforcer not initialized")


@router.get(
    "",
    summary="Get budget status",
    description="Get current budget status and usage"
)
async def get_budget_status(
    tenant_id: str = Depends(get_tenant_id),
    tenant_config: TenantConfig = Depends(get_tenant_config),
    enforcer: BudgetEnforcer = Depends(get_budget_enforcer)
):
    """Get detailed budget status for the tenant."""
    try:
        status = await enforcer.get_budget_status(tenant_config)
        return status
    except Exception as e:
        logger.error(f"Failed to get budget status for {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "",
    summary="Update budget settings",
    description="Update budget limit, threshold, or enforcement policy"
)
async def update_budget(
    request: BudgetUpdateRequest,
    tenant_id: str = Depends(get_tenant_id),
    tenant_config: TenantConfig = Depends(get_tenant_config),
    enforcer: BudgetEnforcer = Depends(get_budget_enforcer)
):
    """Update budget settings for the tenant."""
    try:
        budget = await enforcer.update_budget(
            tenant_id=tenant_id,
            budget_limit=request.budget_limit,
            threshold=request.threshold,
            enforcement=request.enforcement
        )
        
        return {
            "tenant_id": budget.tenant_id,
            "limit": float(budget.limit) if budget.limit else None,
            "threshold": budget.threshold,
            "enforcement": budget.enforcement.value,
            "updated": True
        }
    except Exception as e:
        logger.error(f"Failed to update budget for {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/check",
    summary="Check budget status",
    description="Check if tenant is within budget limits"
)
async def check_budget(
    tenant_id: str = Depends(get_tenant_id),
    tenant_config: TenantConfig = Depends(get_tenant_config),
    enforcer: BudgetEnforcer = Depends(get_budget_enforcer)
):
    """Check current budget status and enforcement."""
    try:
        allowed, reason, alert = await enforcer.check_budget(tenant_config)
        
        return {
            "tenant_id": tenant_id,
            "allowed": allowed,
            "reason": reason,
            "alert": {
                "budget_limit": float(alert.budget_limit),
                "current_cost": float(alert.current_cost),
                "threshold": alert.threshold,
                "usage_percent": alert.usage_percent,
                "timestamp": alert.timestamp.isoformat()
            } if alert else None
        }
    except Exception as e:
        logger.error(f"Failed to check budget for {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/recommendations",
    summary="Get cost optimization recommendations",
    description="Get recommendations for reducing costs"
)
async def get_budget_recommendations(
    tenant_id: str = Depends(get_tenant_id),
    tenant_config: TenantConfig = Depends(get_tenant_config)
):
    """Get cost optimization recommendations."""
    # Mock recommendations for now
    recommendations = [
        {
            "type": "reduce_rpm",
            "description": "Consider reducing rate limits during off-peak hours",
            "estimated_savings": 50.0,
            "priority": "medium"
        },
        {
            "type": "optimize_agents",
            "description": "Some agents have low usage, consider consolidating",
            "estimated_savings": 30.0,
            "priority": "low"
        }
    ]
    
    return {
        "tenant_id": tenant_id,
        "recommendations": recommendations,
        "total_potential_savings": sum(r["estimated_savings"] for r in recommendations)
    }
