"""
Unit tests for matching service.

Tests CPE matching algorithms:
- Exact match
- Version range match
- Wildcard match
- Individual matching execution
"""

import pytest

from src.models.asset import Asset
from src.models.vulnerability import Vulnerability
from src.services.matching_service import (
    execute_matching,
    extract_cpe_from_vulnerability,
    match_exact,
    match_version_range,
    match_wildcard,
)


class TestMatchExact:
    """Test exact CPE matching."""

    def test_exact_match_success(self):
        """Test exact match with identical CPE codes."""
        asset_cpe = "cpe:2.3:a:nginx:nginx:1.25.3:*:*:*:*:*:*:*"
        vuln_cpe = "cpe:2.3:a:nginx:nginx:1.25.3:*:*:*:*:*:*:*"
        assert match_exact(asset_cpe, vuln_cpe) is True

    def test_exact_match_failure_different_version(self):
        """Test exact match fails with different versions."""
        asset_cpe = "cpe:2.3:a:nginx:nginx:1.25.3:*:*:*:*:*:*:*"
        vuln_cpe = "cpe:2.3:a:nginx:nginx:1.25.4:*:*:*:*:*:*:*"
        assert match_exact(asset_cpe, vuln_cpe) is False

    def test_exact_match_failure_different_product(self):
        """Test exact match fails with different products."""
        asset_cpe = "cpe:2.3:a:nginx:nginx:1.25.3:*:*:*:*:*:*:*"
        vuln_cpe = "cpe:2.3:a:apache:httpd:1.25.3:*:*:*:*:*:*:*"
        assert match_exact(asset_cpe, vuln_cpe) is False

    def test_exact_match_failure_different_vendor(self):
        """Test exact match fails with different vendors."""
        asset_cpe = "cpe:2.3:a:nginx:nginx:1.25.3:*:*:*:*:*:*:*"
        vuln_cpe = "cpe:2.3:a:apache:nginx:1.25.3:*:*:*:*:*:*:*"
        assert match_exact(asset_cpe, vuln_cpe) is False

    def test_exact_match_symfony_console(self):
        """Test exact match for Symfony Console."""
        asset_cpe = "cpe:2.3:a:symfony:console:5.4:*:*:*:*:*:*:*"
        vuln_cpe = "cpe:2.3:a:symfony:console:5.4:*:*:*:*:*:*:*"
        assert match_exact(asset_cpe, vuln_cpe) is True


class TestMatchVersionRange:
    """Test version range matching."""

    def test_version_in_range_including(self):
        """Test version within range (versionStartIncluding and versionEndExcluding)."""
        ranges = {"nginx": {"versionStartIncluding": "1.25.0", "versionEndExcluding": "1.25.4"}}
        assert match_version_range("nginx", "nginx", "1.25.3", ranges) is True

    def test_version_below_range(self):
        """Test version below range."""
        ranges = {"nginx": {"versionStartIncluding": "1.25.0", "versionEndExcluding": "1.25.4"}}
        assert match_version_range("nginx", "nginx", "1.24.9", ranges) is False

    def test_version_above_range(self):
        """Test version above range."""
        ranges = {"nginx": {"versionStartIncluding": "1.25.0", "versionEndExcluding": "1.25.4"}}
        assert match_version_range("nginx", "nginx", "1.25.5", ranges) is False

    def test_version_at_start_boundary_including(self):
        """Test version at start boundary (versionStartIncluding)."""
        ranges = {"nginx": {"versionStartIncluding": "1.25.0", "versionEndExcluding": "1.25.4"}}
        assert match_version_range("nginx", "nginx", "1.25.0", ranges) is True

    def test_version_at_end_boundary_excluding(self):
        """Test version at end boundary (versionEndExcluding)."""
        ranges = {"nginx": {"versionStartIncluding": "1.25.0", "versionEndExcluding": "1.25.4"}}
        assert match_version_range("nginx", "nginx", "1.25.4", ranges) is False

    def test_version_start_excluding(self):
        """Test versionStartExcluding."""
        ranges = {"nginx": {"versionStartExcluding": "1.25.0", "versionEndExcluding": "1.25.4"}}
        assert match_version_range("nginx", "nginx", "1.25.0", ranges) is False
        assert match_version_range("nginx", "nginx", "1.25.1", ranges) is True

    def test_version_end_including(self):
        """Test versionEndIncluding."""
        ranges = {"nginx": {"versionStartIncluding": "1.25.0", "versionEndIncluding": "1.25.4"}}
        assert match_version_range("nginx", "nginx", "1.25.4", ranges) is True
        assert match_version_range("nginx", "nginx", "1.25.5", ranges) is False

    def test_vendor_product_format(self):
        """Test vendor:product format in ranges."""
        ranges = {"nginx:nginx": {"versionStartIncluding": "1.25.0", "versionEndExcluding": "1.25.4"}}
        assert match_version_range("nginx", "nginx", "1.25.3", ranges) is True

    def test_product_not_in_ranges(self):
        """Test product not found in ranges."""
        ranges = {"apache": {"versionStartIncluding": "2.4.0", "versionEndExcluding": "2.5.0"}}
        assert match_version_range("nginx", "nginx", "1.25.3", ranges) is False

    def test_empty_ranges(self):
        """Test with empty ranges."""
        assert match_version_range("nginx", "nginx", "1.25.3", {}) is False

    def test_invalid_version_format(self):
        """Test with invalid version format."""
        ranges = {"nginx": {"versionStartIncluding": "1.25.0", "versionEndExcluding": "1.25.4"}}
        assert match_version_range("nginx", "nginx", "invalid", ranges) is False

    def test_complex_version_numbers(self):
        """Test complex version numbers."""
        ranges = {"react": {"versionStartIncluding": "18.0.0", "versionEndExcluding": "18.3.0"}}
        assert match_version_range("facebook", "react", "18.2.0", ranges) is True
        assert match_version_range("facebook", "react", "17.0.0", ranges) is False


class TestMatchWildcard:
    """Test wildcard CPE matching."""

    def test_wildcard_match_version(self):
        """Test wildcard match with version wildcard."""
        asset_cpe = "cpe:2.3:a:nginx:nginx:1.25.3:*:*:*:*:*:*:*"
        vuln_cpe = "cpe:2.3:a:nginx:nginx:*:*:*:*:*:*:*:*"
        assert match_wildcard(asset_cpe, vuln_cpe) is True

    def test_wildcard_match_different_vendor(self):
        """Test wildcard match fails with different vendor."""
        asset_cpe = "cpe:2.3:a:nginx:nginx:1.25.3:*:*:*:*:*:*:*"
        vuln_cpe = "cpe:2.3:a:apache:nginx:*:*:*:*:*:*:*:*"
        assert match_wildcard(asset_cpe, vuln_cpe) is False

    def test_wildcard_match_different_product(self):
        """Test wildcard match fails with different product."""
        asset_cpe = "cpe:2.3:a:nginx:nginx:1.25.3:*:*:*:*:*:*:*"
        vuln_cpe = "cpe:2.3:a:nginx:httpd:*:*:*:*:*:*:*:*"
        assert match_wildcard(asset_cpe, vuln_cpe) is False

    def test_wildcard_match_different_part(self):
        """Test wildcard match fails with different part."""
        asset_cpe = "cpe:2.3:a:nginx:nginx:1.25.3:*:*:*:*:*:*:*"
        vuln_cpe = "cpe:2.3:h:nginx:nginx:*:*:*:*:*:*:*:*"  # h (hardware) instead of a (application)
        assert match_wildcard(asset_cpe, vuln_cpe) is False

    def test_wildcard_match_specific_version(self):
        """Test wildcard match fails with specific version in vulnerability."""
        asset_cpe = "cpe:2.3:a:nginx:nginx:1.25.3:*:*:*:*:*:*:*"
        vuln_cpe = "cpe:2.3:a:nginx:nginx:1.25.4:*:*:*:*:*:*:*"  # Specific version, not wildcard
        assert match_wildcard(asset_cpe, vuln_cpe) is False

    def test_wildcard_match_short_cpe(self):
        """Test wildcard match with short CPE code."""
        asset_cpe = "cpe:2.3:a:nginx"
        vuln_cpe = "cpe:2.3:a:nginx:nginx:*:*:*:*:*:*:*:*"
        assert match_wildcard(asset_cpe, vuln_cpe) is False


class TestExtractCpeFromVulnerability:
    """Test CPE extraction from vulnerability."""

    def test_extract_single_cpe(self):
        """Test extracting single CPE from vulnerability."""
        vuln = Vulnerability(
            cve_id="CVE-2024-0001",
            title="Test",
            description="Test",
            published_date="2024-01-01T00:00:00Z",
            modified_date="2024-01-01T00:00:00Z",
            affected_products={"cpe": ["cpe:2.3:a:nginx:nginx:1.25.3:*:*:*:*:*:*:*"]},
        )
        cpe_list = extract_cpe_from_vulnerability(vuln)
        assert cpe_list == ["cpe:2.3:a:nginx:nginx:1.25.3:*:*:*:*:*:*:*"]

    def test_extract_multiple_cpes(self):
        """Test extracting multiple CPEs from vulnerability."""
        vuln = Vulnerability(
            cve_id="CVE-2024-0001",
            title="Test",
            description="Test",
            published_date="2024-01-01T00:00:00Z",
            modified_date="2024-01-01T00:00:00Z",
            affected_products={
                "cpe": [
                    "cpe:2.3:a:nginx:nginx:1.25.2:*:*:*:*:*:*:*",
                    "cpe:2.3:a:nginx:nginx:1.25.3:*:*:*:*:*:*:*",
                ]
            },
        )
        cpe_list = extract_cpe_from_vulnerability(vuln)
        assert len(cpe_list) == 2

    def test_extract_empty_cpe_list(self):
        """Test extracting from vulnerability with no CPE."""
        vuln = Vulnerability(
            cve_id="CVE-2024-0001",
            title="Test",
            description="Test",
            published_date="2024-01-01T00:00:00Z",
            modified_date="2024-01-01T00:00:00Z",
            affected_products={},
        )
        cpe_list = extract_cpe_from_vulnerability(vuln)
        assert cpe_list == []

    def test_extract_none_affected_products(self):
        """Test extracting from vulnerability with None affected_products."""
        vuln = Vulnerability(
            cve_id="CVE-2024-0001",
            title="Test",
            description="Test",
            published_date="2024-01-01T00:00:00Z",
            modified_date="2024-01-01T00:00:00Z",
            affected_products=None,
        )
        cpe_list = extract_cpe_from_vulnerability(vuln)
        assert cpe_list == []


class TestExecuteMatching:
    """Test individual matching execution."""

    def test_execute_matching_exact_match(self):
        """Test matching with exact match."""
        asset = Asset(
            asset_id="550e8400-e29b-41d4-a716-446655440000",
            asset_name="Test Nginx",
            vendor="nginx",
            product="nginx",
            version="1.25.3",
            cpe_code="cpe:2.3:a:nginx:nginx:1.25.3:*:*:*:*:*:*:*",
            source="manual",
        )
        vuln = Vulnerability(
            cve_id="CVE-2024-0001",
            title="Test Vulnerability",
            description="Test description",
            published_date="2024-01-01T00:00:00Z",
            modified_date="2024-01-01T00:00:00Z",
            affected_products={"cpe": ["cpe:2.3:a:nginx:nginx:1.25.3:*:*:*:*:*:*:*"]},
        )
        result = execute_matching(asset, vuln)
        assert result == "exact_match"

    def test_execute_matching_version_range(self):
        """Test matching with version range."""
        asset = Asset(
            asset_id="550e8400-e29b-41d4-a716-446655440000",
            asset_name="Test Nginx",
            vendor="nginx",
            product="nginx",
            version="1.25.3",
            cpe_code="cpe:2.3:a:nginx:nginx:1.25.3:*:*:*:*:*:*:*",
            source="manual",
        )
        vuln = Vulnerability(
            cve_id="CVE-2024-0001",
            title="Test Vulnerability",
            description="Test description",
            published_date="2024-01-01T00:00:00Z",
            modified_date="2024-01-01T00:00:00Z",
            affected_products={
                "cpe": [],
                "version_ranges": {"nginx": {"versionStartIncluding": "1.25.0", "versionEndExcluding": "1.25.4"}},
            },
        )
        result = execute_matching(asset, vuln)
        assert result == "version_range"

    def test_execute_matching_wildcard(self):
        """Test matching with wildcard."""
        asset = Asset(
            asset_id="550e8400-e29b-41d4-a716-446655440000",
            asset_name="Test Nginx",
            vendor="nginx",
            product="nginx",
            version="1.25.3",
            cpe_code="cpe:2.3:a:nginx:nginx:1.25.3:*:*:*:*:*:*:*",
            source="manual",
        )
        vuln = Vulnerability(
            cve_id="CVE-2024-0001",
            title="Test Vulnerability",
            description="Test description",
            published_date="2024-01-01T00:00:00Z",
            modified_date="2024-01-01T00:00:00Z",
            affected_products={"cpe": ["cpe:2.3:a:nginx:nginx:*:*:*:*:*:*:*:*"]},
        )
        result = execute_matching(asset, vuln)
        assert result == "wildcard_match"

    def test_execute_matching_no_match(self):
        """Test matching with no match."""
        asset = Asset(
            asset_id="550e8400-e29b-41d4-a716-446655440000",
            asset_name="Test Nginx",
            vendor="nginx",
            product="nginx",
            version="1.25.3",
            cpe_code="cpe:2.3:a:nginx:nginx:1.25.3:*:*:*:*:*:*:*",
            source="manual",
        )
        vuln = Vulnerability(
            cve_id="CVE-2024-0001",
            title="Test Vulnerability",
            description="Test description",
            published_date="2024-01-01T00:00:00Z",
            modified_date="2024-01-01T00:00:00Z",
            affected_products={"cpe": ["cpe:2.3:a:apache:httpd:2.4.0:*:*:*:*:*:*:*"]},
        )
        result = execute_matching(asset, vuln)
        assert result is None

    def test_execute_matching_priority_exact_over_wildcard(self):
        """Test matching priority: exact match takes precedence over wildcard."""
        asset = Asset(
            asset_id="550e8400-e29b-41d4-a716-446655440000",
            asset_name="Test Nginx",
            vendor="nginx",
            product="nginx",
            version="1.25.3",
            cpe_code="cpe:2.3:a:nginx:nginx:1.25.3:*:*:*:*:*:*:*",
            source="manual",
        )
        vuln = Vulnerability(
            cve_id="CVE-2024-0001",
            title="Test Vulnerability",
            description="Test description",
            published_date="2024-01-01T00:00:00Z",
            modified_date="2024-01-01T00:00:00Z",
            affected_products={
                "cpe": [
                    "cpe:2.3:a:nginx:nginx:1.25.3:*:*:*:*:*:*:*",  # Exact match
                    "cpe:2.3:a:nginx:nginx:*:*:*:*:*:*:*:*",  # Wildcard
                ]
            },
        )
        result = execute_matching(asset, vuln)
        assert result == "exact_match"  # Exact match should win


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_version_range_invalid_range_format(self):
        """Test version range with invalid range format."""
        ranges = {"nginx": {"invalid_key": "1.25.0"}}
        # Should return True because no valid constraints are present
        assert match_version_range("nginx", "nginx", "1.25.3", ranges) is True

    def test_wildcard_match_extra_parts(self):
        """Test wildcard match with extra parts in CPE."""
        asset_cpe = "cpe:2.3:a:nginx:nginx:1.25.3:*:*:*:*:*:*:*:extra"
        vuln_cpe = "cpe:2.3:a:nginx:nginx:*:*:*:*:*:*:*:*"
        # Should still match based on first 8 parts
        assert match_wildcard(asset_cpe, vuln_cpe) is True
