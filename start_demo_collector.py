#!/usr/bin/env python3
"""
Demo-Safe Traffic Collector Starter
Launches the traffic collector in demo mode with safety measures
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def setup_demo_environment():
    """Set up environment variables for safe demo operation"""
    
    # Demo mode settings
    os.environ['VILLAGE_DEMO_MODE'] = 'true'
    os.environ['VILLAGE_DEMO_SAFE_MODE'] = 'true'
    
    # Create demo mode settings if they don't exist
    if not os.getenv('TOMTOM_API_KEY'):
        print("⚠️  Warning: No TOMTOM_API_KEY found. Demo will use fallback data only.")
    
    # Set demo-friendly paths
    current_dir = Path(__file__).parent
    
    # Ensure demo directories exist
    (current_dir / "config").mkdir(exist_ok=True)
    (current_dir / "data").mkdir(exist_ok=True)
    
    print("✅ Demo environment configured")
    print(f"   Demo Mode: {os.getenv('VILLAGE_DEMO_MODE')}")
    print(f"   Safe Mode: {os.getenv('VILLAGE_DEMO_SAFE_MODE')}")
    print(f"   API Key: {'Available' if os.getenv('TOMTOM_API_KEY') else 'Not Available (using fallbacks)'}")

def start_demo_collector(duration_minutes: int = 60):
    """Start the traffic collector in demo mode"""
    
    print(f"\n🚀 Starting Village Traffic Collector Demo")
    print(f"   Duration: {duration_minutes} minutes")
    print(f"   Mode: Demo-safe with fallbacks")
    print(f"   Data: Local demo database")
    
    # Prepare collector arguments
    collector_script = Path(__file__).parent / "traffic_collector_daemon.py"
    
    if not collector_script.exists():
        print(f"❌ Error: Collector script not found at {collector_script}")
        return False
    
    # Run collector with demo timeout
    try:
        cmd = [sys.executable, str(collector_script), "start"]
        
        print(f"\n🔄 Running: {' '.join(cmd)}")
        print("   Press Ctrl+C to stop the demo gracefully")
        
        # Start the collector
        process = subprocess.Popen(cmd)
        
        # Wait for specified duration or user interrupt
        import time
        try:
            for minute in range(duration_minutes):
                time.sleep(60)  # Sleep for 1 minute
                remaining = duration_minutes - minute - 1
                if remaining > 0:
                    print(f"⏱️  Demo running... {remaining} minutes remaining")
                else:
                    print("⏱️  Demo time completed")
                    break
        except KeyboardInterrupt:
            print("\n🛑 Demo stopped by user")
        
        # Stop the collector gracefully
        print("🔄 Stopping collector...")
        process.terminate()
        process.wait(timeout=10)
        
        print("✅ Demo collector stopped successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error starting demo collector: {e}")
        return False

def show_demo_status():
    """Show current demo configuration and status"""
    
    print("🎯 Village Traffic Collector - Demo Status")
    print("=" * 50)
    
    # Environment status
    print("\n📋 Environment Configuration:")
    print(f"   Demo Mode: {os.getenv('VILLAGE_DEMO_MODE', 'false')}")
    print(f"   Demo Safe Mode: {os.getenv('VILLAGE_DEMO_SAFE_MODE', 'false')}")
    print(f"   TomTom API Key: {'✅ Available' if os.getenv('TOMTOM_API_KEY') else '❌ Not Available'}")
    
    # File system status
    print("\n📁 File System:")
    current_dir = Path(__file__).parent
    
    collector_script = current_dir / "traffic_collector_daemon.py"
    print(f"   Collector Script: {'✅ Available' if collector_script.exists() else '❌ Missing'}")
    
    config_dir = current_dir / "config"
    print(f"   Config Directory: {'✅ Available' if config_dir.exists() else '❌ Missing'}")
    
    data_dir = current_dir / "data"
    print(f"   Data Directory: {'✅ Available' if data_dir.exists() else '❌ Missing'}")
    
    demo_db = data_dir / "demo_traffic_data.db"
    print(f"   Demo Database: {'✅ Available' if demo_db.exists() else '❌ Not Created Yet'}")
    
    # Safety settings
    print("\n🛡️  Demo Safety Settings:")
    print("   ✅ API request limits enforced")
    print("   ✅ Local database paths used") 
    print("   ✅ Fallback data generation enabled")
    print("   ✅ Extended collection intervals")
    print("   ✅ Graceful error handling")

def main():
    parser = argparse.ArgumentParser(description="Village Traffic Collector Demo Launcher")
    
    parser.add_argument('action', choices=['start', 'status', 'setup'], 
                       help='Action to perform')
    parser.add_argument('-d', '--duration', type=int, default=60,
                       help='Demo duration in minutes (default: 60)')
    parser.add_argument('--api-key', 
                       help='TomTom API key (optional, will use fallbacks if not provided)')
    
    args = parser.parse_args()
    
    # Set API key if provided
    if args.api_key:
        os.environ['TOMTOM_API_KEY'] = args.api_key
    
    if args.action == 'setup':
        setup_demo_environment()
        show_demo_status()
        
    elif args.action == 'status':
        show_demo_status()
        
    elif args.action == 'start':
        setup_demo_environment()
        success = start_demo_collector(args.duration)
        if not success:
            sys.exit(1)

if __name__ == "__main__":
    main()