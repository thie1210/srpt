import asyncio
from pathlib import Path
from typing import List
from srpt.downloader import Downloader
from srpt.pypi import PyPIClient
from srpt.resolver import resolve


async def install_command(packages: List[str]):
    """Installs a list of packages."""
    from srpt.installed import is_installed, get_installed_version

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
        # Parse package name and version constraint
        from packaging.requirements import Requirement

        try:
            req = Requirement(pkg)
            pkg_name = req.name
        except Exception:
            pkg_name = (
                pkg.split("==")[0]
                .split("~=")[0]
                .split(">=")[0]
                .split("<=")[0]
                .split(">")[0]
                .split("<")[0]
            )

        existing_version = get_installed_version(pkg_name, site_packages)
        if existing_version:
            print(f"srpt: {pkg_name}=={existing_version} is already installed")
            # Don't skip - let the resolver determine if we need to upgrade
            packages_to_install.append(pkg)
        else:
            packages_to_install.append(pkg)

    if not packages_to_install:
        print("srpt: All packages are already installed")
        return

    # 1. Resolve dependencies
    # Try parallel resolver first, fall back to sequential
    try:
        from srpt.parallel_resolver import parallel_resolve

        candidates = await parallel_resolve(packages_to_install)
    except Exception as e:
        print(f"srpt: Parallel resolver failed: {e}")
        print("srpt: Using standard resolver…")
        candidates = await resolve(packages_to_install)

    # Filter out already-installed packages (including dependencies)
    # If a different version is installed, mark for uninstall first
    from packaging.version import parse as parse_version
    from srpt.uninstall import uninstall_package

    packages_to_uninstall = []
    candidates_to_install = []

    for c in candidates:
        existing_version = get_installed_version(c.name, site_packages)
        if existing_version:
            try:
                existing_ver = parse_version(existing_version)
                target_ver = parse_version(str(c.version))

                if existing_ver == target_ver:
                    print(f"srpt: {c.name}=={c.version} is already installed (skipping)")
                    continue
                else:
                    # Different version installed - need to uninstall first
                    print(f"srpt: Changing {c.name} from {existing_version} to {c.version}")
                    packages_to_uninstall.append(c.name)
                    candidates_to_install.append(c)
            except Exception:
                # Fall back to string comparison
                if existing_version == str(c.version):
                    print(f"srpt: {c.name}=={c.version} is already installed (skipping)")
                    continue
                else:
                    # Different version - uninstall first
                    print(f"srpt: Changing {c.name} from {existing_version} to {c.version}")
                    packages_to_uninstall.append(c.name)
                    candidates_to_install.append(c)
        else:
            candidates_to_install.append(c)

    # Uninstall old versions first
    if packages_to_uninstall:
        print(f"srpt: Uninstalling {len(packages_to_uninstall)} old package version(s)…")
        for pkg_name in packages_to_uninstall:
            uninstall_package(pkg_name, site_packages)

    if not candidates_to_install:
        print("srpt: All packages and dependencies are already installed")
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
        print(f"srpt: Creating virtual environment in {venv_dir}…")
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
    cache_dir = Path.home() / ".local" / "share" / "srpt" / "cache"
    async with Downloader(cache_dir) as downloader:
        wheel_paths = await downloader.download_packages(dependencies)

    # 4. Install wheels in parallel
    if os.name == "posix":
        venv_python = venv_dir / "bin" / "python3"
    else:
        venv_python = venv_dir / "Scripts" / "python.exe"

    from srpt.installer_utils import install_wheels_parallel

    results = await install_wheels_parallel(wheel_paths, target_dir, venv_python)

    failures = [(name, error) for name, success, error in results if not success]
    if failures:
        print(f"srpt: Failed to install {len(failures)} package(s):")
        for name, error in failures:
            print(f"  - {name}: {error}")
        raise RuntimeError(f"Installation failed for {len(failures)} package(s)")

    installed_count = sum(1 for _, success, _ in results if success)
    print(f"srpt: Successfully installed {installed_count} package(s) into {target_dir}")
