import os
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime, timedelta

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

class SupabaseClient:
    def __init__(self):
        self.client = get_supabase_client()
        print("Supabase client initialized successfully")

    def fetch_battery_data(self):
        try:
            all_data = []
            page = 1
            page_size = 1000  # Adjust this value based on your needs

            while True:
                response = self.client.from_('BatteryStatus').select('*').range((page - 1) * page_size, page * page_size - 1).execute()
                data = response.data
                all_data.extend(data)

                if len(data) < page_size:
                    break

                page += 1

            print(f"Battery data fetched: {len(all_data)} records")
            return all_data
        except Exception as e:
            print(f"Error fetching battery data: {str(e)}")
            return []

    def fetch_boat_positions(self):
        try:
            response = self.client.from_('BoatPositions').select('*').execute()
            print(f"Boat positions fetched: {len(response.data)} records")
            return response.data
        except Exception as e:
            print(f"Error fetching boat positions: {str(e)}")
            return []

    def fetch_bilge_pump_data(self):
        try:
            response = self.client.from_('BilgePumpStatus').select('*').execute()
            print(f"Bilge pump data fetched: {len(response.data)} records")
            return response.data
        except Exception as e:
            print(f"Error fetching bilge pump data: {str(e)}")
            return []

    def sign_in(self, email, password):
        try:
            response = self.client.auth.sign_in_with_password({"email": email, "password": password})
            print("Sign in successful")
            return response
        except Exception as e:
            print(f"Error signing in: {str(e)}")
            raise

    def sign_out(self):
        try:
            response = self.client.auth.sign_out()
            print("Sign out successful")
            return response
        except Exception as e:
            print(f"Error signing out: {str(e)}")
            raise

    def get_user(self):
        try:
            user = self.client.auth.get_user()
            print(f"Current user: {user.id if user else 'None'}")
            return user
        except Exception as e:
            print(f"Error getting user: {str(e)}")
            return None

supabase = SupabaseClient()

def init_supabase():
    return supabase
