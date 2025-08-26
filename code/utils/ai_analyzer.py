# utils/ai_analyzer.py - AI-powered traffic incident analysis via Perplexity integration

import streamlit as st
import requests
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import time

class TrafficAnalyzer:
    """AI-powered traffic incident analyzer with Perplexity integration"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with Perplexity API key"""
        self.api_key = api_key or st.secrets.get("PERPLEXITY_API_KEY", "")
        self.base_url = "https://api.perplexity.ai/chat/completions"

        '''
        notes: 
        'Authorization' = Bearer token for Perplexity API
        'Content-Type' = 'application/json' bc issa .json payload
        '''
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def analyze_incident(
        self, 
        incident: Dict[str, Any],
        include_articles: bool = True,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Analyze a traffic incident using Perplexity AI
        
        Args:
            incident: Dict containing incident details
            include_articles: Bool; whether to search for related articles
            max_retries: Number of retry attempts for API calls - limit usage
            
        Returns:
            Dict w analysis results, articles, and metadata
        """
        
        if not self.api_key:
            return self._get_mock_analysis(incident)
        
        try:
            # Generate analysis prompt
            analysis_prompt = self._create_analysis_prompt(incident)
            
            # Get Sonar analysis
            analysis_response = self._call_perplexity_api(
                analysis_prompt, 
                max_retries=max_retries
            )
            
            result = {
                'summary': analysis_response.get('content', 'Analysis unavailable'),
                'planning_insights': self._extract_planning_insights(analysis_response),
                'related_articles': [],
                'timestamp': datetime.now().isoformat(),
                'error': False
            }
            
            # Get related articles if requested
            if include_articles:
                articles_prompt = self._create_articles_prompt(incident)
                articles_response = self._call_perplexity_api(
                    articles_prompt,
                    max_retries=max_retries
                )
                
                result['related_articles'] = self._parse_articles(articles_response)
            
            return result
            
        except Exception as e:
            st.error(f"AI analysis failed: {str(e)}")
            return {
                'summary': f"Analysis error: {str(e)}",
                'planning_insights': "Unable to generate insights due to API error",
                'related_articles': [],
                'timestamp': datetime.now().isoformat(),
                'error': True
            }
    
    def _create_analysis_prompt(self, incident: Dict[str, Any]) -> str:
        """Create analysis prompt for Perplexity AI"""
        
        location = incident.get('location', 'Unknown location')
        description = incident.get('description', 'Traffic incident')
        severity = incident.get('severity', 'Unknown')
        timestamp = incident.get('timestamp', 'Unknown time')
        
        prompt = f"""
        As a municipal traffic planning expert, analyze this traffic incident for planning insights:
        
        **Incident Details:**
        - Location: {location}
        - Description: {description}
        - Severity: {severity}
        - Time: {timestamp}
        
        **Analysis Required:**
        1. Immediate traffic impact assessment
        2. Potential causes and contributing factors
        3. Municipal planning recommendations
        4. Resource allocation suggestions
        5. Prevention strategies for similar incidents
        
        Please provide a concise but comprehensive analysis focusing on actionable insights for transportation planners and municipal officials. Format your response in clear sections.
        """
        
        return prompt
    
    def _create_articles_prompt(self, incident: Dict[str, Any]) -> str:
        """Create prompt to find related news articles and information"""
        
        location = incident.get('location', 'Unknown location')
        description = incident.get('description', 'Traffic incident')
        
        prompt = f"""
        Find recent news articles, traffic reports, and relevant information about:
        - Traffic incidents in {location}
        - Similar {description} situations
        - Municipal traffic planning in Rhode Island
        - Transportation infrastructure updates for {location}
        
        Please provide 3-5 relevant, recent sources with titles and brief summaries. Focus on official municipal sources, local news, and traffic planning resources.
        """
        
        return prompt
    
    def _call_perplexity_api(
        self, 
        prompt: str, 
        model: str = "llama-3.1-sonar-small-128k-online",
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """Make API call to Perplexity with retry logic"""
        
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert municipal traffic planner and transportation analyst. Provide practical, actionable insights for traffic planning professionals."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            "max_tokens": 1000,
            "temperature": 0.3,
            "top_p": 0.9
        }
        
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.base_url,
                    json=payload,
                    headers=self.headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        'content': result['choices'][0]['message']['content'],
                        'usage': result.get('usage', {}),
                        'model': result.get('model', model)
                    }
                else:
                    raise requests.RequestException(f"API returned status {response.status_code}: {response.text}")
                    
            except requests.RequestException as e:
                if attempt == max_retries - 1:
                    raise e
                time.sleep(2 ** attempt)  # Exponential backoff
        
        raise Exception("Max retries exceeded")
    
    def _extract_planning_insights(self, response: Dict[str, Any]) -> str:
        """Extract planning-specific insights from AI response"""
        
        content = response.get('content', '')
        
        # Look for planning-related sections
        planning_keywords = [
            'planning', 'municipal', 'resource', 'infrastructure',
            'prevention', 'allocation', 'recommendation'
        ]
        
        lines = content.split('\n')
        planning_lines = []
        
        for line in lines:
            if any(keyword.lower() in line.lower() for keyword in planning_keywords):
                planning_lines.append(line.strip())
        
        if planning_lines:
            return '\n'.join(planning_lines)
        else:
            # Fallback: Just return last paragraph since it often contains recommendations
            paragraphs = content.split('\n\n')
            return paragraphs[-1] if paragraphs else "No specific planning insights available"
    
    def _parse_articles(self, response: Dict[str, Any]) -> List[Dict[str, str]]:
        """Parse articles from AI response"""
        
        content = response.get('content', '')
        articles = []
        
        # Simple parsing - look for patterns like "Title: ... URL: ..." or bullet points
        lines = content.split('\n')
        current_article = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Look for title patterns
            if any(marker in line.lower() for marker in ['title:', '1.', '2.', '3.', '4.', '5.', '-', '*']):
                if current_article:
                    articles.append(current_article)
                    current_article = {}
                
                # Extract title
                title = line
                for marker in ['title:', '1.', '2.', '3.', '4.', '5.', '-', '*']:
                    title = title.replace(marker, '').strip()
                
                current_article['title'] = title[:100]  # Limit title length
                
            # Look for URL patterns
            elif 'http' in line:
                if current_article:
                    current_article['url'] = line.strip()
                    
            # Look for summary
            elif len(line) > 20 and 'summary' not in current_article:
                current_article['summary'] = line[:200]  # Limit summary length
        
        # Add last article
        if current_article:
            articles.append(current_article)
        
        # If parsing fails, return warning
        if not articles:
            return [{
                'title': 'No articles found',
                'summary': 'No relevant articles could be extracted from the AI response.',
                'url': '#'
            }]
        
        return articles[:5]  # Limit to 5 articles
    
    def _get_mock_analysis(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mock analysis when API is not available"""
        
        location = incident.get('location', 'Unknown location')
        description = incident.get('description', 'Traffic incident')
        severity = incident.get('severity', 1)
        
        severity_text = "high" if severity > 2 else "moderate" if severity > 1 else "low"
        
        mock_summary = f"""
        **Traffic Analysis for {location}**
        
        **Immediate Impact:**
        This {severity_text}-severity incident involving {description.lower()} is likely causing traffic delays and requiring emergency response coordination.
        
        **Planning Considerations:**
        - Monitor traffic flow patterns in the {location} area
        - Consider temporary traffic management measures
        - Evaluate intersection safety if applicable
        - Review emergency response protocols
        
        **Recommendations:**
        - Implement temporary traffic control if needed
        - Monitor for similar incidents in this location
        - Consider infrastructure improvements for prevention
        """
        
        return {
            'summary': mock_summary.strip(),
            'planning_insights': f"Consider traffic pattern analysis for {location} and evaluate need for infrastructure improvements to prevent similar {description.lower()} incidents.",
            'related_articles': [
                {
                    'title': f'Traffic Safety Guidelines for {location}',
                    'summary': 'Municipal guidelines for traffic incident management and prevention',
                    'url': '#'
                },
                {
                    'title': 'Rhode Island Traffic Planning Resources',
                    'summary': 'State resources for municipal traffic planning and safety',
                    'url': '#'
                },
                {
                    'title': 'Emergency Response Coordination',
                    'summary': 'Best practices for coordinating emergency response to traffic incidents',
                    'url': '#'
                }
            ],
            'timestamp': datetime.now().isoformat(),
            'error': False,
            'mock': True
        }

# Streamlit integration functions
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_cached_analysis(incident_id: str, incident_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get cached analysis for an incident"""
    analyzer = TrafficAnalyzer()
    return analyzer.analyze_incident(incident_data)

def display_analysis_popup(analysis: Dict[str, Any], incident: Dict[str, Any]) -> None:
    """Display analysis in a Streamlit popup format"""
    
    # Analysis summary card
    with st.container():
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #faf8f3 0%, #f5f1e8 100%);
            padding: 1.5rem;
            border-radius: 12px;
            border-left: 4px solid #5a7c47;
            margin-bottom: 1rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        ">
            <h3 style="color: #2d5016; margin: 0 0 1rem 0;">
                AI Traffic Analysis
            </h3>
            <div style="color: #2d5016; line-height: 1.6;">
                {analysis.get('summary', 'No analysis available')}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Planning insights
    if analysis.get('planning_insights'):
        st.subheader("Planning Insights")
        st.info(analysis['planning_insights'])
    
    # Related articles in sidebar
    articles = analysis.get('related_articles', [])
    if articles:
        with st.sidebar:
            st.subheader("Related Information")
            
            for i, article in enumerate(articles):
                with st.expander(f"Article {i+1}"):
                    st.markdown(f"**{article.get('title', 'No title')}**")
                    st.write(article.get('summary', 'No summary available'))
                    if article.get('url') and article['url'] != '#':
                        st.markdown(f"[Read more]({article['url']})")

def create_enhanced_popup_html(incident: Dict[str, Any], analysis: Optional[Dict[str, Any]] = None) -> str:
    """Create enhanced popup HTML with AI analysis"""
    
    location = incident.get('location', 'Unknown')
    description = incident.get('description', 'Traffic incident')
    severity = incident.get('severity', 1)
    timestamp = incident.get('timestamp', '')
    
    if hasattr(timestamp, 'strftime'):
        time_str = timestamp.strftime('%H:%M')
    else:
        time_str = str(timestamp)
    
    # Base popup HTML
    popup_html = f"""
    <div style="
        background-color: rgba(255, 255, 255, 0.98); 
        padding: 16px; 
        border-radius: 12px; 
        font-family: 'Segoe UI', sans-serif; 
        font-size: 13px; 
        max-width: 320px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        border: 1px solid #e0e0e0;
    ">
        <div style="
            background: linear-gradient(135deg, #2d5016 0%, #5a7c47 100%);
            color: white;
            padding: 12px;
            margin: -16px -16px 12px -16px;
            border-radius: 12px 12px 0 0;
        ">
            <h4 style="margin: 0; font-size: 16px; font-weight: 600;">
                {location}
            </h4>
        </div>
        
        <div style="margin-bottom: 12px;">
            <p style="margin: 0 0 8px 0; color: #333; line-height: 1.5; font-weight: 500;">
                {description}
            </p>
            
            <div style="
                display: flex; 
                justify-content: space-between; 
                align-items: center; 
                margin: 8px 0;
                padding: 8px;
                background: #f8f9fa;
                border-radius: 6px;
            ">
                <span style="color: #666; font-size: 12px;">
                    <strong>Severity:</strong> {severity}
                </span>
                <span style="color: #666; font-size: 12px;">
                    <strong>Time:</strong> {time_str}
                </span>
            </div>
        </div>
    """
    
    # Add AI analysis if available
    if analysis and not analysis.get('error'):
        summary = analysis.get('summary', '')[:150] + '...' if len(analysis.get('summary', '')) > 150 else analysis.get('summary', '')
        
        popup_html += f"""
        <div style="
            background: linear-gradient(135deg, #e3f2fd 0%, #f5f5f5 100%);
            padding: 10px;
            border-radius: 8px;
            border-left: 3px solid #2196f3;
            margin-bottom: 10px;
        ">
            <h5 style="margin: 0 0 6px 0; color: #1976d2; font-size: 12px;">
                AI Analysis
            </h5>
            <p style="margin: 0; color: #333; font-size: 11px; line-height: 1.4;">
                {summary}
            </p>
        </div>
        """
    
    # Closing elements
    popup_html += f"""
        <div style="
            text-align: center; 
            margin-top: 12px; 
            padding: 8px; 
            background: #e8f5e8; 
            border-radius: 6px;
            border: 1px solid #c8e6c9;
        ">
            <span style="color: #2d5016; font-size: 11px; font-weight: 500;">
                Click marker for detailed analysis
            </span>
        </div>
    </div>
    """
    
    return popup_html