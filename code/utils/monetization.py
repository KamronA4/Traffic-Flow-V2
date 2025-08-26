# utils/monetization.py - Monetization integrations for ads and donations

import streamlit as st
import streamlit.components.v1 as components
import yaml
from pathlib import Path
from typing import Dict, Optional, List
import hashlib
import json

class MonetizationManager:
    """Manage ads, donations, and monetization features"""
    
    def __init__(self):
        self.config = self._load_config()
        self.user_tier = self._get_user_tier()
        
    def _load_config(self) -> Dict:
        """Load monetization configuration"""
        config_path = Path(__file__).parent.parent.parent / 'config' / 'monetization_config.yaml'
        if config_path.exists():
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        return {}
    
    def _get_user_tier(self) -> str:
        """Get current user's subscription tier"""
        # Check if user is authenticated and get their tier
        if 'user' in st.session_state and st.session_state.user:
            if 'organization' in st.session_state:
                return st.session_state.organization.get('subscription_tier', 'free')
        return 'free'
    
    def should_show_ads(self) -> bool:
        """Check if ads should be shown for current user"""
        if not self.config.get('monetization', {}).get('adsense', {}).get('enabled', False):
            return False
        
        # Only show ads to free tier users
        show_for_tiers = self.config.get('monetization', {}).get('adsense', {}).get('show_for_tiers', ['free'])
        return self.user_tier in show_for_tiers
    
    def render_adsense_ad(self, slot_type: str = 'header_banner', page: str = 'home'):
        """Render Google AdSense advertisement"""
        if not self.should_show_ads():
            return
            
        adsense_config = self.config.get('monetization', {}).get('adsense', {})
        if not adsense_config:
            return
            
        publisher_id = adsense_config.get('publisher_id')
        ad_slot = adsense_config.get('ad_slots', {}).get(slot_type, {})
        
        # Check if this ad should show on current page
        allowed_pages = ad_slot.get('pages', [])
        if 'all' not in allowed_pages and page not in allowed_pages:
            return
            
        slot_id = ad_slot.get('slot_id')
        size = ad_slot.get('size', 'responsive')
        
        if publisher_id and slot_id:
            # Create unique key for this ad placement
            ad_key = hashlib.md5(f"{slot_type}_{page}_{slot_id}".encode()).hexdigest()[:8]
            
            # Inject AdSense code
            adsense_html = f"""
            <div class="adsense-container" style="margin: 10px 0; text-align: center;">
                <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js"></script>
                <ins class="adsbygoogle"
                     style="display:block"
                     data-ad-client="{publisher_id}"
                     data-ad-slot="{slot_id}"
                     data-ad-format="auto"
                     data-full-width-responsive="true"></ins>
                <script>
                     (adsbygoogle = window.adsbygoogle || []).push({{}});
                </script>
            </div>
            """
            
            components.html(adsense_html, height=100 if size == '728x90' else 280)
    
    def render_buymeacoffee_widget(self):
        """Render Buy Me a Coffee donation widget"""
        bmc_config = self.config.get('monetization', {}).get('buymeacoffee', {})
        
        if not bmc_config.get('enabled', False):
            return
            
        username = bmc_config.get('username')
        if not username:
            return
            
        button_text = bmc_config.get('button_text', 'Buy me a coffee')
        button_color = bmc_config.get('button_color', '#FFDD00')
        message = bmc_config.get('message', '')
        
        # Buy Me a Coffee widget
        bmc_html = f"""
        <script data-name="BMC-Widget" 
                data-cfasync="false" 
                src="https://cdnjs.buymeacoffee.com/1.0.0/widget.prod.min.js" 
                data-id="{username}" 
                data-description="{message}"
                data-color="{button_color}"
                data-position="Right" 
                data-x_margin="18" 
                data-y_margin="18">
        </script>
        """
        
        components.html(bmc_html, height=0)
    
    def render_buymeacoffee_button(self):
        """Render Buy Me a Coffee button"""
        bmc_config = self.config.get('monetization', {}).get('buymeacoffee', {})
        
        if not bmc_config.get('enabled', False):
            return
            
        username = bmc_config.get('username')
        if not username:
            return
            
        button_text = bmc_config.get('button_text', 'Buy me a coffee')
        
        # Create Buy Me a Coffee button
        bmc_button_html = f"""
        <a href="https://www.buymeacoffee.com/{username}" target="_blank">
            <img src="https://cdn.buymeacoffee.com/buttons/v2/default-green.png" 
                 alt="{button_text}" 
                 style="height: 40px !important; width: 145px !important;">
        </a>
        """
        
        st.markdown(bmc_button_html, unsafe_allow_html=True)
    
    def check_feature_limit(self, feature: str) -> bool:
        """Check if user has reached limit for a feature"""
        if self.user_tier != 'free':
            return False
            
        limits = self.config.get('monetization', {}).get('free_tier', {})
        
        # Get current usage from session state or database
        usage = st.session_state.get('feature_usage', {})
        
        if feature == 'incidents':
            current = usage.get('incidents_this_month', 0)
            limit = limits.get('incidents_per_month', 1000)
            return current >= limit
            
        elif feature == 'reports':
            current = usage.get('reports_this_month', 0)
            limit = limits.get('reports_per_month', 3)
            return current >= limit
            
        elif feature == 'api_calls':
            current = usage.get('api_calls_today', 0)
            limit = limits.get('api_calls_per_day', 100)
            return current >= limit
            
        return False
    
    def show_upgrade_prompt(self, reason: str = 'limit_reached'):
        """Show upgrade prompt to user"""
        if self.user_tier != 'free':
            return
            
        messages = {
            'limit_reached': "🚫 You've reached your free tier limit. Upgrade to Pro for unlimited access!",
            'feature_locked': "🔒 This feature is available in Pro tier. Upgrade to unlock!",
            'trial_expired': "⏰ Your trial has expired. Upgrade to continue using Village!"
        }
        
        benefits = self.config.get('monetization', {}).get('paywall', {}).get('upgrade_benefits', [])
        
        with st.container():
            st.warning(messages.get(reason, messages['limit_reached']))
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### Upgrade to Pro")
                for benefit in benefits:
                    st.markdown(benefit)
                    
            with col2:
                st.markdown("### Special Offer")
                st.markdown("🎉 **50% off** for the first 3 months!")
                st.markdown("Only **$24.50/month** (normally $49)")
                
                if st.button("Upgrade Now", type="primary", key="upgrade_prompt"):
                    st.session_state['show_pricing'] = True
                    st.switch_page("pages/pricing")
    
    def track_revenue_event(self, event_type: str, details: Dict = None):
        """Track revenue-related events"""
        if not self.config.get('monetization', {}).get('analytics', {}).get('internal_tracking', {}).get('enabled', False):
            return
            
        # Store event in session state (in production, send to analytics service)
        if 'revenue_events' not in st.session_state:
            st.session_state['revenue_events'] = []
            
        event = {
            'type': event_type,
            'timestamp': st.session_state.get('current_time', ''),
            'user_tier': self.user_tier,
            'details': details or {}
        }
        
        st.session_state['revenue_events'].append(event)
    
    def render_google_analytics(self):
        """Render Google Analytics tracking code"""
        ga_config = self.config.get('monetization', {}).get('analytics', {}).get('google_analytics', {})
        
        if not ga_config.get('enabled', False):
            return
            
        measurement_id = ga_config.get('measurement_id')
        if not measurement_id:
            return
            
        ga_script = f"""
        <!-- Google Analytics -->
        <script async src="https://www.googletagmanager.com/gtag/js?id={measurement_id}"></script>
        <script>
          window.dataLayer = window.dataLayer || [];
          function gtag(){{dataLayer.push(arguments);}}
          gtag('js', new Date());
          gtag('config', '{measurement_id}');
        </script>
        """
        
        components.html(ga_script, height=0)


# Utility functions for easy integration
def show_ads(position: str = 'header', page: str = 'home'):
    """Quick function to show ads in Streamlit pages"""
    manager = MonetizationManager()
    manager.render_adsense_ad(position, page)

def show_donation_button():
    """Quick function to show donation button"""
    manager = MonetizationManager()
    manager.render_buymeacoffee_button()

def show_donation_widget():
    """Quick function to show donation widget"""
    manager = MonetizationManager()
    manager.render_buymeacoffee_widget()

def check_limit(feature: str) -> bool:
    """Quick function to check feature limits"""
    manager = MonetizationManager()
    return manager.check_feature_limit(feature)

def prompt_upgrade(reason: str = 'limit_reached'):
    """Quick function to show upgrade prompt"""
    manager = MonetizationManager()
    manager.show_upgrade_prompt(reason)

def init_analytics():
    """Initialize analytics tracking"""
    manager = MonetizationManager()
    manager.render_google_analytics()