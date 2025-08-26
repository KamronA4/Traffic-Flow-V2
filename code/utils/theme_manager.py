#!/usr/bin/env python3
"""
Theme Manager for Village Platform
Provides consistent dark/light mode theming across all pages
"""

import streamlit as st
import logging

# Configure logging
logger = logging.getLogger(__name__)

def apply_village_theme():
    """Apply consistent Village theme with dark mode support"""
    
    try:
        st.markdown("""
    <style>
    /* Village theme variables */
    :root {
        --village-pine: #2d5016;
        --village-sage: #5a7c47;
        --village-beige: #f5f1e8;
        --village-brown: #8b4513;
        --village-cream: #faf8f3;
        --village-dark-brown: #5d2e07;
        --village-text: #2d2d2d;
        --village-bg: #ffffff;
    }
    
    /* Dark mode variables */
    @media (prefers-color-scheme: dark) {
        :root {
            --village-pine: #4a7c2a;
            --village-sage: #6b9c57;
            --village-beige: #2d2d2d;
            --village-brown: #b5651d;
            --village-cream: #1e1e1e;
            --village-dark-brown: #8b5a0d;
            --village-text: #ffffff;
            --village-bg: #0e1117;
        }
    }
    
    /* Force dark mode for Streamlit dark theme */
    .stApp[data-theme="dark"] {
        --village-pine: #4a7c2a;
        --village-sage: #6b9c57;
        --village-beige: #2d2d2d;
        --village-brown: #b5651d;
        --village-cream: #1e1e1e;
        --village-dark-brown: #8b5a0d;
        --village-text: #ffffff;
        --village-bg: #0e1117;
    }
    
    /* Common component styling */
    .village-header {
        background: linear-gradient(135deg, var(--village-pine) 0%, var(--village-sage) 50%, var(--village-brown) 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 6px 20px rgba(0,0,0,0.15);
    }
    
    .village-card {
        background: linear-gradient(135deg, var(--village-cream) 0%, var(--village-beige) 100%);
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        border-left: 4px solid var(--village-sage);
        box-shadow: 0 3px 10px rgba(0,0,0,0.1);
        color: var(--village-text);
    }
    
    .village-metric {
        background: linear-gradient(135deg, var(--village-cream) 0%, var(--village-beige) 100%);
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid var(--village-sage);
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
    }
    
    .village-button {
        background: linear-gradient(135deg, var(--village-pine) 0%, var(--village-sage) 100%);
        color: white !important;
        border: none;
        border-radius: 8px;
        font-weight: 500;
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
    }
    
    .village-button:hover {
        background: linear-gradient(135deg, var(--village-sage) 0%, var(--village-brown) 100%);
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* Status indicators */
    .status-active {
        color: var(--village-pine);
        background: rgba(75, 124, 42, 0.2);
        padding: 0.25rem 0.75rem;
        border-radius: 15px;
        font-weight: 600;
        border: 1px solid var(--village-sage);
    }
    
    .status-paused {
        color: var(--village-brown);
        background: rgba(181, 101, 29, 0.2);
        padding: 0.25rem 0.75rem;
        border-radius: 15px;
        font-weight: 600;
        border: 1px solid var(--village-brown);
    }
    
    .status-stopped {
        color: #dc3545;
        background: rgba(220, 53, 69, 0.2);
        padding: 0.25rem 0.75rem;
        border-radius: 15px;
        font-weight: 600;
        border: 1px solid #dc3545;
    }
    
    /* Notification styles */
    .village-success {
        background: linear-gradient(135deg, var(--village-beige) 0%, var(--village-cream) 100%);
        border-left: 4px solid var(--village-sage);
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        color: var(--village-text);
    }
    
    .village-info {
        background: linear-gradient(135deg, var(--village-beige) 0%, var(--village-cream) 100%);
        border-left: 4px solid var(--village-brown);
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        color: var(--village-text);
    }
    
    .village-warning {
        background: rgba(181, 101, 29, 0.2);
        border-left: 4px solid var(--village-brown);
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        color: var(--village-text);
    }
    
    .village-error {
        background: rgba(220, 53, 69, 0.2);
        border-left: 4px solid #dc3545;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        color: var(--village-text);
    }
    
    /* Override Streamlit component styling */
    .stButton > button {
        background: linear-gradient(135deg, var(--village-pine) 0%, var(--village-sage) 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, var(--village-sage) 0%, var(--village-brown) 100%) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important;
    }
    
    .stMetric {
        background: linear-gradient(135deg, var(--village-cream) 0%, var(--village-beige) 100%) !important;
        padding: 1rem !important;
        border-radius: 10px !important;
        border-left: 4px solid var(--village-sage) !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        background-color: var(--village-beige) !important;
        border-radius: 8px !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        color: var(--village-pine) !important;
        background-color: transparent !important;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: var(--village-sage) !important;
        color: white !important;
    }
    
    /* Sidebar theming */
    .stSidebar > div {
        background: linear-gradient(180deg, var(--village-cream) 0%, var(--village-beige) 100%) !important;
        border-right: 3px solid var(--village-sage) !important;
    }
    
    .stSidebar h3 {
        color: var(--village-pine) !important;
        border-bottom: 2px solid var(--village-sage) !important;
        padding-bottom: 0.5rem !important;
    }
    
    /* Selectbox and input styling */
    .stSelectbox > div > div,
    .stTextInput > div > div,
    .stNumberInput > div > div {
        background-color: var(--village-beige) !important;
        border: 1px solid var(--village-sage) !important;
        border-radius: 8px !important;
        color: var(--village-text) !important;
    }
    
    /* DataFrames */
    .stDataFrame {
        background-color: var(--village-cream) !important;
        border-radius: 8px !important;
        border: 1px solid var(--village-sage) !important;
    }
    
    /* Plotly charts dark mode compatibility */
    .plotly {
        background-color: var(--village-cream) !important;
        border-radius: 8px !important;
    }
    
    /* Ensure text visibility in dark mode */
    @media (prefers-color-scheme: dark) {
        .stMarkdown, .stText, p, h1, h2, h3, h4, h5, h6 {
            color: var(--village-text) !important;
        }
        
        .stDataFrame table {
            background-color: var(--village-beige) !important;
            color: var(--village-text) !important;
        }
        
        .stDataFrame th {
            background-color: var(--village-sage) !important;
            color: white !important;
        }
    }
    
    /* Dark mode for Streamlit's dark theme */
    .stApp[data-theme="dark"] .stMarkdown,
    .stApp[data-theme="dark"] .stText,
    .stApp[data-theme="dark"] p,
    .stApp[data-theme="dark"] h1,
    .stApp[data-theme="dark"] h2,
    .stApp[data-theme="dark"] h3,
    .stApp[data-theme="dark"] h4,
    .stApp[data-theme="dark"] h5,
    .stApp[data-theme="dark"] h6 {
        color: #ffffff !important;
    }
    
    /* Force dark mode styling for main content area */
    .stApp[data-theme="dark"] .main .block-container {
        background-color: var(--village-cream) !important;
    }
    
    /* Ensure consistent theming across all elements */
    .stApp {
        background-color: var(--village-bg) !important;
    }
    
    .stApp[data-theme="dark"] {
        background-color: #0e1117 !important;
    }
    
    /* Main content area theming */
    .main .block-container {
        background-color: var(--village-cream) !important;
        color: var(--village-text) !important;
    }
    </style>
    """, unsafe_allow_html=True)
    except Exception as e:
        logger.error(f"Error applying Village theme CSS: {e}")
        # Apply minimal fallback theme
        try:
            st.markdown("""
            <style>
            .stApp { background-color: #f5f1e8; }
            .stButton > button { background-color: #2d5016 !important; color: white !important; }
            </style>
            """, unsafe_allow_html=True)
        except Exception as fallback_error:
            logger.error(f"Error applying fallback theme: {fallback_error}")
            # Continue without any theme - functionality is priority

def create_village_header(title: str, subtitle: str = ""):
    """Create a standardized Village-themed header"""
    try:
        subtitle_html = f'<p style="color: #f5f1e8; margin: 0.5rem 0 0 0; font-size: 1.2rem; font-weight: 300;">{subtitle}</p>' if subtitle else ""
        
        st.markdown(f"""
        <div class="village-header">
            <h1 style="color: #faf8f3; margin: 0; font-size: 2.8rem; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">
                {title}
            </h1>
            {subtitle_html}
        </div>
        """, unsafe_allow_html=True)
    except Exception as e:
        logger.error(f"Error creating Village header: {e}")
        # Fallback to simple header
        st.title(title)
        if subtitle:
            st.caption(subtitle)

def create_village_card(content: str, border_color: str = "var(--village-sage)"):
    """Create a standardized Village-themed card"""
    try:
        st.markdown(f"""
        <div class="village-card" style="border-left-color: {border_color};">
            {content}
        </div>
        """, unsafe_allow_html=True)
    except Exception as e:
        logger.error(f"Error creating Village card: {e}")
        # Fallback to info box
        st.info(content)

def create_status_badge(status: str, text: str):
    """Create a status badge with appropriate styling"""
    try:
        status_class = f"status-{status.lower()}"
        st.markdown(f"""
        <span class="{status_class}">{text}</span>
        """, unsafe_allow_html=True)
    except Exception as e:
        logger.error(f"Error creating status badge: {e}")
        # Fallback to text display
        st.text(f"{status.upper()}: {text}")

def create_village_metric(label: str, value: str, delta: str = "", delta_color: str = "normal"):
    """Create a Village-themed metric display"""
    try:
        delta_html = f'<div style="color: {"green" if delta_color == "normal" else delta_color}; font-size: 0.8rem;">{delta}</div>' if delta else ""
        
        st.markdown(f"""
        <div class="village-metric">
            <div style="font-size: 0.8rem; color: var(--village-text); opacity: 0.8;">{label}</div>
            <div style="font-size: 1.8rem; font-weight: bold; color: var(--village-pine);">{value}</div>
            {delta_html}
        </div>
        """, unsafe_allow_html=True)
    except Exception as e:
        logger.error(f"Error creating Village metric: {e}")
        # Fallback to standard metric
        st.metric(label, value, delta)

def get_village_colors():
    """Get the Village color palette for use in charts and visualizations"""
    return {
        'primary': '#2d5016',
        'secondary': '#5a7c47', 
        'accent': '#8b4513',
        'neutral': '#f5f1e8',
        'palette': ['#2d5016', '#5a7c47', '#8b4513', '#d4a574', '#9c8b7a', '#6b5b95'],
        'dark_palette': ['#4a7c2a', '#6b9c57', '#b5651d', '#d4a574', '#9c8b7a', '#6b5b95']
    }

def apply_chart_theme(fig, dark_mode: bool = False):
    """Apply Village theme to plotly charts"""
    try:
        colors = get_village_colors()
        palette = colors['dark_palette'] if dark_mode else colors['palette']
        
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='var(--village-cream)' if not dark_mode else '#1e1e1e',
            font=dict(color='var(--village-text)'),
            colorway=palette
        )
        
        return fig
    except Exception as e:
        logger.error(f"Error applying chart theme: {e}")
        # Return figure unchanged if theming fails
        return fig

def safe_theme_import():
    """
    Safely import theme functions with fallback implementations.
    Use this in pages that need theme functionality.
    
    Returns:
        tuple: (apply_village_theme, create_village_header, theme_available)
    """
    try:
        # Test if theme functions work by attempting to import
        from utils.theme_manager import apply_village_theme, create_village_header
        return apply_village_theme, create_village_header, True
    except ImportError as e:
        logger.warning(f"Theme manager not available: {e}")
        
        # Return fallback functions
        def fallback_apply_theme():
            """Minimal fallback theme"""
            try:
                st.markdown("""
                <style>
                .stApp { background-color: #f5f1e8; }
                .stButton > button { 
                    background-color: #2d5016 !important; 
                    color: white !important; 
                    border-radius: 8px !important; 
                }
                </style>
                """, unsafe_allow_html=True)
            except:
                pass  # Continue without any styling
        
        def fallback_create_header(title: str, subtitle: str = ""):
            """Minimal fallback header"""
            st.title(title)
            if subtitle:
                st.caption(subtitle)
        
        return fallback_apply_theme, fallback_create_header, False

def get_theme_status():
    """Get current theme system status for debugging"""
    try:
        # Test CSS injection capability
        st.markdown("<style>.test-element { display: none; }</style>", unsafe_allow_html=True)
        css_available = True
    except:
        css_available = False
    
    return {
        'css_injection_available': css_available,
        'streamlit_version': st.__version__,
        'theme_functions_available': True  # If we got here, the module loaded
    }