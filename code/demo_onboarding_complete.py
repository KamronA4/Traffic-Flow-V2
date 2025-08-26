#!/usr/bin/env python3
"""
Complete onboarding for demo accounts
"""

import os
import sys
import sqlite3
import json
from datetime import datetime

def complete_demo_onboarding():
    """Mark demo accounts as having completed onboarding"""
    
    db_path = 'databases/onboarding.db'
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Create onboarding table if it doesn't exist
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS onboarding_progress (
            organization_id TEXT PRIMARY KEY,
            current_step TEXT NOT NULL,
            completed_steps TEXT NOT NULL,
            status TEXT NOT NULL,
            started_at TIMESTAMP NOT NULL,
            completed_at TIMESTAMP,
            data TEXT DEFAULT '{}'
        )
        """)
        
        # Demo organizations
        demo_orgs = [
            "ridot-demo-org",
            "providence-demo-org"
        ]
        
        # All onboarding steps
        all_steps = [
            "welcome",
            "organization_setup", 
            "data_import",
            "feature_tour",
            "team_setup",
            "integration_setup",
            "training_resources",
            "completion"
        ]
        
        for org_id in demo_orgs:
            cursor.execute("""
            INSERT OR REPLACE INTO onboarding_progress 
            (organization_id, current_step, completed_steps, status, started_at, completed_at, data)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                org_id,
                "completion",
                json.dumps(all_steps),
                "completed",
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                json.dumps({
                    "demo_account": True,
                    "completion_percentage": 100,
                    "setup_type": "enterprise_demo"
                })
            ))
        
        conn.commit()
        print("✅ Demo onboarding completed for all accounts")

if __name__ == "__main__":
    complete_demo_onboarding()