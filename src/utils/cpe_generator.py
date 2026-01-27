"""
CPE (Common Platform Enumeration) code generation utilities.

This module provides functions to generate CPE 2.3 format codes from various sources:
- Manual input (vendor, product, version)
- Composer (PHP dependencies)
- NPM (JavaScript dependencies)
- Docker (Dockerfile images and packages)
"""

import re
from typing import Dict, Optional


# NPM package vendor mapping (major packages only)
NPM_VENDOR_MAP: Dict[str, str] = {
    "react": "facebook",
    "react-dom": "facebook",
    "react-native": "facebook",
    "vue": "vuejs",
    "@vue/cli": "vuejs",
    "angular": "angular",
    "@angular/core": "angular",
    "express": "expressjs",
    "next": "vercel",
    "nuxt": "nuxtlabs",
    "gatsby": "gatsbyjs",
    "svelte": "svelte",
    "ember": "emberjs",
    "backbone": "backbonejs",
    "jquery": "jquery",
    "lodash": "lodash",
    "axios": "axios",
    "webpack": "webpack",
    "vite": "vitejs",
    "typescript": "microsoft",
    "eslint": "eslint",
    "prettier": "prettier",
    # Default: "npmjs" for unknown packages
}

# Docker image vendor mapping
DOCKER_VENDOR_MAP: Dict[str, str] = {
    "nginx": "nginx",
    "apache": "apache",
    "httpd": "apache",
    "postgres": "postgresql",
    "postgresql": "postgresql",
    "mysql": "mysql",
    "mariadb": "mariadb",
    "redis": "redis",
    "memcached": "memcached",
    "mongodb": "mongodb",
    "elasticsearch": "elastic",
    "node": "nodejs",
    "python": "python",
    "php": "php",
    "ruby": "ruby",
    "golang": "golang",
    "openjdk": "openjdk",
    "ubuntu": "canonical",
    "debian": "debian",
    "alpine": "alpinelinux",
    "centos": "centos",
    "fedora": "fedoraproject",
    # Default: "docker" for unknown images
}


def normalize_version(version: str) -> str:
    """
    Normalize version string for CPE code.

    Removes version constraint prefixes (^, ~, >=, <=, <, >) and suffixes (-alpine, -slim, etc.).

    Args:
        version: Version string (e.g., "^5.4", "1.25.3-alpine")

    Returns:
        Normalized version (e.g., "5.4", "1.25.3")

    Examples:
        >>> normalize_version("^5.4")
        '5.4'
        >>> normalize_version("~7.5.0")
        '7.5.0'
        >>> normalize_version("1.25.3-alpine")
        '1.25.3'
        >>> normalize_version(">=1.0.0")
        '1.0.0'
    """
    # Remove constraint prefixes (^, ~, >=, <=, <, >)
    version = re.sub(r"^[\^~>=<]+", "", version)

    # Remove suffixes (-alpine, -slim, -buster, etc.)
    version = re.split(r"[-_]", version)[0]

    return version.strip()


def normalize_name(name: str) -> str:
    """
    Normalize vendor/product name for CPE code.

    Converts to lowercase, replaces spaces with underscores.

    Args:
        name: Vendor or product name

    Returns:
        Normalized name

    Examples:
        >>> normalize_name("Nginx")
        'nginx'
        >>> normalize_name("My Product")
        'my_product'
    """
    return name.lower().replace(" ", "_").replace("/", "_")


def generate_cpe_from_manual(vendor: str, product: str, version: str) -> str:
    """
    Generate CPE code from manual input.

    Args:
        vendor: Vendor name (e.g., "Nginx")
        product: Product name (e.g., "Nginx")
        version: Version (e.g., "1.25.3")

    Returns:
        CPE 2.3 format code (e.g., "cpe:2.3:a:nginx:nginx:1.25.3:*:*:*:*:*:*:*")

    Examples:
        >>> generate_cpe_from_manual("Nginx", "Nginx", "1.25.3")
        'cpe:2.3:a:nginx:nginx:1.25.3:*:*:*:*:*:*:*'
        >>> generate_cpe_from_manual("Symfony", "Console", "5.4")
        'cpe:2.3:a:symfony:console:5.4:*:*:*:*:*:*:*'
    """
    vendor_normalized = normalize_name(vendor)
    product_normalized = normalize_name(product)
    version_normalized = normalize_version(version)

    return f"cpe:2.3:a:{vendor_normalized}:{product_normalized}:{version_normalized}:*:*:*:*:*:*:*"


def generate_cpe_from_composer(package_name: str, version: str) -> str:
    """
    Generate CPE code from Composer package (PHP).

    Args:
        package_name: Package name (e.g., "symfony/console")
        version: Version (e.g., "^5.4" → normalized to "5.4")

    Returns:
        CPE 2.3 format code (e.g., "cpe:2.3:a:symfony:console:5.4:*:*:*:*:*:*:*")

    Examples:
        >>> generate_cpe_from_composer("symfony/console", "^5.4")
        'cpe:2.3:a:symfony:console:5.4:*:*:*:*:*:*:*'
        >>> generate_cpe_from_composer("guzzlehttp/guzzle", "~7.5")
        'cpe:2.3:a:guzzlehttp:guzzle:7.5:*:*:*:*:*:*:*'
    """
    # Split package name into vendor/product
    if "/" in package_name:
        vendor, product = package_name.split("/", 1)
    else:
        # Fallback: use package name as both vendor and product
        vendor = package_name
        product = package_name

    vendor_normalized = normalize_name(vendor)
    product_normalized = normalize_name(product)
    version_normalized = normalize_version(version)

    return f"cpe:2.3:a:{vendor_normalized}:{product_normalized}:{version_normalized}:*:*:*:*:*:*:*"


def generate_cpe_from_npm(package_name: str, version: str) -> str:
    """
    Generate CPE code from NPM package (JavaScript).

    Args:
        package_name: Package name (e.g., "react")
        version: Version (e.g., "^18.2.0" → normalized to "18.2.0")

    Returns:
        CPE 2.3 format code (e.g., "cpe:2.3:a:facebook:react:18.2.0:*:*:*:*:*:*:*")

    Examples:
        >>> generate_cpe_from_npm("react", "^18.2.0")
        'cpe:2.3:a:facebook:react:18.2.0:*:*:*:*:*:*:*'
        >>> generate_cpe_from_npm("express", "^4.18.2")
        'cpe:2.3:a:expressjs:express:4.18.2:*:*:*:*:*:*:*'
        >>> generate_cpe_from_npm("unknown-package", "^1.0.0")
        'cpe:2.3:a:npmjs:unknown-package:1.0.0:*:*:*:*:*:*:*'
    """
    # Remove @scope/ prefix if present (e.g., "@vue/cli" → "vue/cli")
    package_clean = package_name.lstrip("@")

    # Get vendor from mapping or use "npmjs" as default
    vendor = NPM_VENDOR_MAP.get(package_name, "npmjs")

    # Product name is the package name (without @scope/)
    product = package_clean.split("/")[-1]

    vendor_normalized = normalize_name(vendor)
    product_normalized = normalize_name(product)
    version_normalized = normalize_version(version)

    return f"cpe:2.3:a:{vendor_normalized}:{product_normalized}:{version_normalized}:*:*:*:*:*:*:*"


def generate_cpe_from_docker(image_name: str, image_tag: str) -> str:
    """
    Generate CPE code from Docker image.

    Args:
        image_name: Image name (e.g., "nginx")
        image_tag: Image tag (e.g., "1.25.3-alpine" → normalized to "1.25.3")

    Returns:
        CPE 2.3 format code (e.g., "cpe:2.3:a:nginx:nginx:1.25.3:*:*:*:*:*:*:*")

    Examples:
        >>> generate_cpe_from_docker("nginx", "1.25.3-alpine")
        'cpe:2.3:a:nginx:nginx:1.25.3:*:*:*:*:*:*:*'
        >>> generate_cpe_from_docker("postgres", "15.2")
        'cpe:2.3:a:postgresql:postgres:15.2:*:*:*:*:*:*:*'
        >>> generate_cpe_from_docker("unknown-image", "1.0.0")
        'cpe:2.3:a:docker:unknown-image:1.0.0:*:*:*:*:*:*:*'
    """
    # Get vendor from mapping or use "docker" as default
    vendor = DOCKER_VENDOR_MAP.get(image_name, "docker")

    vendor_normalized = normalize_name(vendor)
    product_normalized = normalize_name(image_name)
    version_normalized = normalize_version(image_tag)

    return f"cpe:2.3:a:{vendor_normalized}:{product_normalized}:{version_normalized}:*:*:*:*:*:*:*"


def extract_cpe_parts(cpe_code: str) -> Optional[Dict[str, str]]:
    """
    Extract parts from CPE 2.3 code.

    Args:
        cpe_code: CPE 2.3 format code

    Returns:
        Dictionary with parts (part, vendor, product, version) or None if invalid

    Examples:
        >>> extract_cpe_parts("cpe:2.3:a:nginx:nginx:1.25.3:*:*:*:*:*:*:*")
        {'part': 'a', 'vendor': 'nginx', 'product': 'nginx', 'version': '1.25.3'}
    """
    parts = cpe_code.split(":")
    if len(parts) < 6 or parts[0] != "cpe" or parts[1] != "2.3":
        return None

    return {
        "part": parts[2],  # a (application), h (hardware), o (operating system)
        "vendor": parts[3],
        "product": parts[4],
        "version": parts[5],
    }
