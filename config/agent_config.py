"""
Agent Configuration - Agent-specific configuration settings
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class AgentType(Enum):
    """Agent type enumeration"""
    CHAT = "chat"
    TASK = "task"
    EMAIL = "email"
    CALENDAR = "calendar"
    DATA = "data"
    WEATHER = "weather"
    NEWS = "news"
    TRANSLATION = "translation"
    CUSTOM = "custom"


@dataclass
class AgentConfig:
    """Base agent configuration"""
    agent_id: str
    agent_type: AgentType
    enabled: bool = True
    auto_start: bool = True
    auto_restart: bool = True
    max_retries: int = 3
    max_idle_time: int = 300  # 5 minutes
    priority: int = 2  # 1=low, 2=normal, 3=high, 4=critical
    dependencies: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    settings: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


# Chat Agent Configuration
CHAT_AGENT_CONFIG = AgentConfig(
    agent_id="chat_agent",
    agent_type=AgentType.CHAT,
    enabled=True,
    auto_start=True,
    auto_restart=True,
    max_retries=3,
    max_idle_time=600,  # 10 minutes
    priority=3,
    dependencies=[],
    capabilities=[
        "chat",
        "conversation",
        "nlp",
        "intent_recognition",
        "context_awareness"
    ],
    settings={
        "max_history_length": 50,
        "response_timeout": 30,
        "enable_ai": True,
        "ai_service": "openai",
        "default_language": "en",
        "enable_sentiment_analysis": True,
        "enable_entity_extraction": True,
        "max_conversation_length": 100,
        "enable_profanity_filter": False,
        "enable_spam_detection": True
    },
    metadata={
        "description": "Handles conversational interactions and AI-powered responses",
        "version": "1.0.0",
        "author": "Agentic Framework",
        "tags": ["conversation", "ai", "nlp"]
    }
)


# Task Agent Configuration
TASK_AGENT_CONFIG = AgentConfig(
    agent_id="task_agent",
    agent_type=AgentType.TASK,
    enabled=True,
    auto_start=True,
    auto_restart=True,
    max_retries=5,
    max_idle_time=1800,  # 30 minutes
    priority=2,
    dependencies=[],
    capabilities=[
        "task_automation",
        "workflow_execution",
        "scheduling",
        "file_processing",
        "data_transformation"
    ],
    settings={
        "max_concurrent_tasks": 10,
        "task_timeout": 300,  # 5 minutes
        "enable_parallel_execution": True,
        "max_retry_attempts": 3,
        "enable_task_history": True,
        "task_history_retention_days": 30,
        "enable_task_notifications": True,
        "default_working_directory": "./tasks",
        "allowed_file_types": [".txt", ".csv", ".json", ".xml", ".yaml"],
        "max_file_size_mb": 100
    },
    metadata={
        "description": "Handles task automation and workflow execution",
        "version": "1.0.0",
        "author": "Agentic Framework",
        "tags": ["automation", "workflow", "tasks"]
    }
)


# Email Agent Configuration
EMAIL_AGENT_CONFIG = AgentConfig(
    agent_id="email_agent",
    agent_type=AgentType.EMAIL,
    enabled=True,
    auto_start=True,
    auto_restart=True,
    max_retries=3,
    max_idle_time=900,  # 15 minutes
    priority=2,
    dependencies=[],
    capabilities=[
        "email_sending",
        "email_receiving",
        "email_processing",
        "email_filtering",
        "email_templates"
    ],
    settings={
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "smtp_use_tls": True,
        "imap_server": "imap.gmail.com",
        "imap_port": 993,
        "imap_use_ssl": True,
        "check_interval": 300,  # 5 minutes
        "max_emails_per_batch": 50,
        "enable_auto_reply": False,
        "enable_spam_filtering": True,
        "enable_attachment_processing": True,
        "max_attachment_size_mb": 25,
        "email_templates_dir": "./email_templates",
        "enable_email_analytics": True
    },
    metadata={
        "description": "Handles email operations and processing",
        "version": "1.0.0",
        "author": "Agentic Framework",
        "tags": ["email", "communication", "automation"]
    }
)


# Calendar Agent Configuration
CALENDAR_AGENT_CONFIG = AgentConfig(
    agent_id="calendar_agent",
    agent_type=AgentType.CALENDAR,
    enabled=True,
    auto_start=True,
    auto_restart=True,
    max_retries=3,
    max_idle_time=1200,  # 20 minutes
    priority=2,
    dependencies=[],
    capabilities=[
        "calendar_management",
        "event_scheduling",
        "meeting_coordination",
        "reminder_management",
        "availability_checking"
    ],
    settings={
        "calendar_provider": "google",  # google, outlook, ical
        "sync_interval": 300,  # 5 minutes
        "default_calendar": "primary",
        "enable_auto_scheduling": False,
        "enable_meeting_optimization": True,
        "default_meeting_duration": 30,  # minutes
        "enable_reminders": True,
        "reminder_advance_minutes": 15,
        "enable_conflict_detection": True,
        "enable_recurring_events": True,
        "max_events_per_day": 20,
        "enable_calendar_analytics": True
    },
    metadata={
        "description": "Manages calendar operations and event scheduling",
        "version": "1.0.0",
        "author": "Agentic Framework",
        "tags": ["calendar", "scheduling", "events"]
    }
)


# Data Agent Configuration
DATA_AGENT_CONFIG = AgentConfig(
    agent_id="data_agent",
    agent_type=AgentType.DATA,
    enabled=True,
    auto_start=True,
    auto_restart=True,
    max_retries=5,
    max_idle_time=3600,  # 1 hour
    priority=2,
    dependencies=[],
    capabilities=[
        "data_analysis",
        "data_processing",
        "report_generation",
        "data_visualization",
        "statistical_analysis"
    ],
    settings={
        "max_data_size_mb": 1000,
        "enable_data_caching": True,
        "cache_retention_hours": 24,
        "enable_parallel_processing": True,
        "max_parallel_jobs": 5,
        "default_output_format": "json",
        "enable_data_validation": True,
        "enable_outlier_detection": True,
        "enable_trend_analysis": True,
        "enable_forecasting": False,
        "max_forecast_periods": 12,
        "enable_report_scheduling": True,
        "default_chart_type": "line"
    },
    metadata={
        "description": "Handles data analysis and processing operations",
        "version": "1.0.0",
        "author": "Agentic Framework",
        "tags": ["data", "analysis", "processing"]
    }
)


# Weather Agent Configuration
WEATHER_AGENT_CONFIG = AgentConfig(
    agent_id="weather_agent",
    agent_type=AgentType.WEATHER,
    enabled=True,
    auto_start=True,
    auto_restart=True,
    max_retries=3,
    max_idle_time=1800,  # 30 minutes
    priority=1,
    dependencies=[],
    capabilities=[
        "weather_forecasting",
        "weather_alerts",
        "location_services",
        "weather_history",
        "climate_data"
    ],
    settings={
        "weather_provider": "openweathermap",  # openweathermap, accuweather, weather_api
        "api_key": "",
        "default_location": "New York, NY",
        "forecast_days": 7,
        "update_interval": 1800,  # 30 minutes
        "enable_alerts": True,
        "alert_thresholds": {
            "temperature_high": 35,
            "temperature_low": -10,
            "precipitation_probability": 80,
            "wind_speed": 50
        },
        "enable_location_auto_detection": True,
        "enable_weather_history": True,
        "history_days": 30,
        "units": "metric"  # metric, imperial
    },
    metadata={
        "description": "Provides weather information and forecasting",
        "version": "1.0.0",
        "author": "Agentic Framework",
        "tags": ["weather", "forecasting", "alerts"]
    }
)


# News Agent Configuration
NEWS_AGENT_CONFIG = AgentConfig(
    agent_id="news_agent",
    agent_type=AgentType.NEWS,
    enabled=True,
    auto_start=True,
    auto_restart=True,
    max_retries=3,
    max_idle_time=3600,  # 1 hour
    priority=1,
    dependencies=[],
    capabilities=[
        "news_aggregation",
        "news_filtering",
        "news_summarization",
        "trend_analysis",
        "content_curation"
    ],
    settings={
        "news_sources": ["reuters", "ap", "bbc"],
        "api_key": "",
        "update_interval": 3600,  # 1 hour
        "max_articles_per_fetch": 50,
        "enable_content_filtering": True,
        "filter_keywords": [],
        "exclude_keywords": [],
        "enable_sentiment_analysis": True,
        "enable_summarization": True,
        "summary_max_length": 200,
        "enable_trend_detection": True,
        "trend_window_hours": 24,
        "enable_notifications": False,
        "notification_keywords": []
    },
    metadata={
        "description": "Aggregates and processes news content",
        "version": "1.0.0",
        "author": "Agentic Framework",
        "tags": ["news", "content", "aggregation"]
    }
)


# Translation Agent Configuration
TRANSLATION_AGENT_CONFIG = AgentConfig(
    agent_id="translation_agent",
    agent_type=AgentType.TRANSLATION,
    enabled=True,
    auto_start=True,
    auto_restart=True,
    max_retries=3,
    max_idle_time=1800,  # 30 minutes
    priority=1,
    dependencies=[],
    capabilities=[
        "text_translation",
        "language_detection",
        "translation_memory",
        "quality_assessment",
        "multilingual_support"
    ],
    settings={
        "translation_provider": "google",  # google, deepl, azure
        "api_key": "",
        "supported_languages": ["en", "es", "fr", "de", "it", "pt", "ru", "zh", "ja", "ko"],
        "default_source_language": "auto",
        "default_target_language": "en",
        "enable_translation_memory": True,
        "memory_size": 10000,
        "enable_quality_check": True,
        "enable_batch_translation": True,
        "batch_size": 100,
        "enable_glossary": False,
        "glossary_file": "",
        "enable_format_preservation": True,
        "max_text_length": 5000
    },
    metadata={
        "description": "Handles text translation and language processing",
        "version": "1.0.0",
        "author": "Agentic Framework",
        "tags": ["translation", "language", "multilingual"]
    }
)


# Configuration registry
AGENT_CONFIGS = {
    "chat_agent": CHAT_AGENT_CONFIG,
    "task_agent": TASK_AGENT_CONFIG,
    "email_agent": EMAIL_AGENT_CONFIG,
    "calendar_agent": CALENDAR_AGENT_CONFIG,
    "data_agent": DATA_AGENT_CONFIG,
    "weather_agent": WEATHER_AGENT_CONFIG,
    "news_agent": NEWS_AGENT_CONFIG,
    "translation_agent": TRANSLATION_AGENT_CONFIG,
}


def get_agent_config(agent_id: str) -> Optional[AgentConfig]:
    """Get agent configuration by ID"""
    return AGENT_CONFIGS.get(agent_id)


def get_all_agent_configs() -> Dict[str, AgentConfig]:
    """Get all agent configurations"""
    return AGENT_CONFIGS.copy()


def get_agent_configs_by_type(agent_type: AgentType) -> List[AgentConfig]:
    """Get agent configurations by type"""
    return [
        config for config in AGENT_CONFIGS.values()
        if config.agent_type == agent_type
    ]


def get_enabled_agent_configs() -> List[AgentConfig]:
    """Get all enabled agent configurations"""
    return [
        config for config in AGENT_CONFIGS.values()
        if config.enabled
    ]


def register_agent_config(config: AgentConfig):
    """Register a new agent configuration"""
    AGENT_CONFIGS[config.agent_id] = config


def unregister_agent_config(agent_id: str):
    """Unregister an agent configuration"""
    if agent_id in AGENT_CONFIGS:
        del AGENT_CONFIGS[agent_id]


def create_custom_agent_config(
    agent_id: str,
    agent_type: AgentType = AgentType.CUSTOM,
    capabilities: Optional[List[str]] = None,
    settings: Optional[Dict[str, Any]] = None,
    **kwargs
) -> AgentConfig:
    """Create a custom agent configuration"""
    return AgentConfig(
        agent_id=agent_id,
        agent_type=agent_type,
        capabilities=capabilities or [],
        settings=settings or {},
        **kwargs
    )


def validate_agent_config(config: AgentConfig) -> List[str]:
    """Validate agent configuration and return list of errors"""
    errors = []
    
    if not config.agent_id:
        errors.append("Agent ID is required")
    
    if not isinstance(config.agent_type, AgentType):
        errors.append("Agent type must be a valid AgentType")
    
    if config.max_retries < 0:
        errors.append("Max retries must be non-negative")
    
    if config.max_idle_time < 0:
        errors.append("Max idle time must be non-negative")
    
    if config.priority < 1 or config.priority > 4:
        errors.append("Priority must be between 1 and 4")
    
    return errors


def merge_agent_configs(base_config: AgentConfig, override_config: Dict[str, Any]) -> AgentConfig:
    """Merge base configuration with override settings"""
    import copy
    
    # Create a deep copy of the base config
    merged_config = copy.deepcopy(base_config)
    
    # Update with override settings
    for key, value in override_config.items():
        if hasattr(merged_config, key):
            setattr(merged_config, key, value)
    
    return merged_config
