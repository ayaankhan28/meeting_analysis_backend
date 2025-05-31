from twilio.rest import Client
from backend.app.config import *
# Twilio credentials (replace with your actual credentials)

# Initialize Twilio client
client = Client(ACCOUNT_SID, AUTH_TOKEN)

# Send WhatsApp message
def send_whatsapp_message(message, phone_number):
    message = client.messages.create(
        from_=TWILIO_WHATSAPP_NUMBER,
        body=message,
        to=f"whatsapp:{phone_number}"
    )

    print(f"Message sent! ID: {message.sid}")