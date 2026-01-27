"""
CPE matching service for vulnerability and asset correlation.

This module provides matching algorithms to correlate assets with vulnerabilities
based on CPE (Common Platform Enumeration) codes:
- Exact match: Full CPE code match
- Version range match: Version falls within vulnerability's affected range
- Wildcard match: Partial CPE match with wildcards
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from packaging import version
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.models.asset import Asset, AssetVulnerabilityMatch
from src.models.vulnerability import Vulnerability
from src.utils.cpe_generator import extract_cpe_parts

logger = logging.getLogger(__name__)


def match_exact(asset_cpe: str, vulnerability_cpe: str) -> bool:
    """
    Perform exact CPE code matching.

    Compares the first 8 parts of CPE codes (cpe:2.3:part:vendor:product:version:update:edition).

    Args:
        asset_cpe: Asset's CPE code (e.g., "cpe:2.3:a:nginx:nginx:1.25.3:*:*:*:*:*:*:*")
        vulnerability_cpe: Vulnerability's CPE code

    Returns:
        True if exact match, False otherwise

    Examples:
        >>> match_exact("cpe:2.3:a:nginx:nginx:1.25.3:*:*:*:*:*:*:*", "cpe:2.3:a:nginx:nginx:1.25.3:*:*:*:*:*:*:*")
        True
        >>> match_exact("cpe:2.3:a:nginx:nginx:1.25.3:*:*:*:*:*:*:*", "cpe:2.3:a:nginx:nginx:1.25.4:*:*:*:*:*:*:*")
        False
    """
    # Extract first 8 parts (cpe, 2.3, part, vendor, product, version, update, edition)
    asset_parts = asset_cpe.split(":")[:8]
    vuln_parts = vulnerability_cpe.split(":")[:8]

    return asset_parts == vuln_parts


def match_version_range(
    asset_vendor: str, asset_product: str, asset_version: str, vulnerability_ranges: Dict
) -> bool:
    """
    Perform version range matching.

    Checks if asset version falls within vulnerability's version range.

    Args:
        asset_vendor: Asset's vendor name (e.g., "nginx")
        asset_product: Asset's product name (e.g., "nginx")
        asset_version: Asset's version (e.g., "1.25.3")
        vulnerability_ranges: Vulnerability's version ranges (from affected_products.version_ranges)

    Returns:
        True if version is within range, False otherwise

    Examples:
        >>> ranges = {"nginx": {"versionStartIncluding": "1.25.0", "versionEndExcluding": "1.25.4"}}
        >>> match_version_range("nginx", "nginx", "1.25.3", ranges)
        True
        >>> match_version_range("nginx", "nginx", "1.25.5", ranges)
        False
    """
    if not vulnerability_ranges:
        return False

    # Search for product ranges (check both product name and vendor:product format)
    product_ranges = vulnerability_ranges.get(asset_product) or vulnerability_ranges.get(
        f"{asset_vendor}:{asset_product}"
    )

    if not product_ranges:
        return False

    try:
        asset_ver = version.parse(asset_version)
    except Exception as e:
        logger.warning(f"Failed to parse asset version '{asset_version}': {e}")
        return False

    # Check versionStartIncluding (greater than or equal to)
    if "versionStartIncluding" in product_ranges:
        try:
            start_ver = version.parse(product_ranges["versionStartIncluding"])
            if asset_ver < start_ver:
                return False
        except Exception as e:
            logger.warning(f"Failed to parse versionStartIncluding '{product_ranges['versionStartIncluding']}': {e}")
            return False

    # Check versionStartExcluding (greater than)
    if "versionStartExcluding" in product_ranges:
        try:
            start_ver = version.parse(product_ranges["versionStartExcluding"])
            if asset_ver <= start_ver:
                return False
        except Exception as e:
            logger.warning(f"Failed to parse versionStartExcluding '{product_ranges['versionStartExcluding']}': {e}")
            return False

    # Check versionEndIncluding (less than or equal to)
    if "versionEndIncluding" in product_ranges:
        try:
            end_ver = version.parse(product_ranges["versionEndIncluding"])
            if asset_ver > end_ver:
                return False
        except Exception as e:
            logger.warning(f"Failed to parse versionEndIncluding '{product_ranges['versionEndIncluding']}': {e}")
            return False

    # Check versionEndExcluding (less than)
    if "versionEndExcluding" in product_ranges:
        try:
            end_ver = version.parse(product_ranges["versionEndExcluding"])
            if asset_ver >= end_ver:
                return False
        except Exception as e:
            logger.warning(f"Failed to parse versionEndExcluding '{product_ranges['versionEndExcluding']}': {e}")
            return False

    return True


def match_wildcard(asset_cpe: str, vulnerability_cpe: str) -> bool:
    """
    Perform wildcard CPE matching.

    Matches CPE codes with wildcards (*). Requires part, vendor, and product to match,
    and all remaining fields in vulnerability CPE to be wildcards.

    Args:
        asset_cpe: Asset's CPE code
        vulnerability_cpe: Vulnerability's CPE code (may contain wildcards)

    Returns:
        True if wildcard match, False otherwise

    Examples:
        >>> match_wildcard("cpe:2.3:a:nginx:nginx:1.25.3:*:*:*:*:*:*:*", "cpe:2.3:a:nginx:nginx:*:*:*:*:*:*:*:*")
        True
        >>> match_wildcard("cpe:2.3:a:nginx:nginx:1.25.3:*:*:*:*:*:*:*", "cpe:2.3:a:apache:httpd:*:*:*:*:*:*:*:*")
        False
    """
    asset_parts = asset_cpe.split(":")
    vuln_parts = vulnerability_cpe.split(":")

    # Must have at least 8 parts (cpe:2.3:part:vendor:product:version:update:edition)
    if len(asset_parts) < 8 or len(vuln_parts) < 8:
        return False

    # Part, vendor, and product must match
    if (
        asset_parts[2] != vuln_parts[2]  # part (a/h/o)
        or asset_parts[3] != vuln_parts[3]  # vendor
        or asset_parts[4] != vuln_parts[4]  # product
    ):
        return False

    # Version and beyond must be wildcards in vulnerability CPE
    if all(p == "*" for p in vuln_parts[5:8]):  # version, update, edition
        return True

    return False


def extract_cpe_from_vulnerability(vulnerability: Vulnerability) -> List[str]:
    """
    Extract CPE codes from vulnerability's affected_products field.

    Args:
        vulnerability: Vulnerability model instance

    Returns:
        List of CPE codes

    Examples:
        >>> vuln = Vulnerability(affected_products={"cpe": ["cpe:2.3:a:nginx:nginx:1.25.3:*:*:*:*:*:*:*"]})
        >>> extract_cpe_from_vulnerability(vuln)
        ['cpe:2.3:a:nginx:nginx:1.25.3:*:*:*:*:*:*:*']
    """
    affected_products = vulnerability.affected_products or {}
    cpe_list = affected_products.get("cpe", [])
    return cpe_list


def execute_matching(asset: Asset, vulnerability: Vulnerability) -> Optional[str]:
    """
    Execute matching between one asset and one vulnerability.

    Tries matching in order of priority:
    1. Exact match
    2. Version range match
    3. Wildcard match

    Args:
        asset: Asset model instance
        vulnerability: Vulnerability model instance

    Returns:
        Match reason ("exact_match" / "version_range" / "wildcard_match") or None

    Examples:
        >>> asset = Asset(cpe_code="cpe:2.3:a:nginx:nginx:1.25.3:*:*:*:*:*:*:*", vendor="nginx", product="nginx", version="1.25.3")
        >>> vuln = Vulnerability(affected_products={"cpe": ["cpe:2.3:a:nginx:nginx:1.25.3:*:*:*:*:*:*:*"]})
        >>> execute_matching(asset, vuln)
        'exact_match'
    """
    # 1. Exact match (highest priority)
    vuln_cpe_list = extract_cpe_from_vulnerability(vulnerability)
    for vuln_cpe in vuln_cpe_list:
        if match_exact(asset.cpe_code, vuln_cpe):
            return "exact_match"

    # 2. Version range match
    version_ranges = vulnerability.affected_products.get("version_ranges", {}) if vulnerability.affected_products else {}
    if version_ranges:
        # Extract asset parts from CPE code
        asset_parts = extract_cpe_parts(asset.cpe_code)
        if asset_parts:
            if match_version_range(asset_parts["vendor"], asset_parts["product"], asset_parts["version"], version_ranges):
                return "version_range"

    # 3. Wildcard match (lowest priority)
    for vuln_cpe in vuln_cpe_list:
        if match_wildcard(asset.cpe_code, vuln_cpe):
            return "wildcard_match"

    return None  # No match


def execute_full_matching(db: Session) -> Dict[str, int]:
    """
    Execute matching for all assets and vulnerabilities.

    This is a batch processing function that:
    1. Retrieves all assets and vulnerabilities
    2. Performs matching for each asset-vulnerability pair
    3. Stores results in asset_vulnerability_matches table (UPSERT)
    4. Returns matching statistics

    Args:
        db: SQLAlchemy database session

    Returns:
        Dictionary with matching statistics:
        - total_assets: Total number of assets processed
        - total_vulnerabilities: Total number of vulnerabilities processed
        - total_matches: Total number of matches found
        - exact_matches: Number of exact matches
        - version_range_matches: Number of version range matches
        - wildcard_matches: Number of wildcard matches

    Examples:
        >>> stats = execute_full_matching(db)
        >>> print(f"Found {stats['total_matches']} matches")
    """
    logger.info("Starting full matching execution...")

    # Retrieve all assets and vulnerabilities
    assets = db.query(Asset).all()
    vulnerabilities = db.query(Vulnerability).all()

    logger.info(f"Processing {len(assets)} assets and {len(vulnerabilities)} vulnerabilities")

    matches = []
    match_stats = {"exact_match": 0, "version_range": 0, "wildcard_match": 0}

    # Perform matching for each asset-vulnerability pair
    for asset in assets:
        for vulnerability in vulnerabilities:
            match_reason = execute_matching(asset, vulnerability)
            if match_reason:
                matches.append(
                    {
                        "asset_id": asset.asset_id,
                        "cve_id": vulnerability.cve_id,
                        "match_reason": match_reason,
                        "matched_at": datetime.now(),
                    }
                )
                match_stats[match_reason] += 1

    logger.info(f"Found {len(matches)} matches: {match_stats}")

    # UPSERT matches to database (insert or update on conflict)
    if matches:
        for match in matches:
            db.execute(
                text(
                    """
                    INSERT INTO asset_vulnerability_matches (match_id, asset_id, cve_id, match_reason, matched_at)
                    VALUES (gen_random_uuid(), :asset_id, :cve_id, :match_reason, :matched_at)
                    ON CONFLICT (asset_id, cve_id)
                    DO UPDATE SET match_reason = EXCLUDED.match_reason, matched_at = EXCLUDED.matched_at
                    """
                ),
                match,
            )
        db.commit()
        logger.info(f"Stored {len(matches)} matches to database")

    return {
        "total_assets": len(assets),
        "total_vulnerabilities": len(vulnerabilities),
        "total_matches": len(matches),
        "exact_matches": match_stats["exact_match"],
        "version_range_matches": match_stats["version_range"],
        "wildcard_matches": match_stats["wildcard_match"],
    }
