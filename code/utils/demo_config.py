# utils/demo_config.py - Demo mode configuration and utilities

import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class DemoConfig:
    """Configuration class for demo mode settings"""
    
    def __init__(self):
        # Core demo settings
        self.enabled = os.getenv('VILLAGE_DEMO_MODE', 'false').lower() == 'true'
        self.session_timeout = int(os.getenv('DEMO_SESSION_TIMEOUT', '3600'))  # 1 hour
        
        # Database settings
        self.db_timeout = float(os.getenv('DEMO_DB_TIMEOUT', '10.0'))
        self.use_fallback_data = os.getenv('DEMO_USE_FALLBACK', 'true').lower() == 'true'
        
        # Cache settings
        self.cache_ttl = int(os.getenv('DEMO_CACHE_TTL', '300'))  # 5 minutes for demos
        self.cache_warming = os.getenv('DEMO_CACHE_WARMING', 'true').lower() == 'true'
        
        # Collection settings
        self.collection_interval = int(os.getenv('DEMO_COLLECTION_INTERVAL', '300'))  # 5 minutes
        self.max_api_requests = int(os.getenv('DEMO_MAX_API_REQUESTS', '10'))
        
        # UI settings
        self.show_loading_messages = os.getenv('DEMO_SHOW_LOADING', 'true').lower() == 'true'
        self.sanitize_errors = os.getenv('DEMO_SANITIZE_ERRORS', 'true').lower() == 'true'
        self.auto_refresh_disabled = os.getenv('DEMO_DISABLE_AUTO_REFRESH', 'true').lower() == 'true'
        
        # Authentication settings (secure)
        self.demo_username = self._get_secure_setting('VILLAGE_DEMO_USERNAME', 'demo@ridot.ri.gov')
        self.demo_password = self._get_secure_setting('RIDOT_DEMO_PASSWORD', None)  # Force secure password
        
        # Log configuration status
        if self.enabled:
            logger.info("Demo mode is ENABLED")
            logger.info(f"Cache TTL: {self.cache_ttl}s, Collection interval: {self.collection_interval}s")
        else:
            logger.info("Demo mode is DISABLED - running in production mode")
    
    def _get_secure_setting(self, env_var: str, fallback: str) -> str:
        """Get setting from secure sources with fallback"""
        # Try Streamlit secrets first
        try:
            import streamlit as st
            value = st.secrets.get(env_var)
            if value:
                return value
        except:
            pass
        
        # Try environment variable
        value = os.getenv(env_var)
        if value:
            return value
        
        # Use fallback only in demo mode, or fail securely
        if self.enabled and fallback is not None:
            logger.warning(f"Using fallback value for {env_var} in demo mode")
            return fallback
        elif fallback is None:
            # For critical secrets like passwords, fail without fallback
            raise ValueError(
                f"{env_var} must be set in secrets.toml or environment variables. "
                "No fallback available for security reasons."
            )
        else:
            # For non-critical settings, use fallback with warning
            logger.warning(f"Using fallback value for {env_var} in production mode")
            return fallback
    
    def get_error_message(self, error_type: str, technical_message: str = "") -> str:
        """Get user-friendly error messages for demo audiences"""
        if not self.sanitize_errors:
            return technical_message
        
        demo_messages = {
            'database': 'The system is processing data. This will complete momentarily.',
            'api': 'Connecting to live traffic feeds. Please wait a moment.',
            'analysis': 'Traffic analysis is processing. Results will appear shortly.',
            'map': 'Map view is refreshing. Data remains available in the table below.',
            'auth': 'Please verify your credentials and try again.',
            'collection': 'Data collection is optimizing. Normal service will resume shortly.',
            'cache': 'System is updating. Please wait a moment.',
            'import': 'System components are loading. This process will complete shortly.'
        }
        
        return demo_messages.get(error_type, 'The system is updating. Please wait a moment.')
    
    def get_collection_settings(self) -> Dict[str, Any]:
        """Get collection settings appropriate for demo mode"""
        if self.enabled:
            return {
                'interval_seconds': self.collection_interval,
                'max_requests_per_minute': self.max_api_requests,
                'use_cached_data': True,
                'timeout': self.db_timeout,
                'retry_attempts': 1  # Fewer retries during demos
            }
        else:
            return {
                'interval_seconds': 30,  # Normal operation
                'max_requests_per_minute': 50,
                'use_cached_data': False,
                'timeout': 30.0,
                'retry_attempts': 3
            }
    
    def get_cache_settings(self) -> Dict[str, Any]:
        """Get cache settings appropriate for demo mode"""
        return {
            'ttl': self.cache_ttl,
            'warm_on_start': self.cache_warming,
            'show_spinner': not self.enabled  # Hide spinners during demos
        }

# Global demo configuration instance
demo_config = DemoConfig()

def is_demo_mode() -> bool:
    """Check if application is running in demo mode"""
    return demo_config.enabled

def get_demo_message(error_type: str, technical_msg: str = "") -> str:
    """Get appropriate error message for current mode"""
    return demo_config.get_error_message(error_type, technical_msg)

def get_demo_cache_ttl() -> int:
    """Get appropriate cache TTL for current mode"""
    return demo_config.cache_ttl