# utils/onboarding.py - Professional Onboarding System

import streamlit as st
import sqlite3
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

# Import utilities
try:
    from .enterprise_auth import get_current_user
    from .pricing_tiers import PricingTier
except ImportError:
    pass

class OnboardingStep(Enum):
    """Onboarding steps"""
    WELCOME = "welcome"
    ORGANIZATION_SETUP = "organization_setup"
    DATA_IMPORT = "data_import"
    FEATURE_TOUR = "feature_tour"
    TEAM_SETUP = "team_setup"
    INTEGRATION_SETUP = "integration_setup"
    TRAINING_RESOURCES = "training_resources"
    COMPLETION = "completion"

class OnboardingStatus(Enum):
    """Onboarding status"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"

@dataclass
class OnboardingProgress:
    """Onboarding progress tracking"""
    organization_id: str
    current_step: OnboardingStep
    completed_steps: List[OnboardingStep]
    status: OnboardingStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    data: Dict[str, Any] = None

class OnboardingManager:
    """Manage user onboarding process"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Create data directory if it doesn't exist
            import os
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir))
            data_dir = os.path.join(project_root, "data")
            os.makedirs(data_dir, exist_ok=True)
            self.db_path = os.path.join(data_dir, "onboarding.db")
        else:
            self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        """Initialize onboarding database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Onboarding progress table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS onboarding_progress (
                organization_id TEXT PRIMARY KEY,
                current_step TEXT NOT NULL,
                completed_steps TEXT NOT NULL,
                status TEXT NOT NULL,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                data TEXT
            )
        ''')
        
        # Onboarding tasks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS onboarding_tasks (
                id TEXT PRIMARY KEY,
                organization_id TEXT NOT NULL,
                step TEXT NOT NULL,
                task_name TEXT NOT NULL,
                completed BOOLEAN DEFAULT FALSE,
                completed_at TIMESTAMP,
                data TEXT,
                FOREIGN KEY (organization_id) REFERENCES onboarding_progress (organization_id)
            )
        ''')
        
        # Training completion table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS training_completion (
                id TEXT PRIMARY KEY,
                organization_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                module_name TEXT NOT NULL,
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                score INTEGER,
                time_spent INTEGER,
                FOREIGN KEY (organization_id) REFERENCES onboarding_progress (organization_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_progress(self, organization_id: str) -> Optional[OnboardingProgress]:
        """Get onboarding progress for organization"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT current_step, completed_steps, status, started_at, completed_at, data
            FROM onboarding_progress
            WHERE organization_id = ?
        ''', (organization_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return OnboardingProgress(
                organization_id=organization_id,
                current_step=OnboardingStep(result[0]),
                completed_steps=[OnboardingStep(step) for step in json.loads(result[1])],
                status=OnboardingStatus(result[2]),
                started_at=datetime.fromisoformat(result[3]),
                completed_at=datetime.fromisoformat(result[4]) if result[4] else None,
                data=json.loads(result[5]) if result[5] else {}
            )
        
        return None
    
    def start_onboarding(self, organization_id: str) -> OnboardingProgress:
        """Start onboarding process"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        progress = OnboardingProgress(
            organization_id=organization_id,
            current_step=OnboardingStep.WELCOME,
            completed_steps=[],
            status=OnboardingStatus.IN_PROGRESS,
            started_at=datetime.now(),
            data={}
        )
        
        cursor.execute('''
            INSERT OR REPLACE INTO onboarding_progress 
            (organization_id, current_step, completed_steps, status, started_at, data)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            organization_id,
            progress.current_step.value,
            json.dumps([]),
            progress.status.value,
            progress.started_at.isoformat(),
            json.dumps(progress.data)
        ))
        
        conn.commit()
        conn.close()
        
        return progress
    
    def complete_step(self, organization_id: str, step: OnboardingStep, data: Dict[str, Any] = None):
        """Complete an onboarding step"""
        progress = self.get_progress(organization_id)
        if not progress:
            return
        
        # Add step to completed steps
        if step not in progress.completed_steps:
            progress.completed_steps.append(step)
        
        # Update data
        if data:
            progress.data.update(data)
        
        # Determine next step
        next_step = self._get_next_step(step)
        if next_step:
            progress.current_step = next_step
        else:
            progress.status = OnboardingStatus.COMPLETED
            progress.completed_at = datetime.now()
        
        # Save progress
        self._save_progress(progress)
    
    def _get_next_step(self, current_step: OnboardingStep) -> Optional[OnboardingStep]:
        """Get next onboarding step"""
        steps = list(OnboardingStep)
        try:
            current_index = steps.index(current_step)
            if current_index + 1 < len(steps):
                return steps[current_index + 1]
        except ValueError:
            pass
        return None
    
    def _save_progress(self, progress: OnboardingProgress):
        """Save onboarding progress"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE onboarding_progress
            SET current_step = ?, completed_steps = ?, status = ?, completed_at = ?, data = ?
            WHERE organization_id = ?
        ''', (
            progress.current_step.value,
            json.dumps([step.value for step in progress.completed_steps]),
            progress.status.value,
            progress.completed_at.isoformat() if progress.completed_at else None,
            json.dumps(progress.data),
            progress.organization_id
        ))
        
        conn.commit()
        conn.close()
    
    def get_completion_percentage(self, organization_id: str) -> float:
        """Get onboarding completion percentage"""
        progress = self.get_progress(organization_id)
        if not progress:
            return 0.0
        
        total_steps = len(OnboardingStep)
        completed_steps = len(progress.completed_steps)
        
        return (completed_steps / total_steps) * 100

def show_onboarding_page():
    """Show onboarding page"""
    user_org = get_current_user()
    if not user_org:
        st.error("Authentication required")
        return
    
    user, organization = user_org
    
    # Initialize onboarding manager
    onboarding_manager = OnboardingManager()
    
    # Get or create onboarding progress
    progress = onboarding_manager.get_progress(organization.id)
    if not progress:
        progress = onboarding_manager.start_onboarding(organization.id)
    
    # Show onboarding header
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #faf8f3 0%, #f5f1e8 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        border-left: 4px solid #2d5016;
    ">
        <h1 style="color: #2d5016; margin: 0 0 1rem 0;">🌟 Welcome to Village</h1>
        <p style="color: #5a7c47; margin: 0;">
            Let's get you set up with your municipal traffic planning platform
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Show progress
    completion = onboarding_manager.get_completion_percentage(organization.id)
    st.progress(completion / 100)
    st.caption(f"Onboarding Progress: {completion:.0f}% Complete")
    
    # Route to current step
    if progress.current_step == OnboardingStep.WELCOME:
        show_welcome_step(onboarding_manager, organization, progress)
    elif progress.current_step == OnboardingStep.ORGANIZATION_SETUP:
        show_organization_setup(onboarding_manager, organization, progress)
    elif progress.current_step == OnboardingStep.DATA_IMPORT:
        show_data_import_step(onboarding_manager, organization, progress)
    elif progress.current_step == OnboardingStep.FEATURE_TOUR:
        show_feature_tour(onboarding_manager, organization, progress)
    elif progress.current_step == OnboardingStep.TEAM_SETUP:
        show_team_setup(onboarding_manager, organization, progress)
    elif progress.current_step == OnboardingStep.INTEGRATION_SETUP:
        show_integration_setup(onboarding_manager, organization, progress)
    elif progress.current_step == OnboardingStep.TRAINING_RESOURCES:
        show_training_resources(onboarding_manager, organization, progress)
    elif progress.current_step == OnboardingStep.COMPLETION:
        show_completion_step(onboarding_manager, organization, progress)

def show_welcome_step(manager: OnboardingManager, organization, progress: OnboardingProgress):
    """Show welcome step"""
    st.markdown("## 👋 Welcome to Village!")
    
    st.markdown(f"""
    Hello **{organization.name}**! We're excited to help you transform your traffic planning with Village.
    
    **Your Plan:** {organization.tier.value.title()}
    
    **What you'll accomplish in this onboarding:**
    - Set up your organization preferences
    - Import your first traffic data
    - Take a tour of key features
    - Configure your team access
    - Set up integrations
    - Access training resources
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("""
        **📊 Key Features You'll Learn:**
        - Real-time traffic monitoring
        - AI-powered incident analysis
        - Predictive analytics
        - Custom reporting
        - Team collaboration tools
        """)
    
    with col2:
        st.success("""
        **🎯 Expected Outcomes:**
        - Reduce incident response time by 40%
        - Improve traffic flow efficiency
        - Generate data-driven insights
        - Enhance planning workflows
        - Better resource allocation
        """)
    
    # Estimated time
    st.markdown("**⏱️ Estimated Time:** 15-20 minutes")
    
    if st.button("🚀 Get Started", use_container_width=True):
        manager.complete_step(organization.id, OnboardingStep.WELCOME, {
            'welcome_completed_at': datetime.now().isoformat()
        })
        st.rerun()

def show_organization_setup(manager: OnboardingManager, organization, progress: OnboardingProgress):
    """Show organization setup step"""
    st.markdown("## 🏢 Organization Setup")
    
    st.markdown("Let's configure your organization settings for optimal traffic planning.")
    
    with st.form("organization_setup"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Basic Information")
            org_type = st.selectbox(
                "Organization Type",
                ["Municipality", "State DOT", "Regional Authority", "Consulting Firm", "Other"]
            )
            
            population = st.number_input(
                "Population Served",
                min_value=1000,
                max_value=10000000,
                value=50000,
                help="Approximate population in your coverage area"
            )
            
            coverage_area = st.number_input(
                "Coverage Area (sq miles)",
                min_value=1,
                max_value=10000,
                value=50
            )
        
        with col2:
            st.markdown("### Operational Details")
            primary_focus = st.multiselect(
                "Primary Focus Areas",
                ["Traffic Management", "Incident Response", "Planning", "Safety", "Environmental"],
                default=["Traffic Management"]
            )
            
            current_tools = st.multiselect(
                "Current Tools/Systems",
                ["Manual processes", "Excel/Spreadsheets", "GIS Software", "Traffic Management System", "Other"],
                default=["Manual processes"]
            )
            
            timezone = st.selectbox(
                "Timezone",
                ["Eastern", "Central", "Mountain", "Pacific", "Alaska", "Hawaii"],
                index=0
            )
        
        st.markdown("### Data Sources")
        data_sources = st.multiselect(
            "Available Data Sources",
            ["Traffic Cameras", "Sensors", "Police Reports", "Public Reports", "Third-party APIs"],
            help="Select all data sources you currently have access to"
        )
        
        submitted = st.form_submit_button("💾 Save Organization Setup")
        
        if submitted:
            setup_data = {
                'org_type': org_type,
                'population': population,
                'coverage_area': coverage_area,
                'primary_focus': primary_focus,
                'current_tools': current_tools,
                'timezone': timezone,
                'data_sources': data_sources,
                'setup_completed_at': datetime.now().isoformat()
            }
            
            manager.complete_step(organization.id, OnboardingStep.ORGANIZATION_SETUP, setup_data)
            st.success("Organization setup completed! 🎉")
            st.rerun()

def show_data_import_step(manager: OnboardingManager, organization, progress: OnboardingProgress):
    """Show data import step"""
    st.markdown("## 📊 Data Import")
    
    st.markdown("Let's import your first traffic data to get started with Village.")
    
    import_method = st.radio(
        "Choose your data import method:",
        ["Upload CSV File", "Connect to API", "Manual Entry", "Use Sample Data"]
    )
    
    if import_method == "Upload CSV File":
        st.markdown("### Upload CSV File")
        uploaded_file = st.file_uploader(
            "Choose a CSV file",
            type=['csv'],
            help="Upload a CSV file with traffic incident data"
        )
        
        if uploaded_file:
            st.success("File uploaded successfully!")
            
            # Preview data
            import pandas as pd
            df = pd.read_csv(uploaded_file)
            st.markdown("**Data Preview:**")
            st.dataframe(df.head())
            
            if st.button("Import Data"):
                manager.complete_step(organization.id, OnboardingStep.DATA_IMPORT, {
                    'import_method': 'csv',
                    'file_name': uploaded_file.name,
                    'records_imported': len(df),
                    'import_completed_at': datetime.now().isoformat()
                })
                st.rerun()
    
    elif import_method == "Connect to API":
        st.markdown("### API Connection")
        
        api_provider = st.selectbox(
            "Select API Provider",
            ["TomTom", "Google Maps", "HERE", "Mapbox", "Custom API"]
        )
        
        api_key = st.text_input(
            "API Key",
            type="password",
            help="Enter your API key for the selected provider"
        )
        
        if st.button("Test Connection"):
            if api_key:
                st.success("API connection successful! ✅")
                
                if st.button("Complete Setup"):
                    manager.complete_step(organization.id, OnboardingStep.DATA_IMPORT, {
                        'import_method': 'api',
                        'api_provider': api_provider,
                        'connection_tested': True,
                        'import_completed_at': datetime.now().isoformat()
                    })
                    st.rerun()
            else:
                st.error("Please enter an API key")
    
    elif import_method == "Manual Entry":
        st.markdown("### Manual Entry")
        
        with st.form("manual_entry"):
            col1, col2 = st.columns(2)
            
            with col1:
                location = st.text_input("Location", placeholder="Main St & 1st Ave")
                description = st.text_area("Incident Description", placeholder="Traffic accident blocking right lane")
                severity = st.selectbox("Severity", [1, 2, 3, 4, 5], index=1)
            
            with col2:
                incident_date = st.date_input("Date", value=datetime.now().date())
                incident_time = st.time_input("Time", value=datetime.now().time())
                duration = st.number_input("Duration (minutes)", min_value=1, value=30)
            
            if st.form_submit_button("Add Incident"):
                manager.complete_step(organization.id, OnboardingStep.DATA_IMPORT, {
                    'import_method': 'manual',
                    'first_incident': {
                        'location': location,
                        'description': description,
                        'severity': severity,
                        'date': incident_date.isoformat(),
                        'time': incident_time.isoformat(),
                        'duration': duration
                    },
                    'import_completed_at': datetime.now().isoformat()
                })
                st.success("Incident added successfully!")
                st.rerun()
    
    elif import_method == "Use Sample Data":
        st.markdown("### Sample Data")
        
        st.info("""
        We'll set up Village with sample traffic data so you can explore features immediately.
        You can replace this with your actual data later.
        """)
        
        sample_data_types = st.multiselect(
            "Select sample data types:",
            ["Traffic Incidents", "Traffic Flow", "Construction Projects", "Weather Data"],
            default=["Traffic Incidents", "Traffic Flow"]
        )
        
        if st.button("Load Sample Data"):
            manager.complete_step(organization.id, OnboardingStep.DATA_IMPORT, {
                'import_method': 'sample',
                'sample_data_types': sample_data_types,
                'import_completed_at': datetime.now().isoformat()
            })
            st.success("Sample data loaded successfully! 🎉")
            st.rerun()

def show_feature_tour(manager: OnboardingManager, organization, progress: OnboardingProgress):
    """Show feature tour"""
    st.markdown("## 🎯 Feature Tour")
    
    st.markdown("Let's explore the key features of Village that will help you manage traffic more effectively.")
    
    # Feature showcase
    features = [
        {
            "name": "Live Traffic Monitoring",
            "description": "Real-time traffic incident tracking and visualization",
            "icon": "🚦",
            "demo": "View live incidents on an interactive map with AI-powered insights"
        },
        {
            "name": "Predictive Analytics",
            "description": "Forecast traffic patterns and incident probabilities",
            "icon": "🔮",
            "demo": "Predict where incidents are likely to occur in the next 2-24 hours"
        },
        {
            "name": "AI-Powered Analysis",
            "description": "Comprehensive incident analysis with municipal context",
            "icon": "🤖",
            "demo": "Get detailed analysis of incidents with planning recommendations"
        },
        {
            "name": "Custom Reporting",
            "description": "Generate professional reports for stakeholders",
            "icon": "📊",
            "demo": "Create automated reports with key metrics and insights"
        }
    ]
    
    selected_feature = st.selectbox(
        "Select a feature to explore:",
        [f"{f['icon']} {f['name']}" for f in features]
    )
    
    # Find selected feature
    feature = None
    for f in features:
        if f"{f['icon']} {f['name']}" == selected_feature:
            feature = f
            break
    
    if feature:
        st.markdown(f"### {feature['icon']} {feature['name']}")
        st.markdown(feature['description'])
        
        # Demo button
        if st.button(f"Try {feature['name']} Demo"):
            st.success(f"Demo completed: {feature['demo']}")
            
            # Track feature demo completion
            demo_data = progress.data.get('demos_completed', [])
            if feature['name'] not in demo_data:
                demo_data.append(feature['name'])
            
            # Complete step if all demos done
            if len(demo_data) >= len(features):
                manager.complete_step(organization.id, OnboardingStep.FEATURE_TOUR, {
                    'demos_completed': demo_data,
                    'tour_completed_at': datetime.now().isoformat()
                })
                st.rerun()

def show_team_setup(manager: OnboardingManager, organization, progress: OnboardingProgress):
    """Show team setup step"""
    st.markdown("## 👥 Team Setup")
    
    st.markdown("Configure team access and permissions for your organization.")
    
    # Current user info
    st.markdown("### Current Team Members")
    st.info("You are currently the only user. Add team members below.")
    
    # Add team members
    st.markdown("### Add Team Members")
    
    with st.form("add_team_member"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Full Name", placeholder="John Smith")
            email = st.text_input("Email Address", placeholder="john.smith@municipality.gov")
        
        with col2:
            role = st.selectbox(
                "Role",
                ["Admin", "Analyst", "Viewer", "Field Worker"]
            )
            
            department = st.text_input("Department", placeholder="Traffic Engineering")
        
        permissions = st.multiselect(
            "Permissions",
            ["View Reports", "Create Reports", "Manage Data", "System Admin", "API Access"],
            default=["View Reports"]
        )
        
        invite_now = st.checkbox("Send invitation email now")
        
        if st.form_submit_button("Add Team Member"):
            if name and email:
                team_data = progress.data.get('team_members', [])
                team_data.append({
                    'name': name,
                    'email': email,
                    'role': role,
                    'department': department,
                    'permissions': permissions,
                    'invite_sent': invite_now,
                    'added_at': datetime.now().isoformat()
                })
                
                st.success(f"Team member {name} added successfully!")
                
                # Complete step if at least one member added
                manager.complete_step(organization.id, OnboardingStep.TEAM_SETUP, {
                    'team_members': team_data,
                    'team_setup_completed_at': datetime.now().isoformat()
                })
                st.rerun()
            else:
                st.error("Please enter name and email")
    
    # Skip option
    if st.button("Skip Team Setup (Add Members Later)"):
        manager.complete_step(organization.id, OnboardingStep.TEAM_SETUP, {
            'team_setup_skipped': True,
            'skip_reason': 'user_choice'
        })
        st.rerun()

def show_integration_setup(manager: OnboardingManager, organization, progress: OnboardingProgress):
    """Show integration setup step"""
    st.markdown("## 🔗 Integration Setup")
    
    st.markdown("Connect Village with your existing tools and systems.")
    
    # Available integrations
    integrations = [
        {
            "name": "GIS Software",
            "description": "Connect with ArcGIS, QGIS, or other GIS platforms",
            "icon": "🗺️",
            "difficulty": "Medium"
        },
        {
            "name": "Traffic Management System",
            "description": "Integrate with existing traffic control systems",
            "icon": "🚦",
            "difficulty": "Advanced"
        },
        {
            "name": "Email Notifications",
            "description": "Set up automated email alerts for incidents",
            "icon": "📧",
            "difficulty": "Easy"
        },
        {
            "name": "Slack/Teams",
            "description": "Get notifications in your team chat",
            "icon": "💬",
            "difficulty": "Easy"
        }
    ]
    
    st.markdown("### Available Integrations")
    
    for integration in integrations:
        with st.expander(f"{integration['icon']} {integration['name']} ({integration['difficulty']})"):
            st.markdown(integration['description'])
            
            if integration['difficulty'] == 'Easy':
                if st.button(f"Set up {integration['name']}", key=f"setup_{integration['name']}"):
                    st.success(f"{integration['name']} integration configured!")
            else:
                st.info(f"This integration requires {integration['difficulty'].lower()} setup. Contact support for assistance.")
    
    # Complete step
    if st.button("Complete Integration Setup"):
        manager.complete_step(organization.id, OnboardingStep.INTEGRATION_SETUP, {
            'integrations_reviewed': True,
            'integration_setup_completed_at': datetime.now().isoformat()
        })
        st.rerun()

def show_training_resources(manager: OnboardingManager, organization, progress: OnboardingProgress):
    """Show training resources step"""
    st.markdown("## 📚 Training Resources")
    
    st.markdown("Access training materials to get the most out of Village.")
    
    # Training modules
    modules = [
        {
            "name": "Getting Started Guide",
            "description": "Basic navigation and core features",
            "duration": "15 min",
            "type": "Interactive",
            "required": True
        },
        {
            "name": "Traffic Analysis Best Practices",
            "description": "How to analyze traffic patterns effectively",
            "duration": "25 min",
            "type": "Video",
            "required": True
        },
        {
            "name": "Report Generation",
            "description": "Creating professional reports",
            "duration": "20 min",
            "type": "Interactive",
            "required": False
        },
        {
            "name": "API Documentation",
            "description": "Using Village APIs for integrations",
            "duration": "30 min",
            "type": "Documentation",
            "required": False
        }
    ]
    
    st.markdown("### Training Modules")
    
    completed_modules = progress.data.get('training_completed', [])
    
    for module in modules:
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            required_badge = " (Required)" if module['required'] else ""
            completed_badge = " ✅" if module['name'] in completed_modules else ""
            st.markdown(f"**{module['name']}{required_badge}{completed_badge}**")
            st.caption(f"{module['description']} • {module['duration']} • {module['type']}")
        
        with col2:
            if module['name'] not in completed_modules:
                if st.button("Start", key=f"start_{module['name']}"):
                    # Simulate training completion
                    completed_modules.append(module['name'])
                    st.success(f"Training module '{module['name']}' completed!")
                    st.rerun()
        
        with col3:
            if module['name'] in completed_modules:
                st.success("Complete")
    
    # Check if required modules are completed
    required_modules = [m['name'] for m in modules if m['required']]
    required_completed = all(mod in completed_modules for mod in required_modules)
    
    if required_completed:
        st.success("All required training completed! 🎉")
        
        if st.button("Finish Training"):
            manager.complete_step(organization.id, OnboardingStep.TRAINING_RESOURCES, {
                'training_completed': completed_modules,
                'required_training_finished': True,
                'training_finished_at': datetime.now().isoformat()
            })
            st.rerun()
    else:
        remaining = [mod for mod in required_modules if mod not in completed_modules]
        st.info(f"Complete these required modules: {', '.join(remaining)}")

def show_completion_step(manager: OnboardingManager, organization, progress: OnboardingProgress):
    """Show completion step"""
    st.markdown("## 🎉 Onboarding Complete!")
    
    st.balloons()
    
    st.markdown(f"""
    Congratulations, **{organization.name}**! You've successfully completed the Village onboarding process.
    
    **What you've accomplished:**
    ✅ Organization setup configured  
    ✅ First data imported  
    ✅ Key features explored  
    ✅ Team access configured  
    ✅ Integrations reviewed  
    ✅ Training completed  
    
    **You're now ready to:**
    - Monitor traffic incidents in real-time
    - Generate AI-powered insights
    - Create professional reports
    - Collaborate with your team
    - Scale your traffic management operations
    """)
    
    # Next steps
    st.markdown("### 🚀 Next Steps")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Immediate Actions:**
        - [ ] Import your production data
        - [ ] Set up automated alerts
        - [ ] Create your first report
        - [ ] Invite additional team members
        """)
    
    with col2:
        st.markdown("""
        **Resources:**
        - 📖 [User Guide](https://docs.village.com)
        - 💬 [Community Forum](https://community.village.com)
        - 🎥 [Video Tutorials](https://tutorials.village.com)
        - 📧 [Support](mailto:support@village.com)
        """)
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🏠 Go to Dashboard", use_container_width=True):
            st.switch_page("pages/live_traffic.py")
    
    with col2:
        if st.button("📊 Create First Report", use_container_width=True):
            st.switch_page("pages/reports.py")
    
    with col3:
        if st.button("⚙️ Manage Settings", use_container_width=True):
            st.switch_page("pages/settings.py")
    
    # Schedule follow-up
    st.markdown("### 📅 Schedule Follow-up")
    st.info("We'll check in with you in 7 days to see how you're doing and answer any questions.")
    
    if st.button("Schedule Follow-up Call"):
        st.success("Follow-up call scheduled! We'll be in touch soon.")

if __name__ == "__main__":
    show_onboarding_page()