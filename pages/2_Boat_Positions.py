import streamlit as st
import pandas as pd
import pydeck as pdk
from datetime import datetime, timedelta
from supabase_client import init_supabase

st.title("Boat Positions")

# Initialize Supabase client
supabase = init_supabase()

# Date range selection
st.sidebar.header("Date Range Selection")
today = datetime.now().date()

# Initialize session state
if 'show_today' not in st.session_state:
    st.session_state.show_today = False
if 'apply_custom_range' not in st.session_state:
    st.session_state.apply_custom_range = False
if 'start_date' not in st.session_state:
    st.session_state.start_date = today - timedelta(days=7)
if 'end_date' not in st.session_state:
    st.session_state.end_date = today
if 'first_load' not in st.session_state:
    st.session_state.first_load = True

# Show Today's Data button
if st.sidebar.button("Show Today's Data"):
    st.session_state.show_today = True
    st.session_state.apply_custom_range = False
    st.session_state.first_load = False

# Date input boxes (always visible)
start_date = st.sidebar.date_input("Start Date", st.session_state.start_date)
end_date = st.sidebar.date_input("End Date", st.session_state.end_date)

# Apply Custom Range button
if st.sidebar.button("Apply Custom Range"):
    st.session_state.apply_custom_range = True
    st.session_state.show_today = False
    st.session_state.first_load = False
    st.session_state.start_date = start_date
    st.session_state.end_date = end_date

# Set date range based on the current state
if st.session_state.show_today:
    start_date = today
    end_date = today
    st.sidebar.info("Showing today's data. Use the date inputs and 'Apply Custom Range' to select a custom range.")
elif st.session_state.apply_custom_range:
    start_date = st.session_state.start_date
    end_date = st.session_state.end_date
    st.sidebar.info(f"Showing data from {start_date} to {end_date}. Click 'Show Today's Data' to reset.")
elif st.session_state.first_load:
    st.sidebar.info(f"Showing data for the last week by default. Use the date inputs and 'Apply Custom Range' to select a custom range.")
else:
    st.sidebar.info("Select a date range and click 'Apply Custom Range' to update the data.")

if start_date > end_date:
    st.error("Error: End date must fall after start date.")
    st.stop()

# Fetch data from the BoatPositions table
def load_boat_positions(start_date, end_date):
    try:
        response = supabase.fetch_boat_positions()
        df = pd.DataFrame(response)
        df['created_at'] = pd.to_datetime(df['created_at'], utc=True)
        return df[(df['created_at'].dt.date >= start_date) & (df['created_at'].dt.date <= end_date)]
    except Exception as e:
        st.error(f"Error fetching boat positions: {str(e)}")
        return pd.DataFrame()

# Load data for the selected range or on first load
if st.session_state.show_today or st.session_state.apply_custom_range or st.session_state.first_load:
    df_boat_positions = load_boat_positions(start_date, end_date)

    if not df_boat_positions.empty and 'Lat' in df_boat_positions.columns and 'Long' in df_boat_positions.columns:
        # Sort boat positions by time
        df_boat_positions = df_boat_positions.sort_values('created_at')

        # Prepare data for map
        map_data = df_boat_positions[['Lat', 'Long', 'Accuracy', 'created_at']].dropna()
        
        # Create color column (red for all points, blue for the last one)
        colors = [[255, 0, 0] for _ in range(len(map_data) - 1)] + [[0, 0, 255]]
        map_data['color'] = colors

        # Create PyDeck layer
        layer = pdk.Layer(
            "ScatterplotLayer",
            map_data,
            get_position=['Long', 'Lat'],
            get_color='color',
            get_radius='Accuracy',
            radius_scale=2,
            radius_min_pixels=3,
            radius_max_pixels=30,
        )

        # Set the viewport location
        view_state = pdk.ViewState(
            longitude=map_data['Long'].mean(),
            latitude=map_data['Lat'].mean(),
            zoom=11,
            pitch=0)

        # Render the map
        st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state, map_style='mapbox://styles/mapbox/light-v9'))

    else:
        st.warning("No boat position data available to display for the selected date range.")
else:
    st.info("Please select a date range and click 'Apply Custom Range' or click 'Show Today's Data' to view the boat positions.")

# Set first_load to False after the first execution
st.session_state.first_load = False