# traffic_data_collection.py
# this will collect traffic incidents and store them into a .csv file
# Updated to use TomTom API instead of HERE API 

import requests
import csv
from datetime import datetime
import os
import sys

# Add the code directory to the path to import MapFetcher
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'code'))
from MapFetcher import RI_MapFetcher

# Replace with your TomTom API key
api_key = 'ldZpXKM4XNxvJpSb2ZGfUeSgLXt8Db9G'
fetcher = RI_MapFetcher(api_key)
output_csv = 'traffic_incidents.csv'
bbox = '41.146240,-71.899414,41.748681,-71.088867'  # RI bounding box for TomTom API

def fetch_traffic_incidents():
    incidents = fetcher.get_traffic_incidents(bbox)
    return incidents

def append_to_csv(incidents, filename):
    file_exists = os.path.isfile(filename) # check if the file exists
    with open(filename, mode='a', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['timestamp', 'id', 'description', 'severity', 'lat', 'lng', 'startTime', 'endTime', 'length', 'delay', 'location']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        for incident in incidents:
            # Use incident coordinates to determine location (simplified)
            location = f"lat_{incident.get('lat', 0):.3f}_lng_{incident.get('lng', 0):.3f}"
            
            writer.writerow({
                'timestamp': datetime.utcnow().isoformat(),
                'id': incident.get('id', ''),
                'description': incident.get('description', 'Traffic incident'),
                'severity': incident.get('severity', 2),
                'lat': incident.get('lat', 0),
                'lng': incident.get('lng', 0),
                'startTime': incident.get('startTime', ''),
                'endTime': incident.get('endTime', ''),
                'length': incident.get('length', 0),
                'delay': incident.get('delay', 0),
                'location': location
            })

if __name__ == '__main__':
    try:
        incidents = fetch_traffic_incidents()
        append_to_csv(incidents, output_csv)
        print(f'{len(incidents)} incidents logged at {datetime.utcnow().isoformat()}')
    except Exception as e:
        print(f'Error: {e}')
