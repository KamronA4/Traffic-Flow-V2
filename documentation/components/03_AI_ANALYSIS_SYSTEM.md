# AI Analysis System - Deep Dive

## Overview

The Village Platform's AI Analysis System (`utils/ai_analyzer.py`, `utils/enhanced_ai_analyzer.py`) transforms raw traffic incident data into actionable municipal planning insights using Perplexity AI's Sonar models. The system provides contextual analysis, planning recommendations, and related information discovery.

## Architecture

### Core Components

```python
# AI Analysis Modules
- ai_analyzer.py           # Basic Perplexity integration
- enhanced_ai_analyzer.py  # Advanced caching and optimization
- column_utils.py          # Data preprocessing utilities
```

### AI Analyzer Class Structure

```python
class TrafficAnalyzer:
    """AI-powered traffic incident analyzer with Perplexity integration"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or st.secrets.get("PERPLEXITY_API_KEY", "")
        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
    def analyze_incident(self, incident, include_articles=True, max_retries=3):
        """Main analysis entry point"""
        
    def _create_analysis_prompt(self, incident):
        """Generate optimized prompts for municipal insights"""
        
    def _call_perplexity_api(self, prompt, model="llama-3.1-sonar-small-128k-online"):
        """Make API calls with retry logic and error handling"""
```

## Prompt Engineering

### Analysis Prompt Design

The system uses carefully crafted prompts to extract municipal planning insights:

```python
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
    
    Please provide a concise but comprehensive analysis focusing on actionable insights 
    for transportation planners and municipal officials. Format your response in clear sections.
    """
    
    return prompt
```

### Article Discovery Prompt

```python
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
    
    Please provide 3-5 relevant, recent sources with titles and brief summaries. 
    Focus on official municipal sources, local news, and traffic planning resources.
    """
    
    return prompt
```

## API Integration

### Perplexity API Configuration

```python
# Model selection based on use case
MODELS = {
    "analysis": "llama-3.1-sonar-small-128k-online",    # Fast, cost-effective
    "research": "llama-3.1-sonar-large-128k-online",    # Deep research
    "planning": "llama-3.1-sonar-huge-128k-online"      # Complex planning
}

# API payload structure
payload = {
    "model": model,
    "messages": [
        {
            "role": "system",
            "content": "You are an expert municipal traffic planner and transportation analyst."
        },
        {
            "role": "user", 
            "content": prompt
        }
    ],
    "max_tokens": 1000,
    "temperature": 0.3,    # Low temperature for consistent, factual responses
    "top_p": 0.9           # Nucleus sampling for quality
}
```

### Error Handling & Retry Logic

```python
def _call_perplexity_api(
    self, 
    prompt: str, 
    model: str = "llama-3.1-sonar-small-128k-online",
    max_retries: int = 3
) -> Dict[str, Any]:
    """Make API call to Perplexity with retry logic"""
    
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
            elif response.status_code == 429:
                # Rate limiting - exponential backoff
                wait_time = (2 ** attempt) * 2
                time.sleep(wait_time)
                continue
            else:
                raise requests.RequestException(f"API returned status {response.status_code}")
                
        except requests.RequestException as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(2 ** attempt)  # Exponential backoff
    
    raise Exception("Max retries exceeded")
```

## Enhanced Analysis Features

### Caching System

```python
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_cached_analysis(incident_id: str, incident_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get cached analysis for an incident"""
    analyzer = TrafficAnalyzer()
    return analyzer.analyze_incident(incident_data)

class AnalysisCache:
    """Advanced caching with semantic similarity"""
    
    def __init__(self):
        self.cache = {}
        self.similarity_threshold = 0.85
    
    def get_similar_analysis(self, incident):
        """Find cached analysis for similar incidents"""
        
        for cached_key, cached_data in self.cache.items():
            similarity = self.calculate_similarity(
                incident, 
                cached_data['incident']
            )
            
            if similarity > self.similarity_threshold:
                return cached_data['analysis']
        
        return None
    
    def calculate_similarity(self, incident1, incident2):
        """Calculate incident similarity for cache matching"""
        
        # Location similarity
        location_match = self.location_similarity(
            incident1.get('location'), 
            incident2.get('location')
        )
        
        # Description similarity
        desc_match = self.description_similarity(
            incident1.get('description'), 
            incident2.get('description')
        )
        
        # Severity similarity
        severity_match = abs(
            incident1.get('severity', 0) - incident2.get('severity', 0)
        ) <= 1
        
        # Weighted similarity score
        return (location_match * 0.4 + desc_match * 0.4 + severity_match * 0.2)
```

### Analysis Processing Pipeline

```python
def analyze_incident(
    self, 
    incident: Dict[str, Any],
    include_articles: bool = True,
    max_retries: int = 3
) -> Dict[str, Any]:
    """
    Comprehensive incident analysis pipeline
    
    Pipeline Steps:
    1. Input validation and preprocessing
    2. Check analysis cache
    3. Generate analysis prompt
    4. Call Perplexity API
    5. Extract planning insights
    6. Find related articles (optional)
    7. Structure and return results
    """
    
    # Input validation
    if not self._validate_incident_data(incident):
        return self._get_error_response("Invalid incident data")
    
    # Check cache first
    cached_analysis = self.cache.get_similar_analysis(incident)
    if cached_analysis:
        return cached_analysis
    
    try:
        # Generate analysis prompt
        analysis_prompt = self._create_analysis_prompt(incident)
        
        # Get AI analysis
        analysis_response = self._call_perplexity_api(
            analysis_prompt, 
            max_retries=max_retries
        )
        
        # Structure results
        result = {
            'summary': analysis_response.get('content', 'Analysis unavailable'),
            'planning_insights': self._extract_planning_insights(analysis_response),
            'timestamp': datetime.now().isoformat(),
            'model_used': analysis_response.get('model'),
            'usage_stats': analysis_response.get('usage')
        }
        
        # Get related articles if requested
        if include_articles:
            articles_prompt = self._create_articles_prompt(incident)
            articles_response = self._call_perplexity_api(
                articles_prompt,
                max_retries=max_retries
            )
            result['related_articles'] = self._parse_articles(articles_response)
        
        # Cache successful analysis
        self.cache.store_analysis(incident, result)
        
        return result
        
    except Exception as e:
        return self._get_error_response(str(e))
```

## Insight Extraction

### Planning Insights Parser

```python
def _extract_planning_insights(self, response: Dict[str, Any]) -> str:
    """Extract municipal planning insights from AI response"""
    
    content = response.get('content', '')
    
    # Look for planning-related sections
    planning_keywords = [
        'planning', 'municipal', 'resource', 'infrastructure',
        'prevention', 'allocation', 'recommendation', 'policy',
        'improvement', 'safety', 'management', 'coordination'
    ]
    
    lines = content.split('\n')
    planning_lines = []
    
    # Extract lines containing planning keywords
    for line in lines:
        if any(keyword.lower() in line.lower() for keyword in planning_keywords):
            cleaned_line = line.strip()
            if len(cleaned_line) > 10:  # Filter out headers/short lines
                planning_lines.append(cleaned_line)
    
    if planning_lines:
        return '\n'.join(planning_lines)
    else:
        # Fallback: Extract recommendations section
        return self._extract_recommendations_section(content)

def _extract_recommendations_section(self, content: str) -> str:
    """Extract recommendations section from analysis"""
    
    # Look for common section headers
    sections = content.split('\n\n')
    
    for section in sections:
        if any(header in section.lower() for header in 
               ['recommendation', 'suggest', 'action', 'next steps']):
            return section.strip()
    
    # Fallback: Return last substantial paragraph
    paragraphs = [p.strip() for p in sections if len(p.strip()) > 50]
    return paragraphs[-1] if paragraphs else "No specific planning insights available"
```

### Article Parser

```python
def _parse_articles(self, response: Dict[str, Any]) -> List[Dict[str, str]]:
    """Parse articles from AI response using multiple strategies"""
    
    content = response.get('content', '')
    articles = []
    
    # Strategy 1: Structured parsing
    articles.extend(self._parse_structured_articles(content))
    
    # Strategy 2: Markdown list parsing
    if not articles:
        articles.extend(self._parse_markdown_articles(content))
    
    # Strategy 3: Fallback pattern matching
    if not articles:
        articles.extend(self._parse_fallback_articles(content))
    
    # Validate and clean articles
    validated_articles = self._validate_articles(articles)
    
    return validated_articles[:5]  # Limit to 5 articles

def _parse_structured_articles(self, content: str) -> List[Dict[str, str]]:
    """Parse articles with structured format (Title: ... URL: ... Summary: ...)"""
    
    articles = []
    lines = content.split('\n')
    current_article = {}
    
    for line in lines:
        line = line.strip()
        
        if line.startswith(('Title:', '**Title:**')):
            if current_article:
                articles.append(current_article)
                current_article = {}
            current_article['title'] = line.replace('Title:', '').replace('**', '').strip()
            
        elif line.startswith(('URL:', '**URL:**', 'Link:')):
            current_article['url'] = line.replace('URL:', '').replace('Link:', '').replace('**', '').strip()
            
        elif line.startswith(('Summary:', '**Summary:**')):
            current_article['summary'] = line.replace('Summary:', '').replace('**', '').strip()
    
    if current_article:
        articles.append(current_article)
    
    return articles

def _validate_articles(self, articles: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Validate and clean parsed articles"""
    
    validated = []
    
    for article in articles:
        # Ensure required fields
        if not article.get('title'):
            continue
        
        # Clean and validate title
        title = article['title'][:100].strip()
        if len(title) < 10:
            continue
        
        # Clean summary
        summary = article.get('summary', 'No summary available')[:200].strip()
        
        # Validate URL
        url = article.get('url', '#')
        if url and not url.startswith(('http://', 'https://', '#')):
            url = '#'
        
        validated.append({
            'title': title,
            'summary': summary,
            'url': url
        })
    
    return validated
```

## Mock Analysis System

For development and fallback scenarios:

```python
def _get_mock_analysis(self, incident: Dict[str, Any]) -> Dict[str, Any]:
    """Generate realistic mock analysis when API unavailable"""
    
    location = incident.get('location', 'Unknown location')
    description = incident.get('description', 'Traffic incident')
    severity = incident.get('severity', 1)
    
    # Generate context-aware mock content
    severity_text = "high" if severity > 3 else "moderate" if severity > 1 else "low"
    
    # Template-based analysis generation
    analysis_templates = {
        'collision': self._get_collision_template(location, severity_text),
        'construction': self._get_construction_template(location, severity_text),
        'weather': self._get_weather_template(location, severity_text),
        'default': self._get_default_template(location, severity_text)
    }
    
    # Select appropriate template
    template_key = 'default'
    for key in analysis_templates.keys():
        if key in description.lower():
            template_key = key
            break
    
    mock_summary = analysis_templates[template_key]
    
    return {
        'summary': mock_summary,
        'planning_insights': self._generate_mock_insights(location, description),
        'related_articles': self._generate_mock_articles(location),
        'timestamp': datetime.now().isoformat(),
        'error': False,
        'mock': True
    }
```

## Integration with Streamlit

### Popup Display System

```python
def display_analysis_popup(analysis: Dict[str, Any], incident: Dict[str, Any]) -> None:
    """Display analysis in Streamlit with Village theme"""
    
    with st.container():
        # Main analysis card
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
                🤖 AI Traffic Analysis
            </h3>
            <div style="color: #2d5016; line-height: 1.6;">
                {analysis.get('summary', 'No analysis available')}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Planning insights section
    if analysis.get('planning_insights'):
        st.subheader("📋 Planning Insights")
        st.info(analysis['planning_insights'])
    
    # Related articles in sidebar
    articles = analysis.get('related_articles', [])
    if articles and not analysis.get('mock'):
        with st.sidebar:
            st.subheader("📰 Related Information")
            
            for i, article in enumerate(articles):
                with st.expander(f"📄 Article {i+1}"):
                    st.markdown(f"**{article.get('title', 'No title')}**")
                    st.write(article.get('summary', 'No summary available'))
                    if article.get('url') and article['url'] != '#':
                        st.markdown(f"[🔗 Read more]({article['url']})")
    
    # Usage statistics (for admins)
    if analysis.get('usage_stats') and st.session_state.get('user_role') == 'admin':
        with st.expander("📊 API Usage Stats"):
            usage = analysis['usage_stats']
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Tokens Used", usage.get('total_tokens', 0))
            with col2:
                st.metric("Prompt Tokens", usage.get('prompt_tokens', 0))
            with col3:
                st.metric("Completion Tokens", usage.get('completion_tokens', 0))
```

### Map Integration

```python
def create_enhanced_popup_html(
    incident: Dict[str, Any], 
    analysis: Optional[Dict[str, Any]] = None
) -> str:
    """Create enhanced Folium popup with AI analysis preview"""
    
    # Basic incident info
    location = incident.get('location', 'Unknown')
    description = incident.get('description', 'Traffic incident')
    severity = incident.get('severity', 1)
    
    # Base popup structure
    popup_html = f"""
    <div style="max-width: 320px; font-family: 'Segoe UI', sans-serif;">
        <div style="background: linear-gradient(135deg, #2d5016 0%, #5a7c47 100%); 
                    color: white; padding: 12px; margin: -16px -16px 12px -16px;">
            <h4 style="margin: 0;">{location}</h4>
        </div>
        
        <p style="margin: 0 0 8px 0; font-weight: 500;">{description}</p>
        <p style="margin: 0 0 8px 0; color: #666;">Severity: {severity}</p>
    """
    
    # Add AI analysis preview if available
    if analysis and not analysis.get('error'):
        # Truncate summary for popup
        summary = analysis.get('summary', '')
        if len(summary) > 150:
            summary = summary[:150] + '...'
        
        popup_html += f"""
        <div style="background: #e3f2fd; padding: 10px; border-radius: 8px; 
                    margin: 10px 0; border-left: 3px solid #2196f3;">
            <h5 style="margin: 0 0 6px 0; color: #1976d2; font-size: 12px;">
                🤖 AI Analysis Preview
            </h5>
            <p style="margin: 0; font-size: 11px; line-height: 1.4;">{summary}</p>
        </div>
        """
    
    popup_html += """
        <div style="text-align: center; margin-top: 12px; padding: 8px; 
                    background: #e8f5e8; border-radius: 6px;">
            <span style="color: #2d5016; font-size: 11px; font-weight: 500;">
                💡 Click marker for detailed analysis
            </span>
        </div>
    </div>
    """
    
    return popup_html
```

## Performance Optimization

### Response Time Optimization

```python
class PerformanceOptimizer:
    """Optimize AI analysis performance"""
    
    def __init__(self):
        self.response_times = {}
        self.model_performance = {}
    
    def select_optimal_model(self, incident_complexity):
        """Select best model based on complexity and performance history"""
        
        if incident_complexity == 'simple':
            return "llama-3.1-sonar-small-128k-online"  # Fastest
        elif incident_complexity == 'complex':
            return "llama-3.1-sonar-large-128k-online"  # Better quality
        else:
            return "llama-3.1-sonar-small-128k-online"  # Default
    
    def track_performance(self, model, response_time, quality_score):
        """Track model performance for optimization"""
        
        if model not in self.model_performance:
            self.model_performance[model] = {
                'response_times': [],
                'quality_scores': [],
                'usage_count': 0
            }
        
        self.model_performance[model]['response_times'].append(response_time)
        self.model_performance[model]['quality_scores'].append(quality_score)
        self.model_performance[model]['usage_count'] += 1
```

### Cost Management

```python
class CostManager:
    """Monitor and manage AI API costs"""
    
    def __init__(self):
        self.daily_budget = 50.0  # USD
        self.cost_per_1k_tokens = 0.001  # Approximate
    
    def estimate_cost(self, prompt_length):
        """Estimate cost before making API call"""
        
        estimated_tokens = prompt_length * 1.3  # Rough estimation
        estimated_cost = (estimated_tokens / 1000) * self.cost_per_1k_tokens
        
        return estimated_cost
    
    def check_budget_remaining(self):
        """Check if daily budget allows more requests"""
        
        today_usage = self.get_daily_usage()
        return self.daily_budget - today_usage
    
    def optimize_for_cost(self, incident):
        """Optimize analysis to stay within budget"""
        
        remaining_budget = self.check_budget_remaining()
        
        if remaining_budget < 1.0:  # Low budget
            return self._get_lightweight_analysis(incident)
        elif remaining_budget < 5.0:  # Medium budget
            return self._get_standard_analysis(incident)
        else:  # Full budget available
            return self._get_comprehensive_analysis(incident)
```

This AI analysis system provides intelligent, contextual insights that transform raw traffic data into actionable municipal planning intelligence while maintaining cost efficiency and high performance.