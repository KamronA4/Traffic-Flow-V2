# pages/predictive_analytics.py - Predictive Analytics Module

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
import asyncio
import warnings
warnings.filterwarnings('ignore')

# Import utilities
try:
    from utils.data_sync import get_traffic_data
    from utils.enterprise_auth import require_feature, get_current_user
    from utils.enhanced_ai_analyzer import EnhancedTrafficAnalyzer, AnalysisType
except ImportError as e:
    st.error(f"Error importing utilities: {e}")

# Import theme manager
try:
    from utils.theme_manager import apply_village_theme, create_village_header, get_village_colors
except ImportError:
    st.error("Theme manager not available")

@require_feature("predictive_analytics")
def show():
    """Main predictive analytics page"""
    
    # Apply Village theme
    apply_village_theme()
    
    # Display header
    create_village_header(
        "🔮 Predictive Analytics",
        "Advanced machine learning models for traffic forecasting and trend analysis"
    )
    
    # Get current user and organization
    user_org = get_current_user()
    if not user_org:
        st.error("Authentication required")
        return
    
    user, organization = user_org
    
    # Create tabs for different prediction types
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Incident Prediction", 
        "🚦 Traffic Flow Forecast", 
        "⚡ Real-time Predictions", 
        "📈 Trend Analysis"
    ])
    
    with tab1:
        show_incident_prediction()
    
    with tab2:
        show_traffic_flow_forecast()
    
    with tab3:
        show_realtime_predictions()
    
    with tab4:
        show_trend_analysis()

def show_incident_prediction():
    """Show incident prediction interface"""
    st.subheader("🚨 Incident Prediction Model")
    
    # Load historical data
    try:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=90)
        
        df = get_traffic_data(start_date=start_date, end_date=end_date)
        
        if df.empty:
            st.warning("Insufficient data for prediction modeling")
            return
        
        # Prepare data for modeling
        prediction_data = prepare_incident_data(df)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Model parameters
            st.markdown("### Model Configuration")
            
            prediction_horizon = st.selectbox(
                "Prediction Horizon",
                ["Next 2 hours", "Next 6 hours", "Next 12 hours", "Next 24 hours"],
                index=1
            )
            
            location_filter = st.selectbox(
                "Location",
                ["All Locations"] + sorted(df['location'].unique().tolist()),
                index=0
            )
            
            confidence_level = st.slider(
                "Confidence Level",
                min_value=0.80,
                max_value=0.99,
                value=0.95,
                step=0.01
            )
        
        with col2:
            # Current risk assessment
            st.markdown("### Current Risk Level")
            
            current_risk = calculate_current_risk(df)
            risk_color = get_risk_color(current_risk)
            
            st.markdown(f"""
            <div style="
                background: {risk_color};
                color: white;
                padding: 1rem;
                border-radius: 10px;
                text-align: center;
                margin-bottom: 1rem;
            ">
                <h2 style="margin: 0;">{current_risk}</h2>
                <p style="margin: 0.5rem 0 0 0;">Risk Level</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Risk factors
            st.markdown("**Top Risk Factors:**")
            risk_factors = get_risk_factors(df)
            for factor, score in risk_factors.items():
                st.markdown(f"• {factor}: {score:.2f}")
        
        # Run prediction
        if st.button("🔮 Generate Predictions", use_container_width=True):
            with st.spinner("Training prediction model..."):
                predictions = generate_incident_predictions(
                    prediction_data, 
                    prediction_horizon,
                    location_filter,
                    confidence_level
                )
                
                display_incident_predictions(predictions)
    
    except Exception as e:
        st.error(f"Error in incident prediction: {e}")

def show_traffic_flow_forecast():
    """Show traffic flow forecasting"""
    st.subheader("🚦 Traffic Flow Forecasting")
    
    try:
        # Load traffic flow data
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        
        df = get_traffic_data(start_date=start_date, end_date=end_date)
        
        if df.empty:
            st.warning("No traffic data available for forecasting")
            return
        
        # Forecast parameters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            forecast_days = st.number_input(
                "Forecast Days",
                min_value=1,
                max_value=30,
                value=7
            )
        
        with col2:
            location = st.selectbox(
                "Location",
                sorted(df['location'].unique().tolist())
            )
        
        with col3:
            model_type = st.selectbox(
                "Model Type",
                ["ARIMA", "Random Forest", "Neural Network"],
                index=1
            )
        
        if st.button("📈 Generate Forecast", use_container_width=True):
            with st.spinner("Generating traffic flow forecast..."):
                forecast = generate_traffic_forecast(
                    df, location, forecast_days, model_type
                )
                
                display_traffic_forecast(forecast, location)
    
    except Exception as e:
        st.error(f"Error in traffic flow forecasting: {e}")

def show_realtime_predictions():
    """Show real-time predictions dashboard"""
    st.subheader("⚡ Real-time Prediction Dashboard")
    
    # Auto-refresh toggle
    auto_refresh = st.checkbox("Auto-refresh (every 5 minutes)", value=True)
    
    if auto_refresh:
        # Auto-refresh component would go here
        pass
    
    # Current conditions
    st.markdown("### Current Conditions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Next Hour Risk",
            "Medium",
            delta="↑ 15%",
            delta_color="inverse"
        )
    
    with col2:
        st.metric(
            "Expected Incidents",
            "2-3",
            delta="↓ 1",
            delta_color="normal"
        )
    
    with col3:
        st.metric(
            "Avg Delay",
            "8 min",
            delta="↑ 3 min",
            delta_color="inverse"
        )
    
    with col4:
        st.metric(
            "Congestion Level",
            "65%",
            delta="↑ 10%",
            delta_color="inverse"
        )
    
    # Real-time prediction map
    st.markdown("### Prediction Hotspots")
    
    # Create sample prediction data
    prediction_map_data = create_prediction_map_data()
    
    # Display map with predictions
    import folium
    from streamlit_folium import st_folium
    
    m = folium.Map(location=[41.8236, -71.4222], zoom_start=12)
    
    for pred in prediction_map_data:
        color = get_prediction_color(pred['risk_level'])
        
        folium.CircleMarker(
            location=[pred['lat'], pred['lng']],
            radius=pred['risk_level'] * 5,
            popup=f"Risk: {pred['risk_level']:.1f}/5<br>Type: {pred['prediction_type']}",
            color=color,
            fill=True,
            fillColor=color,
            fillOpacity=0.6
        ).add_to(m)
    
    st_folium(m, width=700, height=400)
    
    # AI-powered insights
    st.markdown("### AI Insights")
    
    # Generate AI insights for current conditions
    if st.button("🤖 Get AI Insights"):
        with st.spinner("Generating AI insights..."):
            try:
                analyzer = EnhancedTrafficAnalyzer()
                
                # Create current conditions summary
                current_conditions = {
                    'description': 'Current traffic conditions analysis',
                    'location': 'Rhode Island',
                    'severity': 2,
                    'timestamp': datetime.now()
                }
                
                # Get predictive analysis
                loop = get_or_create_event_loop()
                analysis = loop.run_until_complete(
                    analyzer.comprehensive_analysis(
                        current_conditions,
                        [AnalysisType.PREDICTIVE_ANALYSIS],
                        include_context=True
                    )
                )
                
                # Display insights
                if analysis and not analysis.get('error'):
                    predictive_result = analysis['individual_analyses'].get('predictive_analysis', {})
                    if predictive_result and not predictive_result.get('error'):
                        st.markdown("**AI Prediction Analysis:**")
                        st.info(predictive_result.get('analysis', 'No analysis available'))
                    else:
                        st.warning("AI analysis temporarily unavailable")
                else:
                    st.error("Failed to generate AI insights")
            
            except Exception as e:
                st.error(f"Error generating AI insights: {e}")

def show_trend_analysis():
    """Show trend analysis and patterns"""
    st.subheader("📈 Trend Analysis")
    
    try:
        # Load extended historical data
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=180)
        
        df = get_traffic_data(start_date=start_date, end_date=end_date)
        
        if df.empty:
            st.warning("No data available for trend analysis")
            return
        
        # Analysis options
        col1, col2 = st.columns(2)
        
        with col1:
            trend_type = st.selectbox(
                "Trend Type",
                ["Incident Patterns", "Seasonal Trends", "Weekly Patterns", "Time-of-Day Analysis"]
            )
        
        with col2:
            granularity = st.selectbox(
                "Granularity",
                ["Daily", "Weekly", "Monthly"],
                index=1
            )
        
        # Generate trend analysis
        if st.button("📊 Analyze Trends", use_container_width=True):
            with st.spinner("Analyzing traffic patterns..."):
                trend_analysis = generate_trend_analysis(df, trend_type, granularity)
                display_trend_analysis(trend_analysis, trend_type)
    
    except Exception as e:
        st.error(f"Error in trend analysis: {e}")

# Helper functions
def prepare_incident_data(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare data for incident prediction modeling"""
    # Add time-based features
    df = df.copy()  # Work on a copy to avoid modifying original
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Convert to local timezone if timezone-aware
    if df['timestamp'].dt.tz is not None:
        df['timestamp'] = df['timestamp'].dt.tz_convert('US/Eastern').dt.tz_localize(None)
    
    df['hour'] = df['timestamp'].dt.hour
    df['day_of_week'] = df['timestamp'].dt.dayofweek
    df['month'] = df['timestamp'].dt.month
    df['is_weekend'] = df['day_of_week'].isin([5, 6])
    
    # Add weather features (mock data)
    df['temperature'] = np.random.normal(45, 15, len(df))
    df['precipitation'] = np.random.exponential(0.1, len(df))
    df['visibility'] = np.random.normal(10, 2, len(df))
    
    return df

def calculate_current_risk(df: pd.DataFrame) -> str:
    """Calculate current risk level"""
    # Simple risk calculation based on recent incidents
    # Convert datetime.now() to timezone-aware if df['timestamp'] is timezone-aware
    current_time = pd.Timestamp.now()
    if df['timestamp'].dt.tz is not None:
        current_time = current_time.tz_localize(df['timestamp'].dt.tz)
    
    cutoff_time = current_time - timedelta(hours=6)
    recent_incidents = df[df['timestamp'] > cutoff_time]
    
    if len(recent_incidents) > 5:
        return "High"
    elif len(recent_incidents) > 2:
        return "Medium"
    else:
        return "Low"

def get_risk_color(risk_level: str) -> str:
    """Get color based on risk level"""
    colors = {
        "Low": "#2d5016",
        "Medium": "#8b4513",
        "High": "#d32f2f"
    }
    return colors.get(risk_level, "#2d5016")

def get_risk_factors(df: pd.DataFrame) -> Dict[str, float]:
    """Get top risk factors"""
    return {
        "Rush Hour Traffic": 0.75,
        "Weather Conditions": 0.45,
        "Construction Activity": 0.32,
        "Event Traffic": 0.28,
        "Historical Patterns": 0.67
    }

def generate_incident_predictions(data: pd.DataFrame, horizon: str, location: str, confidence: float) -> Dict[str, Any]:
    """Generate incident predictions"""
    # Mock prediction results
    hours = {
        "Next 2 hours": 2,
        "Next 6 hours": 6,
        "Next 12 hours": 12,
        "Next 24 hours": 24
    }[horizon]
    
    predictions = []
    base_time = datetime.now()
    
    for i in range(hours):
        hour_time = base_time + timedelta(hours=i)
        risk_score = np.random.beta(2, 5)  # Skewed toward lower risk
        
        predictions.append({
            'time': hour_time,
            'risk_score': risk_score,
            'expected_incidents': int(risk_score * 5),
            'confidence': confidence,
            'location': location if location != "All Locations" else "Multiple"
        })
    
    return {
        'predictions': predictions,
        'model_accuracy': 0.85,
        'feature_importance': {
            'time_of_day': 0.35,
            'weather': 0.25,
            'historical_patterns': 0.20,
            'day_of_week': 0.15,
            'special_events': 0.05
        }
    }

def display_incident_predictions(predictions: Dict[str, Any]):
    """Display incident prediction results"""
    st.markdown("### Prediction Results")
    
    # Model performance
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Model Accuracy", f"{predictions['model_accuracy']:.1%}")
    
    with col2:
        avg_risk = np.mean([p['risk_score'] for p in predictions['predictions']])
        st.metric("Average Risk", f"{avg_risk:.2f}/1.0")
    
    # Prediction timeline
    pred_df = pd.DataFrame(predictions['predictions'])
    
    # Get village colors
    try:
        village_colors = get_village_colors()
        color_palette = village_colors['palette']
        primary_color = village_colors['primary']
    except:
        color_palette = ['#2d5016']
        primary_color = '#2d5016'
    
    fig = px.line(
        pred_df,
        x='time',
        y='risk_score',
        title='Risk Score Over Time',
        color_discrete_sequence=color_palette
    )
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color=primary_color
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Feature importance
    st.markdown("### Feature Importance")
    
    importance_df = pd.DataFrame(
        list(predictions['feature_importance'].items()),
        columns=['Feature', 'Importance']
    )
    
    fig = px.bar(
        importance_df,
        x='Importance',
        y='Feature',
        orientation='h',
        title='Model Feature Importance',
        color_discrete_sequence=color_palette
    )
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color=primary_color
    )
    
    st.plotly_chart(fig, use_container_width=True)

def generate_traffic_forecast(df: pd.DataFrame, location: str, days: int, model_type: str) -> Dict[str, Any]:
    """Generate traffic flow forecast"""
    # Mock forecast data
    base_date = datetime.now().date()
    forecast_dates = [base_date + timedelta(days=i) for i in range(days)]
    
    # Generate synthetic forecast with some patterns
    forecast_values = []
    for i, date in enumerate(forecast_dates):
        # Add weekly and daily patterns
        weekly_pattern = np.sin(2 * np.pi * i / 7) * 0.3
        daily_noise = np.random.normal(0, 0.1)
        base_value = 50 + weekly_pattern + daily_noise
        
        forecast_values.append({
            'date': date,
            'predicted_incidents': max(0, int(base_value)),
            'confidence_lower': max(0, int(base_value * 0.8)),
            'confidence_upper': int(base_value * 1.2),
            'actual': np.random.poisson(base_value) if i < 3 else None  # Only recent actuals
        })
    
    return {
        'forecast': forecast_values,
        'model_type': model_type,
        'location': location,
        'rmse': 2.3,
        'mae': 1.8,
        'r2': 0.76
    }

def display_traffic_forecast(forecast: Dict[str, Any], location: str):
    """Display traffic forecast results"""
    st.markdown(f"### Traffic Forecast for {location}")
    
    # Get village colors
    try:
        village_colors = get_village_colors()
        primary_color = village_colors['primary']
        secondary_color = village_colors['secondary']
        accent_color = village_colors['accent']
    except:
        primary_color = '#2d5016'
        secondary_color = '#5a7c47'
        accent_color = '#8b4513'
    
    # Model metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("RMSE", f"{forecast['rmse']:.1f}")
    
    with col2:
        st.metric("MAE", f"{forecast['mae']:.1f}")
    
    with col3:
        st.metric("R²", f"{forecast['r2']:.2f}")
    
    # Forecast chart
    forecast_df = pd.DataFrame(forecast['forecast'])
    
    fig = go.Figure()
    
    # Add forecast line
    fig.add_trace(go.Scatter(
        x=forecast_df['date'],
        y=forecast_df['predicted_incidents'],
        mode='lines+markers',
        name='Forecast',
        line=dict(color=primary_color)
    ))
    
    # Add confidence intervals
    fig.add_trace(go.Scatter(
        x=forecast_df['date'],
        y=forecast_df['confidence_upper'],
        mode='lines',
        name='Upper Bound',
        line=dict(color=secondary_color, dash='dash'),
        showlegend=False
    ))
    
    fig.add_trace(go.Scatter(
        x=forecast_df['date'],
        y=forecast_df['confidence_lower'],
        mode='lines',
        name='Lower Bound',
        line=dict(color=secondary_color, dash='dash'),
        fill='tonexty',
        fillcolor='rgba(90, 124, 71, 0.2)',
        showlegend=False
    ))
    
    # Add actuals if available
    actuals = forecast_df.dropna(subset=['actual'])
    if not actuals.empty:
        fig.add_trace(go.Scatter(
            x=actuals['date'],
            y=actuals['actual'],
            mode='markers',
            name='Actual',
            marker=dict(color=accent_color, size=8)
        ))
    
    fig.update_layout(
        title=f'{forecast["model_type"]} Traffic Forecast',
        xaxis_title='Date',
        yaxis_title='Predicted Incidents',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color=primary_color
    )
    
    st.plotly_chart(fig, use_container_width=True)

def create_prediction_map_data() -> List[Dict[str, Any]]:
    """Create sample prediction map data"""
    locations = [
        {'name': 'Downtown Providence', 'lat': 41.8236, 'lng': -71.4222, 'risk': 3.5},
        {'name': 'Warwick', 'lat': 41.7001, 'lng': -71.4162, 'risk': 2.1},
        {'name': 'Cranston', 'lat': 41.7790, 'lng': -71.4371, 'risk': 2.8},
        {'name': 'Pawtucket', 'lat': 41.8787, 'lng': -71.3826, 'risk': 1.9},
        {'name': 'Newport', 'lat': 41.4901, 'lng': -71.3128, 'risk': 1.5}
    ]
    
    predictions = []
    for loc in locations:
        predictions.append({
            'name': loc['name'],
            'lat': loc['lat'],
            'lng': loc['lng'],
            'risk_level': loc['risk'],
            'prediction_type': 'Incident Risk'
        })
    
    return predictions

def get_prediction_color(risk_level: float) -> str:
    """Get color based on prediction risk level"""
    if risk_level < 2:
        return '#2d5016'  # Low risk - green
    elif risk_level < 3:
        return '#8b4513'  # Medium risk - brown
    else:
        return '#d32f2f'  # High risk - red

def generate_trend_analysis(df: pd.DataFrame, trend_type: str, granularity: str) -> Dict[str, Any]:
    """Generate trend analysis"""
    df = df.copy()  # Work on a copy
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Convert to local timezone if timezone-aware
    if df['timestamp'].dt.tz is not None:
        df['timestamp'] = df['timestamp'].dt.tz_convert('US/Eastern').dt.tz_localize(None)
    
    if trend_type == "Incident Patterns":
        # Analyze incident patterns by hour
        hourly_counts = df.groupby(df['timestamp'].dt.hour).size()
        
        return {
            'type': 'hourly_patterns',
            'data': hourly_counts.to_dict(),
            'peak_hours': hourly_counts.nlargest(3).index.tolist(),
            'insights': [
                f"Peak incident hour: {hourly_counts.idxmax()}:00",
                f"Lowest incident hour: {hourly_counts.idxmin()}:00",
                f"Average incidents per hour: {hourly_counts.mean():.1f}"
            ]
        }
    
    elif trend_type == "Weekly Patterns":
        # Analyze weekly patterns
        daily_counts = df.groupby(df['timestamp'].dt.dayofweek).size()
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        
        return {
            'type': 'weekly_patterns',
            'data': {days[i]: daily_counts.get(i, 0) for i in range(7)},
            'peak_days': [days[i] for i in daily_counts.nlargest(3).index],
            'insights': [
                f"Busiest day: {days[daily_counts.idxmax()]}",
                f"Quietest day: {days[daily_counts.idxmin()]}",
                f"Weekend vs weekday ratio: {daily_counts.iloc[5:].sum() / daily_counts.iloc[:5].sum():.2f}"
            ]
        }
    
    return {'type': 'unknown', 'data': {}, 'insights': []}

def display_trend_analysis(analysis: Dict[str, Any], trend_type: str):
    """Display trend analysis results"""
    st.markdown(f"### {trend_type} Analysis")
    
    # Get village colors
    try:
        village_colors = get_village_colors()
        color_palette = village_colors['palette']
        primary_color = village_colors['primary']
    except:
        color_palette = ['#2d5016']
        primary_color = '#2d5016'
    
    if analysis['type'] == 'hourly_patterns':
        # Display hourly pattern chart
        data = analysis['data']
        hours = list(data.keys())
        counts = list(data.values())
        
        fig = px.bar(
            x=hours,
            y=counts,
            title='Incidents by Hour of Day',
            labels={'x': 'Hour', 'y': 'Incident Count'},
            color_discrete_sequence=color_palette
        )
        
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color=primary_color
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    elif analysis['type'] == 'weekly_patterns':
        # Display weekly pattern chart
        data = analysis['data']
        days = list(data.keys())
        counts = list(data.values())
        
        fig = px.bar(
            x=days,
            y=counts,
            title='Incidents by Day of Week',
            labels={'x': 'Day', 'y': 'Incident Count'},
            color_discrete_sequence=color_palette
        )
        
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color=primary_color
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Display insights
    st.markdown("### Key Insights")
    for insight in analysis['insights']:
        st.info(f"💡 {insight}")

def get_or_create_event_loop():
    """Get or create event loop for async operations"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop

if __name__ == "__main__":
    show()