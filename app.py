import streamlit as st
import pandas as pd
import altair as alt
from supabase_client import init_supabase
from scipy import stats
import numpy as np

def main():
    st.title("Battery Status and Boat Positions Dashboard")

    # Initialize Supabase client
    supabase = init_supabase()

    # Fetch data from the BatteryStatus table
    def load_battery_data():
        try:
            response = supabase.table('BatteryStatus').select('*').execute()
            data = response.data  # Extract data from the response
            return pd.DataFrame(data)
        except Exception as e:
            st.error(f"Error fetching battery data: {str(e)}")
            return pd.DataFrame()

    # Fetch data from the BoatPositions table
    def load_boat_positions():
        try:
            response = supabase.table('BoatPositions').select('*').execute()
            data = response.data  # Extract data from the response
            return pd.DataFrame(data)
        except Exception as e:
            st.error(f"Error fetching boat positions: {str(e)}")
            return pd.DataFrame()

    df_battery = load_battery_data()
    df_boat_positions = load_boat_positions()

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
        st.warning("No battery data available to plot.")

    # Boat Positions Section
    st.header("Boat Positions")

    if not df_boat_positions.empty and 'Lat' in df_boat_positions.columns and 'Long' in df_boat_positions.columns:
        # Prepare data for map
        map_data = df_boat_positions[['Lat', 'Long', 'Accuracy']].dropna()

        # Display map with accuracy information
        st.map(map_data.assign(size=map_data['Accuracy']), latitude='Lat', longitude='Long', size='size')

        # Calculate and display statistics
        st.subheader("Position Statistics")
        avg_accuracy = df_boat_positions['Accuracy'].mean()
        max_accuracy = df_boat_positions['Accuracy'].max()
        min_accuracy = df_boat_positions['Accuracy'].min()

        st.write(f"Average Accuracy: {avg_accuracy:.2f} meters")
        st.write(f"Max Accuracy: {max_accuracy:.2f} meters")
        st.write(f"Min Accuracy: {min_accuracy:.2f} meters")

        # Display the most recent position
        st.subheader("Most Recent Position")
        most_recent = df_boat_positions.sort_values('created_at', ascending=False).iloc[0]
        st.write(f"Latitude: {most_recent['Lat']:.6f}")
        st.write(f"Longitude: {most_recent['Long']:.6f}")
        st.write(f"Accuracy: {most_recent['Accuracy']:.2f} meters")
        st.write(f"Time: {most_recent['created_at']}")

    else:
        st.warning("No boat position data available to display.")

if __name__ == '__main__':
    main()
