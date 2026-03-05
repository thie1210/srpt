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
