"""
Package update functionality.

Handles both package updates and self-updates via --self flag.
"""

import asyncio
from pathlib import Path
from typing import List, Optional

from .self_update import self_update as do_self_update
from .utils.confirm import dry_run_header


async def update_packages(
    project_root: Path,
    packages: Optional[List[str]] = None,
    dry_run: bool = True,
    update_all: bool = False,
    security_only: bool = False,
) -> bool:
    """
    Update packages to latest compatible versions.

    Args:
        project_root: Path to project root
        packages: Specific packages to update (None = all)
        dry_run: If True, only show what would be done
        update_all: If True, ignore constraints and update all
        security_only: If True, only security updates

    Returns:
        True if updates succeeded (or would succeed in dry-run)
    """
    # TODO: Implement package updates in next phase
    if dry_run:
        dry_run_header()

    print("Package updates not yet implemented")
    print("  → Use 'srpt update --self' to update srpt itself")
    return False


async def update(
    project_root: Path,
    update_self: bool = False,
    packages: Optional[List[str]] = None,
    dry_run: bool = True,
    update_all: bool = False,
    security_only: bool = False,
    check_only: bool = False,
    target_version: Optional[str] = None,
) -> bool:
    """
    Main update command router.

    Routes to either self-update or package update based on flags.

    Args:
        project_root: Path to project root
        update_self: If True, update srpt itself
        packages: Specific packages to update
        dry_run: If True, only show what would be done
        update_all: If True, ignore constraints
        security_only: If True, only security updates
        check_only: If True, only check for updates (with --self)
        target_version: Specific version to update to (with --self)

    Returns:
        True if update succeeded
    """
    if update_self:
        # Self-update
        return await do_self_update(
            dry_run=dry_run, check_only=check_only, target_version=target_version
        )
    else:
        # Package update
        return await update_packages(
            project_root=project_root,
            packages=packages,
            dry_run=dry_run,
            update_all=update_all,
            security_only=security_only,
        )
