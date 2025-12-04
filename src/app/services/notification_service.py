"""
Notification service for sending alerts via email and SMS.
Uses Azure Communication Services.
"""
import logging
from typing import List, Optional
from datetime import datetime

from azure.identity import DefaultAzureCredential
from azure.communication.email import EmailClient
from azure.communication.sms import SmsClient

from ..config import Settings
from ..models.notification import Notification, NotificationChannel, NotificationPriority

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending notifications via email and SMS."""
    
    def __init__(self, settings: Settings):
        """Initialize notification service."""
        self.settings = settings
        self.email_client: Optional[EmailClient] = None
        self.sms_client: Optional[SmsClient] = None
        self._mock_mode = settings.local_mock_services
    
    async def initialize(self) -> None:
        """Initialize Azure Communication Services clients."""
        if self._mock_mode:
            logger.warning("Notification service running in mock mode")
            return
        
        try:
            if self.settings.azure_communication_service_endpoint:
                credential = DefaultAzureCredential()
                
                # Initialize email client
                self.email_client = EmailClient(
                    self.settings.azure_communication_service_endpoint,
                    credential
                )
                
                # Initialize SMS client (if connection string available)
                if hasattr(self.settings, 'azure_communication_connection_string'):
                    self.sms_client = SmsClient.from_connection_string(
                        self.settings.azure_communication_connection_string
                    )
                
                logger.info("Notification service initialized")
            else:
                logger.warning("Azure Communication Service endpoint not configured")
                
        except Exception as e:
            logger.error(f"Failed to initialize notification service: {e}")
    
    async def send_notification(
        self,
        notification: Notification
    ) -> bool:
        """
        Send a notification via configured channels.
        
        Args:
            notification: Notification object
        
        Returns:
            True if sent successfully, False otherwise
        """
        success = True
        
        for channel in notification.channels:
            if channel == NotificationChannel.EMAIL:
                result = await self._send_email(notification)
                success = success and result
            elif channel == NotificationChannel.SMS:
                result = await self._send_sms(notification)
                success = success and result
            elif channel == NotificationChannel.IN_APP:
                result = await self._send_in_app(notification)
                success = success and result
        
        return success
    
    async def _send_email(self, notification: Notification) -> bool:
        """Send email notification."""
        if self._mock_mode or not self.email_client:
            logger.info(f"[MOCK EMAIL] To: {notification.recipient}, Subject: {notification.title}")
            return True
        
        try:
            if not notification.recipient:
                logger.warning("No email recipient specified")
                return False
            
            # Construct email message
            message = {
                "senderAddress": self.settings.notification_sender_email or "noreply@enterprisemcp.com",
                "recipients": {
                    "to": [{"address": notification.recipient}]
                },
                "content": {
                    "subject": notification.title,
                    "plainText": notification.message,
                    "html": self._format_html_email(notification)
                }
            }
            
            # Send email
            poller = self.email_client.begin_send(message)
            result = poller.result()
            
            logger.info(f"Email sent to {notification.recipient}: {notification.title}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    async def _send_sms(self, notification: Notification) -> bool:
        """Send SMS notification."""
        if self._mock_mode or not self.sms_client:
            logger.info(f"[MOCK SMS] To: {notification.recipient}, Message: {notification.message[:50]}...")
            return True
        
        try:
            if not notification.recipient:
                logger.warning("No SMS recipient specified")
                return False
            
            # Send SMS
            response = self.sms_client.send(
                from_=self.settings.notification_sender_phone or "+1234567890",
                to=[notification.recipient],
                message=notification.message[:160]  # SMS character limit
            )
            
            logger.info(f"SMS sent to {notification.recipient}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")
            return False
    
    async def _send_in_app(self, notification: Notification) -> bool:
        """Store in-app notification."""
        # In production, this would write to a database
        logger.info(f"[IN-APP] Tenant: {notification.tenant_id}, Title: {notification.title}")
        return True
    
    def _format_html_email(self, notification: Notification) -> str:
        """Format notification as HTML email."""
        priority_colors = {
            NotificationPriority.LOW: "#6c757d",
            NotificationPriority.MEDIUM: "#0d6efd",
            NotificationPriority.HIGH: "#ffc107",
            NotificationPriority.CRITICAL: "#dc3545"
        }
        
        color = priority_colors.get(notification.priority, "#6c757d")
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: {color}; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .footer {{ background-color: #f8f9fa; padding: 10px; text-align: center; font-size: 12px; color: #6c757d; }}
                .priority {{ display: inline-block; padding: 5px 10px; border-radius: 3px; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{notification.title}</h1>
            </div>
            <div class="content">
                <p><span class="priority" style="background-color: {color}; color: white;">
                    {notification.priority.value.upper()}
                </span></p>
                <p>{notification.message}</p>
                {f'<p><strong>Metadata:</strong> {notification.metadata}</p>' if notification.metadata else ''}
            </div>
            <div class="footer">
                <p>Enterprise MCP - Automated Notification</p>
                <p>Sent at {notification.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
            </div>
        </body>
        </html>
        """
        return html
    
    async def send_budget_alert(
        self,
        tenant_id: str,
        recipient: str,
        current_cost: float,
        budget_limit: float,
        usage_percent: float
    ) -> bool:
        """
        Send budget threshold alert.
        
        Args:
            tenant_id: Tenant identifier
            recipient: Email or phone number
            current_cost: Current spend
            budget_limit: Budget limit
            usage_percent: Usage percentage
        
        Returns:
            True if sent successfully
        """
        priority = NotificationPriority.HIGH if usage_percent >= 95 else NotificationPriority.MEDIUM
        
        notification = Notification(
            tenant_id=tenant_id,
            title=f"Budget Alert: {usage_percent:.1f}% Used",
            message=f"Your tenant has used ${current_cost:.2f} of ${budget_limit:.2f} budget ({usage_percent:.1f}%). Please review your usage.",
            priority=priority,
            channels=[NotificationChannel.EMAIL, NotificationChannel.IN_APP],
            recipient=recipient,
            created_at=datetime.utcnow()
        )
        
        return await self.send_notification(notification)
    
    async def send_rate_limit_alert(
        self,
        tenant_id: str,
        recipient: str,
        limit_type: str,
        limit_value: int
    ) -> bool:
        """
        Send rate limit exceeded alert.
        
        Args:
            tenant_id: Tenant identifier
            recipient: Email or phone number
            limit_type: Type of limit (RPM, RPD, monthly)
            limit_value: Limit value
        
        Returns:
            True if sent successfully
        """
        notification = Notification(
            tenant_id=tenant_id,
            title=f"Rate Limit Exceeded: {limit_type}",
            message=f"Your tenant has exceeded the {limit_type} rate limit of {limit_value} requests. Some requests may be throttled.",
            priority=NotificationPriority.MEDIUM,
            channels=[NotificationChannel.IN_APP],
            recipient=recipient,
            created_at=datetime.utcnow()
        )
        
        return await self.send_notification(notification)
    
    async def send_system_alert(
        self,
        tenant_id: str,
        recipient: str,
        alert_message: str,
        priority: NotificationPriority = NotificationPriority.HIGH
    ) -> bool:
        """
        Send general system alert.
        
        Args:
            tenant_id: Tenant identifier
            recipient: Email or phone number
            alert_message: Alert message
            priority: Notification priority
        
        Returns:
            True if sent successfully
        """
        notification = Notification(
            tenant_id=tenant_id,
            title="System Alert",
            message=alert_message,
            priority=priority,
            channels=[NotificationChannel.EMAIL, NotificationChannel.IN_APP],
            recipient=recipient,
            created_at=datetime.utcnow()
        )
        
        return await self.send_notification(notification)
