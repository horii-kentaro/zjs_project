"""
Fetchers package for external API integrations.

This package contains modules for fetching vulnerability data from various sources:
- JVN iPedia API
- NVD API (Phase 2)
- CISA KEV (Phase 2)
"""

from src.fetchers.jvn_fetcher import JVNFetcherService

__all__ = ['JVNFetcherService']
