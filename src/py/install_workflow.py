import asyncio
from pathlib import Path
from typing import List
from py.downloader import Downloader
from py.pypi import PyPIClient
from py.resolver import resolve


async def install_command(packages: List[str]):
    """Installs a list of packages."""
    from py.installed import is_installed, get_installed_version

    # 0. Determine site-packages location
    import os

    venv_dir = Path(".venv")

    if os.name == "posix":
        potential_libs = list(venv_dir.glob("lib/python*/site-packages"))
        if potential_libs:
            site_packages = potential_libs[0]
        else:
            import sys

            v = f"{sys.version_info.major}.{sys.version_info.minor}"
            site_packages = venv_dir / "lib" / f"python{v}" / "site-packages"
    else:
        site_packages = venv_dir / "Lib" / "site-packages"

    # Check if packages are already installed
    packages_to_install = []
    for pkg in packages:
        existing_version = get_installed_version(pkg, site_packages)
        if existing_version:
            print(f"Py: {pkg}=={existing_version} is already installed")
            print(f"Py: Use 'py install --upgrade {pkg}' to upgrade")
        else:
            packages_to_install.append(pkg)

    if not packages_to_install:
        print("Py: All packages are already installed")
        return

    # 1. Resolve dependencies
    # Try parallel resolver first, fall back to sequential
    try:
        from py.parallel_resolver import parallel_resolve

        candidates = await parallel_resolve(packages_to_install)
    except Exception as e:
        print(f"Py: Parallel resolver failed: {e}")
        print("Py: Using standard resolver…")
        candidates = await resolve(packages_to_install)

    # Filter out already-installed packages (including dependencies)
    from packaging.version import parse as parse_version

    candidates_to_install = []
    for c in candidates:
        existing_version = get_installed_version(c.name, site_packages)
        if existing_version:
            try:
                if parse_version(existing_version) == parse_version(str(c.version)):
                    print(f"Py: {c.name}=={c.version} is already installed (skipping)")
                    continue
            except Exception:
                # Fall back to string comparison
                if existing_version == str(c.version):
                    print(f"Py: {c.name}=={c.version} is already installed (skipping)")
                    continue

        candidates_to_install.append(c)

    if not candidates_to_install:
        print("Py: All packages and dependencies are already installed")
        return

    dependencies = [
        {
            "name": c.name,
            "version": str(c.version),
            "url": c.url,
            "sha256": c.hashes.get("sha256") if c.hashes else None,
        }
        for c in candidates_to_install
    ]

    # 2. Create target directory (managed venv)
    # We'll use a .venv directory in the current working directory
    venv_dir = Path(".venv")
    if not venv_dir.exists():
        print(f"Py: Creating virtual environment in {venv_dir}…")
        import venv

        # Create without pip as we'll manage packages ourselves
        venv.create(venv_dir, with_pip=False)

    # Identify site-packages directory
    import os

    if os.name == "posix":
        # Check standard paths
        potential_libs = list(venv_dir.glob("lib/python*/site-packages"))
        if potential_libs:
            site_packages = potential_libs[0]
        else:
            # Fallback for fresh venv
            import sys

            v = f"{sys.version_info.major}.{sys.version_info.minor}"
            site_packages = venv_dir / "lib" / f"python{v}" / "site-packages"
    else:
        # Windows
        site_packages = venv_dir / "Lib" / "site-packages"

    target_dir = site_packages
    target_dir.mkdir(parents=True, exist_ok=True)

    # 3. Download wheels
    cache_dir = Path.home() / ".local" / "share" / "py" / "cache"
    async with Downloader(cache_dir) as downloader:
        wheel_paths = await downloader.download_packages(dependencies)

    # 4. Install wheels in parallel
    if os.name == "posix":
        venv_python = venv_dir / "bin" / "python3"
    else:
        venv_python = venv_dir / "Scripts" / "python.exe"

    from py.installer_utils import install_wheels_parallel

    results = await install_wheels_parallel(wheel_paths, target_dir, venv_python)

    failures = [(name, error) for name, success, error in results if not success]
    if failures:
        print(f"Py: Failed to install {len(failures)} package(s):")
        for name, error in failures:
            print(f"  - {name}: {error}")
        raise RuntimeError(f"Installation failed for {len(failures)} package(s)")

    installed_count = sum(1 for _, success, _ in results if success)
    print(f"Py: Successfully installed {installed_count} package(s) into {target_dir}")
