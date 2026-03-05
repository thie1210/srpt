# srpt Project Context

## Goal

Build `srpt` (serpent) - A modern, performant Python package manager inspired by uv. The project aims to:
- Be fast through profiling and optimization (not language choice)
- Be simple enough for the Python community to contribute
- Support unified tooling: installer + venv + version management in one CLI
- Make Python onboarding simple and confusion-free
- Ship working and tested software (user's explicit requirement)

## Instructions

- User prefers witty, self-aware, humble tone - NOT pretentious
- "PSF-hopeful" not "PSF-owned" - we can dream, right?
- Focus on craftsmanship, not language superiority
- No "fast because Rust" claims - it's about measuring and optimizing
- "Snakes eat snake food" - Python-built, eating our own dog food
- User is a perfectionist and witty, doesn't take themselves too seriously
- When the user says "go", implement without further confirmation
- Test all changes with real commands
- **Package name is `srpt` (serpent)** - renamed from `py` to avoid PyPI conflicts
- **"fix. we ship working and tested software."** - User's explicit instruction to fix all failing tests before moving forward
- **pyproject.toml naming** - Keep as `pyproject.toml` (NOT `srpt-project.toml`) - it's a Python standard (PEP 517/518/621)

## Discoveries

### Naming Journey
1. **Original name `py`** - Conflicted with existing `py` package on PyPI
2. **Chose `srpt` (serpent)** - Clean, available, strong snake theme

### Architecture Decisions
- SQLite for resolution cache (24hr TTL) and metadata/dependency learning (7 day TTL)
- `httpx` with HTTP/2 for all network operations
- Parallel version metadata pre-fetching before resolution
- Rich library for progress bars and status output
- Safe-by-default: All mutating operations are dry-run, require `--apply` flag
- Python installations stored in `~/.local/share/srpt/python/` (consistent with package name)
- Environment variable: `SRPT_BASE_DIR` (defaults to `~/.local/share/srpt/`)

### Key Bug Fixes
1. **pip-audit format** - Returns packages with `vulns` array, not flat vulnerability list
2. **Version arithmetic** - `Version(__version__) + 1` doesn't work; use `f"{v.major}.{v.minor + 1}.{v.micro}"`
3. **venv Python version detection** - Check `lib_path.parent.name` (e.g., "python3.13"), not `lib_path.name` ("site-packages")
4. **Data directory consistency** - Changed from `~/.local/share/py/` to `~/.local/share/srpt/` in v0.2.16

## Accomplished

### ✅ Phase 1: Foundation (Complete) - v0.2.0 through v0.2.15

**Core Features:**
- Self-update command (`srpt update --self`)
- Security audit command (`srpt audit`)
- Health check command (`srpt health`)
- Enhanced status command with health summary
- Python compatibility checking
- **Rebuild command** (`srpt rebuild --with-version X.Y`)

**Testing:**
- 42/42 tests passing (100%)
- Comprehensive test suite for health, audit, self_update

**Releases:**
- v0.2.0-v0.2.11: Core features
- v0.2.12: All tests fixed
- v0.2.13: Rebuild command
- v0.2.14: Fixed version display consistency
- v0.2.15: Fixed rebuild command Python path detection
- v0.2.16: Changed data directory to ~/.local/share/srpt/ (was ~/.local/share/py/)
- v0.2.17: Fixed all 'py' -> 'srpt' naming in user-facing messages
- v0.2.18: Fixed remaining 'PY UPDATE:' message in actual update path
- v0.2.19: Fixed self-update extraction to handle py->srpt repo name transition
- v0.2.20: Fixed health check to use 'srpt_version' instead of 'py_version', comprehensive README update

## Current State

**Latest Release:** v0.2.20 (2026-03-05)
- All user-facing messages now use 'srpt' instead of 'py'
- Health check displays version correctly
- Self-update handles both 'py' and 'srpt' directory names for smooth transition
- Data directory at `~/.local/share/srpt/` (consistent with package name)
- Environment variables: `SRPT_BASE_DIR`, `SRPT_BIN_DIR`
- All tests passing (42/42)
- Ready for Phase 2

## Next Steps

**Phase 2 (v0.3.x):**
- EOL checking with endoflife.date API (plan created at `.opencode/plans/eol-checking-system.md`)
- `srpt upgrade` - Major version upgrades with try/revert/apply
- Lock file support

**Phase 3 (v0.4.0):**
- Enhanced security features
- Compatibility checking improvements

## Relevant files / directories

```
srpt/
├── .opencode/plans/
│   ├── updates-upgrades-health-system.md  # Phase 1-3 implementation plan (Phase 1 complete)
│   └── eol-checking-system.md             # EOL checking plan (ready to implement)
├── src/srpt/
│   ├── __init__.py              # Version: "0.2.20"
│   ├── __main__.py              # CLI entry point, command routing
│   ├── rebuild.py               # Rebuild command
│   ├── health.py                # Health diagnostics, compatibility checking
│   ├── status.py                # Project status dashboard
│   ├── audit.py                 # Security audit (pip-audit wrapper)
│   ├── self_update.py           # Self-update from GitHub releases
│   ├── update.py                # Update command routing
│   ├── fetcher.py               # Python version management (downloads to ~/.local/share/srpt/)
│   └── utils/
│       ├── confirm.py           # --apply flag pattern
│       ├── constraints.py       # Version constraint parsing
│       ├── backup_manager.py    # Backup management
│       └── pypi_client.py       # PyPI API helpers
├── tests/
│   ├── test_health.py           # 16 tests for health command
│   ├── test_audit.py            # 12 tests for audit
│   ├── test_self_update.py      # 11 tests for self-update
│   ├── test_pypi_simple.py      # 1 test
│   ├── test_resolver.py         # 1 test
│   └── test_resolver_httpx.py   # 1 test
├── install.sh                   # Unix installer
├── install.ps1                  # Windows installer
├── pyproject.toml              # name="srpt", version="0.2.20"
└── README.md
```
