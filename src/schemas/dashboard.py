"""
Pydantic schemas for Dashboard API requests and responses.

This module defines Pydantic models for dashboard widget data.
All schemas follow the OpenAPI specification for FastAPI integration.
"""

from datetime import date
from typing import List

from pydantic import BaseModel, Field


class SeverityCountsSchema(BaseModel):
    """Schema for severity counts."""

    critical: int = Field(0, ge=0, description="Number of critical vulnerabilities")
    high: int = Field(0, ge=0, description="Number of high vulnerabilities")
    medium: int = Field(0, ge=0, description="Number of medium vulnerabilities")
    low: int = Field(0, ge=0, description="Number of low vulnerabilities")

    model_config = {
        "json_schema_extra": {
            "example": {
                "critical": 100,
                "high": 200,
                "medium": 300,
                "low": 50,
            }
        }
    }


class DashboardSummaryResponse(BaseModel):
    """
    Schema for dashboard summary response.

    Used by GET /api/dashboard/summary endpoint.
    """

    severityCounts: SeverityCountsSchema = Field(..., description="Current severity counts")
    prevSeverityCounts: SeverityCountsSchema = Field(..., description="Previous week severity counts")

    model_config = {
        "json_schema_extra": {
            "example": {
                "severityCounts": {
                    "critical": 100,
                    "high": 200,
                    "medium": 300,
                    "low": 50,
                },
                "prevSeverityCounts": {
                    "critical": 95,
                    "high": 190,
                    "medium": 290,
                    "low": 48,
                },
            }
        }
    }


class TrendDataPointSchema(BaseModel):
    """Schema for a single trend data point."""

    date: str = Field(..., description="Date in YYYY-MM-DD format")
    detected: int = Field(0, ge=0, description="Number of vulnerabilities detected on this date")

    model_config = {
        "json_schema_extra": {
            "example": {
                "date": "2026-01-01",
                "detected": 10,
            }
        }
    }


class TrendDataResponse(BaseModel):
    """
    Schema for trend data response.

    Used by GET /api/dashboard/trend endpoint.
    """

    dataPoints: List[TrendDataPointSchema] = Field(..., description="List of trend data points")

    model_config = {
        "json_schema_extra": {
            "example": {
                "dataPoints": [
                    {"date": "2026-01-01", "detected": 10},
                    {"date": "2026-01-02", "detected": 15},
                    {"date": "2026-01-03", "detected": 8},
                ]
            }
        }
    }


class SeverityDistributionResponse(BaseModel):
    """
    Schema for severity distribution response.

    Used by GET /api/dashboard/severity-distribution endpoint.
    """

    critical: int = Field(0, ge=0, description="Number of critical vulnerabilities")
    high: int = Field(0, ge=0, description="Number of high vulnerabilities")
    medium: int = Field(0, ge=0, description="Number of medium vulnerabilities")
    low: int = Field(0, ge=0, description="Number of low vulnerabilities")

    model_config = {
        "json_schema_extra": {
            "example": {
                "critical": 100,
                "high": 200,
                "medium": 300,
                "low": 50,
            }
        }
    }


class AssetRankingItemSchema(BaseModel):
    """Schema for a single asset ranking item."""

    asset_id: str = Field(..., description="Asset unique identifier (UUID)")
    asset_name: str = Field(..., description="Asset name")
    vulnerability_count: int = Field(0, ge=0, description="Total number of vulnerabilities for this asset")
    critical_count: int = Field(0, ge=0, description="Number of critical vulnerabilities")
    high_count: int = Field(0, ge=0, description="Number of high vulnerabilities")

    model_config = {
        "json_schema_extra": {
            "example": {
                "asset_id": "123e4567-e89b-12d3-a456-426614174000",
                "asset_name": "Production API Server",
                "vulnerability_count": 15,
                "critical_count": 3,
                "high_count": 8,
            }
        }
    }


class AssetRankingResponse(BaseModel):
    """
    Schema for asset ranking response.

    Used by GET /api/dashboard/asset-ranking endpoint.
    """

    ranking: List[AssetRankingItemSchema] = Field(..., description="List of assets ranked by vulnerability count")

    model_config = {
        "json_schema_extra": {
            "example": {
                "ranking": [
                    {
                        "asset_id": "123e4567-e89b-12d3-a456-426614174000",
                        "asset_name": "Production API Server",
                        "vulnerability_count": 15,
                        "critical_count": 3,
                        "high_count": 8,
                    },
                    {
                        "asset_id": "223e4567-e89b-12d3-a456-426614174001",
                        "asset_name": "Database Server",
                        "vulnerability_count": 12,
                        "critical_count": 2,
                        "high_count": 6,
                    },
                ]
            }
        }
    }
