# Py

[![Py PI](https://img.shields.io/pypi/v/py.svg)](https://pypi.org/project/py/)
[![Python Versions](https://img.shields.io/pypi/pyversions/py.svg)](https://pypi.org/project/py/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**A performance profiled package manager**

Py is a modern, performant Python package manager inspired by uv. It provides a unified interface for Python version management, package installation, and project workflows—designed to make Python onboarding simple and FUD-free.

## Why Py?

- ⚡ **Actually measured**: 6.3x faster than pip through profiling and optimization
- 🐍 **Python-built**: Snakes eat snake food
- 🤞 **PSF-hopeful**: Built with PSF governance in mind (we can dream, right?)
- 📦 **Zero-dependency bootstrap**: Install without any system Python required
- 🔧 **Unified tooling**: Version management + package installation + virtual environments in one CLI

## Quick Install

Bootstraps Python, just run:

**macOS/Linux:**
```bash
curl -sSL https://raw.githubusercontent.com/thie1210/py/v0.1.1/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
```

**Windows (PowerShell):**
```powershell
Invoke-WebRequest -Uri https://raw.githubusercontent.com/thie1210/py/v0.1.1/install.ps1 -OutFile install.ps1
.\install.ps1
$env:PATH += ";$env:USERPROFILE\.local\bin"
```

## Quick Start

```bash
# Start Python interpreter
py

# Check project status
py status

# Install packages
py install requests fastapi

# List installed packages
py list

# Install and use specific Python version
py fetch 3.14
py --with-version 3.14 my_script.py

# See all Python versions
py versions
```

**What's a project?** Just a folder with a `.venv` and `pyproject.toml`. That's it. Transform any folder into a project by running `py init` or `py install <package>`. No ceremony, no complex setup.

## Features

### 🎯 Project Management

A project is just a folder with a `.venv` and `pyproject.toml`. Transform any folder into a project:

```bash
# Initialize a new project (creates pyproject.toml + .venv)
py init

# Or just start installing packages (creates .venv automatically)
py install requests

# Dashboard showing project status, dependencies, and suggestions
py status
```

Output:
```
PROJECT
  ✓ pyproject.toml (myproject)
  ✓ .venv (Python 3.14.3)

PYTHON
  Version: 3.14.3 → Run 'py versions' for all
  → Run 'py fetch <version>' to install another

PACKAGES
  Installed: 42 → Run 'py list' for details

DEPENDENCIES
  Tracked: 5 (requests, flask, django, ...)
  Installed: 42
  Status: ⚠ Out of sync
    → Run 'py sync' to synchronize
```

### 📦 Package Management

```bash
# Install packages (fast!)
py install requests flask

# Uninstall packages
py uninstall old-package

# List installed packages
py list
```

### 🐍 Python Version Management

```bash
# Install Python 3.14
py fetch 3.14

# Install Python 3.13 (or any version)
py fetch 3.13

# List available versions
py fetch --available

# List installed versions
py versions

# Use specific version
py --with-version 3.14 script.py
```

### ⚡ Performance

Py is designed for speed:

- **Parallel operations**: HTTP/2 for downloads, parallel metadata fetches, parallel wheel installation
- **Smart caching**: Resolution cache (24hr TTL), metadata cache (7 day TTL), learning system
- **Learning system**: Remembers dependency relationships for faster future resolutions

**Benchmarks:**

| Scenario | py | pip | Improvement |
|----------|----|----|-------------|
| Fresh install | 13.87s | 13.77s | ~same |
| With learning | 4.23s | 13.77s | **6.3x faster** |
| With cache | 0.01s | 13.77s | **1387x faster** |

## Architecture

Py is built with a modular, async-first architecture:

```
src/py/
├── fetcher.py              # Python version management
├── parallel_resolver.py    # Parallel dependency resolution
├── pypi.py                 # PyPI API client (HTTP/2)
├── downloader.py           # Parallel wheel downloader
├── installer_utils.py      # Parallel wheel installation
├── cache.py                # Resolution cache (SQLite, 24hr TTL)
├── metadata_cache.py       # Learning system (SQLite, 7 day TTL)
├── status.py               # Project status dashboard
├── installed.py            # Installed package detection
└── __main__.py             # CLI entry point
```

### Key Design Decisions

1. **Pure Python**: No Rust or compiled extensions by default
2. **Async I/O**: All network operations use async/await
3. **Modular**: Each component is independent and testable
4. **Caching**: Multi-layer caching strategy for performance
5. **Community-focused**: Clean, maintainable code (PSF-hopeful)

## Comparison with Other Tools

| Feature | py | pip | uv | poetry |
|---------|----|----|----|--------|
| Written in | Python | Python | Rust | Python |
| Package installation | ✓ | ✓ | ✓ | ✓ |
| Version management | ✓ | ✗ | ✓ | ✗ |
| Learning system | ✓ | ✗ | ✗ | ✗ |
| Parallel operations | ✓ | Partial | ✓ | Partial |
| PSF governance | 🤞 | ✓ | ✗ | ✗ |
| Performance | Fast | Slow | Very fast | Medium |
| Easy to contribute | ✓ | Medium | Hard | Medium |

## Development

```bash
# Clone and install
git clone https://github.com/psf/py.git
cd py
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=src

# Format code
black src tests

# Lint code
ruff check src tests

# Type check
mypy src
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## Project Status

Py is currently in **pre-alpha** (v0.1.0). Core features are working:

- ✅ Package installation (`py install`)
- ✅ Package listing (`py list`)
- ✅ Package uninstallation (`py uninstall`)
- ✅ Python version management (`py fetch`, `py versions`)
- ✅ Project status (`py status`)
- ✅ Parallel downloads and installation
- ✅ Learning system for performance
- 🚧 Project initialization (`py init`) - coming soon
- 🚧 Dependency tracking (`py add`, `py remove`, `py sync`) - coming soon
- 🚧 Lock file support - coming soon

## Roadmap

### v0.2.0 - Project Management
- `py init` - Initialize new projects
- `py add` - Add dependencies to pyproject.toml
- `py remove` - Remove dependencies from pyproject.toml
- `py sync` - Synchronize venv with pyproject.toml

### v0.3.0 - Enhanced Features
- Lock file support
- Script metadata (PEP 723)
- Plugin architecture
- Custom repositories

### v1.0.0 - Production Ready
- Full feature parity with pip for core workflows
- Stable API
- Comprehensive documentation
- PSF consideration (hopefully!)

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for:

- Code of Conduct
- Development setup
- Architecture guide
- Testing guidelines
- Pull request process

## Documentation

- [CONTRIBUTING.md](CONTRIBUTING.md) - How to contribute
- [CHANGELOG.md](CHANGELOG.md) - Version history
- [docs/](docs/) - Feature documentation
  - [PYTHON_VERSION_MANAGEMENT.md](docs/PYTHON_VERSION_MANAGEMENT.md)
  - [STATUS_COMMAND.md](docs/STATUS_COMMAND.md)
  - [PARALLEL_INSTALLATION.md](docs/PARALLEL_INSTALLATION.md)

## Community

- **Issues**: [GitHub Issues](https://github.com/psf/py/issues)
- **Discussions**: [GitHub Discussions](https://github.com/psf/py/discussions)
- **Code of Conduct**: [Python Community Code of Conduct](https://www.python.org/psf/conduct/)

## License

MIT License - see [LICENSE](LICENSE) for details.

Hoping the PSF might consider it someday.

## Acknowledgments

Py is inspired by:
- [uv](https://github.com/astral-sh/uv) - Fast Rust-based package manager
- [pip](https://github.com/pypa/pip) - The standard Python package installer
- [poetry](https://github.com/python-poetry/poetry) - Modern dependency management
- [pyenv](https://github.com/pyenv/pyenv) - Python version management

---

**Note**: Py is currently pre-alpha software. While functional, it's not yet recommended for production use. We welcome feedback and contributions as we work toward a stable v1.0 release.
