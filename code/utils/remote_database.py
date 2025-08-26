#!/usr/bin/env python3
"""
Remote Database Access Utilities
Provides access to VM-hosted traffic data via REST API
"""

import os
import requests
import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import streamlit as st
from functools import wraps
import time

logger = logging.getLogger(__name__)

class RemoteDataError(Exception):
    """Custom exception for remote data access errors"""
    pass

class RemoteTrafficData:
    """
    Client for accessing remote traffic data from VM-hosted service
    """
    
    def __init__(self, 
                 api_base_url: str = None, 
                 api_key: str = None,
                 timeout: int = 30,
                 cache_ttl: int = 300):  # 5 minutes default cache
        
        # Configuration from environment or Streamlit secrets
        self.api_base_url = (
            api_base_url or 
            os.getenv('TRAFFIC_API_URL') or
            st.secrets.get('TRAFFIC_API_URL', 'http://localhost:8080')
        ).rstrip('/')
        
        self.api_key = (
            api_key or 
            os.getenv('TRAFFIC_API_KEY') or
            st.secrets.get('TRAFFIC_API_KEY')
        )
        
        self.timeout = timeout
        self.cache_ttl = cache_ttl
        
        # Session for connection reuse
        self.session = requests.Session()
        self.session.headers.update({
            'X-API-Key': self.api_key,
            'Content-Type': 'application/json'
        })
        
        logger.info(f"RemoteTrafficData initialized with base URL: {self.api_base_url}")
    
    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make authenticated API request with error handling"""
        url = f"{self.api_base_url}/{endpoint.lstrip('/')}"
        
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout:
            raise RemoteDataError(f"Request timeout after {self.timeout} seconds")
        except requests.exceptions.ConnectionError:
            raise RemoteDataError(f"Cannot connect to remote service at {self.api_base_url}")
        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                raise RemoteDataError("Invalid API key or authentication failed")
            elif response.status_code == 503:
                raise RemoteDataError("Remote service temporarily unavailable")
            else:
                raise RemoteDataError(f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            raise RemoteDataError(f"Unexpected error: {str(e)}")
    
    @st.cache_data(ttl=300)  # Cache for 5 minutes
    def check_connection(_self) -> Tuple[bool, str]:
        """Check if remote service is accessible"""
        try:
            response = _self._make_request('/health')
            if response.get('status') == 'healthy':
                return True, "Connected successfully"
            else:
                return False, f"Service unhealthy: {response.get('error', 'Unknown error')}"
        except RemoteDataError as e:
            return False, str(e)
    
    @st.cache_data(ttl=60)  # Cache for 1 minute
    def get_service_status(_self) -> Dict[str, Any]:
        """Get remote service status and statistics"""
        try:
            return _self._make_request('/status')
        except RemoteDataError as e:
            logger.error(f"Failed to get service status: {e}")
            return {'error': str(e)}
    
    @st.cache_data(ttl=300)  # Cache for 5 minutes  
    def get_incidents(_self, 
                      start_date: str = None,
                      end_date: str = None,
                      limit: int = 1000,
                      severity_min: int = None,
                      bbox: str = None) -> pd.DataFrame:
        """
        Get traffic incidents data
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format  
            limit: Maximum number of records to return
            severity_min: Minimum severity level (1-5)
            bbox: Bounding box as 'lat1,lng1,lat2,lng2'
            
        Returns:
            DataFrame with incidents data
        """
        params = {'limit': limit}
        
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        if severity_min:
            params['severity_min'] = severity_min
        if bbox:
            params['bbox'] = bbox
            
        try:
            response = _self._make_request('/incidents', params)
            incidents_data = response.get('incidents', [])
            
            if not incidents_data:
                return pd.DataFrame()
            
            df = pd.DataFrame(incidents_data)
            
            # Ensure timestamp is datetime
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                
            # Add derived columns for compatibility with existing code
            if 'timestamp' in df.columns:
                df['date'] = df['timestamp'].dt.date
                df['hour'] = df['timestamp'].dt.hour
                
            logger.info(f"Retrieved {len(df)} incidents from remote service")
            return df
            
        except RemoteDataError as e:
            logger.error(f"Failed to get incidents: {e}")
            st.error(f"Failed to load incidents data: {e}")
            return pd.DataFrame()
    
    @st.cache_data(ttl=300)  # Cache for 5 minutes
    def get_flow_data(_self,
                      start_date: str = None,
                      end_date: str = None,
                      limit: int = 1000,
                      congestion_min: int = None,
                      bbox: str = None) -> pd.DataFrame:
        """
        Get traffic flow data
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            limit: Maximum number of records to return
            congestion_min: Minimum congestion level (1-5)
            bbox: Bounding box as 'lat1,lng1,lat2,lng2'
            
        Returns:
            DataFrame with flow data
        """
        params = {'limit': limit}
        
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        if congestion_min:
            params['congestion_min'] = congestion_min
        if bbox:
            params['bbox'] = bbox
            
        try:
            response = _self._make_request('/flow', params)
            flow_data = response.get('flow_data', [])
            
            if not flow_data:
                return pd.DataFrame()
            
            df = pd.DataFrame(flow_data)
            
            # Ensure timestamp is datetime
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                
            # Add derived columns for compatibility
            if 'timestamp' in df.columns:
                df['date'] = df['timestamp'].dt.date
                df['hour'] = df['timestamp'].dt.hour
                
            logger.info(f"Retrieved {len(df)} flow records from remote service")
            return df
            
        except RemoteDataError as e:
            logger.error(f"Failed to get flow data: {e}")
            st.error(f"Failed to load flow data: {e}")
            return pd.DataFrame()
    
    @st.cache_data(ttl=600)  # Cache for 10 minutes
    def get_analytics_summary(_self) -> Dict[str, Any]:
        """Get analytics summary for dashboard"""
        try:
            return _self._make_request('/analytics/summary')
        except RemoteDataError as e:
            logger.error(f"Failed to get analytics summary: {e}")
            return {'error': str(e)}
    
    @st.cache_data(ttl=3600)  # Cache for 1 hour
    def get_zones(_self) -> List[Dict[str, Any]]:
        """Get collection zones with statistics"""
        try:
            response = _self._make_request('/zones')
            return response.get('zones', [])
        except RemoteDataError as e:
            logger.error(f"Failed to get zones: {e}")
            return []
    
    def export_data(self, data_type: str, format_type: str = 'json', **kwargs) -> Any:
        """
        Export data in various formats
        
        Args:
            data_type: Type of data ('incidents', 'flow', 'analytics')
            format_type: Export format ('json', 'csv')
            **kwargs: Additional parameters (start_date, end_date, limit)
            
        Returns:
            Exported data or file content
        """
        params = {'format': format_type}
        params.update(kwargs)
        
        try:
            if format_type == 'csv':
                # For CSV, we need to handle the response differently
                url = f"{self.api_base_url}/export/{data_type}"
                response = self.session.get(url, params=params, timeout=self.timeout)
                response.raise_for_status()
                return response.content
            else:
                return self._make_request(f'/export/{data_type}', params)
                
        except RemoteDataError as e:
            logger.error(f"Failed to export {data_type} data: {e}")
            raise e


# Utility functions for backward compatibility
@st.cache_data(ttl=300)
def load_remote_incidents(start_date: str = None, 
                         end_date: str = None,
                         limit: int = 1000) -> pd.DataFrame:
    """Load incidents from remote service (backward compatibility)"""
    client = RemoteTrafficData()
    return client.get_incidents(start_date=start_date, end_date=end_date, limit=limit)

@st.cache_data(ttl=300)
def load_remote_flow_data(start_date: str = None,
                         end_date: str = None,
                         limit: int = 1000) -> pd.DataFrame:
    """Load flow data from remote service (backward compatibility)"""
    client = RemoteTrafficData()
    return client.get_flow_data(start_date=start_date, end_date=end_date, limit=limit)

def check_remote_service() -> Tuple[bool, str]:
    """Check remote service connectivity"""
    client = RemoteTrafficData()
    return client.check_connection()

# Configuration helper for Streamlit apps
def configure_remote_data_source():
    """Configure remote data source in Streamlit sidebar"""
    with st.sidebar:
        st.subheader("🔗 Remote Data Configuration")
        
        # Check connection status
        is_connected, status_msg = check_remote_service()
        
        if is_connected:
            st.success(f"✅ {status_msg}")
            
            # Show service status
            client = RemoteTrafficData()
            status = client.get_service_status()
            
            if 'error' not in status:
                st.metric("Incidents Total", status.get('incidents_total', 0))
                st.metric("Flow Records", status.get('flow_records_total', 0))
                st.metric("API Requests Today", status.get('api_requests_today', 0))
                
                # Show last collection time
                latest = status.get('latest_incident_collection')
                if latest:
                    st.caption(f"Last collection: {latest}")
        else:
            st.error(f"❌ {status_msg}")
            st.info("Check your API configuration in secrets.toml")
    
    return is_connected

# Database fallback for local development
def get_fallback_data() -> pd.DataFrame:
    """Get fallback data when remote service is unavailable"""
    try:
        # Try to load from local CSV as fallback
        csv_path = 'data/traffic_incidents.csv'
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df['date'] = df['timestamp'].dt.date
                df['hour'] = df['timestamp'].dt.hour
            return df
    except Exception as e:
        logger.error(f"Failed to load fallback data: {e}")
    
    return pd.DataFrame()

# Smart data loader that tries remote first, then local fallback
def load_traffic_data(prefer_remote: bool = True, **kwargs) -> pd.DataFrame:
    """
    Smart data loader that tries remote service first, then falls back to local data
    
    Args:
        prefer_remote: Whether to prefer remote data source
        **kwargs: Parameters for data loading
        
    Returns:
        DataFrame with traffic data
    """
    if prefer_remote:
        try:
            client = RemoteTrafficData()
            is_connected, _ = client.check_connection()
            
            if is_connected:
                return client.get_incidents(**kwargs)
        except Exception as e:
            logger.warning(f"Remote data unavailable, falling back to local: {e}")
    
    # Fallback to local data
    return get_fallback_data()