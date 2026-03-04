# `py status` Command - Quick Reference

## Usage

```bash
py status              # Dashboard overview
py status --cache      # Include cache statistics
```

## What You'll See

### Scenario 1: New Project (Manual Mode)

When you're just experimenting without `pyproject.toml`:

```
PROJECT
  ℹ No pyproject.toml (manual package management)
  ✗ No .venv found
  → Run 'py install <pkg>' to create one

DEPENDENCIES
  Mode: Manual (no pyproject.toml)
  
  → TRACK workflow (for projects):
    py add <pkg>  (coming soon)
  
  → MANUALLY manage (for experiments):
    py install <pkg>
```

### Scenario 2: Managed Project (Tracked Mode)

When you have `pyproject.toml` and everything is synced:

```
PROJECT
  ✓ pyproject.toml (myproject)
  ✓ .venv (Python 3.14.3)

DEPENDENCIES
  Mode: Tracked
  Tracked: 5 (requests, flask, django, ...)
  Installed: 5
  Status: ✓ Synchronized
```

### Scenario 3: Out of Sync

When installed packages don't match tracked dependencies:

```
DEPENDENCIES
  Mode: Tracked
  Tracked: 5 (requests, flask, django, ...)
  Installed: 42
  Status: ⚠ Out of sync
    Missing: pandas (tracked but not installed)
    Extra: requests (installed but not tracked)
  
  TRACKING workflow (recommended):
    → Run 'py install pandas' to install tracked package
    → Run 'py remove requests' to stop tracking
  
  MANUAL workflow (advanced):
    → Run 'py install <pkg>' (not tracked)
    → Run 'py uninstall <pkg>' (from .venv only)
  
  Or sync automatically:
    → Run 'py sync'
```

## Understanding the Difference

### Local .venv vs Project Dependencies

**Local .venv** (your environment):
- All packages currently installed
- Only exists on your machine
- Found in `.venv/lib/python*/site-packages`
- Use `py list` to see all

**Project Dependencies** (tracked):
- Listed in `pyproject.toml`
- Shared with team members
- Reproducible across machines
- Use `py add`, `py remove`, `py sync`

### Example Workflow

```bash
# 1. Check current status
py status

# 2. Start new project
mkdir myapp && cd myapp

# 3. Check status (no .venv, manual mode)
py status

# 4. Install first package
py install requests

# 5. Check status again (has .venv)
py status

# 6. Initialize project (creates pyproject.toml)
py init

# 7. Track dependencies
py add flask django

# 8. Check status (now in tracked mode)
py status
```

## Cache Information

```bash
py status --cache
```

Shows:
- **Resolution cache**: 24hr TTL, speeds up repeated installs
- **Metadata cache**: 7 day TTL, stores package information
- **Learning relationships**: Dependencies learned from previous installs
- **Total size**: Cache disk usage
- **Location**: Where caches are stored

## Key Features

1. **Automatic domain detection**: Knows if you're in tracked or manual mode
2. **Sync status**: Shows if .venv matches pyproject.toml
3. **Actionable suggestions**: Every section tells you what to do next
4. **Context-aware**: Only shows relevant information
5. **Professional output**: Clean, minimal, color-coded

## Status Indicators

- ✓ Green: Good/exists
- ⚠ Yellow: Warning/out of sync
- ✗ Red: Missing/required
- ℹ Blue: Informational

## Quick Reference Always Shown

At the bottom, relevant commands for your current mode:

**Manual mode:**
```
py install <pkg>      
py list               
py fetch <version>    
```

**Tracked mode:**
```
py add <pkg>          
py remove <pkg>       
py install            
py sync               
```

## Benefits

✓ **Onboarding**: New users understand the difference between venv and tracking
✓ **Diagnostic**: Quickly see if project is set up correctly  
✓ **Discovery**: Learn about commands naturally
✓ **Workflow clarity**: Know which workflow (tracked vs manual) you're using
