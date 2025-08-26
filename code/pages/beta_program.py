# pages/beta_program.py - Beta Program Interface for Participants

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json

# Import theme manager
try:
    from utils.theme_manager import apply_village_theme, create_village_header, get_village_colors
except ImportError:
    st.error("Theme manager not available")

def show_beta_program_page():
    """Show beta program interface for participants"""
    
    # Custom CSS for beta program page
    st.markdown("""
    <style>
    .beta-header {
        background: linear-gradient(135deg, #2d5016 0%, #5a7c47 50%, #8b4513 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 6px 20px rgba(0,0,0,0.15);
    }
    
    .beta-badge {
        background: linear-gradient(45deg, #ff6b6b 0%, #ee5a24 100%);
        color: white;
        padding: 0.5rem 1.5rem;
        border-radius: 25px;
        font-size: 0.9rem;
        font-weight: 600;
        display: inline-block;
        margin-bottom: 1rem;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
    }
    
    .progress-card {
        background: linear-gradient(135deg, #faf8f3 0%, #f5f1e8 100%);
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        border-left: 4px solid #5a7c47;
        box-shadow: 0 3px 10px rgba(0,0,0,0.1);
    }
    
    .milestone {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 3px solid #8b4513;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    
    .milestone.completed {
        border-left-color: #5a7c47;
        background: #f8f9fa;
    }
    
    .feedback-form {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border: 1px solid #e9ecef;
    }
    
    .beta-benefits {
        background: linear-gradient(135deg, #f5f1e8 0%, #faf8f3 100%);
        padding: 2rem;
        border-radius: 15px;
        margin: 2rem 0;
        border: 1px solid #d4a574;
    }
    
    .community-section {
        background: linear-gradient(135deg, #2d5016 0%, #5a7c47 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin: 2rem 0;
        text-align: center;
    }
    
    .beta-timeline {
        position: relative;
        padding: 1rem 0;
    }
    
    .timeline-item {
        position: relative;
        padding: 1rem;
        margin: 1rem 0;
        background: white;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .timeline-item::before {
        content: '';
        position: absolute;
        left: -20px;
        top: 50%;
        transform: translateY(-50%);
        width: 12px;
        height: 12px;
        background: #5a7c47;
        border-radius: 50%;
    }
    
    .timeline-item.completed::before {
        background: #2d5016;
    }
    
    .success-metric {
        background: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border: 1px solid #c3e6cb;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Display header
    create_village_header(
        "🧪 Welcome to Village Beta!",
        "Help us build the future of municipal traffic management"
    )
    
    # Beta badge
    st.markdown("""
    <div class="beta-badge">🧪 BETA PROGRAM</div>
    """, unsafe_allow_html=True)
    
    # Beta program navigation
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🎯 Dashboard", 
        "📋 Milestones", 
        "💬 Feedback", 
        "🏆 Rewards", 
        "👥 Community"
    ])
    
    with tab1:
        show_beta_dashboard()
    
    with tab2:
        show_beta_milestones()
    
    with tab3:
        show_beta_feedback()
    
    with tab4:
        show_beta_rewards()
    
    with tab5:
        show_beta_community()

def show_beta_dashboard():
    """Show beta participant dashboard"""
    st.markdown("## 📊 Your Beta Progress")
    
    # Mock beta participant data
    beta_start_date = datetime.now() - timedelta(days=15)
    beta_end_date = beta_start_date + timedelta(days=90)
    days_remaining = (beta_end_date - datetime.now()).days
    
    # Progress metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Days Active", "15", "+1")
    with col2:
        st.metric("Days Remaining", str(days_remaining), f"-{90-days_remaining}")
    with col3:
        st.metric("Features Tested", "8", "+2")
    with col4:
        st.metric("Feedback Submitted", "12", "+3")
    
    # Beta progress bar
    progress_percentage = (15 / 90) * 100
    st.markdown(f"""
    <div class="progress-card">
        <h3 style="color: #2d5016; margin-bottom: 1rem;">Beta Program Progress</h3>
        <div style="background: #e9ecef; border-radius: 10px; padding: 4px;">
            <div style="
                background: linear-gradient(90deg, #2d5016 0%, #5a7c47 100%);
                width: {progress_percentage}%;
                height: 20px;
                border-radius: 6px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-weight: 600;
                font-size: 0.9rem;
            ">
                {progress_percentage:.1f}%
            </div>
        </div>
        <p style="margin: 0.5rem 0; color: #5a7c47;">
            Great progress! You're ahead of schedule and providing valuable feedback.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Recent activity
    st.markdown("### 📈 Recent Activity")
    
    activity_data = [
        {"Date": "2024-01-15", "Activity": "Tested 3D Visualization", "Feedback": "Submitted 2 suggestions"},
        {"Date": "2024-01-14", "Activity": "Used Predictive Analytics", "Feedback": "Reported 1 bug"},
        {"Date": "2024-01-13", "Activity": "Created Custom Report", "Feedback": "5-star rating"},
        {"Date": "2024-01-12", "Activity": "Imported Traffic Data", "Feedback": "Feature request"},
        {"Date": "2024-01-11", "Activity": "Explored AI Analysis", "Feedback": "Positive feedback"}
    ]
    
    activity_df = pd.DataFrame(activity_data)
    st.dataframe(activity_df, use_container_width=True, hide_index=True)
    
    # Next steps
    st.markdown("### 🎯 Recommended Next Steps")
    
    next_steps = [
        "Test the API integration feature",
        "Try the mobile field app",
        "Explore multi-department access",
        "Submit feedback on reporting tools",
        "Invite a colleague to join your beta workspace"
    ]
    
    for i, step in enumerate(next_steps, 1):
        st.markdown(f"**{i}.** {step}")

def show_beta_milestones():
    """Show beta program milestones"""
    st.markdown("## 🏆 Beta Program Milestones")
    
    milestones = [
        {
            "title": "Welcome & Setup",
            "description": "Complete profile setup and import first dataset",
            "completed": True,
            "date": "2024-01-01",
            "reward": "Village beta t-shirt"
        },
        {
            "title": "Feature Explorer",
            "description": "Test 5 different features",
            "completed": True,
            "date": "2024-01-05",
            "reward": "Early access to new features"
        },
        {
            "title": "Feedback Champion",
            "description": "Submit 10 pieces of feedback",
            "completed": True,
            "date": "2024-01-10",
            "reward": "1-month free Pro subscription"
        },
        {
            "title": "Community Contributor",
            "description": "Help 3 other beta participants",
            "completed": False,
            "date": None,
            "reward": "Village branded mug"
        },
        {
            "title": "Power User",
            "description": "Use Village for 30 consecutive days",
            "completed": False,
            "date": None,
            "reward": "3-month free Pro subscription"
        },
        {
            "title": "Beta Graduate",
            "description": "Complete the full 90-day program",
            "completed": False,
            "date": None,
            "reward": "6-month free Pro subscription + case study feature"
        }
    ]
    
    st.markdown('<div class="beta-timeline">', unsafe_allow_html=True)
    
    for milestone in milestones:
        status_class = "completed" if milestone["completed"] else ""
        status_icon = "✅" if milestone["completed"] else "⏳"
        
        st.markdown(f"""
        <div class="timeline-item {status_class}">
            <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                <span style="font-size: 1.2rem; margin-right: 0.5rem;">{status_icon}</span>
                <h4 style="margin: 0; color: #2d5016;">{milestone['title']}</h4>
            </div>
            <p style="margin: 0.5rem 0; color: #5a7c47;">{milestone['description']}</p>
            <div style="display: flex; justify-content: between; align-items: center;">
                <small style="color: #8b4513;">🎁 Reward: {milestone['reward']}</small>
                {f'<small style="color: #2d5016; margin-left: auto;">Completed: {milestone["date"]}</small>' if milestone["completed"] else ''}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Progress summary
    completed_count = sum(1 for m in milestones if m["completed"])
    total_count = len(milestones)
    
    st.markdown(f"""
    <div class="success-metric">
        <h3 style="margin: 0; color: #155724;">Milestone Progress: {completed_count}/{total_count}</h3>
        <p style="margin: 0.5rem 0 0 0;">You're doing great! Keep testing and providing feedback to unlock more rewards.</p>
    </div>
    """, unsafe_allow_html=True)

def show_beta_feedback():
    """Show beta feedback interface"""
    st.markdown("## 💬 Share Your Feedback")
    
    # Feedback form
    st.markdown('<div class="feedback-form">', unsafe_allow_html=True)
    
    with st.form("beta_feedback_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            feedback_type = st.selectbox(
                "Feedback Type",
                ["🐛 Bug Report", "💡 Feature Request", "👍 General Feedback", "🔧 Usability Issue", "⚡ Performance Issue"]
            )
            
            priority = st.selectbox(
                "Priority Level",
                ["🔴 High", "🟡 Medium", "🟢 Low"]
            )
        
        with col2:
            feature_area = st.selectbox(
                "Feature Area",
                ["📊 Dashboard", "📈 Analytics", "📋 Reporting", "📥 Data Import", "🤖 AI Analysis", "🗺️ Maps", "⚙️ Settings", "🔗 Integrations"]
            )
            
            rating = st.slider("Overall Rating", 1, 5, 4)
        
        # Main feedback
        feedback_title = st.text_input(
            "Feedback Title",
            placeholder="Brief description of your feedback..."
        )
        
        feedback_details = st.text_area(
            "Detailed Feedback",
            placeholder="Please provide detailed feedback, steps to reproduce (for bugs), or suggestions for improvement...",
            height=100
        )
        
        # Additional context
        st.markdown("**Additional Context:**")
        col1, col2 = st.columns(2)
        
        with col1:
            browser = st.selectbox(
                "Browser",
                ["Chrome", "Firefox", "Safari", "Edge", "Other"]
            )
        
        with col2:
            device = st.selectbox(
                "Device",
                ["Desktop", "Tablet", "Mobile"]
            )
        
        # Screenshots or attachments
        st.markdown("**Attachments (Optional):**")
        uploaded_files = st.file_uploader(
            "Upload screenshots or documents",
            accept_multiple_files=True,
            type=['png', 'jpg', 'jpeg', 'pdf', 'doc', 'docx']
        )
        
        # Submit button
        submitted = st.form_submit_button("🚀 Submit Feedback", use_container_width=True)
        
        if submitted:
            if feedback_title and feedback_details:
                # Store feedback (in production, this would go to database)
                st.success("🎉 Thank you for your feedback!")
                st.balloons()
                
                # Show confirmation
                st.markdown(f"""
                **Feedback Submitted Successfully!**
                
                - **Type:** {feedback_type}
                - **Priority:** {priority}
                - **Feature Area:** {feature_area}
                - **Rating:** {"⭐" * rating}
                
                Our team will review your feedback and get back to you within 24 hours.
                """)
                
                # Show feedback tracking ID
                import uuid
                feedback_id = str(uuid.uuid4())[:8]
                st.info(f"📋 Feedback ID: **{feedback_id}** (save this for tracking)")
                
            else:
                st.error("Please fill in the title and detailed feedback fields.")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Previous feedback
    st.markdown("---")
    st.markdown("### 📋 Your Previous Feedback")
    
    # Mock feedback history
    feedback_history = [
        {
            "ID": "fb-001",
            "Date": "2024-01-15",
            "Type": "Feature Request",
            "Title": "Add export to Excel",
            "Status": "✅ Implemented",
            "Response": "Feature added in v1.2"
        },
        {
            "ID": "fb-002",
            "Date": "2024-01-14",
            "Type": "Bug Report",
            "Title": "Map loading issue",
            "Status": "🔧 In Progress",
            "Response": "Fix scheduled for next release"
        },
        {
            "ID": "fb-003",
            "Date": "2024-01-13",
            "Type": "General Feedback",
            "Title": "Love the AI insights!",
            "Status": "👍 Acknowledged",
            "Response": "Thank you for the positive feedback!"
        }
    ]
    
    feedback_df = pd.DataFrame(feedback_history)
    st.dataframe(feedback_df, use_container_width=True, hide_index=True)

def show_beta_rewards():
    """Show beta rewards and benefits"""
    st.markdown("## 🎁 Beta Program Rewards")
    
    # Current rewards earned
    st.markdown("### 🏆 Rewards Earned")
    
    earned_rewards = [
        {"reward": "Village Beta T-Shirt", "earned": "2024-01-01", "status": "Shipped"},
        {"reward": "Early Access to New Features", "earned": "2024-01-05", "status": "Active"},
        {"reward": "1-Month Free Pro Subscription", "earned": "2024-01-10", "status": "Applied"}
    ]
    
    for reward in earned_rewards:
        st.markdown(f"""
        <div class="success-metric">
            <h4 style="margin: 0; color: #155724;">🎁 {reward['reward']}</h4>
            <p style="margin: 0.5rem 0 0 0;">
                Earned: {reward['earned']} | Status: {reward['status']}
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Available rewards
    st.markdown("### 🎯 Available Rewards")
    
    available_rewards = [
        {"reward": "Village Branded Mug", "requirement": "Help 3 other beta participants", "progress": "1/3"},
        {"reward": "3-Month Free Pro Subscription", "requirement": "Use Village for 30 consecutive days", "progress": "15/30"},
        {"reward": "6-Month Free Pro + Case Study", "requirement": "Complete 90-day beta program", "progress": "15/90"}
    ]
    
    for reward in available_rewards:
        st.markdown(f"""
        <div class="milestone">
            <h4 style="margin: 0; color: #2d5016;">🎁 {reward['reward']}</h4>
            <p style="margin: 0.5rem 0; color: #5a7c47;">{reward['requirement']}</p>
            <div style="background: #e9ecef; border-radius: 10px; padding: 2px; margin-top: 0.5rem;">
                <div style="
                    background: linear-gradient(90deg, #2d5016 0%, #5a7c47 100%);
                    width: {min(100, int(reward['progress'].split('/')[0]) / int(reward['progress'].split('/')[1]) * 100)}%;
                    height: 6px;
                    border-radius: 4px;
                "></div>
            </div>
            <small style="color: #8b4513;">Progress: {reward['progress']}</small>
        </div>
        """, unsafe_allow_html=True)
    
    # Beta benefits
    st.markdown("---")
    st.markdown("""
    <div class="beta-benefits">
        <h3 style="color: #2d5016; margin-bottom: 1rem;">🌟 Beta Program Benefits</h3>
        
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1rem;">
            <div>
                <h4 style="color: #5a7c47;">🚀 Early Access</h4>
                <ul style="color: #8b4513;">
                    <li>New features before public release</li>
                    <li>Beta-only advanced tools</li>
                    <li>Priority feature requests</li>
                </ul>
            </div>
            
            <div>
                <h4 style="color: #5a7c47;">🎯 Direct Impact</h4>
                <ul style="color: #8b4513;">
                    <li>Influence product roadmap</li>
                    <li>Shape user experience</li>
                    <li>Co-create solutions</li>
                </ul>
            </div>
            
            <div>
                <h4 style="color: #5a7c47;">💎 Exclusive Perks</h4>
                <ul style="color: #8b4513;">
                    <li>Beta community access</li>
                    <li>Direct developer contact</li>
                    <li>Special pricing on launch</li>
                </ul>
            </div>
            
            <div>
                <h4 style="color: #5a7c47;">🏆 Recognition</h4>
                <ul style="color: #8b4513;">
                    <li>Beta contributor badge</li>
                    <li>Case study opportunities</li>
                    <li>Conference speaking invites</li>
                </ul>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def show_beta_community():
    """Show beta community features"""
    st.markdown("## 👥 Beta Community")
    
    # Community stats
    st.markdown("""
    <div class="community-section">
        <h3 style="margin: 0 0 1rem 0;">🌟 Join Our Beta Community</h3>
        <p style="margin: 0; font-size: 1.1rem; opacity: 0.9;">
            Connect with other municipal planners testing Village
        </p>
        
        <div style="display: flex; justify-content: space-around; margin-top: 2rem;">
            <div>
                <h2 style="margin: 0; color: #faf8f3;">87</h2>
                <p style="margin: 0; opacity: 0.8;">Active Beta Users</p>
            </div>
            <div>
                <h2 style="margin: 0; color: #faf8f3;">342</h2>
                <p style="margin: 0; opacity: 0.8;">Feedback Items</p>
            </div>
            <div>
                <h2 style="margin: 0; color: #faf8f3;">156</h2>
                <p style="margin: 0; opacity: 0.8;">Feature Requests</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Community features
    tab1, tab2, tab3 = st.tabs(["💬 Discussions", "🤝 Help Others", "📊 Leaderboard"])
    
    with tab1:
        st.markdown("### 💬 Recent Discussions")
        
        discussions = [
            {
                "title": "Best practices for importing historical data",
                "author": "Sarah Johnson (City of Warwick)",
                "replies": 12,
                "last_activity": "2 hours ago"
            },
            {
                "title": "AI insights accuracy - your experiences?",
                "author": "Mike Chen (Providence DOT)",
                "replies": 8,
                "last_activity": "4 hours ago"
            },
            {
                "title": "Integration with existing GIS systems",
                "author": "Alex Rodriguez (City of Cranston)",
                "replies": 15,
                "last_activity": "6 hours ago"
            }
        ]
        
        for discussion in discussions:
            st.markdown(f"""
            <div class="milestone">
                <h4 style="margin: 0; color: #2d5016;">{discussion['title']}</h4>
                <p style="margin: 0.5rem 0; color: #5a7c47;">By {discussion['author']}</p>
                <div style="display: flex; justify-content: between; align-items: center;">
                    <small style="color: #8b4513;">💬 {discussion['replies']} replies</small>
                    <small style="color: #8b4513; margin-left: auto;">🕒 {discussion['last_activity']}</small>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # New discussion
        st.markdown("---")
        st.markdown("### 🆕 Start a New Discussion")
        
        with st.form("new_discussion"):
            discussion_title = st.text_input("Discussion Title")
            discussion_content = st.text_area("Your question or topic", height=100)
            
            if st.form_submit_button("Start Discussion"):
                if discussion_title and discussion_content:
                    st.success("Discussion started! Other beta users will be notified.")
                else:
                    st.error("Please fill in both title and content.")
    
    with tab2:
        st.markdown("### 🤝 Help Other Beta Users")
        
        help_requests = [
            {
                "title": "Need help with CSV import format",
                "author": "Jane Smith (City of Newport)",
                "category": "Data Import",
                "urgency": "Medium",
                "time": "30 min ago"
            },
            {
                "title": "Dashboard customization tips?",
                "author": "Tom Wilson (Pawtucket Traffic)",
                "category": "Dashboard",
                "urgency": "Low",
                "time": "1 hour ago"
            }
        ]
        
        for request in help_requests:
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"""
                <div class="milestone">
                    <h4 style="margin: 0; color: #2d5016;">{request['title']}</h4>
                    <p style="margin: 0.5rem 0; color: #5a7c47;">By {request['author']}</p>
                    <small style="color: #8b4513;">📂 {request['category']} | 🕒 {request['time']}</small>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                if st.button("Help", key=f"help_{request['title'][:10]}"):
                    st.success("Thank you for helping! This counts toward your community milestone.")
        
        # Your help stats
        st.markdown("---")
        st.markdown("### 📊 Your Community Impact")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("People Helped", "7")
        with col2:
            st.metric("Best Answers", "3")
        with col3:
            st.metric("Community Rank", "#12")
    
    with tab3:
        st.markdown("### 🏆 Beta Program Leaderboard")
        
        leaderboard_data = [
            {"Rank": 1, "Name": "Sarah Johnson", "Organization": "City of Warwick", "Points": 2450, "Badge": "🥇"},
            {"Rank": 2, "Name": "Mike Chen", "Organization": "Providence DOT", "Points": 2180, "Badge": "🥈"},
            {"Rank": 3, "Name": "Alex Rodriguez", "Organization": "City of Cranston", "Points": 1890, "Badge": "🥉"},
            {"Rank": 4, "Name": "Jennifer Davis", "Organization": "Woonsocket Planning", "Points": 1650, "Badge": "⭐"},
            {"Rank": 5, "Name": "You", "Organization": "Your Organization", "Points": 1420, "Badge": "🎯"}
        ]
        
        leaderboard_df = pd.DataFrame(leaderboard_data)
        
        # Highlight user's row
        def highlight_user(row):
            if row['Name'] == 'You':
                return ['background-color: #f5f1e8'] * len(row)
            return [''] * len(row)
        
        styled_df = leaderboard_df.style.apply(highlight_user, axis=1)
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
        
        # Points explanation
        st.markdown("---")
        st.markdown("### 📈 How Points Are Earned")
        
        points_info = [
            {"Activity": "Daily login", "Points": "10"},
            {"Activity": "Feature testing", "Points": "25"},
            {"Activity": "Feedback submission", "Points": "50"},
            {"Activity": "Bug report", "Points": "100"},
            {"Activity": "Helping others", "Points": "75"},
            {"Activity": "Feature request", "Points": "40"}
        ]
        
        points_df = pd.DataFrame(points_info)
        st.dataframe(points_df, use_container_width=True, hide_index=True)

def show():
    """Main function to display beta program page"""
    # Apply Village theme
    apply_village_theme()
    
    show_beta_program_page()

if __name__ == "__main__":
    show()