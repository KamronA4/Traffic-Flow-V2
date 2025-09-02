# utils/api_management.py - API Management Platform for Village


import streamlit as st
import sqlite3
import json
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import requests
import time
import logging
from flask import Flask, request, jsonify
import threading
import jwt

# Configure logging; Note: find into @ https://docs.python.org/3/library/logging.html#module-logging 
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class APIKeyStatus(Enum):
    """API key status"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    REVOKED = "revoked"

class APIEndpoint(Enum):
    """Available API endpoints"""
    TRAFFIC_INCIDENTS = "traffic_incidents"
    TRAFFIC_FLOW = "traffic_flow"
    ANALYTICS = "analytics"
    PREDICTIONS = "predictions"
    REPORTS = "reports"
    REAL_TIME = "real_time"

@dataclass
class APIKey:
    """API key structure"""
    id: str
    organization_id: str
    key_hash: str
    name: str
    permissions: List[str]
    status: APIKeyStatus
    created_at: datetime
    expires_at: Optional[datetime]
    last_used: Optional[datetime]
    rate_limit: int
    monthly_quota: int

@dataclass
class APIUsage:
    """
    API usage record.
    
    Attributes:
        id: Unique identifier for the usage record
        api_key_id: ID of the API key used
        organization_id: ID of the organization that made the request
        endpoint: API endpoint accessed
        method: HTTP method used (GET, POST, etc.)
        status_code: HTTP status code returned
        response_time: Time taken to process the request in seconds
        timestamp: When the request was made
        ip_address: IP address of the requester
        user_agent: User agent string of the requester
    """
    id: str
    api_key_id: str
    organization_id: str
    endpoint: str
    method: str
    status_code: int
    response_time: float
    timestamp: datetime
    ip_address: str
    user_agent: str

class APIManager:
    """API key and usage management"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Create data directory if it doesn't exist
            import os
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir))
            data_dir = os.path.join(project_root, "data")
            os.makedirs(data_dir, exist_ok=True)
            self.db_path = os.path.join(data_dir, "api_management.db")
        else:
            self.db_path = db_path
        self.secret_key = st.secrets.get("API_SECRET_KEY", "village-api-secret-2024")
        self.init_database()
    
    def init_database(self):
        """Initialize API management database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # API keys table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_keys (
                id TEXT PRIMARY KEY,
                organization_id TEXT NOT NULL,
                key_hash TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                permissions TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                last_used TIMESTAMP,
                rate_limit INTEGER DEFAULT 1000,
                monthly_quota INTEGER DEFAULT 10000
            )
        ''')
        
        # API usage logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_usage (
                id TEXT PRIMARY KEY,
                api_key_id TEXT NOT NULL,
                organization_id TEXT NOT NULL,
                endpoint TEXT NOT NULL,
                method TEXT NOT NULL,
                status_code INTEGER NOT NULL,
                response_time REAL NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ip_address TEXT,
                user_agent TEXT,
                FOREIGN KEY (api_key_id) REFERENCES api_keys (id)
            )
        ''')
        
        # Rate limiting table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rate_limits (
                api_key_id TEXT NOT NULL,
                window_start TIMESTAMP NOT NULL,
                request_count INTEGER DEFAULT 1,
                PRIMARY KEY (api_key_id, window_start),
                FOREIGN KEY (api_key_id) REFERENCES api_keys (id)
            )
        ''')
        
        # API endpoints configuration
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_endpoints (
                endpoint TEXT PRIMARY KEY,
                description TEXT NOT NULL,
                method TEXT NOT NULL,
                rate_limit INTEGER DEFAULT 100,
                requires_auth BOOLEAN DEFAULT 1,
                min_tier TEXT DEFAULT 'basic',
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        conn.commit()
        conn.close()
        
        self.init_default_endpoints()
    
    def init_default_endpoints(self):
        """Initialize default API endpoints"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        endpoints = [
            ("traffic_incidents", "Get traffic incidents", "GET", 100, True, "basic", True),
            ("traffic_flow", "Get traffic flow data", "GET", 200, True, "basic", True),
            ("analytics", "Get traffic analytics", "GET", 50, True, "professional", True),
            ("predictions", "Get traffic predictions", "GET", 25, True, "professional", True),
            ("reports", "Generate custom reports", "POST", 10, True, "enterprise", True),
            ("real_time", "Real-time traffic stream", "GET", 1000, True, "enterprise", True),
        ]
        
        for endpoint_data in endpoints:
            cursor.execute('''
                INSERT OR IGNORE INTO api_endpoints 
                (endpoint, description, method, rate_limit, requires_auth, min_tier, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', endpoint_data)
        
        conn.commit()
        conn.close()
    
    def generate_api_key(self, organization_id: str, name: str, permissions: List[str], 
                        rate_limit: int = 1000, monthly_quota: int = 10000,
                        expires_at: Optional[datetime] = None) -> Tuple[str, str]:
        """
        Description: 
        Generate a new API key for an organization. This is accomplished via 

        Params: 
        - organization_id (str): ID of the organization
        - name (str): Name of the API key
        - permissions (List[str]): List of permissions for the API key
        - rate_limit (int): Rate limit for the API key (default: 1000 requests/hour)
        - monthly_quota (int): Monthly quota for the API key (default: 10000 requests)
        - expires_at (Optional[datetime]): Expiration date for the API key (default: None, meaning no expiration)
        
        Returns:
        - Tuple[str, str]: A tuple containing the API key ID and the raw key string.
        """
        key_id = str(uuid.uuid4()) # note: Using UUID for unique key ID
        raw_key = f"vill_{key_id}_{hashlib.sha256(f'{organization_id}{datetime.now()}'.encode()).hexdigest()[:16]}"
        # Create the raw API keystring which includes:
        # - Prefix "vill_"
        # - Unique key UUID
        # - A 16-character SHA256 hash based on organization ID and current timestamp
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        # Hash the raw key for storage (so that the actual key is not stored in plaintext)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO api_keys 
            (id, organization_id, key_hash, name, permissions, status, expires_at, rate_limit, monthly_quota)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            key_id, organization_id, key_hash, name, json.dumps(permissions),
            APIKeyStatus.ACTIVE.value, expires_at, rate_limit, monthly_quota
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Generated API key for organization {organization_id}")
        return key_id, raw_key
    
    def validate_api_key(self, raw_key: str) -> Optional[APIKey]:
        """Validate API key and return key info"""
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, organization_id, key_hash, name, permissions, status, 
                   created_at, expires_at, last_used, rate_limit, monthly_quota
            FROM api_keys
            WHERE key_hash = ? AND status = 'active'
        ''', (key_hash,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            # Check if key is expired
            expires_at = datetime.fromisoformat(result[7]) if result[7] else None
            if expires_at and datetime.now() > expires_at:
                self.update_key_status(result[0], APIKeyStatus.EXPIRED)
                return None
            
            return APIKey(
                id=result[0],
                organization_id=result[1],
                key_hash=result[2],
                name=result[3],
                permissions=json.loads(result[4]),
                status=APIKeyStatus(result[5]),
                created_at=datetime.fromisoformat(result[6]),
                expires_at=expires_at,
                last_used=datetime.fromisoformat(result[8]) if result[8] else None,
                rate_limit=result[9],
                monthly_quota=result[10]
            )
        
        return None
    
    def check_rate_limit(self, api_key: APIKey) -> bool:
        """Check if API key has exceeded rate limit"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check hourly rate limit
        window_start = datetime.now().replace(minute=0, second=0, microsecond=0)
        
        cursor.execute('''
            SELECT COALESCE(SUM(request_count), 0) as total_requests
            FROM rate_limits
            WHERE api_key_id = ? AND window_start >= ?
        ''', (api_key.id, window_start - timedelta(hours=1)))
        
        result = cursor.fetchone()
        current_requests = result[0] if result else 0
        
        conn.close()
        
        return current_requests < api_key.rate_limit
    
    def check_monthly_quota(self, api_key: APIKey) -> bool:
        """Check if API key has exceeded monthly quota"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check monthly usage
        month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        cursor.execute('''
            SELECT COUNT(*) as monthly_usage
            FROM api_usage
            WHERE api_key_id = ? AND timestamp >= ?
        ''', (api_key.id, month_start))
        
        result = cursor.fetchone()
        monthly_usage = result[0] if result else 0
        
        conn.close()
        
        return monthly_usage < api_key.monthly_quota
    
    def log_api_usage(self, api_key: APIKey, endpoint: str, method: str, 
                     status_code: int, response_time: float,
                     ip_address: str = None, user_agent: str = None):
        """Log API usage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Log usage
        usage_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO api_usage 
            (id, api_key_id, organization_id, endpoint, method, status_code, 
             response_time, ip_address, user_agent)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            usage_id, api_key.id, api_key.organization_id, endpoint, method,
            status_code, response_time, ip_address, user_agent
        ))
        
        # Update rate limiting
        window_start = datetime.now().replace(minute=0, second=0, microsecond=0)
        cursor.execute('''
            INSERT OR REPLACE INTO rate_limits (api_key_id, window_start, request_count)
            VALUES (?, ?, COALESCE((SELECT request_count FROM rate_limits 
                                  WHERE api_key_id = ? AND window_start = ?), 0) + 1)
        ''', (api_key.id, window_start, api_key.id, window_start))
        
        # Update last used
        cursor.execute('''
            UPDATE api_keys SET last_used = CURRENT_TIMESTAMP WHERE id = ?
        ''', (api_key.id,))
        
        conn.commit()
        conn.close()
    
    def get_organization_keys(self, organization_id: str) -> List[APIKey]:
        """Get all API keys for organization"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, organization_id, key_hash, name, permissions, status, 
                   created_at, expires_at, last_used, rate_limit, monthly_quota
            FROM api_keys
            WHERE organization_id = ?
            ORDER BY created_at DESC
        ''', (organization_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        keys = []
        for result in results:
            keys.append(APIKey(
                id=result[0],
                organization_id=result[1],
                key_hash=result[2],
                name=result[3],
                permissions=json.loads(result[4]),
                status=APIKeyStatus(result[5]),
                created_at=datetime.fromisoformat(result[6]),
                expires_at=datetime.fromisoformat(result[7]) if result[7] else None,
                last_used=datetime.fromisoformat(result[8]) if result[8] else None,
                rate_limit=result[9],
                monthly_quota=result[10]
            ))
        
        return keys
    
    def get_usage_analytics(self, organization_id: str, days: int = 30) -> Dict[str, Any]:
        """Get API usage analytics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        start_date = datetime.now() - timedelta(days=days)
        
        # Total requests
        cursor.execute('''
            SELECT COUNT(*) as total_requests
            FROM api_usage
            WHERE organization_id = ? AND timestamp >= ?
        ''', (organization_id, start_date))
        
        total_requests = cursor.fetchone()[0]
        
        # Requests by endpoint
        cursor.execute('''
            SELECT endpoint, COUNT(*) as request_count
            FROM api_usage
            WHERE organization_id = ? AND timestamp >= ?
            GROUP BY endpoint
            ORDER BY request_count DESC
        ''', (organization_id, start_date))
        
        endpoint_usage = dict(cursor.fetchall())
        
        # Requests by day
        cursor.execute('''
            SELECT DATE(timestamp) as date, COUNT(*) as request_count
            FROM api_usage
            WHERE organization_id = ? AND timestamp >= ?
            GROUP BY DATE(timestamp)
            ORDER BY date
        ''', (organization_id, start_date))
        
        daily_usage = dict(cursor.fetchall())
        
        # Average response time
        cursor.execute('''
            SELECT AVG(response_time) as avg_response_time
            FROM api_usage
            WHERE organization_id = ? AND timestamp >= ?
        ''', (organization_id, start_date))
        
        avg_response_time = cursor.fetchone()[0] or 0
        
        # Error rate
        cursor.execute('''
            SELECT 
                COUNT(*) as total_requests,
                COUNT(CASE WHEN status_code >= 400 THEN 1 END) as error_requests
            FROM api_usage
            WHERE organization_id = ? AND timestamp >= ?
        ''', (organization_id, start_date))
        
        result = cursor.fetchone()
        error_rate = (result[1] / result[0]) * 100 if result[0] > 0 else 0
        
        conn.close()
        
        return {
            "total_requests": total_requests,
            "endpoint_usage": endpoint_usage,
            "daily_usage": daily_usage,
            "avg_response_time": avg_response_time,
            "error_rate": error_rate
        }
    
    def update_key_status(self, key_id: str, status: APIKeyStatus):
        """Update API key status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE api_keys SET status = ? WHERE id = ?
        ''', (status.value, key_id))
        
        conn.commit()
        conn.close()
    
    def revoke_key(self, key_id: str):
        """Revoke API key"""
        self.update_key_status(key_id, APIKeyStatus.REVOKED)
        logger.info(f"Revoked API key {key_id}")

def show_api_management_page():
    """Show API management page for organizations"""
    from .enterprise_auth import get_current_user, require_auth
    
    if not require_auth:
        return
    
    user_org = get_current_user()
    if not user_org:
        return
    
    user, organization = user_org
    
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #faf8f3 0%, #f5f1e8 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        border-left: 4px solid #2d5016;
    ">
        <h1 style="color: #2d5016; margin: 0 0 1rem 0;">API Management</h1>
        <p style="color: #5a7c47; margin: 0;">
            Manage your API keys, monitor usage, and access developer documentation
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    api_manager = APIManager()
    
    # Tabs for different sections
    tab1, tab2, tab3, tab4 = st.tabs(["API Keys", "Usage Analytics", "Documentation", "Webhooks"])
    
    with tab1:
        show_api_keys_section(api_manager, organization)
    
    with tab2:
        show_usage_analytics_section(api_manager, organization)
    
    with tab3:
        show_api_documentation()
    
    with tab4:
        show_webhooks_section(organization)

def show_api_keys_section(api_manager: APIManager, organization):
    """Show API keys management section"""
    st.subheader("Your API Keys")
    
    # Create new API key
    with st.expander("Create New API Key"):
        with st.form("new_api_key"):
            col1, col2 = st.columns(2)
            
            with col1:
                key_name = st.text_input("Key Name", placeholder="Production API Key")
                permissions = st.multiselect(
                    "Permissions",
                    ["traffic_incidents", "traffic_flow", "analytics", "predictions", "reports", "real_time"],
                    default=["traffic_incidents", "traffic_flow"]
                )
            
            with col2:
                rate_limit = st.number_input("Rate Limit (requests/hour)", min_value=100, max_value=10000, value=1000)
                monthly_quota = st.number_input("Monthly Quota", min_value=1000, max_value=1000000, value=10000)
            
            expires_in = st.selectbox("Expires In", ["Never", "30 days", "90 days", "1 year"])
            
            if st.form_submit_button("Create API Key"):
                if key_name and permissions:
                    expires_at = None
                    if expires_in != "Never":
                        days = {"30 days": 30, "90 days": 90, "1 year": 365}[expires_in]
                        expires_at = datetime.now() + timedelta(days=days)
                    
                    key_id, raw_key = api_manager.generate_api_key(
                        organization.id, key_name, permissions, rate_limit, monthly_quota, expires_at
                    )
                    
                    st.success("API Key created successfully!")
                    st.code(raw_key, language="text")
                    st.warning("⚠️ Save this key now. You won't be able to see it again!")
                else:
                    st.error("Please provide a name and select permissions")
    
    # Existing API keys
    keys = api_manager.get_organization_keys(organization.id)
    
    if keys:
        for key in keys:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                
                with col1:
                    st.markdown(f"**{key.name}**")
                    st.caption(f"ID: {key.id}")
                
                with col2:
                    status_color = {
                        "active": "🟢",
                        "suspended": "🟡",
                        "expired": "🔴",
                        "revoked": "❌"
                    }
                    st.markdown(f"{status_color[key.status.value]} {key.status.value.title()}")
                    st.caption(f"Created: {key.created_at.strftime('%Y-%m-%d')}")
                
                with col3:
                    st.markdown(f"**Rate Limit:** {key.rate_limit}/hour")
                    st.markdown(f"**Monthly Quota:** {key.monthly_quota:,}")
                
                with col4:
                    if key.status == APIKeyStatus.ACTIVE:
                        if st.button("Revoke", key=f"revoke_{key.id}"):
                            api_manager.revoke_key(key.id)
                            st.rerun()
                
                st.markdown("---")
    else:
        st.info("No API keys found. Create your first API key above.")

def show_usage_analytics_section(api_manager: APIManager, organization):
    """Show usage analytics section"""
    st.subheader("Usage Analytics")
    
    # Time range selector
    time_range = st.selectbox("Time Range", ["Last 7 days", "Last 30 days", "Last 90 days"])
    days = {"Last 7 days": 7, "Last 30 days": 30, "Last 90 days": 90}[time_range]
    
    analytics = api_manager.get_usage_analytics(organization.id, days)
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Requests", f"{analytics['total_requests']:,}")
    
    with col2:
        st.metric("Avg Response Time", f"{analytics['avg_response_time']:.2f}ms")
    
    with col3:
        st.metric("Error Rate", f"{analytics['error_rate']:.2f}%")
    
    with col4:
        daily_avg = analytics['total_requests'] / days
        st.metric("Daily Average", f"{daily_avg:.0f}")
    
    # Charts
    if analytics['daily_usage']:
        st.subheader("Daily Usage")
        import pandas as pd
        daily_df = pd.DataFrame(list(analytics['daily_usage'].items()), columns=['Date', 'Requests'])
        st.line_chart(daily_df.set_index('Date'))
    
    if analytics['endpoint_usage']:
        st.subheader("Usage by Endpoint")
        import pandas as pd
        endpoint_df = pd.DataFrame(list(analytics['endpoint_usage'].items()), columns=['Endpoint', 'Requests'])
        st.bar_chart(endpoint_df.set_index('Endpoint'))

def show_api_documentation():
    """Show API documentation"""
    st.subheader("API Documentation")
    
    st.markdown("""
    ### Base URL
    ```
    https://api.village.com/v1
    ```
    
    ### Authentication
    Include your API key in the header:
    ```
    Authorization: Bearer YOUR_API_KEY
    ```
    """)
    
    # Endpoint documentation
    endpoints = [
        {
            "endpoint": "/traffic/incidents",
            "method": "GET",
            "description": "Get traffic incidents",
            "parameters": [
                {"name": "location", "type": "string", "description": "Filter by location"},
                {"name": "severity", "type": "integer", "description": "Filter by severity (1-5)"},
                {"name": "limit", "type": "integer", "description": "Maximum number of results (default: 100)"}
            ],
            "example": """
curl -X GET "https://api.village.com/v1/traffic/incidents?location=Providence&severity=3" \\
  -H "Authorization: Bearer YOUR_API_KEY"
            """
        },
        {
            "endpoint": "/traffic/flow",
            "method": "GET",
            "description": "Get traffic flow data",
            "parameters": [
                {"name": "location", "type": "string", "description": "Location identifier"},
                {"name": "start_time", "type": "string", "description": "Start time (ISO 8601)"},
                {"name": "end_time", "type": "string", "description": "End time (ISO 8601)"}
            ],
            "example": """
curl -X GET "https://api.village.com/v1/traffic/flow?location=Providence" \\
  -H "Authorization: Bearer YOUR_API_KEY"
            """
        }
    ]
    
    for endpoint in endpoints:
        with st.expander(f"{endpoint['method']} {endpoint['endpoint']}"):
            st.markdown(f"**Description:** {endpoint['description']}")
            
            if endpoint['parameters']:
                st.markdown("**Parameters:**")
                for param in endpoint['parameters']:
                    st.markdown(f"- `{param['name']}` ({param['type']}): {param['description']}")
            
            st.markdown("**Example:**")
            st.code(endpoint['example'], language="bash")

def show_webhooks_section(organization):
    """Show webhooks management section"""
    st.subheader("Webhooks")
    
    st.info("Webhooks allow you to receive real-time notifications when events occur in your Village account.")
    
    # Create webhook
    with st.expander("Create New Webhook"):
        with st.form("new_webhook"):
            webhook_url = st.text_input("Webhook URL", placeholder="https://your-server.com/webhook")
            
            events = st.multiselect(
                "Events to Subscribe",
                ["incident.created", "incident.updated", "incident.resolved", "alert.triggered"],
                default=["incident.created"]
            )
            
            secret = st.text_input("Secret (optional)", placeholder="webhook_secret_123")
            
            if st.form_submit_button("Create Webhook"):
                if webhook_url and events:
                    st.success("Webhook created successfully!")
                    st.json({
                        "id": "webhook_123",
                        "url": webhook_url,
                        "events": events,
                        "status": "active",
                        "created_at": datetime.now().isoformat()
                    })
                else:
                    st.error("Please provide a URL and select events")
    
    # Existing webhooks
    st.markdown("### Your Webhooks")
    st.info("No webhooks configured yet. Create your first webhook above.")

# API authentication decorator
def require_api_key(func):
    """Decorator to require API key for API endpoints"""
    def wrapper(*args, **kwargs):
        # This would be used in the actual API implementation
        # For now, it's a placeholder
        return func(*args, **kwargs)
    return wrapper