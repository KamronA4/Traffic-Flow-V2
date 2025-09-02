# pages/pricing.py - Pricing page with Pro upgrade and waitlist

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime, timedelta
import json

# Add utils to path
current_dir = Path(__file__).parent.parent
sys.path.append(str(current_dir))

from utils.monetization import MonetizationManager, show_ads, init_analytics
from utils.database import DatabaseManager

def show_pricing_page():
    """Display pricing page with Pro tier and early bird special"""
    
    # Initialize analytics
    init_analytics()
    
    # Show ads for free users
    manager = MonetizationManager()
    show_ads('header_banner', 'pricing')
    
    # Page header
    st.markdown("""
    <div style='text-align: center; padding: 2rem 0;'>
        <h1 style='color: #2d5016; font-size: 2.5rem; margin-bottom: 1rem;'>
            💰 Village Pricing
        </h1>
        <p style='font-size: 1.2rem; color: #666; max-width: 600px; margin: 0 auto;'>
            Choose the plan that's right for your municipality
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Pricing toggle
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        billing = st.radio("Billing Cycle", ["Monthly", "Annual (17% off)"], horizontal=True, key="billing_cycle")
    
    # Pricing cards
    col1, col2 = st.columns(2)
    
    # Free tier
    with col1:
        st.markdown("""
        <div style='padding: 2rem; border: 2px solid #5a7c47; border-radius: 15px; height: 600px; background-color: #faf8f3;'>
            <div style='text-align: center;'>
                <h3 style='color: #2d5016; font-size: 1.8rem; margin-bottom: 0.5rem;'>Community Edition</h3>
                <div style='font-size: 3rem; color: #2d5016; font-weight: bold; margin: 1rem 0;'>
                    FREE
                </div>
                <p style='color: #666; margin-bottom: 2rem;'>Perfect for small municipalities</p>
            </div>
            
            <div style='text-align: left; margin-bottom: 2rem;'>
                <h4 style='color: #2d5016; margin-bottom: 1rem;'>✅ What's Included:</h4>
                <ul style='list-style: none; padding-left: 0;'>
                    <li style='margin: 0.5rem 0;'>🚦 Real-time traffic monitoring</li>
                    <li style='margin: 0.5rem 0;'>📊 Basic analytics dashboard</li>
                    <li style='margin: 0.5rem 0;'>📧 Email notifications</li>
                    <li style='margin: 0.5rem 0;'>📄 CSV data export</li>
                    <li style='margin: 0.5rem 0;'>👥 2 user accounts</li>
                    <li style='margin: 0.5rem 0;'>📅 7-day data retention</li>
                    <li style='margin: 0.5rem 0;'>💬 Community support</li>
                </ul>
                
                <div style='margin-top: 1.5rem; padding: 1rem; background-color: #e8f5e8; border-radius: 8px;'>
                    <strong>Usage Limits:</strong><br>
                    • 1,000 incidents/month<br>
                    • 100 API calls/day<br>
                    • 3 custom reports/month
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Get Started Free", use_container_width=True, type="secondary"):
            st.switch_page("pages/signup.py")
    
    # Pro tier
    with col2:
        monthly_price = 24.50 if billing == "Monthly" else 20.25  # Annual discount
        original_price = 49 if billing == "Monthly" else 40.75
        
        st.markdown(f"""
        <div style='padding: 2rem; border: 3px solid #2d5016; border-radius: 15px; height: 600px; background: linear-gradient(135deg, #f5f1e8 0%, #e8f5e8 100%); position: relative;'>
            <div style='position: absolute; top: -10px; left: 50%; transform: translateX(-50%); background-color: #d32f2f; color: white; padding: 0.5rem 1rem; border-radius: 20px; font-weight: bold; font-size: 0.9rem;'>
                🔥 EARLY BIRD SPECIAL
            </div>
            
            <div style='text-align: center; margin-top: 1rem;'>
                <h3 style='color: #2d5016; font-size: 1.8rem; margin-bottom: 0.5rem;'>Village Pro</h3>
                <div style='font-size: 2.5rem; color: #2d5016; font-weight: bold; margin: 0.5rem 0;'>
                    ${monthly_price}<small style='font-size: 1rem;'>/month</small>
                </div>
                <div style='text-decoration: line-through; color: #999; font-size: 1.2rem;'>${original_price}/month</div>
                <p style='color: #d32f2f; font-weight: bold; margin-bottom: 1.5rem;'>Save 50% - First 100 customers!</p>
            </div>
            
            <div style='text-align: left; margin-bottom: 1.5rem;'>
                <h4 style='color: #2d5016; margin-bottom: 1rem;'>🚀 Everything in Community, plus:</h4>
                <ul style='list-style: none; padding-left: 0;'>
                    <li style='margin: 0.4rem 0;'>🤖 AI-powered incident analysis</li>
                    <li style='margin: 0.4rem 0;'>📈 Predictive analytics</li>
                    <li style='margin: 0.4rem 0;'>🔌 Full API access</li>
                    <li style='margin: 0.4rem 0;'>👥 Unlimited users</li>
                    <li style='margin: 0.4rem 0;'>🗄️ 36-month data retention</li>
                    <li style='margin: 0.4rem 0;'>📊 Custom reporting tools</li>
                    <li style='margin: 0.4rem 0;'>🎯 Priority support</li>
                    <li style='margin: 0.4rem 0;'>📱 Mobile app access</li>
                </ul>
                
                <div style='margin-top: 1rem; padding: 1rem; background-color: #d4edda; border-radius: 8px;'>
                    <strong>Unlimited:</strong><br>
                    • Incidents & API calls<br>
                    • Custom reports<br>
                    • Team members
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚀 Start 14-Day Free Trial", use_container_width=True, type="primary"):
            show_trial_signup_form()
    
    # Early bird counter
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Mock early bird counter (in real app, pull from database)
        spots_taken = 47
        spots_remaining = 100 - spots_taken
        
        st.markdown(f"""
        <div style='text-align: center; padding: 1.5rem; background-color: #fff3cd; border: 2px solid #ffc107; border-radius: 10px;'>
            <h3 style='color: #856404; margin-top: 0;'>⏰ Limited Time Offer</h3>
            <div style='font-size: 2rem; color: #856404; font-weight: bold;'>
                {spots_remaining} spots left
            </div>
            <p style='margin-bottom: 0;'>Early Bird pricing expires when we reach 100 customers</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Feature comparison table
    st.markdown("---")
    st.markdown("## 📋 Feature Comparison")
    
    # Sidebar ad
    col_main, col_sidebar = st.columns([3, 1])
    
    with col_sidebar:
        show_ads('sidebar', 'pricing')
    
    with col_main:
        comparison_data = {
            "Feature": [
                "Real-time traffic monitoring",
                "Basic analytics dashboard", 
                "Email notifications",
                "CSV data export",
                "User accounts",
                "Data retention",
                "API calls per day",
                "Custom reports per month",
                "AI incident analysis",
                "Predictive analytics",
                "Priority support",
                "Mobile app",
                "Advanced integrations"
            ],
            "Community (Free)": [
                "✅", "✅", "✅", "✅", "2", "7 days", "100", "3",
                "❌", "❌", "❌", "❌", "❌"
            ],
            "Pro": [
                "✅", "✅", "✅", "✅", "Unlimited", "36 months", "Unlimited", "Unlimited",
                "✅", "✅", "✅", "✅", "✅"
            ]
        }
        
        import pandas as pd
        df = pd.DataFrame(comparison_data)
        st.dataframe(df, hide_index=True, use_container_width=True)
    
    # FAQ Section
    st.markdown("---")
    st.markdown("## ❓ Pricing FAQ")
    
    col1, col2 = st.columns(2)
    
    with col1:
        with st.expander("How does the 14-day trial work?"):
            st.markdown("""
            • Full access to all Pro features for 14 days
            • No credit card required to start
            • Automatically switches to free tier if you don't upgrade
            • Cancel anytime with no charges
            """)
        
        with st.expander("Can I change plans anytime?"):
            st.markdown("""
            • Upgrade from Community to Pro instantly
            • Downgrade at the end of your billing cycle
            • Prorated refunds for annual plans
            • No cancellation fees
            """)
        
        with st.expander("What payment methods do you accept?"):
            st.markdown("""
            • All major credit cards (Visa, MasterCard, Amex)
            • PayPal for annual plans
            • Purchase orders for government agencies
            • Bank transfers for Enterprise customers
            """)
    
    with col2:
        with st.expander("Is my data secure?"):
            st.markdown("""
            • SOC 2 Type II certified security
            • 256-bit SSL encryption
            • GDPR and CCPA compliant
            • Regular security audits and backups
            """)
        
        with st.expander("Do you offer discounts?"):
            st.markdown("""
            • 50% off Early Bird special (limited time)
            • 17% discount for annual billing
            • 50% student discount with verification
            • Custom pricing for large municipalities
            """)
        
        with st.expander("What about Enterprise needs?"):
            st.markdown("""
            • Custom feature development available
            • Multi-municipality management
            • SSO and advanced security
            • Dedicated support and training
            
            Contact us for Enterprise pricing.
            """)
    
    # Testimonials
    st.markdown("---")
    st.markdown("## 💬 Customer Success Stories")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style='padding: 1.5rem; background-color: #f8f9fa; border-left: 4px solid #2d5016; border-radius: 8px;'>
            <p><em>"The AI analysis in Pro helped us identify recurring accident spots we never noticed before."</em></p>
            <div style='margin-top: 1rem;'>
                <strong>Jennifer K.</strong><br>
                <small>Traffic Engineer, Springfield</small>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style='padding: 1.5rem; background-color: #f8f9fa; border-left: 4px solid #2d5016; border-radius: 8px;'>
            <p><em>"API access lets us integrate Village data directly into our GIS system. Game changer!"</em></p>
            <div style='margin-top: 1rem;'>
                <strong>Mark R.</strong><br>
                <small>IT Director, Riverside County</small>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style='padding: 1.5rem; background-color: #f8f9fa; border-left: 4px solid #2d5016; border-radius: 8px;'>
            <p><em>"Started with the free tier, upgraded to Pro within a month. The predictive analytics are incredible."</em></p>
            <div style='margin-top: 1rem;'>
                <strong>Carlos M.</strong><br>
                <small>City Planner, Mesa</small>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Bottom CTA
    st.markdown("---")
    
    # In-content ad
    show_ads('in_content', 'pricing')
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style='text-align: center; padding: 2rem; background: linear-gradient(135deg, #2d5016 0%, #5a7c47 100%); border-radius: 15px; color: white;'>
            <h3 style='color: white; margin-top: 0;'>Ready to Supercharge Your Traffic Planning?</h3>
            <p style='font-size: 1.1rem;'>Join the Early Bird program and save 50% for 3 months!</p>
        </div>
        """, unsafe_allow_html=True)
        
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("🚀 Start Pro Trial", type="primary", use_container_width=True, key="bottom_trial"):
                show_trial_signup_form()
        
        with col_b:
            if st.button("📞 Contact Sales", use_container_width=True, key="contact_sales"):
                show_contact_form()

def show_trial_signup_form():
    """Show Pro trial signup form"""
    
    st.markdown("### 🚀 Start Your 14-Day Pro Trial")
    
    with st.form("pro_trial_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            first_name = st.text_input("First Name*", placeholder="John")
            email = st.text_input("Work Email*", placeholder="john@municipality.gov")
            municipality = st.text_input("Municipality*", placeholder="City of Springfield")
        
        with col2:
            last_name = st.text_input("Last Name*", placeholder="Smith")
            phone = st.text_input("Phone Number", placeholder="+1 (555) 123-4567")
            role = st.selectbox("Your Role", [
                "Select your role...",
                "Traffic Engineer",
                "City Planner", 
                "Public Works Director",
                "IT Administrator",
                "Mayor/Council Member",
                "Other"
            ])
        
        # Additional info
        team_size = st.selectbox("Team Size", [
            "Just me",
            "2-5 people", 
            "6-10 people",
            "11-25 people",
            "25+ people"
        ])
        
        current_solution = st.text_area("What tools do you currently use for traffic planning?", 
                                      placeholder="Tell us about your current workflow...")
        
        # Agreements
        col_check1, col_check2 = st.columns([1, 4])
        with col_check1:
            agree_terms = st.checkbox("")
        with col_check2:
            st.markdown("I agree to the [Terms of Service](https://village.app/terms) and [Privacy Policy](https://village.app/privacy)*")
        
        marketing_consent = st.checkbox("Send me updates about new features and traffic planning tips")
        
        submitted = st.form_submit_button("🚀 Start My Free Trial", type="primary", use_container_width=True)
        
        if submitted:
            if not all([first_name, last_name, email, municipality]) or not agree_terms:
                st.error("Please fill in all required fields and agree to terms.")
            else:
                # In real app: create trial account, send email, etc.
                save_trial_signup({
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': email,
                    'phone': phone,
                    'municipality': municipality,
                    'role': role,
                    'team_size': team_size,
                    'current_solution': current_solution,
                    'marketing_consent': marketing_consent,
                    'signup_date': datetime.now().isoformat()
                })
                
                st.success("""
                🎉 **Trial activated!** Check your email for login instructions.
                
                Your 14-day Pro trial includes:
                • Full access to all Pro features
                • AI-powered traffic analysis
                • Unlimited incidents and users
                • Priority support
                """)
                
                st.balloons()

def show_contact_form():
    """Show contact sales form"""
    
    st.markdown("### 📞 Contact Our Sales Team")
    
    with st.form("contact_sales_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Full Name*")
            email = st.text_input("Work Email*")
            organization = st.text_input("Organization*")
        
        with col2:
            phone = st.text_input("Phone Number*")
            role = st.text_input("Job Title*")
            budget = st.selectbox("Annual Budget Range", [
                "Select budget...",
                "Under $10,000",
                "$10,000 - $25,000",
                "$25,000 - $50,000", 
                "$50,000 - $100,000",
                "Over $100,000"
            ])
        
        message = st.text_area("Tell us about your needs*", 
                              placeholder="What are your traffic planning challenges? How many users? Special requirements?")
        
        submitted = st.form_submit_button("📞 Request Demo", type="primary", use_container_width=True)
        
        if submitted:
            if not all([name, email, organization, phone, role, message]):
                st.error("Please fill in all required fields.")
            else:
                # In real app: send to CRM, schedule demo, etc.
                st.success("""
                ✅ **Demo request received!**
                
                Our team will contact you within 1 business day to schedule a personalized demo.
                
                In the meantime, feel free to explore our free Community Edition!
                """)

def save_trial_signup(data):
    """Save trial signup to database/waitlist"""
    # In production: save to database, send to CRM, trigger email sequence
    
    # For now, store in session state
    if 'trial_signups' not in st.session_state:
        st.session_state['trial_signups'] = []
    
    st.session_state['trial_signups'].append(data)
    
    # Track conversion event
    manager = MonetizationManager()
    manager.track_revenue_event('trial_signup', {
        'email': data['email'],
        'municipality': data['municipality'],
        'team_size': data['team_size']
    })

if __name__ == "__main__":
    show_pricing_page()