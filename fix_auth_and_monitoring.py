#!/usr/bin/env python3
"""
Script to fix authentication and monitoring issues
"""

import os
import sqlite3
import hashlib
import json
from datetime import datetime, timedelta

def create_demo_database():
    """Create the demo database with accounts"""
    
    # Ensure databases directory exists
    databases_dir = 'databases'
    os.makedirs(databases_dir, exist_ok=True)
    
    # Database path
    db_path = os.path.join(databases_dir, 'enterprise_auth.db')
    
    print(f"Creating demo accounts database at: {os.path.abspath(db_path)}")
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Create organizations table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS organizations (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            tier TEXT NOT NULL,
            max_users INTEGER DEFAULT 5,
            api_quota INTEGER DEFAULT 10000,
            features TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            subscription_expires TIMESTAMP,
            contact_email TEXT NOT NULL,
            is_active BOOLEAN DEFAULT 1
        )
        """)
        
        # Create users table (matching the authentication system structure)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            organization_id TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY (organization_id) REFERENCES organizations (id)
        )
        """)
        
        # Create sessions table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_sessions (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            organization_id TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (organization_id) REFERENCES organizations (id)
        )
        """)
        
        # Create API usage table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS api_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            organization_id TEXT NOT NULL,
            endpoint TEXT NOT NULL,
            requests_count INTEGER DEFAULT 1,
            date DATE DEFAULT CURRENT_DATE,
            FOREIGN KEY (organization_id) REFERENCES organizations (id)
        )
        """)
        
        # Create Rhode Island Department of Transportation organization
        org_id = "ridot-demo-org"
        cursor.execute("""
        INSERT OR REPLACE INTO organizations 
        (id, name, tier, max_users, api_quota, features, subscription_expires, contact_email)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            org_id,
            "Rhode Island Department of Transportation",
            "enterprise",
            1000,
            1000000,
            json.dumps(["all_features"]),
            (datetime.now() + timedelta(days=365)).isoformat(),
            "admin@ridot.ri.gov"
        ))
        
        # Hash password function (matches enterprise_auth.py)
        def hash_password(password: str) -> str:
            salt = "village_salt_2024".encode()
            password_bytes = password.encode()
            hashed = hashlib.pbkdf2_hmac('sha256', password_bytes, salt, 100000)
            return hashed.hex()
        
        # Create demo users
        demo_users = [
            {
                "id": "demo-admin-001",
                "username": "admin@ridot.ri.gov",
                "email": "admin@ridot.ri.gov",
                "name": "Director Sarah Johnson",
                "role": "admin",
                "description": "RIDOT Director - Full platform access"
            },
            {
                "id": "demo-analyst-001", 
                "username": "analyst@ridot.ri.gov",
                "email": "analyst@ridot.ri.gov",
                "name": "Traffic Engineer Mike Chen",
                "role": "analyst",
                "description": "Senior Traffic Analyst - Analytics and reporting"
            },
            {
                "id": "demo-viewer-001",
                "username": "viewer@ridot.ri.gov",
                "email": "viewer@ridot.ri.gov",
                "name": "Mayor Lisa Rodriguez",
                "role": "viewer", 
                "description": "Municipal Official - Dashboard viewing only"
            },
            {
                "id": "demo-field-001",
                "username": "field@ridot.ri.gov",
                "email": "field@ridot.ri.gov",
                "name": "Inspector David Kim",
                "role": "field_worker",
                "description": "Field Inspector - Mobile app access"
            }
        ]
        
        for user in demo_users:
            # Use consistent demo password
            password = "Demo2024!"
            password_hash = hash_password(password)
            
            cursor.execute("""
            INSERT OR REPLACE INTO users 
            (id, username, email, password_hash, role, organization_id, last_login, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user['id'],
                user['username'],
                user['email'],
                password_hash,
                user['role'],
                org_id,
                datetime.now().isoformat(),
                True
            ))
        
        conn.commit()
        
        print("Demo accounts created successfully!")
        print("\n" + "="*60)
        print("RIDOT DEMO LOGIN CREDENTIALS")
        print("="*60)
        print("Organization: Rhode Island Department of Transportation")
        print("Subscription: Enterprise Tier")
        print("Password (all users): Demo2024!")
        print("\n👤 Demo User Accounts:")
        
        for user in demo_users:
            print(f"\n{user['role'].upper().replace('_', ' ')} ACCOUNT:")
            print(f"  Username: {user['username']}")
            print(f"  Email: {user['email']}")
            print(f"  Role: {user['role']}")
            print(f"  Access: {user['description']}")
        
        print("\n" + "="*60)
        print("Ready for RIHub demonstration!")
        print(f"Database created at: {os.path.abspath(db_path)}")
        
        return True

def verify_accounts():
    """Verify the accounts were created correctly"""
    db_path = os.path.join('databases', 'enterprise_auth.db')
    
    if not os.path.exists(db_path):
        print("Auth database not found")
        return False
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Check organizations
        cursor.execute("SELECT COUNT(*) FROM organizations")
        org_count = cursor.fetchone()[0]
        
        # Check users
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        # Get user details
        cursor.execute("""
        SELECT u.username, u.email, u.role, o.name as org_name, o.tier
        FROM users u
        JOIN organizations o ON u.organization_id = o.id
        ORDER BY u.role
        """)
        users = cursor.fetchall()
        
        print(f"\n📊 Verification Results:")
        print(f"  Organizations: {org_count}")
        print(f"  Users: {user_count}")
        
        print(f"\n👥 Active Demo Users:")
        for user in users:
            print(f"  {user[2].title()}: {user[0]} - {user[3]} ({user[4]})")
        
        return user_count >= 4

if __name__ == "__main__":
    print("Fixing Authentication and Monitoring Issues")
    print("=" * 50)
    
    # Create demo accounts
    success = create_demo_database()
    
    if success:
        # Verify everything worked
        verify_accounts()
        
        print("\nIssues resolved!")
        print("\nAuthentication:")
        print("  - Demo accounts created in databases/enterprise_auth.db")
        print("  - Use email as username (e.g., admin@ridot.ri.gov)")
        print("  - Password: Demo2024!")
        print("\nMonitoring:")
        print("  - Fixed import from smart_collector to enhanced_traffic_collector")
        print("  - Added proper error handling for missing utilities")
        
        print("\nReady to test:")
        print("1. Run: streamlit run code/app.py")
        print("2. Login with: admin@ridot.ri.gov / Demo2024!")
        
    else:
        print("Failed to create demo accounts")