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


# --- ingest + watermark ------------------------------------------------------

class TestIngest:
    def test_ingest_db_rows_writes_ledger_and_advances_watermark(self, tmp_state):
        _make_db(tmp_state["db"], [_clip_block_row()])
        rows = gr.ingest_new_blocks("console_clip")
        assert len(rows) == 1
        assert rows[0]["gate_name"] == "Stop_removal_completeness_guard"
        assert rows[0]["classification"] == "unresolved"
        assert rows[0]["ledger_id"].startswith("Stop_removal_completeness_guard:")
        assert rows[0]["source_ref"]["sink"] == "diagnostics.db"
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
        _make_db(tmp_state["db"], [_clip_block_row()])
        rows = gr.ingest_new_blocks("console_clip")
        lid = rows[0]["ledger_id"]
        gr.record_classification("console_clip", lid, "confirmed_fp",
                                 {"tool": "Grep", "target": "clip_client.py", "transcript_pos": 0})
        assert lid in gr.recent_residue("console_clip")[0].get("ledger_id", "") \
            or any(r["ledger_id"] == lid for r in gr.recent_residue("console_clip"))
        gr.mark_promoted("console_clip", lid)
        # Promoted => dropped from residue surface.
        assert all(r["ledger_id"] != lid for r in gr.recent_residue("console_clip"))
        assert lid in gr.promoted_ledger_ids("console_clip")

    def test_age_filter(self, tmp_state):
        _make_db(tmp_state["db"], [_clip_block_row()])
        gr.ingest_new_blocks("console_clip")
        # max_age_h=0 => cutoff is now, ts (older) filtered out.
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
        gr.ingest_new_blocks("t")
        assert len(gr.recent_residue("t", max_count=3)) == 3
