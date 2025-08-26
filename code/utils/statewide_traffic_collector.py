#!/usr/bin/env python3
"""
Statewide Traffic Data Collection System for Village Platform
Comprehensive Rhode Island coverage with priority-based sampling
"""

import streamlit as st
import requests
import json
import time
import logging
import sqlite3
import os
import random
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import threading
import math
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SamplingStrategy(Enum):
    """Sampling strategies for data collection"""
    UNIFORM_GRID = "uniform_grid"
    POPULATION_WEIGHTED = "population_weighted"
    ROAD_NETWORK_BASED = "road_network_based"
    ADAPTIVE_DENSITY = "adaptive_density"
    PRIORITY_ZONES = "priority_zones"

class CoverageLevel(Enum):
    """Coverage levels for different areas"""
    INTENSIVE = 1    # Every 0.5 miles
    STANDARD = 2     # Every 1 mile
    BASIC = 3        # Every 2 miles
    SPARSE = 4       # Every 5 miles

@dataclass
class SamplingPoint:
    """Individual sampling point for data collection"""
    id: str
    latitude: float
    longitude: float
    coverage_level: CoverageLevel
    priority: int
    road_type: str
    population_density: float
    last_sampled: Optional[datetime] = None
    success_rate: float = 1.0
    data_quality: float = 1.0

@dataclass
class GeographicRegion:
    """Geographic region with specific sampling parameters"""
    name: str
    bbox: Tuple[float, float, float, float]  # (min_lat, min_lon, max_lat, max_lon)
    coverage_level: CoverageLevel
    sampling_strategy: SamplingStrategy
    priority_multiplier: float
    population_density: float
    road_density: float
    special_considerations: List[str]

class StatewideTrafficCollector:
    """Comprehensive statewide traffic data collection system"""
    
    def __init__(self):
        self.api_key = self._get_api_key()
        self.db_path = self._get_db_path()
        self.init_database()
        
        # Rhode Island bounds
        self.ri_bounds = (41.146, -71.862, 42.018, -71.120)  # (min_lat, min_lon, max_lat, max_lon)
        
        # Initialize geographic regions
        self.geographic_regions = self._initialize_geographic_regions()
        
        # Generate comprehensive sampling points
        self.sampling_points = self._generate_sampling_points()
        
        # Collection parameters
        self.daily_quota = 50000
        self.requests_today = 0
        self.last_quota_reset = datetime.now().date()
        
        # TomTom API base URLs
        self.api_base_urls = {
            'incidents': 'https://api.tomtom.com/traffic/services/5/incidentDetails',
            'flow': 'https://api.tomtom.com/traffic/services/4/flowSegmentData',
            'route': 'https://api.tomtom.com/routing/1/calculateRoute'
        }
        
        logger.info(f"Statewide Traffic Collector initialized with {len(self.sampling_points)} sampling points")
    
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
            logger.warning("No TomTom API key found. Statewide collection will be limited.")
            return ""
        return api_key
    
    def _get_db_path(self) -> str:
        """Get database path"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        data_dir = os.path.join(project_root, "data")
        os.makedirs(data_dir, exist_ok=True)
        return os.path.join(data_dir, "statewide_traffic_data.db")
    
    def init_database(self):
        """Initialize database schema for statewide collection"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Sampling points table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sampling_points (
                id TEXT PRIMARY KEY,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                coverage_level INTEGER NOT NULL,
                priority INTEGER NOT NULL,
                road_type TEXT,
                population_density REAL,
                last_sampled DATETIME,
                success_rate REAL DEFAULT 1.0,
                data_quality REAL DEFAULT 1.0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Statewide traffic data table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS statewide_traffic_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sampling_point_id TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                current_speed REAL,
                free_flow_speed REAL,
                current_travel_time INTEGER,
                free_flow_travel_time INTEGER,
                confidence REAL,
                road_closure BOOLEAN,
                congestion_level INTEGER,
                road_type TEXT,
                coverage_level INTEGER,
                data_quality REAL,
                FOREIGN KEY (sampling_point_id) REFERENCES sampling_points (id)
            )
        ''')
        
        # Geographic regions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS geographic_regions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                bbox TEXT NOT NULL,
                coverage_level INTEGER NOT NULL,
                sampling_strategy TEXT NOT NULL,
                priority_multiplier REAL,
                population_density REAL,
                road_density REAL,
                special_considerations TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Collection statistics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS statewide_collection_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                region_name TEXT NOT NULL,
                points_sampled INTEGER,
                successful_samples INTEGER,
                api_requests_used INTEGER,
                coverage_percentage REAL,
                average_data_quality REAL,
                collection_duration REAL
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Statewide database schema initialized")
    
    def _initialize_geographic_regions(self) -> List[GeographicRegion]:
        """Initialize comprehensive geographic regions covering all of Rhode Island"""
        regions = [
            # Metropolitan Providence Area - Intensive Coverage
            GeographicRegion(
                name="Providence_Metropolitan",
                bbox=(41.700, -71.500, 41.900, -71.350),
                coverage_level=CoverageLevel.INTENSIVE,
                sampling_strategy=SamplingStrategy.ROAD_NETWORK_BASED,
                priority_multiplier=1.0,
                population_density=2800,  # people per sq mile
                road_density=8.5,  # miles per sq mile
                special_considerations=["urban_core", "transit_hub", "business_district"]
            ),
            
            # Northern Rhode Island - Standard Coverage
            GeographicRegion(
                name="Northern_RI",
                bbox=(41.850, -71.700, 42.018, -71.350),
                coverage_level=CoverageLevel.STANDARD,
                sampling_strategy=SamplingStrategy.POPULATION_WEIGHTED,
                priority_multiplier=0.8,
                population_density=1200,
                road_density=6.2,
                special_considerations=["suburban", "commuter_routes"]
            ),
            
            # Southern Rhode Island - Standard Coverage
            GeographicRegion(
                name="Southern_RI",
                bbox=(41.146, -71.600, 41.500, -71.250),
                coverage_level=CoverageLevel.STANDARD,
                sampling_strategy=SamplingStrategy.POPULATION_WEIGHTED,
                priority_multiplier=0.7,
                population_density=800,
                road_density=5.8,
                special_considerations=["coastal", "tourism", "seasonal_variation"]
            ),
            
            # Western Rhode Island - Basic Coverage
            GeographicRegion(
                name="Western_RI",
                bbox=(41.400, -71.862, 41.950, -71.650),
                coverage_level=CoverageLevel.BASIC,
                sampling_strategy=SamplingStrategy.UNIFORM_GRID,
                priority_multiplier=0.6,
                population_density=400,
                road_density=4.2,
                special_considerations=["rural", "agricultural", "forest"]
            ),
            
            # Eastern Rhode Island - Standard Coverage
            GeographicRegion(
                name="Eastern_RI",
                bbox=(41.300, -71.350, 41.700, -71.120),
                coverage_level=CoverageLevel.STANDARD,
                sampling_strategy=SamplingStrategy.POPULATION_WEIGHTED,
                priority_multiplier=0.8,
                population_density=1500,
                road_density=6.8,
                special_considerations=["coastal", "ports", "industrial"]
            ),
            
            # Newport County - Intensive Coverage (Tourism)
            GeographicRegion(
                name="Newport_County",
                bbox=(41.400, -71.400, 41.600, -71.200),
                coverage_level=CoverageLevel.INTENSIVE,
                sampling_strategy=SamplingStrategy.ADAPTIVE_DENSITY,
                priority_multiplier=0.9,
                population_density=1800,
                road_density=7.2,
                special_considerations=["tourism", "historic", "seasonal_peaks", "events"]
            ),
            
            # Major Highway Corridors - Intensive Coverage
            GeographicRegion(
                name="Highway_Corridors",
                bbox=(41.146, -71.862, 42.018, -71.120),  # Full state
                coverage_level=CoverageLevel.INTENSIVE,
                sampling_strategy=SamplingStrategy.ROAD_NETWORK_BASED,
                priority_multiplier=1.2,
                population_density=0,  # Not applicable
                road_density=15.0,  # Highway density
                special_considerations=["interstate", "major_routes", "truck_traffic", "commuter_flow"]
            ),
            
            # Border Areas - Basic Coverage
            GeographicRegion(
                name="Border_Areas",
                bbox=(41.146, -71.862, 42.018, -71.120),  # Full state
                coverage_level=CoverageLevel.BASIC,
                sampling_strategy=SamplingStrategy.UNIFORM_GRID,
                priority_multiplier=0.5,
                population_density=300,
                road_density=3.5,
                special_considerations=["border_crossings", "interstate_commerce"]
            ),
            
            # Special Event Areas - Adaptive Coverage
            GeographicRegion(
                name="Special_Events",
                bbox=(41.146, -71.862, 42.018, -71.120),  # Full state
                coverage_level=CoverageLevel.STANDARD,
                sampling_strategy=SamplingStrategy.ADAPTIVE_DENSITY,
                priority_multiplier=0.8,
                population_density=0,  # Variable
                road_density=0,  # Variable
                special_considerations=["sports_venues", "concerts", "festivals", "universities"]
            )
        ]
        
        # Save regions to database
        self._save_regions_to_db(regions)
        
        logger.info(f"Initialized {len(regions)} geographic regions")
        return regions
    
    def _save_regions_to_db(self, regions: List[GeographicRegion]):
        """Save geographic regions to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            for region in regions:
                cursor.execute('''
                    INSERT OR REPLACE INTO geographic_regions
                    (name, bbox, coverage_level, sampling_strategy, priority_multiplier,
                     population_density, road_density, special_considerations)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    region.name,
                    json.dumps(region.bbox),
                    region.coverage_level.value,
                    region.sampling_strategy.value,
                    region.priority_multiplier,
                    region.population_density,
                    region.road_density,
                    json.dumps(region.special_considerations)
                ))
            
            conn.commit()
            logger.info(f"Saved {len(regions)} regions to database")
            
        except Exception as e:
            logger.error(f"Error saving regions to database: {e}")
        finally:
            conn.close()
    
    def _generate_sampling_points(self) -> List[SamplingPoint]:
        """Generate comprehensive sampling points across Rhode Island"""
        all_points = []
        
        for region in self.geographic_regions:
            region_points = self._generate_points_for_region(region)
            all_points.extend(region_points)
        
        # Remove duplicates (points within 0.001 degrees of each other)
        unique_points = self._remove_duplicate_points(all_points)
        
        # Save to database
        self._save_sampling_points_to_db(unique_points)
        
        logger.info(f"Generated {len(unique_points)} unique sampling points")
        return unique_points
    
    def _generate_points_for_region(self, region: GeographicRegion) -> List[SamplingPoint]:
        """Generate sampling points for a specific region"""
        min_lat, min_lon, max_lat, max_lon = region.bbox
        points = []
        
        # Calculate grid spacing based on coverage level
        spacing_map = {
            CoverageLevel.INTENSIVE: 0.008,  # ~0.5 miles
            CoverageLevel.STANDARD: 0.016,   # ~1 mile
            CoverageLevel.BASIC: 0.032,      # ~2 miles
            CoverageLevel.SPARSE: 0.080      # ~5 miles
        }
        
        spacing = spacing_map[region.coverage_level]
        
        if region.sampling_strategy == SamplingStrategy.UNIFORM_GRID:
            points = self._generate_uniform_grid(region, spacing)
        elif region.sampling_strategy == SamplingStrategy.POPULATION_WEIGHTED:
            points = self._generate_population_weighted(region, spacing)
        elif region.sampling_strategy == SamplingStrategy.ROAD_NETWORK_BASED:
            points = self._generate_road_network_based(region, spacing)
        elif region.sampling_strategy == SamplingStrategy.ADAPTIVE_DENSITY:
            points = self._generate_adaptive_density(region, spacing)
        else:
            points = self._generate_uniform_grid(region, spacing)
        
        return points
    
    def _generate_uniform_grid(self, region: GeographicRegion, spacing: float) -> List[SamplingPoint]:
        """Generate uniform grid of sampling points"""
        min_lat, min_lon, max_lat, max_lon = region.bbox
        points = []
        
        lat = min_lat
        while lat <= max_lat:
            lon = min_lon
            while lon <= max_lon:
                if self._is_point_in_rhode_island(lat, lon):
                    point = SamplingPoint(
                        id=f"{region.name}_{lat:.6f}_{lon:.6f}",
                        latitude=lat,
                        longitude=lon,
                        coverage_level=region.coverage_level,
                        priority=int(region.priority_multiplier * 100),
                        road_type="mixed",
                        population_density=region.population_density
                    )
                    points.append(point)
                lon += spacing
            lat += spacing
        
        return points
    
    def _generate_population_weighted(self, region: GeographicRegion, spacing: float) -> List[SamplingPoint]:
        """Generate population-weighted sampling points"""
        base_points = self._generate_uniform_grid(region, spacing)
        
        # Add extra points in high-population areas
        high_pop_areas = [
            (41.8236, -71.4222),  # Providence
            (41.7001, -71.4147),  # Warwick
            (41.5582, -71.3570),  # Newport
            (41.4901, -71.5295),  # Kingston
        ]
        
        for lat, lon in high_pop_areas:
            if self._is_point_in_region(lat, lon, region.bbox):
                # Add denser sampling around population centers
                for i in range(-2, 3):
                    for j in range(-2, 3):
                        new_lat = lat + i * spacing * 0.5
                        new_lon = lon + j * spacing * 0.5
                        if self._is_point_in_rhode_island(new_lat, new_lon):
                            point = SamplingPoint(
                                id=f"{region.name}_pop_{new_lat:.6f}_{new_lon:.6f}",
                                latitude=new_lat,
                                longitude=new_lon,
                                coverage_level=region.coverage_level,
                                priority=int(region.priority_multiplier * 120),
                                road_type="urban",
                                population_density=region.population_density * 1.5
                            )
                            base_points.append(point)
        
        return base_points
    
    def _generate_road_network_based(self, region: GeographicRegion, spacing: float) -> List[SamplingPoint]:
        """Generate sampling points based on road network"""
        base_points = self._generate_uniform_grid(region, spacing * 0.8)  # Slightly denser
        
        # Add specific points for major roads
        major_roads = [
            # I-95 corridor
            [(41.82, -71.42), (41.75, -71.43), (41.70, -71.42), (41.65, -71.41)],
            # I-195 corridor
            [(41.82, -71.42), (41.80, -71.35), (41.78, -71.30), (41.76, -71.25)],
            # Route 1 coastal
            [(41.70, -71.42), (41.60, -71.38), (41.50, -71.35), (41.40, -71.32)],
            # Route 95 north
            [(41.82, -71.42), (41.85, -71.45), (41.88, -71.48), (41.90, -71.50)]
        ]
        
        for road in major_roads:
            for lat, lon in road:
                if self._is_point_in_region(lat, lon, region.bbox):
                    point = SamplingPoint(
                        id=f"{region.name}_road_{lat:.6f}_{lon:.6f}",
                        latitude=lat,
                        longitude=lon,
                        coverage_level=region.coverage_level,
                        priority=int(region.priority_multiplier * 150),
                        road_type="highway",
                        population_density=region.population_density
                    )
                    base_points.append(point)
        
        return base_points
    
    def _generate_adaptive_density(self, region: GeographicRegion, spacing: float) -> List[SamplingPoint]:
        """Generate adaptive density sampling points"""
        base_points = self._generate_uniform_grid(region, spacing)
        
        # Add extra points based on special considerations
        if "tourism" in region.special_considerations:
            # Add more points around tourist areas
            tourist_areas = [
                (41.4901, -71.3127),  # Newport mansions
                (41.5765, -71.2756),  # Jamestown
                (41.3265, -71.5800),  # Narragansett beaches
            ]
            
            for lat, lon in tourist_areas:
                if self._is_point_in_region(lat, lon, region.bbox):
                    for i in range(-1, 2):
                        for j in range(-1, 2):
                            new_lat = lat + i * spacing * 0.6
                            new_lon = lon + j * spacing * 0.6
                            if self._is_point_in_rhode_island(new_lat, new_lon):
                                point = SamplingPoint(
                                    id=f"{region.name}_tourist_{new_lat:.6f}_{new_lon:.6f}",
                                    latitude=new_lat,
                                    longitude=new_lon,
                                    coverage_level=region.coverage_level,
                                    priority=int(region.priority_multiplier * 110),
                                    road_type="tourist",
                                    population_density=region.population_density * 0.8
                                )
                                base_points.append(point)
        
        return base_points
    
    def _is_point_in_rhode_island(self, lat: float, lon: float) -> bool:
        """Check if a point is within Rhode Island bounds"""
        min_lat, min_lon, max_lat, max_lon = self.ri_bounds
        return min_lat <= lat <= max_lat and min_lon <= lon <= max_lon
    
    def _is_point_in_region(self, lat: float, lon: float, bbox: Tuple[float, float, float, float]) -> bool:
        """Check if a point is within a region's bounding box"""
        min_lat, min_lon, max_lat, max_lon = bbox
        return min_lat <= lat <= max_lat and min_lon <= lon <= max_lon
    
    def _remove_duplicate_points(self, points: List[SamplingPoint]) -> List[SamplingPoint]:
        """Remove duplicate sampling points"""
        unique_points = []
        seen_coords = set()
        
        for point in points:
            # Round coordinates to avoid floating point precision issues
            rounded_coords = (round(point.latitude, 6), round(point.longitude, 6))
            
            if rounded_coords not in seen_coords:
                seen_coords.add(rounded_coords)
                unique_points.append(point)
            else:
                # If duplicate, keep the one with higher priority
                for i, existing_point in enumerate(unique_points):
                    if (round(existing_point.latitude, 6), round(existing_point.longitude, 6)) == rounded_coords:
                        if point.priority > existing_point.priority:
                            unique_points[i] = point
                        break
        
        return unique_points
    
    def _save_sampling_points_to_db(self, points: List[SamplingPoint]):
        """Save sampling points to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            for point in points:
                cursor.execute('''
                    INSERT OR REPLACE INTO sampling_points
                    (id, latitude, longitude, coverage_level, priority, road_type, population_density)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    point.id,
                    point.latitude,
                    point.longitude,
                    point.coverage_level.value,
                    point.priority,
                    point.road_type,
                    point.population_density
                ))
            
            conn.commit()
            logger.info(f"Saved {len(points)} sampling points to database")
            
        except Exception as e:
            logger.error(f"Error saving sampling points to database: {e}")
        finally:
            conn.close()
    
    def select_points_for_collection(self, max_points: int = 1000) -> List[SamplingPoint]:
        """Select sampling points for current collection cycle"""
        # Priority-based selection
        available_points = [p for p in self.sampling_points if self._should_sample_point(p)]
        
        # Sort by priority and time since last sample
        available_points.sort(key=lambda p: (
            -p.priority,  # Higher priority first
            p.last_sampled or datetime.min  # Longer time since last sample
        ))
        
        # Select top points within quota
        selected_points = available_points[:max_points]
        
        logger.info(f"Selected {len(selected_points)} points for collection from {len(available_points)} available")
        return selected_points
    
    def _should_sample_point(self, point: SamplingPoint) -> bool:
        """Determine if a point should be sampled in current cycle"""
        # Check if point hasn't been sampled recently
        if point.last_sampled:
            time_since_last = datetime.now() - point.last_sampled
            min_interval = timedelta(minutes=5 * point.coverage_level.value)
            
            if time_since_last < min_interval:
                return False
        
        # Check data quality and success rate
        if point.success_rate < 0.3 or point.data_quality < 0.5:
            return False
        
        return True
    
    def collect_statewide_data(self, max_points: int = 1000) -> Dict[str, Any]:
        """Collect traffic data from points across Rhode Island"""
        selected_points = self.select_points_for_collection(max_points)
        
        if not selected_points:
            return {"success": False, "message": "No points selected for collection"}
        
        collection_results = {
            "points_attempted": len(selected_points),
            "points_successful": 0,
            "api_requests_used": 0,
            "data_collected": [],
            "errors": []
        }
        
        # Collect data from selected points
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_point = {
                executor.submit(self._collect_point_data, point): point 
                for point in selected_points
            }
            
            for future in as_completed(future_to_point):
                point = future_to_point[future]
                try:
                    result = future.result()
                    if result:
                        collection_results["data_collected"].append(result)
                        collection_results["points_successful"] += 1
                        collection_results["api_requests_used"] += 1
                        
                        # Update point statistics
                        point.last_sampled = datetime.now()
                        point.success_rate = min(1.0, point.success_rate + 0.1)
                        point.data_quality = result.get("confidence", 0.5)
                    else:
                        point.success_rate = max(0.0, point.success_rate - 0.1)
                        
                except Exception as e:
                    collection_results["errors"].append(f"Point {point.id}: {str(e)}")
                    point.success_rate = max(0.0, point.success_rate - 0.2)
        
        # Save collected data
        if collection_results["data_collected"]:
            self._save_statewide_data(collection_results["data_collected"])
        
        # Update requests counter
        self.requests_today += collection_results["api_requests_used"]
        
        logger.info(f"Statewide collection: {collection_results['points_successful']}/{collection_results['points_attempted']} points successful")
        
        return collection_results
    
    def _collect_point_data(self, point: SamplingPoint) -> Optional[Dict[str, Any]]:
        """Collect data from a single sampling point"""
        if not self.api_key:
            return None
        
        # Check API quota
        if self.requests_today >= self.daily_quota:
            return None
        
        try:
            # Construct proper TomTom flow API URL
            flow_url = f"{self.api_base_urls['flow']}/absolute/10/json"
            params = {
                'point': f"{point.latitude},{point.longitude}",
                'unit': 'mph',
                'key': self.api_key
            }
            
            response = requests.get(
                flow_url, 
                params=params, 
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'flowSegmentData' in data:
                    flow_info = data['flowSegmentData']
                    
                    return {
                        "sampling_point_id": point.id,
                        "timestamp": datetime.now(),
                        "latitude": point.latitude,
                        "longitude": point.longitude,
                        "current_speed": flow_info.get('currentSpeed', 0),
                        "free_flow_speed": flow_info.get('freeFlowSpeed', 0),
                        "current_travel_time": flow_info.get('currentTravelTime', 0),
                        "free_flow_travel_time": flow_info.get('freeFlowTravelTime', 0),
                        "confidence": flow_info.get('confidence', 0),
                        "road_closure": flow_info.get('roadClosure', False),
                        "congestion_level": self._calculate_congestion_level(
                            flow_info.get('currentSpeed', 0),
                            flow_info.get('freeFlowSpeed', 60)
                        ),
                        "road_type": point.road_type,
                        "coverage_level": point.coverage_level.value,
                        "data_quality": point.data_quality
                    }
            
        except Exception as e:
            logger.error(f"Error collecting data from point {point.id}: {e}")
        
        return None
    
    def _calculate_congestion_level(self, current_speed: float, free_flow_speed: float) -> int:
        """Calculate congestion level from speed data"""
        if free_flow_speed == 0:
            return 0
        
        ratio = current_speed / free_flow_speed
        if ratio > 0.8:
            return 1  # Free flow
        elif ratio > 0.6:
            return 2  # Light congestion
        elif ratio > 0.4:
            return 3  # Moderate congestion
        elif ratio > 0.2:
            return 4  # Heavy congestion
        else:
            return 5  # Severe congestion
    
    def _save_statewide_data(self, data: List[Dict[str, Any]]):
        """Save statewide traffic data to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            for item in data:
                cursor.execute('''
                    INSERT INTO statewide_traffic_data
                    (sampling_point_id, timestamp, latitude, longitude, current_speed,
                     free_flow_speed, current_travel_time, free_flow_travel_time, confidence,
                     road_closure, congestion_level, road_type, coverage_level, data_quality)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    item["sampling_point_id"],
                    item["timestamp"],
                    item["latitude"],
                    item["longitude"],
                    item["current_speed"],
                    item["free_flow_speed"],
                    item["current_travel_time"],
                    item["free_flow_travel_time"],
                    item["confidence"],
                    item["road_closure"],
                    item["congestion_level"],
                    item["road_type"],
                    item["coverage_level"],
                    item["data_quality"]
                ))
            
            conn.commit()
            logger.info(f"Saved {len(data)} statewide traffic records")
            
        except Exception as e:
            logger.error(f"Error saving statewide data: {e}")
        finally:
            conn.close()
    
    def get_coverage_statistics(self) -> Dict[str, Any]:
        """Get statewide coverage statistics"""
        conn = sqlite3.connect(self.db_path)
        
        try:
            # Total sampling points
            total_points = len(self.sampling_points)
            
            # Points by coverage level
            coverage_stats = {}
            for level in CoverageLevel:
                count = len([p for p in self.sampling_points if p.coverage_level == level])
                coverage_stats[level.name] = count
            
            # Points by region
            region_stats = {}
            for region in self.geographic_regions:
                count = len([p for p in self.sampling_points if region.name in p.id])
                region_stats[region.name] = count
            
            # Recent collection statistics
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) as recent_samples
                FROM statewide_traffic_data
                WHERE timestamp >= ?
            ''', (datetime.now() - timedelta(hours=24),))
            
            recent_samples = cursor.fetchone()[0]
            
            # Data quality metrics
            cursor.execute('''
                SELECT AVG(data_quality) as avg_quality, AVG(confidence) as avg_confidence
                FROM statewide_traffic_data
                WHERE timestamp >= ?
            ''', (datetime.now() - timedelta(hours=24),))
            
            quality_result = cursor.fetchone()
            avg_quality = quality_result[0] if quality_result[0] else 0
            avg_confidence = quality_result[1] if quality_result[1] else 0
            
            return {
                "total_sampling_points": total_points,
                "coverage_by_level": coverage_stats,
                "points_by_region": region_stats,
                "recent_samples_24h": recent_samples,
                "average_data_quality": avg_quality,
                "average_confidence": avg_confidence,
                "api_requests_today": self.requests_today,
                "daily_quota": self.daily_quota,
                "quota_remaining": self.daily_quota - self.requests_today
            }
            
        finally:
            conn.close()
    
    def get_statewide_data(self, hours: int = 24) -> pd.DataFrame:
        """Get recent statewide traffic data"""
        conn = sqlite3.connect(self.db_path)
        
        try:
            import pandas as pd
            
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            df = pd.read_sql_query('''
                SELECT * FROM statewide_traffic_data
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
            ''', conn, params=(cutoff_time,))
            
            return df
            
        finally:
            conn.close()

# Global collector instance
_statewide_collector_instance = None

def get_statewide_collector() -> StatewideTrafficCollector:
    """Get singleton statewide collector instance"""
    global _statewide_collector_instance
    if _statewide_collector_instance is None:
        _statewide_collector_instance = StatewideTrafficCollector()
    return _statewide_collector_instance

if __name__ == "__main__":
    # Test the statewide collector
    collector = StatewideTrafficCollector()
    print(f"Statewide Traffic Collector initialized")
    print(f"API key configured: {'Yes' if collector.api_key else 'No'}")
    print(f"Total sampling points: {len(collector.sampling_points)}")
    
    # Show coverage statistics
    stats = collector.get_coverage_statistics()
    print(f"Coverage statistics: {stats}")
    
    # Test data collection
    if collector.api_key:
        print("Running test collection...")
        results = collector.collect_statewide_data(max_points=50)
        print(f"Test collection results: {results}")
    else:
        print("No API key available for testing collection")