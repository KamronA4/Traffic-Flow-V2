# pages/theme_diagnostics.py - Theme System Diagnostics

import streamlit as st
import logging
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
sys.path.append(str(parent_dir))

# Configure logging
logger = logging.getLogger(__name__)

def show():
    """Display theme diagnostics page"""
    
    st.title("🎨 Theme System Diagnostics")
    st.caption("Diagnose and troubleshoot Village platform theming issues")
    
    # Theme Import Test
    st.subheader("1. Theme Manager Import Test")
    
    try:
        from utils.theme_manager import (
            apply_village_theme, 
            create_village_header, 
            get_village_colors,
            get_theme_status,
            safe_theme_import
        )
        st.success("✅ Theme manager imported successfully")
        
        # Test theme status
        theme_status = get_theme_status()
        st.json(theme_status)
        
    except ImportError as e:
        st.error(f"❌ Theme manager import failed: {e}")
        return
    except Exception as e:
        st.error(f"❌ Unexpected error during theme import: {e}")
        return
    
    # CSS Injection Test
    st.subheader("2. CSS Injection Test")
    
    try:
        # Test basic CSS injection
        st.markdown("""
        <style>
        .diagnostic-test-element {
            background-color: #2d5016;
            color: white;
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="diagnostic-test-element">
            ✅ CSS injection is working - you should see this text with Village green background
        </div>
        """, unsafe_allow_html=True)
        
        st.success("CSS injection capability confirmed")
        
    except Exception as e:
        st.error(f"❌ CSS injection failed: {e}")
    
    # Theme Application Test
    st.subheader("3. Theme Application Test")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Apply Full Village Theme"):
            try:
                apply_village_theme()
                st.success("Village theme applied successfully")
            except Exception as e:
                st.error(f"Error applying theme: {e}")
    
    with col2:
        if st.button("Test Safe Theme Import"):
            try:
                theme_func, header_func, available = safe_theme_import()
                if available:
                    st.success("Safe theme import successful")
                else:
                    st.warning("Using fallback theme functions")
            except Exception as e:
                st.error(f"Safe theme import failed: {e}")
    
    # Header Creation Test
    st.subheader("4. Header Creation Test")
    
    if st.button("Test Village Header"):
        try:
            create_village_header(
                "Test Header",
                "This is a test of the Village header component"
            )
        except Exception as e:
            st.error(f"Header creation failed: {e}")
    
    # Color Palette Test
    st.subheader("5. Color Palette Test")
    
    try:
        colors = get_village_colors()
        
        st.write("**Village Color Palette:**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.color_picker("Primary", colors['primary'], disabled=True)
            st.color_picker("Secondary", colors['secondary'], disabled=True)
        
        with col2:
            st.color_picker("Accent", colors['accent'], disabled=True)
            st.color_picker("Neutral", colors['neutral'], disabled=True)
        
        with col3:
            st.write("**Full Palette:**")
            for i, color in enumerate(colors['palette']):
                st.color_picker(f"Color {i+1}", color, disabled=True)
        
        st.success("Color palette loaded successfully")
        
    except Exception as e:
        st.error(f"Color palette test failed: {e}")
    
    # Environment Information
    st.subheader("6. Environment Information")
    
    env_info = {
        "Streamlit Version": st.__version__,
        "Python Version": sys.version,
        "Platform": sys.platform,
        "Theme Manager Path": str(Path(__file__).parent.parent / "utils" / "theme_manager.py"),
        "Current Working Directory": os.getcwd(),
        "Python Path": sys.path[:3] + ["..."] if len(sys.path) > 3 else sys.path
    }
    
    for key, value in env_info.items():
        st.text(f"{key}: {value}")
    
    # File System Check
    st.subheader("7. File System Check")
    
    theme_manager_path = Path(__file__).parent.parent / "utils" / "theme_manager.py"
    
    if theme_manager_path.exists():
        st.success(f"✅ Theme manager file exists: {theme_manager_path}")
        
        # Check file permissions
        if os.access(theme_manager_path, os.R_OK):
            st.success("✅ Theme manager file is readable")
        else:
            st.error("❌ Theme manager file is not readable")
            
        # Show file size
        file_size = theme_manager_path.stat().st_size
        st.info(f"Theme manager file size: {file_size} bytes")
        
    else:
        st.error(f"❌ Theme manager file not found: {theme_manager_path}")
    
    # Theme Component Demo
    st.subheader("8. Theme Component Demo")
    
    if st.button("Show Theme Component Examples"):
        try:
            # Test various theme components
            st.write("**Village Card Example:**")
            from utils.theme_manager import create_village_card
            create_village_card("This is a test Village card component")
            
            st.write("**Village Metric Example:**")
            from utils.theme_manager import create_village_metric
            create_village_metric("Test Metric", "42", "+5.2%")
            
            st.write("**Status Badge Examples:**")
            from utils.theme_manager import create_status_badge
            col1, col2, col3 = st.columns(3)
            with col1:
                create_status_badge("active", "System Active")
            with col2:
                create_status_badge("paused", "Data Paused")
            with col3:
                create_status_badge("stopped", "Collection Stopped")
            
            st.success("All theme components rendered successfully")
            
        except Exception as e:
            st.error(f"Theme component demo failed: {e}")
    
    # Troubleshooting Guide
    st.subheader("9. Troubleshooting Guide")
    
    with st.expander("Common Issues and Solutions", expanded=False):
        st.markdown("""
        **Issue: "Theme manager not available" error**
        - **Cause:** Import path issues or missing theme_manager.py
        - **Solution:** Check that `utils/theme_manager.py` exists and is accessible
        
        **Issue: CSS not applying correctly**
        - **Cause:** Streamlit's `unsafe_allow_html=True` disabled or restricted
        - **Solution:** Ensure your Streamlit config allows HTML injection
        
        **Issue: Colors not displaying correctly**
        - **Cause:** CSS variables not loading or browser compatibility
        - **Solution:** Try refreshing the page or using a different browser
        
        **Issue: Theme functions raise exceptions**
        - **Cause:** Malformed HTML/CSS or Streamlit version compatibility
        - **Solution:** Check the error logs and update Streamlit if needed
        
        **Issue: Fallback theme used instead of full theme**
        - **Cause:** Silent failures in theme application
        - **Solution:** Check browser console for JavaScript errors
        """)
    
    # Reset Options
    st.subheader("10. Reset Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Clear Streamlit Cache"):
            st.cache_data.clear()
            st.success("Streamlit cache cleared")
    
    with col2:
        if st.button("Refresh Page"):
            st.rerun()

if __name__ == "__main__":
    show()