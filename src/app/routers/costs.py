"""
Cost management router for viewing and analyzing costs.
"""
import logging
from typing import Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Query

from ..dependencies import get_tenant_config, get_tenant_id
from ..models.tenant import TenantConfig
from ..services.cost_tracker import CostTracker

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/costs", tags=["costs"])


def get_cost_tracker(request: Request) -> CostTracker:
    """Get cost tracker from app state."""
    if hasattr(request.app.state, "cost_tracker"):
        return request.app.state.cost_tracker
    raise HTTPException(status_code=500, detail="Cost tracker not initialized")


@router.get(
    "",
    summary="Get tenant costs",
    description="Retrieve cost information for the current tenant"
)
async def get_tenant_costs(
    tenant_id: str = Depends(get_tenant_id),
    tenant_config: TenantConfig = Depends(get_tenant_config),
    tracker: CostTracker = Depends(get_cost_tracker),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """Get cost summary for the tenant."""
    try:
        # Parse dates if provided
        start = datetime.fromisoformat(start_date) if start_date else None
        end = datetime.fromisoformat(end_date) if end_date else None
        
        costs = await tracker.get_tenant_costs(
            tenant_id=tenant_id,
            start_date=start,
            end_date=end
        )
        
        return {
            "tenant_id": costs.tenant_id,
            "period_start": costs.period_start.isoformat(),
            "period_end": costs.period_end.isoformat(),
            "total_cost": float(costs.total_cost),
            "currency": costs.currency,
            "breakdown": [
                {
                    "service": b.service,
                    "cost": float(b.cost),
                    "date": b.date.isoformat()
                }
                for b in costs.breakdowns
            ]
        }
    except Exception as e:
        logger.error(f"Failed to get costs for {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/forecast",
    summary="Get cost forecast",
    description="Get predicted costs for the next N days"
)
async def get_cost_forecast(
    tenant_id: str = Depends(get_tenant_id),
    tenant_config: TenantConfig = Depends(get_tenant_config),
    tracker: CostTracker = Depends(get_cost_tracker),
    days_ahead: int = Query(30, ge=1, le=90, description="Days to forecast")
):
    """Get cost forecast for the tenant."""
    try:
        forecast = await tracker.get_cost_forecast(tenant_id, days_ahead)
        
        return {
            "tenant_id": tenant_id,
            "days_ahead": days_ahead,
            "predicted_cost": float(forecast),
            "currency": "USD",
            "forecast_date": (datetime.utcnow() + timedelta(days=days_ahead)).isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get forecast for {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/summary",
    summary="Get cost summary with forecast",
    description="Get comprehensive cost information including current spend and forecast"
)
async def get_cost_summary(
    tenant_id: str = Depends(get_tenant_id),
    tenant_config: TenantConfig = Depends(get_tenant_config),
    tracker: CostTracker = Depends(get_cost_tracker)
):
    """Get comprehensive cost summary."""
    try:
        # Get current month costs
        costs = await tracker.get_tenant_costs(tenant_id)
        
        # Get forecast
        forecast_30d = await tracker.get_cost_forecast(tenant_id, 30)
        
        # Calculate daily average
        days_in_period = (costs.period_end - costs.period_start).days or 1
        daily_avg = costs.total_cost / days_in_period
        
        return {
            "tenant_id": tenant_id,
            "current_period": {
                "start": costs.period_start.isoformat(),
                "end": costs.period_end.isoformat(),
                "total_cost": float(costs.total_cost),
                "daily_average": float(daily_avg),
                "currency": costs.currency
            },
            "forecast": {
                "next_30_days": float(forecast_30d),
                "projected_month_end": float(costs.total_cost + forecast_30d)
            },
            "breakdown": [
                {
                    "service": b.service,
                    "cost": float(b.cost),
                    "percentage": float(b.cost / costs.total_cost * 100) if costs.total_cost > 0 else 0
                }
                for b in costs.breakdowns
            ]
        }
    except Exception as e:
        logger.error(f"Failed to get cost summary for {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
