import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)


def send_message(message: str) -> None:
    """Send an email notification with the provided message."""
    # Get email configuration from environment variables
    smtp_server = os.environ.get("EMAIL_SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.environ.get("EMAIL_SMTP_PORT", "587"))
    email_username = os.environ["EMAIL_USERNAME"]
    email_password = os.environ["EMAIL_PASSWORD"]
    send_from_email = os.environ["EMAIL_FROM"]
    send_to_email = os.environ["EMAIL_TO"]

    # Create the email message
    msg = MIMEMultipart()
    msg["From"] = send_from_email
    msg["To"] = send_to_email
    msg["Subject"] = "Campsite Notification"

    # Add the message body
    msg.attach(MIMEText(message, "plain"))

    # Connect to the SMTP server and send the email
    logger.info(f"Sending email to {send_to_email}...")
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()  # Encrypt the connection
        server.login(email_username, email_password)
        server.send_message(msg)
    logger.info(f"Sent email to {send_to_email}")
