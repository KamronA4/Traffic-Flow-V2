# utils/ai_cost_manager.py - Token monitoring and cost management for AI APIs

import streamlit as st
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, Any
from pathlib import Path
import sqlite3

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AICostManager:
    """Manage AI API costs with monitoring and caps"""
    
    # Perplexity pricing (as of 2025)
    PRICING = {
        'llama-3.1-sonar-small-128k-online': {
            'per_1k_requests': 5.00,
            'per_1m_input_tokens': 0.20,
            'per_1m_output_tokens': 0.20
        },
        'llama-3.1-sonar-large-128k-online': {
            'per_1k_requests': 5.00,
            'per_1m_input_tokens': 1.00,
            'per_1m_output_tokens': 1.00
        },
        'llama-3.1-sonar-huge-128k-online': {
            'per_1k_requests': 5.00,
            'per_1m_input_tokens': 5.00,
            'per_1m_output_tokens': 5.00
        }
    }
    
    def __init__(self, 
                 max_daily_cost: float = 5.00,
                 max_monthly_cost: float = 50.00,
                 max_tokens_per_request: int = 2000,
                 alert_threshold: float = 0.8):
        """
        Initialize cost manager with limits
        
        Args:
            max_daily_cost: Maximum daily spend in USD
            max_monthly_cost: Maximum monthly spend in USD
            max_tokens_per_request: Maximum tokens per single request
            alert_threshold: Alert when usage reaches this percentage (0.8 = 80%)
        """
        self.max_daily_cost = max_daily_cost
        self.max_monthly_cost = max_monthly_cost
        self.max_tokens_per_request = max_tokens_per_request
        self.alert_threshold = alert_threshold
        
        # Initialize or load usage database
        self.db_path = Path("data/ai_usage.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        
    def _init_database(self):
        """Initialize database for tracking usage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                model TEXT,
                prompt_tokens INTEGER,
                completion_tokens INTEGER,
                total_tokens INTEGER,
                expected_tokens INTEGER,
                token_inflation_ratio REAL,
                cost REAL,
                request_type TEXT,
                incident_id TEXT,
                error BOOLEAN DEFAULT 0
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cost_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                alert_type TEXT,
                message TEXT,
                cost_at_alert REAL,
                threshold_exceeded REAL
            )
        """)
        
        conn.commit()
        conn.close()
    
    def check_cost_limits(self) -> Tuple[bool, str]:
        """
        Check if current usage is within limits
        
        Returns:
            Tuple of (is_within_limits, message)
        """
        daily_cost = self.get_daily_cost()
        monthly_cost = self.get_monthly_cost()
        
        # Check hard limits
        if daily_cost >= self.max_daily_cost:
            return False, f"Daily cost limit reached: ${daily_cost:.2f} / ${self.max_daily_cost:.2f}"
        
        if monthly_cost >= self.max_monthly_cost:
            return False, f"Monthly cost limit reached: ${monthly_cost:.2f} / ${self.max_monthly_cost:.2f}"
        
        # Check alert thresholds
        if daily_cost >= self.max_daily_cost * self.alert_threshold:
            self._log_alert('daily_threshold', daily_cost, self.max_daily_cost * self.alert_threshold)
            message = f"⚠️ Daily cost at {(daily_cost/self.max_daily_cost)*100:.0f}%: ${daily_cost:.2f}"
            return True, message
        
        if monthly_cost >= self.max_monthly_cost * self.alert_threshold:
            self._log_alert('monthly_threshold', monthly_cost, self.max_monthly_cost * self.alert_threshold)
            message = f"⚠️ Monthly cost at {(monthly_cost/self.max_monthly_cost)*100:.0f}%: ${monthly_cost:.2f}"
            return True, message
        
        return True, f"Within limits: ${daily_cost:.2f} today, ${monthly_cost:.2f} this month"
    
    def track_usage(self, 
                   prompt: str,
                   response: Dict[str, Any],
                   model: str,
                   incident_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Track API usage and detect token inflation
        
        Args:
            prompt: The prompt sent to API
            response: The API response with usage data
            model: Model name used
            incident_id: Optional incident ID for tracking
            
        Returns:
            Usage statistics and warnings
        """
        # Calculate expected tokens (rough estimate)
        expected_input = len(prompt.split()) * 1.3  # 1.3 tokens per word average
        expected_output = 300  # Expected response size
        expected_total = expected_input + expected_output
        
        # Get actual usage from response
        usage = response.get('usage', {})
        actual_input = usage.get('prompt_tokens', 0)
        actual_output = usage.get('completion_tokens', 0)
        actual_total = usage.get('total_tokens', 0)
        
        # Calculate inflation ratio
        inflation_ratio = actual_total / expected_total if expected_total > 0 else 1
        
        # Calculate cost
        cost = self.calculate_cost(model, actual_input, actual_output)
        
        # Log to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO ai_usage (
                model, prompt_tokens, completion_tokens, total_tokens,
                expected_tokens, token_inflation_ratio, cost, 
                request_type, incident_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            model, actual_input, actual_output, actual_total,
            expected_total, inflation_ratio, cost,
            'incident_analysis', incident_id
        ))
        
        conn.commit()
        conn.close()
        
        # Generate warnings
        warnings = []
        
        if inflation_ratio > 10:
            warnings.append(f"🔴 Extreme token inflation: {inflation_ratio:.1f}x expected!")
            logger.warning(f"Token inflation {inflation_ratio:.1f}x for incident {incident_id}")
        elif inflation_ratio > 5:
            warnings.append(f"🟡 High token inflation: {inflation_ratio:.1f}x expected")
            logger.info(f"Token inflation {inflation_ratio:.1f}x for incident {incident_id}")
        
        if actual_total > self.max_tokens_per_request:
            warnings.append(f"⚠️ Exceeded token limit: {actual_total} > {self.max_tokens_per_request}")
        
        # Check cost limits
        within_limits, limit_message = self.check_cost_limits()
        if not within_limits:
            warnings.append(f"🚫 {limit_message}")
        elif "⚠️" in limit_message:
            warnings.append(limit_message)
        
        return {
            'expected_tokens': expected_total,
            'actual_tokens': actual_total,
            'inflation_ratio': inflation_ratio,
            'cost': cost,
            'warnings': warnings,
            'within_limits': within_limits
        }
    
    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for a request"""
        pricing = self.PRICING.get(model, self.PRICING['llama-3.1-sonar-small-128k-online'])
        
        # Request fee (per 1000 requests)
        request_cost = pricing['per_1k_requests'] / 1000
        
        # Token costs (per million tokens)
        input_cost = (input_tokens / 1_000_000) * pricing['per_1m_input_tokens']
        output_cost = (output_tokens / 1_000_000) * pricing['per_1m_output_tokens']
        
        return request_cost + input_cost + output_cost
    
    def get_daily_cost(self) -> float:
        """Get total cost for today"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        today = datetime.now().date()
        cursor.execute("""
            SELECT SUM(cost) FROM ai_usage 
            WHERE DATE(timestamp) = DATE(?)
        """, (today,))
        
        result = cursor.fetchone()[0]
        conn.close()
        
        return result if result else 0.0
    
    def get_monthly_cost(self) -> float:
        """Get total cost for current month"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        current_month = datetime.now().strftime('%Y-%m')
        cursor.execute("""
            SELECT SUM(cost) FROM ai_usage 
            WHERE strftime('%Y-%m', timestamp) = ?
        """, (current_month,))
        
        result = cursor.fetchone()[0]
        conn.close()
        
        return result if result else 0.0
    
    def get_usage_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get usage statistics for the last N days"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        since_date = datetime.now() - timedelta(days=days)
        
        # Get summary stats
        cursor.execute("""
            SELECT 
                COUNT(*) as total_requests,
                SUM(total_tokens) as total_tokens,
                AVG(token_inflation_ratio) as avg_inflation,
                MAX(token_inflation_ratio) as max_inflation,
                SUM(cost) as total_cost,
                AVG(cost) as avg_cost
            FROM ai_usage 
            WHERE timestamp >= ?
        """, (since_date,))
        
        stats = cursor.fetchone()
        
        # Get daily breakdown
        cursor.execute("""
            SELECT 
                DATE(timestamp) as date,
                COUNT(*) as requests,
                SUM(total_tokens) as tokens,
                SUM(cost) as cost
            FROM ai_usage 
            WHERE timestamp >= ?
            GROUP BY DATE(timestamp)
            ORDER BY date DESC
        """, (since_date,))
        
        daily_data = cursor.fetchall()
        
        conn.close()
        
        return {
            'total_requests': stats[0] or 0,
            'total_tokens': stats[1] or 0,
            'avg_inflation': stats[2] or 1.0,
            'max_inflation': stats[3] or 1.0,
            'total_cost': stats[4] or 0.0,
            'avg_cost': stats[5] or 0.0,
            'daily_breakdown': [
                {'date': row[0], 'requests': row[1], 'tokens': row[2], 'cost': row[3]}
                for row in daily_data
            ]
        }
    
    def _log_alert(self, alert_type: str, current_cost: float, threshold: float):
        """Log cost alert to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        message = f"{alert_type}: ${current_cost:.2f} exceeds threshold ${threshold:.2f}"
        
        cursor.execute("""
            INSERT INTO cost_alerts (alert_type, message, cost_at_alert, threshold_exceeded)
            VALUES (?, ?, ?, ?)
        """, (alert_type, message, current_cost, threshold))
        
        conn.commit()
        conn.close()
    
    def should_use_cache(self, incident_id: str) -> bool:
        """
        Determine if we should use cached response based on cost limits
        
        Args:
            incident_id: Incident identifier
            
        Returns:
            True if cache should be used, False otherwise
        """
        # Always use cache if over daily limit
        daily_cost = self.get_daily_cost()
        if daily_cost >= self.max_daily_cost * 0.9:  # 90% of daily limit
            logger.info(f"Using cache due to cost limits: ${daily_cost:.2f}")
            return True
        
        # Check if this incident was recently analyzed
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT timestamp FROM ai_usage 
            WHERE incident_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (incident_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            last_analysis = datetime.fromisoformat(result[0])
            if datetime.now() - last_analysis < timedelta(hours=24):
                logger.info(f"Using cache for incident {incident_id} (analyzed {last_analysis})")
                return True
        
        return False


# Streamlit integration functions
def display_cost_metrics():
    """Display cost metrics in Streamlit sidebar"""
    manager = AICostManager()
    
    with st.sidebar:
        st.markdown("### 💰 AI Usage & Costs")
        
        # Current costs
        daily_cost = manager.get_daily_cost()
        monthly_cost = manager.get_monthly_cost()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Today", f"${daily_cost:.2f}", 
                     delta=f"/{manager.max_daily_cost:.0f}")
        with col2:
            st.metric("This Month", f"${monthly_cost:.2f}",
                     delta=f"/{manager.max_monthly_cost:.0f}")
        
        # Progress bars
        daily_progress = min(daily_cost / manager.max_daily_cost, 1.0)
        monthly_progress = min(monthly_cost / manager.max_monthly_cost, 1.0)
        
        st.progress(daily_progress, text=f"Daily: {daily_progress*100:.0f}%")
        st.progress(monthly_progress, text=f"Monthly: {monthly_progress*100:.0f}%")
        
        # Stats
        stats = manager.get_usage_stats(days=7)
        
        with st.expander("📊 7-Day Statistics"):
            st.write(f"**Total Requests:** {stats['total_requests']}")
            st.write(f"**Total Cost:** ${stats['total_cost']:.2f}")
            st.write(f"**Avg Cost/Request:** ${stats['avg_cost']:.3f}")
            st.write(f"**Avg Token Inflation:** {stats['avg_inflation']:.1f}x")
            st.write(f"**Max Token Inflation:** {stats['max_inflation']:.1f}x")
        
        # Warnings
        within_limits, message = manager.check_cost_limits()
        if not within_limits:
            st.error(message)
        elif "⚠️" in message:
            st.warning(message)


def get_cost_safe_analysis(incident: Dict[str, Any], analyzer: Any) -> Dict[str, Any]:
    """
    Wrapper for AI analysis with cost protection
    
    Args:
        incident: Incident data
        analyzer: TrafficAnalyzer instance
        
    Returns:
        Analysis results or cached/mock data if over limits
    """
    manager = AICostManager()
    incident_id = incident.get('id', str(hash(str(incident))))
    
    # Check if we should use cache
    if manager.should_use_cache(incident_id):
        logger.info(f"Using cached analysis for incident {incident_id}")
        return analyzer._get_mock_analysis(incident)
    
    # Check cost limits
    within_limits, message = manager.check_cost_limits()
    if not within_limits:
        logger.warning(f"Cost limit exceeded: {message}")
        st.warning(f"AI analysis disabled: {message}")
        return analyzer._get_mock_analysis(incident)
    
    # Proceed with actual API call
    try:
        analysis = analyzer.analyze_incident(incident)
        
        # Track usage if response includes it
        if 'usage' in analysis:
            usage_stats = manager.track_usage(
                prompt=str(incident),  # Simplified for tracking
                response=analysis,
                model='llama-3.1-sonar-small-128k-online',
                incident_id=incident_id
            )
            
            # Add warnings to analysis
            if usage_stats['warnings']:
                analysis['cost_warnings'] = usage_stats['warnings']
                for warning in usage_stats['warnings']:
                    logger.warning(warning)
        
        return analysis
        
    except Exception as e:
        logger.error(f"API call failed: {e}")
        return analyzer._get_mock_analysis(incident)