# Implementation Plan: Updates, Upgrades & Health System

**Version**: 1.0  
**Date**: 2024-03-04  
**Status**: Ready for Implementation  
**Target Release**: v0.2.0 (Phase 1), v0.3.0 (Phase 2), v0.4.0 (Phase 3)

---

## Overview

**Goal**: Implement a comprehensive update, upgrade, and health system for `py` that is safe by default, user-friendly, and production-ready.

**Philosophy**: All mutating operations are dry-run by default. Users must explicitly use `--apply` to execute changes.

---

## Design Decisions Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Safe-by-default | All commands dry-run, `--apply` to execute | Prevents accidents |
| Self-update command | `py update --self` | Unified command surface, discoverable |
| Backup location | Project root | Easy to find, easy to clean |
| Backup naming | `.venv.backup.upgrade.YYYY-MM-DD.<info>` | Descriptive, sortable |
| Backup retention | Keep, ask if > 7 days | User control |
| Health caching | No cache | Always fresh data |
| pip-audit | Auto-install on first run | Seamless UX |
| Constraint parsing | Smart Hybrid | Safe, predictable, flexible |
| `--try` behavior | Modify `.venv` with backup | Realistic testing |
| Multiple upgrades | One at a time | Safer, easier debugging |
| Revert without try | Error: "nothing to revert to" | Clear feedback |
| Post-rebuild | Auto-run `py health` | Immediate feedback |

---

## Command Reference

### `py status` (Enhanced)
```
$ py status

PROJECT
  ✓ pyproject.toml (myproject)
  ✓ .venv (Python 3.11.9)

PYTHON
  Version: 3.11.9
  ✓ py: 0.1.1 (latest)

PACKAGES
  Installed: 42
  ! Outdated: 2 (django, pillow)
  ! Security: 1 (django EOL April 2024)
  → Run 'py health' for details

DEPENDENCIES
  Tracked: 5
  Status: ✓ In sync

HEALTH
  ✓ Vulnerabilities: 0 found
  ! 2 warnings, 0 errors
  → Run 'py health' for full report
```

### `py health`
```
$ py health

PY HEALTH CHECK
  ✓ py version: 0.1.1 (latest: 0.1.1)
  ✓ Python: 3.11.9
  ✓ Cache: 247 MB

SECURITY
  ✓ Vulnerabilities: 0 found
  ✓ Last audit: 2 hours ago
  ! Django 3.2.18: Security support ends April 2024
    → Run 'py upgrade django' for LTS version

DEPENDENCIES
  ✓ requests 2.31.0 (latest)
  ✓ flask 3.0.0 (latest)
  ! django 3.2.18 (latest: 4.2.11)
  ! pillow 10.0.0 (latest: 10.2.0)
  → Run 'py update' to update all

COMPATIBILITY
  ✓ Python 3.11 → 3.12: 42/42 packages compatible

SUMMARY
  2 warnings, 0 errors
  → Run 'py health --full' for all 42 packages
```

**Flags:**
- `--full` - Show all packages, not just warnings
- `--json` - JSON output for CI/CD
- `--fix` - Auto-fix safe issues

### `py update`
```
$ py update

DRY RUN - No changes will be made

PACKAGES TO UPDATE:
  ✓ django     3.2.18 → 3.2.19  (within >=3.2,<4.0)
  ✓ pillow     10.0.0 → 10.2.0  (within >=10.0)
  ✓ requests   2.31.0 → 2.31.1  (within >=2.28.0)

3 packages can be updated
Run 'py update --apply' to apply changes
```

```
$ py update --self

DRY RUN - No changes will be made

PY UPDATE:
  Current: 0.1.1
  Latest:  0.2.0

CHANGES:
  • New: py update command
  • New: py health command
  • Fix: Parallel installation race condition
  • Security: Update httpx to 0.27.2

Run 'py update --self --apply' to update
```

**Flags:**
- `--apply` - Execute the update
- `--self` - Update py itself
- `--all` - Update all packages (ignore constraints)
- `--security` - Only security updates
- `--check` - Just check for updates (with `--self`)
- `--version <ver>` - Update to specific version (with `--self`)

### `py upgrade`
```
$ py upgrade

AVAILABLE UPGRADES:
  django
    Current: 3.2.18
    Next major: 4.2.11 (LTS until April 2026)
    Constraint: >=3.2,<4.0
    → Run 'py upgrade --try django 4.2' to test
    → Run 'py upgrade --apply django 4.2' to upgrade
  
  python
    Current: 3.11.9
    Next major: 3.12.3
    → Run 'py rebuild --with-version 3.12' to upgrade
```

```
$ py upgrade --try django 4.2

TESTING UPGRADE: django 3.2.18 → 4.2.11

ACTIONS:
  1. Backup current state
  2. Install django 4.2.11 (with ~=4.2 constraint)
  3. Update dependencies
  4. Run health check

BACKUP:
  ✓ Created: .venv.backup.upgrade.2024-03-04.django-4.2

UPGRADING:
  ✓ django 3.2.18 → 4.2.11
  ✓ django-rest 3.14.0 → 3.15.0
  ✓ django-debug-toolbar 3.8.0 → 4.2.0

HEALTH CHECK:
  ✓ All packages compatible
  ! 2 deprecation warnings
  → Check your application manually

STATUS:
  ✓ Upgrade tested successfully
  → Run 'py upgrade --apply django 4.2' to keep changes
  → Run 'py upgrade --revert' to undo
```

**Flags:**
- `--try <package> <version>` - Test upgrade (creates backup)
- `--revert` - Undo last `--try`
- `--apply <package> <version>` - Permanent upgrade

### `py rebuild`
```
$ py rebuild --with-version 3.12

DRY RUN - No changes will be made

PYTHON UPGRADE:
  Current: 3.11.9
  Target:  3.12.3

ACTIONS:
  1. Install Python 3.12.3
  2. Backup current .venv
  3. Remove .venv
  4. Create new .venv with Python 3.12.3
  5. Reinstall 42 packages
  6. Update pyproject.toml (requires-python)

COMPATIBILITY CHECK:
  ✓ 42/42 packages compatible with Python 3.12
  ✓ All dependencies have Python 3.12 wheels

BACKUP:
  ✓ Will create: .venv.backup.upgrade.2024-03-04.python-3.12

Run 'py rebuild --with-version 3.12 --apply' to proceed
```

**Flags:**
- `--with-version <ver>` - Target Python version
- `--apply` - Execute the rebuild
- `--restore` - Restore from last backup
- `--list-backups` - Show available backups

### `py audit`
```
$ py audit

SECURITY AUDIT

VULNERABILITIES:
  ✗ requests 2.28.0
    CVE-2023-32681: Information disclosure
    Severity: MEDIUM (6.5)
    Fixed in: 2.31.0
    → Run 'py update requests --apply'
  
  ✗ pillow 9.5.0
    CVE-2023-44268: Arbitrary code execution
    Severity: HIGH (8.5)
    Fixed in: 10.0.0
    → Run 'py update pillow --apply'

SUMMARY:
  2 vulnerabilities found (1 HIGH, 1 MEDIUM)
  Run 'py audit --fix' to auto-fix all
```

**Flags:**
- `--fix` - Auto-update vulnerable packages
- `--json` - JSON output for CI/CD
- `--ignore <cve>` - Ignore specific CVEs

---

## File Structure

```
src/py/
├── __init__.py
├── __main__.py              # Updated command routing
├── health.py                # Health diagnostics
├── update.py                # Package updates + self-update routing
├── self_update.py           # Self-update logic
├── upgrade.py               # Major version upgrades
├── rebuild.py               # Python version rebuild
├── audit.py                 # Security audit (pip-audit wrapper)
├── backup.py                # Backup management
├── compatibility.py         # Python compatibility checks
├── status.py                # Enhanced with health summary
├── fetcher.py               # Existing
├── parallel_resolver.py     # Existing
├── pypi.py                  # Existing (add version fetching)
├── downloader.py            # Existing
├── installer_utils.py       # Existing
├── install_workflow.py      # Existing
├── cache.py                 # Existing
├── metadata_cache.py        # Existing
├── installed.py             # Existing
├── resolver.py              # Existing
├── uninstall.py             # Existing
└── utils/
    ├── __init__.py
    ├── confirm.py           # --apply flag pattern
    ├── constraints.py       # Version constraint parsing
    ├── backup_manager.py   # Backup file management
    └── pypi_client.py      # PyPI API helpers
```

---

## Implementation Phases

### Phase 1: Foundation (v0.2.0)

**Duration**: 2 weeks  
**Priority**: High - Core safety infrastructure

#### Week 1: Core Utilities & Self-Update

**Day 1-2: Utility Modules**

Create foundational utilities used by all commands.

**Files to create:**
- `src/py/utils/__init__.py`
- `src/py/utils/confirm.py`
- `src/py/utils/constraints.py`
- `src/py/utils/backup_manager.py`
- `src/py/utils/pypi_client.py`

**Key functions:**

`utils/confirm.py`:
```python
def dry_run_header():
    """Print standard dry-run header"""
    print("DRY RUN - No changes will be made\n")

def confirm_apply(apply: bool = False) -> bool:
    """Return True if --apply flag is set"""
    return apply
```

`utils/constraints.py`:
```python
def get_updatable_version(
    package_name: str,
    current_version: str,
    constraint: str
) -> Optional[str]:
    """
    Smart Hybrid approach:
    - Pinned (==): No update
    - Upper bound (<, <=): Respect it
    - >= only: Update to latest
    - ~=: Compatible release
    - No constraint: Latest
    """
```

`utils/backup_manager.py`:
```python
class BackupManager:
    BACKUP_PATTERN = ".venv.backup.upgrade.{date}.{info}"
    
    def create_backup(self, info: str) -> Path
    def restore_backup(self, backup_path: Path) -> bool
    def remove_backup(self, backup_path: Path) -> bool
    def list_backups(self) -> List[Path]
    def get_latest_backup(self) -> Optional[Path]
    def check_backup_age(self, backup_path: Path) -> int
```

`utils/pypi_client.py`:
```python
async def get_package_versions(package_name: str) -> List[str]
async def get_latest_version(package_name: str) -> str
async def get_package_info(package_name: str, version: str) -> dict
```

**Day 3-4: Self-Update**

Implement `py update --self`.

**Files to create:**
- `src/py/self_update.py`

**Files to update:**
- `src/py/__main__.py` - Add `--self` flag to update command
- `src/py/update.py` - Route to self_update when `--self` flag present

**Key functions:**

`self_update.py`:
```python
async def check_for_updates() -> Optional[str]:
    """Check GitHub releases API for latest version"""

async def self_update(
    dry_run: bool = True,
    check_only: bool = False,
    target_version: str = None
):
    """
    Update py to latest or specific version:
    1. Check current version
    2. Fetch latest from GitHub
    3. Download new version
    4. Install dependencies
    5. Update launcher script
    """
```

**Day 5: Testing & Integration**

- Unit tests for utility modules
- Integration tests for self-update
- Manual testing on clean system

**Tests to create:**
- `tests/test_utils_confirm.py`
- `tests/test_utils_constraints.py`
- `tests/test_utils_backup.py`
- `tests/test_self_update.py`

#### Week 2: Package Updates, Audit & Health

**Day 6-7: Package Updates**

Implement `py update` for packages.

**Files to create:**
- `src/py/update.py`

**Files to update:**
- `src/py/pypi.py` - Add version fetching methods

**Key functions:**

`update.py`:
```python
async def check_for_updates(
    project_root: Path,
    packages: List[str] = None
) -> List[dict]:
    """Check for available updates respecting constraints"""

async def update_packages(
    project_root: Path,
    packages: List[str] = None,
    dry_run: bool = True,
    update_all: bool = False,
    security_only: bool = False
):
    """Update packages to latest compatible versions"""
```

**Day 8-9: Security Audit**

Implement `py audit` with pip-audit integration.

**Files to create:**
- `src/py/audit.py`

**Key functions:**

`audit.py`:
```python
def ensure_pip_audit_installed():
    """Install pip-audit if not present"""

async def run_audit(
    project_root: Path,
    fix: bool = False,
    ignore_cves: List[str] = None
) -> List[dict]:
    """Run pip-audit and parse results"""
```

**Day 10-11: Enhanced Status & Health**

Implement `py health` and enhance `py status`.

**Files to create:**
- `src/py/health.py`

**Files to update:**
- `src/py/status.py` - Add health summary section

**Key functions:**

`health.py`:
```python
async def health_check(
    project_root: Path,
    full: bool = False
) -> dict:
    """
    Comprehensive health diagnostics:
    - py version check
    - Python version check
    - Security vulnerabilities
    - Outdated packages
    - Python compatibility matrix
    - Cache status
    """

def format_health_report(health: dict, full: bool = False):
    """Format health report for display"""
```

**Day 12: Testing & Documentation**

- Unit tests for update, audit, health
- Integration tests
- Update README.md
- Create docs/UPDATES_AND_UPGRADES.md
- Create docs/HEALTH_CHECK.md

**Tests to create:**
- `tests/test_update.py`
- `tests/test_audit.py`
- `tests/test_health.py`

**Documentation to create:**
- `docs/UPDATES_AND_UPGRADES.md`
- `docs/HEALTH_CHECK.md`

---

### Phase 2: Advanced Updates (v0.3.0)

**Duration**: 2 weeks  
**Priority**: Medium - Major version upgrades

#### Week 3: Upgrade System

**Day 13-15: Upgrade Command**

Implement `py upgrade` with try/revert/apply workflow.

**Files to create:**
- `src/py/upgrade.py`

**Key functions:**

`upgrade.py`:
```python
class UpgradeManager:
    def get_available_upgrades(self) -> List[dict]:
        """Find packages with major version upgrades available"""
    
    def try_upgrade(
        self,
        package: str,
        target_version: str
    ) -> bool:
        """
        Test upgrade:
        1. Create backup
        2. Install new version
        3. Update dependencies
        4. Run health check
        5. Save state for revert
        """
    
    def revert_upgrade(self) -> bool:
        """Revert last --try"""
    
    def apply_upgrade(
        self,
        package: str,
        target_version: str
    ) -> bool:
        """Permanent upgrade"""
```

**Day 16-17: Testing**

- Unit tests for upgrade
- Integration tests for try/revert/apply workflow
- Manual testing with real packages

**Tests to create:**
- `tests/test_upgrade.py`

#### Week 4: Rebuild System

**Day 18-20: Rebuild Command**

Implement `py rebuild` for Python version upgrades.

**Files to create:**
- `src/py/rebuild.py`
- `src/py/compatibility.py`

**Key functions:**

`rebuild.py`:
```python
class RebuildManager:
    async def check_compatibility(
        self,
        target_python: str
    ) -> dict:
        """Check if all packages are compatible with target Python"""
    
    async def rebuild(
        self,
        target_python: str,
        dry_run: bool = True
    ) -> bool:
        """
        Rebuild project with new Python version:
        1. Install Python version
        2. Backup .venv
        3. Remove .venv
        4. Create new .venv
        5. Reinstall all packages
        6. Update pyproject.toml
        7. Run health check
        """
```

`compatibility.py`:
```python
async def check_python_compatibility(
    packages: List[str],
    target_python: str
) -> dict:
    """Check package compatibility with Python version"""

async def check_wheel_availability(
    packages: List[str],
    target_python: str,
    platform: str
) -> dict:
    """Check if wheels are available for platform"""
```

**Day 21-22: Backup Management**

Implement backup rotation and old backup prompts.

**Files to update:**
- `src/py/backup.py` - Enhance BackupManager

**Key features:**
- Backup naming: `.venv.backup.upgrade.YYYY-MM-DD.<info>`
- Auto-cleanup old backups
- Interactive prompt for backups > 7 days
- Backup metadata tracking

**Day 23-24: Testing & Documentation**

- Unit tests for rebuild
- Integration tests
- Update documentation

**Tests to create:**
- `tests/test_rebuild.py`
- `tests/test_compatibility.py`

---

### Phase 3: Polish & Safety (v0.4.0)

**Duration**: 1 week  
**Priority**: Low - Enhanced features

#### Week 5: Polish

**Day 25-26: Enhanced Security**

- `py health --fix` for safe auto-fixes
- Security advisory integration
- CVE database caching (optional)

**Day 27-28: Compatibility Features**

- Pre-flight checks for `py rebuild`
- Package compatibility matrix improvements
- Platform-specific checks

**Day 29-30: Final Testing & Documentation**

- Full test suite run
- Manual testing checklist
- Documentation review
- Update CHANGELOG.md
- Prepare for v0.2.0 release

---

## CLI Argument Structure

### Updated `__main__.py`

```python
def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    
    # Existing commands
    # install, list, uninstall, fetch, versions
    
    # Enhanced status
    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("--cache", action="store_true")
    
    # New: health
    health_parser = subparsers.add_parser("health")
    health_parser.add_argument("--full", action="store_true")
    health_parser.add_argument("--json", action="store_true")
    health_parser.add_argument("--fix", action="store_true")
    
    # New: update (packages + self)
    update_parser = subparsers.add_parser("update")
    update_parser.add_argument("--apply", action="store_true",
                              help="Apply changes (default is dry-run)")
    update_parser.add_argument("--self", action="store_true", dest="update_self",
                              help="Update py itself")
    update_parser.add_argument("--all", action="store_true",
                              help="Update all packages (ignore constraints)")
    update_parser.add_argument("--security", action="store_true",
                              help="Security updates only")
    update_parser.add_argument("--check", action="store_true",
                              help="Just check for updates (with --self)")
    update_parser.add_argument("--version", metavar="VERSION",
                              help="Update to specific version (with --self)")
    update_parser.add_argument("packages", nargs="*",
                              help="Packages to update (default: all)")
    
    # New: upgrade
    upgrade_parser = subparsers.add_parser("upgrade")
    upgrade_parser.add_argument("--try", nargs=2, metavar=("PACKAGE", "VERSION"),
                               help="Test upgrade")
    upgrade_parser.add_argument("--revert", action="store_true",
                               help="Revert last test upgrade")
    upgrade_parser.add_argument("--apply", nargs=2, metavar=("PACKAGE", "VERSION"),
                               help="Apply upgrade permanently")
    
    # New: rebuild
    rebuild_parser = subparsers.add_parser("rebuild")
    rebuild_parser.add_argument("--with-version", metavar="VERSION",
                               help="Target Python version")
    rebuild_parser.add_argument("--apply", action="store_true")
    rebuild_parser.add_argument("--restore", action="store_true")
    rebuild_parser.add_argument("--list-backups", action="store_true")
    
    # New: audit
    audit_parser = subparsers.add_parser("audit")
    audit_parser.add_argument("--fix", action="store_true")
    audit_parser.add_argument("--json", action="store_true")
    audit_parser.add_argument("--ignore", nargs="+", metavar="CVE")
    
    args = parser.parse_args()
    
    # Command routing
    if args.command == "update":
        if args.update_self:
            # py update --self
            from .self_update import self_update
            asyncio.run(self_update(
                dry_run=not args.apply,
                check_only=args.check,
                target_version=args.version
            ))
        else:
            # py update (packages)
            from .update import update_packages
            asyncio.run(update_packages(
                project_root=Path.cwd(),
                packages=args.packages,
                dry_run=not args.apply,
                update_all=args.all,
                security_only=args.security
            ))
    elif args.command == "health":
        from .health import health_check, format_health_report
        health = asyncio.run(health_check(
            project_root=Path.cwd(),
            full=args.full
        ))
        if args.json:
            print(json.dumps(health, indent=2))
        else:
            format_health_report(health, full=args.full)
    # ... other commands
```

---

## Dependencies

### New Dependencies

**Add to `pyproject.toml`:**
```toml
dependencies = [
    "httpx[http2]>=0.27.0",
    "installer>=0.7.0",
    "packaging>=21.0",
    "resolvelib>=1.0.0",
    "rich>=13.0.0",
    "tomli>=2.0.0",
    "pip-audit>=2.6.0",  # NEW: Security auditing
]
```

---

## Documentation Updates

### Files to Create

**`docs/UPDATES_AND_UPGRADES.md`**:
- Philosophy: Safe by default
- `py update` usage
- `py update --self` usage
- `py upgrade` workflow
- `py rebuild` usage
- Backup management
- Best practices

**`docs/HEALTH_CHECK.md`**:
- `py health` usage
- Understanding health report
- Fixing common issues
- CI/CD integration

### Files to Update

**`README.md`**:
- Add to Quick Start
- Add to Features section
- Update command list

**`CHANGELOG.md`**:
- Add v0.2.0 release notes

---

## Testing Strategy

### Unit Tests

- `tests/test_utils_confirm.py`
- `tests/test_utils_constraints.py`
- `tests/test_utils_backup.py`
- `tests/test_self_update.py`
- `tests/test_update.py`
- `tests/test_audit.py`
- `tests/test_health.py`
- `tests/test_upgrade.py`
- `tests/test_rebuild.py`
- `tests/test_compatibility.py`

### Integration Tests

- End-to-end update workflow
- Try/revert/apply upgrade workflow
- Rebuild workflow
- Backup/restore workflow

### Manual Testing Checklist

- [ ] `py status` shows health summary
- [ ] `py health` shows full diagnostics
- [ ] `py health --full` shows all packages
- [ ] `py health --json` outputs valid JSON
- [ ] `py update` shows dry-run
- [ ] `py update --apply` actually updates
- [ ] `py update --all` ignores constraints
- [ ] `py update --self` checks for py updates
- [ ] `py update --self --apply` updates py
- [ ] `py upgrade` shows available upgrades
- [ ] `py upgrade --try` creates backup
- [ ] `py upgrade --revert` restores backup
- [ ] `py upgrade --apply` makes permanent
- [ ] `py rebuild --with-version` shows dry-run
- [ ] `py rebuild --apply` actually rebuilds
- [ ] `py rebuild --restore` restores backup
- [ ] `py audit` runs security scan
- [ ] `py audit --fix` auto-fixes vulnerabilities
- [ ] Backup naming follows pattern
- [ ] Old backup prompt works
- [ ] Compatibility check works

---

## Edge Cases & Error Handling

### Backup Management

**Multiple backups exist:**
```
$ py rebuild --with-version 3.12

! Multiple backups found:
  1. .venv.backup.upgrade.2024-03-01.django-4.2 (3 days old)
  2. .venv.backup.upgrade.2024-02-28.flask-3.0 (6 days old)

Which backup to restore? [1/2/skip]:
```

**Backup is > 7 days old:**
```
$ py rebuild --with-version 3.12

! Old backup found: .venv.backup.upgrade.2024-02-20.django-4.2 (12 days old)
Keep it? [y/N]:
```

**No backup to revert:**
```
$ py upgrade --revert

Error: Nothing to revert to
No upgrade test in progress. Run 'py upgrade --try <package> <version>' first.
```

### Version Constraints

**Pinned package:**
```
$ py update django

DRY RUN - No changes will be made

PACKAGES TO UPDATE:
  ! django 3.2.18 (pinned with ==)
    → Remove version pin to allow updates
    → Or use 'py upgrade django' for major version change
```

**Upper bound prevents update:**
```
$ py update django

DRY RUN - No changes will be made

PACKAGES TO UPDATE:
  ! django 3.2.18 (constrained to <4.0)
    Latest within constraint: 3.2.19
    Latest overall: 4.2.11
    → Run 'py update django --apply' to update to 3.2.19
    → Run 'py upgrade django 4.2' to upgrade to 4.x
```

### Compatibility Issues

**Incompatible packages for Python upgrade:**
```
$ py rebuild --with-version 3.12

DRY RUN - No changes will be made

COMPATIBILITY CHECK:
  ✗ 4 packages incompatible with Python 3.12:
    • old-package 1.0.0 (requires Python <3.12)
    • legacy-lib 2.0.0 (no Python 3.12 wheel)
    • broken-dep 3.0.0 (dependency conflict)
    • outdated-tool 1.5.0 (deprecated)
  
  Options:
    → Update incompatible packages first: py update old-package legacy-lib
    → Or force rebuild: py rebuild --with-version 3.12 --apply --force
```

### Self-Update Issues

**No internet connection:**
```
$ py update --self

Error: Cannot check for updates
Network error: Unable to reach github.com
Check your internet connection and try again.
```

**Already on latest version:**
```
$ py update --self

✓ py is up to date
Current version: 0.1.1
Latest version:  0.1.1
```

**Mutual exclusivity:**
```
$ py update --self django

Error: Cannot use --self with package names
--self updates py itself, not packages
→ Run 'py update django' to update packages
→ Run 'py update --self' to update py
```

---

## Success Criteria

### Phase 1 Complete When:
- [ ] `py update --self` works end-to-end
- [ ] `py update` respects all constraint types
- [ ] `py audit` detects and reports vulnerabilities
- [ ] `py status` shows health summary
- [ ] `py health` shows full diagnostics
- [ ] All unit tests pass
- [ ] Documentation updated

### Phase 2 Complete When:
- [ ] `py upgrade --try` creates backup and tests
- [ ] `py upgrade --revert` restores correctly
- [ ] `py upgrade --apply` makes permanent
- [ ] `py rebuild` upgrades Python version
- [ ] Backup management works correctly
- [ ] All integration tests pass
- [ ] Documentation complete

### Phase 3 Complete When:
- [ ] `py health --fix` auto-fixes issues
- [ ] Compatibility checks work
- [ ] All edge cases handled
- [ ] Full test coverage
- [ ] Documentation reviewed
- [ ] Ready for v0.2.0 release

---

## Open Questions for Implementation

1. **GitHub API rate limits**: For `py update --self`, should we:
   - Use unauthenticated API (60 req/hour)?
   - Support GitHub token for higher limits?
   - Cache version check results (24hr)?

2. **Backup compression**: Should we:
   - Copy .venv as-is (fast, but large)?
   - Compress backups (slow, but small)?
   - Let user choose with flag?

3. **`py health` performance**: For large projects (100+ packages):
   - Check all packages sequentially?
   - Use parallel checks?
   - Cache PyPI responses?

4. **`py upgrade` dependency updates**: When upgrading Django 3.2 → 4.2:
   - Auto-update compatible dependencies?
   - Prompt for each dependency?
   - Show summary and ask once?

5. **Rollback on failure**: If `py rebuild` fails mid-way:
   - Auto-restore from backup?
   - Leave broken state for manual fix?
   - Ask user what to do?

---

## Recommendations for Open Questions

1. **GitHub API rate limits**: Use unauthenticated API with 24hr cache
2. **Backup compression**: Copy .venv as-is (simplicity over optimization)
3. **`py health` performance**: Use parallel checks for performance
4. **`py upgrade` dependency updates**: Show summary and ask once
5. **Rollback on failure**: Auto-restore from backup on failure

---

## Next Steps

**Begin Phase 1 implementation:**
1. Create utility modules (Day 1-2)
2. Implement self-update (Day 3-4)
3. Testing & integration (Day 5)
4. Implement package updates (Day 6-7)
5. Implement security audit (Day 8-9)
6. Implement health check (Day 10-11)
7. Testing & documentation (Day 12)

---

**Plan Status**: ✅ Ready for Implementation
