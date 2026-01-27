"""
Unit tests for CPE generator utilities.

Tests CPE code generation from various sources:
- Manual input
- Composer (PHP dependencies)
- NPM (JavaScript dependencies)
- Docker (Dockerfile images)
"""

import pytest

from src.utils.cpe_generator import (
    DOCKER_VENDOR_MAP,
    NPM_VENDOR_MAP,
    extract_cpe_parts,
    generate_cpe_from_composer,
    generate_cpe_from_docker,
    generate_cpe_from_manual,
    generate_cpe_from_npm,
    normalize_name,
    normalize_version,
)


class TestNormalizeVersion:
    """Test version normalization function."""

    def test_remove_caret_prefix(self):
        """Test removing ^ prefix."""
        assert normalize_version("^5.4") == "5.4"
        assert normalize_version("^18.2.0") == "18.2.0"

    def test_remove_tilde_prefix(self):
        """Test removing ~ prefix."""
        assert normalize_version("~7.5.0") == "7.5.0"
        assert normalize_version("~1.25.3") == "1.25.3"

    def test_remove_comparison_operators(self):
        """Test removing >=, <=, <, > prefixes."""
        assert normalize_version(">=1.0.0") == "1.0.0"
        assert normalize_version("<=2.0.0") == "2.0.0"
        assert normalize_version(">3.0.0") == "3.0.0"
        assert normalize_version("<4.0.0") == "4.0.0"

    def test_remove_suffix(self):
        """Test removing suffixes like -alpine, -slim."""
        assert normalize_version("1.25.3-alpine") == "1.25.3"
        assert normalize_version("15.2-slim") == "15.2"
        assert normalize_version("3.11-buster") == "3.11"

    def test_plain_version(self):
        """Test plain version without prefix/suffix."""
        assert normalize_version("5.4.0") == "5.4.0"
        assert normalize_version("1.25.3") == "1.25.3"


class TestNormalizeName:
    """Test name normalization function."""

    def test_lowercase_conversion(self):
        """Test converting to lowercase."""
        assert normalize_name("Nginx") == "nginx"
        assert normalize_name("SYMFONY") == "symfony"

    def test_space_replacement(self):
        """Test replacing spaces with underscores."""
        assert normalize_name("My Product") == "my_product"
        assert normalize_name("Some Package Name") == "some_package_name"

    def test_slash_replacement(self):
        """Test replacing slashes with underscores."""
        assert normalize_name("vendor/product") == "vendor_product"


class TestGenerateCpeFromManual:
    """Test manual CPE generation."""

    def test_basic_generation(self):
        """Test basic CPE generation from manual input."""
        cpe = generate_cpe_from_manual("Nginx", "Nginx", "1.25.3")
        assert cpe == "cpe:2.3:a:nginx:nginx:1.25.3:*:*:*:*:*:*:*"

    def test_symfony_console(self):
        """Test Symfony Console package."""
        cpe = generate_cpe_from_manual("Symfony", "Console", "5.4")
        assert cpe == "cpe:2.3:a:symfony:console:5.4:*:*:*:*:*:*:*"

    def test_name_normalization(self):
        """Test name normalization in CPE generation."""
        cpe = generate_cpe_from_manual("My Vendor", "My Product", "1.0.0")
        assert cpe == "cpe:2.3:a:my_vendor:my_product:1.0.0:*:*:*:*:*:*:*"

    def test_version_normalization(self):
        """Test version normalization in CPE generation."""
        cpe = generate_cpe_from_manual("vendor", "product", "^5.4")
        assert cpe == "cpe:2.3:a:vendor:product:5.4:*:*:*:*:*:*:*"


class TestGenerateCpeFromComposer:
    """Test Composer CPE generation."""

    def test_symfony_console(self):
        """Test Symfony Console package."""
        cpe = generate_cpe_from_composer("symfony/console", "^5.4")
        assert cpe == "cpe:2.3:a:symfony:console:5.4:*:*:*:*:*:*:*"

    def test_guzzle(self):
        """Test Guzzle HTTP client."""
        cpe = generate_cpe_from_composer("guzzlehttp/guzzle", "~7.5")
        assert cpe == "cpe:2.3:a:guzzlehttp:guzzle:7.5:*:*:*:*:*:*:*"

    def test_laravel_framework(self):
        """Test Laravel framework."""
        cpe = generate_cpe_from_composer("laravel/framework", "^10.0")
        assert cpe == "cpe:2.3:a:laravel:framework:10.0:*:*:*:*:*:*:*"

    def test_package_without_vendor(self):
        """Test package without vendor (fallback)."""
        cpe = generate_cpe_from_composer("somepackage", "1.0.0")
        assert cpe == "cpe:2.3:a:somepackage:somepackage:1.0.0:*:*:*:*:*:*:*"


class TestGenerateCpeFromNpm:
    """Test NPM CPE generation."""

    def test_react(self):
        """Test React package (mapped to facebook)."""
        cpe = generate_cpe_from_npm("react", "^18.2.0")
        assert cpe == "cpe:2.3:a:facebook:react:18.2.0:*:*:*:*:*:*:*"

    def test_express(self):
        """Test Express package (mapped to expressjs)."""
        cpe = generate_cpe_from_npm("express", "^4.18.2")
        assert cpe == "cpe:2.3:a:expressjs:express:4.18.2:*:*:*:*:*:*:*"

    def test_vue(self):
        """Test Vue package (mapped to vuejs)."""
        cpe = generate_cpe_from_npm("vue", "^3.3.0")
        assert cpe == "cpe:2.3:a:vuejs:vue:3.3.0:*:*:*:*:*:*:*"

    def test_scoped_package(self):
        """Test scoped package (@scope/package)."""
        cpe = generate_cpe_from_npm("@angular/core", "^16.0.0")
        assert cpe == "cpe:2.3:a:angular:core:16.0.0:*:*:*:*:*:*:*"

    def test_unknown_package(self):
        """Test unknown package (default to npmjs)."""
        cpe = generate_cpe_from_npm("unknown-package", "^1.0.0")
        assert cpe == "cpe:2.3:a:npmjs:unknown-package:1.0.0:*:*:*:*:*:*:*"


class TestGenerateCpeFromDocker:
    """Test Docker CPE generation."""

    def test_nginx(self):
        """Test Nginx image (mapped to nginx)."""
        cpe = generate_cpe_from_docker("nginx", "1.25.3-alpine")
        assert cpe == "cpe:2.3:a:nginx:nginx:1.25.3:*:*:*:*:*:*:*"

    def test_postgres(self):
        """Test PostgreSQL image (mapped to postgresql)."""
        cpe = generate_cpe_from_docker("postgres", "15.2")
        assert cpe == "cpe:2.3:a:postgresql:postgres:15.2:*:*:*:*:*:*:*"

    def test_redis(self):
        """Test Redis image (mapped to redis)."""
        cpe = generate_cpe_from_docker("redis", "7.0-alpine")
        assert cpe == "cpe:2.3:a:redis:redis:7.0:*:*:*:*:*:*:*"

    def test_node(self):
        """Test Node.js image (mapped to nodejs)."""
        cpe = generate_cpe_from_docker("node", "18.16.0")
        assert cpe == "cpe:2.3:a:nodejs:node:18.16.0:*:*:*:*:*:*:*"

    def test_unknown_image(self):
        """Test unknown image (default to docker)."""
        cpe = generate_cpe_from_docker("unknown-image", "1.0.0")
        assert cpe == "cpe:2.3:a:docker:unknown-image:1.0.0:*:*:*:*:*:*:*"


class TestExtractCpeParts:
    """Test CPE parts extraction."""

    def test_valid_cpe(self):
        """Test extracting parts from valid CPE code."""
        parts = extract_cpe_parts("cpe:2.3:a:nginx:nginx:1.25.3:*:*:*:*:*:*:*")
        assert parts == {
            "part": "a",
            "vendor": "nginx",
            "product": "nginx",
            "version": "1.25.3",
        }

    def test_invalid_cpe_prefix(self):
        """Test invalid CPE prefix."""
        parts = extract_cpe_parts("invalid:2.3:a:vendor:product:1.0.0:*:*:*:*:*:*:*")
        assert parts is None

    def test_invalid_cpe_version(self):
        """Test invalid CPE version (not 2.3)."""
        parts = extract_cpe_parts("cpe:2.2:a:vendor:product:1.0.0:*:*:*:*:*:*:*")
        assert parts is None

    def test_short_cpe(self):
        """Test CPE code with insufficient parts."""
        parts = extract_cpe_parts("cpe:2.3:a:vendor")
        assert parts is None


class TestVendorMappings:
    """Test vendor mapping dictionaries."""

    def test_npm_vendor_map_coverage(self):
        """Test NPM vendor map contains major packages."""
        assert "react" in NPM_VENDOR_MAP
        assert NPM_VENDOR_MAP["react"] == "facebook"
        assert "express" in NPM_VENDOR_MAP
        assert NPM_VENDOR_MAP["express"] == "expressjs"
        assert "vue" in NPM_VENDOR_MAP
        assert NPM_VENDOR_MAP["vue"] == "vuejs"

    def test_docker_vendor_map_coverage(self):
        """Test Docker vendor map contains major images."""
        assert "nginx" in DOCKER_VENDOR_MAP
        assert DOCKER_VENDOR_MAP["nginx"] == "nginx"
        assert "postgres" in DOCKER_VENDOR_MAP
        assert DOCKER_VENDOR_MAP["postgres"] == "postgresql"
        assert "redis" in DOCKER_VENDOR_MAP
        assert DOCKER_VENDOR_MAP["redis"] == "redis"


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_version(self):
        """Test empty version string."""
        cpe = generate_cpe_from_manual("vendor", "product", "")
        assert cpe == "cpe:2.3:a:vendor:product::*:*:*:*:*:*:*"

    def test_complex_version(self):
        """Test complex version with multiple separators."""
        assert normalize_version("1.25.3-alpine-slim") == "1.25.3"

    def test_multiple_prefixes(self):
        """Test version with multiple constraint prefixes."""
        assert normalize_version(">=^1.0.0") == "1.0.0"

    def test_special_characters_in_name(self):
        """Test handling special characters in names."""
        cpe = generate_cpe_from_manual("Vendor/Sub", "Product Name", "1.0")
        assert cpe == "cpe:2.3:a:vendor_sub:product_name:1.0:*:*:*:*:*:*:*"
