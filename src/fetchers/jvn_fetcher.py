"""
JVN iPedia API Fetcher Service.

This module provides functionality to fetch vulnerability data from JVN iPedia API.
It implements:
- XML response parsing
- Differential data fetching
- Pagination handling
- Timeout settings
- Rate limiting
- Retry logic with exponential backoff

JVN iPedia API Documentation: https://jvndb.jvn.jp/apis/myjvn/
"""

import asyncio
import logging
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import httpx

from src.config import settings
from src.schemas.vulnerability import VulnerabilityCreate

logger = logging.getLogger(__name__)


class JVNFetcherError(Exception):
    """Base exception for JVN Fetcher errors."""

    pass


class JVNAPIError(JVNFetcherError):
    """Exception raised when JVN API returns an error."""

    pass


class JVNParseError(JVNFetcherError):
    """Exception raised when XML parsing fails."""

    pass


class JVNFetcherService:
    """
    Service for fetching vulnerability data from JVN iPedia API.

    This service implements all required features for M1 milestone:
    - M1.1: JVNFetcherService class creation
    - M1.2: XML response parsing (xml.etree.ElementTree)
    - M1.3: Differential fetching logic (lastModStartDate/lastModEndDate)
    - M1.4: Pagination handling (50 items/request)
    - M1.5: Timeout setting (30 seconds)
    - M1.6: Rate limiting (2-3 requests/second)

    Attributes:
        api_endpoint: JVN iPedia API endpoint URL
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
        rate_limit_delay: Delay between requests for rate limiting (0.4s = 2.5 req/s)
    """

    # XML namespace for JVN iPedia API
    NAMESPACES = {
        "status": "http://jvndb.jvn.jp/myjvn/Status",
        "rss": "http://purl.org/rss/1.0/",
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "sec": "http://jvn.jp/rss/mod_sec/3.0/",
        "dc": "http://purl.org/dc/elements/1.1/",
        "dcterms": "http://purl.org/dc/terms/",
    }

    def __init__(self) -> None:
        """Initialize JVN Fetcher Service with configuration from settings."""
        self.api_endpoint = settings.JVN_API_ENDPOINT
        self.timeout = settings.JVN_API_TIMEOUT
        self.max_retries = settings.JVN_API_MAX_RETRIES
        self.retry_delay = settings.JVN_API_RETRY_DELAY
        self.rate_limit_delay = 0.4  # 0.4 seconds = 2.5 requests/second
        self.last_request_time = 0.0

        logger.info(
            f"JVN Fetcher Service initialized: endpoint={self.api_endpoint}, "
            f"timeout={self.timeout}s, max_retries={self.max_retries}"
        )

    async def fetch_vulnerabilities(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        max_items: Optional[int] = None,
    ) -> List[VulnerabilityCreate]:
        """
        Fetch vulnerabilities from JVN iPedia API with pagination.

        This method implements M1.3 (differential fetching) and M1.4 (pagination).

        Args:
            start_date: Start date for differential fetching (ISO 8601: YYYY-MM-DD)
            end_date: End date for differential fetching (ISO 8601: YYYY-MM-DD)
            max_items: Maximum number of items to fetch (None = fetch all)

        Returns:
            List of VulnerabilityCreate objects

        Raises:
            JVNAPIError: When API returns an error
            JVNParseError: When XML parsing fails

        Example:
            >>> service = JVNFetcherService()
            >>> vulnerabilities = await service.fetch_vulnerabilities(
            ...     start_date='2024-01-01',
            ...     end_date='2024-01-31'
            ... )
            >>> len(vulnerabilities)
            150
        """
        logger.info(
            f"Starting vulnerability fetch: start_date={start_date}, end_date={end_date}, max_items={max_items}"
        )

        all_vulnerabilities: List[VulnerabilityCreate] = []
        start_item = 1
        items_per_page = 50  # JVN iPedia API maximum

        while True:
            # Check if we've reached the maximum items limit
            if max_items and len(all_vulnerabilities) >= max_items:
                logger.info(f"Reached maximum items limit: {max_items}")
                all_vulnerabilities = all_vulnerabilities[:max_items]
                break

            # Calculate how many items to fetch in this page
            fetch_count = items_per_page
            if max_items:
                remaining = max_items - len(all_vulnerabilities)
                fetch_count = min(items_per_page, remaining)

            # Fetch one page of results
            try:
                vulnerabilities = await self._fetch_page(
                    start_date=start_date,
                    end_date=end_date,
                    start_item=start_item,
                    max_count=fetch_count,
                )
            except JVNAPIError as e:
                logger.error(f"API error during pagination: {e}")
                raise
            except JVNParseError as e:
                logger.error(f"Parse error during pagination: {e}")
                raise

            if not vulnerabilities:
                logger.info(f"No more vulnerabilities found at start_item={start_item}")
                break

            all_vulnerabilities.extend(vulnerabilities)
            logger.info(f"Fetched {len(vulnerabilities)} vulnerabilities (total: {len(all_vulnerabilities)})")

            # Check if we've fetched all available items
            if len(vulnerabilities) < items_per_page:
                logger.info("Fetched all available vulnerabilities (last page was incomplete)")
                break

            # Move to next page
            start_item += items_per_page

        logger.info(f"Completed vulnerability fetch: total={len(all_vulnerabilities)} items")
        return all_vulnerabilities

    def _handle_retry_error(self, error: Exception, attempt: int, error_type: str) -> None:
        """Handle retry errors with consistent logging."""
        logger.warning(f"{error_type} (attempt {attempt}/{self.max_retries}): {error}")
        if attempt == self.max_retries:
            if isinstance(error, httpx.TimeoutException):
                raise JVNAPIError(f"API request timed out after {self.max_retries} attempts: {error}")
            elif isinstance(error, JVNParseError):
                raise error
            else:
                raise JVNAPIError(f"API request failed after {self.max_retries} attempts: {error}")

    async def _fetch_page(
        self,
        start_date: Optional[str],
        end_date: Optional[str],
        start_item: int,
        max_count: int,
    ) -> List[VulnerabilityCreate]:
        """
        Fetch a single page of vulnerabilities from JVN iPedia API.

        This method implements M1.5 (timeout) and M1.6 (rate limiting).

        Args:
            start_date: Start date for differential fetching
            end_date: End date for differential fetching
            start_item: Starting item index (1-indexed)
            max_count: Maximum items to fetch per request

        Returns:
            List of VulnerabilityCreate objects for this page

        Raises:
            JVNAPIError: When API returns an error or max retries exceeded
        """
        # Rate limiting (M1.6)
        await self._apply_rate_limit()

        # Build request parameters
        params = self._build_request_params(start_date, end_date, start_item, max_count)

        # Retry logic with exponential backoff
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug(f"Fetching page: start_item={start_item}, attempt={attempt}/{self.max_retries}")

                # M1.5: Timeout setting (30 seconds)
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(self.api_endpoint, params=params)
                    response.raise_for_status()

                # Parse XML response (M1.2)
                vulnerabilities = self._parse_xml_response(response.text)
                logger.debug(f"Successfully parsed {len(vulnerabilities)} vulnerabilities")
                return vulnerabilities

            except (httpx.HTTPStatusError, httpx.TimeoutException, httpx.RequestError) as e:
                error_type = e.__class__.__name__.replace("Exception", " error").replace("Error", " error")
                self._handle_retry_error(e, attempt, error_type)

            except JVNParseError as e:
                self._handle_retry_error(e, attempt, "XML parsing error")

            # Exponential backoff
            if attempt < self.max_retries:
                delay = self.retry_delay * (2 ** (attempt - 1))
                logger.info(f"Retrying in {delay} seconds...")
                await asyncio.sleep(delay)

        return []

    def _build_request_params(
        self, start_date: Optional[str], end_date: Optional[str], start_item: int, max_count: int
    ) -> dict:
        """Build request parameters for JVN API."""
        params = {
            "method": "getVulnOverviewList",
            "feed": "hnd",
            "startItem": str(start_item),
            "maxCountItem": str(max_count),
        }

        if start_date:
            params["datePublicStartY"] = start_date.split("-")[0]
            params["datePublicStartM"] = start_date.split("-")[1]
            params["datePublicStartD"] = start_date.split("-")[2]

        if end_date:
            params["datePublicEndY"] = end_date.split("-")[0]
            params["datePublicEndM"] = end_date.split("-")[1]
            params["datePublicEndD"] = end_date.split("-")[2]

        return params

    async def _apply_rate_limit(self) -> None:
        """
        Apply rate limiting to API requests.

        This method implements M1.6: Rate limiting (2-3 requests/second).
        Uses 0.4 seconds delay = 2.5 requests/second (safe middle ground).
        """
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time

        if time_since_last_request < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last_request
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            await asyncio.sleep(sleep_time)

        self.last_request_time = time.time()

    def _parse_xml_response(self, xml_text: str) -> List[VulnerabilityCreate]:
        """
        Parse XML response from JVN iPedia API.

        This method implements M1.2: XML response parsing using xml.etree.ElementTree.

        Args:
            xml_text: Raw XML response text from API

        Returns:
            List of VulnerabilityCreate objects

        Raises:
            JVNParseError: When XML parsing fails or required fields are missing

        Example XML structure:
            <rdf:RDF>
                <item>
                    <title>CVE-2024-0001 Title</title>
                    <link>https://jvndb.jvn.jp/...</link>
                    <description>Description text</description>
                    <sec:identifier>CVE-2024-0001</sec:identifier>
                    <dc:date>2024-01-15T00:00:00+09:00</dc:date>
                    <dcterms:modified>2024-01-20T00:00:00+09:00</dcterms:modified>
                    <sec:cvss score="9.8" severity="Critical" ... />
                </item>
            </rdf:RDF>
        """
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as e:
            raise JVNParseError(f"Failed to parse XML response: {e}")

        vulnerabilities: List[VulnerabilityCreate] = []

        # Find all <item> elements using RSS namespace
        items = root.findall(".//rss:item", self.NAMESPACES)

        if not items:
            # Try without namespace (fallback)
            items = root.findall(".//item")

        logger.debug(f"Found {len(items)} items in XML response")

        for item in items:
            try:
                # Skip "no results" message item
                title = self._get_element_text(item, "rss:title", self.NAMESPACES)
                if title and "MyJVN　該当する脆弱性対策情報はありません" in title:
                    logger.debug('Skipping "no results" message item')
                    continue

                # Extract all CVE IDs from this item
                cve_ids = self._extract_cve_ids(item, title)

                # Create a vulnerability record for each CVE ID
                for cve_id in cve_ids:
                    vulnerability = self._parse_vulnerability_item(item, cve_id)
                    vulnerabilities.append(vulnerability)

                # Log if multiple CVE IDs found
                if len(cve_ids) > 1:
                    jvndb_id = self._get_element_text(item, "sec:identifier", self.NAMESPACES)
                    logger.info(
                        f"Multiple CVE IDs found for {jvndb_id}: {', '.join(cve_ids)} "
                        f"(created {len(cve_ids)} records)"
                    )

            except Exception as e:
                # Log parsing error but continue with other items
                logger.warning(f"Failed to parse vulnerability item: {e}")
                continue

        return vulnerabilities

    def _extract_cve_ids(self, item: ET.Element, title: str) -> List[str]:
        """Extract all CVE IDs from vulnerability item (supports multiple CVEs)."""
        cve_ids = []

        # Extract all CVE IDs from sec:references elements
        references_elements = item.findall("sec:references", self.NAMESPACES)
        for ref in references_elements:
            source = ref.get("source")
            ref_id = ref.get("id")
            if source == "CVE" and ref_id and ref_id.startswith("CVE-"):
                if ref_id not in cve_ids:  # Avoid duplicates
                    cve_ids.append(ref_id)

        # If no CVE IDs found in references, try extracting from title
        if not cve_ids:
            cve_id_from_title = self._extract_cve_from_title(title)
            if cve_id_from_title:
                cve_ids.append(cve_id_from_title)

        # If still no CVE IDs found, raise error
        if not cve_ids:
            jvndb_id = self._get_element_text(item, "sec:identifier", self.NAMESPACES)
            if jvndb_id:
                raise JVNParseError(f"No CVE ID found for JVNDB entry: {jvndb_id}")

        return cve_ids

    def _extract_dates(self, item: ET.Element) -> tuple:
        """Extract published and modified dates from vulnerability item."""
        published_date_str = self._get_element_text(item, "dc:date", self.NAMESPACES)
        modified_date_str = self._get_element_text(item, "dcterms:modified", self.NAMESPACES)

        if not published_date_str:
            raise JVNParseError("Missing required field: published date")

        published_date = self._parse_date(published_date_str)
        modified_date = self._parse_date(modified_date_str) if modified_date_str else published_date

        return published_date, modified_date

    def _extract_cvss_info(self, item: ET.Element) -> tuple:
        """Extract CVSS score and severity from vulnerability item."""
        cvss_element = item.find("sec:cvss", self.NAMESPACES)
        cvss_score = None
        severity = None

        if cvss_element is not None:
            cvss_score_str = cvss_element.get("score")
            severity = cvss_element.get("severity")

            if cvss_score_str:
                try:
                    cvss_score = float(cvss_score_str)
                except ValueError:
                    logger.warning(f"Invalid CVSS score format: {cvss_score_str}")

        return cvss_score, severity

    def _parse_vulnerability_item(self, item: ET.Element, cve_id: str) -> VulnerabilityCreate:
        """
        Parse a single vulnerability item from XML for a specific CVE ID.

        Args:
            item: XML element representing a single vulnerability
            cve_id: CVE ID to use for this record

        Returns:
            VulnerabilityCreate object

        Raises:
            JVNParseError: When required fields are missing
        """
        # Extract required fields
        title = self._get_element_text(item, "rss:title", self.NAMESPACES)
        if not title:
            raise JVNParseError("Missing required field: title")

        description = self._get_element_text(item, "rss:description", self.NAMESPACES)
        if not description:
            raise JVNParseError("Missing required field: description")

        # Extract dates and CVSS info using helper methods
        published_date, modified_date = self._extract_dates(item)
        cvss_score, severity = self._extract_cvss_info(item)

        # Extract additional information
        link = self._get_element_text(item, "rss:link", self.NAMESPACES)
        references = {"jvn_link": link} if link else None

        # Create VulnerabilityCreate object
        return VulnerabilityCreate(
            cve_id=cve_id,
            title=title,
            description=description,
            cvss_score=cvss_score,
            severity=severity,
            published_date=published_date,
            modified_date=modified_date,
            affected_products=None,  # Not available in overview list
            vendor_info=None,  # Not available in overview list
            references=references,
        )

    def _get_element_text(
        self,
        parent: ET.Element,
        tag: str,
        namespaces: Optional[Dict[str, str]] = None,
    ) -> Optional[str]:
        """
        Get text content of a child element.

        Args:
            parent: Parent XML element
            tag: Tag name to search for
            namespaces: XML namespaces (optional)

        Returns:
            Text content or None if element not found
        """
        # Try with namespace first
        element = parent.find(tag, namespaces) if namespaces else None

        # If not found and tag doesn't have namespace prefix, try without namespace
        if element is None and namespaces and ":" not in tag:
            # Search for element by local name (without namespace)
            for child in parent:
                local_name = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                if local_name == tag:
                    element = child
                    break

        # Fallback: try without namespace
        if element is None:
            element = parent.find(tag)

        return element.text.strip() if element is not None and element.text else None

    def _extract_cve_from_title(self, title: str) -> Optional[str]:
        """
        Extract CVE ID from title string.

        Args:
            title: Title string that may contain CVE ID

        Returns:
            CVE ID or None if not found

        Example:
            >>> service._extract_cve_from_title('CVE-2024-0001: Buffer overflow')
            'CVE-2024-0001'
        """
        import re

        pattern = r"CVE-\d{4}-\d{4,}"
        match = re.search(pattern, title)
        return match.group(0) if match else None

    def _parse_date(self, date_str: str) -> datetime:
        """
        Parse date string to datetime object.

        Supports multiple formats:
        - ISO 8601 with timezone: 2024-01-15T00:00:00+09:00
        - ISO 8601 UTC: 2024-01-15T00:00:00Z
        - Simple date: 2024-01-15

        Args:
            date_str: Date string to parse

        Returns:
            datetime object

        Raises:
            JVNParseError: When date parsing fails
        """
        # Remove timezone info for simplicity (store as naive datetime)
        date_str = date_str.replace("Z", "+00:00")

        # Try ISO 8601 format with timezone
        try:
            dt = datetime.fromisoformat(date_str)
            # Convert to naive datetime (remove timezone)
            return dt.replace(tzinfo=None)
        except ValueError:
            pass

        # Try simple date format
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            pass

        raise JVNParseError(f"Failed to parse date: {date_str}")

    async def fetch_since_last_update(self, last_update_date: datetime) -> List[VulnerabilityCreate]:
        """
        Fetch vulnerabilities updated since the last update date.

        This method implements M1.3: Differential fetching logic.

        Args:
            last_update_date: Last update timestamp from database

        Returns:
            List of VulnerabilityCreate objects updated since last_update_date

        Example:
            >>> service = JVNFetcherService()
            >>> last_update = datetime(2024, 1, 1)
            >>> new_vulns = await service.fetch_since_last_update(last_update)
            >>> len(new_vulns)
            50
        """
        start_date = last_update_date.strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")

        logger.info(f"Fetching vulnerabilities updated since: {start_date}")

        return await self.fetch_vulnerabilities(start_date=start_date, end_date=end_date)

    async def fetch_recent_years(self, years: int = 3) -> List[VulnerabilityCreate]:
        """
        Fetch vulnerabilities from the last N years.

        Args:
            years: Number of years to fetch (default: 3)

        Returns:
            List of VulnerabilityCreate objects from the last N years

        Example:
            >>> service = JVNFetcherService()
            >>> recent_vulns = await service.fetch_recent_years(years=3)
            >>> len(recent_vulns)
            1500
        """
        start_date = (datetime.now() - timedelta(days=365 * years)).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")

        logger.info(f"Fetching vulnerabilities from last {years} years: {start_date} to {end_date}")

        return await self.fetch_vulnerabilities(start_date=start_date, end_date=end_date)
