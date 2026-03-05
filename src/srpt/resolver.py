import asyncio
import json
import sys
import urllib.request
from typing import List, Dict, Any, Optional, Iterable, Set
from packaging.version import Version, parse as parse_version
from packaging.requirements import Requirement as PackagingRequirement
from packaging.utils import canonicalize_name
from resolvelib import Resolver, BaseReporter, AbstractProvider
from srpt.pypi import PyPIClient


class Candidate:
    def __init__(
        self,
        name: str,
        version: Version,
        url: str,
        hashes: Dict[str, str],
        requires_python: Optional[str] = None,
    ):
        self.name = canonicalize_name(name)
        self.version = version
        self.url = url
        self.hashes = hashes
        self.requires_python = requires_python
        self.dependencies: List[PackagingRequirement] = []

    def __repr__(self):
        return f"Candidate({self.name}=={self.version})"

    def __hash__(self):
        return hash((self.name, self.version))

    def __eq__(self, other):
        if not isinstance(other, Candidate):
            return False
        return self.name == other.name and self.version == other.version


class Requirement:
    def __init__(self, requirement: PackagingRequirement):
        self.requirement = requirement
        self.name = canonicalize_name(requirement.name)

    def __repr__(self):
        return f"Requirement({self.requirement})"

    def __hash__(self):
        return hash(str(self.requirement))

    def __eq__(self, other):
        if not isinstance(other, Requirement):
            return False
        return str(self.requirement) == str(other.requirement)


class SimpleReporter(BaseReporter):
    def resolving_started(self):
        print("srpt: Starting dependency resolution…")

    def resolving_finished(self):
        print("srpt: Dependency resolution finished.")

    def pin_candidate(self, candidate):
        print(f"srpt: Pinning {candidate.name}=={candidate.version}")


class PyPIProvider(AbstractProvider):
    def __init__(self, client: PyPIClient):
        self.client = client
        self._metadata_cache: Dict[str, Dict[str, Any]] = {}
        self._version_metadata_cache: Dict[
            str, Dict[str, Any]
        ] = {}  # NEW: cache version-specific metadata

    # … rest of methods …

    def identify(self, requirement_or_candidate):
        return requirement_or_candidate.name

    def get_preference(self, identifier, resolutions, candidates, information, backtrack_causes):
        return len(candidates)

    def find_matches(self, identifier, requirements, incompatibilities):
        if identifier not in self._metadata_cache:
            metadata = self.client.get_project_metadata_sync(identifier)
            self._metadata_cache[identifier] = metadata

        metadata = self._metadata_cache[identifier]

        matches = []
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

            # Skip pre-release/dev versions unless explicitly requested
            if version.is_prerelease or version.is_devrelease:
                continue

            # Check if version satisfies all requirements
            is_satisfied = True
            for req_wrapper in requirements.get(identifier, []):
                if not req_wrapper.requirement.specifier.contains(version, prereleases=True):
                    is_satisfied = False
                    break

            if not is_satisfied:
                continue

            # Filter incompatibilities
            if (identifier, version) in incompatibilities:
                continue

            matches.append(
                Candidate(
                    name=identifier,
                    version=version,
                    url=file.get("url"),
                    hashes=file.get("hashes"),
                    requires_python=file.get("requires-python"),
                )
            )

        # Sort by version (newest first)
        matches.sort(key=lambda x: x.version, reverse=True)
        return matches

    def is_satisfied_by(self, requirement, candidate):
        return requirement.requirement.specifier.contains(candidate.version, prereleases=True)

    def get_dependencies(self, candidate):
        # Check version-specific metadata cache first
        cache_key = f"{candidate.name}=={candidate.version}"

        if cache_key in self._version_metadata_cache:
            data = self._version_metadata_cache[cache_key]
            requires_dist = data.get("requires_dist", [])
        else:
            # Not in cache, fetch from PyPI
            print(f"srpt: Getting dependencies for {candidate.name}=={candidate.version}…")
            url = f"https://pypi.org/pypi/{candidate.name}/{candidate.version}/json"
            try:
                with urllib.request.urlopen(url) as response:
                    data = json.loads(response.read().decode())
                    requires_dist = data.get("info", {}).get("requires_dist") or []

                    # Cache it for future use
                    self._version_metadata_cache[cache_key] = {
                        "requires_dist": requires_dist,
                        "data": data,
                    }
            except Exception as e:
                print(f"srpt: Error getting deps for {candidate.name}: {e}")
                return []

        # Basic marker evaluation
        env = {
            "python_version": ".".join(map(str, sys.version_info[:2])),
            "sys_platform": sys.platform,
        }

        deps = []
        for r_str in requires_dist:
            req = PackagingRequirement(r_str)
            if req.marker and not req.marker.evaluate(env):
                continue
            deps.append(Requirement(req))
        return deps

    # Add missing methods to satisfy resolvelib version expectations if any
    def narrow_requirement_selection(self, identifiers, **kwargs):
        return identifiers


async def resolve(requirements_list: List[str]) -> List[Candidate]:
    from srpt.cache import ResolutionCache

    # Check cache first
    cache = ResolutionCache()
    cached = cache.get(requirements_list)

    if cached:
        print(f"srpt: Using cached resolution ({len(cached)} packages)")
        # Reconstruct candidates from cached data
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

    # Not in cache, resolve fresh
    client = PyPIClient()
    provider = PyPIProvider(client)
    reporter = SimpleReporter()
    resolver_obj = Resolver(provider, reporter)

    # 1. Parse requirement strings
    reqs = [Requirement(PackagingRequirement(r)) for r in requirements_list]

    # 2. Run resolution
    result = resolver_obj.resolve(reqs)

    # 3. Extract and return results
    candidates = list(result.mapping.values())

    # 4. Cache the result
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
