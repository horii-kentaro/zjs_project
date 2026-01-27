"""
End-to-End tests for Phase 2 Web UI (Assets & Matching).

These tests verify the complete user workflow for:
1. Asset management page (P-002)
2. Matching results page (P-003)

Note: These are lightweight E2E tests using FastAPI TestClient + BeautifulSoup
for FastAPI + Jinja2 application (not a complex SPA).
"""

import pytest
from fastapi.testclient import TestClient
from bs4 import BeautifulSoup

from src.main import app
from src.database import engine


@pytest.fixture(scope='module')
def setup_database():
    """Setup database tables before running tests."""
    from src.models.asset import Base as AssetBase
    from src.models.vulnerability import Base as VulnBase

    AssetBase.metadata.create_all(bind=engine)
    VulnBase.metadata.create_all(bind=engine)
    yield


@pytest.fixture(scope='function')
def client():
    """Provide FastAPI TestClient."""
    return TestClient(app)


class TestAssetManagementPage:
    """
    E2E tests for Asset Management Page (P-002).

    Test Coverage:
    - HTML rendering
    - Page structure (title, table, buttons)
    - JavaScript loading
    - CSS styling
    """

    def test_page_loads_successfully(self, client, setup_database):
        """
        Test E2E-P2-001: Asset management page loads successfully.

        Verifies:
        - Page returns 200 OK
        - HTML structure is correct
        - Required elements are present
        """
        response = client.get('/assets')

        assert response.status_code == 200, 'Page should load successfully'
        assert 'text/html' in response.headers['content-type'], 'Should return HTML'

        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')

        # Check page title
        title = soup.find('title')
        assert title is not None, 'Page should have a title'
        assert '資産' in title.text or 'Asset' in title.text, \
            'Title should contain asset keyword'

        # Check main container
        assert soup.find('body') is not None, 'Page should have body'
        container = soup.find(class_='container')
        assert container is not None, 'Page should have container'

        print('\n✅ E2E-P2-001: Asset management page loads successfully')

    def test_page_has_asset_table(self, client, setup_database):
        """
        Test E2E-P2-002: Asset table structure is correct.

        Verifies:
        - Table element exists
        - Table headers are correct (資産名、ベンダー、製品名、バージョン、CPEコード等)
        """
        response = client.get('/assets')
        soup = BeautifulSoup(response.text, 'html.parser')

        # Check for table
        table = soup.find('table')
        assert table is not None, 'Page should have asset table'

        # Check for table headers
        headers = table.find_all('th')
        assert len(headers) > 0, 'Table should have headers'

        header_texts = [h.text.strip() for h in headers]

        # Check for expected headers
        expected_headers = ['資産名', 'ベンダー', '製品名', 'バージョン', 'CPEコード']
        for expected_header in expected_headers:
            assert any(expected_header in h for h in header_texts), \
                f'Table should have {expected_header} column'

        print(f'\n✅ E2E-P2-002: Asset table present ({len(headers)} columns)')

    def test_page_has_new_asset_button(self, client, setup_database):
        """
        Test E2E-P2-003: New asset button is present.

        Verifies:
        - "新規登録" button exists
        - Button has correct onclick handler
        """
        response = client.get('/assets')
        soup = BeautifulSoup(response.text, 'html.parser')

        # Check for "新規登録" button
        buttons = soup.find_all('button')
        new_button = None
        for btn in buttons:
            if '新規登録' in btn.text or 'New' in btn.text:
                new_button = btn
                break

        assert new_button is not None, 'Page should have new asset button'

        # Check onclick handler
        onclick = new_button.get('onclick', '')
        assert 'openCreateModal' in onclick, 'Button should call openCreateModal()'

        print('\n✅ E2E-P2-003: New asset button present')

    def test_page_has_file_upload_buttons(self, client, setup_database):
        """
        Test E2E-P2-004: File upload buttons are present.

        Verifies:
        - Composer upload button exists
        - NPM upload button exists
        - Docker upload button exists
        """
        response = client.get('/assets')
        soup = BeautifulSoup(response.text, 'html.parser')

        # Check for upload buttons
        buttons = soup.find_all('button')
        button_texts = [btn.text.strip() for btn in buttons]

        # Check for specific upload buttons
        assert any('Composer' in text and 'アップロード' in text for text in button_texts), \
            'Page should have Composer upload button'
        assert any('NPM' in text and 'アップロード' in text for text in button_texts), \
            'Page should have NPM upload button'
        assert any('Docker' in text and 'アップロード' in text for text in button_texts), \
            'Page should have Docker upload button'

        print('\n✅ E2E-P2-004: File upload buttons present')

    def test_page_has_asset_modal(self, client, setup_database):
        """
        Test E2E-P2-005: Asset modal structure is correct.

        Verifies:
        - Modal element exists
        - Form inputs are present (asset_name, vendor, product, version)
        """
        response = client.get('/assets')
        soup = BeautifulSoup(response.text, 'html.parser')

        # Check for modal
        modal = soup.find('div', class_='modal', id='assetModal')
        assert modal is not None, 'Page should have asset modal'

        # Check for form inputs
        form = modal.find('form', id='assetForm')
        assert form is not None, 'Modal should have form'

        # Check required inputs
        input_ids = ['assetName', 'vendor', 'product', 'version']
        for input_id in input_ids:
            input_field = form.find('input', id=input_id)
            assert input_field is not None, f'Form should have {input_id} input'

        print('\n✅ E2E-P2-005: Asset modal structure correct')

    def test_page_has_upload_modal(self, client, setup_database):
        """
        Test E2E-P2-006: Upload modal structure is correct.

        Verifies:
        - Upload modal element exists
        - File input exists
        - Drop zone exists
        """
        response = client.get('/assets')
        soup = BeautifulSoup(response.text, 'html.parser')

        # Check for upload modal
        modal = soup.find('div', class_='modal', id='uploadModal')
        assert modal is not None, 'Page should have upload modal'

        # Check for file input
        file_input = modal.find('input', {'type': 'file', 'id': 'fileInput'})
        assert file_input is not None, 'Upload modal should have file input'

        # Check for drop zone
        drop_zone = modal.find('div', id='dropZone')
        assert drop_zone is not None, 'Upload modal should have drop zone'

        print('\n✅ E2E-P2-006: Upload modal structure correct')

    def test_page_has_source_filter(self, client, setup_database):
        """
        Test E2E-P2-007: Source filter is present.

        Verifies:
        - Source filter select exists
        - Options include manual, composer, npm, docker
        """
        response = client.get('/assets')
        soup = BeautifulSoup(response.text, 'html.parser')

        # Check for source filter
        source_filter = soup.find('select', id='sourceFilter')
        assert source_filter is not None, 'Page should have source filter'

        # Check filter options
        options = source_filter.find_all('option')
        option_values = [opt.get('value', '') for opt in options]

        expected_values = ['', 'manual', 'composer', 'npm', 'docker']
        for expected_value in expected_values:
            assert expected_value in option_values, \
                f'Source filter should have {expected_value} option'

        print(f'\n✅ E2E-P2-007: Source filter present ({len(options)} options)')

    def test_javascript_loaded(self, client, setup_database):
        """
        Test E2E-P2-008: JavaScript file is loaded.

        Verifies:
        - assets.js script tag exists
        """
        response = client.get('/assets')
        soup = BeautifulSoup(response.text, 'html.parser')

        # Check for assets.js script tag
        scripts = soup.find_all('script', src=True)
        has_assets_js = any('assets.js' in script['src'] for script in scripts)

        assert has_assets_js, 'Page should load assets.js'

        print('\n✅ E2E-P2-008: JavaScript loaded (assets.js)')

    def test_css_loaded(self, client, setup_database):
        """
        Test E2E-P2-009: CSS file is loaded.

        Verifies:
        - style.css link tag exists
        """
        response = client.get('/assets')
        soup = BeautifulSoup(response.text, 'html.parser')

        # Check for style.css link tag
        links = soup.find_all('link', rel='stylesheet')
        has_style_css = any('style.css' in link.get('href', '') for link in links)

        assert has_style_css, 'Page should load style.css'

        print('\n✅ E2E-P2-009: CSS loaded (style.css)')


class TestMatchingResultsPage:
    """
    E2E tests for Matching Results Page (P-003).

    Test Coverage:
    - HTML rendering
    - Dashboard structure
    - Table structure
    - Filters and buttons
    - JavaScript loading
    - CSS styling
    """

    def test_page_loads_successfully(self, client, setup_database):
        """
        Test E2E-P2-010: Matching results page loads successfully.

        Verifies:
        - Page returns 200 OK
        - HTML structure is correct
        - Required elements are present
        """
        response = client.get('/matching')

        assert response.status_code == 200, 'Page should load successfully'
        assert 'text/html' in response.headers['content-type'], 'Should return HTML'

        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')

        # Check page title
        title = soup.find('title')
        assert title is not None, 'Page should have a title'
        assert 'マッチング' in title.text or 'Matching' in title.text, \
            'Title should contain matching keyword'

        # Check main container
        assert soup.find('body') is not None, 'Page should have body'
        container = soup.find(class_='container')
        assert container is not None, 'Page should have container'

        print('\n✅ E2E-P2-010: Matching results page loads successfully')

    def test_page_has_dashboard(self, client, setup_database):
        """
        Test E2E-P2-011: Dashboard structure is correct.

        Verifies:
        - Dashboard element exists
        - Statistics cards are present (affected_assets, critical, high, medium, low, total)
        """
        response = client.get('/matching')
        soup = BeautifulSoup(response.text, 'html.parser')

        # Check for dashboard
        dashboard = soup.find(class_='dashboard')
        assert dashboard is not None, 'Page should have dashboard'

        # Check for stats grid
        stats_grid = dashboard.find(class_='stats-grid')
        assert stats_grid is not None, 'Dashboard should have stats grid'

        # Check for stat cards
        stat_cards = stats_grid.find_all(class_='stat-card')
        assert len(stat_cards) >= 6, 'Dashboard should have at least 6 stat cards'

        # Check for specific stat elements by ID
        stat_ids = [
            'affectedAssetsCount',
            'criticalCount',
            'highCount',
            'mediumCount',
            'lowCount',
            'totalMatches'
        ]

        for stat_id in stat_ids:
            stat_element = soup.find(id=stat_id)
            assert stat_element is not None, f'Dashboard should have {stat_id} element'

        print(f'\n✅ E2E-P2-011: Dashboard present ({len(stat_cards)} stat cards)')

    def test_page_has_matching_results_table(self, client, setup_database):
        """
        Test E2E-P2-012: Matching results table structure is correct.

        Verifies:
        - Table element exists
        - Table headers are correct (資産名、CVE ID、タイトル、重要度、CVSS等)
        """
        response = client.get('/matching')
        soup = BeautifulSoup(response.text, 'html.parser')

        # Check for table
        table = soup.find('table')
        assert table is not None, 'Page should have matching results table'

        # Check for table headers
        headers = table.find_all('th')
        assert len(headers) > 0, 'Table should have headers'

        header_texts = [h.text.strip() for h in headers]

        # Check for expected headers
        expected_headers = ['資産名', 'CVE ID', 'タイトル', '重要度', 'CVSS']
        for expected_header in expected_headers:
            assert any(expected_header in h for h in header_texts), \
                f'Table should have {expected_header} column'

        print(f'\n✅ E2E-P2-012: Matching results table present ({len(headers)} columns)')

    def test_page_has_execute_matching_button(self, client, setup_database):
        """
        Test E2E-P2-013: Execute matching button is present.

        Verifies:
        - "マッチング実行" button exists
        - Button has correct onclick handler
        """
        response = client.get('/matching')
        soup = BeautifulSoup(response.text, 'html.parser')

        # Check for "マッチング実行" button
        execute_button = soup.find('button', id='executeBtn')
        assert execute_button is not None, 'Page should have execute matching button'

        button_text = execute_button.text.strip()
        assert 'マッチング実行' in button_text or 'Execute' in button_text, \
            'Button should have matching execution text'

        # Check onclick handler
        onclick = execute_button.get('onclick', '')
        assert 'executeMatching' in onclick, 'Button should call executeMatching()'

        print('\n✅ E2E-P2-013: Execute matching button present')

    def test_page_has_severity_filter(self, client, setup_database):
        """
        Test E2E-P2-014: Severity filter is present.

        Verifies:
        - Severity filter select exists
        - Options include Critical, High, Medium, Low
        """
        response = client.get('/matching')
        soup = BeautifulSoup(response.text, 'html.parser')

        # Check for severity filter
        severity_filter = soup.find('select', id='severityFilter')
        assert severity_filter is not None, 'Page should have severity filter'

        # Check filter options
        options = severity_filter.find_all('option')
        option_values = [opt.get('value', '') for opt in options]

        expected_values = ['', 'Critical', 'High', 'Medium', 'Low']
        for expected_value in expected_values:
            assert expected_value in option_values, \
                f'Severity filter should have {expected_value} option'

        print(f'\n✅ E2E-P2-014: Severity filter present ({len(options)} options)')

    def test_page_has_source_filter(self, client, setup_database):
        """
        Test E2E-P2-015: Source filter is present.

        Verifies:
        - Source filter select exists
        - Options include manual, composer, npm, docker
        """
        response = client.get('/matching')
        soup = BeautifulSoup(response.text, 'html.parser')

        # Check for source filter
        source_filter = soup.find('select', id='sourceFilter')
        assert source_filter is not None, 'Page should have source filter'

        # Check filter options
        options = source_filter.find_all('option')
        option_values = [opt.get('value', '') for opt in options]

        expected_values = ['', 'manual', 'composer', 'npm', 'docker']
        for expected_value in expected_values:
            assert expected_value in option_values, \
                f'Source filter should have {expected_value} option'

        print(f'\n✅ E2E-P2-015: Source filter present ({len(options)} options)')

    def test_page_has_last_matching_timestamp(self, client, setup_database):
        """
        Test E2E-P2-016: Last matching timestamp element is present.

        Verifies:
        - Last matching timestamp element exists
        """
        response = client.get('/matching')
        soup = BeautifulSoup(response.text, 'html.parser')

        # Check for last matching timestamp
        last_matching_element = soup.find(id='lastMatchingAt')
        assert last_matching_element is not None, \
            'Page should have last matching timestamp element'

        print('\n✅ E2E-P2-016: Last matching timestamp element present')

    def test_javascript_loaded(self, client, setup_database):
        """
        Test E2E-P2-017: JavaScript file is loaded.

        Verifies:
        - matching.js script tag exists
        """
        response = client.get('/matching')
        soup = BeautifulSoup(response.text, 'html.parser')

        # Check for matching.js script tag
        scripts = soup.find_all('script', src=True)
        has_matching_js = any('matching.js' in script['src'] for script in scripts)

        assert has_matching_js, 'Page should load matching.js'

        print('\n✅ E2E-P2-017: JavaScript loaded (matching.js)')

    def test_css_loaded(self, client, setup_database):
        """
        Test E2E-P2-018: CSS file is loaded.

        Verifies:
        - style.css link tag exists
        """
        response = client.get('/matching')
        soup = BeautifulSoup(response.text, 'html.parser')

        # Check for style.css link tag
        links = soup.find_all('link', rel='stylesheet')
        has_style_css = any('style.css' in link.get('href', '') for link in links)

        assert has_style_css, 'Page should load style.css'

        print('\n✅ E2E-P2-018: CSS loaded (style.css)')


class TestNavigation:
    """
    E2E tests for navigation between pages.

    Verifies that all Phase 2 pages have proper navigation.
    """

    def test_navigation_links_present_on_all_pages(self, client, setup_database):
        """
        Test E2E-P2-019: Navigation links are present on all Phase 2 pages.

        Verifies:
        - Navigation element or links exist
        - All pages have navigation
        """
        pages = ['/', '/assets', '/matching']

        for page in pages:
            response = client.get(page)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Check for nav element or navigation links
            nav = soup.find('nav')
            links = soup.find_all('a')

            assert nav is not None or len(links) > 0, \
                f'Page {page} should have navigation'

        print('\n✅ E2E-P2-019: Navigation links present on all pages')

    def test_navigation_includes_phase2_pages(self, client, setup_database):
        """
        Test E2E-P2-020: Navigation includes links to Phase 2 pages.

        Verifies:
        - Navigation includes link to /assets
        - Navigation includes link to /matching
        """
        response = client.get('/')
        soup = BeautifulSoup(response.text, 'html.parser')

        # Get all links
        links = soup.find_all('a')
        link_hrefs = [link.get('href', '') for link in links]

        # Check for Phase 2 page links
        assert any('/assets' in href for href in link_hrefs), \
            'Navigation should include link to assets page'
        assert any('/matching' in href for href in link_hrefs), \
            'Navigation should include link to matching page'

        print('\n✅ E2E-P2-020: Navigation includes Phase 2 pages')


class TestAPIIntegrationPhase2:
    """
    E2E tests for Phase 2 API integration.

    Verifies that the Web UI correctly integrates with Phase 2 backend APIs.
    """

    def test_api_assets_endpoint(self, client, setup_database):
        """
        Test E2E-P2-021: API /api/assets returns data.

        Verifies:
        - API endpoint is accessible
        - Returns JSON data
        - Data structure is correct
        """
        response = client.get('/api/assets')

        assert response.status_code == 200, 'API should return 200 OK'
        assert 'application/json' in response.headers['content-type'], \
            'API should return JSON'

        data = response.json()

        # Check response structure
        assert 'items' in data, 'Response should have items'
        assert 'total' in data, 'Response should have total'
        assert 'page' in data, 'Response should have page'
        assert 'limit' in data, 'Response should have limit'

        print(f'\n✅ E2E-P2-021: API returns {data["total"]} assets')

    def test_api_matching_dashboard_endpoint(self, client, setup_database):
        """
        Test E2E-P2-022: API /api/matching/dashboard returns data.

        Verifies:
        - API endpoint is accessible
        - Returns JSON data
        - Statistics structure is correct
        """
        response = client.get('/api/matching/dashboard')

        assert response.status_code == 200, 'API should return 200 OK'
        assert 'application/json' in response.headers['content-type'], \
            'API should return JSON'

        data = response.json()

        # Check response structure
        required_fields = [
            'affected_assets_count',
            'critical_vulnerabilities',
            'high_vulnerabilities',
            'medium_vulnerabilities',
            'low_vulnerabilities',
            'total_matches'
        ]

        for field in required_fields:
            assert field in data, f'Response should have {field}'

        print('\n✅ E2E-P2-022: Matching dashboard API returns statistics')

    def test_api_matching_results_endpoint(self, client, setup_database):
        """
        Test E2E-P2-023: API /api/matching/results returns data.

        Verifies:
        - API endpoint is accessible
        - Returns JSON data
        - Data structure is correct
        """
        response = client.get('/api/matching/results')

        assert response.status_code == 200, 'API should return 200 OK'
        assert 'application/json' in response.headers['content-type'], \
            'API should return JSON'

        data = response.json()

        # Check response structure
        assert 'items' in data, 'Response should have items'
        assert 'total' in data, 'Response should have total'
        assert 'page' in data, 'Response should have page'
        assert 'limit' in data, 'Response should have limit'

        print(f'\n✅ E2E-P2-023: API returns {data["total"]} matching results')

    def test_api_assets_filter_by_source(self, client, setup_database):
        """
        Test E2E-P2-024: API assets filtering by source works.

        Verifies:
        - Source filter parameter is processed
        - Results are filtered correctly
        """
        # Get all assets
        response_all = client.get('/api/assets')
        total_all = response_all.json()['total']

        # Filter by manual source
        response_filtered = client.get('/api/assets?source=manual')

        assert response_filtered.status_code == 200, 'Filter should return 200 OK'

        data_filtered = response_filtered.json()

        # Filtered results should be equal or less than total
        assert data_filtered['total'] <= total_all, \
            'Filtered results should be subset of all results'

        print(f'\n✅ E2E-P2-024: Assets source filter works '
              f'({data_filtered["total"]}/{total_all} results)')

    def test_api_matching_filter_by_severity(self, client, setup_database):
        """
        Test E2E-P2-025: API matching results filtering by severity works.

        Verifies:
        - Severity filter parameter is processed
        - Results are filtered correctly
        """
        # Get all matching results
        response_all = client.get('/api/matching/results')
        total_all = response_all.json()['total']

        # Filter by Critical severity
        response_filtered = client.get('/api/matching/results?severity=Critical')

        assert response_filtered.status_code == 200, 'Filter should return 200 OK'

        data_filtered = response_filtered.json()

        # Filtered results should be equal or less than total
        assert data_filtered['total'] <= total_all, \
            'Filtered results should be subset of all results'

        print(f'\n✅ E2E-P2-025: Matching severity filter works '
              f'({data_filtered["total"]}/{total_all} results)')

    def test_api_pagination_assets(self, client, setup_database):
        """
        Test E2E-P2-026: API assets pagination works.

        Verifies:
        - Page and limit parameters work
        - Pagination metadata is correct
        """
        # Request page 1 with small limit
        response = client.get('/api/assets?page=1&limit=10')

        assert response.status_code == 200, 'Pagination should return 200 OK'

        data = response.json()

        assert data['page'] == 1, 'Page should be 1'
        assert data['limit'] == 10, 'Limit should be 10'
        assert len(data['items']) <= 10, 'Items should not exceed limit'

        print(f'\n✅ E2E-P2-026: Assets pagination works '
              f'(page {data["page"]}, {len(data["items"])} items)')

    def test_api_pagination_matching_results(self, client, setup_database):
        """
        Test E2E-P2-027: API matching results pagination works.

        Verifies:
        - Page and limit parameters work
        - Pagination metadata is correct
        """
        # Request page 1 with small limit
        response = client.get('/api/matching/results?page=1&limit=10')

        assert response.status_code == 200, 'Pagination should return 200 OK'

        data = response.json()

        assert data['page'] == 1, 'Page should be 1'
        assert data['limit'] == 10, 'Limit should be 10'
        assert len(data['items']) <= 10, 'Items should not exceed limit'

        print(f'\n✅ E2E-P2-027: Matching results pagination works '
              f'(page {data["page"]}, {len(data["items"])} items)')
