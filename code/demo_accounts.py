#!/usr/bin/env python3
"""
Create demo accounts for RIHub presentation
"""

import os
import sys
import sqlite3
import hashlib
import uuid
import json
from datetime import datetime, timedelta

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_demo_accounts():
    """Create demonstration accounts for different user roles"""
    
    # Database path
    db_path = 'databases/enterprise_auth.db'
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
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

def create_municipal_demo_org():
    """Create a second demo organization for comparison"""
    
    db_path = 'databases/enterprise_auth.db'
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Create Providence City organization
        org_id = "providence-demo-org"
        cursor.execute("""
        INSERT OR REPLACE INTO organizations 
        (id, name, domain, tier, subscription_expires, settings)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            org_id,
            "City of Providence",
            "providenceri.gov",
            "pro",
            (datetime.now() + timedelta(days=365)).isoformat(),
            json.dumps({
                "api_quota": 25000,
                "white_label_enabled": False,
                "custom_branding": False,
                "advanced_analytics": True,
                "priority_support": False
            })
        ))
        
        # Create Providence users
        password = "Demo2024!"
        salt = hashlib.sha256("providence@demo.com".encode()).digest()
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        
        cursor.execute("""
        INSERT OR REPLACE INTO users 
        (id, email, name, password_hash, password_salt, role, organization_id, last_login, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "providence-admin-001",
            "mayor@providenceri.gov",
            "Mayor Brett Smiley",
            password_hash,
            salt,
            "admin",
            org_id,
            datetime.now().isoformat(),
            True
        ))
        
        conn.commit()
        print("✅ Providence demo organization created")

def verify_demo_accounts():
    """Verify demo accounts were created correctly"""
    
    db_path = 'databases/enterprise_auth.db'
    
    if not os.path.exists(db_path):
        print("❌ Auth database not found")
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
        SELECT u.name, u.email, u.role, o.name as org_name, o.tier
        FROM users u
        JOIN organizations o ON u.organization_id = o.id
        ORDER BY u.role
        """)
        users = cursor.fetchall()
        
        print(f"\n📊 Database Status:")
        print(f"  Organizations: {org_count}")
        print(f"  Users: {user_count}")
        
        print(f"\n👥 Active Demo Users:")
        for user in users:
            print(f"  {user[2].title()}: {user[0]} ({user[1]}) - {user[3]} ({user[4]})")
        
        return user_count >= 4

def main():
    """Main function to create all demo accounts"""
    
    print("Creating Demo Accounts for RIHub Presentation")
    print("=" * 50)
    
    # Create main demo accounts
    success = create_demo_accounts()
    
    if success:
        # Create additional municipal demo
        create_municipal_demo_org()
        
        # Verify everything worked
        verify_demo_accounts()
        
        print("\n🎯 Demo accounts ready for RIHub presentation!")
        print("\nQuick Demo Flow:")
        print("1. Start with Admin account to show full capabilities")
        print("2. Switch to Analyst account for technical features")
        print("3. Switch to Viewer account to show restricted access")
        print("4. Highlight multi-tenant isolation between orgs")
        
    else:
        print("❌ Failed to create demo accounts")

if __name__ == "__main__":
    main()