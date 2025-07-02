import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

from dotenv import load_dotenv
from twilio.rest import Client

load_dotenv()

logger = logging.getLogger(__name__)


def send_message(message: str) -> None:
    if os.environ.get("TWILIO_ACCOUNT_SID"):
        send_twilio_message(message)
    else:
        send_email_message(message)


def send_email_message(message: str) -> None:
    """Send an email notification with the provided message."""
    smtp_server = os.environ.get("EMAIL_SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.environ.get("EMAIL_SMTP_PORT", "587"))
    email_username = os.environ["EMAIL_USERNAME"]
    email_password = os.environ["EMAIL_PASSWORD"]
    send_from_email = os.environ["EMAIL_FROM"]
    send_to_email = os.environ["EMAIL_TO"]

    msg = MIMEMultipart()
    msg["From"] = send_from_email
    msg["To"] = send_to_email
    msg["Subject"] = "Campsite Notification"

    msg.attach(MIMEText(message, "plain"))

    logger.info(f"Sending email to {send_to_email}...")
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()  # Encrypt the connection
        server.login(email_username, email_password)
        server.send_message(msg)
    logger.info(f"Sent email to {send_to_email}")


def send_twilio_message(message: str) -> None:
    """Send SMS notifications with the provided message to multiple recipients."""
    account_sid = os.environ["TWILIO_ACCOUNT_SID"]
    auth_token = os.environ["TWILIO_AUTH_TOKEN"]
    from_number = os.environ["TWILIO_FROM_NUMBER"]
    to_numbers = os.environ.get("TWILIO_TO_NUMBERS", "").split(",")

    if not to_numbers or to_numbers[0] == "":
        raise ValueError("No recipient phone numbers configured")

    client = Client(account_sid, auth_token)

    for number in to_numbers:
        number = number.strip()  # Remove any whitespace
        try:
            logger.info(f"Sending SMS to {number}...")
            message_obj = client.messages.create(
                body=message, from_=from_number, to=number
            )
            logger.info(f"Sent SMS to {number}, SID: {message_obj.sid}")
        except Exception as e:
            logger.error(f"Failed to send SMS to {number}: {str(e)}")
