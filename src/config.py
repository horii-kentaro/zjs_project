"""
Application configuration management.

This module handles environment variables and application settings.
All configuration is loaded from environment variables with sensible defaults.
"""

import logging
import os
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Environment variables are loaded from .env file in the project root.
    All sensitive information (DATABASE_URL, API keys) must be stored in .env.

    Attributes:
        DATABASE_URL: PostgreSQL connection string
        JVN_API_ENDPOINT: JVN iPedia API endpoint URL
        LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        DEBUG: Debug mode flag (enables SQL query logging)
        PORT: Application port number
    """

    # Database configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5434/vulnerability_db")

    # JVN iPedia API configuration
    JVN_API_ENDPOINT: str = os.getenv("JVN_API_ENDPOINT", "https://jvndb.jvn.jp/myjvn")
    JVN_API_TIMEOUT: int = 30  # Timeout in seconds
    JVN_API_MAX_RETRIES: int = 3  # Maximum retry attempts
    JVN_API_RETRY_DELAY: int = 5  # Delay between retries in seconds

    # NVD API configuration (Phase 2 - optional)
    NVD_API_ENDPOINT: Optional[str] = os.getenv("NVD_API_ENDPOINT", "https://services.nvd.nist.gov/rest/json/cves/2.0")
    NVD_API_KEY: Optional[str] = os.getenv("NVD_API_KEY", None)

    # CISA KEV configuration (Phase 2 - optional)
    CISA_KEV_ENDPOINT: Optional[str] = os.getenv(
        "CISA_KEV_ENDPOINT", "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
    )

    # Logging configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Application configuration
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")
    PORT: int = int(os.getenv("PORT", "8347"))

    # Data fetch configuration
    FETCH_YEARS: int = 3  # Fetch vulnerabilities from the last N years
    FETCH_ALL_DATA: bool = os.getenv("FETCH_ALL_DATA", "False").lower() in (
        "true",
        "1",
        "yes",
    )  # If True, fetch all historical data

    # Pagination defaults
    DEFAULT_PAGE_SIZE: int = 50
    MAX_PAGE_SIZE: int = 100

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }

    def configure_logging(self) -> None:
        """
        Configure application logging based on LOG_LEVEL setting.

        Sets up logging format and level for the entire application.

        Example:
            >>> settings = Settings()
            >>> settings.configure_logging()
        """
        logging.basicConfig(
            level=getattr(logging, self.LOG_LEVEL.upper()),
            format=self.LOG_FORMAT,
        )
        logger = logging.getLogger(__name__)
        logger.info(f"Logging configured with level: {self.LOG_LEVEL}")

    def get_fetch_start_date(self) -> Optional[str]:
        """
        Get the start date for vulnerability data fetch.

        Returns:
            Optional[str]: Start date in ISO 8601 format (YYYY-MM-DD), or None for all data

        Example:
            >>> settings = Settings()
            >>> settings.get_fetch_start_date()
            '2023-01-07'  # 3 years ago from today
        """
        if self.FETCH_ALL_DATA:
            return None

        from datetime import datetime, timedelta

        start_date = datetime.now() - timedelta(days=365 * self.FETCH_YEARS)
        return start_date.strftime("%Y-%m-%d")

    def mask_sensitive_info(self) -> dict:
        """
        Get settings as dictionary with sensitive information masked.

        Used for logging and debugging purposes.

        Returns:
            dict: Settings dictionary with masked sensitive values

        Example:
            >>> settings = Settings()
            >>> settings.mask_sensitive_info()
            {'DATABASE_URL': 'postgresql://***', 'JVN_API_ENDPOINT': 'https://...', ...}
        """
        settings_dict = self.model_dump()

        # Mask sensitive fields
        if "DATABASE_URL" in settings_dict and settings_dict["DATABASE_URL"]:
            settings_dict["DATABASE_URL"] = settings_dict["DATABASE_URL"].split("@")[0].split("//")[0] + "//***"

        if "NVD_API_KEY" in settings_dict and settings_dict["NVD_API_KEY"]:
            settings_dict["NVD_API_KEY"] = (
                "***" + settings_dict["NVD_API_KEY"][-4:] if settings_dict["NVD_API_KEY"] else None
            )

        return settings_dict


# Global settings instance
settings = Settings()

# Configure logging on import
settings.configure_logging()
