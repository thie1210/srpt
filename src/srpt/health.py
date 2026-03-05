"""
Health check functionality.

Comprehensive diagnostics for py, Python, packages, and security.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from . import __version__
from .utils.pypi_client import get_latest_version, get_package_versions
from .utils.confirm import print_success, print_error, print_warning


async def health_check(project_root: Path, full: bool = False) -> Dict:
    """
    Comprehensive health diagnostics.

    Args:
        project_root: Path to project root
        full: If True, show all packages (not just warnings)

    Returns:
        Dict with health information:
        - py_version
        - python_version
        - cache_status
        - vulnerabilities
        - outdated_packages
        - compatibility
        - warnings
        - errors
    """
    health = {
        "py_version": {},
        "python_version": {},
        "cache": {},
        "security": {},
        "dependencies": {},
        "compatibility": {},
        "warnings": 0,
        "errors": 0,
    }

    # Check py version
    health["py_version"] = await check_py_version()
    if health["py_version"].get("update_available"):
        health["warnings"] += 1

    # Check Python version
    health["python_version"] = check_python_version(project_root)

    # Check cache
    health["cache"] = check_cache_status(project_root)

    # Check security
    health["security"] = await check_security(project_root)
    if health["security"].get("vulnerabilities"):
        health["warnings"] += len(health["security"]["vulnerabilities"])

    # Check dependencies
    health["dependencies"] = await check_dependencies(project_root, full)
    if health["dependencies"].get("outdated"):
        health["warnings"] += len(health["dependencies"]["outdated"])

    # Check compatibility
    health["compatibility"] = await check_compatibility(project_root)

    return health


async def check_py_version() -> Dict:
    """
    Check if py is up to date.

    Returns:
        Dict with version information
    """
    from .self_update import check_for_updates

    try:
        latest = await check_for_updates()

        return {
            "current": __version__,
            "latest": latest if latest else __version__,
            "update_available": latest is not None,
        }
    except Exception as e:
        return {
            "current": __version__,
            "latest": __version__,
            "update_available": False,
            "error": str(e),
        }


def check_python_version(project_root: Path) -> Dict:
    """
    Check Python version in project.

    Args:
        project_root: Path to project root

    Returns:
        Dict with Python version information
    """
    import sys

    venv_path = project_root / ".venv"

    if not venv_path.exists():
        return {
            "version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "venv": False,
        }

    # Try to get Python version from venv
    if sys.platform == "win32":
        python_path = venv_path / "Scripts" / "python.exe"
    else:
        python_path = venv_path / "bin" / "python"

    if python_path.exists():
        import subprocess

        try:
            result = subprocess.run([str(python_path), "--version"], capture_output=True, text=True)
            version_str = result.stdout.strip() or result.stderr.strip()
            version_str = version_str.replace("Python ", "")

            return {
                "version": version_str,
                "venv": True,
                "path": str(venv_path),
            }
        except Exception:
            pass

    return {
        "version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "venv": True,
        "path": str(venv_path),
    }


def check_cache_status(project_root: Path) -> Dict:
    """
    Check cache status.

    Args:
        project_root: Path to project root

    Returns:
        Dict with cache information
    """
    import os
    from pathlib import Path

    cache_dir = (
        Path(os.environ.get("PY_BASE_DIR", str(Path.home() / ".local" / "share" / "py"))) / "cache"
    )

    if not cache_dir.exists():
        return {
            "exists": False,
            "size_mb": 0,
        }

    # Calculate cache size
    total_size = 0
    for path in cache_dir.rglob("*"):
        if path.is_file():
            total_size += path.stat().st_size

    size_mb = total_size / (1024 * 1024)

    return {
        "exists": True,
        "size_mb": round(size_mb, 1),
        "path": str(cache_dir),
    }


async def check_security(project_root: Path) -> Dict:
    """
    Check for security vulnerabilities.

    Args:
        project_root: Path to project root

    Returns:
        Dict with security information
    """
    from .audit import run_pip_audit

    vulnerabilities = run_pip_audit(project_root)

    return {
        "vulnerabilities": vulnerabilities,
        "count": len(vulnerabilities),
    }


async def check_dependencies(project_root: Path, full: bool = False) -> Dict:
    """
    Check for outdated packages.

    Args:
        project_root: Path to project root
        full: If True, include all packages

    Returns:
        Dict with dependency information
    """
    import sys

    venv_path = project_root / ".venv"

    if not venv_path.exists():
        return {
            "installed": 0,
            "outdated": [],
        }

    # Get site-packages path
    if sys.platform == "win32":
        site_packages = venv_path / "Lib" / "site-packages"
    else:
        potential = list(venv_path.glob("lib/python*/site-packages"))
        site_packages = potential[0] if potential else None

    if not site_packages or not site_packages.exists():
        return {
            "installed": 0,
            "outdated": [],
        }

    # Get installed packages
    installed = []
    for dist_info in site_packages.glob("*.dist-info"):
        try:
            name = dist_info.name.replace(".dist-info", "")
            parts = name.rsplit("-", 1)
            if len(parts) == 2:
                package_name = parts[0]
                version = parts[1]
                installed.append(
                    {
                        "name": package_name,
                        "version": version,
                    }
                )
        except Exception:
            continue

    # Check for updates (in parallel)
    outdated = []

    if installed:
        # Check each package for updates
        tasks = []
        for pkg in installed[:20]:  # Limit to 20 for performance
            tasks.append(check_package_update(pkg["name"], pkg["version"]))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for pkg, result in zip(installed[:20], results):
            if isinstance(result, Exception):
                continue

            if result and result.get("update_available"):
                outdated.append(
                    {
                        "name": pkg["name"],
                        "current": pkg["version"],
                        "latest": result.get("latest"),
                    }
                )

    return {
        "installed": len(installed),
        "outdated": outdated,
        "all": installed if full else None,
    }


async def check_package_update(package_name: str, current_version: str) -> Optional[Dict]:
    """
    Check if a package has an update available.

    Args:
        package_name: Name of the package
        current_version: Current version

    Returns:
        Dict with update information, or None if no update
    """
    try:
        latest = await get_latest_version(package_name)

        from packaging.version import Version

        if Version(latest) > Version(current_version):
            return {
                "current": current_version,
                "latest": latest,
                "update_available": True,
            }

        return {
            "current": current_version,
            "latest": latest,
            "update_available": False,
        }
    except Exception:
        return None


async def check_compatibility(project_root: Path) -> Dict:
    """
    Check Python compatibility for installed packages.

    Args:
        project_root: Path to project root

    Returns:
        Dict with compatibility information
    """
    # TODO: Implement compatibility checking
    return {
        "python_312": "unknown",
        "python_313": "unknown",
    }


def format_health_report(health: Dict, full: bool = False) -> None:
    """
    Format and print health report.

    Args:
        health: Health dict from health_check
        full: If True, show all packages
    """
    print("\nPY HEALTH CHECK")

    # Py version
    py_version = health.get("py_version", {})
    current = py_version.get("current", "unknown")
    latest = py_version.get("latest", "unknown")
    update_available = py_version.get("update_available", False)

    if update_available:
        print(f"  ⚠ py version: {current} (latest: {latest})")
        print("    → Run 'py update --self --apply' to update")
    else:
        print(f"  ✓ py version: {current} (latest: {latest})")

    # Python version
    python_version = health.get("python_version", {})
    version = python_version.get("version", "unknown")
    venv = python_version.get("venv", False)

    print(f"  ✓ Python: {version}")
    if not venv:
        print("    ⚠ No .venv found")

    # Cache
    cache = health.get("cache", {})
    if cache.get("exists"):
        size_mb = cache.get("size_mb", 0)
        print(f"  ✓ Cache: {size_mb} MB")
    else:
        print("  ○ Cache: Not found")

    print("\nSECURITY")

    # Security
    security = health.get("security", {})
    vulnerabilities = security.get("vulnerabilities", [])

    if not vulnerabilities:
        print("  ✓ Vulnerabilities: 0 found")
    else:
        print(f"  ✗ Vulnerabilities: {len(vulnerabilities)} found")
        for vuln in vulnerabilities[:5]:  # Show first 5
            pkg = vuln.get("package", {})
            name = pkg.get("name", "unknown")
            version = pkg.get("version", "unknown")
            vuln_id = vuln.get("id", {}).get("id", "unknown")
            print(f"    • {name} {version}: {vuln_id}")
        if len(vulnerabilities) > 5:
            print(f"    ... and {len(vulnerabilities) - 5} more")

    print("\nDEPENDENCIES")

    # Dependencies
    dependencies = health.get("dependencies", {})
    installed = dependencies.get("installed", 0)
    outdated = dependencies.get("outdated", [])

    print(f"  Installed: {installed}")

    if outdated:
        print(f"  ⚠ Outdated: {len(outdated)}")
        for pkg in outdated[:10]:  # Show first 10
            name = pkg.get("name", "unknown")
            current = pkg.get("current", "unknown")
            latest = pkg.get("latest", "unknown")
            print(f"    • {name} {current} → {latest}")
        if len(outdated) > 10:
            print(f"    ... and {len(outdated) - 10} more")
        print("  → Run 'py update' to update all")
    else:
        print("  ✓ All packages up to date")

    if full and dependencies.get("all"):
        print("\nALL PACKAGES")
        for pkg in dependencies["all"]:
            name = pkg.get("name", "unknown")
            version = pkg.get("version", "unknown")
            print(f"  • {name} {version}")

    print("\nCOMPATIBILITY")

    # Compatibility
    compatibility = health.get("compatibility", {})
    python_312 = compatibility.get("python_312", "unknown")
    python_313 = compatibility.get("python_313", "unknown")

    print(f"  Python 3.12: {python_312}")
    print(f"  Python 3.13: {python_313}")

    # Summary
    print("\nSUMMARY")
    warnings = health.get("warnings", 0)
    errors = health.get("errors", 0)

    if warnings == 0 and errors == 0:
        print("  ✓ All checks passed")
    else:
        if warnings:
            print(f"  ⚠ {warnings} warnings")
        if errors:
            print(f"  ✗ {errors} errors")

    if not full:
        print(f"  → Run 'py health --full' for all {installed} packages")
