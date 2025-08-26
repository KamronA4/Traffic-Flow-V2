#!/usr/bin/env python3
"""
Database initialization script for Village platform
Run this to ensure all databases are properly set up
"""

import os
import sys
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

def initialize_databases():
    """Initialize all required databases"""
    print("🗄️  Initializing Village Platform Databases...")
    
    try:
        # Test password hashing first
        print("🔐 Testing password hashing...")
        import hashlib
        import hmac
        
        def test_hash_password(password: str) -> str:
            salt = "village_salt_2024".encode()
            password_bytes = password.encode()
            hashed = hashlib.pbkdf2_hmac('sha256', password_bytes, salt, 100000)
            return hashed.hex()
        
        # Test the hashing
        test_hash = test_hash_password("admin123")
        print(f"   Password hashing test: ✅ Success")
        
        # Import and initialize enterprise authentication
        from utils.enterprise_auth import EnterpriseAuthManager
        print("✅ Initializing enterprise authentication database...")
        auth_manager = EnterpriseAuthManager()
        print(f"   Database created at: {auth_manager.db_path}")
        
        # Import and initialize API management
        from utils.api_management import APIManager
        print("✅ Initializing API management database...")
        api_manager = APIManager()
        print(f"   Database created at: {api_manager.db_path}")
        
        # Import and initialize onboarding
        from utils.onboarding import OnboardingManager
        print("✅ Initializing onboarding database...")
        onboarding_manager = OnboardingManager()
        print(f"   Database created at: {onboarding_manager.db_path}")
        
        # Import and initialize main traffic database
        try:
            from utils.database import get_database
            print("✅ Initializing traffic database...")
            traffic_db = get_database()
            print(f"   Traffic database initialized")
        except Exception as e:
            print(f"⚠️  Traffic database initialization skipped: {e}")
        
        print("\n🎉 All databases initialized successfully!")
        print("\nDefault login credentials:")
        print("   Username: admin")
        print("   Password: admin123")
        print("\nYou can now run: streamlit run main.py")
        
    except Exception as e:
        import traceback
        print(f"❌ Error initializing databases: {e}")
        print("\nDetailed error:")
        traceback.print_exc()
        print("\nPlease check:")
        print("1. All dependencies are installed: pip install -r requirements.txt")
        print("2. You're running from the correct directory")
        print("3. The data directory exists and is writable")
        sys.exit(1)

if __name__ == "__main__":
    initialize_databases()