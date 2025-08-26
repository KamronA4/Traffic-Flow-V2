#!/usr/bin/env python3
"""
Historical Traffic Data Collector using TomTom Traffic Stats API
Provides comprehensive historical traffic analysis for municipal planning
"""

import streamlit as st
import requests
import json
import time
import logging
import sqlite3
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import uuid
import threading
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HistoricalDataType(Enum):
    """Types of historical data available"""
    AREA_ANALYSIS = "area_analysis"
    ROUTE_ANALYSIS = "route_analysis"
    TRAFFIC_DENSITY = "traffic_density"
    SPEED_PROFILE = "speed_profile"
    SEASONAL_ANALYSIS = "seasonal_analysis"

class JobStatus(Enum):
    """Traffic Stats API job statuses"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class HistoricalAnalysisJob:
    """Historical analysis job tracking"""
    job_id: str
    job_type: HistoricalDataType
    status: JobStatus
    created_at: datetime
    completed_at: Optional[datetime]
    zone_name: str
    date_range: Tuple[datetime, datetime]
    parameters: Dict[str, Any]
    result_urls: List[str]
    error_message: Optional[str] = None

@dataclass
class HistoricalTrafficData:
    """Historical traffic data structure"""
    timestamp: datetime
    zone_name: str
    data_type: str
    date_analyzed: datetime
    average_speed: float
    v85_speed: float
    median_speed: float
    travel_time_seconds: int
    delay_seconds: int
    congestion_level: int
    volume_count: int
    confidence_score: float
    weather_impact: Optional[str] = None
    special_events: Optional[str] = None

@dataclass
class SeasonalPattern:
    """Seasonal traffic pattern data"""
    zone_name: str
    month: int
    day_of_week: int
    hour: int
    average_speed: float
    volume_index: float
    congestion_probability: float
    peak_hours: List[int]
    pattern_confidence: float

class HistoricalTrafficCollector:
    """Collects and analyzes historical traffic data using TomTom Traffic Stats API"""
    
    def __init__(self):
        self.api_key = self._get_api_key()
        self.db_path = self._get_db_path()
        self.init_database()
        
        # TomTom Traffic Stats API endpoints
        self.base_url = "https://api.tomtom.com/traffic/services/5"
        self.endpoints = {
            'area_analysis': f"{self.base_url}/areaAnalysis/",
            'route_analysis': f"{self.base_url}/routeAnalysis/",
            'traffic_density': f"{self.base_url}/trafficDensity/",
            'available_maps': f"{self.base_url}/availableMaps",
            'search_jobs': f"{self.base_url}/searchJobs"
        }
        
        # Job tracking
        self.active_jobs: Dict[str, HistoricalAnalysisJob] = {}
        self.job_check_interval = 30  # seconds
        
        logger.info("Historical Traffic Collector initialized")
    
    def _get_api_key(self) -> str:
        """Get TomTom API key from secrets or environment"""
        try:
            # Try Streamlit secrets first
            api_key = st.secrets.get("TOMTOM_API_KEY")
            if api_key and api_key != "your-tomtom-api-key-here":
                return api_key
        except:
            pass
        
        # Fall back to environment variable
        api_key = os.getenv('TOMTOM_API_KEY')
        if not api_key:
            logger.warning("No TomTom API key found. Historical analysis will be limited.")
            return ""
        return api_key
    
    def _get_db_path(self) -> str:
        """Get database path for historical data"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        data_dir = os.path.join(project_root, "data")
        os.makedirs(data_dir, exist_ok=True)
        return os.path.join(data_dir, "historical_traffic_data.db")
    
    def init_database(self):
        """Initialize database schema for historical data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Historical traffic data table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS historical_traffic_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                zone_name TEXT NOT NULL,
                data_type TEXT NOT NULL,
                date_analyzed DATETIME NOT NULL,
                average_speed REAL,
                v85_speed REAL,
                median_speed REAL,
                travel_time_seconds INTEGER,
                delay_seconds INTEGER,
                congestion_level INTEGER,
                volume_count INTEGER,
                confidence_score REAL,
                weather_impact TEXT,
                special_events TEXT
            )
        ''')
        
        # Seasonal patterns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS seasonal_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                zone_name TEXT NOT NULL,
                month INTEGER NOT NULL,
                day_of_week INTEGER NOT NULL,
                hour INTEGER NOT NULL,
                average_speed REAL,
                volume_index REAL,
                congestion_probability REAL,
                peak_hours TEXT,
                pattern_confidence REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Analysis jobs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT UNIQUE NOT NULL,
                job_type TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at DATETIME NOT NULL,
                completed_at DATETIME,
                zone_name TEXT NOT NULL,
                date_range_start DATETIME,
                date_range_end DATETIME,
                parameters TEXT,
                result_urls TEXT,
                error_message TEXT
            )
        ''')
        
        # Speed profiles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS speed_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                zone_name TEXT NOT NULL,
                road_segment TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                speed_limit INTEGER,
                v85_speed REAL,
                average_speed REAL,
                median_speed REAL,
                percentile_speeds TEXT,
                sample_size INTEGER,
                confidence_level REAL
            )
        ''')
        
        # Traffic density data table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS traffic_density (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                zone_name TEXT NOT NULL,
                geometry TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                density_score REAL,
                data_availability REAL,
                coverage_percentage REAL,
                measurement_period TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Historical traffic database schema initialized")
    
    def get_available_maps(self) -> List[Dict[str, Any]]:
        """Get available map versions for historical analysis"""
        if not self.api_key:
            return []
        
        try:
            response = requests.get(
                self.endpoints['available_maps'],
                params={'key': self.api_key},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('availableMaps', [])
            else:
                logger.error(f"Failed to get available maps: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting available maps: {e}")
            return []
    
    def submit_area_analysis_job(self, zone_name: str, bbox: Tuple[float, float, float, float], 
                                date_range: Tuple[datetime, datetime], 
                                time_sets: List[Dict[str, Any]]) -> Optional[str]:
        """Submit area analysis job to TomTom Traffic Stats API"""
        if not self.api_key:
            logger.error("No API key available for area analysis")
            return None
        
        # Prepare request payload
        payload = {
            "description": f"Area analysis for {zone_name}",
            "network": {
                "type": "bbox",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [bbox[1], bbox[0]],  # min_lon, min_lat
                        [bbox[3], bbox[0]],  # max_lon, min_lat
                        [bbox[3], bbox[2]],  # max_lon, max_lat
                        [bbox[1], bbox[2]],  # min_lon, max_lat
                        [bbox[1], bbox[0]]   # close polygon
                    ]]
                }
            },
            "dateRanges": [{
                "from": date_range[0].strftime("%Y-%m-%d"),
                "to": date_range[1].strftime("%Y-%m-%d")
            }],
            "timeSets": time_sets,
            "output": {
                "type": "json",
                "aggregation": "segments"
            }
        }
        
        try:
            response = requests.post(
                self.endpoints['area_analysis'],
                json=payload,
                params={'key': self.api_key},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                job_id = result.get('jobId')
                
                if job_id:
                    # Track the job
                    job = HistoricalAnalysisJob(
                        job_id=job_id,
                        job_type=HistoricalDataType.AREA_ANALYSIS,
                        status=JobStatus.PENDING,
                        created_at=datetime.now(),
                        completed_at=None,
                        zone_name=zone_name,
                        date_range=date_range,
                        parameters={'bbox': bbox, 'time_sets': time_sets},
                        result_urls=[]
                    )
                    
                    self.active_jobs[job_id] = job
                    self.save_job_to_db(job)
                    
                    logger.info(f"Area analysis job submitted: {job_id}")
                    return job_id
                else:
                    logger.error("No job ID returned from area analysis request")
                    return None
            else:
                logger.error(f"Area analysis job failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error submitting area analysis job: {e}")
            return None
    
    def submit_route_analysis_job(self, zone_name: str, routes: List[Dict[str, Any]], 
                                 date_range: Tuple[datetime, datetime],
                                 time_sets: List[Dict[str, Any]]) -> Optional[str]:
        """Submit route analysis job to TomTom Traffic Stats API"""
        if not self.api_key:
            logger.error("No API key available for route analysis")
            return None
        
        # Prepare request payload
        payload = {
            "description": f"Route analysis for {zone_name}",
            "routes": routes,
            "dateRanges": [{
                "from": date_range[0].strftime("%Y-%m-%d"),
                "to": date_range[1].strftime("%Y-%m-%d")
            }],
            "timeSets": time_sets,
            "output": {
                "type": "json"
            }
        }
        
        try:
            response = requests.post(
                self.endpoints['route_analysis'],
                json=payload,
                params={'key': self.api_key},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                job_id = result.get('jobId')
                
                if job_id:
                    # Track the job
                    job = HistoricalAnalysisJob(
                        job_id=job_id,
                        job_type=HistoricalDataType.ROUTE_ANALYSIS,
                        status=JobStatus.PENDING,
                        created_at=datetime.now(),
                        completed_at=None,
                        zone_name=zone_name,
                        date_range=date_range,
                        parameters={'routes': routes, 'time_sets': time_sets},
                        result_urls=[]
                    )
                    
                    self.active_jobs[job_id] = job
                    self.save_job_to_db(job)
                    
                    logger.info(f"Route analysis job submitted: {job_id}")
                    return job_id
                else:
                    logger.error("No job ID returned from route analysis request")
                    return None
            else:
                logger.error(f"Route analysis job failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error submitting route analysis job: {e}")
            return None
    
    def check_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Check the status of a submitted job"""
        if not self.api_key:
            return None
        
        try:
            response = requests.get(
                f"{self.endpoints['area_analysis']}/{job_id}",
                params={'key': self.api_key},
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to check job status: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error checking job status: {e}")
            return None
    
    def download_job_results(self, job_id: str, result_urls: List[str]) -> List[Dict[str, Any]]:
        """Download and parse job results"""
        results = []
        
        for url in result_urls:
            try:
                response = requests.get(url, timeout=60)
                if response.status_code == 200:
                    data = response.json()
                    results.append(data)
                else:
                    logger.error(f"Failed to download result: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"Error downloading result: {e}")
                continue
        
        return results
    
    def process_area_analysis_results(self, job: HistoricalAnalysisJob, results: List[Dict[str, Any]]):
        """Process and save area analysis results"""
        processed_data = []
        
        for result in results:
            try:
                # Parse the area analysis result
                if 'statistics' in result:
                    stats = result['statistics']
                    
                    for segment in stats.get('segments', []):
                        data = HistoricalTrafficData(
                            timestamp=datetime.now(),
                            zone_name=job.zone_name,
                            data_type="area_analysis",
                            date_analyzed=job.date_range[0],
                            average_speed=segment.get('averageSpeed', 0),
                            v85_speed=segment.get('v85Speed', 0),
                            median_speed=segment.get('medianSpeed', 0),
                            travel_time_seconds=segment.get('travelTimeSeconds', 0),
                            delay_seconds=segment.get('delaySeconds', 0),
                            congestion_level=self._calculate_congestion_from_speed(
                                segment.get('averageSpeed', 0)
                            ),
                            volume_count=segment.get('volumeCount', 0),
                            confidence_score=segment.get('confidence', 0.0)
                        )
                        processed_data.append(data)
                        
            except Exception as e:
                logger.error(f"Error processing area analysis result: {e}")
                continue
        
        # Save to database
        if processed_data:
            self.save_historical_data(processed_data)
            logger.info(f"Processed {len(processed_data)} area analysis records")
    
    def process_route_analysis_results(self, job: HistoricalAnalysisJob, results: List[Dict[str, Any]]):
        """Process and save route analysis results"""
        processed_data = []
        
        for result in results:
            try:
                # Parse the route analysis result
                for route in result.get('routes', []):
                    route_stats = route.get('statistics', {})
                    
                    data = HistoricalTrafficData(
                        timestamp=datetime.now(),
                        zone_name=job.zone_name,
                        data_type="route_analysis",
                        date_analyzed=job.date_range[0],
                        average_speed=route_stats.get('averageSpeed', 0),
                        v85_speed=route_stats.get('v85Speed', 0),
                        median_speed=route_stats.get('medianSpeed', 0),
                        travel_time_seconds=route_stats.get('travelTimeSeconds', 0),
                        delay_seconds=route_stats.get('delaySeconds', 0),
                        congestion_level=self._calculate_congestion_from_speed(
                            route_stats.get('averageSpeed', 0)
                        ),
                        volume_count=route_stats.get('volumeCount', 0),
                        confidence_score=route_stats.get('confidence', 0.0)
                    )
                    processed_data.append(data)
                    
            except Exception as e:
                logger.error(f"Error processing route analysis result: {e}")
                continue
        
        # Save to database
        if processed_data:
            self.save_historical_data(processed_data)
            logger.info(f"Processed {len(processed_data)} route analysis records")
    
    def _calculate_congestion_from_speed(self, speed: float) -> int:
        """Calculate congestion level from speed"""
        if speed >= 45:
            return 1  # Free flow
        elif speed >= 35:
            return 2  # Light congestion
        elif speed >= 25:
            return 3  # Moderate congestion
        elif speed >= 15:
            return 4  # Heavy congestion
        else:
            return 5  # Severe congestion
    
    def save_job_to_db(self, job: HistoricalAnalysisJob):
        """Save job information to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO analysis_jobs
                (job_id, job_type, status, created_at, completed_at, zone_name,
                 date_range_start, date_range_end, parameters, result_urls, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                job.job_id,
                job.job_type.value,
                job.status.value,
                job.created_at,
                job.completed_at,
                job.zone_name,
                job.date_range[0],
                job.date_range[1],
                json.dumps(job.parameters),
                json.dumps(job.result_urls),
                job.error_message
            ))
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"Error saving job to database: {e}")
        finally:
            conn.close()
    
    def save_historical_data(self, data: List[HistoricalTrafficData]):
        """Save historical traffic data to database"""
        if not data:
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            for item in data:
                cursor.execute('''
                    INSERT INTO historical_traffic_data
                    (timestamp, zone_name, data_type, date_analyzed, average_speed,
                     v85_speed, median_speed, travel_time_seconds, delay_seconds,
                     congestion_level, volume_count, confidence_score, weather_impact, special_events)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    item.timestamp, item.zone_name, item.data_type, item.date_analyzed,
                    item.average_speed, item.v85_speed, item.median_speed,
                    item.travel_time_seconds, item.delay_seconds, item.congestion_level,
                    item.volume_count, item.confidence_score, item.weather_impact,
                    item.special_events
                ))
            
            conn.commit()
            logger.info(f"Saved {len(data)} historical traffic records")
            
        except Exception as e:
            logger.error(f"Error saving historical data: {e}")
        finally:
            conn.close()
    
    def monitor_jobs(self):
        """Monitor active jobs and process completed ones"""
        jobs_to_remove = []
        
        for job_id, job in self.active_jobs.items():
            if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                continue
            
            status_info = self.check_job_status(job_id)
            if status_info:
                status = status_info.get('status', '').lower()
                
                if status == 'completed':
                    job.status = JobStatus.COMPLETED
                    job.completed_at = datetime.now()
                    job.result_urls = status_info.get('resultUrls', [])
                    
                    # Download and process results
                    results = self.download_job_results(job_id, job.result_urls)
                    
                    if job.job_type == HistoricalDataType.AREA_ANALYSIS:
                        self.process_area_analysis_results(job, results)
                    elif job.job_type == HistoricalDataType.ROUTE_ANALYSIS:
                        self.process_route_analysis_results(job, results)
                    
                    jobs_to_remove.append(job_id)
                    logger.info(f"Job {job_id} completed successfully")
                    
                elif status == 'failed':
                    job.status = JobStatus.FAILED
                    job.error_message = status_info.get('errorMessage', 'Unknown error')
                    jobs_to_remove.append(job_id)
                    logger.error(f"Job {job_id} failed: {job.error_message}")
                    
                elif status == 'cancelled':
                    job.status = JobStatus.CANCELLED
                    jobs_to_remove.append(job_id)
                    logger.warning(f"Job {job_id} was cancelled")
                
                # Update job in database
                self.save_job_to_db(job)
        
        # Remove completed/failed jobs from active tracking
        for job_id in jobs_to_remove:
            del self.active_jobs[job_id]
    
    def start_job_monitoring(self):
        """Start background job monitoring"""
        def monitor_loop():
            while True:
                try:
                    self.monitor_jobs()
                    time.sleep(self.job_check_interval)
                except Exception as e:
                    logger.error(f"Error in job monitoring: {e}")
                    time.sleep(60)  # Wait longer on error
        
        monitor_thread = threading.Thread(target=monitor_loop)
        monitor_thread.daemon = True
        monitor_thread.start()
        logger.info("Job monitoring started")
    
    def get_historical_data(self, zone_name: str = None, 
                          date_range: Optional[Tuple[datetime, datetime]] = None,
                          data_type: str = None) -> pd.DataFrame:
        """Get historical traffic data from database"""
        conn = sqlite3.connect(self.db_path)
        
        query = "SELECT * FROM historical_traffic_data WHERE 1=1"
        params = []
        
        if zone_name:
            query += " AND zone_name = ?"
            params.append(zone_name)
        
        if date_range:
            query += " AND date_analyzed BETWEEN ? AND ?"
            params.extend(date_range)
        
        if data_type:
            query += " AND data_type = ?"
            params.append(data_type)
        
        query += " ORDER BY date_analyzed DESC"
        
        try:
            df = pd.read_sql_query(query, conn, params=params)
            return df
        finally:
            conn.close()
    
    def get_job_history(self) -> pd.DataFrame:
        """Get analysis job history"""
        conn = sqlite3.connect(self.db_path)
        
        try:
            df = pd.read_sql_query('''
                SELECT job_id, job_type, status, created_at, completed_at, zone_name,
                       date_range_start, date_range_end, error_message
                FROM analysis_jobs
                ORDER BY created_at DESC
            ''', conn)
            return df
        finally:
            conn.close()
    
    def analyze_seasonal_patterns(self, zone_name: str) -> List[SeasonalPattern]:
        """Analyze seasonal traffic patterns from historical data"""
        conn = sqlite3.connect(self.db_path)
        
        try:
            # Get historical data for the zone
            df = pd.read_sql_query('''
                SELECT date_analyzed, average_speed, volume_count, congestion_level
                FROM historical_traffic_data
                WHERE zone_name = ?
                ORDER BY date_analyzed
            ''', conn, params=[zone_name])
            
            if df.empty:
                return []
            
            # Convert to datetime
            df['date_analyzed'] = pd.to_datetime(df['date_analyzed'])
            df['month'] = df['date_analyzed'].dt.month
            df['day_of_week'] = df['date_analyzed'].dt.dayofweek
            df['hour'] = df['date_analyzed'].dt.hour
            
            # Group by month, day of week, and hour
            patterns = []
            for (month, day_of_week, hour), group in df.groupby(['month', 'day_of_week', 'hour']):
                pattern = SeasonalPattern(
                    zone_name=zone_name,
                    month=month,
                    day_of_week=day_of_week,
                    hour=hour,
                    average_speed=group['average_speed'].mean(),
                    volume_index=group['volume_count'].mean() / df['volume_count'].mean(),
                    congestion_probability=len(group[group['congestion_level'] >= 3]) / len(group),
                    peak_hours=df.groupby('hour')['congestion_level'].mean().nlargest(3).index.tolist(),
                    pattern_confidence=min(len(group) / 10, 1.0)  # Confidence based on sample size
                )
                patterns.append(pattern)
            
            return patterns
            
        finally:
            conn.close()

# Global collector instance
_historical_collector_instance = None

def get_historical_collector() -> HistoricalTrafficCollector:
    """Get singleton historical collector instance"""
    global _historical_collector_instance
    if _historical_collector_instance is None:
        _historical_collector_instance = HistoricalTrafficCollector()
    return _historical_collector_instance

if __name__ == "__main__":
    # Test the historical collector
    collector = HistoricalTrafficCollector()
    print("Historical Traffic Collector initialized")
    print(f"API key configured: {'Yes' if collector.api_key else 'No'}")
    
    # Test available maps
    maps = collector.get_available_maps()
    print(f"Available maps: {len(maps)}")
    
    # Show job history
    jobs = collector.get_job_history()
    print(f"Job history: {len(jobs)} jobs")