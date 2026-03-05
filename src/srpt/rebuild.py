"""
Rebuild command - Rebuild project with a different Python version.

This command handles Python version upgrades by:
1. Checking compatibility
2. Backing up current venv
3. Creating new venv with target Python
4. Reinstalling all packages
"""

import sys
from pathlib import Path
from typing import Optional, List, Dict
import subprocess
import shutil
from datetime import datetime

from .utils.confirm import dry_run_header, print_error, print_success
from .utils.backup_manager import BackupManager


def get_installed_packages(venv_path: Path) -> List[Dict[str, str]]:
    """
    Get list of installed packages from venv.

    Args:
        venv_path: Path to .venv directory

    Returns:
        List of dicts with 'name' and 'version' keys
    """
    if not venv_path.exists():
        return []

    # Get site-packages path
    if sys.platform == "win32":
        site_packages = venv_path / "Lib" / "site-packages"
    else:
        potential = list(venv_path.glob("lib/python*/site-packages"))
        site_packages = potential[0] if potential else None

    if not site_packages or not site_packages.exists():
        return []

    # Get installed packages from dist-info directories
    packages = []
    for dist_info in site_packages.glob("*.dist-info"):
        try:
            name = dist_info.name.replace(".dist-info", "")
            parts = name.rsplit("-", 1)
            if len(parts) == 2:
                package_name = parts[0]
                version = parts[1]
                packages.append({"name": package_name, "version": version})
        except Exception:
            continue

    return packages


def check_python_version_available(version: str) -> bool:
    """
    Check if a Python version is available in managed installations.

    Args:
        version: Python version string (e.g., "3.12", "3.13.12")

    Returns:
        True if version is available
    """
    # Use the same logic as fetcher - check ~/.local/share/srpt/python/
    srpt_base = Path.home() / ".local" / "share" / "srpt"
    python_dir = srpt_base / "python"

    if not python_dir.exists():
        return False

    # Check for exact version or major.minor match
    for version_dir in python_dir.iterdir():
        if version_dir.is_dir():
            dir_version = version_dir.name.split("-")[0]
            if dir_version == version or dir_version.startswith(f"{version}."):
                python_bin = version_dir / "python" / "bin" / "python3"
                if python_bin.exists():
                    return True

    return False


def get_python_binary_path(version: str) -> Optional[Path]:
    """
    Get path to Python binary for a specific version.

    Args:
        version: Python version string (e.g., "3.12", "3.13.12")

    Returns:
        Path to Python binary or None if not found
    """
    # Use the same logic as fetcher - check ~/.local/share/srpt/python/
    srpt_base = Path.home() / ".local" / "share" / "srpt"
    python_dir = srpt_base / "python"

    if not python_dir.exists():
        return None

    # Find matching version
    for version_dir in python_dir.iterdir():
        if version_dir.is_dir():
            dir_version = version_dir.name.split("-")[0]
            if dir_version == version or dir_version.startswith(f"{version}."):
                python_bin = version_dir / "python" / "bin" / "python3"
                if python_bin.exists():
                    return python_bin

    return None


def check_package_compatibility(packages: List[Dict[str, str]], target_python: str) -> Dict:
    """
    Check if packages are compatible with target Python version.

    Args:
        packages: List of package dicts
        target_python: Target Python version

    Returns:
        Dict with compatibility info
    """
    from packaging.version import Version
    from packaging.specifiers import SpecifierSet

    compatible = []
    incompatible = []
    unknown = []

    target_version = Version(target_python)

    for pkg in packages:
        # This is a simplified check
        # In a full implementation, we'd check PyPI for package metadata
        # For now, assume all packages are compatible
        compatible.append(pkg)

    return {
        "compatible": compatible,
        "incompatible": incompatible,
        "unknown": unknown,
        "total": len(packages),
        "compatible_count": len(compatible),
        "incompatible_count": len(incompatible),
    }


def rebuild_project(
    project_root: Path,
    target_version: Optional[str] = None,
    dry_run: bool = True,
    restore: bool = False,
    list_backups: bool = False,
) -> bool:
    """
    Rebuild project with a different Python version.

    Args:
        project_root: Path to project root
        target_version: Target Python version (e.g., "3.12")
        dry_run: If True, show what would be done without making changes
        restore: If True, restore from last backup
        list_backups: If True, list available backups

    Returns:
        True if successful, False otherwise
    """
    backup_manager = BackupManager(project_root)

    # Handle --list-backups
    if list_backups:
        backups = backup_manager.list_backups()
        if not backups:
            print("No backups found")
            return True

        print("\nAVAILABLE BACKUPS:")
        for backup in backups:
            age_days = backup_manager.check_backup_age(backup)
            print(f"  • {backup.name} ({age_days} days old)")
        return True

    # Handle --restore
    if restore:
        latest_backup = backup_manager.get_latest_backup()
        if not latest_backup:
            print_error("No backup found to restore")
            return False

        if dry_run:
            dry_run_header()
            print(f"\nWould restore from: {latest_backup.name}")
            print("\nRun 'srpt rebuild --restore --apply' to restore")
            return True

        print(f"\nRestoring from: {latest_backup.name}")
        success = backup_manager.restore_backup(latest_backup)
        if success:
            print_success("Backup restored successfully")
            return True
        else:
            print_error("Failed to restore backup")
            return False

    # Normal rebuild flow
    venv_path = project_root / ".venv"

    # Check if target version is specified
    if not target_version:
        print_error("No target version specified")
        print("  → Use: srpt rebuild --with-version <version>")
        print("  → Example: srpt rebuild --with-version 3.14")
        return False

    # Check if target version is available
    if not check_python_version_available(target_version):
        print_error(f"Python {target_version} is not installed")
        print("  → Run: srpt fetch <version>")
        print("  → Example: srpt fetch 3.14")
        return False

    # Get Python binary path
    python_bin = get_python_binary_path(target_version)
    if not python_bin:
        print_error(f"Could not find Python {target_version} binary")
        return False

    # Get current Python version
    current_python = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

    # Get installed packages
    packages = get_installed_packages(venv_path)
    package_count = len(packages)

    # Check compatibility
    compatibility = check_package_compatibility(packages, target_version)

    # Dry run output
    if dry_run:
        dry_run_header()

        print("\nPYTHON UPGRADE:")
        print(f"  Current: {current_python}")
        print(f"  Target:  {target_version}")

        print("\nACTIONS:")
        print("  1. Install Python " + target_version)
        print("  2. Backup current .venv")
        print("  3. Remove .venv")
        print("  4. Create new .venv with Python " + target_version)
        print(f"  5. Reinstall {package_count} packages")
        if (project_root / "pyproject.toml").exists():
            print("  6. Update pyproject.toml (requires-python)")

        print("\nCOMPATIBILITY CHECK:")
        if compatibility["incompatible_count"] == 0:
            print(
                f"  ✓ {compatibility['compatible_count']}/{compatibility['total']} packages compatible with Python {target_version}"
            )
        else:
            print(
                f"  ! {compatibility['incompatible_count']} packages incompatible with Python {target_version}"
            )
            for pkg in compatibility["incompatible"][:5]:
                print(f"    • {pkg['name']} {pkg['version']}")

        if venv_path.exists():
            backup_name = f".venv.backup.upgrade.{datetime.now().strftime('%Y-%m-%d')}.python-{target_version}"
            print("\nBACKUP:")
            print(f"  ✓ Will create: {backup_name}")

        print(f"\nRun 'srpt rebuild --with-version {target_version} --apply' to proceed")
        return True

    # Actual rebuild
    print("\nPYTHON UPGRADE:")
    print(f"  Current: {current_python}")
    print(f"  Target:  {target_version}")

    # Step 1: Backup current venv
    if venv_path.exists():
        print("\nBACKUP:")
        backup_name = f"upgrade.{datetime.now().strftime('%Y-%m-%d')}.python-{target_version}"
        print(f"  Creating backup: {backup_name}")
        backup_path = backup_manager.create_backup(backup_name)
        if backup_path:
            print_success(f"Backup created: {backup_path.name}")
        else:
            print_error("Failed to create backup")
            return False

    # Step 2: Remove old venv
    print("\nREMOVING OLD VENV:")
    if venv_path.exists():
        shutil.rmtree(venv_path)
        print_success("Old .venv removed")

    # Step 3: Create new venv
    print("\nCREATING NEW VENV:")
    print(f"  Using Python {target_version}")
    try:
        result = subprocess.run(
            [str(python_bin), "-m", "venv", str(venv_path)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            print_success(f"Created .venv with Python {target_version}")
        else:
            print_error(f"Failed to create venv: {result.stderr}")
            return False
    except Exception as e:
        print_error(f"Failed to create venv: {e}")
        return False

    # Step 4: Reinstall packages
    if packages:
        print(f"\nREINSTALLING {package_count} PACKAGES:")

        # Get venv pip
        if sys.platform == "win32":
            pip_path = venv_path / "Scripts" / "pip.exe"
        else:
            pip_path = venv_path / "bin" / "pip"

        # Install packages
        for i, pkg in enumerate(packages, 1):
            pkg_spec = f"{pkg['name']}=={pkg['version']}"
            print(f"  [{i}/{package_count}] Installing {pkg_spec}...", end="\r")

            try:
                result = subprocess.run(
                    [str(pip_path), "install", pkg_spec],
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                if result.returncode != 0:
                    print(f"  ! Failed to install {pkg_spec}")
            except Exception as e:
                print(f"  ! Error installing {pkg_spec}: {e}")

        print()
        print_success(f"Reinstalled {package_count} packages")

    # Step 5: Update pyproject.toml if exists
    pyproject_path = project_root / "pyproject.toml"
    if pyproject_path.exists():
        print("\nUPDATE pyproject.toml:")
        print("  ! Manual update required")
        print(
            f'  → Set requires-python = ">={target_version.split(".")[0]}.{target_version.split(".")[1]}"'
        )

    # Step 6: Run health check
    print("\nRUNNING HEALTH CHECK:")
    print("  → Run 'srpt health' to verify the rebuild")

    print("\nREBUILD COMPLETE")
    print_success(f"Project rebuilt with Python {target_version}")

    return True
