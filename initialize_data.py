#!/usr/bin/env python3
# initialize_data.py - Initialize and test the data collection system

import os
import sys
import time
import json
from pathlib import Path

# Add code directory to path
code_dir = Path(__file__).parent / "code"
sys.path.insert(0, str(code_dir))

def test_api_connection():
    """Test TomTom API connection"""
    print("Testing TomTom API connection...")
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv('TOMTOM_API_KEY')
        if not api_key:
            print("TomTom API key not found in environment variables")
            return False
        
        import requests
        
        # Test with a simple geocoding request
        url = "https://api.tomtom.com/search/2/search/Providence, RI.json"
        params = {'key': api_key, 'limit': 1}
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            print("TomTom API connection successful")
            return True
        else:
            print(f"TomTom API error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Error testing API connection: {e}")
        return False

def initialize_database():
    """Initialize the database and create tables"""
    print("🗄️ Initializing database...")
    
    try:
        from utils.database import TrafficDatabase, initialize_default_zones
        
        # Initialize database
        db = TrafficDatabase()
        print("Database initialized successfully")
        
        # Initialize default zones
        initialize_default_zones()
        print("Default geographic zones initialized")
        
        # Check database stats
        stats = db.get_database_stats()
        print(f"Database stats: {stats}")
        
        return True
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False

def test_data_collection():
    """Test the data collection system"""
    print("🔄 Testing data collection...")
    
    try:
        from utils.smart_collector import SmartTrafficCollector
        
        # Create collector
        collector = SmartTrafficCollector()
        
        # Get initial status
        status = collector.get_collection_status()
        print(f"Initial collection status:")
        print(f"  - Running: {status['is_running']}")
        print(f"  - Requests today: {status['requests_today']}")
        print(f"  - Quota usage: {status['quota_usage_percent']:.1f}%")
        
        # Test a single collection cycle
        print("Testing single collection cycle...")
        collector.collect_cycle()
        
        # Start background collection
        print("Starting background collection...")
        collector.start_collection()
        
        # Wait a bit and check status
        time.sleep(5)
        updated_status = collector.get_collection_status()
        print(f"Updated collection status:")
        print(f"  - Running: {updated_status['is_running']}")
        print(f"  - Requests today: {updated_status['requests_today']}")
        
        # Stop collection
        collector.stop_collection()
        print("Data collection test completed")
        
        return True
        
    except Exception as e:
        print(f"Error testing data collection: {e}")
        return False

def test_data_sync():
    """Test the data synchronization system"""
    print("Testing data synchronization...")
    
    try:
        from utils.data_sync import DataSync
        
        # Create data sync instance
        data_sync = DataSync()
        
        # Check and sync data
        status = data_sync.check_and_sync_data()
        print(f"Data sync status:")
        print(f"  - Database available: {status['database_available']}")
        print(f"  - Database records: {status['database_records']}")
        print(f"  - CSV available: {status['csv_available']}")
        print(f"  - CSV records: {status['csv_records']}")
        print(f"  - Collector running: {status['collector_running']}")
        print(f"  - Sync performed: {status['sync_performed']}")
        
        if status['error']:
            print(f"Data sync error: {status['error']}")
            return False
        
        print("Data synchronization test completed")
        return True
        
    except Exception as e:
        print(f"Error testing data sync: {e}")
        return False

def main():
    """Main initialization function"""
    print("Village Traffic Data System Initialization")
    print("=" * 50)
    
    # Test API connection
    if not test_api_connection():
        print("API connection failed. Please check your TomTom API key.")
        return
    
    # Initialize database
    if not initialize_database():
        print("Database initialization failed.")
        return
    
    # Test data collection
    if not test_data_collection():
        print("Data collection test failed.")
        return
    
    # Test data synchronization
    if not test_data_sync():
        print("Data synchronization test failed.")
        return
    
    print("\nSystem initialization completed successfully!")
    print("\nNext steps:")
    print("1. Run: streamlit run code/main.py")
    print("2. The system will automatically start collecting data")
    print("3. Check the Live Traffic page for real-time incidents")
    print("4. Use the Analytics page for statistical analysis")

if __name__ == "__main__":
    main()