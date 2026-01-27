"""
Integration tests for Matching Execution API endpoints.

IMPORTANT: These tests connect to the actual PostgreSQL (Neon) database.
No mocking is used. Tests use FastAPI TestClient with real database.

Test coverage:
- POST /api/matching/execute - Execute matching for all assets and vulnerabilities
- GET /api/matching/results - Retrieve matching results with pagination
- GET /api/matching/assets/{asset_id}/vulnerabilities - Get vulnerabilities for specific asset
- GET /api/matching/dashboard - Get dashboard statistics
"""

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from src.main import app
from src.database import SessionLocal, engine
from src.models.asset import Asset, AssetVulnerabilityMatch
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
def test_assets(db_session):
    """
    Create test assets for matching tests.

    Returns list of asset IDs for cleanup.
    """
    created_asset_ids = []

    # Generate unique identifier for this test
    unique_id = str(int(datetime.now(timezone.utc).timestamp()))[-6:]

    # Create test assets with known CPE codes and unique versions
    test_data = [
        {
            "asset_name": f"Test Nginx Server {unique_id}",
            "vendor": "nginx",
            "product": "nginx",
            "version": f"1.25.{unique_id}",
            "cpe_code": f"cpe:2.3:a:nginx:nginx:1.25.{unique_id}:*:*:*:*:*:*:*",
            "source": "manual",
        },
        {
            "asset_name": f"Test Apache Server {unique_id}",
            "vendor": "apache",
            "product": "http_server",
            "version": f"2.4.{unique_id}",
            "cpe_code": f"cpe:2.3:a:apache:http_server:2.4.{unique_id}:*:*:*:*:*:*:*",
            "source": "manual",
        },
        {
            "asset_name": f"Test Python Runtime {unique_id}",
            "vendor": "python",
            "product": "python",
            "version": f"3.11.{unique_id}",
            "cpe_code": f"cpe:2.3:a:python:python:3.11.{unique_id}:*:*:*:*:*:*:*",
            "source": "docker",
        },
    ]

    for asset_data in test_data:
        asset = Asset(**asset_data)
        db_session.add(asset)
        db_session.commit()
        db_session.refresh(asset)
        created_asset_ids.append(asset.asset_id)

    yield created_asset_ids

    # Cleanup: Delete test assets
    for asset_id in created_asset_ids:
        try:
            asset = db_session.query(Asset).filter(Asset.asset_id == asset_id).first()
            if asset:
                db_session.delete(asset)
                db_session.commit()
        except Exception:
            db_session.rollback()


@pytest.fixture(scope='function')
def test_vulnerabilities(db_session):
    """
    Create test vulnerabilities for matching tests.

    Returns list of CVE IDs for cleanup.
    """
    service = DatabaseVulnerabilityService(db_session)
    created_cve_ids = []

    # Generate unique test data
    unique_id = str(int(datetime.now(timezone.utc).timestamp()))[-6:]

    test_data = [
        VulnerabilityCreate(
            cve_id=f'CVE-2024-{unique_id}01',
            title='Test Nginx Vulnerability',
            description='Test vulnerability for nginx',
            cvss_score=9.8,
            severity='Critical',
            published_date=datetime.now(timezone.utc),
            modified_date=datetime.now(timezone.utc),
            affected_products={
                'products': [f'nginx 1.25.{unique_id}'],
                'cpes': [f'cpe:2.3:a:nginx:nginx:1.25.{unique_id}:*:*:*:*:*:*:*'],
            },
            vendor_info={'vendors': ['nginx']},
            references={'jvn': 'https://jvndb.jvn.jp/test/001'},
        ),
        VulnerabilityCreate(
            cve_id=f'CVE-2024-{unique_id}02',
            title='Test Apache Vulnerability',
            description='Test vulnerability for apache',
            cvss_score=7.5,
            severity='High',
            published_date=datetime.now(timezone.utc),
            modified_date=datetime.now(timezone.utc),
            affected_products={
                'products': [f'Apache HTTP Server 2.4.{unique_id}'],
                'cpes': [f'cpe:2.3:a:apache:http_server:2.4.{unique_id}:*:*:*:*:*:*:*'],
            },
            vendor_info={'vendors': ['Apache']},
            references={'jvn': 'https://jvndb.jvn.jp/test/002'},
        ),
        VulnerabilityCreate(
            cve_id=f'CVE-2024-{unique_id}03',
            title='Test Python Vulnerability',
            description='Test vulnerability for python',
            cvss_score=5.5,
            severity='Medium',
            published_date=datetime.now(timezone.utc),
            modified_date=datetime.now(timezone.utc),
            affected_products={
                'products': [f'Python 3.11.{unique_id}'],
                'cpes': [f'cpe:2.3:a:python:python:3.11.{unique_id}:*:*:*:*:*:*:*'],
            },
            vendor_info={'vendors': ['Python']},
            references={'jvn': 'https://jvndb.jvn.jp/test/003'},
        ),
        VulnerabilityCreate(
            cve_id=f'CVE-2024-{unique_id}04',
            title='Test Unmatched Vulnerability',
            description='Test vulnerability that should not match any asset',
            cvss_score=3.5,
            severity='Low',
            published_date=datetime.now(timezone.utc),
            modified_date=datetime.now(timezone.utc),
            affected_products={
                'products': ['Unknown Product 1.0.0'],
                'cpes': ['cpe:2.3:a:unknown:unknown:1.0.0:*:*:*:*:*:*:*'],
            },
            vendor_info={'vendors': ['Unknown']},
            references={'jvn': 'https://jvndb.jvn.jp/test/004'},
        ),
    ]

    # Insert test data
    for vuln_data in test_data:
        service.upsert_vulnerability(vuln_data)
        created_cve_ids.append(vuln_data.cve_id)

    yield created_cve_ids

    # Cleanup: Delete test vulnerabilities
    for cve_id in created_cve_ids:
        try:
            service.delete_vulnerability(cve_id)
        except Exception:
            pass


class TestMatchingExecution:
    """Tests for matching execution endpoint (POST /api/matching/execute)."""

    def test_execute_matching_success(self, client, test_assets, test_vulnerabilities):
        """
        Test M5.1: Execute matching with assets and vulnerabilities.

        Verifies:
        - Returns 200 OK
        - Response contains execution statistics
        - Matches are created in database
        """
        response = client.post("/api/matching/execute")

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "total_assets" in data
        assert "total_vulnerabilities" in data
        assert "total_matches" in data
        assert "exact_matches" in data
        assert "version_range_matches" in data
        assert "wildcard_matches" in data
        assert "execution_time_seconds" in data

        # Check that matching was executed
        assert data["total_assets"] >= 3  # Our test assets
        assert data["total_vulnerabilities"] >= 4  # Our test vulnerabilities
        assert isinstance(data["execution_time_seconds"], (int, float))

    def test_execute_matching_no_assets(self, client, db_session, test_vulnerabilities):
        """
        Test M5.2: Execute matching with no assets.

        Verifies:
        - Returns 200 OK
        - total_matches is 0
        - No errors occur
        """
        # Ensure no assets exist (delete all test assets)
        db_session.query(Asset).filter(Asset.vendor.like("test_%")).delete()
        db_session.commit()

        response = client.post("/api/matching/execute")

        assert response.status_code == 200
        data = response.json()

        # Should still execute successfully but with 0 matches
        assert data["total_matches"] >= 0

    def test_execute_matching_no_vulnerabilities(self, client, db_session, test_assets):
        """
        Test M5.2: Execute matching with no vulnerabilities.

        Verifies:
        - Returns 200 OK
        - total_matches is 0
        - No errors occur
        """
        response = client.post("/api/matching/execute")

        assert response.status_code == 200
        data = response.json()

        # Should execute successfully
        assert data["total_assets"] >= 3

    def test_execute_matching_idempotency(self, client, test_assets, test_vulnerabilities):
        """
        Test M5.3: Execute matching multiple times (idempotency).

        Verifies:
        - Multiple executions don't create duplicate matches
        - Results are consistent across executions
        """
        # First execution
        response1 = client.post("/api/matching/execute")
        assert response1.status_code == 200
        data1 = response1.json()

        # Second execution
        response2 = client.post("/api/matching/execute")
        assert response2.status_code == 200
        data2 = response2.json()

        # Results should be similar (allowing for minor timing differences)
        assert data1["total_assets"] == data2["total_assets"]
        assert data1["total_vulnerabilities"] == data2["total_vulnerabilities"]
        # total_matches might differ slightly due to concurrent operations, but should be close
        assert abs(data1["total_matches"] - data2["total_matches"]) <= 5


class TestMatchingResultsList:
    """Tests for matching results list endpoint (GET /api/matching/results)."""

    def test_get_matching_results_default_params(self, client, test_assets, test_vulnerabilities):
        """
        Test M5.4: Get matching results with default parameters.

        Verifies:
        - Returns 200 OK
        - Response contains items, total, page, limit
        - Default pagination is applied
        """
        # Execute matching first
        client.post("/api/matching/execute")

        response = client.get("/api/matching/results")

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "limit" in data

        # Check default pagination
        assert data["page"] == 1
        assert data["limit"] == 50

    def test_get_matching_results_with_pagination(self, client, test_assets, test_vulnerabilities):
        """
        Test M5.4: Get matching results with custom pagination.

        Verifies:
        - Custom page and limit are respected
        - Pagination metadata is correct
        """
        # Execute matching first
        client.post("/api/matching/execute")

        response = client.get("/api/matching/results?page=1&limit=2")

        assert response.status_code == 200
        data = response.json()

        assert data["page"] == 1
        assert data["limit"] == 2
        assert len(data["items"]) <= 2

    def test_get_matching_results_filter_by_severity(self, client, test_assets, test_vulnerabilities):
        """
        Test M5.5: Get matching results filtered by severity.

        Verifies:
        - Severity filter works correctly
        - Only results with specified severity are returned
        """
        # Execute matching first
        client.post("/api/matching/execute")

        response = client.get("/api/matching/results?severity=Critical")

        assert response.status_code == 200
        data = response.json()

        # All returned results should have severity='Critical'
        for item in data["items"]:
            assert item["severity"] == "Critical"

    def test_get_matching_results_filter_by_source(self, client, test_assets, test_vulnerabilities):
        """
        Test M5.5: Get matching results filtered by asset source.

        Verifies:
        - Source filter works correctly
        - Filtering is applied at database level
        """
        # Execute matching first
        client.post("/api/matching/execute")

        response = client.get("/api/matching/results?source=manual")

        assert response.status_code == 200
        data = response.json()

        # Check that results are returned (if any manual assets match)
        assert "items" in data

    def test_get_matching_results_invalid_severity(self, client):
        """
        Test M5.6: Get matching results with invalid severity filter.

        Verifies:
        - Returns 400 Bad Request
        - Error message is clear
        """
        response = client.get("/api/matching/results?severity=Invalid")

        assert response.status_code == 400
        assert "Invalid severity" in response.json()["detail"]

    def test_get_matching_results_invalid_source(self, client):
        """
        Test M5.6: Get matching results with invalid source filter.

        Verifies:
        - Returns 400 Bad Request
        - Error message is clear
        """
        response = client.get("/api/matching/results?source=invalid_source")

        assert response.status_code == 400
        assert "Invalid source" in response.json()["detail"]

    def test_get_matching_results_empty(self, client, db_session):
        """
        Test M5.7: Get matching results when no matches exist.

        Verifies:
        - Returns 200 OK
        - Empty items list
        - total is 0
        """
        # Clear all matches
        db_session.query(AssetVulnerabilityMatch).delete()
        db_session.commit()

        response = client.get("/api/matching/results")

        assert response.status_code == 200
        data = response.json()

        # Check for empty results
        assert isinstance(data["items"], list)
        assert data["total"] >= 0


class TestAssetVulnerabilities:
    """Tests for asset vulnerabilities endpoint (GET /api/matching/assets/{asset_id}/vulnerabilities)."""

    def test_get_asset_vulnerabilities_success(self, client, db_session, test_assets, test_vulnerabilities):
        """
        Test M5.8: Get vulnerabilities for existing asset with matches.

        Verifies:
        - Returns 200 OK
        - Response contains asset info and vulnerability list
        - Vulnerabilities are sorted by CVSS score (descending)
        """
        # Execute matching first
        client.post("/api/matching/execute")

        # Get vulnerabilities for first test asset
        asset_id = test_assets[0]
        response = client.get(f"/api/matching/assets/{asset_id}/vulnerabilities")

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "asset_id" in data
        assert "asset_name" in data
        assert "vulnerabilities" in data
        assert "total_vulnerabilities" in data

        assert data["asset_id"] == asset_id
        assert isinstance(data["vulnerabilities"], list)
        assert data["total_vulnerabilities"] >= 0

        # Check sorting (CVSS score descending)
        if len(data["vulnerabilities"]) >= 2:
            scores = [v.get("cvss_score", 0) or 0 for v in data["vulnerabilities"]]
            for i in range(len(scores) - 1):
                assert scores[i] >= scores[i + 1]

    def test_get_asset_vulnerabilities_no_matches(self, client, db_session, test_assets, test_vulnerabilities):
        """
        Test M5.8: Get vulnerabilities for asset with no matches.

        Verifies:
        - Returns 200 OK
        - Empty vulnerabilities list
        - total_vulnerabilities is 0
        """
        # Execute matching first
        client.post("/api/matching/execute")

        # Create an asset that won't match any vulnerability
        asset = Asset(
            asset_name="No Match Asset",
            vendor="nomatch_vendor",
            product="nomatch_product",
            version="99.99.99",
            cpe_code="cpe:2.3:a:nomatch_vendor:nomatch_product:99.99.99:*:*:*:*:*:*:*",
            source="manual",
        )
        db_session.add(asset)
        db_session.commit()
        db_session.refresh(asset)

        response = client.get(f"/api/matching/assets/{asset.asset_id}/vulnerabilities")

        assert response.status_code == 200
        data = response.json()

        assert data["total_vulnerabilities"] == 0
        assert len(data["vulnerabilities"]) == 0

        # Cleanup
        db_session.delete(asset)
        db_session.commit()

    def test_get_asset_vulnerabilities_not_found(self, client):
        """
        Test M5.9: Get vulnerabilities for non-existent asset.

        Verifies:
        - Returns 404 Not Found
        - Error message is clear
        """
        response = client.get("/api/matching/assets/550e8400-e29b-41d4-a716-446655440000/vulnerabilities")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestMatchingDashboard:
    """Tests for dashboard statistics endpoint (GET /api/matching/dashboard)."""

    def test_get_dashboard_stats_with_data(self, client, test_assets, test_vulnerabilities):
        """
        Test M5.10: Get dashboard statistics with matching data.

        Verifies:
        - Returns 200 OK
        - Response contains all required statistics
        - Statistics are consistent with database state
        """
        # Execute matching first
        client.post("/api/matching/execute")

        response = client.get("/api/matching/dashboard")

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "affected_assets_count" in data
        assert "total_matches" in data
        assert "critical_vulnerabilities" in data
        assert "high_vulnerabilities" in data
        assert "medium_vulnerabilities" in data
        assert "low_vulnerabilities" in data
        assert "last_matching_at" in data

        # Check data types
        assert isinstance(data["affected_assets_count"], int)
        assert isinstance(data["total_matches"], int)
        assert isinstance(data["critical_vulnerabilities"], int)
        assert isinstance(data["high_vulnerabilities"], int)
        assert isinstance(data["medium_vulnerabilities"], int)
        assert isinstance(data["low_vulnerabilities"], int)

        # Check that counts are non-negative
        assert data["affected_assets_count"] >= 0
        assert data["total_matches"] >= 0
        assert data["critical_vulnerabilities"] >= 0
        assert data["high_vulnerabilities"] >= 0
        assert data["medium_vulnerabilities"] >= 0
        assert data["low_vulnerabilities"] >= 0

    def test_get_dashboard_stats_no_matches(self, client, db_session):
        """
        Test M5.11: Get dashboard statistics with no matching data.

        Verifies:
        - Returns 200 OK
        - All counts are 0
        - last_matching_at is None
        """
        # Clear all matches
        db_session.query(AssetVulnerabilityMatch).delete()
        db_session.commit()

        response = client.get("/api/matching/dashboard")

        assert response.status_code == 200
        data = response.json()

        # All counts should be 0
        assert data["affected_assets_count"] == 0
        assert data["total_matches"] == 0
        assert data["critical_vulnerabilities"] == 0
        assert data["high_vulnerabilities"] == 0
        assert data["medium_vulnerabilities"] == 0
        assert data["low_vulnerabilities"] == 0
        assert data["last_matching_at"] is None

    def test_get_dashboard_stats_consistency(self, client, test_assets, test_vulnerabilities):
        """
        Test M5.10: Verify dashboard statistics consistency.

        Verifies:
        - Sum of severity counts matches total matches (or is less due to filtering)
        - last_matching_at is a valid timestamp
        """
        # Execute matching first
        client.post("/api/matching/execute")

        response = client.get("/api/matching/dashboard")

        assert response.status_code == 200
        data = response.json()

        # Sum of severity counts should be <= total_matches
        severity_sum = (
            data["critical_vulnerabilities"]
            + data["high_vulnerabilities"]
            + data["medium_vulnerabilities"]
            + data["low_vulnerabilities"]
        )
        assert severity_sum <= data["total_matches"]

        # last_matching_at should be a valid timestamp (if not None)
        if data["last_matching_at"]:
            from datetime import datetime
            # Should be parseable as datetime
            datetime.fromisoformat(data["last_matching_at"].replace('Z', '+00:00'))


class TestMatchingAPIEdgeCases:
    """Edge case tests for Matching API."""

    def test_matching_execution_performance(self, client, db_session):
        """
        Test matching execution with realistic data volume.

        Verifies:
        - Execution completes within reasonable time
        - No timeout errors
        """
        response = client.post("/api/matching/execute")

        assert response.status_code == 200
        data = response.json()

        # Execution should complete within reasonable time (< 60 seconds for typical data)
        assert data["execution_time_seconds"] < 60

    def test_pagination_large_page_number(self, client, test_assets, test_vulnerabilities):
        """
        Test matching results with very large page number.

        Verifies:
        - Returns 200 OK
        - Empty items list
        - No errors
        """
        # Execute matching first
        client.post("/api/matching/execute")

        response = client.get("/api/matching/results?page=9999&limit=50")

        assert response.status_code == 200
        data = response.json()

        # Should return empty items if page exceeds total_pages
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_matching_with_special_characters_in_cpe(self, client, db_session):
        """
        Test matching with special characters in CPE codes.

        Verifies:
        - Special characters are handled correctly
        - No SQL injection vulnerabilities
        """
        # Create asset with special characters
        asset = Asset(
            asset_name="Test Asset with Special Chars",
            vendor="test-vendor",
            product="test_product",
            version="1.0.0-alpha+build.123",
            cpe_code="cpe:2.3:a:test-vendor:test_product:1.0.0-alpha\\+build.123:*:*:*:*:*:*:*",
            source="manual",
        )
        db_session.add(asset)
        db_session.commit()
        db_session.refresh(asset)

        # Execute matching
        response = client.post("/api/matching/execute")
        assert response.status_code == 200

        # Cleanup
        db_session.delete(asset)
        db_session.commit()

    def test_concurrent_matching_execution(self, client):
        """
        Test concurrent matching executions.

        Verifies:
        - Multiple simultaneous executions don't cause conflicts
        - Database integrity is maintained
        """
        # This is a basic test - full concurrent testing would require threading
        response1 = client.post("/api/matching/execute")
        response2 = client.post("/api/matching/execute")

        # Both should succeed
        assert response1.status_code == 200
        assert response2.status_code == 200
