"""
NVD API 2.0 Fetcher Service.

This module provides functionality to fetch vulnerability data from NVD (National Vulnerability Database) API 2.0.
It implements:
- JSON response parsing
- Differential data fetching
- Pagination handling
- Timeout settings
- Rate limiting
- Retry logic with exponential backoff

NVD API 2.0 Documentation: https://nvd.nist.gov/developers/vulnerabilities
"""

import asyncio
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import httpx

from src.config import settings
from src.schemas.vulnerability import VulnerabilityCreate

logger = logging.getLogger(__name__)


class NVDFetcherError(Exception):
    """Base exception for NVD Fetcher errors."""

    pass


class NVDAPIError(NVDFetcherError):
    """Exception raised when NVD API returns an error."""

    pass


class NVDParseError(NVDFetcherError):
    """Exception raised when JSON parsing fails."""

    pass


class NVDFetcherService:
    """
    Service for fetching vulnerability data from NVD API 2.0.

    This service implements:
    - JSON response parsing
    - Differential fetching logic (lastModStartDate/lastModEndDate)
    - Pagination handling (2,000 items/request)
    - Timeout setting (30 seconds)
    - Rate limiting (5 req/30s without API key, 50 req/30s with API key)
    - Retry logic with exponential backoff

    Attributes:
        api_endpoint: NVD API 2.0 endpoint URL
        api_key: NVD API key (optional, recommended for higher rate limit)
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
        rate_limit_delay: Delay between requests for rate limiting
    """

    def __init__(self, api_key: Optional[str] = None) -> None:
        """
        Initialize NVD Fetcher Service with configuration.

        Args:
            api_key: NVD API key (optional). If not provided, uses NVD_API_KEY from environment.
        """
        self.api_endpoint = os.getenv("NVD_API_ENDPOINT", "https://services.nvd.nist.gov/rest/json/cves/2.0")
        self.api_key = api_key or os.getenv("NVD_API_KEY")
        self.timeout = int(os.getenv("NVD_API_TIMEOUT", "30"))
        self.max_retries = int(os.getenv("NVD_API_MAX_RETRIES", "3"))
        self.retry_delay = int(os.getenv("NVD_API_RETRY_DELAY", "5"))

        # Rate limiting (with/without API key)
        if self.api_key:
            self.rate_limit_delay = 0.6  # 50 req/30s = 0.6s per request
        else:
            self.rate_limit_delay = 6.0  # 5 req/30s = 6s per request

        self.last_request_time = 0.0

        logger.info(
            f"NVD Fetcher Service initialized: endpoint={self.api_endpoint}, "
            f"timeout={self.timeout}s, max_retries={self.max_retries}, "
            f"api_key={'set' if self.api_key else 'not set'}, "
            f"rate_limit={self.rate_limit_delay}s"
        )

    async def fetch_vulnerabilities(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        max_items: Optional[int] = None,
    ) -> List[VulnerabilityCreate]:
        """
        Fetch vulnerability data from NVD API 2.0.

        Args:
            start_date: Start date for lastModStartDate (ISO 8601: 2024-01-01T00:00:00.000)
            end_date: End date for lastModEndDate (ISO 8601: 2024-01-01T23:59:59.999)
            max_items: Maximum number of items to fetch (default: no limit)

        Returns:
            List of VulnerabilityCreate objects

        Raises:
            NVDAPIError: API request error
            NVDParseError: JSON parsing error
        """
        logger.info(f"Starting NVD API fetch: start_date={start_date}, end_date={end_date}, max_items={max_items}")

        all_vulnerabilities: List[VulnerabilityCreate] = []
        start_index = 0
        results_per_page = 2000  # NVD API 2.0 maximum

        while True:
            # Build request parameters
            params = self._build_request_params(start_date, end_date, start_index, results_per_page)

            # Fetch data with retry logic
            response_data = await self._fetch_with_retry(params)

            # Parse response
            vulnerabilities = self._parse_response(response_data)
            all_vulnerabilities.extend(vulnerabilities)

            logger.info(f"Fetched {len(vulnerabilities)} vulnerabilities (start_index={start_index})")

            # Check if we've fetched all results or reached max_items
            total_results = response_data.get("totalResults", 0)
            if start_index + results_per_page >= total_results:
                break

            if max_items and len(all_vulnerabilities) >= max_items:
                all_vulnerabilities = all_vulnerabilities[:max_items]
                break

            start_index += results_per_page

        logger.info(f"Total fetched from NVD: {len(all_vulnerabilities)} vulnerabilities")
        return all_vulnerabilities

    async def fetch_since_last_update(self, last_update: Optional[datetime] = None) -> List[VulnerabilityCreate]:
        """
        Fetch vulnerabilities modified since the last update (differential fetching).

        Args:
            last_update: Last update datetime. If None, fetches from the last 3 years.

        Returns:
            List of VulnerabilityCreate objects
        """
        if last_update is None:
            # Default: fetch from the last 3 years
            last_update = datetime.now() - timedelta(days=365 * 3)

        # NVD API has a 120-day range limit, so we need to split requests
        all_vulnerabilities: List[VulnerabilityCreate] = []
        current_start = last_update
        now = datetime.now()

        while current_start < now:
            # Calculate end date (max 120 days from start)
            current_end = min(current_start + timedelta(days=120), now)

            start_str = current_start.strftime("%Y-%m-%dT%H:%M:%S.000")
            end_str = current_end.strftime("%Y-%m-%dT%H:%M:%S.999")

            logger.info(f"Fetching NVD data from {start_str} to {end_str}")

            vulnerabilities = await self.fetch_vulnerabilities(start_date=start_str, end_date=end_str)
            all_vulnerabilities.extend(vulnerabilities)

            # Move to next 120-day window
            current_start = current_end + timedelta(seconds=1)

        return all_vulnerabilities

    def _build_request_params(
        self,
        start_date: Optional[str],
        end_date: Optional[str],
        start_index: int,
        results_per_page: int,
    ) -> Dict[str, str]:
        """
        Build request parameters for NVD API 2.0.

        Args:
            start_date: Start date (ISO 8601)
            end_date: End date (ISO 8601)
            start_index: Pagination start index
            results_per_page: Number of results per page

        Returns:
            Dictionary of request parameters
        """
        params = {
            "startIndex": str(start_index),
            "resultsPerPage": str(results_per_page),
        }

        if start_date:
            params["lastModStartDate"] = start_date
        if end_date:
            params["lastModEndDate"] = end_date

        return params

    async def _fetch_with_retry(self, params: Dict[str, str]) -> dict:
        """
        Fetch data from NVD API with retry logic.

        Args:
            params: Request parameters

        Returns:
            Parsed JSON response

        Raises:
            NVDAPIError: API request error after all retries
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                # Rate limiting
                await self._rate_limit()

                # Build headers
                headers = {}
                if self.api_key:
                    headers["apiKey"] = self.api_key

                # Make request
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(self.api_endpoint, params=params, headers=headers)
                    response.raise_for_status()

                    # Parse JSON
                    data = response.json()
                    return data

            except httpx.HTTPStatusError as e:
                logger.error(f"NVD API HTTP error (attempt {attempt}/{self.max_retries}): {e}")
                if attempt == self.max_retries:
                    raise NVDAPIError(f"NVD API request failed after {self.max_retries} retries: {e}")
                await asyncio.sleep(self.retry_delay * (2 ** (attempt - 1)))  # Exponential backoff

            except httpx.RequestError as e:
                logger.error(f"NVD API request error (attempt {attempt}/{self.max_retries}): {e}")
                if attempt == self.max_retries:
                    raise NVDAPIError(f"NVD API request failed after {self.max_retries} retries: {e}")
                await asyncio.sleep(self.retry_delay * (2 ** (attempt - 1)))

            except Exception as e:
                logger.error(f"Unexpected error during NVD API request: {e}")
                raise NVDAPIError(f"Unexpected error: {e}")

        raise NVDAPIError("Failed to fetch data from NVD API")

    async def _rate_limit(self) -> None:
        """
        Implement rate limiting to comply with NVD API limits.

        - Without API key: 5 req/30s (6 seconds per request)
        - With API key: 50 req/30s (0.6 seconds per request)
        """
        current_time = time.time()
        elapsed = current_time - self.last_request_time

        if elapsed < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - elapsed
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
            await asyncio.sleep(sleep_time)

        self.last_request_time = time.time()

    def _parse_response(self, response_data: dict) -> List[VulnerabilityCreate]:
        """
        Parse NVD API 2.0 JSON response.

        Args:
            response_data: JSON response from NVD API

        Returns:
            List of VulnerabilityCreate objects

        Raises:
            NVDParseError: JSON parsing error
        """
        try:
            vulnerabilities: List[VulnerabilityCreate] = []

            for item in response_data.get("vulnerabilities", []):
                cve_data = item.get("cve", {})

                # Extract basic info
                cve_id = cve_data.get("id")
                if not cve_id:
                    logger.warning("Skipping CVE with no ID")
                    continue

                # Extract descriptions (use English)
                descriptions = cve_data.get("descriptions", [])
                description = next((d["value"] for d in descriptions if d["lang"] == "en"), "")
                title = description[:500] if description else cve_id  # Use first 500 chars as title

                # Extract CVSS score and severity
                cvss_score, severity = self._extract_cvss_info(cve_data.get("metrics", {}))

                # Extract dates
                published_date = datetime.fromisoformat(cve_data["published"].replace("Z", "+00:00"))
                modified_date = datetime.fromisoformat(cve_data["lastModified"].replace("Z", "+00:00"))

                # Extract CPE data (affected_products)
                affected_products = self._extract_cpe_data(cve_data.get("configurations", []))

                # Extract references
                references = self._extract_references(cve_id, cve_data.get("references", []))

                # Create VulnerabilityCreate object
                vulnerability = VulnerabilityCreate(
                    cve_id=cve_id,
                    title=title,
                    description=description,
                    cvss_score=cvss_score,
                    severity=severity,
                    published_date=published_date,
                    modified_date=modified_date,
                    affected_products=affected_products,
                    vendor_info={},  # NVD doesn't have specific vendor info field
                    references=references,
                )

                vulnerabilities.append(vulnerability)

            return vulnerabilities

        except Exception as e:
            logger.error(f"Error parsing NVD API response: {e}")
            raise NVDParseError(f"Failed to parse NVD API response: {e}")

    def _extract_cvss_info(self, metrics: dict) -> tuple[Optional[float], Optional[str]]:
        """
        Extract CVSS score and severity from metrics.

        Args:
            metrics: Metrics object from NVD API

        Returns:
            Tuple of (cvss_score, severity)
        """
        # Prefer CVSS v3.1
        cvss_v31 = metrics.get("cvssMetricV31", [])
        if cvss_v31:
            primary_metric = next((m for m in cvss_v31 if m.get("type") == "Primary"), cvss_v31[0])
            cvss_data = primary_metric.get("cvssData", {})
            base_score = cvss_data.get("baseScore")
            base_severity = cvss_data.get("baseSeverity", "").capitalize()

            # Map NVD severity to our severity levels
            severity_map = {
                "Critical": "Critical",
                "High": "High",
                "Medium": "Medium",
                "Low": "Low",
            }
            severity = severity_map.get(base_severity)

            return base_score, severity

        # Fallback to CVSS v2
        cvss_v2 = metrics.get("cvssMetricV2", [])
        if cvss_v2:
            primary_metric = next((m for m in cvss_v2 if m.get("type") == "Primary"), cvss_v2[0])
            cvss_data = primary_metric.get("cvssData", {})
            base_score = cvss_data.get("baseScore")

            # Map CVSS v2 score to severity
            if base_score:
                if base_score >= 9.0:
                    severity = "Critical"
                elif base_score >= 7.0:
                    severity = "High"
                elif base_score >= 4.0:
                    severity = "Medium"
                else:
                    severity = "Low"
                return base_score, severity

        return None, None

    def _extract_cpe_data(self, configurations: list) -> dict:
        """
        Extract CPE data from configurations array.

        Args:
            configurations: Configurations array from NVD API

        Returns:
            Dictionary with CPE list and version ranges
        """
        cpe_list = []
        version_ranges = {}

        for config in configurations:
            for node in config.get("nodes", []):
                for cpe_match in node.get("cpeMatch", []):
                    if not cpe_match.get("vulnerable", False):
                        continue

                    criteria = cpe_match.get("criteria")
                    if criteria:
                        cpe_list.append(criteria)

                        # Extract version range info
                        version_start_including = cpe_match.get("versionStartIncluding")
                        version_start_excluding = cpe_match.get("versionStartExcluding")
                        version_end_including = cpe_match.get("versionEndIncluding")
                        version_end_excluding = cpe_match.get("versionEndExcluding")

                        # Extract product name from CPE
                        cpe_parts = criteria.split(":")
                        if len(cpe_parts) >= 5:
                            product_name = cpe_parts[4]

                            if any([version_start_including, version_start_excluding, version_end_including, version_end_excluding]):
                                if product_name not in version_ranges:
                                    version_ranges[product_name] = {}

                                if version_start_including:
                                    version_ranges[product_name]["versionStartIncluding"] = version_start_including
                                if version_start_excluding:
                                    version_ranges[product_name]["versionStartExcluding"] = version_start_excluding
                                if version_end_including:
                                    version_ranges[product_name]["versionEndIncluding"] = version_end_including
                                if version_end_excluding:
                                    version_ranges[product_name]["versionEndExcluding"] = version_end_excluding

        return {
            "cpe": cpe_list,
            "version_ranges": version_ranges,
        }

    def _extract_references(self, cve_id: str, references: list) -> dict:
        """
        Extract reference links from NVD API.

        Args:
            cve_id: CVE ID
            references: References array from NVD API

        Returns:
            Dictionary with reference links
        """
        ref_dict = {
            "nvd": f"https://nvd.nist.gov/vuln/detail/{cve_id}",
            "source": "nvd",
        }

        # Add external references (limit to first 10)
        external_refs = []
        for ref in references[:10]:
            url = ref.get("url")
            if url:
                external_refs.append(url)

        if external_refs:
            ref_dict["external"] = external_refs

        return ref_dict
