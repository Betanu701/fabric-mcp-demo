"""
Rate limiting service with Redis backend.
Supports per-tenant rate limits: RPM (requests per minute), RPD (requests per day), and monthly quotas.
"""
import logging
from typing import Optional
from datetime import datetime, timedelta
import redis.asyncio as redis
from redis.asyncio import Redis

from ..config import Settings

logger = logging.getLogger(__name__)


class RateLimiter:
    """Redis-backed rate limiter with multi-level quotas."""
    
    def __init__(self, settings: Settings):
        """Initialize rate limiter."""
        self.settings = settings
        self.redis_client: Optional[Redis] = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize Redis connection."""
        if self._initialized:
            return
        
        if self.settings.local_mock_services:
            logger.warning("Rate limiter running in mock mode - no limits enforced")
            self._initialized = True
            return
        
        try:
            self.redis_client = await redis.from_url(
                self.settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            # Test connection
            await self.redis_client.ping()
            logger.info("Rate limiter initialized with Redis")
            self._initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize rate limiter: {e}")
            logger.warning("Rate limiter will run in mock mode")
            self._initialized = True
    
    async def check_rate_limit(
        self,
        tenant_id: str,
        rpm_limit: int,
        rpd_limit: int,
        monthly_limit: Optional[int] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Check if request is within rate limits.
        
        Args:
            tenant_id: Tenant identifier
            rpm_limit: Requests per minute limit
            rpd_limit: Requests per day limit
            monthly_limit: Optional monthly request limit
        
        Returns:
            Tuple of (allowed: bool, reason: Optional[str])
        """
        if self.redis_client is None:
            # Mock mode - always allow
            return True, None
        
        try:
            # Check RPM (requests per minute)
            rpm_key = f"ratelimit:rpm:{tenant_id}"
            rpm_count = await self.redis_client.get(rpm_key)
            
            if rpm_count and int(rpm_count) >= rpm_limit:
                return False, f"Rate limit exceeded: {rpm_limit} requests per minute"
            
            # Check RPD (requests per day)
            rpd_key = f"ratelimit:rpd:{tenant_id}:{datetime.utcnow().strftime('%Y-%m-%d')}"
            rpd_count = await self.redis_client.get(rpd_key)
            
            if rpd_count and int(rpd_count) >= rpd_limit:
                return False, f"Daily quota exceeded: {rpd_limit} requests per day"
            
            # Check monthly limit if specified
            if monthly_limit:
                monthly_key = f"ratelimit:monthly:{tenant_id}:{datetime.utcnow().strftime('%Y-%m')}"
                monthly_count = await self.redis_client.get(monthly_key)
                
                if monthly_count and int(monthly_count) >= monthly_limit:
                    return False, f"Monthly quota exceeded: {monthly_limit} requests per month"
            
            return True, None
            
        except Exception as e:
            logger.error(f"Rate limit check failed for {tenant_id}: {e}")
            # Fail open - allow request if rate limiter has issues
            return True, None
    
    async def record_request(
        self,
        tenant_id: str,
        rpm_limit: int,
        rpd_limit: int,
        monthly_limit: Optional[int] = None
    ) -> None:
        """
        Record a request and update rate limit counters.
        
        Args:
            tenant_id: Tenant identifier
            rpm_limit: Requests per minute limit (for TTL)
            rpd_limit: Requests per day limit (for TTL)
            monthly_limit: Optional monthly request limit
        """
        if self.redis_client is None:
            return
        
        try:
            # Increment RPM counter
            rpm_key = f"ratelimit:rpm:{tenant_id}"
            await self.redis_client.incr(rpm_key)
            await self.redis_client.expire(rpm_key, 60)  # 60 seconds TTL
            
            # Increment RPD counter
            rpd_key = f"ratelimit:rpd:{tenant_id}:{datetime.utcnow().strftime('%Y-%m-%d')}"
            await self.redis_client.incr(rpd_key)
            await self.redis_client.expire(rpd_key, 86400)  # 24 hours TTL
            
            # Increment monthly counter if tracking
            if monthly_limit:
                monthly_key = f"ratelimit:monthly:{tenant_id}:{datetime.utcnow().strftime('%Y-%m')}"
                await self.redis_client.incr(monthly_key)
                # Set TTL to end of next month
                days_in_month = 31
                await self.redis_client.expire(monthly_key, days_in_month * 86400)
            
            logger.debug(f"Recorded request for tenant {tenant_id}")
            
        except Exception as e:
            logger.error(f"Failed to record request for {tenant_id}: {e}")
    
    async def get_usage_stats(self, tenant_id: str) -> dict:
        """
        Get current usage statistics for a tenant.
        
        Args:
            tenant_id: Tenant identifier
        
        Returns:
            Dictionary with usage statistics
        """
        if self.redis_client is None:
            return {
                "rpm": 0,
                "rpd": 0,
                "monthly": 0,
                "mock_mode": True
            }
        
        try:
            rpm_key = f"ratelimit:rpm:{tenant_id}"
            rpd_key = f"ratelimit:rpd:{tenant_id}:{datetime.utcnow().strftime('%Y-%m-%d')}"
            monthly_key = f"ratelimit:monthly:{tenant_id}:{datetime.utcnow().strftime('%Y-%m')}"
            
            rpm_count = await self.redis_client.get(rpm_key)
            rpd_count = await self.redis_client.get(rpd_key)
            monthly_count = await self.redis_client.get(monthly_key)
            
            return {
                "rpm": int(rpm_count) if rpm_count else 0,
                "rpd": int(rpd_count) if rpd_count else 0,
                "monthly": int(monthly_count) if monthly_count else 0,
                "mock_mode": False
            }
            
        except Exception as e:
            logger.error(f"Failed to get usage stats for {tenant_id}: {e}")
            return {
                "rpm": 0,
                "rpd": 0,
                "monthly": 0,
                "error": str(e)
            }
    
    async def reset_limits(self, tenant_id: str) -> bool:
        """
        Reset all rate limits for a tenant (admin function).
        
        Args:
            tenant_id: Tenant identifier
        
        Returns:
            True if successful, False otherwise
        """
        if self.redis_client is None:
            return True  # Mock mode
        
        try:
            # Find and delete all keys for this tenant
            pattern = f"ratelimit:*:{tenant_id}*"
            keys = []
            async for key in self.redis_client.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                await self.redis_client.delete(*keys)
                logger.info(f"Reset rate limits for tenant {tenant_id}: {len(keys)} keys deleted")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to reset limits for {tenant_id}: {e}")
            return False
    
    async def close(self) -> None:
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Rate limiter closed")
