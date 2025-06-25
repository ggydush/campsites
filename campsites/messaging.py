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


# import os
# from dotenv import load_dotenv
# import logging
# from twilio.rest import Client

# load_dotenv()

# logger = logging.getLogger(__name__)


# def send_message(message: str) -> None:
#     """Send SMS notifications with the provided message to multiple recipients."""
#     # Get Twilio configuration from environment variables
#     account_sid = os.environ["TWILIO_ACCOUNT_SID"]
#     auth_token = os.environ["TWILIO_AUTH_TOKEN"]
#     from_number = os.environ["TWILIO_FROM_NUMBER"]

#     # Get recipient numbers (comma-separated list in env var)
#     to_numbers = os.environ.get("TWILIO_TO_NUMBERS", "").split(",")

#     if not to_numbers or to_numbers[0] == "":
#         logger.error("No recipient phone numbers configured")
#         return

#     # Initialize Twilio client
#     client = Client(account_sid, auth_token)

#     # Send message to each recipient
#     for number in to_numbers:
#         number = number.strip()  # Remove any whitespace
#         try:
#             logger.info(f"Sending SMS to {number}...")
#             message_obj = client.messages.create(
#                 body=message, from_=from_number, to=number
#             )
#             logger.info(f"Sent SMS to {number}, SID: {message_obj.sid}")
#         except Exception as e:
#             logger.error(f"Failed to send SMS to {number}: {str(e)}")
