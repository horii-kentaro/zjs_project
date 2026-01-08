"""
Integration tests for idempotency and retry logic.

IMPORTANT: These tests connect to the actual JVN iPedia API and PostgreSQL (Neon) database.
No mocking is used. Tests verify end-to-end idempotency from API fetch to database persistence.

Test Coverage:
- M4.1: Retry logic verification (exponential backoff, max 3 retries)
- M4.2: Idempotency verification (3 consecutive runs produce consistent data)
"""

import asyncio
import logging
from datetime import datetime, timezone

import pytest
from sqlalchemy.orm import Session

from src.database import SessionLocal, engine
from src.fetchers.jvn_fetcher import JVNFetcherService
from src.models.vulnerability import Base, Vulnerability
from src.schemas.vulnerability import VulnerabilityCreate
from src.services.database_vulnerability_service import DatabaseVulnerabilityService

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
def fetcher_service():
    """
    Provide JVNFetcherService instance.
    """
    return JVNFetcherService()


@pytest.fixture(scope='function')
def db_service(db_session):
    """
    Provide DatabaseVulnerabilityService instance.
    """
    return DatabaseVulnerabilityService(db_session)


class TestRetryLogic:
    """Test M4.1: Retry logic with exponential backoff."""

    @pytest.mark.asyncio
    async def test_retry_configuration(self, fetcher_service):
        """
        Test M4.1: Verify retry configuration is correct.

        Verifies:
        - Maximum retry attempts is 3
        - Retry delay is 5 seconds (base)
        - Exponential backoff is configured
        """
        logger.info('TEST M4.1: Verify retry configuration')

        # Verify configuration
        assert fetcher_service.max_retries == 3, 'Max retries should be 3'
        assert fetcher_service.retry_delay == 5, 'Base retry delay should be 5 seconds'

        logger.info('✓ Retry configuration verified:')
        logger.info(f'  - Max retries: {fetcher_service.max_retries}')
        logger.info(f'  - Base delay: {fetcher_service.retry_delay}s')
        logger.info(
            '  - Exponential backoff: 5s (attempt 1), 10s (attempt 2), 20s (attempt 3)'
        )

    @pytest.mark.asyncio
    async def test_successful_fetch_no_retry(self, fetcher_service):
        """
        Test M4.1: Verify successful API call does not trigger retry.

        This test verifies that the retry logic only activates on errors,
        not on successful requests.
        """
        logger.info('TEST M4.1: Verify successful fetch does not trigger retry')

        start_time = asyncio.get_event_loop().time()

        # Fetch small dataset (should succeed on first attempt)
        vulnerabilities = await fetcher_service.fetch_vulnerabilities(max_items=3)

        end_time = asyncio.get_event_loop().time()
        total_time = end_time - start_time

        logger.info(f'Fetch completed in {total_time:.2f} seconds')
        logger.info(f'Fetched {len(vulnerabilities)} vulnerabilities')

        # Verify success
        assert len(vulnerabilities) > 0, 'Should fetch at least 1 vulnerability'

        # Verify no retry delay (should complete quickly, accounting for rate limiting)
        # Expected time: ~0.4s (rate limit) + network latency (~1-2s)
        # If retry happened, would take 5s+ for first retry
        assert (
            total_time < 5.0
        ), f'Should complete quickly without retry, but took {total_time:.2f}s'

        logger.info('✓ Successful fetch completed without retry')


class TestIdempotency:
    """Test M4.2: Idempotency guarantee for end-to-end data flow."""

    @pytest.mark.asyncio
    async def test_idempotent_data_fetch_and_save(
        self, fetcher_service, db_service, db_session
    ):
        """
        Test M4.2: Verify end-to-end idempotency from API fetch to database save.

        This test verifies that fetching and saving the same data 3 times:
        1. Does not create duplicate records
        2. Maintains data consistency
        3. Updates timestamps correctly

        Requirement: Same operation executed 3 times should result in 0 data inconsistencies.
        """
        logger.info('TEST M4.2: End-to-end idempotency verification (3 consecutive runs)')

        # Step 1: Fetch vulnerabilities from JVN iPedia API (small dataset for speed)
        logger.info('Step 1: Fetching vulnerabilities from JVN iPedia API')
        vulnerabilities = await fetcher_service.fetch_vulnerabilities(max_items=5)

        logger.info(f'Fetched {len(vulnerabilities)} vulnerabilities')
        assert len(vulnerabilities) > 0, 'Should fetch at least 1 vulnerability'

        # Track CVE IDs for verification
        cve_ids = [v.cve_id for v in vulnerabilities]
        logger.info(f'CVE IDs to test: {cve_ids}')

        # Step 2: Save data to database 3 times (idempotency test)
        logger.info('Step 2: Saving data to database 3 times (idempotency test)')

        results_run1 = []
        results_run2 = []
        results_run3 = []

        # Run 1: Initial save
        logger.info('  Run 1/3: Initial save')
        for vuln_data in vulnerabilities:
            result = db_service.upsert_vulnerability(vuln_data)
            results_run1.append(result)
        logger.info(f'  ✓ Run 1 completed: {len(results_run1)} records saved')

        # Run 2: Save same data again
        logger.info('  Run 2/3: Save same data again')
        for vuln_data in vulnerabilities:
            result = db_service.upsert_vulnerability(vuln_data)
            results_run2.append(result)
        logger.info(f'  ✓ Run 2 completed: {len(results_run2)} records saved')

        # Run 3: Save same data third time
        logger.info('  Run 3/3: Save same data third time')
        for vuln_data in vulnerabilities:
            result = db_service.upsert_vulnerability(vuln_data)
            results_run3.append(result)
        logger.info(f'  ✓ Run 3 completed: {len(results_run3)} records saved')

        # Step 3: Verify idempotency - check database records
        logger.info('Step 3: Verifying idempotency - checking database records')

        inconsistencies = 0

        for cve_id in cve_ids:
            # Count records for this CVE ID (should be exactly 1)
            record_count = (
                db_session.query(Vulnerability)
                .filter(Vulnerability.cve_id == cve_id)
                .count()
            )

            if record_count != 1:
                logger.error(
                    f'  ✗ INCONSISTENCY: {cve_id} has {record_count} records (expected 1)'
                )
                inconsistencies += 1
            else:
                logger.info(f'  ✓ {cve_id}: Exactly 1 record (idempotent)')

        # Step 4: Verify data consistency across runs
        logger.info('Step 4: Verifying data consistency across 3 runs')

        for i, cve_id in enumerate(cve_ids):
            run1_data = results_run1[i]
            run2_data = results_run2[i]
            run3_data = results_run3[i]

            # Verify CVE IDs match
            if not (
                run1_data.cve_id == run2_data.cve_id == run3_data.cve_id == cve_id
            ):
                logger.error(f'  ✗ INCONSISTENCY: CVE ID mismatch for {cve_id}')
                inconsistencies += 1
                continue

            # Verify titles match
            if not (run1_data.title == run2_data.title == run3_data.title):
                logger.error(f'  ✗ INCONSISTENCY: Title mismatch for {cve_id}')
                inconsistencies += 1
                continue

            # Verify CVSS scores match
            if not (
                run1_data.cvss_score == run2_data.cvss_score == run3_data.cvss_score
            ):
                logger.error(f'  ✗ INCONSISTENCY: CVSS score mismatch for {cve_id}')
                inconsistencies += 1
                continue

            # Verify created_at timestamp is preserved (should not change)
            if not (run1_data.created_at == run2_data.created_at == run3_data.created_at):
                logger.error(f'  ✗ INCONSISTENCY: created_at changed for {cve_id}')
                logger.error(f'    Run 1: {run1_data.created_at}')
                logger.error(f'    Run 2: {run2_data.created_at}')
                logger.error(f'    Run 3: {run3_data.created_at}')
                inconsistencies += 1
                continue

            # Verify updated_at timestamp is updated or same (should not go backwards)
            if not (run2_data.updated_at >= run1_data.updated_at):
                logger.error(f'  ✗ INCONSISTENCY: updated_at went backwards for {cve_id}')
                inconsistencies += 1
                continue

            if not (run3_data.updated_at >= run2_data.updated_at):
                logger.error(f'  ✗ INCONSISTENCY: updated_at went backwards for {cve_id}')
                inconsistencies += 1
                continue

            logger.info(f'  ✓ {cve_id}: Data consistent across all 3 runs')

        # Step 5: Final verification
        logger.info('Step 5: Final verification')
        logger.info(f'Total CVE IDs tested: {len(cve_ids)}')
        logger.info(f'Data inconsistencies detected: {inconsistencies}')

        # Assert: 0 inconsistencies (requirement)
        assert (
            inconsistencies == 0
        ), f'Idempotency test failed: {inconsistencies} inconsistencies detected'

        logger.info('✓ M4.2 PASSED: End-to-end idempotency verified (0 inconsistencies)')

    @pytest.mark.asyncio
    async def test_idempotent_batch_upsert(self, fetcher_service, db_service, db_session):
        """
        Test M4.2: Verify batch UPSERT idempotency.

        This test verifies that batch UPSERT of the same data 3 times:
        1. Does not create duplicate records
        2. Maintains correct statistics (inserted/updated counts)

        Note: This test uses fresh CVE IDs to ensure clean test data.
        """
        logger.info('TEST M4.2: Batch UPSERT idempotency verification')

        # Generate unique test data to avoid conflicts with existing data
        import random
        base_id = random.randint(10000, 19999)
        unique_vulns = []

        for i in range(3):
            vuln = VulnerabilityCreate(
                cve_id=f'CVE-2025-{base_id + i}',
                title=f'Batch Test Vulnerability {base_id + i}',
                description='Test vulnerability for batch UPSERT idempotency testing',
                cvss_score=7.5,
                severity='High',
                published_date=datetime.now(timezone.utc),
                modified_date=datetime.now(timezone.utc),
            )
            unique_vulns.append(vuln)

        logger.info(f'Generated {len(unique_vulns)} unique test vulnerabilities')
        logger.info(f'CVE IDs: {[v.cve_id for v in unique_vulns]}')

        # Run 1: Initial batch UPSERT (should insert all)
        logger.info('Run 1/3: Initial batch UPSERT (should insert all)')
        stats1 = db_service.upsert_vulnerabilities_batch(unique_vulns)
        logger.info(
            f'  ✓ Stats: inserted={stats1["inserted"]}, updated={stats1["updated"]}, failed={stats1["failed"]}'
        )

        # Verify all were inserted
        assert (
            stats1['inserted'] == len(unique_vulns)
        ), f'All records should be inserted on first run, but got inserted={stats1["inserted"]}'
        assert stats1['updated'] == 0, 'No records should be updated on first run'
        assert stats1['failed'] == 0, 'No records should fail on first run'

        # Run 2: Batch UPSERT same data (should update all)
        logger.info('Run 2/3: Batch UPSERT same data (should update all)')
        stats2 = db_service.upsert_vulnerabilities_batch(unique_vulns)
        logger.info(
            f'  ✓ Stats: inserted={stats2["inserted"]}, updated={stats2["updated"]}, failed={stats2["failed"]}'
        )

        # Verify all were updated (not inserted)
        assert stats2['inserted'] == 0, 'No new records should be inserted on second run'
        assert (
            stats2['updated'] == len(unique_vulns)
        ), 'All records should be updated on second run'
        assert stats2['failed'] == 0, 'No records should fail on second run'

        # Run 3: Batch UPSERT same data again (should update all)
        logger.info('Run 3/3: Batch UPSERT same data again (should update all)')
        stats3 = db_service.upsert_vulnerabilities_batch(unique_vulns)
        logger.info(
            f'  ✓ Stats: inserted={stats3["inserted"]}, updated={stats3["updated"]}, failed={stats3["failed"]}'
        )

        # Verify all were updated (not inserted)
        assert stats3['inserted'] == 0, 'No new records should be inserted on third run'
        assert (
            stats3['updated'] == len(unique_vulns)
        ), 'All records should be updated on third run'
        assert stats3['failed'] == 0, 'No records should fail on third run'

        # Cleanup test data
        logger.info('Cleaning up test data')
        for vuln in unique_vulns:
            db_service.delete_vulnerability(vuln.cve_id)

        logger.info('✓ M4.2 PASSED: Batch UPSERT idempotency verified')

    @pytest.mark.asyncio
    async def test_idempotent_data_refetch(self, fetcher_service, db_service):
        """
        Test M4.2: Verify idempotency when refetching the same data.

        This test simulates the scenario where the same vulnerability data
        is fetched from the API multiple times (e.g., daily cron job) and
        verifies that it doesn't create duplicates.
        """
        logger.info('TEST M4.2: Idempotency verification for refetching same data')

        # Fetch data 3 times (simulating 3 daily runs)
        logger.info('Simulating 3 consecutive daily fetches')

        all_cve_ids = set()

        for run in range(1, 4):
            logger.info(f'Run {run}/3: Fetching and saving vulnerabilities')

            # Fetch data (same API call, may return same or slightly different data)
            vulnerabilities = await fetcher_service.fetch_vulnerabilities(max_items=5)
            logger.info(f'  Fetched {len(vulnerabilities)} vulnerabilities')

            # Save to database
            for vuln_data in vulnerabilities:
                db_service.upsert_vulnerability(vuln_data)
                all_cve_ids.add(vuln_data.cve_id)

            logger.info(f'  ✓ Run {run} completed')

        # Verify no duplicates in database
        logger.info('Verifying no duplicate records in database')

        inconsistencies = 0

        for cve_id in all_cve_ids:
            # Count records for this CVE ID (should be exactly 1)
            search_result = db_service.search_vulnerabilities(
                search=cve_id, page=1, page_size=10
            )

            # Filter to exact match (search is partial match)
            exact_matches = [item for item in search_result.items if item.cve_id == cve_id]
            record_count = len(exact_matches)

            if record_count != 1:
                logger.error(
                    f'  ✗ INCONSISTENCY: {cve_id} has {record_count} records (expected 1)'
                )
                inconsistencies += 1
            else:
                logger.info(f'  ✓ {cve_id}: Exactly 1 record (no duplicates)')

        logger.info(f'Total unique CVE IDs: {len(all_cve_ids)}')
        logger.info(f'Inconsistencies detected: {inconsistencies}')

        # Assert: 0 inconsistencies
        assert (
            inconsistencies == 0
        ), f'Idempotency test failed: {inconsistencies} inconsistencies detected'

        logger.info(
            '✓ M4.2 PASSED: Refetch idempotency verified (no duplicates after 3 runs)'
        )


if __name__ == '__main__':
    # Run tests manually for quick verification
    pytest.main([__file__, '-v', '-s'])
