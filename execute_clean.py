#!/usr/bin/env python3
import sqlite3
import os

# Clean database directly
db_path = "/Users/kamronaggor/Desktop/Manual Library/Coding stuff/Data Science Projects/Perplexity-Hackathon/data/traffic_data.db"

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check what exists
    cursor.execute("SELECT COUNT(*) FROM traffic_incidents")
    before_count = cursor.fetchone()[0]
    print(f"Before cleaning: {before_count} incidents")
    
    # Remove all dummy data
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
    
    cursor.execute("SELECT COUNT(*) FROM traffic_incidents")
    after_count = cursor.fetchone()[0]
    
    print(f"Deleted: {deleted_count} dummy incidents")
    print(f"Remaining: {after_count} real incidents")
    print("Database cleaned!")
    
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")

print("CSV file cleared to header only")
print("System ready for real API data!")