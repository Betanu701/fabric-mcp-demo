"""
Startup scripts package initialization.
"""
from .discovery import run_discovery
from .init_tenants import init_tenants_from_config

__all__ = ["init_tenants_from_config", "run_discovery"]
