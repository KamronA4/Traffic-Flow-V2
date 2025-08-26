# pages/live_traffic.py - Live Traffic Monitoring Module

import streamlit as st
import folium
from streamlit_folium import st_folium
from streamlit_autorefresh import st_autorefresh
import datetime
import pandas as pd
import os
import sys
import logging
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
sys.path.append(str(parent_dir))

# Import database utilities
try:
    from utils.database import get_database
    from utils.data_sync import get_traffic_data, get_traffic_flow_data
    DATABASE_AVAILABLE = True
except ImportError as e:
    DATABASE_AVAILABLE = False
    st.error("**System Configuration Required**")
    st.info("The traffic monitoring system is currently being configured. Please check back in a few moments.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Retry Connection"):
            st.rerun()
    with col2:
        if st.button("Contact Support"):
            st.info("Please contact your system administrator for assistance.")
    
    with st.expander("Technical Details", expanded=False):
        st.code(f"Import error: {e}")
        st.markdown("""
        **Possible solutions:**
        1. Ensure all required packages are installed: `pip install -r requirements.txt`
        2. Check that the database file exists and is accessible
        3. Verify all utility modules are present in the utils/ directory
        """)
    st.stop()

# Import interactive tables utility
try:
    from utils.interactive_tables import (
        create_interactive_dataframe,
        create_professional_table_layout,
        TRAFFIC_INCIDENT_METRICS
    )
    INTERACTIVE_TABLES_AVAILABLE = True
except ImportError:
    INTERACTIVE_TABLES_AVAILABLE = False

# Import AI analyzer utility
try:
    from utils.enhanced_ai_analyzer import (
        EnhancedTrafficAnalyzer,
        AnalysisType,
        get_enhanced_analysis,
        display_enhanced_analysis,
        create_enhanced_analysis_interface
    )
    from utils.ai_analyzer import (
        TrafficAnalyzer,
        get_cached_analysis,
        display_analysis_popup,
        create_enhanced_popup_html
    )
    AI_ANALYZER_AVAILABLE = True
    ENHANCED_AI_AVAILABLE = True
except ImportError:
    AI_ANALYZER_AVAILABLE = False
    ENHANCED_AI_AVAILABLE = False

# Import theme manager with graceful fallback
try:
    from utils.theme_manager import apply_village_theme, create_village_header
    THEME_MANAGER_AVAILABLE = True
except ImportError as e:
    THEME_MANAGER_AVAILABLE = False
    logger.warning(f"Theme manager not available: {e}")
    
    # Fallback theme functions
    def apply_village_theme():
        """Fallback theme - basic styling"""
        st.markdown("""
        <style>
        .stApp { 
            background-color: #f5f1e8; 
        }
        .stButton > button {
            background-color: #2d5016 !important;
            color: white !important;
            border-radius: 8px !important;
        }
        </style>
        """, unsafe_allow_html=True)
    
    def create_village_header(title: str, subtitle: str = ""):
        """Fallback header - simple styling"""
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #2d5016 0%, #5a7c47 100%); 
                    color: white; padding: 2rem; border-radius: 15px; 
                    text-align: center; margin-bottom: 2rem;">
            <h1 style="color: white; margin: 0; font-size: 2.8rem;">{title}</h1>
            {f'<p style="color: #f5f1e8; margin: 0.5rem 0 0 0; font-size: 1.2rem;">{subtitle}</p>' if subtitle else ""}
        </div>
        """, unsafe_allow_html=True)

def show():
    """Display the Live Traffic Monitoring page"""
    
    # Apply Village theme with error handling
    try:
        apply_village_theme()
    except Exception as e:
        logger.error(f"Error applying Village theme: {e}")
        # Continue without theme - functionality is more important than styling
    
    # Display header with error handling
    try:
        create_village_header(
            "Live Traffic Monitoring",
            "Real-time traffic incidents and flow analysis for Rhode Island municipalities"
        )
    except Exception as e:
        logger.error(f"Error creating Village header: {e}")
        # Fallback to simple header
        st.title("Live Traffic Monitoring")
        st.caption("Real-time traffic incidents and flow analysis for Rhode Island municipalities")
    
    # Auto-refresh for live data
    st_autorefresh(interval=15 * 60 * 1000, key="traffic_refresh")  # 15 minutes
    
    # Control panel
    with st.container():
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            # Get available date range from real data
            try:
                from utils.database import get_database
                db = get_database()
                all_data = db.get_traffic_incidents()
                
                if not all_data.empty:
                    all_data['timestamp'] = pd.to_datetime(all_data['timestamp'])
                    min_date = all_data['timestamp'].dt.date.min()
                    max_date = all_data['timestamp'].dt.date.max()
                    default_date = max_date  # Most recent data
                    date_help = f"Real data available: {min_date} to {max_date}"
                else:
                    min_date = datetime.date.today() - datetime.timedelta(days=1)
                    max_date = datetime.date.today()
                    default_date = datetime.date.today()
                    date_help = "⏳ Waiting for real API data collection"
                    
            except Exception:
                min_date = datetime.date.today() - datetime.timedelta(days=7)
                max_date = datetime.date.today()
                default_date = datetime.date.today()
                date_help = "Select date to view traffic data"
            
            # Date filter with dynamic range
            selected_date = st.date_input(
                "Date",
                value=default_date,
                min_value=min_date,
                max_value=max_date,
                help=date_help
            )
        
        with col2:
            # Time filter
            selected_hour = st.slider(
                "Hour (24H)",
                min_value=0,
                max_value=23,
                value=datetime.datetime.now().hour,
                help="Filter incidents by hour of day"
            )
        
        with col3:
            # Refresh button
            if st.button("Refresh", help="Manually refresh traffic data"):
                st.rerun()
    
    # Load and filter traffic data (database-first approach)
    try:
        # Get data from database through data sync
        incidents_df = get_traffic_data(
            start_date=selected_date,
            end_date=selected_date
        )
        
        if incidents_df.empty:
            st.info(f"No real traffic incidents found for {selected_date}")
            
            # Check if this is because no data exists at all vs. no data for selected date
            try:
                all_incidents = get_traffic_data()  # Get all data
                if all_incidents.empty:
                    st.info("**Live Traffic Data Loading**")
                    st.markdown("""
                    The Village platform is currently connecting to live traffic monitoring systems for Rhode Island.
                    
                    **Current Status:**
                    - Connecting to TomTom Traffic API
                    - Monitoring 11 key Rhode Island traffic zones
                    - Real-time data will appear as incidents occur
                    
                    **Expected Timeline:**
                    - **Next 5-15 minutes**: Initial traffic data
                    - **Within 1-2 hours**: Comprehensive Rhode Island coverage
                    - **Ongoing**: Automatic updates every 15 minutes
                    """)
                    
                    # Add demo data option for presentations
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("**Load Demo Data**", use_container_width=True):
                            st.session_state['demo_mode'] = True
                            st.info("Demo mode activated - using sample traffic data for presentation.")
                            st.rerun()
                    
                    with col2:
                        if st.button("**Check for New Data**", use_container_width=True):
                            st.cache_data.clear()
                            st.rerun()
                    
                    # Show collection status in collapsible section
                    with st.expander("System Information", expanded=False):
                        st.markdown("""
                        **Data Collection Zones:**
                        - I-95 Providence Corridor (Priority 1)
                        - Downtown Providence (Priority 1) 
                        - Route 195 East-West (Priority 2)
                        - Newport Tourist Area (Priority 2)
                        - 7 additional monitoring zones
                        
                        **Update Frequency:** Every 15 minutes during peak hours
                        **Data Source:** TomTom Traffic API
                        """)
                else:
                    # Data exists but not for selected date
                    available_dates = pd.to_datetime(all_incidents['timestamp']).dt.date.unique()
                    st.info(f"**Real data available for {len(available_dates)} other dates**")
                    st.write("**Available dates with real incidents:**")
                    for date in sorted(available_dates)[-10:]:  # Show last 10 dates
                        incident_count = len(all_incidents[pd.to_datetime(all_incidents['timestamp']).dt.date == date])
                        st.write(f"- {date}: {incident_count} incidents")
                    
            except Exception as e:
                st.error(f"Error checking data availability: {e}")
            
            return
        
        # Process timestamp and filter by hour
        incidents_df['timestamp'] = pd.to_datetime(incidents_df['timestamp'])
        incidents_df['date'] = incidents_df['timestamp'].dt.date
        incidents_df['hour'] = incidents_df['timestamp'].dt.hour
        
        # Apply hour filter
        filtered_incidents = incidents_df[incidents_df['hour'] == selected_hour]
        
        # Also get traffic flow data
        flow_df = get_traffic_flow_data(
            start_date=selected_date,
            end_date=selected_date
        )
        
        # Filter flow data by hour if not empty
        if not flow_df.empty:
            flow_df['timestamp'] = pd.to_datetime(flow_df['timestamp'])
            flow_df['hour'] = flow_df['timestamp'].dt.hour
            filtered_flow = flow_df[flow_df['hour'] == selected_hour]
        else:
            filtered_flow = pd.DataFrame()
        
        if filtered_incidents.empty and filtered_flow.empty:
            st.info(f"No traffic data found for {selected_date} at {selected_hour}:00")
            # Show available hours for this date
            available_hours = sorted(incidents_df['hour'].unique())
            if available_hours:
                st.info(f"Available incident hours for {selected_date}: {', '.join(map(str, available_hours))}")
            if not flow_df.empty:
                flow_hours = sorted(flow_df['hour'].unique())
                if flow_hours:
                    st.info(f"Available flow data hours: {', '.join(map(str, flow_hours))}")
            return
        
    except Exception as e:
        st.error(f"Error loading traffic data: {e}")
        st.error("Please check that the database is properly configured and data collection is running.")
        return
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Incidents",
            len(filtered_incidents),
            delta=None,
            help="Number of active traffic incidents"
        )
    
    with col2:
        if not filtered_flow.empty:
            avg_congestion = filtered_flow['congestion_level'].mean()
            congestion_status = "Low" if avg_congestion < 2 else "Moderate" if avg_congestion < 3 else "High"
            st.metric(
                f"Avg Congestion ({congestion_status})",
                f"{avg_congestion:.1f}",
                delta=None,
                help="Average congestion level (1=free, 5=severe)"
            )
        else:
            high_severity = len(filtered_incidents[filtered_incidents['severity'] > 2]) if not filtered_incidents.empty else 0
            st.metric(
                "High Severity",
                high_severity,
                delta=None,
                help="Incidents with severity level > 2"
            )
    
    with col3:
        if not filtered_flow.empty:
            avg_speed = filtered_flow['current_speed_mph'].mean()
            st.metric(
                "Avg Speed",
                f"{avg_speed:.0f} mph" if not pd.isna(avg_speed) else "N/A",
                help="Average current traffic speed"
            )
        else:
            # Handle different column names for duration
            duration_col = 'length_hours' if 'length_hours' in filtered_incidents.columns else 'Length_of_Time(Hours)'
            avg_duration = filtered_incidents[duration_col].mean() if duration_col in filtered_incidents.columns and not filtered_incidents.empty else 0
            st.metric(
                "Avg Duration",
                f"{avg_duration:.1f}h" if not pd.isna(avg_duration) else "N/A",
                help="Average incident duration in hours"
            )
    
    with col4:
        if not filtered_flow.empty:
            flow_points = len(filtered_flow)
            st.metric(
                "Flow Sensors",
                flow_points,
                help="Number of traffic flow measurement points"
            )
        else:
            locations = filtered_incidents['location'].nunique() if not filtered_incidents.empty else 0
            st.metric(
                "Locations",
                locations,
                help="Number of unique locations with incidents"
            )
    
    # Map section
    st.subheader("Live Traffic Map")
    st.caption("Triangle markers = Traffic incidents (Red: High severity, Orange: Medium, Green: Low) | Circle markers = Traffic flow data (Green: Free flow, Yellow: Moderate congestion, Red: Heavy congestion)")
    
    # Town input for map centering
    col1, col2 = st.columns([3, 1])
    with col1:
        town = st.text_input(
            "Center on Town:",
            value="Providence",
            help="Enter a Rhode Island town name to center the map"
        )
    
    with col2:
        map_style = st.selectbox(
            "Map Style:",
            ["OpenStreetMap", "CartoDB positron", "CartoDB dark_matter"],
            help="Choose map visual style"
        )
    
    # Create and display map with error handling
    map_creation_success = False
    map_error_message = None
    
    try:
        # Default center coordinates (Providence)
        lat, lng = 41.8236, -71.4222
        
        # Try to center on selected town if it has incidents
        town_incidents = filtered_incidents[
            filtered_incidents['location'].str.lower() == town.lower()
        ]
        if not town_incidents.empty:
            lat = town_incidents.iloc[0]['latitude'] if 'latitude' in town_incidents.columns else town_incidents.iloc[0]['lat']
            lng = town_incidents.iloc[0]['longitude'] if 'longitude' in town_incidents.columns else town_incidents.iloc[0]['lng']
            st.success(f"Map centered on {town}")
        else:
            st.info(f"No incidents found for {town}. Showing Providence area.")
        
        # Create map with error handling
        tiles = {
            "OpenStreetMap": None,
            "CartoDB positron": "CartoDB positron",
            "CartoDB dark_matter": "CartoDB dark_matter"
        }
        
        try:
            m = folium.Map(
                location=[lat, lng],
                zoom_start=12,
                tiles=tiles[map_style]
            )
            map_creation_success = True
        except Exception as map_error:
            map_error_message = f"Map rendering failed: {str(map_error)}"
            logger.error(map_error_message)
            m = None
        
        # Add incident markers
        incident_lookup = {}
        for _, incident in filtered_incidents.iterrows():
            incident_id = f"{incident['location']}-{incident['timestamp'].strftime('%Y%m%d%H')}-{incident.name}"
            incident_lookup[incident_id] = incident.to_dict()
            
            # Create enhanced popup with AI preview
            if AI_ANALYZER_AVAILABLE:
                # Get cached analysis for popup preview
                incident_id = f"{incident['location']}-{incident['timestamp'].strftime('%Y%m%d%H')}-{incident.name}"
                cached_analysis = st.session_state.get(f"analysis_{incident_id}")
                popup_html = create_enhanced_popup_html(incident, cached_analysis)
            else:
                # Fallback popup
                popup_html = f"""
                <div style="background-color: rgba(255, 255, 255, 0.95); 
                            padding: 12px; border-radius: 8px; 
                            font-family: 'Segoe UI', sans-serif; 
                            font-size: 13px; max-width: 280px;
                            box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    <h4 style="margin: 0 0 8px 0; color: #1976d2; font-size: 14px;">
                        {incident['location']}
                    </h4>
                    <p style="margin: 0 0 8px 0; color: #333; line-height: 1.4;">
                        <strong>{incident['description']}</strong>
                    </p>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px;">
                        <span style="color: #666; font-size: 11px;">
                            Severity: {incident['severity']} | {incident['timestamp'].strftime('%H:%M')}
                        </span>
                    </div>
                    <div style="margin-top: 8px; padding: 6px; background: #e3f2fd; border-radius: 4px; text-align: center;">
                        <span style="color: #1976d2; font-size: 10px; font-weight: 500;">
                            Click marker for analysis
                        </span>
                    </div>
                </div>
                """
            
            popup = folium.Popup(popup_html, max_width=300)
            
            # Color coding by severity
            color = 'red' if incident['severity'] > 2 else 'orange' if incident['severity'] > 1 else 'green'
            
            # Handle both database and CSV column names
            lat_col = 'latitude' if 'latitude' in incident else 'lat'
            lng_col = 'longitude' if 'longitude' in incident else 'lng'
            
            folium.Marker(
                location=[incident[lat_col], incident[lng_col]],
                popup=popup,
                icon=folium.Icon(
                    color=color,
                    icon='exclamation-triangle' if incident['severity'] > 2 else 'warning-sign',
                    prefix='fa'
                ),
                tooltip=f"{incident['location']}: {incident['description'][:50]}..."
            ).add_to(m)
        
        # Add traffic flow markers
        for _, flow_point in filtered_flow.iterrows():
            # Color code by congestion level
            congestion = flow_point['congestion_level']
            if congestion <= 1:
                flow_color = 'green'
                flow_icon = 'play'
            elif congestion <= 2:
                flow_color = 'lightgreen'
                flow_icon = 'play'
            elif congestion <= 3:
                flow_color = 'orange'
                flow_icon = 'pause'
            else:
                flow_color = 'red'
                flow_icon = 'stop'
            
            # Create flow popup
            flow_popup_html = f"""
            <div style="background-color: rgba(255, 255, 255, 0.95); 
                        padding: 12px; border-radius: 8px; 
                        font-family: 'Segoe UI', sans-serif; 
                        font-size: 13px; max-width: 280px;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <h4 style="margin: 0 0 8px 0; color: #2e7d32; font-size: 14px;">
                    Traffic Flow Data
                </h4>
                <p style="margin: 0 0 8px 0; color: #333; line-height: 1.4;">
                    <strong>Speed:</strong> {flow_point['current_speed_mph']:.0f} mph<br>
                    <strong>Free Flow:</strong> {flow_point['free_flow_speed_mph']:.0f} mph<br>
                    <strong>Congestion:</strong> Level {flow_point['congestion_level']}/5<br>
                    <strong>Location:</strong> {flow_point.get('location', 'Unknown')}
                </p>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px;">
                    <span style="color: #666; font-size: 11px;">
                        {flow_point['timestamp'].strftime('%H:%M')}
                    </span>
                </div>
            </div>
            """
            
            folium.CircleMarker(
                location=[flow_point['latitude'], flow_point['longitude']],
                radius=8,
                popup=folium.Popup(flow_popup_html, max_width=300),
                color=flow_color,
                fill=True,
                fillColor=flow_color,
                fillOpacity=0.7,
                tooltip=f"Flow: {flow_point['current_speed_mph']:.0f} mph (Level {flow_point['congestion_level']})"
            ).add_to(m)
        
        # Display map with fallback handling
        if map_creation_success and m is not None:
            try:
                map_data = st_folium(m, width=700, height=500, returned_objects=["last_object_clicked"])
            except Exception as display_error:
                st.error("Map display encountered an issue. Data remains available in the table below.")
                map_data = None
                map_creation_success = False
                map_error_message = f"Map display failed: {str(display_error)}"
        else:
            map_data = None
        
        # Handle marker clicks for AI analysis
        if map_data and map_data.get("last_object_clicked"):
            clicked_obj = map_data["last_object_clicked"]
            if clicked_obj and "lat" in clicked_obj and "lng" in clicked_obj:
                clicked_lat = clicked_obj["lat"]
                clicked_lng = clicked_obj["lng"]
                
                # Find matching incident
                for incident_id, incident_data in incident_lookup.items():
                    # Handle both database and CSV column names
                    lat_key = 'latitude' if 'latitude' in incident_data else 'lat'
                    lng_key = 'longitude' if 'longitude' in incident_data else 'lng'
                    
                    if (abs(incident_data[lat_key] - clicked_lat) < 0.0001 and 
                        abs(incident_data[lng_key] - clicked_lng) < 0.0001):
                        
                        st.session_state["selected_incident"] = incident_data
                        st.session_state["incident_analysis"] = None  # Reset analysis
                        st.rerun()
                        break
        
    except Exception as e:
        map_error_message = f"Map system error: {str(e)}"
        logger.error(map_error_message)
        map_creation_success = False
    
    # Display fallback UI if map failed
    if not map_creation_success:
        st.warning("Map view is currently unavailable. Traffic data remains accessible below.")
        
        # Show fallback incident selection interface
        if not filtered_incidents.empty:
            st.subheader("Select Incident for Analysis")
            incident_options = {}
            for idx, incident in filtered_incidents.iterrows():
                key = f"{incident['location']} - {incident['description'][:50]}..."
                incident_options[key] = incident.to_dict()
            
            selected_key = st.selectbox(
                "Choose an incident to analyze:",
                options=list(incident_options.keys()),
                help="Select an incident to view detailed AI analysis"
            )
            
            if selected_key and st.button("Analyze Selected Incident"):
                st.session_state["selected_incident"] = incident_options[selected_key]
                st.session_state["incident_analysis"] = None
                st.rerun()
        
        # Technical details in expandable section for troubleshooting
        if map_error_message:
            with st.expander("Technical Information", expanded=False):
                st.code(map_error_message)
                st.markdown("""
                **Potential solutions:**
                - Refresh the page to retry map loading
                - Check internet connectivity for map tiles
                - Try a different map style from the dropdown above
                - Contact support if the issue persists
                """)
    
    # AI Analysis section
    if "selected_incident" in st.session_state:
        st.subheader("Enhanced AI Traffic Analysis")
        
        incident = st.session_state["selected_incident"]
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.info(f"**Selected:** {incident['location']} - {incident['description']}")
        
        with col2:
            if st.button("🔍 Analyze", key="analyze_incident"):
                with st.spinner('🔍 Performing comprehensive analysis...'):
                    st.session_state["show_analysis_options"] = True
                    st.rerun()
        
        # Show analysis options if requested
        if st.session_state.get("show_analysis_options", False):
            if ENHANCED_AI_AVAILABLE:
                # Use enhanced analysis interface
                selected_analyses, include_context = create_enhanced_analysis_interface()
                
                if st.button("🚀 Run Enhanced Analysis", key="run_enhanced_analysis"):
                    with st.spinner('🔍 Running comprehensive AI analysis...'):
                        try:
                            incident_id = f"{incident['location']}-{pd.to_datetime(incident['timestamp']).strftime('%Y%m%d%H')}"
                            
                            # Run enhanced analysis
                            analysis_result = get_enhanced_analysis(
                                incident_id,
                                incident,
                                selected_analyses,
                                include_context
                            )
                            
                            st.session_state["enhanced_analysis"] = analysis_result
                            st.session_state[f"analysis_{incident_id}"] = analysis_result  # Cache for popup
                            st.session_state["show_analysis_options"] = False
                        except Exception as e:
                            st.error(f"Enhanced analysis failed: {e}")
            else:
                # Fallback to basic analysis
                if st.button("Run Basic Analysis", key="run_basic_analysis"):
                    with st.spinner('🔍 Running basic analysis...'):
                        try:
                            if AI_ANALYZER_AVAILABLE:
                                # Use basic AI analysis
                                incident_id = f"{incident['location']}-{pd.to_datetime(incident['timestamp']).strftime('%Y%m%d%H')}"
                                analysis = get_cached_analysis(incident_id, incident)
                                st.session_state["incident_analysis"] = analysis
                                st.session_state[f"analysis_{incident_id}"] = analysis  # Cache for popup
                            else:
                                # Fallback mock analysis
                                analysis = {
                                    'summary': f"Traffic analysis for {incident['description']} in {incident['location']}. This is a mock analysis pending AI integration.",
                                    'planning_insights': "Municipal planning considerations include potential rerouting and resource allocation.",
                                    'related_articles': [],
                                    'error': False
                                }
                                st.session_state["incident_analysis"] = analysis
                            st.session_state["show_analysis_options"] = False
                        except Exception as e:
                            st.error(f"Analysis failed: {e}")
            
            # Cancel button
            if st.button("Cancel", key="cancel_analysis"):
                st.session_state["show_analysis_options"] = False
                st.rerun()
        
        # Display enhanced analysis if available
        if "enhanced_analysis" in st.session_state:
            analysis_result = st.session_state["enhanced_analysis"]
            
            if analysis_result and not analysis_result.get('error'):
                display_enhanced_analysis(analysis_result)
            else:
                st.error(f"Enhanced analysis error: {analysis_result.get('error', 'Unknown error')}")
        
        # Display basic analysis if available (fallback)
        elif "incident_analysis" in st.session_state:
            analysis = st.session_state["incident_analysis"]
            
            if not analysis.get('error'):
                if AI_ANALYZER_AVAILABLE:
                    # Use enhanced display function
                    display_analysis_popup(analysis, incident)
                else:
                    # Fallback display
                    with st.expander("Analysis Results", expanded=True):
                        st.markdown("**Current Situation:**")
                        st.write(analysis.get('summary', 'No summary available'))
                        
                        st.markdown("**Planning Insights:**")
                        st.write(analysis.get('planning_insights', 'No insights available'))
                        
                        if analysis.get('related_articles'):
                            st.markdown("**Related Information:**")
                            for article in analysis.get('related_articles', [])[:3]:
                                st.markdown(f"- [{article.get('title', 'Article')}]({article.get('url', '#')})")
            else:
                st.error(f"Analysis error: {analysis.get('summary', 'Unknown error')}")
        
        if st.button("Clear Selection"):
            st.session_state.pop("selected_incident", None)
            st.session_state.pop("incident_analysis", None)
            st.session_state.pop("enhanced_analysis", None)
            st.session_state.pop("show_analysis_options", None)
            st.rerun()
    
    # Incident summary table with interactive features
    st.subheader("Incident Summary")
    
    if not filtered_incidents.empty:
        # Display key columns (handle different column names)
        base_cols = ['location', 'description', 'severity', 'timestamp']
        duration_col = 'length_hours' if 'length_hours' in filtered_incidents.columns else 'Length_of_Time(Hours)'
        
        display_cols = base_cols.copy()
        if duration_col in filtered_incidents.columns:
            display_cols.append(duration_col)
        
        summary_df = filtered_incidents[display_cols].copy()
        
        # Format timestamp
        summary_df['timestamp'] = summary_df['timestamp'].dt.strftime('%H:%M')
        # Rename columns for display
        rename_dict = {
            'location': 'Location',
            'description': 'Description',
            'severity': 'Severity',
            'timestamp': 'Time'
        }
        
        if duration_col in summary_df.columns:
            rename_dict[duration_col] = 'Duration (hrs)'
        
        summary_df = summary_df.rename(columns=rename_dict)
        
        # Use interactive table if available
        if INTERACTIVE_TABLES_AVAILABLE:
            create_professional_table_layout(
                summary_df,
                title="Live Traffic Incidents",
                summary_metrics=[
                    {
                        'title': 'Active Incidents',
                        'value_func': lambda df: len(df),
                        'help': 'Total incidents for selected time'
                    },
                    {
                        'title': 'High Severity',
                        'value_func': lambda df: (df['Severity'] > 2).sum() if 'Severity' in df.columns else 0,
                        'help': 'Incidents with severity > 2'
                    },
                    {
                        'title': 'Avg Severity',
                        'value_func': lambda df: df['Severity'].mean() if 'Severity' in df.columns else 0,
                        'format': '{:.2f}',
                        'help': 'Average severity level'
                    },
                    {
                        'title': 'Locations Affected',
                        'value_func': lambda df: df['Location'].nunique() if 'Location' in df.columns else 0,
                        'help': 'Number of unique locations'
                    }
                ],
                search_columns=['Location', 'Description'],
                filter_columns=['Severity', 'Location'],
                export_formats=["CSV", "Excel"]
            )
        else:
            st.dataframe(
                summary_df,
                use_container_width=True,
                hide_index=True
            )
            
            # Export option fallback
            csv = summary_df.to_csv(index=False)
            st.download_button(
                "Download CSV",
                csv,
                f"traffic_incidents_{selected_date}_{selected_hour:02d}00.csv",
                "text/csv",
                help="Download filtered incident data as CSV"
            )
    else:
        st.info("No incidents to display for the selected filters")

if __name__ == "__main__":
    show()