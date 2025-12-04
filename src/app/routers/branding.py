"""
Branding management router for white-label customization.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Form
from pydantic import BaseModel

from ..dependencies import get_tenant_id
from ..services.branding_service import BrandingService
from ..models.tenant import BrandingConfig

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/branding", tags=["branding"])


class BrandingUpdateRequest(BaseModel):
    """Request to update branding settings."""
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    accent_color: Optional[str] = None
    font_family: Optional[str] = None
    custom_css: Optional[str] = None
    inherit_global: bool = True


def get_branding_service(request: Request) -> BrandingService:
    """Get branding service from app state."""
    if hasattr(request.app.state, "branding_service"):
        return request.app.state.branding_service
    raise HTTPException(status_code=500, detail="Branding service not initialized")


@router.get(
    "",
    summary="Get tenant branding",
    description="Get branding configuration for the current tenant"
)
async def get_tenant_branding(
    tenant_id: str = Depends(get_tenant_id),
    service: BrandingService = Depends(get_branding_service)
):
    """Get branding configuration for the tenant."""
    try:
        branding = await service.get_tenant_branding(tenant_id)
        
        return {
            "tenant_id": tenant_id,
            "logo_url": branding.logo_url,
            "primary_color": branding.primary_color,
            "secondary_color": branding.secondary_color,
            "accent_color": branding.accent_color,
            "font_family": branding.font_family,
            "custom_css": branding.custom_css,
            "inherit_global": branding.inherit_global
        }
    except Exception as e:
        logger.error(f"Failed to get branding for {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "",
    summary="Update tenant branding",
    description="Update branding configuration"
)
async def update_tenant_branding(
    request: BrandingUpdateRequest,
    tenant_id: str = Depends(get_tenant_id),
    service: BrandingService = Depends(get_branding_service)
):
    """Update branding configuration for the tenant."""
    try:
        branding = BrandingConfig(**request.model_dump())
        success = await service.set_tenant_branding(tenant_id, branding)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update branding")
        
        return {
            "tenant_id": tenant_id,
            "updated": True,
            "branding": request.model_dump()
        }
    except Exception as e:
        logger.error(f"Failed to update branding for {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/logo",
    summary="Upload tenant logo",
    description="Upload a logo image for the tenant"
)
async def upload_logo(
    file: UploadFile = File(..., description="Logo image file (PNG, JPG, SVG)"),
    tenant_id: str = Depends(get_tenant_id),
    service: BrandingService = Depends(get_branding_service)
):
    """Upload logo for the tenant."""
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read file data
        logo_data = await file.read()
        
        # Upload to storage
        logo_url = await service.upload_logo(
            tenant_id=tenant_id,
            logo_data=logo_data,
            filename=file.filename or "logo.png"
        )
        
        if not logo_url:
            raise HTTPException(status_code=500, detail="Failed to upload logo")
        
        return {
            "tenant_id": tenant_id,
            "logo_url": logo_url,
            "uploaded": True
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload logo for {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/brand-guide",
    summary="Upload brand guide",
    description="Upload a brand guide document (PDF)"
)
async def upload_brand_guide(
    file: UploadFile = File(..., description="Brand guide PDF"),
    tenant_id: str = Depends(get_tenant_id),
    service: BrandingService = Depends(get_branding_service)
):
    """Upload brand guide document."""
    try:
        # Validate file type
        if file.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail="File must be a PDF")
        
        # Read file data
        guide_data = await file.read()
        
        # Upload to storage
        guide_url = await service.upload_brand_guide(
            tenant_id=tenant_id,
            guide_data=guide_data,
            filename=file.filename or "brand-guide.pdf"
        )
        
        if not guide_url:
            raise HTTPException(status_code=500, detail="Failed to upload brand guide")
        
        return {
            "tenant_id": tenant_id,
            "guide_url": guide_url,
            "uploaded": True
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload brand guide for {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/global",
    summary="Get global branding defaults",
    description="Get global default branding configuration"
)
async def get_global_branding(
    service: BrandingService = Depends(get_branding_service)
):
    """Get global default branding."""
    try:
        branding = await service.get_global_branding()
        
        return {
            "logo_url": branding.logo_url,
            "primary_color": branding.primary_color,
            "secondary_color": branding.secondary_color,
            "accent_color": branding.accent_color,
            "font_family": branding.font_family,
            "custom_css": branding.custom_css
        }
    except Exception as e:
        logger.error(f"Failed to get global branding: {e}")
        raise HTTPException(status_code=500, detail=str(e))
