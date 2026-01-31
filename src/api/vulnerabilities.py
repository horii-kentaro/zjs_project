"""
FastAPI endpoints for vulnerability management.

This module provides REST API endpoints for vulnerability data:
- GET / - HTML page rendering (Jinja2 template)
- GET /api/vulnerabilities - JSON API with search, sort, pagination
- GET /api/vulnerabilities/{cve_id} - Detailed vulnerability information
- POST /api/fetch-now - Fetch latest vulnerabilities from JVN iPedia API
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.database import get_db
from src.fetchers.jvn_fetcher import JVNFetcherService
from src.schemas.vulnerability import VulnerabilityListResponse, VulnerabilityResponse
from src.services.database_vulnerability_service import DatabaseVulnerabilityService

logger = logging.getLogger(__name__)

# Router for vulnerability endpoints
router = APIRouter()

# Jinja2 templates configuration
templates = Jinja2Templates(directory="src/templates")


@router.get("/", response_class=HTMLResponse, tags=["Frontend"])
async def get_vulnerabilities_page(request: Request):
    """
    Render vulnerability list page (HTML).

    This endpoint serves the main vulnerability list page using Jinja2 template.
    The page is public (no authentication required).

    Args:
        request: FastAPI request object

    Returns:
        HTMLResponse: Rendered HTML page
    """
    logger.info("Rendering vulnerability list page")
    return templates.TemplateResponse("vulnerabilities.html", {"request": request})


@router.get("/api/vulnerabilities", response_model=VulnerabilityListResponse, tags=["API"])
async def list_vulnerabilities(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: Optional[int] = Query(None, ge=1, le=100, description="Number of items per page (deprecated, use limit)"),
    limit: Optional[int] = Query(None, ge=1, le=100, description="Number of items per page"),
    sort_by: str = Query(
        "modified_date",
        description="Sort field (published_date, modified_date, severity, cvss_score)",
    ),
    sort_order: str = Query("desc", description="Sort order (asc or desc)"),
    search: Optional[str] = Query(None, description="Search keyword (CVE ID or title)"),
    db: Session = Depends(get_db),
):
    """
    Get paginated vulnerability list with search and sort functionality.

    This endpoint returns vulnerability data as JSON with support for:
    - Pagination (page, page_size)
    - Sorting (sort_by, sort_order)
    - Search (CVE ID or title partial match)

    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page (1-100)
        sort_by: Sort field
        sort_order: Sort order (asc or desc)
        search: Search keyword
        db: Database session (dependency injection)

    Returns:
        VulnerabilityListResponse: Paginated vulnerability list

    Raises:
        HTTPException: 400 for invalid parameters, 500 for server errors
    """
    try:
        # Validate sort_by parameter
        valid_sort_fields = {"cve_id", "title", "published_date", "modified_date", "severity", "cvss_score"}
        if sort_by not in valid_sort_fields:
            logger.warning(f"Invalid sort_by parameter: {sort_by}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid sort_by parameter. Must be one of: {valid_sort_fields}",
            )

        # Validate sort_order parameter
        valid_sort_orders = {"asc", "desc"}
        if sort_order not in valid_sort_orders:
            logger.warning(f"Invalid sort_order parameter: {sort_order}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid sort_order parameter. Must be one of: {valid_sort_orders}",
            )

        # Support both 'limit' and 'page_size' parameters (limit takes precedence)
        items_per_page = limit or page_size or 50

        logger.info(
            f"API request: page={page}, limit={items_per_page}, "
            f"sort_by={sort_by}, sort_order={sort_order}, search={search}"
        )

        # Use database service for real data
        service = DatabaseVulnerabilityService(db)
        result = service.search_vulnerabilities(
            page=page,
            page_size=items_per_page,
            sort_by=sort_by,
            sort_order=sort_order,
            search=search,
        )

        logger.info(f"Returning {len(result.items)} vulnerabilities (page {page}/{result.total_pages})")
        return result

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching vulnerabilities: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database connection error")
    except Exception as e:
        logger.error(f"Error fetching vulnerabilities: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/api/vulnerabilities/{cve_id}",
    response_model=VulnerabilityResponse,
    tags=["API"],
)
async def get_vulnerability_detail(cve_id: str, db: Session = Depends(get_db)):
    """
    Get detailed vulnerability information by CVE ID.

    This endpoint returns detailed information for a specific vulnerability.
    Used for modal display in the frontend.

    Args:
        cve_id: CVE identifier (e.g., CVE-2024-0001)
        db: Database session (dependency injection)

    Returns:
        VulnerabilityResponse: Detailed vulnerability information

    Raises:
        HTTPException: 404 if CVE not found, 500 for server errors
    """
    try:
        logger.info(f"API request for vulnerability detail: {cve_id}")

        # Use database service for real data
        service = DatabaseVulnerabilityService(db)
        vulnerability = service.get_vulnerability_by_cve_id(cve_id)

        if not vulnerability:
            logger.warning(f"Vulnerability not found: {cve_id}")
            raise HTTPException(status_code=404, detail=f"Vulnerability not found: {cve_id}")

        logger.info(f"Returning vulnerability detail: {cve_id}")
        return vulnerability

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching vulnerability {cve_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database connection error")
    except Exception as e:
        logger.error(f"Error fetching vulnerability {cve_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


class FetchNowResponse(BaseModel):
    """Response model for fetch-now endpoint"""

    success: bool
    message: str
    fetched: int
    inserted: int
    updated: int
    failed: int
    elapsed_seconds: float


@router.post("/api/fetch-now", response_model=FetchNowResponse, tags=["API"])
async def fetch_vulnerabilities_now(db: Session = Depends(get_db)):
    """
    Fetch latest vulnerabilities from JVN iPedia API in real-time.

    This endpoint triggers an immediate fetch of vulnerability data from JVN iPedia API
    and stores it in the database. It uses differential fetching (fetches only new/updated
    data since last fetch) for better performance.

    Returns:
        FetchNowResponse: Result of the fetch operation

    Raises:
        HTTPException: 500 for server errors
    """
    start_time = datetime.now()

    try:
        logger.info("Manual fetch triggered via API")

        # Initialize services
        fetcher = JVNFetcherService()
        service = DatabaseVulnerabilityService(db)

        # Get latest modified date from database for differential fetching
        latest_modified = service.get_latest_modified_date()

        # Determine fetch strategy
        if latest_modified:
            # Differential fetch: only fetch data modified since last update
            logger.info(f"Differential fetch: fetching data since {latest_modified}")
            latest_date = datetime.fromisoformat(latest_modified)
            # Fetch from last modified date to now
            vulnerabilities = await fetcher.fetch_since_last_update(latest_date)
        else:
            # Initial fetch: fetch last 3 years of data
            logger.info("Initial fetch: no existing data, fetching last 3 years")
            end_date = datetime.now()
            start_date = end_date - timedelta(days=3 * 365)
            logger.info(f"Fetching vulnerabilities from {start_date.date()} to {end_date.date()}")
            vulnerabilities = await fetcher.fetch_vulnerabilities(
                start_date=start_date.strftime("%Y-%m-%d"), end_date=end_date.strftime("%Y-%m-%d")
            )

        fetched_count = len(vulnerabilities)
        logger.info(f"Fetched {fetched_count} vulnerabilities from JVN iPedia API")

        # Store in database (service already initialized above)
        result = service.upsert_vulnerabilities_batch(vulnerabilities)

        elapsed = (datetime.now() - start_time).total_seconds()

        logger.info(
            f'Fetch completed: fetched={fetched_count}, inserted={result["inserted"]}, '
            f'updated={result["updated"]}, failed={result["failed"]}, elapsed={elapsed:.2f}s'
        )

        return FetchNowResponse(
            success=True,
            message=f"Successfully fetched {fetched_count} vulnerabilities from JVN iPedia",
            fetched=fetched_count,
            inserted=result["inserted"],
            updated=result["updated"],
            failed=result["failed"],
            elapsed_seconds=elapsed,
        )

    except Exception as e:
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.error(f"Error during manual fetch: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch vulnerabilities: {str(e)}",
        )
