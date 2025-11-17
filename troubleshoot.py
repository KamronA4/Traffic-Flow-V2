#!/usr/bin/env python3
# troubleshoot.py - Troubleshooting script for Village data issues

import os
import sys
from pathlib import Path

# Add code directory to path
code_dir = Path(__file__).parent / "code"
sys.path.insert(0, str(code_dir))

def check_environment():
    """Check environment setup"""
    print("🔍 Checking environment setup...")
    
    issues = []
    
    # Check .env file
    env_file = Path(__file__).parent / ".env"
    if not env_file.exists():
        issues.append(".env file not found")
    else:
        print(".env file found")
        
        # Check API keys
        from dotenv import load_dotenv
        load_dotenv()
        
        tomtom_key = os.getenv('TOMTOM_API_KEY')
        perplexity_key = os.getenv('PERPLEXITY_API_KEY')
        
        if not tomtom_key:
            issues.append("TOMTOM_API_KEY not found in .env")
        else:
            print("TomTom API key found")
            
        if not perplexity_key:
            issues.append("PERPLEXITY_API_KEY not found in .env")
        else:
            print("Perplexity API key found")
    
    # Check required directories
    data_dir = Path(__file__).parent / "data"
    if not data_dir.exists():
        data_dir.mkdir(exist_ok=True)
        print("Created data directory")
    else:
        print("Data directory exists")
    
    return issues

def check_dependencies():
    """Check required dependencies"""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        'streamlit', 'pandas', 'numpy', 'folium', 'requests', 
        'plotly', 'scipy', 'scikit-learn', 'python-dotenv'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"{package}")
        except ImportError:
            missing.append(package)
            print(f"{package} - not installed")
    
    if missing:
        print(f"\nInstall missing packages with:")
        print(f"pip install {' '.join(missing)}")
    
    return missing

def check_database():
    """Check database connectivity and structure"""
    print("Checking database...")
    
    try:
        from utils.database import get_database
        
        db = get_database()
        stats = db.get_database_stats()
        
        print(f"Database connected")
        print(f"  - Traffic incidents: {stats.get('traffic_incidents_count', 0)}")
        print(f"  - Traffic flow: {stats.get('traffic_flow_count', 0)}")
        print(f"  - API usage: {stats.get('api_usage_count', 0)}")
        print(f"  - Database size: {stats.get('database_size_mb', 0):.1f} MB")
        
        return True
        
    except Exception as e:
        print(f"Database error: {e}")
        return False

def check_data_collection():
    """Check data collection system"""
    print("Checking data collection...")
    
    try:
        from utils.smart_collector import get_collector
        
        collector = get_collector()
        status = collector.get_collection_status()
        
        print(f"Collector status:")
        print(f"  - Running: {status['is_running']}")
        print(f"  - Requests today: {status['requests_today']}")
        print(f"  - Daily quota: {status['daily_quota']}")
        print(f"  - Quota usage: {status['quota_usage_percent']:.1f}%")
        
        # Check individual targets
        print(f"  - Collection targets: {len(status['targets'])}")
        for target in status['targets'][:3]:  # Show first 3
            print(f"    • {target['name']}: {target['priority']} priority")
        
        return True
        
    except Exception as e:
        print(f"Collection system error: {e}")
        return False

def check_csv_fallback():
    """Check CSV fallback data"""
    print("Checking CSV fallback...")
    
    csv_paths = [
        "traffic_incidents.csv",
        "code/traffic_incidents.csv",
        "data/traffic_incidents.csv"
    ]
    
    for path in csv_paths:
        csv_file = Path(__file__).parent / path
        if csv_file.exists():
            try:
                import pandas as pd
                df = pd.read_csv(csv_file)
                print(f"Found CSV at {path} with {len(df)} records")
                return True
            except Exception as e:
                print(f"CSV error at {path}: {e}")
    
    print("No valid CSV fallback found")
    return False

def check_streamlit_pages():
    """Check Streamlit pages can be imported"""
    print("🔍 Checking Streamlit pages...")
    
    pages = ['live_traffic', 'analytics', 'planning', 'reports', 'monitoring']
    
    for page in pages:
        try:
            module = __import__(f'pages.{page}', fromlist=[page])
            print(f"{page} page")
        except Exception as e:
            print(f"{page} page: {e}")

def run_diagnostics():
    """Run comprehensive diagnostics"""
    print("Village System Diagnostics")
    print("=" * 50)
    
    all_issues = []
    
    # Check environment
    env_issues = check_environment()
    all_issues.extend(env_issues)
    
    print()
    
    # Check dependencies
    missing_deps = check_dependencies()
    if missing_deps:
        all_issues.append(f"Missing dependencies: {', '.join(missing_deps)}")
    
    print()
    
    # Check database
    if not check_database():
        all_issues.append("Database connectivity issues")
    
    print()
    
    # Check data collection
    if not check_data_collection():
        all_issues.append("Data collection system issues")
    
    print()
    
    # Check CSV fallback
    if not check_csv_fallback():
        all_issues.append("No CSV fallback available")
    
    print()
    
    # Check Streamlit pages
    check_streamlit_pages()
    
    print("\n" + "=" * 50)
    
    if all_issues:
        print("Issues found:")
        for issue in all_issues:
            print(f"  - {issue}")
        print("\n💡 Fix these issues before running the application")
    else:
        print("All checks passed! System should be working correctly.")
        print("\nTo start the application:")
        print("   streamlit run code/main.py")

if __name__ == "__main__":
    run_diagnostics()