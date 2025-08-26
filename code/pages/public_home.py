# pages/public_home.py - Public landing page for free tier users

import streamlit as st
import sys
from pathlib import Path

# Add utils to path
current_dir = Path(__file__).parent.parent
sys.path.append(str(current_dir))

from utils.monetization import MonetizationManager, show_ads, show_donation_widget, init_analytics

def show_public_home():
    """Display public home page with free tier features"""
    
    # Initialize analytics
    init_analytics()
    
    # Initialize monetization
    manager = MonetizationManager()
    
    # Header ad
    show_ads('header_banner', 'home')
    
    # Hero section
    st.markdown("""
    <div style='text-align: center; padding: 2rem 0;'>
        <h1 style='color: #2d5016; font-size: 3rem; margin-bottom: 1rem;'>
            🏘️ Village
        </h1>
        <h2 style='color: #5a7c47; font-size: 1.5rem; margin-bottom: 2rem;'>
            Free Municipal Traffic Planning Platform
        </h2>
        <p style='font-size: 1.2rem; color: #666; max-width: 800px; margin: 0 auto;'>
            Monitor traffic incidents in real-time, analyze patterns, and make data-driven 
            planning decisions for your municipality - completely free for small communities.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # CTA buttons
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Start Free Monitoring", type="primary", use_container_width=True):
            st.switch_page("pages/live_traffic.py")
            
        if st.button("📊 View Demo Dashboard", use_container_width=True):
            st.switch_page("pages/analytics.py")
    
    # Features grid with sidebar ad
    col_main, col_sidebar = st.columns([3, 1])
    
    with col_main:
        st.markdown("## 🌟 Free Features")
        
        # Feature cards
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div style='padding: 1.5rem; border: 2px solid #5a7c47; border-radius: 10px; margin-bottom: 1rem;'>
                <h3 style='color: #2d5016; margin-top: 0;'>🚦 Real-Time Monitoring</h3>
                <p>Track traffic incidents as they happen with live updates from TomTom API</p>
                <ul>
                    <li>Live incident mapping</li>
                    <li>Automatic updates every 15 minutes</li>
                    <li>1,000 incidents per month</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div style='padding: 1.5rem; border: 2px solid #5a7c47; border-radius: 10px; margin-bottom: 1rem;'>
                <h3 style='color: #2d5016; margin-top: 0;'>📈 Basic Analytics</h3>
                <p>Understand traffic patterns with simple charts and statistics</p>
                <ul>
                    <li>Incident frequency charts</li>
                    <li>Peak hour analysis</li>
                    <li>Basic trend visualization</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div style='padding: 1.5rem; border: 2px solid #5a7c47; border-radius: 10px; margin-bottom: 1rem;'>
                <h3 style='color: #2d5016; margin-top: 0;'>📧 Email Alerts</h3>
                <p>Get notified about significant traffic events in your area</p>
                <ul>
                    <li>Daily incident summaries</li>
                    <li>Major incident alerts</li>
                    <li>Weekly trend reports</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div style='padding: 1.5rem; border: 2px solid #5a7c47; border-radius: 10px; margin-bottom: 1rem;'>
                <h3 style='color: #2d5016; margin-top: 0;'>📄 CSV Export</h3>
                <p>Download your data for further analysis or record keeping</p>
                <ul>
                    <li>Export incident data</li>
                    <li>7-day data retention</li>
                    <li>Compatible with Excel</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
    
    with col_sidebar:
        # Sidebar ad
        show_ads('sidebar', 'home')
        
        # Donation section
        st.markdown("---")
        st.markdown("### ☕ Support Village")
        st.markdown("Help us keep Village free for small municipalities!")
        
        # Buy Me a Coffee button
        manager.render_buymeacoffee_button()
        
        st.markdown("""
        <small style='color: #666;'>
            Donations help cover server costs and API usage, 
            keeping Village free for communities that need it most.
        </small>
        """, unsafe_allow_html=True)
    
    # Social proof section
    st.markdown("---")
    st.markdown("## 🏆 Trusted by Municipalities")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Active Users", "2,500+", "↗️ 25%")
    with col2:
        st.metric("Incidents Tracked", "1.2M+", "📈")
    with col3:
        st.metric("Municipalities", "150+", "🌍")
    with col4:
        st.metric("Uptime", "99.9%", "⚡")
    
    # Testimonials
    st.markdown("### 💬 What Users Say")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style='padding: 1rem; background-color: #f5f1e8; border-radius: 8px;'>
            <p><em>"Village transformed how we monitor traffic. The free tier is perfect for our small town!"</em></p>
            <strong>- Sarah M., Traffic Coordinator</strong>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style='padding: 1rem; background-color: #f5f1e8; border-radius: 8px;'>
            <p><em>"Real-time alerts help us respond to incidents faster than ever before."</em></p>
            <strong>- Mike R., Public Works</strong>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style='padding: 1rem; background-color: #f5f1e8; border-radius: 8px;'>
            <p><em>"The data exports save us hours of manual reporting each week."</em></p>
            <strong>- Lisa T., City Planner</strong>
        </div>
        """, unsafe_allow_html=True)
    
    # Pro features preview
    st.markdown("---")
    st.markdown("## 🔒 Unlock More with Pro")
    
    # In-content ad
    show_ads('in_content', 'home')
    
    col_features, col_pricing = st.columns([2, 1])
    
    with col_features:
        st.markdown("""
        ### Upgrade to unlock powerful features:
        
        🤖 **AI-Powered Analysis**
        - Contextual incident insights with Perplexity AI
        - Automated pattern recognition
        - Intelligent traffic predictions
        
        📊 **Advanced Analytics**
        - Predictive traffic modeling
        - Custom dashboard creation
        - Historical trend analysis
        
        🔌 **API Access**
        - Integrate with existing systems
        - Real-time data feeds
        - Custom applications
        
        📈 **Unlimited Usage**
        - No incident limits
        - Unlimited team members
        - Extended data retention
        """)
    
    with col_pricing:
        st.markdown("""
        <div style='padding: 2rem; border: 3px solid #2d5016; border-radius: 10px; text-align: center; background-color: #f5f1e8;'>
            <h3 style='color: #2d5016; margin-top: 0;'>Village Pro</h3>
            <div style='font-size: 2rem; color: #2d5016; font-weight: bold;'>
                $24<small style='font-size: 1rem;'>/month</small>
            </div>
            <div style='text-decoration: line-through; color: #999;'>$49/month</div>
            <p style='color: #d32f2f; font-weight: bold;'>50% OFF Early Bird Special!</p>
            <p style='font-size: 0.9rem;'>First 100 customers only</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚀 Start Pro Trial", type="primary", use_container_width=True):
            st.switch_page("pages/pricing.py")
        
        st.markdown("""
        <div style='text-align: center; margin-top: 1rem;'>
            <small>✅ 14-day free trial<br>
            ✅ No credit card required<br>
            ✅ Cancel anytime</small>
        </div>
        """, unsafe_allow_html=True)
    
    # FAQ section
    st.markdown("---")
    st.markdown("## ❓ Frequently Asked Questions")
    
    with st.expander("Is Village really free?"):
        st.markdown("""
        Yes! Our Community Edition is completely free for small municipalities. 
        It includes real-time monitoring, basic analytics, and data export for up to 1,000 incidents per month.
        We support this through optional donations and Pro subscriptions.
        """)
    
    with st.expander("What's the difference between Community and Pro?"):
        st.markdown("""
        **Community (Free):**
        - 1,000 incidents/month
        - Basic monitoring & analytics  
        - Email notifications
        - 2 users, 7-day data retention
        
        **Pro ($24/month):**
        - Unlimited incidents
        - AI-powered analysis
        - Predictive analytics
        - API access, unlimited users
        - Extended data retention
        """)
    
    with st.expander("How do donations work?"):
        st.markdown("""
        Donations are completely optional and help us keep the free tier available. 
        All donations go toward server costs, API usage, and platform development.
        You can donate any amount through Buy Me a Coffee - even $3 helps!
        """)
    
    with st.expander("Can I upgrade or downgrade anytime?"):
        st.markdown("""
        Yes! You can upgrade to Pro anytime to unlock advanced features. 
        If you downgrade, you'll keep Pro features until your current billing period ends,
        then transition back to the free Community Edition.
        """)
    
    # Footer CTA
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style='text-align: center; padding: 2rem; background-color: #2d5016; border-radius: 10px; color: white;'>
            <h3 style='color: white; margin-top: 0;'>Ready to Get Started?</h3>
            <p>Join thousands of municipalities using Village to improve their traffic planning.</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🏘️ Create Free Account", type="primary", use_container_width=True, key="footer_cta"):
            st.switch_page("pages/signup.py")
    
    # Donation widget (floating)
    show_donation_widget()

if __name__ == "__main__":
    show_public_home()