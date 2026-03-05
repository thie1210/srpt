# Srpt

[![srpt on GitHub](https://img.shields.io/github/v/release/thie1210/srpt?label=srpt)](https://github.com/thie1210/srpt/releases)
[![Python Versions](https://img.shields.io/pypi/pyversions/srpt.svg)](https://pypi.org/project/srpt/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**A performance profiled package manager**

Srpt is a modern, performant Python package manager inspired by uv. It provides a unified interface for Python version management, package installation, and project workflows—designed to make Python onboarding simple and FUD-free.

## Why Srpt?

- ⚡ **Actually measured**: 6.3x faster than pip through profiling and optimization
- 🐍 **Python-built**: Snakes eat snake food
- 🤞 **PSF-hopeful**: Built with PSF governance in mind (we can dream, right?)
- 📦 **Zero-dependency bootstrap**: Install without any system Python required
- 🔧 **Unified tooling**: Version management + package installation + virtual environments in one CLI
- 🛡️ **Safe by default**: All mutating operations are dry-run, require `--apply` flag

## Quick Install

Bootstraps Python, just run:

**macOS/Linux:**
```bash
curl -sSL https://raw.githubusercontent.com/thie1210/srpt/main/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
```

**Windows (PowerShell):**
```powershell
Invoke-WebRequest -Uri https://raw.githubusercontent.com/thie1210/srpt/main/install.ps1 -OutFile install.ps1
.\install.ps1
$env:PATH += ";$env:USERPROFILE\.local\bin"
```

## Quick Start

```bash
# Start Python interpreter
srpt

# Check project status
srpt status

# Install packages
srpt install requests fastapi

# List installed packages
srpt list

# Install and use specific Python version
srpt fetch 3.14
srpt --with-version 3.14 my_script.py

# See all Python versions
srpt versions

# Check project health
srpt health

# Security audit
srpt audit

# Update srpt itself
srpt update --self
```

**What's a project?** Just a folder with a `.venv` and `pyproject.toml`. That's it. Transform any folder into a project by running `srpt init` or `srpt install <package>`. No ceremony, no complex setup.

## Features

### 🎯 Project Management

A project is just a folder with a `.venv` and `pyproject.toml`. Transform any folder into a project:

```bash
# Initialize a new project (creates pyproject.toml + .venv)
srpt init

# Or just start installing packages (creates .venv automatically)
srpt install requests

# Dashboard showing project status, dependencies, and suggestions
srpt status
```

Output:
```
PROJECT
  ✓ pyproject.toml (myproject)
  ✓ .venv (Python 3.14.3)

PYTHON
  Version: 3.14.3 → Run 'srpt versions' for all
  → Run 'srpt fetch <version>' to install another

PACKAGES
  Installed: 42 → Run 'srpt list' for details

DEPENDENCIES
  Tracked: 5 (requests, flask, django, ...)
  Installed: 42
  Status: ! Out of sync
    → Run 'srpt sync' to synchronize
```

### 📦 Package Management

```bash
# Install packages (fast!)
srpt install requests flask

# Uninstall packages
srpt uninstall old-package

# List installed packages
srpt list
```

### 🐍 Python Version Management

```bash
# Install Python 3.14
srpt fetch 3.14

# Install Python 3.13 (or any version)
srpt fetch 3.13

# List available versions
srpt fetch --available

# List installed versions
srpt versions

# Use specific version
srpt --with-version 3.14 script.py

# Rebuild venv with different Python version
srpt rebuild --with-version 3.13 --apply
```

### 🏥 Health & Security

```bash
# Comprehensive health check
srpt health

# Detailed health check
srpt health --full

# Security audit (uses pip-audit)
srpt audit

# Update srpt itself
srpt update --self

# Check for updates (dry-run)
srpt update --self
```

### ⚡ Performance

Srpt is designed for speed:

- **Parallel operations**: HTTP/2 for downloads, parallel metadata fetches, parallel wheel installation
- **Smart caching**: Resolution cache (24hr TTL), metadata cache (7 day TTL), learning system
- **Learning system**: Remembers dependency relationships for faster future resolutions

**Benchmarks:**

| Scenario | srpt | pip | Improvement |
|----------|----|----|-------------|
| Fresh install | 13.87s | 13.77s | ~same |
| With learning | 4.23s | 13.77s | **6.3x faster** |
| With cache | 0.01s | 13.77s | **1387x faster** |

## Architecture

Srpt is built with a modular, async-first architecture:

```
src/srpt/
├── fetcher.py              # Python version management
├── parallel_resolver.py    # Parallel dependency resolution
├── pypi.py                 # PyPI API client (HTTP/2)
├── downloader.py           # Parallel wheel downloader
├── installer_utils.py      # Parallel wheel installation
├── cache.py                # Resolution cache (SQLite, 24hr TTL)
├── metadata_cache.py       # Learning system (SQLite, 7 day TTL)
├── status.py               # Project status dashboard
├── health.py               # Health diagnostics
├── audit.py                # Security audit
├── self_update.py          # Self-update from GitHub
├── rebuild.py              # Rebuild venv with different Python
├── installed.py            # Installed package detection
└── __main__.py             # CLI entry point
```

### Key Design Decisions

1. **Pure Python**: Python, Python, Python, or compiled extensions by default
2. **Async I/O**: All network operations use async/await
3. **Modular**: Each component is independent and testable
4. **Caching**: Multi-layer caching strategy for performance
5. **Community-focused**: Clean, maintainable code (PSF-hopeful)
6. **Safe by default**: All mutating operations require `--apply` flag

## Comparison with Other Tools

| Feature | srpt | pip | uv | poetry |
|---------|------|-----|----|----|
| Written in | Python | Python | Rust | Python |
| Package installation | ✓ | ✓ | ✓ | ✓ |
| Version management | ✓ | ✗ | ✓ | ✗ |
| Learning system | ✓ | ✗ | ✗ | ✗ |
| Parallel operations | ✓ | Partial | ✓ | Partial |
| Health check | ✓ | ✗ | ✗ | ✗ |
| Security audit | ✓ | ✓ | ✓ | ✗ |
| Self-update | ✓ | ✗ | ✓ | ✗ |
| PSF governance | 🤞 | ✓ | ✗ | ✗ |
| Performance | Fast | Slow | Very fast | Medium |
| Easy to contribute | ✓ | Medium | Hard | Medium |

## Development

```bash
# Clone and install
git clone https://github.com/thie1210/srpt.git
cd srpt
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

Srpt is currently in **pre-alpha** (v0.2.20). Core features are working:

- ✅ Package installation (`srpt install`)
- ✅ Package listing (`srpt list`)
- ✅ Package uninstallation (`srpt uninstall`)
- ✅ Python version management (`srpt fetch`, `srpt versions`)
- ✅ Project status (`srpt status`)
- ✅ Health check (`srpt health`)
- ✅ Security audit (`srpt audit`)
- ✅ Self-update (`srpt update --self`)
- ✅ Rebuild venv (`srpt rebuild --with-version X.Y`)
- ✅ Parallel downloads and installation
- ✅ Learning system for performance
- 🚧 Project initialization (`srpt init`) - coming soon
- 🚧 Dependency tracking (`srpt add`, `srpt remove`, `srpt sync`) - coming soon
- 🚧 Lock file support - coming soon
- 🚧 EOL checking - coming soon

## Roadmap

### v0.3.0 - Enhanced Features (Next)
- EOL checking with endoflife.date API
- `srpt upgrade` - Major version upgrades with try/revert/apply
- Lock file support
- `srpt init` - Initialize new projects
- `srpt add` - Add dependencies to pyproject.toml
- `srpt remove` - Remove dependencies from pyproject.toml
- `srpt sync` - Synchronize venv with pyproject.toml

### v0.4.0 - Advanced Features
- Script metadata (PEP 723)
- Plugin architecture
- Custom repositories
- Enhanced security features

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

- **Issues**: [GitHub Issues](https://github.com/thie1210/srpt/issues)
- **Discussions**: [GitHub Discussions](https://github.com/thie1210/srpt/discussions)
- **Code of Conduct**: [Python Community Code of Conduct](https://www.python.org/psf/conduct/)

## License

MIT License - see [LICENSE](LICENSE) for details.

Hoping the PSF might consider it someday.

## Acknowledgments

Srpt is inspired by:
- [uv](https://github.com/astral-sh/uv) - Fast Rust-based package manager
- [pip](https://github.com/pypa/pip) - The standard Python package installer
- [poetry](https://github.com/python-poetry/poetry) - Modern dependency management
- [pyenv](https://github.com/pyenv/pyenv) - Python version management

---

**Note**: Srpt is currently pre-alpha software. While functional, it's not yet recommended for production use. We welcome feedback and contributions as we work toward a stable v1.0 release.
