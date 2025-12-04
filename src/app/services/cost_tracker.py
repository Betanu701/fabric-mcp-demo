"""
Cost tracking service with Azure Cost Management API integration.
Tracks resource usage and costs per tenant.
"""
import logging
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from decimal import Decimal

from azure.identity import DefaultAzureCredential
from azure.mgmt.costmanagement import CostManagementClient
from azure.mgmt.costmanagement.models import (
    QueryDefinition,
    QueryTimePeriod,
    TimeframeType,
    QueryDataset,
    QueryAggregation,
    QueryGrouping
)

from ..config import Settings
from ..models.cost import TenantCost, CostBreakdown

logger = logging.getLogger(__name__)


class CostTracker:
    """Tracks and reports Azure resource costs per tenant."""
    
    def __init__(self, settings: Settings):
        """Initialize cost tracker."""
        self.settings = settings
        self.cost_client: Optional[CostManagementClient] = None
        self._mock_costs: Dict[str, Decimal] = {}
    
    async def initialize(self) -> None:
        """Initialize Azure Cost Management client."""
        if self.settings.local_mock_services or not self.settings.azure_subscription_id:
            logger.warning("Cost tracker running in mock mode")
            return
        
        try:
            credential = DefaultAzureCredential()
            self.cost_client = CostManagementClient(credential)
            logger.info("Cost tracker initialized with Azure Cost Management API")
        except Exception as e:
            logger.error(f"Failed to initialize cost tracker: {e}")
            logger.warning("Cost tracker will run in mock mode")
    
    async def get_tenant_costs(
        self,
        tenant_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> TenantCost:
        """
        Get cost summary for a tenant.
        
        Args:
            tenant_id: Tenant identifier
            start_date: Start date for cost query (default: beginning of month)
            end_date: End date for cost query (default: today)
        
        Returns:
            TenantCost object with cost breakdown
        """
        if self.cost_client is None:
            return self._get_mock_costs(tenant_id, start_date, end_date)
        
        try:
            # Default to current month
            if not start_date:
                start_date = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if not end_date:
                end_date = datetime.utcnow()
            
            # Query Azure Cost Management API
            scope = f"/subscriptions/{self.settings.azure_subscription_id}"
            
            query = QueryDefinition(
                type="ActualCost",
                timeframe=TimeframeType.CUSTOM,
                time_period=QueryTimePeriod(
                    from_property=start_date.isoformat(),
                    to=end_date.isoformat()
                ),
                dataset=QueryDataset(
                    granularity="Daily",
                    aggregation={
                        "totalCost": QueryAggregation(name="PreTaxCost", function="Sum")
                    },
                    grouping=[
                        QueryGrouping(type="Dimension", name="ServiceName"),
                        QueryGrouping(type="Tag", name="TenantId")
                    ],
                    filter={
                        "tags": {
                            "name": "TenantId",
                            "operator": "In",
                            "values": [tenant_id]
                        }
                    }
                )
            )
            
            result = self.cost_client.query.usage(scope, query)
            
            # Parse results
            total_cost = Decimal("0.0")
            breakdowns: List[CostBreakdown] = []
            
            if result.rows:
                for row in result.rows:
                    # row format: [cost, service_name, tenant_id, date]
                    cost = Decimal(str(row[0]))
                    service = row[1]
                    date = row[3]
                    
                    total_cost += cost
                    breakdowns.append(CostBreakdown(
                        service=service,
                        cost=cost,
                        date=datetime.fromisoformat(date)
                    ))
            
            return TenantCost(
                tenant_id=tenant_id,
                total_cost=total_cost,
                period_start=start_date,
                period_end=end_date,
                currency="USD",
                breakdowns=breakdowns
            )
            
        except Exception as e:
            logger.error(f"Failed to get costs for tenant {tenant_id}: {e}")
            return self._get_mock_costs(tenant_id, start_date, end_date)
    
    def _get_mock_costs(
        self,
        tenant_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> TenantCost:
        """Generate mock cost data for testing."""
        if not start_date:
            start_date = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if not end_date:
            end_date = datetime.utcnow()
        
        # Generate predictable mock costs based on tenant ID hash
        base_cost = Decimal(str(hash(tenant_id) % 1000))
        
        if tenant_id not in self._mock_costs:
            self._mock_costs[tenant_id] = base_cost
        
        # Increment mock costs slightly each time
        self._mock_costs[tenant_id] += Decimal("10.50")
        
        breakdowns = [
            CostBreakdown(
                service="Azure Container Apps",
                cost=self._mock_costs[tenant_id] * Decimal("0.4"),
                date=start_date
            ),
            CostBreakdown(
                service="Azure Key Vault",
                cost=self._mock_costs[tenant_id] * Decimal("0.1"),
                date=start_date
            ),
            CostBreakdown(
                service="Azure Cache for Redis",
                cost=self._mock_costs[tenant_id] * Decimal("0.3"),
                date=start_date
            ),
            CostBreakdown(
                service="Azure Blob Storage",
                cost=self._mock_costs[tenant_id] * Decimal("0.2"),
                date=start_date
            )
        ]
        
        return TenantCost(
            tenant_id=tenant_id,
            total_cost=self._mock_costs[tenant_id],
            period_start=start_date,
            period_end=end_date,
            currency="USD",
            breakdowns=breakdowns
        )
    
    async def track_request_cost(
        self,
        tenant_id: str,
        service: str,
        cost: Decimal
    ) -> None:
        """
        Track cost for an individual request (for immediate tracking).
        
        Args:
            tenant_id: Tenant identifier
            service: Service name (e.g., "FoundryIQ", "OpenAI")
            cost: Cost in USD
        """
        # In production, this would write to a tracking database
        # For now, just log it
        logger.debug(f"Cost tracked - Tenant: {tenant_id}, Service: {service}, Cost: ${cost}")
    
    async def get_cost_forecast(
        self,
        tenant_id: str,
        days_ahead: int = 30
    ) -> Decimal:
        """
        Forecast costs for the next N days based on current usage trends.
        
        Args:
            tenant_id: Tenant identifier
            days_ahead: Number of days to forecast
        
        Returns:
            Forecasted total cost
        """
        if self.cost_client is None:
            # Mock forecast: current daily cost * days
            current_costs = await self.get_tenant_costs(tenant_id)
            days_in_period = (current_costs.period_end - current_costs.period_start).days or 1
            daily_cost = current_costs.total_cost / Decimal(str(days_in_period))
            return daily_cost * Decimal(str(days_ahead))
        
        try:
            # Query actual forecast from Azure
            scope = f"/subscriptions/{self.settings.azure_subscription_id}"
            
            end_date = datetime.utcnow() + timedelta(days=days_ahead)
            query = QueryDefinition(
                type="ForecastCost",
                timeframe=TimeframeType.CUSTOM,
                time_period=QueryTimePeriod(
                    from_property=datetime.utcnow().isoformat(),
                    to=end_date.isoformat()
                ),
                dataset=QueryDataset(
                    granularity="Daily",
                    aggregation={
                        "totalCost": QueryAggregation(name="PreTaxCost", function="Sum")
                    },
                    filter={
                        "tags": {
                            "name": "TenantId",
                            "operator": "In",
                            "values": [tenant_id]
                        }
                    }
                )
            )
            
            result = self.cost_client.query.usage(scope, query)
            
            total_forecast = Decimal("0.0")
            if result.rows:
                for row in result.rows:
                    total_forecast += Decimal(str(row[0]))
            
            return total_forecast
            
        except Exception as e:
            logger.error(f"Failed to get cost forecast for {tenant_id}: {e}")
            # Fallback to simple calculation
            current_costs = await self.get_tenant_costs(tenant_id)
            days_in_period = (current_costs.period_end - current_costs.period_start).days or 1
            daily_cost = current_costs.total_cost / Decimal(str(days_in_period))
            return daily_cost * Decimal(str(days_ahead))
    
    async def get_all_tenant_costs(self) -> List[TenantCost]:
        """
        Get costs for all tenants.
        
        Returns:
            List of TenantCost objects
        """
        # This would query all unique tenant IDs from tags
        # For now, return empty list as this requires tenant registry
        logger.warning("get_all_tenant_costs not fully implemented")
        return []
