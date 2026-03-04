"""
Parallel dependency resolver with iterative learning.

Learns from each installation without pre-seeded knowledge.
"""

import asyncio
import json
import sys
import urllib.request
from typing import List, Set, Dict, Any, Tuple
from packaging.requirements import Requirement as PackagingRequirement
from packaging.version import parse as parse_version
from py.pypi import PyPIClient
from py.metadata_cache import MetadataCache
from py.resolver import Resolver as ResolvelibResolver, Candidate, Requirement
from py.resolver import PyPIProvider, SimpleReporter


async def fetch_version_metadata_batch(
    client: PyPIClient, version_specs: List[Tuple[str, str]]
) -> Dict[str, Dict[str, Any]]:
    """
    Fetch version-specific metadata in parallel using HTTP/2.

    Args:
        version_specs: List of (package_name, version) tuples

    Returns:
        Dict mapping "package==version" to metadata
    """
    import httpx

    async def fetch_one(http_client, package: str, version: str) -> Tuple[str, str, Dict]:
        url = f"https://pypi.org/pypi/{package}/{version}/json"
        try:
            async with http_client.stream("GET", url) as response:
                if response.status_code == 200:
                    data = await response.aread()
                    parsed = json.loads(data)
                    requires_dist = parsed.get("info", {}).get("requires_dist") or []
                    return (package, version, {"requires_dist": requires_dist, "data": parsed})
                else:
                    return (package, version, {"requires_dist": [], "data": {}})
        except Exception as e:
            print(f"Py: Warning: Failed to fetch {package}=={version}: {e}")
            return (package, version, {"requires_dist": [], "data": {}})

    # Use HTTP/2 for better performance with connection pooling
    async with httpx.AsyncClient(
        http2=True,
        timeout=30.0,
        limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
    ) as http_client:
        tasks = [fetch_one(http_client, pkg, ver) for pkg, ver in version_specs]
        results = await asyncio.gather(*tasks)

        return {f"{pkg}=={ver}": data for pkg, ver, data in results}


def extract_top_candidates(
    metadata_dict: Dict[str, Dict[str, Any]], max_per_package: int = 3
) -> List[Tuple[str, str]]:
    """
    Extract top candidate versions from package metadata.

    Args:
        metadata_dict: Dict of package_name -> metadata
        max_per_package: Maximum candidates per package

    Returns:
        List of (package_name, version) tuples
    """
    candidates = []

    for package_name, metadata in metadata_dict.items():
        if not metadata or "files" not in metadata:
            continue

        version_count = 0
        seen_versions = set()

        for file in metadata.get("files", []):
            if version_count >= max_per_package:
                break

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

            # Skip pre-release versions
            if version.is_prerelease or version.is_devrelease:
                continue

            if version_str not in seen_versions:
                candidates.append((package_name, version_str))
                seen_versions.add(version_str)
                version_count += 1

    return candidates


async def parallel_resolve(requirements_list: List[str]) -> List[Candidate]:
    """
    Resolve dependencies using parallel metadata fetching.

    Strategy:
    1. Iteratively expand package list using learned dependency graph
    2. Batch fetch package metadata in parallel
    3. Pre-fetch version-specific metadata for top candidates
    4. Run resolution using cached data
    5. Record newly discovered dependencies for future use
    """
    from py.cache import ResolutionCache

    # Check resolution cache first
    cache = ResolutionCache()
    cached = cache.get(requirements_list)

    if cached:
        print(f"Py: Using cached resolution ({len(cached)} packages)")
        candidates = []
        for item in cached:
            candidates.append(
                Candidate(
                    name=item["name"],
                    version=parse_version(item["version"]),
                    url=item["url"],
                    hashes=item.get("hashes", {}),
                    requires_python=item.get("requires_python"),
                )
            )
        return candidates

    # Initialize
    client = PyPIClient()
    metadata_cache = MetadataCache()

    # Phase 1: Predict packages using learned dependency graph
    print("Py: Predicting dependencies from learned data…")
    predicted_packages = metadata_cache.predict_dependencies(requirements_list, max_depth=3)

    if len(predicted_packages) > len(requirements_list):
        print(
            f"Py: Predicted {len(predicted_packages)} packages (from {len(requirements_list)} requested)"
        )
    else:
        print(f"Py: No predictions yet, will learn from this installation")
        predicted_packages = set(p.lower() for p in requirements_list)

    # Phase 2: Batch fetch package metadata in PARALLEL
    print(f"Py: Pre-fetching package metadata for {len(predicted_packages)} packages…")

    # Normalize package names (strip extras and version specifiers)
    # e.g., "Django~=3.2" -> "django", "package[extra]>=1.0" -> "package"
    normalized_packages = []
    for p in predicted_packages:
        # Use packaging.requirements to properly parse
        try:
            req = PackagingRequirement(p)
            normalized = req.name.lower()
        except Exception:
            # Fallback: strip manually
            normalized = (
                p.split("[")[0]
                .split("~=")[0]
                .split("==")[0]
                .split(">=")[0]
                .split("<=")[0]
                .split(">")[0]
                .split("<")[0]
                .lower()
            )
        normalized_packages.append(normalized)

    # Remove duplicates
    normalized_packages = list(set(normalized_packages))

    cached_metadata = metadata_cache.get_batch(normalized_packages)
    packages_to_fetch = [p for p in normalized_packages if p not in cached_metadata]

    prefetched_metadata = {}

    if packages_to_fetch:
        print(
            f"Py: Fetching {len(packages_to_fetch)} packages in parallel ({len(cached_metadata)} cached)"
        )
        try:
            new_metadata = await client.get_project_metadata_batch(packages_to_fetch)
            prefetched_metadata = {**cached_metadata, **new_metadata}

            # Cache the fetched metadata
            for pkg_name, metadata in new_metadata.items():
                metadata_cache.set(pkg_name, metadata, dependencies=[])

        except Exception as e:
            print(f"Py: Warning: Parallel fetch failed: {e}")
            print("Py: Falling back to sequential fetching in resolver")
            prefetched_metadata = cached_metadata
    else:
        print(f"Py: All {len(cached_metadata)} packages already cached!")
        prefetched_metadata = cached_metadata

    # Phase 3: Pre-fetch version-specific metadata in PARALLEL
    print("Py: Extracting top candidate versions…")
    top_candidates = extract_top_candidates(prefetched_metadata, max_per_package=3)

    if top_candidates:
        print(
            f"Py: Pre-fetching version metadata for {len(top_candidates)} candidates in parallel…"
        )
        try:
            version_metadata = await fetch_version_metadata_batch(client, top_candidates)
            print(f"Py: Pre-fetched {len(version_metadata)} version metadata entries")
        except Exception as e:
            print(f"Py: Warning: Version metadata fetch failed: {e}")
            version_metadata = {}
    else:
        version_metadata = {}

    # Phase 4: Run resolution with pre-fetched metadata
    print("Py: Resolving dependencies…")

    # Create provider and inject all cached data
    provider = PyPIProvider(client)
    provider._metadata_cache.update(prefetched_metadata)
    provider._version_metadata_cache.update(version_metadata)  # NEW!

    # Use the existing resolver
    reporter = SimpleReporter()
    resolver_obj = ResolvelibResolver(provider, reporter)
    reqs = [Requirement(PackagingRequirement(r)) for r in requirements_list]

    result = resolver_obj.resolve(reqs)
    candidates = list(result.mapping.values())

    # Phase 5: Record discovered dependencies
    discovered_deps: Dict[str, List[str]] = {}

    for candidate in candidates:
        deps = provider.get_dependencies(candidate)
        dep_names = [d.name.lower() for d in deps]

        if dep_names:
            discovered_deps[candidate.name] = dep_names

    # Update metadata cache with learned dependencies
    if discovered_deps:
        print(f"Py: Learned {len(discovered_deps)} new dependency relationships")
        for pkg_name, deps in discovered_deps.items():
            pkg_lower = pkg_name.lower()
            metadata = prefetched_metadata.get(pkg_lower) or provider._metadata_cache.get(
                pkg_lower, {}
            )
            if metadata:
                metadata_cache.set(pkg_lower, metadata, deps)

    # Cache the resolution result
    cache_data = [
        {
            "name": c.name,
            "version": str(c.version),
            "url": c.url,
            "hashes": c.hashes,
            "requires_python": c.requires_python,
        }
        for c in candidates
    ]
    cache.set(requirements_list, cache_data)

    return candidates
