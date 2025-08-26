# pages/planning.py - Strategic Planning and Scenario Modeling Module

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import datetime

# Import theme manager
try:
    from utils.theme_manager import apply_village_theme, create_village_header, get_village_colors
except ImportError:
    st.error("Theme manager not available")

def show():
    """Display the Planning page with strategic planning tools"""
    
    # Apply Village theme
    apply_village_theme()
    
    # Display header
    create_village_header(
        "Strategic Traffic Planning",
        "Long-term planning tools and scenario modeling for transportation professionals"
    )
    
    # Planning modules
    planning_module = st.selectbox(
        "Select Planning Module:",
        ["🎯 Traffic Impact Analysis", "📈 Scenario Modeling", "💰 Cost-Benefit Analysis", 
         "🚧 Infrastructure Planning", "📊 Performance Monitoring"]
    )
    
    if planning_module == "🎯 Traffic Impact Analysis":
        show_impact_analysis()
    elif planning_module == "📈 Scenario Modeling":
        show_scenario_modeling()
    elif planning_module == "💰 Cost-Benefit Analysis":
        show_cost_benefit_analysis()
    elif planning_module == "🚧 Infrastructure Planning":
        show_infrastructure_planning()
    elif planning_module == "📊 Performance Monitoring":
        show_performance_monitoring()

def show_impact_analysis():
    """Traffic impact analysis tools"""
    
    st.subheader("🎯 Traffic Impact Analysis")
    
    # Impact scenarios
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 🚧 Proposed Infrastructure Changes")
        
        # Infrastructure input form
        with st.form("infrastructure_form"):
            project_name = st.text_input("Project Name", value="Route 95 Lane Addition")
            project_type = st.selectbox("Project Type", 
                ["Lane Addition", "Traffic Signal", "Roundabout", "Bridge Repair", "Road Closure"])
            
            location = st.text_input("Location", value="Providence")
            estimated_cost = st.number_input("Estimated Cost ($)", min_value=0, value=500000, step=10000)
            timeline = st.slider("Timeline (months)", min_value=1, max_value=60, value=12)
            
            submitted = st.form_submit_button("🔍 Analyze Impact")
        
        if submitted:
            # Mock analysis results
            st.success(f"✅ Impact analysis completed for {project_name}")
            
            # Traffic flow prediction
            st.markdown("### 📊 Predicted Traffic Flow Changes")
            
            # Generate mock data
            months = list(range(1, timeline + 1))
            baseline_flow = [100] * len(months)
            predicted_flow = [100 + (i * 2) - np.random.normal(0, 5) for i in months]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=months, y=baseline_flow, mode='lines', name='Baseline', line=dict(dash='dash')))
            fig.add_trace(go.Scatter(x=months, y=predicted_flow, mode='lines', name='Predicted'))
            
            fig.update_layout(
                title="Traffic Flow Index Over Time",
                xaxis_title="Months",
                yaxis_title="Traffic Flow Index",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Impact metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Traffic Improvement", "+15%", delta="5%")
            with col2:
                st.metric("Travel Time Reduction", "8 min", delta="-3 min")
            with col3:
                st.metric("Incident Reduction", "25%", delta="10%")
    
    with col2:
        st.markdown("### 📋 Analysis Parameters")
        
        st.info("""
        **Current Settings:**
        - Analysis Period: 12 months
        - Traffic Model: SUMO
        - Weather Impact: Included
        - Event Calendar: Integrated
        """)
        
        st.markdown("### 🎯 Key Metrics")
        st.metric("Baseline Traffic", "2,450 vehicles/hour")
        st.metric("Peak Congestion", "Level C")
        st.metric("Average Delay", "12.3 minutes")

def show_scenario_modeling():
    """Scenario modeling and what-if analysis"""
    
    st.subheader("📈 Scenario Modeling")
    
    st.markdown("### 🔮 What-If Analysis")
    
    # Scenario builder
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Multiple scenarios comparison
        scenarios = st.multiselect(
            "Select Scenarios to Compare:",
            ["Baseline", "Add Express Lane", "Implement Congestion Pricing", 
             "New Transit Line", "Work from Home 30%", "Electric Vehicle 50%"],
            default=["Baseline", "Add Express Lane"]
        )
        
        if len(scenarios) >= 2:
            # Generate mock comparison data
            years = list(range(2025, 2035))
            
            fig = go.Figure()
            colors = ['#1976d2', '#f44336', '#ff9800', '#4caf50', '#9c27b0', '#00bcd4']
            
            for i, scenario in enumerate(scenarios):
                # Mock traffic volume projection
                base_volume = 100
                growth_rate = np.random.uniform(0.02, 0.08)  # 2-8% annual growth
                volumes = [base_volume * (1 + growth_rate) ** (year - 2025) for year in years]
                
                # Add scenario-specific adjustments
                if "Express Lane" in scenario:
                    volumes = [v * 1.15 for v in volumes]  # 15% improvement
                elif "Congestion Pricing" in scenario:
                    volumes = [v * 0.9 for v in volumes]   # 10% reduction
                elif "Transit Line" in scenario:
                    volumes = [v * 0.85 for v in volumes]  # 15% reduction
                elif "Work from Home" in scenario:
                    volumes = [v * 0.7 for v in volumes]   # 30% reduction
                elif "Electric Vehicle" in scenario:
                    volumes = [v * 1.05 for v in volumes]  # 5% efficiency gain
                
                fig.add_trace(go.Scatter(
                    x=years, y=volumes, mode='lines+markers',
                    name=scenario, line=dict(color=colors[i % len(colors)], width=3)
                ))
            
            fig.update_layout(
                title="Traffic Volume Projections by Scenario",
                xaxis_title="Year",
                yaxis_title="Traffic Volume Index",
                height=500,
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Scenario comparison table
            st.markdown("### 📊 Scenario Comparison (2030 Projections)")
            
            comparison_data = []
            for scenario in scenarios:
                # Mock metrics
                traffic_volume = np.random.randint(90, 130)
                co2_emissions = np.random.randint(80, 120)
                travel_time = np.random.randint(85, 115)
                cost = np.random.randint(50, 200) * 1000000
                
                comparison_data.append({
                    'Scenario': scenario,
                    'Traffic Volume (% of baseline)': f"{traffic_volume}%",
                    'CO2 Emissions (% of baseline)': f"{co2_emissions}%",
                    'Travel Time (% of baseline)': f"{travel_time}%",
                    'Investment Cost': f"${cost:,}"
                })
            
            comparison_df = pd.DataFrame(comparison_data)
            st.dataframe(comparison_df, use_container_width=True, hide_index=True)
    
    with col2:
        st.markdown("### ⚙️ Model Parameters")
        
        population_growth = st.slider("Population Growth Rate (%/year)", 0.0, 5.0, 1.2, 0.1)
        economic_growth = st.slider("Economic Growth Rate (%/year)", 0.0, 8.0, 3.5, 0.1)
        fuel_price = st.slider("Fuel Price Change (%/year)", -10.0, 15.0, 2.0, 0.5)
        
        st.markdown("### 🎯 Key Assumptions")
        st.info("""
        - Base year: 2025
        - Analysis period: 10 years
        - Discount rate: 3%
        - Vehicle occupancy: 1.2 persons
        """)

def show_cost_benefit_analysis():
    """Cost-benefit analysis tools"""
    
    st.subheader("💰 Cost-Benefit Analysis")
    
    st.markdown("### 📊 Project Economics")
    
    # Project input
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 💸 Costs")
        
        capital_cost = st.number_input("Capital Cost ($M)", min_value=0.0, value=50.0, step=1.0)
        annual_maintenance = st.number_input("Annual Maintenance ($M)", min_value=0.0, value=2.0, step=0.1)
        project_life = st.slider("Project Life (years)", min_value=10, max_value=50, value=25)
        discount_rate = st.slider("Discount Rate (%)", min_value=1.0, max_value=10.0, value=3.0, step=0.1)
    
    with col2:
        st.markdown("#### 📈 Benefits")
        
        time_savings = st.number_input("Annual Time Savings ($M)", min_value=0.0, value=15.0, step=1.0)
        accident_reduction = st.number_input("Annual Accident Cost Savings ($M)", min_value=0.0, value=5.0, step=0.5)
        fuel_savings = st.number_input("Annual Fuel Savings ($M)", min_value=0.0, value=3.0, step=0.5)
        emissions_reduction = st.number_input("Annual Emissions Benefit ($M)", min_value=0.0, value=2.0, step=0.5)
    
    # Calculate NPV and BCR
    if st.button("💰 Calculate Cost-Benefit Analysis"):
        
        # NPV calculation
        annual_benefits = time_savings + accident_reduction + fuel_savings + emissions_reduction
        
        years = list(range(1, project_life + 1))
        discount_factors = [(1 / (1 + discount_rate/100)**year) for year in years]
        
        # Present value of benefits
        pv_benefits = sum([annual_benefits * factor for factor in discount_factors])
        
        # Present value of costs
        pv_maintenance = sum([annual_maintenance * factor for factor in discount_factors])
        total_costs = capital_cost + pv_maintenance
        
        # Metrics
        npv = pv_benefits - total_costs
        bcr = pv_benefits / total_costs if total_costs > 0 else 0
        
        # Display results
        st.markdown("### 📊 Analysis Results")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Net Present Value", f"${npv:.1f}M")
        with col2:
            st.metric("Benefit-Cost Ratio", f"{bcr:.2f}")
        with col3:
            recommendation = "Recommended" if bcr > 1.0 else "Not Recommended"
            st.metric("Recommendation", recommendation)
        with col4:
            payback_period = capital_cost / annual_benefits if annual_benefits > 0 else float('inf')
            st.metric("Payback Period", f"{payback_period:.1f} years")
        
        # Cash flow chart
        cash_flows = [-capital_cost] + [annual_benefits - annual_maintenance] * project_life
        cumulative_cash_flow = np.cumsum(cash_flows)
        
        fig_cash_flow = go.Figure()
        fig_cash_flow.add_trace(go.Scatter(
            x=list(range(0, project_life + 1)),
            y=cumulative_cash_flow,
            mode='lines+markers',
            name='Cumulative Cash Flow',
            line=dict(color='#1976d2', width=3)
        ))
        fig_cash_flow.add_hline(y=0, line_dash="dash", line_color="red")
        
        fig_cash_flow.update_layout(
            title="Cumulative Cash Flow Over Project Life",
            xaxis_title="Year",
            yaxis_title="Cumulative Cash Flow ($M)",
            height=400
        )
        st.plotly_chart(fig_cash_flow, use_container_width=True)

def show_infrastructure_planning():
    """Infrastructure planning tools"""
    
    st.subheader("🚧 Infrastructure Planning")
    
    st.markdown("### 🗺️ Infrastructure Asset Management")
    
    # Mock infrastructure inventory
    infrastructure_data = {
        'Asset Type': ['Bridges', 'Traffic Signals', 'Road Segments', 'Parking Facilities', 'Transit Stops'],
        'Total Count': [45, 234, 1250, 78, 156],
        'Good Condition (%)': [65, 78, 72, 82, 69],
        'Fair Condition (%)': [25, 18, 22, 15, 25],
        'Poor Condition (%)': [10, 4, 6, 3, 6],
        'Avg Age (years)': [32, 8, 15, 12, 7],
        'Replacement Cost ($M)': [125.5, 23.4, 450.2, 34.7, 12.8]
    }
    
    infra_df = pd.DataFrame(infrastructure_data)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Infrastructure condition chart
        fig_condition = go.Figure()
        
        fig_condition.add_trace(go.Bar(
            name='Good', x=infra_df['Asset Type'], y=infra_df['Good Condition (%)'],
            marker_color='#4caf50'
        ))
        fig_condition.add_trace(go.Bar(
            name='Fair', x=infra_df['Asset Type'], y=infra_df['Fair Condition (%)'],
            marker_color='#ff9800'
        ))
        fig_condition.add_trace(go.Bar(
            name='Poor', x=infra_df['Asset Type'], y=infra_df['Poor Condition (%)'],
            marker_color='#f44336'
        ))
        
        fig_condition.update_layout(
            title="Infrastructure Condition by Asset Type",
            xaxis_title="Asset Type",
            yaxis_title="Percentage",
            barmode='stack',
            height=400
        )
        st.plotly_chart(fig_condition, use_container_width=True)
    
    with col2:
        st.markdown("### 🎯 Priority Metrics")
        st.metric("Assets in Poor Condition", "87", delta="-12")
        st.metric("Annual Replacement Need", "$45.2M")
        st.metric("Maintenance Backlog", "$23.8M")
        
        st.markdown("### ⚠️ Critical Assets")
        st.error("🚨 5 bridges need immediate attention")
        st.warning("⚠️ 23 traffic signals due for upgrade")
    
    # Infrastructure investment planning
    st.markdown("### 💰 Investment Planning")
    
    years = list(range(2025, 2030))
    budget_scenarios = {
        'Conservative': [40, 42, 44, 46, 48],
        'Moderate': [50, 55, 58, 62, 65],
        'Aggressive': [65, 70, 75, 80, 85]
    }
    
    fig_budget = go.Figure()
    colors = ['#1976d2', '#ff9800', '#4caf50']
    
    for i, (scenario, values) in enumerate(budget_scenarios.items()):
        fig_budget.add_trace(go.Scatter(
            x=years, y=values, mode='lines+markers',
            name=f'{scenario} Budget', line=dict(color=colors[i], width=3)
        ))
    
    fig_budget.update_layout(
        title="Infrastructure Investment Scenarios",
        xaxis_title="Year",
        yaxis_title="Annual Budget ($M)",
        height=400
    )
    st.plotly_chart(fig_budget, use_container_width=True)

def show_performance_monitoring():
    """Performance monitoring dashboard"""
    
    st.subheader("📊 Performance Monitoring")
    
    st.markdown("### 🎯 Key Performance Indicators")
    
    # KPI metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Average Travel Speed",
            "28.5 mph",
            delta="1.2 mph",
            delta_color="normal"
        )
    
    with col2:
        st.metric(
            "Incident Response Time",
            "8.3 min",
            delta="-0.7 min",
            delta_color="inverse"
        )
    
    with col3:
        st.metric(
            "Traffic Signal Uptime",
            "99.2%",
            delta="0.3%",
            delta_color="normal"
        )
    
    with col4:
        st.metric(
            "Public Satisfaction",
            "7.2/10",
            delta="0.4",
            delta_color="normal"
        )
    
    # Performance trends
    st.markdown("### 📈 Performance Trends")
    
    # Mock time series data
    dates = pd.date_range('2024-01-01', '2024-12-31', freq='D')
    np.random.seed(42)
    
    travel_speed = 28 + np.random.normal(0, 2, len(dates)) + \
                   2 * np.sin(2 * np.pi * np.arange(len(dates)) / 365)  # Seasonal pattern
    
    response_time = 8.5 + np.random.normal(0, 1, len(dates)) - \
                   0.5 * np.sin(2 * np.pi * np.arange(len(dates)) / 365)  # Inverse seasonal
    
    fig_performance = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Average Travel Speed (mph)', 'Incident Response Time (min)'),
        vertical_spacing=0.1
    )
    
    fig_performance.add_trace(
        go.Scatter(x=dates, y=travel_speed, mode='lines', name='Travel Speed',
                  line=dict(color='#1976d2')), row=1, col=1
    )
    
    fig_performance.add_trace(
        go.Scatter(x=dates, y=response_time, mode='lines', name='Response Time',
                  line=dict(color='#f44336')), row=2, col=1
    )
    
    fig_performance.update_layout(height=600, showlegend=False)
    st.plotly_chart(fig_performance, use_container_width=True)
    
    # Performance targets
    st.markdown("### 🎯 Performance Targets vs Actual")
    
    targets_data = {
        'Metric': ['Travel Speed', 'Response Time', 'Signal Uptime', 'Satisfaction'],
        'Target': ['30 mph', '7 min', '99.5%', '8.0/10'],
        'Actual': ['28.5 mph', '8.3 min', '99.2%', '7.2/10'],
        'Status': ['Below Target', 'Below Target', 'Below Target', 'Below Target'],
        'Trend': ['↗️ Improving', '↘️ Declining', '→ Stable', '↗️ Improving']
    }
    
    targets_df = pd.DataFrame(targets_data)
    st.dataframe(targets_df, use_container_width=True, hide_index=True)

if __name__ == "__main__":
    show()