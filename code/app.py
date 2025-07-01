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

# Real Sonar API call
SONAR_API_KEY = st.secrets.get("SONAR_API_KEY", "key") # via local .env

def get_sonar_summary(description):
    '''
    Params:
        description (str): A traffic incident description string used to prompt Sonar

    Returns:
        str: A natural language explanation of the incident from Sonar API
    '''
    headers = {
        "Authorization": f"Bearer {SONAR_API_KEY}",
        "Content-Type": "application/json"
    }
    prompt = (
        f"Explain the possible causes and implications of this traffic report in plain language:\n"
        f"\"{description}\""
    )
    data = {
        "query": prompt,
        "source": "web",
        "num_results": 1
    }

    try:
        response = requests.post("https://api.perplexity.ai/sonar/v1/query", headers=headers, json=data)
        response.raise_for_status()
        return response.json().get("answer", "No answer provided.")  # Extract model output
    except Exception as e:
        return f"Error retrieving Sonar summary: {e}" 

# Date/hour filter
date_options = sorted(incidents['date'].unique())
today = datetime.date.today()
default_date = today if today in date_options else date_options[0]
selected_date = st.sidebar.selectbox('Select Date', date_options, index=date_options.index(default_date))
selected_hour = st.sidebar.slider('Select Hour (24H):', min_value=0, max_value=23, value=datetime.datetime.now().hour)
filtered_incidents = incidents[(incidents['date'] == selected_date) & (incidents['hour'] == selected_hour)]  # Filter incidents

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
        st.session_state["sonar_summary"] = get_sonar_summary(incident["description"])  # Live API call

def sonar_card(incident, summary):
    '''
    Params:
        incident (pd.Series): The incident metadata selected by the user.
        summary (str): The Sonar-generated contextual explanation.

    Returns:
        None: Displays an interactive card UI component in the Streamlit app.
    '''
    with elements("sonar_sidebar_card"):
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
                title="Sonar Insight",
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
                    href=f"https://www.perplexity.ai/search?q={incident['description']}",
                    target="_blank"
                )
                mui.Button("Dismiss", variant="contained", size="small", color="primary")

# Show the Sonar card if something is selected
if "selected_incident" in st.session_state:
    sonar_card(
        incident=st.session_state["selected_incident"],
        summary=st.session_state["sonar_summary"]
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
                "Powered by Sonar API and Streamlit",
                style={"fontFamily": "Arial, sans-serif", "fontSize": "14px"}
            )

# Refresh every 15 minutes
st_autorefresh(interval=15 * 60 * 1000)
footer()
