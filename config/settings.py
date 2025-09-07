"""
Framework Settings - Configuration management for the agentic framework
"""

import os
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pathlib import Path
import json
import yaml
from datetime import datetime


@dataclass
class DatabaseConfig:
    """Database configuration settings"""
    type: str = "sqlite"  # sqlite, postgresql, mysql
    host: str = "localhost"
    port: int = 5432
    database: str = "agentic_framework"
    username: str = ""
    password: str = ""
    url: str = ""
    
    def get_connection_string(self) -> str:
        """Get database connection string"""
        if self.url:
            return self.url
        
        if self.type == "sqlite":
            return f"sqlite:///{self.database}.db"
        elif self.type == "postgresql":
            return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        elif self.type == "mysql":
            return f"mysql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        else:
            raise ValueError(f"Unsupported database type: {self.type}")


@dataclass
class LoggingConfig:
    """Logging configuration settings"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: Optional[str] = None
    max_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    console: bool = True


@dataclass
class APIConfig:
    """API configuration settings"""
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    api_key_header: str = "X-API-Key"
    rate_limit: int = 100  # requests per minute
    timeout: int = 30  # seconds


@dataclass
class SecurityConfig:
    """Security configuration settings"""
    secret_key: str = ""
    jwt_secret: str = ""
    jwt_expiration: int = 3600  # 1 hour
    password_min_length: int = 8
    enable_ssl: bool = False
    ssl_cert_file: str = ""
    ssl_key_file: str = ""


@dataclass
class MonitoringConfig:
    """Monitoring configuration settings"""
    enabled: bool = True
    metrics_port: int = 9090
    health_check_interval: int = 30  # seconds
    alert_email: str = ""
    alert_webhook: str = ""


@dataclass
class FrameworkConfig:
    """Main framework configuration"""
    # Core settings
    name: str = "Agentic Framework"
    version: str = "1.0.0"
    environment: str = "development"  # development, staging, production
    
    # Paths
    base_dir: Path = field(default_factory=lambda: Path.cwd())
    data_dir: Path = field(default_factory=lambda: Path.cwd() / "data")
    logs_dir: Path = field(default_factory=lambda: Path.cwd() / "logs")
    config_dir: Path = field(default_factory=lambda: Path.cwd() / "config")
    
    # Components
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    api: APIConfig = field(default_factory=APIConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    
    # Agent settings
    max_agents: int = 100
    agent_startup_timeout: int = 30  # seconds
    agent_health_check_interval: int = 30  # seconds
    agent_auto_restart: bool = True
    agent_max_retries: int = 3
    
    # Message bus settings
    message_bus_max_queue_size: int = 10000
    message_bus_worker_threads: int = 4
    message_bus_cleanup_interval: int = 300  # 5 minutes
    
    # Context settings
    context_max_items: int = 10000
    context_cleanup_interval: int = 300  # 5 minutes
    context_persistence: bool = True
    
    # External services
    openai_api_key: str = ""
    openai_model: str = "gpt-3.5-turbo"
    openai_max_tokens: int = 1000
    
    # Feature flags
    enable_web_interface: bool = True
    enable_api: bool = True
    enable_metrics: bool = True
    enable_persistence: bool = True
    
    def __post_init__(self):
        """Post-initialization setup"""
        # Create directories if they don't exist
        self.data_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        self.config_dir.mkdir(exist_ok=True)
        
        # Set default secret key if not provided
        if not self.security.secret_key:
            self.security.secret_key = os.urandom(32).hex()
        
        if not self.security.jwt_secret:
            self.security.jwt_secret = os.urandom(32).hex()


class Settings:
    """
    Settings manager for the agentic framework.
    
    Handles configuration loading, validation, and environment variable overrides.
    """
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file
        self.config = FrameworkConfig()
        self._load_config()
        self._setup_logging()
    
    def _load_config(self):
        """Load configuration from file and environment variables"""
        # Load from config file if specified
        if self.config_file and os.path.exists(self.config_file):
            self._load_from_file(self.config_file)
        
        # Override with environment variables
        self._load_from_environment()
        
        # Validate configuration
        self._validate_config()
    
    def _load_from_file(self, config_file: str):
        """Load configuration from file"""
        try:
            file_path = Path(config_file)
            if file_path.suffix.lower() == '.json':
                with open(file_path, 'r') as f:
                    config_data = json.load(f)
            elif file_path.suffix.lower() in ['.yml', '.yaml']:
                with open(file_path, 'r') as f:
                    config_data = yaml.safe_load(f)
            else:
                raise ValueError(f"Unsupported config file format: {file_path.suffix}")
            
            # Update configuration
            self._update_config_from_dict(config_data)
            
        except Exception as e:
            logging.warning(f"Failed to load config file {config_file}: {e}")
    
    def _load_from_environment(self):
        """Load configuration from environment variables"""
        env_mappings = {
            # Core settings
            'FRAMEWORK_ENVIRONMENT': 'environment',
            'FRAMEWORK_NAME': 'name',
            'FRAMEWORK_VERSION': 'version',
            
            # Database
            'DB_TYPE': 'database.type',
            'DB_HOST': 'database.host',
            'DB_PORT': 'database.port',
            'DB_NAME': 'database.database',
            'DB_USER': 'database.username',
            'DB_PASSWORD': 'database.password',
            'DB_URL': 'database.url',
            
            # API
            'API_HOST': 'api.host',
            'API_PORT': 'api.port',
            'API_DEBUG': 'api.debug',
            
            # Security
            'SECRET_KEY': 'security.secret_key',
            'JWT_SECRET': 'security.jwt_secret',
            'JWT_EXPIRATION': 'security.jwt_expiration',
            
            # OpenAI
            'OPENAI_API_KEY': 'openai_api_key',
            'OPENAI_MODEL': 'openai_model',
            'OPENAI_MAX_TOKENS': 'openai_max_tokens',
            
            # Feature flags
            'ENABLE_WEB_INTERFACE': 'enable_web_interface',
            'ENABLE_API': 'enable_api',
            'ENABLE_METRICS': 'enable_metrics',
            'ENABLE_PERSISTENCE': 'enable_persistence',
        }
        
        for env_var, config_path in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                self._set_config_value(config_path, value)
    
    def _set_config_value(self, path: str, value: Any):
        """Set a configuration value using dot notation path"""
        keys = path.split('.')
        obj = self.config
        
        for key in keys[:-1]:
            if hasattr(obj, key):
                obj = getattr(obj, key)
            else:
                return
        
        # Convert value type if needed
        if hasattr(obj, keys[-1]):
            current_value = getattr(obj, keys[-1])
            if isinstance(current_value, bool):
                value = value.lower() in ('true', '1', 'yes', 'on')
            elif isinstance(current_value, int):
                value = int(value)
            elif isinstance(current_value, float):
                value = float(value)
            elif isinstance(current_value, list):
                value = value.split(',') if isinstance(value, str) else value
            
            setattr(obj, keys[-1], value)
    
    def _update_config_from_dict(self, config_data: Dict[str, Any]):
        """Update configuration from dictionary"""
        for key, value in config_data.items():
            if hasattr(self.config, key):
                if isinstance(value, dict):
                    # Handle nested objects
                    obj = getattr(self.config, key)
                    for sub_key, sub_value in value.items():
                        if hasattr(obj, sub_key):
                            setattr(obj, sub_key, sub_value)
                else:
                    setattr(self.config, key, value)
    
    def _validate_config(self):
        """Validate configuration settings"""
        errors = []
        
        # Validate required settings
        if not self.config.security.secret_key:
            errors.append("Secret key is required")
        
        if self.config.environment not in ['development', 'staging', 'production']:
            errors.append("Environment must be one of: development, staging, production")
        
        if self.config.api.port < 1 or self.config.api.port > 65535:
            errors.append("API port must be between 1 and 65535")
        
        if self.config.max_agents < 1:
            errors.append("Max agents must be at least 1")
        
        # Validate database settings
        if self.config.database.type not in ['sqlite', 'postgresql', 'mysql']:
            errors.append("Database type must be one of: sqlite, postgresql, mysql")
        
        if self.config.database.type in ['postgresql', 'mysql']:
            if not self.config.database.username:
                errors.append(f"Database username is required for {self.config.database.type}")
        
        if errors:
            raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")
    
    def _setup_logging(self):
        """Setup logging configuration"""
        log_level = getattr(logging, self.config.logging.level.upper(), logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(self.config.logging.format)
        
        # Setup root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Console handler
        if self.config.logging.console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)
        
        # File handler
        if self.config.logging.file:
            from logging.handlers import RotatingFileHandler
            log_file = self.config.logs_dir / self.config.logging.file
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=self.config.logging.max_size,
                backupCount=self.config.logging.backup_count
            )
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
    
    def get_config(self) -> FrameworkConfig:
        """Get the current configuration"""
        return self.config
    
    def save_config(self, file_path: str):
        """Save current configuration to file"""
        config_dict = self._config_to_dict(self.config)
        
        file_path = Path(file_path)
        if file_path.suffix.lower() == '.json':
            with open(file_path, 'w') as f:
                json.dump(config_dict, f, indent=2, default=str)
        elif file_path.suffix.lower() in ['.yml', '.yaml']:
            with open(file_path, 'w') as f:
                yaml.dump(config_dict, f, default_flow_style=False)
        else:
            raise ValueError(f"Unsupported config file format: {file_path.suffix}")
    
    def _config_to_dict(self, config_obj) -> Dict[str, Any]:
        """Convert configuration object to dictionary"""
        result = {}
        for key, value in config_obj.__dict__.items():
            if hasattr(value, '__dict__'):
                result[key] = self._config_to_dict(value)
            else:
                result[key] = value
        return result
    
    def reload(self):
        """Reload configuration"""
        self._load_config()
    
    def get_database_url(self) -> str:
        """Get database connection URL"""
        return self.config.database.get_connection_string()
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.config.environment == 'production'
    
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.config.environment == 'development'


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get global settings instance"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def init_settings(config_file: Optional[str] = None) -> Settings:
    """Initialize global settings"""
    global _settings
    _settings = Settings(config_file)
    return _settings




