# Data Collection Engine - Deep Dive

## Overview

The Village Platform's data collection engine is a sophisticated system that continuously gathers traffic data from multiple sources, with the TomTom Traffic API as the primary data provider. The system is designed for 24/7 operation with intelligent scheduling, quota management, and fault tolerance.

## Architecture

### Core Components

```python
# Primary collection modules
- enhanced_traffic_collector.py    # Main TomTom API integration
- statewide_traffic_collector.py   # State-wide data collection
- historical_traffic_collector.py  # Historical pattern analysis
- origin_destination_collector.py  # O/D matrix generation
- data_collection_manager.py       # Orchestration and scheduling
- traffic_collector_daemon.py      # VM-optimized standalone service
```

## Enhanced Traffic Collector

### Collection Zones

The system divides Rhode Island into 11 prioritized collection zones:

```python
COLLECTION_ZONES = [
    # Priority 1 - Critical Infrastructure
    {
        "name": "I-95_Providence_Corridor",
        "bbox": [41.7, -71.6, 41.9, -71.3],
        "priority": 1,
        "interval_minutes": 3,
        "data_types": ["flow", "incidents", "routes"]
    },
    {
        "name": "I-195_East_West",
        "bbox": [41.6, -71.5, 41.8, -71.1],
        "priority": 1,
        "interval_minutes": 5,
        "data_types": ["flow", "incidents"]
    },
    
    # Priority 2 - Urban Centers
    {
        "name": "Providence_Downtown",
        "bbox": [41.81, -71.43, 41.84, -71.40],
        "priority": 2,
        "interval_minutes": 8,
        "data_types": ["flow", "incidents", "congestion"]
    },
    
    # Priority 3 - Secondary Roads
    {
        "name": "Route_1_Coastal",
        "bbox": [41.3, -71.6, 41.7, -71.4],
        "priority": 3,
        "interval_minutes": 15,
        "data_types": ["flow", "incidents"]
    }
    
    # ... additional zones
]
```

### Adaptive Scheduling

The collection system adjusts frequency based on various factors:

```python
class AdaptiveScheduler:
    """Intelligent scheduling based on context"""
    
    def calculate_interval(self, zone, current_time):
        base_interval = zone['interval_minutes']
        
        # Time-based adjustments
        if self.is_rush_hour(current_time):
            multiplier = 0.6  # Collect more frequently
        elif self.is_weekend(current_time):
            multiplier = 1.5  # Collect less frequently
        elif self.is_holiday(current_time):
            multiplier = 2.0  # Minimal collection
        else:
            multiplier = 1.0
            
        # Quota-based adjustments
        quota_usage = self.get_quota_usage()
        if quota_usage > 0.9:
            multiplier *= 3.0  # Dramatically reduce
        elif quota_usage > 0.75:
            multiplier *= 1.5  # Moderately reduce
            
        return int(base_interval * multiplier)
```

### API Integration

#### TomTom Traffic Incidents
```python
def collect_traffic_incidents(self, zone):
    """Collect traffic incidents for a specific zone"""
    
    # Build API request
    bbox = ','.join(map(str, zone['bbox']))
    url = f"{self.incidents_endpoint}/s3/{bbox}/10/-1/json"
    
    params = {
        'key': self.api_key,
        'language': 'en-US',
        'categoryFilter': '0,1,2,3,4,5,6,7,8,9,10,11,14',
        'timeValidityFilter': 'present'
    }
    
    # Make request with error handling
    response = self.make_api_request(url, params)
    
    if response and 'incidents' in response:
        incidents = self.process_incidents(response['incidents'])
        self.store_incidents(incidents)
        return len(incidents)
    
    return 0
```

#### Traffic Flow Data
```python
def collect_traffic_flow(self, zone):
    """Collect real-time traffic flow data"""
    
    # Calculate zone center point
    bbox = zone['bbox']
    center_lat = (bbox[0] + bbox[2]) / 2
    center_lon = (bbox[1] + bbox[3]) / 2
    
    url = f"{self.flow_endpoint}/absolute/10/json"
    params = {
        'key': self.api_key,
        'point': f"{center_lat},{center_lon}",
        'unit': 'mph',
        'thickness': 10
    }
    
    response = self.make_api_request(url, params)
    
    if response and 'flowSegmentData' in response:
        flow_data = self.process_flow_data(response['flowSegmentData'])
        self.store_flow_data(flow_data, zone)
        return 1
    
    return 0
```

### Data Processing Pipeline

#### Incident Processing
```python
def process_incidents(self, raw_incidents):
    """Transform raw API data into structured incidents"""
    
    processed = []
    for incident in raw_incidents:
        try:
            # Extract coordinates
            geometry = incident.get('geometry', {})
            coordinates = geometry.get('coordinates', [[0, 0]])
            
            if isinstance(coordinates[0], list):
                lat, lng = coordinates[0][1], coordinates[0][0]
            else:
                lat, lng = coordinates[1], coordinates[0]
            
            # Extract incident details
            properties = incident.get('properties', {})
            events = properties.get('events', [{}])
            main_event = events[0] if events else {}
            
            # Create structured incident
            processed_incident = {
                'external_id': properties.get('id'),
                'timestamp': datetime.now(),
                'latitude': lat,
                'longitude': lng,
                'location': f"{properties.get('from', '')} to {properties.get('to', '')}".strip(),
                'description': main_event.get('description', 'Traffic incident'),
                'severity': self.calculate_severity(properties),
                'incident_type': main_event.get('code', 0),
                'delay_minutes': properties.get('delay', 0),
                'length_meters': properties.get('length', 0),
                'data_source': 'tomtom'
            }
            
            processed.append(processed_incident)
            
        except Exception as e:
            self.logger.error(f"Error processing incident: {e}")
            continue
    
    return processed
```

#### Severity Calculation
```python
def calculate_severity(self, properties):
    """Calculate incident severity (1-5 scale)"""
    
    # Base severity from magnitude of delay
    magnitude = properties.get('magnitudeOfDelay', 0)
    
    # Factors that increase severity
    factors = {
        'delay': properties.get('delay', 0),
        'length': properties.get('length', 0),
        'events_count': len(properties.get('events', [])),
        'road_type': self.classify_road_importance(properties.get('from', ''))
    }
    
    # Calculate weighted severity
    severity = min(max(magnitude, 1), 3)  # Base 1-3
    
    if factors['delay'] > 30:  # 30+ minute delays
        severity += 1
    if factors['length'] > 5000:  # 5km+ incidents
        severity += 1
    if factors['road_type'] == 'highway':  # Major highways
        severity += 1
        
    return min(severity, 5)  # Cap at 5
```

### Error Handling & Recovery

#### Credit Exhaustion Management
```python
class CreditManager:
    """Manage API credit exhaustion scenarios"""
    
    def handle_credit_exhaustion(self):
        """Handle when API credits are exhausted"""
        
        # Stop all collection immediately
        self.stop_collection_due_to_credits = True
        
        # Log critical event
        self.logger.error("🚨 CRITICAL: TomTom API credits exhausted!")
        
        # Notify administrators
        self.send_admin_notification({
            'type': 'CREDIT_EXHAUSTION',
            'timestamp': datetime.now(),
            'remaining_quota': 0,
            'next_reset': self.get_quota_reset_time()
        })
        
        # Set flag in database
        self.db.execute(
            "UPDATE api_status SET credit_exhausted = 1, exhausted_at = ?",
            (datetime.now(),)
        )
        
        # Schedule recovery check
        self.schedule_recovery_check()
```

#### Retry Logic
```python
def make_api_request_with_retry(self, url, params, max_retries=3):
    """Make API request with exponential backoff retry"""
    
    for attempt in range(max_retries):
        try:
            response = requests.get(
                url, 
                params=params, 
                timeout=30,
                headers={'User-Agent': 'Village-Platform/1.0'}
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 403:
                # Check if it's credit exhaustion
                if 'quota' in response.text.lower():
                    self.handle_credit_exhaustion()
                    return None
            elif response.status_code == 429:
                # Rate limiting - wait longer
                wait_time = (2 ** attempt) * 2
                time.sleep(wait_time)
                continue
            else:
                self.logger.warning(f"API request failed: {response.status_code}")
                
        except requests.exceptions.Timeout:
            wait_time = 2 ** attempt
            time.sleep(wait_time)
        except requests.exceptions.ConnectionError:
            wait_time = (2 ** attempt) * 3
            time.sleep(wait_time)
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            break
    
    return None
```

## Daemon Service (VM Deployment)

### Architecture
```python
class CollectorDaemon:
    """VM-optimized standalone collection service"""
    
    def __init__(self, config_path):
        self.config = self.load_config(config_path)
        self.running = False
        self.collection_thread = None
        
        # Signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def collection_loop(self):
        """Main collection loop"""
        while self.running:
            try:
                self.collection_cycle()
                time.sleep(30)  # Base cycle interval
            except Exception as e:
                self.logger.error(f"Collection cycle error: {e}")
                time.sleep(60)  # Wait longer on error
```

### Service Management
```bash
# Systemd service configuration
[Unit]
Description=Traffic Data Collector Service
After=network-online.target

[Service]
Type=simple
User=traffic-collector
ExecStart=/opt/traffic-collector/venv/bin/python traffic_collector_daemon.py start --foreground
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
```

## Data Storage

### Database Schema
```sql
-- Traffic incidents storage
CREATE TABLE traffic_incidents (
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
    length_meters REAL,
    data_source TEXT DEFAULT 'tomtom',
    ai_analysis TEXT,
    processed BOOLEAN DEFAULT FALSE
);

-- Traffic flow data
CREATE TABLE traffic_flow (
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
    travel_time_seconds INTEGER,
    data_source TEXT DEFAULT 'tomtom'
);

-- API usage tracking
CREATE TABLE api_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    endpoint TEXT NOT NULL,
    status_code INTEGER,
    response_time_ms INTEGER,
    error_message TEXT,
    requests_count INTEGER DEFAULT 1
);
```

### Data Quality Assurance
```python
class DataQualityManager:
    """Ensure data quality and integrity"""
    
    def validate_incident(self, incident):
        """Validate incident data before storage"""
        
        checks = {
            'coordinates': self.validate_coordinates(
                incident['latitude'], 
                incident['longitude']
            ),
            'timestamp': self.validate_timestamp(incident['timestamp']),
            'severity': 1 <= incident['severity'] <= 5,
            'description': len(incident['description']) > 0
        }
        
        return all(checks.values()), checks
    
    def detect_duplicates(self, incident):
        """Detect potential duplicate incidents"""
        
        # Check for incidents within 100m and 15 minutes
        similar = self.db.execute("""
            SELECT id FROM traffic_incidents 
            WHERE ABS(latitude - ?) < 0.001 
            AND ABS(longitude - ?) < 0.001
            AND ABS(strftime('%s', timestamp) - strftime('%s', ?)) < 900
        """, (incident['latitude'], incident['longitude'], incident['timestamp']))
        
        return len(similar) > 0
```

## Performance Optimization

### Caching Strategy
```python
class CollectionCache:
    """Cache management for collection efficiency"""
    
    def __init__(self):
        self.incident_cache = {}
        self.flow_cache = {}
        self.cache_ttl = 300  # 5 minutes
    
    def get_cached_incidents(self, zone_id):
        """Get cached incidents if still valid"""
        
        if zone_id in self.incident_cache:
            cached_time, data = self.incident_cache[zone_id]
            if (datetime.now() - cached_time).seconds < self.cache_ttl:
                return data
        
        return None
    
    def cache_incidents(self, zone_id, incidents):
        """Cache incidents for zone"""
        self.incident_cache[zone_id] = (datetime.now(), incidents)
```

### Batch Processing
```python
def batch_store_incidents(self, incidents):
    """Efficiently store multiple incidents"""
    
    if not incidents:
        return
    
    # Prepare batch insert
    placeholders = ','.join(['(?,?,?,?,?,?,?,?,?,?)'] * len(incidents))
    
    values = []
    for incident in incidents:
        values.extend([
            incident['external_id'],
            incident['timestamp'],
            incident['latitude'],
            incident['longitude'],
            incident['location'],
            incident['description'],
            incident['severity'],
            incident['incident_type'],
            incident['delay_minutes'],
            incident['data_source']
        ])
    
    # Execute batch insert
    self.db.execute(f"""
        INSERT OR REPLACE INTO traffic_incidents 
        (external_id, timestamp, latitude, longitude, location, 
         description, severity, incident_type, delay_minutes, data_source)
        VALUES {placeholders}
    """, values)
```

## Monitoring & Analytics

### Collection Metrics
```python
class CollectionMetrics:
    """Track collection performance and health"""
    
    def record_collection_stats(self, zone, success, records_collected, duration):
        """Record collection statistics"""
        
        self.db.execute("""
            INSERT INTO collection_stats 
            (timestamp, zone_name, success, records_collected, 
             collection_duration_seconds, api_requests_used)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(),
            zone['name'],
            success,
            records_collected,
            duration,
            1  # One API request per collection
        ))
    
    def get_collection_health(self):
        """Get overall collection system health"""
        
        # Success rate last 24 hours
        success_rate = self.db.execute("""
            SELECT AVG(CAST(success AS FLOAT)) * 100 as success_rate
            FROM collection_stats 
            WHERE timestamp > datetime('now', '-24 hours')
        """).fetchone()[0]
        
        # Records collected today
        records_today = self.db.execute("""
            SELECT SUM(records_collected) 
            FROM collection_stats 
            WHERE DATE(timestamp) = DATE('now')
        """).fetchone()[0]
        
        # API quota usage
        quota_used = self.get_daily_api_usage()
        
        return {
            'success_rate': success_rate or 0,
            'records_collected_today': records_today or 0,
            'api_quota_used': quota_used,
            'quota_remaining': 50000 - quota_used,
            'health_score': self.calculate_health_score(success_rate, quota_used)
        }
```

### Alert System
```python
def check_collection_alerts(self):
    """Monitor for collection issues requiring attention"""
    
    alerts = []
    
    # Check quota usage
    quota_usage = self.get_quota_usage_percentage()
    if quota_usage > 90:
        alerts.append({
            'type': 'QUOTA_CRITICAL',
            'message': f"API quota at {quota_usage}%",
            'severity': 'high'
        })
    
    # Check success rate
    success_rate = self.get_recent_success_rate()
    if success_rate < 80:
        alerts.append({
            'type': 'SUCCESS_RATE_LOW',
            'message': f"Collection success rate: {success_rate}%",
            'severity': 'medium'
        })
    
    # Check data freshness
    last_collection = self.get_last_successful_collection()
    if last_collection and (datetime.now() - last_collection).minutes > 30:
        alerts.append({
            'type': 'STALE_DATA',
            'message': "No successful collection in 30+ minutes",
            'severity': 'high'
        })
    
    return alerts
```

This data collection engine provides robust, scalable traffic data gathering with intelligent scheduling, comprehensive error handling, and enterprise-grade monitoring capabilities.