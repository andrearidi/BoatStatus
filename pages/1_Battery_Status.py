import streamlit as st
import pandas as pd
import altair as alt
from scipy import stats
from datetime import datetime, timedelta
from supabase_client import init_supabase
import pytz

st.title("Battery Status")

# Initialize Supabase client
supabase = init_supabase()

# Date range selection
st.sidebar.header("Date Range Selection")
now = datetime.now(pytz.utc)
today = now.date()

# Initialize session state
if 'show_recent' not in st.session_state:
    st.session_state.show_recent = True
if 'apply_custom_range' not in st.session_state:
    st.session_state.apply_custom_range = False
if 'start_date' not in st.session_state:
    st.session_state.start_date = now - timedelta(hours=24)
if 'end_date' not in st.session_state:
    st.session_state.end_date = now
if 'first_load' not in st.session_state:
    st.session_state.first_load = True

# Show Recent Data button
if st.sidebar.button("Show Recent Data (Last 24 Hours)"):
    st.session_state.show_recent = True
    st.session_state.apply_custom_range = False
    st.session_state.first_load = False

# Date input boxes (always visible)
start_date = st.sidebar.date_input("Start Date", st.session_state.start_date)
end_date = st.sidebar.date_input("End Date", st.session_state.end_date)

# Apply Custom Range button
if st.sidebar.button("Apply Custom Range"):
    st.session_state.apply_custom_range = True
    st.session_state.show_recent = False
    st.session_state.first_load = False
    st.session_state.start_date = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=pytz.utc)
    st.session_state.end_date = datetime.combine(end_date, datetime.max.time()).replace(tzinfo=pytz.utc)

# Set date range based on the current state
if st.session_state.show_recent:
    start_date = now - timedelta(hours=24)
    end_date = now
    st.sidebar.info("Showing last 24 hours of data. Use the date inputs and 'Apply Custom Range' to select a custom range.")
elif st.session_state.apply_custom_range:
    start_date = st.session_state.start_date
    end_date = st.session_state.end_date
    st.sidebar.info(f"Showing data from {start_date.strftime('%Y-%m-%d %H:%M:%S')} to {end_date.strftime('%Y-%m-%d %H:%M:%S')} UTC. Click 'Show Recent Data' to reset.")
elif st.session_state.first_load:
    start_date = now - timedelta(hours=24)
    end_date = now
    st.sidebar.info(f"Showing data for the last 24 hours by default. Use the date inputs and 'Apply Custom Range' to select a custom range.")
else:
    st.sidebar.info("Select a date range and click 'Apply Custom Range' to update the data.")

if start_date > end_date:
    st.error("Error: End date must fall after start date.")
    st.stop()

# Fetch data from the BatteryStatus table
def load_battery_data(start_date, end_date):
    try:
        response = supabase.fetch_battery_data()
        df = pd.DataFrame(response)
        # Use format='ISO8601' to handle the datetime format from Supabase
        df['created_at'] = pd.to_datetime(df['created_at'], format='ISO8601', utc=True)
        return df[(df['created_at'] >= start_date) & (df['created_at'] <= end_date)]
    except Exception as e:
        st.error(f"Error fetching battery data: {str(e)}")
        return pd.DataFrame()

# Load data for the selected range or on first load
if st.session_state.show_recent or st.session_state.apply_custom_range or st.session_state.first_load:
    df_battery = load_battery_data(start_date, end_date)

    # Plot Voltage over time using Altair
    if not df_battery.empty and 'Voltage' in df_battery.columns and 'created_at' in df_battery.columns:
        # Sort values by created_at
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
        line = alt.Chart(df_battery).mark_line().encode(
            x=alt.X('created_at:T', axis=alt.Axis(title='Time (UTC)', format='%Y-%m-%d %H:%M:%S')),
            y=alt.Y('Voltage:Q', scale=alt.Scale(domain=[y_min, y_max])),
            tooltip=[
                alt.Tooltip('created_at:T', title='Time (UTC)', format='%Y-%m-%d %H:%M:%S'),
                alt.Tooltip('Voltage:Q', title='Voltage', format='.2f')
            ]
        )

        # Add points to highlight individual data points
        points = alt.Chart(df_battery).mark_circle(size=60).encode(
            x='created_at:T',
            y='Voltage:Q',
            tooltip=[
                alt.Tooltip('created_at:T', title='Time (UTC)', format='%Y-%m-%d %H:%M:%S'),
                alt.Tooltip('Voltage:Q', title='Voltage', format='.2f')
            ]
        )

        # Combine line and points
        chart = (line + points).properties(
            title='Voltage Over Time (Auto-scaled Y-axis)'
        ).interactive()

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
                return pd.to_datetime(target_timestamp, unit='s', utc=True)
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

        # Display the most recent voltage reading
        latest_reading = df_battery.iloc[-1]
        st.info(f"Latest voltage reading: {latest_reading['Voltage']:.2f}V at {latest_reading['created_at'].strftime('%Y-%m-%d %H:%M:%S')} UTC")
    else:
        st.warning("No battery data available to plot for the selected date range.")
else:
    st.info("Please select a date range and click 'Apply Custom Range' or click 'Show Recent Data' to view the battery status.")

# Set first_load to False after the first execution
st.session_state.first_load = False
