# pages/monitoring.py - System Monitoring and Data Collection Dashboard

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import datetime
import sys
from pathlib import Path
import json

# Add parent dir to path for imports
parent_dir = Path(__file__).parent.parent
sys.path.append(str(parent_dir))

try:
    from utils.database import get_database
    from utils.enhanced_traffic_collector import get_enhanced_collector
    from utils.column_utils import get_coordinate_columns, get_flexible_column_reference, COORDINATE_ALIASES
    DATABASE_UTILITIES_AVAILABLE = True
except ImportError as e:
    st.error(f"Database utilities not available: {e}")
    DATABASE_UTILITIES_AVAILABLE = False

# Import theme manager
try:
    from utils.theme_manager import apply_village_theme, create_village_header, get_village_colors
except ImportError:
    st.error("Theme manager not available")

def show():
    # Apply Village theme
    apply_village_theme()
    
    # Display header
    create_village_header(
        "System Monitoring & Data Collection",
        "Real-time monitoring of data collection, API usage, and database status"
    )
    
    # Check if database utilities are available
    if not DATABASE_UTILITIES_AVAILABLE:
        st.error("Monitoring utilities are not available. Please ensure database system is properly configured.")
        return
    
    # Init database and collector
    try:
        db = get_database()
        collector = get_enhanced_collector()
    except Exception as e:
        st.error(f"Error initializing monitoring systems: {e}")
        return
    
    # Control panel
    st.subheader("Collection Control Panel")
    
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        if st.button("Start Collection", type="primary"):
            try:
                # Enhanced collector doesn't have background start/stop - show info instead
                st.info("Enhanced collector runs automatically. Data collection is always active.")
                st.rerun()
            except Exception as e:
                st.error(f"Error starting collection: {e}")
    
    with col2:
        if st.button("Stop Collection"):
            try:
                # Enhanced collector doesn't have background start/stop - show info instead
                st.info("Enhanced collector runs automatically. Cannot manually stop collection.")
                st.rerun()
            except Exception as e:
                st.error(f"Error stopping collection: {e}")
    
    with col3:
        if st.button("Refresh"):
            st.rerun()
    
    # Get current status
    try:
        status = collector.get_collection_status()
        db_stats = db.get_database_stats()
        api_usage = db.get_daily_api_usage()
    except Exception as e:
        st.error(f"Error getting system status: {e}")
        return
    
    # Collection Status Overview
    st.subheader("Collection Status Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        status_color = "🟢" if status.get('is_running', False) else "🔴"
        st.metric(
            "Collection Status",
            f"{status_color} {'Running' if status.get('is_running', False) else 'Stopped'}"
        )
    
    with col2:
        st.metric(
            "API Requests Today",
            f"{status.get('requests_today', 0):,}",
            help="Number of API requests made today"
        )
    
    with col3:
        quota_percent = status.get('quota_usage_percent', 0)
        delta_color = "inverse" if quota_percent > 80 else "normal"
        st.metric(
            "Daily Quota Usage",
            f"{quota_percent:.1f}%",
            delta=f"{quota_percent:.1f}%" if quota_percent > 0 else None,
            delta_color=delta_color,
            help="Percentage of daily API quota used"
        )
    
    with col4:
        st.metric(
            "Total Records",
            f"{db_stats.get('traffic_incidents_count', 0):,}",
            help="Total traffic incidents in database"
        )
    
    # API Usage Chart
    st.subheader("📈 API Usage Trends")
    
    if api_usage.get('endpoints'):
        # Create API usage chart
        endpoint_data = []
        for endpoint, data in api_usage['endpoints'].items():
            endpoint_data.append({
                'endpoint': endpoint,
                'requests': data['total_requests'],
                'avg_response_time': data['avg_response_time_ms'],
                'errors': data['error_count']
            })
        
        if endpoint_data:
            endpoint_df = pd.DataFrame(endpoint_data)
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig_requests = px.bar(
                    endpoint_df,
                    x='endpoint',
                    y='requests',
                    title="API Requests by Endpoint",
                    color='requests',
                    color_continuous_scale='Blues'
                )
                fig_requests.update_layout(height=400)
                st.plotly_chart(fig_requests, use_container_width=True)
            
            with col2:
                fig_response = px.bar(
                    endpoint_df,
                    x='endpoint',
                    y='avg_response_time',
                    title="Average Response Time (ms)",
                    color='avg_response_time',
                    color_continuous_scale='Reds'
                )
                fig_response.update_layout(height=400)
                st.plotly_chart(fig_response, use_container_width=True)
    else:
        st.info("No API usage data available yet")
    
    # Collection Targets Status
    st.subheader("Collection Targets Status")
    
    if status.get('targets'):
        targets_data = []
        for target in status['targets']:
            targets_data.append({
                'Target': target['name'],
                'Priority': target['priority'],
                'Interval (min)': target['current_interval_minutes'],
                'Next Collection': target['minutes_until_next'],
                'Failures': target['consecutive_failures'],
                'Status': '⏰ Overdue' if target['is_overdue'] else '✅ On Schedule'
            })
        
        targets_df = pd.DataFrame(targets_data)
        
        # Color code the dataframe
        def highlight_status(val):
            if 'Overdue' in val:
                return 'background-color: #ffebee'
            elif 'On Schedule' in val:
                return 'background-color: #e8f5e8'
            return ''
        
        styled_df = targets_df.style.applymap(highlight_status, subset=['Status'])
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
        
        # Create timeline chart for next collections
        fig_timeline = px.bar(
            targets_df,
            x='Target',
            y='Next Collection',
            title="Minutes Until Next Collection",
            color='Priority',
            color_discrete_map={
                'CRITICAL': '#f44336',
                'HIGH': '#ff9800',
                'MEDIUM': '#2196f3',
                'LOW': '#4caf50'
            }
        )
        fig_timeline.update_layout(height=400)
        fig_timeline.update_xaxes(tickangle=45)
        st.plotly_chart(fig_timeline, use_container_width=True)
    
    # Database Statistics
    st.subheader("Database Statistics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Traffic Incidents",
            f"{db_stats.get('traffic_incidents_count', 0):,}",
            help="Total traffic incident records"
        )
    
    with col2:
        st.metric(
            "Traffic Flow Records",
            f"{db_stats.get('traffic_flow_count', 0):,}",
            help="Total traffic flow data points"
        )
    
    with col3:
        st.metric(
            "Database Size",
            f"{db_stats.get('database_size_mb', 0):.1f} MB",
            help="Total database file size"
        )
    
    # Data Range Information
    if db_stats.get('data_date_range'):
        date_range = db_stats['data_date_range']
        st.info(f"📅 **Data Range:** {date_range.get('earliest', 'N/A')} to {date_range.get('latest', 'N/A')}")
    
    # Recent Activity Log
    st.subheader("📋 Recent Activity Log")
    
    try:
        # Get recent incidents for activity feed
        recent_incidents = db.get_traffic_incidents(
            start_date=datetime.date.today() - datetime.timedelta(days=1)
        )
        
        if not recent_incidents.empty:
            # Show last 10 incidents
            recent_display = recent_incidents.head(10)[['timestamp', 'location', 'description', 'severity']]
            recent_display['timestamp'] = pd.to_datetime(recent_display['timestamp']).dt.strftime('%H:%M:%S')
            
            st.dataframe(
                recent_display,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No recent incident data available")
    
    except Exception as e:
        st.error(f"Error loading recent activity: {e}")
    
    # Data Quality Metrics
    st.subheader("✅ Data Quality Metrics")
    
    try:
        # Calculate basic data quality metrics
        all_incidents = db.get_traffic_incidents()
        
        if not all_incidents.empty:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                # Use utility function to get coordinate columns
                lat_col, lng_col = get_coordinate_columns(all_incidents)
                
                if lat_col and lng_col:
                    missing_coords = all_incidents[[lat_col, lng_col]].isnull().any(axis=1).sum()
                    missing_percent = (missing_coords / len(all_incidents)) * 100
                else:
                    missing_percent = 0.0  # No coordinate columns found
                
                st.metric(
                    "Missing Coordinates",
                    f"{missing_percent:.1f}%",
                    help="Percentage of records with missing location data"
                )
            
            with col2:
                missing_desc = all_incidents['description'].isnull().sum()
                missing_desc_percent = (missing_desc / len(all_incidents)) * 100
                st.metric(
                    "Missing Descriptions",
                    f"{missing_desc_percent:.1f}%",
                    help="Percentage of records with missing descriptions"
                )
            
            with col3:
                # Check for reasonable severity values (1-5)
                invalid_severity = all_incidents[(all_incidents['severity'] < 1) | (all_incidents['severity'] > 5)].shape[0]
                invalid_severity_percent = (invalid_severity / len(all_incidents)) * 100
                st.metric(
                    "Invalid Severity",
                    f"{invalid_severity_percent:.1f}%",
                    help="Percentage of records with invalid severity values"
                )
            
            with col4:
                # Check for duplicate records using utility function
                lat_col, lng_col = get_coordinate_columns(all_incidents)
                
                if lat_col and lng_col and 'timestamp' in all_incidents.columns:
                    duplicates = all_incidents.duplicated([lat_col, lng_col, 'timestamp']).sum()
                    duplicate_percent = (duplicates / len(all_incidents)) * 100
                else:
                    duplicate_percent = 0.0  # Can't check duplicates without required columns
                
                st.metric(
                    "Potential Duplicates",
                    f"{duplicate_percent:.1f}%",
                    help="Percentage of potentially duplicate records"
                )
    
    except Exception as e:
        st.error(f"Error calculating data quality metrics: {e}")
    
    # System Configuration
    with st.expander("⚙️ System Configuration"):
        st.subheader("Collection Configuration")
        
        config_data = {
            "Daily API Quota": f"{status.get('daily_quota', 50000):,} requests",
            "Collection Targets": len(status.get('targets', [])),
            "Auto Refresh": "15 minutes",
            "Database Path": "data/traffic_data.db",
            "Peak Hours": "7-9 AM, 4-6 PM",
            "Weekend Multiplier": "1.5x slower collection"
        }
        
        for key, value in config_data.items():
            st.text(f"**{key}:** {value}")
    
    # Export Options
    st.subheader("📤 Export Options")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Export Status Report"):
            # Create comprehensive status report
            report_data = {
                'timestamp': datetime.datetime.now().isoformat(),
                'collection_status': status,
                'database_stats': db_stats,
                'api_usage': api_usage
            }
            
            report_json = json.dumps(report_data, indent=2, default=str)
            st.download_button(
                "Download Status Report (JSON)",
                report_json,
                f"traffic_system_status_{datetime.date.today()}.json",
                "application/json"
            )
    
    with col2:
        if st.button("📋 Export Target Status"):
            if status.get('targets'):
                targets_df = pd.DataFrame(status['targets'])
                csv = targets_df.to_csv(index=False)
                st.download_button(
                    "Download Target Status (CSV)",
                    csv,
                    f"collection_targets_{datetime.date.today()}.csv",
                    "text/csv"
                )
    
    with col3:
        if st.button("📈 Export API Usage"):
            if api_usage.get('endpoints'):
                usage_df = pd.DataFrame(api_usage['endpoints']).T
                csv = usage_df.to_csv()
                st.download_button(
                    "Download API Usage (CSV)",
                    csv,
                    f"api_usage_{datetime.date.today()}.csv",
                    "text/csv"
                )

if __name__ == "__main__":
    show()