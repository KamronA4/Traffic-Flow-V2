# utils/pricing_tiers.py - Pricing Tiers and Subscription Management

import streamlit as st
import pandas as pd
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import json
from datetime import datetime, timedelta

class PricingTier(Enum):
    """Pricing tier definitions"""
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"

@dataclass
class PricingPlan:
    """Pricing plan structure"""
    tier: PricingTier
    name: str
    price_monthly: int
    price_annual: int
    description: str
    features: List[str]
    limits: Dict[str, Any]
    popular: bool = False
    
class PricingManager:
    """Manage pricing tiers and subscription features"""
    
    def __init__(self):
        self.plans = self._initialize_plans()
    
    def _initialize_plans(self) -> Dict[PricingTier, PricingPlan]:
        """Initialize pricing plans"""
        return {
            PricingTier.FREE: PricingPlan(
                tier=PricingTier.FREE,
                name="Free",
                price_monthly=0,
                price_annual=0,
                description="Perfect for getting started with traffic monitoring",
                features=[
                    "Real-time traffic monitoring",
                    "Basic incident reporting",
                    "Standard analytics dashboard",
                    "Email notifications",
                    "CSV data export",
                    "Community support",
                    "Basic visualizations"
                ],
                limits={
                    "users": 2,
                    "api_calls_monthly": 1000,
                    "data_retention_months": 3,
                    "incidents_per_month": 1000,
                    "custom_reports": 1,
                    "support_level": "community"
                }
            ),
            
            PricingTier.STARTER: PricingPlan(
                tier=PricingTier.STARTER,
                name="Starter",
                price_monthly=79,
                price_annual=790,
                description="Essential features for small to medium municipalities",
                features=[
                    "Everything in Free",
                    "Basic AI incident analysis",
                    "Predictive insights",
                    "Advanced filtering",
                    "Priority email support",
                    "Extended data retention (12 months)",
                    "Custom dashboard"
                ],
                limits={
                    "users": 5,
                    "api_calls_monthly": 5000,
                    "data_retention_months": 12,
                    "incidents_per_month": 5000,
                    "custom_reports": 5,
                    "support_level": "email"
                }
            ),
            
            PricingTier.PRO: PricingPlan(
                tier=PricingTier.PRO,
                name="Pro",
                price_monthly=199,
                price_annual=1990,
                description="Advanced features for growing municipalities",
                features=[
                    "Everything in Starter",
                    "Advanced AI analysis with municipal context",
                    "Predictive analytics and forecasting",
                    "Custom reporting tools",
                    "API integrations",
                    "Multi-department access",
                    "Historical trend analysis",
                    "3D visualizations",
                    "Real-time alerts",
                    "Priority support"
                ],
                limits={
                    "users": 15,
                    "api_calls_monthly": 25000,
                    "data_retention_months": 36,
                    "incidents_per_month": 25000,
                    "custom_reports": 50,
                    "support_level": "priority"
                },
                popular=True
            ),
            
            PricingTier.ENTERPRISE: PricingPlan(
                tier=PricingTier.ENTERPRISE,
                name="Enterprise",
                price_monthly=0,  # Custom pricing
                price_annual=0,   # Custom pricing
                description="Complete solution for large municipalities and regions",
                features=[
                    "Everything in Pro",
                    "Custom feature selection (à la carte)",
                    "Multi-municipality management",
                    "Advanced IoT integration",
                    "Custom AI models",
                    "White-label options",
                    "SSO integration",
                    "Dedicated support",
                    "Custom integrations",
                    "Advanced compliance features",
                    "On-site training",
                    "Custom SLAs"
                ],
                limits={
                    "users": -1,  # unlimited
                    "api_calls_monthly": -1,  # unlimited
                    "data_retention_months": -1,  # unlimited
                    "incidents_per_month": -1,  # unlimited
                    "custom_reports": -1,  # unlimited
                    "support_level": "dedicated"
                }
            )
        }
    
    def get_plan(self, tier: PricingTier) -> PricingPlan:
        """Get pricing plan by tier"""
        return self.plans.get(tier)
    
    def get_all_plans(self) -> List[PricingPlan]:
        """Get all pricing plans"""
        return list(self.plans.values())
    
    def calculate_savings(self, plan: PricingPlan) -> int:
        """Calculate annual savings percentage"""
        monthly_annual = plan.price_monthly * 12
        return int(((monthly_annual - plan.price_annual) / monthly_annual) * 100)

def show_pricing_page():
    """Display comprehensive pricing page"""
    st.markdown("""
    <div style="
        text-align: center;
        padding: 3rem 0;
        background: linear-gradient(135deg, #faf8f3 0%, #f5f1e8 100%);
        border-radius: 15px;
        margin-bottom: 2rem;
    ">
        <h1 style="color: #2d5016; margin-bottom: 1rem;">Village Pricing Plans</h1>
        <p style="color: #5a7c47; font-size: 1.2rem; margin-bottom: 2rem;">
            Choose the perfect plan for your municipality
        </p>
        <div style="display: flex; justify-content: center; gap: 1rem;">
            <div style="
                background: white;
                padding: 0.5rem 1rem;
                border-radius: 25px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            ">
                <span style="color: #2d5016; font-weight: 600;">✓ 30-day free trial</span>
            </div>
            <div style="
                background: white;
                padding: 0.5rem 1rem;
                border-radius: 25px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            ">
                <span style="color: #2d5016; font-weight: 600;">✓ No setup fees</span>
            </div>
            <div style="
                background: white;
                padding: 0.5rem 1rem;
                border-radius: 25px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            ">
                <span style="color: #2d5016; font-weight: 600;">✓ Cancel anytime</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Billing toggle
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        billing_cycle = st.radio(
            "Billing Cycle",
            ["Monthly", "Annual"],
            index=1,
            horizontal=True,
            help="Annual billing offers significant savings"
        )
    
    pricing_manager = PricingManager()
    plans = pricing_manager.get_all_plans()
    
    # Create pricing cards
    cols = st.columns(len(plans))
    
    for i, plan in enumerate(plans):
        with cols[i]:
            # Determine if this is the popular plan
            card_style = """
            background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
            border-radius: 15px;
            padding: 2rem;
            margin-bottom: 1rem;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            position: relative;
            height: 100%;
            """
            
            if plan.popular:
                card_style += """
                border: 2px solid #2d5016;
                transform: scale(1.05);
                """
            
            st.markdown(f"""
            <div style="{card_style}">
            """, unsafe_allow_html=True)
            
            # Popular badge
            if plan.popular:
                st.markdown("""
                <div style="
                    background: #2d5016;
                    color: white;
                    padding: 0.5rem 1rem;
                    border-radius: 20px;
                    text-align: center;
                    font-weight: 600;
                    font-size: 0.9rem;
                    margin-bottom: 1rem;
                ">
                    MOST POPULAR
                </div>
                """, unsafe_allow_html=True)
            
            # Plan name and price
            st.markdown(f"""
            <h3 style="color: #2d5016; text-align: center; margin-bottom: 0.5rem;">
                {plan.name}
            </h3>
            """, unsafe_allow_html=True)
            
            # Price display
            if billing_cycle == "Monthly":
                price = plan.price_monthly
                price_text = f"${price:,}/month"
            else:
                price = plan.price_annual
                price_text = f"${price:,}/year"
                savings = pricing_manager.calculate_savings(plan)
                if savings > 0:
                    st.markdown(f"""
                    <div style="text-align: center; margin-bottom: 0.5rem;">
                        <span style="
                            background: #d4edda;
                            color: #155724;
                            padding: 0.25rem 0.5rem;
                            border-radius: 12px;
                            font-size: 0.8rem;
                            font-weight: 600;
                        ">
                            Save {savings}%
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style="text-align: center; margin-bottom: 1rem;">
                <span style="
                    font-size: 2.5rem;
                    font-weight: 700;
                    color: #2d5016;
                ">
                    {price_text}
                </span>
            </div>
            """, unsafe_allow_html=True)
            
            # Description
            st.markdown(f"""
            <p style="
                text-align: center;
                color: #5a7c47;
                margin-bottom: 2rem;
                font-size: 0.95rem;
            ">
                {plan.description}
            </p>
            """, unsafe_allow_html=True)
            
            # Features list
            st.markdown("**Features:**")
            for feature in plan.features:
                st.markdown(f"✓ {feature}")
            
            # Limits section
            st.markdown("**Limits:**")
            limits_text = []
            for key, value in plan.limits.items():
                if value == -1:
                    limits_text.append(f"• {key.replace('_', ' ').title()}: Unlimited")
                else:
                    limits_text.append(f"• {key.replace('_', ' ').title()}: {value:,}")
            
            for limit in limits_text:
                st.markdown(f"<small>{limit}</small>", unsafe_allow_html=True)
            
            # CTA Button
            button_style = "secondary"
            if plan.popular:
                button_style = "primary"
            
            if plan.tier == PricingTier.FREE:
                if st.button(f"Get Started Free", key=f"free_{plan.tier.value}", use_container_width=True):
                    show_signup_form(plan)
            elif plan.tier == PricingTier.ENTERPRISE:
                if st.button(f"Contact Sales", key=f"contact_{plan.tier.value}", use_container_width=True):
                    show_contact_form(plan)
            elif plan.tier == PricingTier.PRO:
                if st.button(f"Start 14-Day Free Trial", key=f"trial_{plan.tier.value}", use_container_width=True):
                    show_signup_form(plan, has_trial=True)
            else:
                if st.button(f"Get Started", key=f"start_{plan.tier.value}", use_container_width=True):
                    show_signup_form(plan)
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    # Feature comparison table
    st.markdown("---")
    st.subheader("📊 Feature Comparison")
    
    # Create comparison DataFrame
    comparison_data = []
    all_features = set()
    
    for plan in plans:
        all_features.update(plan.features)
    
    for feature in all_features:
        row = {"Feature": feature}
        for plan in plans:
            row[plan.name] = "✓" if feature in plan.features else "❌"
        comparison_data.append(row)
    
    comparison_df = pd.DataFrame(comparison_data)
    st.dataframe(comparison_df, use_container_width=True, hide_index=True)
    
    # FAQ Section
    st.markdown("---")
    st.subheader("🤔 Frequently Asked Questions")
    
    faqs = [
        {
            "question": "Is the Free plan really free?",
            "answer": "Yes! The Free plan is completely free with no hidden fees. You get 1,000 incidents/month, basic features, and community support. Perfect for small municipalities getting started."
        },
        {
            "question": "What happens after my Pro trial ends?",
            "answer": "Your 14-day Pro trial includes all Pro features with no credit card required. After the trial, you can choose to subscribe to Pro or downgrade to Free or Starter."
        },
        {
            "question": "Can I change my plan later?",
            "answer": "Yes! You can upgrade or downgrade your plan at any time. Changes take effect immediately, and billing is prorated."
        },
        {
            "question": "What happens if I exceed my incident limits?",
            "answer": "We'll notify you when you approach your limits. You can either upgrade your plan or purchase additional incidents at $0.10 per incident."
        },
        {
            "question": "How does Enterprise pricing work?",
            "answer": "Enterprise pricing is custom based on your specific needs. You can select à la carte features, unlimited incidents, and custom integrations. Contact sales for a personalized quote."
        },
        {
            "question": "Do you offer discounts for non-profits?",
            "answer": "Yes! We offer 50% discounts for verified non-profit organizations and educational institutions on all paid plans."
        },
        {
            "question": "What kind of support do you provide?",
            "answer": "Support levels vary by plan: Community (forums), Email (within 24h), Priority (email within 4h), Dedicated (phone + email within 1h)."
        }
    ]
    
    for faq in faqs:
        with st.expander(faq["question"]):
            st.write(faq["answer"])

def show_signup_form(plan: PricingPlan):
    """Show signup form for selected plan"""
    st.markdown("### Complete Your Signup")
    
    with st.form(f"signup_{plan.tier.value}"):
        st.markdown(f"**Selected Plan:** {plan.name} - ${plan.price_monthly:,}/month")
        
        col1, col2 = st.columns(2)
        with col1:
            org_name = st.text_input("Organization Name*", placeholder="City of Springfield")
            contact_name = st.text_input("Contact Name*", placeholder="John Smith")
            title = st.text_input("Title", placeholder="Traffic Engineer")
        
        with col2:
            email = st.text_input("Email Address*", placeholder="john.smith@springfield.gov")
            phone = st.text_input("Phone Number", placeholder="(555) 123-4567")
            population = st.number_input("Municipality Population", min_value=1000, value=50000)
        
        # Additional information
        st.markdown("**Tell us about your needs:**")
        current_solution = st.text_area("Current Traffic Management Solution", 
                                       placeholder="Describe your current system or challenges...")
        
        primary_goals = st.multiselect(
            "Primary Goals",
            ["Reduce traffic congestion", "Improve incident response", "Data-driven planning", 
             "Cost reduction", "Better reporting", "Public safety", "Environmental impact"]
        )
        
        # Terms and conditions
        agree_terms = st.checkbox("I agree to the Terms of Service and Privacy Policy*")
        
        if st.form_submit_button("Start Free Trial", use_container_width=True):
            if not all([org_name, contact_name, email, agree_terms]):
                st.error("Please fill in all required fields and agree to terms")
            else:
                # Here you would typically:
                # 1. Create organization in database
                # 2. Send welcome email
                # 3. Set up trial period
                # 4. Redirect to onboarding
                
                st.success("🎉 Welcome to Village!")
                st.balloons()
                st.markdown("""
                **Next Steps:**
                1. Check your email for login credentials
                2. Complete the onboarding process
                3. Import your first data set
                4. Schedule a demo call with our team
                """)

def show_contact_form(plan: PricingPlan):
    """Show contact form for custom/enterprise plans"""
    st.markdown("### Contact Our Sales Team")
    
    with st.form(f"contact_{plan.tier.value}"):
        st.markdown(f"**Interested in:** {plan.name}")
        
        col1, col2 = st.columns(2)
        with col1:
            contact_name = st.text_input("Name*", placeholder="John Smith")
            email = st.text_input("Email*", placeholder="john.smith@city.gov")
            org_name = st.text_input("Organization*", placeholder="City of Springfield")
        
        with col2:
            phone = st.text_input("Phone Number", placeholder="(555) 123-4567")
            title = st.text_input("Title", placeholder="Director of Transportation")
            budget = st.selectbox("Annual Budget Range", 
                                 ["$10K - $50K", "$50K - $100K", "$100K - $500K", "$500K+"])
        
        # Project details
        st.markdown("**Project Details:**")
        timeline = st.selectbox("Implementation Timeline", 
                               ["Immediately", "1-3 months", "3-6 months", "6+ months"])
        
        requirements = st.text_area("Specific Requirements", 
                                   placeholder="Tell us about your specific needs, integrations, or challenges...")
        
        if st.form_submit_button("Request Demo", use_container_width=True):
            if not all([contact_name, email, org_name]):
                st.error("Please fill in all required fields")
            else:
                st.success("📞 Demo Request Received!")
                st.markdown("""
                **What happens next:**
                1. Our sales team will contact you within 24 hours
                2. We'll schedule a personalized demo
                3. Discuss your specific requirements
                4. Provide a custom quote
                """)

def show_current_subscription():
    """Show current subscription information for authenticated users"""
    from .enterprise_auth import get_current_user
    
    user_org = get_current_user()
    if not user_org:
        return
    
    user, organization = user_org
    
    st.markdown("### Your Current Subscription")
    
    # Current plan info
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Current Plan", organization.tier.value.title())
    
    with col2:
        days_remaining = (organization.subscription_expires - datetime.now()).days
        st.metric("Days Remaining", days_remaining)
    
    with col3:
        st.metric("Users", f"{organization.max_users}")
    
    # Usage information
    from .enterprise_auth import EnterpriseAuthManager
    auth_manager = EnterpriseAuthManager()
    stats = auth_manager.get_organization_usage_stats(organization.id)
    
    if stats:
        st.markdown("### Usage This Month")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                "API Calls", 
                f"{stats['today_usage']:,}",
                f"{stats['quota_remaining']:,} remaining"
            )
        
        with col2:
            st.metric(
                "Active Users",
                stats['user_count'],
                f"{organization.max_users - stats['user_count']} available"
            )
        
        # Progress bars
        st.progress(stats['quota_usage_percent'] / 100)
        st.caption(f"API Usage: {stats['quota_usage_percent']:.1f}%")
    
    # Upgrade options
    if organization.tier != PricingTier.ENTERPRISE:
        st.markdown("### Upgrade Your Plan")
        pricing_manager = PricingManager()
        
        if organization.tier == PricingTier.FREE:
            next_plan = pricing_manager.get_plan(PricingTier.STARTER)
        elif organization.tier == PricingTier.STARTER:
            next_plan = pricing_manager.get_plan(PricingTier.PRO)
        elif organization.tier == PricingTier.PRO:
            next_plan = pricing_manager.get_plan(PricingTier.ENTERPRISE)
        else:
            next_plan = None
        
        if next_plan:
            col1, col2 = st.columns([3, 1])
            with col1:
                if next_plan.tier == PricingTier.ENTERPRISE:
                    st.write(f"**{next_plan.name}** - Custom Pricing")
                    st.write(f"✓ Unlimited users")
                    st.write(f"✓ Unlimited incidents")
                    st.write(f"✓ Custom features")
                else:
                    st.write(f"**{next_plan.name}** - ${next_plan.price_monthly:,}/month")
                    st.write(f"✓ {next_plan.limits['users']} users (+{next_plan.limits['users'] - organization.max_users})")
                    st.write(f"✓ {next_plan.limits['incidents_per_month']:,} incidents/month")
            
            with col2:
                if next_plan.tier == PricingTier.ENTERPRISE:
                    if st.button("Contact Sales"):
                        st.success("Sales team will contact you within 24 hours!")
                else:
                    if st.button("Upgrade Now"):
                        st.success("Upgrade request submitted! Our team will contact you shortly.")
        else:
            st.info("You're on our highest tier! Contact sales for custom enterprise solutions.")