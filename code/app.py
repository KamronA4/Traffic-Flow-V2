# app.py
# App file for streamlit deployment.

# Need: Mapfetcher.get_town_coords() -> https://www.here.com/docs/bundle/geocoding-and-search-api-developer-guide/page/topics-api/code-geocode-address.html

import streamlit as st
import folium
from streamlit_folium import st_folium
from streamlit_autorefresh import st_autorefresh
import datetime
import pandas as pd
import os
import requests
from streamlit_elements import elements, mui, html
from ai_providers import AIInsightProvider

# Load data
file_path = 'code/traffic_incidents.csv'
if os.path.exists(file_path):
    try:
        incidents = pd.read_csv(file_path)
        if incidents.empty or not {'timestamp', 'lat', 'lng', 'location', 'severity', 'description'}.issubset(incidents.columns):
            st.error("The CSV file is empty or missing required columns.")
            st.stop()
        incidents['timestamp'] = pd.to_datetime(incidents['timestamp'])
        incidents['date'] = incidents['timestamp'].dt.date
        incidents['hour'] = incidents['timestamp'].dt.hour
    except Exception as e:
        st.error(f"Error reading CSV file: {e}")
        st.stop()
else:
    st.error(f"File not found: {file_path}")
    st.stop()

# Initialize AI provider with backwards compatibility
ai_provider = AIInsightProvider() 

# Date/hour filter
date_options = sorted(incidents['date'].unique())
today = datetime.date.today()
default_date = today if today in date_options else date_options[0]
selected_date = st.sidebar.selectbox('Select Date', date_options, index=date_options.index(default_date))
selected_hour = st.sidebar.slider('Select Hour (24H):', min_value=0, max_value=23, value=datetime.datetime.now().hour)
filtered_incidents = incidents[(incidents['date'] == selected_date) & (incidents['hour'] == selected_hour)]  # Filter incidents

# AI Provider Status & Controls
st.sidebar.markdown("---")
st.sidebar.markdown("### AI Provider Status")
provider_status = ai_provider.get_provider_status()
if provider_status["gemini_available"]:
    st.sidebar.success("✅ Gemini API Available")
else:
    st.sidebar.error("❌ Gemini API Not Configured")

if provider_status["sonar_available"]:
    st.sidebar.success("✅ Sonar API Available")
else:
    st.sidebar.error("❌ Sonar API Not Configured")

st.sidebar.info(f"Primary: {provider_status['primary_provider'].title()}")
st.sidebar.info(f"Cache: {provider_status['cache_size']} items")

if st.sidebar.button("Clear AI Cache"):
    ai_provider.clear_cache()
    st.sidebar.success("Cache cleared!")

# Town loc logic
lat, lng = 41.8236, -71.4222  # Default to Providence
town = st.text_input('Enter a Rhode Island town name:', 'Providence')
town_incidents = filtered_incidents[filtered_incidents['location'].str.lower() == town.lower()]
if not town_incidents.empty:
    lat = town_incidents.iloc[0]['lat']
    lng = town_incidents.iloc[0]['lng']
    st.success(f"Showing map for {town} at ({lat}, {lng})")
else:
    st.warning(f"No incidents found for {town}. Centering on Providence by default.")

# Folium map with incident markers
m = folium.Map(location=[lat, lng], zoom_start=12)
for _, incident in filtered_incidents.iterrows():
    popup_html = (
        f"<div style='background-color: rgba(255,255,255,0.85);"
        f"padding:10px;border-radius:8px;font-family:Verdana,sans-serif;"
        f"font-size:13px;max-width:200px;'>"
        f"<strong>{incident['description']}</strong><br></div>"
    )
    popup = folium.Popup(popup_html, max_width=250)
    folium.Marker(
        location=[incident['lat'], incident['lng']],
        popup=popup,
        icon=folium.Icon(color='red' if incident['severity'] > 2 else 'orange')  # Visual severity indicator
    ).add_to(m)

# Streamlit layout
st.title('Rhode Island Traffic Map')
map_data = st_folium(m, width=700, height=500)  # Render map in app

# Handling marker click to fetch Sonar insight
if map_data and map_data.get("last_object_clicked"):
    clicked_lat = map_data["last_object_clicked"]["lat"]
    clicked_lng = map_data["last_object_clicked"]["lng"]
    matched = filtered_incidents[
        (filtered_incidents["lat"].sub(clicked_lat).abs() < 1e-4) &
        (filtered_incidents["lng"].sub(clicked_lng).abs() < 1e-4)
    ]  # Match clicked marker to incident
    if not matched.empty:
        incident = matched.iloc[0]
        st.session_state["selected_incident"] = incident
        incident_id = str(incident.get('id', hash(incident['description'])))
        st.session_state["ai_summary"] = ai_provider.get_incident_explanation(
            incident["description"], incident_id
        )

def ai_insight_card(incident, summary):
    '''
    Params:
        incident (pd.Series): The incident metadata selected by the user.
        summary (str): The AI-generated contextual explanation.

    Returns:
        None: Displays an interactive card UI component in the Streamlit app.
    '''
    with elements("ai_insight_card"):
        with mui.Card(
            sx={
                "display": "flex",
                "flexDirection": "column",
                "maxHeight": "500px",
                "margin": "1rem 0",
                "borderRadius": "20px",
                "boxShadow": "0 8px 32px rgba(0,0,0,0.12)",
                "background": "linear-gradient(145deg, #ffffff 0%, #f8fafc 100%)",
                "border": "1px solid rgba(255,255,255,0.2)",
                "backdropFilter": "blur(10px)",
                "overflow": "hidden",
                "transition": "all 0.3s ease",
                "&:hover": {
                    "boxShadow": "0 12px 40px rgba(0,0,0,0.15)",
                    "transform": "translateY(-2px)"
                }
            }
        ):
            # Header with gradient and icon
            with mui.Box(
                sx={
                    "background": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                    "color": "white",
                    "padding": "1.25rem 1.5rem"
                }
            ):
                with mui.Box(sx={"display": "flex", "alignItems": "center", "gap": "0.75rem", "marginBottom": "0.5rem"}):
                    mui.Typography(
                        "🧠",
                        sx={"fontSize": "1.5rem", "lineHeight": 1}
                    )
                    mui.Typography(
                        "AI Traffic Insight",
                        variant="h6",
                        sx={"fontWeight": 500, "fontSize": "1.1rem"}
                    )
                mui.Typography(
                    f"📍 {incident.get('location', 'Unknown Location')} • {incident['date']} at {incident['hour']}:00",
                    variant="body2",
                    sx={"opacity": 0.9, "fontSize": "0.9rem"}
                )
            
            # Content area with better spacing
            with mui.CardContent(
                sx={
                    "flex": 1,
                    "overflow": "auto",
                    "padding": "1.75rem 1.5rem",
                    "background": "rgba(255,255,255,0.7)"
                }
            ):
                # Clean up the summary text by removing excessive bold formatting
                clean_summary = summary.replace("**", "").replace("*", "")
                
                html.div(
                    clean_summary,
                    style={
                        "fontFamily": "'Inter', 'Segoe UI', sans-serif",
                        "fontSize": "15px",
                        "color": "#4b5563",
                        "lineHeight": "1.7",
                        "textAlign": "left",
                        "letterSpacing": "0.01em",
                        "marginBottom": "0.5rem"
                    }
                )
            
            # Enhanced action buttons
            with mui.CardActions(
                sx={
                    "justifyContent": "space-between",
                    "padding": "1rem 1.5rem",
                    "background": "rgba(248,250,252,0.8)",
                    "borderTop": "1px solid rgba(0,0,0,0.05)"
                }
            ):
                mui.Button(
                    "🔍 Learn More",
                    variant="outlined",
                    size="medium",
                    href=f"https://www.perplexity.ai/search?q={incident['description']}",
                    target="_blank",
                    sx={
                        "borderRadius": "12px",
                        "textTransform": "none",
                        "fontWeight": 500,
                        "borderColor": "#667eea",
                        "color": "#667eea",
                        "&:hover": {
                            "borderColor": "#764ba2",
                            "color": "#764ba2",
                            "background": "rgba(102,126,234,0.05)"
                        }
                    }
                )
                mui.Button(
                    "✕ Close",
                    variant="contained",
                    size="medium",
                    sx={
                        "borderRadius": "12px",
                        "textTransform": "none",
                        "fontWeight": 500,
                        "background": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                        "boxShadow": "0 4px 12px rgba(102,126,234,0.3)",
                        "&:hover": {
                            "background": "linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%)",
                            "boxShadow": "0 6px 16px rgba(102,126,234,0.4)"
                        }
                    }
                )

# Show the AI insight card if something is selected
if "selected_incident" in st.session_state:
    ai_insight_card(
        incident=st.session_state["selected_incident"],
        summary=st.session_state["ai_summary"]
    )

def footer():
    '''
    Params: NONE

    Returns:
        NULL: Displays an app footer with source branding.
    '''
    with elements("footer"):
        with mui.Box(
            sx={
                "display": "flex",
                "justifyContent": "center",
                "alignItems": "center",
                "padding": "1rem",
                "backgroundColor": "#1976d2",
                "color": "#fff",
                "borderRadius": "8px",
                "marginTop": "1rem"
            }
        ):
            html.div(
                "Powered by AI and Streamlit",
                style={"fontFamily": "Arial, sans-serif", "fontSize": "14px"}
            )

# Refresh every 15 minutes
st_autorefresh(interval=15 * 60 * 1000)
footer()
