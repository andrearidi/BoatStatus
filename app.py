import streamlit as st
import time

# Force reload of supabase_client
import importlib
import supabase_client
importlib.reload(supabase_client)

from supabase_client import init_supabase

# Initialize Supabase client
supabase = init_supabase()

def login():
    st.title("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        try:
            response = supabase.sign_in(email, password)
            st.session_state.user = response.user
            st.success("Logged in successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"Login failed: {str(e)}")

def logout():
    supabase.sign_out()
    st.session_state.user = None
    st.rerun()

def main():
    st.write(f"Last reload: {time.time()}")  # Add this line to show when the app was last reloaded
    
    if 'user' not in st.session_state or st.session_state.user is None:
        login()
        return

    st.title("Battery Status, Boat Positions, and Bilge Pump Dashboard")
    st.sidebar.button("Logout", on_click=logout)

    st.write("Welcome to the Dashboard!")
    st.write("Please select a page from the sidebar to view specific information.")

if __name__ == '__main__':
    main()
