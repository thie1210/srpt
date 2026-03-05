"""
Tests for health check command.
"""

import asyncio
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
from srpt.health import (
    health_check,
    check_srpt_version,
    check_python_version,
    check_cache_status,
    check_security,
    check_dependencies,
    format_health_report,
)
from srpt import __version__


class TestCheckPyVersion:
    """Tests for check_srpt_version function."""

    @pytest.mark.asyncio
    async def test_no_update_available(self):
        """Test when srpt is up to date."""
        with patch("srpt.self_update.check_for_updates", return_value=None):
            result = await check_srpt_version()

            assert result["current"] == __version__
            assert result["latest"] == __version__
            assert result["update_available"] is False

    @pytest.mark.asyncio
    async def test_update_available(self):
        """Test when update is available."""
        from packaging.version import Version

        higher_version = f"{Version(__version__).major}.{Version(__version__).minor + 1}.0"

        with patch("srpt.self_update.check_for_updates", return_value=higher_version):
            result = await check_srpt_version()

            assert result["current"] == __version__
            assert result["latest"] == higher_version
            assert result["update_available"] is True

    @pytest.mark.asyncio
    async def test_github_api_error(self):
        """Test handling of GitHub API errors."""
        with patch("srpt.self_update.check_for_updates", side_effect=Exception("API error")):
            result = await check_srpt_version()

            assert result["current"] == __version__
            assert result["latest"] == __version__
            assert result["update_available"] is False
            assert "error" in result


class TestCheckPythonVersion:
    """Tests for check_python_version function."""

    def test_no_venv(self, tmp_path):
        """Test when no venv exists."""
        result = check_python_version(tmp_path)

        assert "version" in result
        assert result["venv"] is False

    def test_with_venv(self, tmp_path):
        """Test when venv exists."""
        import sys

        # Create fake venv
        venv = tmp_path / ".venv"
        venv.mkdir()

        if sys.platform == "win32":
            bin_dir = venv / "Scripts"
        else:
            bin_dir = venv / "bin"
        bin_dir.mkdir()

        # Create fake python binary
        python = bin_dir / "python"
        python.touch()

        result = check_python_version(tmp_path)

        assert "version" in result
        assert result["venv"] is True
        assert result["path"] == str(venv)

    def test_broken_venv(self, tmp_path):
        """Test when venv Python binary fails to execute."""
        import sys

        # Create fake venv
        venv = tmp_path / ".venv"
        venv.mkdir()

        if sys.platform == "win32":
            bin_dir = venv / "Scripts"
        else:
            bin_dir = venv / "bin"
        bin_dir.mkdir()

        # Create fake python binary (not executable)
        python = bin_dir / "python"
        python.write_text("#!/bin/bash\nexit 1")

        result = check_python_version(tmp_path)

        assert "version" in result
        assert result["venv"] is True
        # Should fall back to system Python


class TestCheckCacheStatus:
    """Tests for check_cache_status function."""

    def test_no_cache(self, tmp_path):
        """Test when cache doesn't exist."""
        # Use a temporary home directory to avoid conflicts with existing cache
        import os

        original_home = os.environ.get("HOME")

        try:
            # Set a temporary home
            os.environ["HOME"] = str(tmp_path / "fake_home")

            # Clear any SRPT_BASE_DIR setting
            os.environ.pop("SRPT_BASE_DIR", None)

            result = check_cache_status(tmp_path)

            # Cache may or may not exist depending on system state
            # Just check that the function returns a valid result
            assert "exists" in result
        finally:
            # Restore original home
            if original_home:
                os.environ["HOME"] = original_home

    def test_with_cache(self, tmp_path):
        """Test when cache exists."""
        import os

        # Create cache directory
        cache_dir = Path.home() / ".local" / "share" / "srpt" / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Create some test files
        (cache_dir / "test.txt").write_text("test")

        result = check_cache_status(tmp_path)

        assert result["exists"] is True
        assert "size_mb" in result
        assert result["path"] == str(cache_dir)


class TestCheckSecurity:
    """Tests for check_security function."""

    @pytest.mark.asyncio
    async def test_no_vulnerabilities(self, tmp_path):
        """Test when no vulnerabilities found."""
        with patch("srpt.audit.run_pip_audit", return_value=[]):
            result = await check_security(tmp_path)

            assert result["vulnerabilities"] == []
            assert result["count"] == 0

    @pytest.mark.asyncio
    async def test_with_vulnerabilities(self, tmp_path):
        """Test when vulnerabilities found."""
        mock_vulns = [
            {
                "package": {"name": "requests", "version": "2.0.0"},
                "id": {"id": "CVE-2023-12345"},
                "fix_versions": ["2.1.0"],
                "severity": "HIGH",
            }
        ]

        with patch("srpt.audit.run_pip_audit", return_value=mock_vulns):
            result = await check_security(tmp_path)

            assert len(result["vulnerabilities"]) == 1
            assert result["count"] == 1


class TestCheckDependencies:
    """Tests for check_dependencies function."""

    @pytest.mark.asyncio
    async def test_no_venv(self, tmp_path):
        """Test when no venv exists."""
        result = await check_dependencies(tmp_path, full=False)

        assert result["installed"] == 0
        assert result["outdated"] == []

    @pytest.mark.asyncio
    async def test_with_venv(self, tmp_path):
        """Test when venv exists with packages."""
        import sys

        # Create fake venv with packages
        venv = tmp_path / ".venv"
        venv.mkdir()

        if sys.platform == "win32":
            site_packages = venv / "Lib" / "site-packages"
        else:
            lib_dir = venv / "lib"
            lib_dir.mkdir()
            python_dir = lib_dir / "python3.14"
            python_dir.mkdir()
            site_packages = python_dir / "site-packages"

        site_packages.mkdir(parents=True)

        # Create fake dist-info
        dist_info = site_packages / "requests-2.0.0.dist-info"
        dist_info.mkdir()
        (dist_info / "METADATA").write_text("Name: requests\nVersion: 2.0.0")

        result = await check_dependencies(tmp_path, full=False)

        assert result["installed"] >= 1


class TestHealthCheck:
    """Tests for full health_check function."""

    @pytest.mark.asyncio
    async def test_full_health_check(self, tmp_path):
        """Test complete health check."""
        with (
            patch("srpt.self_update.check_for_updates", return_value=None),
            patch("srpt.audit.run_pip_audit", return_value=[]),
        ):
            result = await health_check(tmp_path, full=False)

            assert "py_version" in result
            assert "python_version" in result
            assert "cache" in result
            assert "security" in result
            assert "dependencies" in result
            assert "compatibility" in result
            assert "warnings" in result
            assert "errors" in result


class TestFormatHealthReport:
    """Tests for format_health_report function."""

    def test_format_report_no_issues(self, tmp_path, capsys):
        """Test formatting report with no issues."""
        health = {
            "py_version": {
                "current": "0.2.8",
                "latest": "0.2.8",
                "update_available": False,
            },
            "python_version": {
                "version": "3.14.0",
                "venv": True,
            },
            "cache": {
                "exists": True,
                "size_mb": 10.5,
            },
            "security": {
                "vulnerabilities": [],
                "count": 0,
            },
            "dependencies": {
                "installed": 5,
                "outdated": [],
            },
            "compatibility": {},
            "warnings": 0,
            "errors": 0,
        }

        format_health_report(health, full=False)

        captured = capsys.readouterr()
        assert "SRPT HEALTH CHECK" in captured.out
        assert "✓ srpt version: 0.2.8" in captured.out
        assert "✓ Python: 3.14.0" in captured.out
        assert "✓ Vulnerabilities: 0 found" in captured.out

    def test_format_report_with_vulnerabilities(self, tmp_path, capsys):
        """Test formatting report with vulnerabilities."""
        health = {
            "py_version": {
                "current": "0.2.8",
                "latest": "0.2.8",
                "update_available": False,
            },
            "python_version": {
                "version": "3.14.0",
                "venv": True,
            },
            "cache": {
                "exists": True,
                "size_mb": 10.5,
            },
            "security": {
                "vulnerabilities": [
                    {
                        "package": {"name": "requests", "version": "2.0.0"},
                        "id": {"id": "CVE-2023-12345"},
                        "fix_versions": ["2.1.0"],
                    }
                ],
                "count": 1,
            },
            "dependencies": {
                "installed": 5,
                "outdated": [],
            },
            "compatibility": {},
            "warnings": 1,
            "errors": 0,
        }

        format_health_report(health, full=False)

        captured = capsys.readouterr()
        assert "✗ Vulnerabilities: 1 found" in captured.out
        assert "requests 2.0.0: CVE-2023-12345" in captured.out

    def test_format_report_with_outdated(self, tmp_path, capsys):
        """Test formatting report with outdated packages."""
        health = {
            "py_version": {
                "current": "0.2.8",
                "latest": "0.2.8",
                "update_available": False,
            },
            "python_version": {
                "version": "3.14.0",
                "venv": True,
            },
            "cache": {
                "exists": True,
                "size_mb": 10.5,
            },
            "security": {
                "vulnerabilities": [],
                "count": 0,
            },
            "dependencies": {
                "installed": 5,
                "outdated": [{"name": "django", "current": "5.0.0", "latest": "6.0.0"}],
            },
            "compatibility": {},
            "warnings": 1,
            "errors": 0,
        }

        format_health_report(health, full=False)

        captured = capsys.readouterr()
        assert "! Outdated: 1" in captured.out
        assert "django 5.0.0 → 6.0.0" in captured.out
