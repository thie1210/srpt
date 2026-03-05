# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-03-05

### Changed
- **Renamed project from `py` to `srpt` (serpent)**
- Updated all package imports and references
- Updated installation scripts and documentation
- Reset version to 0.1.0 for new package name

### Why srpt?
- "srpt" = serpent (snake theme) 🐍
- Avoids conflicts with existing `py` package on PyPI
- Honors the "snakes eat snake food" philosophy
- Perfect metaphor: serpents shed skin to grow (like package updates)

## [0.2.21] - 2026-03-05

### Fixed
- Fixed backup naming bug in rebuild command that caused duplicate naming
- Backup names now correctly formatted as `.venv.backup.upgrade.YYYY-MM-DD.python-X.Y`
- Previously created duplicate names like `.venv.backup.upgrade.YYYY-MM-DD.upgrade.YYYY-MM-DD.python-X.Y`

## [0.2.20] - 2026-03-05

### Fixed
- Fixed health check to use 'srpt_version' instead of 'py_version' in output
- Fixed 'unknown' version display in health check
- Updated all test data to use correct key name

## [0.2.19] - 2026-03-05

### Fixed
- Fixed self-update to handle both 'py' and 'srpt' directory names during extraction
- Renamed get_py_install_dir to get_srpt_install_dir
- Added better error messages showing expected extraction paths
- Handles transition from old 'py' repo name to new 'srpt' repo name

## [0.2.18] - 2026-03-05

### Fixed
- Fixed remaining 'PY UPDATE:' message in actual update path (was 'SRPT UPDATE:' only in dry-run)
- Renamed get_py_launcher_path to get_srpt_launcher_path
- Changed PY_BIN_DIR to SRPT_BIN_DIR environment variable

## [0.2.17] - 2026-03-05

### Fixed
- Replaced all 'py' references with 'srpt' in user-facing messages
- Fixed self-update message: 'py is up to date' -> 'srpt is up to date'
- Fixed example commands in fetcher.py
- Renamed check_py_version to check_srpt_version in health.py

## [0.2.16] - 2026-03-05

### Changed
- **BREAKING**: Changed data directory from `~/.local/share/py/` to `~/.local/share/srpt/` for consistency
- Updated all paths to use `SRPT_BASE_DIR` environment variable (was `PY_BASE_DIR`)
- Updated install.ps1 to use srpt naming throughout

### Migration
If you have existing Python installations in `~/.local/share/py/python/`, you can:
1. Move them: `mv ~/.local/share/py/python ~/.local/share/srpt/python`
2. Or re-download with: `srpt fetch <version>`

## [0.2.15] - 2026-03-05

### Fixed
- Fixed rebuild command Python path detection to use ~/.local/share/py/python/ (not ~/.local/share/srpt/python/)
- Aligned rebuild command with fetcher logic for Python installation discovery

## [Unreleased]

### Added
- Python version management with `srpt fetch` command
- `srpt versions` command to list installed Python versions
- `--with-version` flag to specify Python version for scripts
- `srpt status` command for project health dashboard
- `srpt list` command to show installed packages
- `srpt uninstall` command to remove packages
- Parallel wheel installation with progress bar
- HTTP/2 support for all network operations
- Learning system that caches dependency relationships
- Resolution cache with 24hr TTL
- Metadata cache with 7 day TTL
- Case-insensitive package name detection
- Zero-Python bootstrap scripts (`install.sh`, `install.ps1`)

### Performance
- 6.3x faster than pip with learning enabled
- Parallel metadata fetching (up to 114 concurrent requests)
- Parallel wheel downloads via HTTP/2
- Parallel wheel installation via thread pool
- ~40x faster install.sh (optimized file copying)

### Changed
- Changed `--python` flag to `--with-version` for clarity
- Removed decorative headers from status output
- Updated installer output style to match status command
- Optimized install.sh to copy only essential files

### Fixed
- Fixed case-sensitive package name matching in .dist-info detection
- Fixed race condition in parallel wheel installation
- Fixed ellipsis rendering in shell scripts

## [0.1.0] - 2026-01-XX

### Added
- Initial release
- Core package management functionality
- Basic dependency resolution using resolvelib
- Virtual environment management
- Bootstrap installer for zero-Python setup
- PyPI package metadata fetching
- Wheel download and installation

### Architecture
- Async I/O using httpx
- SQLite-based caching
- Modular architecture (fetcher, resolver, installer)

[Unreleased]: https://github.com/psf/py/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/psf/py/releases/tag/v0.1.0
