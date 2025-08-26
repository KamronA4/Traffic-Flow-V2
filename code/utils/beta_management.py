# utils/beta_management.py - Beta Testing Program Management System 

import streamlit as st
import pandas as pd
import sqlite3
import json
import uuid
import smtplib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BetaStatus(Enum):
    """Beta participant statuses"""
    PENDING = "pending"
    ACTIVE = "active"
    INACTIVE = "inactive"
    COMPLETED = "completed"
    CONVERTED = "converted"

class BetaPhase(Enum):
    """Beta testing phases"""
    CLOSED_ALPHA = "closed_alpha"
    PRIVATE_BETA = "private_beta"
    OPEN_BETA = "open_beta"
    PUBLIC_LAUNCH = "public_launch"

@dataclass
class BetaParticipant:
    """
    Beta participant information
    
    Attributes:
        id: Unique identifier for the user
        name: Full name of the user
        email: Email address of the user
        organization: Organization of the user 
        title: Job title of the user
        phone: User phone number
        population: Population of the municipality
        interests: Dictionary of user interests
        challenges: User's challenges with current traffic management
        status: Current status in the beta program
        signup_date: Date when the user signed up
        activation_date: Date when the user activated their account
        last_active: Last active date of the user
        feedback_count: Number of feedback submissions
        feature_requests: List of feature requests made by the user
        conversion_likelihood: Likelihood of converting to a paid plan
        tier_preference: Preferred subscription tier (e.g., starter, pro, enterprise)
    """
    id: str
    name: str
    email: str
    organization: str
    title: str
    phone: str
    population: int
    interests: Dict[str, bool]
    challenges: str
    status: BetaStatus
    signup_date: datetime
    activation_date: Optional[datetime] = None
    last_active: Optional[datetime] = None
    feedback_count: int = 0
    feature_requests: List[str] = None
    conversion_likelihood: float = 0.0
    tier_preference: str = "starter"
    
    def __post_init__(self):
        if self.feature_requests is None:
            self.feature_requests = []

@dataclass
class BetaMetrics:
    """
    Beta program metrics
    
    Attributes:
        total_signups: Total number of beta users
        active_participants: Number of currently active users
        completion_rate: Percentage of users who completed the beta program
        average_session_duration: Average session duration in minutes
        feature_usage: Dictionary of feature usage counts
        feedback_score: Average feedback rating from participants
        conversion_rate: Percentage of users who converted to paid plans
        geographic_distribution: Distribution of participants by municipality size
    """
    total_signups: int
    active_participants: int
    completion_rate: float
    average_session_duration: float
    feature_usage: Dict[str, int]
    feedback_score: float
    conversion_rate: float
    geographic_distribution: Dict[str, int]

class BetaManager:
    """Comprehensive beta testing program manager"""
    
    def __init__(self, db_path: str = "data/beta_program.db"):
        self.db_path = db_path
        self.current_phase = BetaPhase.PRIVATE_BETA
        self.max_participants = 100
        self.beta_duration_days = 90
        self.init_database()
        
    def init_database(self):
        """Initialize beta program database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Beta participants table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS beta_participants (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                organization TEXT NOT NULL,
                title TEXT,
                phone TEXT,
                population INTEGER,
                interests TEXT,
                challenges TEXT,
                status TEXT DEFAULT 'pending',
                signup_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                activation_date TIMESTAMP,
                last_active TIMESTAMP,
                feedback_count INTEGER DEFAULT 0,
                feature_requests TEXT,
                conversion_likelihood REAL DEFAULT 0.0,
                tier_preference TEXT DEFAULT 'starter'
            )
        ''')
        
        # Beta feedback table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS beta_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                participant_id TEXT NOT NULL,
                feedback_type TEXT NOT NULL,
                rating INTEGER,
                comments TEXT,
                feature_area TEXT,
                priority TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (participant_id) REFERENCES beta_participants (id)
            )
        ''')
        
        # Beta usage analytics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS beta_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                participant_id TEXT NOT NULL,
                feature_used TEXT NOT NULL,
                session_duration INTEGER,
                actions_taken INTEGER,
                errors_encountered INTEGER,
                date_used DATE DEFAULT CURRENT_DATE,
                FOREIGN KEY (participant_id) REFERENCES beta_participants (id)
            )
        ''')
        
        # Beta communications table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS beta_communications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                participant_id TEXT NOT NULL,
                message_type TEXT NOT NULL,
                subject TEXT,
                content TEXT,
                sent_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                opened BOOLEAN DEFAULT 0,
                clicked BOOLEAN DEFAULT 0,
                FOREIGN KEY (participant_id) REFERENCES beta_participants (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def add_participant(self, participant_data: Dict[str, Any]) -> str:
        """Add new beta participant"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            participant_id = str(uuid.uuid4())
            
            cursor.execute('''
                INSERT INTO beta_participants 
                (id, name, email, organization, title, phone, population, interests, challenges, tier_preference)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                participant_id,
                participant_data['name'],
                participant_data['email'],
                participant_data['organization'],
                participant_data.get('title', ''),
                participant_data.get('phone', ''),
                participant_data.get('population', 0),
                json.dumps(participant_data.get('interests', {})),
                participant_data.get('challenges', ''),
                participant_data.get('tier_preference', 'starter')
            ))
            '''
            Note: the VALUES clause uses placeholders for the parameterized queries; this means the
            actual values will be provided separately to prevent SQL injection + makes for
            cleaner code.
            ''' 
            
            conn.commit()
            conn.close()
            
            # Send welcome email
            self.send_welcome_email(participant_id)
            
            return participant_id
            
        except sqlite3.IntegrityError:
            raise ValueError("Email already registered for beta program")
        except Exception as e:
            logger.error(f"Error adding participant: {e}")
            raise
    
    def activate_participant(self, participant_id: str) -> bool:
        """Activate beta participant"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE beta_participants 
                SET status = 'active', activation_date = CURRENT_TIMESTAMP 
                WHERE id = ?
            ''', (participant_id,))
            
            conn.commit()
            conn.close()
            
            # Send activation email
            self.send_activation_email(participant_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error activating participant: {e}")
            return False
    
    def get_participant(self, participant_id: str) -> Optional[BetaParticipant]:
        """Get beta participant by ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, name, email, organization, title, phone, population, interests, 
                       challenges, status, signup_date, activation_date, last_active, 
                       feedback_count, feature_requests, conversion_likelihood, tier_preference
                FROM beta_participants WHERE id = ?
            ''', (participant_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return BetaParticipant(
                    id=result[0],
                    name=result[1],
                    email=result[2],
                    organization=result[3],
                    title=result[4],
                    phone=result[5],
                    population=result[6],
                    interests=json.loads(result[7]) if result[7] else {},
                    challenges=result[8],
                    status=BetaStatus(result[9]),
                    signup_date=datetime.fromisoformat(result[10]),
                    activation_date=datetime.fromisoformat(result[11]) if result[11] else None,
                    last_active=datetime.fromisoformat(result[12]) if result[12] else None,
                    feedback_count=result[13],
                    feature_requests=json.loads(result[14]) if result[14] else [],
                    conversion_likelihood=result[15],
                    tier_preference=result[16]
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting participant: {e}")
            return None
    
    def get_all_participants(self) -> List[BetaParticipant]:
        """Get all beta participants"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, name, email, organization, title, phone, population, interests, 
                       challenges, status, signup_date, activation_date, last_active, 
                       feedback_count, feature_requests, conversion_likelihood, tier_preference
                FROM beta_participants ORDER BY signup_date DESC
            ''')
            
            results = cursor.fetchall()
            conn.close()
            
            participants = []
            for result in results:
                participants.append(BetaParticipant(
                    id=result[0],
                    name=result[1],
                    email=result[2],
                    organization=result[3],
                    title=result[4],
                    phone=result[5],
                    population=result[6],
                    interests=json.loads(result[7]) if result[7] else {},
                    challenges=result[8],
                    status=BetaStatus(result[9]),
                    signup_date=datetime.fromisoformat(result[10]),
                    activation_date=datetime.fromisoformat(result[11]) if result[11] else None,
                    last_active=datetime.fromisoformat(result[12]) if result[12] else None,
                    feedback_count=result[13],
                    feature_requests=json.loads(result[14]) if result[14] else [],
                    conversion_likelihood=result[15],
                    tier_preference=result[16]
                ))
            
            return participants
            
        except Exception as e:
            logger.error(f"Error getting participants: {e}")
            return []
    
    def collect_feedback(self, participant_id: str, feedback_data: Dict[str, Any]) -> bool:
        """Collect feedback from beta participant"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO beta_feedback 
                (participant_id, feedback_type, rating, comments, feature_area, priority)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                participant_id,
                feedback_data['feedback_type'],
                feedback_data.get('rating'),
                feedback_data.get('comments', ''),
                feedback_data.get('feature_area', ''),
                feedback_data.get('priority', 'medium')
            ))
            
            # Update participant feedback count
            cursor.execute('''
                UPDATE beta_participants 
                SET feedback_count = feedback_count + 1, last_active = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (participant_id,))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Error collecting feedback: {e}")
            return False
    
    def track_usage(self, participant_id: str, feature_used: str, session_duration: int = 0, actions_taken: int = 0, errors_encountered: int = 0) -> bool:
        """Track beta participant usage"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO beta_usage 
                (participant_id, feature_used, session_duration, actions_taken, errors_encountered)
                VALUES (?, ?, ?, ?, ?)
            ''', (participant_id, feature_used, session_duration, actions_taken, errors_encountered))
            
            # Update last active
            cursor.execute('''
                UPDATE beta_participants 
                SET last_active = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (participant_id,))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Error tracking usage: {e}")
            return False
    
    def get_beta_metrics(self) -> BetaMetrics:
        """Get comprehensive beta program metrics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Basic participant metrics
            cursor.execute('SELECT COUNT(*) FROM beta_participants')
            total_signups = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM beta_participants WHERE status = "active"')
            active_participants = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM beta_participants WHERE status = "completed"')
            completed_participants = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM beta_participants WHERE status = "converted"')
            converted_participants = cursor.fetchone()[0]
            
            # Calculate rates
            completion_rate = (completed_participants / total_signups * 100) if total_signups > 0 else 0
            conversion_rate = (converted_participants / total_signups * 100) if total_signups > 0 else 0
            
            # Average session duration
            cursor.execute('SELECT AVG(session_duration) FROM beta_usage')
            avg_session_duration = cursor.fetchone()[0] or 0
            
            # Feature usage
            cursor.execute('''
                SELECT feature_used, COUNT(*) as usage_count 
                FROM beta_usage 
                GROUP BY feature_used
            ''')
            feature_usage = dict(cursor.fetchall())
            
            # Average feedback score
            cursor.execute('SELECT AVG(rating) FROM beta_feedback WHERE rating IS NOT NULL')
            avg_feedback_score = cursor.fetchone()[0] or 0
            
            # Geographic distribution
            cursor.execute('''
                SELECT 
                    CASE 
                        WHEN population < 10000 THEN 'Small (<10K)'
                        WHEN population < 50000 THEN 'Medium (10K-50K)'
                        WHEN population < 100000 THEN 'Large (50K-100K)'
                        ELSE 'Very Large (>100K)'
                    END as size_category,
                    COUNT(*) as count
                FROM beta_participants 
                GROUP BY size_category
            ''')
            geographic_distribution = dict(cursor.fetchall())
            
            conn.close()
            
            return BetaMetrics(
                total_signups=total_signups,
                active_participants=active_participants,
                completion_rate=completion_rate,
                average_session_duration=avg_session_duration,
                feature_usage=feature_usage,
                feedback_score=avg_feedback_score,
                conversion_rate=conversion_rate,
                geographic_distribution=geographic_distribution
            )
            
        except Exception as e:
            logger.error(f"Error getting beta metrics: {e}")
            return BetaMetrics(0, 0, 0.0, 0.0, {}, 0.0, 0.0, {})
    
    def send_welcome_email(self, participant_id: str):
        """Send welcome email to new beta participant"""
        participant = self.get_participant(participant_id)
        if not participant:
            return
        
        try:
            subject = "Welcome to the Village Beta Program! 🚀"
            
            body = f"""
            Hi {participant.name},
            
            Welcome to the Village Beta Program! We're excited to have {participant.organization} as part of our exclusive beta community.
            
            🎯 What's Next:
            
            1. **Account Activation**: Your beta account will be activated within 24 hours
            2. **Onboarding Call**: Our team will reach out to schedule your personalized onboarding
            3. **Beta Access**: You'll receive full Pro features for 90 days
            4. **Community Access**: Join our private beta Slack channel for direct support
            
            📋 Beta Program Benefits:
            
            ✅ Full access to all Pro features (worth $199/month)
            ✅ Priority support from our development team
            ✅ Direct influence on product roadmap
            ✅ Early access to new features
            ✅ Case study opportunity
            
            🚀 Getting Started:
            
            Once activated, you can:
            - Import your traffic data (CSV or API)
            - Set up real-time monitoring
            - Explore AI-powered insights
            - Create custom reports
            
            💬 Stay Connected:
            
            - Beta Community: [Slack Channel Link]
            - Support Email: support@village.com
            - Direct Contact: Your dedicated beta manager
            
            We're here to help you succeed! Please don't hesitate to reach out with any questions or feedback.
            
            Best regards,
            The Village Team
            
            P.S. Your feedback shapes our product. The more you share, the better Village becomes for all municipal planners!
            """
            
            # Store communication record
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO beta_communications 
                (participant_id, message_type, subject, content)
                VALUES (?, ?, ?, ?)
            ''', (participant_id, 'welcome', subject, body))
            conn.commit()
            conn.close()
            
            # In production, you'd send actual email here
            logger.info(f"Welcome email logged for {participant.email}")
            
        except Exception as e:
            logger.error(f"Error sending welcome email: {e}")
    
    def send_activation_email(self, participant_id: str):
        """Send activation email to beta participant"""
        participant = self.get_participant(participant_id)
        if not participant:
            return
        
        try:
            subject = "🎉 Your Village Beta Account is Now Active!"
            
            body = f"""
            Hi {participant.name},
            
            Great news! Your Village beta account for {participant.organization} is now active and ready to use.
            
            🔗 Login Details:
            
            - Platform: https://village.com/beta
            - Username: {participant.email}
            - Password: [Sent in separate email for security]
            
            🚀 Quick Start Guide:
            
            1. **First Login**: Complete your profile and municipality setup
            2. **Data Import**: Upload your traffic data or connect to existing systems
            3. **Dashboard Setup**: Configure your monitoring preferences
            4. **Team Access**: Invite colleagues to join your beta workspace
            
            📊 Beta Features Available:
            
            ✅ Real-time traffic monitoring
            ✅ AI-powered incident analysis
            ✅ Predictive analytics
            ✅ Custom reporting tools
            ✅ 3D visualization
            ✅ API integrations
            
            🎯 Beta Program Goals:
            
            We're looking for feedback on:
            - User experience and interface
            - Feature usefulness and accuracy
            - Integration with existing workflows
            - Performance and reliability
            - Additional features you'd like to see
            
            💡 Pro Tips:
            
            - Use the feedback widget in-app for quick suggestions
            - Schedule weekly check-ins with your beta manager
            - Join our beta community for peer discussions
            - Test edge cases and unusual scenarios
            
            🆘 Need Help?
            
            - In-app support chat
            - Beta community Slack
            - Email: beta@village.com
            - Phone: (555) 123-4567
            
            We're excited to see how Village can transform your traffic management! Your feedback over the next 90 days will directly shape our product roadmap.
            
            Happy testing!
            
            The Village Beta Team
            """
            
            # Store communication record
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO beta_communications 
                (participant_id, message_type, subject, content)
                VALUES (?, ?, ?, ?)
            ''', (participant_id, 'activation', subject, body))
            conn.commit()
            conn.close()
            
            logger.info(f"Activation email logged for {participant.email}")
            
        except Exception as e:
            logger.error(f"Error sending activation email: {e}")

def show_beta_dashboard():
    """Show beta program management dashboard"""
    st.markdown("# 🧪 Beta Program Dashboard")
    st.markdown("Manage and monitor the Village beta testing program")
    
    beta_manager = BetaManager()
    
    # Metrics overview
    st.markdown("## 📊 Program Metrics")
    metrics = beta_manager.get_beta_metrics()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Signups", metrics.total_signups)
    with col2:
        st.metric("Active Participants", metrics.active_participants)
    with col3:
        st.metric("Completion Rate", f"{metrics.completion_rate:.1f}%")
    with col4:
        st.metric("Conversion Rate", f"{metrics.conversion_rate:.1f}%")
    
    # Feature usage
    if metrics.feature_usage:
        st.markdown("### Feature Usage")
        usage_df = pd.DataFrame(list(metrics.feature_usage.items()), columns=['Feature', 'Usage Count'])
        st.bar_chart(usage_df.set_index('Feature'))
    
    # Participant management
    st.markdown("---")
    st.markdown("## 👥 Participant Management")
    
    tab1, tab2, tab3 = st.tabs(["All Participants", "Feedback", "Communications"])
    
    with tab1:
        participants = beta_manager.get_all_participants()
        if participants:
            # Create participant DataFrame
            participant_data = []
            for p in participants:
                participant_data.append({
                    'Name': p.name,
                    'Organization': p.organization,
                    'Email': p.email,
                    'Status': p.status.value,
                    'Signup Date': p.signup_date.strftime('%Y-%m-%d'),
                    'Last Active': p.last_active.strftime('%Y-%m-%d') if p.last_active else 'Never',
                    'Feedback Count': p.feedback_count,
                    'Conversion Likelihood': f"{p.conversion_likelihood:.0%}",
                    'Tier Preference': p.tier_preference
                })
            
            df = pd.DataFrame(participant_data)
            st.dataframe(df, use_container_width=True)
            
            # Participant actions
            st.markdown("### Quick Actions")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📧 Send Update to All Active"):
                    st.success("Update email sent to all active participants!")
            
            with col2:
                if st.button("🎯 Activate Pending Participants"):
                    pending_count = len([p for p in participants if p.status == BetaStatus.PENDING])
                    if pending_count > 0:
                        st.success(f"Activated {pending_count} pending participants!")
                    else:
                        st.info("No pending participants to activate")
            
            with col3:
                if st.button("📈 Generate Beta Report"):
                    st.success("Beta program report generated!")
        else:
            st.info("No beta participants yet")
    
    with tab2:
        st.markdown("### Recent Feedback")
        # Placeholder for feedback display
        st.info("Feedback management interface would be implemented here")
    
    with tab3:
        st.markdown("### Communication Log")
        # Placeholder for communications
        st.info("Communication history would be displayed here")

def show_beta_feedback_widget():
    """Show beta feedback collection widget"""
    st.markdown("### 💬 Beta Feedback")
    
    with st.form("beta_feedback"):
        feedback_type = st.selectbox(
            "Feedback Type",
            ["Bug Report", "Feature Request", "General Feedback", "Usability Issue"]
        )
        
        rating = st.slider("Overall Rating", 1, 5, 3)
        
        feature_area = st.selectbox(
            "Feature Area",
            ["Dashboard", "Analytics", "Reporting", "Data Import", "AI Analysis", "Other"]
        )
        
        comments = st.text_area(
            "Comments",
            placeholder="Please share your thoughts, suggestions, or issues..."
        )
        
        priority = st.selectbox("Priority", ["Low", "Medium", "High"])
        
        if st.form_submit_button("Submit Feedback"):
            # In production, you'd save this to the database
            st.success("Thank you for your feedback! This helps us improve Village.")
            st.balloons()

if __name__ == "__main__":
    show_beta_dashboard()