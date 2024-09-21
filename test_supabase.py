import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

def get_supabase_client() -> Client:
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_KEY")
    print(f"Supabase URL: {url}")
    print(f"Supabase Key: {key[:5]}...{key[-5:]}")
    if not url or not key:
        raise ValueError("Supabase URL or Key is missing from environment variables")
    return create_client(url, key)

def test_supabase_connection():
    try:
        client = get_supabase_client()
        print("Supabase client initialized successfully")

        # Test fetching data from BilgePumpStatus
        response = client.table('BilgePumpStatus').select('*').limit(5).execute()
        print(f"Bilge pump data fetched: {len(response.data)} records")
        print("First few records:")
        for record in response.data:
            print(record)

        # Test fetching data from BatteryStatus
        response = client.table('BatteryStatus').select('*').limit(5).execute()
        print(f"Battery data fetched: {len(response.data)} records")
        print("First few records:")
        for record in response.data:
            print(record)

        # Test fetching data from BoatPositions
        response = client.table('BoatPositions').select('*').limit(5).execute()
        print(f"Boat positions fetched: {len(response.data)} records")
        print("First few records:")
        for record in response.data:
            print(record)

    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_supabase_connection()