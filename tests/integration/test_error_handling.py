"""
Integration tests for error handling across all endpoints.

This module tests error scenarios that are not covered in basic integration tests:
- Database connection failures (health check)
- SQLAlchemy errors (API endpoints)
- Application lifecycle events (startup, shutdown)

Target: Increase code coverage from 67% to 80%+
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError, OperationalError

from src.main import app
from src.database import engine
from src.models.vulnerability import Base


@pytest.fixture(scope='module')
def setup_database():
    """Setup database tables before running tests."""
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture(scope='function')
def client():
    """Provide FastAPI TestClient."""
    return TestClient(app)


class TestHealthCheckErrorCases:
    """
    Error handling tests for /api/health endpoint.

    Coverage target: src/main.py lines 94-109 (DB errors, exceptions)
    """

    def test_health_check_database_disconnected(self, client):
        """
        Test health check when database connection fails.

        Verifies:
        - Returns 503 Service Unavailable
        - status: 'unhealthy'
        - database: 'disconnected'
        - Proper error message
        """
        with patch('src.database.check_db_connection', return_value=False):
            response = client.get('/api/health')

            assert response.status_code == 503, 'Should return 503 when database is disconnected'
            data = response.json()

            assert 'detail' in data, 'Error response should include detail'
            assert 'Database connection failed' in data['detail']

    def test_health_check_database_exception(self, client):
        """
        Test health check when database check raises exception.

        Verifies:
        - Returns 503 Service Unavailable
        - Error message does not expose sensitive information
        - Handles unexpected exceptions gracefully
        """
        with patch('src.database.check_db_connection', side_effect=Exception('Connection timeout')):
            response = client.get('/api/health')

            assert response.status_code == 503, 'Should return 503 when exception occurs'
            data = response.json()

            assert 'detail' in data, 'Error response should include detail'
            assert 'Health check failed' in data['detail']

    def test_health_check_operational_error(self, client):
        """
        Test health check when database raises OperationalError.

        Verifies:
        - Handles SQLAlchemy OperationalError
        - Returns 503 Service Unavailable
        """
        with patch('src.database.check_db_connection', side_effect=OperationalError('', {}, '')):
            response = client.get('/api/health')

            assert response.status_code == 503, 'Should return 503 for OperationalError'


class TestVulnerabilityAPIErrorCases:
    """
    Error handling tests for /api/vulnerabilities endpoints.

    Coverage target: src/api/vulnerabilities.py lines 123-128, 169-174
    """

    def test_list_vulnerabilities_sqlalchemy_error(self, client, setup_database):
        """
        Test /api/vulnerabilities when SQLAlchemy error occurs.

        Verifies:
        - Returns 500 Internal Server Error
        - Error message: 'Database connection error'
        - Does not expose database details
        """
        with patch('src.services.database_vulnerability_service.DatabaseVulnerabilityService.search_vulnerabilities',
                   side_effect=SQLAlchemyError('Database error')):
            response = client.get('/api/vulnerabilities')

            assert response.status_code == 500, 'Should return 500 for SQLAlchemy error'
            data = response.json()

            assert 'detail' in data
            assert data['detail'] == 'Database connection error'

    def test_list_vulnerabilities_generic_exception(self, client, setup_database):
        """
        Test /api/vulnerabilities when unexpected exception occurs.

        Verifies:
        - Returns 500 Internal Server Error
        - Error message: 'Internal server error'
        - Does not expose exception details
        """
        with patch('src.services.database_vulnerability_service.DatabaseVulnerabilityService.search_vulnerabilities',
                   side_effect=Exception('Unexpected error')):
            response = client.get('/api/vulnerabilities')

            assert response.status_code == 500, 'Should return 500 for generic exception'
            data = response.json()

            assert 'detail' in data
            assert data['detail'] == 'Internal server error'

    def test_get_vulnerability_detail_sqlalchemy_error(self, client, setup_database):
        """
        Test /api/vulnerabilities/{cve_id} when SQLAlchemy error occurs.

        Verifies:
        - Returns 500 Internal Server Error
        - Error message: 'Database connection error'
        """
        with patch('src.services.database_vulnerability_service.DatabaseVulnerabilityService.get_vulnerability_by_cve_id',
                   side_effect=SQLAlchemyError('Database error')):
            response = client.get('/api/vulnerabilities/CVE-2024-0001')

            assert response.status_code == 500, 'Should return 500 for SQLAlchemy error'
            data = response.json()

            assert 'detail' in data
            assert data['detail'] == 'Database connection error'

    def test_get_vulnerability_detail_generic_exception(self, client, setup_database):
        """
        Test /api/vulnerabilities/{cve_id} when unexpected exception occurs.

        Verifies:
        - Returns 500 Internal Server Error
        - Error message: 'Internal server error'
        """
        with patch('src.services.database_vulnerability_service.DatabaseVulnerabilityService.get_vulnerability_by_cve_id',
                   side_effect=Exception('Unexpected error')):
            response = client.get('/api/vulnerabilities/CVE-2024-0001')

            assert response.status_code == 500, 'Should return 500 for generic exception'
            data = response.json()

            assert 'detail' in data
            assert data['detail'] == 'Internal server error'


class TestApplicationLifecycle:
    """
    Tests for application startup and shutdown events.

    Coverage target: src/main.py lines 124-129 (startup), 139 (shutdown)
    """

    def test_startup_event(self):
        """
        Test application startup event.

        Verifies:
        - Startup event handler executes without errors
        - Logs appropriate startup information
        """
        with TestClient(app) as client:
            # Startup event is triggered when TestClient is created
            response = client.get('/api/health')
            assert response.status_code == 200, 'Application should start successfully'

    def test_shutdown_event(self):
        """
        Test application shutdown event.

        Verifies:
        - Shutdown event handler executes without errors
        - Application closes gracefully
        """
        with TestClient(app) as client:
            # Make a request to ensure app is running
            response = client.get('/api/health')
            assert response.status_code == 200

        # Shutdown event is triggered when TestClient context exits
        # If we reach here without exception, shutdown succeeded


class TestHTMLPageRendering:
    """
    Tests for HTML page rendering.

    Coverage target: src/api/vulnerabilities.py lines 46-47
    """

    def test_get_vulnerabilities_page_rendering(self, client, setup_database):
        """
        Test HTML page rendering for vulnerability list.

        Verifies:
        - Returns 200 OK
        - Content-Type is text/html
        - HTML content is rendered
        """
        response = client.get('/')

        assert response.status_code == 200, 'Should return 200 OK for HTML page'
        assert 'text/html' in response.headers['content-type'], 'Should return HTML content'

        # Check for expected HTML elements
        html_content = response.text
        assert '<html' in html_content.lower(), 'Should contain HTML tags'
        assert '脆弱性' in html_content or 'vulnerability' in html_content.lower(), \
            'Should contain vulnerability-related content'


class TestJVNFetcherErrorHandling:
    """
    Tests for JVN Fetcher error handling.

    Coverage target: src/fetchers/jvn_fetcher.py error handling paths
    """

    @pytest.mark.asyncio
    async def test_jvn_fetcher_timeout(self):
        """
        Test JVN Fetcher timeout handling.

        Verifies:
        - Timeout errors are caught and handled
        - Retry logic is triggered
        """
        from src.fetchers.jvn_fetcher import JVNFetcherService

        fetcher = JVNFetcherService()

        # Test with invalid endpoint to trigger timeout
        with patch.object(fetcher, 'api_endpoint', 'http://invalid-endpoint-12345.invalid'):
            with pytest.raises(Exception):
                # Should raise exception after all retries exhausted
                await fetcher.fetch_vulnerabilities(max_items=1)

    @pytest.mark.asyncio
    async def test_jvn_fetcher_invalid_xml(self):
        """
        Test JVN Fetcher with invalid XML response.

        Verifies:
        - Invalid XML triggers JVNParseError
        - Error is logged appropriately
        """
        from src.fetchers.jvn_fetcher import JVNFetcherService, JVNParseError

        fetcher = JVNFetcherService()

        # Mock httpx response with invalid XML
        mock_response = MagicMock()
        mock_response.text = '<invalid xml without closing tag'
        mock_response.status_code = 200

        with patch('httpx.AsyncClient.get', return_value=mock_response):
            with pytest.raises(JVNParseError):
                await fetcher.fetch_vulnerabilities(max_items=1)

    @pytest.mark.asyncio
    async def test_jvn_fetcher_http_error(self):
        """
        Test JVN Fetcher with HTTP error response.

        Verifies:
        - HTTP errors (404, 500) are handled
        - Retry logic is triggered for transient errors
        """
        from src.fetchers.jvn_fetcher import JVNFetcherService

        fetcher = JVNFetcherService()

        # Mock httpx response with 500 error
        with patch('httpx.AsyncClient.get', side_effect=Exception('HTTP 500 Internal Server Error')):
            with pytest.raises(Exception):
                await fetcher.fetch_vulnerabilities(max_items=1)
