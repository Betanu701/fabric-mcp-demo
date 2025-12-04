"""
Initialization script for seeding tenant configurations from YAML to Key Vault.
Runs on application startup (idempotent).
"""
import json
import logging
from datetime import datetime
from typing import Dict, List

from azure.core.exceptions import ResourceNotFoundError
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

from ..config import Settings, get_tenants_config
from ..models.tenant import TenantConfig, TenantRegistry

logger = logging.getLogger(__name__)


class TenantInitializer:
    """Initializes tenant configurations from YAML to Key Vault."""
    
    def __init__(self, settings: Settings):
        """Initialize tenant initializer."""
        self.settings = settings
        
        if settings.key_vault_url and not settings.local_mock_services:
            credential = DefaultAzureCredential()
            self.kv_client = SecretClient(
                vault_url=settings.key_vault_url,
                credential=credential
            )
        else:
            self.kv_client = None
            logger.warning("Key Vault client not initialized - skipping tenant initialization")
    
    async def initialize_tenants(self) -> Dict[str, any]:
        """
        Initialize tenants from config/tenants.yaml to Key Vault.
        Idempotent - only creates missing tenants, doesn't overwrite existing.
        """
        if self.kv_client is None:
            logger.info("Skipping tenant initialization in local mode")
            return {"status": "skipped", "reason": "local_mode"}
        
        logger.info("Starting tenant initialization from YAML config")
        
        try:
            # Load tenants from YAML
            tenants_config = get_tenants_config()
            
            if not tenants_config or "tenants" not in tenants_config:
                logger.warning("No tenants found in config file")
                return {"status": "skipped", "reason": "no_tenants_in_config"}
            
            # Load or create registry
            registry = await self._load_or_create_registry()
            
            # Process each tenant
            results = {
                "created": [],
                "skipped": [],
                "errors": []
            }
            
            for tenant_data in tenants_config["tenants"]:
                try:
                    tenant_id = tenant_data["id"]
                    
                    # Check if tenant already exists
                    if await self._tenant_exists(tenant_id):
                        logger.debug(f"Tenant already exists, skipping: {tenant_id}")
                        results["skipped"].append(tenant_id)
                        continue
                    
                    # Create tenant config
                    tenant_config = TenantConfig(**tenant_data)
                    
                    # Save to Key Vault
                    await self._save_tenant_config(tenant_config)
                    
                    # Add to registry
                    if tenant_id not in registry.tenants:
                        registry.tenants.append(tenant_id)
                    
                    results["created"].append(tenant_id)
                    logger.info(f"Initialized tenant: {tenant_id}")
                    
                except Exception as e:
                    error_msg = f"Failed to initialize tenant {tenant_data.get('id', 'unknown')}: {e}"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)
            
            # Save updated registry
            if results["created"]:
                registry.updated_at = datetime.utcnow()
                await self._save_registry(registry)
            
            logger.info(
                f"Tenant initialization complete: "
                f"{len(results['created'])} created, "
                f"{len(results['skipped'])} skipped, "
                f"{len(results['errors'])} errors"
            )
            
            return {
                "status": "completed",
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Tenant initialization failed: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def _load_or_create_registry(self) -> TenantRegistry:
        """Load existing registry or create new one."""
        try:
            secret = self.kv_client.get_secret("tenant-registry")
            registry_data = json.loads(secret.value)
            return TenantRegistry(**registry_data)
        except ResourceNotFoundError:
            logger.info("Creating new tenant registry")
            return TenantRegistry(tenants=[])
    
    async def _tenant_exists(self, tenant_id: str) -> bool:
        """Check if tenant config exists in Key Vault."""
        secret_name = f"tenant-{tenant_id}-config"
        try:
            self.kv_client.get_secret(secret_name)
            return True
        except ResourceNotFoundError:
            return False
    
    async def _save_tenant_config(self, tenant_config: TenantConfig) -> None:
        """Save tenant configuration to Key Vault."""
        secret_name = f"tenant-{tenant_config.id}-config"
        config_json = tenant_config.model_dump_json()
        self.kv_client.set_secret(secret_name, config_json)
    
    async def _save_registry(self, registry: TenantRegistry) -> None:
        """Save tenant registry to Key Vault."""
        registry_json = registry.model_dump_json()
        self.kv_client.set_secret("tenant-registry", registry_json)


async def init_tenants_from_config(settings: Settings) -> Dict[str, any]:
    """
    Convenience function to initialize tenants from config.
    Called during application startup.
    """
    initializer = TenantInitializer(settings)
    return await initializer.initialize_tenants()
