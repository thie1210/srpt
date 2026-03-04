# Contributing to Py

Thank you for your interest in contributing to Py! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Development Setup](#development-setup)
- [Project Architecture](#project-architecture)
- [Making Contributions](#making-contributions)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Performance](#performance)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)

## Code of Conduct

This project follows the [Python Community Code of Conduct](https://www.python.org/psf/conduct/). By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## Development Setup

### Prerequisites

- Python 3.9 or higher
- pip or another package manager

### Installation

```bash
# Clone the repository
git clone https://github.com/psf/py.git
cd py

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode with all dev tools
pip install -e ".[dev]"

# Install pre-commit hooks (optional)
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_resolver.py

# Run tests matching a pattern
pytest -k "test_install"

# Run only fast tests
pytest -m "not slow"
```

### Code Quality Tools

```bash
# Format code
black src tests

# Sort imports
ruff check --fix src tests

# Type check
mypy src

# Run all checks
ruff check src tests && mypy src && black --check src tests
```

## Project Architecture

Py is designed with a modular architecture:

### Core Modules

- **`fetcher.py`** - Python version management (download, install, manage Python versions)
- **`resolver.py`** / **`parallel_resolver.py`** - Dependency resolution using resolvelib
- **`pypi.py`** - PyPI API client with HTTP/2 support
- **`downloader.py`** - Parallel wheel downloader
- **`installer_utils.py`** - Parallel wheel installation
- **`cache.py`** - Resolution cache (24hr TTL, SQLite)
- **`metadata_cache.py`** - Learning cache (7 day TTL, stores dependency graph)
- **`status.py`** - Project status dashboard
- **`installed.py`** - Installed package detection
- **`uninstall.py`** - Package uninstallation
- **`__main__.py`** - CLI entry point

### Key Design Principles

1. **Pure Python First** - No Rust or compiled extensions by default
2. **Async I/O** - Use async/await for all network operations
3. **Learning System** - Cache dependency graphs for faster future resolutions
4. **Minimal Dependencies** - Keep the dependency tree small
5. **PSF-Ready** - Code should be maintainable by the broader Python community

### Performance Strategy

Py achieves performance through:

- **Parallel Operations** - HTTP/2 for metadata fetches, parallel wheel downloads/installation
- **Smart Caching** - Resolution cache (24hr), metadata cache (7 day), learning system
- **Async I/O** - Non-blocking network operations
- **Efficient Algorithms** - Good dependency resolution strategies

## Making Contributions

### Types of Contributions

We welcome:

- 🐛 **Bug fixes** - Fix issues or improve error handling
- ✨ **New features** - Add new functionality (discuss in issue first)
- 📚 **Documentation** - Improve docs, add examples
- 🧪 **Tests** - Increase test coverage
- ⚡ **Performance** - Make py faster
- 🌐 **Translations** - Help internationalize (future)

### Before You Start

1. **Check existing issues** - Your idea might already be tracked
2. **Open an issue** - For major changes, discuss the approach first
3. **Keep it focused** - One feature/fix per PR
4. **Write tests** - All new code needs tests

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add/update tests
5. Update documentation
6. Run all checks (`ruff`, `mypy`, `black`, `pytest`)
7. Commit with clear message
8. Push to your fork
9. Open a Pull Request

## Coding Standards

### Python Style

- Follow [PEP 8](https://pep8.org/)
- Use [Black](https://black.readthedocs.io/) for formatting (line length: 100)
- Use [Ruff](https://docs.astral.sh/ruff/) for linting
- Use type hints everywhere (strict mypy checking)
- Write docstrings for public functions (Google style)

#### Example

```python
from typing import Optional, List


def install_packages(
    packages: List[str],
    python_version: Optional[str] = None,
) -> bool:
    """Install packages into the virtual environment.
    
    Args:
        packages: List of package names to install.
        python_version: Specific Python version to use.
    
    Returns:
        True if installation succeeded, False otherwise.
    
    Raises:
        PackageNotFoundError: If a package cannot be found on PyPI.
    """
    # Implementation
    pass
```

### Code Organization

- Keep functions small and focused (< 50 lines ideal)
- Use descriptive names (not abbreviated)
- Separate concerns (download vs install vs resolve)
- Handle errors explicitly with meaningful messages
- Add type hints for all public APIs

### Error Handling

```python
# Good
try:
    result = await fetch_metadata(package)
except httpx.HTTPError as e:
    raise PackageNotFoundError(f"Failed to fetch metadata for {package}: {e}")

# Avoid
try:
    result = await fetch_metadata(package)
except:  # Bare except
    pass
```

### Async Style

```python
# Good - parallel
results = await asyncio.gather(
    fetch_metadata(pkg1),
    fetch_metadata(pkg2),
    fetch_metadata(pkg3),
)

# Avoid - sequential
result1 = await fetch_metadata(pkg1)
result2 = await fetch_metadata(pkg2)
result3 = await fetch_metadata(pkg3)
```

## Testing

### Test Requirements

- All new code must have tests
- Aim for >90% code coverage
- Test edge cases and error conditions
- Use fixtures for common setup
- Mark slow tests with `@pytest.mark.slow`

### Test Organization

```
tests/
├── test_resolver.py       # Resolver tests
├── test_pypi.py          # PyPI client tests
├── test_fetcher.py       # Version manager tests
├── test_installer.py     # Installation tests
└── conftest.py           # Shared fixtures
```

### Example Test

```python
import pytest
from py.resolver import resolve


def test_resolve_simple_package():
    """Test resolving a single package with no dependencies."""
    result = resolve(["requests"])
    assert "requests" in [r.name for r in result]


@pytest.mark.asyncio
async def test_parallel_fetch():
    """Test parallel metadata fetch."""
    from py.parallel_resolver import fetch_version_metadata_batch
    
    specs = [("requests", "2.32.0"), ("flask", "3.0.0")]
    results = await fetch_version_metadata_batch(None, specs)
    
    assert len(results) == 2
    assert "requests==2.32.0" in results


@pytest.mark.slow
def test_large_dependency_tree():
    """Test resolving a large dependency tree."""
    # This test is slow, mark it
    result = resolve(["django", "djangorestframework"])
    assert len(result) > 10
```

## Performance

### Benchmarking

Use the provided benchmarks:

```bash
# Compare with pip
./benchmark_pip_vs_py.sh

# Test specific scenario
python benchmark_3run.py

# Profile specific code
python -m cProfile -s cumulative src/py/__main__.py install requests
```

### Performance Guidelines

1. **Profile first** - Use profiling tools to find actual bottlenecks
2. **Think async** - Parallelize I/O operations
3. **Cache wisely** - Cache expensive computations, but respect TTL
4. **Measure impact** - Run benchmarks before and after changes
5. **Document improvements** - Note speedup percentages in PRs

### Performance Testing

Always benchmark performance-critical changes:

```python
import time

def test_parallel_vs_sequential(benchmark):
    """Compare parallel vs sequential metadata fetch."""
    packages = ["requests", "flask", "django", "fastapi"]
    
    # Sequential
    start = time.time()
    sequential_fetch(packages)
    sequential_time = time.time() - start
    
    # Parallel
    start = time.time()
    parallel_fetch(packages)
    parallel_time = time.time() - start
    
    # Parallel should be significantly faster
    assert parallel_time < sequential_time * 0.5
```

## Documentation

### Documentation Structure

```
docs/
├── README.md                      # This file
├── STATUS_COMMAND.md              # Status command guide
├── PYTHON_VERSION_MANAGEMENT.md   # Version management guide
├── PARALLEL_INSTALLATION.md       # Parallel installation docs
└── ...                            # Other feature docs
```

### Writing Documentation

- Update docs for new features
- Include usage examples
- Add command examples where relevant
- Keep README.md concise (details go in docs/)
- Use clear, simple language
- Include "Quick Start" sections

### Docstrings

Use Google-style docstrings:

```python
def resolve_dependencies(requirements: List[str]) -> List[Requirement]:
    """Resolve dependencies for given requirements.
    
    Analyzes the requirements list and resolves all transitive
    dependencies using the resolvelib library.
    
    Args:
        requirements: List of requirement strings (e.g., ["requests>=2.0"]).
    
    Returns:
        List of resolved requirements with locked versions.
    
    Raises:
        ResolutionError: If no valid resolution exists.
        NetworkError: If PyPI is unreachable.
    
    Example:
        >>> resolve_dependencies(["requests>=2.0"])
        [Requirement('requests==2.32.0'), Requirement('urllib3==2.0.0'), ...]
    
    Note:
        Results are cached for 24 hours to speed up repeated calls.
    """
    pass
```

## Pull Request Process

### Before Submitting

- [ ] Code follows style guidelines (run `black`, `ruff`, `mypy`)
- [ ] Tests pass locally (`pytest`)
- [ ] Coverage maintained or improved
- [ ] Documentation updated
- [ ] CHANGELOG.md updated (if applicable)
- [ ] Commit messages are clear

### PR Title Format

Use conventional commits:

- `feat: Add py fetch command for installing Python versions`
- `fix: Resolve dependency conflicts in parallel resolver`
- `perf: Speed up wheel installation with thread pool`
- `docs: Add status command documentation`
- `test: Add integration tests for version manager`

### PR Description Template

```markdown
## Description
Brief description of changes

## Motivation
Why is this change needed?

## Changes
- List of main changes

## Testing
How was this tested?

## Performance Impact
Any performance improvements or regressions?

## Breaking Changes
Are there any breaking changes?

## Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Type hints added
```

### Review Process

1. All PRs require at least one review
2. CI must pass (tests, linting, type checks)
3. Address review comments
4. Squash commits before merge (if requested)

### After Merge

- Delete your feature branch
- Monitor for any issues in main
- Update related issues

## Getting Help

- Open an issue for bugs or feature requests
- Use GitHub Discussions for questions
- Tag maintainers for urgent issues

## Recognition

Contributors are recognized in:

- Git history
- Release notes
- CONTRIBUTORS file (coming soon)

Thank you for contributing to Py! 🎉
