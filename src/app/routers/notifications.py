"""
Notification management router for alerts and messages.
"""
import logging
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from ..dependencies import get_tenant_id
from ..services.notification_service import NotificationService
from ..models.notification import Notification, NotificationChannel, NotificationPriority

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


class SendNotificationRequest(BaseModel):
    """Request to send a notification."""
    title: str
    message: str
    priority: NotificationPriority = NotificationPriority.MEDIUM
    channels: List[NotificationChannel]
    recipient: Optional[str] = None


def get_notification_service(request: Request) -> NotificationService:
    """Get notification service from app state."""
    if hasattr(request.app.state, "notification_service"):
        return request.app.state.notification_service
    raise HTTPException(status_code=500, detail="Notification service not initialized")


@router.post(
    "",
    summary="Send notification",
    description="Send a notification via specified channels"
)
async def send_notification(
    request: SendNotificationRequest,
    tenant_id: str = Depends(get_tenant_id),
    service: NotificationService = Depends(get_notification_service)
):
    """Send a notification."""
    try:
        notification = Notification(
            tenant_id=tenant_id,
            title=request.title,
            message=request.message,
            priority=request.priority,
            channels=request.channels,
            recipient=request.recipient,
            created_at=datetime.utcnow()
        )
        
        success = await service.send_notification(notification)
        
        return {
            "tenant_id": tenant_id,
            "sent": success,
            "channels": [c.value for c in request.channels],
            "timestamp": notification.created_at.isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to send notification for {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/test",
    summary="Send test notification",
    description="Send a test notification to verify configuration"
)
async def send_test_notification(
    channel: NotificationChannel,
    recipient: str,
    tenant_id: str = Depends(get_tenant_id),
    service: NotificationService = Depends(get_notification_service)
):
    """Send a test notification."""
    try:
        notification = Notification(
            tenant_id=tenant_id,
            title="Test Notification",
            message=f"This is a test notification from Enterprise MCP. If you received this, {channel.value} notifications are working correctly.",
            priority=NotificationPriority.LOW,
            channels=[channel],
            recipient=recipient,
            created_at=datetime.utcnow()
        )
        
        success = await service.send_notification(notification)
        
        return {
            "tenant_id": tenant_id,
            "test_sent": success,
            "channel": channel.value,
            "recipient": recipient
        }
    except Exception as e:
        logger.error(f"Failed to send test notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/history",
    summary="Get notification history",
    description="Get recent notifications for the tenant"
)
async def get_notification_history(
    tenant_id: str = Depends(get_tenant_id),
    limit: int = 50
):
    """Get notification history."""
    # Mock data for now - would query from database in production
    return {
        "tenant_id": tenant_id,
        "notifications": [
            {
                "id": "notif-1",
                "title": "Budget Alert: 85% Used",
                "message": "Your tenant has used 85% of budget",
                "priority": "high",
                "channels": ["in-app", "email"],
                "timestamp": (datetime.utcnow()).isoformat(),
                "read": False
            },
            {
                "id": "notif-2",
                "title": "Rate Limit Approaching",
                "message": "You've used 80% of daily rate limit",
                "priority": "medium",
                "channels": ["in-app"],
                "timestamp": (datetime.utcnow()).isoformat(),
                "read": True
            }
        ],
        "total": 2,
        "unread": 1
    }


@router.post(
    "/{notification_id}/read",
    summary="Mark notification as read",
    description="Mark a notification as read"
)
async def mark_notification_read(
    notification_id: str,
    tenant_id: str = Depends(get_tenant_id)
):
    """Mark notification as read."""
    # Would update database in production
    return {
        "notification_id": notification_id,
        "tenant_id": tenant_id,
        "marked_read": True
    }


@router.get(
    "/preferences",
    summary="Get notification preferences",
    description="Get notification preferences for the tenant"
)
async def get_notification_preferences(
    tenant_id: str = Depends(get_tenant_id)
):
    """Get notification preferences."""
    # Mock preferences - would load from database
    return {
        "tenant_id": tenant_id,
        "preferences": {
            "budget_alerts": {
                "enabled": True,
                "channels": ["email", "in-app"],
                "threshold": 90
            },
            "rate_limit_alerts": {
                "enabled": True,
                "channels": ["in-app"],
                "threshold": 80
            },
            "system_alerts": {
                "enabled": True,
                "channels": ["email", "in-app"]
            }
        }
    }


@router.put(
    "/preferences",
    summary="Update notification preferences",
    description="Update notification preferences"
)
async def update_notification_preferences(
    preferences: dict,
    tenant_id: str = Depends(get_tenant_id)
):
    """Update notification preferences."""
    # Would save to database in production
    return {
        "tenant_id": tenant_id,
        "preferences": preferences,
        "updated": True
    }
