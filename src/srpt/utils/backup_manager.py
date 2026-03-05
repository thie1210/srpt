"""
Backup management for safe upgrades.

Backup naming: .venv.backup.upgrade.YYYY-MM-DD.<info>
Example: .venv.backup.upgrade.2024-03-04.django-4.2
"""

import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict


class BackupManager:
    """Manages backups for safe upgrade operations."""

    BACKUP_PATTERN = ".venv.backup.upgrade.{date}.{info}"
    METADATA_FILE = ".backup-metadata.json"

    def __init__(self, project_root: Path):
        """
        Initialize backup manager.

        Args:
            project_root: Path to the project root directory
        """
        self.project_root = project_root
        self.venv_path = project_root / ".venv"

    def create_backup(self, info: str) -> Path:
        """
        Create a backup of the current .venv.

        Args:
            info: Description of the backup (e.g., "django-4.2", "python-3.12")

        Returns:
            Path to the created backup

        Raises:
            ValueError: If .venv doesn't exist
            OSError: If backup creation fails
        """
        if not self.venv_path.exists():
            raise ValueError(f"No .venv found at {self.venv_path}")

        # Generate backup name with date
        date = datetime.now().strftime("%Y-%m-%d")
        backup_name = self.BACKUP_PATTERN.format(date=date, info=info)
        backup_path = self.project_root / backup_name

        # Check if backup already exists for today
        if backup_path.exists():
            # Add timestamp to make unique
            timestamp = datetime.now().strftime("%H%M%S")
            backup_name = self.BACKUP_PATTERN.format(date=date, info=f"{info}.{timestamp}")
            backup_path = self.project_root / backup_name

        # Copy .venv to backup
        print(f"  Creating backup: {backup_name}")
        shutil.copytree(self.venv_path, backup_path)

        # Save metadata
        metadata = {
            "created": datetime.now().isoformat(),
            "info": info,
            "original_path": str(self.venv_path),
            "backup_path": str(backup_path),
        }

        # Try to get Python version if possible
        try:
            python_version = self._get_python_version(backup_path)
            metadata["python_version"] = python_version
        except Exception:
            pass

        metadata_file = backup_path / self.METADATA_FILE
        metadata_file.write_text(json.dumps(metadata, indent=2))

        print(f"  ✓ Backup created: {backup_path.name}")
        return backup_path

    def restore_backup(self, backup_path: Path) -> bool:
        """
        Restore .venv from a backup.

        Args:
            backup_path: Path to the backup directory

        Returns:
            True if restore succeeded

        Raises:
            ValueError: If backup doesn't exist
            OSError: If restore fails
        """
        if not backup_path.exists():
            raise ValueError(f"Backup not found: {backup_path}")

        print(f"  Restoring from: {backup_path.name}")

        # Remove current .venv if it exists
        if self.venv_path.exists():
            shutil.rmtree(self.venv_path)

        # Copy backup to .venv
        shutil.copytree(backup_path, self.venv_path)

        print(f"  ✓ Restored from backup")
        return True

    def remove_backup(self, backup_path: Path) -> bool:
        """
        Remove a backup.

        Args:
            backup_path: Path to the backup directory

        Returns:
            True if removal succeeded
        """
        if not backup_path.exists():
            return False

        print(f"  Removing backup: {backup_path.name}")
        shutil.rmtree(backup_path)
        print(f"  ✓ Backup removed")
        return True

    def list_backups(self) -> List[Path]:
        """
        List all backups in the project root.

        Returns:
            List of backup paths, sorted by date (newest first)
        """
        backups = []

        for path in self.project_root.iterdir():
            if path.is_dir() and path.name.startswith(".venv.backup.upgrade."):
                backups.append(path)

        # Sort by name (which includes date)
        backups.sort(reverse=True)
        return backups

    def get_latest_backup(self) -> Optional[Path]:
        """
        Get the most recent backup.

        Returns:
            Path to latest backup, or None if no backups exist
        """
        backups = self.list_backups()
        return backups[0] if backups else None

    def get_backup_metadata(self, backup_path: Path) -> Optional[Dict]:
        """
        Get metadata for a backup.

        Args:
            backup_path: Path to the backup directory

        Returns:
            Metadata dict, or None if not found
        """
        metadata_file = backup_path / self.METADATA_FILE
        if not metadata_file.exists():
            return None

        try:
            return json.loads(metadata_file.read_text())
        except Exception:
            return None

    def check_backup_age(self, backup_path: Path) -> int:
        """
        Check the age of a backup in days.

        Args:
            backup_path: Path to the backup directory

        Returns:
            Age in days
        """
        metadata = self.get_backup_metadata(backup_path)
        if not metadata:
            # Fall back to directory modification time
            mtime = datetime.fromtimestamp(backup_path.stat().st_mtime)
            return (datetime.now() - mtime).days

        try:
            created = datetime.fromisoformat(metadata["created"])
            return (datetime.now() - created).days
        except Exception:
            return 0

    def should_ask_about_old_backup(self, backup_path: Path, days: int = 7) -> bool:
        """
        Check if backup is old enough to prompt user.

        Args:
            backup_path: Path to the backup directory
            days: Threshold in days (default: 7)

        Returns:
            True if backup is older than threshold
        """
        age = self.check_backup_age(backup_path)
        return age > days

    def cleanup_old_backups(self, keep_days: int = 7, dry_run: bool = True) -> List[Path]:
        """
        Remove backups older than keep_days.

        Args:
            keep_days: Keep backups newer than this (default: 7)
            dry_run: If True, don't actually remove (just list)

        Returns:
            List of backups that would be/were removed
        """
        to_remove = []

        for backup_path in self.list_backups():
            age = self.check_backup_age(backup_path)
            if age > keep_days:
                to_remove.append(backup_path)

        if not dry_run:
            for backup_path in to_remove:
                self.remove_backup(backup_path)

        return to_remove

    def _get_python_version(self, venv_path: Path) -> str:
        """
        Get Python version from a venv.

        Args:
            venv_path: Path to the venv directory

        Returns:
            Python version string
        """
        # Try to find python executable
        python_paths = [
            venv_path / "bin" / "python",
            venv_path / "bin" / "python3",
            venv_path / "Scripts" / "python.exe",
            venv_path / "Scripts" / "python3.exe",
        ]

        for python_path in python_paths:
            if python_path.exists():
                import subprocess

                result = subprocess.run(
                    [str(python_path), "--version"], capture_output=True, text=True
                )
                if result.returncode == 0:
                    # Output is like "Python 3.11.9"
                    return result.stdout.strip()

        return "unknown"
