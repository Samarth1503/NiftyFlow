import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from backend.core.config import settings
import logging

logger = logging.getLogger(__name__)

def send_password_reset_email(to_email: str, token: str):
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning("SMTP_USER or SMTP_PASSWORD not set. Check terminal for token.")
        print(f"\n[DEV MODE] PASSWORD RESET TOKEN FOR {to_email}: {token}\n")
        return
    
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 10px;">
        <h2 style="color: #1a73e8;">Password Reset Request</h2>
        <p>You recently requested a password reset for your NiftyFlow account.</p>
        <p>Please click the button below to securely set a new password. You will be automatically logged in after resetting:</p>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="http://localhost:3000/login?mode=reset&token={token}" style="background-color: #1a73e8; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 16px; display: inline-block;">Reset Password</a>
        </div>
        
        <p style="color: #5f6368; font-size: 14px;">If the button doesn't work, copy and paste this link into your browser:</p>
        <p style="color: #5f6368; font-size: 12px; word-break: break-all;">http://localhost:3000/login?mode=reset&token={token}</p>
        
        <p style="color: #5f6368; font-size: 14px;">If you didn't request this, you can safely ignore this email. Your password will remain unchanged.</p>
        <p style="color: #5f6368; font-size: 14px;">- The NiftyFlow Team</p>
    </div>
    """
    
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Reset your NiftyFlow password"
    msg["From"] = f"NiftyFlow <{settings.SMTP_USER}>"
    msg["To"] = to_email
    
    part = MIMEText(html_content, "html")
    msg.attach(part)
    
    try:
        # Connect to Gmail's SMTP server on port 465 using SSL
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"Password reset email sent to {to_email}")
        print(f"\n[EMAIL SENT] Password reset email successfully dispatched to {to_email} via Gmail SMTP.\n")
    except Exception as e:
        logger.error(f"Failed to send email via Gmail: {e}")
        print(f"\n[FALLBACK] Failed to send email via Gmail. Token for {to_email}: {token}\n")
