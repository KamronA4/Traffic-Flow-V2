# pages/demo_controls.py - Demo Control Panel for Presenters

import streamlit as st
import os
import sys
import subprocess
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3
import pandas as pd

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
sys.path.append(str(parent_dir))

# Configure logging
logger = logging.getLogger(__name__)

def show():
    """Display the demo control panel"""
    
    # Check if demo mode is enabled
    demo_mode = os.getenv('VILLAGE_DEMO_MODE', 'false').lower() == 'true'
    
    if not demo_mode:
        st.warning("🔒 Demo Controls are only available when VILLAGE_DEMO_MODE=true")
        st.info("Set the environment variable and restart the application to access demo features.")
        return
    
    st.title("🎮 Demo Control Panel")
    st.caption("Presenter tools and demo management for Village Platform")
    
    # Demo Status Overview
    st.subheader("📊 Demo Status Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Demo Mode", "Active", "✅")
    
    with col2:
        api_key_available = bool(os.getenv('TOMTOM_API_KEY'))
        st.metric("API Status", "Connected" if api_key_available else "Fallback", 
                 "🔗" if api_key_available else "🔄")
    
    with col3:
        # Check database status
        db_path = Path(__file__).parent.parent / "data" / "traffic_data.db"
        db_exists = db_path.exists()
        st.metric("Database", "Ready" if db_exists else "Initializing", 
                 "💾" if db_exists else "⏳")
    
    with col4:
        # Check collector status (simplified)
        st.metric("Collector", "Demo Mode", "🚀")
    
    # Quick Demo Actions
    st.subheader("⚡ Quick Demo Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🎯 Generate Demo Data", use_container_width=True):
            with st.spinner("Generating realistic demo traffic data..."):
                generate_demo_traffic_data()
            st.success("Demo traffic data generated successfully!")
            st.rerun()
    
    with col2:
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.success("All cached data refreshed!")
            st.rerun()
    
    with col3:
        if st.button("🧹 Clear Demo Data", use_container_width=True):
            if st.session_state.get('confirm_clear', False):
                clear_demo_data()
                st.success("Demo data cleared!")
                st.session_state.confirm_clear = False
                st.rerun()
            else:
                st.session_state.confirm_clear = True
                st.warning("Click again to confirm data clearing")
    
    # Data Control Panel
    st.subheader("📊 Data Control Panel")
    
    # Traffic incident controls
    with st.expander("🚨 Traffic Incident Controls", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            incident_type = st.selectbox(
                "Incident Type",
                ["accident", "roadwork", "congestion", "weather", "closure"],
                help="Type of incident to simulate"
            )
            
            severity = st.slider(
                "Severity Level",
                min_value=1, max_value=5, value=3,
                help="1=Minor, 5=Critical"
            )
        
        with col2:
            location = st.selectbox(
                "Location",
                ["I-95 Providence", "Downtown Providence", "Route 195", "Newport Bridge", "Custom"],
                help="Predefined locations for incidents"
            )
            
            duration_hours = st.slider(
                "Duration (hours)",
                min_value=0.5, max_value=8.0, value=2.0, step=0.5,
                help="How long the incident should last"
            )
        
        if st.button("➕ Add Custom Incident", use_container_width=True):
            add_custom_incident(incident_type, severity, location, duration_hours)
            st.success(f"Added {incident_type} incident at {location}")
    
    # Real-time demo controls
    with st.expander("⏱️ Real-Time Demo Controls"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Time Simulation:**")
            time_mode = st.radio(
                "Demo Time Mode",
                ["Real Time", "Accelerated (2x)", "Accelerated (5x)", "Static"],
                help="Control how time progresses in the demo"
            )
            
            if time_mode != "Real Time":
                st.info(f"Demo running in {time_mode} mode")
        
        with col2:
            st.markdown("**Data Refresh:**")
            auto_refresh = st.checkbox("Auto-refresh enabled", value=True)
            
            if auto_refresh:
                refresh_interval = st.selectbox(
                    "Refresh interval",
                    ["30 seconds", "1 minute", "5 minutes", "15 minutes"],
                    index=2
                )
                st.info(f"Auto-refreshing every {refresh_interval}")
    
    # Scenario Presets
    st.subheader("🎬 Demo Scenarios")
    
    scenarios = {
        "Morning Rush Hour": {
            "description": "Heavy traffic with multiple incidents during morning commute",
            "incidents": 5,
            "congestion": "high",
            "locations": ["I-95", "Route 195", "Downtown"]
        },
        "Construction Zone": {
            "description": "Major roadwork causing traffic diversions",
            "incidents": 2,
            "congestion": "moderate",
            "locations": ["I-95 Providence"]
        },
        "Weather Event": {
            "description": "Severe weather causing multiple weather-related incidents",
            "incidents": 7,
            "congestion": "severe",
            "locations": ["Multiple"]
        },
        "Normal Operations": {
            "description": "Typical traffic flow with minimal incidents",
            "incidents": 1,
            "congestion": "low",
            "locations": ["Random"]
        }
    }
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        selected_scenario = st.selectbox(
            "Select Demo Scenario",
            list(scenarios.keys()),
            help="Pre-configured scenarios for different demo purposes"
        )
        
        scenario = scenarios[selected_scenario]
        st.info(f"**{selected_scenario}:** {scenario['description']}")
        
        st.write(f"• **Incidents:** {scenario['incidents']}")
        st.write(f"• **Congestion Level:** {scenario['congestion'].title()}")
        st.write(f"• **Affected Areas:** {', '.join(scenario['locations'])}")
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # Spacing
        if st.button("🎬 Load Scenario", use_container_width=True):
            load_demo_scenario(selected_scenario, scenario)
            st.success(f"Loaded '{selected_scenario}' scenario!")
            st.rerun()
    
    # Current Data Preview
    st.subheader("👀 Current Data Preview")
    
    try:
        # Get current incident data
        from utils.data_sync import get_traffic_data
        current_data = get_traffic_data()
        
        if not current_data.empty:
            # Show summary statistics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Incidents", len(current_data))
            
            with col2:
                high_severity = len(current_data[current_data['severity'] > 3])
                st.metric("High Severity", high_severity)
            
            with col3:
                unique_locations = current_data['location'].nunique()
                st.metric("Affected Areas", unique_locations)
            
            # Show recent incidents
            st.markdown("**Recent Incidents:**")
            recent_data = current_data.head(5)[['location', 'description', 'severity', 'timestamp']]
            recent_data['timestamp'] = pd.to_datetime(recent_data['timestamp']).dt.strftime('%H:%M')
            st.dataframe(recent_data, use_container_width=True, hide_index=True)
            
        else:
            st.info("No current traffic data available. Use 'Generate Demo Data' to create sample data.")
    
    except Exception as e:
        st.error(f"Error loading current data: {e}")
    
    # Presenter Notes
    st.subheader("📝 Presenter Notes")
    
    with st.expander("Demo Tips and Talking Points"):
        st.markdown("""
        **Key Demo Points:**
        - Village provides real-time traffic monitoring for municipal planners
        - AI-powered incident analysis helps with decision-making
        - Interactive maps allow detailed incident investigation
        - Role-based access ensures appropriate data visibility
        
        **Demo Flow Suggestions:**
        1. Start with "Normal Operations" scenario
        2. Show live traffic monitoring and map interaction
        3. Demonstrate AI analysis features
        4. Switch to "Morning Rush Hour" to show high-activity periods
        5. Highlight planning insights and reporting capabilities
        
        **Common Questions & Responses:**
        - **Data Sources:** TomTom Traffic API, real-time incident feeds
        - **Update Frequency:** Every 15 minutes for live data
        - **Coverage Area:** Currently focused on Rhode Island
        - **AI Analysis:** Powered by Perplexity for real-time insights
        """)
    
    # Technical Info for Troubleshooting
    with st.expander("🔧 Technical Information"):
        st.markdown("**Environment Variables:**")
        env_vars = {
            'VILLAGE_DEMO_MODE': os.getenv('VILLAGE_DEMO_MODE', 'Not Set'),
            'TOMTOM_API_KEY': 'Available' if os.getenv('TOMTOM_API_KEY') else 'Not Set',
            'PERPLEXITY_API_KEY': 'Available' if os.getenv('PERPLEXITY_API_KEY') else 'Not Set',
            'VILLAGE_DEMO_SAFE_MODE': os.getenv('VILLAGE_DEMO_SAFE_MODE', 'Not Set')
        }
        
        for key, value in env_vars.items():
            st.text(f"{key}: {value}")
        
        st.markdown("**System Status:**")
        st.text(f"Python Version: {sys.version}")
        st.text(f"Streamlit Version: {st.__version__}")
        st.text(f"Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def generate_demo_traffic_data():
    """Generate realistic demo traffic data"""
    try:
        from utils.database import get_database
        import random
        import uuid
        
        db = get_database()
        
        # Generate 10-15 realistic incidents
        incident_types = [
            {"type": "accident", "desc": "Multi-vehicle accident", "severity": 4},
            {"type": "roadwork", "desc": "Lane closure for maintenance", "severity": 2},
            {"type": "congestion", "desc": "Heavy traffic congestion", "severity": 3},
            {"type": "weather", "desc": "Weather-related slow traffic", "severity": 2},
            {"type": "closure", "desc": "Road closure due to emergency", "severity": 5},
        ]
        
        locations = [
            {"name": "I-95 Providence Corridor", "lat": 41.82, "lng": -71.42},
            {"name": "Route 195 Eastbound", "lat": 41.80, "lng": -71.40},
            {"name": "Downtown Providence", "lat": 41.824, "lng": -71.419},
            {"name": "Newport Bridge Area", "lat": 41.50, "lng": -71.32},
            {"name": "Warwick Mall Area", "lat": 41.73, "lng": -71.45},
        ]
        
        # Generate incidents
        for i in range(random.randint(10, 15)):
            incident_type = random.choice(incident_types)
            location = random.choice(locations)
            
            # Add some randomness to coordinates
            lat_offset = random.uniform(-0.01, 0.01)
            lng_offset = random.uniform(-0.01, 0.01)
            
            incident_data = {
                'external_id': f"demo_{uuid.uuid4().hex[:8]}",
                'timestamp': datetime.now() - timedelta(minutes=random.randint(0, 180)),
                'latitude': location['lat'] + lat_offset,
                'longitude': location['lng'] + lng_offset,
                'location': location['name'],
                'description': incident_type['desc'],
                'severity': incident_type['severity'],
                'type': 1,
                'Length_of_Time(Hours)': random.uniform(0.5, 4.0),
                'data_source': 'demo_generator'
            }
            
            db.insert_traffic_incident(incident_data)
        
        logger.info("Generated demo traffic data successfully")
        
    except Exception as e:
        logger.error(f"Error generating demo data: {e}")
        raise

def clear_demo_data():
    """Clear all demo-generated data"""
    try:
        from utils.database import get_database
        
        db = get_database()
        
        # Clear demo data only
        import sqlite3
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM traffic_incidents WHERE data_source = 'demo_generator'")
            deleted_count = cursor.rowcount
            conn.commit()
        
        logger.info(f"Cleared {deleted_count} demo incidents")
        
    except Exception as e:
        logger.error(f"Error clearing demo data: {e}")
        raise

def add_custom_incident(incident_type: str, severity: int, location: str, duration_hours: float):
    """Add a custom incident for demo purposes"""
    try:
        from utils.database import get_database
        import uuid
        
        # Location coordinates mapping
        location_coords = {
            "I-95 Providence": {"lat": 41.82, "lng": -71.42},
            "Downtown Providence": {"lat": 41.824, "lng": -71.419},
            "Route 195": {"lat": 41.80, "lng": -71.40},
            "Newport Bridge": {"lat": 41.50, "lng": -71.32},
            "Custom": {"lat": 41.83, "lng": -71.41}  # Default custom location
        }
        
        coords = location_coords.get(location, location_coords["Custom"])
        
        db = get_database()
        
        incident_data = {
            'external_id': f"custom_{uuid.uuid4().hex[:8]}",
            'timestamp': datetime.now(),
            'latitude': coords['lat'],
            'longitude': coords['lng'],
            'location': location,
            'description': f"Custom {incident_type} incident",
            'severity': severity,
            'type': 1,
            'Length_of_Time(Hours)': duration_hours,
            'data_source': 'demo_custom'
        }
        
        db.insert_traffic_incident(incident_data)
        logger.info(f"Added custom incident: {incident_type} at {location}")
        
    except Exception as e:
        logger.error(f"Error adding custom incident: {e}")
        raise

def load_demo_scenario(scenario_name: str, scenario_config: dict):
    """Load a predefined demo scenario"""
    try:
        # Clear existing demo data first
        clear_demo_data()
        
        # Generate scenario-specific data
        from utils.database import get_database
        import random
        import uuid
        
        db = get_database()
        
        # Scenario-specific incident generation
        if scenario_name == "Morning Rush Hour":
            # Generate multiple incidents during rush hour
            for i in range(scenario_config['incidents']):
                incident_data = {
                    'external_id': f"rush_{uuid.uuid4().hex[:8]}",
                    'timestamp': datetime.now().replace(hour=8, minute=random.randint(0, 59)),
                    'latitude': 41.82 + random.uniform(-0.05, 0.05),
                    'longitude': -71.42 + random.uniform(-0.05, 0.05),
                    'location': random.choice(scenario_config['locations']),
                    'description': f"Rush hour traffic incident #{i+1}",
                    'severity': random.randint(2, 4),
                    'type': 1,
                    'Length_of_Time(Hours)': random.uniform(1.0, 3.0),
                    'data_source': f'scenario_{scenario_name.lower().replace(" ", "_")}'
                }
                db.insert_traffic_incident(incident_data)
        
        elif scenario_name == "Weather Event":
            # Generate weather-related incidents
            for i in range(scenario_config['incidents']):
                incident_data = {
                    'external_id': f"weather_{uuid.uuid4().hex[:8]}",
                    'timestamp': datetime.now() - timedelta(minutes=random.randint(0, 120)),
                    'latitude': 41.82 + random.uniform(-0.1, 0.1),
                    'longitude': -71.42 + random.uniform(-0.1, 0.1),
                    'location': f"Weather Zone {i+1}",
                    'description': f"Weather-related incident: {random.choice(['Heavy rain', 'Fog', 'Ice', 'Snow'])}",
                    'severity': random.randint(3, 5),
                    'type': 1,
                    'Length_of_Time(Hours)': random.uniform(2.0, 6.0),
                    'data_source': f'scenario_{scenario_name.lower().replace(" ", "_")}'
                }
                db.insert_traffic_incident(incident_data)
        
        # Add more scenario types as needed
        else:
            # Generic scenario generation
            for i in range(scenario_config['incidents']):
                incident_data = {
                    'external_id': f"scenario_{uuid.uuid4().hex[:8]}",
                    'timestamp': datetime.now() - timedelta(minutes=random.randint(0, 180)),
                    'latitude': 41.82 + random.uniform(-0.05, 0.05),
                    'longitude': -71.42 + random.uniform(-0.05, 0.05),
                    'location': random.choice(scenario_config['locations']) if scenario_config['locations'] != ['Random'] else "General Area",
                    'description': f"Scenario incident #{i+1}",
                    'severity': random.randint(1, 3) if scenario_config['congestion'] == 'low' else random.randint(2, 5),
                    'type': 1,
                    'Length_of_Time(Hours)': random.uniform(0.5, 2.0),
                    'data_source': f'scenario_{scenario_name.lower().replace(" ", "_")}'
                }
                db.insert_traffic_incident(incident_data)
        
        logger.info(f"Loaded scenario: {scenario_name}")
        
    except Exception as e:
        logger.error(f"Error loading scenario: {e}")
        raise

if __name__ == "__main__":
    show()