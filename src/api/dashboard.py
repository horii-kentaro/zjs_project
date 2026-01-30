"""
FastAPI endpoints for dashboard data.

This module provides REST API endpoints for dashboard widgets:
- GET /api/dashboard/summary - Summary data with severity counts and previous week comparison
- GET /api/dashboard/trend - Trend data with daily vulnerability detection counts
- GET /api/dashboard/severity-distribution - Severity distribution data
- GET /api/dashboard/asset-ranking - Asset ranking by vulnerability count (TOP 10)
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, case, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.database import get_db
from src.models.asset import Asset, AssetVulnerabilityMatch
from src.models.vulnerability import Vulnerability
from src.schemas.dashboard import (
    AssetRankingResponse,
    DashboardSummaryResponse,
    SeverityDistributionResponse,
    SeverityCountsSchema,
    TrendDataPointSchema,
    TrendDataResponse,
    AssetRankingItemSchema,
)

logger = logging.getLogger(__name__)

# Router for dashboard endpoints
router = APIRouter(prefix="/api/dashboard")


@router.get("/summary", response_model=DashboardSummaryResponse, tags=["Dashboard"])
async def get_dashboard_summary(db: Session = Depends(get_db)):
    """
    Get dashboard summary data with severity counts and previous week comparison.

    This endpoint returns:
    - Current severity counts (Critical/High/Medium/Low)
    - Previous week severity counts (7 days ago)

    Args:
        db: Database session (dependency injection)

    Returns:
        DashboardSummaryResponse: Summary data with severity counts

    Raises:
        HTTPException: 500 for server errors
    """
    try:
        logger.info("Fetching dashboard summary data")

        # Current severity counts
        current_counts = (
            db.query(
                Vulnerability.severity,
                func.count(Vulnerability.cve_id).label("count"),
            )
            .group_by(Vulnerability.severity)
            .all()
        )

        # 7 days ago
        seven_days_ago = datetime.now() - timedelta(days=7)

        # Previous week severity counts (published_date <= seven_days_ago)
        prev_counts = (
            db.query(
                Vulnerability.severity,
                func.count(Vulnerability.cve_id).label("count"),
            )
            .filter(Vulnerability.published_date <= seven_days_ago)
            .group_by(Vulnerability.severity)
            .all()
        )

        # Convert to dictionaries
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        prev_severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}

        for severity, count in current_counts:
            if severity:
                severity_counts[severity.lower()] = count

        for severity, count in prev_counts:
            if severity:
                prev_severity_counts[severity.lower()] = count

        logger.info(
            f"Dashboard summary fetched: current={severity_counts}, previous={prev_severity_counts}"
        )

        return DashboardSummaryResponse(
            severityCounts=SeverityCountsSchema(**severity_counts),
            prevSeverityCounts=SeverityCountsSchema(**prev_severity_counts),
        )

    except SQLAlchemyError as e:
        logger.error(f"Database error fetching dashboard summary: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database connection error")
    except Exception as e:
        logger.error(f"Error fetching dashboard summary: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/trend", response_model=TrendDataResponse, tags=["Dashboard"])
async def get_dashboard_trend(
    days: int = Query(30, ge=1, le=365, description="Number of days to fetch trend data"),
    db: Session = Depends(get_db),
):
    """
    Get dashboard trend data with daily vulnerability detection counts.

    This endpoint returns:
    - Daily vulnerability counts based on published_date
    - Data points for the specified number of days (default: 30)

    Args:
        days: Number of days to fetch trend data (1-365)
        db: Database session (dependency injection)

    Returns:
        TrendDataResponse: Trend data with daily counts

    Raises:
        HTTPException: 500 for server errors
    """
    try:
        logger.info(f"Fetching dashboard trend data for {days} days")

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days - 1)

        # Query daily counts
        daily_counts = (
            db.query(
                func.date(Vulnerability.published_date).label("date"),
                func.count(Vulnerability.cve_id).label("detected"),
            )
            .filter(
                and_(
                    Vulnerability.published_date >= start_date,
                    Vulnerability.published_date <= end_date,
                )
            )
            .group_by(func.date(Vulnerability.published_date))
            .order_by(func.date(Vulnerability.published_date))
            .all()
        )

        # Convert to list of TrendDataPointSchema
        data_points = []
        for date_obj, detected in daily_counts:
            data_points.append(
                TrendDataPointSchema(
                    date=date_obj.strftime("%Y-%m-%d") if hasattr(date_obj, 'strftime') else str(date_obj),
                    detected=detected,
                )
            )

        logger.info(f"Dashboard trend data fetched: {len(data_points)} data points")

        return TrendDataResponse(dataPoints=data_points)

    except SQLAlchemyError as e:
        logger.error(f"Database error fetching dashboard trend: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database connection error")
    except Exception as e:
        logger.error(f"Error fetching dashboard trend: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/severity-distribution", response_model=SeverityDistributionResponse, tags=["Dashboard"])
async def get_severity_distribution(db: Session = Depends(get_db)):
    """
    Get severity distribution data.

    This endpoint returns:
    - Counts of vulnerabilities by severity level (Critical/High/Medium/Low)

    Args:
        db: Database session (dependency injection)

    Returns:
        SeverityDistributionResponse: Severity distribution data

    Raises:
        HTTPException: 500 for server errors
    """
    try:
        logger.info("Fetching severity distribution data")

        # Query severity counts
        severity_counts = (
            db.query(
                Vulnerability.severity,
                func.count(Vulnerability.cve_id).label("count"),
            )
            .group_by(Vulnerability.severity)
            .all()
        )

        # Convert to dictionary
        distribution = {"critical": 0, "high": 0, "medium": 0, "low": 0}

        for severity, count in severity_counts:
            if severity:
                distribution[severity.lower()] = count

        logger.info(f"Severity distribution fetched: {distribution}")

        return SeverityDistributionResponse(**distribution)

    except SQLAlchemyError as e:
        logger.error(f"Database error fetching severity distribution: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database connection error")
    except Exception as e:
        logger.error(f"Error fetching severity distribution: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/asset-ranking", response_model=AssetRankingResponse, tags=["Dashboard"])
async def get_asset_ranking(db: Session = Depends(get_db)):
    """
    Get asset ranking by vulnerability count (TOP 10).

    This endpoint returns:
    - Assets ranked by total vulnerability count
    - Critical and high vulnerability counts for each asset
    - Limited to TOP 10 assets

    Args:
        db: Database session (dependency injection)

    Returns:
        AssetRankingResponse: Asset ranking data

    Raises:
        HTTPException: 500 for server errors
    """
    try:
        logger.info("Fetching asset ranking data")

        # Query asset ranking with JOIN
        # Count total vulnerabilities, critical, and high for each asset
        ranking_query = (
            db.query(
                Asset.asset_id,
                Asset.asset_name,
                func.count(AssetVulnerabilityMatch.match_id).label("vulnerability_count"),
                func.sum(
                    case(
                        (Vulnerability.severity == "Critical", 1),
                        else_=0,
                    )
                ).label("critical_count"),
                func.sum(
                    case(
                        (Vulnerability.severity == "High", 1),
                        else_=0,
                    )
                ).label("high_count"),
            )
            .join(AssetVulnerabilityMatch, Asset.asset_id == AssetVulnerabilityMatch.asset_id)
            .join(Vulnerability, AssetVulnerabilityMatch.cve_id == Vulnerability.cve_id)
            .group_by(Asset.asset_id, Asset.asset_name)
            .order_by(func.count(AssetVulnerabilityMatch.match_id).desc())
            .limit(10)
            .all()
        )

        # Convert to list of AssetRankingItemSchema
        ranking = []
        for asset_id, asset_name, vuln_count, critical_count, high_count in ranking_query:
            ranking.append(
                AssetRankingItemSchema(
                    asset_id=asset_id,
                    asset_name=asset_name,
                    vulnerability_count=vuln_count,
                    critical_count=critical_count or 0,
                    high_count=high_count or 0,
                )
            )

        logger.info(f"Asset ranking fetched: {len(ranking)} assets")

        return AssetRankingResponse(ranking=ranking)

    except SQLAlchemyError as e:
        logger.error(f"Database error fetching asset ranking: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database connection error")
    except Exception as e:
        logger.error(f"Error fetching asset ranking: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
