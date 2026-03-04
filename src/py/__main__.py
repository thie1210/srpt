"""
Py - A PSF-owned, Python-written replacement for pip

This is the entry point for the Py CLI tool.
"""

import argparse
import sys
import os
import subprocess
from pathlib import Path
from typing import Optional, List
from py import __version__


def main():
    """Main entry point for the Py CLI."""
    parser = argparse.ArgumentParser(
        prog="py",
        description="A PSF-owned, Python-written replacement for pip — inspired by uv",
    )

    parser.add_argument(
        "command_or_script",
        nargs="?",
        help="Command to execute (repl, run, install, add, etc.) or path to a script",
    )

    parser.add_argument(
        "args",
        nargs=argparse.REMAINDER,
        help="Arguments for the command or script",
    )

    # Version information
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    parser.add_argument(
        "--with-version",
        dest="with_version",
        help="Python version to use (e.g., 3.14, 3.14.3)",
    )

    # Parse arguments
    args = parser.parse_args()

    # Logic for use case 1: "py" (no args) -> download/start repl
    with_version = getattr(args, "with_version", None)

    if not args.command_or_script:
        return run_repl(with_version)

    # Logic for use case 2: "py <script.py>" -> download/run script
    if args.command_or_script.endswith(".py") or Path(args.command_or_script).is_file():
        return run_script(args.command_or_script, args.args, with_version)

    # Handle specific commands
    if args.command_or_script == "run":
        if not args.args:
            print("Error: No script path provided")
            sys.exit(1)
        return run_script(args.args[0], args.args[1:], with_version)
    elif args.command_or_script == "install":
        return install_packages(args.args, with_version)
    elif args.command_or_script == "uninstall":
        return uninstall_packages(args.args)
    elif args.command_or_script == "list":
        return list_packages()
    elif args.command_or_script == "add":
        return add_packages(args.args)
    elif args.command_or_script == "repl":
        return run_repl(with_version)
    elif args.command_or_script == "fetch":
        return fetch_python(args.args)
    elif args.command_or_script == "versions":
        return list_versions()
    elif args.command_or_script == "status":
        show_cache = "--cache" in args.args or "-c" in args.args
        return show_status(show_cache)
    else:
        # If it's not a known command and not a file, it might be a script that doesn't exist yet
        # or we just default to helping the user
        print(f"Unknown command or script: {args.command_or_script}")
        parser.print_help()
        sys.exit(1)


def run_repl(with_version: Optional[str] = None):
    """Run the Python REPL with the latest stable version."""
    from py.fetcher import get_python_binary

    print("Py: Checking for latest stable Python…")
    binary_path = get_python_binary(with_version)

    # Setup environment to use .venv if it exists
    env = os.environ.copy()
    venv_dir = Path(".venv")
    if venv_dir.exists():
        # Add site-packages to PYTHONPATH
        if os.name == "posix":
            site_packages = list(venv_dir.glob("lib/python*/site-packages"))
        else:
            site_packages = [venv_dir / "Lib" / "site-packages"]

        if site_packages:
            current_pp = env.get("PYTHONPATH", "")
            new_pp = str(site_packages[0])
            env["PYTHONPATH"] = f"{new_pp}{os.pathsep}{current_pp}" if current_pp else new_pp
            print(f"Py: Using virtual environment at {venv_dir}")

    print(f"Py: Launching REPL ({binary_path})")
    try:
        subprocess.call([str(binary_path)], env=env)
    except KeyboardInterrupt:
        pass


def run_script(script_path, args, with_version: Optional[str] = None):
    """Run a Python script with the latest stable version."""
    from py.fetcher import get_python_binary

    script_path = Path(script_path)
    if not script_path.exists():
        print(f"Error: Script not found: {script_path}")
        sys.exit(1)

    print(f"Py: Checking for latest stable Python for {script_path}…")
    binary_path = get_python_binary(with_version)

    # Setup environment to use .venv if it exists
    env = os.environ.copy()
    venv_dir = Path(".venv")
    if venv_dir.exists():
        if os.name == "posix":
            site_packages = list(venv_dir.glob("lib/python*/site-packages"))
        else:
            site_packages = [venv_dir / "Lib" / "site-packages"]

        if site_packages:
            current_pp = env.get("PYTHONPATH", "")
            new_pp = str(site_packages[0])
            env["PYTHONPATH"] = f"{new_pp}{os.pathsep}{current_pp}" if current_pp else new_pp
            print(f"Py: Using virtual environment at {venv_dir}")

    # TODO: Check for PEP 723 inline metadata for dependencies

    cmd = [str(binary_path), str(script_path)] + args
    subprocess.call(cmd, env=env)


def install_packages(packages, with_version: Optional[str] = None):
    """Install packages."""
    if not packages:
        print("Error: No packages provided")
        sys.exit(1)

    if with_version:
        print(f"Py: Note: --with-version flag specified but install currently uses system Python")
        print(f"Py: Python version management will be integrated in a future update")

    import asyncio
    from py.install_workflow import install_command
    from py.pypi import PackageNotFoundError

    print(f"Py: Installing packages: {packages}")
    try:
        asyncio.run(install_command(packages))
    except PackageNotFoundError as e:
        print(f"\nPy: {e}")
        sys.exit(1)
    except ValueError as e:
        # Handle other value errors
        print(f"\nPy: Error: {e}")
        sys.exit(1)


def uninstall_packages(packages):
    """Uninstall packages."""
    if not packages:
        print("Error: No packages provided")
        sys.exit(1)

    from py.uninstall import uninstall_command
    import os

    venv_dir = Path(".venv")
    if not venv_dir.exists():
        print(f"Py: No virtual environment found at {venv_dir}")
        sys.exit(1)

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

    uninstall_command(packages, site_packages)


def list_packages():
    """List installed packages."""
    from py.uninstall import list_command
    import os

    venv_dir = Path(".venv")
    if not venv_dir.exists():
        print(f"Py: No virtual environment found at {venv_dir}")
        print("Py: Install packages first with 'py install <package>'")
        return

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

    list_command(site_packages)


def add_packages(packages):
    """Add packages to project."""
    if not packages:
        print("Error: No packages provided")
        sys.exit(1)

    print(f"Py: Adding packages: {packages}")
    # TODO: Implement project package addition logic
    print("Note: Package addition is not yet implemented.")


def fetch_python(args: List[str]):
    """Download and install Python versions."""
    from py.fetcher import fetch_command

    list_available = "--available" in args or "-a" in args
    version = None

    for arg in args:
        if arg not in ("--available", "-a"):
            version = arg
            break

    fetch_command(version, list_available)


def list_versions():
    """List installed Python versions."""
    from py.fetcher import versions_command

    versions_command()


def show_status(show_cache: bool = False):
    """Show project and environment status."""
    from py.status import status_command

    status_command(show_cache)


if __name__ == "__main__":
    main()
