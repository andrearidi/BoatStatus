import streamlit as st
from supabase_client import init_supabase, sign_in, sign_out, get_user

# Initialize Supabase client
supabase = init_supabase()

def login():
    st.title("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        try:
            response = sign_in(supabase, email, password)
            st.session_state.user = response.user
            st.success("Logged in successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"Login failed: {str(e)}")

def logout():
    sign_out(supabase)
    st.session_state.user = None
    st.rerun()

def main():
    if 'user' not in st.session_state or st.session_state.user is None:
        login()
        return

    st.title("Battery Status and Boat Positions Dashboard")
    st.sidebar.button("Logout", on_click=logout)

    st.write("Welcome to the Battery Status and Boat Positions Dashboard!")
    st.write("Please select a page from the sidebar to view specific information.")

if __name__ == '__main__':
    main()
