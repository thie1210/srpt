import asyncio
import httpx
import hashlib
from pathlib import Path
from typing import List, Dict, Any


class Downloader:
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.client = None

    async def __aenter__(self):
        # Use HTTP/2 with connection pooling for parallel downloads
        self.client = httpx.AsyncClient(
            http2=True,
            timeout=30.0,
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()

    async def download_package(self, url: str, expected_sha256: str = None) -> Path:
        """Downloads a package from a URL using HTTP/2 and returns the path to the cached file."""
        filename = url.split("/")[-1]
        target_path = self.cache_dir / filename

        if target_path.exists() and expected_sha256:
            if self._verify_checksum(target_path, expected_sha256):
                return target_path

        if not self.client:
            raise RuntimeError("Downloader client not started. Use 'async with' context manager.")

        print(f"Py: Downloading {filename}…")
        response = await self.client.get(url)
        response.raise_for_status()

        with open(target_path, "wb") as f:
            f.write(response.content)

        if expected_sha256 and not self._verify_checksum(target_path, expected_sha256):
            target_path.unlink()
            raise ValueError(f"Checksum mismatch for {filename}")

        return target_path

    def _verify_checksum(self, path: Path, expected_sha256: str) -> bool:
        sha256_hash = hashlib.sha256()
        with open(path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest() == expected_sha256

    async def download_packages(self, package_urls: List[Dict[str, str]]) -> List[Path]:
        """Downloads multiple packages in parallel using HTTP/2."""
        tasks = [self.download_package(pkg["url"], pkg.get("sha256")) for pkg in package_urls]
        return await asyncio.gather(*tasks)
