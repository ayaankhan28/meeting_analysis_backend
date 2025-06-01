import os
from supabase import create_client, Client
from app.config import SUPABASE_URL, SUPABASE_KEY


if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError('Supabase credentials not found in environment variables')

# Create Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Function to get database client
def get_db() -> Client:
    return supabase