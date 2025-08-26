# Authentication System - Deep Dive

## Overview

The Village Platform authentication system (`utils/enterprise_auth.py`) provides a robust, multi-tenant authentication solution with role-based access control (RBAC), JWT token management, and enterprise-grade security features.

## Architecture

### Core Components

```python
# Key classes in the authentication system
class User:
    """Represents an authenticated user"""
    - id: str
    - email: str
    - name: str
    - role: UserRole
    - organization_id: str
    - created_at: datetime
    - last_login: datetime

class Organization:
    """Multi-tenant organization"""
    - id: str
    - name: str
    - domain: str
    - tier: SubscriptionTier
    - settings: dict
    - created_at: datetime

class UserRole(Enum):
    """User permission levels"""
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"
    FIELD_WORKER = "field_worker"
```

## Authentication Flow

### 1. User Registration

```python
def register_user(email: str, password: str, name: str, organization_id: str) -> User:
    """
    Register a new user with secure password hashing.
    
    Process:
    1. Validate email format and uniqueness
    2. Check organization exists and has capacity
    3. Generate salt and hash password
    4. Create user record in database
    5. Send verification email
    6. Log registration event
    """
```

**Security Measures:**
- Email validation with regex
- Password strength requirements (8+ chars, mixed case, numbers)
- PBKDF2 password hashing with 100,000 iterations
- Unique salt per password
- Rate limiting on registration attempts

### 2. User Login

```python
def login(email: str, password: str) -> Dict[str, str]:
    """
    Authenticate user and return JWT tokens.
    
    Process:
    1. Retrieve user by email
    2. Verify password hash
    3. Check account status (active, verified)
    4. Generate access and refresh tokens
    5. Update last login timestamp
    6. Log authentication event
    """
```

**Token Structure:**
```json
{
  "user_id": "uuid",
  "email": "user@example.com",
  "role": "analyst",
  "organization_id": "org_uuid",
  "exp": 1234567890,
  "iat": 1234567890,
  "jti": "unique_token_id"
}
```

### 3. Session Management

```python
# Streamlit session state management
if 'auth_token' not in st.session_state:
    st.session_state.auth_token = None
    st.session_state.user = None
    st.session_state.organization = None
```

**Session Features:**
- Automatic token renewal before expiry
- Secure cookie storage (httpOnly, secure flags)
- Session timeout after inactivity
- Concurrent session limiting
- Device tracking and management

## Role-Based Access Control (RBAC)

### Permission Matrix

| Feature | Admin | Analyst | Viewer | Field Worker |
|---------|-------|---------|--------|--------------|
| View Dashboard | ✓ | ✓ | ✓ | ✓ |
| View Reports | ✓ | ✓ | ✓ | Limited |
| Create Reports | ✓ | ✓ | ✗ | ✗ |
| Modify Settings | ✓ | ✗ | ✗ | ✗ |
| Manage Users | ✓ | ✗ | ✗ | ✗ |
| API Access | ✓ | ✓ | ✗ | ✗ |
| Delete Data | ✓ | ✗ | ✗ | ✗ |

### Permission Checking

```python
@require_role([UserRole.ADMIN, UserRole.ANALYST])
def sensitive_operation():
    """Decorator-based permission checking"""
    pass

# Manual permission check
if not has_permission(current_user, "create_report"):
    st.error("Insufficient permissions")
    return
```

## Security Features

### 1. Password Security

**Hashing Implementation:**
```python
def hash_password(password: str) -> Tuple[bytes, bytes]:
    """Generate salt and hash password"""
    salt = os.urandom(32)  # 32 bytes = 256 bits
    pwdhash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        100000  # iterations
    )
    return salt, pwdhash
```

**Password Policies:**
- Minimum 8 characters
- At least one uppercase letter
- At least one number
- No common passwords (checked against list)
- Password history (prevent reuse)
- Expiration after 90 days (configurable)

### 2. Token Security

**JWT Configuration:**
```python
JWT_CONFIG = {
    "algorithm": "HS256",
    "access_token_expire": 3600,      # 1 hour
    "refresh_token_expire": 604800,   # 7 days
    "issuer": "village-platform",
    "audience": "village-users"
}
```

**Token Validation:**
- Signature verification
- Expiration checking
- Issuer/audience validation
- Token blacklisting for logout
- JTI tracking for one-time use

### 3. Brute Force Protection

```python
class LoginAttemptTracker:
    """Track and limit login attempts"""
    
    def check_rate_limit(self, email: str, ip_address: str) -> bool:
        attempts = self.get_recent_attempts(email, ip_address)
        
        if attempts > 5:
            lockout_time = 15 * (2 ** (attempts - 5))  # Exponential backoff
            return False, lockout_time
            
        return True, 0
```

### 4. Audit Logging

```python
def log_auth_event(event_type: str, user_id: str, details: dict):
    """Log all authentication events for security audit"""
    event = {
        "timestamp": datetime.utcnow(),
        "event_type": event_type,
        "user_id": user_id,
        "ip_address": get_client_ip(),
        "user_agent": get_user_agent(),
        "details": details
    }
    audit_logger.log(event)
```

**Logged Events:**
- Login attempts (success/failure)
- Password changes
- Permission changes
- Account lockouts
- Token generation/revocation
- Suspicious activity

## Multi-Tenancy

### Organization Isolation

```python
class OrganizationContext:
    """Ensure data isolation between organizations"""
    
    def filter_by_organization(self, query):
        """Add organization filter to all queries"""
        return query.filter(
            data.organization_id == current_user.organization_id
        )
```

### Features:
- Complete data isolation
- Separate user pools
- Organization-specific settings
- Custom branding (Enterprise tier)
- Subdomain support
- SSO integration (Enterprise)

## Integration Points

### 1. Streamlit Integration

```python
# Authentication decorator for pages
def require_auth(func):
    """Ensure user is authenticated before accessing page"""
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            show_login_page()
            st.stop()
        return func(*args, **kwargs)
    return wrapper

# Usage
@require_auth
def protected_page():
    st.write("Welcome to protected content!")
```

### 2. API Integration

```python
# API authentication middleware
@app.before_request
def verify_api_token():
    """Verify JWT token for API requests"""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"error": "Missing authorization"}), 401
    
    try:
        token = auth_header.split(' ')[1]  # Bearer <token>
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        g.current_user = get_user(payload['user_id'])
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401
```

### 3. Database Integration

```sql
-- Users table schema
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    password_hash BLOB NOT NULL,
    password_salt BLOB NOT NULL,
    role TEXT NOT NULL,
    organization_id TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (organization_id) REFERENCES organizations(id)
);

-- Authentication logs
CREATE TABLE auth_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id TEXT,
    event_type TEXT NOT NULL,
    ip_address TEXT,
    user_agent TEXT,
    success BOOLEAN,
    details JSON
);
```

## Best Practices

### 1. Secure Development
- Never log passwords or tokens
- Use environment variables for secrets
- Implement proper error handling without leaking info
- Regular security audits
- Dependency scanning

### 2. User Experience
- Clear error messages without security details
- Password strength indicators
- Remember me functionality (secure)
- Social login options (OAuth2)
- Passwordless options (magic links)

### 3. Compliance
- GDPR compliance (data deletion)
- Password policy configuration
- Session timeout configuration
- Audit trail retention
- Data encryption at rest

## Troubleshooting

### Common Issues

1. **"Invalid token" errors**
   - Check token expiration
   - Verify SECRET_KEY consistency
   - Ensure proper token format

2. **Login failures**
   - Check password hash compatibility
   - Verify database connectivity
   - Review audit logs

3. **Permission denied**
   - Verify user role assignment
   - Check organization tier
   - Review permission matrix

### Debug Mode

```python
# Enable auth debugging
AUTH_DEBUG = os.getenv('AUTH_DEBUG', 'false').lower() == 'true'

if AUTH_DEBUG:
    logging.getLogger('auth').setLevel(logging.DEBUG)
```

## Future Enhancements

1. **Two-Factor Authentication (2FA)**
   - TOTP support
   - SMS backup codes
   - Authenticator app integration

2. **Single Sign-On (SSO)**
   - SAML 2.0 support
   - OAuth2/OpenID Connect
   - Active Directory integration

3. **Advanced Security**
   - Biometric authentication
   - Hardware token support
   - Zero-trust architecture

4. **Enhanced Monitoring**
   - Real-time threat detection
   - Anomaly detection
   - Security dashboards

This authentication system provides a solid foundation for secure, scalable multi-tenant applications while maintaining flexibility for future enhancements.