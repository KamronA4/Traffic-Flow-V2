#!/usr/bin/env python3
"""
Reset credit exhaustion flag and resume collection
Run this script after adding more TomTom API credits
"""

import sys
import os
from pathlib import Path

# Add current directory to path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

def reset_credit_flags():
    """Reset credit exhaustion flags and resume collection"""
    print("🔄 Resetting Credit Exhaustion Flags")
    print("=" * 40)
    
    try:
        # Reset enhanced collector
        print("Resetting enhanced traffic collector...")
        from utils.enhanced_traffic_collector import get_enhanced_collector
        enhanced_collector = get_enhanced_collector()
        enhanced_collector.reset_credit_flag()
        
        # Reset quota tracking for new day/new credits
        enhanced_collector.requests_today = 0
        
        status = enhanced_collector.get_collection_status()
        print(f"✅ Enhanced collector reset")
        print(f"   - Credit exhausted: {status.get('credit_exhausted', False)}")
        print(f"   - API requests today: {status.get('api_requests_today', 0)}")
        print(f"   - Daily quota: {status.get('daily_quota', 0)}")
        
    except Exception as e:
        print(f"❌ Error resetting enhanced collector: {e}")
    
    print("\n" + "=" * 40)
    print("✅ Credit Flags Reset Complete")
    print("\nNext steps:")
    print("1. Collection will resume automatically")
    print("2. Monitor the Live Traffic page to verify data is being collected")
    print("3. Check the Monitoring page for API usage statistics")

def test_api_connection():
    """Test API connection with current credits"""
    print("\n🔍 Testing API Connection")
    print("=" * 40)
    
    try:
        import requests
        import streamlit as st
        
        # Get API key
        try:
            api_key = st.secrets.get("TOMTOM_API_KEY")
            if not api_key or api_key == "your-tomtom-api-key-here":
                api_key = os.getenv('TOMTOM_API_KEY')
        except:
            api_key = os.getenv('TOMTOM_API_KEY')
        
        if not api_key:
            print("❌ No API key found")
            return False
        
        # Test with a simple geocoding request
        url = "https://api.tomtom.com/search/2/search/Providence, RI.json"
        params = {'key': api_key, 'limit': 1}
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            print("✅ API connection successful")
            print("   - Credits are available")
            return True
        elif response.status_code == 403:
            try:
                error_data = response.json()
                if error_data.get('detailedError', {}).get('code') == 'InsufficientFunds':
                    print("❌ API credits still exhausted")
                    print("   - Please add more credits to your TomTom account")
                    return False
                else:
                    print(f"❌ API access forbidden: {error_data}")
                    return False
            except:
                print(f"❌ API error: {response.status_code}")
                return False
        else:
            print(f"❌ API error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing API: {e}")
        return False

if __name__ == "__main__":
    print("🔄 TomTom API Credit Recovery")
    print("=" * 50)
    
    # Test API connection first
    if test_api_connection():
        # Reset credit flags
        reset_credit_flags()
        
        print("\n🎉 Collection should now resume automatically!")
        print("💡 Check the Live Traffic page in a few minutes to verify data is being collected")
    else:
        print("\n⚠️  API credits may still be exhausted")
        print("💡 Please check your TomTom dashboard and add more credits if needed")