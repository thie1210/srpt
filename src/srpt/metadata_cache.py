"""
Metadata cache for storing PyPI package metadata.

Learns from every installation to enable faster future resolutions.
"""

import sqlite3
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, List, Set


class MetadataCache:
    """SQLite-based cache for package metadata from PyPI."""

    CACHE_DIR = Path.home() / ".local" / "share" / "srpt" / "cache"
    CACHE_DB = CACHE_DIR / "metadata.db"
    TTL_SECONDS = 7 * 24 * 60 * 60  # 7 days for metadata

    def __init__(self):
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize the metadata cache database."""
        conn = sqlite3.connect(str(self.CACHE_DB))
        cursor = conn.cursor()

        # Main metadata table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metadata_cache (
                package_name TEXT PRIMARY KEY,
                metadata TEXT NOT NULL,
                timestamp REAL NOT NULL,
                dependencies TEXT,
                last_used REAL
            )
        """)

        # Dependency graph table (learned relationships)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dependency_graph (
                package TEXT NOT NULL,
                dependency TEXT NOT NULL,
                count INTEGER DEFAULT 1,
                last_seen REAL,
                PRIMARY KEY (package, dependency)
            )
        """)

        # Index for fast lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_package_deps
            ON dependency_graph(package)
        """)

        conn.commit()
        conn.close()

    def get(self, package_name: str) -> Optional[Dict[str, Any]]:
        """Get cached metadata for a package."""
        conn = sqlite3.connect(str(self.CACHE_DB))
        cursor = conn.cursor()

        try:
            cursor.execute(
                """SELECT metadata, timestamp FROM metadata_cache 
                   WHERE package_name = ?""",
                (package_name.lower(),),
            )
            row = cursor.fetchone()

            if not row:
                return None

            metadata_json, timestamp = row

            # Check TTL
            if time.time() - timestamp > self.TTL_SECONDS:
                # Expired
                cursor.execute(
                    "DELETE FROM metadata_cache WHERE package_name = ?", (package_name.lower(),)
                )
                conn.commit()
                return None

            # Update last_used timestamp
            cursor.execute(
                "UPDATE metadata_cache SET last_used = ? WHERE package_name = ?",
                (time.time(), package_name.lower()),
            )
            conn.commit()

            return json.loads(metadata_json)

        finally:
            conn.close()

    def get_batch(self, package_names: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get cached metadata for multiple packages."""
        result = {}
        for pkg in package_names:
            metadata = self.get(pkg)
            if metadata:
                result[pkg] = metadata
        return result

    def set(self, package_name: str, metadata: Dict[str, Any], dependencies: List[str] = None):
        """Cache metadata for a package and record its dependencies."""
        conn = sqlite3.connect(str(self.CACHE_DB))
        cursor = conn.cursor()

        try:
            # Store metadata
            cursor.execute(
                """INSERT OR REPLACE INTO metadata_cache 
                   (package_name, metadata, timestamp, dependencies, last_used)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    package_name.lower(),
                    json.dumps(metadata),
                    time.time(),
                    json.dumps(dependencies or []),
                    time.time(),
                ),
            )

            # Record dependency relationships
            if dependencies:
                for dep in dependencies:
                    # Normalize dependency name
                    dep_name = dep.lower().split("[")[0].split(";")[0].strip()
                    if not dep_name:
                        continue

                    cursor.execute(
                        """INSERT INTO dependency_graph (package, dependency, count, last_seen)
                           VALUES (?, ?, 1, ?)
                           ON CONFLICT(package, dependency) 
                           DO UPDATE SET 
                             count = count + 1,
                             last_seen = excluded.last_seen""",
                        (package_name.lower(), dep_name, time.time()),
                    )

            conn.commit()
        finally:
            conn.close()

    def set_batch(self, metadata_dict: Dict[str, Dict[str, Any]]):
        """Cache metadata for multiple packages."""
        for pkg_name, metadata in metadata_dict.items():
            self.set(pkg_name, metadata)

    def get_known_dependencies(self, package_name: str) -> List[str]:
        """Get known dependencies for a package from the learned graph."""
        conn = sqlite3.connect(str(self.CACHE_DB))
        cursor = conn.cursor()

        try:
            cursor.execute(
                """SELECT dependency FROM dependency_graph 
                   WHERE package = ? 
                   ORDER BY count DESC""",
                (package_name.lower(),),
            )

            deps = [row[0] for row in cursor.fetchall()]
            return deps
        finally:
            conn.close()

    def predict_dependencies(self, packages: List[str], max_depth: int = 2) -> Set[str]:
        """
        Predict all packages that might be needed based on learned dependency graph.

        Uses BFS traversal of the dependency graph.
        """
        all_packages = set(p.lower() for p in packages)
        frontier = set(all_packages)
        depth = 0

        while frontier and depth < max_depth:
            next_frontier = set()

            for pkg in frontier:
                known_deps = self.get_known_dependencies(pkg)
                for dep in known_deps:
                    if dep not in all_packages:
                        all_packages.add(dep)
                        next_frontier.add(dep)

            frontier = next_frontier
            depth += 1

        return all_packages

    def get_stats(self) -> Dict[str, Any]:
        """Get metadata cache statistics."""
        conn = sqlite3.connect(str(self.CACHE_DB))
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM metadata_cache")
        metadata_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM dependency_graph")
        graph_edges = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT package) FROM dependency_graph")
        packages_with_deps = cursor.fetchone()[0]

        conn.close()

        db_size = 0
        if self.CACHE_DB.exists():
            db_size = self.CACHE_DB.stat().st_size

        return {
            "cached_packages": metadata_count,
            "dependency_edges": graph_edges,
            "packages_with_known_deps": packages_with_deps,
            "db_path": str(self.CACHE_DB),
            "db_size_bytes": db_size,
        }

    def clear(self):
        """Clear all cached metadata."""
        conn = sqlite3.connect(str(self.CACHE_DB))
        cursor = conn.cursor()
        cursor.execute("DELETE FROM metadata_cache")
        cursor.execute("DELETE FROM dependency_graph")
        conn.commit()
        conn.close()
