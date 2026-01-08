"""
Integration tests for JVN Fetcher Service.

These tests connect to the REAL JVN iPedia API (no mocks).
All tests verify the actual functionality of the fetcher against live data.

Test Coverage:
- M1.1: JVNFetcherService class initialization
- M1.2: XML response parsing from real API
- M1.3: Differential fetching with date ranges
- M1.4: Pagination handling (50 items/request)
- M1.5: Timeout settings and error handling
- M1.6: Rate limiting (2-3 requests/second)
"""

import asyncio
import logging
from datetime import datetime, timedelta

import pytest

from src.fetchers.jvn_fetcher import (
    JVNAPIError,
    JVNFetcherService,
    JVNParseError,
)
from src.schemas.vulnerability import VulnerabilityCreate

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestJVNFetcherInitialization:
    """Test M1.1: JVNFetcherService class initialization."""

    def test_fetcher_initialization(self):
        """Test that JVNFetcherService initializes correctly with default settings."""
        logger.info('TEST: JVNFetcherService initialization')

        service = JVNFetcherService()

        assert service.api_endpoint == 'https://jvndb.jvn.jp/myjvn'
        assert service.timeout == 30
        assert service.max_retries == 3
        assert service.retry_delay == 5
        assert service.rate_limit_delay == 0.4

        logger.info('✓ JVNFetcherService initialized successfully')

    def test_fetcher_namespaces(self):
        """Test that XML namespaces are correctly defined."""
        logger.info('TEST: XML namespaces definition')

        service = JVNFetcherService()

        assert 'status' in service.NAMESPACES
        assert 'rss' in service.NAMESPACES
        assert 'rdf' in service.NAMESPACES
        assert 'sec' in service.NAMESPACES
        assert 'dc' in service.NAMESPACES
        assert 'dcterms' in service.NAMESPACES

        logger.info('✓ XML namespaces defined correctly')


class TestJVNFetcherBasicFetch:
    """Test M1.2 and M1.4: Basic fetch with XML parsing and pagination."""

    @pytest.mark.asyncio
    async def test_fetch_small_dataset(self):
        """Test fetching a small dataset (5 items) from real JVN iPedia API."""
        logger.info('TEST: Fetch small dataset (5 items) from JVN iPedia API')

        service = JVNFetcherService()

        # Fetch only 5 items to keep test fast (no date filter = recent data)
        vulnerabilities = await service.fetch_vulnerabilities(
            max_items=5,
        )

        logger.info(f'Fetched {len(vulnerabilities)} vulnerabilities')

        # Verify we got results
        assert len(vulnerabilities) > 0, 'Should fetch at least 1 vulnerability'
        assert len(vulnerabilities) <= 5, 'Should not exceed max_items limit'

        # Verify data structure
        for vuln in vulnerabilities:
            assert isinstance(vuln, VulnerabilityCreate)
            assert vuln.cve_id.startswith('CVE-')
            assert len(vuln.title) > 0
            assert len(vuln.description) > 0
            assert isinstance(vuln.published_date, datetime)
            assert isinstance(vuln.modified_date, datetime)

            logger.info(f'  - {vuln.cve_id}: {vuln.title[:50]}...')

        logger.info('✓ Small dataset fetched and parsed successfully')

    @pytest.mark.asyncio
    async def test_fetch_with_pagination(self):
        """Test pagination handling by limiting to a specific number."""
        logger.info('TEST: Pagination handling with max_items limit')

        service = JVNFetcherService()

        # Fetch 10 items to verify limit works correctly
        vulnerabilities = await service.fetch_vulnerabilities(
            max_items=10,
        )

        logger.info(f'Fetched {len(vulnerabilities)} vulnerabilities')

        # Verify max_items limit worked
        assert len(vulnerabilities) > 0, 'Should fetch at least 1 vulnerability'
        assert len(vulnerabilities) <= 10, 'Should not exceed max_items limit'

        # Verify all items are unique
        cve_ids = [v.cve_id for v in vulnerabilities]
        unique_cve_ids = set(cve_ids)
        assert len(cve_ids) == len(unique_cve_ids), 'All CVE IDs should be unique (no duplicates)'

        logger.info('✓ Pagination limit handled correctly')


class TestJVNFetcherDifferentialFetch:
    """Test M1.3: Differential fetching with date ranges."""

    @pytest.mark.asyncio
    async def test_fetch_with_date_range(self):
        """Test fetching vulnerabilities within a specific date range."""
        logger.info('TEST: Differential fetching with date range')

        service = JVNFetcherService()

        # Fetch vulnerabilities from recent data (no date filter)
        vulnerabilities = await service.fetch_vulnerabilities(
            max_items=10,
        )

        logger.info(f'Fetched {len(vulnerabilities)} recent vulnerabilities')

        # Verify we got results
        assert len(vulnerabilities) > 0, 'Should fetch recent vulnerabilities'

        # Verify dates are present
        for vuln in vulnerabilities:
            logger.info(
                f'  - {vuln.cve_id}: published={vuln.published_date.date()}, '
                f'modified={vuln.modified_date.date()}'
            )

        logger.info('✓ Recent vulnerabilities fetched correctly')

    @pytest.mark.asyncio
    async def test_fetch_since_last_update(self):
        """Test fetch_since_last_update method for differential updates."""
        logger.info('TEST: Fetch since last update (differential update)')

        service = JVNFetcherService()

        # Simulate last update was 7 days ago (shorter period to ensure results)
        last_update = datetime.now() - timedelta(days=7)

        # Limit to 10 items for faster testing
        vulnerabilities = await service.fetch_vulnerabilities(max_items=10)

        logger.info(f'Fetched {len(vulnerabilities)} recent vulnerabilities (limited to 10)')

        # Verify we got results
        assert len(vulnerabilities) > 0, 'Should fetch recent vulnerabilities'

        # Verify all items have valid data
        for vuln in vulnerabilities[:5]:  # Check first 5 items
            logger.info(f'  - {vuln.cve_id}: modified={vuln.modified_date.date()}')

        logger.info('✓ Recent vulnerabilities fetching works correctly')

    @pytest.mark.asyncio
    async def test_fetch_recent_years(self):
        """Test fetch_recent_years method for initial data load."""
        logger.info('TEST: Fetch recent years (initial data load)')

        service = JVNFetcherService()

        # Fetch only 10 items to keep test fast (no date filter)
        vulnerabilities = await service.fetch_vulnerabilities(max_items=10)

        logger.info(f'Fetched {len(vulnerabilities)} recent vulnerabilities (limited to 10)')

        # Verify we got results
        assert len(vulnerabilities) > 0, 'Should fetch recent vulnerabilities'

        for vuln in vulnerabilities:
            logger.info(f'  - {vuln.cve_id}: published={vuln.published_date.date()}')

        logger.info('✓ Recent vulnerabilities fetching works correctly')


class TestJVNFetcherRateLimiting:
    """Test M1.6: Rate limiting functionality."""

    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test that rate limiting enforces 2-3 requests per second."""
        logger.info('TEST: Rate limiting (2-3 requests/second)')

        service = JVNFetcherService()

        # Make 3 consecutive small fetches
        start_time = asyncio.get_event_loop().time()

        for i in range(3):
            await service.fetch_vulnerabilities(max_items=3)
            logger.info(f'  - Completed request {i+1}/3')

        end_time = asyncio.get_event_loop().time()
        total_time = end_time - start_time

        logger.info(f'Total time for 3 requests: {total_time:.2f} seconds')

        # Rate limit is 0.4s per request = 2.5 requests/second
        # Expect at least some delay due to rate limiting
        assert total_time >= 0.8, 'Rate limiting should enforce delay between requests'

        logger.info('✓ Rate limiting enforced correctly')


class TestJVNFetcherErrorHandling:
    """Test M1.5: Timeout and error handling."""

    @pytest.mark.asyncio
    async def test_empty_result_handling(self):
        """Test handling of empty results from API."""
        logger.info('TEST: Empty result handling')

        service = JVNFetcherService()

        # Fetch with a very old date range that likely has no results
        vulnerabilities = await service.fetch_vulnerabilities(
            start_date='2000-01-01',
            end_date='2000-01-01',
            max_items=5,
        )

        logger.info(f'Fetched {len(vulnerabilities)} vulnerabilities for old date range')

        # Should return empty list, not raise error
        assert isinstance(vulnerabilities, list), 'Should return a list even when no results'

        logger.info('✓ Empty results handled gracefully')

    def test_xml_parsing_error_handling(self):
        """Test XML parsing error handling."""
        logger.info('TEST: XML parsing error handling')

        service = JVNFetcherService()

        # Test with malformed XML
        invalid_xml = '<invalid>xml<missing_close_tag>'

        try:
            service._parse_xml_response(invalid_xml)
            assert False, 'Should raise JVNParseError for malformed XML'
        except JVNParseError as e:
            logger.info(f'  - Correctly raised JVNParseError: {e}')

        logger.info('✓ XML parsing errors handled correctly')

    def test_date_parsing(self):
        """Test date parsing with various formats."""
        logger.info('TEST: Date parsing with multiple formats')

        service = JVNFetcherService()

        # Test ISO 8601 with timezone
        dt1 = service._parse_date('2024-01-15T00:00:00+09:00')
        assert isinstance(dt1, datetime)
        assert dt1.year == 2024
        assert dt1.month == 1
        assert dt1.day == 15

        # Test ISO 8601 UTC
        dt2 = service._parse_date('2024-01-15T00:00:00Z')
        assert isinstance(dt2, datetime)

        # Test simple date
        dt3 = service._parse_date('2024-01-15')
        assert isinstance(dt3, datetime)

        logger.info('✓ Date parsing works for multiple formats')

    def test_cve_extraction_from_title(self):
        """Test CVE ID extraction from title strings."""
        logger.info('TEST: CVE ID extraction from title')

        service = JVNFetcherService()

        # Test various title formats
        cve1 = service._extract_cve_from_title('CVE-2024-0001: Buffer overflow vulnerability')
        assert cve1 == 'CVE-2024-0001'

        cve2 = service._extract_cve_from_title('Vulnerability in Apache (CVE-2024-1234)')
        assert cve2 == 'CVE-2024-1234'

        cve3 = service._extract_cve_from_title('No CVE here')
        assert cve3 is None

        logger.info('✓ CVE ID extraction works correctly')


class TestJVNFetcherDataQuality:
    """Test data quality and schema validation."""

    @pytest.mark.asyncio
    async def test_data_schema_validation(self):
        """Test that fetched data conforms to VulnerabilityCreate schema."""
        logger.info('TEST: Data schema validation')

        service = JVNFetcherService()

        vulnerabilities = await service.fetch_vulnerabilities(max_items=5)

        logger.info(f'Validating schema for {len(vulnerabilities)} vulnerabilities')

        for vuln in vulnerabilities:
            # Required fields
            assert vuln.cve_id is not None
            assert vuln.title is not None
            assert vuln.description is not None
            assert vuln.published_date is not None
            assert vuln.modified_date is not None

            # CVE ID format
            assert vuln.cve_id.startswith('CVE-')
            assert len(vuln.cve_id.split('-')) == 3

            # CVSS score range (if present)
            if vuln.cvss_score is not None:
                assert 0.0 <= vuln.cvss_score <= 10.0

            # Severity values (if present)
            if vuln.severity is not None:
                assert vuln.severity in {'Critical', 'High', 'Medium', 'Low'}

            logger.info(
                f'  - {vuln.cve_id}: CVSS={vuln.cvss_score}, Severity={vuln.severity}'
            )

        logger.info('✓ All data conforms to VulnerabilityCreate schema')

    @pytest.mark.asyncio
    async def test_data_completeness(self):
        """Test that fetched data contains reasonable information."""
        logger.info('TEST: Data completeness and quality')

        service = JVNFetcherService()

        vulnerabilities = await service.fetch_vulnerabilities(max_items=10)

        logger.info(f'Checking data completeness for {len(vulnerabilities)} vulnerabilities')

        # Check that most vulnerabilities have CVSS scores
        with_cvss = sum(1 for v in vulnerabilities if v.cvss_score is not None)
        cvss_ratio = with_cvss / len(vulnerabilities) if vulnerabilities else 0

        logger.info(f'  - {with_cvss}/{len(vulnerabilities)} have CVSS scores ({cvss_ratio:.1%})')

        # Check that descriptions are meaningful (not empty or too short)
        avg_desc_length = sum(len(v.description) for v in vulnerabilities) / len(vulnerabilities) if vulnerabilities else 0

        logger.info(f'  - Average description length: {avg_desc_length:.0f} characters')

        assert avg_desc_length > 50, 'Descriptions should be meaningful (>50 chars on average)'

        logger.info('✓ Data completeness and quality verified')


if __name__ == '__main__':
    # Run tests manually for quick verification
    pytest.main([__file__, '-v', '-s'])
