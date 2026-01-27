"""
FastAPI application entry point.

This module initializes the FastAPI application with:
- API routers
- Static files and templates
- CORS configuration
- Health check endpoint
"""

import logging
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.api.assets import router as assets_router
from src.api.matching import router as matching_router
from src.api.vulnerabilities import router as vulnerabilities_router
from src.config import settings

logger = logging.getLogger(__name__)

# Initialize FastAPI application
app = FastAPI(
    title="脆弱性管理システム",
    description="JVN iPedia API を利用した脆弱性情報管理システム（Phase 2: CPEマッチング機能）",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="src/static"), name="static")

# Include routers
app.include_router(vulnerabilities_router, tags=["Vulnerabilities"])
app.include_router(assets_router, tags=["Assets"])
app.include_router(matching_router, tags=["Matching"])


@app.get("/api/health", tags=["System"])
async def health_check():
    """
    Health check endpoint.

    Returns application status and basic information.
    Response time must be within 5 seconds.

    Checks:
    - Database connection (SELECT 1 query)
    - Response time within 5 seconds

    Returns:
        dict: Health status information
            - status: 'healthy' or 'unhealthy'
            - database: 'connected' or 'disconnected'
            - timestamp: ISO 8601 format
            - version: Application version
            - environment: Debug mode and port

    Raises:
        HTTPException: 503 Service Unavailable if database connection fails
    """
    from fastapi import HTTPException

    from src.database import check_db_connection

    logger.info("Health check requested")

    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "environment": {
            "debug": settings.DEBUG,
            "port": settings.PORT,
        },
    }

    # Database connection check (M5.1)
    try:
        db_connected = check_db_connection()

        if db_connected:
            health_status["database"] = "connected"
            logger.info("Health check completed: database connected")
        else:
            health_status["status"] = "unhealthy"
            health_status["database"] = "disconnected"
            logger.error("Health check failed: database disconnected")
            raise HTTPException(
                status_code=503,
                detail="Database connection failed",
            )

    except HTTPException:
        # Re-raise HTTPException for FastAPI to handle
        raise
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", exc_info=True)
        health_status["status"] = "unhealthy"
        health_status["database"] = "error"
        raise HTTPException(
            status_code=503,
            detail=f"Health check failed: {str(e)}",
        )

    return health_status


@app.on_event("startup")
async def startup_event():
    """
    Application startup event handler.

    Logs application startup information.
    """
    logger.info("=" * 80)
    logger.info("Starting vulnerability management system")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"Port: {settings.PORT}")
    logger.info(f"Log level: {settings.LOG_LEVEL}")
    logger.info("=" * 80)


@app.on_event("shutdown")
async def shutdown_event():
    """
    Application shutdown event handler.

    Logs application shutdown information.
    """
    logger.info("Shutting down vulnerability management system")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
