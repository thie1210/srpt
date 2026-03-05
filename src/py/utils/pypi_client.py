"""
PyPI API client for fetching package information.

Uses PyPI JSON API for fast, reliable package metadata retrieval.
"""

import asyncio
from typing import List, Dict, Optional
from pathlib import Path

import httpx


PYPI_JSON_API = "https://pypi.org/pypi/{package}/json"
PYPI_SIMPLE_API = "https://pypi.org/pypi/{package}/json"


async def get_package_versions(package_name: str) -> List[str]:
    """
    Get all available versions for a package from PyPI.

    Args:
        package_name: Name of the package

    Returns:
        List of version strings, sorted oldest to newest

    Raises:
        httpx.HTTPError: If request fails
        ValueError: If package not found
    """
    url = PYPI_JSON_API.format(package=package_name)

    async with httpx.AsyncClient(http2=True, timeout=30.0) as client:
        response = await client.get(url)

        if response.status_code == 404:
            raise ValueError(f"Package not found: {package_name}")

        response.raise_for_status()

        data = response.json()
        versions = list(data["releases"].keys())

        # Sort versions using packaging.version
        from packaging.version import Version

        versions.sort(key=Version)

        return versions


async def get_latest_version(package_name: str) -> str:
    """
    Get the latest stable version for a package.

    Args:
        package_name: Name of the package

    Returns:
        Latest stable version string

    Raises:
        httpx.HTTPError: If request fails
        ValueError: If package not found
    """
    url = PYPI_JSON_API.format(package=package_name)

    async with httpx.AsyncClient(http2=True, timeout=30.0) as client:
        response = await client.get(url)

        if response.status_code == 404:
            raise ValueError(f"Package not found: {package_name}")

        response.raise_for_status()

        data = response.json()

        # Get latest version from info
        latest = data["info"]["version"]

        return latest


async def get_package_info(package_name: str, version: Optional[str] = None) -> Dict:
    """
    Get detailed information about a package.

    Args:
        package_name: Name of the package
        version: Specific version (optional, defaults to latest)

    Returns:
        Dict with package information including:
        - name
        - version
        - summary
        - author
        - license
        - requires_python
        - dependencies

    Raises:
        httpx.HTTPError: If request fails
        ValueError: If package or version not found
    """
    if version:
        url = f"https://pypi.org/pypi/{package_name}/{version}/json"
    else:
        url = PYPI_JSON_API.format(package=package_name)

    async with httpx.AsyncClient(http2=True, timeout=30.0) as client:
        response = await client.get(url)

        if response.status_code == 404:
            if version:
                raise ValueError(f"Package {package_name} version {version} not found")
            else:
                raise ValueError(f"Package not found: {package_name}")

        response.raise_for_status()

        data = response.json()
        info = data["info"]

        return {
            "name": info.get("name"),
            "version": info.get("version"),
            "summary": info.get("summary"),
            "author": info.get("author"),
            "author_email": info.get("author_email"),
            "license": info.get("license"),
            "requires_python": info.get("requires_python"),
            "dependencies": info.get("requires_dist", []),
            "home_page": info.get("home_page"),
            "project_url": info.get("project_url"),
            "project_urls": info.get("project_urls", {}),
            "classifiers": info.get("classifiers", []),
        }


async def get_multiple_package_versions(package_names: List[str]) -> Dict[str, List[str]]:
    """
    Get versions for multiple packages in parallel.

    Args:
        package_names: List of package names

    Returns:
        Dict mapping package name to list of versions
    """
    tasks = [get_package_versions(name) for name in package_names]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    versions_dict = {}
    for name, result in zip(package_names, results):
        if isinstance(result, Exception):
            versions_dict[name] = []
        else:
            versions_dict[name] = result

    return versions_dict


async def check_package_exists(package_name: str) -> bool:
    """
    Check if a package exists on PyPI.

    Args:
        package_name: Name of the package

    Returns:
        True if package exists
    """
    try:
        await get_latest_version(package_name)
        return True
    except Exception:
        return False


async def get_package_wheel_info(package_name: str, version: str) -> List[Dict]:
    """
    Get wheel information for a specific package version.

    Args:
        package_name: Name of the package
        version: Version string

    Returns:
        List of wheel information dicts with:
        - filename
        - url
        - size
        - python_version
        - platform
    """
    url = f"https://pypi.org/pypi/{package_name}/{version}/json"

    async with httpx.AsyncClient(http2=True, timeout=30.0) as client:
        response = await client.get(url)

        if response.status_code == 404:
            raise ValueError(f"Package {package_name} version {version} not found")

        response.raise_for_status()

        data = response.json()
        releases = data.get("releases", {}).get(version, [])

        wheels = []
        for release in releases:
            if release.get("packagetype") == "bdist_wheel":
                wheels.append(
                    {
                        "filename": release.get("filename"),
                        "url": release.get("url"),
                        "size": release.get("size"),
                        "python_version": release.get("python_version"),
                        "platform": release.get("platform", ""),
                        "sha256": release.get("digests", {}).get("sha256"),
                    }
                )

        return wheels
