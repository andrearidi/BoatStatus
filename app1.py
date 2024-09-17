# app.py

import streamlit as st
import pandas as pd
import altair as alt
import datetime
from dateutil.relativedelta import relativedelta  # For month calculations
from supabase_client import init_supabase
import pytz  # For timezone handling
import pydeck as pdk  # For advanced mapping

def main():
    st.title("Battery Status Dashboard")

    # Initialize Supabase client
    supabase = init_supabase()

    # Fetch data from the BatteryStatus table
    def load_battery_status():
        try:
            response = supabase.table('BatteryStatus').select('*').execute()
            data = response.data  # Extract data from the response
            return pd.DataFrame(data)
        except Exception as e:
            st.error(f"Error fetching battery status data: {str(e)}")
            return pd.DataFrame()

    # Fetch data from the BoatPositions table
    def load_boat_positions():
        try:
            response = supabase.table('BoatPositions').select('*').execute()
            data = response.data  # Extract data from the response
            return pd.DataFrame(data)
        except Exception as e:
            st.error(f"Error fetching boat positions data: {str(e)}")
            return pd.DataFrame()

    # Load data
    battery_df = load_battery_status()
    boat_df = load_boat_positions()

    # Process and display battery status data
    if not battery_df.empty and 'Voltage' in battery_df.columns and 'created_at' in battery_df.columns:
        battery_df['created_at'] = pd.to_datetime(battery_df['created_at'], errors='coerce')
        battery_df.sort_values('created_at', inplace=True)

        # Add time range selector for battery data
        time_option = st.selectbox('Select Time Range for Battery Data', ['Today', 'This Week', 'Day', 'Week', 'Month'])

        # Set timezone to UTC
        utc = pytz.UTC

        if time_option == 'Today':
            today = datetime.date.today()
            start_date = datetime.datetime.combine(today, datetime.time.min)
            end_date = datetime.datetime.combine(today, datetime.time.max)
            # Localize to UTC
            start_date = utc.localize(start_date)
            end_date = utc.localize(end_date)
        elif time_option == 'This Week':
            today = datetime.date.today()
            start_of_week = today - datetime.timedelta(days=today.weekday())  # Monday
            start_date = datetime.datetime.combine(start_of_week, datetime.time.min)
            end_date = datetime.datetime.combine(today, datetime.time.max)
            # Localize to UTC
            start_date = utc.localize(start_date)
            end_date = utc.localize(end_date)
        elif time_option == 'Day':
            selected_date = st.date_input('Select a date', datetime.date.today(), key='battery_day')
            start_date = datetime.datetime.combine(selected_date, datetime.time.min)
            end_date = datetime.datetime.combine(selected_date, datetime.time.max)
            # Localize to UTC
            start_date = utc.localize(start_date)
            end_date = utc.localize(end_date)
        elif time_option == 'Week':
            selected_date = st.date_input('Select a week (pick a date within the week)', datetime.date.today(), key='battery_week')
            start_of_week = selected_date - datetime.timedelta(days=selected_date.weekday())
            end_of_week = start_of_week + datetime.timedelta(days=6)
            start_date = datetime.datetime.combine(start_of_week, datetime.time.min)
            end_date = datetime.datetime.combine(end_of_week, datetime.time.max)
            # Localize to UTC
            start_date = utc.localize(start_date)
            end_date = utc.localize(end_date)
        elif time_option == 'Month':
            selected_date = st.date_input('Select a month (pick a date within the month)', datetime.date.today(), key='battery_month')
            start_of_month = selected_date.replace(day=1)
            next_month = start_of_month + relativedelta(months=1)
            start_date = datetime.datetime.combine(start_of_month, datetime.time.min)
            end_date = datetime.datetime.combine(next_month, datetime.time.min) - datetime.timedelta(seconds=1)
            # Localize to UTC
            start_date = utc.localize(start_date)
            end_date = utc.localize(end_date)
        else:
            start_date = battery_df['created_at'].min()
            end_date = battery_df['created_at'].max()

        # Filter DataFrame based on the selected date range
        mask = (battery_df['created_at'] >= start_date) & (battery_df['created_at'] <= end_date)
        battery_df = battery_df.loc[mask]

        if not battery_df.empty:
            # Compute min and max voltage
            min_voltage = battery_df['Voltage'].min()
            max_voltage = battery_df['Voltage'].max()

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
            chart = alt.Chart(battery_df).mark_line().encode(
                x=alt.X('created_at:T', axis=alt.Axis(title='Time')),
                y=alt.Y('Voltage:Q', scale=alt.Scale(domain=[y_min, y_max])),
                tooltip=['created_at', 'Voltage']
            ).properties(
                title=f'Voltage Over Time ({time_option})'
            )

            st.altair_chart(chart, use_container_width=True)
        else:
            st.warning("No battery data available for the selected time range.")
    else:
        st.warning("No battery data available to plot.")

    # Process and display boat positions data
    if not boat_df.empty and all(col in boat_df.columns for col in ['Lat', 'Long', 'created_at']):
        st.header("Boat Positions Map")

        # Convert 'created_at' to datetime
        boat_df['created_at'] = pd.to_datetime(boat_df['created_at'], errors='coerce')

        # Drop rows where 'created_at' could not be converted
        boat_df = boat_df.dropna(subset=['created_at'])

        boat_df.sort_values('created_at', inplace=True)

        # Add time range selector for map data
        map_time_option = st.selectbox(
            'Select Time Range for Map',
            ['Today', 'This Week', 'Day', 'Week', 'Month']
        )

        # Set timezone to UTC
        utc = pytz.UTC

        if map_time_option == 'Today':
            today = datetime.date.today()
            map_start_date = datetime.datetime.combine(today, datetime.time.min)
            map_end_date = datetime.datetime.combine(today, datetime.time.max)
            # Localize to UTC
            map_start_date = utc.localize(map_start_date)
            map_end_date = utc.localize(map_end_date)
        elif map_time_option == 'This Week':
            today = datetime.date.today()
            start_of_week = today - datetime.timedelta(days=today.weekday())  # Monday
            map_start_date = datetime.datetime.combine(start_of_week, datetime.time.min)
            map_end_date = datetime.datetime.combine(today, datetime.time.max)
            # Localize to UTC
            map_start_date = utc.localize(map_start_date)
            map_end_date = utc.localize(map_end_date)
        elif map_time_option == 'Day':
            map_selected_date = st.date_input('Select a date for map', datetime.date.today(), key='map_day')
            map_start_date = datetime.datetime.combine(map_selected_date, datetime.time.min)
            map_end_date = datetime.datetime.combine(map_selected_date, datetime.time.max)
            # Localize to UTC
            map_start_date = utc.localize(map_start_date)
            map_end_date = utc.localize(map_end_date)
        elif map_time_option == 'Week':
            map_selected_date = st.date_input('Select a week for map (pick a date within the week)', datetime.date.today(), key='map_week')
            start_of_week = map_selected_date - datetime.timedelta(days=map_selected_date.weekday())
            end_of_week = start_of_week + datetime.timedelta(days=6)
            map_start_date = datetime.datetime.combine(start_of_week, datetime.time.min)
            map_end_date = datetime.datetime.combine(end_of_week, datetime.time.max)
            # Localize to UTC
            map_start_date = utc.localize(map_start_date)
            map_end_date = utc.localize(map_end_date)
        elif map_time_option == 'Month':
            map_selected_date = st.date_input('Select a month for map (pick a date within the month)', datetime.date.today(), key='map_month')
            start_of_month = map_selected_date.replace(day=1)
            next_month = start_of_month + relativedelta(months=1)
            map_start_date = datetime.datetime.combine(start_of_month, datetime.time.min)
            map_end_date = datetime.datetime.combine(next_month, datetime.time.min) - datetime.timedelta(seconds=1)
            # Localize to UTC
            map_start_date = utc.localize(map_start_date)
            map_end_date = utc.localize(map_end_date)
        else:
            map_start_date = boat_df['created_at'].min()
            map_end_date = boat_df['created_at'].max()

        # Filter DataFrame based on the selected date range
        map_mask = (boat_df['created_at'] >= map_start_date) & (boat_df['created_at'] <= map_end_date)
        boat_df_filtered = boat_df.loc[map_mask].copy()  # <-- Added .copy() here

        # Debug: Display the number of records before and after filtering
        st.write(f"Total boat position records before filtering: {len(boat_df)}")
        st.write(f"Total boat position records after filtering: {len(boat_df_filtered)}")

        if not boat_df_filtered.empty:
            # Rename columns for PyDeck
            boat_df_filtered = boat_df_filtered.rename(columns={'Lat': 'lat', 'Long': 'lon'})

            # Convert lat and lon to numeric
            boat_df_filtered['lat'] = pd.to_numeric(boat_df_filtered['lat'], errors='coerce')
            boat_df_filtered['lon'] = pd.to_numeric(boat_df_filtered['lon'], errors='coerce')

            # Drop rows with missing or invalid lat/lon
            boat_df_filtered = boat_df_filtered.dropna(subset=['lat', 'lon'])

            # Debug: Display the DataFrame after processing
            st.write("Boat Positions DataFrame after processing:")
            st.write(boat_df_filtered[['lat', 'lon', 'created_at']].head())

            # Check if there are still records after dropping NaNs
            if not boat_df_filtered.empty:
                # Define the layer
                layer = pdk.Layer(
                    'ScatterplotLayer',
                    data=boat_df_filtered,
                    get_position='[lon, lat]',
                    get_fill_color='[200, 30, 0, 160]',
                    get_radius=100,
                    pickable=True,
                )

                # Calculate the center of the map
                mid_lon = boat_df_filtered['lon'].mean()
                mid_lat = boat_df_filtered['lat'].mean()

                # Check for NaN values in mid_lon and mid_lat
                if pd.isna(mid_lon) or pd.isna(mid_lat):
                    st.error("Cannot compute map center due to missing longitude or latitude values.")
                else:
                    # Set the initial view state
                    view_state = pdk.ViewState(
                        longitude=mid_lon,
                        latitude=mid_lat,
                        zoom=10,
                        pitch=0,
                    )

                    # Create the deck.gl map
                    r = pdk.Deck(
                        layers=[layer],
                        initial_view_state=view_state,
                        tooltip={"text": "Latitude: {lat}\nLongitude: {lon}\nTime: {created_at}"},
                    )

                    st.pydeck_chart(r)
            else:
                st.warning("No valid boat positions available after processing.")
        else:
            st.warning("No boat positions available for the selected time range.")
    else:
        st.warning("No boat position data available.")

if __name__ == '__main__':
    main()
