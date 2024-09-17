# app.py

import streamlit as st
import pandas as pd
import altair as alt  # Import Altair for plotting
from supabase_client import init_supabase

def main():
    st.title("Battery Status Dashboard")

    # Initialize Supabase client
    supabase = init_supabase()

    # Fetch data from the BatteryStatus table
    def load_data():
        try:
            response = supabase.table('BatteryStatus').select('*').execute()
            data = response.data  # Extract data from the response
            return pd.DataFrame(data)
        except Exception as e:
            st.error(f"Error fetching data: {str(e)}")
            return pd.DataFrame()

    df = load_data()

    # The data table display has been removed as per your request

    # Plot Voltage over time using Altair
    if not df.empty and 'Voltage' in df.columns and 'created_at' in df.columns:
        df['created_at'] = pd.to_datetime(df['created_at'])
        df.sort_values('created_at', inplace=True)

        # Compute min and max voltage
        min_voltage = df['Voltage'].min()
        max_voltage = df['Voltage'].max()

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

        # Create Altair chart with dynamic y-axis limits and custom X-axis label
        chart = alt.Chart(df).mark_line().encode(
            x=alt.X('created_at:T', axis=alt.Axis(title='Time')),
            y=alt.Y('Voltage:Q', scale=alt.Scale(domain=[y_min, y_max])),
            tooltip=['created_at', 'Voltage']
        ).properties(
            title='Voltage Over Time (Auto-scaled Y-axis)'
        )

        st.altair_chart(chart, use_container_width=True)
    else:
        st.warning("No data available to plot.")

    # The data entry form has been removed as per your request

if __name__ == '__main__':
    main()

