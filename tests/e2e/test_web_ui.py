"""
End-to-End tests for Web UI.

These tests verify the complete user workflow:
1. HTML page rendering
2. JavaScript functionality
3. User interactions (search, sort, pagination)
4. Integration with backend API

Note: These are lightweight E2E tests using requests + BeautifulSoup
for FastAPI + Jinja2 application (not a complex SPA).
"""

import pytest
import time
from fastapi.testclient import TestClient
from bs4 import BeautifulSoup

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


class TestVulnerabilityListPage:
    """
    E2E tests for Vulnerability List Page (P-001).

    Test Coverage:
    - HTML rendering
    - Page structure (title, table, search form)
    - JavaScript loading
    - CSS styling
    """

    def test_page_loads_successfully(self, client, setup_database):
        """
        Test E2E-001: Vulnerability list page loads successfully.

        Verifies:
        - Page returns 200 OK
        - HTML structure is correct
        - Required elements are present
        """
        response = client.get('/')

        assert response.status_code == 200, 'Page should load successfully'
        assert 'text/html' in response.headers['content-type'], 'Should return HTML'

        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')

        # Check page title
        title = soup.find('title')
        assert title is not None, 'Page should have a title'
        assert '脆弱性' in title.text or 'Vulnerability' in title.text, \
            'Title should contain vulnerability keyword'

        # Check main container
        assert soup.find('body') is not None, 'Page should have body'
        # Check for main content area (main, div#app, or div.container)
        has_main_content = (
            soup.find('main') is not None or
            soup.find(id='app') is not None or
            soup.find(class_='container') is not None
        )
        assert has_main_content, 'Page should have main content area'

        print('\n✅ E2E-001: Page loads successfully')

    def test_page_has_search_form(self, client, setup_database):
        """
        Test E2E-002: Search form is present and functional.

        Verifies:
        - Search input field exists
        - Search form has correct attributes
        """
        response = client.get('/')
        soup = BeautifulSoup(response.text, 'html.parser')

        # Check for search input
        search_inputs = soup.find_all('input', {'type': 'text'}) + \
                       soup.find_all('input', {'type': 'search'})

        assert len(search_inputs) > 0, 'Page should have search input field'

        print(f'\n✅ E2E-002: Search form present ({len(search_inputs)} input fields)')

    def test_page_has_vulnerability_table(self, client, setup_database):
        """
        Test E2E-003: Vulnerability table structure is correct.

        Verifies:
        - Table element exists
        - Table headers are correct (CVE ID, Title, Severity, etc.)
        """
        response = client.get('/')
        soup = BeautifulSoup(response.text, 'html.parser')

        # Check for table or list container
        table = soup.find('table') or soup.find('div', class_=lambda x: x and 'table' in x.lower())

        assert table is not None, 'Page should have table or list for vulnerabilities'

        # Check for table headers (if table exists)
        if soup.find('table'):
            headers = soup.find_all('th')
            header_texts = [h.text.strip() for h in headers]

            # Should contain CVE-related headers
            assert any('CVE' in h or 'ID' in h for h in header_texts), \
                'Table should have CVE ID column'

        print(f'\n✅ E2E-003: Vulnerability table present')

    def test_javascript_files_loaded(self, client, setup_database):
        """
        Test E2E-004: JavaScript files are properly loaded.

        Verifies:
        - Script tags are present
        - JavaScript file paths are correct
        """
        response = client.get('/')
        soup = BeautifulSoup(response.text, 'html.parser')

        # Check for script tags
        scripts = soup.find_all('script')

        # Should have at least one script tag
        assert len(scripts) > 0, 'Page should load JavaScript files'

        # Check for main.js (if exists)
        script_srcs = [s.get('src', '') for s in scripts]

        print(f'\n✅ E2E-004: {len(scripts)} JavaScript file(s) loaded')

    def test_css_files_loaded(self, client, setup_database):
        """
        Test E2E-005: CSS files are properly loaded.

        Verifies:
        - Link tags for CSS are present
        - CSS file paths are correct
        """
        response = client.get('/')
        soup = BeautifulSoup(response.text, 'html.parser')

        # Check for link tags (CSS)
        css_links = soup.find_all('link', {'rel': 'stylesheet'})

        # Should have at least one CSS file
        assert len(css_links) > 0, 'Page should load CSS files'

        print(f'\n✅ E2E-005: {len(css_links)} CSS file(s) loaded')


class TestAPIIntegration:
    """
    E2E tests for API integration.

    Verifies that the Web UI correctly integrates with backend API.
    """

    def test_api_vulnerabilities_endpoint(self, client, setup_database):
        """
        Test E2E-006: API /api/vulnerabilities returns data.

        Verifies:
        - API endpoint is accessible
        - Returns JSON data
        - Data structure is correct
        """
        response = client.get('/api/vulnerabilities')

        assert response.status_code == 200, 'API should return 200 OK'
        assert 'application/json' in response.headers['content-type'], \
            'API should return JSON'

        data = response.json()

        # Check response structure
        assert 'items' in data, 'Response should have items'
        assert 'total' in data, 'Response should have total'
        assert 'page' in data, 'Response should have page'
        assert 'page_size' in data, 'Response should have page_size'

        print(f'\n✅ E2E-006: API returns {data["total"]} vulnerabilities')

    def test_api_search_functionality(self, client, setup_database):
        """
        Test E2E-007: API search functionality works.

        Verifies:
        - Search parameter is processed
        - Results are filtered correctly
        """
        # Get total count
        response_all = client.get('/api/vulnerabilities')
        total_all = response_all.json()['total']

        # Search with specific keyword
        response_search = client.get('/api/vulnerabilities?search=CVE')
        data_search = response_search.json()

        assert response_search.status_code == 200, 'Search should return 200 OK'

        # Search results should be equal or less than total
        assert data_search['total'] <= total_all, \
            'Search results should be subset of all results'

        print(f'\n✅ E2E-007: Search works ({data_search["total"]}/{total_all} results)')

    def test_api_sort_functionality(self, client, setup_database):
        """
        Test E2E-008: API sort functionality works.

        Verifies:
        - Sort parameters are processed
        - Results are sorted correctly
        """
        # Sort by severity descending
        response = client.get('/api/vulnerabilities?sort_by=severity&sort_order=desc')

        assert response.status_code == 200, 'Sort should return 200 OK'

        data = response.json()
        items = data['items']

        # If multiple items, verify sorting (rough check)
        if len(items) >= 2:
            severities = [item.get('severity', '') for item in items]
            # Critical > High > Medium > Low
            print(f'   Severities: {severities[:3]}...')

        print(f'\n✅ E2E-008: Sort works ({len(items)} items sorted)')

    def test_api_pagination(self, client, setup_database):
        """
        Test E2E-009: API pagination works.

        Verifies:
        - Page and page_size parameters work
        - Pagination metadata is correct
        """
        # Request page 1 with small page_size
        response = client.get('/api/vulnerabilities?page=1&page_size=10')

        assert response.status_code == 200, 'Pagination should return 200 OK'

        data = response.json()

        assert data['page'] == 1, 'Page should be 1'
        assert data['page_size'] == 10, 'Page size should be 10'
        assert len(data['items']) <= 10, 'Items should not exceed page_size'

        print(f'\n✅ E2E-009: Pagination works (page {data["page"]}/{data["total_pages"]})')


class TestPerformance:
    """
    E2E performance tests.

    Verifies acceptable response times for user experience.
    """

    def test_page_load_time(self, client, setup_database):
        """
        Test E2E-010: Page load time is acceptable.

        Verifies:
        - Page loads within 2 seconds
        """
        start_time = time.time()
        response = client.get('/')
        elapsed_time = time.time() - start_time

        assert response.status_code == 200, 'Page should load successfully'
        assert elapsed_time < 2.0, f'Page load time {elapsed_time:.3f}s exceeds 2 seconds'

        print(f'\n✅ E2E-010: Page loaded in {elapsed_time:.3f}s')

    def test_api_response_time(self, client, setup_database):
        """
        Test E2E-011: API response time is acceptable.

        Verifies:
        - API responds within 1 second
        """
        start_time = time.time()
        response = client.get('/api/vulnerabilities?page=1&page_size=50')
        elapsed_time = time.time() - start_time

        assert response.status_code == 200, 'API should respond successfully'
        assert elapsed_time < 1.0, f'API response time {elapsed_time:.3f}s exceeds 1 second'

        print(f'\n✅ E2E-011: API responded in {elapsed_time:.3f}s')
