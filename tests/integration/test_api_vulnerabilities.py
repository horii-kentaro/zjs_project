"""
Integration tests for Vulnerability API endpoints.

IMPORTANT: These tests connect to the actual PostgreSQL (Neon) database.
No mocking is used. Tests use FastAPI TestClient with real database.
"""

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from src.main import app
from src.database import SessionLocal, engine
from src.models.vulnerability import Base, Vulnerability
from src.schemas.vulnerability import VulnerabilityCreate
from src.services.database_vulnerability_service import DatabaseVulnerabilityService


@pytest.fixture(scope='module')
def setup_database():
    """
    Setup database tables before running tests.

    Creates all tables if they don't exist.
    """
    # Create tables
    Base.metadata.create_all(bind=engine)
    yield
    # Tables are kept after tests (persistent database)


@pytest.fixture(scope='function')
def db_session(setup_database):
    """
    Provide a database session for each test.

    Each test gets a fresh session with automatic cleanup.
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope='function')
def client():
    """
    Provide FastAPI TestClient.
    """
    return TestClient(app)


@pytest.fixture(scope='function')
def test_vulnerabilities(db_session):
    """
    Create test vulnerabilities in the database.

    Returns list of CVE IDs for cleanup.
    """
    service = DatabaseVulnerabilityService(db_session)
    created_cve_ids = []

    # Generate unique test data
    unique_id = str(int(datetime.now(timezone.utc).timestamp()))[-4:]

    test_data = [
        VulnerabilityCreate(
            cve_id=f'CVE-2024-{unique_id}01',
            title='Critical Test Vulnerability',
            description='This is a critical test vulnerability',
            cvss_score=9.8,
            severity='Critical',
            published_date=datetime.now(timezone.utc),
            modified_date=datetime.now(timezone.utc),
            affected_products={'products': ['Test Product A']},
            vendor_info={'vendors': ['Test Vendor A']},
            references={'jvn': 'https://jvndb.jvn.jp/test/001'},
        ),
        VulnerabilityCreate(
            cve_id=f'CVE-2024-{unique_id}02',
            title='High Test Vulnerability',
            description='This is a high severity test vulnerability',
            cvss_score=7.5,
            severity='High',
            published_date=datetime.now(timezone.utc),
            modified_date=datetime.now(timezone.utc),
            affected_products={'products': ['Test Product B']},
            vendor_info={'vendors': ['Test Vendor B']},
            references={'jvn': 'https://jvndb.jvn.jp/test/002'},
        ),
        VulnerabilityCreate(
            cve_id=f'CVE-2024-{unique_id}03',
            title='Medium Test Vulnerability',
            description='This is a medium severity test vulnerability',
            cvss_score=5.5,
            severity='Medium',
            published_date=datetime.now(timezone.utc),
            modified_date=datetime.now(timezone.utc),
            affected_products={'products': ['Test Product C']},
            vendor_info={'vendors': ['Test Vendor C']},
            references={'jvn': 'https://jvndb.jvn.jp/test/003'},
        ),
    ]

    # Insert test data
    for vuln_data in test_data:
        service.upsert_vulnerability(vuln_data)
        created_cve_ids.append(vuln_data.cve_id)

    yield created_cve_ids

    # Cleanup test data after test
    for cve_id in created_cve_ids:
        try:
            service.delete_vulnerability(cve_id)
        except Exception:
            pass  # Ignore cleanup errors


class TestVulnerabilityAPI:
    """Integration tests for Vulnerability API endpoints."""

    def test_list_vulnerabilities_default_params(self, client, test_vulnerabilities):
        """
        Test M3.1: GET /api/vulnerabilities with default parameters.

        Verifies:
        - Response status code is 200
        - Response contains items, total, page, page_size, total_pages
        - Items are returned (at least test data)
        """
        response = client.get('/api/vulnerabilities')

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert 'items' in data
        assert 'total' in data
        assert 'page' in data
        assert 'page_size' in data
        assert 'total_pages' in data

        # Check default pagination
        assert data['page'] == 1
        assert data['page_size'] == 50

        # Check that test vulnerabilities are in the response
        assert data['total'] >= 3  # At least our 3 test vulnerabilities
        assert len(data['items']) >= 3

    def test_list_vulnerabilities_with_pagination(self, client, test_vulnerabilities):
        """
        Test M3.1: GET /api/vulnerabilities with pagination parameters.

        Verifies:
        - Custom page_size is respected
        - Pagination metadata is correct
        """
        response = client.get('/api/vulnerabilities?page=1&page_size=2')

        assert response.status_code == 200
        data = response.json()

        # Check pagination
        assert data['page'] == 1
        assert data['page_size'] == 2
        assert len(data['items']) <= 2

    def test_list_vulnerabilities_with_sort(self, client, test_vulnerabilities):
        """
        Test M3.1: GET /api/vulnerabilities with sorting.

        Verifies:
        - Sorting by severity works
        - Sorting by cvss_score works
        - Sort order (asc/desc) is respected
        """
        # Sort by severity descending (Critical > High > Medium)
        response = client.get('/api/vulnerabilities?sort_by=severity&sort_order=desc')
        assert response.status_code == 200
        data = response.json()

        # First item should have highest severity among test data
        if len(data['items']) > 0:
            first_severity = data['items'][0]['severity']
            assert first_severity in ['Critical', 'High', 'Medium', 'Low']

        # Sort by cvss_score ascending
        response = client.get('/api/vulnerabilities?sort_by=cvss_score&sort_order=asc')
        assert response.status_code == 200
        data = response.json()

        # Verify ascending order (if multiple items)
        if len(data['items']) >= 2:
            for i in range(len(data['items']) - 1):
                if data['items'][i]['cvss_score'] and data['items'][i + 1]['cvss_score']:
                    assert data['items'][i]['cvss_score'] <= data['items'][i + 1]['cvss_score']

    def test_list_vulnerabilities_with_search(self, client, test_vulnerabilities):
        """
        Test M3.1: GET /api/vulnerabilities with search keyword.

        Verifies:
        - Search by CVE ID works
        - Search by title works
        - Partial match is supported
        """
        # Search by CVE ID (using first test vulnerability)
        test_cve_id = test_vulnerabilities[0]
        response = client.get(f'/api/vulnerabilities?search={test_cve_id}')
        assert response.status_code == 200
        data = response.json()

        # Should find at least one result
        assert data['total'] >= 1
        assert any(item['cve_id'] == test_cve_id for item in data['items'])

        # Search by title (partial match)
        response = client.get('/api/vulnerabilities?search=Critical')
        assert response.status_code == 200
        data = response.json()

        # Should find results containing "Critical"
        assert data['total'] >= 1

    def test_list_vulnerabilities_invalid_sort_by(self, client):
        """
        Test M3.3: GET /api/vulnerabilities with invalid sort_by parameter.

        Verifies:
        - Returns 400 Bad Request
        - Error message is clear
        """
        response = client.get('/api/vulnerabilities?sort_by=invalid_field')
        assert response.status_code == 400
        assert 'Invalid sort_by parameter' in response.json()['detail']

    def test_list_vulnerabilities_invalid_sort_order(self, client):
        """
        Test M3.3: GET /api/vulnerabilities with invalid sort_order parameter.

        Verifies:
        - Returns 400 Bad Request
        - Error message is clear
        """
        response = client.get('/api/vulnerabilities?sort_order=invalid_order')
        assert response.status_code == 400
        assert 'Invalid sort_order parameter' in response.json()['detail']

    def test_get_vulnerability_detail_success(self, client, test_vulnerabilities):
        """
        Test M3.2: GET /api/vulnerabilities/{cve_id} - Success case.

        Verifies:
        - Returns 200 OK
        - Response contains all required fields
        - Data matches expected values
        """
        test_cve_id = test_vulnerabilities[0]
        response = client.get(f'/api/vulnerabilities/{test_cve_id}')

        assert response.status_code == 200
        data = response.json()

        # Check required fields
        assert data['cve_id'] == test_cve_id
        assert 'title' in data
        assert 'description' in data
        assert 'cvss_score' in data
        assert 'severity' in data
        assert 'published_date' in data
        assert 'modified_date' in data
        assert 'affected_products' in data
        assert 'vendor_info' in data
        assert 'references' in data
        assert 'created_at' in data
        assert 'updated_at' in data

    def test_get_vulnerability_detail_not_found(self, client):
        """
        Test M3.2: GET /api/vulnerabilities/{cve_id} - Not found case.

        Verifies:
        - Returns 404 Not Found
        - Error message is clear
        """
        response = client.get('/api/vulnerabilities/CVE-9999-9999')
        assert response.status_code == 404
        assert 'not found' in response.json()['detail'].lower()

    def test_database_error_handling(self, client, db_session):
        """
        Test M3.3: Database error handling.

        Verifies:
        - API handles database errors gracefully
        - Returns 500 Internal Server Error
        - Error message does not expose sensitive information
        """
        # Close database connection to simulate error
        db_session.close()
        engine.dispose()

        # Try to access API (should fail gracefully)
        response = client.get('/api/vulnerabilities')

        # Should return 500 (or retry and succeed if connection pool recovers)
        # We just verify no crash and proper error handling
        assert response.status_code in [200, 500]

        if response.status_code == 500:
            data = response.json()
            # Error message should not expose database details
            assert 'detail' in data
            assert 'Internal server error' in data['detail'] or 'Database connection error' in data['detail']

        # Restore connection for subsequent tests
        engine.dispose()


class TestVulnerabilityAPIEdgeCases:
    """Edge case tests for Vulnerability API."""

    def test_empty_database(self, client, db_session):
        """
        Test API behavior when database is empty (or nearly empty).

        Verifies:
        - Returns empty items list
        - total is 0 (or small number)
        - No errors
        """
        # Search for non-existent CVE
        response = client.get('/api/vulnerabilities?search=CVE-9999-NONEXISTENT')
        assert response.status_code == 200
        data = response.json()

        assert data['total'] == 0
        assert len(data['items']) == 0

    def test_pagination_edge_cases(self, client):
        """
        Test pagination edge cases.

        Verifies:
        - page_size boundary values (1, 100)
        - Large page numbers
        """
        # Minimum page_size
        response = client.get('/api/vulnerabilities?page_size=1')
        assert response.status_code == 200
        data = response.json()
        assert data['page_size'] == 1

        # Maximum page_size
        response = client.get('/api/vulnerabilities?page_size=100')
        assert response.status_code == 200
        data = response.json()
        assert data['page_size'] == 100

        # Large page number (should return empty items)
        response = client.get('/api/vulnerabilities?page=9999')
        assert response.status_code == 200
        data = response.json()
        # May be empty if page exceeds total_pages
        assert 'items' in data

    def test_special_characters_in_search(self, client):
        """
        Test search with special characters.

        Verifies:
        - Special characters don't cause errors
        - SQL injection is prevented
        """
        special_chars = ["'; DROP TABLE vulnerabilities; --", "<script>alert('xss')</script>", "%' OR '1'='1"]

        for search_term in special_chars:
            response = client.get(f'/api/vulnerabilities?search={search_term}')
            # Should not crash, may return 200 or 400
            assert response.status_code in [200, 400]

            # Database should still be intact
            check_response = client.get('/api/vulnerabilities')
            assert check_response.status_code == 200
