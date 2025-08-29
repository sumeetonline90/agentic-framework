"""
Configuration Package

This package contains configuration management for the agentic framework.
"""

from .settings import Settings
from .agent_config import AgentType, AgentConfig, get_agent_config

__all__ = [
    "Settings",
    "AgentType",
    "AgentConfig", 
    "get_agent_config"
]
