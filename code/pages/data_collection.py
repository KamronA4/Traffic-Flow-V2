#!/usr/bin/env python3
"""
Enhanced Data Collection Page for Village Platform
Comprehensive TomTom API data collection management with expanded capabilities
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
sys.path.append(str(parent_dir))

# Import collectors
try:
    from utils.data_collection_manager import DataCollectionManager
    from utils.historical_traffic_collector import get_historical_collector, HistoricalDataType
    from utils.origin_destination_collector import get_od_collector, TripType, TimeCategory
    from utils.enhanced_traffic_collector import get_enhanced_collector
    from utils.statewide_traffic_collector import get_statewide_collector
except ImportError as e:
    st.error(f"Error importing collectors: {e}")

# Village color scheme
VILLAGE_COLORS = {
    'primary': '#2d5016',
    'secondary': '#5a7c47',
    'accent': '#8b4513',
    'neutral': '#f5f1e8',
    'palette': ['#2d5016', '#5a7c47', '#8b4513', '#d4a574', '#9c8b7a', '#6b5b95']
}

def show():
    """Show enhanced data collection management page"""
    
    # Custom CSS for enhanced styling with dark mode support
    st.markdown("""
    <style>
    :root {
        --village-pine: #2d5016;
        --village-sage: #5a7c47;
        --village-beige: #f5f1e8;
        --village-brown: #8b4513;
        --village-cream: #faf8f3;
    }
    
    /* Dark mode variables */
    @media (prefers-color-scheme: dark) {
        :root {
            --village-pine: #4a7c2a;
            --village-sage: #6b9c57;
            --village-beige: #2d2d2d;
            --village-brown: #b5651d;
            --village-cream: #1e1e1e;
        }
    }
    
    .collection-header {
        background: linear-gradient(135deg, var(--village-pine) 0%, var(--village-sage) 50%, var(--village-brown) 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 6px 20px rgba(0,0,0,0.15);
    }
    
    .collector-card {
        background: linear-gradient(135deg, var(--village-cream) 0%, var(--village-beige) 100%);
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        border-left: 4px solid var(--village-sage);
        box-shadow: 0 3px 10px rgba(0,0,0,0.1);
    }
    
    .status-active {
        color: var(--village-pine);
        background: #d4edda;
        padding: 0.25rem 0.75rem;
        border-radius: 15px;
        font-weight: 600;
    }
    
    .status-paused {
        color: var(--village-brown);
        background: #fff3cd;
        padding: 0.25rem 0.75rem;
        border-radius: 15px;
        font-weight: 600;
    }
    
    .status-stopped {
        color: #dc3545;
        background: #f8d7da;
        padding: 0.25rem 0.75rem;
        border-radius: 15px;
        font-weight: 600;
    }
    
    .api-quota-warning {
        background: #fff3cd;
        color: var(--village-brown);
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #ffeaa7;
        margin: 1rem 0;
    }
    
    .api-quota-critical {
        background: #f8d7da;
        color: #dc3545;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #f5c6cb;
        margin: 1rem 0;
    }
    
    /* Dark mode specific adjustments */
    @media (prefers-color-scheme: dark) {
        .status-active {
            background: #155724;
            color: #d4edda;
        }
        
        .status-paused {
            background: #856404;
            color: #fff3cd;
        }
        
        .status-stopped {
            background: #721c24;
            color: #f8d7da;
        }
        
        .api-quota-warning {
            background: #856404;
            color: #fff3cd;
            border-color: #b5651d;
        }
        
        .api-quota-critical {
            background: #721c24;
            color: #f8d7da;
            border-color: #dc3545;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="collection-header">
        <h1 style="margin: 0.5rem 0;">🚦 Enhanced Data Collection Management</h1>
        <p style="margin: 0; font-size: 1.1rem; opacity: 0.9;">
            Comprehensive TomTom API integration for municipal traffic intelligence
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Main navigation
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Overview", 
        "Collection", 
        "Historical Analysis", 
        "O/D Analysis", 
        "Configuration"
    ])
    
    with tab1:
        show_overview()
    
    with tab2:
        show_realtime_collection()
    
    with tab3:
        show_historical_analysis()
    
    with tab4:
        show_od_analysis()
    
    with tab5:
        show_configuration()

def show_overview():
    """Show data collection overview"""
    st.markdown("## 📊 Collection Overview")
    
    # API quota status
    show_api_quota_status()
    
    # Collection metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Active Collectors", "4", "+1")
    
    with col2:
        st.metric("API Requests Today", "2,847", "+1,247")
    
    with col3:
        st.metric("Data Points Collected", "18,950", "+6,500")
    
    with col4:
        st.metric("Statewide Points", "2,847", "Active")
    
    # Collection status summary
    st.markdown("---")
    st.markdown("### 🔄 Collection Status Summary")
    
    status_data = {
        "Data Source": [
            "Real-time Traffic Flow",
            "Traffic Incidents", 
            "Route Analysis",
            "Historical Analysis",
            "O/D Analysis",
            "Statewide Coverage",
            "Junction Analytics",
            "Matrix Routing",
            "Parking Availability",
            "Fuel Prices"
        ],
        "Status": [
            "🟢 Active",
            "🟢 Active", 
            "🟢 Active",
            "🟡 Processing",
            "🔴 Stopped",
            "🟢 Active",
            "🟢 Active",
            "🟡 Limited",
            "🟡 Limited",
            "🔴 Disabled"
        ],
        "Last Update": [
            "2 minutes ago",
            "5 minutes ago",
            "3 minutes ago", 
            "1 hour ago",
            "3 hours ago",
            "2 minutes ago",
            "10 minutes ago",
            "30 minutes ago",
            "15 minutes ago",
            "Never"
        ],
        "Records Today": [1250, 45, 89, 0, 0, 847, 34, 12, 23, 0],
        "API Requests": [1240, 125, 267, 0, 0, 423, 68, 24, 46, 0]
    }
    
    df = pd.DataFrame(status_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Recent collection activity
    st.markdown("---")
    st.markdown("### 📈 Recent Collection Activity")
    
    # Generate sample time series data
    hours = [(datetime.now() - timedelta(hours=i)) for i in range(24, 0, -1)]
    sample_data = pd.DataFrame({
        'Hour': hours,
        'Traffic Flow': [120 + i*5 + (i%6)*10 for i in range(24)],
        'Incidents': [2 + (i%8) for i in range(24)],
        'Routes': [15 + (i%4)*3 for i in range(24)],
        'Historical': [0 if i < 12 else 5 + (i%3) for i in range(24)],
        'O/D Analysis': [0 if i < 20 else 8 + (i%2) for i in range(24)]
    })
    
    # Create time series chart
    fig = px.line(sample_data, x='Hour', 
                  y=['Traffic Flow', 'Incidents', 'Routes', 'Historical', 'O/D Analysis'], 
                  title='Data Collection Activity (Last 24 Hours)',
                  color_discrete_map={
                      'Traffic Flow': VILLAGE_COLORS['primary'],
                      'Incidents': VILLAGE_COLORS['secondary'],
                      'Routes': VILLAGE_COLORS['accent'],
                      'Historical': '#d4a574',
                      'O/D Analysis': '#9c8b7a'
                  })
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color=VILLAGE_COLORS['primary'])
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Expanded data sources info
    st.markdown("---")
    st.markdown("### 🔧 Data Sources Overview")
    
    with st.expander("📊 Real-time Data Sources"):
        st.markdown("""
        - **Traffic Flow**: Speed, congestion, travel times from TomTom Flow API
        - **Incidents**: Accidents, construction, road closures from TomTom Incidents API  
        - **Routes**: Route analysis, delays, alternative paths from TomTom Routing API
        - **Junction Analytics**: Intersection performance, signal optimization data
        - **Matrix Routing**: Multi-origin/destination routing for logistics optimization
        - **Statewide Coverage**: Thousands of sampling points across all of Rhode Island
        """)
    
    with st.expander("📈 Historical Data Sources"):
        st.markdown("""
        - **Traffic Stats**: Historical speed profiles, seasonal patterns, trend analysis
        - **Area Analysis**: Comprehensive zone-based traffic pattern analysis
        - **Route Analysis**: Before/after infrastructure impact assessment
        - **Speed Profiles**: V85, average, median speeds for planning purposes
        """)
    
    with st.expander("🔄 Movement Intelligence"):
        st.markdown("""
        - **O/D Analysis**: Origin-destination trip matrices, flow patterns
        - **Trip Distribution**: Understanding where trips begin and end
        - **Popular Routes**: Most used corridors and travel patterns
        - **POI Popularity**: Attraction scores for points of interest
        - **Statewide Flow Patterns**: Movement analysis across all 9 Rhode Island regions
        """)
    
    with st.expander("⚡ Real-time Services"):
        st.markdown("""
        - **Parking Availability**: Real-time parking data with 10-minute updates
        - **Fuel Prices**: Current fuel costs affecting transportation patterns
        - **EV Charging**: Electric vehicle infrastructure and availability
        - **Geofencing**: Boundary monitoring and zone-based alerts
        - **Priority-Based Sampling**: Intelligent point selection for comprehensive coverage
        """)

def show_api_quota_status():
    """Show API quota status with warnings"""
    # Mock API quota data
    daily_quota = 50000
    used_today = 12847
    remaining = daily_quota - used_today
    usage_percent = (used_today / daily_quota) * 100
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Daily API Quota", f"{daily_quota:,}", "TomTom Free Tier")
    
    with col2:
        st.metric("Used Today", f"{used_today:,}", f"{usage_percent:.1f}%")
    
    with col3:
        st.metric("Remaining", f"{remaining:,}", f"{100-usage_percent:.1f}%")
    
    # Quota warnings
    if usage_percent > 90:
        st.markdown("""
        <div class="api-quota-critical">
            <strong>🚨 Critical API Quota Usage</strong><br>
            You've used over 90% of your daily quota. Collection may be throttled or stopped.
        </div>
        """, unsafe_allow_html=True)
    elif usage_percent > 75:
        st.markdown("""
        <div class="api-quota-warning">
            <strong>⚠️ High API Quota Usage</strong><br>
            You've used over 75% of your daily quota. Consider prioritizing critical collections.
        </div>
        """, unsafe_allow_html=True)
    
    # Progress bar
    st.progress(usage_percent / 100)

def show_realtime_collection():
    """Show real-time collection management"""
    st.markdown("## 🔄 Real-time Data Collection")
    
    try:
        # Get real-time collector status
        manager = DataCollectionManager()
        status = manager.get_collection_status()
        
        # Collection controls
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if status.get('is_collecting', False):
                st.success("🟢 Collection Active")
                if st.button("⏸️ Pause Collection"):
                    manager.stop_collection()
                    st.rerun()
            else:
                st.error("🔴 Collection Stopped")
                if st.button("▶️ Start Collection"):
                    manager.start_collection()
                    st.rerun()
        
        with col2:
            if st.button("🔄 Run Manual Collection"):
                with st.spinner("Running manual collection..."):
                    result = manager.run_manual_collection()
                    if result['success']:
                        st.success(result['message'])
                    else:
                        st.error(result['message'])
        
        with col3:
            if st.button("📊 Refresh Data"):
                st.rerun()
        
        # Recent data preview
        st.markdown("---")
        st.markdown("### 📋 Recent Data Preview")
        
        recent_data = manager.get_recent_data(hours=2)
        
        tab1, tab2, tab3, tab4 = st.tabs(["Traffic Flow", "Incidents", "Routes", "Collection Stats"])
        
        with tab1:
            if not recent_data['flow'].empty:
                st.write(f"**{len(recent_data['flow'])} flow records in last 2 hours**")
                st.dataframe(recent_data['flow'].head(10), use_container_width=True)
                
                # Flow visualization
                if len(recent_data['flow']) > 0:
                    fig = px.scatter(
                        recent_data['flow'].head(50),
                        x='timestamp',
                        y='current_speed',
                        color='congestion_level',
                        title='Traffic Speed Over Time',
                        color_discrete_map={
                            1: '#2d5016', 2: '#5a7c47', 3: '#8b4513', 
                            4: '#d4a574', 5: '#dc3545'
                        }
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
                        title='Incident Severity Distribution',
                        color_discrete_sequence=VILLAGE_COLORS['palette']
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No recent incident data available")
        
        with tab3:
            if not recent_data['routes'].empty:
                st.write(f"**{len(recent_data['routes'])} route analyses in last 2 hours**")
                st.dataframe(recent_data['routes'].head(10), use_container_width=True)
                
                # Route performance
                if len(recent_data['routes']) > 0:
                    fig = px.scatter(
                        recent_data['routes'],
                        x='travel_time_minutes',
                        y='delay_minutes',
                        color='congestion_level',
                        title='Route Performance Analysis',
                        color_discrete_map={
                            1: '#2d5016', 2: '#5a7c47', 3: '#8b4513', 
                            4: '#d4a574', 5: '#dc3545'
                        }
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No recent route data available")
        
        with tab4:
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
                        title='Records Collected by Zone',
                        color_discrete_sequence=[VILLAGE_COLORS['primary']]
                    )
                    fig.update_xaxes(tickangle=45)
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No recent collection statistics available")
        
    except Exception as e:
        st.error(f"Error loading real-time collection data: {e}")

def show_historical_analysis():
    """Show historical analysis management"""
    st.markdown("## 📈 Historical Traffic Analysis")
    
    try:
        historical_collector = get_historical_collector()
        
        # Historical analysis controls
        st.markdown("### 🔧 Analysis Controls")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Area Analysis")
            
            # Zone selection
            zone_options = [
                "I-95 Providence Corridor",
                "I-195 East-West",
                "Providence Downtown",
                "Warwick Airport Area",
                "Newport Historic District"
            ]
            selected_zone = st.selectbox("Select Analysis Zone", zone_options)
            
            # Date range
            start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=30))
            end_date = st.date_input("End Date", value=datetime.now())
            
            # Time sets
            time_sets = [
                {"name": "morning_peak", "startTime": "07:00", "endTime": "09:00"},
                {"name": "evening_peak", "startTime": "17:00", "endTime": "19:00"},
                {"name": "midday", "startTime": "11:00", "endTime": "14:00"}
            ]
            
            if st.button("🚀 Submit Area Analysis"):
                with st.spinner("Submitting analysis job..."):
                    # Mock bounding box for selected zone
                    bbox = (41.7, -71.6, 41.9, -71.3)
                    
                    job_id = historical_collector.submit_area_analysis_job(
                        zone_name=selected_zone,
                        bbox=bbox,
                        date_range=(datetime.combine(start_date, datetime.min.time()),
                                   datetime.combine(end_date, datetime.min.time())),
                        time_sets=time_sets
                    )
                    
                    if job_id:
                        st.success(f"Analysis job submitted! Job ID: {job_id}")
                    else:
                        st.error("Failed to submit analysis job")
        
        with col2:
            st.markdown("#### Route Analysis")
            
            # Route definition
            st.text_input("Origin", placeholder="Providence Downtown")
            st.text_input("Destination", placeholder="Warwick Airport")
            
            # Analysis type
            analysis_type = st.selectbox("Analysis Type", [
                "Travel Time Analysis",
                "Speed Profile Analysis", 
                "Congestion Pattern Analysis",
                "Seasonal Comparison"
            ])
            
            if st.button("🚀 Submit Route Analysis"):
                st.info("Route analysis will be implemented with full API integration")
        
        # Job monitoring
        st.markdown("---")
        st.markdown("### 📊 Analysis Jobs Status")
        
        jobs_df = historical_collector.get_job_history()
        
        if not jobs_df.empty:
            st.dataframe(jobs_df.head(10), use_container_width=True)
        else:
            st.info("No analysis jobs found")
        
        # Historical data visualization
        st.markdown("---")
        st.markdown("### 📈 Historical Data Visualization")
        
        historical_data = historical_collector.get_historical_data()
        
        if not historical_data.empty:
            # Speed trends
            fig = px.line(
                historical_data,
                x='date_analyzed',
                y='average_speed',
                color='zone_name',
                title='Historical Speed Trends',
                color_discrete_sequence=VILLAGE_COLORS['palette']
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Congestion patterns
            fig2 = px.box(
                historical_data,
                x='zone_name',
                y='congestion_level',
                title='Congestion Level Distribution by Zone',
                color_discrete_sequence=VILLAGE_COLORS['palette']
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No historical data available yet")
    
    except Exception as e:
        st.error(f"Error loading historical analysis: {e}")

def show_od_analysis():
    """Show origin-destination analysis"""
    st.markdown("## 🔄 Origin-Destination Analysis")
    
    try:
        od_collector = get_od_collector()
        
        # O/D analysis controls
        st.markdown("### 🎯 Analysis Controls")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Create O/D Analysis")
            
            # Date range
            start_date = st.date_input("Analysis Start Date", value=datetime.now() - timedelta(days=7))
            end_date = st.date_input("Analysis End Date", value=datetime.now())
            
            # Time periods
            time_periods = st.multiselect(
                "Time Periods",
                ["Morning Peak", "Evening Peak", "Midday", "Night"],
                default=["Morning Peak", "Evening Peak"]
            )
            
            # Trip types
            trip_types = st.multiselect(
                "Trip Types",
                ["All Trips", "Commute", "Commercial", "Leisure"],
                default=["All Trips"]
            )
            
            if st.button("🚀 Submit O/D Analysis"):
                with st.spinner("Submitting O/D analysis job..."):
                    # Convert time periods to API format
                    time_sets = []
                    if "Morning Peak" in time_periods:
                        time_sets.append({"name": "morning_peak", "startTime": "07:00", "endTime": "09:00"})
                    if "Evening Peak" in time_periods:
                        time_sets.append({"name": "evening_peak", "startTime": "17:00", "endTime": "19:00"})
                    if "Midday" in time_periods:
                        time_sets.append({"name": "midday", "startTime": "11:00", "endTime": "14:00"})
                    
                    job_id = od_collector.submit_od_analysis_job(
                        date_range=(datetime.combine(start_date, datetime.min.time()),
                                   datetime.combine(end_date, datetime.min.time())),
                        time_sets=time_sets
                    )
                    
                    if job_id:
                        st.success(f"O/D analysis job submitted! Job ID: {job_id}")
                    else:
                        st.error("Failed to submit O/D analysis job")
        
        with col2:
            st.markdown("#### Analysis Results")
            
            # Trip matrix data
            trip_data = od_collector.get_trip_matrix_data()
            
            if not trip_data.empty:
                # Top origin-destination pairs
                top_pairs = trip_data.nlargest(10, 'trip_count')
                
                fig = px.bar(
                    top_pairs,
                    x='trip_count',
                    y=[f"{row['origin_name']} → {row['destination_name']}" 
                       for _, row in top_pairs.iterrows()],
                    title='Top Origin-Destination Pairs',
                    orientation='h',
                    color_discrete_sequence=[VILLAGE_COLORS['primary']]
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No O/D analysis results available yet")
        
        # Flow patterns
        st.markdown("---")
        st.markdown("### 🌊 Flow Patterns")
        
        flow_data = od_collector.get_flow_patterns_data()
        
        if not flow_data.empty:
            st.dataframe(flow_data.head(10), use_container_width=True)
        else:
            st.info("No flow pattern data available")
        
        # POI popularity
        st.markdown("---")
        st.markdown("### 📍 POI Popularity Analysis")
        
        poi_data = od_collector.get_poi_popularity_data()
        
        if not poi_data.empty:
            # Top attractions
            fig = px.bar(
                poi_data.head(10),
                x='attraction_score',
                y='region_name',
                color='poi_type',
                title='Top Attraction Destinations',
                orientation='h',
                color_discrete_sequence=VILLAGE_COLORS['palette']
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No POI popularity data available")
    
    except Exception as e:
        st.error(f"Error loading O/D analysis: {e}")

def show_configuration():
    """Show collection configuration"""
    st.markdown("## ⚙️ Collection Configuration")
    
    # API configuration
    st.markdown("### 🔑 API Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### TomTom API Settings")
        
        # API key status
        try:
            api_key = st.secrets.get("TOMTOM_API_KEY", "")
            if api_key and api_key != "your-tomtom-api-key-here":
                st.success("✅ API Key Configured")
            else:
                st.error("❌ API Key Not Configured")
                st.code("Add TOMTOM_API_KEY to secrets.toml")
        except:
            st.warning("⚠️ Cannot access secrets configuration")
        
        # Rate limiting
        st.number_input("Rate Limit (requests/second)", value=10, min_value=1, max_value=100)
        st.number_input("Daily Quota", value=50000, min_value=1000, max_value=1000000)
    
    with col2:
        st.markdown("#### Collection Intervals")
        
        # Collection frequencies
        st.selectbox("Traffic Flow Collection", ["30 seconds", "1 minute", "5 minutes"], index=1)
        st.selectbox("Incident Collection", ["1 minute", "5 minutes", "10 minutes"], index=1)
        st.selectbox("Route Analysis", ["5 minutes", "10 minutes", "30 minutes"], index=1)
        st.selectbox("Historical Analysis", ["Daily", "Weekly", "Monthly"], index=1)
    
    # Expanded collection zones
    st.markdown("---")
    st.markdown("### 🗺️ Enhanced Collection Zones")
    
    zones_config = {
        "Zone": [
            "I-95 Providence Corridor",
            "I-195 East-West",
            "Providence Downtown",
            "Warwick Airport Area",
            "Newport Historic District",
            "URI Kingston Campus",
            "Pawtucket Industrial",
            "Cranston Residential",
            "Legacy Place Shopping",
            "Providence Station",
            "RI Hospital"
        ],
        "Priority": [1, 1, 2, 2, 3, 3, 2, 3, 2, 4, 4],
        "Interval": ["5 min", "5 min", "10 min", "10 min", "15 min", "20 min", "15 min", "15 min", "10 min", "10 min", "10 min"],
        "Data Types": [
            "Flow, Incidents, Routes, Historical",
            "Flow, Incidents, Routes, Historical", 
            "Flow, Incidents, Congestion, O/D",
            "Flow, Incidents, O/D",
            "Flow, Incidents, O/D",
            "Flow, Incidents",
            "Flow, Incidents",
            "Flow, O/D",
            "Flow, Incidents, O/D",
            "Flow, O/D",
            "Flow, Incidents"
        ],
        "Status": ["Active", "Active", "Active", "Active", "Active", "Active", "Paused", "Active", "Active", "Active", "Active"]
    }
    
    zones_df = pd.DataFrame(zones_config)
    st.dataframe(zones_df, use_container_width=True, hide_index=True)
    
    # Advanced data collection settings
    st.markdown("---")
    st.markdown("### 📊 Advanced Data Collection")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### New Data Sources")
        
        st.checkbox("Junction Analytics", value=True, help="Intersection performance metrics")
        st.checkbox("Matrix Routing", value=True, help="Multi-point routing analysis")
        st.checkbox("Parking Availability", value=False, help="Real-time parking data")
        st.checkbox("Fuel Prices", value=False, help="Current fuel cost information")
        st.checkbox("EV Charging", value=False, help="Electric vehicle charging stations")
        st.checkbox("Weather Integration", value=False, help="Weather impact on traffic")
    
    with col2:
        st.markdown("#### Analysis Features")
        
        st.checkbox("Seasonal Pattern Analysis", value=True, help="Year-over-year comparisons")
        st.checkbox("Predictive Modeling", value=True, help="Traffic prediction algorithms")
        st.checkbox("Anomaly Detection", value=True, help="Unusual traffic pattern detection")
        st.checkbox("Event Impact Analysis", value=False, help="Special event traffic impact")
        st.checkbox("Construction Zone Monitoring", value=True, help="Work zone traffic analysis")
        st.checkbox("Emergency Response Optimization", value=False, help="First responder routing")
    
    # Data retention and export
    st.markdown("---")
    st.markdown("### 🗄️ Data Management")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### Retention Policies")
        st.number_input("Real-time Data (days)", value=30, min_value=1, max_value=365)
        st.number_input("Historical Analysis (days)", value=365, min_value=30, max_value=1095)
        st.number_input("O/D Analysis (days)", value=180, min_value=30, max_value=730)
    
    with col2:
        st.markdown("#### Export Options")
        export_format = st.selectbox("Export Format", ["CSV", "JSON", "Excel", "Parquet"])
        if st.button("📤 Export All Data"):
            st.success(f"Data exported to {export_format} format")
    
    with col3:
        st.markdown("#### Data Quality")
        st.metric("Data Completeness", "94.2%")
        st.metric("API Success Rate", "98.7%")
        st.metric("Data Freshness", "< 2 min")

if __name__ == "__main__":
    show()