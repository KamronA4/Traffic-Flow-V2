#!/usr/bin/env python3
"""
Fix database initialization issues for RIHub demo
"""

import os
import sys
import sqlite3
from datetime import datetime
import json

# Add project paths
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'code'))

def ensure_directories():
    """Ensure all required directories exist"""
    directories = [
        'data',
        'code/data',
        'code/databases',
        'databases'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✓ Created directory: {directory}")

def initialize_traffic_database():
    """Initialize traffic data database"""
    db_path = 'data/traffic_data.db'
    
    print(f"Initializing traffic database at: {db_path}")
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Traffic incidents table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS traffic_incidents (
            id TEXT PRIMARY KEY,
            timestamp TIMESTAMP NOT NULL,
            description TEXT NOT NULL,
            severity INTEGER NOT NULL,
            lat REAL NOT NULL,
            lng REAL NOT NULL,
            location TEXT NOT NULL,
            startTime TIMESTAMP,
            endTime TIMESTAMP,
            length INTEGER DEFAULT 0,
            delay INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Traffic flow table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS traffic_flow (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP NOT NULL,
            location TEXT NOT NULL,
            lat REAL NOT NULL,
            lng REAL NOT NULL,
            current_speed REAL,
            free_flow_speed REAL,
            congestion_level INTEGER,
            confidence REAL DEFAULT 1.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # API usage tracking
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS api_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            service TEXT NOT NULL,
            requests_count INTEGER DEFAULT 1,
            status_code INTEGER,
            response_time_ms INTEGER
        )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_incidents_timestamp ON traffic_incidents(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_incidents_location ON traffic_incidents(location)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_flow_timestamp ON traffic_flow(timestamp)")
        
        conn.commit()
        print("✓ Traffic database initialized")

def initialize_auth_database():
    """Initialize authentication database"""
    db_path = 'databases/auth.db'
    
    print(f"Initializing auth database at: {db_path}")
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Organizations table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS organizations (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            domain TEXT,
            tier TEXT DEFAULT 'free',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            subscription_expires TIMESTAMP,
            settings TEXT DEFAULT '{}'
        )
        """)
        
        # Users table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            password_hash BLOB NOT NULL,
            password_salt BLOB NOT NULL,
            role TEXT DEFAULT 'viewer',
            organization_id TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE,
            FOREIGN KEY (organization_id) REFERENCES organizations(id)
        )
        """)
        
        # User activity logs
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            action TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            details TEXT,
            ip_address TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """)
        
        # API keys table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS api_keys (
            id TEXT PRIMARY KEY,
            organization_id TEXT NOT NULL,
            key_hash TEXT NOT NULL,
            name TEXT,
            permissions TEXT DEFAULT '[]',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_used TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE,
            FOREIGN KEY (organization_id) REFERENCES organizations(id)
        )
        """)
        
        conn.commit()
        print("✓ Auth database initialized")

def create_demo_organization():
    """Create demo organization and users"""
    import hashlib
    import uuid
    from datetime import datetime, timedelta
    
    db_path = 'databases/auth.db'
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Create demo organization
        org_id = str(uuid.uuid4())
        cursor.execute("""
        INSERT OR REPLACE INTO organizations 
        (id, name, domain, tier, subscription_expires, settings)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            org_id,
            "Rhode Island Department of Transportation",
            "ridot.ri.gov",
            "enterprise",
            (datetime.now() + timedelta(days=365)).isoformat(),
            json.dumps({
                "api_quota": 50000,
                "white_label": True,
                "custom_branding": True
            })
        ))
        
        # Create demo users
        demo_users = [
            {
                "email": "admin@ridot.ri.gov",
                "name": "RIDOT Administrator",
                "role": "admin"
            },
            {
                "email": "analyst@ridot.ri.gov", 
                "name": "Traffic Analyst",
                "role": "analyst"
            },
            {
                "email": "viewer@ridot.ri.gov",
                "name": "Municipal Viewer",
                "role": "viewer"
            },
            {
                "email": "field@ridot.ri.gov",
                "name": "Field Worker",
                "role": "field_worker"
            }
        ]
        
        for user in demo_users:
            user_id = str(uuid.uuid4())
            
            # Create password hash for demo (password: "demo123")
            password = "demo123"
            salt = hashlib.sha256(user['email'].encode()).digest()
            password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
            
            cursor.execute("""
            INSERT OR REPLACE INTO users 
            (id, email, name, password_hash, password_salt, role, organization_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                user['email'],
                user['name'],
                password_hash,
                salt,
                user['role'],
                org_id
            ))
        
        conn.commit()
        print("✓ Demo organization and users created")
        print("\nDemo Login Credentials:")
        print("All users password: demo123")
        for user in demo_users:
            print(f"  {user['role'].title()}: {user['email']}")

def initialize_beta_database():
    """Initialize beta program database"""
    db_path = 'databases/beta_program.db'
    
    print(f"Initializing beta database at: {db_path}")
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS beta_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            organization TEXT,
            role TEXT,
            interest_level INTEGER DEFAULT 5,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'pending',
            notes TEXT
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS feature_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            feature_title TEXT NOT NULL,
            description TEXT,
            priority INTEGER DEFAULT 3,
            status TEXT DEFAULT 'submitted',
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        conn.commit()
        print("✓ Beta database initialized")

def load_sample_data():
    """Load sample traffic data into database"""
    import pandas as pd
    
    # Load CSV data
    csv_path = 'data/traffic_incidents.csv'
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        
        db_path = 'data/traffic_data.db'
        with sqlite3.connect(db_path) as conn:
            # Insert incidents
            for _, row in df.iterrows():
                conn.execute("""
                INSERT OR REPLACE INTO traffic_incidents 
                (id, timestamp, description, severity, lat, lng, location, startTime, endTime, length, delay)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row['id'],
                    row['timestamp'], 
                    row['description'],
                    row['severity'],
                    row['lat'],
                    row['lng'],
                    row['location'],
                    row['startTime'],
                    row['endTime'],
                    row['length'],
                    row['delay']
                ))
            
            conn.commit()
            print(f"✓ Loaded {len(df)} traffic incidents")

def verify_databases():
    """Verify all databases are working"""
    databases = [
        ('data/traffic_data.db', 'traffic_incidents'),
        ('databases/auth.db', 'users'),
        ('databases/beta_program.db', 'beta_users')
    ]
    
    print("\nVerifying databases:")
    for db_path, table in databases:
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"✓ {db_path} - {table}: {count} records")
        except Exception as e:
            print(f"✗ {db_path} - {table}: ERROR - {e}")

def main():
    """Main initialization function"""
    print("Village Platform Database Initialization")
    print("=" * 50)
    
    # Ensure directories exist
    ensure_directories()
    
    # Initialize databases
    initialize_traffic_database()
    initialize_auth_database()
    initialize_beta_database()
    
    # Create demo data
    create_demo_organization()
    load_sample_data()
    
    # Verify everything works
    verify_databases()
    
    print("\n" + "=" * 50)
    print("✓ Database initialization complete!")
    print("\nDemo is ready for RIHub presentation")

if __name__ == "__main__":
    main()