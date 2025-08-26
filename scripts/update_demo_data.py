#!/usr/bin/env python3
"""
Update demo data with current timestamps for RIHub presentation
"""

import pandas as pd
import os
from datetime import datetime, timedelta
import random

def update_traffic_data():
    """Update existing traffic data with current timestamps"""
    
    # Check for existing CSV file
    csv_paths = [
        'scripts/traffic_incidents.csv',
        'code/data/traffic_incidents.csv',
        'data/traffic_incidents.csv'
    ]
    
    csv_path = None
    for path in csv_paths:
        if os.path.exists(path):
            csv_path = path
            break
    
    if not csv_path:
        print("No existing traffic incidents CSV found. Creating new demo data...")
        create_demo_data()
        return
    
    print(f"Found existing data at: {csv_path}")
    
    # Read existing data
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} existing incidents")
    
    # Update timestamps to current time
    current_time = datetime.now()
    
    # Distribute incidents over the last 24 hours
    for i in range(len(df)):
        # Random time in last 24 hours
        hours_ago = random.uniform(0, 24)
        new_timestamp = current_time - timedelta(hours=hours_ago)
        
        df.loc[i, 'timestamp'] = new_timestamp.isoformat()
        
        # Update date and hour columns if they exist
        if 'date' in df.columns:
            df.loc[i, 'date'] = new_timestamp.date().isoformat()
        if 'hour' in df.columns:
            df.loc[i, 'hour'] = new_timestamp.hour
    
    # Ensure critical columns exist
    if 'lat' not in df.columns and 'latitude' in df.columns:
        df['lat'] = df['latitude']
    if 'lng' not in df.columns and 'longitude' in df.columns:
        df['lng'] = df['longitude']
    
    # Save updated data
    save_paths = [
        'data/traffic_incidents.csv',
        'code/data/traffic_incidents.csv'
    ]
    
    for save_path in save_paths:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        df.to_csv(save_path, index=False)
        print(f"Saved updated data to: {save_path}")

def create_demo_data():
    """Create new demo data for Rhode Island"""
    
    # Rhode Island key locations
    ri_locations = [
        {'name': 'I-95 @ Providence', 'lat': 41.8236, 'lng': -71.4222},
        {'name': 'I-195 @ East Providence', 'lat': 41.8187, 'lng': -71.3706},
        {'name': 'Route 6 @ Johnston', 'lat': 41.8280, 'lng': -71.5062},
        {'name': 'Newport Bridge', 'lat': 41.5048, 'lng': -71.3389},
        {'name': 'T.F. Green Airport Access', 'lat': 41.7243, 'lng': -71.4283},
        {'name': 'Downtown Providence', 'lat': 41.8236, 'lng': -71.4138},
        {'name': 'URI Main Campus', 'lat': 41.4831, 'lng': -71.5267},
        {'name': 'Pawtucket Main St', 'lat': 41.8787, 'lng': -71.3826},
        {'name': 'Warwick Mall Area', 'lat': 41.7324, 'lng': -71.4788},
        {'name': 'Cranston St @ Providence', 'lat': 41.8097, 'lng': -71.4351}
    ]
    
    # Incident types
    incident_types = [
        {'desc': 'Multi-vehicle accident', 'severity': 4},
        {'desc': 'Road construction', 'severity': 2},
        {'desc': 'Disabled vehicle', 'severity': 2},
        {'desc': 'Heavy traffic congestion', 'severity': 3},
        {'desc': 'Lane closure', 'severity': 2},
        {'desc': 'Emergency roadwork', 'severity': 3},
        {'desc': 'Weather-related delays', 'severity': 3},
        {'desc': 'Special event traffic', 'severity': 2}
    ]
    
    # Generate incidents
    incidents = []
    current_time = datetime.now()
    
    for i in range(25):  # Create 25 incidents
        location = random.choice(ri_locations)
        incident_type = random.choice(incident_types)
        
        # Time distribution - more recent incidents
        if i < 10:
            # Last 3 hours
            hours_ago = random.uniform(0, 3)
        else:
            # Last 24 hours
            hours_ago = random.uniform(3, 24)
        
        timestamp = current_time - timedelta(hours=hours_ago)
        
        # Adjust severity for rush hour
        if timestamp.hour in [7, 8, 9, 16, 17, 18]:
            severity = min(incident_type['severity'] + 1, 5)
        else:
            severity = incident_type['severity']
        
        incidents.append({
            'timestamp': timestamp.isoformat(),
            'id': f'INC_{i+1:04d}',
            'description': incident_type['desc'],
            'severity': severity,
            'lat': round(location['lat'] + random.uniform(-0.01, 0.01), 6),
            'lng': round(location['lng'] + random.uniform(-0.01, 0.01), 6),
            'location': location['name'],
            'startTime': timestamp.isoformat(),
            'endTime': (timestamp + timedelta(hours=random.uniform(0.5, 3))).isoformat(),
            'length': random.randint(100, 3000),
            'delay': random.randint(5, 45),
            'date': timestamp.date().isoformat(),
            'hour': timestamp.hour
        })
    
    # Create DataFrame
    df = pd.DataFrame(incidents)
    
    # Sort by timestamp (most recent first)
    df = df.sort_values('timestamp', ascending=False)
    
    # Save data
    save_paths = [
        'data/traffic_incidents.csv',
        'code/data/traffic_incidents.csv'
    ]
    
    for save_path in save_paths:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        df.to_csv(save_path, index=False)
        print(f"Created demo data at: {save_path}")
    
    print(f"\nCreated {len(incidents)} demo incidents")
    print("\nSample incidents:")
    for inc in incidents[:3]:
        print(f"- {inc['description']} at {inc['location']} (Severity: {inc['severity']})")

def main():
    """Main execution"""
    print("Updating demo data for RIHub presentation")
    print("=" * 50)
    
    update_traffic_data()
    
    print("\nDemo data update complete!")

if __name__ == "__main__":
    main()