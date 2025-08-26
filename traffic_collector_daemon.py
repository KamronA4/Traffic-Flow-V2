#!/usr/bin/env python3
"""
Traffic Collector Daemon - VM-Optimized Standalone Service
Continuous traffic data collection service for deployment on virtual machines
"""

import os
import sys
import time
import json
import signal
import logging
import threading
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import yaml
import schedule
import requests
from concurrent.futures import ThreadPoolExecutor
import argparse
import random
import uuid

# Configure logging for daemon operation
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/traffic-collector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CollectorDaemon:
    """Main daemon class for traffic data collection"""
    
    def __init__(self, config_path: str = "/etc/traffic-collector/config.yaml"):
        self.config_path = config_path
        
        # Detect demo mode
        self.demo_mode = os.getenv('VILLAGE_DEMO_MODE', 'false').lower() == 'true'
        self.demo_safe_mode = os.getenv('VILLAGE_DEMO_SAFE_MODE', 'true').lower() == 'true'
        
        # Use demo-appropriate paths
        if self.demo_mode:
            self.config_path = self._get_demo_config_path()
        
        self.config = self._load_config()
        self.running = False
        self.collection_thread = None
        self.api_key = self.config.get('tomtom_api_key') or os.getenv('TOMTOM_API_KEY')
        
        # Database setup with demo-safe paths
        if self.demo_mode:
            self.db_path = self._get_demo_db_path()
        else:
            self.db_path = self.config.get('database_path', '/var/lib/traffic-collector/traffic_data.db')
        
        self._setup_database()
        
        # Collection state
        self.last_collection_times = {}
        self.requests_today = 0
        self.daily_quota = self.config.get('daily_quota', 50000)
        self.rate_limit_delay = self.config.get('rate_limit_delay', 0.1)
        
        # Signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        logger.info(f"Traffic Collector Daemon initialized (Demo Mode: {self.demo_mode})")
        if self.demo_mode:
            logger.info("Running in demo-safe mode with fallbacks enabled")
    
    def _get_demo_config_path(self) -> str:
        """Get demo-appropriate config path"""
        current_dir = Path(__file__).parent
        demo_config_path = current_dir / "config" / "demo_collector_config.yaml"
        
        # Create demo config directory if it doesn't exist
        demo_config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create demo config if it doesn't exist
        if not demo_config_path.exists():
            self._create_demo_config(demo_config_path)
        
        return str(demo_config_path)
    
    def _get_demo_db_path(self) -> str:
        """Get demo-appropriate database path"""
        current_dir = Path(__file__).parent
        return str(current_dir / "data" / "demo_traffic_data.db")
    
    def _create_demo_config(self, config_path: Path):
        """Create demo configuration file"""
        demo_config = {
            'tomtom_api_key': os.getenv('TOMTOM_API_KEY', ''),
            'database_path': self._get_demo_db_path(),
            'daily_quota': 100,  # Lower quota for demos
            'rate_limit_delay': 2.0,  # Slower rate for demos
            'log_level': 'INFO',
            'demo_mode': True,
            'demo_safe_mode': True,
            'max_demo_requests': 50,  # Hard limit for demos
            'collection_zones': [
                {
                    'name': 'Demo_Providence_Area',
                    'bbox': [41.8, -71.5, 41.85, -71.4],
                    'priority': 1,
                    'interval_minutes': 30,  # Longer intervals for demos
                    'data_types': ['incidents']  # Only incidents for demos
                }
            ]
        }
        
        with open(config_path, 'w') as f:
            yaml.dump(demo_config, f, default_flow_style=False)
        
        logger.info(f"Created demo configuration at {config_path}")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Configuration loaded from {self.config_path}")
            return config
        except FileNotFoundError:
            logger.warning(f"Config file not found at {self.config_path}, using defaults")
            return self._get_default_config()
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'tomtom_api_key': '',
            'database_path': '/var/lib/traffic-collector/traffic_data.db',
            'daily_quota': 50000,
            'rate_limit_delay': 0.1,
            'log_level': 'INFO',
            'collection_zones': [
                {
                    'name': 'I-95_Providence_Corridor',
                    'bbox': [41.7, -71.6, 41.9, -71.3],
                    'priority': 1,
                    'interval_minutes': 5,
                    'data_types': ['flow', 'incidents']
                },
                {
                    'name': 'Providence_Downtown',
                    'bbox': [41.81, -71.43, 41.84, -71.40],
                    'priority': 2,
                    'interval_minutes': 10,
                    'data_types': ['flow', 'incidents']
                }
            ],
            'api_endpoints': {
                'incidents': 'https://api.tomtom.com/traffic/services/5/incidentDetails',
                'flow': 'https://api.tomtom.com/traffic/services/4/flowSegmentData'
            }
        }
    
    def _setup_database(self):
        """Setup database and ensure directory exists"""
        db_dir = os.path.dirname(self.db_path)
        os.makedirs(db_dir, exist_ok=True)
        
        # Initialize database schema
        self._create_tables()
        logger.info(f"Database initialized at {self.db_path}")
    
    def _create_tables(self):
        """Create database tables for traffic data"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Traffic incidents table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS traffic_incidents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    external_id TEXT UNIQUE,
                    timestamp TIMESTAMP NOT NULL,
                    collection_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    location TEXT NOT NULL,
                    description TEXT NOT NULL,
                    severity INTEGER NOT NULL,
                    incident_type INTEGER,
                    delay_minutes REAL,
                    data_source TEXT DEFAULT 'tomtom'
                )
            """)
            
            # Traffic flow table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS traffic_flow (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP NOT NULL,
                    collection_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    location TEXT,
                    current_speed_mph REAL,
                    free_flow_speed_mph REAL,
                    confidence_level REAL,
                    congestion_level INTEGER,
                    data_source TEXT DEFAULT 'tomtom'
                )
            """)
            
            # API usage tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS api_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    endpoint TEXT NOT NULL,
                    status_code INTEGER,
                    response_time_ms INTEGER,
                    error_message TEXT,
                    requests_count INTEGER DEFAULT 1
                )
            """)
            
            # Collection statistics
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS collection_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    zone_name TEXT NOT NULL,
                    data_type TEXT NOT NULL,
                    records_collected INTEGER,
                    collection_duration_seconds REAL,
                    success BOOLEAN
                )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_incidents_timestamp ON traffic_incidents(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_flow_timestamp ON traffic_flow(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_api_usage_timestamp ON api_usage(timestamp)")
            
            conn.commit()
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.stop()
    
    def check_api_quota(self) -> bool:
        """Check if we're within daily API quota"""
        today = datetime.now().date()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT SUM(requests_count) FROM api_usage 
                WHERE DATE(timestamp) = ?
            """, (today,))
            
            result = cursor.fetchone()
            self.requests_today = result[0] if result[0] else 0
        
        return self.requests_today < self.daily_quota
    
    def make_api_request(self, url: str, params: Dict[str, Any]) -> Optional[Dict]:
        """Make rate-limited API request with logging and demo fallbacks"""
        
        # Demo mode safety checks
        if self.demo_mode and self.demo_safe_mode:
            # Check demo request limits
            max_demo_requests = self.config.get('max_demo_requests', 50)
            if self.requests_today >= max_demo_requests:
                logger.info(f"Demo request limit reached ({max_demo_requests}), using fallback data")
                return self._generate_demo_fallback_data(url, params)
        
        if not self.check_api_quota():
            logger.warning("Daily API quota exceeded")
            if self.demo_mode:
                logger.info("Using demo fallback data due to quota exhaustion")
                return self._generate_demo_fallback_data(url, params)
            return None
        
        if not self.api_key:
            if self.demo_mode:
                logger.info("No API key configured, using demo fallback data")
                return self._generate_demo_fallback_data(url, params)
            else:
                logger.error("No TomTom API key configured")
                return None
        
        params['key'] = self.api_key
        start_time = time.time()
        
        try:
            time.sleep(self.rate_limit_delay)
            response = requests.get(url, params=params, timeout=30)
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Log API usage
            self._log_api_usage(url, response.status_code, response_time_ms, 
                              None if response.status_code == 200 else response.text)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"API request failed: {response.status_code} - {response.text}")
                if self.demo_mode:
                    logger.info("Using demo fallback data due to API error")
                    return self._generate_demo_fallback_data(url, params)
                return None
                
        except Exception as e:
            response_time_ms = int((time.time() - start_time) * 1000)
            self._log_api_usage(url, 0, response_time_ms, str(e))
            logger.error(f"API request error: {e}")
            if self.demo_mode:
                logger.info("Using demo fallback data due to request error")
                return self._generate_demo_fallback_data(url, params)
            return None
    
    def _log_api_usage(self, endpoint: str, status_code: int, response_time_ms: int, error_message: str = None):
        """Log API usage to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO api_usage (endpoint, status_code, response_time_ms, error_message)
                    VALUES (?, ?, ?, ?)
                """, (endpoint, status_code, response_time_ms, error_message))
                conn.commit()
        except Exception as e:
            logger.error(f"Error logging API usage: {e}")
    
    def _generate_demo_fallback_data(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate realistic demo data when API is unavailable"""
        if 'incidentDetails' in url:
            return self._generate_demo_incidents(params)
        elif 'flowSegmentData' in url:
            return self._generate_demo_flow_data(params)
        else:
            return {}
    
    def _generate_demo_incidents(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate demo traffic incidents"""
        # Parse bbox if provided
        bbox = params.get('bbox', '41.8,-71.5,41.85,-71.4').split(',')
        min_lat, min_lon, max_lat, max_lon = map(float, bbox)
        
        # Generate 1-3 random incidents
        num_incidents = random.randint(1, 3)
        incidents = []
        
        incident_types = [
            {"category": "accident", "description": "Vehicle accident blocking right lane"},
            {"category": "roadwork", "description": "Lane closure for emergency repairs"},
            {"category": "congestion", "description": "Heavy traffic congestion"},
            {"category": "weather", "description": "Weather-related slow traffic"},
        ]
        
        for i in range(num_incidents):
            incident_type = random.choice(incident_types)
            lat = random.uniform(min_lat, max_lat)
            lon = random.uniform(min_lon, max_lon)
            
            incident = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat]
                },
                "properties": {
                    "id": f"demo_incident_{uuid.uuid4().hex[:8]}",
                    "iconCategory": incident_type["category"],
                    "magnitudeOfDelay": random.randint(1, 3),
                    "events": [
                        {
                            "description": incident_type["description"],
                            "code": random.randint(100, 999),
                            "iconCategory": incident_type["category"]
                        }
                    ],
                    "startTime": datetime.now().isoformat(),
                    "endTime": (datetime.now() + timedelta(hours=random.randint(1, 4))).isoformat(),
                    "from": "Demo Street",
                    "to": "Demo Avenue",
                    "length": random.randint(100, 500),
                    "delay": random.randint(5, 30),
                    "roadNumbers": ["I-95", "Route 1"],
                    "timeValidity": "continuous"
                }
            }
            incidents.append(incident)
        
        return {"incidents": incidents}
    
    def _generate_demo_flow_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate demo traffic flow data"""
        # Parse point if provided
        point = params.get('point', '41.82,-71.42').split(',')
        lat, lon = map(float, point)
        
        # Generate realistic flow data
        free_flow_speed = random.randint(45, 65)  # mph
        current_speed = random.randint(25, free_flow_speed)  # Current speed <= free flow
        
        return {
            "flowSegmentData": {
                "frc": "FRC3",
                "currentSpeed": current_speed,
                "freeFlowSpeed": free_flow_speed,
                "currentTravelTime": random.randint(60, 180),
                "freeFlowTravelTime": random.randint(45, 120),
                "confidence": random.uniform(0.7, 1.0),
                "roadClosure": False,
                "coordinates": {
                    "coordinate": [
                        {
                            "latitude": lat,
                            "longitude": lon
                        }
                    ]
                }
            }
        }
    
    def collect_traffic_incidents(self, zone: Dict[str, Any]) -> int:
        """Collect traffic incidents for a zone"""
        # Use correct TomTom API format with query parameters
        url = self.config['api_endpoints']['incidents']
        
        params = {
            'bbox': ','.join(map(str, zone['bbox'])),
            'language': 'en-US',
            'categoryFilter': '0,1,2,3,4,5,6,7,8,9,10,11,14',  # All incident types
            'fields': '{incidents{type,geometry{type,coordinates},properties{id,iconCategory,magnitudeOfDelay,events{description,code,iconCategory},startTime,endTime,from,to,length,delay,roadNumbers,timeValidity}}}'
        }
        response = self.make_api_request(url, params)
        
        if not response:
            return 0
        
        incidents_count = 0
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for incident in response.get('incidents', []):
                try:
                    properties = incident.get('properties', {})
                    geometry = incident.get('geometry', {})
                    coordinates = geometry.get('coordinates', [[0, 0]])
                    
                    if isinstance(coordinates[0], list):
                        lat, lon = coordinates[0][1], coordinates[0][0]
                    else:
                        lat, lon = coordinates[1], coordinates[0]
                    
                    events = properties.get('events', [{}])
                    main_event = events[0] if events else {}
                    
                    cursor.execute("""
                        INSERT OR REPLACE INTO traffic_incidents 
                        (external_id, timestamp, latitude, longitude, location, description, 
                         severity, incident_type, delay_minutes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        properties.get('id', f"incident_{int(time.time())}"),
                        datetime.now(),
                        lat, lon,
                        f"{properties.get('from', '')} to {properties.get('to', '')}",
                        main_event.get('description', 'Traffic incident'),
                        min(max(properties.get('magnitudeOfDelay', 0), 1), 5),
                        main_event.get('code', 0),
                        properties.get('delay', 0)
                    ))
                    
                    incidents_count += 1
                    
                except Exception as e:
                    logger.error(f"Error processing incident: {e}")
                    continue
            
            conn.commit()
        
        logger.info(f"Collected {incidents_count} incidents for {zone['name']}")
        return incidents_count
    
    def collect_traffic_flow(self, zone: Dict[str, Any]) -> int:
        """Collect traffic flow for a zone"""
        bbox = zone['bbox']
        center_lat = (bbox[0] + bbox[2]) / 2
        center_lon = (bbox[1] + bbox[3]) / 2
        
        url = f"{self.config['api_endpoints']['flow']}/absolute/10/json"
        params = {
            'point': f"{center_lat},{center_lon}",
            'unit': 'mph'
        }
        
        response = self.make_api_request(url, params)
        
        if not response or 'flowSegmentData' not in response:
            return 0
        
        flow_data = response['flowSegmentData']
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            try:
                cursor.execute("""
                    INSERT INTO traffic_flow 
                    (timestamp, latitude, longitude, location, current_speed_mph, 
                     free_flow_speed_mph, confidence_level, congestion_level)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    datetime.now(),
                    center_lat, center_lon,
                    zone['name'],
                    flow_data.get('currentSpeed', 0),
                    flow_data.get('freeFlowSpeed', 0),
                    flow_data.get('confidence', 0) / 100.0,
                    self._calculate_congestion_level(
                        flow_data.get('currentSpeed', 0),
                        flow_data.get('freeFlowSpeed', 60)
                    )
                ))
                
                conn.commit()
                logger.info(f"Collected flow data for {zone['name']}")
                return 1
                
            except Exception as e:
                logger.error(f"Error saving flow data: {e}")
                return 0
    
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
    
    def collect_zone_data(self, zone: Dict[str, Any]):
        """Collect all data types for a zone"""
        start_time = time.time()
        total_records = 0
        
        try:
            for data_type in zone.get('data_types', []):
                if data_type == 'incidents':
                    records = self.collect_traffic_incidents(zone)
                    total_records += records
                elif data_type == 'flow':
                    records = self.collect_traffic_flow(zone)
                    total_records += records
                
                # Small delay between data types
                time.sleep(1)
            
            duration = time.time() - start_time
            
            # Log collection statistics
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO collection_stats 
                    (zone_name, data_type, records_collected, collection_duration_seconds, success)
                    VALUES (?, ?, ?, ?, ?)
                """, (zone['name'], 'combined', total_records, duration, True))
                conn.commit()
                
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Error collecting data for {zone['name']}: {e}")
            
            # Log failed collection
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO collection_stats 
                    (zone_name, data_type, records_collected, collection_duration_seconds, success)
                    VALUES (?, ?, ?, ?, ?)
                """, (zone['name'], 'combined', 0, duration, False))
                conn.commit()
    
    def collection_cycle(self):
        """Main collection cycle"""
        if not self.check_api_quota():
            logger.warning("Skipping collection cycle - quota exceeded")
            return
        
        logger.info("Starting collection cycle")
        cycle_start = time.time()
        
        for zone in self.config.get('collection_zones', []):
            zone_name = zone['name']
            interval_minutes = zone.get('interval_minutes', 15)
            
            # Check if it's time to collect for this zone
            last_collection = self.last_collection_times.get(zone_name, datetime.min)
            if (datetime.now() - last_collection).total_seconds() >= interval_minutes * 60:
                
                logger.info(f"Collecting data for zone: {zone_name}")
                self.collect_zone_data(zone)
                self.last_collection_times[zone_name] = datetime.now()
        
        cycle_duration = time.time() - cycle_start
        logger.info(f"Collection cycle completed in {cycle_duration:.2f} seconds")
    
    def collection_loop(self):
        """Main collection loop that runs continuously"""
        logger.info("Starting continuous collection loop")
        
        while self.running:
            try:
                self.collection_cycle()
                time.sleep(30)  # Wait 30 seconds between cycles
            except Exception as e:
                logger.error(f"Error in collection loop: {e}")
                time.sleep(60)  # Wait longer on error
        
        logger.info("Collection loop stopped")
    
    def start(self):
        """Start the daemon"""
        if self.running:
            logger.warning("Daemon is already running")
            return
        
        self.running = True
        logger.info("Starting Traffic Collector Daemon")
        
        # Start collection in separate thread
        self.collection_thread = threading.Thread(target=self.collection_loop, daemon=True)
        self.collection_thread.start()
        
        logger.info("Traffic Collector Daemon started successfully")
    
    def stop(self):
        """Stop the daemon gracefully"""
        if not self.running:
            return
        
        logger.info("Stopping Traffic Collector Daemon")
        self.running = False
        
        if self.collection_thread:
            self.collection_thread.join(timeout=10)
        
        logger.info("Traffic Collector Daemon stopped")
    
    def status(self) -> Dict[str, Any]:
        """Get daemon status"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get record counts
            cursor.execute("SELECT COUNT(*) FROM traffic_incidents")
            incidents_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM traffic_flow")
            flow_count = cursor.fetchone()[0]
            
            # Get API usage today
            today = datetime.now().date()
            cursor.execute("SELECT SUM(requests_count) FROM api_usage WHERE DATE(timestamp) = ?", (today,))
            api_usage = cursor.fetchone()[0] or 0
        
        return {
            'running': self.running,
            'api_requests_today': api_usage,
            'daily_quota': self.daily_quota,
            'quota_remaining': self.daily_quota - api_usage,
            'incidents_total': incidents_count,
            'flow_records_total': flow_count,
            'zones_configured': len(self.config.get('collection_zones', [])),
            'last_collection_times': {k: v.isoformat() for k, v in self.last_collection_times.items()}
        }

def main():
    """Main entry point for the daemon"""
    parser = argparse.ArgumentParser(description='Traffic Collector Daemon')
    parser.add_argument('action', choices=['start', 'stop', 'status', 'restart'], 
                       help='Action to perform')
    parser.add_argument('--config', default='/etc/traffic-collector/config.yaml',
                       help='Path to configuration file')
    parser.add_argument('--foreground', action='store_true',
                       help='Run in foreground (don\'t daemonize)')
    
    args = parser.parse_args()
    
    daemon = CollectorDaemon(args.config)
    
    if args.action == 'start':
        daemon.start()
        if args.foreground:
            try:
                while daemon.running:
                    time.sleep(1)
            except KeyboardInterrupt:
                daemon.stop()
        else:
            # In production, this would properly daemonize
            logger.info("Daemon started (use --foreground for interactive mode)")
    
    elif args.action == 'stop':
        daemon.stop()
    
    elif args.action == 'status':
        status = daemon.status()
        print(json.dumps(status, indent=2))
    
    elif args.action == 'restart':
        daemon.stop()
        time.sleep(2)
        daemon.start()

if __name__ == "__main__":
    main()