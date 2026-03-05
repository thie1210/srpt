"""
Utility functions for working with installed packages.
"""

import re
from pathlib import Path
from typing import Optional, List, Dict
from packaging.version import parse as parse_version


def normalize_name(name: str) -> str:
    """Normalize package name according to PEP 503."""
    return re.sub(r"[-_.]+", "-", name).lower()


def find_dist_info(package_name: str, site_packages: Path) -> Optional[Path]:
    """
    Find the .dist-info directory for a package.

    Returns None if not found.
    """
    normalized = normalize_name(package_name)

    for dist_info in site_packages.glob("*.dist-info"):
        dist_name = dist_info.name.replace(".dist-info", "")
        parts = dist_name.rsplit("-", 1)
        if len(parts) == 2:
            dist_package = normalize_name(parts[0])
            if dist_package == normalized:
                return dist_info

    return None


def get_installed_version(package_name: str, site_packages: Path) -> Optional[str]:
    """
    Get the installed version of a package.

    Returns None if not installed.
    """
    dist_info = find_dist_info(package_name, site_packages)

    if not dist_info:
        return None

    # Extract version from dist-info name
    # e.g., requests-2.32.5.dist-info -> 2.32.5
    name = dist_info.name
    # Remove .dist-info extension first
    if name.endswith(".dist-info"):
        name = name[:-10]  # Remove ".dist-info"

    # Now split: requests-2.32.5 -> ["requests", "2.32.5"]
    parts = name.rsplit("-", 1)
    if len(parts) == 2:
        return parts[1]

    return None


def is_installed(package_name: str, version: str, site_packages: Path) -> bool:
    """
    Check if a specific version of a package is installed.
    """
    installed_version = get_installed_version(package_name, site_packages)

    if not installed_version:
        return False

    # Compare versions
    try:
        return parse_version(installed_version) == parse_version(version)
    except Exception:
        # Fallback to string comparison
        return installed_version == version


def list_installed_packages(site_packages: Path) -> List[Dict[str, str]]:
    """
    List all installed packages in a site-packages directory.

    Returns list of dicts with 'name' and 'version' keys.
    """
    packages = []

    # Find all .dist-info directories
    for dist_info in site_packages.glob("*.dist-info"):
        try:
            # Extract name and version from directory name
            # e.g., requests-2.32.5.dist-info
            name_version = dist_info.name.replace(".dist-info", "")
            parts = name_version.rsplit("-", 1)
            if len(parts) == 2:
                name = parts[0].replace("_", "-")
                version = parts[1]
                packages.append(
                    {
                        "name": name,
                        "version": version,
                        "dist_info": str(dist_info),
                    }
                )
        except Exception:
            continue

    # Sort by name
    packages.sort(key=lambda p: p["name"].lower())

    return packages


def parse_record_file(record_path: Path) -> List[Path]:
    """
    Parse a RECORD file to get list of installed files.

    Returns list of paths relative to site-packages.
    """
    if not record_path.exists():
        return []

    files = []

    try:
        with open(record_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                # RECORD format: path,hash,size
                # We only need the path
                parts = line.split(",", 1)
                if parts:
                    file_path = record_path.parent.parent / parts[0]
                    if file_path.exists():
                        files.append(file_path)
    except Exception:
        pass

    return files
