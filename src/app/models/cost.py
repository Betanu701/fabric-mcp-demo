"""
Pydantic models for cost tracking and budget management.
"""
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from .tenant import BudgetEnforcement


class CostBreakdown(BaseModel):
    """Cost breakdown by service."""
    service_name: str
    cost: Decimal
    currency: str = "USD"
    percentage: float = 0.0


class TenantCost(BaseModel):
    """Tenant cost information."""
    tenant_id: str
    period_start: datetime
    period_end: datetime
    total_cost: Decimal
    currency: str = "USD"
    breakdowns: List["CostBreakdown"] = Field(default_factory=list)  # Changed from breakdown
    tags: Dict[str, str] = Field(default_factory=dict)


class CostBreakdown(BaseModel):
    """Cost breakdown by service with date."""
    service: str  # Changed from service_name
    cost: Decimal
    date: datetime
    currency: str = "USD"
class Budget(BaseModel):
    """Budget configuration."""
    tenant_id: str
    limit: Optional[Decimal] = None  # Changed from amount
    threshold: int = Field(default=90, ge=0, le=100, description="Alert threshold percentage")
    enforcement: BudgetEnforcement = Field(default=BudgetEnforcement.BLOCK)
    period_start: datetime
    period_end: datetime
    currency: str = "USD"
    enabled: bool = True
    
    # Current usage
    current_spend: Decimal = Field(default=Decimal("0.00"))
    percentage_used: float = 0.0
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class BudgetAlert(BaseModel):
    """Budget alert event."""
    tenant_id: str
    budget_limit: Decimal
    current_cost: Decimal
    threshold: float
    usage_percent: float
    timestamp: datetime
    alert_type: str = Field(default="threshold_exceeded")
    enforcement_action: Optional[str] = None


class CostForecast(BaseModel):
    """Cost forecast."""
    tenant_id: str
    forecast_date: datetime
    predicted_cost: Decimal
    confidence_level: float
    based_on_days: int


class CostOptimizationRecommendation(BaseModel):
    """Cost optimization recommendation."""
    tenant_id: str
    recommendation_type: str
    description: str
    estimated_savings: Decimal
    priority: str = Field(default="medium", description="low, medium, high")
    action_url: Optional[str] = None
