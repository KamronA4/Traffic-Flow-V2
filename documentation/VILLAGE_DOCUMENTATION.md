# Village Platform - Complete Documentation

## Table of Contents

1. [Platform Overview](#platform-overview)
2. [Core Components](#core-components)
3. [Infrastructure & Deployment](#infrastructure--deployment)
4. [Configuration & Integration](#configuration--integration)
5. [Utilities & Scripts](#utilities--scripts)
6. [Developer Resources](#developer-resources)

---

# Platform Overview

## Introduction to Village Platform

Village is a comprehensive municipal traffic planning platform designed to empower city planners, transportation professionals, and municipal decision-makers with real-time traffic insights and AI-driven analysis. Built with modern web technologies and enterprise-grade features, Village transforms raw traffic data into actionable intelligence for safer, more efficient urban transportation planning.

### Key Features
- **Real-time Traffic Monitoring**: Live incident tracking and traffic flow analysis
- **AI-Powered Insights**: Contextual analysis using advanced language models
- **Predictive Analytics**: Machine learning models for traffic pattern prediction
- **Professional Reporting**: Export-ready reports for stakeholder presentations
- **Multi-tenant Architecture**: Enterprise support for multiple organizations
- **Role-based Access**: Granular permissions for different user types

### Target Users
- Municipal traffic planners
- Transportation engineers
- Emergency response coordinators
- City administrators
- Policy makers
- Urban development teams

## Architecture Overview

Village follows a modular architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Streamlit)                      │
├─────────────────────────────────────────────────────────────┤
│                  Application Layer (main.py)                 │
├─────────────────────────────────────────────────────────────┤
│   Pages     │    Utils    │   API      │   Background      │
│   ├─ Live   │  ├─ Auth    │ ├─ REST    │  ├─ Collector    │
│   ├─ Analytics  ├─ Data   │ ├─ WebSocket   ├─ Analyzer    │
│   ├─ Planning   ├─ AI     │ └─ GraphQL │  └─ Scheduler   │
│   └─ Reports    └─ Theme  │            │                   │
├─────────────────────────────────────────────────────────────┤
│                   Data Layer (SQLite/PostgreSQL)            │
├─────────────────────────────────────────────────────────────┤
│              External Services (TomTom, Perplexity)         │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

**Frontend Technologies:**
- Streamlit 1.28+ - Rapid web app development
- Folium - Interactive mapping
- Plotly - Advanced data visualization
- Streamlit Elements - Material-UI components

**Backend Technologies:**
- Python 3.8+ - Core language
- SQLite/PostgreSQL - Database
- pandas/numpy - Data processing
- scikit-learn - Machine learning
- Flask - API server

**External Services:**
- TomTom Traffic API - Real-time traffic data
- Perplexity AI - Contextual analysis
- Stripe - Payment processing (planned)

**Infrastructure:**
- Docker - Containerization
- Nginx - Reverse proxy
- Systemd - Service management
- Ubuntu 20.04+ - Deployment OS

## Getting Started Guide

### Prerequisites
- Python 3.8 or higher
- Git
- 4GB RAM minimum
- TomTom API key
- Perplexity API key

### Quick Start
```bash
# Clone the repository
git clone https://github.com/your-org/village-platform.git
cd village-platform

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure API keys
cp code/.streamlit/secrets.toml.example code/.streamlit/secrets.toml
# Edit secrets.toml with your API keys

# Initialize databases
python code/initialize_databases.py

# Run the application
streamlit run code/main.py
```

### First-Time Setup
1. Create an admin account
2. Configure your organization
3. Set up data collection zones
4. Start background collectors
5. Access the dashboard

---

# Core Components

## 1. Main Application Framework

### main.py - The Heart of Village

The main.py file serves as the entry point and orchestrator for the entire Village platform. It handles:

#### Navigation System
```python
# Page routing with role-based access
base_pages = ["Live Traffic", "Analytics"]
tier_pages = ["Planning", "Reports", "Monitoring"]
admin_pages = ["API Management", "Pricing", "Marketing"]
```

The navigation system dynamically adjusts based on:
- User authentication status
- Organization subscription tier
- User role permissions

#### Theme Management
Village uses a custom nature-inspired theme with CSS variables:
```css
--village-pine: #2d5016;    /* Deep green */
--village-sage: #5a7c47;    /* Medium green */
--village-beige: #f5f1e8;   /* Light neutral */
--village-brown: #8b4513;   /* Earth brown */
```

The theme automatically adapts to light/dark mode preferences.

#### Authentication Integration
```python
if not is_authenticated():
    show_login_page()
    st.stop()
```

Authentication is checked on every page load, ensuring secure access.

#### System Status Monitoring
The sidebar displays real-time status for:
- TomTom API quota usage
- Remote VM connection status
- Database connectivity
- AI service availability

### Key Components:

**Session Management**
- Maintains user state across page refreshes
- Tracks authentication tokens
- Manages organization context

**Error Handling**
- Graceful degradation for service outages
- User-friendly error messages
- Automatic retry logic

**Performance Optimization**
- Lazy loading of heavy components
- Caching of frequently accessed data
- Efficient state management

## 2. User-Facing Pages

### Live Traffic (pages/live_traffic.py)

The Live Traffic page provides real-time monitoring of traffic incidents with interactive mapping and AI-powered analysis.

#### Core Features:

**Interactive Map Display**
```python
# Folium integration for rich mapping
m = folium.Map(location=[center_lat, center_lng], zoom_start=12)
for incident in filtered_incidents:
    folium.Marker(
        location=[incident.lat, incident.lng],
        popup=create_popup_html(incident),
        icon=get_severity_icon(incident.severity)
    ).add_to(m)
```

**Real-time Updates**
- Auto-refresh every 15 minutes
- WebSocket support for instant updates (planned)
- Efficient delta updates to minimize data transfer

**AI-Powered Analysis**
When users click on an incident, the system:
1. Fetches incident details
2. Sends context to Perplexity AI
3. Generates municipal planning insights
4. Displays in an elegant card format

**Filtering System**
- Date range selection
- Time-of-day filters
- Severity levels
- Geographic boundaries

#### Technical Implementation:

**Data Flow:**
1. MapFetcher retrieves incidents from TomTom API
2. Data is cached with 15-minute TTL
3. Frontend filters apply without API calls
4. Map renders using Folium with custom styling

**Performance Considerations:**
- Incidents are clustered at low zoom levels
- Lazy loading of incident details
- Progressive rendering for large datasets

### Analytics (pages/analytics.py)

The Analytics page transforms raw traffic data into actionable insights through statistical analysis and machine learning.

#### Analysis Modules:

**Incident Statistics**
- Frequency analysis by time/location
- Severity distribution charts
- Trend identification
- Anomaly detection

**Traffic Flow Analysis**
- Speed heatmaps
- Congestion patterns
- Peak hour identification
- Route optimization suggestions

**Machine Learning Models**
```python
# Incident prediction model
model = RandomForestClassifier()
features = ['hour', 'day_of_week', 'location_cluster', 'weather']
model.fit(X_train, y_train)
predictions = model.predict(X_future)
```

**Visualization Components:**
- Plotly interactive charts
- Time series analysis
- Correlation matrices
- Predictive model outputs

#### Key Algorithms:

**Clustering Analysis**
- DBSCAN for incident hotspots
- K-means for zone definition
- Hierarchical clustering for patterns

**Time Series Forecasting**
- ARIMA models for trend prediction
- Seasonal decomposition
- Prophet integration for holidays

### Planning (pages/planning.py)

Strategic planning tools for infrastructure and policy decisions.

#### Planning Modules:

**Scenario Modeling**
- What-if analysis for road changes
- Construction impact simulation
- Event planning optimization
- Emergency route planning

**Resource Allocation**
- Optimal placement of traffic signals
- Emergency service positioning
- Maintenance scheduling
- Budget impact analysis

**Impact Assessment**
- Environmental impact calculations
- Economic benefit analysis
- Safety improvement metrics
- Community feedback integration

### Reports (pages/reports.py)

Professional report generation for stakeholder communication.

#### Report Types:

**Executive Summary**
- High-level KPIs
- Trend visualizations
- Action recommendations
- Budget implications

**Technical Reports**
- Detailed incident analysis
- Traffic flow studies
- Infrastructure assessments
- Compliance documentation

**Public Reports**
- Community-friendly summaries
- Safety statistics
- Improvement highlights
- Planned initiatives

#### Export Formats:
- PDF with custom branding
- Excel with raw data
- PowerPoint presentations
- Interactive HTML dashboards

### Monitoring (pages/monitoring.py)

System health and performance monitoring dashboard.

#### Monitoring Components:

**Data Collection Status**
- Zone coverage metrics
- Collection success rates
- API quota usage
- Error tracking

**System Performance**
- Response time metrics
- Database query performance
- Memory usage tracking
- Concurrent user monitoring

**Data Quality**
- Completeness checks
- Accuracy validation
- Anomaly detection
- Duplicate identification

## 3. Data Management System

### Database Layer (utils/database.py)

The database module provides a robust abstraction layer for all data operations.

#### Core Classes:

**DatabaseManager**
```python
class DatabaseManager:
    def __init__(self, db_path: str = "data/traffic_data.db"):
        self.db_path = db_path
        self.ensure_database_exists()
    
    def get_connection(self):
        """Thread-safe connection management"""
        return sqlite3.connect(self.db_path)
```

**Schema Design:**

```sql
-- Traffic incidents table
CREATE TABLE traffic_incidents (
    id INTEGER PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    lat REAL NOT NULL,
    lng REAL NOT NULL,
    location TEXT,
    severity INTEGER,
    description TEXT,
    ai_analysis TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Traffic flow measurements
CREATE TABLE traffic_flow (
    id INTEGER PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    segment_id TEXT,
    current_speed REAL,
    free_flow_speed REAL,
    congestion_level INTEGER
);

-- User activity tracking
CREATE TABLE user_activity (
    id INTEGER PRIMARY KEY,
    user_id TEXT,
    action TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSON
);
```

#### Key Features:

**Connection Pooling**
- Efficient resource usage
- Thread-safe operations
- Automatic cleanup

**Query Optimization**
- Prepared statements
- Index management
- Query plan analysis

**Data Integrity**
- Foreign key constraints
- Transaction management
- Backup procedures

### Enhanced Traffic Collector (utils/enhanced_traffic_collector.py)

Comprehensive data collection from TomTom APIs with intelligent scheduling and error handling.

#### Collection Strategy:

**Multi-Zone Collection**
```python
COLLECTION_ZONES = [
    {"name": "Downtown", "bbox": [41.81, -71.43, 41.84, -71.40], "priority": 1},
    {"name": "Highway_I95", "bbox": [41.7, -71.6, 41.9, -71.3], "priority": 1},
    {"name": "Suburban", "bbox": [41.73, -71.50, 41.81, -71.43], "priority": 2}
]
```

**Adaptive Scheduling**
- High-priority zones: 5-minute intervals
- Medium-priority: 15-minute intervals
- Low-priority: 30-minute intervals
- Dynamic adjustment based on incidents

**API Management**
```python
def manage_api_quota(self):
    """Intelligent quota management"""
    usage = self.get_daily_usage()
    remaining = self.daily_quota - usage
    
    if remaining < 1000:  # Critical threshold
        self.reduce_collection_frequency()
    elif usage > self.daily_quota * 0.9:  # Warning threshold
        self.prioritize_critical_zones()
```

#### Error Handling:

**Retry Logic**
- Exponential backoff
- Circuit breaker pattern
- Fallback data sources

**Credit Exhaustion**
- Graceful degradation
- Admin notifications
- Automatic recovery

### Data Synchronization (utils/data_sync.py)

Manages the complex dance between local and remote data sources.

#### Sync Strategies:

**Incremental Updates**
```python
def sync_incremental(self, last_sync_time):
    """Sync only new records since last update"""
    remote_data = self.fetch_remote_updates(since=last_sync_time)
    local_data = self.get_local_updates(since=last_sync_time)
    
    conflicts = self.detect_conflicts(remote_data, local_data)
    resolved = self.resolve_conflicts(conflicts)
    
    self.apply_updates(resolved)
```

**Conflict Resolution**
- Timestamp-based priority
- Source authority rules
- Manual override options

**Performance Optimization**
- Batch processing
- Compression for transfers
- Delta synchronization

## 4. AI & Analytics Engine

### Enhanced AI Analyzer (utils/enhanced_ai_analyzer.py)

Integrates Perplexity AI for contextual traffic analysis with advanced caching and optimization.

#### Analysis Pipeline:

**Context Building**
```python
def build_analysis_context(self, incident):
    """Create rich context for AI analysis"""
    context = {
        "incident": incident,
        "historical_patterns": self.get_historical_patterns(incident.location),
        "nearby_incidents": self.get_nearby_incidents(incident.lat, incident.lng),
        "time_context": self.get_temporal_context(incident.timestamp),
        "infrastructure": self.get_infrastructure_data(incident.location)
    }
    return context
```

**AI Integration**
- Streaming responses for real-time feedback
- Token optimization for cost control
- Response caching with semantic similarity
- Fallback to local models

**Analysis Types:**

1. **Incident Analysis**
   - Root cause identification
   - Impact assessment
   - Mitigation recommendations
   - Historical comparisons

2. **Pattern Recognition**
   - Recurring incident detection
   - Seasonal trend analysis
   - Anomaly identification
   - Predictive insights

3. **Planning Recommendations**
   - Infrastructure improvements
   - Policy suggestions
   - Resource allocation
   - Community communication

### Visualization Components

#### Interactive Tables (utils/interactive_tables.py)

Professional-grade data tables with advanced features.

**Features:**
- Sorting and filtering
- Column resizing
- Export functionality
- Cell formatting
- Conditional styling

**Implementation:**
```python
def create_interactive_dataframe(df, config):
    """Create feature-rich interactive table"""
    return st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config=config,
        height=400
    )
```

#### 3D Visualization (utils/visualization_3d.py)

Three-dimensional traffic flow visualization for spatial analysis.

**Technologies:**
- Plotly 3D scatter plots
- Deck.gl integration
- WebGL rendering
- GPU acceleration

**Visualizations:**
- Traffic density clouds
- Speed gradient surfaces
- Incident clustering spheres
- Time-based animations

## 5. Enterprise Features

### Authentication System (utils/enterprise_auth.py)

Multi-tenant authentication with role-based access control.

#### Architecture:

**User Roles:**
```python
class UserRole(Enum):
    ADMIN = "admin"          # Full system access
    ANALYST = "analyst"      # Data analysis and reporting
    VIEWER = "viewer"        # Read-only access
    FIELD_WORKER = "field"   # Mobile app access
```

**Organization Management:**
```python
class Organization:
    def __init__(self, name, tier, domain):
        self.name = name
        self.tier = tier  # Free, Starter, Pro, Enterprise
        self.domain = domain
        self.users = []
        self.settings = {}
```

**Security Features:**
- JWT token authentication
- Session management
- Password policies
- Two-factor authentication (planned)
- IP whitelisting
- Audit logging

#### Implementation Details:

**Password Hashing**
```python
def hash_password(password: str, salt: bytes) -> bytes:
    """Secure password hashing using PBKDF2"""
    return hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        100000  # iterations
    )
```

**Token Management**
- Access tokens: 1-hour expiry
- Refresh tokens: 7-day expiry
- Automatic renewal
- Revocation support

### API Management (utils/api_management.py)

External API access control and monitoring.

#### Features:

**API Key Management**
- Generation and rotation
- Scoped permissions
- Rate limiting
- Usage tracking

**Endpoints:**
```python
# Public endpoints
GET /api/v1/incidents/public
GET /api/v1/statistics/summary

# Authenticated endpoints
GET /api/v1/incidents/detailed
POST /api/v1/analysis/custom
GET /api/v1/reports/generate
```

**Rate Limiting:**
- Per-key limits
- Tier-based quotas
- Burst allowances
- Graceful degradation

### Subscription & Pricing (utils/pricing_tiers.py)

Flexible subscription management with feature gating.

#### Tier Structure:

**Free Tier**
- 5 users maximum
- Basic incident monitoring
- 7-day data retention
- Community support

**Starter Tier ($99/month)**
- 20 users
- Advanced analytics
- 30-day retention
- Email support

**Pro Tier ($499/month)**
- 100 users
- Predictive analytics
- 90-day retention
- Priority support
- API access

**Enterprise Tier (Custom)**
- Unlimited users
- Custom retention
- Dedicated support
- White-label options
- SLA guarantees

#### Feature Gates:
```python
def check_feature_access(organization, feature):
    """Verify organization has access to feature"""
    feature_map = {
        "predictive_analytics": ["pro", "enterprise"],
        "api_access": ["pro", "enterprise"],
        "white_label": ["enterprise"],
        "custom_reports": ["starter", "pro", "enterprise"]
    }
    return organization.tier in feature_map.get(feature, [])
```

---

# Infrastructure & Deployment

## Local Development

### Development Environment Setup

#### Required Software:
- Python 3.8-3.11 (3.12 has compatibility issues)
- Git 2.x
- SQLite 3.x
- Redis (optional, for caching)
- Node.js (for frontend tools)

#### Environment Configuration:
```bash
# .env file structure
ENVIRONMENT=development
DEBUG=True
LOG_LEVEL=DEBUG
DATABASE_URL=sqlite:///data/traffic_data.db
REDIS_URL=redis://localhost:6379/0
```

#### Development Workflow:

1. **Branch Strategy**
   ```bash
   git checkout -b feature/your-feature-name
   # Make changes
   git add .
   git commit -m "feat: add new feature"
   git push origin feature/your-feature-name
   ```

2. **Testing**
   ```bash
   # Run unit tests
   pytest tests/unit/
   
   # Run integration tests
   pytest tests/integration/
   
   # Run linting
   flake8 code/
   black code/ --check
   ```

3. **Local Services**
   ```bash
   # Start Redis (macOS)
   brew services start redis
   
   # Start background collector
   python traffic_collector_daemon.py start --foreground
   ```

## Docker Deployment

### Container Architecture

Village uses a multi-container setup for production deployment:

```yaml
services:
  traffic-collector:   # Data collection daemon
  traffic-api:        # REST API server
  nginx:              # Reverse proxy
  redis:              # Cache and queues
  postgres:           # Production database
```

### Docker Compose Configuration

#### Key Features:
- **Service Isolation**: Each component runs in its own container
- **Network Security**: Internal network for service communication
- **Volume Management**: Persistent data storage
- **Health Checks**: Automatic container monitoring
- **Resource Limits**: CPU and memory constraints

#### Deployment Steps:
```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f traffic-collector

# Scale services
docker-compose up -d --scale traffic-api=3
```

### Container Optimization:
- Multi-stage builds for smaller images
- Layer caching for faster builds
- Non-root user execution
- Minimal base images (Alpine Linux)

## Production Setup

### VM Deployment Guide

#### Server Requirements:
- **Minimum**: 2 vCPU, 4GB RAM, 20GB storage
- **Recommended**: 4 vCPU, 8GB RAM, 50GB storage
- **OS**: Ubuntu 20.04 LTS or newer
- **Network**: Static IP, ports 80/443 open

#### Automated Setup:
```bash
# Run setup script
sudo bash deploy/setup_vm.sh

# Configure environment
sudo nano /etc/traffic-collector/environment
# Add: TOMTOM_API_KEY=your_key_here

# Start services
sudo systemctl start traffic-collector
sudo systemctl start traffic-collector-api
```

### Security Hardening:

1. **Firewall Configuration**
   ```bash
   sudo ufw allow 22/tcp    # SSH
   sudo ufw allow 80/tcp    # HTTP
   sudo ufw allow 443/tcp   # HTTPS
   sudo ufw enable
   ```

2. **SSL/TLS Setup**
   ```bash
   sudo certbot --nginx -d your-domain.com
   ```

3. **System Hardening**
   - Disable root SSH
   - Key-based authentication only
   - Fail2ban installation
   - Regular security updates

### Monitoring & Maintenance:

#### Health Monitoring:
```bash
# Service status
systemctl status traffic-collector

# API health
curl https://your-domain.com/api/health

# Resource usage
htop
df -h
```

#### Backup Strategy:
- **Database**: Daily automated backups
- **Configuration**: Version controlled
- **Logs**: 30-day retention with rotation
- **Recovery**: Tested monthly

---

# Configuration & Integration

## API Integrations

### TomTom Traffic API

#### Setup Process:
1. Create TomTom Developer account
2. Generate API key
3. Configure rate limits
4. Set up billing alerts

#### API Endpoints Used:
```python
# Traffic incidents
INCIDENTS_URL = "https://api.tomtom.com/traffic/services/5/incidentDetails"

# Traffic flow
FLOW_URL = "https://api.tomtom.com/traffic/services/4/flowSegmentData"

# Routing
ROUTING_URL = "https://api.tomtom.com/routing/1/calculateRoute"
```

#### Rate Limiting Strategy:
- 50,000 daily requests (free tier)
- Request batching for efficiency
- Caching to reduce API calls
- Graceful degradation on limit

### Perplexity AI Integration

#### Configuration:
```python
PERPLEXITY_CONFIG = {
    "api_key": os.getenv("PERPLEXITY_API_KEY"),
    "model": "pplx-70b-online",
    "max_tokens": 1500,
    "temperature": 0.7,
    "stream": True
}
```

#### Prompt Engineering:
```python
def create_analysis_prompt(incident_context):
    """Generate optimized prompts for municipal planning insights"""
    return f"""
    As a municipal traffic planning expert, analyze this incident:
    
    Location: {incident_context['location']}
    Type: {incident_context['type']}
    Severity: {incident_context['severity']}
    Time: {incident_context['timestamp']}
    
    Provide:
    1. Root cause analysis
    2. Impact on traffic flow
    3. Recommended immediate actions
    4. Long-term infrastructure improvements
    5. Similar historical incidents
    
    Focus on actionable insights for city planners.
    """
```

## Theme & UI Customization

### Village Theme System

#### Design Philosophy:
- Nature-inspired colors
- High contrast for accessibility
- Responsive across devices
- Consistent component styling

#### Theme Variables:
```css
:root {
    /* Primary Colors */
    --village-pine: #2d5016;      /* Headers, primary buttons */
    --village-sage: #5a7c47;      /* Secondary elements */
    --village-beige: #f5f1e8;     /* Backgrounds */
    --village-brown: #8b4513;     /* Accents */
    
    /* Semantic Colors */
    --success: #28a745;
    --warning: #ffc107;
    --danger: #dc3545;
    --info: #17a2b8;
    
    /* Spacing */
    --spacing-unit: 8px;
    --border-radius: 8px;
}
```

#### Component Styling:
- Custom Streamlit components
- Material-UI integration
- Consistent iconography
- Responsive grid layouts

## Onboarding System

### User Onboarding Flow

#### First-Time Setup:
1. **Welcome Screen**
   - Platform introduction
   - Value proposition
   - Quick demo video

2. **Organization Setup**
   - Organization name
   - Domain configuration
   - Team size selection
   - Use case identification

3. **Initial Configuration**
   - Primary monitoring zones
   - Alert preferences
   - Report scheduling
   - Integration setup

4. **Tutorial System**
   - Interactive walkthroughs
   - Contextual help tooltips
   - Progress tracking
   - Achievement system

#### Onboarding Metrics:
```python
def track_onboarding_progress(user_id):
    """Monitor user progress through onboarding"""
    checkpoints = {
        "account_created": True,
        "organization_configured": True,
        "first_login": True,
        "viewed_dashboard": False,
        "created_first_report": False,
        "invited_team_member": False
    }
    completion_rate = sum(checkpoints.values()) / len(checkpoints)
    return completion_rate
```

## Background Services

### Traffic Collector Daemon

#### Service Architecture:
```python
class TrafficCollectorDaemon:
    def __init__(self, config_path):
        self.config = self.load_config(config_path)
        self.collection_queue = Queue()
        self.error_handler = ErrorHandler()
        self.scheduler = Scheduler()
    
    def run(self):
        """Main daemon loop"""
        while self.running:
            task = self.scheduler.get_next_task()
            self.execute_collection(task)
            self.handle_results()
```

#### Scheduling System:
- Cron-based scheduling
- Priority queue for zones
- Adaptive timing based on traffic
- Holiday/event adjustments

#### Error Recovery:
- Automatic retry with backoff
- Error notification system
- Fallback data sources
- Manual intervention alerts

---

# Utilities & Scripts

## Maintenance Scripts

### Data Initialization (initialize_data.py)

#### Purpose:
Seeds the database with initial data for development and testing.

#### Features:
- Synthetic incident generation
- Realistic traffic patterns
- Historical data creation
- Test user accounts

#### Usage:
```bash
python initialize_data.py --days 30 --incidents-per-day 50
```

### Emergency Controls

#### Emergency Stop (emergency_stop_collection.py)
```python
def emergency_stop():
    """Immediately halt all data collection"""
    # Stop all collectors
    collector_manager.stop_all()
    
    # Notify administrators
    send_admin_alert("Emergency stop activated")
    
    # Log the action
    audit_log.record("EMERGENCY_STOP", user_id, timestamp)
```

#### Credit Reset (reset_credit_flag.py)
Resets API credit exhaustion flags after quota renewal:
```python
def reset_credit_flags():
    """Reset credit exhaustion flags after adding quota"""
    db = DatabaseManager()
    db.execute("UPDATE api_status SET credit_exhausted = 0")
    db.execute("UPDATE api_status SET last_reset = CURRENT_TIMESTAMP")
    
    # Restart collectors
    collector_manager.restart_all()
```

### Monitoring Tools

#### API Status Checker (check_api_status.py)
```python
def check_all_services():
    """Comprehensive service health check"""
    services = {
        "tomtom_api": check_tomtom_api(),
        "perplexity_ai": check_perplexity_api(),
        "database": check_database_connection(),
        "redis": check_redis_connection(),
        "background_jobs": check_job_queue()
    }
    
    return {
        "timestamp": datetime.now(),
        "services": services,
        "overall_health": all(services.values())
    }
```

#### Credit Monitor (credit_monitor.py)
Real-time monitoring of API credit usage:
```python
def monitor_credits():
    """Monitor API credit usage and send alerts"""
    usage = get_current_usage()
    quota = get_daily_quota()
    percentage = (usage / quota) * 100
    
    if percentage > 90:
        send_critical_alert(f"API usage at {percentage}%")
    elif percentage > 75:
        send_warning_alert(f"API usage at {percentage}%")
```

## Database Management

### Schema Migrations

#### Migration System:
```python
class Migration:
    def __init__(self, version, description):
        self.version = version
        self.description = description
    
    def up(self):
        """Apply migration"""
        pass
    
    def down(self):
        """Rollback migration"""
        pass
```

#### Version Control:
- Sequential versioning
- Automatic rollback capability
- Migration history tracking
- Conflict detection

### Data Integrity

#### Validation Rules:
```python
VALIDATION_RULES = {
    "incidents": {
        "lat": lambda x: -90 <= x <= 90,
        "lng": lambda x: -180 <= x <= 180,
        "severity": lambda x: 1 <= x <= 5,
        "timestamp": lambda x: x <= datetime.now()
    }
}
```

#### Cleanup Procedures:
- Duplicate detection and removal
- Orphaned record cleanup
- Data consistency checks
- Archive old records

---

# Developer Resources

## Code Standards

### Project Structure:
```
village-platform/
├── code/
│   ├── main.py              # Entry point
│   ├── pages/               # UI pages
│   ├── utils/               # Shared utilities
│   └── tests/               # Test suite
├── data/                    # Local data storage
├── deploy/                  # Deployment configs
├── documentation/           # Project docs
└── scripts/                 # Maintenance scripts
```

### Coding Conventions:

#### Python Style:
- PEP 8 compliance
- Type hints for all functions
- Docstrings for public APIs
- Maximum line length: 100 chars

#### Naming Conventions:
```python
# Classes: PascalCase
class TrafficAnalyzer:
    pass

# Functions: snake_case
def calculate_congestion_level():
    pass

# Constants: UPPER_SNAKE_CASE
MAX_RETRY_ATTEMPTS = 3

# Private methods: leading underscore
def _internal_helper():
    pass
```

### TODO Management:
```python
# TODO: PRIORITY - CATEGORY - Description
# Categories: FEATURE, BUG, OPTIMIZATION, DOCUMENTATION
# Priorities: HIGH, MEDIUM, LOW

# TODO: HIGH - FEATURE - Implement WebSocket support
# TODO: MEDIUM - OPTIMIZATION - Cache analysis results
# TODO: LOW - DOCUMENTATION - Add API examples
```

## Testing & Verification

### Test Structure:
```
tests/
├── unit/           # Unit tests
├── integration/    # Integration tests
├── e2e/           # End-to-end tests
└── fixtures/      # Test data
```

### Testing Strategy:

#### Unit Tests:
```python
def test_incident_severity_calculation():
    """Test severity calculation logic"""
    incident = create_test_incident(
        delay_minutes=30,
        affected_roads=3
    )
    assert calculate_severity(incident) == 4
```

#### Integration Tests:
```python
def test_data_collection_pipeline():
    """Test complete data collection flow"""
    # Start collector
    collector = TrafficCollector()
    
    # Trigger collection
    results = collector.collect_zone("test_zone")
    
    # Verify storage
    assert database.get_incidents_count() > 0
```

### Verification Tools:

#### Auth Verification (verify_auth.py):
```python
def verify_authentication_flow():
    """Comprehensive auth system verification"""
    # Test user registration
    user = register_test_user()
    
    # Test login
    token = login_user(user.email, user.password)
    
    # Test token validation
    assert validate_token(token) == True
    
    # Test role-based access
    assert check_permission(user, "view_reports") == True
```

## Documentation Standards

### Code Documentation:

#### Function Documentation:
```python
def analyze_traffic_pattern(
    incidents: List[Incident],
    time_range: DateRange,
    zone: CollectionZone
) -> PatternAnalysis:
    """
    Analyze traffic patterns for strategic planning.
    
    This function performs comprehensive pattern analysis on traffic
    incidents within a specified time range and geographic zone.
    
    Args:
        incidents: List of traffic incidents to analyze
        time_range: Date range for analysis period
        zone: Geographic zone for spatial filtering
        
    Returns:
        PatternAnalysis object containing:
        - Temporal patterns (peak hours, day patterns)
        - Spatial clusters (hotspots, corridors)
        - Severity distributions
        - Recommendations for improvements
        
    Raises:
        ValueError: If time_range is invalid
        DataError: If insufficient data for analysis
        
    Example:
        >>> incidents = fetch_incidents(zone="downtown")
        >>> analysis = analyze_traffic_pattern(
        ...     incidents,
        ...     DateRange(start="2024-01-01", end="2024-01-31"),
        ...     zone="downtown"
        ... )
        >>> print(analysis.peak_hours)
        [7, 8, 17, 18]  # Morning and evening rush hours
    """
```

### API Documentation:

#### Endpoint Documentation:
```python
@app.route('/api/v1/incidents', methods=['GET'])
def get_incidents():
    """
    Retrieve traffic incidents with filtering options.
    
    Query Parameters:
        - start_date (str): ISO format date (YYYY-MM-DD)
        - end_date (str): ISO format date (YYYY-MM-DD)
        - severity_min (int): Minimum severity (1-5)
        - bbox (str): Bounding box (lat1,lng1,lat2,lng2)
        - limit (int): Maximum results (default: 1000)
        
    Returns:
        JSON response:
        {
            "incidents": [...],
            "count": 150,
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
    Status Codes:
        - 200: Success
        - 400: Invalid parameters
        - 401: Authentication required
        - 429: Rate limit exceeded
        - 500: Server error
    """
```

### Change Management:

#### Version History:
```python
"""
Version History:
- 1.0.0 (2024-01-01): Initial release
- 1.1.0 (2024-01-15): Added predictive analytics
- 1.2.0 (2024-02-01): Enterprise features
- 1.3.0 (2024-02-15): VM deployment support

Breaking Changes:
- 1.2.0: API authentication required
- 1.3.0: Database schema migration needed
"""
```

---

## Conclusion

The Village Platform represents a comprehensive solution for municipal traffic planning, combining real-time data collection, AI-powered analysis, and enterprise-grade features. This documentation provides a complete reference for developers, administrators, and contributors to understand, maintain, and extend the platform.

For additional support or questions, please contact the development team or refer to the project's GitHub repository.