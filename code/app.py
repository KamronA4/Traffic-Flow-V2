# app.py

import streamlit as st
import folium
from streamlit_folium import st_folium
from streamlit_autorefresh import st_autorefresh
import datetime
import pandas as pd
import csv
import os

# Init
# Access 'traffic_incidents.csv'
file_path = 'code/traffic_incidents.csv'
if os.path.exists(file_path):
    try:
        incidents = pd.read_csv(file_path)

        if incidents.empty or not {'timestamp', 'lat', 'lng', 'location', 'severity', 'description'}.issubset(incidents.columns):
            st.error("The CSV file is empty or missing required columns.")
            st.stop()

        # Process .csv data
        incidents['timestamp'] = pd.to_datetime(incidents['timestamp'])
        incidents['date'] = incidents['timestamp'].dt.date
        incidents['hour'] = incidents['timestamp'].dt.hour

    except Exception as e:
        st.error(f"Error reading CSV file: {e}")
        st.stop()
else:
    st.error(f"File not found: {file_path}")
    st.stop()

# AI Analysis mock function
def get_ai_summary(description):
    # Mock summary for municipal planning analysis
    return f"Planning Analysis for incident: {description}. This analysis provides contextual insights for municipal planning and traffic management decisions."

# Filters

# Date filter
date_options = sorted(incidents['date'].unique())
today = datetime.date.today()

# Default to today if exists in data, otherwise -> first available entry
default_date = today if today in date_options else date_options[0]
default_hour = datetime.datetime.now().hour

# Streamlit sidebar with default
selected_date = st.sidebar.selectbox('Select Date', date_options, index=date_options.index(default_date))

# Hour slider
selected_hour = st.sidebar.slider('Select Hour (24H):', min_value=0, max_value=23, value=datetime.datetime.now().hour)

# Date-time Filter
filtered_incidents = incidents[
    (incidents['date'] == selected_date) & (incidents['hour'] == selected_hour)
]


# Old, ignore for now
""" # Town input
town = st.text_input('Enter a Rhode Island town name:', 'Providence')

# Town output
try:
    lat, lng = fetcher.get_town_coords(town)
    st.success(f"Showing map for {town} at ({lat}, {lng})")
except Exception as e:
    st.error(f"Error fetching town coordinates: {e}")
    st.stop() """

# Default center coordinates
lat, lng = 41.8236, -71.4222  # This is Providence

# Town input
town = st.text_input('Enter a Rhode Island town name:', 'Providence')
town_incidents = filtered_incidents[filtered_incidents['location'].str.lower() == town.lower()]
if not town_incidents.empty:
    lat = town_incidents.iloc[0]['lat']
    lng = town_incidents.iloc[0]['lng']
    st.success(f"Showing map for {town} at ({lat}, {lng})")
else:
    st.warning(f"No incidents found for {town}. Centering on Providence by default.")

# Folium map
m = folium.Map(location=[lat, lng], zoom_start=12)

# Streamlit component
st_autorefresh(interval=15 * 60 * 1000)  # Refresh every 15 minutes to avoid crashing

st.title('Village - Municipal Traffic Planning Tool')

# Display the folium map w/ features in Streamlit
st_folium(m, width=700, height=500)

# Store the incident buttons in a list
incident_buttons = []

# Add traffic incidents to the map
# Note: popup is where we integrate AI-powered planning analysis
for _, incident in filtered_incidents.iterrows():
    # Get ids
    incident_id = f"{incident['location']}-{incident['timestamp'].strftime('%Y%m%d%H')}"
    # Clause to customize each marker
    html = f"""
            <div style="background-color: rgba(255, 255, 255, 0.85); 
                    padding: 10px; 
                    border-radius: 8px; 
                    font-family: 'Verdana', sans-serif; 
                    font-size: 13px;
                    max-width: 200px;">
                <strong>{incident['description']}</strong><br>
            </div>
            """
    # Then we add the popup to the marker
    popup = folium.Popup(html, max_width=250)
    folium.Marker(
        location=[incident['lat'], incident['lng']],
        popup=popup,
        icon=folium.Icon(color='red' if incident['severity'] > 2 else 'orange')
    ).add_to(m)

    # Add a button for each incident
    incident_buttons.append((incident_id, incident))

# Display buttons after map
for incident_id, incident in incident_buttons:
    if st.button(f"{incident['description'][:30]}..."):
        st.session_state["selected_incident"] = incident
        st.session_state["ai_summary"] = get_ai_summary(incident['description'])
    # Clear selection button
    if st.button("Clear Selection"):
    st.session_state.pop("selected_incident", None)
    st.session_state.pop("ai_summary", None)

# Card component
from streamlit_elements import elements, mui, html

# Sidebar card display
def planning_analysis_card(incident, summary):
    with elements("planning_analysis_card"):
        with mui.Card(
            sx={
                "display": "flex",
                "flexDirection": "column",
                "height": 350,
                "margin": "1rem",
                "padding": "1rem",
                "borderRadius": "16px",
                "boxShadow": "0 4px 16px rgba(0,0,0,0.1)",
                "background": "#f9f9fb",
                "borderLeft": "6px solid #1976d2",
            }
        ):
            mui.CardHeader(
                title="Planning Analysis",
                subheader=f"{incident['location']} — {incident['date']} at {incident['hour']}:00",
                sx={"color": "#333", "paddingBottom": "0"}
            )
            with mui.CardContent(sx={"flex": 1, "overflow": "auto"}):
                html.div(
                    summary,
                    style={
                        "fontFamily": "Segoe UI, sans-serif",
                        "fontSize": "14px",
                        "color": "#444",
                        "lineHeight": "1.5",
                    }
                )
            with mui.CardActions(sx={"justifyContent": "flex-end"}):
                mui.Button(
                    "Explain",
                    variant="outlined",
                    size="small",
                    href=f"#",
                    target="_blank"
                )
                mui.Button("Dismiss", variant="contained", size="small", color="primary")

# Show planning analysis card
if "selected_incident" in st.session_state:
    planning_analysis_card(
        incident=st.session_state["selected_incident"],
        summary=st.session_state["ai_summary"]
    )

# Footer
def footer():
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
                "Village - Municipal Traffic Planning Tool",
                style={"fontFamily": "Arial, sans-serif", "fontSize": "14px"}
            )
footer()
# End