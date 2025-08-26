# pages/demo_dashboard.py - Demo Dashboard for Presentations

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
sys.path.append(str(parent_dir))

# Configure logging
logger = logging.getLogger(__name__)

def show():
    """Display the demo dashboard"""
    
    # Import theme manager with error handling
    try:
        from utils.theme_manager import apply_village_theme, create_village_header, get_village_colors
        apply_village_theme()
        create_village_header("Demo Dashboard", "Real-time overview for presentations and demonstrations")
    except ImportError:
        st.title("📊 Demo Dashboard")
        st.caption("Real-time overview for presentations and demonstrations")
    
    # Check demo mode
    demo_mode = os.getenv('VILLAGE_DEMO_MODE', 'false').lower() == 'true'
    
    if not demo_mode:
        st.warning("🔒 Demo Dashboard requires demo mode to be enabled")
        st.info("Set VILLAGE_DEMO_MODE=true and restart the application")
        return
    
    # Get current data
    try:
        from utils.data_sync import get_traffic_data, get_traffic_flow_data
        incidents_data = get_traffic_data()
        flow_data = get_traffic_flow_data()
    except ImportError:
        st.error("Unable to load traffic data modules")
        return
    except Exception as e:
        st.error(f"Error loading traffic data: {e}")
        incidents_data = pd.DataFrame()
        flow_data = pd.DataFrame()
    
    # Real-time metrics
    st.subheader("📈 Real-Time Metrics")
    
    if incidents_data.empty:
        st.info("🎯 No demo data available. Use the Demo Controls page to generate sample data.")
        return
    
    # Process timestamp if needed
    if not incidents_data.empty:
        incidents_data['timestamp'] = pd.to_datetime(incidents_data['timestamp'])
        incidents_data['hour'] = incidents_data['timestamp'].dt.hour
    
    # Key metrics row
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        total_incidents = len(incidents_data)
        st.metric("🚨 Active Incidents", total_incidents)
    
    with col2:
        high_severity = len(incidents_data[incidents_data['severity'] > 3])
        st.metric("⚠️ High Severity", high_severity, 
                 f"{(high_severity/total_incidents)*100:.1f}%" if total_incidents > 0 else "0%")
    
    with col3:
        affected_areas = incidents_data['location'].nunique()
        st.metric("📍 Affected Areas", affected_areas)
    
    with col4:
        avg_severity = incidents_data['severity'].mean()
        st.metric("📊 Avg Severity", f"{avg_severity:.1f}", 
                 "🔺" if avg_severity > 2.5 else "▲" if avg_severity > 2 else "🔽")
    
    with col5:
        recent_incidents = len(incidents_data[incidents_data['timestamp'] > datetime.now() - timedelta(hours=1)])
        st.metric("🕐 Last Hour", recent_incidents)
    
    # Charts section
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Incident Distribution by Severity")
        
        if not incidents_data.empty:
            severity_counts = incidents_data['severity'].value_counts().sort_index()
            
            # Create color mapping for severity
            colors = ['#2ecc71', '#f39c12', '#e67e22', '#e74c3c', '#8e44ad']
            
            fig_severity = px.bar(
                x=severity_counts.index,
                y=severity_counts.values,
                labels={'x': 'Severity Level', 'y': 'Number of Incidents'},
                title="Incident Count by Severity Level",
                color=severity_counts.index,
                color_continuous_scale=colors
            )
            
            fig_severity.update_layout(
                showlegend=False,
                height=400,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            
            st.plotly_chart(fig_severity, use_container_width=True)
        else:
            st.info("No data to display")
    
    with col2:
        st.subheader("🕒 Incidents by Hour")
        
        if not incidents_data.empty:
            hourly_counts = incidents_data['hour'].value_counts().sort_index()
            
            fig_hourly = px.line(
                x=hourly_counts.index,
                y=hourly_counts.values,
                labels={'x': 'Hour of Day', 'y': 'Number of Incidents'},
                title="Incident Distribution Throughout the Day",
                markers=True
            )
            
            # Highlight rush hours
            fig_hourly.add_vrect(
                x0=7, x1=9, fillcolor="red", opacity=0.2, 
                annotation_text="Morning Rush", annotation_position="top left"
            )
            fig_hourly.add_vrect(
                x0=16, x1=18, fillcolor="red", opacity=0.2,
                annotation_text="Evening Rush", annotation_position="top right"
            )
            
            fig_hourly.update_layout(
                height=400,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            
            st.plotly_chart(fig_hourly, use_container_width=True)
        else:
            st.info("No data to display")
    
    # Geographic distribution
    st.subheader("🗺️ Geographic Distribution")
    
    if not incidents_data.empty and 'latitude' in incidents_data.columns:
        # Create a simple scatter plot on map
        fig_map = px.scatter_mapbox(
            incidents_data,
            lat='latitude',
            lon='longitude',
            color='severity',
            size='severity',
            hover_name='location',
            hover_data=['description', 'timestamp'],
            color_continuous_scale='Reds',
            title="Incident Locations and Severity",
            zoom=10,
            height=500
        )
        
        fig_map.update_layout(
            mapbox_style="open-street-map",
            mapbox_center_lat=incidents_data['latitude'].mean(),
            mapbox_center_lon=incidents_data['longitude'].mean(),
            margin={"r":0,"t":30,"l":0,"b":0}
        )
        
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.info("Geographic data not available for mapping")
    
    # Recent incidents table
    st.subheader("📋 Recent Incidents")
    
    if not incidents_data.empty:
        # Show most recent 10 incidents
        recent_data = incidents_data.nlargest(10, 'timestamp')[
            ['timestamp', 'location', 'description', 'severity']
        ].copy()
        
        # Format timestamp for display
        recent_data['Time'] = recent_data['timestamp'].dt.strftime('%H:%M')
        recent_data = recent_data.drop('timestamp', axis=1)
        recent_data = recent_data.rename(columns={
            'location': 'Location',
            'description': 'Description', 
            'severity': 'Severity'
        })
        
        # Add severity color coding
        def severity_color(val):
            if val >= 4:
                return 'background-color: #ffebee'  # Light red
            elif val >= 3:
                return 'background-color: #fff3e0'  # Light orange
            else:
                return 'background-color: #e8f5e8'  # Light green
        
        styled_df = recent_data.style.applymap(severity_color, subset=['Severity'])
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
    
    # Live demo controls (if presenter mode active)
    try:
        from utils.presenter_mode import is_presenter_mode
        
        if is_presenter_mode():
            st.subheader("🎮 Live Demo Controls")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🔄 Refresh All Data", use_container_width=True):
                    st.cache_data.clear()
                    st.success("Data refreshed!")
                    st.rerun()
            
            with col2:
                if st.button("➕ Add Random Incident", use_container_width=True):
                    try:
                        from pages.demo_controls import generate_demo_traffic_data
                        generate_demo_traffic_data()
                        st.success("Random incident added!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error adding incident: {e}")
            
            with col3:
                if st.button("🧹 Clear Demo Data", use_container_width=True):
                    try:
                        from pages.demo_controls import clear_demo_data
                        clear_demo_data()
                        st.success("Demo data cleared!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error clearing data: {e}")
    
    except ImportError:
        pass  # Presenter mode not available
    
    # Footer with demo information
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**🎯 Demo Mode Active**")
        st.caption("This is a demonstration environment")
    
    with col2:
        st.markdown("**🔄 Auto-Refresh**")
        st.caption("Data updates automatically every 30 seconds")
    
    with col3:
        st.markdown("**⏰ Last Updated**") 
        st.caption(datetime.now().strftime("%H:%M:%S"))
    
    # Auto-refresh the page
    st_autorefresh = None
    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=30000, key="demo_dashboard_refresh")  # 30 seconds
    except ImportError:
        pass  # Auto-refresh not available

if __name__ == "__main__":
    show()