"""
Branding service for managing white-label customization.
Handles brand assets (logos, colors, themes) with Azure Blob Storage.
"""
import logging
from typing import Optional, Dict
import json
from io import BytesIO

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, ContentSettings
from azure.core.exceptions import ResourceNotFoundError

from ..config import Settings
from ..models.tenant import BrandingConfig, GlobalBranding

logger = logging.getLogger(__name__)


class BrandingService:
    """Service for managing tenant branding and white-label customization."""
    
    def __init__(self, settings: Settings):
        """Initialize branding service."""
        self.settings = settings
        self.blob_service_client: Optional[BlobServiceClient] = None
        self.container_name = "branding"
        self._mock_mode = settings.local_mock_services
        self._cache: Dict[str, BrandingConfig] = {}
    
    async def initialize(self) -> None:
        """Initialize Azure Blob Storage client."""
        if self._mock_mode or not self.settings.azure_storage_account_url:
            logger.warning("Branding service running in mock mode")
            return
        
        try:
            credential = DefaultAzureCredential()
            self.blob_service_client = BlobServiceClient(
                account_url=self.settings.azure_storage_account_url,
                credential=credential
            )
            
            # Ensure container exists
            try:
                container_client = self.blob_service_client.get_container_client(self.container_name)
                container_client.get_container_properties()
            except ResourceNotFoundError:
                container_client = self.blob_service_client.create_container(self.container_name)
                logger.info(f"Created branding container: {self.container_name}")
            
            logger.info("Branding service initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize branding service: {e}")
    
    async def get_global_branding(self) -> GlobalBranding:
        """
        Get global default branding configuration.
        
        Returns:
            GlobalBranding object
        """
        if self._mock_mode or not self.blob_service_client:
            return self._get_default_branding()
        
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob="global-branding.json"
            )
            
            data = blob_client.download_blob().readall()
            config_dict = json.loads(data)
            
            return GlobalBranding(**config_dict)
            
        except ResourceNotFoundError:
            logger.info("Global branding not found, using defaults")
            return self._get_default_branding()
        except Exception as e:
            logger.error(f"Failed to load global branding: {e}")
            return self._get_default_branding()
    
    async def set_global_branding(self, branding: GlobalBranding) -> bool:
        """
        Set global default branding configuration.
        
        Args:
            branding: GlobalBranding object
        
        Returns:
            True if successful
        """
        if self._mock_mode or not self.blob_service_client:
            logger.info("[MOCK] Global branding updated")
            return True
        
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob="global-branding.json"
            )
            
            data = json.dumps(branding.model_dump(), indent=2)
            blob_client.upload_blob(
                data,
                overwrite=True,
                content_settings=ContentSettings(content_type="application/json")
            )
            
            logger.info("Global branding updated")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set global branding: {e}")
            return False
    
    async def get_tenant_branding(self, tenant_id: str) -> BrandingConfig:
        """
        Get branding configuration for a tenant.
        Inherits from global if not overridden.
        
        Args:
            tenant_id: Tenant identifier
        
        Returns:
            BrandingConfig object
        """
        # Check cache
        if tenant_id in self._cache:
            return self._cache[tenant_id]
        
        if self._mock_mode or not self.blob_service_client:
            return self._get_default_tenant_branding(tenant_id)
        
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=f"tenants/{tenant_id}/branding.json"
            )
            
            data = blob_client.download_blob().readall()
            config_dict = json.loads(data)
            
            branding = BrandingConfig(**config_dict)
            self._cache[tenant_id] = branding
            
            return branding
            
        except ResourceNotFoundError:
            # No custom branding, use defaults with global inheritance
            branding = self._get_default_tenant_branding(tenant_id)
            self._cache[tenant_id] = branding
            return branding
        except Exception as e:
            logger.error(f"Failed to load tenant branding for {tenant_id}: {e}")
            return self._get_default_tenant_branding(tenant_id)
    
    async def set_tenant_branding(
        self,
        tenant_id: str,
        branding: BrandingConfig
    ) -> bool:
        """
        Set branding configuration for a tenant.
        
        Args:
            tenant_id: Tenant identifier
            branding: BrandingConfig object
        
        Returns:
            True if successful
        """
        if self._mock_mode or not self.blob_service_client:
            logger.info(f"[MOCK] Branding updated for tenant {tenant_id}")
            self._cache[tenant_id] = branding
            return True
        
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=f"tenants/{tenant_id}/branding.json"
            )
            
            data = json.dumps(branding.model_dump(), indent=2)
            blob_client.upload_blob(
                data,
                overwrite=True,
                content_settings=ContentSettings(content_type="application/json")
            )
            
            # Update cache
            self._cache[tenant_id] = branding
            
            logger.info(f"Branding updated for tenant {tenant_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set tenant branding for {tenant_id}: {e}")
            return False
    
    async def upload_logo(
        self,
        tenant_id: str,
        logo_data: bytes,
        filename: str
    ) -> Optional[str]:
        """
        Upload logo image for a tenant.
        
        Args:
            tenant_id: Tenant identifier
            logo_data: Logo image bytes
            filename: Original filename
        
        Returns:
            URL of uploaded logo, or None if failed
        """
        if self._mock_mode or not self.blob_service_client:
            mock_url = f"https://mock.blob.core.windows.net/branding/tenants/{tenant_id}/logo.png"
            logger.info(f"[MOCK] Logo uploaded: {mock_url}")
            return mock_url
        
        try:
            # Determine content type
            content_type = "image/png"
            if filename.lower().endswith(".jpg") or filename.lower().endswith(".jpeg"):
                content_type = "image/jpeg"
            elif filename.lower().endswith(".svg"):
                content_type = "image/svg+xml"
            
            blob_name = f"tenants/{tenant_id}/logo{filename[filename.rfind('.'):]}"
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            blob_client.upload_blob(
                logo_data,
                overwrite=True,
                content_settings=ContentSettings(content_type=content_type)
            )
            
            # Construct URL
            logo_url = f"{self.settings.azure_storage_account_url}/{self.container_name}/{blob_name}"
            
            logger.info(f"Logo uploaded for tenant {tenant_id}: {logo_url}")
            return logo_url
            
        except Exception as e:
            logger.error(f"Failed to upload logo for {tenant_id}: {e}")
            return None
    
    async def upload_brand_guide(
        self,
        tenant_id: str,
        guide_data: bytes,
        filename: str
    ) -> Optional[str]:
        """
        Upload brand guide document for a tenant.
        
        Args:
            tenant_id: Tenant identifier
            guide_data: Brand guide document bytes
            filename: Original filename
        
        Returns:
            URL of uploaded document, or None if failed
        """
        if self._mock_mode or not self.blob_service_client:
            mock_url = f"https://mock.blob.core.windows.net/branding/tenants/{tenant_id}/brand-guide.pdf"
            logger.info(f"[MOCK] Brand guide uploaded: {mock_url}")
            return mock_url
        
        try:
            blob_name = f"tenants/{tenant_id}/brand-guide{filename[filename.rfind('.'):]}"
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            blob_client.upload_blob(
                guide_data,
                overwrite=True,
                content_settings=ContentSettings(content_type="application/pdf")
            )
            
            guide_url = f"{self.settings.azure_storage_account_url}/{self.container_name}/{blob_name}"
            
            logger.info(f"Brand guide uploaded for tenant {tenant_id}: {guide_url}")
            return guide_url
            
        except Exception as e:
            logger.error(f"Failed to upload brand guide for {tenant_id}: {e}")
            return None
    
    def _get_default_branding(self) -> GlobalBranding:
        """Get default global branding."""
        return GlobalBranding(
            logo_url=None,
            primary_color="#0078d4",
            secondary_color="#50e6ff",
            accent_color="#00bcf2",
            font_family="Segoe UI, sans-serif",
            custom_css=None
        )
    
    def _get_default_tenant_branding(self, tenant_id: str) -> BrandingConfig:
        """Get default tenant branding (inherits from global)."""
        return BrandingConfig(
            logo_url=None,
            primary_color=None,
            secondary_color=None,
            accent_color=None,
            font_family=None,
            custom_css=None,
            inherit_global=True
        )
