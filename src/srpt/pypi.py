import json
import urllib.request
import urllib.error
import asyncio
from typing import List, Dict, Any, Optional
from packaging.version import parse as parse_version
from packaging.requirements import Requirement


class PackageNotFoundError(Exception):
    """Raised when a package is not found on PyPI."""

    pass


class PyPIClient:
    def __init__(self, index_url: str = "https://pypi.org/simple/"):
        self.index_url = index_url.rstrip("/") + "/"

    async def get_project_metadata(self, project_name: str) -> Dict[str, Any]:
        """Fetches metadata for a project from the PyPI Simple API (PEP 691 JSON) asynchronously using HTTP/2."""
        import httpx

        url = f"{self.index_url}{project_name}/"
        headers = {"Accept": "application/vnd.pypi.simple.v1+json"}

        async with httpx.AsyncClient(http2=True, timeout=30.0) as client:
            response = await client.get(url, headers=headers)
            if response.status_code == 404:
                raise ValueError(f"Project not found: {project_name}")
            response.raise_for_status()
            return response.json()

    def get_project_metadata_sync(self, project_name: str) -> Dict[str, Any]:
        """Fetches metadata for a project from the PyPI Simple API (PEP 691 JSON) synchronously."""
        url = f"{self.index_url}{project_name}/"
        headers = {"Accept": "application/vnd.pypi.simple.v1+json"}
        req = urllib.request.Request(url, headers=headers)

        try:
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise PackageNotFoundError(
                    f"Package '{project_name}' not found on PyPI\n"
                    f"Check the package name at https://pypi.org/project/{project_name}/"
                )
            raise
        except urllib.error.URLError as e:
            raise Exception(f"Failed to connect to PyPI: {e}")

    def get_candidates(
        self, metadata: Dict[str, Any], requirement: Requirement
    ) -> List[Dict[str, Any]]:
        """Extracts candidates (wheels) for a project that match the requirement."""
        candidates = []
        project_name = metadata.get("name", "").lower()

        for file in metadata.get("files", []):
            filename = file.get("filename", "")
            if not filename.endswith(".whl"):
                continue

            parts = filename.rsplit("-", 4)
            if len(parts) < 5:
                continue

            version_str = parts[1]
            try:
                version = parse_version(version_str)
            except Exception:
                continue

            if not requirement.specifier.contains(version, prereleases=True):
                continue

            candidates.append(
                {
                    "name": project_name,
                    "version": version,
                    "version_str": version_str,
                    "filename": filename,
                    "url": file.get("url"),
                    "hashes": file.get("hashes", {}),
                    "requires_python": file.get("requires-python"),
                }
            )

        # Sort candidates by version (newest first)
        candidates.sort(key=lambda x: x["version"], reverse=True)
        return candidates

    async def get_project_metadata_batch(
        self, project_names: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """Fetches metadata for multiple projects in parallel using HTTP/2."""
        import httpx

        async def fetch_one(client, project_name: str) -> tuple:
            url = f"{self.index_url}{project_name}/"
            headers = {"Accept": "application/vnd.pypi.simple.v1+json"}

            try:
                response = await client.get(url, headers=headers)
                if response.status_code == 404:
                    raise PackageNotFoundError(
                        f"Package '{project_name}' not found on PyPI\n"
                        f"Check the package name at https://pypi.org/project/{project_name}/"
                    )
                response.raise_for_status()
                data = response.json()
                return (project_name, data)
            except PackageNotFoundError:
                raise
            except Exception as e:
                raise Exception(f"Failed to fetch {project_name}: {e}")

        # Use HTTP/2 for better performance
        async with httpx.AsyncClient(
            http2=True,
            timeout=30.0,
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
        ) as client:
            tasks = [fetch_one(client, name) for name in project_names]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            metadata = {}
            errors = []

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    errors.append((project_names[i], result))
                else:
                    name, data = result
                    metadata[name] = data

            if errors:
                # Report first error
                name, error = errors[0]
                raise error

            return metadata

    async def get_latest_version(self, project_name: str) -> str:
        """Helper to get the latest version for a project."""
        metadata = await self.get_project_metadata(project_name)
        return "latest"

        """Helper to get the latest version for a project."""
        metadata = await self.get_project_metadata(project_name)
        return "latest"
