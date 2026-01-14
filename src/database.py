"""
Database configuration and session management.

This module provides SQLAlchemy engine, session factory, and dependency injection
for FastAPI endpoints.
"""

import logging
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from src.config import settings

logger = logging.getLogger(__name__)

# SQLAlchemy engine
# Connection pooling is configured for production use
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # Log SQL queries in debug mode
    pool_pre_ping=True,  # Verify connections before using them
    pool_size=5,  # Maximum number of connections in the pool
    max_overflow=10,  # Maximum overflow connections
)

# Session factory
# Use Session() to create new database sessions
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency injection for FastAPI endpoints.

    Yields a database session and ensures proper cleanup.

    Usage:
        @app.get('/vulnerabilities')
        def get_vulnerabilities(db: Session = Depends(get_db)):
            ...

    Yields:
        Session: SQLAlchemy database session

    Example:
        >>> from fastapi import Depends
        >>> from src.database import get_db
        >>> def my_endpoint(db: Session = Depends(get_db)):
        ...     vulnerabilities = db.query(Vulnerability).all()
        ...     return vulnerabilities
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize database tables.

    Creates all tables defined in SQLAlchemy models.
    This function should be called once during application startup.

    Note:
        In production, use Alembic migrations instead of this function.
        This is provided for development and testing purposes.

    Example:
        >>> from src.database import init_db
        >>> init_db()  # Creates all tables
    """
    from src.models.vulnerability import Base

    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully")


def check_db_connection() -> bool:
    """
    Check database connection health.

    Used by health check endpoint (/api/health).
    Executes a simple SELECT 1 query to verify connection.
    Timeout is enforced at the connection level (pool_pre_ping).

    Returns:
        bool: True if connection is healthy, False otherwise

    Example:
        >>> from src.database import check_db_connection
        >>> if check_db_connection():
        ...     print('Database is healthy')
        ... else:
        ...     print('Database connection failed')
    """
    import time

    try:
        start_time = time.time()
        db = SessionLocal()

        # Execute simple query to verify connection (SQLAlchemy 2.0 style)
        result = db.execute(text("SELECT 1"))
        result.scalar()

        elapsed = time.time() - start_time
        logger.debug(f"Database health check completed in {elapsed:.3f}s")

        db.close()
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


def close_db() -> None:
    """
    Close database connections.

    Should be called during application shutdown.

    Example:
        >>> from src.database import close_db
        >>> close_db()  # Clean up all connections
    """
    logger.info("Closing database connections...")
    engine.dispose()
    logger.info("Database connections closed")
