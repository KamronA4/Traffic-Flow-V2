#!/usr/bin/env python3
"""Verify authentication system works correctly"""

import os
import sys
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

def verify_authentication():
    """Verify authentication system works"""
    print("🔐 Verifying Authentication System...")
    
    try:
        # Import the authentication manager
        from utils.enterprise_auth import EnterpriseAuthManager
        
        # Initialize the manager
        auth_manager = EnterpriseAuthManager()
        print(f"✅ Authentication manager initialized")
        print(f"   Database path: {auth_manager.db_path}")
        
        # Test password hashing
        test_password = "admin123"
        hashed = auth_manager.hash_password(test_password)
        print(f"✅ Password hashing working: {hashed[:20]}...")
        
        # Test password verification
        is_valid = auth_manager.verify_password(test_password, hashed)
        print(f"✅ Password verification working: {is_valid}")
        
        # Test authentication
        result = auth_manager.authenticate_user("admin", "admin123")
        if result:
            user, organization = result
            print(f"✅ Authentication successful:")
            print(f"   User: {user.username} ({user.email})")
            print(f"   Organization: {organization.name}")
            print(f"   Tier: {organization.tier.value}")
            
            # Test session creation
            token = auth_manager.create_session(user, organization)
            print(f"✅ Session token created: {token[:20]}...")
            
            # Test session validation
            validated = auth_manager.validate_session(token)
            if validated:
                print(f"✅ Session validation working")
            else:
                print(f"❌ Session validation failed")
        else:
            print(f"❌ Authentication failed - default user not found")
            
        print("\n🎉 Authentication system verification complete!")
        
    except Exception as e:
        import traceback
        print(f"❌ Error verifying authentication: {e}")
        print("\nDetailed error:")
        traceback.print_exc()
        return False
        
    return True

if __name__ == "__main__":
    success = verify_authentication()
    if not success:
        sys.exit(1)