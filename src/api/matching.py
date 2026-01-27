"""
Matching execution API endpoints.

This module provides REST API endpoints for:
- Matching execution (POST /api/matching/execute)
- Matching results retrieval (GET /api/matching/results)
- Asset-specific vulnerability list (GET /api/assets/{asset_id}/vulnerabilities)
- Dashboard statistics (GET /api/matching/dashboard)
"""

import logging
import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import distinct, func
from sqlalchemy.orm import Session

from src.database import get_db
from src.models.asset import Asset, AssetVulnerabilityMatch
from src.models.vulnerability import Vulnerability
from src.schemas.matching import (
    AssetVulnerabilityListResponse,
    DashboardResponse,
    MatchingExecutionResponse,
    MatchingResultListResponse,
    MatchingResultResponse,
)
from src.services.matching_service import execute_full_matching

router = APIRouter(tags=["matching"])
logger = logging.getLogger(__name__)
templates = Jinja2Templates(directory="src/templates")


@router.get("/matching", response_class=HTMLResponse, tags=["Frontend"])
async def get_matching_page(request: Request):
    """
    Render matching results page (HTML).

    This page provides:
    - Matching execution
    - Dashboard statistics
    - Matching results list with filtering
    - Pagination

    Args:
        request: FastAPI request object

    Returns:
        HTMLResponse: Rendered HTML page
    """
    logger.info("Rendering matching results page")
    return templates.TemplateResponse("matching_results.html", {"request": request})


@router.post("/api/matching/execute", response_model=MatchingExecutionResponse)
def execute_matching(db: Session = Depends(get_db)):
    """
    Execute matching for all assets and vulnerabilities.

    This is a batch process that matches all assets against all vulnerabilities
    and stores the results in the database.

    Args:
        db: Database session

    Returns:
        Matching execution statistics
    """
    logger.info("Starting matching execution...")

    start_time = time.time()

    try:
        stats = execute_full_matching(db)
        execution_time = time.time() - start_time

        logger.info(f"Matching execution completed in {execution_time:.2f}s: {stats}")

        return MatchingExecutionResponse(**stats, execution_time_seconds=round(execution_time, 2))

    except Exception as e:
        logger.error(f"Matching execution failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Matching execution failed: {str(e)}"
        )


@router.get("/api/matching/results", response_model=MatchingResultListResponse)
def get_matching_results(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    severity: Optional[str] = Query(None, description="Filter by severity (Critical/High/Medium/Low)"),
    source: Optional[str] = Query(None, description="Filter by asset source (manual/composer/npm/docker)"),
    db: Session = Depends(get_db),
):
    """
    Retrieve matching results with pagination and filtering.

    Args:
        page: Page number (starting from 1)
        limit: Items per page (max 100)
        severity: Optional filter by severity level
        source: Optional filter by asset source type
        db: Database session

    Returns:
        Paginated matching results
    """
    logger.info(f"Fetching matching results: page={page}, limit={limit}, severity={severity}, source={source}")

    # Build query with joins
    query = (
        db.query(
            AssetVulnerabilityMatch.match_id,
            AssetVulnerabilityMatch.asset_id,
            Asset.asset_name,
            AssetVulnerabilityMatch.cve_id,
            Vulnerability.title.label("vulnerability_title"),
            Vulnerability.severity,
            Vulnerability.cvss_score,
            AssetVulnerabilityMatch.match_reason,
            AssetVulnerabilityMatch.matched_at,
        )
        .join(Asset, AssetVulnerabilityMatch.asset_id == Asset.asset_id)
        .join(Vulnerability, AssetVulnerabilityMatch.cve_id == Vulnerability.cve_id)
    )

    # Apply filters
    if severity:
        if severity not in ["Critical", "High", "Medium", "Low"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid severity: {severity}. Must be one of: Critical, High, Medium, Low",
            )
        query = query.filter(Vulnerability.severity == severity)

    if source:
        if source not in ["manual", "composer", "npm", "docker"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid source: {source}. Must be one of: manual, composer, npm, docker",
            )
        query = query.filter(Asset.source == source)

    # Get total count
    total = query.count()

    # Apply pagination and sorting
    offset = (page - 1) * limit
    results = query.order_by(AssetVulnerabilityMatch.matched_at.desc()).offset(offset).limit(limit).all()

    # Convert to response model
    items = [
        MatchingResultResponse(
            match_id=str(r.match_id),
            asset_id=str(r.asset_id),
            asset_name=r.asset_name,
            cve_id=r.cve_id,
            vulnerability_title=r.vulnerability_title,
            severity=r.severity,
            cvss_score=r.cvss_score,
            match_reason=r.match_reason,
            matched_at=r.matched_at,
        )
        for r in results
    ]

    logger.info(f"Fetched {len(items)} matching results (total: {total})")

    return MatchingResultListResponse(items=items, total=total, page=page, limit=limit)


@router.get("/api/matching/assets/{asset_id}/vulnerabilities", response_model=AssetVulnerabilityListResponse)
def get_asset_vulnerabilities(asset_id: str, db: Session = Depends(get_db)):
    """
    Retrieve all vulnerabilities affecting a specific asset.

    Args:
        asset_id: Asset UUID
        db: Database session

    Returns:
        List of vulnerabilities affecting the asset

    Raises:
        HTTPException: 404 if asset not found
    """
    logger.info(f"Fetching vulnerabilities for asset: {asset_id}")

    # Check if asset exists
    asset = db.query(Asset).filter(Asset.asset_id == asset_id).first()
    if not asset:
        logger.warning(f"Asset not found: {asset_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Asset not found: {asset_id}")

    # Get matching results for this asset
    matches = (
        db.query(
            Vulnerability.cve_id,
            Vulnerability.title,
            Vulnerability.severity,
            Vulnerability.cvss_score,
            AssetVulnerabilityMatch.match_reason,
            AssetVulnerabilityMatch.matched_at,
        )
        .join(AssetVulnerabilityMatch, Vulnerability.cve_id == AssetVulnerabilityMatch.cve_id)
        .filter(AssetVulnerabilityMatch.asset_id == asset_id)
        .order_by(Vulnerability.cvss_score.desc().nullslast())
        .all()
    )

    # Convert to dict format
    vulnerabilities = [
        {
            "cve_id": m.cve_id,
            "title": m.title,
            "severity": m.severity,
            "cvss_score": m.cvss_score,
            "match_reason": m.match_reason,
            "matched_at": m.matched_at,
        }
        for m in matches
    ]

    logger.info(f"Found {len(vulnerabilities)} vulnerabilities for asset {asset_id}")

    return AssetVulnerabilityListResponse(
        asset_id=str(asset.asset_id),
        asset_name=asset.asset_name,
        vulnerabilities=vulnerabilities,
        total_vulnerabilities=len(vulnerabilities),
    )


@router.get("/api/matching/dashboard", response_model=DashboardResponse)
def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    Retrieve dashboard statistics.

    Returns aggregate statistics about matching results:
    - Number of affected assets
    - Total matches
    - Breakdown by severity level
    - Last matching execution timestamp

    Args:
        db: Database session

    Returns:
        Dashboard statistics
    """
    logger.info("Fetching dashboard statistics...")

    # Count affected assets (distinct)
    affected_assets_count = db.query(func.count(distinct(AssetVulnerabilityMatch.asset_id))).scalar() or 0

    # Total matches
    total_matches = db.query(func.count(AssetVulnerabilityMatch.match_id)).scalar() or 0

    # Count vulnerabilities by severity
    severity_counts = (
        db.query(Vulnerability.severity, func.count(distinct(AssetVulnerabilityMatch.match_id)))
        .join(AssetVulnerabilityMatch, Vulnerability.cve_id == AssetVulnerabilityMatch.cve_id)
        .group_by(Vulnerability.severity)
        .all()
    )

    severity_map = {severity: count for severity, count in severity_counts}
    critical_vulnerabilities = severity_map.get("Critical", 0)
    high_vulnerabilities = severity_map.get("High", 0)
    medium_vulnerabilities = severity_map.get("Medium", 0)
    low_vulnerabilities = severity_map.get("Low", 0)

    # Last matching timestamp
    last_matching_result = db.query(func.max(AssetVulnerabilityMatch.matched_at)).scalar()

    logger.info(
        f"Dashboard stats: affected_assets={affected_assets_count}, total_matches={total_matches}, "
        f"critical={critical_vulnerabilities}, high={high_vulnerabilities}, "
        f"medium={medium_vulnerabilities}, low={low_vulnerabilities}"
    )

    return DashboardResponse(
        affected_assets_count=affected_assets_count,
        total_matches=total_matches,
        critical_vulnerabilities=critical_vulnerabilities,
        high_vulnerabilities=high_vulnerabilities,
        medium_vulnerabilities=medium_vulnerabilities,
        low_vulnerabilities=low_vulnerabilities,
        last_matching_at=last_matching_result,
    )
