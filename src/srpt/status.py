"""
Status command - Dashboard for project and environment health.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional


def format_size(bytes_size: int) -> str:
    """Format bytes to human-readable size."""
    if bytes_size < 1024:
        return f"{bytes_size} B"
    elif bytes_size < 1024 * 1024:
        return f"{bytes_size / 1024:.1f} KB"
    else:
        return f"{bytes_size / (1024 * 1024):.1f} MB"


def get_project_status() -> Dict:
    """Get project status (pyproject.toml and .venv)."""
    cwd = Path.cwd()
    pyproject_path = cwd / "pyproject.toml"
    venv_path = cwd / ".venv"

    has_pyproject = pyproject_path.exists()
    has_venv = venv_path.exists()

    project_name = None
    if has_pyproject:
        try:
            import tomli

            with open(pyproject_path, "rb") as f:
                data = tomli.load(f)
                project_name = data.get("project", {}).get("name")
        except Exception:
            pass

    venv_python_version = None
    if has_venv:
        if os.name == "posix":
            potential_libs = list(venv_path.glob("lib/python*/site-packages"))
            if potential_libs:
                lib_path = potential_libs[0]
                version_match = lib_path.name
                if "python" in version_match:
                    venv_python_version = version_match.replace("python", "").strip()
        else:
            venv_python_version = None

    return {
        "has_pyproject": has_pyproject,
        "project_name": project_name,
        "has_venv": has_venv,
        "venv_python_version": venv_python_version,
        "cwd": cwd,
    }


def get_python_status() -> Dict:
    """Get Python environment status."""
    from srpt.fetcher import get_installed_python_versions

    installed = get_installed_python_versions()

    if installed:
        latest_version, latest_path = installed[0]
    else:
        latest_version = None
        latest_path = None

    return {
        "installed_count": len(installed),
        "latest_version": latest_version,
        "latest_path": latest_path,
    }


def get_package_status() -> Dict:
    """Get installed packages in .venv."""
    venv_dir = Path(".venv")

    if not venv_dir.exists():
        return {
            "has_venv": False,
            "installed_count": 0,
            "installed_packages": [],
        }

    if os.name == "posix":
        potential_libs = list(venv_dir.glob("lib/python*/site-packages"))
    else:
        potential_libs = [venv_dir / "Lib" / "site-packages"]

    if not potential_libs:
        return {
            "has_venv": True,
            "installed_count": 0,
            "installed_packages": [],
        }

    site_packages = potential_libs[0]

    from srpt.installed import list_installed_packages

    packages = list_installed_packages(site_packages)

    return {
        "has_venv": True,
        "installed_count": len(packages),
        "installed_packages": [(p["name"], p["version"]) for p in packages],
    }


def get_tracked_dependencies() -> Dict:
    """Get dependencies from pyproject.toml."""
    pyproject_path = Path("pyproject.toml")

    if not pyproject_path.exists():
        return {
            "has_pyproject": False,
            "dependencies": [],
        }

    try:
        import tomli

        with open(pyproject_path, "rb") as f:
            data = tomli.load(f)

        deps = data.get("project", {}).get("dependencies", [])

        parsed_deps = []
        from packaging.requirements import Requirement

        for dep_str in deps:
            try:
                req = Requirement(dep_str)
                parsed_deps.append(req.name)
            except Exception:
                parsed_deps.append(dep_str.split()[0])

        return {
            "has_pyproject": True,
            "dependencies": parsed_deps,
        }
    except Exception as e:
        return {
            "has_pyproject": True,
            "dependencies": [],
            "error": str(e),
        }


def get_dependency_sync_status() -> Dict:
    """Compare tracked dependencies vs installed packages."""
    tracked = get_tracked_dependencies()
    installed = get_package_status()

    if not tracked["has_pyproject"]:
        return {
            "mode": "manual",
            "has_pyproject": False,
            "tracked_count": 0,
            "tracked_packages": [],
            "installed_count": installed["installed_count"],
            "installed_packages": installed["installed_packages"],
            "is_sync": None,
        }

    tracked_packages = tracked["dependencies"]
    installed_packages = [name for name, version in installed["installed_packages"]]

    tracked_set = set(name.lower() for name in tracked_packages)
    installed_set = set(name.lower() for name in installed_packages)

    missing = sorted(tracked_set - installed_set)
    extra = sorted(installed_set - tracked_set)

    is_sync = len(missing) == 0 and len(extra) == 0

    return {
        "mode": "tracked",
        "has_pyproject": True,
        "tracked_count": len(tracked_packages),
        "tracked_packages": tracked_packages,
        "installed_count": len(installed_packages),
        "installed_packages": installed["installed_packages"],
        "missing": missing,
        "extra": extra,
        "is_sync": is_sync,
    }


def get_cache_stats() -> Dict:
    """Get statistics from both cache databases."""
    from srpt.cache import ResolutionCache
    from srpt.metadata_cache import MetadataCache

    resolution_cache = ResolutionCache()
    metadata_cache = MetadataCache()

    res_stats = resolution_cache.stats()
    meta_stats = metadata_cache.get_stats()

    total_size = res_stats.get("db_size_bytes", 0) + meta_stats.get("db_size_bytes", 0)

    return {
        "resolution": res_stats,
        "metadata": meta_stats,
        "total_size_bytes": total_size,
    }


def get_health_summary() -> Dict:
    """Get quick health summary for status command."""
    import asyncio
    from srpt.health import health_check

    try:
        # Run health check synchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        health = loop.run_until_complete(health_check(Path.cwd(), full=False))
        loop.close()

        return {
            "warnings": health.get("warnings", 0),
            "errors": health.get("errors", 0),
            "vulnerabilities": health.get("security", {}).get("count", 0),
            "outdated": len(health.get("dependencies", {}).get("outdated", [])),
        }
    except Exception:
        return {
            "warnings": 0,
            "errors": 0,
            "vulnerabilities": 0,
            "outdated": 0,
        }


def format_status(show_cache: bool = False):
    """Format and print status dashboard."""
    from rich.console import Console
    from rich.text import Text

    console = Console()

    project = get_project_status()
    python = get_python_status()
    packages = get_package_status()
    deps = get_dependency_sync_status()

    console.print("PROJECT", style="bold cyan")
    if project["has_pyproject"]:
        if project["project_name"]:
            console.print(f"  ✓ pyproject.toml ({project['project_name']})")
        else:
            console.print("  ✓ pyproject.toml found")
    else:
        console.print("  ℹ No pyproject.toml (manual package management)")

    if project["has_venv"]:
        if project["venv_python_version"]:
            console.print(f"  ✓ .venv (Python {project['venv_python_version']})")
        else:
            console.print("  ✓ .venv exists")
    else:
        console.print("  ✗ No .venv found", style="yellow")
        console.print("  → Run 'py install <pkg>' to create one", style="dim")
    console.print()

    console.print("PYTHON", style="bold cyan")
    if python["latest_version"]:
        console.print(f"  Version: {python['latest_version']}")
        console.print(
            f"  → Run 'py versions' to see all {python['installed_count']} installed", style="dim"
        )
        console.print("  → Run 'py fetch <version>' to install another", style="dim")
    else:
        console.print("  ✗ No Python versions managed", style="yellow")
        console.print("  → Run 'py fetch 3.14' to install Python", style="dim")
    console.print()

    console.print("PACKAGES", style="bold cyan")
    if packages["has_venv"]:
        count = packages["installed_count"]
        console.print(f"  Installed: {count}")
        console.print("  → Run 'py list' for details", style="dim")
    else:
        console.print("  ✗ No packages installed (no .venv)", style="yellow")
    console.print()

    console.print("DEPENDENCIES", style="bold cyan")
    if deps["mode"] == "manual":
        console.print("  Mode: Manual (no pyproject.toml)", style="yellow")
        console.print(f"  Installed: {deps['installed_count']} in .venv")
        console.print()
        console.print("  To TRACK dependencies for your project:", style="dim")
        console.print("    → Run 'py init' to create pyproject.toml (coming soon)", style="dim")
        console.print("    → Then use 'py add <pkg>' to track packages", style="dim")
        console.print()
        console.print("  Or continue manually:", style="dim")
        console.print("    → Run 'py install <pkg>' (not tracked)", style="dim")
    else:
        tracked_str = ", ".join(deps["tracked_packages"])
        if len(tracked_str) > 50:
            tracked_str = tracked_str[:47] + "..."

        console.print(f"  Mode: Tracked")
        console.print(f"  Tracked: {deps['tracked_count']} ({tracked_str})")
        console.print(f"  Installed: {deps['installed_count']}")

        if deps["is_sync"]:
            console.print("  Status: ✓ Synchronized", style="green")
        else:
            console.print("  Status: ⚠ Out of sync", style="yellow")

            if deps["missing"]:
                missing_str = ", ".join(deps["missing"])
                if len(missing_str) > 50:
                    missing_str = missing_str[:47] + "..."
                console.print(f"    Missing: {missing_str}")

            if deps["extra"]:
                extra_str = ", ".join(deps["extra"])
                if len(extra_str) > 50:
                    extra_str = extra_str[:47] + "..."
                console.print(f"    Extra: {extra_str}")

            console.print()
            console.print("  TRACKING workflow (recommended):", style="dim")
            if deps["missing"]:
                console.print(
                    f"    → Run 'py install {deps['missing'][0]}' to install tracked package",
                    style="dim",
                )
            if deps["extra"]:
                console.print(
                    f"    → Run 'py remove {deps['extra'][0]}' to stop tracking", style="dim"
                )

            console.print()
            console.print("  MANUAL workflow (advanced):", style="dim")
            console.print("    → Run 'py install <pkg>' (not tracked)", style="dim")
            console.print("    → Run 'py uninstall <pkg>' (from .venv only)", style="dim")

            console.print()
            console.print("  Or sync automatically:", style="dim")
            console.print("    → Run 'py sync' to synchronize", style="dim")
    console.print()

    # Health summary
    console.print("HEALTH", style="bold cyan")
    health = get_health_summary()

    if health["vulnerabilities"] > 0:
        console.print(f"  ✗ Vulnerabilities: {health['vulnerabilities']} found", style="red")
        console.print("    → Run 'py audit' for details", style="dim")
    else:
        console.print("  ✓ Vulnerabilities: 0 found", style="green")

    if health["outdated"] > 0:
        console.print(f"  ⚠ Outdated: {health['outdated']} packages", style="yellow")
        console.print("    → Run 'py update' to update", style="dim")
    else:
        console.print("  ✓ All packages up to date", style="green")

    if health["warnings"] > 0 or health["errors"] > 0:
        console.print(
            f"  ⚠ {health['warnings']} warnings, {health['errors']} errors", style="yellow"
        )
        console.print("    → Run 'py health' for full report", style="dim")
    else:
        console.print("  ✓ All checks passed", style="green")

    console.print()

    if show_cache:
        cache = get_cache_stats()

        console.print("CACHES", style="bold cyan")

        res_count = cache["resolution"].get("active_entries", 0)
        console.print(f"  Resolution: {res_count} cached → 24hr TTL")

        meta_count = cache["metadata"].get("cached_packages", 0)
        console.print(f"  Metadata: {meta_count} cached → 7 day TTL")

        learning_count = cache["metadata"].get("dependency_edges", 0)
        console.print(f"  Learning: {learning_count} relationships")

        total_size = format_size(cache["total_size_bytes"])
        console.print(f"  Size: {total_size}")

        cache_dir = Path.home() / ".local" / "share" / "py" / "cache"
        console.print(f"  Location: {cache_dir}")
        console.print()

    console.print("QUICK REFERENCE", style="bold cyan")

    if deps["mode"] == "manual":
        console.print("  py install <pkg>      Install package manually", style="dim")
        console.print("  py list               Show installed packages", style="dim")
    else:
        console.print("  py add <pkg>          Track + install (recommended)", style="dim")
        console.print("  py remove <pkg>       Untrack package", style="dim")
        console.print("  py install            Install all tracked dependencies", style="dim")

    console.print("  py fetch <version>    Install Python version", style="dim")
    console.print("  py versions           List Python versions", style="dim")
    console.print("  py --help             Show all commands", style="dim")


def status_command(show_cache: bool = False):
    """Main entry point for status command."""
    format_status(show_cache)
