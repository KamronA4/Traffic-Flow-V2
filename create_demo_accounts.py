#!/usr/bin/env python3
"""
Quick script to create demo accounts for the RIHub presentation
"""

import os
import sys
import sqlite3
import hashlib
import json
from datetime import datetime, timedelta

def create_demo_accounts():
    """Create demonstration accounts for different user roles"""
    
    # Ensure databases directory exists
    databases_dir = 'databases'
    os.makedirs(databases_dir, exist_ok=True)
    
    # Database path
    db_path = os.path.join(databases_dir, 'enterprise_auth.db')
    
    print(f"Creating demo accounts database at: {db_path}")
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Create tables if they don't exist
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
        
        # Create Rhode Island Department of Transportation organization
        org_id = "ridot-demo-org"
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
                "white_label_enabled": True,
                "custom_branding": True,
                "advanced_analytics": True,
                "priority_support": True
            })
        ))
        
        # Create demo users with different roles
        demo_users = [
            {
                "id": "demo-admin-001",
                "email": "admin@ridot.ri.gov",
                "name": "Director Sarah Johnson",
                "role": "admin",
                "description": "RIDOT Director - Full platform access"
            },
            {
                "id": "demo-analyst-001", 
                "email": "analyst@ridot.ri.gov",
                "name": "Traffic Engineer Mike Chen",
                "role": "analyst",
                "description": "Senior Traffic Analyst - Analytics and reporting"
            },
            {
                "id": "demo-viewer-001",
                "email": "viewer@ridot.ri.gov",
                "name": "Mayor Lisa Rodriguez",
                "role": "viewer", 
                "description": "Municipal Official - Dashboard viewing only"
            },
            {
                "id": "demo-field-001",
                "email": "field@ridot.ri.gov",
                "name": "Inspector David Kim",
                "role": "field_worker",
                "description": "Field Inspector - Mobile app access"
            }
        ]
        
        for user in demo_users:
            # Use consistent demo password
            password = "Demo2024!"
            
            # Create deterministic salt based on email
            salt = hashlib.sha256(user['email'].encode()).digest()
            
            # Hash password
            password_hash = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode('utf-8'),
                salt,
                100000
            )
            
            cursor.execute("""
            INSERT OR REPLACE INTO users 
            (id, email, name, password_hash, password_salt, role, organization_id, last_login, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user['id'],
                user['email'],
                user['name'],
                password_hash,
                salt,
                user['role'],
                org_id,
                datetime.now().isoformat(),
                True
            ))
        
        conn.commit()
        
        print("✅ Demo accounts created successfully!")
        print("\n" + "="*60)
        print("RIDOT DEMO LOGIN CREDENTIALS")
        print("="*60)
        print("Organization: Rhode Island Department of Transportation")
        print("Subscription: Enterprise Tier")
        print("Password (all users): Demo2024!")
        print("\n👤 Demo User Accounts:")
        
        for user in demo_users:
            print(f"\n{user['role'].upper().replace('_', ' ')} ACCOUNT:")
            print(f"  Email: {user['email']}")
            print(f"  Name: {user['name']}")
            print(f"  Role: {user['role']}")
            print(f"  Access: {user['description']}")
        
        print("\n" + "="*60)
        print("Ready for RIHub demonstration!")
        
        return True

if __name__ == "__main__":
    print("Creating Demo Accounts for RIHub Presentation")
    print("=" * 50)
    
    success = create_demo_accounts()
    
    if success:
        print("\n🎯 Demo accounts ready for RIHub presentation!")
        print("\nTo test login:")
        print("1. Run: streamlit run code/app.py")
        print("2. Use email: admin@ridot.ri.gov")
        print("3. Use password: Demo2024!")
    else:
        print("❌ Failed to create demo accounts")