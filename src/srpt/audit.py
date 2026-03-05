"""
Security audit functionality using pip-audit.

Checks installed packages for known vulnerabilities.
"""

import asyncio
import json
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Optional

from .utils.confirm import dry_run_header, print_success, print_error, print_warning


def ensure_pip_audit_installed() -> bool:
    """
    Install pip-audit if not present.

    Returns:
        True if pip-audit is available
    """
    try:
        # Check if pip-audit is installed
        result = subprocess.run(
            [sys.executable, "-m", "pip_audit", "--version"], capture_output=True, text=True
        )

        if result.returncode == 0:
            return True
    except Exception:
        pass

    # Install pip-audit
    print("Installing pip-audit...")
    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--quiet",
                "--disable-pip-version-check",
                "pip-audit>=2.6.0",
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print("  ✓ pip-audit installed")
            return True
        else:
            print_error(f"Failed to install pip-audit: {result.stderr}")
            return False
    except Exception as e:
        print_error(f"Failed to install pip-audit: {e}")
        return False


def run_pip_audit(
    project_root: Path, ignore_cves: Optional[List[str]] = None, json_output: bool = False
) -> List[Dict]:
    """
    Run pip-audit and parse results.

    Args:
        project_root: Path to project root
        ignore_cves: List of CVE IDs to ignore
        json_output: If True, return raw JSON output

    Returns:
        List of vulnerability dicts
    """
    # Ensure pip-audit is installed
    if not ensure_pip_audit_installed():
        return []

    # Build command - use current Python (managed Python)
    cmd = [sys.executable, "-m", "pip_audit", "--format", "json"]

    # Check if we're in a venv
    venv_path = project_root / ".venv"
    if venv_path.exists():
        # Use pip-audit's --python flag to specify the venv
        if sys.platform == "win32":
            python_path = venv_path / "Scripts" / "python.exe"
        else:
            python_path = venv_path / "bin" / "python"

        if python_path.exists():
            # Tell pip-audit to audit the venv's packages
            cmd.extend(["--python", str(python_path)])

    # Run pip-audit
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(project_root))

        # pip-audit returns non-zero if vulnerabilities found
        # but we still want to parse the output
        if result.returncode not in (0, 1):
            print_error(f"pip-audit failed: {result.stderr}")
            return []

        # Parse JSON output
        if not result.stdout:
            return []

        data = json.loads(result.stdout)

        # Filter ignored CVEs
        if ignore_cves:
            data = [vuln for vuln in data if vuln.get("id", {}).get("id", "") not in ignore_cves]

        return data

    except json.JSONDecodeError as e:
        print_error(f"Failed to parse pip-audit output: {e}")
        return []
    except Exception as e:
        print_error(f"Failed to run pip-audit: {e}")
        return []


def format_vulnerability(vuln: Dict) -> str:
    """
    Format a vulnerability for display.

    Args:
        vuln: Vulnerability dict from pip-audit

    Returns:
        Formatted string
    """
    package = vuln.get("package", {})
    package_name = package.get("name", "unknown")
    package_version = package.get("version", "unknown")

    vuln_id = vuln.get("id", {})
    vuln_id_str = vuln_id.get("id", "unknown")

    fix_versions = vuln.get("fix_versions", [])
    fix_str = fix_versions[0] if fix_versions else "unknown"

    # Get severity if available
    severity = vuln.get("severity", "UNKNOWN")

    # Get description if available
    description = vuln.get("description", "No description available")

    lines = [
        f"  ✗ {package_name} {package_version}",
        f"    {vuln_id_str}: {description}",
        f"    Severity: {severity}",
        f"    Fixed in: {fix_str}",
        f"    → Run 'srpt update {package_name} --apply'",
    ]

    return "\n".join(lines)


async def run_audit(
    project_root: Path,
    fix: bool = False,
    ignore_cves: Optional[List[str]] = None,
    json_output: bool = False,
) -> List[Dict]:
    """
    Run security audit on installed packages.

    Args:
        project_root: Path to project root
        fix: If True, auto-update vulnerable packages
        ignore_cves: List of CVE IDs to ignore
        json_output: If True, return JSON output

    Returns:
        List of vulnerabilities found
    """
    print("\nSECURITY AUDIT\n")

    # Run pip-audit
    vulnerabilities = run_pip_audit(
        project_root=project_root, ignore_cves=ignore_cves, json_output=json_output
    )

    if json_output:
        return vulnerabilities

    if not vulnerabilities:
        print("VULNERABILITIES:")
        print("  ✓ No vulnerabilities found\n")
        return []

    # Display vulnerabilities
    print("VULNERABILITIES:")
    for vuln in vulnerabilities:
        print(format_vulnerability(vuln))
        print()

    # Summary
    high_count = sum(1 for v in vulnerabilities if v.get("severity") == "HIGH")
    medium_count = sum(1 for v in vulnerabilities if v.get("severity") == "MEDIUM")
    low_count = sum(1 for v in vulnerabilities if v.get("severity") == "LOW")

    print("SUMMARY:")
    print(f"  {len(vulnerabilities)} vulnerabilities found")
    if high_count:
        print(f"  {high_count} HIGH")
    if medium_count:
        print(f"  {medium_count} MEDIUM")
    if low_count:
        print(f"  {low_count} LOW")

    if fix:
        print("\n  Auto-fixing vulnerable packages...")
        # TODO: Implement auto-fix
        print("  Auto-fix not yet implemented")
    else:
        print("\n  Run 'srpt audit --fix' to auto-fix all")

    return vulnerabilities


def get_vulnerable_packages(vulnerabilities: List[Dict]) -> List[str]:
    """
    Get list of packages with vulnerabilities.

    Args:
        vulnerabilities: List of vulnerability dicts

    Returns:
        List of package names
    """
    packages = set()
    for vuln in vulnerabilities:
        package = vuln.get("package", {})
        name = package.get("name")
        if name:
            packages.add(name)
    return list(packages)
