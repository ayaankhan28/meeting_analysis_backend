from twilio.rest import Client
from app.config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

def send_whatsapp_message(message, phone_number):
    message = client.messages.create(
        from_=TWILIO_PHONE_NUMBER,
        body=message,
        to=f"whatsapp:{phone_number}"
    )

# send_whatsapp_message("Hello, this is a test message", "+919343282801")