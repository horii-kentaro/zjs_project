#!/usr/bin/env python3
"""
Vulnerability data fetch script for GitHub Actions automation.

This script fetches vulnerability data from JVN iPedia API and stores it in the database.
It supports both full fetch and differential fetch modes.

Usage:
    # Full fetch (fetch from last 3 years)
    python scripts/fetch_vulnerabilities.py

    # Differential fetch (fetch only new/updated data)
    python scripts/fetch_vulnerabilities.py --differential

    # Fetch specific date range
    python scripts/fetch_vulnerabilities.py --start-date 2024-01-01 --end-date 2024-12-31

    # Fetch all historical data
    python scripts/fetch_vulnerabilities.py --all

Exit codes:
    0: Success
    1: Fetch error (API failure, network error, etc.)
    2: Database error
    3: Configuration error
"""

import argparse
import asyncio
import logging
import sys
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.exc import SQLAlchemyError

# Add project root to Python path
sys.path.insert(0, '/home/horii-kentaro/projects/zjs_project')

from src.config import settings
from src.database import SessionLocal, check_db_connection
from src.fetchers.jvn_fetcher import JVNAPIError, JVNFetcherService, JVNParseError
from src.fetchers.nvd_fetcher import NVDAPIError, NVDFetcherService, NVDParseError
from src.services.database_vulnerability_service import DatabaseVulnerabilityService

logger = logging.getLogger(__name__)


def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.

    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description='Fetch vulnerability data from JVN iPedia API and store in database.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        '--differential',
        action='store_true',
        help='Fetch only new/updated data since last update (default: fetch last 3 years)',
    )

    parser.add_argument(
        '--all',
        action='store_true',
        help='Fetch all historical data (may take a long time)',
    )

    parser.add_argument(
        '--start-date',
        type=str,
        help='Start date for fetching (ISO 8601: YYYY-MM-DD)',
    )

    parser.add_argument(
        '--end-date',
        type=str,
        help='End date for fetching (ISO 8601: YYYY-MM-DD)',
    )

    parser.add_argument(
        '--max-items',
        type=int,
        help='Maximum number of items to fetch (for testing)',
    )

    parser.add_argument(
        '--log-level',
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default=settings.LOG_LEVEL,
        help=f'Logging level (default: {settings.LOG_LEVEL})',
    )

    parser.add_argument(
        '--nvd-only',
        action='store_true',
        help='Fetch from NVD API only (skip JVN iPedia)',
    )

    parser.add_argument(
        '--jvn-only',
        action='store_true',
        help='Fetch from JVN iPedia API only (skip NVD)',
    )

    return parser.parse_args()


async def fetch_and_store(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    max_items: Optional[int] = None,
    differential: bool = False,
    nvd_only: bool = False,
    jvn_only: bool = False,
) -> dict:
    """
    Fetch vulnerabilities from JVN iPedia API and/or NVD API 2.0 and store in database.

    Args:
        start_date: Start date for fetching (ISO 8601: YYYY-MM-DD)
        end_date: End date for fetching (ISO 8601: YYYY-MM-DD)
        max_items: Maximum number of items to fetch (None = fetch all)
        differential: If True, fetch only data updated since last database update
        nvd_only: If True, fetch from NVD API only (skip JVN iPedia)
        jvn_only: If True, fetch from JVN iPedia API only (skip NVD)

    Returns:
        dict: Statistics with keys 'fetched', 'inserted', 'updated', 'failed'

    Raises:
        JVNAPIError: When JVN API request fails
        JVNParseError: When JVN XML parsing fails
        NVDAPIError: When NVD API request fails
        NVDParseError: When NVD JSON parsing fails
        SQLAlchemyError: When database operation fails
    """
    stats = {
        'jvn_fetched': 0,
        'nvd_fetched': 0,
        'fetched': 0,
        'inserted': 0,
        'updated': 0,
        'failed': 0,
        'start_time': datetime.now(),
        'end_time': None,
    }

    # Initialize services
    fetcher = JVNFetcherService()
    db = SessionLocal()

    try:
        db_service = DatabaseVulnerabilityService(db)

        # Determine date range
        fetch_start_date = start_date
        fetch_end_date = end_date

        if differential:
            # Fetch only new/updated data since last update
            logger.info('Differential fetch mode: fetching data since last update')
            latest_date_str = db_service.get_latest_modified_date()

            if latest_date_str:
                latest_date = datetime.fromisoformat(latest_date_str)
                fetch_start_date = latest_date.strftime('%Y-%m-%d')
                logger.info(f'Last update date: {fetch_start_date}')
            else:
                # No data in database, fetch last 3 years
                logger.warning('No data in database, falling back to last 3 years')
                fetch_start_date = (datetime.now() - timedelta(days=365 * settings.FETCH_YEARS)).strftime(
                    '%Y-%m-%d'
                )

            fetch_end_date = datetime.now().strftime('%Y-%m-%d')

        elif not start_date:
            # Default: fetch last 3 years
            fetch_start_date = (datetime.now() - timedelta(days=365 * settings.FETCH_YEARS)).strftime(
                '%Y-%m-%d'
            )
            fetch_end_date = datetime.now().strftime('%Y-%m-%d')
            logger.info(f'Default fetch mode: fetching last {settings.FETCH_YEARS} years')

        logger.info(f'Fetch date range: {fetch_start_date} to {fetch_end_date}')

        all_vulnerabilities = []

        # Fetch from JVN iPedia API (unless nvd_only is set)
        if not nvd_only:
            logger.info('Starting data fetch from JVN iPedia API...')
            jvn_fetcher = JVNFetcherService()
            jvn_vulnerabilities = await jvn_fetcher.fetch_vulnerabilities(
                start_date=fetch_start_date, end_date=fetch_end_date, max_items=max_items
            )

            stats['jvn_fetched'] = len(jvn_vulnerabilities)
            logger.info(f'Fetched {stats["jvn_fetched"]} vulnerabilities from JVN iPedia API')
            all_vulnerabilities.extend(jvn_vulnerabilities)

            # Store JVN data first
            if jvn_vulnerabilities:
                logger.info('Storing JVN vulnerabilities in database...')
                jvn_db_stats = db_service.upsert_vulnerabilities_batch(jvn_vulnerabilities)
                logger.info(
                    f'JVN data stored: inserted={jvn_db_stats["inserted"]}, '
                    f'updated={jvn_db_stats["updated"]}, failed={jvn_db_stats["failed"]}'
                )

        # Fetch from NVD API 2.0 (unless jvn_only is set)
        if not jvn_only:
            logger.info('Starting data fetch from NVD API 2.0...')
            nvd_fetcher = NVDFetcherService()

            # Convert date format for NVD API (ISO 8601 with time)
            nvd_start_date = f"{fetch_start_date}T00:00:00.000" if fetch_start_date else None
            nvd_end_date = f"{fetch_end_date}T23:59:59.999" if fetch_end_date else None

            try:
                nvd_vulnerabilities = await nvd_fetcher.fetch_vulnerabilities(
                    start_date=nvd_start_date,
                    end_date=nvd_end_date,
                    max_items=max_items,
                )

                stats['nvd_fetched'] = len(nvd_vulnerabilities)
                logger.info(f'Fetched {stats["nvd_fetched"]} vulnerabilities from NVD API 2.0')

                # Filter out duplicates (CVE IDs already in database)
                existing_cve_ids = db_service.get_all_cve_ids()
                new_vulnerabilities = [v for v in nvd_vulnerabilities if v.cve_id not in existing_cve_ids]

                logger.info(
                    f'NVD filtering: {len(nvd_vulnerabilities)} total, '
                    f'{len(new_vulnerabilities)} new (skipped {len(nvd_vulnerabilities) - len(new_vulnerabilities)} duplicates)'
                )

                all_vulnerabilities.extend(new_vulnerabilities)

                # Store NVD data
                if new_vulnerabilities:
                    logger.info('Storing NVD vulnerabilities in database...')
                    nvd_db_stats = db_service.upsert_vulnerabilities_batch(new_vulnerabilities)
                    logger.info(
                        f'NVD data stored: inserted={nvd_db_stats["inserted"]}, '
                        f'updated={nvd_db_stats["updated"]}, failed={nvd_db_stats["failed"]}'
                    )
                    stats['inserted'] += nvd_db_stats['inserted']
                    stats['updated'] += nvd_db_stats['updated']
                    stats['failed'] += nvd_db_stats['failed']

            except (NVDAPIError, NVDParseError) as e:
                logger.error(f'NVD API error (continuing with JVN data only): {e}')
                # Continue with JVN data even if NVD fails

        stats['fetched'] = len(all_vulnerabilities)

        if not all_vulnerabilities:
            logger.warning('No vulnerabilities fetched from any API')
            return stats

        logger.info(
            f'Total vulnerabilities processed: {stats["fetched"]} '
            f'(JVN: {stats["jvn_fetched"]}, NVD: {stats["nvd_fetched"]})'
        )

        return stats

    finally:
        stats['end_time'] = datetime.now()
        db.close()


def main() -> int:
    """
    Main entry point for vulnerability fetch script.

    Returns:
        int: Exit code (0 = success, 1 = fetch error, 2 = database error, 3 = configuration error)
    """
    args = parse_arguments()

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )

    logger.info('=== Vulnerability Data Fetch Started ===')
    logger.info(f'Configuration: {settings.mask_sensitive_info()}')

    # Check database connection
    logger.info('Checking database connection...')
    if not check_db_connection():
        logger.error('Database connection failed')
        logger.error('Please check DATABASE_URL in .env file')
        return 2

    logger.info('Database connection successful')

    # Determine fetch mode and parameters
    start_date = args.start_date
    end_date = args.end_date
    max_items = args.max_items
    differential = args.differential

    if args.all:
        logger.info('Fetch mode: ALL historical data')
        start_date = None
        end_date = None
    elif differential:
        logger.info('Fetch mode: DIFFERENTIAL (only new/updated data)')
    elif start_date or end_date:
        logger.info(f'Fetch mode: CUSTOM date range ({start_date} to {end_date})')
    else:
        logger.info(f'Fetch mode: DEFAULT (last {settings.FETCH_YEARS} years)')

    # Run fetch and store operation
    try:
        stats = asyncio.run(
            fetch_and_store(
                start_date=start_date,
                end_date=end_date,
                max_items=max_items,
                differential=differential,
                nvd_only=args.nvd_only,
                jvn_only=args.jvn_only,
            )
        )

        # Calculate elapsed time
        elapsed = (stats['end_time'] - stats['start_time']).total_seconds()

        # Display summary
        logger.info('=== Vulnerability Data Fetch Completed ===')
        logger.info(f'JVN fetched: {stats["jvn_fetched"]} vulnerabilities')
        logger.info(f'NVD fetched: {stats["nvd_fetched"]} vulnerabilities')
        logger.info(f'Total fetched: {stats["fetched"]} vulnerabilities')
        logger.info(f'Inserted: {stats["inserted"]} new records')
        logger.info(f'Updated: {stats["updated"]} existing records')
        logger.info(f'Failed: {stats["failed"]} errors')
        logger.info(f'Elapsed time: {elapsed:.2f} seconds')

        if stats['failed'] > 0:
            logger.warning(f'{stats["failed"]} vulnerabilities failed to store')
            return 1

        return 0

    except JVNAPIError as e:
        logger.error(f'JVN API error: {e}')
        return 1
    except JVNParseError as e:
        logger.error(f'XML parsing error: {e}')
        return 1
    except SQLAlchemyError as e:
        logger.error(f'Database error: {e}', exc_info=True)
        return 2
    except Exception as e:
        logger.error(f'Unexpected error: {e}', exc_info=True)
        return 3


if __name__ == '__main__':
    sys.exit(main())
