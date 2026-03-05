"""
Self-update functionality for srpt.

Updates srpt to the latest version from GitHub releases.
"""

import asyncio
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional

import httpx

from . import __version__
from .utils.confirm import dry_run_header, print_success, print_error, print_warning


GITHUB_API = "https://api.github.com/repos/thie1210/srpt/releases/latest"
GITHUB_ARCHIVE = "https://github.com/thie1210/srpt/archive/refs/tags/v{version}.tar.gz"


async def check_for_updates() -> Optional[str]:
    """
    Check GitHub releases API for latest version.

    Returns:
        Latest version string if update available, None if up to date

    Raises:
        httpx.HTTPError: If request fails
    """
    async with httpx.AsyncClient(http2=True, timeout=10.0) as client:
        try:
            response = await client.get(GITHUB_API)
            response.raise_for_status()

            data = response.json()
            latest_version = data["tag_name"].lstrip("v")

            # Compare versions
            from packaging.version import Version

            current = Version(__version__)
            latest = Version(latest_version)

            if latest > current:
                return latest_version
            return None
        except httpx.HTTPError as e:
            print(f"Error checking for updates: {e}")
            raise


async def get_latest_release_info() -> dict:
    """
    Get information about the latest release.

    Returns:
        Dict with release information:
        - version
        - changelog
        - published_at

    Raises:
        httpx.HTTPError: If request fails
    """
    async with httpx.AsyncClient(http2=True, timeout=10.0) as client:
        try:
            response = await client.get(GITHUB_API)

            if response.status_code == 404:
                # No releases yet, fall back to tags
                tags_url = "https://api.github.com/repos/thie1210/srpt/tags"
                response = await client.get(tags_url)
                response.raise_for_status()

                tags_data = response.json()
                if tags_data:
                    latest_tag = tags_data[0]
                    return {
                        "version": latest_tag["name"].lstrip("v"),
                        "changelog": "",
                        "published_at": "",
                        "html_url": latest_tag.get("zipball_url", ""),
                    }
                else:
                    raise ValueError("No releases or tags found")

            response.raise_for_status()

            data = response.json()

            return {
                "version": data["tag_name"].lstrip("v"),
                "changelog": data.get("body", ""),
                "published_at": data.get("published_at", ""),
                "html_url": data.get("html_url", ""),
            }
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ValueError("No releases found. Create a release first.")
            raise


async def download_release(version: str, target_dir: Path) -> Path:
    """
    Download a specific release from GitHub.

    Args:
        version: Version to download
        target_dir: Directory to download to

    Returns:
        Path to downloaded tar.gz file

    Raises:
        httpx.HTTPError: If download fails
    """
    url = GITHUB_ARCHIVE.format(version=version)
    target_file = target_dir / f"srpt-{version}.tar.gz"

    print(f"  Downloading srpt {version}...")

    async with httpx.AsyncClient(http2=True, timeout=60.0, follow_redirects=True) as client:
        response = await client.get(url)
        response.raise_for_status()

        target_file.write_bytes(response.content)

    print(f"  ✓ Downloaded to {target_file.name}")
    return target_file


def get_srpt_install_dir() -> Path:
    """
    Get the srpt installation directory.

    Returns:
        Path to srpt installation directory
    """
    # Check environment variable first
    srpt_base_dir = os.environ.get("SRPT_BASE_DIR", str(Path.home() / ".local" / "share" / "srpt"))
    return Path(srpt_base_dir) / "lib" / "srpt"


def get_srpt_launcher_path() -> Path:
    """
    Get the srpt launcher script path.

    Returns:
        Path to srpt launcher script
    """
    srpt_bin_dir = os.environ.get("SRPT_BIN_DIR", str(Path.home() / ".local" / "bin"))
    return Path(srpt_bin_dir) / "srpt"


async def self_update(
    dry_run: bool = True, check_only: bool = False, target_version: Optional[str] = None
) -> bool:
    """
    Update srpt to latest or specific version.

    Args:
        dry_run: If True, only show what would be done
        check_only: If True, only check for updates (don't show dry-run)
        target_version: Specific version to update to (optional)

    Returns:
        True if update succeeded (or would succeed in dry-run)

    Raises:
        ValueError: If version not found
        httpx.HTTPError: If download fails
    """
    # Get current version
    current_version = __version__

    # Check for updates
    if check_only:
        print("Checking for updates...")
        latest = await check_for_updates()

        if latest is None:
            print(f"\n✓ srpt is up to date")
            print(f"  Current version: {current_version}")
            return True
        else:
            print(f"\n! Update available")
            print(f"  Current version: {current_version}")
            print(f"  Latest version:  {latest}")
            print(f"\n  Run 'srpt update --self' to see changes")
            print(f"  Run 'srpt update --self --apply' to update")
            return True

    # Get target version
    changelog = ""
    if target_version:
        version = target_version
    else:
        release_info = await get_latest_release_info()
        version = release_info["version"]
        changelog = release_info.get("changelog", "")

    # Check if already on target version
    from packaging.version import Version

    if Version(version) <= Version(current_version):
        print(f"\n✓ srpt is up to date")
        print(f"  Current version: {current_version}")
        print(f"  Target version:  {version}")
        return True

    # Show dry-run or proceed
    if dry_run:
        dry_run_header()

        print("SRPT UPDATE:")
        print(f"  Current: {current_version}")
        print(f"  Latest:  {version}")

        if not target_version:
            print(f"\nCHANGES:")
            # Parse changelog (simple version)
            if changelog:
                # Show first few lines
                lines = changelog.split("\n")[:10]
                for line in lines:
                    if line.strip():
                        print(f"  {line}")

        print(f"\nRun 'srpt update --self --apply' to update")
        return True

    # Actually perform the update
    print("\nSRPT UPDATE:")
    print(f"  Current: {current_version}")
    print(f"  Target:  {version}")
    print()

    # Create temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Download release
        try:
            tar_file = await download_release(version, tmpdir_path)
        except httpx.HTTPError as e:
            print_error(f"Failed to download: {e}")
            return False

        # Extract
        print("  Extracting...")
        import tarfile

        with tarfile.open(tar_file, "r:gz") as tar:
            tar.extractall(tmpdir_path)

        # Find extracted directory (handle both old 'py' and new 'srpt' naming)
        extracted_dir = tmpdir_path / f"srpt-{version}"
        if not extracted_dir.exists():
            # Try old naming for backward compatibility
            extracted_dir = tmpdir_path / f"py-{version}"

        if not extracted_dir.exists():
            print_error("Failed to find extracted files")
            print_error(
                f"  Expected: {tmpdir_path / f'srpt-{version}'} or {tmpdir_path / f'py-{version}'}"
            )
            return False

        # Get installation directory
        install_dir = get_srpt_install_dir()

        # Backup current installation
        if install_dir.exists():
            backup_dir = install_dir.parent / f"srpt.backup.{current_version}"
            print(f"  Backing up to {backup_dir.name}...")
            if backup_dir.exists():
                shutil.rmtree(backup_dir)
            shutil.copytree(install_dir, backup_dir)

        # Remove old installation
        if install_dir.exists():
            shutil.rmtree(install_dir)

        # Copy new installation
        print(f"  Installing to {install_dir}...")
        shutil.copytree(extracted_dir, install_dir)

        # Install dependencies
        print("  Installing dependencies...")
        python_bin = get_python_bin()

        # Install dependencies from pyproject.toml
        proc = await asyncio.create_subprocess_exec(
            python_bin,
            "-m",
            "pip",
            "install",
            "--quiet",
            "--disable-pip-version-check",
            "httpx[http2]>=0.27.0",
            "installer>=0.7.0",
            "packaging>=21.0",
            "resolvelib>=1.0.0",
            "rich>=13.0.0",
            "tomli>=2.0.0",
            "pip-audit>=2.6.0",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.wait()

        print_success(f"srpt updated to {version}")
        print()
        print("  → Run 'srpt --version' to verify")
        print("  → Run 'srpt health' to check system health")

        return True


def get_python_bin() -> str:
    """
    Get the Python binary path for the managed installation.

    Returns:
        Path to Python binary
    """
    srpt_base_dir = os.environ.get("SRPT_BASE_DIR", str(Path.home() / ".local" / "share" / "srpt"))
    python_version = "3.13.12"
    build_tag = "20260211"

    python_bin = (
        Path(srpt_base_dir)
        / "python"
        / f"{python_version}-{build_tag}"
        / "python"
        / "bin"
        / "python3"
    )

    if python_bin.exists():
        return str(python_bin)

    # Fall back to system Python
    return "python3"
