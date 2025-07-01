# ai_providers.py
# AI provider abstraction layer for backwards compatibility between Sonar and Gemini APIs

import os
import time
import requests
import streamlit as st
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


class SimpleCache:
    """Simple in-memory cache with TTL support"""
    
    def __init__(self, default_ttl: int = 600):  # 10 minutes default
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
    
    def get(self, key: str) -> Optional[str]:
        if key in self.cache:
            entry = self.cache[key]
            if datetime.now() < entry['expires']:
                return entry['value']
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, value: str, ttl: Optional[int] = None) -> None:
        ttl = ttl or self.default_ttl
        expires = datetime.now() + timedelta(seconds=ttl)
        self.cache[key] = {
            'value': value,
            'expires': expires
        }
    
    def clear(self) -> None:
        self.cache.clear()


class AIInsightProvider:
    """
    Unified AI provider that supports both Perplexity Sonar and Google Gemini APIs
    with intelligent fallback and caching capabilities.
    """
    
    def __init__(self):
        self.cache = SimpleCache(default_ttl=600)  # 10-minute cache
        
        # Safely get secrets (only works in streamlit context)
        try:
            self.sonar_api_key = st.secrets.get("SONAR_API_KEY")
            self.gemini_api_key = st.secrets.get("GOOGLE_API_KEY")
            self.primary_provider = st.secrets.get("PRIMARY_AI_PROVIDER", "gemini").lower()
        except Exception:
            # Fallback for testing outside streamlit context
            self.sonar_api_key = None
            self.gemini_api_key = None
            self.primary_provider = "gemini"
        
        # Initialize Gemini if available and configured
        self.gemini_model = None
        if GEMINI_AVAILABLE and self.gemini_api_key:
            try:
                genai.configure(api_key=self.gemini_api_key)
                # Use Flash for cost efficiency, Pro for premium quality
                model_name = st.secrets.get("GEMINI_MODEL", "gemini-2.5-flash-latest")
                self.gemini_model = genai.GenerativeModel(model_name)
            except Exception as e:
                st.warning(f"Failed to initialize Gemini: {e}")
    
    def get_incident_explanation(self, description: str, incident_id: Optional[str] = None) -> str:
        """
        Get AI-powered explanation for a traffic incident with fallback support.
        
        Args:
            description: Traffic incident description
            incident_id: Optional unique incident ID for caching
            
        Returns:
            AI-generated explanation string
        """
        # Create cache key
        cache_key = f"{incident_id or hash(description)}_{self.primary_provider}"
        
        # Check cache first
        cached_result = self.cache.get(cache_key)
        if cached_result:
            return cached_result
        
        # Determine API order based on primary provider
        if self.primary_provider == "gemini":
            providers = [("gemini", self._get_gemini_explanation), 
                        ("sonar", self._get_sonar_explanation)]
        else:
            providers = [("sonar", self._get_sonar_explanation),
                        ("gemini", self._get_gemini_explanation)]
        
        # Try providers in order
        for provider_name, provider_func in providers:
            try:
                result = provider_func(description)
                if result and not result.startswith("Error"):
                    # Cache successful result
                    self.cache.set(cache_key, result)
                    return result
            except Exception as e:
                st.warning(f"{provider_name.title()} API failed: {e}")
                continue
        
        # All providers failed
        return "AI explanation temporarily unavailable. Please try again later."
    
    def _get_gemini_explanation(self, description: str) -> Optional[str]:
        """Get explanation from Gemini API"""
        if not self.gemini_model:
            return None
            
        prompt = (
            "You are a helpful traffic assistant. Explain the following traffic incident "
            "clearly and concisely for a user looking at a map. Focus on potential causes, "
            "impact on traffic flow, and what drivers should expect. Keep it under 100 words.\n\n"
            f"Incident: {description}"
        )
        
        try:
            response = self.gemini_model.generate_content(prompt)
            return response.text
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower():
                raise Exception(f"Gemini rate limit exceeded: {e}")
            raise Exception(f"Gemini API error: {e}")
    
    def _get_sonar_explanation(self, description: str) -> Optional[str]:
        """Get explanation from Perplexity Sonar API"""
        if not self.sonar_api_key or self.sonar_api_key == "key":
            return None
            
        headers = {
            "Authorization": f"Bearer {self.sonar_api_key}",
            "Content-Type": "application/json"
        }
        
        prompt = (
            f"Explain the possible causes and implications of this traffic report in plain language:\n"
            f'"{description}"'
        )
        
        data = {
            "query": prompt,
            "source": "web",
            "num_results": 1
        }
        
        try:
            response = requests.post(
                "https://api.perplexity.ai/sonar/v1/query", 
                headers=headers, 
                json=data,
                timeout=30
            )
            response.raise_for_status()
            return response.json().get("answer", "No answer provided.")
        except requests.exceptions.RequestException as e:
            if response.status_code == 429:
                raise Exception(f"Sonar rate limit exceeded: {e}")
            raise Exception(f"Sonar API error: {e}")
    
    def get_provider_status(self) -> Dict[str, bool]:
        """Check which providers are available"""
        return {
            "gemini_available": bool(self.gemini_model),
            "sonar_available": bool(self.sonar_api_key and self.sonar_api_key != "key"),
            "primary_provider": self.primary_provider,
            "cache_size": len(self.cache.cache)
        }
    
    def clear_cache(self) -> None:
        """Clear the response cache"""
        self.cache.clear()