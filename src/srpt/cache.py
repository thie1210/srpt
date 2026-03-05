"""
Resolution cache for storing dependency resolution results.

Uses SQLite for fast, reliable storage with TTL support.
"""

import sqlite3
import hashlib
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional


class ResolutionCache:
    """SQLite-based cache for dependency resolution results."""

    CACHE_DIR = Path.home() / ".local" / "share" / "srpt" / "cache"
    CACHE_DB = CACHE_DIR / "resolution.db"
    TTL_SECONDS = 24 * 60 * 60  # 24 hours

    def __init__(self):
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize the cache database."""
        conn = sqlite3.connect(str(self.CACHE_DB))
        cursor = conn.cursor()

        # Create table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resolution_cache (
                requirements_hash TEXT PRIMARY KEY,
                requirements TEXT NOT NULL,
                resolution TEXT NOT NULL,
                timestamp REAL NOT NULL,
                hits INTEGER DEFAULT 0
            )
        """)

        # Create index on timestamp for cleanup
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp 
            ON resolution_cache(timestamp)
        """)

        conn.commit()
        conn.close()

    def _hash_requirements(self, requirements: List[str]) -> str:
        """Create a hash key from requirements list."""
        # Sort for consistent hashing
        sorted_reqs = sorted([r.lower().strip() for r in requirements])
        req_str = json.dumps(sorted_reqs)
        return hashlib.sha256(req_str.encode()).hexdigest()

    def get(self, requirements: List[str]) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached resolution for requirements.

        Returns None if not found or expired.
        """
        req_hash = self._hash_requirements(requirements)

        conn = sqlite3.connect(str(self.CACHE_DB))
        cursor = conn.cursor()

        try:
            cursor.execute(
                "SELECT resolution, timestamp FROM resolution_cache WHERE requirements_hash = ?",
                (req_hash,),
            )
            row = cursor.fetchone()

            if not row:
                return None

            resolution_json, timestamp = row

            # Check TTL
            if time.time() - timestamp > self.TTL_SECONDS:
                # Expired, delete it
                cursor.execute(
                    "DELETE FROM resolution_cache WHERE requirements_hash = ?", (req_hash,)
                )
                conn.commit()
                return None

            # Update hit counter
            cursor.execute(
                "UPDATE resolution_cache SET hits = hits + 1 WHERE requirements_hash = ?",
                (req_hash,),
            )
            conn.commit()

            # Parse and return
            return json.loads(resolution_json)

        finally:
            conn.close()

    def set(self, requirements: List[str], resolution: List[Dict[str, Any]]):
        """Cache a resolution result."""
        req_hash = self._hash_requirements(requirements)

        conn = sqlite3.connect(str(self.CACHE_DB))
        cursor = conn.cursor()

        try:
            cursor.execute(
                """INSERT OR REPLACE INTO resolution_cache 
                   (requirements_hash, requirements, resolution, timestamp, hits)
                   VALUES (?, ?, ?, ?, 0)""",
                (req_hash, json.dumps(requirements), json.dumps(resolution), time.time()),
            )
            conn.commit()
        finally:
            conn.close()

    def clear(self):
        """Clear all cached resolutions."""
        conn = sqlite3.connect(str(self.CACHE_DB))
        cursor = conn.cursor()
        cursor.execute("DELETE FROM resolution_cache")
        conn.commit()
        conn.close()

    def cleanup_expired(self):
        """Remove expired entries from cache."""
        conn = sqlite3.connect(str(self.CACHE_DB))
        cursor = conn.cursor()

        cutoff = time.time() - self.TTL_SECONDS
        cursor.execute("DELETE FROM resolution_cache WHERE timestamp < ?", (cutoff,))

        deleted = cursor.rowcount
        conn.commit()
        conn.close()

        return deleted

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        conn = sqlite3.connect(str(self.CACHE_DB))
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM resolution_cache")
        total_entries = cursor.fetchone()[0]

        cursor.execute("SELECT SUM(hits) FROM resolution_cache")
        total_hits = cursor.fetchone()[0] or 0

        cursor.execute(
            "SELECT COUNT(*) FROM resolution_cache WHERE timestamp > ?",
            (time.time() - self.TTL_SECONDS,),
        )
        active_entries = cursor.fetchone()[0]

        conn.close()

        db_size = 0
        if self.CACHE_DB.exists():
            db_size = self.CACHE_DB.stat().st_size

        return {
            "total_entries": total_entries,
            "active_entries": active_entries,
            "total_hits": total_hits,
            "db_path": str(self.CACHE_DB),
            "db_size_bytes": db_size,
        }
