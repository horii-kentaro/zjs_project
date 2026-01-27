"""
Pydantic schemas for Matching API.

These schemas define request/response models for matching execution endpoints.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class MatchingExecutionResponse(BaseModel):
    """Schema for matching execution response."""

    total_assets: int = Field(..., description="Total number of assets processed")
    total_vulnerabilities: int = Field(..., description="Total number of vulnerabilities processed")
    total_matches: int = Field(..., description="Total number of matches found")
    exact_matches: int = Field(..., description="Number of exact matches")
    version_range_matches: int = Field(..., description="Number of version range matches")
    wildcard_matches: int = Field(..., description="Number of wildcard matches")
    execution_time_seconds: Optional[float] = Field(None, description="Execution time in seconds")

    class Config:
        json_schema_extra = {
            "example": {
                "total_assets": 150,
                "total_vulnerabilities": 963,
                "total_matches": 42,
                "exact_matches": 15,
                "version_range_matches": 20,
                "wildcard_matches": 7,
                "execution_time_seconds": 12.5,
            }
        }


class MatchingResultResponse(BaseModel):
    """Schema for individual matching result."""

    match_id: str = Field(..., description="Match UUID")
    asset_id: str = Field(..., description="Asset UUID")
    asset_name: str = Field(..., description="Asset name")
    cve_id: str = Field(..., description="CVE ID")
    vulnerability_title: str = Field(..., description="Vulnerability title")
    severity: Optional[str] = Field(None, description="Severity level")
    cvss_score: Optional[float] = Field(None, description="CVSS base score")
    match_reason: str = Field(..., description="Match reason")
    matched_at: datetime = Field(..., description="Match timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "match_id": "650e8400-e29b-41d4-a716-446655440000",
                "asset_id": "550e8400-e29b-41d4-a716-446655440000",
                "asset_name": "Production API Server - Nginx",
                "cve_id": "CVE-2024-0001",
                "vulnerability_title": "Nginx HTTP/2 Buffer Overflow",
                "severity": "Critical",
                "cvss_score": 9.8,
                "match_reason": "exact_match",
                "matched_at": "2026-01-27T09:00:00Z",
            }
        }


class MatchingResultListResponse(BaseModel):
    """Schema for matching result list response."""

    items: list[MatchingResultResponse] = Field(..., description="List of matching results")
    total: int = Field(..., description="Total number of matches")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Items per page")

    class Config:
        json_schema_extra = {
            "example": {
                "items": [
                    {
                        "match_id": "650e8400-e29b-41d4-a716-446655440000",
                        "asset_id": "550e8400-e29b-41d4-a716-446655440000",
                        "asset_name": "Production API Server - Nginx",
                        "cve_id": "CVE-2024-0001",
                        "vulnerability_title": "Nginx HTTP/2 Buffer Overflow",
                        "severity": "Critical",
                        "cvss_score": 9.8,
                        "match_reason": "exact_match",
                        "matched_at": "2026-01-27T09:00:00Z",
                    }
                ],
                "total": 42,
                "page": 1,
                "limit": 50,
            }
        }


class AssetVulnerabilityListResponse(BaseModel):
    """Schema for asset's vulnerability list response."""

    asset_id: str = Field(..., description="Asset UUID")
    asset_name: str = Field(..., description="Asset name")
    vulnerabilities: list[dict] = Field(..., description="List of vulnerabilities affecting this asset")
    total_vulnerabilities: int = Field(..., description="Total number of vulnerabilities")

    class Config:
        json_schema_extra = {
            "example": {
                "asset_id": "550e8400-e29b-41d4-a716-446655440000",
                "asset_name": "Production API Server - Nginx",
                "vulnerabilities": [
                    {
                        "cve_id": "CVE-2024-0001",
                        "title": "Nginx HTTP/2 Buffer Overflow",
                        "severity": "Critical",
                        "cvss_score": 9.8,
                        "match_reason": "exact_match",
                        "matched_at": "2026-01-27T09:00:00Z",
                    }
                ],
                "total_vulnerabilities": 3,
            }
        }


class DashboardResponse(BaseModel):
    """Schema for dashboard statistics response."""

    affected_assets_count: int = Field(..., description="Number of affected assets")
    total_matches: int = Field(..., description="Total number of matches")
    critical_vulnerabilities: int = Field(..., description="Number of Critical vulnerabilities")
    high_vulnerabilities: int = Field(..., description="Number of High vulnerabilities")
    medium_vulnerabilities: int = Field(..., description="Number of Medium vulnerabilities")
    low_vulnerabilities: int = Field(..., description="Number of Low vulnerabilities")
    last_matching_at: Optional[datetime] = Field(None, description="Last matching execution timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "affected_assets_count": 35,
                "total_matches": 42,
                "critical_vulnerabilities": 8,
                "high_vulnerabilities": 15,
                "medium_vulnerabilities": 12,
                "low_vulnerabilities": 7,
                "last_matching_at": "2026-01-27T09:00:00Z",
            }
        }
