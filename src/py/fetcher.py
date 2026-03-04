import os
import platform
import sys
import tarfile
import urllib.request
import json
import shutil
from pathlib import Path
from typing import Optional, List, Tuple

# Constants
LATEST_RELEASE_JSON_URL = "https://raw.githubusercontent.com/astral-sh/python-build-standalone/latest-release/latest-release.json"
PY_BASE_DIR = Path.home() / ".local" / "share" / "py"
PYTHON_DIR = PY_BASE_DIR / "python"
RELEASE_TAG = "20260211"  # Current release tag


def get_target_triple() -> str:
    """Returns the LLVM target triple for the current system."""
    system = platform.system().lower()
    machine = platform.machine().lower()

    if machine in ("aarch64", "arm64"):
        arch = "aarch64"
    elif machine in ("x86_64", "amd64"):
        arch = "x86_64"
    else:
        raise RuntimeError(f"Unsupported architecture: {machine}")

    if system == "darwin":
        return f"{arch}-apple-darwin"
    elif system == "linux":
        return f"{arch}-unknown-linux-gnu"
    elif system == "windows":
        return f"{arch}-pc-windows-msvc"
    else:
        raise RuntimeError(f"Unsupported system: {system}")


def get_available_python_versions() -> List[str]:
    """Fetch available Python versions from python-build-standalone."""
    try:
        api_url = f"https://api.github.com/repos/astral-sh/python-build-standalone/releases/tags/{RELEASE_TAG}"
        with urllib.request.urlopen(api_url) as response:
            release_data = json.loads(response.read().decode())

        versions = set()
        for asset in release_data.get("assets", []):
            name = asset["name"]
            if "cpython" in name and "install_only" in name:
                parts = name.split("-")
                if len(parts) >= 2:
                    version_full = parts[1]
                    version = version_full.split("+")[0]
                    versions.add(version)

        return sorted(versions, reverse=True)
    except Exception as e:
        print(f"Py: Could not fetch available versions: {e}")
        return ["3.14.3", "3.13.12", "3.12.12", "3.11.14", "3.10.19"]


def get_installed_python_versions() -> List[Tuple[str, Path]]:
    """List installed Python versions with their paths."""
    PYTHON_DIR.mkdir(parents=True, exist_ok=True)

    installed = []
    for version_dir in PYTHON_DIR.iterdir():
        if version_dir.is_dir():
            binary_name = "python.exe" if os.name == "nt" else "bin/python3"
            binary_path = version_dir / "python" / binary_name
            if binary_path.exists():
                version = version_dir.name.split("-")[0]
                installed.append((version, binary_path))

    return sorted(installed, key=lambda x: x[0], reverse=True)


def download_python_version(version: str) -> Path:
    """Download and install a specific Python version."""
    PYTHON_DIR.mkdir(parents=True, exist_ok=True)

    target = get_target_triple()

    full_versions = get_available_python_versions()
    major_minor = ".".join(version.split(".")[:2])

    matching_full = [v for v in full_versions if v.startswith(major_minor)]
    if not matching_full:
        raise RuntimeError(f"Python {version} not found. Available: {', '.join(full_versions[:5])}")

    actual_version = matching_full[0]
    if actual_version != version:
        print(f"Py: Resolved {version} to {actual_version}")

    asset_name = f"cpython-{actual_version}+{RELEASE_TAG}-{target}-install_only.tar.gz"

    download_url = f"https://github.com/astral-sh/python-build-standalone/releases/download/{RELEASE_TAG}/{asset_name}"

    target_dir = PYTHON_DIR / f"{actual_version}-{RELEASE_TAG}"
    binary_name = "python.exe" if os.name == "nt" else "bin/python3"
    binary_path = target_dir / "python" / binary_name

    if binary_path.exists():
        print(f"Py: Python {actual_version} already installed at {target_dir}")
        return binary_path

    print(f"Py: Downloading Python {actual_version} for {target}…")
    download_path = PY_BASE_DIR / "downloads" / asset_name
    download_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        urllib.request.urlretrieve(download_url, download_path)

        print(f"Py: Extracting to {target_dir}…")
        target_dir.mkdir(parents=True, exist_ok=True)

        if asset_name.endswith(".tar.gz"):
            with tarfile.open(download_path, "r:gz") as tar:
                tar.extractall(path=target_dir)

        download_path.unlink()

        print(f"Py: Successfully installed Python {actual_version}")
        return binary_path
    except Exception as e:
        if target_dir.exists():
            shutil.rmtree(target_dir)
        if download_path.exists():
            download_path.unlink()
        raise RuntimeError(f"Failed to download or extract Python {actual_version}: {e}")


def get_python_binary(version: Optional[str] = None) -> Path:
    """
    Get path to Python binary, downloading if necessary.

    Args:
        version: Specific version (e.g., "3.14" or "3.14.3").
                 If None, uses latest installed or downloads 3.13.12
    """
    installed = get_installed_python_versions()

    if version:
        if "." not in version:
            print(f"Py: Invalid version format '{version}'. Use format like '3.14' or '3.14.3'")
            sys.exit(1)

        major_minor = ".".join(version.split(".")[:2])

        matching_installed = [(v, p) for v, p in installed if v.startswith(major_minor)]

        if matching_installed:
            matching_installed.sort(key=lambda x: x[0], reverse=True)
            selected_version, binary_path = matching_installed[0]
            print(f"Py: Using Python {selected_version} (matched {version})")
            return binary_path

        print(f"Py: Python {version} not installed. Downloading…")
        full_versions = get_available_python_versions()
        matching_full = [v for v in full_versions if v.startswith(major_minor)]
        if matching_full:
            version_to_download = matching_full[0]
            return download_python_version(version_to_download)
        else:
            print(f"Py: Python {version} not available. Available: {', '.join(full_versions[:5])}")
            sys.exit(1)

    if not installed:
        print("Py: No Python versions installed. Downloading 3.13.12…")
        return download_python_version("3.13.12")

    version, binary_path = installed[0]
    print(f"Py: Using Python {version}")
    return binary_path


def fetch_command(version: Optional[str] = None, list_available: bool = False):
    """Handle the 'py fetch' command."""
    if list_available:
        print("Py: Available Python versions:")
        for v in get_available_python_versions():
            installed = any(
                v == inst_v or v.startswith(inst_v + ".")
                for inst_v, _ in get_installed_python_versions()
            )
            marker = " (installed)" if installed else ""
            print(f"  {v}{marker}")
        return

    if not version:
        print("Py: No version specified. Use 'py fetch <version>' or 'py fetch --available'")
        print("Examples:")
        print("  py fetch 3.14       Install Python 3.14")
        print("  py fetch 3.14.3     Install Python 3.14.3")
        print("  py fetch --available  List available versions")
        sys.exit(1)

    binary_path = download_python_version(version)
    print(f"Py: Python binary at: {binary_path}")


def versions_command():
    """Handle the 'py versions' command."""
    installed = get_installed_python_versions()

    if not installed:
        print("Py: No Python versions installed")
        print("Use 'py fetch <version>' to install one")
        return

    print(f"Py: {len(installed)} Python version(s) installed:")
    for version, path in installed:
        print(f"  {version:10s} {path}")
