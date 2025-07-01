# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Village is a municipal traffic planning tool designed for transportation professionals and municipal planners. The application visualizes real-time traffic incidents using Streamlit and Folium maps, with AI-powered incident analysis to support data-driven planning decisions.

## Key Components & Architecture

### Core Application Structure
- **`code/app.py`**: Main Streamlit application with interactive map, date/time filtering, and card-based incident display
- **`code/MapFetcher.py`**: RI_MapFetcher class that interfaces with TomTom API for geocoding and traffic incident data
- **`scripts/traffic_data_collection.py`**: Data collection script that fetches and stores traffic incidents to CSV
- **`code/tests.py`**: Simple data access testing script

### Data Flow
1. Traffic incidents are collected via HERE API using MapFetcher class
2. Data is stored in `traffic_incidents.csv` (both in `/code` and `/data` directories)
3. Streamlit app reads CSV data, applies date/time filters, and displays on interactive map
4. Clicking incident buttons shows AI-powered analysis cards for planning insights

### Key Features
- Interactive Folium map with incident markers
- Date and hour-based filtering via sidebar
- Town-based map centering
- Card-based incident summaries using streamlit-elements for planning analysis
- Auto-refresh functionality (15-minute intervals)

## Development Commands

### Running the Application
```bash
streamlit run code/app.py
```

### Installing Dependencies
```bash
pip install -r requirements.txt
```

### Data Collection
```bash
python scripts/traffic_data_collection.py
```

### Testing Data Access
```bash
python code/tests.py
```

## Key Technical Details

### API Integration
- **TomTom API**: Used for geocoding (town coordinates) and traffic incident data
  - Geocoding: `https://api.tomtom.com/search/2/search/{query}.json`
  - Traffic Incidents: `https://api.tomtom.com/traffic/services/5/incidentDetails`
- **AI Analysis**: Planned integration for incident analysis (currently mocked in `get_ai_summary()`)
- API keys should be set as environment variables or configuration

### Data Structure
Traffic incidents CSV contains: `timestamp`, `id`, `description`, `severity`, `lat`, `lng`, `startTime`, `endTime`, `length`, `delay`, `location`
App expects: `timestamp`, `lat`, `lng`, `location`, `severity`, `description` plus derived `date` and `hour` fields

### Caching Strategy
- MapFetcher methods use `@st.cache_data(ttl=900)` for 15-minute caching
- Auto-refresh prevents application crashes from constant API calls
- TomTom API provides 50,000 free requests daily with generous pricing beyond that

### UI Components
- Uses `streamlit-elements` for Material-UI card components
- Folium markers with custom HTML popups
- Sidebar controls for date/time filtering

## Important Notes

- The application centers on Rhode Island (TomTom bounding box: `41.146240,-71.899414,41.748681,-71.088867`)
- Default location is Providence, RI (`41.8236, -71.4222`)
- CSV data paths are relative to the `code/` directory
- AI analysis integration is currently mocked but structured for easy implementation
- Designed specifically for municipal planning workflows and decision-making
- TomTom API provides better pricing structure than HERE API for municipal use

## TomTom API Setup

### Getting Started
1. Sign up for a free TomTom Developer account at https://developer.tomtom.com/
2. Create a new application to get your API key
3. Replace placeholder API keys in the code:
   - `scripts/traffic_data_collection.py`: Update `api_key` variable
   - When initializing `RI_MapFetcher` in `app.py`

### Testing Integration
Run the test script to verify TomTom API integration:
```bash
python test_tomtom_integration.py
```

### API Limits
- Free tier: 50,000 requests per day
- Pay-as-you-go: $0.08 per 1,000 requests beyond free limit
- Much more generous than HERE API pricing