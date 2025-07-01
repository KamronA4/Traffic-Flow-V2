# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
```bash
streamlit run code/app.py
```

### Data Collection
```bash
python scripts/traffic_data_collection.py
```

### Environment Setup
```bash
pip install -r requirements.txt
```

## Architecture Overview

This is a Streamlit-based traffic incident visualization application for Rhode Island that integrates real-time traffic data with AI-powered insights.

### Core Components

- **`code/app.py`**: Main Streamlit application with interactive map and Sonar API integration
- **`code/MapFetcher.py`**: HERE API client for geocoding and traffic incident retrieval
- **`scripts/traffic_data_collection.py`**: Background data collection script for CSV generation
- **`data/traffic_incidents.csv`**: Primary data source for incident visualization

### Data Flow

1. Traffic incidents are collected via HERE API (`MapFetcher.py`)
2. Data is stored in CSV format with timestamp, coordinates, severity, and descriptions
3. Streamlit app filters incidents by date/hour and displays on interactive Folium map
4. User clicks on markers trigger Sonar API calls for contextual incident analysis
5. Results are displayed in Material-UI cards via streamlit-elements

### API Dependencies

- **HERE API**: Geocoding and traffic incident data (API key in `MapFetcher.py`)
- **Sonar API**: AI-powered incident analysis (API key via Streamlit secrets as `SONAR_API_KEY`)

### Key Features

- Real-time incident filtering by date and hour
- Town-based map centering with geocoding fallback
- Interactive marker popups with severity-based color coding
- On-demand AI analysis of incident context via Sonar API
- Automatic refresh every 15 minutes
- Material-UI component integration for enhanced UX

### File Structure Notes

- Main application code in `code/` directory
- Data collection utilities in `scripts/`
- CSV data stored in both `code/` and `data/` directories
- Virtual environment in `venv/` (not tracked)