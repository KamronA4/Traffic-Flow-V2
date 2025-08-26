#!/usr/bin/env python3
"""
Debug script to check database contents and date filtering
"""

import sqlite3
import pandas as pd
from datetime import datetime, date

def check_database_contents():
    """Check what's in the traffic database"""
    db_path = "data/traffic_data.db"
    
    try:
        conn = sqlite3.connect(db_path)
        
        # Check if tables exist
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
        print(f"Tables in database: {[t[0] for t in tables]}")
        
        # Check traffic_incidents table structure
        if any('traffic_incidents' in str(t) for t in tables):
            schema = conn.execute("PRAGMA table_info(traffic_incidents);").fetchall()
            print(f"\ntraffic_incidents columns: {[col[1] for col in schema]}")
            
            # Count total incidents
            count = conn.execute("SELECT COUNT(*) FROM traffic_incidents").fetchone()[0]
            print(f"Total incidents in database: {count}")
            
            if count > 0:
                # Check date range
                dates = conn.execute("SELECT MIN(date(timestamp)), MAX(date(timestamp)) FROM traffic_incidents").fetchone()
                print(f"Date range: {dates[0]} to {dates[1]}")
                
                # Check specific May dates
                may_count = conn.execute("""
                    SELECT COUNT(*) FROM traffic_incidents 
                    WHERE date(timestamp) BETWEEN '2024-05-02' AND '2024-05-08'
                """).fetchone()[0]
                print(f"Incidents between 2024-05-02 and 2024-05-08: {may_count}")
                
                # Show sample data
                sample = conn.execute("SELECT timestamp, location, description FROM traffic_incidents LIMIT 5").fetchall()
                print("\nSample incidents:")
                for row in sample:
                    print(f"  {row[0]} | {row[1]} | {row[2]}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error checking database: {e}")

def check_csv_file():
    """Check the CSV file contents"""
    try:
        df = pd.read_csv("data/traffic_incidents.csv")
        print(f"\nCSV file has {len(df)} rows")
        
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['date'] = df['timestamp'].dt.date
            
            print(f"Date range in CSV: {df['date'].min()} to {df['date'].max()}")
            
            # Check May dates
            may_mask = (df['date'] >= date(2024, 5, 2)) & (df['date'] <= date(2024, 5, 8))
            may_incidents = df[may_mask]
            print(f"Incidents in CSV between May 2-8, 2024: {len(may_incidents)}")
            
            if len(may_incidents) > 0:
                print("\nSample May incidents from CSV:")
                for _, row in may_incidents.head(3).iterrows():
                    print(f"  {row['timestamp']} | {row['location']} | {row['description']}")
        
    except Exception as e:
        print(f"Error reading CSV: {e}")

if __name__ == "__main__":
    print("Debugging Database and CSV Contents")
    print("=" * 50)
    
    check_database_contents()
    check_csv_file()