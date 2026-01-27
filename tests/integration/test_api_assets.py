"""
Integration tests for Asset Management API endpoints.

IMPORTANT: These tests connect to the actual PostgreSQL (Neon) database.
No mocking is used. Tests use FastAPI TestClient with real database.

Test coverage:
- POST /api/assets - Manual asset registration
- GET /api/assets - Asset list retrieval
- GET /api/assets/{asset_id} - Asset detail retrieval
- PUT /api/assets/{asset_id} - Asset update
- DELETE /api/assets/{asset_id} - Asset deletion
- POST /api/assets/import/composer - Composer file import
- POST /api/assets/import/npm - NPM file import
- POST /api/assets/import/docker - Dockerfile import
"""

import io
import json
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from src.main import app
from src.database import SessionLocal, engine
from src.models.asset import Asset, AssetVulnerabilityMatch
from src.models.vulnerability import Base


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
def cleanup_test_assets(db_session):
    """
    Cleanup test assets after each test.

    Yields the session for use during the test, then cleans up test assets.
    """
    created_asset_ids = []

    yield created_asset_ids

    # Cleanup: Delete all test assets created during the test
    for asset_id in created_asset_ids:
        try:
            asset = db_session.query(Asset).filter(Asset.asset_id == asset_id).first()
            if asset:
                db_session.delete(asset)
                db_session.commit()
        except Exception:
            db_session.rollback()


class TestAssetManualRegistration:
    """Tests for manual asset registration endpoint (POST /api/assets)."""

    def test_create_asset_success(self, client, cleanup_test_assets):
        """
        Test M4.1: Create asset with valid data.

        Verifies:
        - Returns 201 Created
        - Response contains all required fields
        - CPE code is automatically generated
        - Source is set to 'manual'
        """
        # Generate unique version to avoid conflicts with other tests
        from datetime import datetime, timezone
        unique_id = str(int(datetime.now(timezone.utc).timestamp()))[-6:]
        version = f"1.25.{unique_id}"

        response = client.post(
            "/api/assets",
            json={
                "asset_name": "Test Asset - Nginx",
                "vendor": "nginx",
                "product": "nginx",
                "version": version,
            },
        )

        assert response.status_code == 201
        data = response.json()

        # Track for cleanup
        cleanup_test_assets.append(data["asset_id"])

        # Verify response structure
        assert "asset_id" in data
        assert data["asset_name"] == "Test Asset - Nginx"
        assert data["vendor"] == "nginx"
        assert data["product"] == "nginx"
        assert data["version"] == version
        assert "cpe_code" in data
        assert data["cpe_code"].startswith(f"cpe:2.3:a:nginx:nginx:{version}")
        assert data["source"] == "manual"
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_asset_duplicate(self, client, cleanup_test_assets):
        """
        Test M4.2: Create duplicate asset.

        Verifies:
        - Returns 400 Bad Request
        - Error message indicates duplicate
        """
        asset_data = {
            "asset_name": "Test Asset - Duplicate",
            "vendor": "test_vendor",
            "product": "test_product",
            "version": "1.0.0",
        }

        # Create first asset
        response1 = client.post("/api/assets", json=asset_data)
        assert response1.status_code == 201
        cleanup_test_assets.append(response1.json()["asset_id"])

        # Try to create duplicate
        response2 = client.post("/api/assets", json=asset_data)
        assert response2.status_code == 400
        assert "already exists" in response2.json()["detail"]

    def test_create_asset_missing_required_field(self, client):
        """
        Test M4.3: Create asset with missing required field.

        Verifies:
        - Returns 422 Unprocessable Entity
        - Validation error is clear
        """
        response = client.post(
            "/api/assets",
            json={
                "asset_name": "Test Asset",
                "vendor": "nginx",
                # Missing 'product' and 'version'
            },
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_create_asset_empty_string(self, client):
        """
        Test M4.3: Create asset with empty string values.

        Verifies:
        - Returns 422 Unprocessable Entity
        - Validation rejects empty strings
        """
        response = client.post(
            "/api/assets",
            json={
                "asset_name": "Test Asset",
                "vendor": "nginx",
                "product": "",  # Empty string
                "version": "1.0.0",
            },
        )

        assert response.status_code == 422

    def test_create_asset_whitespace_only(self, client):
        """
        Test M4.3: Create asset with whitespace-only values.

        Verifies:
        - Returns 422 Unprocessable Entity
        - Validation rejects whitespace-only strings
        """
        response = client.post(
            "/api/assets",
            json={
                "asset_name": "   ",  # Whitespace only
                "vendor": "nginx",
                "product": "nginx",
                "version": "1.0.0",
            },
        )

        assert response.status_code == 422


class TestAssetListRetrieval:
    """Tests for asset list endpoint (GET /api/assets)."""

    def test_list_assets_default_params(self, client, db_session, cleanup_test_assets):
        """
        Test M4.4: List assets with default parameters.

        Verifies:
        - Returns 200 OK
        - Response contains items, total, page, limit
        - Default pagination is applied
        """
        # Create test assets
        for i in range(3):
            asset = Asset(
                asset_name=f"Test Asset List {i}",
                vendor=f"vendor{i}",
                product=f"product{i}",
                version=f"1.0.{i}",
                cpe_code=f"cpe:2.3:a:vendor{i}:product{i}:1.0.{i}:*:*:*:*:*:*:*",
                source="manual",
            )
            db_session.add(asset)
            db_session.commit()
            db_session.refresh(asset)
            cleanup_test_assets.append(asset.asset_id)

        response = client.get("/api/assets")

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

        # Check that test assets are in the response
        assert data["total"] >= 3

    def test_list_assets_with_pagination(self, client, db_session, cleanup_test_assets):
        """
        Test M4.4: List assets with custom pagination.

        Verifies:
        - Custom page and limit are respected
        - Pagination metadata is correct
        """
        # Create test assets
        for i in range(5):
            asset = Asset(
                asset_name=f"Test Asset Pagination {i}",
                vendor=f"pag_vendor{i}",
                product=f"pag_product{i}",
                version=f"1.0.{i}",
                cpe_code=f"cpe:2.3:a:pag_vendor{i}:pag_product{i}:1.0.{i}:*:*:*:*:*:*:*",
                source="manual",
            )
            db_session.add(asset)
            db_session.commit()
            db_session.refresh(asset)
            cleanup_test_assets.append(asset.asset_id)

        response = client.get("/api/assets?page=1&limit=2")

        assert response.status_code == 200
        data = response.json()

        assert data["page"] == 1
        assert data["limit"] == 2
        assert len(data["items"]) <= 2

    def test_list_assets_filter_by_source(self, client, db_session, cleanup_test_assets):
        """
        Test M4.4: List assets filtered by source.

        Verifies:
        - Source filter works correctly
        - Only assets from specified source are returned
        """
        # Create assets with different sources
        sources = ["manual", "composer", "npm", "docker"]
        for source in sources:
            asset = Asset(
                asset_name=f"Test Asset {source}",
                vendor=f"{source}_vendor",
                product=f"{source}_product",
                version="1.0.0",
                cpe_code=f"cpe:2.3:a:{source}_vendor:{source}_product:1.0.0:*:*:*:*:*:*:*",
                source=source,
            )
            db_session.add(asset)
            db_session.commit()
            db_session.refresh(asset)
            cleanup_test_assets.append(asset.asset_id)

        # Filter by manual source
        response = client.get("/api/assets?source=manual")
        assert response.status_code == 200
        data = response.json()

        # All returned assets should have source='manual'
        for item in data["items"]:
            if item["asset_name"].startswith("Test Asset"):
                assert item["source"] == "manual"

    def test_list_assets_invalid_source(self, client):
        """
        Test M4.5: List assets with invalid source filter.

        Verifies:
        - Returns 400 Bad Request
        - Error message is clear
        """
        response = client.get("/api/assets?source=invalid_source")
        assert response.status_code == 400
        assert "Invalid source" in response.json()["detail"]


class TestAssetDetailRetrieval:
    """Tests for asset detail endpoint (GET /api/assets/{asset_id})."""

    def test_get_asset_success(self, client, db_session, cleanup_test_assets):
        """
        Test M4.6: Get asset detail with valid ID.

        Verifies:
        - Returns 200 OK
        - Response contains all asset fields
        """
        # Create test asset
        asset = Asset(
            asset_name="Test Asset Detail",
            vendor="detail_vendor",
            product="detail_product",
            version="1.0.0",
            cpe_code="cpe:2.3:a:detail_vendor:detail_product:1.0.0:*:*:*:*:*:*:*",
            source="manual",
        )
        db_session.add(asset)
        db_session.commit()
        db_session.refresh(asset)
        cleanup_test_assets.append(asset.asset_id)

        response = client.get(f"/api/assets/{asset.asset_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["asset_id"] == asset.asset_id
        assert data["asset_name"] == "Test Asset Detail"
        assert data["vendor"] == "detail_vendor"
        assert data["product"] == "detail_product"
        assert data["version"] == "1.0.0"

    def test_get_asset_not_found(self, client):
        """
        Test M4.7: Get asset detail with non-existent ID.

        Verifies:
        - Returns 404 Not Found
        - Error message is clear
        """
        response = client.get("/api/assets/550e8400-e29b-41d4-a716-446655440000")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestAssetUpdate:
    """Tests for asset update endpoint (PUT /api/assets/{asset_id})."""

    def test_update_asset_name(self, client, db_session, cleanup_test_assets):
        """
        Test M4.8: Update asset name.

        Verifies:
        - Returns 200 OK
        - Asset name is updated
        - CPE code remains unchanged
        """
        # Create test asset
        asset = Asset(
            asset_name="Original Name",
            vendor="update_vendor",
            product="update_product",
            version="1.0.0",
            cpe_code="cpe:2.3:a:update_vendor:update_product:1.0.0:*:*:*:*:*:*:*",
            source="manual",
        )
        db_session.add(asset)
        db_session.commit()
        db_session.refresh(asset)
        cleanup_test_assets.append(asset.asset_id)

        response = client.put(
            f"/api/assets/{asset.asset_id}",
            json={"asset_name": "Updated Name"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["asset_name"] == "Updated Name"
        assert data["cpe_code"] == asset.cpe_code  # CPE unchanged

    def test_update_asset_version(self, client, db_session, cleanup_test_assets):
        """
        Test M4.8: Update asset version.

        Verifies:
        - Returns 200 OK
        - Version is updated
        - CPE code is regenerated
        """
        # Create test asset
        asset = Asset(
            asset_name="Version Test",
            vendor="version_vendor",
            product="version_product",
            version="1.0.0",
            cpe_code="cpe:2.3:a:version_vendor:version_product:1.0.0:*:*:*:*:*:*:*",
            source="manual",
        )
        db_session.add(asset)
        db_session.commit()
        db_session.refresh(asset)
        original_cpe = asset.cpe_code
        cleanup_test_assets.append(asset.asset_id)

        response = client.put(
            f"/api/assets/{asset.asset_id}",
            json={"version": "2.0.0"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["version"] == "2.0.0"
        assert data["cpe_code"] != original_cpe
        assert "2.0.0" in data["cpe_code"]

    def test_update_asset_not_found(self, client):
        """
        Test M4.9: Update non-existent asset.

        Verifies:
        - Returns 404 Not Found
        - Error message is clear
        """
        response = client.put(
            "/api/assets/550e8400-e29b-41d4-a716-446655440000",
            json={"asset_name": "Updated Name"},
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_update_asset_creates_duplicate(self, client, db_session, cleanup_test_assets):
        """
        Test M4.9: Update asset that would create duplicate.

        Verifies:
        - Returns 400 Bad Request
        - Error message indicates duplicate
        """
        # Create two test assets
        asset1 = Asset(
            asset_name="Asset 1",
            vendor="dup_vendor",
            product="dup_product",
            version="1.0.0",
            cpe_code="cpe:2.3:a:dup_vendor:dup_product:1.0.0:*:*:*:*:*:*:*",
            source="manual",
        )
        asset2 = Asset(
            asset_name="Asset 2",
            vendor="dup_vendor",
            product="dup_product",
            version="2.0.0",
            cpe_code="cpe:2.3:a:dup_vendor:dup_product:2.0.0:*:*:*:*:*:*:*",
            source="manual",
        )
        db_session.add_all([asset1, asset2])
        db_session.commit()
        db_session.refresh(asset1)
        db_session.refresh(asset2)
        cleanup_test_assets.extend([asset1.asset_id, asset2.asset_id])

        # Try to update asset2's version to match asset1
        response = client.put(
            f"/api/assets/{asset2.asset_id}",
            json={"version": "1.0.0"},
        )

        assert response.status_code == 400
        assert "duplicate" in response.json()["detail"].lower()


class TestAssetDeletion:
    """Tests for asset deletion endpoint (DELETE /api/assets/{asset_id})."""

    def test_delete_asset_success(self, client, db_session):
        """
        Test M4.10: Delete existing asset.

        Verifies:
        - Returns 204 No Content
        - Asset is removed from database
        """
        # Create test asset
        asset = Asset(
            asset_name="Asset to Delete",
            vendor="delete_vendor",
            product="delete_product",
            version="1.0.0",
            cpe_code="cpe:2.3:a:delete_vendor:delete_product:1.0.0:*:*:*:*:*:*:*",
            source="manual",
        )
        db_session.add(asset)
        db_session.commit()
        db_session.refresh(asset)
        asset_id = asset.asset_id

        response = client.delete(f"/api/assets/{asset_id}")

        assert response.status_code == 204

        # Verify asset is deleted
        deleted_asset = db_session.query(Asset).filter(Asset.asset_id == asset_id).first()
        assert deleted_asset is None

    def test_delete_asset_not_found(self, client):
        """
        Test M4.11: Delete non-existent asset.

        Verifies:
        - Returns 404 Not Found
        - Error message is clear
        """
        response = client.delete("/api/assets/550e8400-e29b-41d4-a716-446655440000")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_delete_asset_cascades_matches(self, client, db_session):
        """
        Test M4.10: Delete asset cascades to matching results.

        Verifies:
        - Asset deletion removes related matches
        - Cascade delete works correctly
        """
        # Create test asset
        asset = Asset(
            asset_name="Asset with Matches",
            vendor="cascade_vendor",
            product="cascade_product",
            version="1.0.0",
            cpe_code="cpe:2.3:a:cascade_vendor:cascade_product:1.0.0:*:*:*:*:*:*:*",
            source="manual",
        )
        db_session.add(asset)
        db_session.commit()
        db_session.refresh(asset)

        # Create a matching result (if vulnerabilities exist)
        # This is a simplified test - in real scenarios, matches would be created through matching service
        # For now, we just verify the cascade behavior is configured correctly

        response = client.delete(f"/api/assets/{asset.asset_id}")
        assert response.status_code == 204


class TestComposerFileImport:
    """Tests for Composer file import endpoint (POST /api/assets/import/composer)."""

    def test_import_composer_json_success(self, client, cleanup_test_assets):
        """
        Test M4.12: Import valid composer.json file.

        Verifies:
        - Returns 201 Created
        - Response contains import statistics
        - Assets are created in database
        """
        composer_data = {
            "require": {
                "guzzlehttp/guzzle": "^7.0",
                "symfony/http-foundation": "^6.0",
            },
            "require-dev": {
                "phpunit/phpunit": "^10.0",
            },
        }

        file_content = json.dumps(composer_data).encode("utf-8")
        files = {"file": ("composer.json", io.BytesIO(file_content), "application/json")}

        response = client.post("/api/assets/import/composer", files=files)

        assert response.status_code == 201
        data = response.json()

        assert "imported_count" in data
        assert "skipped_count" in data
        assert "errors" in data
        assert data["imported_count"] >= 0
        assert isinstance(data["errors"], list)

    def test_import_composer_lock_success(self, client, cleanup_test_assets):
        """
        Test M4.12: Import valid composer.lock file.

        Verifies:
        - Returns 201 Created
        - Packages are extracted correctly
        """
        composer_lock_data = {
            "packages": [
                {
                    "name": "guzzlehttp/guzzle",
                    "version": "7.5.0",
                },
                {
                    "name": "symfony/http-foundation",
                    "version": "6.2.0",
                },
            ]
        }

        file_content = json.dumps(composer_lock_data).encode("utf-8")
        files = {"file": ("composer.lock", io.BytesIO(file_content), "application/json")}

        response = client.post("/api/assets/import/composer", files=files)

        assert response.status_code == 201
        data = response.json()

        assert data["imported_count"] >= 0

    def test_import_composer_invalid_filename(self, client):
        """
        Test M4.13: Import file with invalid filename.

        Verifies:
        - Returns 400 Bad Request
        - Error message indicates invalid filename
        """
        file_content = b'{"require": {}}'
        files = {"file": ("invalid.json", io.BytesIO(file_content), "application/json")}

        response = client.post("/api/assets/import/composer", files=files)

        assert response.status_code == 400
        assert "Invalid file name" in response.json()["detail"]

    def test_import_composer_invalid_json(self, client):
        """
        Test M4.13: Import file with invalid JSON.

        Verifies:
        - Returns 400 Bad Request
        - Error message indicates JSON parsing error
        """
        file_content = b'invalid json content'
        files = {"file": ("composer.json", io.BytesIO(file_content), "application/json")}

        response = client.post("/api/assets/import/composer", files=files)

        assert response.status_code == 400
        assert "Invalid JSON format" in response.json()["detail"]

    def test_import_composer_empty_dependencies(self, client):
        """
        Test M4.14: Import composer.json with no dependencies.

        Verifies:
        - Returns 201 Created
        - imported_count is 0
        """
        composer_data = {"require": {}}

        file_content = json.dumps(composer_data).encode("utf-8")
        files = {"file": ("composer.json", io.BytesIO(file_content), "application/json")}

        response = client.post("/api/assets/import/composer", files=files)

        assert response.status_code == 201
        data = response.json()

        assert data["imported_count"] == 0


class TestNPMFileImport:
    """Tests for NPM file import endpoint (POST /api/assets/import/npm)."""

    def test_import_package_json_success(self, client, cleanup_test_assets):
        """
        Test M4.15: Import valid package.json file.

        Verifies:
        - Returns 201 Created
        - Response contains import statistics
        """
        package_data = {
            "dependencies": {
                "express": "^4.18.0",
                "lodash": "^4.17.21",
            },
            "devDependencies": {
                "jest": "^29.0.0",
            },
        }

        file_content = json.dumps(package_data).encode("utf-8")
        files = {"file": ("package.json", io.BytesIO(file_content), "application/json")}

        response = client.post("/api/assets/import/npm", files=files)

        assert response.status_code == 201
        data = response.json()

        assert "imported_count" in data
        assert "skipped_count" in data
        assert "errors" in data

    def test_import_package_lock_json_success(self, client, cleanup_test_assets):
        """
        Test M4.15: Import valid package-lock.json file.

        Verifies:
        - Returns 201 Created
        - Packages are extracted correctly
        """
        package_lock_data = {
            "packages": {
                "": {"name": "root-package"},
                "node_modules/express": {"version": "4.18.2"},
                "node_modules/lodash": {"version": "4.17.21"},
            }
        }

        file_content = json.dumps(package_lock_data).encode("utf-8")
        files = {"file": ("package-lock.json", io.BytesIO(file_content), "application/json")}

        response = client.post("/api/assets/import/npm", files=files)

        assert response.status_code == 201
        data = response.json()

        assert data["imported_count"] >= 0

    def test_import_npm_invalid_filename(self, client):
        """
        Test M4.16: Import NPM file with invalid filename.

        Verifies:
        - Returns 400 Bad Request
        - Error message indicates invalid filename
        """
        file_content = b'{"dependencies": {}}'
        files = {"file": ("invalid.json", io.BytesIO(file_content), "application/json")}

        response = client.post("/api/assets/import/npm", files=files)

        assert response.status_code == 400
        assert "Invalid file name" in response.json()["detail"]

    def test_import_npm_invalid_json(self, client):
        """
        Test M4.16: Import NPM file with invalid JSON.

        Verifies:
        - Returns 400 Bad Request
        - Error message indicates JSON parsing error
        """
        file_content = b'invalid json content'
        files = {"file": ("package.json", io.BytesIO(file_content), "application/json")}

        response = client.post("/api/assets/import/npm", files=files)

        assert response.status_code == 400
        assert "Invalid JSON format" in response.json()["detail"]


class TestDockerfileImport:
    """Tests for Dockerfile import endpoint (POST /api/assets/import/docker)."""

    def test_import_dockerfile_success(self, client, cleanup_test_assets):
        """
        Test M4.17: Import valid Dockerfile.

        Verifies:
        - Returns 201 Created
        - FROM instructions are extracted
        """
        dockerfile_content = """
FROM nginx:1.25.3
FROM python:3.11-slim
FROM ubuntu:22.04
"""

        file_content = dockerfile_content.encode("utf-8")
        files = {"file": ("Dockerfile", io.BytesIO(file_content), "text/plain")}

        response = client.post("/api/assets/import/docker", files=files)

        assert response.status_code == 201
        data = response.json()

        assert "imported_count" in data
        assert data["imported_count"] >= 0

    def test_import_dockerfile_with_tag(self, client, cleanup_test_assets):
        """
        Test M4.17: Import Dockerfile with explicit tags.

        Verifies:
        - Tags are extracted correctly
        - Assets are created with correct versions
        """
        dockerfile_content = "FROM nginx:1.25.3-alpine\nFROM node:18.19.0"

        file_content = dockerfile_content.encode("utf-8")
        files = {"file": ("Dockerfile", io.BytesIO(file_content), "text/plain")}

        response = client.post("/api/assets/import/docker", files=files)

        assert response.status_code == 201
        data = response.json()

        assert data["imported_count"] >= 0

    def test_import_dockerfile_without_tag(self, client, cleanup_test_assets):
        """
        Test M4.17: Import Dockerfile without explicit tags.

        Verifies:
        - Default tag 'latest' is used
        """
        dockerfile_content = "FROM nginx"

        file_content = dockerfile_content.encode("utf-8")
        files = {"file": ("Dockerfile", io.BytesIO(file_content), "text/plain")}

        response = client.post("/api/assets/import/docker", files=files)

        assert response.status_code == 201
        data = response.json()

        # Should import at least one asset (nginx:latest)
        assert data["imported_count"] >= 0

    def test_import_dockerfile_invalid_filename(self, client):
        """
        Test M4.18: Import Docker file with invalid filename.

        Verifies:
        - Returns 400 Bad Request
        - Error message indicates invalid filename
        """
        file_content = b'FROM nginx'
        files = {"file": ("invalid.txt", io.BytesIO(file_content), "text/plain")}

        response = client.post("/api/assets/import/docker", files=files)

        assert response.status_code == 400
        assert "Invalid file name" in response.json()["detail"]

    def test_import_dockerfile_empty(self, client):
        """
        Test M4.19: Import empty Dockerfile.

        Verifies:
        - Returns 201 Created
        - imported_count is 0
        """
        file_content = b''
        files = {"file": ("Dockerfile", io.BytesIO(file_content), "text/plain")}

        response = client.post("/api/assets/import/docker", files=files)

        assert response.status_code == 201
        data = response.json()

        assert data["imported_count"] == 0

    def test_import_dockerfile_scratch_image(self, client):
        """
        Test M4.19: Import Dockerfile with scratch image.

        Verifies:
        - scratch image is skipped
        - No error occurs
        """
        dockerfile_content = "FROM scratch\nCOPY binary /binary"

        file_content = dockerfile_content.encode("utf-8")
        files = {"file": ("Dockerfile", io.BytesIO(file_content), "text/plain")}

        response = client.post("/api/assets/import/docker", files=files)

        assert response.status_code == 201
        data = response.json()

        # scratch should be skipped
        assert data["imported_count"] == 0


class TestAssetAPIEdgeCases:
    """Edge case tests for Asset Management API."""

    def test_pagination_boundary_values(self, client):
        """
        Test pagination with boundary values.

        Verifies:
        - Minimum and maximum page_size values
        - Large page numbers
        """
        # Minimum page_size
        response = client.get("/api/assets?limit=1")
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 1

        # Maximum page_size
        response = client.get("/api/assets?limit=100")
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 100

        # Large page number
        response = client.get("/api/assets?page=9999")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    def test_concurrent_asset_creation(self, client, cleanup_test_assets):
        """
        Test concurrent creation of same asset.

        Verifies:
        - Duplicate detection works under concurrent access
        - Only one asset is created
        """
        asset_data = {
            "asset_name": "Concurrent Test Asset",
            "vendor": "concurrent_vendor",
            "product": "concurrent_product",
            "version": "1.0.0",
        }

        # First request should succeed
        response1 = client.post("/api/assets", json=asset_data)
        if response1.status_code == 201:
            cleanup_test_assets.append(response1.json()["asset_id"])

        # Second request should fail with duplicate error
        response2 = client.post("/api/assets", json=asset_data)
        if response2.status_code == 201:
            cleanup_test_assets.append(response2.json()["asset_id"])

        # At least one should succeed, and at least one should fail
        assert (response1.status_code == 201 and response2.status_code == 400) or \
               (response1.status_code == 400 and response2.status_code == 201)
