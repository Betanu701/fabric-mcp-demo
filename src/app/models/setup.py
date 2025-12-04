"""
Pydantic models for setup wizard and configuration.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl


class SetupStep(str, Enum):
    """Setup wizard steps."""
    WELCOME = "welcome"
    REQUIRED_CONFIG = "required_config"
    SECURITY = "security"
    NOTIFICATIONS = "notifications"
    DISCOVERY = "discovery"
    BRANDING = "branding"
    REVIEW = "review"
    COMPLETE = "complete"


class SetupStatus(str, Enum):
    """Setup wizard status."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class SetupState(BaseModel):
    """Setup wizard state."""
    status: SetupStatus = Field(default=SetupStatus.NOT_STARTED)
    current_step: SetupStep = Field(default=SetupStep.WELCOME)
    completed_steps: List[SetupStep] = Field(default_factory=list)
    skipped_steps: List[SetupStep] = Field(default_factory=list)
    
    # Configuration collected
    config: Dict[str, Any] = Field(default_factory=dict)
    
    # Timestamps
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True


class RequiredConfig(BaseModel):
    """Required configuration step data."""
    foundry_endpoint: str = Field(..., description="FoundryIQ API endpoint")
    admin_email: str = Field(..., description="Admin contact email")
    azure_subscription_id: Optional[str] = None
    azure_resource_group: Optional[str] = None


class SecurityConfig(BaseModel):
    """Security configuration step data."""
    entra_enabled: bool = False
    entra_tenant_id: Optional[str] = None
    entra_client_id: Optional[str] = None
    test_connection: bool = False


class NotificationConfig(BaseModel):
    """Notification configuration step data."""
    in_app_enabled: bool = True
    email_enabled: bool = False
    sms_enabled: bool = False
    email_addresses: List[str] = Field(default_factory=list)
    phone_numbers: List[str] = Field(default_factory=list)
    test_notification: bool = False


class DiscoveryConfig(BaseModel):
    """Discovery configuration step data."""
    auto_discover: bool = True
    selected_sources: List[str] = Field(default_factory=list)
    source_descriptions: Dict[str, str] = Field(default_factory=dict)


class BrandingSetup(BaseModel):
    """Branding configuration step data."""
    upload_logo: bool = False
    logo_url: Optional[HttpUrl] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    style_guide_uploaded: bool = False


class SetupReview(BaseModel):
    """Setup review summary."""
    required_config: RequiredConfig
    security_config: Optional[SecurityConfig] = None
    notification_config: NotificationConfig
    discovery_config: DiscoveryConfig
    branding_setup: Optional[BrandingSetup] = None
    
    ready_to_complete: bool = True
    warnings: List[str] = Field(default_factory=list)
