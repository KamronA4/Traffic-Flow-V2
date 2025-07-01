# MapFetcher.py
# This file defines RI_MapFetcher class; 
# functions to get town coordinates based on town name in RI, as well as the traffic incidents
# Updated to use TomTom API instead of HERE API

import requests
import streamlit as st
from datetime import datetime

class RI_MapFetcher:
    def __init__(self, api_key):
        self.api_key = api_key

    @st.cache_data(ttl=900)  # cache result for 15 mins
    def get_town_coords(_self, town_name):
        # TomTom Search API for geocoding
        # Ref: https://developer.tomtom.com/search-api/documentation/search-service/fuzzy-search
        geocode_url = f'https://api.tomtom.com/search/2/search/{town_name}.json?key={_self.api_key}&countrySet=US&limit=1'
        response = requests.get(geocode_url)
        response.raise_for_status()
        data = response.json()
        
        if data['results']:
            position = data['results'][0]['position']
            return position['lat'], position['lon']
        else:
            raise Exception(f"No coordinates found for {town_name}")

    @st.cache_data(ttl=900)  # cache result for 15 mins to prevent excessive API calls
    def get_traffic_incidents(_self, bounding_box='41.146240,-71.899414,41.748681,-71.088867'):
        # TomTom Traffic Incidents API
        # Ref: https://developer.tomtom.com/traffic-api/documentation/traffic-incidents/incident-details
        # Bounding box format: min_lon,min_lat,max_lon,max_lat (adjusted for Rhode Island)
        # Request detailed fields for incident analysis
        fields = '{incidents{type,geometry{type,coordinates},properties{iconCategory,magnitudeOfDelay,events{description,code}}}}'
        traffic_url = f'https://api.tomtom.com/traffic/services/5/incidentDetails?key={_self.api_key}&bbox={bounding_box}&fields={fields}&timeValidityFilter=present'
        response = requests.get(traffic_url)
        response.raise_for_status()
        data = response.json()
        
        # Transform TomTom response to match expected format
        incidents = []
        if 'incidents' in data:
            for incident in data['incidents']:
                # Extract coordinates from geometry
                coords = incident.get('geometry', {}).get('coordinates', [])
                if coords and len(coords) > 0:
                    # Use first coordinate pair for incident location
                    # TomTom coordinates are [lon, lat] format
                    lat, lon = coords[0][1], coords[0][0]
                    
                    # Get event description if available
                    events = incident.get('properties', {}).get('events', [])
                    description = 'Traffic incident'
                    if events and len(events) > 0:
                        description = events[0].get('description', 'Traffic incident')
                    
                    # Get magnitude of delay
                    magnitude_of_delay = incident.get('properties', {}).get('magnitudeOfDelay', 0)
                    
                    # Transform to expected format
                    transformed_incident = {
                        'id': f"tomtom_{incident.get('properties', {}).get('iconCategory', 0)}_{lat:.6f}_{lon:.6f}",
                        'description': description,
                        'severity': _self._map_severity(incident.get('properties', {}).get('iconCategory', 0)),
                        'lat': lat,
                        'lng': lon,
                        'startTime': '',  # TomTom doesn't provide exact start time in this format
                        'endTime': '',    # TomTom doesn't provide exact end time in this format
                        'length': magnitude_of_delay,  # Use magnitude of delay as length
                        'delay': magnitude_of_delay
                    }
                    incidents.append(transformed_incident)
        
        return incidents

    def _map_severity(_self, icon_category):
        # Map TomTom iconCategory to severity level (1-5 scale)
        # TomTom iconCategory reference: 0-14 different incident types
        severity_mapping = {
            0: 2,  # Unknown
            1: 4,  # Accident
            2: 3,  # Fog
            3: 4,  # Dangerous Conditions
            4: 2,  # Rain
            5: 3,  # Ice
            6: 3,  # Jam
            7: 4,  # Lane Closed
            8: 5,  # Road Closed
            9: 3,  # Road Works
            10: 2, # Wind
            11: 4, # Flooding
            12: 2, # Broken Down Vehicle
            13: 3, # Other
            14: 2  # Mass Transit
        }
        return severity_mapping.get(icon_category, 2)
