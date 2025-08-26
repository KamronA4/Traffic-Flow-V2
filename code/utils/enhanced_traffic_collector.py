#!/usr/bin/env python3
"""
Enhanced Traffic Data Collection System for Village Platform
Comprehensive TomTom API integration for municipal traffic planning

This system collects:
- Traffic flow data (speed, congestion, volume)
- Incident data (accidents, construction, road closures)
- Route analysis (travel times, delays)
- Historical patterns and trends
- Real-time traffic conditions
"""


import streamlit as st
import requests
import json
import time
import logging
import sqlite3
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import schedule
import math
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import credit tracker
try:
    from .credit_tracker import get_credit_tracker
    CREDIT_TRACKER_AVAILABLE = True
except ImportError:
    CREDIT_TRACKER_AVAILABLE = False
    logger.warning("Credit tracker not available")

class TrafficDataType(Enum):
    """Types of traffic data to collect"""
    FLOW = "flow"
    INCIDENTS = "incidents"
    ROUTE = "route"
    SPEED_PROFILE = "speed_profile"
    CONGESTION = "congestion"
    CONSTRUCTION = "construction"
    WEATHER_IMPACT = "weather_impact"

class SeverityLevel(Enum):
    """Traffic severity levels"""
    LOW = 1
    MODERATE = 2
    HIGH = 3
    SEVERE = 4
    CRITICAL = 5

@dataclass
class TrafficFlowData:
    """Traffic flow data structure"""
    timestamp: datetime
    location: str
    latitude: float
    longitude: float
    current_speed: float
    free_flow_speed: float
    current_travel_time: int
    free_flow_travel_time: int
    confidence: float
    road_closure: bool
    congestion_level: int
    data_type: str = "flow"

@dataclass
class TrafficIncident:
    """Enhanced traffic incident data structure"""
    timestamp: datetime
    incident_id: str
    location: str
    latitude: float
    longitude: float
    description: str
    severity: int
    category: str
    subcategory: str
    start_time: datetime
    end_time: Optional[datetime]
    delay_minutes: int
    affected_road: str
    direction: str
    lane_count: int
    lanes_blocked: int
    verified: bool
    data_type: str = "incident"

@dataclass
class RouteData:
    """Route analysis data"""
    timestamp: datetime
    origin: str
    destination: str
    distance_km: float
    travel_time_minutes: int
    delay_minutes: int
    congestion_level: int
    route_summary: str
    alternative_routes: int
    data_type: str = "route"

@dataclass
class CollectionZone:
    """Geographic collection zone"""
    name: str
    bbox: Tuple[float, float, float, float]  # (min_lat, min_lon, max_lat, max_lon)
    priority: int  # 1=highest, 5=lowest
    collection_interval: int  # minutes
    data_types: List[TrafficDataType]
    
    def get_center(self) -> Tuple[float, float]:
        """Get center point of the zone"""
        min_lat, min_lon, max_lat, max_lon = self.bbox
        return ((min_lat + max_lat) / 2, (min_lon + max_lon) / 2)

class EnhancedTrafficCollector:
    """Enhanced traffic data collector with comprehensive TomTom integration"""
    
    def __init__(self):
        self.api_key = self._get_api_key()
        self.db_path = self._get_db_path()
        self.init_database()
        
        # Initialize credit tracker
        if CREDIT_TRACKER_AVAILABLE:
            self.credit_tracker = get_credit_tracker()
            # Get current status from tracker
            status = self.credit_tracker.get_credit_status()
            self.daily_quota = status['daily_quota']
            self.requests_today = status['requests_today']
            self.stop_collection_due_to_credits = status['credits_exhausted']
        else:
            # Fallback to old system
            self.daily_quota = 50000  # TomTom free tier
            self.requests_today = 0
            self.stop_collection_due_to_credits = False
            self.credit_tracker = None
        
        self.last_quota_reset = datetime.now().date()
        self.rate_limit_delay = 0.1  # seconds between requests
        
        # Collection zones for Rhode Island
        self.collection_zones = self._initialize_collection_zones()
        
        # TomTom API base URLs
        self.api_base_urls = {
            'incidents': 'https://api.tomtom.com/traffic/services/5/incidentDetails',
            'flow': 'https://api.tomtom.com/traffic/services/4/flowSegmentData',
            'route': 'https://api.tomtom.com/routing/1/calculateRoute'
        }
        
        # Collection status
        self.is_collecting = False
        self.collection_thread = None
        self.last_collection_time = {}
        self.stop_collection_due_to_credits = False
        
        logger.info("Enhanced Traffic Collector initialized")
    
    def _get_api_key(self) -> str:
        """Get TomTom API key from secrets or environment"""
        try:
            # Try Streamlit secrets first
            api_key = st.secrets.get("TOMTOM_API_KEY")
            if api_key and api_key != "your-tomtom-api-key-here":
                return api_key
        except:
            pass
        
        # Fall back to environment variable
        api_key = os.getenv('TOMTOM_API_KEY')
        if not api_key:
            logger.warning("No TomTom API key found. Set TOMTOM_API_KEY in secrets.toml or environment")
            return ""
        return api_key
    
    def _get_db_path(self) -> str:
        """Get database path"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        data_dir = os.path.join(project_root, "data")
        os.makedirs(data_dir, exist_ok=True)
        return os.path.join(data_dir, "enhanced_traffic_data.db")
    
    def init_database(self):
        """Initialize enhanced database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Traffic flow data table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS traffic_flow (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                location TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                current_speed REAL,
                free_flow_speed REAL,
                current_travel_time INTEGER,
                free_flow_travel_time INTEGER,
                confidence REAL,
                road_closure BOOLEAN,
                congestion_level INTEGER,
                data_type TEXT DEFAULT 'flow'
            )
        ''')
        
        # Enhanced incidents table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS traffic_incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                incident_id TEXT UNIQUE,
                location TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                description TEXT,
                severity INTEGER,
                category TEXT,
                subcategory TEXT,
                start_time DATETIME,
                end_time DATETIME,
                delay_minutes INTEGER,
                affected_road TEXT,
                direction TEXT,
                lane_count INTEGER,
                lanes_blocked INTEGER,
                verified BOOLEAN,
                data_type TEXT DEFAULT 'incident'
            )
        ''')
        
        # Route analysis table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS route_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                origin TEXT NOT NULL,
                destination TEXT NOT NULL,
                distance_km REAL,
                travel_time_minutes INTEGER,
                delay_minutes INTEGER,
                congestion_level INTEGER,
                route_summary TEXT,
                alternative_routes INTEGER,
                data_type TEXT DEFAULT 'route'
            )
        ''')
        
        # Collection statistics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS collection_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                data_type TEXT NOT NULL,
                zone_name TEXT NOT NULL,
                records_collected INTEGER,
                api_requests_used INTEGER,
                success_rate REAL,
                collection_duration REAL
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database schema initialized")
    
    def _initialize_collection_zones(self) -> List[CollectionZone]:
        """Initialize comprehensive collection zones for Rhode Island"""
        zones = [
            # Major highways - highest priority
            CollectionZone(
                name="I-95_Providence_Corridor",
                bbox=(41.7, -71.6, 41.9, -71.3),
                priority=1,
                collection_interval=5,
                data_types=[TrafficDataType.FLOW, TrafficDataType.INCIDENTS, TrafficDataType.ROUTE]
            ),
            CollectionZone(
                name="I-195_East_West",
                bbox=(41.6, -71.5, 41.8, -71.1),
                priority=1,
                collection_interval=5,
                data_types=[TrafficDataType.FLOW, TrafficDataType.INCIDENTS, TrafficDataType.ROUTE]
            ),
            CollectionZone(
                name="Route_95_North",
                bbox=(41.8, -71.6, 42.0, -71.4),
                priority=1,
                collection_interval=5,
                data_types=[TrafficDataType.FLOW, TrafficDataType.INCIDENTS]
            ),
            
            # Urban areas - high priority
            CollectionZone(
                name="Providence_Downtown",
                bbox=(41.81, -71.43, 41.84, -71.40),
                priority=2,
                collection_interval=10,
                data_types=[TrafficDataType.FLOW, TrafficDataType.INCIDENTS, TrafficDataType.CONGESTION]
            ),
            CollectionZone(
                name="Newport_Tourist_Area",
                bbox=(41.47, -71.33, 41.52, -71.30),
                priority=2,
                collection_interval=10,
                data_types=[TrafficDataType.FLOW, TrafficDataType.INCIDENTS]
            ),
            CollectionZone(
                name="Warwick_Airport_Area",
                bbox=(41.69, -71.45, 41.74, -71.40),
                priority=2,
                collection_interval=10,
                data_types=[TrafficDataType.FLOW, TrafficDataType.INCIDENTS]
            ),
            
            # Secondary roads - medium priority
            CollectionZone(
                name="Route_1_Coastal",
                bbox=(41.3, -71.6, 41.7, -71.4),
                priority=3,
                collection_interval=15,
                data_types=[TrafficDataType.FLOW, TrafficDataType.INCIDENTS]
            ),
            CollectionZone(
                name="Route_6_Hartford_Ave",
                bbox=(41.7, -71.5, 41.9, -71.3),
                priority=3,
                collection_interval=15,
                data_types=[TrafficDataType.FLOW, TrafficDataType.INCIDENTS]
            ),
            
            # Construction zones - special monitoring
            CollectionZone(
                name="Construction_Monitoring",
                bbox=(41.7, -71.5, 41.9, -71.3),
                priority=2,
                collection_interval=10,
                data_types=[TrafficDataType.CONSTRUCTION, TrafficDataType.INCIDENTS]
            ),
            
            # Tourist and event areas
            CollectionZone(
                name="URI_Kingston_Campus",
                bbox=(41.48, -71.54, 41.50, -71.52),
                priority=3,
                collection_interval=20,
                data_types=[TrafficDataType.FLOW, TrafficDataType.INCIDENTS]
            ),
            CollectionZone(
                name="Foxwoods_Mohegan_Corridor",
                bbox=(41.50, -71.95, 41.60, -71.85),
                priority=3,
                collection_interval=20,
                data_types=[TrafficDataType.FLOW, TrafficDataType.ROUTE]
            )
        ]
        
        logger.info(f"Initialized {len(zones)} collection zones")
        return zones
    
    def check_rate_limit(self) -> bool:
        """Check if we're within API rate limits"""
        # Reset daily counter if it's a new day
        if datetime.now().date() > self.last_quota_reset:
            self.requests_today = 0
            self.last_quota_reset = datetime.now().date()
        
        return self.requests_today < self.daily_quota
    
    def make_api_request(self, url: str, params: Dict[str, Any]) -> Optional[Dict]:
        """Make rate-limited API request with accurate credit tracking"""
        if not self.check_rate_limit():
            logger.warning("Daily API quota exceeded")
            return None
        
        if not self.api_key:
            logger.warning("No API key available")
            return None
        
        try:
            # Add API key to parameters
            params['key'] = self.api_key
            
            # Rate limiting
            time.sleep(self.rate_limit_delay)
            
            response = requests.get(url, params=params, timeout=30)
            
            # Record the API call with credit tracker
            error_code = None
            error_message = None
            
            if response.status_code == 200:
                # Success - record and return data
                if self.credit_tracker:
                    self.credit_tracker.record_api_call(url, response.status_code)
                else:
                    self.requests_today += 1
                return response.json()
                
            elif response.status_code == 403:
                # Check for insufficient funds or forbidden access
                try:
                    error_data = response.json()
                    error_code = error_data.get('detailedError', {}).get('code')
                    error_message = error_data.get('detailedError', {}).get('message')
                    
                    if error_code == 'InsufficientFunds':
                        logger.error("🚨 CRITICAL: TomTom API credits exhausted! Stopping data collection.")
                        self.stop_collection_due_to_credits = True
                        
                        # Display terminal status
                        if self.credit_tracker:
                            self.credit_tracker.record_api_call(url, response.status_code, error_code, error_message)
                            self.credit_tracker.display_terminal_status()
                        return None
                        
                    elif error_code == 'Forbidden':
                        logger.error("🚨 API endpoint forbidden - check your TomTom API tier")
                        if self.credit_tracker:
                            self.credit_tracker.record_api_call(url, response.status_code, error_code, error_message)
                        return None
                except:
                    pass
                
                # Record failed request
                if self.credit_tracker:
                    self.credit_tracker.record_api_call(url, response.status_code, error_code, error_message)
                else:
                    self.requests_today += 1
                    
                logger.error(f"API request failed: {response.status_code} - {response.text}")
                return None
                
            else:
                # Other error
                if self.credit_tracker:
                    self.credit_tracker.record_api_call(url, response.status_code, error_code, response.text)
                else:
                    self.requests_today += 1
                    
                logger.error(f"API request failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error making API request: {e}")
            return None
    
    def collect_traffic_flow(self, zone: CollectionZone) -> List[TrafficFlowData]:
        """Collect traffic flow data for a zone"""
        center_lat, center_lon = zone.get_center()
        
        # Get flow data for multiple points in the zone
        flow_data = []
        points = self._generate_sample_points(zone.bbox, 20)  # 20 sample points
        
        for lat, lon in points:
            # Construct proper TomTom flow API URL
            flow_url = f"{self.api_base_urls['flow']}/absolute/10/json"
            params = {
                'point': f"{lat},{lon}",
                'unit': 'mph'
            }
            
            response = self.make_api_request(flow_url, params)
            if response and 'flowSegmentData' in response:
                flow_info = response['flowSegmentData']
                
                flow_data.append(TrafficFlowData(
                    timestamp=datetime.now(),
                    location=zone.name,
                    latitude=lat,
                    longitude=lon,
                    current_speed=flow_info.get('currentSpeed', 0),
                    free_flow_speed=flow_info.get('freeFlowSpeed', 0),
                    current_travel_time=flow_info.get('currentTravelTime', 0),
                    free_flow_travel_time=flow_info.get('freeFlowTravelTime', 0),
                    confidence=flow_info.get('confidence', 0),
                    road_closure=flow_info.get('roadClosure', False),
                    congestion_level=self._calculate_congestion_level(
                        flow_info.get('currentSpeed', 0),
                        flow_info.get('freeFlowSpeed', 60)
                    )
                ))
        
        logger.info(f"Collected {len(flow_data)} flow data points for {zone.name}")
        return flow_data
    
    def collect_traffic_incidents(self, zone: CollectionZone) -> List[TrafficIncident]:
        """Collect traffic incidents for a zone"""
        min_lat, min_lon, max_lat, max_lon = zone.bbox
        
        # Construct proper TomTom incidents API URL
        # Format: /incidentDetails?bbox=min_lat,min_lon,max_lat,max_lon&categoryFilter=...
        incidents_url = f"{self.api_base_urls['incidents']}/incidentDetails"
        
        params = {
            'bbox': f"{min_lat},{min_lon},{max_lat},{max_lon}",
            'language': 'en-US',
            'categoryFilter': '0,1,2,3,4,5,6,7,8,9,10,11,14'  # All incident types
        }
        
        response = self.make_api_request(incidents_url, params)
        
        incidents = []
        if response and 'incidents' in response:
            for incident_data in response['incidents']:
                try:
                    properties = incident_data.get('properties', {})
                    geometry = incident_data.get('geometry', {})
                    coordinates = geometry.get('coordinates', [[0, 0]])
                    
                    # Handle different coordinate formats
                    if isinstance(coordinates[0], list):
                        lat, lon = coordinates[0][1], coordinates[0][0]
                    else:
                        lat, lon = coordinates[1], coordinates[0]
                    
                    events = properties.get('events', [{}])
                    main_event = events[0] if events else {}
                    
                    incidents.append(TrafficIncident(
                        timestamp=datetime.now(),
                        incident_id=properties.get('id', f"incident_{int(time.time())}"),
                        location=f"{properties.get('from', '')} to {properties.get('to', '')}",
                        latitude=lat,
                        longitude=lon,
                        description=main_event.get('description', 'Traffic incident'),
                        severity=self._map_severity(properties.get('magnitudeOfDelay', 0)),
                        category=main_event.get('iconCategory', 'unknown'),
                        subcategory=str(main_event.get('code', 0)),
                        start_time=self._parse_time(properties.get('startTime')),
                        end_time=self._parse_time(properties.get('endTime')),
                        delay_minutes=properties.get('delay', 0),
                        affected_road=', '.join(properties.get('roadNumbers', [])),
                        direction='',
                        lane_count=0,
                        lanes_blocked=0,
                        verified=True
                    ))
                    
                except Exception as e:
                    logger.error(f"Error parsing incident: {e}")
                    continue
        
        logger.info(f"Collected {len(incidents)} incidents for {zone.name}")
        return incidents
    
    def collect_route_analysis(self, zone: CollectionZone) -> List[RouteData]:
        """Collect route analysis data"""
        center_lat, center_lon = zone.get_center()
        
        # Define some common routes within the zone
        routes = [
            ((center_lat - 0.05, center_lon - 0.05), (center_lat + 0.05, center_lon + 0.05)),
            ((center_lat - 0.02, center_lon - 0.02), (center_lat + 0.02, center_lon + 0.02)),
            ((center_lat, center_lon - 0.03), (center_lat, center_lon + 0.03))
        ]
        
        route_data = []
        for origin, destination in routes:
            # Construct proper TomTom routing API URL
            route_locations = f"{origin[0]},{origin[1]}:{destination[0]},{destination[1]}"
            route_url = f"{self.api_base_urls['route']}/{route_locations}/json"
            
            params = {
                'travelMode': 'car',
                'traffic': 'true',
                'routeType': 'fastest'
            }
            
            response = self.make_api_request(route_url, params)
            if response and 'routes' in response and response['routes']:
                route_info = response['routes'][0]
                summary = route_info.get('summary', {})
                
                route_data.append(RouteData(
                    timestamp=datetime.now(),
                    origin=f"{origin[0]:.4f},{origin[1]:.4f}",
                    destination=f"{destination[0]:.4f},{destination[1]:.4f}",
                    distance_km=summary.get('lengthInMeters', 0) / 1000,
                    travel_time_minutes=summary.get('travelTimeInSeconds', 0) / 60,
                    delay_minutes=summary.get('trafficDelayInSeconds', 0) / 60,
                    congestion_level=self._calculate_route_congestion(summary),
                    route_summary=f"Distance: {summary.get('lengthInMeters', 0)/1000:.1f}km",
                    alternative_routes=len(response.get('routes', [])) - 1
                ))
        
        logger.info(f"Collected {len(route_data)} route analyses for {zone.name}")
        return route_data
    
    def _generate_sample_points(self, bbox: Tuple[float, float, float, float], count: int) -> List[Tuple[float, float]]:
        """Generate sample points within a bounding box"""
        min_lat, min_lon, max_lat, max_lon = bbox
        points = []
        
        for i in range(count):
            lat = min_lat + (max_lat - min_lat) * (i / count)
            lon = min_lon + (max_lon - min_lon) * (i / count)
            points.append((lat, lon))
        
        return points
    
    def _calculate_congestion_level(self, current_speed: float, free_flow_speed: float) -> int:
        """Calculate congestion level from speed data"""
        if free_flow_speed == 0:
            return 0
        
        ratio = current_speed / free_flow_speed
        if ratio > 0.8:
            return 1  # Free flow
        elif ratio > 0.6:
            return 2  # Light congestion
        elif ratio > 0.4:
            return 3  # Moderate congestion
        elif ratio > 0.2:
            return 4  # Heavy congestion
        else:
            return 5  # Severe congestion
    
    def _calculate_route_congestion(self, summary: Dict) -> int:
        """Calculate congestion level from route summary"""
        delay = summary.get('trafficDelayInSeconds', 0)
        travel_time = summary.get('travelTimeInSeconds', 1)
        
        if delay == 0:
            return 1
        
        delay_ratio = delay / travel_time
        if delay_ratio < 0.1:
            return 1
        elif delay_ratio < 0.25:
            return 2
        elif delay_ratio < 0.5:
            return 3
        elif delay_ratio < 0.75:
            return 4
        else:
            return 5
    
    def _map_severity(self, magnitude: int) -> int:
        """Map TomTom magnitude to our severity scale"""
        severity_map = {0: 1, 1: 2, 2: 3, 3: 4, 4: 5}
        return severity_map.get(magnitude, 1)
    
    def _parse_time(self, time_str: Optional[str]) -> Optional[datetime]:
        """Parse time string to datetime"""
        if not time_str:
            return None
        try:
            return datetime.fromisoformat(time_str.replace('Z', '+00:00'))
        except:
            return None
    
    def save_data(self, data: List[Any], table_name: str):
        """Save collected data to database"""
        if not data:
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            for item in data:
                if isinstance(item, TrafficFlowData):
                    cursor.execute('''
                        INSERT INTO traffic_flow 
                        (timestamp, location, latitude, longitude, current_speed, free_flow_speed,
                         current_travel_time, free_flow_travel_time, confidence, road_closure, congestion_level)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        item.timestamp, item.location, item.latitude, item.longitude,
                        item.current_speed, item.free_flow_speed, item.current_travel_time,
                        item.free_flow_travel_time, item.confidence, item.road_closure,
                        item.congestion_level
                    ))
                
                elif isinstance(item, TrafficIncident):
                    # Use the database manager's insert method for proper formatting
                    from utils.database import get_database
                    db = get_database()
                    
                    # Convert TrafficIncident to dict format expected by database
                    incident_dict = {
                        'external_id': item.incident_id,
                        'timestamp': item.timestamp,
                        'latitude': item.latitude,
                        'longitude': item.longitude,
                        'location': item.location,
                        'description': item.description,
                        'severity': item.severity,
                        'type': 1,  # Default incident type
                        'Length_of_Time(Hours)': item.delay_minutes / 60.0 if item.delay_minutes else 0,
                        'data_source': 'tomtom_api'  # Mark as real API data
                    }
                    
                    db.insert_traffic_incident(incident_dict)
                
                elif isinstance(item, RouteData):
                    cursor.execute('''
                        INSERT INTO route_analysis 
                        (timestamp, origin, destination, distance_km, travel_time_minutes,
                         delay_minutes, congestion_level, route_summary, alternative_routes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        item.timestamp, item.origin, item.destination, item.distance_km,
                        item.travel_time_minutes, item.delay_minutes, item.congestion_level,
                        item.route_summary, item.alternative_routes
                    ))
            
            conn.commit()
            logger.info(f"Saved {len(data)} records to {table_name}")
            
        except Exception as e:
            logger.error(f"Error saving data: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def collect_zone_data(self, zone: CollectionZone) -> Dict[str, int]:
        """Collect all data types for a zone"""
        collected_counts = {}
        
        for data_type in zone.data_types:
            try:
                if data_type == TrafficDataType.FLOW:
                    data = self.collect_traffic_flow(zone)
                    self.save_data(data, 'traffic_flow')
                    collected_counts['flow'] = len(data)
                
                elif data_type == TrafficDataType.INCIDENTS:
                    data = self.collect_traffic_incidents(zone)
                    self.save_data(data, 'traffic_incidents')
                    collected_counts['incidents'] = len(data)
                
                elif data_type == TrafficDataType.ROUTE:
                    data = self.collect_route_analysis(zone)
                    self.save_data(data, 'route_analysis')
                    collected_counts['routes'] = len(data)
                
                # Add small delay between data types
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error collecting {data_type} data for {zone.name}: {e}")
                collected_counts[data_type.value] = 0
        
        return collected_counts
    
    def run_collection_cycle(self):
        """Run one complete collection cycle"""
        logger.info("Starting collection cycle")
        start_time = time.time()
        
        # Check if collection should be stopped due to credit exhaustion
        if self.stop_collection_due_to_credits:
            logger.error("🚨 Collection stopped due to API credit exhaustion. Please add more credits or wait for reset.")
            self.stop_collection()
            return
        
        total_collected = 0
        
        # Sort zones by priority
        sorted_zones = sorted(self.collection_zones, key=lambda x: x.priority)
        
        for zone in sorted_zones:
            # Check if it's time to collect for this zone
            last_collection = self.last_collection_time.get(zone.name, datetime.min)
            if (datetime.now() - last_collection).total_seconds() >= zone.collection_interval * 60:
                
                logger.info(f"Collecting data for zone: {zone.name}")
                collected = self.collect_zone_data(zone)
                
                # Update last collection time
                self.last_collection_time[zone.name] = datetime.now()
                
                # Log collection stats
                total_zone_collected = sum(collected.values())
                total_collected += total_zone_collected
                
                logger.info(f"Zone {zone.name}: {collected}")
                
                # Save collection statistics
                self.save_collection_stats(zone.name, collected, time.time() - start_time)
        
        duration = time.time() - start_time
        logger.info(f"Collection cycle completed: {total_collected} records in {duration:.2f}s")
        logger.info(f"API requests used today: {self.requests_today}/{self.daily_quota}")
    
    def save_collection_stats(self, zone_name: str, collected: Dict[str, int], duration: float):
        """Save collection statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            for data_type, count in collected.items():
                cursor.execute('''
                    INSERT INTO collection_stats 
                    (timestamp, data_type, zone_name, records_collected, api_requests_used, 
                     success_rate, collection_duration)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    datetime.now(), data_type, zone_name, count, 
                    1, 1.0 if count > 0 else 0.0, duration
                ))
            
            conn.commit()
        except Exception as e:
            logger.error(f"Error saving collection stats: {e}")
        finally:
            conn.close()
    
    def start_continuous_collection(self):
        """Start continuous data collection"""
        if self.is_collecting:
            logger.warning("Collection already running")
            return
        
        self.is_collecting = True
        logger.info("Starting continuous traffic data collection")
        
        def collection_loop():
            while self.is_collecting and not self.stop_collection_due_to_credits:
                try:
                    self.run_collection_cycle()
                    time.sleep(30)  # Wait 30 seconds between cycles
                except Exception as e:
                    logger.error(f"Error in collection loop: {e}")
                    time.sleep(60)  # Wait longer on error
        
        self.collection_thread = threading.Thread(target=collection_loop)
        self.collection_thread.daemon = True
        self.collection_thread.start()
    
    def stop_collection(self):
        """Stop continuous data collection"""
        self.is_collecting = False
        if self.collection_thread:
            self.collection_thread.join(timeout=5)
        logger.info("Traffic data collection stopped")
    
    def get_collection_status(self) -> Dict[str, Any]:
        """Get current collection status with accurate credit tracking"""
        if self.credit_tracker:
            credit_status = self.credit_tracker.get_credit_status()
            return {
                'is_collecting': self.is_collecting,
                'api_requests_today': credit_status['requests_today'],
                'successful_requests': credit_status['successful_today'],
                'failed_requests': credit_status['failed_today'],
                'daily_quota': credit_status['daily_quota'],
                'quota_remaining': credit_status['remaining'],
                'usage_percent': credit_status['usage_percent'],
                'zones_configured': len(self.collection_zones),
                'last_collection_times': self.last_collection_time,
                'credit_exhausted': credit_status['credits_exhausted'],
                'last_updated': credit_status['last_updated']
            }
        else:
            # Fallback to old system
            return {
                'is_collecting': self.is_collecting,
                'api_requests_today': self.requests_today,
                'daily_quota': self.daily_quota,
                'quota_remaining': self.daily_quota - self.requests_today,
                'zones_configured': len(self.collection_zones),
                'last_collection_times': self.last_collection_time,
                'credit_exhausted': self.stop_collection_due_to_credits
            }
    
    def reset_credit_flag(self):
        """Reset the credit exhaustion flag (call this when credits are renewed)"""
        self.stop_collection_due_to_credits = False
        
        if self.credit_tracker:
            self.credit_tracker.reset_credits()
        
        logger.info("Credit exhaustion flag reset")

# Global collector instance
_collector_instance = None

def get_enhanced_collector() -> EnhancedTrafficCollector:
    """Get singleton collector instance"""
    global _collector_instance
    if _collector_instance is None:
        _collector_instance = EnhancedTrafficCollector()
    return _collector_instance

if __name__ == "__main__":
    # Test the enhanced collector
    collector = EnhancedTrafficCollector()
    print("Enhanced Traffic Collector initialized")
    print(f"Zones configured: {len(collector.collection_zones)}")
    print(f"API key configured: {'Yes' if collector.api_key else 'No'}")
    
    # Run a single collection cycle
    collector.run_collection_cycle()
    
    # Show status
    status = collector.get_collection_status()
    print(f"Collection status: {status}")