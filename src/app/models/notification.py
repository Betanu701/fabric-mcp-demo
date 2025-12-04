"""
Pydantic models for notifications and alerts.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class NotificationPriority(str, Enum):
    """Notification priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationChannel(str, Enum):
    """Notification delivery channels."""
    EMAIL = "email"
    SMS = "sms"
    IN_APP = "in-app"
    WEBHOOK = "webhook"


class NotificationType(str, Enum):
    """Notification type categories."""
    BUDGET_ALERT = "budget_alert"
    RATE_LIMIT = "rate_limit"
    AGENT_ERROR = "agent_error"
    SYSTEM = "system"
    SECURITY = "security"
    MAINTENANCE = "maintenance"


class Notification(BaseModel):
    """Notification message."""
    tenant_id: str
    title: str
    message: str
    priority: NotificationPriority = NotificationPriority.MEDIUM
    channels: List[NotificationChannel] = Field(default_factory=list)
    recipient: Optional[str] = None  # Email or phone number
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    id: str
    tenant_id: str
    type: NotificationType
    priority: NotificationPriority = Field(default=NotificationPriority.MEDIUM)
    title: str
    message: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Status
    read: bool = False
    acknowledged: bool = False
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    read_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    
    class Config:
        use_enum_values = True


class NotificationSettings(BaseModel):
    """Notification preferences per tenant."""
    tenant_id: str
    
    # Channels
    in_app_enabled: bool = True
    email_enabled: bool = False
    sms_enabled: bool = False
    
    # Contact info
    email_addresses: list[str] = Field(default_factory=list)
    phone_numbers: list[str] = Field(default_factory=list)
    
    # Filtering
    min_priority: NotificationPriority = Field(default=NotificationPriority.LOW)
    enabled_types: list[NotificationType] = Field(
        default_factory=lambda: list(NotificationType)
    )
    
    # Delivery settings
    email_digest: bool = False
    email_digest_frequency: str = Field(default="daily", description="daily, weekly")
    quiet_hours_start: Optional[str] = None  # HH:MM format
    quiet_hours_end: Optional[str] = None
    
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True


class NotificationDeliveryRequest(BaseModel):
    """Request to send notification."""
    tenant_id: str
    notification: Notification
    force_channels: Optional[list[str]] = None  # Override tenant preferences


class NotificationDeliveryResult(BaseModel):
    """Result of notification delivery."""
    notification_id: str
    tenant_id: str
    channels_attempted: list[str]
    channels_succeeded: list[str]
    channels_failed: list[str]
    errors: Dict[str, str] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
