# Village Platform - Clean Codebase Structure

## Overview
This document outlines the clean, production-ready structure of the Village Municipal Traffic Planning Platform after removing unused files and development artifacts.

## Core Application Structure

### 📁 Root Directory
```
Village-Platform/
├── code/                           # Core application code
├── data/                          # Data storage directory
├── CLAUDE.md                      # Project documentation for AI assistant
├── README.md                      # User documentation
├── requirements.txt               # Python dependencies
├── LICENSE                        # MIT License
├── DEMO_SCRIPT.md                # Demo walkthrough guide
├── cleanup_unused_files.py       # Cleanup script (run once, then remove)
└── CODEBASE_STRUCTURE.md         # This file
```

### 📁 Code Directory (`code/`)
```
code/
├── main.py                        # Main Streamlit application entry point
├── traffic_incidents.csv          # Sample traffic data
├── pages/                         # Streamlit page modules
│   ├── __init__.py               # Page module initialization
│   ├── analytics.py              # Statistical analysis & ML models
│   ├── live_traffic.py           # Real-time traffic monitoring
│   ├── monitoring.py             # System monitoring dashboard
│   ├── planning.py               # Strategic planning tools
│   └── reports.py                # Professional report generation
└── utils/                         # Utility modules
    ├── __init__.py               # Utils package initialization
    ├── ai_analyzer.py            # Perplexity AI integration
    ├── database.py               # SQLite database management
    ├── interactive_tables.py     # Professional DataFrame components
    └── smart_collector.py        # Intelligent data collection
```

### 📁 Data Directory (`data/`)
```
data/
└── traffic_data.db               # SQLite database file
```

## File Purposes & Dependencies

### 🚀 Main Application
- **`code/main.py`** - Primary entry point, navigation, Village theming
  - Dependencies: All page modules, Streamlit
  - Command: `streamlit run code/main.py`

### 📄 Page Modules
- **`code/pages/analytics.py`** - Statistical analysis, ML models, Seaborn visualizations
  - Features: Traffic flow forecasting, pattern detection, severity prediction
  - Dependencies: pandas, numpy, seaborn, matplotlib, scikit-learn, interactive_tables

- **`code/pages/live_traffic.py`** - Real-time traffic monitoring with AI analysis
  - Features: Interactive maps, incident markers, AI-powered analysis
  - Dependencies: folium, streamlit-folium, ai_analyzer, interactive_tables

- **`code/pages/monitoring.py`** - System monitoring and data collection status
  - Features: API usage tracking, collection status, database metrics
  - Dependencies: database, smart_collector

- **`code/pages/planning.py`** - Strategic planning and scenario modeling
  - Features: Impact analysis, cost-benefit analysis, infrastructure planning
  - Dependencies: plotly, pandas, numpy

- **`code/pages/reports.py`** - Professional report generation
  - Features: PDF/Excel export, customizable reports, stakeholder summaries
  - Dependencies: reportlab, openpyxl, matplotlib, seaborn

### 🛠️ Utility Modules
- **`code/utils/ai_analyzer.py`** - Perplexity AI integration for traffic analysis
  - Features: Incident analysis, related articles, enhanced popups
  - Dependencies: requests, streamlit

- **`code/utils/database.py`** - SQLite database management
  - Features: Traffic data storage, API usage tracking, zone management
  - Dependencies: sqlite3, pandas

- **`code/utils/interactive_tables.py`** - Professional DataFrame components
  - Features: Search, filtering, export, Village theming
  - Dependencies: streamlit, pandas, numpy

- **`code/utils/smart_collector.py`** - Intelligent traffic data collection
  - Features: Priority-based sampling, API quota management, zone targeting
  - Dependencies: requests, database, TomTom API

## Removed Files (No Longer Needed)

### 🗑️ Test Files
- `simple_test.py` - Basic system test
- `test_aggressive_sampling.py` - Sampling system test
- `test_tomtom_integration.py` - TomTom API test
- `start_collection.py` - Collection startup script

### 🗑️ Development Artifacts
- `code/notes.md` - Development notes
- `traffic_collection.log` - Collection log file
- `code/utils/database_lite.py` - Redundant database utility

### 🗑️ Design Mockups
- `village_mockup.html` - HTML mockup
- `village_analytics_mockup.html` - Analytics mockup
- `village_enterprise_mockup.html` - Enterprise mockup

## Key Features Preserved

### ✅ Core Functionality
- Multi-page Streamlit application
- Real-time traffic monitoring
- AI-powered incident analysis
- Professional interactive DataFrames
- Statistical analysis and ML models
- Strategic planning tools
- Professional report generation

### ✅ Technical Features
- Village color scheme theming
- Perplexity AI integration
- TomTom API integration
- SQLite database management
- Intelligent data collection
- Professional export capabilities

### ✅ Enterprise Features
- Search and filtering
- Data export (CSV, Excel, JSON)
- Professional styling
- Performance optimization
- Error handling and fallbacks

## Dependencies

### 📦 Core Libraries
- `streamlit` - Web application framework
- `pandas` - Data manipulation
- `numpy` - Numerical computing
- `requests` - HTTP requests

### 📦 Visualization
- `seaborn` - Statistical plotting
- `matplotlib` - Plotting library
- `folium` - Interactive maps
- `streamlit-folium` - Folium-Streamlit integration

### 📦 Machine Learning
- `scikit-learn` - ML algorithms
- `scipy` - Scientific computing

### 📦 Data Export
- `openpyxl` - Excel export
- `reportlab` - PDF generation

### 📦 Database
- `sqlite3` - Built-in SQLite support

## Running the Application

### 🚀 Quick Start
```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run code/main.py
```

### 🔧 Configuration
- Set `PERPLEXITY_API_KEY` for AI features
- Set `TOMTOM_API_KEY` for traffic data collection
- Database automatically created in `data/traffic_data.db`

## Summary

The Village platform now has a clean, production-ready codebase with:
- **8 core Python files** (main + 5 pages + 4 utils)
- **Professional enterprise features** throughout
- **Zero unused files** or development artifacts
- **Comprehensive documentation** and structure
- **Easy deployment** and maintenance

The platform is ready for production use by municipal planners and transportation professionals.