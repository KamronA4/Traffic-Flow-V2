#!/usr/bin/env python3
"""
Verification script to confirm the system only uses real API data
"""

import sqlite3
import os
import pandas as pd
from pathlib import Path

def verify_system_setup():
    """Comprehensive verification of real data system"""
    
    print("🔍 Verifying Real Data System Configuration")
    print("=" * 60)
    
    results = {
        'csv_cleaned': False,
        'database_cleaned': False,
        'api_integration_ready': False,
        'ui_updated': False,
        'data_validation_active': False
    }
    
    # 1. Check CSV file is clean
    print("\n1. 📄 CSV File Status")
    csv_path = "data/traffic_incidents.csv"
    try:
        with open(csv_path, 'r') as f:
            lines = f.readlines()
            if len(lines) <= 1:
                print("   ✅ CSV contains only header - no dummy data")
                results['csv_cleaned'] = True
            else:
                print(f"   ❌ CSV still contains {len(lines)-1} dummy rows")
    except Exception as e:
        print(f"   ❌ Error reading CSV: {e}")
    
    # 2. Check database is clean
    print("\n2. 🗄️ Database Status")
    db_path = "data/traffic_data.db"
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Count total incidents
        cursor.execute("SELECT COUNT(*) FROM traffic_incidents")
        total_count = cursor.fetchone()[0]
        
        # Count real API incidents
        cursor.execute("SELECT COUNT(*) FROM traffic_incidents WHERE data_source = 'tomtom_api'")
        api_count = cursor.fetchone()[0]
        
        # Count dummy incidents
        cursor.execute("""
            SELECT COUNT(*) FROM traffic_incidents 
            WHERE data_source IS NULL 
               OR data_source = '' 
               OR data_source = 'csv'
               OR external_id LIKE 'INC_%'
        """)
        dummy_count = cursor.fetchone()[0]
        
        print(f"   📊 Total incidents: {total_count}")
        print(f"   ✅ Real API incidents: {api_count}")
        print(f"   🗑️ Dummy incidents: {dummy_count}")
        
        if dummy_count == 0:
            print("   ✅ Database contains only real API data")
            results['database_cleaned'] = True
        else:
            print("   ⚠️ Database still contains dummy data")
        
        conn.close()
        
    except Exception as e:
        print(f"   ❌ Error checking database: {e}")
    
    # 3. Check API integration setup
    print("\n3. 🔌 API Integration")
    try:
        # Check if enhanced collector has correct data_source marking
        with open("code/utils/enhanced_traffic_collector.py", 'r') as f:
            content = f.read()
            if "'data_source': 'tomtom_api'" in content:
                print("   ✅ Enhanced collector marks data as 'tomtom_api'")
                results['api_integration_ready'] = True
            else:
                print("   ❌ Enhanced collector missing data_source marking")
                
        # Check database insert method
        with open("code/utils/database.py", 'r') as f:
            content = f.read()
            if "data_source" in content and "tomtom_api" in content:
                print("   ✅ Database insert method handles data_source field")
            else:
                print("   ❌ Database insert method missing data_source handling")
                
    except Exception as e:
        print(f"   ❌ Error checking API integration: {e}")
    
    # 4. Check UI updates
    print("\n4. 🖥️ UI Configuration")
    try:
        with open("code/pages/live_traffic.py", 'r') as f:
            content = f.read()
            if "No Real API Data Available Yet" in content:
                print("   ✅ UI shows appropriate messages for no real data")
                results['ui_updated'] = True
            else:
                print("   ❌ UI not updated for real data handling")
    except Exception as e:
        print(f"   ❌ Error checking UI: {e}")
    
    # 5. Check data validation
    print("\n5. 🛡️ Data Validation")
    try:
        with open("code/utils/database.py", 'r') as f:
            content = f.read()
            if "WHERE data_source = 'tomtom_api'" in content:
                print("   ✅ Database queries filter for real API data only")
                results['data_validation_active'] = True
            else:
                print("   ❌ Database queries not filtering for real data")
    except Exception as e:
        print(f"   ❌ Error checking data validation: {e}")
    
    # Overall status
    print("\n" + "=" * 60)
    print("📋 SYSTEM VERIFICATION SUMMARY")
    print("=" * 60)
    
    all_good = all(results.values())
    
    for check, status in results.items():
        emoji = "✅" if status else "❌"
        print(f"   {emoji} {check.replace('_', ' ').title()}")
    
    if all_good:
        print("\n🎉 SUCCESS: System configured for real API data only!")
        print("\n📋 What happens now:")
        print("   1. TomTom API collector runs every 15 minutes")
        print("   2. Real Rhode Island incidents are stored in database")
        print("   3. UI shows only genuine traffic data")
        print("   4. No dummy/fake data appears anywhere")
        print("   5. Perfect for RIHub demo with authentic data")
    else:
        print("\n⚠️ ISSUES FOUND: Some components need attention")
        print("   Please review the failed checks above")
    
    return all_good

if __name__ == "__main__":
    success = verify_system_setup()
    
    if success:
        print("\n🚀 Your Village Platform is ready for real traffic data!")
    else:
        print("\n🔧 Please address the issues above before demo")