"""
srpt (serpent) - A modern Python package manager

This is the entry point for the srpt CLI tool.
"""

import argparse
import sys
import os
import subprocess
from pathlib import Path
from typing import Optional, List
from srpt import __version__


def main():
    """Main entry point for the srpt CLI."""
    parser = argparse.ArgumentParser(
        prog="srpt",
        description="A modern Python package manager — inspired by uv",
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

    # Logic for use case 1: "srpt" (no args) -> download/start repl
    with_version = getattr(args, "with_version", None)

    if not args.command_or_script:
        return run_repl(with_version)

    # Logic for use case 2: "srpt <script.py>" -> download/run script
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
    elif args.command_or_script == "update":
        return update_command(args.args)
    elif args.command_or_script == "audit":
        return audit_command(args.args)
    elif args.command_or_script == "health":
        return health_command(args.args)
    elif args.command_or_script == "rebuild":
        return rebuild_command(args.args)
    else:
        # If it's not a known command and not a file, it might be a script that doesn't exist yet
        # or we just default to helping the user
        print(f"Unknown command or script: {args.command_or_script}")
        parser.print_help()
        sys.exit(1)


def run_repl(with_version: Optional[str] = None):
    """Run the Python REPL with the latest stable version."""
    from srpt.fetcher import get_python_binary

    print("srpt: Checking for latest stable Python…")
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
            print(f"srpt: Using virtual environment at {venv_dir}")

    print(f"srpt: Launching REPL ({binary_path})")
    try:
        subprocess.call([str(binary_path)], env=env)
    except KeyboardInterrupt:
        pass


def run_script(script_path, args, with_version: Optional[str] = None):
    """Run a Python script with the latest stable version."""
    from srpt.fetcher import get_python_binary

    script_path = Path(script_path)
    if not script_path.exists():
        print(f"Error: Script not found: {script_path}")
        sys.exit(1)

    print(f"srpt: Checking for latest stable Python for {script_path}…")
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
            print(f"srpt: Using virtual environment at {venv_dir}")

    # TODO: Check for PEP 723 inline metadata for dependencies

    cmd = [str(binary_path), str(script_path)] + args
    subprocess.call(cmd, env=env)


def install_packages(packages, with_version: Optional[str] = None):
    """Install packages."""
    if not packages:
        print("Error: No packages provided")
        sys.exit(1)

    if with_version:
        print(f"srpt: Note: --with-version flag specified but install currently uses system Python")
        print(f"srpt: Python version management will be integrated in a future update")

    import asyncio
    from srpt.install_workflow import install_command
    from srpt.pypi import PackageNotFoundError

    print(f"srpt: Installing packages: {packages}")
    try:
        asyncio.run(install_command(packages))
    except PackageNotFoundError as e:
        print(f"\nsrpt: {e}")
        sys.exit(1)
    except ValueError as e:
        # Handle other value errors
        print(f"\nsrpt: Error: {e}")
        sys.exit(1)


def uninstall_packages(packages):
    """Uninstall packages."""
    if not packages:
        print("Error: No packages provided")
        sys.exit(1)

    from srpt.uninstall import uninstall_command
    import os

    venv_dir = Path(".venv")
    if not venv_dir.exists():
        print(f"srpt: No virtual environment found at {venv_dir}")
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
    from srpt.uninstall import list_command
    import os

    venv_dir = Path(".venv")
    if not venv_dir.exists():
        print(f"srpt: No virtual environment found at {venv_dir}")
        print("srpt: Install packages first with 'srpt install <package>'")
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

    print(f"srpt: Adding packages: {packages}")
    # TODO: Implement project package addition logic
    print("Note: Package addition is not yet implemented.")


def fetch_python(args: List[str]):
    """Download and install Python versions."""
    from srpt.fetcher import fetch_command

    list_available = "--available" in args or "-a" in args
    version = None

    for arg in args:
        if arg not in ("--available", "-a"):
            version = arg
            break

    fetch_command(version, list_available)


def list_versions():
    """List installed Python versions."""
    from srpt.fetcher import versions_command

    versions_command()


def show_status(show_cache: bool = False):
    """Show project and environment status."""
    from srpt.status import status_command

    status_command(show_cache)


def update_command(args: List[str]):
    """Update packages or srpt itself."""
    import asyncio

    # Parse update-specific arguments
    update_self = "--self" in args
    apply = "--apply" in args
    check_only = "--check" in args
    update_all = "--all" in args
    security_only = "--security" in args

    # Get target version if specified
    target_version = None
    for i, arg in enumerate(args):
        if arg == "--version" and i + 1 < len(args):
            target_version = args[i + 1]
            break

    # Get packages to update (non-flag arguments)
    packages = [arg for arg in args if not arg.startswith("--") and arg != target_version]

    # Import and run update
    from srpt.update import update

    asyncio.run(
        update(
            project_root=Path.cwd(),
            update_self=update_self,
            packages=packages if packages else None,
            dry_run=not apply,
            update_all=update_all,
            security_only=security_only,
            check_only=check_only,
            target_version=target_version,
        )
    )


def audit_command(args: List[str]):
    """Run security audit on installed packages."""
    import asyncio

    # Parse audit-specific arguments
    fix = "--fix" in args
    json_output = "--json" in args

    # Get CVEs to ignore
    ignore_cves = []
    for i, arg in enumerate(args):
        if arg == "--ignore" and i + 1 < len(args):
            # Get all following arguments until next flag
            for j in range(i + 1, len(args)):
                if args[j].startswith("--"):
                    break
                ignore_cves.append(args[j])
            break

    # Import and run audit
    from srpt.audit import run_audit

    asyncio.run(
        run_audit(
            project_root=Path.cwd(),
            fix=fix,
            ignore_cves=ignore_cves if ignore_cves else None,
            json_output=json_output,
        )
    )


def health_command(args: List[str]):
    """Run comprehensive health check."""
    import asyncio
    import json

    # Parse health-specific arguments
    full = "--full" in args
    json_output = "--json" in args
    fix = "--fix" in args

    # Import and run health check
    from srpt.health import health_check, format_health_report

    health = asyncio.run(health_check(project_root=Path.cwd(), full=full))

    if json_output:
        print(json.dumps(health, indent=2))
    else:
        format_health_report(health, full=full)

    # TODO: Implement --fix
    if fix:
        print("\n  Auto-fix not yet implemented")


def rebuild_command(args: List[str]):
    """Rebuild project with a different Python version."""
    from srpt.rebuild import rebuild_project

    # Parse rebuild-specific arguments
    target_version = None
    apply = "--apply" in args
    restore = "--restore" in args
    list_backups = "--list-backups" in args

    # Get target version if specified
    for i, arg in enumerate(args):
        if arg == "--with-version" and i + 1 < len(args):
            target_version = args[i + 1]
            break

    # Run rebuild
    success = rebuild_project(
        project_root=Path.cwd(),
        target_version=target_version,
        dry_run=not apply,
        restore=restore,
        list_backups=list_backups,
    )

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
