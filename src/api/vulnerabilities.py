"""
FastAPI endpoints for vulnerability management.

This module provides REST API endpoints for vulnerability data:
- GET / - HTML page rendering (Jinja2 template)
- GET /api/vulnerabilities - JSON API with search, sort, pagination
- GET /api/vulnerabilities/{cve_id} - Detailed vulnerability information
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from src.schemas.vulnerability import VulnerabilityListResponse, VulnerabilityResponse
from src.services.mock_vulnerability_service import mock_service

logger = logging.getLogger(__name__)

# Router for vulnerability endpoints
router = APIRouter()

# Jinja2 templates configuration
templates = Jinja2Templates(directory='src/templates')


@router.get('/', response_class=HTMLResponse, tags=['Frontend'])
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
    logger.info('Rendering vulnerability list page')
    return templates.TemplateResponse('vulnerabilities.html', {'request': request})


@router.get('/api/vulnerabilities', response_model=VulnerabilityListResponse, tags=['API'])
async def list_vulnerabilities(
    page: int = Query(1, ge=1, description='Page number (1-indexed)'),
    page_size: int = Query(50, ge=1, le=100, description='Number of items per page'),
    sort_by: str = Query(
        'modified_date',
        description='Sort field (published_date, modified_date, severity, cvss_score)',
    ),
    sort_order: str = Query('desc', description='Sort order (asc or desc)'),
    search: Optional[str] = Query(None, description='Search keyword (CVE ID or title)'),
):
    """
    Get paginated vulnerability list with search and sort functionality.

    This endpoint returns vulnerability data as JSON with support for:
    - Pagination (page, page_size)
    - Sorting (sort_by, sort_order)
    - Search (CVE ID or title partial match)

    @MOCK_TO_API: Currently uses mock data. Replace with database queries in Phase 5.

    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page (1-100)
        sort_by: Sort field
        sort_order: Sort order (asc or desc)
        search: Search keyword

    Returns:
        VulnerabilityListResponse: Paginated vulnerability list

    Raises:
        HTTPException: 400 for invalid parameters, 500 for server errors
    """
    try:
        # Validate sort_by parameter
        valid_sort_fields = {'published_date', 'modified_date', 'severity', 'cvss_score'}
        if sort_by not in valid_sort_fields:
            logger.warning(f'Invalid sort_by parameter: {sort_by}')
            raise HTTPException(
                status_code=400,
                detail=f'Invalid sort_by parameter. Must be one of: {valid_sort_fields}',
            )

        # Validate sort_order parameter
        valid_sort_orders = {'asc', 'desc'}
        if sort_order not in valid_sort_orders:
            logger.warning(f'Invalid sort_order parameter: {sort_order}')
            raise HTTPException(
                status_code=400,
                detail=f'Invalid sort_order parameter. Must be one of: {valid_sort_orders}',
            )

        logger.info(
            f'API request: page={page}, page_size={page_size}, '
            f'sort_by={sort_by}, sort_order={sort_order}, search={search}'
        )

        # @MOCK_TO_API: Replace with database service
        result = mock_service.search_vulnerabilities(
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
            search=search,
        )

        logger.info(f'Returning {len(result.items)} vulnerabilities (page {page}/{result.total_pages})')
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Error fetching vulnerabilities: {str(e)}', exc_info=True)
        raise HTTPException(status_code=500, detail='Internal server error')


@router.get(
    '/api/vulnerabilities/{cve_id}',
    response_model=VulnerabilityResponse,
    tags=['API'],
)
async def get_vulnerability_detail(cve_id: str):
    """
    Get detailed vulnerability information by CVE ID.

    This endpoint returns detailed information for a specific vulnerability.
    Used for modal display in the frontend.

    @MOCK_TO_API: Currently uses mock data. Replace with database query in Phase 5.

    Args:
        cve_id: CVE identifier (e.g., CVE-2024-0001)

    Returns:
        VulnerabilityResponse: Detailed vulnerability information

    Raises:
        HTTPException: 404 if CVE not found, 500 for server errors
    """
    try:
        logger.info(f'API request for vulnerability detail: {cve_id}')

        # @MOCK_TO_API: Replace with database service
        vulnerability = mock_service.get_vulnerability_by_cve_id(cve_id)

        if not vulnerability:
            logger.warning(f'Vulnerability not found: {cve_id}')
            raise HTTPException(status_code=404, detail=f'Vulnerability not found: {cve_id}')

        logger.info(f'Returning vulnerability detail: {cve_id}')
        return vulnerability

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Error fetching vulnerability {cve_id}: {str(e)}', exc_info=True)
        raise HTTPException(status_code=500, detail='Internal server error')
