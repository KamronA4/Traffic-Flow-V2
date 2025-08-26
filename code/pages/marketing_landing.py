# pages/marketing_landing.py - Marketing Landing Page for Pre-Launch

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import sqlite3
from typing import Dict, List, Optional, Any
import uuid

# Import theme manager
try:
    from utils.theme_manager import apply_village_theme, create_village_header, get_village_colors
except ImportError:
    st.error("Theme manager not available")

def show_marketing_landing():
    """Show marketing landing page for pre-launch"""
    
    # Apply Village theme
    apply_village_theme()
    
    # Configure page
    st.set_page_config(
        page_title="Village - Municipal Traffic Planning Platform",
        page_icon="🌲",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Custom CSS for landing page
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(135deg, #2d5016 0%, #5a7c47 50%, #8b4513 100%);
        color: white;
        padding: 4rem 2rem;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 3rem;
        box-shadow: 0 8px 32px rgba(0,0,0,0.2);
    }
    
    .hero-title {
        font-size: 3.5rem;
        font-weight: 700;
        margin-bottom: 1rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .hero-subtitle {
        font-size: 1.5rem;
        margin-bottom: 2rem;
        opacity: 0.9;
    }
    
    .cta-button {
        background: linear-gradient(45deg, #faf8f3 0%, #f5f1e8 100%);
        color: #2d5016;
        padding: 1rem 2rem;
        border-radius: 50px;
        font-size: 1.2rem;
        font-weight: 600;
        text-decoration: none;
        display: inline-block;
        margin: 0.5rem;
        transition: all 0.3s ease;
        border: none;
        cursor: pointer;
    }
    
    .cta-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }
    
    .feature-card {
        background: linear-gradient(135deg, #faf8f3 0%, #f5f1e8 100%);
        padding: 2rem;
        border-radius: 15px;
        margin: 1rem 0;
        border-left: 4px solid #5a7c47;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        transition: transform 0.3s ease;
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }
    
    .stats-container {
        background: linear-gradient(135deg, #f5f1e8 0%, #faf8f3 100%);
        padding: 2rem;
        border-radius: 15px;
        margin: 2rem 0;
        text-align: center;
    }
    
    .stat-number {
        font-size: 3rem;
        font-weight: 700;
        color: #2d5016;
        margin: 0;
    }
    
    .stat-label {
        font-size: 1.1rem;
        color: #5a7c47;
        margin-top: 0.5rem;
    }
    
    .testimonial {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        margin: 1rem 0;
        border-left: 4px solid #8b4513;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        font-style: italic;
    }
    
    .early-access-form {
        background: linear-gradient(135deg, #2d5016 0%, #5a7c47 100%);
        color: white;
        padding: 3rem;
        border-radius: 20px;
        margin: 3rem 0;
        text-align: center;
    }
    
    .comparison-table {
        background: white;
        border-radius: 15px;
        padding: 2rem;
        margin: 2rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .hidden {
        display: none;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Hero Section
    st.markdown("""
    <div class="main-header">
        <h1 class="hero-title">🌲 Village</h1>
        <p class="hero-subtitle">The AI-Powered Municipal Traffic Planning Platform</p>
        <p style="font-size: 1.2rem; margin-bottom: 2rem;">
            Transform your traffic management with intelligent analytics, predictive insights, and real-time monitoring
        </p>
        <div>
            <button class="cta-button" onclick="document.getElementById('early-access').scrollIntoView()">
                🚀 Join the Beta
            </button>
            <button class="cta-button" onclick="document.getElementById('demo').scrollIntoView()">
                📺 Watch Demo
            </button>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Problem Statement
    st.markdown("""
    ## 🚨 The Challenge Facing Municipal Traffic Management
    
    Municipal traffic departments are struggling with outdated tools and reactive approaches:
    """)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h3 style="color: #2d5016;">📊 Legacy GIS Systems</h3>
            <p>Expensive, complex tools that take months to implement and require specialized training</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h3 style="color: #2d5016;">⏰ Reactive Management</h3>
            <p>Most municipalities can only respond to incidents after they occur, missing prevention opportunities</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <h3 style="color: #2d5016;">💸 Budget Constraints</h3>
            <p>Traditional solutions cost $10,000+ annually, making them inaccessible to smaller municipalities</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Solution Overview
    st.markdown("""
    ## 🌟 Introducing Village: The Modern Solution
    
    Village is the first AI-powered traffic planning platform designed specifically for municipal planners:
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h3 style="color: #2d5016;">🆓 Start Free</h3>
            <p>Get started with 1,000 incidents/month at no cost. No credit card required.</p>
            <ul>
                <li>Real-time traffic monitoring</li>
                <li>Basic incident reporting</li>
                <li>Standard analytics dashboard</li>
                <li>Email notifications</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h3 style="color: #2d5016;">🤖 AI-Powered Intelligence</h3>
            <p>Advanced AI analysis with municipal context starting at just $79/month.</p>
            <ul>
                <li>Predictive incident forecasting</li>
                <li>Municipal planning insights</li>
                <li>Historical pattern analysis</li>
                <li>Custom reporting tools</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Stats Section
    st.markdown("""
    <div class="stats-container">
        <div style="display: flex; justify-content: space-around; flex-wrap: wrap;">
            <div>
                <p class="stat-number">50x</p>
                <p class="stat-label">More Affordable</p>
            </div>
            <div>
                <p class="stat-number">40%</p>
                <p class="stat-label">Faster Response</p>
            </div>
            <div>
                <p class="stat-number">30</p>
                <p class="stat-label">Day Setup</p>
            </div>
            <div>
                <p class="stat-number">24/7</p>
                <p class="stat-label">AI Monitoring</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Feature Showcase
    st.markdown("## 🎯 Key Features")
    
    # Feature tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🚦 Live Monitoring", "🔮 Predictive Analytics", "🤖 AI Analysis", "📊 Reporting"])
    
    with tab1:
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown("""
            ### Real-Time Traffic Monitoring
            
            Monitor traffic incidents as they happen with our intelligent dashboard:
            
            - **Live incident tracking** with automatic detection
            - **Interactive maps** with real-time updates
            - **Severity assessment** with AI-powered analysis
            - **Multi-source data** integration (cameras, sensors, reports)
            - **Instant notifications** via email, SMS, or app
            """)
        
        with col2:
            # Placeholder for demo/screenshot
            st.image("https://via.placeholder.com/400x300/2d5016/ffffff?text=Live+Traffic+Dashboard", 
                    caption="Real-time traffic monitoring dashboard")
    
    with tab2:
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown("""
            ### Predictive Analytics
            
            Anticipate problems before they occur:
            
            - **2-24 hour incident forecasting** with 85% accuracy
            - **Traffic pattern analysis** to identify high-risk areas
            - **Seasonal trend identification** for better planning
            - **Resource allocation optimization** based on predictions
            - **Prevention strategy recommendations**
            """)
        
        with col2:
            st.image("https://via.placeholder.com/400x300/5a7c47/ffffff?text=Predictive+Analytics", 
                    caption="Predictive analytics dashboard")
    
    with tab3:
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown("""
            ### AI-Powered Analysis
            
            Get intelligent insights with municipal context:
            
            - **Incident impact assessment** with stakeholder analysis
            - **Policy recommendations** based on local regulations
            - **Resource planning** with budget considerations
            - **Historical comparison** with similar municipalities
            - **Automated reporting** with actionable insights
            """)
        
        with col2:
            st.image("https://via.placeholder.com/400x300/8b4513/ffffff?text=AI+Analysis", 
                    caption="AI-powered incident analysis")
    
    with tab4:
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown("""
            ### Professional Reporting
            
            Create compelling reports for stakeholders:
            
            - **Custom report builder** with drag-and-drop interface
            - **Automated scheduling** for regular updates
            - **Professional templates** for different audiences
            - **Data visualization** with interactive charts
            - **Export options** (PDF, Excel, PowerPoint)
            """)
        
        with col2:
            st.image("https://via.placeholder.com/400x300/d4a574/ffffff?text=Professional+Reports", 
                    caption="Professional reporting tools")
    
    # Comparison Table
    st.markdown("""
    <div class="comparison-table">
        <h2 style="text-align: center; color: #2d5016; margin-bottom: 2rem;">📊 How Village Compares</h2>
    </div>
    """, unsafe_allow_html=True)
    
    comparison_data = {
        "Feature": [
            "Starting Price",
            "Setup Time",
            "AI Analysis",
            "Predictive Analytics",
            "Free Tier",
            "Municipal Context",
            "Training Required",
            "Support Level"
        ],
        "Village": [
            "Free ($0/month)",
            "30 minutes",
            "✅ Built-in",
            "✅ Advanced",
            "✅ 1,000 incidents",
            "✅ Rhode Island specific",
            "❌ None required",
            "✅ Community to dedicated"
        ],
        "Traditional GIS": [
            "$10,000+/year",
            "6+ months",
            "❌ Add-on only",
            "❌ Limited",
            "❌ None",
            "❌ Generic",
            "✅ Extensive",
            "✅ Variable"
        ],
        "Build Your Own": [
            "$100,000+",
            "12+ months",
            "❌ Must develop",
            "❌ Must develop",
            "❌ N/A",
            "❌ Must customize",
            "✅ Extensive",
            "❌ Internal only"
        ]
    }
    
    comparison_df = pd.DataFrame(comparison_data)
    st.dataframe(comparison_df, use_container_width=True, hide_index=True)
    
    # Testimonials Section
    st.markdown("## 💬 What Beta Users Are Saying")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="testimonial">
            <p>"Village transformed our traffic management approach. We went from reactive to proactive, reducing incident response time by 40%."</p>
            <p><strong>- Sarah Johnson, Traffic Engineer, City of Warwick</strong></p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="testimonial">
            <p>"The AI analysis provides insights we never had before. It's like having a traffic planning consultant available 24/7."</p>
            <p><strong>- Michael Chen, Transportation Director, Providence</strong></p>
        </div>
        """, unsafe_allow_html=True)
    
    # Early Access Form
    st.markdown("""
    <div class="early-access-form" id="early-access">
        <h2 style="margin-bottom: 1rem;">🚀 Join the Beta Program</h2>
        <p style="font-size: 1.2rem; margin-bottom: 2rem;">
            Be among the first to experience Village's revolutionary traffic management platform
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Beta signup form
    with st.form("beta_signup", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Full Name*", placeholder="John Smith")
            email = st.text_input("Email Address*", placeholder="john@city.gov")
            organization = st.text_input("Organization*", placeholder="City of Springfield")
        
        with col2:
            title = st.text_input("Job Title", placeholder="Traffic Engineer")
            phone = st.text_input("Phone Number", placeholder="(555) 123-4567")
            population = st.number_input("Municipality Population", min_value=1000, value=50000)
        
        # Interest areas
        st.markdown("**Areas of Interest** (select all that apply):")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            interest_monitoring = st.checkbox("Real-time Monitoring")
            interest_analytics = st.checkbox("Predictive Analytics")
        
        with col2:
            interest_ai = st.checkbox("AI Analysis")
            interest_reporting = st.checkbox("Custom Reporting")
        
        with col3:
            interest_integration = st.checkbox("System Integration")
            interest_training = st.checkbox("Training & Support")
        
        # Current challenges
        challenges = st.text_area(
            "Current Traffic Management Challenges",
            placeholder="Describe your biggest challenges with current traffic management tools or processes..."
        )
        
        # Beta program benefits
        st.markdown("""
        **🎁 Beta Program Benefits:**
        - Free access to all Pro features for 90 days
        - Priority support from our development team
        - Influence on product roadmap and features
        - Early access to new releases
        - Case study opportunity for marketing
        """)
        
        # Submit button
        submitted = st.form_submit_button("🚀 Join Beta Program", use_container_width=True)
        
        if submitted:
            if name and email and organization:
                # Save beta signup
                beta_data = {
                    'name': name,
                    'email': email,
                    'organization': organization,
                    'title': title,
                    'phone': phone,
                    'population': population,
                    'interests': {
                        'monitoring': interest_monitoring,
                        'analytics': interest_analytics,
                        'ai': interest_ai,
                        'reporting': interest_reporting,
                        'integration': interest_integration,
                        'training': interest_training
                    },
                    'challenges': challenges,
                    'signup_date': datetime.now().isoformat()
                }
                
                # Save to database (implement this)
                save_beta_signup(beta_data)
                
                st.success("🎉 Welcome to the Village Beta Program!")
                st.balloons()
                
                st.markdown("""
                **Next Steps:**
                1. Check your email for beta access credentials
                2. Schedule your onboarding call with our team
                3. Start exploring Village with your traffic data
                4. Join our private beta community Slack channel
                """)
                
                # Show beta access instructions
                st.info("""
                **Beta Access Instructions:**
                - Your beta account will be activated within 24 hours
                - You'll receive login credentials via email
                - Our team will reach out to schedule your onboarding call
                - Beta program runs for 90 days with full Pro features
                """)
                
            else:
                st.error("Please fill in all required fields (marked with *)")
    
    # Demo Section
    st.markdown("""
    <div id="demo" style="margin-top: 3rem;">
        <h2 style="text-align: center; color: #2d5016;">📺 See Village in Action</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Demo video placeholder
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.image("https://via.placeholder.com/600x400/2d5016/ffffff?text=Village+Demo+Video", 
                caption="Village Platform Demo (5 minutes)")
        
        if st.button("▶️ Watch Demo Video", use_container_width=True):
            st.success("Demo video would play here (YouTube embed or video file)")
    
    # FAQ Section
    st.markdown("## ❓ Frequently Asked Questions")
    
    faqs = [
        {
            "question": "How is Village different from traditional GIS software?",
            "answer": "Village is purpose-built for municipal traffic management with built-in AI analysis, predictive capabilities, and municipal context. Traditional GIS software is generic and requires extensive customization."
        },
        {
            "question": "What's included in the free tier?",
            "answer": "The free tier includes 1,000 incidents/month, basic monitoring, standard analytics, email notifications, and community support. Perfect for small municipalities getting started."
        },
        {
            "question": "How quickly can we get started?",
            "answer": "Most municipalities are up and running in under 30 minutes. Our guided onboarding process helps you import data and configure your dashboard quickly."
        },
        {
            "question": "Do you integrate with existing systems?",
            "answer": "Yes! Village integrates with major GIS platforms, traffic management systems, and municipal databases through our API. We also support CSV imports for legacy systems."
        },
        {
            "question": "Is Village secure for government use?",
            "answer": "Absolutely. Village is SOC 2 Type II compliant, supports SSO integration, and follows government security standards. We're also pursuing FedRAMP authorization."
        },
        {
            "question": "What kind of support do you provide?",
            "answer": "Support ranges from community forums (free tier) to dedicated phone support (enterprise). All paid tiers include priority email support and comprehensive documentation."
        }
    ]
    
    for i, faq in enumerate(faqs):
        with st.expander(f"**{faq['question']}**"):
            st.write(faq['answer'])
    
    # Footer
    st.markdown("""
    ---
    <div style="text-align: center; padding: 2rem; color: #5a7c47;">
        <p><strong>Village</strong> - Transforming Municipal Traffic Management</p>
        <p>Built for transportation professionals | Powered by AI | Trusted by municipalities</p>
        <p>
            <a href="mailto:hello@village.com" style="color: #2d5016;">Contact Us</a> | 
            <a href="/privacy" style="color: #2d5016;">Privacy Policy</a> | 
            <a href="/terms" style="color: #2d5016;">Terms of Service</a>
        </p>
    </div>
    """, unsafe_allow_html=True)

def save_beta_signup(data: Dict[str, Any]):
    """Save beta signup data to database"""
    try:
        # Initialize database if it doesn't exist
        conn = sqlite3.connect('data/beta_signups.db')
        cursor = conn.cursor()
        
        # Create table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS beta_signups (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                organization TEXT NOT NULL,
                title TEXT,
                phone TEXT,
                population INTEGER,
                interests TEXT,
                challenges TEXT,
                signup_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending'
            )
        ''')
        
        # Insert signup data
        signup_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO beta_signups 
            (id, name, email, organization, title, phone, population, interests, challenges, signup_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            signup_id,
            data['name'],
            data['email'],
            data['organization'],
            data['title'],
            data['phone'],
            data['population'],
            json.dumps(data['interests']),
            data['challenges'],
            data['signup_date']
        ))
        
        conn.commit()
        conn.close()
        
        return signup_id
        
    except sqlite3.IntegrityError:
        # Email already exists
        st.error("This email is already registered for the beta program.")
        return None
    except Exception as e:
        st.error(f"Error saving signup: {e}")
        return None

def get_beta_signups() -> List[Dict[str, Any]]:
    """Get all beta signups for admin review"""
    try:
        conn = sqlite3.connect('data/beta_signups.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, email, organization, title, phone, population, 
                   interests, challenges, signup_date, status
            FROM beta_signups
            ORDER BY signup_date DESC
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        signups = []
        for row in results:
            signups.append({
                'id': row[0],
                'name': row[1],
                'email': row[2],
                'organization': row[3],
                'title': row[4],
                'phone': row[5],
                'population': row[6],
                'interests': json.loads(row[7]) if row[7] else {},
                'challenges': row[8],
                'signup_date': row[9],
                'status': row[10]
            })
        
        return signups
        
    except Exception as e:
        st.error(f"Error retrieving signups: {e}")
        return []

def show():
    """Main function for Village pages"""
    show_marketing_landing()

if __name__ == "__main__":
    show_marketing_landing()