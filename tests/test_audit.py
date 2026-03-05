"""
Tests for audit module.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, call
import subprocess
import sys

from py.audit import (
    ensure_pip_audit_installed,
    run_pip_audit,
    format_vulnerability,
    get_vulnerable_packages,
)


class TestEnsurePipAuditInstalled:
    """Tests for ensure_pip_audit_installed function."""

    def test_already_installed(self):
        """Test when pip-audit is already installed."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            result = ensure_pip_audit_installed()
            assert result is True
            # Should check version, not install
            assert "pip_audit" in str(mock_run.call_args)
            assert "--version" in str(mock_run.call_args)

    def test_not_installed_then_installs(self):
        """Test when pip-audit is not installed, then installs it."""
        with patch("subprocess.run") as mock_run:
            # First call (version check) fails
            # Second call (install) succeeds
            mock_run.side_effect = [
                MagicMock(returncode=1),
                MagicMock(returncode=0),
            ]

            result = ensure_pip_audit_installed()
            assert result is True
            # Should have called install
            assert len(mock_run.call_args_list) == 2

    def test_install_fails(self):
        """Test when pip-audit installation fails."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stderr="Install failed")

            result = ensure_pip_audit_installed()
            assert result is False


class TestRunPipAudit:
    """Tests for run_pip_audit function."""

    def test_uses_managed_python_not_venv_python(self, tmp_path):
        """Test that pip-audit uses managed Python, not venv Python.

        This is the fix for the library path issue where venv Python
        had broken symlinks.
        """
        # Create a fake venv
        venv = tmp_path / ".venv"
        venv.mkdir()
        bin_dir = venv / "bin"
        bin_dir.mkdir()
        python = bin_dir / "python"
        python.touch()

        with patch("py.audit.ensure_pip_audit_installed", return_value=True):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=0,
                    stdout="[]",  # No vulnerabilities
                )

                run_pip_audit(tmp_path)

                # Check that we used sys.executable (managed Python)
                # not the venv's python
                call_args = mock_run.call_args[0][0]
                assert call_args[0] == sys.executable
                assert str(python) not in call_args

    def test_uses_python_flag_for_venv(self, tmp_path):
        """Test that pip-audit uses --python flag to specify venv."""
        # Create a fake venv
        venv = tmp_path / ".venv"
        venv.mkdir()
        bin_dir = venv / "bin"
        bin_dir.mkdir()
        python = bin_dir / "python"
        python.touch()

        with patch("py.audit.ensure_pip_audit_installed", return_value=True):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=0,
                    stdout="[]",
                )

                run_pip_audit(tmp_path)

                # Check that we used --python flag
                call_args = mock_run.call_args[0][0]
                assert "--python" in call_args
                # The venv python path should be after --python
                python_idx = call_args.index("--python")
                assert str(python) == call_args[python_idx + 1]

    def test_no_venv_uses_current_environment(self, tmp_path):
        """Test that without venv, pip-audit uses current environment."""
        with patch("py.audit.ensure_pip_audit_installed", return_value=True):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=0,
                    stdout="[]",
                )

                run_pip_audit(tmp_path)

                # Should not have --python flag
                call_args = mock_run.call_args[0][0]
                assert "--python" not in call_args

    def test_handles_broken_venv_gracefully(self, tmp_path):
        """Test handling of broken venv (e.g., missing libpython)."""
        # Create a fake venv
        venv = tmp_path / ".venv"
        venv.mkdir()
        bin_dir = venv / "bin"
        bin_dir.mkdir()
        python = bin_dir / "python"
        python.touch()

        with patch("py.audit.ensure_pip_audit_installed", return_value=True):
            with patch("subprocess.run") as mock_run:
                # Simulate pip-audit failing due to broken venv
                mock_run.return_value = MagicMock(
                    returncode=1,
                    stderr="dyld: Library not loaded: @rpath/libpython3.13.dylib",
                    stdout="",
                )

                result = run_pip_audit(tmp_path)
                # Should return empty list, not crash
                assert result == []

    def test_parses_vulnerabilities(self, tmp_path):
        """Test parsing of vulnerability JSON output."""
        with patch("py.audit.ensure_pip_audit_installed", return_value=True):
            with patch("subprocess.run") as mock_run:
                vuln_json = """[
                    {
                        "package": {"name": "requests", "version": "2.28.0"},
                        "id": {"id": "CVE-2023-32681"},
                        "severity": "MEDIUM",
                        "description": "Info disclosure",
                        "fix_versions": ["2.31.0"]
                    }
                ]"""
                mock_run.return_value = MagicMock(
                    returncode=1,  # Non-zero when vulns found
                    stdout=vuln_json,
                )

                result = run_pip_audit(tmp_path)
                assert len(result) == 1
                assert result[0]["package"]["name"] == "requests"

    def test_filters_ignored_cves(self, tmp_path):
        """Test filtering of ignored CVEs."""
        with patch("py.audit.ensure_pip_audit_installed", return_value=True):
            with patch("subprocess.run") as mock_run:
                vuln_json = """[
                    {
                        "package": {"name": "requests", "version": "2.28.0"},
                        "id": {"id": "CVE-2023-32681"},
                        "severity": "MEDIUM"
                    },
                    {
                        "package": {"name": "pillow", "version": "9.5.0"},
                        "id": {"id": "CVE-2023-44268"},
                        "severity": "HIGH"
                    }
                ]"""
                mock_run.return_value = MagicMock(
                    returncode=1,
                    stdout=vuln_json,
                )

                result = run_pip_audit(tmp_path, ignore_cves=["CVE-2023-32681"])
                assert len(result) == 1
                assert result[0]["id"]["id"] == "CVE-2023-44268"


class TestFormatVulnerability:
    """Tests for format_vulnerability function."""

    def test_formats_vulnerability(self):
        """Test formatting of vulnerability info."""
        vuln = {
            "package": {"name": "requests", "version": "2.28.0"},
            "id": {"id": "CVE-2023-32681"},
            "severity": "MEDIUM",
            "description": "Information disclosure",
            "fix_versions": ["2.31.0"],
        }

        result = format_vulnerability(vuln)
        assert "requests 2.28.0" in result
        assert "CVE-2023-32681" in result
        assert "MEDIUM" in result
        assert "2.31.0" in result


class TestGetVulnerablePackages:
    """Tests for get_vulnerable_packages function."""

    def test_extracts_package_names(self):
        """Test extraction of package names from vulnerabilities."""
        vulns = [
            {"package": {"name": "requests"}},
            {"package": {"name": "pillow"}},
            {"package": {"name": "requests"}},  # Duplicate
        ]

        result = get_vulnerable_packages(vulns)
        assert set(result) == {"requests", "pillow"}

    def test_empty_list(self):
        """Test with empty vulnerability list."""
        result = get_vulnerable_packages([])
        assert result == []
