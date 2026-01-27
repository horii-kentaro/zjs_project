"""
Pydantic schemas for Asset API.

These schemas define request/response models for asset management endpoints.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class AssetCreate(BaseModel):
    """Schema for creating a new asset (manual registration)."""

    asset_name: str = Field(..., min_length=1, max_length=200, description="Asset name")
    vendor: str = Field(..., min_length=1, max_length=100, description="Vendor name")
    product: str = Field(..., min_length=1, max_length=100, description="Product name")
    version: str = Field(..., min_length=1, max_length=50, description="Version")

    @field_validator("asset_name", "vendor", "product", "version")
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Validate that string fields are not empty after stripping."""
        if not v.strip():
            raise ValueError("Field cannot be empty or whitespace only")
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "asset_name": "Production API Server - Nginx",
                "vendor": "nginx",
                "product": "nginx",
                "version": "1.25.3",
            }
        }


class AssetUpdate(BaseModel):
    """Schema for updating an existing asset."""

    asset_name: Optional[str] = Field(None, min_length=1, max_length=200, description="Asset name")
    version: Optional[str] = Field(None, min_length=1, max_length=50, description="Version")

    @field_validator("asset_name", "version")
    @classmethod
    def validate_not_empty(cls, v: Optional[str]) -> Optional[str]:
        """Validate that string fields are not empty after stripping."""
        if v is not None and not v.strip():
            raise ValueError("Field cannot be empty or whitespace only")
        return v.strip() if v is not None else None

    class Config:
        json_schema_extra = {
            "example": {
                "asset_name": "Production API Server - Nginx (Updated)",
                "version": "1.25.4",
            }
        }


class AssetResponse(BaseModel):
    """Schema for asset response."""

    asset_id: str = Field(..., description="Asset UUID")
    asset_name: str = Field(..., description="Asset name")
    vendor: str = Field(..., description="Vendor name")
    product: str = Field(..., description="Product name")
    version: str = Field(..., description="Version")
    cpe_code: str = Field(..., description="CPE 2.3 code")
    source: str = Field(..., description="Source type (manual/composer/npm/docker)")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "asset_id": "550e8400-e29b-41d4-a716-446655440000",
                "asset_name": "Production API Server - Nginx",
                "vendor": "nginx",
                "product": "nginx",
                "version": "1.25.3",
                "cpe_code": "cpe:2.3:a:nginx:nginx:1.25.3:*:*:*:*:*:*:*",
                "source": "manual",
                "created_at": "2026-01-27T09:00:00Z",
                "updated_at": "2026-01-27T09:00:00Z",
            }
        }


class AssetListResponse(BaseModel):
    """Schema for asset list response."""

    items: list[AssetResponse] = Field(..., description="List of assets")
    total: int = Field(..., description="Total number of assets")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Items per page")

    class Config:
        json_schema_extra = {
            "example": {
                "items": [
                    {
                        "asset_id": "550e8400-e29b-41d4-a716-446655440000",
                        "asset_name": "Production API Server - Nginx",
                        "vendor": "nginx",
                        "product": "nginx",
                        "version": "1.25.3",
                        "cpe_code": "cpe:2.3:a:nginx:nginx:1.25.3:*:*:*:*:*:*:*",
                        "source": "manual",
                        "created_at": "2026-01-27T09:00:00Z",
                        "updated_at": "2026-01-27T09:00:00Z",
                    }
                ],
                "total": 150,
                "page": 1,
                "limit": 50,
            }
        }


class FileImportResponse(BaseModel):
    """Schema for file import response."""

    imported_count: int = Field(..., description="Number of assets imported")
    skipped_count: int = Field(..., description="Number of assets skipped (duplicates)")
    errors: list[str] = Field(default_factory=list, description="List of error messages")

    class Config:
        json_schema_extra = {
            "example": {
                "imported_count": 25,
                "skipped_count": 3,
                "errors": [],
            }
        }
