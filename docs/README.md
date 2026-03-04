# Py Documentation

Welcome to the Py documentation! This directory contains detailed guides and references for all features.

## Getting Started

- **[Main README](../README.md)** - Quick start and overview
- **[CONTRIBUTING.md](../CONTRIBUTING.md)** - How to contribute
- **[CHANGELOG.md](../CHANGELOG.md)** - Version history

## Feature Documentation

### Python Version Management

- **[PYTHON_VERSION_MANAGEMENT.md](PYTHON_VERSION_MANAGEMENT.md)** - Complete guide to installing and managing Python versions
  - Installing Python versions with `py fetch`
  - Listing available and installed versions
  - Using `--with-version` flag
  
### Package Management

- **[STATUS_COMMAND.md](STATUS_COMMAND.md)** - Project status dashboard
  - Understanding tracked vs manual dependencies
  - Reading the status output
  - Syncing dependencies

- **[STATUS_QUICK_REF.md](STATUS_QUICK_REF.md)** - Quick reference for status command

### Performance

- **[PARALLEL_INSTALLATION.md](PARALLEL_INSTALLATION.md)** - Parallel wheel installation
- **[PARALLEL_INSTALLATION_FINAL.md](PARALLEL_INSTALLATION_FINAL.md)** - Final implementation and results

### Implementation Details

- **[COMPLETE_OPTIMIZATION_JOURNEY.md](COMPLETE_OPTIMIZATION_JOURNEY.md)** - Full optimization journey and benchmarks
- **[PARALLEL_METADATA_COMPLETE.md](PARALLEL_METADATA_COMPLETE.md)** - Parallel metadata fetching implementation

## Implementation History

These documents track the development journey:

- **[BOOTSTRAP_COMPLETE.md](BOOTSTRAP_COMPLETE.md)** - Zero-Python bootstrap implementation
- **[BENCHMARKS.md](BENCHMARKS.md)** - Benchmark methodology and results
- **[IMPROVEMENTS_SUMMARY.md](IMPROVEMENTS_SUMMARY.md)** - Summary of all improvements

## Quick Links

### Common Commands

```bash
py status              # Show project dashboard
py install <pkg>       # Install packages
py fetch 3.14          # Install Python 3.14
py versions            # List Python versions
py list                # List installed packages
```

### Key Concepts

- **Tracked dependencies**: Packages listed in `pyproject.toml` (team-friendly)
- **Manual dependencies**: Packages installed in `.venv` (individual work)
- **Learning system**: Caches dependency relationships for faster future resolutions
- **Parallel operations**: HTTP/2 downloads, parallel metadata fetch, parallel installation

### Architecture

```
py/
├── src/py/
│   ├── fetcher.py          # Python version management
│   ├── parallel_resolver.py # Parallel resolution
│   ├── pypi.py             # PyPI client
│   ├── downloader.py       # Wheel downloader
│   ├── installer_utils.py  # Wheel installer
│   ├── cache.py            # Resolution cache
│   ├── metadata_cache.py   # Learning system
│   └── status.py           # Status dashboard
├── docs/
├── tests/
└── .github/
```

## Contributing

Found a bug or have a feature request? Check out:

1. [Contributing Guide](../CONTRIBUTING.md)
2. [GitHub Issues](https://github.com/psf/py/issues)
3. [GitHub Discussions](https://github.com/psf/py/discussions)

## License

MIT License - see [LICENSE](../LICENSE) file.
