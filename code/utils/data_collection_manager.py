#!/usr/bin/env python3
"""
Data Collection Manager for Village Platform
Integrates enhanced traffic collection with statewide coverage
"""

import streamlit as st
import pandas as pd
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from .enhanced_traffic_collector import get_enhanced_collector, EnhancedTrafficCollector
from .statewide_traffic_collector import get_statewide_collector, StatewideTrafficCollector
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

logger = logging.getLogger(__name__)

class DataCollectionManager:
    """Manages the enhanced traffic data collection system with statewide coverage"""
    
    def __init__(self):
        self.collector = get_enhanced_collector()
        self.statewide_collector = get_statewide_collector()
        
    def start_collection(self) -> bool:
        """Start data collection"""
        try:
            self.collector.start_continuous_collection()
            return True
        except Exception as e:
            logger.error(f"Failed to start collection: {e}")
            return False
    
    def stop_collection(self) -> bool:
        """Stop data collection"""
        try:
            self.collector.stop_collection()
            return True
        except Exception as e:
            logger.error(f"Failed to stop collection: {e}")
            return False
    
    def get_collection_status(self) -> Dict[str, Any]:
        """Get current collection status including statewide coverage"""
        status = self.collector.get_collection_status()
        statewide_stats = self.statewide_collector.get_coverage_statistics()
        
        # Merge the statuses
        status.update({
            'statewide_points': statewide_stats['total_sampling_points'],
            'coverage_levels': statewide_stats['coverage_by_level'],
            'statewide_quota_remaining': statewide_stats['quota_remaining'],
            'statewide_recent_samples': statewide_stats['recent_samples_24h']
        })
        
        return status
    
    def run_manual_collection(self) -> Dict[str, Any]:
        """Run manual collection cycle including statewide data"""
        try:
            # Run enhanced collector
            self.collector.run_collection_cycle()
            
            # Run statewide collector
            statewide_result = self.statewide_collector.collect_statewide_data(max_points=500)
            
            total_collected = statewide_result.get('points_successful', 0)
            
            return {
                "success": True, 
                "message": f"Manual collection completed - {total_collected} statewide points collected"
            }
        except Exception as e:
            logger.error(f"Manual collection failed: {e}")
            return {"success": False, "message": str(e)}
    
    def get_recent_data(self, hours: int = 24) -> Dict[str, pd.DataFrame]:
        """Get recent collected data including statewide coverage"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # Get enhanced collector data
        conn = sqlite3.connect(self.collector.db_path)
        
        try:
            # Get flow data
            flow_data = pd.read_sql_query('''
                SELECT * FROM traffic_flow 
                WHERE timestamp >= ? 
                ORDER BY timestamp DESC
            ''', conn, params=(cutoff_time,))
            
            # Get incident data
            incident_data = pd.read_sql_query('''
                SELECT * FROM traffic_incidents 
                WHERE timestamp >= ? 
                ORDER BY timestamp DESC
            ''', conn, params=(cutoff_time,))
            
            # Get route data
            route_data = pd.read_sql_query('''
                SELECT * FROM route_analysis 
                WHERE timestamp >= ? 
                ORDER BY timestamp DESC
            ''', conn, params=(cutoff_time,))
            
            # Get collection stats
            stats_data = pd.read_sql_query('''
                SELECT * FROM collection_stats 
                WHERE timestamp >= ? 
                ORDER BY timestamp DESC
            ''', conn, params=(cutoff_time,))
            
        finally:
            conn.close()
        
        # Get statewide data
        statewide_data = self.statewide_collector.get_statewide_data(hours=hours)
        
        return {
            'flow': flow_data,
            'incidents': incident_data,
            'routes': route_data,
            'stats': stats_data,
            'statewide': statewide_data
        }
    
    def get_data_summary(self) -> Dict[str, Any]:
        """Get summary statistics of collected data including statewide coverage"""
        conn = sqlite3.connect(self.collector.db_path)
        
        try:
            # Total records
            flow_count = pd.read_sql_query('SELECT COUNT(*) as count FROM traffic_flow', conn).iloc[0]['count']
            incident_count = pd.read_sql_query('SELECT COUNT(*) as count FROM traffic_incidents', conn).iloc[0]['count']
            route_count = pd.read_sql_query('SELECT COUNT(*) as count FROM route_analysis', conn).iloc[0]['count']
            
            # Recent data (last 24 hours)
            cutoff_time = datetime.now() - timedelta(hours=24)
            recent_flow = pd.read_sql_query('''
                SELECT COUNT(*) as count FROM traffic_flow 
                WHERE timestamp >= ?
            ''', conn, params=(cutoff_time,)).iloc[0]['count']
            
            recent_incidents = pd.read_sql_query('''
                SELECT COUNT(*) as count FROM traffic_incidents 
                WHERE timestamp >= ?
            ''', conn, params=(cutoff_time,)).iloc[0]['count']
            
            # Collection zones
            zones_data = pd.read_sql_query('''
                SELECT zone_name, COUNT(*) as collections, 
                       SUM(records_collected) as total_records,
                       AVG(success_rate) as avg_success_rate
                FROM collection_stats 
                WHERE timestamp >= ?
                GROUP BY zone_name
            ''', conn, params=(cutoff_time,))
            
        finally:
            conn.close()
        
        # Get statewide statistics
        statewide_stats = self.statewide_collector.get_coverage_statistics()
        statewide_data = self.statewide_collector.get_statewide_data(hours=24)
        
        return {
            'total_records': {
                'flow': flow_count,
                'incidents': incident_count,
                'routes': route_count,
                'statewide': len(statewide_data),
                'total': flow_count + incident_count + route_count + len(statewide_data)
            },
            'recent_24h': {
                'flow': recent_flow,
                'incidents': recent_incidents,
                'statewide': statewide_stats['recent_samples_24h'],
                'total': recent_flow + recent_incidents + statewide_stats['recent_samples_24h']
            },
            'zones': zones_data.to_dict('records') if not zones_data.empty else [],
            'statewide_coverage': statewide_stats
        }

def show_collection_management_page():
    """Show the data collection management page"""
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #faf8f3 0%, #f5f1e8 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        border-left: 4px solid #2d5016;
    ">
        <h1 style="color: #2d5016; margin: 0 0 1rem 0;">🚦 Traffic Data Collection Manager</h1>
        <p style="color: #5a7c47; margin: 0;">
            Comprehensive TomTom API integration for real-time traffic monitoring
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    manager = DataCollectionManager()
    
    # Collection status and controls
    st.subheader("Collection Status & Controls")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status = manager.get_collection_status()
        if status['is_collecting']:
            st.success("🟢 Collection Active")
            if st.button("Stop Collection"):
                if manager.stop_collection():
                    st.success("Collection stopped")
                    st.rerun()
                else:
                    st.error("Failed to stop collection")
        else:
            st.error("🔴 Collection Stopped")
            if st.button("Start Collection"):
                if manager.start_collection():
                    st.success("Collection started")
                    st.rerun()
                else:
                    st.error("Failed to start collection")
    
    with col2:
        st.metric(
            "API Requests Today",
            f"{status['api_requests_today']:,}",
            f"{status['quota_remaining']:,} remaining"
        )
    
    with col3:
        st.metric(
            "Collection Zones",
            status['zones_configured'],
            "Active zones"
        )
    
    # Manual collection
    st.subheader("Manual Collection")
    if st.button("Run Manual Collection Cycle"):
        with st.spinner("Running manual collection..."):
            result = manager.run_manual_collection()
            if result['success']:
                st.success(result['message'])
            else:
                st.error(result['message'])
    
    # Data summary
    st.subheader("Data Collection Summary")
    
    try:
        summary = manager.get_data_summary()
        
        # Total records metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Records", f"{summary['total_records']['total']:,}")
        
        with col2:
            st.metric("Flow Data", f"{summary['total_records']['flow']:,}")
        
        with col3:
            st.metric("Incidents", f"{summary['total_records']['incidents']:,}")
        
        with col4:
            st.metric("Statewide Points", f"{summary['total_records']['statewide']:,}")
        
        # Recent activity
        st.subheader("Recent Activity (24 hours)")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Recent Flow Data", f"{summary['recent_24h']['flow']:,}")
        
        with col2:
            st.metric("Recent Incidents", f"{summary['recent_24h']['incidents']:,}")
        
        with col3:
            st.metric("Recent Statewide", f"{summary['recent_24h']['statewide']:,}")
        
        # Zone performance
        if summary['zones']:
            st.subheader("Zone Performance")
            zones_df = pd.DataFrame(summary['zones'])
            st.dataframe(zones_df, use_container_width=True)
    
    except Exception as e:
        st.error(f"Error loading data summary: {e}")
    
    # Recent data preview
    st.subheader("Recent Data Preview")
    
    try:
        recent_data = manager.get_recent_data(hours=2)
        
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["Flow Data", "Incidents", "Routes", "Statewide Data", "Collection Stats"])
        
        with tab1:
            if not recent_data['flow'].empty:
                st.write(f"**{len(recent_data['flow'])} flow records in last 2 hours**")
                st.dataframe(recent_data['flow'].head(10), use_container_width=True)
                
                # Simple visualization
                if len(recent_data['flow']) > 0:
                    flow_viz = recent_data['flow'].copy()
                    flow_viz['timestamp'] = pd.to_datetime(flow_viz['timestamp'])
                    
                    fig = px.scatter(
                        flow_viz.head(50),
                        x='timestamp',
                        y='current_speed',
                        color='congestion_level',
                        title='Traffic Speed Over Time',
                        labels={'current_speed': 'Speed (mph)', 'congestion_level': 'Congestion Level'}
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No recent flow data available")
        
        with tab2:
            if not recent_data['incidents'].empty:
                st.write(f"**{len(recent_data['incidents'])} incidents in last 2 hours**")
                st.dataframe(recent_data['incidents'].head(10), use_container_width=True)
                
                # Incident severity chart
                if len(recent_data['incidents']) > 0:
                    severity_counts = recent_data['incidents']['severity'].value_counts()
                    fig = px.pie(
                        values=severity_counts.values,
                        names=severity_counts.index,
                        title='Incident Severity Distribution'
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No recent incident data available")
        
        with tab3:
            if not recent_data['routes'].empty:
                st.write(f"**{len(recent_data['routes'])} route analyses in last 2 hours**")
                st.dataframe(recent_data['routes'].head(10), use_container_width=True)
                
                # Route delay visualization
                if len(recent_data['routes']) > 0:
                    routes_viz = recent_data['routes'].copy()
                    routes_viz['timestamp'] = pd.to_datetime(routes_viz['timestamp'])
                    
                    fig = px.scatter(
                        routes_viz,
                        x='travel_time_minutes',
                        y='delay_minutes',
                        color='congestion_level',
                        title='Route Travel Time vs Delay',
                        labels={'travel_time_minutes': 'Travel Time (min)', 'delay_minutes': 'Delay (min)'}
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No recent route data available")
        
        with tab4:
            if not recent_data['statewide'].empty:
                st.write(f"**{len(recent_data['statewide'])} statewide records in last 2 hours**")
                st.dataframe(recent_data['statewide'].head(10), use_container_width=True)
                
                # Statewide coverage visualization
                if len(recent_data['statewide']) > 0:
                    statewide_viz = recent_data['statewide'].copy()
                    statewide_viz['timestamp'] = pd.to_datetime(statewide_viz['timestamp'])
                    
                    # Coverage by level
                    coverage_counts = statewide_viz['coverage_level'].value_counts().sort_index()
                    level_names = {1: 'Intensive', 2: 'Standard', 3: 'Basic', 4: 'Sparse'}
                    
                    fig = px.bar(
                        x=[level_names.get(idx, f'Level {idx}') for idx in coverage_counts.index],
                        y=coverage_counts.values,
                        title='Statewide Data Points by Coverage Level',
                        labels={'x': 'Coverage Level', 'y': 'Data Points'}
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Geographic distribution
                    fig2 = px.scatter(
                        statewide_viz.sample(min(200, len(statewide_viz))),
                        x='longitude',
                        y='latitude',
                        color='coverage_level',
                        size='current_speed',
                        title='Statewide Data Collection Points',
                        labels={'longitude': 'Longitude', 'latitude': 'Latitude', 'coverage_level': 'Coverage Level'}
                    )
                    st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("No recent statewide data available")
        
        with tab5:
            if not recent_data['stats'].empty:
                st.write(f"**Collection statistics for last 2 hours**")
                st.dataframe(recent_data['stats'], use_container_width=True)
                
                # Collection performance
                if len(recent_data['stats']) > 0:
                    stats_viz = recent_data['stats'].copy()
                    stats_viz['timestamp'] = pd.to_datetime(stats_viz['timestamp'])
                    
                    fig = px.bar(
                        stats_viz.groupby('zone_name')['records_collected'].sum().reset_index(),
                        x='zone_name',
                        y='records_collected',
                        title='Records Collected by Zone'
                    )
                    fig.update_xaxes(tickangle=45)
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No recent collection statistics available")
    
    except Exception as e:
        st.error(f"Error loading recent data: {e}")
    
    # Configuration
    st.subheader("Collection Configuration")
    
    with st.expander("View Collection Zones"):
        zones_info = []
        for zone in manager.collector.collection_zones:
            zones_info.append({
                'Zone Name': zone.name,
                'Priority': zone.priority,
                'Interval (min)': zone.collection_interval,
                'Data Types': ', '.join([dt.value for dt in zone.data_types]),
                'Bounding Box': f"{zone.bbox}"
            })
        
        if zones_info:
            zones_df = pd.DataFrame(zones_info)
            st.dataframe(zones_df, use_container_width=True)
    
    with st.expander("View Statewide Coverage"):
        statewide_stats = manager.statewide_collector.get_coverage_statistics()
        
        # Coverage summary
        st.metric("Total Sampling Points", f"{statewide_stats['total_sampling_points']:,}")
        
        # Coverage by level
        coverage_data = []
        for level, count in statewide_stats['coverage_by_level'].items():
            coverage_data.append({
                'Coverage Level': level,
                'Sample Points': count,
                'Description': {
                    'INTENSIVE': 'Every 0.5 miles - Urban cores, major highways',
                    'STANDARD': 'Every 1 mile - Suburban areas, main roads',
                    'BASIC': 'Every 2 miles - Rural areas, secondary roads',
                    'SPARSE': 'Every 5 miles - Remote areas, low density'
                }.get(level, 'Unknown')
            })
        
        if coverage_data:
            coverage_df = pd.DataFrame(coverage_data)
            st.dataframe(coverage_df, use_container_width=True)
        
        # Geographic regions
        st.subheader("Geographic Regions")
        region_data = []
        for region_name, count in statewide_stats['points_by_region'].items():
            region_data.append({
                'Region': region_name,
                'Sample Points': count
            })
        
        if region_data:
            region_df = pd.DataFrame(region_data)
            st.dataframe(region_df, use_container_width=True)
        
        # API quota usage
        st.subheader("API Quota Usage")
        quota_used = statewide_stats['api_requests_today']
        quota_total = statewide_stats['daily_quota']
        quota_remaining = statewide_stats['quota_remaining']
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Used Today", f"{quota_used:,}")
        with col2:
            st.metric("Remaining", f"{quota_remaining:,}")
        with col3:
            st.metric("Usage %", f"{(quota_used/quota_total)*100:.1f}%")
    
    # API key status
    st.subheader("API Configuration")
    if manager.collector.api_key:
        st.success("✅ TomTom API Key Configured")
        st.info("The enhanced collector with statewide coverage is ready to gather comprehensive traffic data from across Rhode Island including flow, incidents, routes, and congestion patterns.")
        
        # Show coverage capabilities
        st.markdown("**Coverage Capabilities:**")
        st.markdown("- 🎯 **Statewide Coverage**: Thousands of sampling points across all of Rhode Island")
        st.markdown("- 📊 **Priority Zones**: Intensive monitoring of high-traffic areas")
        st.markdown("- 🌐 **Geographic Regions**: 9 distinct regions with adaptive sampling")
        st.markdown("- 📈 **Real-time Data**: Live traffic flow, incidents, and congestion")
        st.markdown("- 🔄 **Historical Analysis**: Long-term pattern recognition")
        st.markdown("- 📍 **O/D Analysis**: Origin-destination trip matrices")
    else:
        st.error("❌ TomTom API Key Not Configured")
        st.warning("Please set your TomTom API key in secrets.toml or environment variables to enable statewide data collection.")
        st.code("TOMTOM_API_KEY = 'your-api-key-here'")

if __name__ == "__main__":
    show_collection_management_page()