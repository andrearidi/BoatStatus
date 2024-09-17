import os
from supabase import create_client, Client
from dotenv import load_dotenv  # Import the dotenv package

# Load environment variables from .env file
load_dotenv()

def init_supabase() -> Client:
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_KEY")
    supabase: Client = create_client(url, key)
    return supabase
