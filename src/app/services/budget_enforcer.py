"""
Budget enforcement service.
Checks budget thresholds and enforces policies (warn, throttle, block).
"""
import logging
from typing import Optional, Tuple
from decimal import Decimal
from datetime import datetime

from ..config import Settings
from ..models.tenant import TenantConfig, BudgetEnforcement
from ..models.cost import Budget, BudgetAlert
from .cost_tracker import CostTracker

logger = logging.getLogger(__name__)


class BudgetEnforcer:
    """Enforces budget policies for tenants."""
    
    def __init__(self, settings: Settings, cost_tracker: CostTracker):
        """Initialize budget enforcer."""
        self.settings = settings
        self.cost_tracker = cost_tracker
    
    async def check_budget(
        self,
        tenant_config: TenantConfig
    ) -> Tuple[bool, Optional[str], Optional[BudgetAlert]]:
        """
        Check if tenant is within budget.
        
        Args:
            tenant_config: Tenant configuration with budget settings
        
        Returns:
            Tuple of (allowed: bool, reason: Optional[str], alert: Optional[BudgetAlert])
        """
        # If no budget limit set, always allow
        if not tenant_config.budget_limit:
            return True, None, None
        
        try:
            # Get current costs for the month
            costs = await self.cost_tracker.get_tenant_costs(tenant_config.id)
            
            budget_limit = Decimal(str(tenant_config.budget_limit))
            current_cost = costs.total_cost
            threshold = tenant_config.budget_threshold  # e.g., 90%
            
            # Calculate usage percentage
            usage_percent = (current_cost / budget_limit * 100) if budget_limit > 0 else 0
            
            # Check if threshold exceeded
            if usage_percent < threshold:
                # Within budget
                return True, None, None
            
            # Threshold exceeded - create alert
            alert = BudgetAlert(
                tenant_id=tenant_config.id,
                budget_limit=budget_limit,
                current_cost=current_cost,
                threshold=threshold,
                usage_percent=usage_percent,
                timestamp=datetime.utcnow()
            )
            
            # Apply enforcement policy
            enforcement = tenant_config.budget_enforcement
            
            if enforcement == BudgetEnforcement.BLOCK:
                # Block all requests
                return False, f"Budget exceeded: ${current_cost:.2f} / ${budget_limit:.2f} ({usage_percent:.1f}%)", alert
            
            elif enforcement == BudgetEnforcement.THROTTLE:
                # Allow with warning, throttle will be applied by rate limiter
                logger.warning(f"Budget threshold reached for {tenant_config.id}: {usage_percent:.1f}%")
                return True, f"Budget warning: {usage_percent:.1f}% used", alert
            
            elif enforcement == BudgetEnforcement.WARN:
                # Just warn, don't block
                logger.warning(f"Budget threshold reached for {tenant_config.id}: {usage_percent:.1f}%")
                return True, f"Budget warning: {usage_percent:.1f}% used", alert
            
            else:
                # Unknown enforcement, default to warn
                return True, None, alert
                
        except Exception as e:
            logger.error(f"Budget check failed for {tenant_config.id}: {e}")
            # Fail open - allow request if budget check has issues
            return True, None, None
    
    async def get_budget_status(self, tenant_config: TenantConfig) -> dict:
        """
        Get detailed budget status for a tenant.
        
        Args:
            tenant_config: Tenant configuration
        
        Returns:
            Dictionary with budget status details
        """
        if not tenant_config.budget_limit:
            return {
                "tenant_id": tenant_config.id,
                "budget_enabled": False,
                "message": "No budget limit set"
            }
        
        try:
            costs = await self.cost_tracker.get_tenant_costs(tenant_config.id)
            budget_limit = Decimal(str(tenant_config.budget_limit))
            current_cost = costs.total_cost
            remaining = budget_limit - current_cost
            usage_percent = (current_cost / budget_limit * 100) if budget_limit > 0 else 0
            
            # Get forecast
            forecast = await self.cost_tracker.get_cost_forecast(tenant_config.id, days_ahead=30)
            projected_total = current_cost + forecast
            projected_percent = (projected_total / budget_limit * 100) if budget_limit > 0 else 0
            
            status = "OK"
            if usage_percent >= tenant_config.budget_threshold:
                status = "THRESHOLD_EXCEEDED"
            if usage_percent >= 100:
                status = "OVER_BUDGET"
            
            return {
                "tenant_id": tenant_config.id,
                "budget_enabled": True,
                "budget_limit": float(budget_limit),
                "current_cost": float(current_cost),
                "remaining": float(remaining),
                "usage_percent": float(usage_percent),
                "threshold": tenant_config.budget_threshold,
                "enforcement": tenant_config.budget_enforcement.value,
                "status": status,
                "forecast_30_days": float(forecast),
                "projected_total": float(projected_total),
                "projected_percent": float(projected_percent),
                "period_start": costs.period_start.isoformat(),
                "period_end": costs.period_end.isoformat(),
                "currency": costs.currency
            }
            
        except Exception as e:
            logger.error(f"Failed to get budget status for {tenant_config.id}: {e}")
            return {
                "tenant_id": tenant_config.id,
                "budget_enabled": True,
                "error": str(e)
            }
    
    async def update_budget(
        self,
        tenant_id: str,
        budget_limit: Optional[float],
        threshold: Optional[int],
        enforcement: Optional[BudgetEnforcement]
    ) -> Budget:
        """
        Update budget settings for a tenant.
        
        Args:
            tenant_id: Tenant identifier
            budget_limit: New budget limit in USD
            threshold: New threshold percentage (0-100)
            enforcement: New enforcement policy
        
        Returns:
            Updated Budget object
        """
        # This would update the tenant configuration
        # For now, return a Budget object
        budget = Budget(
            tenant_id=tenant_id,
            limit=Decimal(str(budget_limit)) if budget_limit else None,
            threshold=threshold or 90,
            enforcement=enforcement or BudgetEnforcement.BLOCK,
            period_start=datetime.utcnow().replace(day=1),
            period_end=datetime.utcnow()
        )
        
        logger.info(f"Budget updated for {tenant_id}: ${budget_limit}, threshold={threshold}%, enforcement={enforcement}")
        return budget
    
    def should_throttle(self, usage_percent: float, threshold: float) -> bool:
        """
        Determine if requests should be throttled based on usage.
        
        Args:
            usage_percent: Current budget usage percentage
            threshold: Threshold percentage
        
        Returns:
            True if throttling should be applied
        """
        # Apply progressive throttling
        if usage_percent < threshold:
            return False
        
        # Throttle more aggressively as usage approaches 100%
        # 90-95%: slow down slightly
        # 95-100%: significant throttling
        # >100%: maximum throttling
        
        if usage_percent >= 100:
            return True
        elif usage_percent >= 95:
            return True
        elif usage_percent >= threshold:
            return True
        
        return False
    
    def get_throttle_factor(self, usage_percent: float, threshold: float) -> float:
        """
        Calculate throttle factor (multiplier for rate limits).
        
        Args:
            usage_percent: Current budget usage percentage
            threshold: Threshold percentage
        
        Returns:
            Throttle factor (0.0 to 1.0, where 1.0 is normal, 0.5 is half speed)
        """
        if usage_percent < threshold:
            return 1.0  # No throttling
        
        if usage_percent >= 100:
            return 0.1  # 90% reduction
        elif usage_percent >= 95:
            return 0.25  # 75% reduction
        elif usage_percent >= threshold:
            # Linear reduction from 1.0 at threshold to 0.5 at 95%
            reduction = (usage_percent - threshold) / (95 - threshold)
            return 1.0 - (0.5 * reduction)
        
        return 1.0
