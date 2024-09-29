# Test script for fetch_battery_data function
from supabase_client import init_supabase

def test_fetch_battery_data():
    supabase = init_supabase()
    battery_data = supabase.fetch_battery_data()
    
    print(f"Total number of records retrieved: {len(battery_data)}")
    
    if len(battery_data) > 0:
        print("\nFirst record:")
        print(battery_data[0])
        
        if len(battery_data) > 1:
            print("\nLast record:")
            print(battery_data[-1])
    
    print("\nData retrieval test completed.")
    print("If the number of records matches your expectation and you can see both first and last records,")
    print("it's likely that all data has been successfully retrieved.")

if __name__ == "__main__":
    test_fetch_battery_data()