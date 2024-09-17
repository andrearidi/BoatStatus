import streamlit as st
import pandas as pd
import altair as alt
from supabase_client import init_supabase
from scipy import stats
import numpy as np
from datetime import datetime, timedelta
import pydeck as pdk

def main():
    st.title("Battery Status and Boat Positions Dashboard")

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
        return

    # Fetch data from the BatteryStatus table
    def load_battery_data(start_date, end_date):
        try:
            response = supabase.table('BatteryStatus').select('*').gte('created_at', start_date.isoformat()).lte('created_at', (end_date + timedelta(days=1)).isoformat()).execute()
            data = response.data  # Extract data from the response
            return pd.DataFrame(data)
        except Exception as e:
            st.error(f"Error fetching battery data: {str(e)}")
            return pd.DataFrame()

    # Fetch data from the BoatPositions table
    def load_boat_positions(start_date, end_date):
        try:
            response = supabase.table('BoatPositions').select('*').gte('created_at', start_date.isoformat()).lte('created_at', (end_date + timedelta(days=1)).isoformat()).execute()
            data = response.data  # Extract data from the response
            return pd.DataFrame(data)
        except Exception as e:
            st.error(f"Error fetching boat positions: {str(e)}")
            return pd.DataFrame()

    # Load data for the selected range or on first load
    if st.session_state.show_today or st.session_state.apply_custom_range or st.session_state.first_load:
        df_battery = load_battery_data(start_date, end_date)
        df_boat_positions = load_boat_positions(start_date, end_date)

        # Battery Status Section
        st.header("Battery Status")

        # Plot Voltage over time using Altair
        if not df_battery.empty and 'Voltage' in df_battery.columns and 'created_at' in df_battery.columns:
            # Make created_at timezone-aware (assuming data is in UTC)
            df_battery['created_at'] = pd.to_datetime(df_battery['created_at'], utc=True)
            df_battery.sort_values('created_at', inplace=True)

            # Compute min and max voltage
            min_voltage = df_battery['Voltage'].min()
            max_voltage = df_battery['Voltage'].max()

            # Calculate y-axis limits with 1% extension
            y_min = min_voltage - 0.01 * abs(min_voltage)
            y_max = max_voltage + 0.01 * abs(max_voltage)

            # Handle cases where min_voltage == max_voltage (flat line)
            if min_voltage == max_voltage:
                y_min = min_voltage - 0.01 * abs(min_voltage)
                y_max = max_voltage + 0.01 * abs(max_voltage)
                # If min_voltage is zero, set default y-axis limits
                if min_voltage == 0:
                    y_min = -1
                    y_max = 1

            # Linear interpolation for missing data
            df_battery['Voltage'] = df_battery['Voltage'].interpolate(method='linear')

            # Create Altair chart with dynamic y-axis limits and custom X-axis label
            chart = alt.Chart(df_battery).mark_line().encode(
                x=alt.X('created_at:T', axis=alt.Axis(title='Time')),
                y=alt.Y('Voltage:Q', scale=alt.Scale(domain=[y_min, y_max])),
                tooltip=['created_at', 'Voltage']
            ).properties(
                title='Voltage Over Time (Auto-scaled Y-axis)'
            )

            st.altair_chart(chart, use_container_width=True)

            # Linear regression to predict when Voltage will reach 12V
            # Convert datetime to timestamp (in seconds) for linear regression
            df_battery['timestamp'] = df_battery['created_at'].apply(lambda x: x.timestamp())

            # Fit a linear regression model on the data
            slope, intercept, r_value, p_value, std_err = stats.linregress(df_battery['timestamp'], df_battery['Voltage'])

            # Define a function to predict the timestamp when voltage will be 12V
            def predict_time_for_voltage(target_voltage):
                if slope != 0:
                    target_timestamp = (target_voltage - intercept) / slope
                    return pd.to_datetime(target_timestamp, unit='s', utc=True)  # Ensure timezone-aware
                else:
                    return None

            # Forecast when the voltage will reach 12V
            forecast_time = predict_time_for_voltage(12)

            # Compare forecast_time with timezone-aware max 'created_at'
            if forecast_time is not None and forecast_time > df_battery['created_at'].max():
                time_difference = forecast_time - df_battery['created_at'].max()
                days_to_reach_12v = time_difference.days + time_difference.seconds / 86400  # Convert seconds to days

                st.success(f"The voltage is forecasted to reach 12V on {forecast_time.strftime('%Y-%m-%d %H:%M:%S')} UTC.")
                st.info(f"It will take approximately {days_to_reach_12v:.2f} days to reach 12V.")
            else:
                st.warning("Insufficient data or voltage will not reach 12V based on current trend.")
        else:
            st.warning("No battery data available to plot for the selected date range.")

        # Boat Positions Section
        st.header("Boat Positions")

        if not df_boat_positions.empty and 'Lat' in df_boat_positions.columns and 'Long' in df_boat_positions.columns:
            # Sort boat positions by time
            df_boat_positions['created_at'] = pd.to_datetime(df_boat_positions['created_at'], utc=True)
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
        st.info("Please select a date range and click 'Apply Custom Range' or click 'Show Today's Data' to view the dashboard.")

    # Set first_load to False after the first execution
    st.session_state.first_load = False

if __name__ == '__main__':
    main()
