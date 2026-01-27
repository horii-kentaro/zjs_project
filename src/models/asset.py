"""
SQLAlchemy models for Asset and AssetVulnerabilityMatch tables.

This module defines the Asset and AssetVulnerabilityMatch models for CPE matching functionality.
"""

import re
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.models.vulnerability import Base


class Asset(Base):
    """
    Asset information (software, libraries, containers).

    This model stores asset data for CPE matching:
    - Asset identification (name, vendor, product, version)
    - CPE code (automatically generated)
    - Source (manual/composer/npm/docker)
    - Timestamps for tracking
    """

    __tablename__ = "assets"

    # Primary key: UUID
    asset_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="Asset unique identifier (UUID)",
    )

    # Basic information
    asset_name: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="Asset name (e.g., 'Production API Server - Nginx')"
    )
    vendor: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True, comment="Vendor name (e.g., 'nginx')"
    )
    product: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True, comment="Product name (e.g., 'nginx')"
    )
    version: Mapped[str] = mapped_column(String(50), nullable=False, comment="Version (e.g., '1.25.3')")

    # CPE code
    cpe_code: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
        comment="CPE 2.3 code (e.g., 'cpe:2.3:a:nginx:nginx:1.25.3:*:*:*:*:*:*:*')",
    )

    # Source
    source: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="Source type (manual/composer/npm/docker)"
    )

    # Metadata: DB timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, comment="Record creation timestamp"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Record last update timestamp",
    )

    # Relationships
    matches: Mapped[list["AssetVulnerabilityMatch"]] = relationship(
        "AssetVulnerabilityMatch", back_populates="asset", cascade="all, delete-orphan"
    )

    # Unique constraint: Prevent duplicate assets with same vendor, product, version
    __table_args__ = (UniqueConstraint("vendor", "product", "version", name="uq_vendor_product_version"),)

    def __repr__(self) -> str:
        """String representation of Asset model."""
        return f"<Asset(asset_id={self.asset_id}, asset_name={self.asset_name}, cpe_code={self.cpe_code})>"

    @staticmethod
    def validate_cpe_code(cpe_code: str) -> bool:
        """
        Validate CPE 2.3 code format.

        Args:
            cpe_code: CPE code string

        Returns:
            True if valid, False otherwise

        Examples:
            >>> Asset.validate_cpe_code('cpe:2.3:a:nginx:nginx:1.25.3:*:*:*:*:*:*:*')
            True
            >>> Asset.validate_cpe_code('invalid')
            False
        """
        pattern = r"^cpe:2\.3:[aho]:[a-z0-9_\-]+:[a-z0-9_\-]+:[a-z0-9_\.\-]+:.*$"
        return bool(re.match(pattern, cpe_code))

    @staticmethod
    def validate_source(source: str) -> bool:
        """
        Validate source type.

        Args:
            source: Source type string

        Returns:
            True if valid, False otherwise

        Examples:
            >>> Asset.validate_source('manual')
            True
            >>> Asset.validate_source('invalid')
            False
        """
        valid_sources = {"manual", "composer", "npm", "docker"}
        return source in valid_sources


class AssetVulnerabilityMatch(Base):
    """
    Matching results between assets and vulnerabilities.

    This model stores the results of CPE matching:
    - Asset ID (foreign key to assets table)
    - CVE ID (foreign key to vulnerabilities table)
    - Match reason (exact_match/version_range/wildcard_match)
    - Matched timestamp
    """

    __tablename__ = "asset_vulnerability_matches"

    # Primary key: UUID
    match_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="Match unique identifier (UUID)",
    )

    # Foreign keys
    asset_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("assets.asset_id", ondelete="CASCADE"), nullable=False, index=True, comment="Asset ID"
    )
    cve_id: Mapped[str] = mapped_column(
        String(20),
        ForeignKey("vulnerabilities.cve_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="CVE ID",
    )

    # Match information
    match_reason: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="Match reason (exact_match/version_range/wildcard_match)"
    )
    matched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        comment="Match execution timestamp",
    )

    # Relationships
    asset: Mapped["Asset"] = relationship("Asset", back_populates="matches")
    # Note: Vulnerability relationship is not defined here to avoid circular import
    # It will be accessed via join queries when needed

    # Unique constraint: Prevent duplicate matches for same asset and vulnerability
    __table_args__ = (UniqueConstraint("asset_id", "cve_id", name="uq_asset_cve"),)

    def __repr__(self) -> str:
        """String representation of AssetVulnerabilityMatch model."""
        return (
            f"<AssetVulnerabilityMatch(match_id={self.match_id}, "
            f"asset_id={self.asset_id}, cve_id={self.cve_id}, match_reason={self.match_reason})>"
        )

    @staticmethod
    def validate_match_reason(match_reason: str) -> bool:
        """
        Validate match reason.

        Args:
            match_reason: Match reason string

        Returns:
            True if valid, False otherwise

        Examples:
            >>> AssetVulnerabilityMatch.validate_match_reason('exact_match')
            True
            >>> AssetVulnerabilityMatch.validate_match_reason('invalid')
            False
        """
        valid_reasons = {"exact_match", "version_range", "wildcard_match"}
        return match_reason in valid_reasons
