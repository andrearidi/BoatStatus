import streamlit as st
import pandas as pd
from supabase_client import init_supabase

def main():
    st.title("Bilge Pump Status")
    
    supabase = init_supabase()
    
    # Fetch bilge pump data
    bilge_pump_data = supabase.fetch_bilge_pump_data()
    
    if bilge_pump_data:
        df = pd.DataFrame(bilge_pump_data)
        df['created_at'] = pd.to_datetime(df['created_at'])
        df = df.sort_values('created_at', ascending=False)
        
        st.subheader("Recent Bilge Pump Actions (Last 10 Entries)")
        
        # Display only the 10 most recent entries, but reverse the order
        recent_data = df.head(10).iloc[::-1]
        
        # Format the 'created_at' column to display only date and time
        recent_data['created_at'] = recent_data['created_at'].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Display the table with formatted columns
        st.table(recent_data[['created_at', 'Status', 'El_Time']].rename(columns={
            'created_at': 'Timestamp',
            'Status': 'Pump Status',
            'El_Time': 'Duration (seconds)'
        }))
        
    else:
        st.warning("No bilge pump data available.")

if __name__ == "__main__":
    main()