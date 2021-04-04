import os

from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()


def send_message(
    message: str,
):
    account_sid = os.environ["TWILIO_ACCOUNT_SID"]
    auth_token = os.environ["TWILIO_AUTH_TOKEN"]
    send_from_number = os.environ["TWILIO_FROM_NUMBER"]
    send_to_number = os.environ["TWILIO_TO_NUMBER"]
    client = Client(account_sid, auth_token)
    return client.messages.create(
        body=message,
        from_=send_from_number,
        to=send_to_number,
    )
