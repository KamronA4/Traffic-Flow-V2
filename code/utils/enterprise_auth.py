# utils/enterprise_auth.py - Enterprise Authentication and Multi-tenancy System

import streamlit as st
import hashlib
import hmac
import json
import sqlite3
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import uuid
import logging

# Try to import JWT, fallback to None if not available
try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    jwt = None
    JWT_AVAILABLE = False
    st.warning("PyJWT not installed. Please run: pip install PyJWT")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserRole(Enum):
    """User roles for access control"""
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"
    FIELD_WORKER = "field_worker"

class SubscriptionTier(Enum):
    """Subscription tiers for municipalities"""
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"

@dataclass
class User:
    """User information"""
    id: str
    username: str
    email: str
    role: UserRole
    organization_id: str
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool = True

@dataclass
class Organization:
    """Organization/Municipality information"""
    id: str
    name: str
    tier: SubscriptionTier
    max_users: int
    api_quota: int
    features: List[str]
    created_at: datetime
    subscription_expires: datetime
    contact_email: str
    is_active: bool = True

class EnterpriseAuthManager:
    """Enterprise authentication and multi-tenancy manager"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Check multiple possible locations for the auth database
            import os
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir))
            
            # Try databases directory first (where demo accounts are created)
            databases_dir = os.path.join(project_root, "databases")
            databases_path = os.path.join(databases_dir, "enterprise_auth.db")
            
            # Try data directory as fallback
            data_dir = os.path.join(project_root, "data")
            data_path = os.path.join(data_dir, "enterprise_auth.db")
            
            if os.path.exists(databases_path):
                self.db_path = databases_path
            else:
                # Create databases directory and use it
                os.makedirs(databases_dir, exist_ok=True)
                self.db_path = databases_path
        else:
            self.db_path = db_path
        self.secret_key = self._get_secure_secret_key()
        self.init_database()
    
    def _get_secure_secret_key(self) -> str:
        """Get JWT secret key from secure sources"""
        # Try Streamlit secrets first
        try:
            secret_key = st.secrets.get("JWT_SECRET_KEY")
            if secret_key and secret_key != "village-secret-key-change-in-production":
                return secret_key
        except:
            pass
        
        # Try environment variable
        secret_key = os.getenv('JWT_SECRET_KEY')
        if secret_key:
            return secret_key
        
        # Generate a secure random key for development (not recommended for production)
        if os.getenv('VILLAGE_DEMO_MODE', 'false').lower() == 'true':
            logger.warning("Using generated secret key for demo mode. Not secure for production!")
            return f"demo-key-{uuid.uuid4()}"
        
        # Fail with helpful error message for production
        raise ValueError(
            "JWT_SECRET_KEY must be set in secrets.toml or environment variables for production use. "
            "Set VILLAGE_DEMO_MODE=true for development with auto-generated key."
        )
    
    def _get_secure_password(self, env_var: str, fallback: str) -> str:
        \"\"\"Get password from secure sources with fallback\"\"\"
        # Try Streamlit secrets first
        try:
            password = st.secrets.get(env_var)
            if password:
                return password
        except:
            pass
        
        # Try environment variable
        password = os.getenv(env_var)
        if password:
            return password
        
        # Use fallback only in demo mode
        if os.getenv('VILLAGE_DEMO_MODE', 'false').lower() == 'true':
            logger.warning(f"Using fallback password for {env_var} in demo mode")
            return fallback
        
        # Generate secure random password for production
        import secrets
        import string
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        secure_password = ''.join(secrets.choice(alphabet) for _ in range(16))
        logger.info(f"Generated secure password for {env_var}. Store this securely!")
        return secure_password
        
    def init_database(self):
        """Initialize authentication database"""
        try:
            # Ensure directory exists
            db_dir = os.path.dirname(self.db_path)
            os.makedirs(db_dir, exist_ok=True)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
        except Exception as e:
            logger.error(f"Error creating database at {self.db_path}: {e}")
            raise
        
        # Create organizations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS organizations (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                tier TEXT NOT NULL,
                max_users INTEGER DEFAULT 5,
                api_quota INTEGER DEFAULT 10000,
                features TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                subscription_expires TIMESTAMP,
                contact_email TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                organization_id TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (organization_id) REFERENCES organizations (id)
            )
        ''')
        
        # Create API usage tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                organization_id TEXT NOT NULL,
                endpoint TEXT NOT NULL,
                requests_count INTEGER DEFAULT 1,
                date DATE DEFAULT CURRENT_DATE,
                FOREIGN KEY (organization_id) REFERENCES organizations (id)
            )
        ''')
        
        # Create sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                organization_id TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (organization_id) REFERENCES organizations (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # Create default admin organization if it doesn't exist
        self.create_default_organization()
    
    def create_default_organization(self):
        """Create default organization and demo accounts for development"""
        # Only create demo accounts if explicitly enabled via environment variable
        if not os.getenv('VILLAGE_CREATE_DEMO_ACCOUNTS', 'false').lower() == 'true':
            logger.info("Demo account creation disabled. Set VILLAGE_CREATE_DEMO_ACCOUNTS=true to enable.")
            return
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get secure passwords from environment or secrets
        ridot_password = self._get_secure_password('RIDOT_DEMO_PASSWORD', 'Demo2024!')
        admin_password = self._get_secure_password('VILLAGE_ADMIN_PASSWORD', 'admin123')
        
        # Create RIDOT demo organization
        cursor.execute("SELECT id FROM organizations WHERE name = 'Rhode Island Department of Transportation'")
        if not cursor.fetchone():
            org_id = "ridot-demo-org"
            cursor.execute('''
                INSERT INTO organizations (id, name, tier, max_users, api_quota, features, 
                                        subscription_expires, contact_email)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                org_id,
                "Rhode Island Department of Transportation",
                SubscriptionTier.ENTERPRISE.value,
                1000,
                1000000,
                json.dumps(["all_features"]),
                datetime.now() + timedelta(days=365),
                "admin@ridot.ri.gov"
            ))
            
            # Create demo users with different roles
            demo_users = [
                {
                    "id": "demo-admin-001",
                    "username": "admin@ridot.ri.gov",
                    "email": "admin@ridot.ri.gov",
                    "role": "admin",
                    "description": "RIDOT Director - Full platform access"
                },
                {
                    "id": "demo-analyst-001", 
                    "username": "analyst@ridot.ri.gov",
                    "email": "analyst@ridot.ri.gov",
                    "role": "analyst",
                    "description": "Senior Traffic Analyst - Analytics and reporting"
                },
                {
                    "id": "demo-viewer-001",
                    "username": "viewer@ridot.ri.gov",
                    "email": "viewer@ridot.ri.gov",
                    "role": "viewer", 
                    "description": "Municipal Official - Dashboard viewing only"
                },
                {
                    "id": "demo-field-001",
                    "username": "field@ridot.ri.gov",
                    "email": "field@ridot.ri.gov",
                    "role": "field_worker",
                    "description": "Field Inspector - Mobile app access"
                }
            ]
            
            for user in demo_users:
                password_hash = self.hash_password(ridot_password)
                cursor.execute('''
                    INSERT INTO users (id, username, email, password_hash, role, organization_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    user['id'],
                    user['username'],
                    user['email'],
                    password_hash,
                    user['role'],
                    org_id
                ))
            
            conn.commit()
            logger.info("Created RIDOT demo organization and users")
        
        # Also create the default Village Admin for fallback (only if explicitly enabled)
        if os.getenv('VILLAGE_CREATE_ADMIN_ACCOUNT', 'false').lower() == 'true':
            cursor.execute("SELECT id FROM organizations WHERE name = 'Village Admin'")
            if not cursor.fetchone():
                admin_org_id = str(uuid.uuid4())
                cursor.execute('''
                    INSERT INTO organizations (id, name, tier, max_users, api_quota, features, 
                                            subscription_expires, contact_email)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    admin_org_id,
                    "Village Admin",
                    SubscriptionTier.ENTERPRISE.value,
                    1000,
                    1000000,
                    json.dumps(["all_features"]),
                    datetime.now() + timedelta(days=365),
                    "admin@village.com"
                ))
                
                # Create default admin user
                user_id = str(uuid.uuid4())
                password_hash = self.hash_password(admin_password)
                cursor.execute('''
                    INSERT INTO users (id, username, email, password_hash, role, organization_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    user_id,
                    "admin",
                    "admin@village.com",
                    password_hash,
                    UserRole.ADMIN.value,
                    admin_org_id
                ))
                
                conn.commit()
                logger.info("Created default admin organization and user")
        
        conn.close()
    
    def hash_password(self, password: str) -> str:
        """Hash password with salt"""
        salt = "village_salt_2024".encode()
        password_bytes = password.encode()
        # Use PBKDF2 from hashlib
        hashed = hashlib.pbkdf2_hmac('sha256', password_bytes, salt, 100000)
        return hashed.hex()
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return hmac.compare_digest(self.hash_password(password), password_hash)
    
    def authenticate_user(self, username: str, password: str) -> Optional[Tuple[User, Organization]]:
        """Authenticate user and return user/organization info"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT u.id, u.username, u.email, u.password_hash, u.role, u.organization_id, 
                   u.created_at, u.last_login, u.is_active,
                   o.id, o.name, o.tier, o.max_users, o.api_quota, o.features,
                   o.created_at, o.subscription_expires, o.contact_email, o.is_active
            FROM users u
            JOIN organizations o ON u.organization_id = o.id
            WHERE u.username = ? AND u.is_active = 1 AND o.is_active = 1
        ''', (username,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result and self.verify_password(password, result[3]):
            # Update last login
            self.update_last_login(result[0])
            
            # Create user object
            user = User(
                id=result[0],
                username=result[1],
                email=result[2],
                role=UserRole(result[4]),
                organization_id=result[5],
                created_at=datetime.fromisoformat(result[6]),
                last_login=datetime.fromisoformat(result[7]) if result[7] else None,
                is_active=bool(result[8])
            )
            
            # Create organization object
            organization = Organization(
                id=result[9],
                name=result[10],
                tier=SubscriptionTier(result[11]),
                max_users=result[12],
                api_quota=result[13],
                features=json.loads(result[14]),
                created_at=datetime.fromisoformat(result[15]),
                subscription_expires=datetime.fromisoformat(result[16]),
                contact_email=result[17],
                is_active=bool(result[18])
            )
            
            return user, organization
        
        return None
    
    def update_last_login(self, user_id: str):
        """Update user's last login timestamp"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?
        ''', (user_id,))
        
        conn.commit()
        conn.close()
    
    def create_session(self, user: User, organization: Organization) -> str:
        """Create user session and return session token"""
        session_id = str(uuid.uuid4())
        expires_at = datetime.now() + timedelta(hours=8)  # 8-hour sessions
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO user_sessions (id, user_id, organization_id, expires_at)
            VALUES (?, ?, ?, ?)
        ''', (session_id, user.id, organization.id, expires_at))
        
        conn.commit()
        conn.close()
        
        # Create JWT token or fallback to session ID
        if JWT_AVAILABLE:
            token_payload = {
                "session_id": session_id,
                "user_id": user.id,
                "organization_id": organization.id,
                "role": user.role.value,
                "tier": organization.tier.value,
                "exp": expires_at.timestamp()
            }
            token = jwt.encode(token_payload, self.secret_key, algorithm="HS256")
        else:
            # Fallback to simple session ID if JWT not available
            token = f"session_{session_id}"
        
        return token
    
    def validate_session(self, token: str) -> Optional[Tuple[User, Organization]]:
        """Validate session token and return user/organization info"""
        try:
            # Handle JWT or fallback session ID
            if JWT_AVAILABLE and not token.startswith("session_"):
                payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
                session_id = payload["session_id"]
            else:
                # Fallback: extract session ID from simple token
                session_id = token.replace("session_", "")
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT s.user_id, s.organization_id, s.expires_at, s.is_active
                FROM user_sessions s
                WHERE s.id = ? AND s.is_active = 1
            ''', (session_id,))
            
            session_result = cursor.fetchone()
            
            if session_result and datetime.now() < datetime.fromisoformat(session_result[2]):
                # Get user and organization info
                cursor.execute('''
                    SELECT u.id, u.username, u.email, u.role, u.organization_id, 
                           u.created_at, u.last_login, u.is_active,
                           o.id, o.name, o.tier, o.max_users, o.api_quota, o.features,
                           o.created_at, o.subscription_expires, o.contact_email, o.is_active
                    FROM users u
                    JOIN organizations o ON u.organization_id = o.id
                    WHERE u.id = ? AND u.is_active = 1 AND o.is_active = 1
                ''', (session_result[0],))
                
                result = cursor.fetchone()
                conn.close()
                
                if result:
                    user = User(
                        id=result[0],
                        username=result[1],
                        email=result[2],
                        role=UserRole(result[3]),
                        organization_id=result[4],
                        created_at=datetime.fromisoformat(result[5]),
                        last_login=datetime.fromisoformat(result[6]) if result[6] else None,
                        is_active=bool(result[7])
                    )
                    
                    organization = Organization(
                        id=result[8],
                        name=result[9],
                        tier=SubscriptionTier(result[10]),
                        max_users=result[11],
                        api_quota=result[12],
                        features=json.loads(result[13]),
                        created_at=datetime.fromisoformat(result[14]),
                        subscription_expires=datetime.fromisoformat(result[15]),
                        contact_email=result[16],
                        is_active=bool(result[17])
                    )
                    
                    return user, organization
            
            conn.close()
            
        except Exception as e:
            if JWT_AVAILABLE:
                if "jwt" in str(e).lower():
                    logger.warning("JWT token error")
                else:
                    logger.error(f"Session validation error: {e}")
            else:
                logger.error(f"Session validation error: {e}")
        
        return None
    
    def logout_user(self, session_id: str):
        """Logout user by deactivating session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE user_sessions SET is_active = 0 WHERE id = ?
        ''', (session_id,))
        
        conn.commit()
        conn.close()
    
    def check_feature_access(self, organization: Organization, feature: str) -> bool:
        """Check if organization has access to specific feature"""
        if "all_features" in organization.features:
            return True
        return feature in organization.features
    
    def check_api_quota(self, organization_id: str, endpoint: str) -> bool:
        """Check if organization has remaining API quota"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get organization quota
        cursor.execute('''
            SELECT api_quota FROM organizations WHERE id = ?
        ''', (organization_id,))
        
        quota_result = cursor.fetchone()
        if not quota_result:
            conn.close()
            return False
        
        max_quota = quota_result[0]
        
        # Get today's usage
        cursor.execute('''
            SELECT COALESCE(SUM(requests_count), 0) as today_usage
            FROM api_usage
            WHERE organization_id = ? AND date = CURRENT_DATE
        ''', (organization_id,))
        
        usage_result = cursor.fetchone()
        conn.close()
        
        today_usage = usage_result[0] if usage_result else 0
        
        return today_usage < max_quota
    
    def track_api_usage(self, organization_id: str, endpoint: str, count: int = 1):
        """Track API usage for billing and quota management"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO api_usage (organization_id, endpoint, requests_count)
            VALUES (?, ?, ?)
            ON CONFLICT(organization_id, endpoint, date) DO UPDATE SET
            requests_count = requests_count + ?
        ''', (organization_id, endpoint, count, count))
        
        conn.commit()
        conn.close()
    
    def get_organization_usage_stats(self, organization_id: str) -> Dict[str, Any]:
        """Get organization usage statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get quota and current usage
        cursor.execute('''
            SELECT o.api_quota, COALESCE(SUM(u.requests_count), 0) as today_usage
            FROM organizations o
            LEFT JOIN api_usage u ON o.id = u.organization_id AND u.date = CURRENT_DATE
            WHERE o.id = ?
            GROUP BY o.id, o.api_quota
        ''', (organization_id,))
        
        result = cursor.fetchone()
        
        # Get user count
        cursor.execute('''
            SELECT COUNT(*) as user_count FROM users WHERE organization_id = ? AND is_active = 1
        ''', (organization_id,))
        
        user_count = cursor.fetchone()[0]
        
        conn.close()
        
        if result:
            return {
                "api_quota": result[0],
                "today_usage": result[1],
                "quota_remaining": result[0] - result[1],
                "quota_usage_percent": (result[1] / result[0]) * 100 if result[0] > 0 else 0,
                "user_count": user_count
            }
        
        return {}

# Streamlit authentication decorators and functions
def require_auth(func):
    """Decorator to require authentication for Streamlit pages"""
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            show_login_page()
            return
        return func(*args, **kwargs)
    return wrapper

def require_role(required_role: UserRole):
    """Decorator to require specific role"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not is_authenticated():
                show_login_page()
                return
            
            user, _ = get_current_user()
            if user.role != required_role and user.role != UserRole.ADMIN:
                show_role_requirement_error(required_role)
                return
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def has_role_access(user_role: UserRole, required_role: UserRole) -> bool:
    """Check if user role has access to required role"""
    # Admin has access to everything
    if user_role == UserRole.ADMIN:
        return True
    
    # Role hierarchy: ADMIN > ANALYST > FIELD_WORKER > VIEWER
    role_hierarchy = {
        UserRole.ADMIN: 4,
        UserRole.ANALYST: 3,
        UserRole.FIELD_WORKER: 2,
        UserRole.VIEWER: 1
    }
    
    return role_hierarchy.get(user_role, 0) >= role_hierarchy.get(required_role, 0)

def require_feature(feature: str):
    """Decorator to require specific feature access"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not is_authenticated():
                show_login_page()
                return
            
            _, organization = get_current_user()
            auth_manager = EnterpriseAuthManager()
            
            if not auth_manager.check_feature_access(organization, feature):
                st.error(f"Feature '{feature}' not available in your subscription tier: {organization.tier.value.title()}")
                st.info("Please upgrade your subscription to access this feature.")
                
                # Show upgrade options
                with st.expander("🚀 Upgrade Options"):
                    st.markdown("""
                    **Starter Plan** - Planning & Reports  
                    **Pro Plan** - Advanced Analytics & 3D Visualization  
                    **Enterprise Plan** - All Features + Priority Support
                    """)
                    if st.button("Contact Sales"):
                        st.info("Please contact sales@village.com for upgrade options.")
                return
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def is_authenticated() -> bool:
    """Check if user is authenticated"""
    return "auth_token" in st.session_state and st.session_state.auth_token is not None

def get_current_user() -> Optional[Tuple[User, Organization]]:
    """Get current authenticated user and organization"""
    if not is_authenticated():
        return None
    
    auth_manager = EnterpriseAuthManager()
    return auth_manager.validate_session(st.session_state.auth_token)

def create_organization(name: str, contact_email: str, tier: SubscriptionTier = SubscriptionTier.FREE) -> str:
    """Create a new organization and return its ID"""
    auth_manager = EnterpriseAuthManager()
    conn = sqlite3.connect(auth_manager.db_path)
    cursor = conn.cursor()
    
    org_id = str(uuid.uuid4())
    
    # Tier-based limits
    tier_config = {
        SubscriptionTier.FREE: {"max_users": 2, "api_quota": 1000, "features": ["basic_analytics"]},
        SubscriptionTier.STARTER: {"max_users": 5, "api_quota": 10000, "features": ["basic_analytics", "planning", "reports"]},
        SubscriptionTier.PRO: {"max_users": 25, "api_quota": 50000, "features": ["basic_analytics", "planning", "reports", "predictive", "3d_viz"]},
        SubscriptionTier.ENTERPRISE: {"max_users": 1000, "api_quota": 1000000, "features": ["all_features"]}
    }
    
    config = tier_config[tier]
    
    cursor.execute('''
        INSERT INTO organizations (id, name, tier, max_users, api_quota, features, 
                                subscription_expires, contact_email)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        org_id,
        name,
        tier.value,
        config["max_users"],
        config["api_quota"],
        json.dumps(config["features"]),
        datetime.now() + timedelta(days=30),  # 30-day trial
        contact_email
    ))
    
    conn.commit()
    conn.close()
    
    return org_id

def create_user(username: str, email: str, password: str, organization_id: str, role: UserRole = UserRole.VIEWER) -> str:
    """Create a new user and return their ID"""
    auth_manager = EnterpriseAuthManager()
    conn = sqlite3.connect(auth_manager.db_path)
    cursor = conn.cursor()
    
    # Check if username or email already exists
    cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?", (username, email))
    if cursor.fetchone():
        conn.close()
        raise ValueError("Username or email already exists")
    
    user_id = str(uuid.uuid4())
    password_hash = auth_manager.hash_password(password)
    
    cursor.execute('''
        INSERT INTO users (id, username, email, password_hash, role, organization_id)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        user_id,
        username,
        email,
        password_hash,
        role.value,
        organization_id
    ))
    
    conn.commit()
    conn.close()
    
    return user_id

def show_signup_page():
    """Show comprehensive sign-up flow"""
    st.markdown("""
    <div style="
        max-width: 500px;
        margin: 3rem auto;
        padding: 2rem;
        background: linear-gradient(135deg, #faf8f3 0%, #f5f1e8 100%);
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        border-left: 4px solid #2d5016;
    ">
        <h2 style="text-align: center; color: #2d5016; margin-bottom: 1rem;">
            🌲 Join Village
        </h2>
        <p style="text-align: center; color: #5a7c47; margin-bottom: 2rem;">
            Municipal Traffic Planning Platform
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sign-up type selection
    signup_type = st.radio(
        "Sign-up Type:",
        ["New Organization", "Join Existing Organization"],
        help="Choose whether you're creating a new municipal account or joining an existing one"
    )
    
    if signup_type == "New Organization":
        show_organization_signup()
    else:
        show_user_signup()

def show_organization_signup():
    """Show organization creation form"""
    with st.form("org_signup_form"):
        st.subheader("Create New Organization")
        
        # Organization details
        org_name = st.text_input(
            "Organization Name *",
            placeholder="City of Providence, Town of Warwick, etc.",
            help="Enter your municipality or organization name"
        )
        
        contact_email = st.text_input(
            "Contact Email *",
            placeholder="admin@cityname.gov",
            help="Primary contact email for the organization"
        )
        
        # Admin user details
        st.subheader("Administrator Account")
        admin_username = st.text_input(
            "Admin Username *",
            placeholder="admin",
            help="Username for the administrator account"
        )
        
        admin_email = st.text_input(
            "Admin Email *",
            placeholder="admin@cityname.gov",
            help="Email for the administrator account"
        )
        
        admin_password = st.text_input(
            "Admin Password *",
            type="password",
            help="Password for the administrator account (min 8 characters)"
        )
        
        confirm_password = st.text_input(
            "Confirm Password *",
            type="password",
            help="Confirm the administrator password"
        )
        
        # Subscription tier
        tier = st.selectbox(
            "Subscription Tier",
            ["Free (Trial)", "Starter", "Pro", "Enterprise"],
            help="Choose your subscription tier (can be upgraded later)"
        )
        
        # Terms acceptance
        accept_terms = st.checkbox(
            "I accept the Terms of Service and Privacy Policy",
            help="Required to create an account"
        )
        
        submit_org = st.form_submit_button("Create Organization", use_container_width=True)
        
        if submit_org:
            # Validation
            errors = []
            if not org_name.strip():
                errors.append("Organization name is required")
            if not contact_email or "@" not in contact_email:
                errors.append("Valid contact email is required")
            if not admin_username.strip():
                errors.append("Admin username is required")
            if not admin_email or "@" not in admin_email:
                errors.append("Valid admin email is required")
            if len(admin_password) < 8:
                errors.append("Password must be at least 8 characters")
            if admin_password != confirm_password:
                errors.append("Passwords do not match")
            if not accept_terms:
                errors.append("You must accept the terms of service")
            
            if errors:
                for error in errors:
                    st.error(error)
            else:
                try:
                    # Map tier selection
                    tier_mapping = {
                        "Free (Trial)": SubscriptionTier.FREE,
                        "Starter": SubscriptionTier.STARTER,
                        "Pro": SubscriptionTier.PRO,
                        "Enterprise": SubscriptionTier.ENTERPRISE
                    }
                    
                    # Create organization
                    org_id = create_organization(org_name, contact_email, tier_mapping[tier])
                    
                    # Create admin user
                    user_id = create_user(admin_username, admin_email, admin_password, org_id, UserRole.ADMIN)
                    
                    st.success(f"Organization '{org_name}' created successfully!")
                    st.success(f"Administrator account '{admin_username}' created.")
                    st.info("You can now log in with your administrator credentials.")
                    
                    # Auto-login the new admin
                    if st.button("Login Now"):
                        auth_manager = EnterpriseAuthManager()
                        auth_result = auth_manager.authenticate_user(admin_username, admin_password)
                        if auth_result:
                            user, organization = auth_result
                            token = auth_manager.create_session(user, organization)
                            
                            st.session_state.auth_token = token
                            st.session_state.user = user
                            st.session_state.organization = organization
                            st.rerun()
                    
                except ValueError as e:
                    st.error(f"Error creating account: {e}")
                except Exception as e:
                    st.error(f"Unexpected error: {e}")

def show_user_signup():
    """Show user registration form for existing organization"""
    with st.form("user_signup_form"):
        st.subheader("Join Existing Organization")
        
        # Organization lookup
        org_code = st.text_input(
            "Organization Code",
            placeholder="Enter organization invitation code",
            help="Contact your organization administrator for the invitation code"
        )
        
        # User details
        username = st.text_input(
            "Username *",
            placeholder="your.username",
            help="Choose a unique username"
        )
        
        email = st.text_input(
            "Email *",
            placeholder="your.email@domain.com",
            help="Your email address"
        )
        
        password = st.text_input(
            "Password *",
            type="password",
            help="Password (min 8 characters)"
        )
        
        confirm_password = st.text_input(
            "Confirm Password *",
            type="password",
            help="Confirm your password"
        )
        
        role = st.selectbox(
            "Requested Role",
            ["Viewer", "Analyst", "Field Worker"],
            help="Select your role (subject to administrator approval)"
        )
        
        accept_terms = st.checkbox(
            "I accept the Terms of Service and Privacy Policy",
            help="Required to create an account"
        )
        
        submit_user = st.form_submit_button("Request Account", use_container_width=True)
        
        if submit_user:
            # Validation
            errors = []
            if not org_code.strip():
                errors.append("Organization code is required")
            if not username.strip():
                errors.append("Username is required")
            if not email or "@" not in email:
                errors.append("Valid email is required")
            if len(password) < 8:
                errors.append("Password must be at least 8 characters")
            if password != confirm_password:
                errors.append("Passwords do not match")
            if not accept_terms:
                errors.append("You must accept the terms of service")
            
            if errors:
                for error in errors:
                    st.error(error)
            else:
                st.info("Account creation for existing organizations is not yet implemented.")
                st.info("Please contact your organization administrator or use the 'New Organization' option.")

def show_login_page():
    """Show login page with sign-up option"""
    st.markdown("""
    <div style="
        max-width: 400px;
        margin: 5rem auto;
        padding: 2rem;
        background: linear-gradient(135deg, #faf8f3 0%, #f5f1e8 100%);
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        border-left: 4px solid #2d5016;
    ">
        <h2 style="text-align: center; color: #2d5016; margin-bottom: 2rem;">
            🌲 Village Login
        </h2>
        <p style="text-align: center; color: #5a7c47; margin-bottom: 2rem;">
            Municipal Traffic Planning Platform
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Login/Signup tabs
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            
            col1, col2 = st.columns(2)
            with col1:
                submit_button = st.form_submit_button("Login", use_container_width=True)
            with col2:
                if st.form_submit_button("Demo Login", use_container_width=True):
                    # Use secure demo credentials from environment
                    username = os.getenv('VILLAGE_DEMO_USERNAME', 'admin@ridot.ri.gov')
                    password = os.getenv('RIDOT_DEMO_PASSWORD', 'Demo2024!')
                    submit_button = True
                    
                    # Show warning for production use
                    if not os.getenv('VILLAGE_DEMO_MODE', 'false').lower() == 'true':
                        st.warning("Demo login disabled in production. Set VILLAGE_DEMO_MODE=true to enable.")
                        submit_button = False
            
            if submit_button:
                if username and password:
                    auth_manager = EnterpriseAuthManager()
                    auth_result = auth_manager.authenticate_user(username, password)
                    
                    if auth_result:
                        user, organization = auth_result
                        token = auth_manager.create_session(user, organization)
                        
                        st.session_state.auth_token = token
                        st.session_state.user = user
                        st.session_state.organization = organization
                        
                        st.success(f"Welcome, {user.username}! ({organization.name})")
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
                else:
                    st.error("Please enter both username and password")
    
    with tab2:
        show_signup_page()

def show_logout_button():
    """Show logout button in sidebar"""
    if is_authenticated():
        user, organization = get_current_user()
        if user and organization:
            st.sidebar.markdown(f"**{user.username}** ({organization.name})")
            st.sidebar.markdown(f"*{user.role.value.title()}* | *{organization.tier.value.title()}*")
            
            if st.sidebar.button("Logout"):
                # Extract session ID from token for logout
                try:
                    auth_manager = EnterpriseAuthManager()
                    
                    # Handle JWT or fallback session ID
                    if JWT_AVAILABLE and not st.session_state.auth_token.startswith("session_"):
                        payload = jwt.decode(st.session_state.auth_token, 
                                           st.secrets.get("JWT_SECRET_KEY", "village-secret-key-change-in-production"), 
                                           algorithms=["HS256"])
                        session_id = payload["session_id"]
                    else:
                        # Fallback: extract session ID from simple token
                        session_id = st.session_state.auth_token.replace("session_", "")
                    
                    auth_manager.logout_user(session_id)
                except:
                    pass
                
                # Clear session state
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                
                st.rerun()

def show_usage_stats():
    """Show usage statistics in sidebar"""
    if is_authenticated():
        user, organization = get_current_user()
        if user and organization:
            auth_manager = EnterpriseAuthManager()
            stats = auth_manager.get_organization_usage_stats(organization.id)
            
            if stats:
                st.sidebar.markdown("### Usage Statistics")
                st.sidebar.progress(stats["quota_usage_percent"] / 100)
                st.sidebar.markdown(f"**API Calls Today:** {stats['today_usage']:,} / {stats['api_quota']:,}")
                st.sidebar.markdown(f"**Users:** {stats['user_count']} / {organization.max_users}")
                
                if stats["quota_usage_percent"] > 80:
                    st.sidebar.warning("⚠️ Approaching API quota limit")
                elif stats["quota_usage_percent"] > 95:
                    st.sidebar.error("🚨 API quota almost exhausted")

def show_role_requirement_error(required_role: UserRole):
    """Show role requirement error message"""
    st.error(f"Access denied. This feature requires {required_role.value.title()} role or higher.")
    st.info("Please contact your organization administrator to upgrade your access level.")
    
    # Show current user role
    if is_authenticated():
        user, _ = get_current_user()
        if user:
            st.info(f"Your current role: {user.role.value.title()}")