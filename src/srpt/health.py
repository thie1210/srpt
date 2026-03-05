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
            result = subprocess.run(
                [str(python_path), "--version"], capture_output=True, text=True, timeout=5
            )

            # Check if command succeeded
            if result.returncode == 0:
                version_str = result.stdout.strip() or result.stderr.strip()
                version_str = version_str.replace("Python ", "")

                return {
                    "version": version_str,
                    "venv": True,
                    "path": str(venv_path),
                }
            else:
                # Python binary exists but failed to run
                return {
                    "version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                    "venv": True,
                    "path": str(venv_path),
                    "error": "venv Python binary failed to execute",
                }
        except subprocess.TimeoutExpired:
            return {
                "version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                "venv": True,
                "path": str(venv_path),
                "error": "venv Python check timed out",
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
        Path(os.environ.get("SRPT_BASE_DIR", str(Path.home() / ".local" / "share" / "srpt")))
        / "cache"
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
    import sys

    venv_path = project_root / ".venv"

    if not venv_path.exists():
        return {
            "current_version": f"{sys.version_info.major}.{sys.version_info.minor}",
            "status": "no venv",
            "checked_versions": [],
        }

    # Get the venv's Python version
    if sys.platform == "win32":
        python_path = venv_path / "Scripts" / "python.exe"
    else:
        python_path = venv_path / "bin" / "python"

    current_version = None
    if python_path.exists():
        import subprocess

        try:
            result = subprocess.run(
                [str(python_path), "--version"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                version_str = result.stdout.strip() or result.stderr.strip()
                version_str = version_str.replace("Python ", "")
                # Extract major.minor
                parts = version_str.split(".")
                if len(parts) >= 2:
                    current_version = f"{parts[0]}.{parts[1]}"
        except Exception:
            pass

    if not current_version:
        current_version = f"{sys.version_info.major}.{sys.version_info.minor}"

    # Get site-packages path
    if sys.platform == "win32":
        site_packages = venv_path / "Lib" / "site-packages"
    else:
        potential = list(venv_path.glob("lib/python*/site-packages"))
        site_packages = potential[0] if potential else None

    if not site_packages or not site_packages.exists():
        return {
            "current_version": current_version,
            "status": "no packages",
            "checked_versions": [],
        }

    # Determine which versions to check
    # Check current version and nearby versions
    try:
        major = int(current_version.split(".")[0])
        minor = int(current_version.split(".")[1])

        # Check current, previous, and next versions
        versions_to_check = [
            f"{major}.{minor - 1}" if minor > 0 else None,
            current_version,
            f"{major}.{minor + 1}",
        ]
        versions_to_check = [v for v in versions_to_check if v is not None]
    except Exception:
        versions_to_check = [current_version]

    # Check compatibility for each Python version
    version_compatibility = {}
    total_packages = 0

    for dist_info in site_packages.glob("*.dist-info"):
        try:
            metadata_file = dist_info / "METADATA"
            if not metadata_file.exists():
                continue

            total_packages += 1

            # Read metadata to find Requires-Python
            requires_python = None
            with open(metadata_file, "r") as f:
                for line in f:
                    if line.startswith("Requires-Python:"):
                        requires_python = line.split(":", 1)[1].strip()
                        break

            if requires_python:
                # Check each version
                for version in versions_to_check:
                    if version not in version_compatibility:
                        version_compatibility[version] = True

                    if not is_python_version_compatible(version, requires_python):
                        version_compatibility[version] = False
        except Exception:
            continue

    if total_packages == 0:
        return {
            "current_version": current_version,
            "status": "no packages",
            "checked_versions": [],
        }

    # Format results
    checked_results = []
    for version in versions_to_check:
        if version in version_compatibility:
            compatible = version_compatibility[version]
            checked_results.append(
                {
                    "version": version,
                    "compatible": compatible,
                    "is_current": version == current_version,
                }
            )

    return {
        "current_version": current_version,
        "total_packages": total_packages,
        "checked_versions": checked_results,
    }


def is_python_version_compatible(python_version: str, requires_python: str) -> bool:
    """
    Check if a Python version is compatible with a Requires-Python specifier.

    Args:
        python_version: Python version string (e.g., "3.12")
        requires_python: Requires-Python specifier (e.g., ">=3.8,<4.0")

    Returns:
        True if compatible, False otherwise
    """
    try:
        from packaging.specifiers import SpecifierSet
        from packaging.version import Version

        specifiers = SpecifierSet(requires_python)
        version = Version(python_version)

        return version in specifiers
    except Exception:
        # If we can't parse, assume compatible
        return True


def format_health_report(health: Dict, full: bool = False) -> None:
    """
    Format and print health report.

    Args:
        health: Health dict from health_check
        full: If True, show all packages
    """
    print("\nSRPT HEALTH CHECK")

    # srpt version
    srpt_version = health.get("py_version", {})
    current = srpt_version.get("current", "unknown")
    latest = srpt_version.get("latest", "unknown")
    update_available = srpt_version.get("update_available", False)

    if update_available:
        print(f"  ! srpt version: {current} (latest: {latest})")
        print("    → Run 'srpt update --self --apply' to update")
    else:
        print(f"  ✓ srpt version: {current} (latest: {latest})")

    # Python version
    python_version = health.get("python_version", {})
    version = python_version.get("version", "unknown")
    venv = python_version.get("venv", False)
    python_error = python_version.get("error")

    if python_error:
        print(f"  ! Python: {version}")
        print(f"    ! {python_error}")
    else:
        print(f"  ✓ Python: {version}")
        if not venv:
            print("    ! No .venv found")

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
            vuln_id_obj = vuln.get("id", {})
            vuln_id = (
                vuln_id_obj.get("id", "unknown")
                if isinstance(vuln_id_obj, dict)
                else str(vuln_id_obj)
            )
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
        print(f"  ! Outdated: {len(outdated)}")
        for pkg in outdated[:10]:  # Show first 10
            name = pkg.get("name", "unknown")
            current = pkg.get("current", "unknown")
            latest = pkg.get("latest", "unknown")
            print(f"    • {name} {current} → {latest}")
        if len(outdated) > 10:
            print(f"    ... and {len(outdated) - 10} more")
        print("  → Run 'srpt update' to update all")
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
    current_version = compatibility.get("current_version", "unknown")
    checked_versions = compatibility.get("checked_versions", [])

    if not checked_versions:
        status = compatibility.get("status", "unknown")
        print(f"  Status: {status}")
    else:
        print(f"  Current: Python {current_version}")
        print(f"  Checked {compatibility.get('total_packages', 0)} packages for compatibility:")

        for version_info in checked_versions:
            version = version_info.get("version", "unknown")
            compatible = version_info.get("compatible", True)
            is_current = version_info.get("is_current", False)

            if compatible:
                status = "✓"
            else:
                status = "✗"

            label = f"Python {version}"
            if is_current:
                label += " (current)"

            print(f"  {status} {label}")

    # Summary
    print("\nSUMMARY")
    warnings = health.get("warnings", 0)
    errors = health.get("errors", 0)

    if warnings == 0 and errors == 0:
        print("  ✓ All checks passed")
    else:
        if warnings:
            print(f"  ! {warnings} warnings")
        if errors:
            print(f"  ✗ {errors} errors")

    if not full:
        print(f"  → Run 'srpt health --full' for all {installed} packages")
