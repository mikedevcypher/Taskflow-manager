# src/task_management/auth/email.py

import logging
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app, render_template
from threading import Thread

logger = logging.getLogger(__name__)

def send_async_email(app, msg):
    with app.app_context():
        try:
            # Get email settings from environment variables or config
            smtp_host = current_app.config.get('SMTP_HOST', os.environ.get('SMTP_HOST'))
            smtp_port = int(current_app.config.get('SMTP_PORT', os.environ.get('SMTP_PORT', 587)))
            smtp_user = current_app.config.get('SMTP_USER', os.environ.get('SMTP_USER'))
            smtp_password = current_app.config.get('SMTP_PASSWORD', os.environ.get('SMTP_PASSWORD'))
            use_tls = current_app.config.get('SMTP_USE_TLS', True)
            
            # If SMTP settings are not configured, log the email
            if not all([smtp_host, smtp_user, smtp_password]):
                logger.warning("SMTP not configured. Email would have been sent:")
                logger.info(f"To: {msg['To']}")
                logger.info(f"Subject: {msg['Subject']}")
                
                # Get email body from the message
                body = ""
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode()
                        break
                
                logger.info(f"Body: {body}")
                return
            
            # Send email via SMTP
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                if use_tls:
                    server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
                
            logger.info(f"Email sent to {msg['To']}")
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")

def send_email(recipient, subject, body, html=None, sender=None, attachments=None):
    """
    Send email 
    """
    # Get sender from config or environment
    if not sender:
        sender = current_app.config.get('MAIL_DEFAULT_SENDER', 
                 os.environ.get('FROM_EMAIL', 'taskflow@example.com'))
    
    # Create message
    msg = MIMEMultipart('alternative')
    msg['From'] = sender
    msg['To'] = recipient
    msg['Subject'] = subject
    
    # Attach plain text body
    msg.attach(MIMEText(body, 'plain'))
    
    # Attach HTML body if provided
    if html:
        msg.attach(MIMEText(html, 'html'))
    
    # Add attachments if provided
    if attachments:
        for attachment in attachments:
            filename, content_type, data = attachment
            attachment_part = MIMEText(data, 'base64')
            attachment_part['Content-Disposition'] = f'attachment; filename="{filename}"'
            attachment_part['Content-Type'] = content_type
            msg.attach(attachment_part)
    
    # Send email asynchronously
    thread = Thread(target=send_async_email, args=(current_app._get_current_object(), msg))
    thread.start()
    
    return True

def send_password_reset_email(user, reset_url):
    """
    Send password reset email with token link.

    """
    subject = "TaskFlow Password Reset"
    
    # Render plain text email
    text_body = f"""
Hello {user.username},

We received a request to reset your password for your TaskFlow account.
Please click the following link to reset your password:

{reset_url}

If you didn't request this password reset, you can safely ignore this email.
This password reset link will expire in 24 hours.

Best regards,
The TaskFlow Team
"""

    # Render HTML email using template
    html_body = render_template('email/reset_password.html', 
                               username=user.username, 
                               reset_url=reset_url)
    
    return send_email(
        recipient=user.email_id,
        subject=subject,
        body=text_body,
        html=html_body
    )