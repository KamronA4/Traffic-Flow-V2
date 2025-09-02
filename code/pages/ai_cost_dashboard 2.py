# pages/ai_cost_dashboard.py - AI Cost Monitoring Dashboard

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add utils to path
current_dir = Path(__file__).parent.parent
sys.path.append(str(current_dir))

from utils.ai_cost_manager import AICostManager
from utils.enterprise_auth import require_auth

@require_auth(min_role="admin")
def show_ai_cost_dashboard():
    """Display AI cost monitoring and analytics dashboard"""
    
    st.title("🤖 AI Cost Monitoring Dashboard")
    st.markdown("Track and manage Perplexity API usage and costs")
    
    # Initialize cost manager
    manager = AICostManager()
    
    # Top metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    daily_cost = manager.get_daily_cost()
    monthly_cost = manager.get_monthly_cost()
    stats = manager.get_usage_stats(days=7)
    
    with col1:
        daily_pct = (daily_cost / manager.max_daily_cost) * 100
        color = "inverse" if daily_pct > 80 else "normal" if daily_pct > 50 else "off"
        st.metric(
            "Today's Cost",
            f"${daily_cost:.2f}",
            delta=f"{daily_pct:.0f}% of limit",
            delta_color=color
        )
    
    with col2:
        monthly_pct = (monthly_cost / manager.max_monthly_cost) * 100
        color = "inverse" if monthly_pct > 80 else "normal" if monthly_pct > 50 else "off"
        st.metric(
            "Monthly Cost",
            f"${monthly_cost:.2f}",
            delta=f"{monthly_pct:.0f}% of limit",
            delta_color=color
        )
    
    with col3:
        st.metric(
            "Avg Token Inflation",
            f"{stats['avg_inflation']:.1f}x",
            delta="Expected vs Actual"
        )
    
    with col4:
        st.metric(
            "7-Day Requests",
            f"{stats['total_requests']:,}",
            delta=f"${stats['avg_cost']:.3f}/req"
        )
    
    # Cost limits progress bars
    st.markdown("### 📊 Usage vs Limits")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Daily Usage**")
        daily_progress = min(daily_cost / manager.max_daily_cost, 1.0)
        
        if daily_progress > 0.9:
            st.error(f"⚠️ Daily limit nearly reached!")
        elif daily_progress > 0.8:
            st.warning(f"📈 At {daily_progress*100:.0f}% of daily limit")
        else:
            st.success(f"✅ Within daily limits: {daily_progress*100:.0f}%")
        
        st.progress(daily_progress)
        st.caption(f"${daily_cost:.2f} / ${manager.max_daily_cost:.2f}")
    
    with col2:
        st.markdown("**Monthly Usage**")
        monthly_progress = min(monthly_cost / manager.max_monthly_cost, 1.0)
        
        if monthly_progress > 0.9:
            st.error(f"⚠️ Monthly limit nearly reached!")
        elif monthly_progress > 0.8:
            st.warning(f"📈 At {monthly_progress*100:.0f}% of monthly limit")
        else:
            st.success(f"✅ Within monthly limits: {monthly_progress*100:.0f}%")
        
        st.progress(monthly_progress)
        st.caption(f"${monthly_cost:.2f} / ${manager.max_monthly_cost:.2f}")
    
    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Usage Trends", "🔍 Token Analysis", "💰 Cost Breakdown", "⚠️ Alerts"])
    
    with tab1:
        show_usage_trends(manager, stats)
    
    with tab2:
        show_token_analysis(manager)
    
    with tab3:
        show_cost_breakdown(manager, stats)
    
    with tab4:
        show_alerts_and_warnings(manager)
    
    # Cost optimization recommendations
    st.markdown("---")
    st.markdown("### 💡 Cost Optimization Recommendations")
    
    recommendations = generate_cost_recommendations(stats, daily_cost, monthly_cost, manager)
    
    for rec in recommendations:
        if rec['priority'] == 'high':
            st.error(f"🔴 **{rec['title']}**: {rec['description']}")
        elif rec['priority'] == 'medium':
            st.warning(f"🟡 **{rec['title']}**: {rec['description']}")
        else:
            st.info(f"💡 **{rec['title']}**: {rec['description']}")
    
    # Settings section
    with st.expander("⚙️ Cost Management Settings"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            new_daily_limit = st.number_input(
                "Daily Limit ($)",
                min_value=1.0,
                max_value=50.0,
                value=manager.max_daily_cost,
                step=1.0
            )
            
            if st.button("Update Daily Limit"):
                manager.max_daily_cost = new_daily_limit
                st.success(f"Daily limit updated to ${new_daily_limit:.2f}")
        
        with col2:
            new_monthly_limit = st.number_input(
                "Monthly Limit ($)",
                min_value=10.0,
                max_value=500.0,
                value=manager.max_monthly_cost,
                step=10.0
            )
            
            if st.button("Update Monthly Limit"):
                manager.max_monthly_cost = new_monthly_limit
                st.success(f"Monthly limit updated to ${new_monthly_limit:.2f}")
        
        with col3:
            alert_threshold = st.slider(
                "Alert Threshold",
                min_value=0.5,
                max_value=1.0,
                value=manager.alert_threshold,
                step=0.05,
                format="%.0%%"
            )
            
            if st.button("Update Alert Threshold"):
                manager.alert_threshold = alert_threshold
                st.success(f"Alert threshold updated to {alert_threshold*100:.0f}%")

def show_usage_trends(manager, stats):
    """Show usage trends over time"""
    
    # Daily breakdown chart
    if stats['daily_breakdown']:
        df = pd.DataFrame(stats['daily_breakdown'])
        df['date'] = pd.to_datetime(df['date'])
        
        # Cost trend
        fig_cost = px.line(
            df,
            x='date',
            y='cost',
            title='Daily AI Costs',
            markers=True
        )
        fig_cost.add_hline(
            y=manager.max_daily_cost,
            line_dash="dash",
            line_color="red",
            annotation_text="Daily Limit"
        )
        fig_cost.update_layout(
            xaxis_title="Date",
            yaxis_title="Cost ($)",
            hovermode='x unified'
        )
        st.plotly_chart(fig_cost, use_container_width=True)
        
        # Request volume
        fig_requests = px.bar(
            df,
            x='date',
            y='requests',
            title='Daily Request Volume',
            color='cost',
            color_continuous_scale='Greens'
        )
        fig_requests.update_layout(
            xaxis_title="Date",
            yaxis_title="Number of Requests"
        )
        st.plotly_chart(fig_requests, use_container_width=True)
    else:
        st.info("No usage data available yet. Start analyzing incidents to see trends.")

def show_token_analysis(manager):
    """Show token usage analysis"""
    
    st.markdown("#### Token Usage Patterns")
    
    # Get detailed token data
    import sqlite3
    conn = sqlite3.connect(manager.db_path)
    
    # Token inflation distribution
    query = """
        SELECT 
            token_inflation_ratio,
            COUNT(*) as count
        FROM ai_usage
        WHERE timestamp >= datetime('now', '-7 days')
        GROUP BY CAST(token_inflation_ratio AS INTEGER)
        ORDER BY token_inflation_ratio
    """
    
    df_inflation = pd.read_sql_query(query, conn)
    
    if not df_inflation.empty:
        fig_inflation = px.bar(
            df_inflation,
            x='token_inflation_ratio',
            y='count',
            title='Token Inflation Distribution (Last 7 Days)',
            labels={'token_inflation_ratio': 'Inflation Ratio', 'count': 'Number of Requests'}
        )
        
        # Add color coding
        colors = ['green' if x < 5 else 'yellow' if x < 10 else 'red' 
                 for x in df_inflation['token_inflation_ratio']]
        fig_inflation.update_traces(marker_color=colors)
        
        st.plotly_chart(fig_inflation, use_container_width=True)
    
    # Top token-consuming requests
    query = """
        SELECT 
            incident_id,
            total_tokens,
            token_inflation_ratio,
            cost,
            timestamp
        FROM ai_usage
        WHERE timestamp >= datetime('now', '-7 days')
        ORDER BY total_tokens DESC
        LIMIT 10
    """
    
    df_top = pd.read_sql_query(query, conn)
    
    if not df_top.empty:
        st.markdown("#### Top Token-Consuming Requests")
        
        # Format the dataframe
        df_top['timestamp'] = pd.to_datetime(df_top['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
        df_top['cost'] = df_top['cost'].apply(lambda x: f"${x:.4f}")
        df_top['token_inflation_ratio'] = df_top['token_inflation_ratio'].apply(lambda x: f"{x:.1f}x")
        
        st.dataframe(
            df_top.rename(columns={
                'incident_id': 'Incident',
                'total_tokens': 'Tokens',
                'token_inflation_ratio': 'Inflation',
                'cost': 'Cost',
                'timestamp': 'Time'
            }),
            use_container_width=True,
            hide_index=True
        )
    
    conn.close()

def show_cost_breakdown(manager, stats):
    """Show cost breakdown analysis"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Cost by model
        st.markdown("#### Cost by Model")
        
        model_costs = {
            'Sonar Small': stats['total_cost'] * 0.7,  # Estimate
            'Sonar Large': stats['total_cost'] * 0.2,
            'Articles': stats['total_cost'] * 0.1
        }
        
        fig_pie = px.pie(
            values=list(model_costs.values()),
            names=list(model_costs.keys()),
            title="Cost Distribution by Model"
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        # Cost efficiency metrics
        st.markdown("#### Cost Efficiency")
        
        if stats['total_requests'] > 0:
            st.metric("Average Cost per Request", f"${stats['avg_cost']:.4f}")
            st.metric("Total Weekly Cost", f"${stats['total_cost']:.2f}")
            st.metric("Projected Monthly Cost", f"${stats['total_cost'] * 4.3:.2f}")
            
            # Efficiency score (lower inflation = better)
            efficiency_score = max(0, 100 - (stats['avg_inflation'] - 1) * 20)
            st.metric("Efficiency Score", f"{efficiency_score:.0f}/100")

def show_alerts_and_warnings(manager):
    """Show alerts and warnings"""
    
    import sqlite3
    conn = sqlite3.connect(manager.db_path)
    
    # Get recent alerts
    query = """
        SELECT * FROM cost_alerts
        WHERE timestamp >= datetime('now', '-7 days')
        ORDER BY timestamp DESC
        LIMIT 20
    """
    
    df_alerts = pd.read_sql_query(query, conn)
    
    if not df_alerts.empty:
        st.markdown("#### Recent Alerts")
        
        for _, alert in df_alerts.iterrows():
            alert_time = pd.to_datetime(alert['timestamp']).strftime('%Y-%m-%d %H:%M')
            
            if 'daily' in alert['alert_type']:
                st.warning(f"⚠️ **{alert_time}**: {alert['message']}")
            elif 'monthly' in alert['alert_type']:
                st.error(f"🚨 **{alert_time}**: {alert['message']}")
            else:
                st.info(f"ℹ️ **{alert_time}**: {alert['message']}")
    else:
        st.success("✅ No recent alerts - all systems operating within limits")
    
    # High inflation warnings
    query = """
        SELECT 
            COUNT(*) as high_inflation_count
        FROM ai_usage
        WHERE timestamp >= datetime('now', '-24 hours')
        AND token_inflation_ratio > 5
    """
    
    result = conn.execute(query).fetchone()
    high_inflation_count = result[0] if result else 0
    
    if high_inflation_count > 0:
        st.warning(f"⚠️ {high_inflation_count} requests with high token inflation (>5x) in last 24 hours")
    
    conn.close()

def generate_cost_recommendations(stats, daily_cost, monthly_cost, manager):
    """Generate cost optimization recommendations"""
    
    recommendations = []
    
    # Check token inflation
    if stats['avg_inflation'] > 5:
        recommendations.append({
            'title': 'High Token Inflation Detected',
            'description': f"Average token usage is {stats['avg_inflation']:.1f}x expected. Consider using simplified prompts or checking for API response issues.",
            'priority': 'high'
        })
    elif stats['avg_inflation'] > 3:
        recommendations.append({
            'title': 'Moderate Token Inflation',
            'description': f"Token usage is {stats['avg_inflation']:.1f}x expected. Review prompt engineering to reduce costs.",
            'priority': 'medium'
        })
    
    # Check daily usage patterns
    if daily_cost > manager.max_daily_cost * 0.5:
        recommendations.append({
            'title': 'Enable Aggressive Caching',
            'description': 'Daily usage is high. Enable 48-hour caching for similar incidents to reduce API calls.',
            'priority': 'high'
        })
    
    # Check request frequency
    if stats['total_requests'] > 100:
        recommendations.append({
            'title': 'Consider Batch Processing',
            'description': 'High request volume detected. Batch similar incidents together to reduce per-request costs.',
            'priority': 'medium'
        })
    
    # Model recommendations
    if stats['avg_cost'] > 0.01:
        recommendations.append({
            'title': 'Use Tiered Model Selection',
            'description': 'Use cheaper models for minor incidents and save expensive models for critical analysis.',
            'priority': 'medium'
        })
    
    # Success message if optimized
    if stats['avg_inflation'] < 2 and daily_cost < manager.max_daily_cost * 0.3:
        recommendations.append({
            'title': 'Excellent Cost Management',
            'description': 'Your API usage is well-optimized with low token inflation and efficient caching.',
            'priority': 'low'
        })
    
    return recommendations

if __name__ == "__main__":
    show_ai_cost_dashboard()