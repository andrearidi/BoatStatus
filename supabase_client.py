import os
from supabase import create_client, Client
import streamlit as st
#from dotenv import load_dotenv

# Load environment variables from .env file
#load_dotenv()

def init_supabase() -> Client:
    #url: str = os.environ.get("SUPABASE_URL")
    #key: str = os.environ.get("SUPABASE_KEY")
    
    supabase: Client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    return supabase

def sign_up(supabase: Client, email: str, password: str):
    return supabase.auth.sign_up({"email": email, "password": password})

def sign_in(supabase: Client, email: str, password: str):
    return supabase.auth.sign_in_with_password({"email": email, "password": password})

def sign_out(supabase: Client):
    return supabase.auth.sign_out()

def get_user(supabase: Client):
    return supabase.auth.get_user()
