#!/usr/bin/env python3
"""Tests for the canonical state resolver (Phase 0C)."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

# Patch PROJECT_ROOT before importing state_resolver
TEST_ROOT = Path(__file__).resolve().parent.parent.parent.parent  # P:/
os.environ.setdefault("PROJECT_ROOT", str(TEST_ROOT))

sys.path.insert(0, str(TEST_ROOT))
import state_resolver as sr
from state_resolver import (
    StateCategory,
    StateTypeEntry,
    Resolution,
    STATE_TYPE_REGISTRY,
    TYPE_NAME_INDEX,
)


# ── Fixtures ──────────────────────────────────────────────────────────────



# ── Type registration tests ──────────────────────────────────────────────

def test_type_index_is_complete() -> None:
    """Every entry in STATE_TYPE_REGISTRY is in TYPE_NAME_INDEX."""
    assert len(TYPE_NAME_INDEX) == len(STATE_TYPE_REGISTRY)
    for entry in STATE_TYPE_REGISTRY:
        assert TYPE_NAME_INDEX[entry.name] is entry


def test_no_duplicate_names() -> None:
    """No two entries share the same type name."""
    names = [e.name for e in STATE_TYPE_REGISTRY]
    assert len(names) == len(set(names))


def test_every_entry_has_category() -> None:
    """All entries have a non-None category."""
    for entry in STATE_TYPE_REGISTRY:
        assert isinstance(entry.category, StateCategory), entry.name


def test_every_entry_has_current_root() -> None:
    """All entries have a current_root."""
    for entry in STATE_TYPE_REGISTRY:
        assert isinstance(entry.current_root, Path), entry.name


# ── classify_filename tests ──────────────────────────────────────────────

class TestClassifyFilename:
    def test_investigation_state_matches(self) -> None:
        e = sr.classify_filename("investigation_state_console_abc.json")
        assert e is not None
        assert e.name == "investigation_state_console"

    def test_followup_context_matches(self) -> None:
        e = sr.classify_filename("followup_context_console_123.json")
        assert e is not None
        assert e.name == "followup_context"

    def test_followup_context_simple(self) -> None:
        e = sr.classify_filename("followup_context.json")
        assert e is not None
        assert e.name == "followup_context"

    def test_anti_sycophancy_subdir(self) -> None:
        """The injector stores files in a subdirectory; the bare name works."""
        e = sr.classify_filename("anti_sycophancy_injector_console_x.json")
        assert e is not None
        assert e.name == "anti_sycophancy_injector"

    def test_session_ledger(self) -> None:
        e = sr.classify_filename("session_ledger_abc123.json")
        assert e is not None
        assert e.name == "session_ledger"

    def test_reasoning_metrics(self) -> None:
        e = sr.classify_filename("reasoning_metrics.jsonl")
        assert e is not None
        assert e.name == "reasoning_metrics"

    def test_tool_use_log(self) -> None:
        e = sr.classify_filename("tool_use_log_console_x.jsonl")
        assert e is not None
        assert e.name == "tool_use_log"

    def test_unknown_type(self) -> None:
        e = sr.classify_filename("some_random_file.json")
        assert e is None

    def test_unknown_no_extension(self) -> None:
        e = sr.classify_filename("nobody_knows")
        assert e is None

    def test_deprecated_agentic_reliability(self) -> None:
        """The .deprecated suffix should still match the stem."""
        e = sr.classify_filename("agentic_reliability_telemetry.jsonl.deprecated")
        assert e is not None
        assert e.name == "agentic_reliability_telemetry"


# ── resolve_type tests ───────────────────────────────────────────────────

class TestResolveType:
    def test_terminal_scoped_returns_terminal_category(self) -> None:
        r = sr.resolve_type("anti_sycophancy_injector", terminal_id="console_t1")
        assert r is not None
        assert r.category == StateCategory.TERMINAL

    def test_terminal_scoped_includes_tid_in_path(self) -> None:
        r = sr.resolve_type("delegation_expected", terminal_id="con_abc")
        assert r is not None
        assert "con_abc" in str(r.primary)

    def test_session_scoped_returns_session_category(self) -> None:
        r = sr.resolve_type("compaction_marker", session_id="sid_example")
        assert r is not None
        assert r.category == StateCategory.SESSION

    def test_session_scoped_includes_sid_in_path(self) -> None:
        r = sr.resolve_type("compaction_marker", session_id="sid_example")
        assert r is not None
        assert "sid_example" in str(r.primary)

    def test_shared_type_returns_shared_category(self) -> None:
        r = sr.resolve_type("hook_ledger")
        assert r is not None
        assert r.category == StateCategory.SHARED

    def test_unknown_type_returns_none(self) -> None:
        r = sr.resolve_type("nonexistent_type_xyz")
        assert r is None

    def test_resolution_has_current_and_primary(self) -> None:
        r = sr.resolve_type("arch_declaration", terminal_id="t1")
        assert r is not None
        assert isinstance(r.current, Path)
        assert isinstance(r.primary, Path)
        # When canonical_root differs, primary != current
        assert r.current != r.primary

    def test_resolution_has_alternate_roots_field(self) -> None:
        r = sr.resolve_type("compaction_marker", session_id="s1")
        assert r is not None
        assert isinstance(r.alternate_roots, list)

    def test_log_type_returns_log_category(self) -> None:
        r = sr.resolve_type("tool_use_log", terminal_id="t1")
        assert r is not None
        assert r.category == StateCategory.LOG

    def test_diagnostic_type(self) -> None:
        r = sr.resolve_type("hook_observability")
        assert r is not None
        assert r.category == StateCategory.DIAGNOSTIC

    def test_cache_type(self) -> None:
        r = sr.resolve_type("cks_cache")
        assert r is not None
        assert r.category == StateCategory.CACHE

    def test_session_ledger_type(self) -> None:
        r = sr.resolve_type("session_ledger")
        assert r is not None
        assert r.category == StateCategory.SESSION_LEDGER

    def test_entry_has_description(self) -> None:
        r = sr.resolve_type("anti_sycophancy_injector")
        assert r is not None
        assert r.entry is not None
        assert len(r.entry.description) > 0

    def test_resolution_with_custom_filename(self) -> None:
        r = sr.resolve_type("auth_gate", session_id="s1", filename="state.json")
        assert r is not None
        assert r.primary.name == "state.json"


# ── matches_filename method ──────────────────────────────────────────────

class TestMatchesFilename:
    def test_prefix_match(self) -> None:
        """Default pattern matches when stem starts with the type name."""
        entry = TYPE_NAME_INDEX["pretool_degraded"]
        assert entry.matches_filename("pretool_degraded_console_abc")
        assert entry.matches_filename("pretool_degraded_tid_shared_pytest")

    def test_no_match(self) -> None:
        entry = TYPE_NAME_INDEX["pretool_degraded"]
        assert not entry.matches_filename("something_else")
        assert not entry.matches_filename("degraded_pretool")

    def test_exact_name_match(self) -> None:
        entry = TYPE_NAME_INDEX["hook_ledger"]
        assert entry.matches_filename("hook_ledger")
        assert entry.matches_filename("hook_ledger_db")


# ── inventory basics ─────────────────────────────────────────────────────

class TestInventory:
    def test_inventory_returns_required_keys(self) -> None:
        inv = sr.inventory()
        for key in ("schema_version", "created_at", "roots", "by_category",
                     "total_files", "total_bytes"):
            assert key in inv, f"missing key: {key}"

    def test_inventory_has_nonzero_files(self) -> None:
        inv = sr.inventory()
        assert inv["total_files"] > 0

    def test_inventory_roots_are_string_keys(self) -> None:
        inv = sr.inventory()
        for root_key, count in inv["roots"].items():
            assert isinstance(root_key, str), root_key
            assert isinstance(count, int)

    def test_by_category_groups_have_paths(self) -> None:
        inv = sr.inventory()
        for cat_name, entries in inv["by_category"].items():
            for entry in entries:
                assert "path" in entry
                assert "state_type" in entry


# ── CLI entry point ──────────────────────────────────────────────────────

class TestCLI:
    def test_resolve_known_type_exit_zero(self) -> None:
        ret = sr.main(["--resolve", "hook_ledger"])
        assert ret == 0

    def test_resolve_unknown_type_exit_one(self) -> None:
        ret = sr.main(["--resolve", "nonexistent"])
        assert ret == 1

    def test_resolve_terminal_scoped(self) -> None:
        ret = sr.main(["--resolve", "followup_context", "--terminal-id", "t1"])
        assert ret == 0

    def test_resolve_session_scoped(self) -> None:
        ret = sr.main(["--resolve", "compaction_marker", "--session-id", "s1"])
        assert ret == 0

    def test_resolve_with_filename(self) -> None:
        ret = sr.main(["--resolve", "auth_gate", "--filename", "state.json"])
        assert ret == 0

    def test_inventory_exit_zero(self) -> None:
        ret = sr.main([])
        assert ret == 0

    def test_inventory_with_output(self, tmp_path: Path) -> None:
        out = tmp_path / "report.json"
        ret = sr.main(["--output", str(out)])
        assert ret == 0
        assert out.exists()
        data = json.loads(out.read_text(encoding="utf-8"))
        assert "roots" in data


# ── Edge cases ───────────────────────────────────────────────────────────

def test_empty_terminal_id_falls_back_to_root() -> None:
    """No terminal_id → path doesn't include tid segment."""
    r = sr.resolve_type("delegation_expected", terminal_id="")
    assert r is not None
    # Should not have a terminal subdirectory
    assert r.primary.parent.name != "delegation_expected"


def test_empty_session_id_falls_back_to_root() -> None:
    r = sr.resolve_type("compaction_marker", session_id="")
    assert r is not None
    assert r.current.parent.name != ""  # still resolves to something
