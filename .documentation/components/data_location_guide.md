# Village Platform: Data Storage Location Guide

## 📍 Where Your Traffic Data Is Saved

When you run the data collection module, your traffic incident data flows through multiple components and gets stored in specific database files. Here's the complete data flow:

## Primary Data Storage Locations

### 1. **Main Database (Used by UI)**
```
📁 /data/traffic_data.db
```
- **Used by**: All UI pages (Live Traffic, Analytics, etc.)
- **Managed by**: `code/utils/database.py` (TrafficDatabase class)
- **Table**: `traffic_incidents` with `data_source = 'tomtom_api'`
- **Access via**: `get_database()` function

### 2. **Enhanced Traffic Database (Collector's Direct Storage)**
```
📁 /data/enhanced_traffic_data.db
```
- **Used by**: `code/utils/enhanced_traffic_collector.py`
- **Tables**: `traffic_incidents`, `traffic_flow`
- **Direct API data storage**: Raw data from TomTom API

### 3. **CSV File (Now Empty - Header Only)**
```
📁 /data/traffic_incidents.csv
```
- **Status**: Contains only header row (dummy data removed)
- **Purpose**: Legacy fallback (not used in current system)

## Data Flow Diagram

```
TomTom API → Enhanced Traffic Collector → Multiple Databases
                        ↓
    ┌─────────────────────────────────────────────────────────┐
    │                                                         │
    ├─→ enhanced_traffic_data.db (direct collector storage)   │
    │   ├── traffic_incidents table                           │
    │   ├── traffic_flow table                               │
    │   └── collection_stats table                           │
    │                                                         │
    └─→ traffic_data.db (main UI database) ←── data_sync.py  │
        ├── traffic_incidents (filtered: tomtom_api only)    │
        ├── traffic_flow                                      │
        └── api_usage tracking                               │
```

## Key Database Tables Structure

### traffic_incidents Table (in both databases)
```sql
CREATE TABLE traffic_incidents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    incident_id TEXT UNIQUE,
    location TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    description TEXT,
    severity INTEGER,
    data_source TEXT DEFAULT 'tomtom_api',  -- ← This identifies real data
    -- ... additional fields
);
```

### traffic_flow Table
```sql
CREATE TABLE traffic_flow (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    location TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    current_speed REAL,
    free_flow_speed REAL,
    -- ... additional flow metrics
);
```

## How to Check Your Data

### Method 1: SQLite Command Line
```bash
# Check main database
sqlite3 data/traffic_data.db "SELECT COUNT(*) FROM traffic_incidents WHERE data_source = 'tomtom_api';"

# Check enhanced database
sqlite3 data/enhanced_traffic_data.db "SELECT COUNT(*) FROM traffic_incidents;"

# View recent incidents
sqlite3 data/traffic_data.db "SELECT timestamp, location, description FROM traffic_incidents WHERE data_source = 'tomtom_api' ORDER BY timestamp DESC LIMIT 5;"
```

### Method 2: Through Streamlit UI
1. **Live Traffic page**: Shows filtered real data from `traffic_data.db`
2. **Monitoring page**: Shows collection statistics
3. **Historical Data page**: Shows data accumulation progress

### Method 3: Python Script
```python
import sqlite3
import pandas as pd

# Check main database
conn = sqlite3.connect('data/traffic_data.db')
df = pd.read_sql_query(
    "SELECT * FROM traffic_incidents WHERE data_source = 'tomtom_api'", 
    conn
)
print(f"Real incidents in main DB: {len(df)}")
conn.close()

# Check enhanced database
conn = sqlite3.connect('data/enhanced_traffic_data.db')
df = pd.read_sql_query("SELECT * FROM traffic_incidents", conn)
print(f"Total incidents in enhanced DB: {len(df)}")
conn.close()
```

## Data Collection Process Details

### When Collection Runs:
1. **Enhanced Traffic Collector** (`enhanced_traffic_collector.py`) runs every 15 minutes
2. **Queries TomTom API** for 11 Rhode Island zones
3. **Saves raw data** to `enhanced_traffic_data.db`
4. **Data Sync** (`data_sync.py`) processes and filters data to `traffic_data.db`

### What Gets Saved:
- **Traffic Incidents**: Accidents, construction, road closures, etc.
- **Traffic Flow**: Speed data, congestion levels, travel times
- **Collection Metadata**: Timestamps, API usage, collection statistics
- **Data Source Tracking**: All real data marked as `'tomtom_api'`

## Backup and Retention

### Automatic Backups:
- **Data retention**: 365 days (configurable)
- **Archive creation**: Old data archived to JSON files before deletion
- **Location**: `data/archived_incidents_YYYYMMDD.json`

### Manual Backup:
```bash
# Copy main database
cp data/traffic_data.db data/backups/traffic_data_$(date +%Y%m%d).db

# Copy enhanced database
cp data/enhanced_traffic_data.db data/backups/enhanced_traffic_data_$(date +%Y%m%d).db
```

## Troubleshooting Data Issues

### No Data Appearing?
1. Check if collection is running: Look at logs for "Starting collection cycle"
2. Verify database exists: `ls -la data/`
3. Check API credits: Look for credit exhaustion messages
4. Verify data source filter: Ensure UI queries for `data_source = 'tomtom_api'`

### Data in Wrong Database?
- The **enhanced collector** saves to `enhanced_traffic_data.db`
- The **UI systems** read from `traffic_data.db`
- **Data sync** should bridge between them

## Summary

**Your real TomTom API traffic data is saved in:**
- **Primary location**: `/data/traffic_data.db` → `traffic_incidents` table (filtered for real API data)
- **Collector storage**: `/data/enhanced_traffic_data.db` → `traffic_incidents` table (raw API data)
- **Data source identifier**: `data_source = 'tomtom_api'` distinguishes real from dummy data
- **Access method**: All UI pages use `get_database()` function to read from `traffic_data.db`

The system ensures only authentic Rhode Island traffic incidents appear in your maps and analysis tools.