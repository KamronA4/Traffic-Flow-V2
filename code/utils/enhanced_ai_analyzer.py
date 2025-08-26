# utils/enhanced_ai_analyzer.py - Advanced AI Context Layer for Municipal Planning

import streamlit as st
import requests
import json
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import time
import logging
from dataclasses import dataclass
from enum import Enum
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnalysisType(Enum):
    """Types of AI analysis available"""
    IMMEDIATE_RESPONSE = "immediate_response"
    PLANNING_INSIGHTS = "planning_insights"
    HISTORICAL_CONTEXT = "historical_context"
    PREDICTIVE_ANALYSIS = "predictive_analysis"
    POLICY_RECOMMENDATIONS = "policy_recommendations"
    STAKEHOLDER_IMPACT = "stakeholder_impact"

@dataclass
class ContextualData:
    """Contextual information for enhanced analysis"""
    location: str
    historical_incidents: List[Dict]
    weather_conditions: Optional[Dict] = None
    traffic_patterns: Optional[Dict] = None
    demographic_data: Optional[Dict] = None
    infrastructure_info: Optional[Dict] = None
    policy_context: Optional[Dict] = None

class EnhancedTrafficAnalyzer:
    """
    Advanced AI-powered traffic incident analyzer with comprehensive municipal planning context
    
    Features:
    - Multi-layered analysis (immediate, planning, historical, predictive)
    - Contextual data enrichment
    - Real-time news correlation
    - Policy and infrastructure recommendations
    - Stakeholder impact assessment
    - Professional report generation
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with Perplexity API key and context databases"""
        self.api_key = api_key or st.secrets.get("PERPLEXITY_API_KEY", "")
        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Context databases
        self.municipal_database = self._load_municipal_context()
        self.infrastructure_database = self._load_infrastructure_context()
        self.policy_database = self._load_policy_context()
        
        # Analysis templates
        self.analysis_templates = self._load_analysis_templates()
        
        logger.info("Enhanced Traffic Analyzer initialized with full context layer")
    
    def _load_municipal_context(self) -> Dict:
        """Load municipal planning context database"""
        return {
            'Rhode Island': {
                'state_policies': [
                    'Transportation 2040 Long Range Plan',
                    'Complete Streets Policy',
                    'Vision Zero Initiative',
                    'Climate Change Action Plan'
                ],
                'key_stakeholders': [
                    'RIDOT (Rhode Island Department of Transportation)',
                    'Rhode Island Emergency Management Agency',
                    'Local Police Departments',
                    'Municipal Public Works',
                    'Rhode Island Public Transit Authority'
                ],
                'funding_sources': [
                    'Federal Highway Administration',
                    'Rhode Island Infrastructure Bank',
                    'Municipal Capital Improvement Plans',
                    'Transportation Improvement Program'
                ]
            },
            'Providence': {
                'population': 190934,
                'key_infrastructure': ['I-95', 'I-195', 'Route 6', 'Kennedy Plaza'],
                'recent_projects': [
                    'Downtown Providence Streetscape',
                    'Washington Bridge Rehabilitation',
                    'Bus Rapid Transit Planning'
                ],
                'contact_info': {
                    'traffic_engineer': 'Providence Traffic Engineering',
                    'planning_dept': 'Providence Planning Department',
                    'emergency_management': 'Providence Emergency Management'
                }
            },
            'Warwick': {
                'population': 82823,
                'key_infrastructure': ['T.F. Green Airport', 'Route 95', 'Post Road'],
                'recent_projects': [
                    'Warwick Intermodal Hub',
                    'Route 2 Improvements',
                    'Bicycle Infrastructure Plan'
                ]
            }
        }
    
    def _load_infrastructure_context(self) -> Dict:
        """Load infrastructure and engineering context"""
        return {
            'road_classifications': {
                'Interstate': {'capacity': 'High', 'priority': 'Critical', 'maintenance': 'State'},
                'Arterial': {'capacity': 'Medium-High', 'priority': 'High', 'maintenance': 'State/Local'},
                'Collector': {'capacity': 'Medium', 'priority': 'Medium', 'maintenance': 'Local'},
                'Local': {'capacity': 'Low', 'priority': 'Low', 'maintenance': 'Local'}
            },
            'incident_impact_factors': {
                'time_of_day': {
                    'rush_hours': {'multiplier': 3.0, 'considerations': 'Peak capacity usage'},
                    'off_peak': {'multiplier': 1.0, 'considerations': 'Normal operations'},
                    'overnight': {'multiplier': 0.5, 'considerations': 'Minimal impact'}
                },
                'weather_conditions': {
                    'rain': {'multiplier': 1.5, 'considerations': 'Reduced visibility and traction'},
                    'snow': {'multiplier': 2.5, 'considerations': 'Severe capacity reduction'},
                    'fog': {'multiplier': 2.0, 'considerations': 'Visibility concerns'}
                }
            },
            'standard_responses': {
                'construction': ['Traffic control setup', 'Public notification', 'Detour planning'],
                'accident': ['Emergency response', 'Traffic management', 'Investigation'],
                'weather': ['Road treatment', 'Public advisories', 'Service adjustments']
            }
        }
    
    def _load_policy_context(self) -> Dict:
        """Load policy and regulatory context"""
        return {
            'federal_regulations': {
                'MUTCD': 'Manual on Uniform Traffic Control Devices',
                'ADA': 'Americans with Disabilities Act compliance',
                'NEPA': 'National Environmental Policy Act requirements'
            },
            'state_regulations': {
                'RIDOT_standards': 'Rhode Island design standards',
                'environmental_review': 'State environmental requirements',
                'permitting': 'State permitting processes'
            },
            'best_practices': {
                'traffic_calming': ['Speed humps', 'Chicanes', 'Roundabouts'],
                'safety_improvements': ['Better signage', 'Lighting', 'Sight distance'],
                'capacity_management': ['Signal timing', 'Lane management', 'ITS systems']
            }
        }
    
    def _load_analysis_templates(self) -> Dict:
        """Load analysis prompt templates"""
        return {
            'immediate_response': """
            As a municipal traffic engineer, analyze this incident for immediate response:
            
            **Incident**: {description} at {location}
            **Severity**: {severity}/5 | **Time**: {timestamp}
            **Context**: {context}
            
            Provide:
            1. Immediate traffic impact assessment
            2. Required emergency response resources
            3. Recommended traffic management actions
            4. Estimated duration and affected routes
            5. Public communication priorities
            
            Focus on actionable immediate steps for traffic operations center.
            """,
            
            'planning_insights': """
            As a municipal transportation planner, analyze this incident for planning insights:
            
            **Incident**: {description} at {location}
            **Historical Context**: {historical_data}
            **Infrastructure**: {infrastructure_info}
            **Policy Context**: {policy_context}
            
            Provide:
            1. Root cause analysis and contributing factors
            2. Infrastructure improvement recommendations
            3. Policy implications and regulatory considerations
            4. Long-term prevention strategies
            5. Budget and funding recommendations
            6. Stakeholder coordination needs
            
            Focus on strategic planning and infrastructure investment priorities.
            """,
            
            'historical_context': """
            As a data analyst specializing in transportation planning, analyze historical patterns:
            
            **Current Incident**: {description} at {location}
            **Historical Incidents**: {historical_incidents}
            **Temporal Patterns**: {temporal_patterns}
            **Comparative Analysis**: {comparative_data}
            
            Provide:
            1. Historical frequency and trend analysis
            2. Seasonal and temporal pattern identification
            3. Comparison with similar locations
            4. Risk assessment and probability metrics
            5. Data-driven recommendations
            
            Focus on statistical insights and predictive intelligence.
            """,
            
            'predictive_analysis': """
            As a transportation systems analyst, provide predictive analysis:
            
            **Current Situation**: {description} at {location}
            **System Context**: {system_context}
            **Predictive Factors**: {predictive_factors}
            **Modeling Data**: {modeling_data}
            
            Provide:
            1. Short-term impact predictions (next 2-4 hours)
            2. Secondary incident probability assessment
            3. Network-wide congestion propagation analysis
            4. Alternative route capacity analysis
            5. Recovery time estimation
            
            Focus on operational decision support and resource allocation.
            """,
            
            'policy_recommendations': """
            As a transportation policy advisor, provide policy recommendations:
            
            **Incident Analysis**: {description} at {location}
            **Policy Context**: {policy_context}
            **Regulatory Framework**: {regulatory_info}
            **Stakeholder Impact**: {stakeholder_impact}
            
            Provide:
            1. Relevant policy and regulatory analysis
            2. Compliance requirements and considerations
            3. Inter-agency coordination recommendations
            4. Public engagement strategies
            5. Legislative or regulatory change recommendations
            
            Focus on policy implementation and governance aspects.
            """,
            
            'stakeholder_impact': """
            As a municipal communications director, analyze stakeholder impacts:
            
            **Incident**: {description} at {location}
            **Affected Stakeholders**: {stakeholders}
            **Communication Context**: {communication_context}
            **Public Impact**: {public_impact}
            
            Provide:
            1. Stakeholder impact assessment
            2. Communication strategy recommendations
            3. Public information priorities
            4. Media relations considerations
            5. Community engagement opportunities
            
            Focus on public communication and stakeholder management.
            """
        }
    
    async def comprehensive_analysis(
        self,
        incident: Dict[str, Any],
        analysis_types: List[AnalysisType] = None,
        include_context: bool = True
    ) -> Dict[str, Any]:
        """
        Perform comprehensive multi-layered analysis
        
        Args:
            incident: Incident data dictionary
            analysis_types: List of analysis types to perform
            include_context: Whether to include contextual data enrichment
            
        Returns:
            Comprehensive analysis results
        """
        if analysis_types is None:
            analysis_types = [AnalysisType.IMMEDIATE_RESPONSE, AnalysisType.PLANNING_INSIGHTS]
        
        # Gather contextual data
        context = await self._gather_contextual_data(incident) if include_context else None
        
        # Perform parallel analysis
        analysis_results = {}
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            
            for analysis_type in analysis_types:
                task = self._perform_analysis_type(
                    session, incident, analysis_type, context
                )
                tasks.append((analysis_type, task))
            
            # Execute all analyses in parallel
            for analysis_type, task in tasks:
                try:
                    result = await task
                    analysis_results[analysis_type.value] = result
                except Exception as e:
                    logger.error(f"Error in {analysis_type.value} analysis: {e}")
                    analysis_results[analysis_type.value] = {
                        'error': str(e),
                        'analysis': 'Analysis failed'
                    }
        
        # Synthesize results
        synthesis = await self._synthesize_analysis_results(analysis_results, incident)
        
        return {
            'incident': incident,
            'contextual_data': context,
            'individual_analyses': analysis_results,
            'synthesis': synthesis,
            'recommendations': self._generate_recommendations(analysis_results),
            'action_items': self._generate_action_items(analysis_results),
            'timestamp': datetime.now().isoformat(),
            'analysis_types': [t.value for t in analysis_types]
        }
    
    async def _gather_contextual_data(self, incident: Dict[str, Any]) -> ContextualData:
        """Gather comprehensive contextual data for analysis"""
        location = incident.get('location', 'Unknown')
        
        # Gather historical incidents (simplified - would query database)
        historical_incidents = await self._get_historical_incidents(location)
        
        # Gather weather context (simplified - would query weather API)
        weather_conditions = await self._get_weather_context(location)
        
        # Gather traffic patterns (simplified - would query traffic database)
        traffic_patterns = await self._get_traffic_patterns(location)
        
        # Gather demographic data
        demographic_data = self._get_demographic_data(location)
        
        # Gather infrastructure information
        infrastructure_info = self._get_infrastructure_info(location)
        
        # Gather policy context
        policy_context = self._get_policy_context(location)
        
        return ContextualData(
            location=location,
            historical_incidents=historical_incidents,
            weather_conditions=weather_conditions,
            traffic_patterns=traffic_patterns,
            demographic_data=demographic_data,
            infrastructure_info=infrastructure_info,
            policy_context=policy_context
        )
    
    async def _perform_analysis_type(
        self,
        session: aiohttp.ClientSession,
        incident: Dict[str, Any],
        analysis_type: AnalysisType,
        context: ContextualData
    ) -> Dict[str, Any]:
        """Perform specific type of analysis"""
        
        # Prepare analysis prompt
        prompt = self._prepare_analysis_prompt(incident, analysis_type, context)
        
        # Call Perplexity API
        result = await self._call_perplexity_async(session, prompt, analysis_type)
        
        return result
    
    def _prepare_analysis_prompt(
        self,
        incident: Dict[str, Any],
        analysis_type: AnalysisType,
        context: ContextualData
    ) -> str:
        """Prepare analysis prompt with context"""
        
        template = self.analysis_templates.get(analysis_type.value, "")
        
        # Prepare context variables
        context_vars = {
            'description': incident.get('description', 'Traffic incident'),
            'location': incident.get('location', 'Unknown'),
            'severity': incident.get('severity', 1),
            'timestamp': incident.get('timestamp', datetime.now()),
            'context': self._format_context_summary(context),
            'historical_data': self._format_historical_data(context.historical_incidents if context else []),
            'infrastructure_info': self._format_infrastructure_info(context.infrastructure_info if context else {}),
            'policy_context': self._format_policy_context(context.policy_context if context else {}),
            'historical_incidents': self._format_historical_incidents(context.historical_incidents if context else []),
            'temporal_patterns': self._format_temporal_patterns(context.traffic_patterns if context else {}),
            'comparative_data': self._format_comparative_data(context.demographic_data if context else {}),
            'system_context': self._format_system_context(context),
            'predictive_factors': self._format_predictive_factors(context),
            'modeling_data': self._format_modeling_data(context),
            'regulatory_info': self._format_regulatory_info(context.policy_context if context else {}),
            'stakeholder_impact': self._format_stakeholder_impact(context),
            'stakeholders': self._format_stakeholders(context),
            'communication_context': self._format_communication_context(context),
            'public_impact': self._format_public_impact(context)
        }
        
        return template.format(**context_vars)
    
    async def _call_perplexity_async(
        self,
        session: aiohttp.ClientSession,
        prompt: str,
        analysis_type: AnalysisType,
        model: str = "llama-3.1-sonar-large-128k-online"
    ) -> Dict[str, Any]:
        """Make async API call to Perplexity"""
        
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": f"You are an expert municipal traffic planner and transportation analyst specializing in {analysis_type.value}. Provide practical, actionable insights for municipal transportation professionals."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 1500,
            "temperature": 0.2,
            "top_p": 0.9
        }
        
        async with session.post(
            self.base_url,
            json=payload,
            headers=self.headers,
            timeout=30
        ) as response:
            if response.status == 200:
                result = await response.json()
                return {
                    'analysis': result['choices'][0]['message']['content'],
                    'usage': result.get('usage', {}),
                    'model': result.get('model', model),
                    'analysis_type': analysis_type.value
                }
            else:
                error_text = await response.text()
                raise Exception(f"API error {response.status}: {error_text}")
    
    async def _synthesize_analysis_results(
        self,
        analysis_results: Dict[str, Any],
        incident: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Synthesize multiple analysis results into coherent recommendations"""
        
        synthesis_prompt = f"""
        As a senior municipal transportation director, synthesize these analysis results:
        
        **Incident**: {incident.get('description', 'Traffic incident')} at {incident.get('location', 'Unknown')}
        
        **Analysis Results**:
        {json.dumps(analysis_results, indent=2)}
        
        Provide a comprehensive executive summary including:
        1. Key findings and insights
        2. Priority recommendations
        3. Resource allocation priorities
        4. Timeline for implementation
        5. Success metrics and monitoring plan
        
        Format as a professional executive briefing.
        """
        
        # Call Perplexity for synthesis
        try:
            async with aiohttp.ClientSession() as session:
                synthesis_result = await self._call_perplexity_async(
                    session, synthesis_prompt, AnalysisType.PLANNING_INSIGHTS
                )
            return synthesis_result
        except Exception as e:
            logger.error(f"Error in synthesis: {e}")
            return {
                'analysis': 'Synthesis failed - please review individual analyses',
                'error': str(e)
            }
    
    def _generate_recommendations(self, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate prioritized recommendations from analysis results"""
        recommendations = []
        
        for analysis_type, result in analysis_results.items():
            if not result.get('error'):
                # Extract recommendations from each analysis
                analysis_text = result.get('analysis', '')
                
                # Simple keyword-based recommendation extraction
                if 'recommend' in analysis_text.lower():
                    recommendations.append({
                        'type': analysis_type,
                        'priority': self._determine_priority(analysis_type),
                        'text': analysis_text,
                        'source': 'AI Analysis'
                    })
        
        return sorted(recommendations, key=lambda x: x['priority'])
    
    def _generate_action_items(self, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate specific action items from analysis results"""
        action_items = []
        
        # Standard action items based on analysis type
        action_templates = {
            'immediate_response': [
                {'action': 'Deploy traffic management team', 'timeframe': 'Immediate', 'responsible': 'Traffic Operations'},
                {'action': 'Issue public advisory', 'timeframe': '15 minutes', 'responsible': 'Communications'},
                {'action': 'Coordinate with emergency services', 'timeframe': 'Immediate', 'responsible': 'Emergency Management'}
            ],
            'planning_insights': [
                {'action': 'Schedule infrastructure assessment', 'timeframe': '1 week', 'responsible': 'Engineering'},
                {'action': 'Review funding options', 'timeframe': '2 weeks', 'responsible': 'Planning'},
                {'action': 'Engage stakeholders', 'timeframe': '1 month', 'responsible': 'Community Relations'}
            ]
        }
        
        for analysis_type, result in analysis_results.items():
            if not result.get('error') and analysis_type in action_templates:
                action_items.extend(action_templates[analysis_type])
        
        return action_items
    
    # Helper methods for formatting context data
    def _format_context_summary(self, context: ContextualData) -> str:
        if not context:
            return "Limited context available"
        
        return f"Location: {context.location}, Historical incidents: {len(context.historical_incidents)}, Weather: {context.weather_conditions}, Infrastructure: {bool(context.infrastructure_info)}"
    
    def _format_historical_data(self, historical_incidents: List[Dict]) -> str:
        if not historical_incidents:
            return "No historical data available"
        
        return f"Found {len(historical_incidents)} similar incidents in the past 6 months"
    
    def _format_infrastructure_info(self, infrastructure_info: Dict) -> str:
        if not infrastructure_info:
            return "Infrastructure data not available"
        
        return json.dumps(infrastructure_info, indent=2)
    
    def _format_policy_context(self, policy_context: Dict) -> str:
        if not policy_context:
            return "Policy context not available"
        
        return json.dumps(policy_context, indent=2)
    
    def _format_historical_incidents(self, historical_incidents: List[Dict]) -> str:
        return f"Historical incidents: {len(historical_incidents)} similar events"
    
    def _format_temporal_patterns(self, traffic_patterns: Dict) -> str:
        if not traffic_patterns:
            return "Traffic patterns not available"
        
        return json.dumps(traffic_patterns, indent=2)
    
    def _format_comparative_data(self, demographic_data: Dict) -> str:
        if not demographic_data:
            return "Comparative data not available"
        
        return json.dumps(demographic_data, indent=2)
    
    def _format_system_context(self, context: ContextualData) -> str:
        if not context:
            return "System context not available"
        
        return f"Location: {context.location}, Infrastructure: {bool(context.infrastructure_info)}"
    
    def _format_predictive_factors(self, context: ContextualData) -> str:
        if not context:
            return "Predictive factors not available"
        
        return f"Weather: {context.weather_conditions}, Traffic: {context.traffic_patterns}"
    
    def _format_modeling_data(self, context: ContextualData) -> str:
        if not context:
            return "Modeling data not available"
        
        return f"Historical: {len(context.historical_incidents)} incidents, Demographics: {bool(context.demographic_data)}"
    
    def _format_regulatory_info(self, policy_context: Dict) -> str:
        return json.dumps(policy_context, indent=2) if policy_context else "Regulatory info not available"
    
    def _format_stakeholder_impact(self, context: ContextualData) -> str:
        if not context:
            return "Stakeholder impact not available"
        
        return f"Location: {context.location}, Population affected: {context.demographic_data.get('population', 'Unknown') if context.demographic_data else 'Unknown'}"
    
    def _format_stakeholders(self, context: ContextualData) -> str:
        if not context:
            return "Stakeholders not available"
        
        location = context.location
        municipal_info = self.municipal_database.get(location, {})
        return json.dumps(municipal_info.get('key_stakeholders', []), indent=2)
    
    def _format_communication_context(self, context: ContextualData) -> str:
        if not context:
            return "Communication context not available"
        
        return f"Location: {context.location}, Public impact: Localized traffic disruption"
    
    def _format_public_impact(self, context: ContextualData) -> str:
        if not context:
            return "Public impact not available"
        
        return f"Traffic disruption in {context.location}, affecting local commuters and businesses"
    
    def _determine_priority(self, analysis_type: str) -> int:
        """Determine priority level for recommendations"""
        priority_map = {
            'immediate_response': 1,
            'planning_insights': 2,
            'historical_context': 3,
            'predictive_analysis': 1,
            'policy_recommendations': 4,
            'stakeholder_impact': 3
        }
        return priority_map.get(analysis_type, 5)
    
    # Simplified context gathering methods (would be enhanced with real data sources)
    async def _get_historical_incidents(self, location: str) -> List[Dict]:
        """Get historical incident data for location"""
        # This would query the database for historical incidents
        return [
            {'date': '2024-01-15', 'type': 'construction', 'severity': 2},
            {'date': '2024-01-10', 'type': 'accident', 'severity': 3}
        ]
    
    async def _get_weather_context(self, location: str) -> Dict:
        """Get current weather conditions"""
        # This would query a weather API
        return {
            'condition': 'clear',
            'temperature': 45,
            'visibility': 'good',
            'precipitation': 0
        }
    
    async def _get_traffic_patterns(self, location: str) -> Dict:
        """Get traffic pattern data"""
        # This would query traffic database
        return {
            'typical_volume': 'medium',
            'peak_hours': ['7-9 AM', '4-6 PM'],
            'congestion_level': 'moderate'
        }
    
    def _get_demographic_data(self, location: str) -> Dict:
        """Get demographic data for location"""
        municipal_info = self.municipal_database.get(location, {})
        return {
            'population': municipal_info.get('population', 0),
            'density': 'medium',
            'economic_activity': 'mixed'
        }
    
    def _get_infrastructure_info(self, location: str) -> Dict:
        """Get infrastructure information"""
        municipal_info = self.municipal_database.get(location, {})
        return {
            'key_infrastructure': municipal_info.get('key_infrastructure', []),
            'recent_projects': municipal_info.get('recent_projects', [])
        }
    
    def _get_policy_context(self, location: str) -> Dict:
        """Get policy context for location"""
        return self.policy_database


# Streamlit integration functions
def create_enhanced_analysis_interface():
    """Create enhanced analysis interface for Streamlit"""
    
    st.subheader("🤖 Advanced AI Analysis")
    
    # Analysis type selection
    analysis_options = {
        "Immediate Response": AnalysisType.IMMEDIATE_RESPONSE,
        "Planning Insights": AnalysisType.PLANNING_INSIGHTS,
        "Historical Context": AnalysisType.HISTORICAL_CONTEXT,
        "Predictive Analysis": AnalysisType.PREDICTIVE_ANALYSIS,
        "Policy Recommendations": AnalysisType.POLICY_RECOMMENDATIONS,
        "Stakeholder Impact": AnalysisType.STAKEHOLDER_IMPACT
    }
    
    selected_analyses = st.multiselect(
        "Select Analysis Types:",
        options=list(analysis_options.keys()),
        default=["Immediate Response", "Planning Insights"],
        help="Choose which types of analysis to perform"
    )
    
    # Context enrichment options
    include_context = st.checkbox(
        "Include Contextual Data Enrichment",
        value=True,
        help="Gather additional context like weather, demographics, and infrastructure data"
    )
    
    return [analysis_options[name] for name in selected_analyses], include_context

@st.cache_data(ttl=1800)  # Cache for 30 minutes
def get_enhanced_analysis(
    incident_id: str,
    incident_data: Dict[str, Any],
    analysis_types: List[AnalysisType],
    include_context: bool = True
) -> Dict[str, Any]:
    """Get enhanced analysis with caching"""
    
    analyzer = EnhancedTrafficAnalyzer()
    
    # Run async analysis in sync context
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(
        analyzer.comprehensive_analysis(
            incident_data,
            analysis_types,
            include_context
        )
    )

def display_enhanced_analysis(analysis_result: Dict[str, Any]):
    """Display enhanced analysis results in Streamlit"""
    
    if not analysis_result:
        st.warning("No analysis results available")
        return
    
    # Display synthesis first
    synthesis = analysis_result.get('synthesis', {})
    if synthesis and not synthesis.get('error'):
        st.subheader("🎯 Executive Summary")
        with st.container():
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #faf8f3 0%, #f5f1e8 100%);
                padding: 1.5rem;
                border-radius: 12px;
                border-left: 4px solid #2d5016;
                margin-bottom: 1rem;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            ">
                <div style="color: #2d5016; line-height: 1.6;">
                    {synthesis.get('analysis', 'No synthesis available')}
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Display individual analyses
    individual_analyses = analysis_result.get('individual_analyses', {})
    if individual_analyses:
        st.subheader("📊 Detailed Analysis")
        
        for analysis_type, result in individual_analyses.items():
            if not result.get('error'):
                with st.expander(f"{analysis_type.replace('_', ' ').title()} Analysis"):
                    st.markdown(result.get('analysis', 'No analysis available'))
    
    # Display recommendations
    recommendations = analysis_result.get('recommendations', [])
    if recommendations:
        st.subheader("💡 Recommendations")
        for i, rec in enumerate(recommendations[:5]):  # Show top 5
            st.info(f"**{rec['type'].replace('_', ' ').title()}**: {rec['text'][:200]}...")
    
    # Display action items
    action_items = analysis_result.get('action_items', [])
    if action_items:
        st.subheader("✅ Action Items")
        
        for item in action_items:
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.write(f"• {item['action']}")
            with col2:
                st.write(f"⏱️ {item['timeframe']}")
            with col3:
                st.write(f"👤 {item['responsible']}")

if __name__ == "__main__":
    # Test the enhanced analyzer
    analyzer = EnhancedTrafficAnalyzer()
    
    test_incident = {
        'id': 'test_123',
        'description': 'Vehicle accident on I-95',
        'location': 'Providence',
        'severity': 3,
        'timestamp': datetime.now()
    }
    
    # Test comprehensive analysis
    import asyncio
    result = asyncio.run(
        analyzer.comprehensive_analysis(
            test_incident,
            [AnalysisType.IMMEDIATE_RESPONSE, AnalysisType.PLANNING_INSIGHTS]
        )
    )
    
    print("Analysis completed successfully!")
    print(f"Analysis types: {result['analysis_types']}")
    print(f"Recommendations: {len(result['recommendations'])}")
    print(f"Action items: {len(result['action_items'])}")