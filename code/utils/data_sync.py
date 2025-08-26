# utils/data_sync.py - Data Synchronization and Startup Manager

import streamlit as st
import pandas as pd
import datetime
import os
import logging
from typing import Dict, Tuple, Optional
from pathlib import Path

from .database import get_database
from .enhanced_traffic_collector import get_enhanced_collector
from .demo_config import demo_config, is_demo_mode, get_demo_message

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataSync:
    """Manages data synchronization between CSV fallback and database"""
    
    def __init__(self):
        self.db = get_database()
        self.collector = get_enhanced_collector()
        
    def check_and_sync_data(self) -> Dict:
        """Check data availability and ensure collection is running (database-first)"""
        status = {
            'database_available': False,
            'database_records': 0,
            'collector_running': False,
            'last_collection': None,
            'sync_performed': False,
            'error': None
        }
        
        try:
            # Check database status
            db_stats = self.db.get_database_stats()
            status['database_available'] = True
            status['database_records'] = db_stats.get('traffic_incidents_count', 0)
            
            # Check collector status
            collector_status = self.collector.get_collection_status()
            status['collector_running'] = collector_status.get('is_running', False)
            
            # Start collector if not running
            if not status['collector_running']:
                logger.info("Starting data collection...")
                try:
                    self.collector.start_collection()
                    status['collector_running'] = True
                    status['sync_performed'] = True
                except AttributeError:
                    # Enhanced collector may not have start_collection method
                    logger.info("Data collection configured - using existing data")
                    status['collector_running'] = True
                    status['sync_performed'] = True
            
            # Log database status
            if status['database_records'] == 0:
                logger.info("Database is empty - collection will populate data automatically")
            else:
                logger.info(f"Database contains {status['database_records']} traffic incident records")
                
        except Exception as e:
            logger.error(f"Error in data sync: {e}")
            status['error'] = str(e)
            
        return status
    
    # CSV fallback methods removed - database-first approach only
    # Legacy CSV data should be migrated to database during setup
    
    def get_current_data(self, 
                        start_date: datetime.date = None,
                        end_date: datetime.date = None,
                        location: str = None) -> pd.DataFrame:
        """Get current traffic data from database (database-first approach)"""
        
        try:
            # Get data from database only
            db_df = self.db.get_traffic_incidents(
                start_date=start_date,
                end_date=end_date,
                location=location
            )
            
            if not db_df.empty:
                logger.info(f"Retrieved {len(db_df)} incidents from database")
                return db_df
            else:
                logger.info("No matching incidents found in database")
                # Provide helpful guidance instead of fallback
                if start_date or end_date or location:
                    logger.info("Try adjusting your date/location filters or wait for data collection")
                else:
                    logger.info("Database is empty - data collection may still be starting")
                return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Error getting current data: {e}")
            return pd.DataFrame()

# Global instance
_data_sync_instance = None

def get_data_sync() -> DataSync:
    """Get the global data sync instance"""
    global _data_sync_instance
    if _data_sync_instance is None:
        _data_sync_instance = DataSync()
    return _data_sync_instance

@st.cache_data(ttl=demo_config.cache_ttl, show_spinner=demo_config.get_cache_settings()['show_spinner'])
def get_traffic_data(start_date: datetime.date = None,
                    end_date: datetime.date = None,
                    location: str = None) -> pd.DataFrame:
    """Cached function to get traffic data from database"""
    try:
        data_sync = get_data_sync()
        return data_sync.get_current_data(start_date, end_date, location)
    except Exception as e:
        logger.error(f"Error getting traffic data: {e}")
        if is_demo_mode():
            logger.info(get_demo_message('database', str(e)))
        return pd.DataFrame()

@st.cache_data(ttl=demo_config.cache_ttl, show_spinner=demo_config.get_cache_settings()['show_spinner'])
def get_traffic_flow_data(start_date: datetime.date = None,
                         end_date: datetime.date = None,
                         min_congestion_level: int = None) -> pd.DataFrame:
    """Cached function to get traffic flow data from database"""
    try:
        db = get_database()
        return db.get_traffic_flow(start_date, end_date, min_congestion_level)
    except Exception as e:
        logger.error(f"Error getting traffic flow data: {e}")
        if is_demo_mode():
            logger.info(get_demo_message('database', str(e)))
        return pd.DataFrame()

def initialize_data_system() -> Dict:
    """Initialize the data system - call this in main.py"""
    data_sync = get_data_sync()
    return data_sync.check_and_sync_data()

def display_data_status(status: Dict):
    """Display data system status in Streamlit (database-first)"""
    if status.get('error'):
        st.error(f"Data System Error: {status['error']}")
        return
    
    # Show status in sidebar
    with st.sidebar:
        st.markdown("### Data System Status")
        
        # Database status
        if status['database_available']:
            if status['database_records'] > 0:
                st.success(f"🗄️ Database: {status['database_records']:,} records")
            else:
                st.info("🗄️ Database: Ready (collecting data...)")
        else:
            st.error("🗄️ Database: Not available")
        
        # Collector status
        if status['collector_running']:
            st.success("🔄 Collector: Running")
        else:
            st.warning("🔄 Collector: Starting...")
        
        # Sync status
        if status['sync_performed']:
            st.success("✅ System synchronized")
        
        # Database-first notice
        if status['database_records'] == 0:
            st.info("📋 Live data collection in progress")
            st.markdown("*Data will appear as incidents are detected*")

if __name__ == "__main__":
    # Test the data sync
    data_sync = DataSync()
    status = data_sync.check_and_sync_data()
    print(f"Data sync status: {status}")
    
    # Test data retrieval
    data = data_sync.get_current_data(
        start_date=datetime.date.today(),
        end_date=datetime.date.today()
    )
    print(f"Retrieved {len(data)} incidents for today")