#!/usr/bin/env python3
"""
Origin/Destination Analysis Collector using TomTom O/D Analysis API
Provides trip distribution and movement pattern analysis for municipal planning
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
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TripType(Enum):
    """Types of trips to analyze"""
    ALL_TRIPS = "all"
    COMMUTE = "commute"
    COMMERCIAL = "commercial"
    LEISURE = "leisure"
    EMERGENCY = "emergency"

class TimeCategory(Enum):
    """Time categories for analysis"""
    PEAK_MORNING = "peak_morning"
    PEAK_EVENING = "peak_evening"
    MIDDAY = "midday"
    NIGHT = "night"
    WEEKEND = "weekend"

@dataclass
class OriginDestinationRegion:
    """Custom region definition for O/D analysis"""
    region_id: str
    name: str
    description: str
    geometry: Dict[str, Any]  # GeoJSON geometry
    population: int
    poi_types: List[str]  # Points of interest types
    land_use: str  # residential, commercial, industrial, mixed
    importance: int  # 1-5 scale for analysis priority

@dataclass
class TripMatrix:
    """Origin-destination trip matrix data"""
    timestamp: datetime
    origin_region_id: str
    destination_region_id: str
    origin_name: str
    destination_name: str
    trip_count: int
    average_trip_time: float
    average_distance: float
    trip_type: TripType
    time_category: TimeCategory
    confidence_score: float
    sample_size: int
    date_analyzed: datetime

@dataclass
class FlowPattern:
    """Traffic flow pattern between regions"""
    origin_region: str
    destination_region: str
    dominant_flow_direction: str
    flow_ratio: float  # origin->destination vs destination->origin
    peak_hours: List[int]
    flow_strength: float  # relative to other flows
    seasonal_variation: float
    route_diversity: int  # number of different routes used

@dataclass
class PopularityIndex:
    """POI popularity based on trip destinations"""
    region_id: str
    region_name: str
    poi_type: str
    attraction_score: float  # incoming trips
    generation_score: float  # outgoing trips
    peak_times: List[int]
    visitor_origins: List[str]
    seasonal_patterns: Dict[str, float]

class OriginDestinationCollector:
    """Collects and analyzes origin-destination data using TomTom O/D Analysis API"""
    
    def __init__(self):
        self.api_key = self._get_api_key()
        self.db_path = self._get_db_path()
        self.init_database()
        
        # TomTom O/D Analysis API endpoints
        self.base_url = "https://api.tomtom.com/od-analysis/1"
        self.endpoints = {
            'create_report': f"{self.base_url}/create-report",
            'get_report': f"{self.base_url}/get-report",
            'list_reports': f"{self.base_url}/list-reports"
        }
        
        # Rhode Island regions for O/D analysis
        self.regions = self._initialize_regions()
        
        # Job tracking
        self.active_jobs: Dict[str, Dict[str, Any]] = {}
        
        logger.info("Origin/Destination Collector initialized")
    
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
            logger.warning("No TomTom API key found. O/D analysis will be limited.")
            return ""
        return api_key
    
    def _get_db_path(self) -> str:
        """Get database path for O/D data"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        data_dir = os.path.join(project_root, "data")
        os.makedirs(data_dir, exist_ok=True)
        return os.path.join(data_dir, "origin_destination_data.db")
    
    def init_database(self):
        """Initialize database schema for O/D data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Trip matrix table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trip_matrix (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                origin_region_id TEXT NOT NULL,
                destination_region_id TEXT NOT NULL,
                origin_name TEXT NOT NULL,
                destination_name TEXT NOT NULL,
                trip_count INTEGER,
                average_trip_time REAL,
                average_distance REAL,
                trip_type TEXT,
                time_category TEXT,
                confidence_score REAL,
                sample_size INTEGER,
                date_analyzed DATETIME NOT NULL
            )
        ''')
        
        # Flow patterns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS flow_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                origin_region TEXT NOT NULL,
                destination_region TEXT NOT NULL,
                dominant_flow_direction TEXT,
                flow_ratio REAL,
                peak_hours TEXT,
                flow_strength REAL,
                seasonal_variation REAL,
                route_diversity INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # POI popularity table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS poi_popularity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                region_id TEXT NOT NULL,
                region_name TEXT NOT NULL,
                poi_type TEXT NOT NULL,
                attraction_score REAL,
                generation_score REAL,
                peak_times TEXT,
                visitor_origins TEXT,
                seasonal_patterns TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Regions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_regions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                region_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                geometry TEXT NOT NULL,
                population INTEGER,
                poi_types TEXT,
                land_use TEXT,
                importance INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # O/D analysis jobs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS od_analysis_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT UNIQUE NOT NULL,
                status TEXT NOT NULL,
                created_at DATETIME NOT NULL,
                completed_at DATETIME,
                date_range_start DATETIME,
                date_range_end DATETIME,
                parameters TEXT,
                result_url TEXT,
                error_message TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("O/D analysis database schema initialized")
    
    def _initialize_regions(self) -> List[OriginDestinationRegion]:
        """Initialize analysis regions for Rhode Island"""
        regions = [
            # Major cities
            OriginDestinationRegion(
                region_id="providence_downtown",
                name="Providence Downtown",
                description="Downtown Providence business district",
                geometry={
                    "type": "Polygon",
                    "coordinates": [[
                        [-71.43, 41.81], [-71.40, 41.81], 
                        [-71.40, 41.84], [-71.43, 41.84], 
                        [-71.43, 41.81]
                    ]]
                },
                population=18000,
                poi_types=["business", "government", "entertainment"],
                land_use="commercial",
                importance=5
            ),
            
            OriginDestinationRegion(
                region_id="warwick_airport",
                name="Warwick Airport Area",
                description="T.F. Green Airport and surrounding area",
                geometry={
                    "type": "Polygon",
                    "coordinates": [[
                        [-71.45, 41.69], [-71.40, 41.69], 
                        [-71.40, 41.74], [-71.45, 41.74], 
                        [-71.45, 41.69]
                    ]]
                },
                population=12000,
                poi_types=["airport", "hotels", "business"],
                land_use="mixed",
                importance=4
            ),
            
            OriginDestinationRegion(
                region_id="newport_historic",
                name="Newport Historic District",
                description="Historic Newport tourist area",
                geometry={
                    "type": "Polygon",
                    "coordinates": [[
                        [-71.33, 41.47], [-71.30, 41.47], 
                        [-71.30, 41.52], [-71.33, 41.52], 
                        [-71.33, 41.47]
                    ]]
                },
                population=8000,
                poi_types=["tourism", "historic", "entertainment"],
                land_use="mixed",
                importance=3
            ),
            
            # Residential areas
            OriginDestinationRegion(
                region_id="cranston_residential",
                name="Cranston Residential",
                description="Suburban residential area",
                geometry={
                    "type": "Polygon",
                    "coordinates": [[
                        [-71.50, 41.75], [-71.45, 41.75], 
                        [-71.45, 41.80], [-71.50, 41.80], 
                        [-71.50, 41.75]
                    ]]
                },
                population=35000,
                poi_types=["residential", "retail", "schools"],
                land_use="residential",
                importance=3
            ),
            
            OriginDestinationRegion(
                region_id="pawtucket_industrial",
                name="Pawtucket Industrial",
                description="Industrial and manufacturing area",
                geometry={
                    "type": "Polygon",
                    "coordinates": [[
                        [-71.40, 41.85], [-71.35, 41.85], 
                        [-71.35, 41.90], [-71.40, 41.90], 
                        [-71.40, 41.85]
                    ]]
                },
                population=15000,
                poi_types=["industrial", "manufacturing", "logistics"],
                land_use="industrial",
                importance=2
            ),
            
            # Educational institutions
            OriginDestinationRegion(
                region_id="uri_kingston",
                name="URI Kingston Campus",
                description="University of Rhode Island main campus",
                geometry={
                    "type": "Polygon",
                    "coordinates": [[
                        [-71.54, 41.48], [-71.52, 41.48], 
                        [-71.52, 41.50], [-71.54, 41.50], 
                        [-71.54, 41.48]
                    ]]
                },
                population=16000,
                poi_types=["education", "research", "student_housing"],
                land_use="institutional",
                importance=3
            ),
            
            # Shopping and entertainment
            OriginDestinationRegion(
                region_id="legacy_place",
                name="Legacy Place Shopping",
                description="Major shopping and entertainment center",
                geometry={
                    "type": "Polygon",
                    "coordinates": [[
                        [-71.52, 41.69], [-71.50, 41.69], 
                        [-71.50, 41.71], [-71.52, 41.71], 
                        [-71.52, 41.69]
                    ]]
                },
                population=5000,
                poi_types=["retail", "entertainment", "dining"],
                land_use="commercial",
                importance=2
            ),
            
            # Transportation hubs
            OriginDestinationRegion(
                region_id="providence_station",
                name="Providence Train Station",
                description="Amtrak and commuter rail station",
                geometry={
                    "type": "Polygon",
                    "coordinates": [[
                        [-71.44, 41.82], [-71.43, 41.82], 
                        [-71.43, 41.83], [-71.44, 41.83], 
                        [-71.44, 41.82]
                    ]]
                },
                population=2000,
                poi_types=["transportation", "transit"],
                land_use="transportation",
                importance=4
            ),
            
            # Healthcare facilities
            OriginDestinationRegion(
                region_id="ri_hospital",
                name="Rhode Island Hospital",
                description="Major medical center",
                geometry={
                    "type": "Polygon",
                    "coordinates": [[
                        [-71.42, 41.81], [-71.41, 41.81], 
                        [-71.41, 41.82], [-71.42, 41.82], 
                        [-71.42, 41.81]
                    ]]
                },
                population=8000,
                poi_types=["healthcare", "medical"],
                land_use="institutional",
                importance=4
            ),
            
            # Coastal areas
            OriginDestinationRegion(
                region_id="narragansett_beaches",
                name="Narragansett Beaches",
                description="Coastal recreation area",
                geometry={
                    "type": "Polygon",
                    "coordinates": [[
                        [-71.48, 41.40], [-71.45, 41.40], 
                        [-71.45, 41.45], [-71.48, 41.45], 
                        [-71.48, 41.40]
                    ]]
                },
                population=4000,
                poi_types=["recreation", "tourism", "beaches"],
                land_use="recreational",
                importance=2
            )
        ]
        
        # Save regions to database
        self._save_regions_to_db(regions)
        
        logger.info(f"Initialized {len(regions)} analysis regions")
        return regions
    
    def _save_regions_to_db(self, regions: List[OriginDestinationRegion]):
        """Save region definitions to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            for region in regions:
                cursor.execute('''
                    INSERT OR REPLACE INTO analysis_regions
                    (region_id, name, description, geometry, population, poi_types, land_use, importance)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    region.region_id,
                    region.name,
                    region.description,
                    json.dumps(region.geometry),
                    region.population,
                    json.dumps(region.poi_types),
                    region.land_use,
                    region.importance
                ))
            
            conn.commit()
            logger.info(f"Saved {len(regions)} regions to database")
            
        except Exception as e:
            logger.error(f"Error saving regions to database: {e}")
        finally:
            conn.close()
    
    def submit_od_analysis_job(self, date_range: Tuple[datetime, datetime], 
                              time_sets: List[Dict[str, Any]], 
                              trip_types: List[TripType] = None) -> Optional[str]:
        """Submit O/D analysis job to TomTom API"""
        if not self.api_key:
            logger.error("No API key available for O/D analysis")
            return None
        
        # Prepare regions for API request
        regions = []
        for region in self.regions:
            regions.append({
                "id": region.region_id,
                "name": region.name,
                "geometry": region.geometry
            })
        
        # Default time sets if none provided
        if not time_sets:
            time_sets = [
                {"name": "morning_peak", "startTime": "07:00", "endTime": "09:00"},
                {"name": "evening_peak", "startTime": "17:00", "endTime": "19:00"},
                {"name": "midday", "startTime": "11:00", "endTime": "14:00"}
            ]
        
        # Prepare request payload
        payload = {
            "description": f"O/D Analysis for Rhode Island {date_range[0].strftime('%Y-%m-%d')} to {date_range[1].strftime('%Y-%m-%d')}",
            "regions": regions,
            "dateRanges": [{
                "from": date_range[0].strftime("%Y-%m-%d"),
                "to": date_range[1].strftime("%Y-%m-%d")
            }],
            "timeSets": time_sets,
            "outputFormat": "json"
        }
        
        try:
            response = requests.post(
                self.endpoints['create_report'],
                json=payload,
                params={'key': self.api_key},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                job_id = result.get('reportId')
                
                if job_id:
                    # Track the job
                    self.active_jobs[job_id] = {
                        'status': 'pending',
                        'created_at': datetime.now(),
                        'date_range': date_range,
                        'time_sets': time_sets,
                        'trip_types': trip_types or [TripType.ALL_TRIPS]
                    }
                    
                    # Save to database
                    self._save_job_to_db(job_id, date_range, time_sets)
                    
                    logger.info(f"O/D analysis job submitted: {job_id}")
                    return job_id
                else:
                    logger.error("No job ID returned from O/D analysis request")
                    return None
            else:
                logger.error(f"O/D analysis job failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error submitting O/D analysis job: {e}")
            return None
    
    def check_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Check the status of an O/D analysis job"""
        if not self.api_key:
            return None
        
        try:
            response = requests.get(
                f"{self.endpoints['get_report']}/{job_id}",
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
    
    def download_and_process_results(self, job_id: str) -> bool:
        """Download and process O/D analysis results"""
        status_info = self.check_job_status(job_id)
        
        if not status_info or status_info.get('status') != 'completed':
            logger.warning(f"Job {job_id} not completed")
            return False
        
        result_url = status_info.get('resultUrl')
        if not result_url:
            logger.error(f"No result URL for job {job_id}")
            return False
        
        try:
            # Download results
            response = requests.get(result_url, timeout=60)
            if response.status_code != 200:
                logger.error(f"Failed to download results: {response.status_code}")
                return False
            
            results = response.json()
            
            # Process the results
            trip_matrices = self._process_od_results(results, job_id)
            
            # Save to database
            if trip_matrices:
                self._save_trip_matrices(trip_matrices)
                logger.info(f"Processed {len(trip_matrices)} trip matrices for job {job_id}")
                return True
            else:
                logger.warning(f"No trip matrices processed for job {job_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error processing results for job {job_id}: {e}")
            return False
    
    def _process_od_results(self, results: Dict[str, Any], job_id: str) -> List[TripMatrix]:
        """Process O/D analysis results into trip matrices"""
        trip_matrices = []
        
        try:
            # Extract trip matrices from results
            matrices = results.get('matrices', [])
            
            for matrix in matrices:
                time_set = matrix.get('timeSet', {})
                time_category = self._classify_time_category(time_set)
                
                # Process each origin-destination pair
                for origin_data in matrix.get('origins', []):
                    origin_id = origin_data.get('id')
                    origin_name = origin_data.get('name')
                    
                    for dest_data in origin_data.get('destinations', []):
                        dest_id = dest_data.get('id')
                        dest_name = dest_data.get('name')
                        
                        # Create trip matrix entry
                        trip_matrix = TripMatrix(
                            timestamp=datetime.now(),
                            origin_region_id=origin_id,
                            destination_region_id=dest_id,
                            origin_name=origin_name,
                            destination_name=dest_name,
                            trip_count=dest_data.get('trips', 0),
                            average_trip_time=dest_data.get('averageTravelTime', 0),
                            average_distance=dest_data.get('averageDistance', 0),
                            trip_type=TripType.ALL_TRIPS,
                            time_category=time_category,
                            confidence_score=dest_data.get('confidence', 0.0),
                            sample_size=dest_data.get('sampleSize', 0),
                            date_analyzed=datetime.now()
                        )
                        
                        trip_matrices.append(trip_matrix)
                        
        except Exception as e:
            logger.error(f"Error processing O/D results: {e}")
        
        return trip_matrices
    
    def _classify_time_category(self, time_set: Dict[str, Any]) -> TimeCategory:
        """Classify time category based on time set"""
        start_time = time_set.get('startTime', '00:00')
        
        if start_time in ['07:00', '08:00', '09:00']:
            return TimeCategory.PEAK_MORNING
        elif start_time in ['17:00', '18:00', '19:00']:
            return TimeCategory.PEAK_EVENING
        elif start_time in ['11:00', '12:00', '13:00', '14:00']:
            return TimeCategory.MIDDAY
        else:
            return TimeCategory.NIGHT
    
    def _save_job_to_db(self, job_id: str, date_range: Tuple[datetime, datetime], 
                       time_sets: List[Dict[str, Any]]):
        """Save job information to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO od_analysis_jobs
                (job_id, status, created_at, date_range_start, date_range_end, parameters)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                job_id,
                'pending',
                datetime.now(),
                date_range[0],
                date_range[1],
                json.dumps(time_sets)
            ))
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"Error saving job to database: {e}")
        finally:
            conn.close()
    
    def _save_trip_matrices(self, trip_matrices: List[TripMatrix]):
        """Save trip matrices to database"""
        if not trip_matrices:
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            for matrix in trip_matrices:
                cursor.execute('''
                    INSERT INTO trip_matrix
                    (timestamp, origin_region_id, destination_region_id, origin_name, destination_name,
                     trip_count, average_trip_time, average_distance, trip_type, time_category,
                     confidence_score, sample_size, date_analyzed)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    matrix.timestamp,
                    matrix.origin_region_id,
                    matrix.destination_region_id,
                    matrix.origin_name,
                    matrix.destination_name,
                    matrix.trip_count,
                    matrix.average_trip_time,
                    matrix.average_distance,
                    matrix.trip_type.value,
                    matrix.time_category.value,
                    matrix.confidence_score,
                    matrix.sample_size,
                    matrix.date_analyzed
                ))
            
            conn.commit()
            logger.info(f"Saved {len(trip_matrices)} trip matrices to database")
            
        except Exception as e:
            logger.error(f"Error saving trip matrices: {e}")
        finally:
            conn.close()
    
    def analyze_flow_patterns(self) -> List[FlowPattern]:
        """Analyze flow patterns from trip matrices"""
        conn = sqlite3.connect(self.db_path)
        
        try:
            # Get trip data
            df = pd.read_sql_query('''
                SELECT origin_region_id, destination_region_id, origin_name, destination_name,
                       trip_count, time_category, average_trip_time
                FROM trip_matrix
                WHERE trip_count > 0
            ''', conn)
            
            if df.empty:
                return []
            
            # Group by origin-destination pairs
            flow_patterns = []
            for (origin_id, dest_id), group in df.groupby(['origin_region_id', 'destination_region_id']):
                if origin_id == dest_id:
                    continue  # Skip internal trips
                
                # Calculate bidirectional flow
                reverse_flow = df[
                    (df['origin_region_id'] == dest_id) & 
                    (df['destination_region_id'] == origin_id)
                ]
                
                forward_trips = group['trip_count'].sum()
                reverse_trips = reverse_flow['trip_count'].sum() if not reverse_flow.empty else 0
                
                total_trips = forward_trips + reverse_trips
                if total_trips == 0:
                    continue
                
                # Determine dominant direction
                if forward_trips > reverse_trips:
                    dominant_direction = f"{group.iloc[0]['origin_name']} → {group.iloc[0]['destination_name']}"
                    flow_ratio = forward_trips / total_trips
                else:
                    dominant_direction = f"{group.iloc[0]['destination_name']} → {group.iloc[0]['origin_name']}"
                    flow_ratio = reverse_trips / total_trips
                
                # Find peak hours
                peak_hours = self._find_peak_hours(group)
                
                flow_pattern = FlowPattern(
                    origin_region=group.iloc[0]['origin_name'],
                    destination_region=group.iloc[0]['destination_name'],
                    dominant_flow_direction=dominant_direction,
                    flow_ratio=flow_ratio,
                    peak_hours=peak_hours,
                    flow_strength=total_trips / df['trip_count'].sum(),
                    seasonal_variation=0.0,  # Would need historical data
                    route_diversity=1  # Would need route data
                )
                
                flow_patterns.append(flow_pattern)
            
            # Save flow patterns
            self._save_flow_patterns(flow_patterns)
            
            return flow_patterns
            
        finally:
            conn.close()
    
    def _find_peak_hours(self, group: pd.DataFrame) -> List[int]:
        """Find peak hours from trip data"""
        # This is a simplified version - would need more detailed time data
        peak_categories = group.groupby('time_category')['trip_count'].sum()
        
        peak_hours = []
        if peak_categories.get('peak_morning', 0) > 0:
            peak_hours.extend([7, 8, 9])
        if peak_categories.get('peak_evening', 0) > 0:
            peak_hours.extend([17, 18, 19])
        if peak_categories.get('midday', 0) > 0:
            peak_hours.extend([12, 13])
        
        return sorted(list(set(peak_hours)))
    
    def _save_flow_patterns(self, flow_patterns: List[FlowPattern]):
        """Save flow patterns to database"""
        if not flow_patterns:
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            for pattern in flow_patterns:
                cursor.execute('''
                    INSERT OR REPLACE INTO flow_patterns
                    (origin_region, destination_region, dominant_flow_direction, flow_ratio,
                     peak_hours, flow_strength, seasonal_variation, route_diversity)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    pattern.origin_region,
                    pattern.destination_region,
                    pattern.dominant_flow_direction,
                    pattern.flow_ratio,
                    json.dumps(pattern.peak_hours),
                    pattern.flow_strength,
                    pattern.seasonal_variation,
                    pattern.route_diversity
                ))
            
            conn.commit()
            logger.info(f"Saved {len(flow_patterns)} flow patterns to database")
            
        except Exception as e:
            logger.error(f"Error saving flow patterns: {e}")
        finally:
            conn.close()
    
    def calculate_poi_popularity(self) -> List[PopularityIndex]:
        """Calculate POI popularity based on trip destinations"""
        conn = sqlite3.connect(self.db_path)
        
        try:
            # Get trip data and region info
            df = pd.read_sql_query('''
                SELECT tm.destination_region_id, tm.destination_name, tm.origin_region_id, 
                       tm.origin_name, tm.trip_count, tm.time_category,
                       ar.poi_types, ar.land_use
                FROM trip_matrix tm
                JOIN analysis_regions ar ON tm.destination_region_id = ar.region_id
                WHERE tm.trip_count > 0
            ''', conn)
            
            if df.empty:
                return []
            
            popularity_indices = []
            
            # Group by destination (attraction score)
            for region_id, group in df.groupby('destination_region_id'):
                region_name = group.iloc[0]['destination_name']
                poi_types = json.loads(group.iloc[0]['poi_types'])
                
                # Calculate attraction score (incoming trips)
                attraction_score = group['trip_count'].sum()
                
                # Calculate generation score (outgoing trips)
                outgoing_trips = df[df['origin_region_id'] == region_id]['trip_count'].sum()
                
                # Find peak times
                peak_times = self._find_peak_hours(group)
                
                # Get visitor origins
                visitor_origins = group.groupby('origin_name')['trip_count'].sum().nlargest(5).index.tolist()
                
                for poi_type in poi_types:
                    popularity_index = PopularityIndex(
                        region_id=region_id,
                        region_name=region_name,
                        poi_type=poi_type,
                        attraction_score=attraction_score / len(poi_types),
                        generation_score=outgoing_trips / len(poi_types),
                        peak_times=peak_times,
                        visitor_origins=visitor_origins,
                        seasonal_patterns={}  # Would need historical data
                    )
                    
                    popularity_indices.append(popularity_index)
            
            # Save popularity indices
            self._save_popularity_indices(popularity_indices)
            
            return popularity_indices
            
        finally:
            conn.close()
    
    def _save_popularity_indices(self, popularity_indices: List[PopularityIndex]):
        """Save POI popularity indices to database"""
        if not popularity_indices:
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            for index in popularity_indices:
                cursor.execute('''
                    INSERT OR REPLACE INTO poi_popularity
                    (region_id, region_name, poi_type, attraction_score, generation_score,
                     peak_times, visitor_origins, seasonal_patterns)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    index.region_id,
                    index.region_name,
                    index.poi_type,
                    index.attraction_score,
                    index.generation_score,
                    json.dumps(index.peak_times),
                    json.dumps(index.visitor_origins),
                    json.dumps(index.seasonal_patterns)
                ))
            
            conn.commit()
            logger.info(f"Saved {len(popularity_indices)} popularity indices to database")
            
        except Exception as e:
            logger.error(f"Error saving popularity indices: {e}")
        finally:
            conn.close()
    
    def get_trip_matrix_data(self, origin_region: str = None, 
                           destination_region: str = None,
                           time_category: TimeCategory = None) -> pd.DataFrame:
        """Get trip matrix data from database"""
        conn = sqlite3.connect(self.db_path)
        
        query = "SELECT * FROM trip_matrix WHERE 1=1"
        params = []
        
        if origin_region:
            query += " AND origin_region_id = ?"
            params.append(origin_region)
        
        if destination_region:
            query += " AND destination_region_id = ?"
            params.append(destination_region)
        
        if time_category:
            query += " AND time_category = ?"
            params.append(time_category.value)
        
        query += " ORDER BY trip_count DESC"
        
        try:
            df = pd.read_sql_query(query, conn, params=params)
            return df
        finally:
            conn.close()
    
    def get_flow_patterns_data(self) -> pd.DataFrame:
        """Get flow patterns data from database"""
        conn = sqlite3.connect(self.db_path)
        
        try:
            df = pd.read_sql_query('''
                SELECT * FROM flow_patterns
                ORDER BY flow_strength DESC
            ''', conn)
            return df
        finally:
            conn.close()
    
    def get_poi_popularity_data(self) -> pd.DataFrame:
        """Get POI popularity data from database"""
        conn = sqlite3.connect(self.db_path)
        
        try:
            df = pd.read_sql_query('''
                SELECT * FROM poi_popularity
                ORDER BY attraction_score DESC
            ''', conn)
            return df
        finally:
            conn.close()

# Global collector instance
_od_collector_instance = None

def get_od_collector() -> OriginDestinationCollector:
    """Get singleton O/D collector instance"""
    global _od_collector_instance
    if _od_collector_instance is None:
        _od_collector_instance = OriginDestinationCollector()
    return _od_collector_instance

if __name__ == "__main__":
    # Test the O/D collector
    collector = OriginDestinationCollector()
    print("Origin/Destination Collector initialized")
    print(f"API key configured: {'Yes' if collector.api_key else 'No'}")
    print(f"Regions configured: {len(collector.regions)}")
    
    # Test region data
    for region in collector.regions[:3]:
        print(f"Region: {region.name} - {region.land_use} - Pop: {region.population}")