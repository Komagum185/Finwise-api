import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def send_otp_email(email, otp_code, purpose="verification"):
    """
    Send OTP via email
    Replace this with your actual email service (SendGrid, AWS SES, etc.)
    """
    try:
        # TODO: Replace with actual email service
        # Example with SendGrid:
        # from sendgrid import SendGridAPIClient
        # from sendgrid.helpers.mail import Mail
        # 
        # message = Mail(
        #     from_email='noreply@yourdomain.com',
        #     to_emails=email,
        #     subject=f'Your {purpose.title()} OTP',
        #     html_content=f'<p>Your OTP code is: <strong>{otp_code}</strong></p>'
        # )
        # sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        # response = sg.send(message)
        
        # For now, just log the OTP (remove this in production)
        logger.info(f"OTP for {email}: {otp_code} (Purpose: {purpose})")
        
        return True
    except Exception as e:
        logger.error(f"Failed to send OTP email to {email}: {str(e)}")
        return False


def send_otp_sms(phone_number, otp_code, purpose="verification"):
    """
    Send OTP via SMS
    Replace this with your actual SMS service (Twilio, AWS SNS, etc.)
    """
    try:
        # TODO: Replace with actual SMS service
        # Example with Twilio:
        # from twilio.rest import Client
        # 
        # client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        # message = client.messages.create(
        #     body=f'Your {purpose} OTP is: {otp_code}',
        #     from_=settings.TWILIO_PHONE_NUMBER,
        #     to=phone_number
        # )
        
        # For now, just log the OTP (remove this in production)
        logger.info(f"SMS OTP for {phone_number}: {otp_code} (Purpose: {purpose})")
        
        return True
    except Exception as e:
        logger.error(f"Failed to send OTP SMS to {phone_number}: {str(e)}")
        return False


def send_registration_approval_email(email, username, approval_status, rejection_reason=None):
    """
    Send registration approval/rejection email
    """
    try:
        if approval_status == 'approved':
            subject = 'Registration Approved'
            message = f"""
            Dear {username},
            
            Your registration has been approved! You can now log in to your account.
            
            Best regards,
            The Finwise Team
            """
        else:
            subject = 'Registration Rejected'
            message = f"""
            Dear {username},
            
            Your registration has been rejected.
            
            Reason: {rejection_reason or 'No reason provided'}
            
            If you have any questions, please contact support.
            
            Best regards,
            The Finwise Team
            """
        
        # TODO: Replace with actual email service
        logger.info(f"Registration {approval_status} email for {email}: {message}")
        
        return True
    except Exception as e:
        logger.error(f"Failed to send registration {approval_status} email to {email}: {str(e)}")
        return False 