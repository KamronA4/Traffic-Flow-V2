# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Village is a comprehensive municipal traffic planning platform designed for transportation professionals and city planners. Built with Streamlit, it provides real-time traffic monitoring, AI-powered analysis, statistical insights, and professional report generation to support data-driven planning decisions.

## Core Architecture

### Application Structure
- **`code/main.py`**: Multi-page Streamlit application entry point with authentication, navigation, and Village-themed UI
- **`code/pages/`**: Feature modules including:
  - `live_traffic.py`: Real-time incident monitoring with interactive maps
  - `analytics.py`: Statistical analysis and machine learning models
  - `planning.py`: Strategic planning and scenario modeling
  - `reports.py`: Professional report generation
  - `monitoring.py`: System health and data collection status
- **`code/utils/`**: Core utilities:
  - `enhanced_traffic_collector.py`: TomTom API integration for data collection
  - `ai_analyzer.py`: Perplexity AI integration for contextual analysis
  - `database.py`: SQLite database management
  - `enterprise_auth.py`: Authentication and role-based access

### Data Flow
1. **Collection**: TomTom API → Traffic Collector Daemon → SQLite Database
2. **Storage**: Primary database at `data/traffic_data.db` with CSV backups
3. **Analysis**: Real-time AI analysis via Perplexity, statistical processing
4. **Presentation**: Interactive maps (Folium), charts (Plotly), reports (PDF/Excel)

## Development Commands

### Running the Application
```bash
# Main application
streamlit run code/main.py

# Start background data collection
python traffic_collector_daemon.py

# Run API server
python api/data_api.py

# Docker deployment
docker-compose -f deploy/docker-compose.yml up
```

### Testing & Verification
```bash
# Check API connections
python code/check_api_status.py

# Monitor TomTom credit usage
python code/credit_monitor.py

# Verify system end-to-end
python verify_real_data_system.py
```

### Data Management
```bash
# Initialize databases
python code/initialize_databases.py

# Emergency stop collection
python code/emergency_stop_collection.py

# Reset credit exhaustion flags
python code/reset_credit_flag.py
```

## Key Technical Details

### API Configuration
- **TomTom API**: Traffic incidents, flow data, routing (50k daily free requests)
  - Set `TOMTOM_API_KEY` environment variable
  - Collection zones configured in `config/collector_config.yaml`
- **Perplexity AI**: Real-time incident analysis with web search
  - Set `PERPLEXITY_API_KEY` environment variable
  - Uses Sonar model for fast municipal planning insights

### Database Schema
- **traffic_incidents**: Core incident data with AI analysis
- **traffic_flow**: Speed and congestion measurements
- **users/organizations**: Multi-tenant authentication
- **api_keys**: External API access management

### Subscription Tiers
- **Free**: 5 users, basic monitoring, 7-day retention
- **Starter** ($99/mo): 20 users, analytics, 30-day retention
- **Pro** ($499/mo): 100 users, predictive analytics, API access
- **Enterprise**: Custom pricing, unlimited features

### Performance Optimizations
- 15-minute caching for TomTom API calls
- 30-minute caching for AI analysis
- Adaptive collection scheduling based on priority zones
- Automatic quota management with graceful degradation

## Important Patterns

### Error Handling
- All API calls include retry logic with exponential backoff
- Credit exhaustion triggers automatic collection pause
- User-friendly error messages with actionable guidance

### Authentication Flow
- JWT-based authentication with role-based access (Admin, Analyst, Viewer)
- Organization-based multi-tenancy
- Feature gating based on subscription tier

### Background Services
- Traffic Collector Daemon runs continuously with systemd
- Adaptive scheduling adjusts collection frequency based on:
  - Zone priority (1-4)
  - Time of day (peak hours)
  - API quota usage
  - System resources

## Development Guidelines

### When Adding Features
1. Check organization tier for feature access
2. Add appropriate authentication decorators
3. Follow Village theme styling (pine green, nature-inspired)
4. Include proper error handling and user feedback
5. Update relevant documentation

### Testing Requirements
- Verify API connections before deployment
- Test with demo accounts (created via `code/demo_accounts.py`)
- Check credit monitoring to avoid quota exhaustion
- Ensure background collectors are running

### Common Issues
- **Credit Exhaustion**: Run `reset_credit_flag.py` after adding quota
- **Database Lock**: Stop collectors before manual database operations
- **API Timeouts**: Check `config/collector_config.yaml` for timeout settings
- **Auth Issues**: Verify JWT secret in environment variables