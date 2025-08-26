# main.py - Village Municipal Traffic Planning Platform
# Main entry point for the Streamlit application


import streamlit as st
import os
import sys
from pathlib import Path

# Add the current directory to Path for imports
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

# Streamlit page config
st.set_page_config(
    page_title="Village - A Municipal Traffic Planning Platform",
    page_icon="🏘️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': '''
        # Village - A Municipal Traffic Planning Platform
        
        Village is a comprehensive analysis and planning tool designed for municipal planners 
        and transportation professionals. 
        
        Features traffic monitoring in real time, AI-driven context and 
        insights, statistical analysis tools, and professional reporting tools.
        
        Built with Streamlit, TomTom APIs, Perplexity AI, and other data science libraries.
        '''
    }
)

# Apply theme immediately after page config
try:
    from utils.theme_manager import apply_village_theme
    apply_village_theme()
except ImportError:
    pass

# Import page modules
try:
    from pages import live_traffic, analytics, planning, reports, monitoring
    from utils.data_sync import initialize_data_system, display_data_status
    from utils.enterprise_auth import (
        is_authenticated, get_current_user, show_login_page, 
        show_logout_button, show_usage_stats, require_auth
    )
    from utils.pricing_tiers import show_pricing_page, show_current_subscription
    from utils.api_management import show_api_management_page
    from utils.remote_database import configure_remote_data_source
except ImportError as e:
    st.error("🚫 System initialization error. Please contact support.")
    st.info("The Village Platform is temporarily unavailable. Please try again in a few minutes.")
    st.stop()

def main():
    """Main application w page nav"""
    
    # Check authentication first
    if not is_authenticated():
        show_login_page()
        return
    
    # Get current user and organization
    user_org = get_current_user()
    if not user_org:
        st.error("Session expired. Please login again.")
        if 'auth_token' in st.session_state:
            del st.session_state['auth_token']
        st.rerun()
        return
    
    user, organization = user_org
    
    # Initialize data system
    try:
        data_status = initialize_data_system()
        display_data_status(data_status)
    except Exception as e:
        st.error(f"Error initializing data system: {e}")
    
    # Village-themed styling with dark mode support
    st.markdown("""
    <style>
    :root {
        --village-pine: #2d5016;
        --village-sage: #5a7c47;
        --village-beige: #f5f1e8;
        --village-brown: #8b4513;
        --village-cream: #faf8f3;
        --village-dark-brown: #5d2e07;
    }
    
    /* Dark mode variables */
    [data-theme="dark"] {
        --village-pine: #4a7c2a;
        --village-sage: #6b9c57;
        --village-beige: #2d2d2d;
        --village-brown: #b5651d;
        --village-cream: #1e1e1e;
        --village-dark-brown: #8b5a0d;
    }
    
    /* Auto-detect dark mode */
    @media (prefers-color-scheme: dark) {
        :root {
            --village-pine: #4a7c2a;
            --village-sage: #6b9c57;
            --village-beige: #2d2d2d;
            --village-brown: #b5651d;
            --village-cream: #1e1e1e;
            --village-dark-brown: #8b5a0d;
        }
    }
    
    /* Sidebar styling - is also responsive to theme */
    .stSidebar > div {
        background: linear-gradient(180deg, var(--village-cream) 0%, var(--village-beige) 100%);
        border-right: 3px solid var(--village-sage);
    }
    
    /* Sidebar headers */
    .stSidebar h3 {
        color: var(--village-pine) !important;
        border-bottom: 2px solid var(--village-sage);
        padding-bottom: 0.5rem;
    }
    
    /* Selectbox styling */
    .stSelectbox > div > div {
        background-color: var(--village-beige);
        border: 1px solid var(--village-sage);
        border-radius: 8px;
    }
    
    /* Metric styling */
    .stMetric {
        background: linear-gradient(135deg, var(--village-cream) 0%, var(--village-beige) 100%);
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid var(--village-sage);
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, var(--village-pine) 0%, var(--village-sage) 100%);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 500;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, var(--village-sage) 0%, var(--village-brown) 100%);
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* Success/info/warning styling */
    .stSuccess {
        background: linear-gradient(135deg, var(--village-beige) 0%, var(--village-cream) 100%);
        border-left: 4px solid var(--village-sage);
    }
    
    .stInfo {
        background: linear-gradient(135deg, var(--village-beige) 0%, var(--village-cream) 100%);
        border-left: 4px solid var(--village-brown);
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        background-color: var(--village-beige);
        border-radius: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        color: var(--village-pine);
        background-color: transparent;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: var(--village-sage) !important;
        color: white !important;
    }
    
    /* Card styling for dark mode */
    .stContainer > div {
        background-color: var(--village-cream);
        border-radius: 8px;
    }
    
    /* Text color adjustments for dark mode */
    @media (prefers-color-scheme: dark) {
        .stMarkdown {
            color: #ffffff;
        }
        
        .stText {
            color: #ffffff;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # App header with village theme
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #2d5016 0%, #5a7c47 50%, #8b4513 100%);
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    ">
        <h1 style="color: #faf8f3; margin: 0; font-size: 2.8rem; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">
            Village
        </h1>
        <p style="color: #f5f1e8; margin: 0.5rem 0 0 0; font-size: 1.2rem; font-weight: 300;">
            Municipal Traffic Planning Platform
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown("### Navigation")
        
        # Show user info and logout
        show_logout_button()
        
        st.markdown("---")
        
        # Consolidated page selection with role-based access
        from utils.enterprise_auth import UserRole
        
        # Base pages available to all users
        base_pages = ["Live Traffic", "Analytics"]
        
        # Tier-based feature pages
        if organization.tier.value in ["pro", "enterprise"]:
            tier_pages = ["Planning", "Reports", "Monitoring", "Predictive Analytics", "3D Visualization"]
        elif organization.tier.value == "starter":
            tier_pages = ["Planning", "Reports"]
        else:  # free tier
            tier_pages = []
        
        # Admin-only pages (role-based access)
        admin_pages = []
        if user.role in [UserRole.ADMIN]:
            admin_pages = ["API Management", "Data Collection", "Monitoring"]
        
        # User management pages (always available)
        user_pages = ["Subscription", "Onboarding"]
        
        # Special pages
        special_pages = ["Beta Program"]
        
        # Combine all available pages
        all_pages = base_pages + tier_pages + admin_pages + user_pages + special_pages
        
        page = st.selectbox(
            "Select Module:",
            all_pages,
            help="Choose a module to explore different aspects of traffic planning"
        )
        
        st.markdown("---")
        
        # Show usage stats
        show_usage_stats()
        
        st.markdown("---")
        
        # System status
        st.markdown("### System Status")
        
        # Configure remote data source and show connection status
        is_remote_connected = configure_remote_data_source()
        
        # Check TomTom API credit status with enhanced tracking
        try:
            if is_remote_connected:
                # Get status from remote VM service
                from utils.remote_database import RemoteTrafficData
                client = RemoteTrafficData()
                status = client.get_service_status()
                
                if 'error' not in status:
                    quota_used = status.get('api_requests_today', 0)
                    quota_total = 50000  # Default quota
                    usage_percent = (quota_used / quota_total) * 100 if quota_total > 0 else 0
                    
                    if usage_percent > 90:
                        st.warning(f"🟡 TomTom API: {usage_percent:.1f}% quota used")
                        st.warning(f"Remaining: {quota_total - quota_used:,} requests")
                    elif usage_percent > 75:
                        st.warning(f"🟡 TomTom API: {usage_percent:.1f}% quota used")
                        st.info(f"Remaining: {quota_total - quota_used:,} requests")
                    else:
                        st.success("🟢 TomTom API: Connected (VM)")
                        if usage_percent > 0:
                            st.info(f"Usage: {usage_percent:.1f}% ({quota_total - quota_used:,} remaining)")
                else:
                    st.error("🔴 Remote service unavailable")
            else:
                # Fall back to local collection status
                from utils.enhanced_traffic_collector import get_enhanced_collector
                collector = get_enhanced_collector()
                status = collector.get_collection_status()
                
                if status.get('credit_exhausted', False):
                    st.error("🔴 TomTom API: Credits Exhausted")
                    st.error("⚠️ Data collection stopped")
                    st.markdown("**Fix:** Run `python code/reset_credit_flag.py` after adding credits")
                    
                    # Show detailed credit info
                    if 'usage_percent' in status:
                        st.error(f"Usage: {status['usage_percent']:.1f}% of daily quota")
                    if 'successful_requests' in status and 'failed_requests' in status:
                        st.error(f"Today: {status['successful_requests']:,} successful, {status['failed_requests']:,} failed")
                else:
                    quota_used = status.get('api_requests_today', 0)
                    quota_total = status.get('daily_quota', 50000)
                    usage_percent = status.get('usage_percent', (quota_used / quota_total) * 100)
                    
                    if usage_percent > 90:
                        st.warning(f"🟡 TomTom API: {usage_percent:.1f}% quota used")
                        st.warning(f"Remaining: {status.get('quota_remaining', 0):,} requests")
                    elif usage_percent > 75:
                        st.warning(f"🟡 TomTom API: {usage_percent:.1f}% quota used")
                        st.info(f"Remaining: {status.get('quota_remaining', 0):,} requests")
                    else:
                        st.success("🟢 TomTom API: Connected (Local)")
                        if usage_percent > 0:
                            st.info(f"Usage: {usage_percent:.1f}% ({status.get('quota_remaining', 0):,} remaining)")
        except Exception as e:
            st.warning(f"🟡 API Status: Cannot determine ({str(e)[:50]}...)")
        
        st.success("🟢 Perplexity AI: Connected")
        
        # Show data source mode
        if is_remote_connected:
            st.success("🟢 Database: Remote VM Mode")
        else:
            st.info(f"🟡 Database: Local Mode")
        
        # Consolidated status section
        st.markdown("### Account Status")
        st.markdown(f"**Plan:** {organization.tier.value.title()}")
        st.markdown(f"**Role:** {user.role.value.title()}")
        
        # Subscription expiry warning
        from datetime import datetime, timedelta
        days_remaining = (organization.subscription_expires - datetime.now()).days
        if days_remaining < 30:
            st.warning(f"⚠️ Subscription expires in {days_remaining} days")
        
        # Help and documentation
        with st.expander("📚 Resources & Support"):
            st.markdown("""
            - [Support & Inquiries](mailto:kamron.agg@gmail.com)
            - [Documentation](https://village-docs.example.com)
            - [Community Forum](https://community.village.com)
            """)
    
    # Route to selected page
    if page == "Live Traffic":
        live_traffic.show()
    elif page == "Analytics":
        analytics.show()
    elif page == "Planning":
        planning.show()
    elif page == "Reports":
        reports.show()
    elif page == "Monitoring":
        monitoring.show()
    elif page == "Predictive Analytics":
        from pages.predictive_analytics import show
        show()
    elif page == "3D Visualization":
        from utils.visualization_3d import show_3d_visualization_page
        show_3d_visualization_page()
    elif page == "API Management":
        # Admin-only check
        if user.role != UserRole.ADMIN:
            st.error("Access denied. This page requires Administrator privileges.")
            st.info("Contact your system administrator for access.")
        else:
            show_api_management_page()
    elif page == "Subscription":
        show_current_subscription()
    elif page == "Onboarding":
        from utils.onboarding import show_onboarding_page
        show_onboarding_page()
    elif page == "Data Collection":
        # Admin-only check
        if user.role != UserRole.ADMIN:
            st.error("Access denied. This page requires Administrator privileges.")
            st.info("Contact your system administrator for access.")
        else:
            from pages.data_collection import show
            show()
    elif page == "Beta Program":
        from pages.beta_program import show
        show()
    
    # Footer with village theme
    st.markdown("""
    <div style="
        background: linear-gradient(90deg, #f5f1e8 0%, #faf8f3 100%);
        border-top: 3px solid #5a7c47;
        margin-top: 2rem;
        padding: 1.5rem;
        text-align: center;
        border-radius: 8px;
    ">
        <p style="color: #2d5016; margin: 0; font-weight: 500;"> 
        Built for transportation professionals | Powered by Village
        </p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()