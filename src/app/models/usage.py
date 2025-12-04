"""
Pydantic models for usage tracking and metrics.
"""
from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel, Field


class UsageMetrics(BaseModel):
    """Usage metrics for a tenant."""
    tenant_id: str
    period_start: datetime
    period_end: datetime
    
    # Request metrics
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    throttled_requests: int = 0
    
    # Token metrics
    total_tokens: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    
    # Latency metrics (milliseconds)
    avg_latency_ms: float = 0.0
    p50_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    
    # Agent usage
    agents_used: Dict[str, int] = Field(default_factory=dict)
    sources_queried: Dict[str, int] = Field(default_factory=dict)


class QuotaStatus(BaseModel):
    """Current quota usage status."""
    tenant_id: str
    
    # Request quotas
    requests_used_rpm: int = 0
    requests_limit_rpm: int = 100
    requests_remaining_rpm: int = 100
    
    requests_used_rpd: int = 0
    requests_limit_rpd: int = 10000
    requests_remaining_rpd: int = 10000
    
    requests_used_monthly: int = 0
    requests_limit_monthly: int = 100000
    requests_remaining_monthly: int = 100000
    
    # Token quotas
    tokens_used_monthly: int = 0
    tokens_limit_monthly: int = 1000000
    tokens_remaining_monthly: int = 1000000
    
    # Status
    is_throttled: bool = False
    throttle_reason: Optional[str] = None
    reset_at: Optional[datetime] = None
    
    # Timestamp
    checked_at: datetime = Field(default_factory=datetime.utcnow)


class RateLimitEvent(BaseModel):
    """Rate limit event."""
    tenant_id: str
    limit_type: str = Field(description="rpm, rpd, monthly_requests, monthly_tokens")
    limit_value: int
    current_value: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_path: Optional[str] = None
    user_id: Optional[str] = None
