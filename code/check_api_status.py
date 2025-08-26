#!/usr/bin/env python3
"""
Check TomTom API credit status and collection state
Quick diagnostic tool for API issues with enhanced credit tracking
"""

import sys
import os
from pathlib import Path
import requests
from datetime import datetime

# Add current directory to path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

def check_api_credits():
    """Check TomTom API credit status"""
    print("🔍 Checking TomTom API Credits")
    print("=" * 40)
    
    # Get API key
    api_key = None
    try:
        import streamlit as st
        api_key = st.secrets.get("TOMTOM_API_KEY")
        if not api_key or api_key == "your-tomtom-api-key-here":
            api_key = os.getenv('TOMTOM_API_KEY')
    except:
        api_key = os.getenv('TOMTOM_API_KEY')
    
    if not api_key:
        print("❌ No API key found in secrets.toml or environment")
        return False
    
    print(f"✅ API key found (length: {len(api_key)})")
    
    # Test API with minimal request
    try:
        url = "https://api.tomtom.com/search/2/search/Providence, RI.json"
        params = {'key': api_key, 'limit': 1}
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            print("✅ API Request Success - Credits Available")
            return True
        elif response.status_code == 403:
            try:
                error_data = response.json()
                error_code = error_data.get('detailedError', {}).get('code')
                error_msg = error_data.get('detailedError', {}).get('message')
                
                if error_code == 'InsufficientFunds':
                    print("❌ API Credits Exhausted")
                    print(f"   Message: {error_msg}")
                    return False
                elif error_code == 'Forbidden':
                    print("❌ API Access Forbidden")
                    print(f"   Message: {error_msg}")
                    return False
                else:
                    print(f"❌ API Error: {error_code} - {error_msg}")
                    return False
            except:
                print(f"❌ API Error: {response.status_code} - {response.text}")
                return False
        else:
            print(f"❌ API Error: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def check_collection_status():
    """Check current data collection status with enhanced tracking"""
    print("\n📊 Collection Status")
    print("=" * 40)
    
    try:
        from utils.enhanced_traffic_collector import get_enhanced_collector
        collector = get_enhanced_collector()
        status = collector.get_collection_status()
        
        print(f"Collection Active: {status.get('is_collecting', False)}")
        print(f"Credit Exhausted: {status.get('credit_exhausted', False)}")
        print(f"API Requests Today: {status.get('api_requests_today', 0):,}")
        print(f"Successful Requests: {status.get('successful_requests', 0):,}")
        print(f"Failed Requests: {status.get('failed_requests', 0):,}")
        print(f"Daily Quota: {status.get('daily_quota', 0):,}")
        print(f"Quota Remaining: {status.get('quota_remaining', 0):,}")
        print(f"Usage Percentage: {status.get('usage_percent', 0):.1f}%")
        
        if 'last_updated' in status:
            print(f"Last Updated: {status['last_updated'].strftime('%Y-%m-%d %H:%M:%S')}")
        
        if status.get('credit_exhausted'):
            print("\n🚨 CREDIT EXHAUSTION DETECTED!")
            print("   - Data collection has been stopped")
            print("   - No new API requests will be made")
            print("   - Add credits or wait for daily reset")
        
        return status
        
    except Exception as e:
        print(f"❌ Error checking collection status: {e}")
        return None

def show_credit_tracker_status():
    """Show detailed credit tracker status"""
    print("\n💳 Credit Tracker Status")
    print("=" * 40)
    
    try:
        from utils.credit_tracker import get_credit_tracker
        tracker = get_credit_tracker()
        
        # Display formatted terminal status
        tracker.display_terminal_status()
        
        # Show usage history
        print("\n📈 Usage History (Last 7 Days)")
        print("-" * 40)
        
        history = tracker.get_usage_history(7)
        for entry in history:
            date = entry['date']
            requests = entry['requests_made']
            successful = entry['successful_requests']
            failed = entry['failed_requests']
            exhausted = "🚨 EXHAUSTED" if entry['credits_exhausted'] else "✅ OK"
            
            print(f"{date}: {requests:,} total ({successful:,} success, {failed:,} failed) - {exhausted}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error accessing credit tracker: {e}")
        return False

def show_solutions():
    """Show solutions for credit issues"""
    print("\n💡 Solutions for Credit Issues")
    print("=" * 40)
    
    print("1. **Add More Credits to TomTom Account:**")
    print("   - Visit TomTom Developer Portal")
    print("   - Add credits to your account")
    print("   - Run: python code/reset_credit_flag.py")
    
    print("\n2. **Wait for Daily Reset (Free Tier):**")
    print("   - Free tier resets at midnight UTC")
    print("   - 50,000 requests per day")
    print("   - Run: python code/reset_credit_flag.py after reset")
    
    print("\n3. **Upgrade TomTom Plan:**")
    print("   - Consider upgrading to paid tier")
    print("   - Higher quotas and better rate limits")
    print("   - Access to premium endpoints")
    
    print("\n4. **Stop Data Collection:**")
    print("   - Run: python code/emergency_stop_collection.py")
    print("   - This will halt all API requests")

if __name__ == "__main__":
    print("🚨 TomTom API Credit Diagnostic")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check API credits
    credits_available = check_api_credits()
    
    # Check collection status
    status = check_collection_status()
    
    # Show detailed credit tracker status
    show_credit_tracker_status()
    
    # Show solutions if needed
    if not credits_available or (status and status.get('credit_exhausted')):
        show_solutions()
    else:
        print("\n✅ All systems operational!")
        print("💡 Data collection should be working normally")
        
    print("\n🔧 Available Management Commands:")
    print("- python code/check_api_status.py    # Check current status")
    print("- python code/emergency_stop_collection.py  # Stop all collection")
    print("- python code/reset_credit_flag.py   # Reset after adding credits")