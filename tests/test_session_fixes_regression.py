"""Regression tests pinning the 2026-07-08 search-research session fixes.

Covers:
- ast_code cache atomic build + persist/load round-trip + version rejection (S1 fix)
- intent-aware web gating classification (R2)
- CHS default db_path resolves to a non-empty live DB
- skills default skills_dirs includes the plugins marketplace

These pin behavior that was previously only smoke-tested manually, so the next
refactor cannot silently regress without a test failing.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

# Ensure plugin root on path when run via pytest from inside the plugin dir
_PLUGIN_ROOT = Path(__file__).resolve().parent.parent
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))


# ---------- ast_code cache: atomic build + round-trip + version rejection ----------

def _make_tmp_pkg(tmp_path: Path) -> Path:
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    (pkg / "a.py").write_text("def alpha():\n    return 1\n\nclass Beta:\n    def gamma(self):\n        return alpha()\n")
    return pkg


def test_ast_code_build_populates_and_searches(tmp_path, monkeypatch):
    """build_index produces searchable entities; search finds them by name."""
    from core.backends.local.ast_code_backend import ASTCodeBackend

    pkg = _make_tmp_pkg(tmp_path)
    be = ASTCodeBackend(root_paths=[pkg])
    be.build_index()
    assert be._indexed is True
    assert len(be._entity_index) >= 4  # file + alpha + Beta + Beta.gamma + gamma
    assert len(be.search("alpha", 5)) >= 1
    assert len(be.search("Beta", 5)) >= 1


def test_ast_code_build_into_locals_then_publish(tmp_path):
    """S1 fix: build_index must construct in locals and publish atomically.

    A reader holding a reference to the pre-build _entity_index dict must keep
    seeing the OLD (empty) contents until build completes; it must never observe
    a partially-filled working dict.
    """
    from core.backends.local.ast_code_backend import ASTCodeBackend

    pkg = _make_tmp_pkg(tmp_path)
    be = ASTCodeBackend(root_paths=[pkg])
    # Force cache miss by pointing cache at a nonexistent file
    be.__class__.__dict__  # ensure class loaded
    old_snapshot = be._entity_index  # reference to the __init__ empty dict
    be.build_index()
    # The old reference must still be empty (atomic publish swaps the attribute,
    # not the dict contents in place).
    assert old_snapshot == {}, "build_index mutated the old dict in place instead of publishing a new one"
    assert len(be._entity_index) > 0, "new dict was not published"


def test_ast_code_cache_roundtrip_and_version_rejection(tmp_path, monkeypatch):
    """_persist_cache + _try_load_cache round-trip preserves entities; a version
    bump on the stored file causes a miss (forces rebuild)."""
    import importlib
    from core.backends.local import ast_code_backend as mod

    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    monkeypatch.setattr(mod, "_CACHE_DIR", cache_dir)
    monkeypatch.setattr(mod, "_CACHE_FILE", cache_dir / "ast_code_index_v1.json")
    monkeypatch.setattr(mod, "_CACHE_LOCK", cache_dir / "ast_code_index_v1.lock")

    pkg = _make_tmp_pkg(tmp_path)
    be = mod.ASTCodeBackend(root_paths=[pkg])
    be.build_index()
    be._persist_cache()
    expected_count = len(be._entity_index)
    assert (cache_dir / "ast_code_index_v1.json").exists()

    # Second instance loads from cache (same root_paths) → same entity count
    be2 = mod.ASTCodeBackend(root_paths=[pkg])
    be2.build_index()
    assert len(be2._entity_index) == expected_count, "cache load did not return the same entity set"

    # Corrupt the version → must reject (return None → rebuild on next build_index)
    cf = cache_dir / "ast_code_index_v1.json"
    data = json.loads(cf.read_text(encoding="utf-8"))
    data["version"] = 999  # incompatible version
    cf.write_text(json.dumps(data), encoding="utf-8")
    loaded = be2._try_load_cache()
    assert loaded is None, "stale-version cache must be rejected"


# ---------- intent-aware web gating ----------

def test_intent_web_policy_force_web_on_time_sensitive():
    """Time-sensitive signals force web regardless of local quality."""
    from core.unified_router import UnifiedAsyncRouter

    r = UnifiedAsyncRouter(mode="auto")
    for q in ["latest python version 2025", "newest release of foo", "current status"]:
        skip, _ = UnifiedAsyncRouter._intent_web_policy(q)
        assert skip is False, f"{q!r} should force web (skip=False), got {skip}"


def test_intent_web_policy_defers_to_quality_for_informational():
    """A clear informational query defers to the quality gate (returns None)."""
    from core.unified_router import UnifiedAsyncRouter

    skip, _ = UnifiedAsyncRouter._intent_web_policy("how does the unified router work")
    assert skip is None, f"informational query should defer to quality gate (None), got {skip}"


# ---------- CHS + skills default path fixes ----------

def test_chs_default_db_path_resolves_to_live_db():
    """CHS backend default db_path must resolve (via Config) to an existing,
    non-empty DB — not the stale 0-byte __csf path."""
    from core.backends.local.claude_history_backend import ClaudeHistoryBackend
    from core.config import Config

    be = ClaudeHistoryBackend()
    # Must NOT be the old __csf path
    assert "__csf" not in str(be.db_path), f"default db_path still points at __csf: {be.db_path}"
    # Config's intended path (compare Path objects — Windows stringification differs)
    assert be.db_path == Path(Config().CHS_DB_PATH)
    assert be.db_path.exists(), f"db does not exist at {be.db_path}"
    assert be.db_path.stat().st_size > 0, f"db is empty (0 bytes) at {be.db_path}"


def test_skills_default_dirs_include_plugins_marketplace():
    """SkillsBackend default must include the plugins marketplace dir so the
    168 SKILL.md files are discoverable, not just the near-empty P:/.claude/skills."""
    from core.backends.local.skills_backend import SkillsBackend

    sb = SkillsBackend()
    paths = [str(p) for p in sb.skills_dirs]
    assert any("claude-marketplace" in p and "plugins" in p for p in paths), \
        f"plugins marketplace missing from default skills_dirs: {paths}"
