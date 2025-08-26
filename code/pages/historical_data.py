#!/usr/bin/env python3
"""
Historical Data Analysis Page
Shows progress of real-time data collection and historical analysis capabilities
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json

# Import theme manager
try:
    from utils.theme_manager import apply_village_theme, create_village_header, get_village_colors
except ImportError:
    st.error("Theme manager not available")

# Import data utilities
try:
    from utils.data_retention_manager import get_retention_manager
    from utils.database import get_database
    RETENTION_AVAILABLE = True
except ImportError:
    RETENTION_AVAILABLE = False
    st.error("Data retention manager not available")

def show():
    """Display the Historical Data Analysis page"""
    
    # Apply Village theme
    apply_village_theme()
    
    # Display header
    create_village_header(
        "Historical Data Analysis",
        "Building Rhode Island's traffic incident historical database through real-time collection"
    )
    
    if not RETENTION_AVAILABLE:
        st.error("Historical data management components not available")
        return
    
    # Get data managers
    retention_manager = get_retention_manager()
    db = get_database()
    
    # Get historical summary
    with st.spinner("Analyzing historical data collection..."):
        summary = retention_manager.get_historical_summary()
    
    # Display overview metrics
    st.subheader("📊 Collection Progress Overview")
    
    if 'total_incidents' in summary and summary['total_incidents'] > 0:
        # Data is available - show metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Real Incidents",
                f"{summary['total_incidents']:,}",
                help="Real traffic incidents collected from TomTom API"
            )
        
        with col2:
            st.metric(
                "Collection Days",
                summary['unique_collection_days'],
                help="Number of days with incident data"
            )
        
        with col3:
            st.metric(
                "Daily Average",
                f"{summary['daily_average']:.1f}",
                help="Average incidents per day"
            )
        
        with col4:
            st.metric(
                "Collection Rate",
                f"{summary['collection_rate_percent']}%",
                help="Percentage of days with successful data collection"
            )
        
        # Data quality indicator
        if summary['collection_rate_percent'] >= 80:
            st.success("✅ Excellent data collection consistency")
        elif summary['collection_rate_percent'] >= 60:
            st.warning("⚠️ Good data collection with some gaps")
        else:
            st.info("🔄 Building collection consistency")
        
        # Timeline display
        st.subheader("📅 Collection Timeline")
        col1, col2 = st.columns(2)
        
        with col1:
            st.info(f"**First Incident:** {summary['first_incident_date']}")
        with col2:
            st.info(f"**Latest Incident:** {summary['latest_incident_date']}")
        
        # Data distribution analysis
        st.subheader("📈 Historical Data Analysis")
        
        # Severity distribution
        if summary['severity_distribution']:
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Incident Severity Distribution**")
                severity_df = pd.DataFrame(
                    list(summary['severity_distribution'].items()),
                    columns=['Severity', 'Count']
                )
                severity_df['Severity'] = severity_df['Severity'].map({
                    1: 'Minor', 2: 'Low', 3: 'Moderate', 4: 'High', 5: 'Critical'
                })
                
                fig = px.pie(
                    severity_df, 
                    values='Count', 
                    names='Severity',
                    color_discrete_sequence=get_village_colors()['palette']
                )
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.write("**Top Incident Locations**")
                if summary['top_locations']:
                    locations_df = pd.DataFrame(
                        summary['top_locations'],
                        columns=['Location', 'Incidents']
                    )
                    
                    fig = px.bar(
                        locations_df,
                        x='Incidents',
                        y='Location',
                        orientation='h',
                        color='Incidents',
                        color_continuous_scale='Blues'
                    )
                    fig.update_layout(height=300)
                    st.plotly_chart(fig, use_container_width=True)
        
        # Historical trends (if enough data)
        if summary['unique_collection_days'] >= 7:
            st.subheader("📊 Historical Trends")
            
            # Get daily incident counts
            try:
                daily_data = db.get_traffic_incidents()
                if not daily_data.empty:
                    daily_data['timestamp'] = pd.to_datetime(daily_data['timestamp'])
                    daily_data['date'] = daily_data['timestamp'].dt.date
                    
                    daily_counts = daily_data.groupby('date').size().reset_index(name='incidents')
                    daily_counts['date'] = pd.to_datetime(daily_counts['date'])
                    
                    fig = px.line(
                        daily_counts,
                        x='date',
                        y='incidents',
                        title='Daily Incident Count Trend',
                        labels={'incidents': 'Number of Incidents', 'date': 'Date'}
                    )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Show trend analysis
                    if len(daily_counts) >= 7:
                        recent_avg = daily_counts['incidents'].tail(7).mean()
                        overall_avg = daily_counts['incidents'].mean()
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric(
                                "Recent 7-Day Average",
                                f"{recent_avg:.1f}",
                                delta=f"{recent_avg - overall_avg:.1f} vs overall"
                            )
                        with col2:
                            st.metric(
                                "Overall Average",
                                f"{overall_avg:.1f}",
                                help="Average incidents per day across all data"
                            )
                            
            except Exception as e:
                st.error(f"Error generating trends: {e}")
    
    else:
        # No data yet - show getting started info
        st.warning("⏳ **Historical Data Collection Starting**")
        
        st.markdown("""
        🔄 **Real-Time Collection Active**: Your Village Platform is now collecting authentic Rhode Island traffic incidents.
        
        **Why No Historical Archives?**
        - TomTom Traffic API provides real-time data only (not historical archives)
        - Historical incident data is not available for past months/weeks
        - Your system builds its own historical dataset through continuous collection
        
        **Collection Progress:**
        """)
        
        # Show collection timeline projection
        projection = retention_manager.get_collection_timeline_projection()
        
        st.info("📅 **Expected Historical Data Timeline:**")
        
        timeline_data = [
            ("5-15 minutes", "First real incidents appear"),
            ("1 day", "Basic daily patterns visible"),
            ("1 week", "Weekly patterns and trends emerge"),
            ("1 month", "Reliable historical analysis available"),
            ("3 months", "Seasonal pattern detection"),
            ("6 months", "Comprehensive trend analysis"),
            ("1 year", "Full annual traffic cycle data")
        ]
        
        for timeframe, description in timeline_data:
            st.write(f"- **{timeframe}**: {description}")
    
    # Collection status and controls
    st.subheader("⚙️ Data Collection Management")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("**Current Status**")
        if summary.get('total_incidents', 0) > 0:
            st.success("🟢 Actively collecting data")
        else:
            st.info("🟡 Waiting for first incidents")
    
    with col2:
        st.write("**Retention Period**")
        st.info("365 days (1 year)")
        
    with col3:
        st.write("**Data Quality**")
        data_quality = summary.get('data_quality', 'Unknown')
        if data_quality == 'Real API Data':
            st.success("✅ Authentic API data")
        else:
            st.info("⏳ Waiting for real data")
    
    # Technical details
    with st.expander("🔍 Technical Implementation Details"):
        st.markdown("""
        **Data Collection Architecture:**
        - **Source**: TomTom Traffic Incidents API (real-time)
        - **Frequency**: Every 15 minutes
        - **Coverage**: 11 Rhode Island collection zones
        - **Storage**: SQLite database with `data_source = 'tomtom_api'`
        - **Retention**: 365 days with automatic archival
        
        **Why This Approach:**
        - ✅ Provides authentic local Rhode Island data
        - ✅ Builds institutional knowledge over time
        - ✅ More accurate than generic historical datasets
        - ✅ Demonstrates commitment to data-driven planning
        - ✅ Perfect for municipal planning needs
        
        **For RIHub Demo:**
        - Show live collection system in action
        - Explain long-term value proposition
        - Highlight real local data vs. synthetic data
        - Demonstrate platform's capability to build historical insights
        """)
    
    # Export options
    if summary.get('total_incidents', 0) > 0:
        st.subheader("📤 Export Historical Data")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 Download Summary Report"):
                summary_json = json.dumps(summary, indent=2, default=str)
                st.download_button(
                    "Download JSON Report",
                    summary_json,
                    f"village_historical_summary_{datetime.now().strftime('%Y%m%d')}.json",
                    "application/json"
                )
        
        with col2:
            if st.button("📋 Export Incident Data"):
                try:
                    incidents_df = db.get_traffic_incidents()
                    if not incidents_df.empty:
                        csv = incidents_df.to_csv(index=False)
                        st.download_button(
                            "Download CSV Data",
                            csv,
                            f"village_incidents_{datetime.now().strftime('%Y%m%d')}.csv",
                            "text/csv"
                        )
                    else:
                        st.warning("No incident data available for export")
                except Exception as e:
                    st.error(f"Error exporting data: {e}")

if __name__ == "__main__":
    show()