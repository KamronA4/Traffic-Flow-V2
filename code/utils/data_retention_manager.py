#!/usr/bin/env python3
"""
Data Retention Manager for Building Historical Traffic Dataset
Manages long-term storage and analysis of real-time collected incident data
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataRetentionManager:
    """Manages historical data retention and analysis for Village Platform"""
    
    def __init__(self, db_path: str = "data/traffic_data.db"):
        self.db_path = db_path
        self.retention_days = 365  # Keep data for 1 year
        
    def get_historical_summary(self) -> Dict:
        """Get summary of historical data collection progress"""
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get real API data statistics
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_incidents,
                        MIN(date(timestamp)) as first_incident,
                        MAX(date(timestamp)) as latest_incident,
                        COUNT(DISTINCT date(timestamp)) as unique_days
                    FROM traffic_incidents 
                    WHERE data_source = 'tomtom_api'
                """)
                
                result = cursor.fetchone()
                
                if result and result[0] > 0:
                    total_incidents, first_date, latest_date, unique_days = result
                    
                    # Calculate collection progress
                    if first_date and latest_date:
                        first_dt = datetime.strptime(first_date, '%Y-%m-%d')
                        latest_dt = datetime.strptime(latest_date, '%Y-%m-%d')
                        days_elapsed = (latest_dt - first_dt).days + 1
                        collection_rate = (unique_days / days_elapsed) * 100 if days_elapsed > 0 else 0
                    else:
                        days_elapsed = 0
                        collection_rate = 0
                    
                    # Get incident distribution by severity
                    cursor.execute("""
                        SELECT severity, COUNT(*) as count
                        FROM traffic_incidents 
                        WHERE data_source = 'tomtom_api'
                        GROUP BY severity
                        ORDER BY severity
                    """)
                    severity_dist = dict(cursor.fetchall())
                    
                    # Get top locations
                    cursor.execute("""
                        SELECT location, COUNT(*) as count
                        FROM traffic_incidents 
                        WHERE data_source = 'tomtom_api'
                        GROUP BY location
                        ORDER BY count DESC
                        LIMIT 5
                    """)
                    top_locations = cursor.fetchall()
                    
                    return {
                        'total_incidents': total_incidents,
                        'first_incident_date': first_date,
                        'latest_incident_date': latest_date,
                        'unique_collection_days': unique_days,
                        'days_elapsed': days_elapsed,
                        'collection_rate_percent': round(collection_rate, 1),
                        'daily_average': round(total_incidents / max(unique_days, 1), 1),
                        'severity_distribution': severity_dist,
                        'top_locations': top_locations,
                        'data_quality': 'Real API Data' if total_incidents > 0 else 'No Data Yet'
                    }
                else:
                    return {
                        'total_incidents': 0,
                        'message': 'No historical data available yet - collection starting',
                        'expected_timeline': 'First incidents should appear within 15-30 minutes',
                        'data_quality': 'Waiting for Real API Data'
                    }
                    
        except Exception as e:
            logger.error(f"Error getting historical summary: {e}")
            return {'error': str(e)}
    
    def cleanup_old_data(self, days_to_keep: int = None) -> Dict:
        """Clean up data older than retention period"""
        
        if days_to_keep is None:
            days_to_keep = self.retention_days
            
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Count records to be deleted
                cursor.execute("""
                    SELECT COUNT(*) FROM traffic_incidents 
                    WHERE timestamp < ? AND data_source = 'tomtom_api'
                """, (cutoff_date,))
                
                records_to_delete = cursor.fetchone()[0]
                
                if records_to_delete > 0:
                    # Archive old data before deletion (optional)
                    self._archive_old_data(cursor, cutoff_date)
                    
                    # Delete old records
                    cursor.execute("""
                        DELETE FROM traffic_incidents 
                        WHERE timestamp < ? AND data_source = 'tomtom_api'
                    """, (cutoff_date,))
                    
                    conn.commit()
                    
                    logger.info(f"Cleaned up {records_to_delete} old incident records")
                    
                    return {
                        'records_deleted': records_to_delete,
                        'cutoff_date': cutoff_date.strftime('%Y-%m-%d'),
                        'retention_days': days_to_keep
                    }
                else:
                    return {
                        'records_deleted': 0,
                        'message': 'No old records to clean up'
                    }
                    
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            return {'error': str(e)}
    
    def _archive_old_data(self, cursor, cutoff_date):
        """Archive old data to JSON file before deletion"""
        
        try:
            # Get old records
            cursor.execute("""
                SELECT * FROM traffic_incidents 
                WHERE timestamp < ? AND data_source = 'tomtom_api'
            """, (cutoff_date,))
            
            old_records = cursor.fetchall()
            
            if old_records:
                # Get column names
                cursor.execute("PRAGMA table_info(traffic_incidents)")
                columns = [col[1] for col in cursor.fetchall()]
                
                # Convert to list of dicts
                archive_data = []
                for record in old_records:
                    archive_data.append(dict(zip(columns, record)))
                
                # Save to archive file
                archive_file = f"data/archived_incidents_{cutoff_date.strftime('%Y%m%d')}.json"
                with open(archive_file, 'w') as f:
                    json.dump(archive_data, f, indent=2, default=str)
                
                logger.info(f"Archived {len(old_records)} records to {archive_file}")
                
        except Exception as e:
            logger.warning(f"Error archiving old data: {e}")
    
    def get_collection_timeline_projection(self) -> Dict:
        """Project when meaningful historical data will be available"""
        
        summary = self.get_historical_summary()
        
        if 'total_incidents' not in summary or summary['total_incidents'] == 0:
            return {
                'current_status': 'Starting collection',
                'projections': {
                    '1_week': 'Basic patterns visible',
                    '1_month': 'Reliable trend analysis',
                    '3_months': 'Seasonal pattern detection',
                    '6_months': 'Comprehensive historical analysis',
                    '1_year': 'Full annual traffic cycle data'
                },
                'recommendation': 'Continue real-time collection - historical value builds over time'
            }
        else:
            days_collected = summary.get('unique_collection_days', 0)
            
            projections = {}
            
            if days_collected < 7:
                projections['current_status'] = f"Early collection phase ({days_collected} days)"
                projections['next_milestone'] = "1 week for basic patterns"
            elif days_collected < 30:
                projections['current_status'] = f"Building baseline ({days_collected} days)"
                projections['next_milestone'] = "1 month for trend analysis"
            elif days_collected < 90:
                projections['current_status'] = f"Establishing patterns ({days_collected} days)"
                projections['next_milestone'] = "3 months for seasonal insights"
            else:
                projections['current_status'] = f"Mature dataset ({days_collected} days)"
                projections['analysis_ready'] = "Historical analysis fully available"
            
            return projections

def get_retention_manager() -> DataRetentionManager:
    """Get singleton instance of retention manager"""
    return DataRetentionManager()

if __name__ == "__main__":
    # Test the retention manager
    manager = DataRetentionManager()
    summary = manager.get_historical_summary()
    print("Historical Data Summary:")
    print(json.dumps(summary, indent=2))