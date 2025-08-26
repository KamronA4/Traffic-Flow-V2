# pages/__init__.py - Page modules for Village platform

# Import all page modules to make them available as pages.module_name
from . import live_traffic
from . import analytics  
from . import planning
from . import reports
from . import monitoring

__all__ = ['live_traffic', 'analytics', 'planning', 'reports', 'monitoring']