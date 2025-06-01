
from dotenv import load_dotenv
import os
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

DATABASE_URL = os.getenv("DATABASE_URL")
TWILIO_ACCOUNT_SID= os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN= os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER= os.getenv("TWILIO_PHONE_NUMBER")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
