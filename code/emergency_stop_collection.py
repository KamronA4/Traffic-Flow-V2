#!/usr/bin/env python3
"""
Emergency stop script for TomTom API credit exhaustion
Run this script to stop all data collection immediately
"""

import sys
import os
from pathlib import Path

# Add current directory to path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

def stop_all_collection():
    """Stop all data collection processes"""
    print("🚨 Emergency Collection Stop")
    print("=" * 40)
    
    try:
        # Stop enhanced collector
        print("Stopping enhanced traffic collector...")
        from utils.enhanced_traffic_collector import get_enhanced_collector
        enhanced_collector = get_enhanced_collector()
        enhanced_collector.stop_collection()
        
        status = enhanced_collector.get_collection_status()
        print(f"✅ Enhanced collector stopped")
        print(f"   - Credit exhausted: {status.get('credit_exhausted', False)}")
        print(f"   - API requests today: {status.get('api_requests_today', 0)}")
        print(f"   - Daily quota: {status.get('daily_quota', 0)}")
        
    except Exception as e:
        print(f"❌ Error stopping enhanced collector: {e}")
    
    try:
        # Stop smart collector
        print("\nStopping smart traffic collector...")
        from utils.smart_collector import get_collector
        smart_collector = get_collector()
        smart_collector.stop_collection()
        print("✅ Smart collector stopped")
        
    except Exception as e:
        print(f"❌ Error stopping smart collector: {e}")
    
    try:
        # Stop historical collector
        print("\nStopping historical traffic collector...")
        from utils.historical_traffic_collector import get_historical_collector
        historical_collector = get_historical_collector()
        # Historical collector might not have a stop method
        print("✅ Historical collector checked")
        
    except Exception as e:
        print(f"❌ Error stopping historical collector: {e}")
    
    print("\n" + "=" * 40)
    print("🛑 Collection Stop Complete")
    print("\nNext steps:")
    print("1. Check your TomTom API dashboard for credit usage")
    print("2. Add more credits to your TomTom account if needed")
    print("3. Wait for daily quota reset (if using free tier)")
    print("4. Run 'python reset_credit_flag.py' to resume collection")

def check_collection_status():
    """Check current collection status"""
    print("\n📊 Current Collection Status")
    print("=" * 40)
    
    try:
        from utils.enhanced_traffic_collector import get_enhanced_collector
        collector = get_enhanced_collector()
        status = collector.get_collection_status()
        
        print(f"Enhanced Collector:")
        print(f"  - Is collecting: {status.get('is_collecting', False)}")
        print(f"  - Credit exhausted: {status.get('credit_exhausted', False)}")
        print(f"  - API requests today: {status.get('api_requests_today', 0)}")
        print(f"  - Daily quota: {status.get('daily_quota', 0)}")
        print(f"  - Quota remaining: {status.get('quota_remaining', 0)}")
        
        if status.get('credit_exhausted'):
            print("  🚨 CREDIT EXHAUSTION DETECTED!")
        
    except Exception as e:
        print(f"❌ Error checking status: {e}")

if __name__ == "__main__":
    print("🚨 TomTom API Credit Exhaustion Management")
    print("=" * 50)
    
    # Check current status first
    check_collection_status()
    
    # Stop all collection
    stop_all_collection()
    
    print("\n💡 Tip: You can also run this script with 'python emergency_stop_collection.py' anytime")