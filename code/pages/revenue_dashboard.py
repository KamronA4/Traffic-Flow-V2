# pages/revenue_dashboard.py - Revenue tracking and analytics dashboard

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
import sys
from pathlib import Path
import json

# Add utils to path
current_dir = Path(__file__).parent.parent
sys.path.append(str(current_dir))

from utils.monetization import MonetizationManager
from utils.enterprise_auth import require_auth, get_current_user

@require_auth(min_role="admin")
def show_revenue_dashboard():
    """Display revenue analytics dashboard for admins"""
    
    st.title("💰 Revenue Analytics Dashboard")
    st.markdown("Track monetization performance and growth metrics")
    
    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", date.today() - timedelta(days=30))
    with col2:
        end_date = st.date_input("End Date", date.today())
    
    # Generate sample data (in production, pull from analytics APIs)
    revenue_data = generate_sample_revenue_data(start_date, end_date)
    
    # Key metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Revenue",
            f"${revenue_data['total_revenue']:,.2f}",
            delta=f"{revenue_data['revenue_growth']:+.1f}%"
        )
    
    with col2:
        st.metric(
            "Monthly Recurring Revenue",
            f"${revenue_data['mrr']:,.2f}",
            delta=f"{revenue_data['mrr_growth']:+.1f}%"
        )
    
    with col3:
        st.metric(
            "Active Subscribers",
            f"{revenue_data['subscribers']:,}",
            delta=f"{revenue_data['subscriber_growth']:+d}"
        )
    
    with col4:
        st.metric(
            "Avg Revenue per User",
            f"${revenue_data['arpu']:.2f}",
            delta=f"{revenue_data['arpu_growth']:+.1f}%"
        )
    
    # Revenue breakdown chart
    st.markdown("## 📊 Revenue Breakdown")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Revenue sources pie chart
        sources = {
            'Pro Subscriptions': revenue_data['subscription_revenue'],
            'Google AdSense': revenue_data['ad_revenue'],
            'Donations': revenue_data['donation_revenue'],
            'Enterprise': revenue_data['enterprise_revenue']
        }
        
        fig_pie = px.pie(
            values=list(sources.values()),
            names=list(sources.keys()),
            title="Revenue by Source",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        # Monthly revenue trend
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
        monthly_revenue = [1200, 1850, 2400, 3100, 3800, 4500]
        
        fig_line = px.line(
            x=months, 
            y=monthly_revenue,
            title="Monthly Revenue Trend",
            labels={'x': 'Month', 'y': 'Revenue ($)'}
        )
        fig_line.update_traces(line_color='#2d5016', line_width=3)
        st.plotly_chart(fig_line, use_container_width=True)
    
    # Detailed analytics tabs
    tab1, tab2, tab3, tab4 = st.tabs(["💳 Subscriptions", "📺 Advertising", "☕ Donations", "📈 Growth"])
    
    with tab1:
        show_subscription_analytics(revenue_data)
    
    with tab2:
        show_advertising_analytics(revenue_data)
    
    with tab3:
        show_donation_analytics(revenue_data)
    
    with tab4:
        show_growth_analytics(revenue_data)
    
    # Revenue events log
    st.markdown("## 📋 Recent Revenue Events")
    
    # Get events from session state (in production, from database)
    events = st.session_state.get('revenue_events', [])
    
    if events:
        events_df = pd.DataFrame(events[-20:])  # Last 20 events
        st.dataframe(events_df, use_container_width=True)
    else:
        st.info("No revenue events recorded yet. Events will appear here as users interact with monetization features.")
    
    # Revenue optimization recommendations
    st.markdown("## 💡 Optimization Recommendations")
    
    recommendations = generate_recommendations(revenue_data)
    
    for rec in recommendations:
        if rec['priority'] == 'high':
            st.error(f"🔥 **{rec['title']}**: {rec['description']}")
        elif rec['priority'] == 'medium':
            st.warning(f"⚡ **{rec['title']}**: {rec['description']}")
        else:
            st.info(f"💡 **{rec['title']}**: {rec['description']}")

def show_subscription_analytics(data):
    """Show subscription-specific analytics"""
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Pro Subscribers", f"{data['pro_subscribers']:,}", "+12")
        st.metric("Free Users", f"{data['free_users']:,}", "+156")
    
    with col2:
        st.metric("Conversion Rate", f"{data['conversion_rate']:.1f}%", "+0.3%")
        st.metric("Churn Rate", f"{data['churn_rate']:.1f}%", "-0.2%")
    
    with col3:
        st.metric("Trial Signups", f"{data['trial_signups']:,}", "+8")
        st.metric("Trial Conversion", f"{data['trial_conversion']:.1f}%", "+2.1%")
    
    # Subscription funnel
    st.markdown("### Subscription Funnel")
    
    funnel_data = {
        'Stage': ['Visitors', 'Free Signups', 'Trial Starts', 'Paid Conversions'],
        'Count': [data['visitors'], data['free_signups'], data['trial_signups'], data['pro_subscribers']],
        'Conversion': [100, data['signup_rate'], data['trial_rate'], data['conversion_rate']]
    }
    
    funnel_df = pd.DataFrame(funnel_data)
    
    fig_funnel = px.funnel(
        funnel_df, 
        x='Count', 
        y='Stage',
        title="Subscription Conversion Funnel"
    )
    st.plotly_chart(fig_funnel, use_container_width=True)
    
    # Subscriber cohorts
    st.markdown("### Subscriber Cohorts")
    
    cohort_data = {
        'Cohort': ['Jan 2025', 'Feb 2025', 'Mar 2025', 'Apr 2025', 'May 2025'],
        'Initial Size': [25, 38, 52, 67, 83],
        'Retained (Month 1)': [23, 35, 48, 61, 79],
        'Retained (Month 2)': [21, 32, 44, 58, None],
        'Retained (Month 3)': [19, 29, 41, None, None]
    }
    
    cohort_df = pd.DataFrame(cohort_data)
    st.dataframe(cohort_df, use_container_width=True)

def show_advertising_analytics(data):
    """Show advertising revenue analytics"""
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Ad Revenue", f"${data['ad_revenue']:,.2f}", "+15%")
    
    with col2:
        st.metric("Impressions", f"{data['ad_impressions']:,}", "+8%")
    
    with col3:
        st.metric("Click Rate", f"{data['ad_ctr']:.2f}%", "+0.1%")
    
    with col4:
        st.metric("RPM", f"${data['ad_rpm']:.2f}", "+12%")
    
    # Ad performance by placement
    st.markdown("### Ad Performance by Placement")
    
    placement_data = {
        'Placement': ['Header Banner', 'Sidebar', 'In-Content', 'Footer'],
        'Impressions': [45000, 38000, 25000, 12000],
        'Clicks': [315, 228, 175, 48],
        'Revenue': [127.50, 89.20, 68.25, 18.40],
        'CTR': [0.70, 0.60, 0.70, 0.40]
    }
    
    placement_df = pd.DataFrame(placement_data)
    st.dataframe(placement_df, use_container_width=True)
    
    # Top performing pages
    st.markdown("### Top Revenue Pages")
    
    page_data = {
        'Page': ['/live-traffic', '/analytics', '/reports', '/pricing', '/home'],
        'Visitors': [12500, 8900, 6200, 4300, 15600],
        'Ad Revenue': [45.20, 32.10, 28.50, 12.80, 38.90],
        'RPM': [3.62, 3.61, 4.60, 2.98, 2.49]
    }
    
    pages_df = pd.DataFrame(page_data)
    
    fig_pages = px.bar(
        pages_df,
        x='Page',
        y='Ad Revenue',
        title="Ad Revenue by Page",
        color='RPM',
        color_continuous_scale='Greens'
    )
    st.plotly_chart(fig_pages, use_container_width=True)

def show_donation_analytics(data):
    """Show donation analytics"""
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Donations", f"${data['donation_revenue']:,.2f}", "+22%")
    
    with col2:
        st.metric("Donors", f"{data['donors']:,}", "+5")
    
    with col3:
        st.metric("Avg Donation", f"${data['avg_donation']:.2f}", "+$0.50")
    
    with col4:
        st.metric("Conversion Rate", f"{data['donation_conversion']:.2f}%", "+0.1%")
    
    # Donation amounts distribution
    st.markdown("### Donation Distribution")
    
    donation_amounts = {
        'Amount': ['$3', '$5', '$10', '$25', '$50', '$100+'],
        'Count': [45, 32, 28, 12, 6, 3],
        'Percentage': [36, 25.6, 22.4, 9.6, 4.8, 2.4]
    }
    
    amounts_df = pd.DataFrame(donation_amounts)
    
    fig_donations = px.bar(
        amounts_df,
        x='Amount',
        y='Count',
        title="Donation Amounts",
        text='Percentage'
    )
    fig_donations.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    st.plotly_chart(fig_donations, use_container_width=True)
    
    # Top donors (anonymized)
    st.markdown("### Recent Donations")
    
    recent_donations = {
        'Date': ['2025-01-15', '2025-01-14', '2025-01-13', '2025-01-12', '2025-01-11'],
        'Amount': ['$25.00', '$10.00', '$5.00', '$50.00', '$15.00'],
        'Message': [
            'Great tool for our city planning!',
            'Keep up the awesome work!',
            'Thanks for keeping it free!',
            'Love the AI analysis feature',
            'Hope this helps with server costs'
        ],
        'Location': ['Springfield, IL', 'Austin, TX', 'Portland, OR', 'Denver, CO', 'Miami, FL']
    }
    
    donations_df = pd.DataFrame(recent_donations)
    st.dataframe(donations_df, use_container_width=True, hide_index=True)

def show_growth_analytics(data):
    """Show growth and cohort analytics"""
    
    # Growth metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Monthly Growth Rate", f"{data['growth_rate']:.1f}%", "+2.3%")
        st.metric("Customer Acquisition Cost", f"${data['cac']:.2f}", "-$5.20")
    
    with col2:
        st.metric("Customer Lifetime Value", f"${data['ltv']:.2f}", "+$12.50")
        st.metric("LTV/CAC Ratio", f"{data['ltv_cac_ratio']:.1f}x", "+0.4x")
    
    with col3:
        st.metric("Payback Period", f"{data['payback_months']:.1f} months", "-0.5")
        st.metric("Net Revenue Retention", f"{data['nrr']:.0f}%", "+5%")
    
    # Growth projections
    st.markdown("### Revenue Projections")
    
    months = ['Current', '+1 Month', '+2 Months', '+3 Months', '+6 Months', '+12 Months']
    projections = {
        'Conservative': [4500, 5200, 6000, 6900, 10500, 18000],
        'Optimistic': [4500, 5800, 7200, 9100, 15200, 28000],
        'Aggressive': [4500, 6500, 8800, 12200, 22000, 42000]
    }
    
    fig_projections = go.Figure()
    
    for scenario, values in projections.items():
        fig_projections.add_trace(go.Scatter(
            x=months,
            y=values,
            mode='lines+markers',
            name=scenario,
            line=dict(width=3)
        ))
    
    fig_projections.update_layout(
        title="Revenue Growth Projections",
        xaxis_title="Timeline",
        yaxis_title="Monthly Revenue ($)",
        hovermode='x unified'
    )
    
    st.plotly_chart(fig_projections, use_container_width=True)
    
    # Key growth drivers
    st.markdown("### Growth Drivers & Initiatives")
    
    initiatives = [
        {'name': 'SEO Content Marketing', 'impact': 'High', 'effort': 'Medium', 'timeline': '3-6 months'},
        {'name': 'Referral Program Launch', 'impact': 'Medium', 'effort': 'Low', 'timeline': '1 month'},
        {'name': 'Municipality Partnerships', 'impact': 'High', 'effort': 'High', 'timeline': '6-12 months'},
        {'name': 'Mobile App Development', 'impact': 'Medium', 'effort': 'High', 'timeline': '6-9 months'},
        {'name': 'Enterprise Sales Team', 'impact': 'High', 'effort': 'High', 'timeline': '3-6 months'},
        {'name': 'API Marketplace', 'impact': 'Medium', 'effort': 'Medium', 'timeline': '4-6 months'}
    ]
    
    initiatives_df = pd.DataFrame(initiatives)
    st.dataframe(initiatives_df, use_container_width=True, hide_index=True)

def generate_sample_revenue_data(start_date, end_date):
    """Generate sample revenue data for dashboard"""
    
    return {
        # Overall metrics
        'total_revenue': 4520.75,
        'revenue_growth': 28.5,
        'mrr': 3890.00,
        'mrr_growth': 15.2,
        'subscribers': 157,
        'subscriber_growth': 23,
        'arpu': 24.77,
        'arpu_growth': 3.8,
        
        # Revenue breakdown
        'subscription_revenue': 3890.00,
        'ad_revenue': 303.45,
        'donation_revenue': 247.30,
        'enterprise_revenue': 80.00,
        
        # Subscription metrics
        'pro_subscribers': 157,
        'free_users': 2340,
        'trial_signups': 45,
        'conversion_rate': 2.8,
        'trial_conversion': 35.2,
        'churn_rate': 3.2,
        'visitors': 15600,
        'free_signups': 312,
        'signup_rate': 2.0,
        'trial_rate': 14.4,
        
        # Ad metrics
        'ad_impressions': 120000,
        'ad_ctr': 0.62,
        'ad_rpm': 2.53,
        
        # Donation metrics
        'donors': 126,
        'avg_donation': 8.95,
        'donation_conversion': 0.81,
        
        # Growth metrics
        'growth_rate': 18.3,
        'cac': 47.20,
        'ltv': 385.50,
        'ltv_cac_ratio': 8.2,
        'payback_months': 1.9,
        'nrr': 112
    }

def generate_recommendations(data):
    """Generate optimization recommendations based on data"""
    
    recommendations = []
    
    # Conversion rate optimization
    if data['conversion_rate'] < 3.0:
        recommendations.append({
            'title': 'Improve Trial Conversion',
            'description': f'Conversion rate is {data["conversion_rate"]:.1f}%. Add onboarding flow and feature demos to increase to 5%+',
            'priority': 'high'
        })
    
    # Ad revenue optimization
    if data['ad_rpm'] < 3.0:
        recommendations.append({
            'title': 'Optimize Ad Placement',
            'description': f'RPM is ${data["ad_rpm"]:.2f}. Test above-fold placements and responsive ad units',
            'priority': 'medium'
        })
    
    # Donation optimization
    if data['donation_conversion'] < 1.0:
        recommendations.append({
            'title': 'Enhance Donation Appeal',
            'description': f'Donation rate is {data["donation_conversion"]:.2f}%. Add impact messaging and supporter recognition',
            'priority': 'medium'
        })
    
    # Growth recommendations
    if data['growth_rate'] < 20.0:
        recommendations.append({
            'title': 'Accelerate User Acquisition',
            'description': f'Growth is {data["growth_rate"]:.1f}%. Launch referral program and content marketing',
            'priority': 'high'
        })
    
    # Always include positive reinforcement
    recommendations.append({
        'title': 'Strong LTV/CAC Ratio',
        'description': f'Your {data["ltv_cac_ratio"]:.1f}x ratio indicates healthy unit economics. Consider increasing marketing spend',
        'priority': 'low'
    })
    
    return recommendations

if __name__ == "__main__":
    show_revenue_dashboard()