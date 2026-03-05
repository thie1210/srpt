"""
Version constraint parsing and resolution.

Implements Smart Hybrid approach for determining updatable versions:
- Pinned (==): No update
- Upper bound (<, <=): Respect it
- >= only: Update to latest
- ~=: Compatible release
- No constraint: Latest
"""

from typing import Optional, List
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.version import Version


def parse_constraint(constraint_string: str) -> Requirement:
    """
    Parse a PEP 508 constraint string.

    Args:
        constraint_string: The constraint string (e.g., "django>=3.2,<4.0")

    Returns:
        A Requirement object

    Example:
        >>> req = parse_constraint("django>=3.2,<4.0")
        >>> req.name
        'django'
        >>> str(req.specifier)
        '>=3.2,<4.0'
    """
    return Requirement(constraint_string)


def is_pinned(requirement: Requirement) -> bool:
    """
    Check if a requirement is pinned to an exact version.

    Args:
        requirement: The requirement to check

    Returns:
        True if pinned with == operator
    """
    for spec in requirement.specifier:
        if spec.operator == "==":
            return True
    return False


def has_upper_bound(requirement: Requirement) -> bool:
    """
    Check if a requirement has an upper bound.

    Args:
        requirement: The requirement to check

    Returns:
        True if has < or <= operator
    """
    for spec in requirement.specifier:
        if spec.operator in ("<", "<="):
            return True
    return False


def is_greater_equal_only(requirement: Requirement) -> bool:
    """
    Check if a requirement only has >= operators.

    Args:
        requirement: The requirement to check

    Returns:
        True if only >= operators present
    """
    has_ge = False
    for spec in requirement.specifier:
        if spec.operator == ">=":
            has_ge = True
        elif spec.operator not in (">",):  # Allow > as well
            return False
    return has_ge


def is_compatible_release(requirement: Requirement) -> bool:
    """
    Check if a requirement uses compatible release operator.

    Args:
        requirement: The requirement to check

    Returns:
        True if uses ~= operator
    """
    for spec in requirement.specifier:
        if spec.operator == "~=":
            return True
    return False


def get_updatable_version(
    package_name: str, current_version: str, constraint: str, available_versions: List[str]
) -> Optional[str]:
    """
    Determine the latest updatable version based on constraint.

    Smart Hybrid approach:
    - Pinned (==): No update (return None)
    - Upper bound (<, <=): Find latest within bounds
    - >= only: Return latest available
    - ~=: Find latest compatible release
    - No constraint: Return latest available

    Args:
        package_name: Name of the package
        current_version: Currently installed version
        constraint: Version constraint string
        available_versions: List of all available versions (sorted oldest to newest)

    Returns:
        The latest updatable version, or None if no update allowed

    Example:
        >>> versions = ["3.2.18", "3.2.19", "4.0.0", "4.2.11"]
        >>> get_updatable_version("django", "3.2.18", ">=3.2,<4.0", versions)
        '3.2.19'
        >>> get_updatable_version("django", "3.2.18", "==3.2.18", versions)
        None
        >>> get_updatable_version("django", "3.2.18", ">=3.2", versions)
        '4.2.11'
    """
    if not constraint:
        # No constraint - return latest
        if available_versions:
            latest = available_versions[-1]
            if latest != current_version:
                return latest
        return None

    try:
        requirement = parse_constraint(constraint)
    except Exception:
        # Invalid constraint - be safe, no update
        return None

    # Rule 1: Pinned - no update
    if is_pinned(requirement):
        return None

    # Rule 2: Upper bound - respect it
    if has_upper_bound(requirement):
        # Find latest version that satisfies constraint
        for version in reversed(available_versions):
            if version in requirement.specifier and version != current_version:
                return version
        return None

    # Rule 3: >= only - update to latest
    if is_greater_equal_only(requirement):
        # Find latest version that satisfies constraint
        for version in reversed(available_versions):
            if version in requirement.specifier and version != current_version:
                return version
        return None

    # Rule 4: ~= - compatible release
    if is_compatible_release(requirement):
        # Find latest version that satisfies constraint
        for version in reversed(available_versions):
            if version in requirement.specifier and version != current_version:
                return version
        return None

    # Rule 5: Default - find any version that satisfies constraint
    for version in reversed(available_versions):
        if version in requirement.specifier and version != current_version:
            return version

    return None


def get_constraint_type(constraint: str) -> str:
    """
    Get a human-readable description of the constraint type.

    Args:
        constraint: The constraint string

    Returns:
        Description like "pinned", "upper bound", ">= only", etc.
    """
    if not constraint:
        return "no constraint"

    try:
        requirement = parse_constraint(constraint)
    except Exception:
        return "invalid"

    if is_pinned(requirement):
        return "pinned"
    if has_upper_bound(requirement):
        return "upper bound"
    if is_greater_equal_only(requirement):
        return "minimum version"
    if is_compatible_release(requirement):
        return "compatible release"

    return "version range"


def format_constraint_info(
    constraint: str, current: str, latest: str, updatable: Optional[str]
) -> str:
    """
    Format constraint information for display.

    Args:
        constraint: The constraint string
        current: Current version
        latest: Latest available version
        updatable: Updatable version (or None)

    Returns:
        Formatted string for display
    """
    constraint_type = get_constraint_type(constraint)

    if updatable is None:
        if constraint_type == "pinned":
            return f"{current} (pinned with ==)"
        elif constraint_type == "upper bound":
            return f"{current} (constrained)"
        else:
            return f"{current} (no update available)"
    else:
        if constraint:
            return f"{current} → {updatable} (within {constraint})"
        else:
            return f"{current} → {updatable}"
