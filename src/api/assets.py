"""
Asset management API endpoints.

This module provides REST API endpoints for:
- Manual asset registration (POST /api/assets)
- Asset list retrieval (GET /api/assets)
- Asset update (PUT /api/assets/{asset_id})
- Asset deletion (DELETE /api/assets/{asset_id})
- File import (POST /api/assets/import/{composer|npm|docker})
"""

import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.database import get_db
from src.models.asset import Asset
from src.schemas.asset import (
    AssetCreate,
    AssetListResponse,
    AssetResponse,
    AssetUpdate,
    FileImportResponse,
)
from src.utils.cpe_generator import (
    generate_cpe_from_composer,
    generate_cpe_from_docker,
    generate_cpe_from_manual,
    generate_cpe_from_npm,
)

router = APIRouter(tags=["assets"])
logger = logging.getLogger(__name__)
templates = Jinja2Templates(directory="src/templates")


@router.get("/assets", response_class=HTMLResponse, tags=["Frontend"])
async def get_assets_page(request: Request):
    """
    Render asset management page (HTML).

    This page provides:
    - Asset list display
    - Manual asset registration
    - File upload (Composer/NPM/Docker)
    - Asset edit/delete operations

    Args:
        request: FastAPI request object

    Returns:
        HTMLResponse: Rendered HTML page
    """
    logger.info("Rendering asset management page")
    return templates.TemplateResponse("assets.html", {"request": request})


@router.post("/api/assets", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
def create_asset(asset_data: AssetCreate, db: Session = Depends(get_db)):
    """
    Create a new asset (manual registration).

    Generates CPE code automatically from vendor, product, and version.

    Args:
        asset_data: Asset creation data
        db: Database session

    Returns:
        Created asset

    Raises:
        HTTPException: 400 if duplicate asset (same vendor, product, version)
    """
    logger.info(f"Creating asset: {asset_data.asset_name}")

    # Generate CPE code
    cpe_code = generate_cpe_from_manual(asset_data.vendor, asset_data.product, asset_data.version)

    # Create asset instance
    asset = Asset(
        asset_name=asset_data.asset_name,
        vendor=asset_data.vendor,
        product=asset_data.product,
        version=asset_data.version,
        cpe_code=cpe_code,
        source="manual",
    )

    try:
        db.add(asset)
        db.commit()
        db.refresh(asset)
        logger.info(f"Asset created successfully: {asset.asset_id}")
        return asset
    except IntegrityError as e:
        db.rollback()
        logger.warning(f"Duplicate asset detected: {asset_data.vendor}/{asset_data.product}/{asset_data.version}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Asset with vendor '{asset_data.vendor}', product '{asset_data.product}', "
            f"and version '{asset_data.version}' already exists",
        )


@router.get("/api/assets", response_model=AssetListResponse)
def list_assets(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    source: Optional[str] = Query(None, description="Filter by source (manual/composer/npm/docker)"),
    db: Session = Depends(get_db),
):
    """
    Retrieve asset list with pagination.

    Args:
        page: Page number (starting from 1)
        limit: Items per page (max 100)
        source: Optional filter by source type
        db: Database session

    Returns:
        Paginated asset list
    """
    logger.info(f"Fetching assets: page={page}, limit={limit}, source={source}")

    # Build query
    query = db.query(Asset)
    if source:
        if source not in ["manual", "composer", "npm", "docker"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid source: {source}. Must be one of: manual, composer, npm, docker"
            )
        query = query.filter(Asset.source == source)

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * limit
    assets = query.order_by(Asset.created_at.desc()).offset(offset).limit(limit).all()

    logger.info(f"Fetched {len(assets)} assets (total: {total})")

    return AssetListResponse(items=assets, total=total, page=page, limit=limit)


@router.get("/api/assets/{asset_id}", response_model=AssetResponse)
def get_asset(asset_id: str, db: Session = Depends(get_db)):
    """
    Retrieve a single asset by ID.

    Args:
        asset_id: Asset UUID
        db: Database session

    Returns:
        Asset details

    Raises:
        HTTPException: 404 if asset not found
    """
    logger.info(f"Fetching asset: {asset_id}")

    asset = db.query(Asset).filter(Asset.asset_id == asset_id).first()
    if not asset:
        logger.warning(f"Asset not found: {asset_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Asset not found: {asset_id}")

    return asset


@router.put("/api/assets/{asset_id}", response_model=AssetResponse)
def update_asset(asset_id: str, asset_data: AssetUpdate, db: Session = Depends(get_db)):
    """
    Update an existing asset.

    Only asset_name and version can be updated. If version is updated, CPE code is regenerated.

    Args:
        asset_id: Asset UUID
        asset_data: Asset update data
        db: Database session

    Returns:
        Updated asset

    Raises:
        HTTPException: 404 if asset not found, 400 if update would create duplicate
    """
    logger.info(f"Updating asset: {asset_id}")

    asset = db.query(Asset).filter(Asset.asset_id == asset_id).first()
    if not asset:
        logger.warning(f"Asset not found: {asset_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Asset not found: {asset_id}")

    # Update fields
    if asset_data.asset_name is not None:
        asset.asset_name = asset_data.asset_name

    if asset_data.version is not None:
        asset.version = asset_data.version
        # Regenerate CPE code with new version
        asset.cpe_code = generate_cpe_from_manual(asset.vendor, asset.product, asset.version)

    try:
        db.commit()
        db.refresh(asset)
        logger.info(f"Asset updated successfully: {asset_id}")
        return asset
    except IntegrityError as e:
        db.rollback()
        logger.warning(f"Update would create duplicate asset: {asset.vendor}/{asset.product}/{asset.version}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Update would create duplicate asset with vendor '{asset.vendor}', "
            f"product '{asset.product}', and version '{asset.version}'",
        )


@router.delete("/api/assets/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_asset(asset_id: str, db: Session = Depends(get_db)):
    """
    Delete an asset.

    Also deletes all related matching results (CASCADE).

    Args:
        asset_id: Asset UUID
        db: Database session

    Raises:
        HTTPException: 404 if asset not found
    """
    logger.info(f"Deleting asset: {asset_id}")

    asset = db.query(Asset).filter(Asset.asset_id == asset_id).first()
    if not asset:
        logger.warning(f"Asset not found: {asset_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Asset not found: {asset_id}")

    db.delete(asset)
    db.commit()
    logger.info(f"Asset deleted successfully: {asset_id}")


@router.post("/api/assets/import/composer", response_model=FileImportResponse, status_code=status.HTTP_201_CREATED)
async def import_composer(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Import assets from Composer file (composer.json or composer.lock).

    Args:
        file: Uploaded Composer file
        db: Database session

    Returns:
        Import statistics

    Raises:
        HTTPException: 400 if file format is invalid
    """
    logger.info(f"Importing Composer file: {file.filename}")

    # Validate file name
    if not file.filename or not (file.filename.endswith("composer.json") or file.filename.endswith("composer.lock")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file name. Must be composer.json or composer.lock",
        )

    # Read and parse JSON
    try:
        content = await file.read()
        data = json.loads(content)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid JSON format: {e}")

    # Extract dependencies
    dependencies = {}
    if "require" in data:
        dependencies.update(data["require"])
    if "require-dev" in data:
        dependencies.update(data["require-dev"])

    # For composer.lock, extract from packages
    if "packages" in data:
        for package in data["packages"]:
            package_name = package.get("name")
            package_version = package.get("version", "").lstrip("v")
            if package_name and package_version:
                dependencies[package_name] = package_version

    logger.info(f"Found {len(dependencies)} dependencies in Composer file")

    # Import assets
    imported_count = 0
    skipped_count = 0
    errors = []

    for package_name, version_spec in dependencies.items():
        try:
            # Skip PHP version constraint
            if package_name == "php":
                continue

            # Generate CPE code
            cpe_code = generate_cpe_from_composer(package_name, version_spec)

            # Extract vendor/product from package name
            if "/" in package_name:
                vendor, product = package_name.split("/", 1)
            else:
                vendor = product = package_name

            # Normalize version
            from src.utils.cpe_generator import normalize_version

            version = normalize_version(version_spec)

            # Create asset
            asset = Asset(
                asset_name=package_name, vendor=vendor, product=product, version=version, cpe_code=cpe_code, source="composer"
            )

            try:
                db.add(asset)
                db.commit()
                imported_count += 1
            except IntegrityError:
                db.rollback()
                skipped_count += 1
                logger.debug(f"Skipped duplicate: {package_name} {version}")

        except Exception as e:
            logger.error(f"Failed to import {package_name}: {e}")
            errors.append(f"{package_name}: {str(e)}")

    logger.info(f"Composer import completed: imported={imported_count}, skipped={skipped_count}, errors={len(errors)}")

    return FileImportResponse(imported_count=imported_count, skipped_count=skipped_count, errors=errors)


@router.post("/api/assets/import/npm", response_model=FileImportResponse, status_code=status.HTTP_201_CREATED)
async def import_npm(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Import assets from NPM file (package.json or package-lock.json).

    Args:
        file: Uploaded NPM file
        db: Database session

    Returns:
        Import statistics

    Raises:
        HTTPException: 400 if file format is invalid
    """
    logger.info(f"Importing NPM file: {file.filename}")

    # Validate file name
    if not file.filename or not (file.filename.endswith("package.json") or file.filename.endswith("package-lock.json")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file name. Must be package.json or package-lock.json",
        )

    # Read and parse JSON
    try:
        content = await file.read()
        data = json.loads(content)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid JSON format: {e}")

    # Extract dependencies
    dependencies = {}
    if "dependencies" in data:
        dependencies.update(data["dependencies"])
    if "devDependencies" in data:
        dependencies.update(data["devDependencies"])

    # For package-lock.json, extract from packages
    if "packages" in data:
        for package_path, package_info in data["packages"].items():
            if package_path == "":  # Root package
                continue
            package_name = package_path.lstrip("node_modules/")
            package_version = package_info.get("version", "")
            if package_name and package_version:
                dependencies[package_name] = package_version

    logger.info(f"Found {len(dependencies)} dependencies in NPM file")

    # Import assets
    imported_count = 0
    skipped_count = 0
    errors = []

    for package_name, version_spec in dependencies.items():
        try:
            # Generate CPE code
            cpe_code = generate_cpe_from_npm(package_name, version_spec)

            # Extract vendor/product
            from src.utils.cpe_generator import NPM_VENDOR_MAP, normalize_version

            vendor = NPM_VENDOR_MAP.get(package_name, "npmjs")
            product = package_name.lstrip("@").split("/")[-1]
            version = normalize_version(version_spec)

            # Create asset
            asset = Asset(
                asset_name=package_name, vendor=vendor, product=product, version=version, cpe_code=cpe_code, source="npm"
            )

            try:
                db.add(asset)
                db.commit()
                imported_count += 1
            except IntegrityError:
                db.rollback()
                skipped_count += 1
                logger.debug(f"Skipped duplicate: {package_name} {version}")

        except Exception as e:
            logger.error(f"Failed to import {package_name}: {e}")
            errors.append(f"{package_name}: {str(e)}")

    logger.info(f"NPM import completed: imported={imported_count}, skipped={skipped_count}, errors={len(errors)}")

    return FileImportResponse(imported_count=imported_count, skipped_count=skipped_count, errors=errors)


@router.post("/api/assets/import/docker", response_model=FileImportResponse, status_code=status.HTTP_201_CREATED)
async def import_docker(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Import assets from Dockerfile.

    Extracts base images from FROM instructions.

    Args:
        file: Uploaded Dockerfile
        db: Database session

    Returns:
        Import statistics

    Raises:
        HTTPException: 400 if file format is invalid
    """
    logger.info(f"Importing Dockerfile: {file.filename}")

    # Validate file name
    if not file.filename or not (file.filename == "Dockerfile" or file.filename.startswith("Dockerfile.")):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file name. Must be Dockerfile or Dockerfile.*")

    # Read content
    try:
        content = await file.read()
        dockerfile_content = content.decode("utf-8")
    except Exception as e:
        logger.error(f"Failed to read Dockerfile: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to read file: {e}")

    # Extract FROM instructions
    import re

    from_pattern = re.compile(r"^FROM\s+([^:\s]+)(?::([^\s]+))?", re.MULTILINE | re.IGNORECASE)
    matches = from_pattern.findall(dockerfile_content)

    logger.info(f"Found {len(matches)} FROM instructions in Dockerfile")

    # Import assets
    imported_count = 0
    skipped_count = 0
    errors = []

    for image_name, image_tag in matches:
        try:
            # Skip scratch image
            if image_name.lower() == "scratch":
                continue

            # Default tag is "latest"
            if not image_tag:
                image_tag = "latest"

            # Generate CPE code
            cpe_code = generate_cpe_from_docker(image_name, image_tag)

            # Extract vendor/product
            from src.utils.cpe_generator import DOCKER_VENDOR_MAP, normalize_version

            vendor = DOCKER_VENDOR_MAP.get(image_name, "docker")
            product = image_name
            version = normalize_version(image_tag)

            # Create asset
            asset = Asset(
                asset_name=f"Docker: {image_name}:{image_tag}",
                vendor=vendor,
                product=product,
                version=version,
                cpe_code=cpe_code,
                source="docker",
            )

            try:
                db.add(asset)
                db.commit()
                imported_count += 1
            except IntegrityError:
                db.rollback()
                skipped_count += 1
                logger.debug(f"Skipped duplicate: {image_name}:{image_tag}")

        except Exception as e:
            logger.error(f"Failed to import {image_name}:{image_tag}: {e}")
            errors.append(f"{image_name}:{image_tag}: {str(e)}")

    logger.info(f"Docker import completed: imported={imported_count}, skipped={skipped_count}, errors={len(errors)}")

    return FileImportResponse(imported_count=imported_count, skipped_count=skipped_count, errors=errors)
