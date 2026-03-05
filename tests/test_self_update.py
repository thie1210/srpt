"""
Tests for self_update module.
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from srpt.self_update import (
    check_for_updates,
    get_latest_release_info,
    download_release,
    self_update,
)
from srpt import __version__


class TestCheckForUpdates:
    """Tests for check_for_updates function."""

    @pytest.mark.asyncio
    async def test_no_update_available(self):
        """Test when already on latest version."""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {"tag_name": f"v{__version__}"}
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            result = await check_for_updates()
            assert result is None

    @pytest.mark.asyncio
    async def test_update_available(self):
        """Test when update is available."""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = MagicMock()
            # Return a higher version
            from packaging.version import Version

            higher_version = str(Version(__version__) + 1)
            mock_response.json.return_value = {"tag_name": f"v{higher_version}"}
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            result = await check_for_updates()
            assert result == higher_version

    @pytest.mark.asyncio
    async def test_github_api_error(self):
        """Test handling of GitHub API errors."""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.side_effect = httpx.HTTPError("API Error")

            with pytest.raises(httpx.HTTPError):
                await check_for_updates()


class TestGetLatestReleaseInfo:
    """Tests for get_latest_release_info function."""

    @pytest.mark.asyncio
    async def test_successful_release_fetch(self):
        """Test successful fetch of release info."""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "tag_name": "v0.1.6",
                "body": "Release notes",
                "published_at": "2024-03-04T00:00:00Z",
                "html_url": "https://github.com/thie1210/py/releases/tag/v0.1.6",
            }
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            result = await get_latest_release_info()
            assert result["version"] == "0.1.6"
            assert result["changelog"] == "Release notes"

    @pytest.mark.asyncio
    async def test_fallback_to_tags_on_404(self):
        """Test fallback to tags when no releases exist."""
        with patch("httpx.AsyncClient.get") as mock_get:
            # First call (releases/latest) returns 404
            mock_response_404 = MagicMock()
            mock_response_404.status_code = 404
            mock_response_404.raise_for_status.side_effect = httpx.HTTPStatusError(
                "404", request=MagicMock(), response=mock_response_404
            )

            # Second call (tags) returns tags
            mock_response_tags = MagicMock()
            mock_response_tags.json.return_value = [
                {"name": "v0.1.6", "zipball_url": "https://github.com/..."}
            ]
            mock_response_tags.raise_for_status = MagicMock()

            mock_get.side_effect = [mock_response_404, mock_response_tags]

            result = await get_latest_release_info()
            assert result["version"] == "0.1.6"


class TestDownloadRelease:
    """Tests for download_release function."""

    @pytest.mark.asyncio
    async def test_successful_download(self, tmp_path):
        """Test successful download of release."""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = MagicMock()
            mock_response.content = b"fake tar.gz content"
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            result = await download_release("0.1.6", tmp_path)

            assert result.exists()
            assert result.name == "py-0.1.6.tar.gz"
            assert result.read_bytes() == b"fake tar.gz content"

    @pytest.mark.asyncio
    async def test_download_uses_correct_url(self, tmp_path):
        """Test that download uses GitHub archive URL, not release download URL."""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = MagicMock()
            mock_response.content = b"content"
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            await download_release("0.1.6", tmp_path)

            # Verify the URL is correct (archive, not releases/download)
            call_args = mock_get.call_args
            assert "archive/refs/tags" in str(call_args)
            assert "releases/download" not in str(call_args)

    @pytest.mark.asyncio
    async def test_download_404_error(self, tmp_path):
        """Test handling of 404 error during download."""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "404 Not Found", request=MagicMock(), response=mock_response
            )
            mock_get.return_value = mock_response

            with pytest.raises(httpx.HTTPStatusError):
                await download_release("0.1.6", tmp_path)


class TestSelfUpdate:
    """Tests for self_update function."""

    @pytest.mark.asyncio
    async def test_dry_run_shows_available_update(self):
        """Test dry-run shows update information."""
        with patch("srpt.self_update.get_latest_release_info") as mock_info:
            from packaging.version import Version

            higher_version = str(Version(__version__) + 1)
            mock_info.return_value = {
                "version": higher_version,
                "changelog": "New features",
            }

            result = await self_update(dry_run=True, check_only=False)
            assert result is True

    @pytest.mark.asyncio
    async def test_already_up_to_date(self):
        """Test when already on latest version."""
        with patch("srpt.self_update.get_latest_release_info") as mock_info:
            mock_info.return_value = {
                "version": __version__,
                "changelog": "",
            }

            result = await self_update(dry_run=False, check_only=False)
            assert result is True

    @pytest.mark.asyncio
    async def test_check_only_mode(self):
        """Test check-only mode."""
        with patch("srpt.self_update.check_for_updates") as mock_check:
            mock_check.return_value = None  # No update available

            result = await self_update(dry_run=False, check_only=True)
            assert result is True
