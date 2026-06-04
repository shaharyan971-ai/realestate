"""Email notification service."""
from typing import List, Dict, Any, Optional
import logging
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from datetime import datetime

from app.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Email service using SendGrid."""
    
    def __init__(self):
        self.sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        self.from_email = settings.SENDGRID_FROM_EMAIL
        self.from_name = settings.SENDGRID_FROM_NAME
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        plain_text: Optional[str] = None
    ) -> bool:
        """Send email."""
        try:
            if not settings.ENABLE_EMAIL_NOTIFICATIONS:
                logger.info(f"Email notifications disabled. Skipping email to {to_email}")
                return True

            # Add logo to the top of every email
            logo_url = getattr(settings, "LOGO_URL", "https://realestate.app/static/logo.png")
            html_content = f"""
            <div style='text-align:center; margin-bottom:24px;'>
                <img src='{logo_url}' alt='RealEstate Logo' style='height:60px;'>
            </div>
            {html_content}
            """

            message = Mail(
                from_email=Email(self.from_email, self.from_name),
                to_emails=To(to_email),
                subject=subject,
                html_content=html_content,
                plain_text_content=plain_text
            )
            
            response = self.sg.send(message)
            logger.info(f"✅ Email sent to {to_email}: {response.status_code}")
            return response.status_code in [200, 201, 202]
        except Exception as e:
            logger.error(f"❌ Error sending email to {to_email}: {str(e)}")
            return False
    
    async def send_booking_confirmation(
        self,
        to_email: str,
        customer_name: str,
        property_title: str,
        visit_date: datetime,
        booking_id: str
    ) -> bool:
        """Send booking confirmation email."""
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 30px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                    <h2 style="color: #f1c40f; text-align: center;">Booking Confirmed! 🎉</h2>
                    
                    <p>Dear {customer_name},</p>
                    
                    <p>Your property booking has been confirmed. Here are the details:</p>
                    
                    <div style="background-color: #f9f9f9; padding: 20px; border-left: 4px solid #f1c40f; margin: 20px 0;">
                        <p><strong>Property:</strong> {property_title}</p>
                        <p><strong>Visit Date:</strong> {visit_date.strftime('%d %B %Y at %I:%M %p')}</p>
                        <p><strong>Booking ID:</strong> {booking_id}</p>
                    </div>
                    
                    <p>Your agent will contact you shortly to confirm the visit.</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{settings.FRONTEND_URL}/bookings/{booking_id}" style="background-color: #f1c40f; color: #000; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">View Booking</a>
                    </div>
                    
                    <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                    
                    <p style="font-size: 12px; color: #666;">
                        © 2024 RealEstate Platform. All rights reserved.<br>
                        If you have any questions, contact us at {settings.ADMIN_EMAIL}
                    </p>
                </div>
            </body>
        </html>
        """
        
        return await self.send_email(
            to_email=to_email,
            subject=f"Booking Confirmed - {property_title}",
            html_content=html_content
        )
    
    async def send_payment_confirmation(
        self,
        to_email: str,
        customer_name: str,
        amount: float,
        currency: str,
        transaction_id: str,
        description: str
    ) -> bool:
        """Send payment confirmation email."""
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 30px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                    <h2 style="color: #51cf66; text-align: center;">Payment Successful ✓</h2>
                    
                    <p>Dear {customer_name},</p>
                    
                    <p>Your payment has been successfully processed.</p>
                    
                    <div style="background-color: #f9f9f9; padding: 20px; border-left: 4px solid #51cf66; margin: 20px 0;">
                        <p><strong>Amount:</strong> {currency} {amount:.2f}</p>
                        <p><strong>Description:</strong> {description}</p>
                        <p><strong>Transaction ID:</strong> {transaction_id}</p>
                        <p><strong>Date:</strong> {datetime.now().strftime('%d %B %Y at %I:%M %p')}</p>
                    </div>
                    
                    <p>Thank you for your payment. You should receive the service shortly.</p>
                    
                    <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                    
                    <p style="font-size: 12px; color: #666;">
                        © 2024 RealEstate Platform. All rights reserved.<br>
                        If you have any questions, contact us at {settings.ADMIN_EMAIL}
                    </p>
                </div>
            </body>
        </html>
        """
        
        return await self.send_email(
            to_email=to_email,
            subject="Payment Confirmation",
            html_content=html_content
        )
    
    async def send_subscription_expiry_reminder(
        self,
        to_email: str,
        customer_name: str,
        plan_name: str,
        expiry_date: datetime
    ) -> bool:
        """Send subscription expiry reminder."""
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 30px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                    <h2 style="color: #ff6b6b; text-align: center;">Subscription Expiring Soon ⚠️</h2>
                    
                    <p>Dear {customer_name},</p>
                    
                    <p>Your <strong>{plan_name}</strong> subscription is expiring on <strong>{expiry_date.strftime('%d %B %Y')}</strong>.</p>
                    
                    <p>Renew your subscription now to continue enjoying premium features:</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{settings.FRONTEND_URL}/subscriptions/renew" style="background-color: #f1c40f; color: #000; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">Renew Subscription</a>
                    </div>
                    
                    <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                    
                    <p style="font-size: 12px; color: #666;">
                        © 2024 RealEstate Platform. All rights reserved.<br>
                        If you have any questions, contact us at {settings.ADMIN_EMAIL}
                    </p>
                </div>
            </body>
        </html>
        """
        
        return await self.send_email(
            to_email=to_email,
            subject=f"Your {plan_name} Subscription is Expiring",
            html_content=html_content
        )
    
    async def send_property_approval_email(
        self,
        to_email: str,
        name: str,
        property_title: str,
        is_approved: bool,
        reason: Optional[str] = None
    ) -> bool:
        """Send property approval/rejection email."""
        if is_approved:
            html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif;">
                    <div style="max-width: 600px; margin: 20px auto; padding: 30px; background: #ffffff; border-radius: 10px;">
                        <h2 style="color: #51cf66;">Property Approved ✓</h2>
                        <p>Your property "<strong>{property_title}</strong>" has been approved and is now live on the platform!</p>
                        <a href="{settings.FRONTEND_URL}/properties" style="background: #51cf66; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">View Property</a>
                    </div>
                </body>
            </html>
            """
            subject = f"Property Approved - {property_title}"
        else:
            html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif;">
                    <div style="max-width: 600px; margin: 20px auto; padding: 30px; background: #ffffff; border-radius: 10px;">
                        <h2 style="color: #ff6b6b;">Property Rejected</h2>
                        <p>Your property "<strong>{property_title}</strong>" could not be approved.</p>
                        <p><strong>Reason:</strong> {reason or "Please contact support for details."}</p>
                        <a href="{settings.FRONTEND_URL}/support" style="background: #ff6b6b; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Contact Support</a>
                    </div>
                </body>
            </html>
            """
            subject = f"Property Rejected - {property_title}"
        
        return await self.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content
        )


# Initialize email service
email_service = EmailService()
