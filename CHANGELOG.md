# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Python version management with `py fetch` command
- `py versions` command to list installed Python versions
- `--with-version` flag to specify Python version for scripts
- `py status` command for project health dashboard
- `py list` command to show installed packages
- `py uninstall` command to remove packages
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
