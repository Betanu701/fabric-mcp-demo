"""
Tenant management service.
Handles tenant registry, configuration loading from Key Vault, and caching.
"""
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

from azure.core.exceptions import ResourceNotFoundError
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

from ..config import Settings
from ..models.tenant import TenantConfig, TenantRegistry

logger = logging.getLogger(__name__)


class TenantManager:
    """Manages tenant configurations and Key Vault integration."""
    
    REGISTRY_SECRET_NAME = "tenant-registry"
    TENANT_CONFIG_PREFIX = "tenant-"
    TENANT_CONFIG_SUFFIX = "-config"
    
    def __init__(self, settings: Settings):
        """Initialize tenant manager."""
        self.settings = settings
        self._cache: Dict[str, TenantConfig] = {}
        self._registry: Optional[TenantRegistry] = None
        self._cache_timestamp: Optional[datetime] = None
        self._cache_ttl = 300  # 5 minutes
        self._local_tenants: Dict[str, TenantConfig] = {}
        
        # Initialize Key Vault client
        if settings.key_vault_url and not settings.local_mock_services:
            credential = DefaultAzureCredential()
            self.kv_client = SecretClient(
                vault_url=settings.key_vault_url,
                credential=credential
            )
        else:
            self.kv_client = None
            logger.warning("Key Vault client not initialized - using local mode")
            self._load_local_tenants()
    
    def _load_local_tenants(self) -> None:
        """Load tenant configurations from local YAML file for development."""
        import yaml
        from pathlib import Path
        
        config_path = Path(__file__).parent.parent.parent.parent / "config" / "tenants.yaml"
        if not config_path.exists():
            logger.warning(f"Local tenants config not found: {config_path}")
            return
        
        try:
            with open(config_path) as f:
                data = yaml.safe_load(f)
            
            tenants_data = data.get("tenants", [])
            for tenant_data in tenants_data:
                tenant_id = tenant_data.get("id")
                if tenant_id:
                    tenant_config = TenantConfig(**tenant_data)
                    self._local_tenants[tenant_id] = tenant_config
            
            logger.info(f"Loaded {len(self._local_tenants)} tenants from local config")
        except Exception as e:
            logger.error(f"Failed to load local tenants: {e}")
    
    async def initialize(self) -> None:
        """Initialize tenant manager, load registry from Key Vault."""
        logger.info("Initializing tenant manager")
        
        # In local mode, use local tenants
        if self.kv_client is None:
            tenant_ids = list(self._local_tenants.keys())
            self._registry = TenantRegistry(tenants=tenant_ids)
            logger.info(f"Initialized with {len(tenant_ids)} local tenants: {tenant_ids}")
            return
        
        try:
            await self.refresh_registry()
            logger.info(f"Tenant manager initialized with {len(self._cache)} tenants")
        except Exception as e:
            logger.error(f"Failed to initialize tenant manager: {e}")
            if not self.settings.local_dev_mode:
                raise
    
    async def refresh_registry(self) -> None:
        """Refresh tenant registry and cache from Key Vault."""
        if self.kv_client is None:
            logger.debug("Skipping registry refresh in local mode")
            return
        
        try:
            # Load tenant registry
            secret = self.kv_client.get_secret(self.REGISTRY_SECRET_NAME)
            registry_data = json.loads(secret.value)
            self._registry = TenantRegistry(**registry_data)
            
            # Load all tenant configurations
            for tenant_id in self._registry.tenants:
                await self._load_tenant_config(tenant_id)
            
            self._cache_timestamp = datetime.utcnow()
            logger.info(f"Refreshed tenant registry: {len(self._registry.tenants)} tenants")
            
        except ResourceNotFoundError:
            logger.warning("Tenant registry not found in Key Vault")
            self._registry = TenantRegistry(tenants=[])
        except Exception as e:
            logger.error(f"Failed to refresh tenant registry: {e}")
            raise
    
    async def _load_tenant_config(self, tenant_id: str) -> Optional[TenantConfig]:
        """Load tenant configuration from Key Vault."""
        if self.kv_client is None:
            return None
        
        secret_name = f"{self.TENANT_CONFIG_PREFIX}{tenant_id}{self.TENANT_CONFIG_SUFFIX}"
        
        try:
            secret = self.kv_client.get_secret(secret_name)
            config_data = json.loads(secret.value)
            tenant_config = TenantConfig(**config_data)
            self._cache[tenant_id] = tenant_config
            logger.debug(f"Loaded tenant config: {tenant_id}")
            return tenant_config
        except ResourceNotFoundError:
            logger.warning(f"Tenant config not found: {tenant_id}")
            return None
        except Exception as e:
            logger.error(f"Failed to load tenant config {tenant_id}: {e}")
            return None
    
    async def get_tenant(self, tenant_id: str) -> Optional[TenantConfig]:
        """Get tenant configuration by ID."""
        # Check cache first
        if tenant_id in self._cache:
            return self._cache[tenant_id]
        
        # In local mode, check local tenants
        if self.kv_client is None:
            tenant_config = self._local_tenants.get(tenant_id)
            if tenant_config:
                self._cache[tenant_id] = tenant_config
            return tenant_config
        
        # Try loading from Key Vault
        tenant_config = await self._load_tenant_config(tenant_id)
        return tenant_config
    
    async def list_tenants(self) -> List[TenantConfig]:
        """List all tenant configurations."""
        if self._registry is None:
            await self.refresh_registry()
        
        return [
            tenant_config
            for tenant_id in (self._registry.tenants if self._registry else [])
            if (tenant_config := await self.get_tenant(tenant_id)) is not None
        ]
    
    async def create_tenant(self, tenant_config: TenantConfig) -> TenantConfig:
        """Create new tenant configuration."""
        if self.kv_client is None:
            raise RuntimeError("Key Vault client not available")
        
        # Validate tenant doesn't exist
        if tenant_config.id in self._cache:
            raise ValueError(f"Tenant already exists: {tenant_config.id}")
        
        # Save to Key Vault
        secret_name = f"{self.TENANT_CONFIG_PREFIX}{tenant_config.id}{self.TENANT_CONFIG_SUFFIX}"
        config_json = tenant_config.model_dump_json()
        
        try:
            self.kv_client.set_secret(secret_name, config_json)
            logger.info(f"Created tenant config: {tenant_config.id}")
            
            # Update registry
            await self._add_to_registry(tenant_config.id)
            
            # Update cache
            self._cache[tenant_config.id] = tenant_config
            
            return tenant_config
        except Exception as e:
            logger.error(f"Failed to create tenant {tenant_config.id}: {e}")
            raise
    
    async def update_tenant(self, tenant_config: TenantConfig) -> TenantConfig:
        """Update existing tenant configuration."""
        if self.kv_client is None:
            raise RuntimeError("Key Vault client not available")
        
        # Validate tenant exists
        if tenant_config.id not in self._cache:
            raise ValueError(f"Tenant not found: {tenant_config.id}")
        
        # Update timestamp
        tenant_config.updated_at = datetime.utcnow()
        
        # Save to Key Vault
        secret_name = f"{self.TENANT_CONFIG_PREFIX}{tenant_config.id}{self.TENANT_CONFIG_SUFFIX}"
        config_json = tenant_config.model_dump_json()
        
        try:
            self.kv_client.set_secret(secret_name, config_json)
            logger.info(f"Updated tenant config: {tenant_config.id}")
            
            # Update cache
            self._cache[tenant_config.id] = tenant_config
            
            return tenant_config
        except Exception as e:
            logger.error(f"Failed to update tenant {tenant_config.id}: {e}")
            raise
    
    async def delete_tenant(self, tenant_id: str) -> None:
        """Delete tenant configuration."""
        if self.kv_client is None:
            raise RuntimeError("Key Vault client not available")
        
        secret_name = f"{self.TENANT_CONFIG_PREFIX}{tenant_id}{self.TENANT_CONFIG_SUFFIX}"
        
        try:
            # Begin delete (soft delete with recovery option)
            self.kv_client.begin_delete_secret(secret_name)
            logger.info(f"Deleted tenant config: {tenant_id}")
            
            # Update registry
            await self._remove_from_registry(tenant_id)
            
            # Update cache
            if tenant_id in self._cache:
                del self._cache[tenant_id]
        except Exception as e:
            logger.error(f"Failed to delete tenant {tenant_id}: {e}")
            raise
    
    async def _add_to_registry(self, tenant_id: str) -> None:
        """Add tenant to registry."""
        if self._registry is None:
            self._registry = TenantRegistry(tenants=[])
        
        if tenant_id not in self._registry.tenants:
            self._registry.tenants.append(tenant_id)
            self._registry.updated_at = datetime.utcnow()
            await self._save_registry()
    
    async def _remove_from_registry(self, tenant_id: str) -> None:
        """Remove tenant from registry."""
        if self._registry and tenant_id in self._registry.tenants:
            self._registry.tenants.remove(tenant_id)
            self._registry.updated_at = datetime.utcnow()
            await self._save_registry()
    
    async def _save_registry(self) -> None:
        """Save tenant registry to Key Vault."""
        if self.kv_client is None or self._registry is None:
            return
        
        try:
            registry_json = self._registry.model_dump_json()
            self.kv_client.set_secret(self.REGISTRY_SECRET_NAME, registry_json)
            logger.debug("Saved tenant registry")
        except Exception as e:
            logger.error(f"Failed to save tenant registry: {e}")
            raise
    
    def is_cache_valid(self) -> bool:
        """Check if cache is still valid."""
        if self._cache_timestamp is None:
            return False
        
        age = (datetime.utcnow() - self._cache_timestamp).total_seconds()
        return age < self._cache_ttl
    
    async def validate_tenant(self, tenant_id: str) -> bool:
        """Validate if tenant exists and is enabled."""
        if self.settings.allow_all_tenants:
            return True
        
        tenant = await self.get_tenant(tenant_id)
        return tenant is not None and tenant.enabled
    
    def get_cached_tenant_count(self) -> int:
        """Get number of cached tenants."""
        return len(self._cache)
