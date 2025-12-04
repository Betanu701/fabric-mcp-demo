"""
Pydantic models for data validation and serialization.
"""
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl


class BudgetEnforcement(str, Enum):
    """Budget enforcement policy options."""
    BLOCK = "block"
    THROTTLE = "throttle"
    WARN = "warn"


class NotificationChannel(str, Enum):
    """Notification channel options."""
    IN_APP = "in-app"
    EMAIL = "email"
    SMS = "sms"


class BrandingConfig(BaseModel):
    """Tenant branding configuration."""
    inherit_global: bool = True
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    accent_color: Optional[str] = None
    font_family: Optional[str] = None
    logo_url: Optional[HttpUrl] = None
    favicon_url: Optional[HttpUrl] = None
    custom_css: Optional[str] = None


class TenantConfig(BaseModel):
    """Tenant configuration schema."""
    id: str = Field(..., description="Unique tenant identifier")
    name: str = Field(..., description="Tenant display name")
    enabled: bool = Field(default=True, description="Whether tenant is active")
    
    # FoundryIQ configuration
    foundry_endpoint: str = Field(..., description="FoundryIQ API endpoint")
    
    # Entra ID authentication
    entra_client_id: Optional[str] = Field(default=None, description="Entra ID client ID")
    entra_tenant_id: Optional[str] = Field(default=None, description="Entra ID tenant ID")
    
    # Data sources
    allowed_sources: List[str] = Field(
        default_factory=list,
        description="Allowed DataAgent source IDs (empty = all)"
    )
    
    # Rate limiting
    rate_limit_rpm: int = Field(default=100, description="Requests per minute")
    rate_limit_rpd: int = Field(default=10000, description="Requests per day")
    quota_monthly_requests: int = Field(default=100000, description="Monthly request quota")
    quota_monthly_tokens: int = Field(default=1000000, description="Monthly token quota")
    
    # Budget management
    budget_limit: Optional[float] = Field(default=None, description="Monthly budget limit in USD")
    budget_threshold: int = Field(default=90, ge=0, le=100, description="Budget alert %")
    budget_enforcement: BudgetEnforcement = Field(
        default=BudgetEnforcement.BLOCK,
        description="Budget enforcement policy"
    )
    
    # Notifications
    notification_channels: List[NotificationChannel] = Field(
        default_factory=lambda: [NotificationChannel.IN_APP],
        description="Enabled notification channels"
    )
    
    # Branding
    branding: BrandingConfig = Field(default_factory=BrandingConfig)
    
    # Metadata
    admin_contact: str = Field(..., description="Admin email contact")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True


class TenantRegistry(BaseModel):
    """Tenant registry stored in Key Vault."""
    tenants: List[str] = Field(
        default_factory=list,
        description="List of tenant IDs"
    )
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class GlobalBranding(BaseModel):
    """Global branding configuration."""
    primary_color: str = Field(default="#0078D4", description="Primary brand color")
    secondary_color: str = Field(default="#50E6FF", description="Secondary brand color")
    accent_color: str = Field(default="#FFB900", description="Accent brand color")
    font_family: str = Field(
        default="Segoe UI, -apple-system, BlinkMacSystemFont, sans-serif",
        description="Brand font family"
    )
    logo_url: Optional[HttpUrl] = Field(default=None, description="Global logo URL")
    favicon_url: Optional[HttpUrl] = Field(default=None, description="Global favicon URL")
    app_name: str = Field(default="Enterprise MCP", description="Application name")
