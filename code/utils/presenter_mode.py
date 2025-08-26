# utils/presenter_mode.py - Presenter Mode Utilities

import streamlit as st
import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class PresenterMode:
    """Manage presenter mode features and controls"""
    
    def __init__(self):
        self.demo_mode = os.getenv('VILLAGE_DEMO_MODE', 'false').lower() == 'true'
        self.presenter_mode = st.session_state.get('presenter_mode', False)
    
    def is_presenter_mode(self) -> bool:
        """Check if presenter mode is active"""
        return self.presenter_mode and self.demo_mode
    
    def toggle_presenter_mode(self):
        """Toggle presenter mode on/off"""
        if self.demo_mode:
            st.session_state['presenter_mode'] = not st.session_state.get('presenter_mode', False)
            self.presenter_mode = st.session_state['presenter_mode']
            
            if self.presenter_mode:
                st.success("🎯 Presenter Mode Activated")
                st.info("Additional controls and shortcuts are now available.")
            else:
                st.info("👤 Presenter Mode Deactivated")
        else:
            st.error("Presenter mode requires VILLAGE_DEMO_MODE=true")
    
    def show_presenter_toggle(self):
        """Show presenter mode toggle in sidebar"""
        if not self.demo_mode:
            return
        
        with st.sidebar:
            st.markdown("---")
            st.markdown("### 🎯 Presenter Mode")
            
            current_status = st.session_state.get('presenter_mode', False)
            
            if st.button("🎮 Toggle Presenter Mode", key="presenter_toggle"):
                self.toggle_presenter_mode()
                st.rerun()
            
            if current_status:
                st.success("Active")
                st.caption("Enhanced controls available")
            else:
                st.info("Inactive")
                st.caption("Click to activate demo features")
    
    def show_quick_controls(self):
        """Show quick presenter controls when in presenter mode"""
        if not self.is_presenter_mode():
            return
        
        with st.sidebar:
            st.markdown("### ⚡ Quick Controls")
            
            # Quick data refresh
            if st.button("🔄 Refresh Data", key="quick_refresh"):
                st.cache_data.clear()
                st.success("Data refreshed!")
                st.rerun()
            
            # Quick scenario switch
            scenario = st.selectbox(
                "Quick Scenario",
                ["Current", "Rush Hour", "Weather Event", "Normal"],
                key="quick_scenario"
            )
            
            if st.button("🎬 Load Scenario", key="load_quick_scenario"):
                if scenario != "Current":
                    try:
                        from pages.demo_controls import load_demo_scenario
                        scenarios = {
                            "Rush Hour": {
                                "incidents": 5,
                                "congestion": "high",
                                "locations": ["I-95", "Route 195", "Downtown"]
                            },
                            "Weather Event": {
                                "incidents": 7,
                                "congestion": "severe", 
                                "locations": ["Multiple"]
                            },
                            "Normal": {
                                "incidents": 1,
                                "congestion": "low",
                                "locations": ["Random"]
                            }
                        }
                        load_demo_scenario(scenario, scenarios[scenario])
                        st.success(f"Loaded {scenario} scenario!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error loading scenario: {e}")
    
    def show_presenter_tips(self, page_name: str):
        """Show context-sensitive presenter tips"""
        if not self.is_presenter_mode():
            return
        
        tips = self._get_page_tips(page_name)
        
        if tips:
            with st.expander("💡 Presenter Tips", expanded=False):
                for tip in tips:
                    st.markdown(f"• {tip}")
    
    def _get_page_tips(self, page_name: str) -> list:
        """Get presenter tips for specific pages"""
        tips_map = {
            "Live Traffic": [
                "Click on incident markers to show AI analysis",
                "Use date/time filters to show historical patterns",
                "Switch map styles to demonstrate flexibility",
                "Highlight the real-time data refresh capability"
            ],
            "Analytics": [
                "Show trend analysis over different time periods",
                "Demonstrate predictive capabilities",
                "Highlight cost-benefit analysis features",
                "Show data export capabilities"
            ],
            "Planning": [
                "Demonstrate scenario planning tools",
                "Show infrastructure impact analysis",
                "Highlight budget allocation features",
                "Show integration with municipal systems"
            ],
            "Reports": [
                "Generate sample reports for different audiences",
                "Show automated scheduling capabilities",
                "Demonstrate data visualization options",
                "Highlight compliance reporting features"
            ]
        }
        
        return tips_map.get(page_name, [])
    
    def add_presenter_shortcuts(self):
        """Add keyboard shortcuts for presenters"""
        if not self.is_presenter_mode():
            return
        
        # Add JavaScript for keyboard shortcuts
        st.markdown("""
        <script>
        document.addEventListener('keydown', function(event) {
            // Ctrl+R: Refresh data
            if (event.ctrlKey && event.key === 'r') {
                event.preventDefault();
                // Trigger refresh
                window.parent.postMessage({type: 'presenter_refresh'}, '*');
            }
            
            // Ctrl+1-4: Quick scenarios
            if (event.ctrlKey && ['1', '2', '3', '4'].includes(event.key)) {
                event.preventDefault();
                const scenarios = ['Normal', 'Rush Hour', 'Weather Event', 'Custom'];
                const scenario = scenarios[parseInt(event.key) - 1];
                window.parent.postMessage({type: 'load_scenario', scenario: scenario}, '*');
            }
        });
        </script>
        """, unsafe_allow_html=True)
    
    def show_presenter_status(self):
        """Show presenter mode status and shortcuts"""
        if not self.is_presenter_mode():
            return
        
        # Show status in a compact format
        with st.container():
            st.markdown("""
            <div style="position: fixed; top: 10px; right: 10px; 
                        background: rgba(0,0,0,0.8); color: white; 
                        padding: 8px 12px; border-radius: 6px; 
                        font-size: 12px; z-index: 999;">
                🎯 PRESENTER MODE
            </div>
            """, unsafe_allow_html=True)
    
    def get_demo_metrics(self) -> Dict[str, Any]:
        """Get current demo metrics for presenter dashboard"""
        try:
            from utils.data_sync import get_traffic_data
            
            data = get_traffic_data()
            
            if data.empty:
                return {
                    "total_incidents": 0,
                    "high_severity": 0,
                    "active_locations": 0,
                    "avg_severity": 0,
                    "last_updated": "No data"
                }
            
            return {
                "total_incidents": len(data),
                "high_severity": len(data[data['severity'] > 3]),
                "active_locations": data['location'].nunique(),
                "avg_severity": round(data['severity'].mean(), 1),
                "last_updated": "Live"
            }
            
        except Exception as e:
            logger.error(f"Error getting demo metrics: {e}")
            return {
                "total_incidents": "Error",
                "high_severity": "Error", 
                "active_locations": "Error",
                "avg_severity": "Error",
                "last_updated": "Error"
            }

# Global presenter mode instance
presenter_mode = PresenterMode()

def show_presenter_controls():
    """Convenience function to show all presenter controls"""
    presenter_mode.show_presenter_toggle()
    presenter_mode.show_quick_controls()
    presenter_mode.show_presenter_status()
    presenter_mode.add_presenter_shortcuts()

def is_presenter_mode() -> bool:
    """Convenience function to check presenter mode"""
    return presenter_mode.is_presenter_mode()

def show_page_tips(page_name: str):
    """Convenience function to show page-specific tips"""
    presenter_mode.show_presenter_tips(page_name)