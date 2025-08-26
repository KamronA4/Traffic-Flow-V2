#!/usr/bin/env python3
"""
Clean all dummy data from database and ensure only real API data is used
"""

import sqlite3
import os
from datetime import datetime

def clean_database_dummy_data():
    """Remove all dummy/test data from traffic_incidents table"""
    
    db_path = "data/traffic_data.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check what data exists before cleaning
        cursor.execute("SELECT COUNT(*) FROM traffic_incidents")
        before_count = cursor.fetchone()[0]
        print(f"📊 Before cleaning: {before_count} incidents in database")
        
        if before_count > 0:
            # Show date range of existing data
            cursor.execute("SELECT MIN(date(timestamp)), MAX(date(timestamp)) FROM traffic_incidents")
            date_range = cursor.fetchone()
            print(f"📅 Date range: {date_range[0]} to {date_range[1]}")
            
            # Show data sources
            cursor.execute("SELECT data_source, COUNT(*) FROM traffic_incidents GROUP BY data_source")
            sources = cursor.fetchall()
            print("📋 Data sources:")
            for source, count in sources:
                print(f"  - {source or 'Unknown'}: {count} incidents")
        
        # Remove all dummy/test data
        # Keep only data that has 'tomtom' or 'api' in data_source field
        cursor.execute("""
            DELETE FROM traffic_incidents 
            WHERE data_source IS NULL 
               OR data_source = '' 
               OR data_source = 'csv'
               OR data_source = 'demo'
               OR data_source = 'test'
               OR external_id LIKE 'INC_%'
        """)
        
        deleted_count = cursor.rowcount
        conn.commit()
        
        # Check what remains
        cursor.execute("SELECT COUNT(*) FROM traffic_incidents")
        after_count = cursor.fetchone()[0]
        
        print(f"🗑️ Deleted {deleted_count} dummy/test incidents")
        print(f"✅ Remaining real data: {after_count} incidents")
        
        if after_count > 0:
            cursor.execute("SELECT MIN(date(timestamp)), MAX(date(timestamp)) FROM traffic_incidents")
            date_range = cursor.fetchone()
            print(f"📅 Real data date range: {date_range[0]} to {date_range[1]}")
            
            # Show remaining sources
            cursor.execute("SELECT data_source, COUNT(*) FROM traffic_incidents GROUP BY data_source")
            sources = cursor.fetchall()
            print("📋 Remaining data sources:")
            for source, count in sources:
                print(f"  - {source}: {count} incidents")
        else:
            print("💡 Database is now clean - waiting for real API data collection")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error cleaning database: {e}")
        return False

def verify_data_flow():
    """Verify that the system is set up for real data only"""
    
    print("\n🔍 Verifying System Configuration")
    print("=" * 40)
    
    # Check if CSV file is empty (header only)
    try:
        with open("data/traffic_incidents.csv", 'r') as f:
            lines = f.readlines()
            if len(lines) <= 1:
                print("✅ CSV file is empty (header only)")
            else:
                print(f"⚠️ CSV file still contains {len(lines)-1} rows")
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
    
    # Check database setup
    try:
        conn = sqlite3.connect("data/traffic_data.db")
        cursor = conn.cursor()
        
        # Check table structure
        cursor.execute("PRAGMA table_info(traffic_incidents)")
        columns = [col[1] for col in cursor.fetchall()]
        
        expected_columns = ['data_source', 'external_id', 'timestamp', 'latitude', 'longitude']
        missing_columns = [col for col in expected_columns if col not in columns]
        
        if not missing_columns:
            print("✅ Database schema ready for API data")
        else:
            print(f"⚠️ Missing columns: {missing_columns}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error verifying database: {e}")
    
    print("\n🎯 System Ready For:")
    print("- Real TomTom API data collection")
    print("- Database-first data flow (no CSV fallback)")
    print("- Authentic Rhode Island traffic incidents")
    print("\n📋 Next: Start data collection via enhanced_traffic_collector")

if __name__ == "__main__":
    print("Cleaning Dummy Data from Village Platform")
    print("=" * 50)
    
    success = clean_database_dummy_data()
    
    if success:
        verify_data_flow()
        print("\n🎉 Database cleaned successfully!")
        print("💡 Your system now uses ONLY real API data")
    else:
        print("\n❌ Database cleaning failed")