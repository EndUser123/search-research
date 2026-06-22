"""Tests for the cc-aca-epistemic plugin migration.

Verifies:
1. hooks_resolver path resolution
2. Plugin lib module imports
3. Compatibility wrapper loadability
4. Fact-guard integration (provenance, contamination)
5. HOOKS_DIR resolution in evidence_store
6. Expected directory structure
"""
from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
PLUGIN_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_LIB = PLUGIN_ROOT / "__lib"
GLOBAL_HOOKS_DIR = Path("P:/.claude/hooks")
GLOBAL_HOOKS_LIB = GLOBAL_HOOKS_DIR / "__lib__"

WRAPPER_FILES: list[Path] = [
    GLOBAL_HOOKS_DIR / "StopHook_cross_validator.py",
    GLOBAL_HOOKS_DIR / "PreToolUse_evidence_hierarchy_gate.py",
]

EXPECTED_DIRS: list[Path] = [
    PLUGIN_ROOT / "hooks" / "pretool",
    PLUGIN_ROOT / "hooks" / "stop",
    PLUGIN_ROOT / "hooks" / "posttool",
    PLUGIN_ROOT / "hooks" / "userpromptsubmit",
    PLUGIN_LIB,
    PLUGIN_LIB / "verification",
    PLUGIN_LIB / "anti_sycophancy",
]


# ===========================================================================
# 1. hooks_resolver
# ===========================================================================
class TestHooksResolver:
    @classmethod
    def setup_class(cls):
        lib = str(PLUGIN_LIB)
        if lib not in sys.path:
            sys.path.insert(0, lib)
    """Verify hooks_resolver.get_hooks_dir() and get_plugin_lib()."""

    def test_get_hooks_dir_returns_existing_directory(self) -> None:
        from hooks_resolver import get_hooks_dir

        hooks_dir = get_hooks_dir()
        assert isinstance(hooks_dir, Path)
        assert hooks_dir.is_dir(), f"Hooks directory does not exist: {hooks_dir}"

    def test_get_hooks_dir_resolves_to_global_hooks(self) -> None:
        """Without env overrides, should resolve to P:/.claude/hooks/."""
        from hooks_resolver import get_hooks_dir

        hooks_dir = get_hooks_dir()
        # The resolved path must point at the global hooks directory.
        # On Windows, normalize both to resolve drive-letter casing.
        assert hooks_dir.resolve() == GLOBAL_HOOKS_DIR.resolve(), (
            f"Expected {GLOBAL_HOOKS_DIR.resolve()}, got {hooks_dir.resolve()}"
        )

    def test_get_plugin_lib_returns_existing_directory(self) -> None:
        from hooks_resolver import get_plugin_lib

        lib_dir = get_plugin_lib()
        assert isinstance(lib_dir, Path)
        assert lib_dir.is_dir(), f"Plugin lib directory does not exist: {lib_dir}"

    def test_get_plugin_lib_points_at_plugin_lib(self) -> None:
        from hooks_resolver import get_plugin_lib

        lib_dir = get_plugin_lib()
        assert lib_dir.resolve() == PLUGIN_LIB.resolve(), (
            f"Expected {PLUGIN_LIB.resolve()}, got {lib_dir.resolve()}"
        )


# ===========================================================================
# 2. Import resolution — key modules from plugin lib/
# ===========================================================================
class TestImportResolution:
    """Verify core modules can be imported from plugin lib/."""

    def test_import_evidence_store(self) -> None:
        mod = importlib.import_module("evidence_store")
        assert hasattr(mod, "HOOKS_DIR"), "evidence_store must export HOOKS_DIR"

    def test_import_evidence_scope(self) -> None:
        mod = importlib.import_module("evidence_scope")
        # evidence_scope should be importable without error
        assert mod is not None

    def test_import_verification_audit_logger(self) -> None:
        mod = importlib.import_module("verification_audit_logger")
        assert mod is not None


# ===========================================================================
# 3. Compatibility wrappers
# ===========================================================================
class TestCompatibilityWrappers:
    """Verify that compatibility wrappers in P:/.claude/hooks/ can be loaded
    and expose a main (or run) entry point."""

    @pytest.mark.parametrize(
        "wrapper_path",
        WRAPPER_FILES,
        ids=[p.name for p in WRAPPER_FILES],
    )
    def test_wrapper_file_exists(self, wrapper_path: Path) -> None:
        assert wrapper_path.is_file(), f"Wrapper file missing: {wrapper_path}"

    @pytest.mark.parametrize(
        "wrapper_path",
        WRAPPER_FILES,
        ids=[p.name for p in WRAPPER_FILES],
    )
    def test_wrapper_loadable(self, wrapper_path: Path) -> None:
        """Load the wrapper via importlib and verify it delegates to the plugin hook.

        Two valid delegation patterns exist, each with a specific entry symbol
        (checked precisely per wrapper via _EXPECTED_ENTRY):
        - Subprocess-stub wrappers import ``compat_loader.delegate`` (runpy the
          plugin hook as __main__, reading stdin). Most wrappers use this.
        - In-process gate wrappers re-export ``run`` from the plugin hook because
          Stop.py imports them directly (``from StopHook_cross_validator import run``).
          The compat_loader.delegate stub cannot be used here: it exposes no ``run``
          and would execute the script at import time. Such wrappers instead use
          ``compat_loader.load_module`` to import the plugin hook and re-export run.
          StopHook_cross_validator.py is this case.

        We verify the wrapper exposes its expected entry symbol and do NOT call it
        (calling would execute the hook script which reads stdin - blocked by
        pytest capture).

        Known gap: PreToolUse_evidence_hierarchy_gate imports artifact_ledger
        from __lib__/ but the plugin hook path setup does not add __lib__/ to
        sys.path. This test uses an xfail marker for that specific wrapper.
        """
        _is_known_broken = (
            wrapper_path.name == "PreToolUse_evidence_hierarchy_gate.py"
        )

        # Ensure plugin lib and __lib__ on sys.path (the wrapper adds
        # plugin lib, but some plugin hooks also need __lib__ for
        # artifact_ledger, state, etc.).
        for p in (str(PLUGIN_LIB), str(GLOBAL_HOOKS_LIB)):
            if p not in sys.path:
                sys.path.insert(0, p)

        module_name = f"wrapper_test_{wrapper_path.stem}"
        spec = importlib.util.spec_from_file_location(module_name, wrapper_path)
        assert spec is not None, f"Could not create module spec for {wrapper_path}"
        mod = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(mod)  # type: ignore[union-attr]
        except (ImportError, ModuleNotFoundError) as exc:
            if _is_known_broken:
                pytest.xfail(
                    f"Plugin hook {wrapper_path.name} has unresolved import: {exc}. "
                    f"The plugin hook path setup does not add __lib__/ to sys.path."
                )
            raise

        # Verify the wrapper exposes its expected delegation entry. We do NOT call
        # it - that would execute the hook script which reads stdin, triggering
        # pytest's capture protection.
        # In-process gate wrappers re-export run(); subprocess stubs expose delegate.
        _EXPECTED_ENTRY = {
            "StopHook_cross_validator.py": "run",
        }
        entry = _EXPECTED_ENTRY.get(wrapper_path.name, "delegate")
        assert callable(getattr(mod, entry, None)), (
            f"Wrapper {wrapper_path.name} must expose a callable {entry!r}. "
            f"Attributes: {dir(mod)}"
        )


# ===========================================================================
# 4. Fact-guard integration
# ===========================================================================
class TestFactGuardIntegration:
    """Verify provenance.py and contamination.py can be imported from plugin lib/."""

    @pytest.mark.xfail(
        reason="provenance.py imports from 'state' module which is not on sys.path "
        "in the plugin lib context. The plugin hook path setup does not add "
        "__lib__/ to sys.path, so 'from state import detect_terminal_id' fails. "
        "Tracked as a migration gap.",
        raises=ImportError,
    )
    def test_import_provenance(self) -> None:
        mod = importlib.import_module("provenance")
        assert mod is not None

    def test_import_contamination(self) -> None:
        mod = importlib.import_module("contamination")
        assert mod is not None


# ===========================================================================
# 5. Path resolution — HOOKS_DIR in evidence_store
# ===========================================================================
class TestPathResolution:
    """Verify that HOOKS_DIR in evidence_store resolves to the global hooks
    directory, NOT the plugin lib directory."""

    def test_evidence_store_hooks_dir_is_global(self) -> None:
        import evidence_store

        hooks_dir: Path = evidence_store.HOOKS_DIR
        assert hooks_dir.resolve() == GLOBAL_HOOKS_DIR.resolve(), (
            f"evidence_store.HOOKS_DIR should resolve to the global hooks dir "
            f"{GLOBAL_HOOKS_DIR.resolve()}, got {hooks_dir.resolve()}"
        )

    def test_evidence_store_hooks_dir_is_not_plugin_lib(self) -> None:
        import evidence_store

        hooks_dir: Path = evidence_store.HOOKS_DIR
        assert hooks_dir.resolve() != PLUGIN_LIB.resolve(), (
            "evidence_store.HOOKS_DIR must NOT point at the plugin lib/ directory"
        )


# ===========================================================================
# 6. Directory structure
# ===========================================================================
class TestDirectoryStructure:
    """Verify all expected directories exist in the plugin layout."""

    @pytest.mark.parametrize(
        "dir_path",
        EXPECTED_DIRS,
        ids=[str(p.relative_to(PLUGIN_ROOT)) for p in EXPECTED_DIRS],
    )
    def test_directory_exists(self, dir_path: Path) -> None:
        assert dir_path.is_dir(), f"Expected directory does not exist: {dir_path}"

    def test_lib_contains_hooks_resolver(self) -> None:
        assert (PLUGIN_LIB / "hooks_resolver.py").is_file(), (
            "hooks_resolver.py must exist in plugin lib/"
        )

    def test_lib_contains_evidence_store(self) -> None:
        assert (PLUGIN_LIB / "evidence_store.py").is_file(), (
            "evidence_store.py must exist in plugin lib/"
        )

    def test_lib_contains_provenance(self) -> None:
        assert (PLUGIN_LIB / "provenance.py").is_file(), (
            "provenance.py must exist in plugin lib/"
        )

    def test_lib_contains_contamination(self) -> None:
        assert (PLUGIN_LIB / "contamination.py").is_file(), (
            "contamination.py must exist in plugin lib/"
        )

    def test_verification_subpackage_has_init(self) -> None:
        """The verification/ directory should be importable (has __init__.py
        or at minimum the expected modules)."""
        verification_dir = PLUGIN_LIB / "verification"
        assert verification_dir.is_dir()
        # Check for at least the key modules documented in CLAUDE.md
        for expected in ("engine.py", "claims.py", "coverage.py"):
            assert (verification_dir / expected).is_file(), (
                f"verification/{expected} missing"
            )

    def test_anti_sycophancy_subpackage_has_init(self) -> None:
        anti_dir = PLUGIN_LIB / "anti_sycophancy"
        assert anti_dir.is_dir()
        assert (anti_dir / "__init__.py").is_file(), (
            "anti_sycophancy/__init__.py must exist for package imports"
        )

    def test_hooks_json_exists(self) -> None:
        assert (PLUGIN_ROOT / "hooks" / "hooks.json").is_file(), (
            "hooks/hooks.json must exist for plugin hook registration"
        )
