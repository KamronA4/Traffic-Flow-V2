#!/usr/bin/env python3
"""
Weather API integration for contextual traffic analysis
"""

import requests
import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import json

class WeatherAnalyzer:
    """Integrate weather data for traffic analysis"""
    
    def __init__(self):
        # Use OpenWeatherMap API (free tier: 1000 calls/day)
        self.api_key = st.secrets.get("OPENWEATHER_API_KEY", "demo_key")
        self.base_url = "https://api.openweathermap.org/data/2.5"
        
        # Rhode Island coordinates
        self.ri_coords = {
            'lat': 41.5801,
            'lon': -71.4774
        }
    
    @st.cache_data(ttl=1800)  # Cache for 30 minutes
    def get_current_weather(_self) -> Dict:
        """Get current weather conditions for Rhode Island"""
        
        if _self.api_key == "demo_key":
            return _self._get_mock_weather()
        
        try:
            url = f"{_self.base_url}/weather"
            params = {
                'lat': _self.ri_coords['lat'],
                'lon': _self.ri_coords['lon'],
                'appid': _self.api_key,
                'units': 'imperial'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return _self._process_weather_data(data)
            else:
                return _self._get_mock_weather()
                
        except Exception:
            return _self._get_mock_weather()
    
    def _process_weather_data(self, data: Dict) -> Dict:
        """Process weather API response"""
        
        return {
            'temperature': round(data['main']['temp']),
            'feels_like': round(data['main']['feels_like']),
            'humidity': data['main']['humidity'],
            'description': data['weather'][0]['description'].title(),
            'wind_speed': round(data['wind']['speed']),
            'visibility': data.get('visibility', 10000) / 1000,  # Convert to km
            'conditions': data['weather'][0]['main'],
            'icon': data['weather'][0]['icon'],
            'timestamp': datetime.now()
        }
    
    def _get_mock_weather(self) -> Dict:
        """Generate realistic mock weather for demo"""
        import random
        
        # Realistic Rhode Island weather patterns
        temp = random.randint(25, 75)
        conditions = random.choice([
            'Clear', 'Partly Cloudy', 'Cloudy', 'Rain', 'Snow'
        ])
        
        descriptions = {
            'Clear': 'Clear sky',
            'Partly Cloudy': 'Few clouds',
            'Cloudy': 'Overcast clouds',
            'Rain': 'Light rain',
            'Snow': 'Light snow'
        }
        
        return {
            'temperature': temp,
            'feels_like': temp + random.randint(-5, 5),
            'humidity': random.randint(40, 90),
            'description': descriptions[conditions],
            'wind_speed': random.randint(3, 15),
            'visibility': random.uniform(5.0, 10.0),
            'conditions': conditions,
            'icon': '01d',
            'timestamp': datetime.now()
        }
    
    def get_weather_impact_analysis(self, weather: Dict) -> Dict:
        """Analyze weather impact on traffic"""
        
        # Weather impact scoring
        impact_score = 0
        factors = []
        
        # Temperature impacts
        if weather['temperature'] < 32:
            impact_score += 3
            factors.append("Freezing temperatures increase accident risk")
        elif weather['temperature'] > 90:
            impact_score += 1
            factors.append("High temperatures may affect vehicle performance")
        
        # Precipitation impacts
        conditions = weather['conditions'].lower()
        if 'rain' in conditions:
            impact_score += 2
            factors.append("Rain reduces visibility and road traction")
        elif 'snow' in conditions:
            impact_score += 4
            factors.append("Snow creates hazardous driving conditions")
        
        # Visibility impacts
        if weather['visibility'] < 2:
            impact_score += 3
            factors.append("Poor visibility significantly increases risk")
        elif weather['visibility'] < 5:
            impact_score += 2
            factors.append("Reduced visibility affects driving conditions")
        
        # Wind impacts
        if weather['wind_speed'] > 25:
            impact_score += 2
            factors.append("High winds affect vehicle stability")
        
        # Impact level classification
        if impact_score >= 6:
            impact_level = "High"
            color = "red"
        elif impact_score >= 3:
            impact_level = "Moderate"
            color = "orange"
        else:
            impact_level = "Low"
            color = "green"
        
        return {
            'impact_score': impact_score,
            'impact_level': impact_level,
            'color': color,
            'factors': factors,
            'recommendations': self._get_weather_recommendations(impact_score, weather)
        }
    
    def _get_weather_recommendations(self, impact_score: int, weather: Dict) -> List[str]:
        """Get weather-based traffic management recommendations"""
        
        recommendations = []
        
        if impact_score >= 6:
            recommendations.extend([
                "Issue weather advisory to drivers",
                "Increase emergency service patrol frequency",
                "Consider temporary speed limit reductions",
                "Pre-position emergency vehicles at high-risk locations"
            ])
        elif impact_score >= 3:
            recommendations.extend([
                "Monitor traffic conditions closely",
                "Alert emergency services to potential delays",
                "Encourage alternative transportation methods"
            ])
        else:
            recommendations.append("Normal traffic monitoring sufficient")
        
        # Specific weather-based recommendations
        conditions = weather['conditions'].lower()
        if 'snow' in conditions or weather['temperature'] < 32:
            recommendations.extend([
                "Deploy salt trucks on major routes",
                "Monitor bridge and overpass conditions",
                "Issue frost/ice warnings to commuters"
            ])
        
        return recommendations

def display_weather_widget():
    """Display weather information in Streamlit sidebar"""
    
    analyzer = WeatherAnalyzer()
    weather = analyzer.get_current_weather()
    impact = analyzer.get_weather_impact_analysis(weather)
    
    with st.sidebar:
        st.markdown("### 🌤️ Weather Conditions")
        
        # Current conditions
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Temperature", f"{weather['temperature']}°F")
        with col2:
            st.metric("Wind", f"{weather['wind_speed']} mph")
        
        st.markdown(f"**{weather['description']}**")
        st.markdown(f"Humidity: {weather['humidity']}%")
        st.markdown(f"Visibility: {weather['visibility']:.1f} km")
        
        # Traffic impact
        st.markdown("#### Traffic Impact")
        
        if impact['impact_level'] == "High":
            st.error(f"🔴 {impact['impact_level']} Impact")
        elif impact['impact_level'] == "Moderate":
            st.warning(f"🟡 {impact['impact_level']} Impact")
        else:
            st.success(f"🟢 {impact['impact_level']} Impact")
        
        # Impact factors
        if impact['factors']:
            with st.expander("Impact Factors"):
                for factor in impact['factors']:
                    st.write(f"• {factor}")
        
        # Recommendations
        if len(impact['recommendations']) > 1:
            with st.expander("Recommendations"):
                for rec in impact['recommendations']:
                    st.write(f"• {rec}")

def get_weather_context_for_ai(incident_location: str = "Rhode Island") -> str:
    """Get weather context for AI analysis"""
    
    analyzer = WeatherAnalyzer()
    weather = analyzer.get_current_weather()
    impact = analyzer.get_weather_impact_analysis(weather)
    
    context = f"""
Current Weather Context for {incident_location}:
- Temperature: {weather['temperature']}°F (feels like {weather['feels_like']}°F)
- Conditions: {weather['description']}
- Visibility: {weather['visibility']:.1f} km
- Wind: {weather['wind_speed']} mph
- Traffic Impact Level: {impact['impact_level']}
- Weather Factors: {', '.join(impact['factors']) if impact['factors'] else 'None'}
"""
    
    return context

# Integration with existing AI analyzer
def enhance_incident_analysis_with_weather(incident_data: Dict) -> Dict:
    """Enhance incident analysis with weather context"""
    
    # Get weather context
    weather_context = get_weather_context_for_ai(
        incident_data.get('location', 'Rhode Island')
    )
    
    # Add weather context to incident data
    enhanced_data = incident_data.copy()
    enhanced_data['weather_context'] = weather_context
    
    return enhanced_data