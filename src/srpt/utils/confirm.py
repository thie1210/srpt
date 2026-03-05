"""
Confirmation utilities for safe-by-default operations.

All mutating operations are dry-run by default.
Users must explicitly use --apply to execute changes.
"""

from typing import Optional


def dry_run_header() -> None:
    """Print standard dry-run header."""
    print("\nDRY RUN - No changes will be made\n")


def confirm_apply(apply: bool = False) -> bool:
    """
    Check if --apply flag is set.

    Args:
        apply: True if --apply flag was provided

    Returns:
        True if operation should proceed, False if dry-run
    """
    return apply


def format_dry_run_message(message: str) -> str:
    """
    Format a message for dry-run output.

    Args:
        message: The message to format

    Returns:
        Formatted message with dry-run context
    """
    return f"Would {message}"


def format_apply_message(message: str) -> str:
    """
    Format a message for apply output.

    Args:
        message: The message to format

    Returns:
        Formatted message with apply context
    """
    return message


def print_action(action: str, dry_run: bool = True) -> None:
    """
    Print an action message with appropriate context.

    Args:
        action: The action being performed
        dry_run: True if this is a dry-run
    """
    if dry_run:
        print(f"  Would {action}")
    else:
        print(f"  {action}")


def print_success(message: str, dry_run: bool = True) -> None:
    """
    Print a success message with appropriate symbol.

    Args:
        message: The success message
        dry_run: True if this is a dry-run
    """
    symbol = "✓" if not dry_run else "○"
    print(f"  {symbol} {message}")


def print_warning(message: str) -> None:
    """
    Print a warning message.

    Args:
        message: The warning message
    """
    print(f"  ⚠ {message}")


def print_error(message: str) -> None:
    """
    Print an error message.

    Args:
        message: The error message
    """
    print(f"  ✗ {message}")
