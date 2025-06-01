from twilio.rest import Client
from app.config import *

client = Client(ACCOUNT_SID, AUTH_TOKEN)

def send_whatsapp_message(message, phone_number):
    message = client.messages.create(
        from_=TWILIO_WHATSAPP_NUMBER,
        body=message,
        to=f"whatsapp:{phone_number}"
    )
