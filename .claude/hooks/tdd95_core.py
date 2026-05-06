#!/usr/bin/env python3
"""
TDD-95 Core - Simplified state management for frictionless TDD.

Design Principles:
- Default ON: TDD is the default, not the exception
- Auto-Scaffold: Tests created automatically when impl files appear
- Smart Detection: Recognize when TDD is needed vs not
- Progressive Enhancement: Simple path -> full TDD cycle
- Graceful Degradation: Never block without offering a path forward

State Model (simplified from original 6-phase):
- NONE: No test file exists
- TEST_EXISTS: Test file created, not yet run
- FAILING: Test runs but fails (RED)
- PASSING: Test passes (GREEN)
- COMPLETE: TDD cycle done, can refactor
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path

try:
    from __lib.file_lock import FileLock
except ImportError:
    from file_lock import FileLock  # type: ignore

# Cache for config - avoids N+1 loading during MultiEdit
_config_cache: dict | None = None

# =============================================================================
# PATH HANDLING - Windows-safe, pathlib-based everywhere
# =============================================================================


def canonicalize_path(raw: str) -> Path:
    """
    Normalize a raw path string to a canonical Path object.

    This is the SINGLE entry point for all path normalization.
    Handles:
    - Environment variable expansion (~USER, %TEMP%, etc.)
    - Relative path resolution (relative to cwd)
    - Path normalization (resolves .., symlinks)
    - POSIX-style storage for JSON persistence

    Args:
        raw: Raw path string (may contain env vars, backslashes, etc.)

    Returns:
        Absolute, normalized Path object
    """
    if not raw:
        return Path()

    # Expand environment variables first (handles ~USER, %TEMP%, etc.)
    expanded = os.path.expandvars(os.path.expanduser(raw))

    # Convert to Path
    p = Path(expanded)

    # Make absolute if relative
    if not p.is_absolute():
        p = Path.cwd() / p

    # Resolve to canonical form (resolves .., symlinks)
    # But don't fail if path doesn't exist yet
    try:
        p = p.resolve()
    except OSError:
        pass  # Path might not exist yet - that's ok

    return p


def path_to_posix(path: Path) -> str:
    """
    Convert Path to POSIX-style string for JSON storage.

    This ensures Windows paths are stored consistently:
    P:\\project\\file.py -> P:/project/file.py

    Args:
        path: Path object

    Returns:
        POSIX-style path string (forward slashes)
    """
    return path.as_posix()


def path_from_posix(posix_str: str) -> Path:
    """
    Reconstruct Path from POSIX-stored string.

    Args:
        posix_str: POSIX-style path string from storage

    Returns:
        Path object
    """
    return Path(posix_str)


def path_matches_tier(path: Path, pattern: str) -> bool:
    """
    Check if a path matches a glob-style tier pattern.

    Args:
        path: Path object (use canonicalize_path first)
        pattern: Glob pattern (e.g., "src/**/*.py", "**/*.ts")

    Returns:
        True if path matches pattern, False otherwise

    Note on Path.match():
        - Matches against individual path components only
        - Pattern "dir/*.py" matches "file.py" but NOT "dir/file.py"
        - Pattern "**/*.py" matches "file.py" (with **, parent is ignored)
        - For full path matching, use fnmatch or glob
    """
    import fnmatch

    path_str = str(path)

    # Handle ** patterns properly
    if "**/" in pattern:
        # Double-star pattern - match against full path
        # Convert pattern: **/*.md -> *.md
        match_pattern = pattern.replace("**/", "")
        return fnmatch.fnmatch(path.name, match_pattern)

    if pattern.startswith("**"):
        # Pattern like **/*.py - match filename only
        match_pattern = pattern[2:]  # Remove **/
        return fnmatch.fnmatch(path.name, match_pattern)

    if "/" in pattern or "\\" in pattern:
        # Directory-specific pattern like "src/**" - check if path starts with it
        parts = pattern.split("/**")[0] if "/**" in pattern else pattern.split("\\*")[0]
        return fnmatch.fnmatch(path_str, parts + "/*") if "/" in parts else path_str

    # Simple pattern - match filename
    return fnmatch.fnmatch(path.name, pattern)


# =============================================================================
# CONFIG LOADING - From settings.json
# =============================================================================

# Default configuration
DEFAULT_CONFIG = {
    "enabled": True,
    "enforcement_mode": "smart",  # smart, strict, warn, disabled
    "autoscaffold": {
        "enabled": True,
        "on_create": True,
        "on_edit_missing": True,
        "template": "minimal",  # minimal, full
    },
    "gate": {
        "check_test_exists": True,
        "check_test_recency_minutes": 10,
        "check_test_passing": False,
        "block_on_missing": "warn",  # warn, scaffold, block
        "block_on_stale": "suggest",  # suggest, block, allow
    },
    "exemptions": {
        "patterns": [
            "**/__init__.py",
            "**/conftest.py",
            "**/tests/**/*.py",
            "**/test/**/*.py",
            "**/*.md",
            "**/*.txt",
            "**/*.json",
            "**/*.yaml",
            "**/*.yml",
            "**/*.toml",
            "**/*.ini",
        ],
        "directories": [
            "docs",
            "tests",
            "test",
            ".git",
            "__pycache__",
            "node_modules",
            "venv",
            "env",
            "build",
            "dist",
        ],
    },
    "tiers": {
        # Only Python and TypeScript for TDD-95
        "TIER0": {
            "enabled": True,
            "files": ["**/*.py", "**/*.ts", "**/*.tsx"],
            "action": "scaffold",  # scaffold, warn, block
            "description": "Core implementation files - auto-scaffold tests",
        },
        "TIER1": {
            "enabled": True,
            "files": ["src/**", "lib/**", "app/**"],
            "action": "scaffold",
            "description": "Production code - auto-scaffold tests",
        },
        "TIER2": {
            "enabled": False,
            "files": ["experimental/**", "prototype/**"],
            "action": "optional",
            "description": "Experimental code - TDD optional",
        },
    },
    "critical_hooks": {
        "enabled": True,
        "require_integration_tests": True,
        "manifest_path": "P:/.claude/hooks/critical_hooks.json",
    },
}


def load_config() -> dict:
    """
    Load TDD-95 configuration from settings.json.

    Returns merged config: defaults + user overrides.
    Cached after first load to avoid N+1 during MultiEdit.
    """
    global _config_cache
    if _config_cache is not None:
        return _config_cache

    settings_path = Path("P:/.claude/settings.json")

    if not settings_path.exists():
        _config_cache = DEFAULT_CONFIG.copy()
        return _config_cache

    try:
        with open(settings_path, encoding="utf-8") as f:
            settings = json.load(f)

        # Merge tdd95 section if it exists
        tdd95_config = DEFAULT_CONFIG.copy()
        user_config = settings.get("tdd95", {})

        # Deep merge user config over defaults
        for key, value in user_config.items():
            if isinstance(value, dict) and key in tdd95_config:
                tdd95_config[key].update(value)
            else:
                tdd95_config[key] = value

        _config_cache = tdd95_config
        return tdd95_config

    except (json.JSONDecodeError, OSError):
        _config_cache = DEFAULT_CONFIG.copy()
        return _config_cache


# =============================================================================
# MAINTENANCE MODE
# =============================================================================

# These will be defined after STATE_DIR (line ~660)
# MAINTENANCE_STATE_FILE and helpers are defined below

# Deferred maintenance state file - will reference STATE_DIR
MAINTENANCE_STATE_FILE_REF = "P:/.claude/state/tdd95/maintenance.json"


def in_maintenance_mode() -> bool:
    """
    Check if TDD-95 is in maintenance mode.

    Maintenance mode is enabled when:
    - TDD95_MAINTENANCE env var is set to a truthy value, OR
    - P:/.claude/state/tdd95/maintenance.json exists with "enabled": true

    Returns:
        True if maintenance mode is active
    """
    # Check env var first
    if os.environ.get("TDD95_MAINTENANCE", "").lower() in ("1", "true", "yes", "on"):
        return True

    # Check state file
    maintenance_state_file = Path(MAINTENANCE_STATE_FILE_REF)
    if maintenance_state_file.exists():
        try:
            with open(maintenance_state_file, encoding="utf-8") as f:
                state = json.load(f)
                return state.get("enabled", False)
        except (json.JSONDecodeError, OSError):
            pass

    return False


def maintenance_scope_paths() -> list[Path]:
    """
    Get list of files considered in-scope for maintenance mode.

    These are the core TDD-95 files that can be edited during maintenance
    without strict TDD enforcement.

    Returns:
        List of canonical Path objects
    """
    base_paths = [
        "P:/.claude/hooks/tdd95_core.py",
        "P:/.claude/hooks/PreToolUse_tdd95_gate.py",
        "P:/.claude/hooks/PostToolUse_tdd95_autoscaffold.py",
        "P:/.claude/hooks/PostToolUse_tdd95_runner.py",
        "P:/.claude/hooks/critical_hooks.json",
    ]

    # Also include tests directory
    test_pattern = "P:/.claude/hooks/tests/test_tdd95_*.py"

    return [canonicalize_path(p) for p in base_paths] + list(
        Path(test_pattern).parent.glob("test_tdd95_*.py")
    )


def is_in_maintenance_scope(path: Path, config: dict | None = None) -> bool:
    """
    Check if a given file path is within maintenance scope.

    Args:
        path: File path to check
        config: Optional config dict (not used currently, reserved for future)

    Returns:
        True if file is in maintenance scope
    """
    if not in_maintenance_mode():
        return False

    canonical = canonicalize_path(path)
    scope_paths = maintenance_scope_paths()

    # Direct path match
    for scope_path in scope_paths:
        if canonical == scope_path or canonical in scope_path.parents:
            return True

    # Test pattern match
    for scope_path in scope_paths:
        if scope_path.is_dir():
            try:
                # Check if path is relative to scope directory
                relative = canonical.relative_to(scope_path)
                # If we can compute relative path, it's under this scope dir
                if not relative.startswith(".."):
                    return True
            except ValueError:
                # Different drives on Windows, not relative
                pass

    return False


# =============================================================================
# STATE ENUM
# =============================================================================


class TDD95State(Enum):
    """
    Simplified TDD state machine.

    NONE -> TEST_EXISTS -> FAILING -> PASSING -> COMPLETE

    Extended with RED/GREEN/REFACTOR for Three-File Contract enforcement:
    - RED: Test editable, impl editable
    - GREEN: Test locked, impl editable
    - REFACTOR: Test locked, impl editable
    """

    NONE = "none"  # No test file exists
    TEST_EXISTS = "test_exists"  # Test created, not yet run
    FAILING = "failing"  # Test runs but fails (RED)
    PASSING = "passing"  # Test passes (GREEN)
    COMPLETE = "complete"  # TDD cycle done, ready to refactor

    # Extended phases for Three-File Contract
    RED = "red"  # Test editable, impl editable
    GREEN = "green"  # Test locked, impl editable
    REFACTOR = "refactor"  # Test locked, impl editable

    @classmethod
    def from_string(cls, value: str) -> TDD95State:
        """Parse state from string, defaulting to NONE."""
        if not value:
            return cls.NONE

        try:
            return cls(value)
        except ValueError:
            # Handle legacy values from old TDD system
            legacy_map = {
                "idle": cls.NONE,
                "discover": cls.NONE,
                "awaiting_red": cls.TEST_EXISTS,
                "red_confirmed": cls.FAILING,
                "green_confirmed": cls.PASSING,
                "refactoring": cls.COMPLETE,
                # Legacy aliases for extended phases
                "red": cls.RED,
                "green": cls.GREEN,
                "refactor": cls.REFACTOR,
            }
            return legacy_map.get(value.lower(), cls.NONE)

    def can_edit_impl(self) -> bool:
        """Check if implementation file can be edited in this state."""
        return self in (
            TDD95State.FAILING,
            TDD95State.PASSING,
            TDD95State.COMPLETE,
            TDD95State.RED,
            TDD95State.GREEN,
            TDD95State.REFACTOR,
        )

    def can_edit_test(self, file_path: str | Path | None = None) -> bool:
        """
        Check if test file can be edited in this state.

        Three-File Contract: Test files can ONLY be edited in RED phase.
        This prevents accidental test modification during implementation.

        Args:
            file_path: Optional path to check (currently unused, for future
                      per-file granularity if needed). For now, uses global state.

        Returns:
            True only in RED phase (or legacy FAILING state for backward compat)
        """
        # RED phase: tests can be edited
        # Legacy FAILING maps to RED behavior
        return self in (TDD95State.RED, TDD95State.FAILING)

    def is_red_phase(self) -> bool:
        """Check if currently in RED phase (test-first, test-editable)."""
        return self in (TDD95State.RED, TDD95State.FAILING)

    def is_green_phase(self) -> bool:
        """Check if currently in GREEN phase (test-locked, impl-editable)."""
        return self in (TDD95State.GREEN, TDD95State.PASSING)

    def is_refactor_phase(self) -> bool:
        """Check if currently in REFACTOR phase (cleanup, test-locked)."""
        return self == TDD95State.REFACTOR

    def requires_test_run(self) -> bool:
        """Check if state requires running tests."""
        return self == TDD95State.TEST_EXISTS


# =============================================================================
# FILE <-> TEST MAPPING
# =============================================================================


def get_test_candidates(impl_path: Path, config: dict | None = None) -> list[Path]:
    """
    Get candidate test file paths for an implementation file.

    Python:
        src/module.py -> tests/test_module.py
        package/module.py -> tests/test_module.py
        hooks/my_hook.py -> hooks/tests/test_my_hook_unit.py

    TypeScript:
        src/module.ts -> tests/module.test.ts
        app/component.tsx -> tests/component.test.tsx

    Args:
        impl_path: Implementation file path (canonicalized)
        config: TDD-95 config dict (optional)

    Returns:
        List of candidate test paths (may not exist)
    """
    if config is None:
        config = load_config()

    stem = impl_path.stem
    suffix = impl_path.suffix.lower()

    # Find project root
    # Priority: pyproject.toml (Python) > package.json (Node/TS) > .git (repo root)
    project_root = find_project_root(impl_path)
    if not project_root:
        # No project root, use current directory
        project_root = impl_path.parent

    candidates = []

    # Python mapping
    if suffix == ".py":
        # Special case for hooks directory
        if "hooks" in impl_path.parts and impl_path.name != "__init__.py":
            # hooks/module.py -> hooks/tests/test_module_unit.py
            hooks_tests_dir = impl_path.parent / "tests"
            candidates.append(hooks_tests_dir / f"test_{stem}_unit.py")
            candidates.append(hooks_tests_dir / f"test_{stem}_integration.py")
        else:
            # Standard Python: tests/test_module.py
            tests_dir = project_root / "tests"
            candidates.append(tests_dir / f"test_{stem}.py")
            candidates.append(tests_dir / f"{stem}_test.py")

            # Package structure: tests/package/test_module.py
            # Note: __csf is NOT a package structure, so skip it
            if "src" in impl_path.parts:
                rel_path = impl_path.relative_to(project_root)
                parts = list(rel_path.parts)
                if "src" in parts:
                    src_idx = parts.index("src")
                    parts = parts[src_idx + 1 :]  # Remove src/

                if parts and len(parts) > 1:
                    # Only add package path if there's actual directory structure
                    # e.g., src/package/module.py -> tests/package/test_module.py
                    package_tests_dir = tests_dir / Path(*parts[:-1])
                    candidate_path = package_tests_dir / f"test_{stem}.py"
                    if candidate_path not in candidates:
                        candidates.append(candidate_path)

    # TypeScript mapping
    elif suffix in (".ts", ".tsx"):
        # Standard TS: tests/module.test.ts
        tests_dir = project_root / "tests"
        candidates.append(tests_dir / f"{stem}.test.ts")
        candidates.append(tests_dir / f"{stem}.test.tsx")

        # Alternative: __tests__/ directory
        alt_tests_dir = project_root / "__tests__"
        candidates.append(alt_tests_dir / f"{stem}.test.ts")

    return [c for c in candidates if c]  # Filter out None


def find_project_root(start_path: Path) -> Path | None:
    """
    Find project root by walking up from start_path.

    Priority:
    1. .git directory (repository root)
    2. pyproject.toml (Python project)
    3. package.json (Node/TS project)
    """
    path = start_path

    # If file, start from parent
    if path.is_file() or not path.exists():
        path = path.parent

    for parent in [path] + list(path.parents):
        if (parent / ".git").exists():
            return parent
        if (parent / "pyproject.toml").exists():
            return parent
        if (parent / "package.json").exists():
            return parent
        if parent == parent.parent:
            break

    return None


def is_impl_file(path: Path, config: dict | None = None) -> bool:
    """Check if path is an implementation file (not a test)."""
    if config is None:
        config = load_config()

    stem_lower = path.stem.lower()
    parts_str = [p.lower() for p in path.parts]

    # Check if in tests directory
    if "tests" in parts_str or "test" in parts_str:
        return False

    # Check test file patterns
    if stem_lower.startswith("test_") or stem_lower.endswith("_test"):
        return False

    # Check suffix
    if path.suffix.lower() not in (".py", ".ts", ".tsx"):
        return False

    # Check exemptions
    for pattern in config.get("exemptions", {}).get("patterns", []):
        if path_matches_tier(path, pattern):
            return False

    return True


def is_test_file(path: Path, config: dict | None = None) -> bool:
    """Check if path is a test file."""
    if config is None:
        config = load_config()

    stem_lower = path.stem.lower()
    parts_str = [p.lower() for p in path.parts]

    # In tests directory
    if "tests" in parts_str or "test" in parts_str:
        return True

    # Test naming patterns
    if stem_lower.startswith("test_") or stem_lower.endswith("_test"):
        return True

    # .test.ts pattern
    if path.suffix == ".ts" and ".test." in path.name:
        return True

    return False


# =============================================================================
# CRITICAL HOOKS MAPPING
# =============================================================================


@dataclass
class CriticalHookTest:
    """Test requirements for a critical hook."""

    hook_file: str
    required_tests: list[str] = field(default_factory=list)
    requires_integration: bool = False


def load_critical_hooks_manifest() -> dict[str, CriticalHookTest]:
    """
    Load critical hooks manifest.

    Either from manifest file or via naming convention.
    """
    config = load_config()
    manifest_path = Path(
        config.get("critical_hooks", {}).get(
            "manifest_path", "P:/.claude/hooks/critical_hooks.json"
        )
    )

    manifest = {}

    # Try loading from manifest file
    if manifest_path.exists():
        try:
            with open(manifest_path, encoding="utf-8") as f:
                data = json.load(f)
            for hook_file, tests in data.items():
                # Skip comment keys and non-dict values
                if hook_file.startswith("_") or not isinstance(tests, dict):
                    continue
                manifest[hook_file] = CriticalHookTest(
                    hook_file=hook_file,
                    required_tests=tests.get("required_tests", []),
                    requires_integration=tests.get("requires_integration", False),
                )
        except (json.JSONDecodeError, OSError):
            pass

    # Scan hooks directory for convention-based detection
    hooks_dir = Path("P:/.claude/hooks")
    if hooks_dir.exists():
        for hook_file in hooks_dir.glob("*.py"):
            # Skip special files
            if hook_file.name.startswith("_") or hook_file.name in (
                "critical_hooks.py",
                "hook_base.py",
            ):
                continue

            # Check if hook has @critical_hook marker
            try:
                content = hook_file.read_text(encoding="utf-8")
                if "@critical_hook" in content or "CRITICAL_HOOK" in content:
                    stem = hook_file.stem
                    if stem not in manifest:
                        # Derive test names from convention
                        required_tests = [
                            f"tests/test_{stem}_unit.py",
                            f"tests/test_{stem}_integration.py",
                        ]
                        manifest[stem] = CriticalHookTest(
                            hook_file=stem, required_tests=required_tests, requires_integration=True
                        )
            except (OSError, UnicodeDecodeError):
                pass

    return manifest


def get_critical_hook_tests(hook_name: str) -> CriticalHookTest | None:
    """
    Get required test configuration for a critical hook.
    """
    manifest = load_critical_hooks_manifest()

    # Try exact match
    if hook_name in manifest:
        return manifest[hook_name]

    # Try stem match
    hook_stem = Path(hook_name).stem
    if hook_stem in manifest:
        return manifest[hook_stem]

    return None


# =============================================================================
# STATE MANAGEMENT - Multi-terminal coordination
# =============================================================================

# State directory
STATE_DIR = Path("P:/.claude/state/tdd95")
GLOBAL_INDEX_FILE = STATE_DIR / "global.json"
TTL_HOURS = 24


@dataclass
class FileState:
    """State for a single implementation file."""

    impl_path: str  # POSIX-stored
    test_paths: list[str] = field(default_factory=list)  # POSIX-stored
    state: str = TDD95State.NONE.value
    last_test_run: str | None = None  # ISO timestamp
    last_result: str | None = None  # TDD95State value
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class GlobalIndex:
    """Global index shared across terminals."""

    version: str = "1"
    files: dict[str, FileState] = field(default_factory=dict)
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())


class TDD95StateManager:
    """
    Manages TDD-95 state with multi-terminal coordination.

    Architecture:
    - Per-terminal state: P:/.claude/state/tdd95/{terminal_id}/{test_hash}.json
    - Global index: P:/.claude/state/tdd95/global.json

    Terminal isolation prevents cross-contamination.
    Global index enables coordination without git.
    """

    def __init__(self, terminal_id: str | None = None):
        """
        Initialize state manager.

        Args:
            terminal_id: Terminal identifier (auto-detected if None)
        """
        self.terminal_id = terminal_id or self._detect_terminal_id()
        self.state_dir = STATE_DIR / self.terminal_id
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def _detect_terminal_id(self) -> str:
        """Detect terminal ID using existing infrastructure."""
        # Try importing terminal_detection
        try:
            from __lib.terminal_detection import detect_terminal_id

            return detect_terminal_id()
        except ImportError:
            # Fallback to PID-based ID
            return f"pid_{os.getpid()}"

    def _get_state_path(self, key: str) -> Path:
        """Get state file path for a given key."""
        # Use hash of key for filename
        import hashlib

        hash_key = hashlib.md5(key.encode()).hexdigest()[:12]
        return self.state_dir / f"{hash_key}.json"

    def _get_global_index(self) -> GlobalIndex:
        """Load global index."""
        if not GLOBAL_INDEX_FILE.exists():
            return GlobalIndex()

        try:
            with open(GLOBAL_INDEX_FILE, encoding="utf-8") as f:
                data = json.load(f)
            # Reconstruct FileState objects
            files = {}
            for path, state_data in data.get("files", {}).items():
                files[path] = FileState(**state_data)
            return GlobalIndex(
                version=data.get("version", "1"),
                files=files,
                last_updated=data.get("last_updated", ""),
            )
        except (json.JSONDecodeError, OSError):
            return GlobalIndex()

    def _save_global_index(self, index: GlobalIndex) -> None:
        """Save global index atomically."""
        GLOBAL_INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict for JSON serialization
        data = {
            "version": index.version,
            "files": {
                path: {
                    "impl_path": s.impl_path,
                    "test_paths": s.test_paths,
                    "state": s.state,
                    "last_test_run": s.last_test_run,
                    "last_result": s.last_result,
                    "created_at": s.created_at,
                    "updated_at": s.updated_at,
                }
                for path, s in index.files.items()
            },
            "last_updated": datetime.now().isoformat(),
        }

        # Atomic write with temp file
        temp_file = GLOBAL_INDEX_FILE.with_suffix(".tmp")
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            temp_file.replace(GLOBAL_INDEX_FILE)
        except OSError:
            # Clean up temp on error
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except OSError:
                    pass
            raise

    def record_impl_edit(self, impl_path: Path) -> None:
        """
        Record that an implementation file was edited.

        Creates state if needed, sets to TEST_EXISTS if test found.
        """
        impl_key = path_to_posix(impl_path)

        # Find test candidates
        test_candidates = get_test_candidates(impl_path)
        existing_tests = [str(t) for t in test_candidates if t.exists()]

        if not existing_tests:
            state = TDD95State.NONE.value
        else:
            state = TDD95State.TEST_EXISTS.value

        # Create FileState
        file_state = FileState(
            impl_path=impl_key,
            test_paths=[path_to_posix(t) for t in test_candidates],
            state=state,
        )

        # Save to per-terminal file
        state_path = self._get_state_path(impl_key)
        self._save_state_file(state_path, file_state)

        # Update global index - LOCKED for multi-terminal safety
        lock_path = GLOBAL_INDEX_FILE.with_suffix(".lock")
        with FileLock(lock_path, timeout=5.0):
            index = self._get_global_index()
            index.files[impl_key] = file_state
            self._save_global_index(index)

    def _save_state_file(self, state_path: Path, file_state: FileState) -> None:
        """Save state file atomically."""
        data = {
            "impl_path": file_state.impl_path,
            "test_paths": file_state.test_paths,
            "state": file_state.state,
            "last_test_run": file_state.last_test_run,
            "last_result": file_state.last_result,
            "created_at": file_state.created_at,
            "updated_at": datetime.now().isoformat(),
        }

        temp_file = state_path.with_suffix(".tmp")
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            temp_file.replace(state_path)
        except OSError:
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except OSError:
                    pass
            raise

    def record_test_run(
        self, test_path: Path, status: TDD95State, when: datetime | None = None
    ) -> None:
        """
        Record a test run result.

        Updates all impl files that map to this test.
        """
        if when is None:
            when = datetime.now()

        test_key = path_to_posix(test_path)

        # Find all impl files that map to this test - LOCKED for multi-terminal safety
        lock_path = GLOBAL_INDEX_FILE.with_suffix(".lock")
        with FileLock(lock_path, timeout=5.0):
            index = self._get_global_index()

            for impl_key, file_state in index.files.items():
                # Check if this test is in the candidate list
                if test_key in file_state.test_paths:
                    # Update state
                    file_state.state = status.value
                    file_state.last_test_run = when.isoformat()
                    file_state.last_result = status.value
                    file_state.updated_at = when.isoformat()

                    # Save to per-terminal file
                    state_path = self._get_state_path(impl_key)
                    self._save_state_file(state_path, file_state)

            # Save updated global index
            self._save_global_index(index)

    def get_state_for_impl(self, impl_path: Path) -> FileState | None:
        """
        Get current state for an implementation file.
        """
        impl_key = path_to_posix(impl_path)
        index = self._get_global_index()

        # Check if we need to refresh from disk (stale check)
        if self._is_index_stale(index):
            index = self._get_global_index()  # Force reload

        return index.files.get(impl_key)

    def _is_index_stale(self, index: GlobalIndex) -> bool:
        """Check if global index is stale (> 5 seconds old)."""
        try:
            last_updated = datetime.fromisoformat(index.last_updated)
            return (datetime.now() - last_updated) > timedelta(seconds=5)
        except (ValueError, TypeError):
            return True

    def get_test_candidates(self, impl_path: Path) -> list[Path]:
        """Get test candidates for an impl file."""
        state = self.get_state_for_impl(impl_path)

        if state and state.test_paths:
            # Use stored candidates
            return [path_from_posix(p) for p in state.test_paths]

        # Fall back to computation
        return get_test_candidates(impl_path)

    def record_maintenance_edit(self, impl_path: Path) -> None:
        """
        Record that an implementation file was edited during maintenance mode.

        This tracks edits made to TDD-95 core files for later
        verification that tests were run.

        Args:
            impl_path: Path to the implementation file being edited
        """
        impl_key = path_to_posix(impl_path)

        # Load or create maintenance state
        maintenance_file = self.state_dir / "maintenance_edits.json"
        try:
            if maintenance_file.exists():
                with open(maintenance_file, encoding="utf-8") as f:
                    maintenance_edits = json.load(f)
            else:
                maintenance_edits = {}
        except (json.JSONDecodeError, OSError):
            maintenance_edits = {}

        # Record this edit with timestamp
        maintenance_edits[impl_key] = {
            "last_edit": datetime.now().isoformat(),
            "needs_test": True,  # Tests should be run after maintenance
        }

        # Save atomically
        temp_file = maintenance_file.with_suffix(".tmp")
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(maintenance_edits, f, indent=2)
            temp_file.replace(maintenance_file)
        except OSError:
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except OSError:
                    pass

    def list_maintenance_edits(self) -> dict[str, dict]:
        """
        List all files edited during maintenance mode.

        Returns:
            Dict mapping impl_path to maintenance edit record
        """
        maintenance_file = self.state_dir / "maintenance_edits.json"
        if not maintenance_file.exists():
            return {}

        try:
            with open(maintenance_file, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}

    def cleanup_expired(self) -> int:
        """
        Clean up expired state files.

        Returns count of files cleaned.
        """
        cutoff = datetime.now() - timedelta(hours=TTL_HOURS)
        cleaned = 0

        for state_file in self.state_dir.glob("*.json"):
            try:
                with open(state_file, encoding="utf-8") as f:
                    data = json.load(f)

                created_str = data.get("created_at", data.get("updated_at"))
                if created_str:
                    try:
                        created = datetime.fromisoformat(created_str)
                        if created < cutoff:
                            state_file.unlink()
                            cleaned += 1
                    except ValueError:
                        pass
            except (json.JSONDecodeError, OSError, ValueError):
                pass

        return cleaned


# =============================================================================
# TEMPLATES - Auto-scaffolding
# =============================================================================

PYTHON_MINIMAL_TEMPLATE = '''"""Auto-scaffolded test for {module_name}."""

import pytest
from {import_path} import {export_name}


def test_{module_name}_exists():
    """Smoke test: {module_name} can be imported."""
    assert {export_name} is not None


# TODO: Add more tests based on actual functionality
# Run: pytest {test_file} -v
'''

PYTHON_HOOK_TEMPLATE = '''"""Auto-scaffolded test for critical hook: {hook_name}."""

import pytest
import json
import sys
from pathlib import Path

# Add hooks directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from {import_name} import main


def test_{hook_name}_exists():
    """Smoke test: {hook_name} can be imported."""
    assert main is not None


def test_{hook_name}_hook_structure():
    """Test that hook has required main() function."""
    assert callable(main)
    assert hasattr(main, "__call__") or hasattr(main, "__code__")


def test_{hook_name}_input_output():
    """Test hook processes JSON input and outputs JSON."""
    import subprocess

    # Sample input
    test_input = {{"tool_name": "Read", "tool_input": {{"file_path": "test.py"}}}

    result = subprocess.run(
        [sys.executable, "-c", "import json; import sys; from {import_name} import main; main("],
        input=json.dumps(test_input),
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent.parent,
    )

    # Should output valid JSON
    if result.stdout:
        json.loads(result.stdout)


# TODO: Add integration-style tests with realistic tool sequences
# Run: pytest {test_file} -v
'''


def summarize_maintenance_and_enforce_tests() -> dict:
    """
    Summarize maintenance mode activity and identify missing tests.

    This should be called at the end of a maintenance task to ensure
    all modified files have corresponding test updates.

    Returns:
        Dict with:
        - maintenance_mode: bool
        - files_edited: list of file paths
        - tests_needed: list of (file, tests) tuples that need running
        - commands_to_run: suggested pytest/npm commands
    """
    if not in_maintenance_mode():
        return {"maintenance_mode": False, "message": "Not in maintenance mode"}

    # Get list of files edited during maintenance
    maintenance_edits = {}
    try:
        # Import TDD95StateManager lazily to avoid circular import
        from tdd95_core import TDD95StateManager

        state_mgr = TDD95StateManager()
        maintenance_edits = state_mgr.list_maintenance_edits()
    except Exception:
        # If state manager fails, continue with empty dict
        maintenance_edits = {}

    files_edited = list(maintenance_edits.keys())
    tests_needed = []

    # For each edited file, find relevant tests
    for impl_path_str in files_edited:
        impl_path = path_from_posix(impl_path_str)

        # Find relevant test files
        stem = Path(impl_path).stem

        # Map to test files using conventions
        potential_tests = []

        # Check critical_hooks manifest
        try:
            from tdd95_core import load_critical_hooks_manifest

            manifest = load_critical_hooks_manifest()
            if stem in manifest:
                hook_tests = manifest[stem]
                if hook_tests and hook_tests.required_tests:
                    potential_tests.extend(hook_tests.required_tests)
        except Exception:
            pass

        # Also use naming convention
        from tdd95_core import STATE_DIR

        test_patterns = [
            STATE_DIR / f"../tests/test_{stem}_unit.py",
            STATE_DIR / f"../tests/test_{stem}_integration.py",
        ]

        # Filter to existing tests
        existing_tests = [t for t in potential_tests if t.exists()]

        # Determine test command
        test_command = None
        impl_suffix = Path(impl_path).suffix.lower()

        if impl_suffix == ".py":
            test_command = "pytest -xvs"
        elif impl_suffix in (".ts", ".tsx", ".js"):
            test_command = "npm test --"
        elif impl_suffix == ".go":
            test_command = "go test ./..."

        # Build result
        if existing_tests:
            result = {"file": impl_path_str, "tests_found": existing_tests, "status": "tests_exist"}
        else:
            result = {
                "file": impl_path_str,
                "tests_needed": potential_tests,
                "test_command": test_command,
                "status": "needs_tests",
            }
            tests_needed.append((impl_path_str, potential_tests))

    return {
        "maintenance_mode": True,
        "files_edited": files_edited,
        "tests_needed": tests_needed,
        "commands_to_run": _build_test_commands(tests_needed),
    }


def _build_test_commands(tests_needed: list[tuple[str, list[str]]]) -> list[str]:
    """
    Build shell commands to run missing tests.

    Args:
        tests_needed: List of (impl_file, test_files) tuples

    Returns:
        List of command strings to run
    """
    commands = []

    for impl_file, test_files in tests_needed:
        impl_stem = Path(impl_file).stem
        impl_suffix = Path(impl_file).suffix.lower()

        # Group test files by type for the impl
        if not test_files:
            continue

        # Determine test command based on impl suffix
        if impl_suffix == ".py":
            # Run pytest for all test files
            test_dirs = set()
            for t in test_files:
                t_path = Path(t)
                if t_path.suffix == ".py":
                    # Add parent directory for pytest
                    test_dirs.add(str(t_path.parent))
                elif t_path.suffix in (".ts", ".tsx"):
                    # TypeScript tests use npm
                    test_dirs.add(str(t_path.parent))

            if test_dirs:
                commands.append(f"pytest {' '.join(set(test_dirs))}")
        elif impl_suffix in (".ts", ".tsx"):
            commands.append("npm test --")
        elif impl_suffix == ".go":
            commands.append("go test ./...")
        elif impl_suffix in (".js", ".jsx"):
            commands.append("npm test --")

    return commands


TS_MINIMAL_TEMPLATE = """/**
 * Auto-scaffolded test for {module_name}
 */

import {{ {export_name} }} from './{module_path}';

describe('{module_name}', () => {{
  it('should exist', () => {{
    expect({export_name}).toBeDefined();
  }});

  // TODO: Add more tests based on actual functionality
  // Run: npm test -- {test_file}
}});
"""


def get_template_for_impl(impl_path: Path, template_type: str = "minimal") -> str:
    """
    Get appropriate test template for an implementation file.

    Args:
        impl_path: Implementation file path
        template_type: Template style (minimal, full)

    Returns:
        Template string with placeholders
    """
    stem = impl_path.stem
    suffix = impl_path.suffix.lower()

    # Check if this is a critical hook
    is_critical_hook = "hooks" in impl_path.parts and impl_path.name != "__init__.py"

    if suffix == ".py":
        if is_critical_hook:
            # Use critical hook template
            module_name = stem.replace("_", "")
            import_name = module_name
            import_path = f"{impl_path.parent.name}/{stem}"
            return PYTHON_HOOK_TEMPLATE.format(
                hook_name=module_name,
                import_name=import_name,
                module_path=import_path,
                test_file=f"tests/test_{stem}_unit.py",
            )
        else:
            # Determine import path
            parts = impl_path.parts
            if "src" in parts or "__csf" in parts:
                # src/module.py -> module
                import_path = stem
                export_name = stem
            else:
                # module.py -> module
                import_path = stem
                export_name = stem

            return PYTHON_MINIMAL_TEMPLATE.format(
                module_name=stem,
                import_path=import_path,
                export_name=export_name,
                test_file=f"tests/test_{stem}.py",
            )

    elif suffix in (".ts", ".tsx"):
        # Determine import path for TS
        import_path = stem
        export_name = stem
        return TS_MINIMAL_TEMPLATE.format(
            module_name=stem,
            module_path=import_path,
            export_name=export_name,
            test_file=f"tests/{stem}.test.ts",
        )

    # Default to Python
    return PYTHON_MINIMAL_TEMPLATE.format(
        module_name=stem,
        import_path=stem,
        export_name=stem,
        test_file=f"tests/test_{stem}.py",
    )


# =============================================================================
# UTILITIES
# =============================================================================


def is_exempt(path: Path, config: dict | None = None) -> bool:
    """
    Check if path is exempt from TDD enforcement.
    """
    if config is None:
        config = load_config()

    # Check directory exemptions
    parts_str = [p.lower() for p in path.parts]
    for exempt_dir in config.get("exemptions", {}).get("directories", []):
        if exempt_dir.lower() in parts_str:
            return True

    # Check pattern exemptions
    for pattern in config.get("exemptions", {}).get("patterns", []):
        if path_matches_tier(path, pattern):
            return True

    return False


def in_tier(path: Path, tier_name: str, config: dict | None = None) -> bool:
    """
    Check if path matches a tier's file patterns.
    """
    if config is None:
        config = load_config()

    tier = config.get("tiers", {}).get(tier_name, {})
    if not tier.get("enabled", False):
        return False

    for pattern in tier.get("files", []):
        if path_matches_tier(path, pattern):
            return True

    return False


def is_critical_hook(path: Path, config: dict | None = None) -> bool:
    """
    Check if path is a critical hook requiring strict testing.
    """
    if config is None:
        config = load_config()

    if not config.get("critical_hooks", {}).get("enabled", True):
        return False

    # Check if in hooks directory
    if "hooks" not in path.parts:
        return False

    # Check critical hook manifest
    manifest = load_critical_hooks_manifest()
    hook_stem = path.stem

    return hook_stem in manifest or any(hook_stem in h.hook_file for h in manifest.values())


def get_bypass_flag() -> bool:
    """Check if TDD_BYPASS is set."""
    return os.environ.get("TDD_BYPASS", "").lower() in ("1", "true", "yes")


def cleanup_expired_states() -> int:
    """
    Clean up expired state files across all terminals.

    Returns total count cleaned.
    """
    total_cleaned = 0
    cutoff = datetime.now() - timedelta(hours=TTL_HOURS)

    # Scan all terminal directories
    if STATE_DIR.exists():
        for terminal_dir in STATE_DIR.iterdir():
            if not terminal_dir.is_dir():
                continue

            for state_file in terminal_dir.glob("*.json"):
                try:
                    with open(state_file, encoding="utf-8") as f:
                        data = json.load(f)

                    created_str = data.get("created_at", data.get("updated_at"))
                    if created_str:
                        try:
                            created = datetime.fromisoformat(created_str)
                            if created < cutoff:
                                state_file.unlink()
                                total_cleaned += 1
                        except ValueError:
                            pass
                except (json.JSONDecodeError, OSError, ValueError):
                    pass

    return total_cleaned
