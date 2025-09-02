# utils/database.py - SQLite Database Manager for Traffic Data

import sqlite3
import pandas as pd
import datetime
import os
import time
import logging
from typing import List, Dict, Optional, Tuple
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TrafficDatabase:
    """
    Comprehensive database manager for traffic data storage and retrieval
    Handles incidents, traffic flow, API usage tracking, and analytics
    """
    
    def __init__(self, db_path: str = "data/traffic_data.db", read_only: bool = False):
        """Initialize database connection and create tables if needed"""
        self.db_path = db_path
        self.read_only = read_only
        
        if not read_only:
            # Ensure data directory exists
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
            # Initialize database
            self._create_tables()
            logger.info(f"Database initialized at {db_path}")
        else:
            logger.info(f"Database connected in read-only mode at {db_path}")
    
    def _create_tables(self):
        """Create all necessary tables for traffic data storage"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Traffic Incidents Table - Enhanced schema
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS traffic_incidents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    external_id TEXT UNIQUE,
                    timestamp TIMESTAMP NOT NULL,
                    collection_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    location TEXT NOT NULL,
                    location_numerical INTEGER,
                    description TEXT NOT NULL,
                    severity INTEGER NOT NULL,
                    incident_type INTEGER NOT NULL,
                    length_hours REAL,
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    delay_minutes REAL,
                    
                    -- Temporal analysis fields
                    hour INTEGER,
                    day_of_week TEXT,
                    is_weekend BOOLEAN,
                    is_holiday BOOLEAN,
                    morning_rush BOOLEAN,
                    evening_rush BOOLEAN,
                    rush_hour BOOLEAN,
                    
                    -- Weather and conditions
                    weather_condition TEXT,
                    temperature_f REAL,
                    precipitation_inch REAL,
                    visibility_miles REAL,
                    
                    -- Aggregation fields
                    incidents_per_town_hour INTEGER,
                    incidents_per_type INTEGER,
                    
                    -- Data quality
                    data_source TEXT DEFAULT 'tomtom',
                    data_quality_score REAL DEFAULT 1.0,
                    is_verified BOOLEAN DEFAULT FALSE,
                    
                    UNIQUE(external_id, timestamp)
                )
            """)
            
            # Traffic Flow Table - Real-time speed/volume data
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS traffic_flow (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP NOT NULL,
                    collection_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    road_name TEXT,
                    road_type TEXT,
                    speed_limit_mph INTEGER,
                    current_speed_mph REAL,
                    free_flow_speed_mph REAL,
                    confidence_level REAL,
                    travel_time_minutes REAL,
                    
                    -- Traffic metrics
                    congestion_level INTEGER, -- 0=free, 1=light, 2=moderate, 3=heavy, 4=severe
                    volume_vehicles_hour INTEGER,
                    occupancy_percent REAL,
                    
                    -- Road characteristics
                    num_lanes INTEGER,
                    road_closure BOOLEAN DEFAULT FALSE,
                    construction_zone BOOLEAN DEFAULT FALSE,
                    
                    -- Data quality
                    data_source TEXT DEFAULT 'tomtom',
                    data_quality_score REAL DEFAULT 1.0
                )
            """)
            
            # API Usage Tracking Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS api_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    api_endpoint TEXT NOT NULL,
                    request_count INTEGER NOT NULL,
                    response_time_ms INTEGER,
                    status_code INTEGER,
                    error_message TEXT,
                    daily_quota_used INTEGER,
                    monthly_quota_used INTEGER,
                    
                    -- Rate limiting
                    requests_per_minute INTEGER,
                    quota_reset_time TIMESTAMP,
                    
                    -- Cost tracking
                    estimated_cost_usd REAL DEFAULT 0.0,
                    is_free_tier BOOLEAN DEFAULT TRUE
                )
            """)
            
            # Data Collection Schedule Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS collection_schedule (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data_type TEXT NOT NULL, -- 'incidents', 'flow', 'weather'
                    last_collection TIMESTAMP,
                    next_collection TIMESTAMP,
                    collection_interval_minutes INTEGER,
                    is_active BOOLEAN DEFAULT TRUE,
                    priority_level INTEGER DEFAULT 1, -- 1=high, 2=medium, 3=low
                    
                    -- Adaptive scheduling
                    peak_hours TEXT, -- JSON array of hour ranges
                    weekend_interval_minutes INTEGER,
                    holiday_interval_minutes INTEGER,
                    
                    -- Success tracking
                    successful_collections INTEGER DEFAULT 0,
                    failed_collections INTEGER DEFAULT 0,
                    last_error TEXT
                )
            """)
            
            # Geographic Zones Table - For targeted data collection
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS geographic_zones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    zone_name TEXT NOT NULL UNIQUE,
                    zone_type TEXT NOT NULL, -- 'city', 'highway', 'intersection', 'custom'
                    bounding_box TEXT NOT NULL, -- JSON: {north, south, east, west}
                    center_lat REAL,
                    center_lng REAL,
                    priority_level INTEGER DEFAULT 1,
                    collection_frequency_minutes INTEGER DEFAULT 15,
                    is_active BOOLEAN DEFAULT TRUE,
                    
                    -- Zone characteristics
                    population INTEGER,
                    typical_traffic_volume TEXT, -- 'low', 'medium', 'high'
                    special_events_calendar TEXT, -- JSON array
                    
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Data Quality Metrics Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS data_quality (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    table_name TEXT NOT NULL,
                    total_records INTEGER,
                    missing_values INTEGER,
                    duplicate_records INTEGER,
                    anomalous_values INTEGER,
                    quality_score REAL, -- 0.0 to 1.0
                    
                    -- Specific quality checks
                    coordinate_accuracy REAL,
                    timestamp_consistency REAL,
                    data_freshness_hours REAL,
                    source_reliability REAL,
                    
                    -- Quality flags
                    needs_cleanup BOOLEAN DEFAULT FALSE,
                    verified_quality BOOLEAN DEFAULT FALSE
                )
            """)
            
            # Create indexes for performance
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_incidents_timestamp ON traffic_incidents(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_incidents_location ON traffic_incidents(location)",
                "CREATE INDEX IF NOT EXISTS idx_incidents_severity ON traffic_incidents(severity)",
                "CREATE INDEX IF NOT EXISTS idx_incidents_rush ON traffic_incidents(rush_hour)",
                "CREATE INDEX IF NOT EXISTS idx_flow_timestamp ON traffic_flow(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_flow_coordinates ON traffic_flow(latitude, longitude)",
                "CREATE INDEX IF NOT EXISTS idx_api_usage_timestamp ON api_usage(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_api_usage_endpoint ON api_usage(api_endpoint)"
            ]
            
            for index in indexes:
                cursor.execute(index)
            
            conn.commit()
            logger.info("Database tables and indexes created successfully")
    
    def insert_traffic_incident(self, incident: Dict) -> bool:
        """Insert a single traffic incident into the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Calculate derived fields
                timestamp = pd.to_datetime(incident['timestamp'])
                
                cursor.execute("""
                    INSERT OR REPLACE INTO traffic_incidents (
                        external_id, timestamp, latitude, longitude, location,
                        description, severity, incident_type, length_hours,
                        hour, day_of_week, is_weekend, morning_rush, evening_rush, rush_hour,
                        location_numerical, incidents_per_town_hour, incidents_per_type, data_source
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    incident.get('external_id', incident.get('id')),
                    timestamp.to_pydatetime() if hasattr(timestamp, 'to_pydatetime') else timestamp,
                    incident['latitude'],
                    incident['longitude'],
                    incident['location'],
                    incident['description'],
                    incident['severity'],
                    incident.get('type', 1),
                    incident.get('Length_of_Time(Hours)', 0),
                    timestamp.hour,
                    timestamp.day_name(),
                    timestamp.weekday() >= 5,  # Weekend
                    7 <= timestamp.hour <= 9,  # Morning rush
                    16 <= timestamp.hour <= 18,  # Evening rush
                    (7 <= timestamp.hour <= 9) or (16 <= timestamp.hour <= 18),  # Any rush
                    incident.get('location_numerical', 0),
                    incident.get('incidents_per_town_hour', 0),
                    incident.get('incidents_per_type', 0),
                    incident.get('data_source', 'tomtom_api')  # Default to API source
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error inserting incident: {e}")
            return False
    
    def insert_traffic_flow(self, flow_data: Dict) -> bool:
        """Insert traffic flow data into the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Convert timestamp if it's a pandas Timestamp
                timestamp = flow_data['timestamp']
                if hasattr(timestamp, 'to_pydatetime'):
                    timestamp = timestamp.to_pydatetime()
                
                cursor.execute("""
                    INSERT INTO traffic_flow (
                        timestamp, latitude, longitude, road_name, road_type,
                        speed_limit_mph, current_speed_mph, free_flow_speed_mph,
                        confidence_level, congestion_level, travel_time_minutes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    timestamp,
                    flow_data['latitude'],
                    flow_data['longitude'],
                    flow_data.get('road_name', ''),
                    flow_data.get('road_type', ''),
                    flow_data.get('speed_limit_mph', 0),
                    flow_data.get('current_speed_mph', 0),
                    flow_data.get('free_flow_speed_mph', 0),
                    flow_data.get('confidence_level', 0.0),
                    flow_data.get('congestion_level', 0),
                    flow_data.get('travel_time_minutes', 0)
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error inserting traffic flow: {e}")
            return False
    
    def log_api_usage(self, endpoint: str, request_count: int = 1, 
                     response_time_ms: int = 0, status_code: int = 200,
                     error_message: str = None) -> bool:
        """Log API usage for quota tracking"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get today's usage
                today = datetime.date.today()
                cursor.execute("""
                    SELECT COALESCE(SUM(request_count), 0) 
                    FROM api_usage 
                    WHERE DATE(timestamp) = ? AND api_endpoint = ?
                """, (today, endpoint))
                
                daily_used = cursor.fetchone()[0] + request_count
                
                # Get this month's usage
                month_start = today.replace(day=1)
                cursor.execute("""
                    SELECT COALESCE(SUM(request_count), 0) 
                    FROM api_usage 
                    WHERE DATE(timestamp) >= ? AND api_endpoint = ?
                """, (month_start, endpoint))
                
                monthly_used = cursor.fetchone()[0] + request_count
                
                # Insert usage record
                cursor.execute("""
                    INSERT INTO api_usage (
                        api_endpoint, request_count, response_time_ms, status_code,
                        error_message, daily_quota_used, monthly_quota_used
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    endpoint, request_count, response_time_ms, status_code,
                    error_message, daily_used, monthly_used
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error logging API usage: {e}")
            return False
    
    def get_daily_api_usage(self, date: datetime.date = None) -> Dict:
        """Get API usage statistics for a specific date"""
        if date is None:
            date = datetime.date.today()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        api_endpoint,
                        SUM(request_count) as total_requests,
                        AVG(response_time_ms) as avg_response_time,
                        COUNT(*) as call_count,
                        SUM(CASE WHEN status_code != 200 THEN 1 ELSE 0 END) as error_count
                    FROM api_usage 
                    WHERE DATE(timestamp) = ?
                    GROUP BY api_endpoint
                """, (date,))
                
                results = cursor.fetchall()
                
                return {
                    'date': date,
                    'endpoints': {
                        row[0]: {
                            'total_requests': row[1],
                            'avg_response_time_ms': row[2],
                            'call_count': row[3],
                            'error_count': row[4]
                        }
                        for row in results
                    },
                    'total_requests': sum(row[1] for row in results),
                    'free_tier_limit': 50000,
                    'usage_percentage': (sum(row[1] for row in results) / 50000) * 100
                }
                
        except Exception as e:
            logger.error(f"Error getting API usage: {e}")
            return {}
    
    def get_traffic_incidents(self, 
                            start_date: datetime.date = None,
                            end_date: datetime.date = None,
                            location: str = None,
                            min_severity: int = None) -> pd.DataFrame:
        """Retrieve traffic incidents with filtering options"""
        
        try:
            # Select with column aliases to match expected format
            query = """
                SELECT 
                    id,
                    external_id,
                    timestamp,
                    latitude as lat,
                    longitude as lng,
                    location,
                    description,
                    severity,
                    incident_type as type,
                    length_hours as "Length_of_Time(Hours)",
                    hour,
                    day_of_week,
                    is_weekend,
                    morning_rush,
                    evening_rush,
                    rush_hour as rush,
                    location_numerical,
                    incidents_per_town_hour,
                    incidents_per_type,
                    data_source,
                    collection_time
                FROM traffic_incidents 
                WHERE data_source = 'tomtom_api'
            """
            params = []
            
            if start_date:
                query += " AND DATE(timestamp) >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND DATE(timestamp) <= ?"
                params.append(end_date)
            
            if location:
                query += " AND location = ?"
                params.append(location)
            
            if min_severity:
                query += " AND severity >= ?"
                params.append(min_severity)
            
            query += " ORDER BY timestamp DESC"
            
            # Use connection with timeout for better reliability
            conn = sqlite3.connect(self.db_path, timeout=10.0)
            try:
                df = pd.read_sql_query(query, conn, params=params)
                
                # Ensure expected columns exist
                if not df.empty:
                    # Convert timestamp to datetime
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    
                    # Add derived fields if missing
                    if 'date' not in df.columns:
                        df['date'] = df['timestamp'].dt.date
                    if 'hour' not in df.columns:
                        df['hour'] = df['timestamp'].dt.hour
                
                return df
            finally:
                conn.close()
                
        except Exception as e:
            logger.error(f"Error retrieving incidents: {e}")
            return pd.DataFrame()
    
    def get_traffic_flow(self, 
                        start_date: datetime.date = None,
                        end_date: datetime.date = None,
                        min_congestion_level: int = None,
                        road_name: str = None) -> pd.DataFrame:
        """Retrieve traffic flow data with filtering options"""
        
        try:
            query = """
                SELECT 
                    id,
                    timestamp,
                    latitude,
                    longitude,
                    location,
                    current_speed_mph,
                    free_flow_speed_mph,
                    confidence_level,
                    congestion_level,
                    data_source,
                    collection_time
                FROM traffic_flow 
                WHERE 1=1
            """
            params = []
            
            if start_date:
                query += " AND DATE(timestamp) >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND DATE(timestamp) <= ?"
                params.append(end_date)
            
            if min_congestion_level is not None:
                query += " AND congestion_level >= ?"
                params.append(min_congestion_level)
                
            if road_name:
                query += " AND location LIKE ?"
                params.append(f"%{road_name}%")
            
            query += " ORDER BY timestamp DESC"
            
            # Use connection with timeout for better reliability
            conn = sqlite3.connect(self.db_path, timeout=10.0)
            try:
                df = pd.read_sql_query(query, conn, params=params)
                
                if not df.empty:
                    # Convert timestamp to datetime
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    
                    # Calculate speed ratio for visualization
                    df['speed_ratio'] = df['current_speed_mph'] / df['free_flow_speed_mph'].replace(0, 1)
                    df['speed_ratio'] = df['speed_ratio'].clip(0, 1)
                
                return df
            finally:
                conn.close()
                
        except Exception as e:
            logger.error(f"Error retrieving traffic flow: {e}")
            return pd.DataFrame()
    
    def get_database_stats(self) -> Dict:
        """Get comprehensive database statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get record counts for each table
                tables = ['traffic_incidents', 'traffic_flow', 'api_usage', 'collection_schedule']
                stats = {}
                
                for table in tables:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        stats[f"{table}_count"] = cursor.fetchone()[0]
                    except sqlite3.OperationalError:
                        stats[f"{table}_count"] = 0
                
                # Get date range of real API data only
                cursor.execute("""
                    SELECT MIN(timestamp), MAX(timestamp) 
                    FROM traffic_incidents 
                    WHERE data_source = 'tomtom_api'
                """)
                date_range = cursor.fetchone()
                stats['data_date_range'] = {
                    'earliest': date_range[0] if date_range[0] else None,
                    'latest': date_range[1] if date_range[1] else None
                }
                
                # Calculate data accumulation metrics
                if date_range[0] and date_range[1]:
                    from datetime import datetime
                    start_date = datetime.fromisoformat(date_range[0])
                    end_date = datetime.fromisoformat(date_range[1])
                    days_collected = (end_date - start_date).days + 1
                    stats['collection_days'] = days_collected
                    stats['daily_average_incidents'] = stats['traffic_incidents_count'] / max(days_collected, 1)
                else:
                    stats['collection_days'] = 0
                    stats['daily_average_incidents'] = 0
                
                # Get database file size
                stats['database_size_mb'] = os.path.getsize(self.db_path) / (1024 * 1024)
                
                return stats
                
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {}
    
    def cleanup_old_data(self, days_to_keep: int = 90) -> int:
        """Remove data older than specified days to manage database size"""
        try:
            cutoff_date = datetime.date.today() - datetime.timedelta(days=days_to_keep)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Clean up old incidents
                cursor.execute("DELETE FROM traffic_incidents WHERE DATE(timestamp) < ?", (cutoff_date,))
                incidents_deleted = cursor.rowcount
                
                # Clean up old flow data
                cursor.execute("DELETE FROM traffic_flow WHERE DATE(timestamp) < ?", (cutoff_date,))
                flow_deleted = cursor.rowcount
                
                # Clean up old API usage (keep longer for analytics)
                api_cutoff = datetime.date.today() - datetime.timedelta(days=365)
                cursor.execute("DELETE FROM api_usage WHERE DATE(timestamp) < ?", (api_cutoff,))
                api_deleted = cursor.rowcount
                
                # Vacuum database to reclaim space
                cursor.execute("VACUUM")
                
                conn.commit()
                
                total_deleted = incidents_deleted + flow_deleted + api_deleted
                logger.info(f"Cleaned up {total_deleted} old records (incidents: {incidents_deleted}, flow: {flow_deleted}, api: {api_deleted})")
                
                return total_deleted
                
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            return 0

# Utility functions for easy database access
def get_database() -> TrafficDatabase:
    """Get a database instance (singleton pattern) with robust error handling"""
    if not hasattr(get_database, '_instance'):
        # Check if database file exists and is readable/writable
        db_path = "data/traffic_data.db"
        
        # Try different fallback strategies
        for attempt in range(3):
            try:
                # Test if we can read from the database first
                if os.path.exists(db_path):
                    test_conn = sqlite3.connect(db_path, timeout=5.0)
                    test_conn.execute("SELECT 1")
                    
                    # Test if we can write
                    try:
                        test_conn.execute("CREATE TABLE IF NOT EXISTS test_write (id INTEGER)")
                        test_conn.commit()
                        test_conn.close()
                        # If successful, use normal mode
                        get_database._instance = TrafficDatabase(db_path, read_only=False)
                        logger.info("Database initialized in read-write mode")
                        break
                    except (sqlite3.OperationalError, PermissionError):
                        test_conn.close()
                        # If write fails, use read-only mode
                        logger.info("Database opened in read-only mode due to permissions")
                        get_database._instance = TrafficDatabase(db_path, read_only=True)
                        break
                else:
                    # Database doesn't exist, try to create it
                    get_database._instance = TrafficDatabase(db_path, read_only=False)
                    logger.info("Database created successfully")
                    break
                    
            except Exception as e:
                logger.warning(f"Database connection attempt {attempt + 1} failed: {e}")
                if attempt < 2:  # Not the last attempt
                    time.sleep(1)  # Wait before retry
                else:
                    # Last resort: create in-memory database for demo continuity
                    logger.error("All database connection attempts failed, using in-memory database")
                    get_database._instance = TrafficDatabase(":memory:", read_only=False)
                    # Populate with basic schema for demo
                    get_database._instance._create_tables()
    
    return get_database._instance

def initialize_default_zones():
    """Initialize default geographic zones for Rhode Island"""
    db = get_database()
    
    # Rhode Island zones
    zones = [
        {
            'zone_name': 'Providence Metro',
            'zone_type': 'city',
            'bounding_box': json.dumps({
                'north': 41.9,
                'south': 41.7,
                'east': -71.3,
                'west': -71.5
            }),
            'center_lat': 41.8236,
            'center_lng': -71.4222,
            'collection_frequency_minutes': 5,  # High frequency for major city
            'population': 190934
        },
        {
            'zone_name': 'I-95 Corridor',
            'zone_type': 'highway',
            'bounding_box': json.dumps({
                'north': 42.0,
                'south': 41.3,
                'east': -71.1,
                'west': -71.9
            }),
            'center_lat': 41.65,
            'center_lng': -71.5,
            'collection_frequency_minutes': 3,  # Very high frequency for major highway
            'typical_traffic_volume': 'high'
        },
        {
            'zone_name': 'Route 95 Warwick',
            'zone_type': 'intersection',
            'bounding_box': json.dumps({
                'north': 41.75,
                'south': 41.65,
                'east': -71.4,
                'west': -71.5
            }),
            'center_lat': 41.7,
            'center_lng': -71.45,
            'collection_frequency_minutes': 10,
            'population': 82823
        }
    ]
    
    try:
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.cursor()
            
            for zone in zones:
                cursor.execute("""
                    INSERT OR REPLACE INTO geographic_zones (
                        zone_name, zone_type, bounding_box, center_lat, center_lng,
                        collection_frequency_minutes, population, typical_traffic_volume
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    zone['zone_name'],
                    zone['zone_type'],
                    zone['bounding_box'],
                    zone['center_lat'],
                    zone['center_lng'],
                    zone['collection_frequency_minutes'],
                    zone.get('population'),
                    zone.get('typical_traffic_volume', 'medium')
                ))
            
            conn.commit()
            logger.info(f"Initialized {len(zones)} default geographic zones")
            
    except Exception as e:
        logger.error(f"Error initializing zones: {e}")

if __name__ == "__main__":
    # Test database functionality
    db = TrafficDatabase()
    print("Database initialized successfully")
    print("Database stats:", db.get_database_stats())
    
    # Initialize default zones
    initialize_default_zones()
    print("Default zones initialized")