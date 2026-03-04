# `py status` Command - Implementation Complete

## Overview

Implemented comprehensive `py status` command that serves as a dashboard + help hybrid to ease onboarding and understand the difference between local .venv and project dependencies.

## Command Options

```bash
py status              # Main dashboard
py status --cache      # Include cache statistics
```

## What It Shows

### 1. PROJECT Section
- Checks for `pyproject.toml` (tracked dependencies mode)
- Checks for `.venv` (virtual environment)
- Shows Python version in .venv

### 2. PYTHON Section
- Currently used Python version
- Number of installed Python versions
- Promotes `py fetch` and `py versions` commands

### 3. PACKAGES Section
- Count of installed packages in .venv
- Promotes `py list` command

### 4. DEPENDENCIES Section
**Two modes:**

**Manual Mode (no pyproject.toml):**
```
DEPENDENCIES
  Mode: Manual (no pyproject.toml)
  Installed: 42 in .venv

  To TRACK dependencies for your project:
    → Run 'py init' to create pyproject.toml (coming soon)
    → Then use 'py add <pkg>' to track packages

  Or continue manually:
    → Run 'py install <pkg>' (not tracked)
```

**Tracked Mode (has pyproject.toml):**
```
DEPENDENCIES
  Mode: Tracked
  Tracked: 6 (httpx, installer, packaging, resolvelib, rich, ...)
  Installed: 19
  Status: ⚠ Out of sync
    Extra: anyio, certifi, h11, h2, ...

  TRACKING workflow (recommended):
    → Run 'py remove anyio' to stop tracking

  MANUAL workflow (advanced):
    → Run 'py install <pkg>' (not tracked)
    → Run 'py uninstall <pkg>' (from .venv only)

  Or sync automatically:
    → Run 'py sync' to synchronize
```

### 5. CACHES Section (with --cache flag)
```
CACHES
  Resolution: 8 cached → 24hr TTL
  Metadata: 39 cached → 7 day TTL
  Learning: 51 relationships
  Size: 23.6 MB
  Location: /Users/you/.local/share/py/cache
```

## Implementation Details

### New Files

**`src/py/status.py`** - Status checking module:
- `get_project_status()` - Check for pyproject.toml and .venv
- `get_python_status()` - Get Python versions info
- `get_package_status()` - Count installed packages
- `get_tracked_dependencies()` - Parse pyproject.toml
- `get_dependency_sync_status()` - Compare tracked vs installed
- `get_cache_stats()` - Query cache databases
- `format_status()` - Rich-formatted output
- `status_command()` - Main entry point

### Modified Files

**`src/py/__main__.py`**:
- Added `status` command
- Added `--cache` flag support
- Added `show_status()` function

**`src/py/cache.py`**:
- Enhanced `stats()` method to include `db_size_bytes`

**`src/py/metadata_cache.py`**:
- Enhanced `get_stats()` method to include `db_size_bytes`

## Key Features

### 1. Clear Mode Distinction
Shows users whether they're in:
- **Tracked mode** (has pyproject.toml, team-friendly)
- **Manual mode** (no pyproject.toml, individual work)

### 2. Context-Aware Help
Promotes relevant commands based on current state:
- If no .venv: suggests `py install`
- If no pyproject.toml: suggests `py init`
- If out of sync: suggests `py sync` or individual commands

### 3. Out-of-Sync Explanation
When dependencies are out of sync, shows:
- **Tracked but not installed**: "Missing: pandas"
- **Installed but not tracked**: "Extra: requests"

### 4. Workflow Options
Clearly presents two workflows:
- **TRACKING workflow** (recommended for projects)
- **MANUAL workflow** (for quick experiments)

### 5. Quick Reference
Always shows relevant commands at the bottom:
```bash
QUICK REFERENCE
  py install <pkg>      Install package manually
  py fetch <version>    Install Python version
  py --help             Show all commands
```

## Testing Results

**Test 1: Clean directory (no .venv, no pyproject.toml)**
```
PROJECT
  ℹ No pyproject.toml (manual package management)
  ✗ No .venv found
  → Run 'py install <pkg>' to create one
```

**Test 2: With pyproject.toml and .venv**
```
PROJECT
  ✓ pyproject.toml (py)
  ✓ .venv exists

DEPENDENCIES
  Mode: Tracked
  Status: ⚠ Out of sync
    Extra: anyio, certifi, h11, ...
```

**Test 3: With --cache flag**
```
CACHES
  Resolution: 8 cached → 24hr TTL
  Metadata: 39 cached → 7 day TTL
  Learning: 51 relationships
  Size: 23.6 MB
```

## Design Decisions

1. **Minimal output by default**: No cache info unless requested
2. **Clear status indicators**: ✓ (good), ⚠ (warning), ✗ (error), ℹ (info)
3. **Inline truncated lists**: Shows first few items + "..." for brevity
4. **Human-readable sizes**: "23.6 MB" instead of bytes
5. **Promotes best practices**: Suggests tracking workflow
6. **Context-aware commands**: Quick reference adapts to current mode

## Benefits

1. **Easier onboarding**: New users see what to do next
2. **Domain clarity**: Clearly separated .venv vs project dependencies
3. **Actionable**: Every section shows what command to run
4. **Discovery**: Users learn about commands naturally
5. **Professional**: Clean, minimal, color-coded output
6. **Diagnostic**: Quickly identify if project is set up correctly

## Usage Examples

```bash
# Check overall status
py status

# Check with cache details
py status --cache

# Typical workflow
py status              # See you're in manual mode
py init                # Create pyproject.toml (coming)
py add requests        # Track + install
py status              # See synchronized status
```

## Future Enhancements

- `py status --json` for tooling integration
- `py status --short` for minimal output
- Show package sizes in .venv
- Show outdated packages
- Integration with `py sync` command

## Status

✅ **Fully functional and tested**

All scenarios working:
- ✓ No .venv, no pyproject.toml
- ✓ Has .venv, no pyproject.toml  
- ✓ Has .venv and pyproject.toml (synced)
- ✓ Has .venv and pyproject.toml (out of sync)
- ✓ With --cache flag
- ✓ Globally installed command
