"""Regression-first tests for gate_residue (FP-feedback loop v1).

Locks in the calibration:
  - confirmed_fp requires an artifact (a referencing tool_use on a block-specific
    token). The /rns regression: prose-only rebuttal => disputed, never confirmed_fp.
  - unresolved when the post-block turn has no reference to the block.
  - Incremental ingestion advances the watermark and never reprocesses.
  - Promotion is one-shot per ledger_id (no duplicate TaskCreate directives).

Gold specimen = sanitized #1415 incident: a Stop_removal_completeness_guard block
whose reason mentions `clip_client.py`, refuted by a Grep targeting clip_client.py.
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
import time
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT / "__lib"))

import gate_residue as gr  # noqa: E402


# --- fixtures ----------------------------------------------------------------

@pytest.fixture
def tmp_state(tmp_path):
    """Isolate ALL state + sources under tmp_path (no real-state pollution).

    Direct assignment to DEFAULT_STATE_ROOT is safe because both debt_store
    and gate_residue hold module-level Path references (not functions), and
    each test gets a fresh tmp_path so there is no inter-test leak.
    """
    state_root = tmp_path / "state"
    state_root.mkdir()

    import debt_store as ds

    ds.DEFAULT_STATE_ROOT = state_root
    gr.DEFAULT_STATE_ROOT = state_root  # from the 'from debt_store import ...' copy

    # Synthetic sources.
    db = tmp_path / "diag.db"
    jsonl = tmp_path / "stop_blocks.jsonl"
    gr.DIAGNOSTICS_DB = db
    gr.STOP_BLOCKS_JSONL = jsonl

    yield {"root": state_root, "db": db, "jsonl": jsonl}


def _make_db(db: Path, rows: list[dict]) -> None:
    con = sqlite3.connect(str(db))
    con.execute(
        """CREATE TABLE hooks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            session_id TEXT NOT NULL,
            terminal_id TEXT NOT NULL,
            turn_id TEXT,
            event TEXT NOT NULL,
            hook_name TEXT NOT NULL,
            event_type TEXT NOT NULL,
            action TEXT NOT NULL,
            injection_preview TEXT,
            injection_length INTEGER,
            reason TEXT,
            duration_ms REAL,
            execution_time_ms REAL,
            timeout_ms INTEGER,
            output_size_bytes INTEGER
        )"""
    )
    for r in rows:
        con.execute(
            "INSERT INTO hooks (id, timestamp, session_id, terminal_id, event, "
            "hook_name, event_type, action, reason) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                r["id"], r["timestamp"], r["session_id"], r["terminal_id"],
                r.get("event", "hook_invoked"), r["hook_name"], "Stop",
                r.get("action", "block"), r["reason"],
            ),
        )
    con.commit()
    con.close()


def _append_jsonl(path: Path, obj: dict) -> None:
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj))
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())


# --- gold specimens (#1415 sanitized) ----------------------------------------

def _clip_block_row() -> dict:
    return {
        "id": 9001,
        "timestamp": "2026-07-10T12:00:00.000000+00:00",
        "session_id": "sess-clip",
        "terminal_id": "console_clip",
        "hook_name": "Stop_removal_completeness_guard",
        "action": "block",
        "reason": (
            "Unverified removal claim. The response asserts `import cli` was "
            "removed from clip_client.py but no Read/Grep on clip_client.py "
            "confirms the deletion. Verify clip_client.py before claiming removal."
        ),
    }


# --- classify_block ----------------------------------------------------------

class TestClassify:
    def test_confirmed_fp_with_artifact(self):
        block = {
            "gate_name": "Stop_removal_completeness_guard",
            "block_reason_excerpt": _clip_block_row()["reason"],
        }
        tools = [
            {"type": "tool_use", "name": "Grep",
             "input": {"pattern": "import cli", "path": "clip_client.py"}},
        ]
        cls, artifact = gr.classify_block(block, tools, "")
        assert cls == "confirmed_fp"
        assert artifact is not None
        assert artifact["tool"] == "Grep"
        assert "clip_client.py" in artifact["target"]
        assert artifact["transcript_pos"] == 0

    def test_disputed_prose_only_no_artifact(self):
        """The /rns regression: 'that's by design' with no tool => disputed."""
        block = {
            "gate_name": "Stop_removal_completeness_guard",
            "block_reason_excerpt": _clip_block_row()["reason"],
        }
        # Prose references the block's specific token (clip_client.py) but no tool.
        text = "That's by design — clip_client.py is a generated shim, not removed."
        cls, artifact = gr.classify_block(block, [], text)
        assert cls == "disputed"
        assert artifact is None

    def test_unresolved_no_reference(self):
        block = {
            "gate_name": "Stop_removal_completeness_guard",
            "block_reason_excerpt": _clip_block_row()["reason"],
        }
        cls, artifact = gr.classify_block(block, [], "")
        assert cls == "unresolved"
        assert artifact is None

    def test_unresolved_unrelated_tool_not_confirmed(self):
        """A generic, unrelated tool call must NOT升级 to confirmed_fp."""
        block = {
            "gate_name": "Stop_removal_completeness_guard",
            "block_reason_excerpt": _clip_block_row()["reason"],
        }
        # Grep on an unrelated file with no block-specific token overlap.
        tools = [{"type": "tool_use", "name": "Grep",
                  "input": {"pattern": "TODO", "path": "README.md"}}]
        cls, artifact = gr.classify_block(block, tools, "")
        assert cls != "confirmed_fp"
        assert artifact is None

    def test_no_misclassify_retry_as_confirmed_fp(self):
        """A block whose same-session retry simply re-ran the SAME claimed tool
        (weak signal) surfaces read-only — it does not get the FP promotion
        unless the tool actually targets the block's specific token. Here the
        retry touches a different identifier not in the reason."""
        block = {
            "gate_name": "Stop_removal_completeness_guard",
            "block_reason_excerpt": (
                "Unverified removal claim re clip_client.py — verify before claiming."
            ),
        }
        tools = [{"type": "tool_use", "name": "Edit",
                  "input": {"file_path": "other_module.py"}}]
        cls, _ = gr.classify_block(block, tools, "")
        assert cls != "confirmed_fp"


def _seed_watermark_zero(tid: str, state_root: Path) -> None:
    """Explicitly seed a watermark at zero so ingest picks up existing rows."""
    p = state_root / "cc-lazy-closure-debt" / "cc-gate-residue" / f"{tid}.watermark.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"db_max_id": 0, "jsonl_byte_offset": 0}), encoding="utf-8")


# --- ingest + watermark ------------------------------------------------------

class TestIngest:
    def test_ingest_db_rows_writes_ledger_and_advances_watermark(self, tmp_state):
        _seed_watermark_zero("console_clip", tmp_state["root"])
        _make_db(tmp_state["db"], [_clip_block_row()])
        rows = gr.ingest_new_blocks("console_clip")
        assert len(rows) == 1
        assert rows[0]["gate_name"] == "Stop_removal_completeness_guard"
        assert rows[0]["classification"] == "unresolved"
        assert rows[0]["ledger_id"].startswith("Stop_removal_completeness_guard:")
        assert rows[0]["source_ref"]["sink"] == "diagnostics.db"
        assert rows[0].get("normalized_gate") == "removal_completeness_guard"
        # Ledger file written.
        ledger = tmp_state["root"] / "cc-lazy-closure-debt" / "cc-gate-residue" / "console_clip.jsonl"
        assert ledger.exists()
        # Watermark advanced to the row's id.
        wm = json.loads(
            (tmp_state["root"] / "cc-lazy-closure-debt" / "cc-gate-residue"
             / "console_clip.watermark.json").read_text()
        )
        assert wm["db_max_id"] == 9001

    def test_incremental_second_call_no_reprocess(self, tmp_state):
        _seed_watermark_zero("console_clip", tmp_state["root"])
        _make_db(tmp_state["db"], [_clip_block_row()])
        first = gr.ingest_new_blocks("console_clip")
        assert len(first) == 1
        second = gr.ingest_new_blocks("console_clip")
        assert second == []
        # Ledger still has exactly one block row.
        ledger = (tmp_state["root"] / "cc-lazy-closure-debt" / "cc-gate-residue"
                  / "console_clip.jsonl")
        count = sum(1 for line in ledger.read_text().splitlines() if line.strip())
        assert count == 1

    def test_incremental_picks_up_only_new_rows(self, tmp_state):
        _seed_watermark_zero("console_clip", tmp_state["root"])
        _make_db(tmp_state["db"], [_clip_block_row()])
        gr.ingest_new_blocks("console_clip")
        # Add a second block with a higher id.
        con = sqlite3.connect(str(tmp_state["db"]))
        con.execute(
            "INSERT INTO hooks (id, timestamp, session_id, terminal_id, event, "
            "hook_name, event_type, action, reason) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (9002, "2026-07-10T12:05:00.000000+00:00", "s2", "t2",
             "hook_invoked", "StopHook_unverified_stance.py", "Stop", "block",
             "Unverified stance on target_module.py"),
        )
        con.commit()
        con.close()
        rows = gr.ingest_new_blocks("console_clip")
        assert len(rows) == 1
        assert rows[0]["source_ref"]["row_id"] == 9002

    def test_ingest_jsonl_tail(self, tmp_state):
        _seed_watermark_zero("tj", tmp_state["root"])
        _append_jsonl(tmp_state["jsonl"], {
            "timestamp": "2026-07-10T12:10:00.000000+00:00",
            "event": "Stop", "gate_name": "deletion_verification_guard",
            "reason": "verify deletion of purge_tool.py",
            "matched_span": "x", "response_hash": "abcd1234abcd",
            "session_id": "sj", "terminal_id": "", "transcript_path": "P:/t.jsonl",
        })
        rows = gr.ingest_new_blocks("tj")
        assert any(r["gate_name"] == "deletion_verification_guard" for r in rows)
        clip = [r for r in rows if r["gate_name"] == "deletion_verification_guard"][0]
        assert clip["source_ref"]["sink"] == "stop_blocks.jsonl"
        assert clip["source_ref"]["response_hash"] == "abcd1234abcd"
        # Watermark byte offset advanced past the written bytes.
        wm = json.loads(
            (tmp_state["root"] / "cc-lazy-closure-debt" / "cc-gate-residue"
             / "tj.watermark.json").read_text()
        )
        assert wm["jsonl_byte_offset"] > 0
        # Second call: appending a new line yields only that line.
        _append_jsonl(tmp_state["jsonl"], {
            "timestamp": "2026-07-10T12:11:00.000000+00:00", "event": "Stop",
            "gate_name": "g2", "reason": "r2", "matched_span": "x",
            "response_hash": "ef56", "session_id": "sj2", "terminal_id": "",
            "transcript_path": "",
        })
        rows2 = gr.ingest_new_blocks("tj")
        assert len(rows2) == 1
        assert rows2[0]["gate_name"] == "g2"

    def test_empty_sources_return_empty(self, tmp_state):
        # No DB rows, no jsonl lines.
        _make_db(tmp_state["db"], [])
        rows = gr.ingest_new_blocks("nobody")
        assert rows == []


# --- recent_residue + promotion ---------------------------------------------

class TestRecentResidueAndPromotion:
    def test_recent_residue_after_classification(self, tmp_state):
        _seed_watermark_zero("console_clip", tmp_state["root"])
        _make_db(tmp_state["db"], [_clip_block_row()])
        rows = gr.ingest_new_blocks("console_clip")
        lid = rows[0]["ledger_id"]
        gr.record_classification(
            "console_clip", lid, "confirmed_fp",
            {"tool": "Grep", "target": "clip_client.py", "transcript_pos": 0},
        )
        residue = gr.recent_residue("console_clip")
        assert len(residue) == 1
        assert residue[0]["classification"] == "confirmed_fp"
        assert residue[0]["artifact"]["target"] == "clip_client.py"

    def test_promotion_excludes_row_and_one_shot(self, tmp_state):
        _seed_watermark_zero("console_clip", tmp_state["root"])
        _make_db(tmp_state["db"], [_clip_block_row()])
        rows = gr.ingest_new_blocks("console_clip")
        lid = rows[0]["ledger_id"]
        gr.record_classification("console_clip", lid, "confirmed_fp",
                                 {"tool": "Grep", "target": "clip_client.py", "transcript_pos": 0})
        assert lid in gr.recent_residue("console_clip")[0].get("ledger_id", "") \
            or any(r["ledger_id"] == lid for r in gr.recent_residue("console_clip"))
        gr.mark_promoted("console_clip", lid)
        assert all(r["ledger_id"] != lid for r in gr.recent_residue("console_clip"))
        assert lid in gr.promoted_ledger_ids("console_clip")

    def test_age_filter(self, tmp_state):
        _seed_watermark_zero("console_clip", tmp_state["root"])
        _make_db(tmp_state["db"], [_clip_block_row()])
        gr.ingest_new_blocks("console_clip")
        assert gr.recent_residue("console_clip", max_age_h=0.0) == []

    def test_max_count(self, tmp_state):
        rows = []
        for i in range(7):
            rows.append({
                "id": 9100 + i, "timestamp": "2026-07-10T12:00:00.000000+00:00",
                "session_id": f"s{i}", "terminal_id": "t",
                "hook_name": f"gate_{i}", "action": "block", "reason": f"reason {i}",
            })
        _make_db(tmp_state["db"], rows)
        _seed_watermark_zero("t", tmp_state["root"])

        gr.ingest_new_blocks("t")
        assert len(gr.recent_residue("t", max_count=3)) == 3


class TestDedupeAndNormalization:
    """Regression tests for #1434 (R1-R5): dedupe, fresh-seed, normalization."""

    def test_gold_dual_sink_dedupes_to_one_row(self, tmp_state):
        """R2: a block in BOTH sinks → ONE ledger row (jsonl primary)."""
        _seed_watermark_zero("merge", tmp_state["root"])

        _make_db(tmp_state["db"], [{
            "id": 1001, "timestamp": "2026-07-10T12:30:00.000000+00:00",
            "session_id": "s1", "terminal_id": "t",
            "hook_name": "StopHook_cross_validator.py",
            "action": "block", "reason": "cross valid failed",
        }])

        jsonl_path = tmp_state["jsonl"]
        jsonl_path.write_text(
            json.dumps({
                "timestamp": "2026-07-10T12:30:00.000000+00:00", "event": "Stop",
                "gate_name": "cross_validator", "reason": "cross valid from jsonl",
                "matched_span": "x", "response_hash": "abcd1234abcd",
                "session_id": "s2", "terminal_id": "", "transcript_path": "P:/t.jsonl",
            }) + "\n"
        )

        rows = gr.ingest_new_blocks("merge")
        assert len(rows) == 1, f"expected 1 deduped row, got {len(rows)}"
        r = rows[0]
        assert r["source_ref"]["sink"] == "stop_blocks.jsonl", \
            "jsonl row should be primary"
        assert r["source_ref"]["response_hash"] == "abcd1234abcd", \
            "jsonl response_hash preserved"
        assert "cross valid from jsonl" in r["block_reason_excerpt"], \
            "jsonl reason should be primary"

    def test_boundary_straddle_dedupes(self, tmp_state):
        """R2 regression: same block straddling a 5s-bucket boundary must dedupe.

        Old fixed-bucket key put 12:30:04.9 in bucket 0 and 12:30:05.1 in
        bucket 5 → two ledger rows for one block. The ±1s adjacency probe
        (secs 4 and 5) must merge them.
        """
        _seed_watermark_zero("straddle", tmp_state["root"])

        _make_db(tmp_state["db"], [{
            "id": 2001, "timestamp": "2026-07-10T12:30:04.900000+00:00",
            "session_id": "s1", "terminal_id": "t",
            "hook_name": "StopHook_cross_validator.py",
            "action": "block", "reason": "boundary block",
        }])
        _append_jsonl(tmp_state["jsonl"], {
            "timestamp": "2026-07-10T12:30:05.100000+00:00", "event": "Stop",
            "gate_name": "cross_validator", "reason": "boundary block jsonl",
            "matched_span": "x", "response_hash": "beefbeefbeef",
            "session_id": "s1", "terminal_id": "", "transcript_path": "",
        })

        rows = gr.ingest_new_blocks("straddle")
        assert len(rows) == 1, f"boundary straddle must dedupe, got {len(rows)}"
        assert rows[0]["source_ref"]["sink"] == "stop_blocks.jsonl"

    def test_distinct_blocks_two_plus_seconds_apart_stay_distinct(self, tmp_state):
        """R2 regression: same gate, blocks ≥2s apart are DISTINCT events.

        Old fixed bucket merged any same-gate blocks inside one 5s window
        (e.g. 12:30:00 and 12:30:03) into one row, silently dropping a block.
        """
        _seed_watermark_zero("distinct", tmp_state["root"])

        for ts, rid in (("2026-07-10T12:30:00.000000+00:00", "aaaa1111"),
                        ("2026-07-10T12:30:03.000000+00:00", "bbbb2222")):
            _append_jsonl(tmp_state["jsonl"], {
                "timestamp": ts, "event": "Stop",
                "gate_name": "cross_validator", "reason": f"block at {ts}",
                "matched_span": "x", "response_hash": rid,
                "session_id": "s1", "terminal_id": "", "transcript_path": "",
            })

        rows = gr.ingest_new_blocks("distinct")
        assert len(rows) == 2, \
            f"blocks 3s apart are distinct events, got {len(rows)} row(s)"

    def test_fresh_terminal_no_history(self, tmp_state):
        """R3: fresh terminal over populated history → 0 rows."""
        _make_db(tmp_state["db"], [
            {"id": 1, "timestamp": "2026-07-09T23:00:00", "session_id": "s_old",
             "terminal_id": "t", "hook_name": "Stop_deletion_verification_guard",
             "action": "block", "reason": "old block"},
        ])
        assert gr.ingest_new_blocks("fresh-t") == []

    def test_fresh_terminal_ingests_new_blocks_after_seed(self, tmp_state):
        """R3: new block appended after fresh-terminal seeding IS ingested."""
        _make_db(tmp_state["db"], [])
        assert gr.ingest_new_blocks("fresh2") == []

        con = sqlite3.connect(str(tmp_state["db"]))
        con.execute(
            "INSERT INTO hooks (id, timestamp, session_id, terminal_id, event, "
            "hook_name, event_type, action, reason) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (3,
             "2026-07-10T22:00:00",
             "s-new", "t",
             "hook_invoked",
             "Stop_deletion_verification_guard",
             "Stop", "block",
             "fresh block after seeding"),
        )
        con.commit()
        con.close()

        rows = gr.ingest_new_blocks("fresh2")
        assert len(rows) == 1
        assert "fresh block" in str(rows[0].get("block_reason_excerpt", ""))

    @pytest.mark.parametrize("v1,v2,expected", [
        ("StopHook_cross_validator.py", "cross_validator", "cross_validator"),
        ("Stop.py:epistemic_contract", "epistemic_contract", "epistemic_contract"),
        ("StopHook_unverified_stance.py", "unverified_stance", "unverified_stance"),
        ("Stop.py:semantic_critic", "semantic_critic", "semantic_critic"),
        ("Stop.py:proposal_critique_gate", "proposal_critique_gate",
         "proposal_critique_gate"),
        ("Stop.py:cjk_drift_detector", "cjk_drift_detector", "cjk_drift_detector"),
        ("Stop.py:skill_first_stop_gate", "skill_first_stop_gate",
         "skill_first_stop_gate"),
        ("Stop.py:safety_gate", "Stop_safety_gate.py", "safety_gate"),
        ("skill-guard_Stop:slash_gate", "slash_gate", "slash_gate"),
    ])
    def test_name_normalization(self, v1, v2, expected):
        """R2: every live gate-name variant pair normalizes to same key."""
        from gate_residue import _normalize_gate_name
        assert _normalize_gate_name(v1) == expected
        assert _normalize_gate_name(v2) == expected
