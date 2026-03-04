"""
Uninstall command implementation.
"""

import shutil
from pathlib import Path
from typing import List
from py.installed import (
    find_dist_info,
    parse_record_file,
    list_installed_packages,
)


def uninstall_command(packages: List[str], site_packages: Path):
    """Uninstalls packages from site-packages."""
    for package_name in packages:
        uninstall_package(package_name, site_packages)


def uninstall_package(package_name: str, site_packages: Path) -> bool:
    """
    Uninstalls a package by removing its files and metadata.

    Returns True if successful, False if package not found.
    """
    # Find dist-info
    dist_info = find_dist_info(package_name, site_packages)

    if not dist_info:
        print(f"Py: Package '{package_name}' is not installed")
        return False

    # Get version for user feedback
    name = dist_info.name
    if name.endswith(".dist-info"):
        name = name[:-10]  # Remove ".dist-info"

    parts = name.rsplit("-", 1)
    if len(parts) == 2:
        version = parts[1]
        print(f"Py: Uninstalling {package_name}=={version}…")
    else:
        print(f"Py: Uninstalling {package_name}…")

    # Parse RECORD file
    record_path = dist_info / "RECORD"
    files_to_remove = parse_record_file(record_path)

    # Remove all files
    removed_count = 0
    for file_path in files_to_remove:
        try:
            if file_path.is_file():
                file_path.unlink()
                removed_count += 1
            elif file_path.is_dir():
                shutil.rmtree(file_path)
                removed_count += 1
        except Exception as e:
            print(f"Py: Warning: Could not remove {file_path}: {e}")

    # Remove dist-info
    try:
        shutil.rmtree(dist_info)
        removed_count += 1
    except Exception as e:
        print(f"Py: Warning: Could not remove dist-info: {e}")

    # Also try to remove the package directory (if it exists)
    # Some packages have both dist-info and the package directory
    package_dir_candidates = [
        site_packages / package_name.replace("-", "_"),
        site_packages / package_name.replace("-", "_").lower(),
        site_packages / package_name.lower(),
    ]

    for pkg_dir in package_dir_candidates:
        if pkg_dir.exists() and pkg_dir.is_dir():
            # Make sure it's not a dist-info or egg-info
            if not pkg_dir.name.endswith((".dist-info", ".egg-info")):
                try:
                    shutil.rmtree(pkg_dir)
                    removed_count += 1
                except Exception:
                    pass

    print(f"Py: Successfully uninstalled {package_name} ({removed_count} files removed)")
    return True


def list_command(site_packages: Path):
    """List all installed packages."""
    packages = list_installed_packages(site_packages)

    if not packages:
        print("Py: No packages installed in this environment")
        return

    print(f"Py: {len(packages)} packages installed:\n")

    for pkg in packages:
        print(f"  {pkg['name']:<30} {pkg['version']}")
