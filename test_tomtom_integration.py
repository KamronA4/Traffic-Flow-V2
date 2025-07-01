#!/usr/bin/env python3
"""
Test script to verify TomTom API integration works correctly
"""

import sys
import os
sys.path.append('code')

from MapFetcher import RI_MapFetcher

# Test configuration
TEST_API_KEY = "ldZpXKM4XNxvJpSb2ZGfUeSgLXt8Db9G"  # TomTom API key
TEST_TOWN = "Providence"
TEST_BBOX = "41.146240,-71.899414,41.748681,-71.088867"  # Rhode Island

def test_geocoding():
    """Test TomTom geocoding functionality"""
    print("Testing TomTom Geocoding...")
    try:
        fetcher = RI_MapFetcher(TEST_API_KEY)
        lat, lng = fetcher.get_town_coords(TEST_TOWN)
        print(f"✓ Geocoding successful: {TEST_TOWN} -> ({lat}, {lng})")
        return True
    except Exception as e:
        print(f"✗ Geocoding failed: {e}")
        return False

def test_traffic_incidents():
    """Test TomTom traffic incidents functionality"""
    print("Testing TomTom Traffic Incidents...")
    try:
        fetcher = RI_MapFetcher(TEST_API_KEY)
        incidents = fetcher.get_traffic_incidents(TEST_BBOX)
        print(f"✓ Traffic incidents successful: Found {len(incidents)} incidents")
        
        if incidents:
            # Check first incident structure
            incident = incidents[0]
            required_fields = ['id', 'description', 'severity', 'lat', 'lng']
            missing_fields = [field for field in required_fields if field not in incident]
            
            if missing_fields:
                print(f"✗ Missing required fields: {missing_fields}")
                return False
            else:
                print("✓ Incident structure is correct")
                print(f"Sample incident: {incident}")
        
        return True
    except Exception as e:
        print(f"✗ Traffic incidents failed: {e}")
        return False

def test_api_key_validation():
    """Test API key validation"""
    print("Testing API key validation...")
    try:
        fetcher = RI_MapFetcher("invalid_key")
        fetcher.get_town_coords(TEST_TOWN)
        print("✗ API key validation failed - should have thrown an error")
        return False
    except Exception as e:
        print(f"✓ API key validation works: {e}")
        return True

if __name__ == "__main__":
    print("=== TomTom API Integration Test ===")
    print(f"API Key: {TEST_API_KEY[:10]}..." if len(TEST_API_KEY) > 10 else "API Key not set")
    print()
    
    if TEST_API_KEY == "YOUR_TOMTOM_API_KEY_HERE":
        print("⚠️  Please set a valid TomTom API key in TEST_API_KEY to run tests")
        print("   You can get a free API key from https://developer.tomtom.com/")
        sys.exit(1)
    
    tests = [
        test_api_key_validation,
        test_geocoding,
        test_traffic_incidents
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"=== Test Results: {passed}/{total} passed ===")
    
    if passed == total:
        print("🎉 All tests passed! TomTom integration is ready.")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Please check the errors above.")
        sys.exit(1)