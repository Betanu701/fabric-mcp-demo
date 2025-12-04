"""
Enterprise Multi-Tenant MCP Server Configuration
Loads settings from environment variables and YAML configuration files.
"""
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment and config files."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application identity
    app_name: str = Field(default="Enterprise MCP", alias="APP_NAME")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    environment: str = Field(default="development", alias="ENVIRONMENT")
    
    # API configuration
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    api_reload: bool = Field(default=False, alias="API_RELOAD")
    api_timeout: int = Field(default=60, alias="API_TIMEOUT")
    api_max_payload_size: int = Field(default=10485760, alias="API_MAX_PAYLOAD_SIZE")
    
    # Logging and monitoring
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    application_insights_enabled: bool = Field(default=True, alias="FEATURE_TELEMETRY")
    applicationinsights_connection_string: Optional[str] = Field(
        default=None, alias="APPLICATIONINSIGHTS_CONNECTION_STRING"
    )
    telemetry_sampling_rate: float = Field(default=1.0, alias="TELEMETRY_SAMPLING_RATE")
    
    # Azure resources
    azure_subscription_id: Optional[str] = Field(default=None, alias="AZURE_SUBSCRIPTION_ID")
    azure_resource_group: Optional[str] = Field(default=None, alias="AZURE_RESOURCE_GROUP")
    azure_location: str = Field(default="eastus", alias="AZURE_LOCATION")
    
    # Azure Key Vault
    key_vault_url: Optional[str] = Field(default=None, alias="KEY_VAULT_URL")
    
    # Azure Blob Storage
    blob_storage_url: Optional[str] = Field(default=None, alias="BLOB_STORAGE_URL")
    blob_container_branding: str = Field(default="brand-assets", alias="BLOB_STORAGE_CONTAINER")
    
    # Azure Cache for Redis
    redis_url: str = Field(default="redis://localhost:6379", alias="REDIS_URL")
    redis_password: Optional[str] = Field(default=None, alias="REDIS_PASSWORD")
    redis_ssl: bool = Field(default=False, alias="REDIS_SSL")
    redis_max_connections: int = Field(default=50, alias="REDIS_MAX_CONNECTIONS")
    
    # Azure Cost Management
    cost_tracking_enabled: bool = Field(default=True, alias="FEATURE_COST_TRACKING")
    cost_management_scope: Optional[str] = Field(default=None, alias="COST_MANAGEMENT_SCOPE")
    cost_refresh_interval: int = Field(default=3600, alias="COST_REFRESH_INTERVAL")
    
    # Azure Communication Services
    communication_services_connection_string: Optional[str] = Field(
        default=None, alias="COMMUNICATION_SERVICES_CONNECTION_STRING"
    )
    notification_default_sender: str = Field(
        default="noreply@example.com", alias="NOTIFICATION_DEFAULT_SENDER"
    )
    
    # FoundryIQ configuration
    foundry_api_base: str = Field(
        default="https://foundry.azure.com", alias="FOUNDRY_API_BASE"
    )
    foundry_api_key: Optional[str] = Field(default=None, alias="FOUNDRY_API_KEY")
    foundry_timeout: int = Field(default=30, alias="FOUNDRY_TIMEOUT")
    foundry_max_retries: int = Field(default=3, alias="FOUNDRY_MAX_RETRIES")
    
    # Entra ID authentication
    entra_enabled: bool = Field(default=False, alias="ENTRA_ENABLED")
    entra_tenant_id: Optional[str] = Field(default=None, alias="ENTRA_TENANT_ID")
    entra_client_id: Optional[str] = Field(default=None, alias="ENTRA_CLIENT_ID")
    entra_client_secret: Optional[str] = Field(default=None, alias="ENTRA_CLIENT_SECRET")
    entra_authority: str = Field(
        default="https://login.microsoftonline.com/", alias="ENTRA_AUTHORITY"
    )
    
    # Security
    cors_origins: List[str] = Field(
        default=["http://localhost:5173", "http://localhost:3000"], alias="CORS_ORIGINS"
    )
    allowed_hosts: List[str] = Field(
        default=["localhost", "127.0.0.1"], alias="ALLOWED_HOSTS"
    )
    
    # Tenant management
    allow_all_tenants: bool = Field(default=True, alias="ALLOW_ALL_TENANTS")
    
    # Rate limiting
    global_rate_limit_rpm: int = Field(default=1000, alias="GLOBAL_RATE_LIMIT_RPM")
    default_rate_limit_rpm: int = Field(default=100, alias="DEFAULT_RATE_LIMIT_RPM")
    default_rate_limit_rpd: int = Field(default=10000, alias="DEFAULT_RATE_LIMIT_RPD")
    
    # Budget enforcement
    default_budget_enforcement: str = Field(default="block", alias="DEFAULT_BUDGET_ENFORCEMENT")
    default_budget_threshold: int = Field(default=90, alias="DEFAULT_BUDGET_THRESHOLD")
    
    # Feature flags
    feature_auto_discovery: bool = Field(default=True, alias="FEATURE_AUTO_DISCOVERY")
    feature_setup_wizard: bool = Field(default=True, alias="FEATURE_SETUP_WIZARD")
    feature_multi_region_dr: bool = Field(default=False, alias="FEATURE_MULTI_REGION_DR")
    
    # Local development
    local_dev_mode: bool = Field(default=False, alias="LOCAL_DEV_MODE")
    local_mock_services: bool = Field(default=False, alias="LOCAL_MOCK_SERVICES")
    
    # Configuration file paths
    config_dir: Path = Field(default=Path("config"))
    tenants_config_file: Path = Field(default=Path("config/tenants.yaml"))
    default_config_file: Path = Field(default=Path("config/default.yaml"))
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"
    
    def get_redis_connection_kwargs(self) -> Dict[str, Any]:
        """Get Redis connection parameters."""
        kwargs: Dict[str, Any] = {
            "max_connections": self.redis_max_connections,
            "decode_responses": True,
        }
        
        if self.redis_password:
            kwargs["password"] = self.redis_password
        
        if self.redis_ssl:
            kwargs["ssl"] = True
            kwargs["ssl_cert_reqs"] = "required"
        
        return kwargs


def load_yaml_config(file_path: Path) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    if not file_path.exists():
        return {}
    
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()


def get_default_config() -> Dict[str, Any]:
    """Load default configuration from YAML file."""
    settings = get_settings()
    return load_yaml_config(settings.default_config_file)


def get_tenants_config() -> Dict[str, Any]:
    """Load tenants configuration from YAML file."""
    settings = get_settings()
    return load_yaml_config(settings.tenants_config_file)
