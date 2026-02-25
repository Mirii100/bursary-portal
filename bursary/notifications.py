from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def send_bursary_notification(user, subject, message):
    """
    Sends both Email and SMS notifications to the user.
    """
    # 1. Send Email
    if user.email:
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            logger.info(f"Email sent to {user.email}")
        except Exception as e:
            logger.error(f"Failed to send email to {user.email}: {e}")

    # 2. Send SMS (Placeholder logic)
    if hasattr(user, 'phone') and user.phone:
        # In a real app, you'd call an API like Africa's Talking or Twilio here
        # For this prototype, we log to console/log file
        sms_content = f"CBMS: {message}"
        logger.info(f"SMS to {user.phone}: {sms_content}")
        # print(f"DEBUG SMS: {user.phone} -> {sms_content}")
