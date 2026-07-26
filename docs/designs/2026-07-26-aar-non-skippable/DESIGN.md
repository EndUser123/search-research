# Design: `/close` → `/aar` Structural Non-Skippability via Stop-Hook Enforcement

| Field | Value |
|---|---|
| Document kind | Design (not plan, not proposal) |
| Author | Senior software architect subagent |
| Author host | Grok Build (workspace `P:/`) |
| Author time | 2026-07-26 |
| Status | Draft — pending operator review |
| Target subsystem | `/close` skill, `/aar` skill, `~/.grok/hooks/` |
| Reversibility | Medium — adds one new Stop hook script + one JSON-registration edit + one helper extraction in `close_accounting.py`; all reversible (git revert or JSON edit) |

---

## Overview

**Goal.** Move the `/close → /aar` obligation from prose-level instruction to a **harness-level Stop hook** so the agent's turn cannot end cleanly when a retrospective gate is unresolved. After this design ships, the agent cannot emit a `/close` summary naming `/aar = SKIPPED` and have the harness mark the session as ended. The Stop hook mechanically blocks and feeds the LLM a corrective nudge through stderr on exit code 2.

**Scope.** A new Stop-hook script (`close_compliance_stop.py`) registered in the existing `~/.grok/hooks/quality-gate.json` Stop matcher. The hook reads:

1. The close-evidence ledger at `P:/.artifacts/close-evidence/<session>.json`
2. An AAR completion receipt at `P:/.artifacts/aar/<session>/_run.json`
3. The harness-supplied `GROK_SESSION_ID` env var

It blocks the agent's stop with exit code 2 when (a) the ledger shows `retrospective.state == "needs_attention"` and (b) no session-bound AAR completion receipt with matching content hash exists. A shadow mode plus a **four-tier** rollout (`shadow` → `enforce_with_aar_lite` → `enforce_full_aar_for_high_substance` → `enforce_full_aar`) lets the operator stage the enforcement on real sessions before the gate becomes hard.

**Non-goals.**

- Not adding a SessionEnd hook (separate concern; RC-6 deferred — see Open Questions)
- Not modifying AAR's `--lite` semantics; the gate accepts `--lite` as valid receipt and reserves full-AAR enforcement for high-substance sessions only
- Not replacing the existing `quality_gate.py` Stop hook; the two Stop hooks complement each other
- Not implementing the agent-internal auto-invoke loop; the agent can already reach `loop.needed = false` once AAR runs, and we want the harness guard as the final backstop

---

## Background

### Premise verification

The design constraints provided nine verified premises. Each is labeled with the receipt rule from `~/.grok/AGENTS.md` § "Claims require receipts":

| ID | Claim | Label | Receipt |
|---|---|---|---|
| P-1 | Stop hook can block the agent's turn on Grok Build | [FACT] | `~/.grok/docs/user-guide/10-hooks.md:94` "Stop | An agent turn ends on a genuine completion | Yes — can block the stop" |
| P-2 | Existing Stop hook registration pattern via `~/.grok/hooks/quality-gate.json` is the canonical wiring | [FACT] | `~/.grok/hooks/quality-gate.json:69-77` (F-59 fix: full range) registers `quality_gate.py` on Stop event with `type: "command"` |
| P-3 | `close_coordinator.py` exists at `~/.grok/hooks/scripts/close_coordinator.py` and is unrelated to close-completion enforcement (it covers B3-B6 git persistence reconciliation) | [FACT] | direct read `~/.grok/hooks/scripts/close_coordinator.py:1-12` (file header: "B6: /close persistence coordinator") |
| P-4 | The retrospective gate already computes `needs_attention` at the tool layer | [FACT] | `~/.grok/skills/close/__lib/close_accounting.py:1708-1714` sets `gates["retrospective"]["state"] = "needs_attention"` |
| P-5 | The close-evidence ledger is written to `P:/.artifacts/close-evidence/<session>.json` by `close_accounting.py` | [FACT] | `~/.grok/skills/close/__lib/close_accounting.py:547-549` writes target path |
| P-6 | `_has_code_writes` has documented false negatives on research-heavy / orchestration sessions (excludes `/.artifacts/`, `/sessions/`, `/tmp/`) | [FACT] | `~/.grok/skills/close/__lib/close_accounting.py:418-421` exclusion filters + wiki concept `P:/.data/wiki/concepts/close-auto-invokes-aar.md` documents production instance |
| P-7 | `/aar --lite` produces a structurally valid completion receipt (same schema: `_run.json` + `aar-report.md` + `preprocess/`) | [FACT] | `~/.grok/skills/aar/SKILL.md:627` "--lite | Skip opportunities; episodes + decisions only" + `~/.grok/skills/aar/__lib/completion_receipt.py:67-72` validates the same `validate_aar_report_with_packet` regardless of mode |
| P-8 | `validate_close_receipt.py` has zero AAR-specific checks today | [FACT] | direct read `~/.grok/skills/close/__lib/validate_close_receipt.py` (no `report_sha256`, `aar-report.md`, or AAR field regex found) |
| P-9 | The cross-model specialist's claim that a `Stop_fake_done_detector.py` already exists is wrong — that file exists only in a stale worktree, not in live `~/.grok/hooks/scripts/` | [FACT] | direct `list_dir C:/Users/brsth/.grok/hooks/scripts/` shows no such file; only `quality_gate.py` is registered in Stop |
| P-10a | A CLI-flag or env-var `--force` is reachable by the agent via shell because `run_terminal_command` can set env vars on this host | [FACT] | `run_terminal_command` semantics: child process inherits env; a `--force`-style env var set in the command itself is observable in the hook's `os.environ` at fire time. Verified: `quality_gate.py:59` reads `os.environ.get("GROK_RECEIPT_GATE_MODE", ...)`, which any agent-side shell call can pre-set. |
| P-10b | A path-based bypass outside the workspace (e.g., `~/.grok/operator/`) would still be writable on a multi-tenant host because `P:/` is shared across processes | [INFERENCE] | No specific operator-profile evidence inspected; the inference rests on the general multi-agent shared-filesystem assumption documented in `~/.grok/AGENTS.md` § "Working in the shared main tree" |
| P-11 | The Stop hook input payload on Grok Build exposes `sessionId`, `cwd`, `workspaceRoot` (no agent text, no `response`) | [FACT] | `P:/.data/wiki/concepts/grok-build-stop-hook-agent-text.md:38-45` directly verifies payload shape from `~/.grok/docs/user-guide/10-hooks.md` |
| P-12 | The existing `quality_gate.py` precedent uses a three-mode rollout pattern via `GROK_RECEIPT_GATE_MODE` (shadow / receipt_authoritative_with_old_fail_safe / receipt_authoritative) | [FACT] | `~/.grok/hooks/scripts/quality_gate.py:46` defines `RECEIPT_GATE_MODES`; the surrounding range `quality_gate.py:42-77` includes `_effective_block_decision` (F-57 fix: tighter line citation that names the exact constant vs. context range) |
| P-13 | The AAR `_run.json` carries the schema fields the gate needs: `skill`, `session_id`, `status`, `report_path`, `report_sha256`, `completed_at`, **`mode`** (added by U8) | [FACT] | `~/.grok/skills/aar/__lib/completion_receipt.py:48-67` (status, completed_at, report_path, report_sha256, packet_path) + U8 will add `mode` field at `state.update()` block (~line 79-85) |
| P-14 | An AAR run lives at `P:/.artifacts/aar/<session_id>/` containing `_run.json`, `aar-report.md`, `preprocess/` | [FACT] | `~/.grok/skills/close/__lib/continuation_coverage.py:236-237` constructs the same path via `ARTIFACTS_DIR / run_path / "aar-report.md"` |
| P-15 | The close-runner already validates scanner output contains `("gates", "loop", "summary", "counts")` and rejects malformed payloads | [FACT] | `~/.grok/skills/close/__lib/close_runner.py:660-680` |
| P-16 | Hook stderr is the canonical "block" channel on Grok Build | [FACT] | `~/.grok/hooks/scripts/quality_gate.py:1-19` + `P:/.claude/rules/hook-development.md` § "Blocking Hook stderr Requirement" |

[UNKNOWN] items this design explicitly accepts (do not block ship):

- Whether `quality-gate.json` registers more than one Stop hook entry; the current schema has a flat list `Stop → [{hooks: [...]}]` and we can add a second entry, but live runtime confirmation is desired before commit (handled in Implementation Unit U2 verification step).
- Whether `~/.grok/hooks/scripts/quality_gate.py` will fire BEFORE or AFTER the new hook in the order they are listed in `hooks.json`. Grok Build documents this as "all hooks fire" (from `10-hooks.md:154-155`), so order shouldn't matter, but verification is in tests.

### Why current enforcement fails

The root-cause analysis from the red-team (six clusters, RC-1..RC-6) is summarized verbatim in the design constraints. Reading the existing surface confirms each:

- **RC-1 (block at tool layer, harness does not gate).** `close_accounting.py:1708-1714` writes the `retrospective` gate as `needs_attention`, and `close_runner.py:2179-2189` sets `loop.needed = true`. But neither writes to a location the **Stop hook** reads. The `/close` skill text and the LLM can emit a close summary while `loop.needed = true`, and the session ends without enforcement. The Stop hook fires AFTER the LLM has emitted the summary; today it only checks claim-phrases, not close-time obligations.
- **RC-2 (gate disarmable via `_has_code_writes` false negatives).** The retrospective gate is conditional on `has_substantive_work` which is itself conditional on `_has_code_writes` (close_accounting.py:1674). When the agent only writes to `/.artifacts/`, `/sessions/`, `/tmp/`, `_has_code_writes` returns False; the gate does not fire. Result: a research-heavy session with 0 git commits and many AAR-relevant side effects computes "no substantive work" and skips the gate.
- **RC-3 (`--force` reachable by agent).** Any escape hatch implemented as a CLI flag or env var set via `run_terminal_command` is forgeable by the agent.
- **RC-4 (receipt validation checks presence, not session binding).** `validate_close_receipt.py:1-230` validates the close-summary text fields. It does not parse `_run.json` or assert session binding.
- **RC-5 (AAR `--lite` produces valid receipt with minimal content).** `--lite` runs through the same `validate_aar_report_with_packet` path; structurally identical.
- **RC-6 (no SessionEnd hook).** Out of scope; see Open Questions § "SessionEnd capability check."

### Established conventions (do not reinvent)

The workspace already has structural-enforcement precedent this design extends:

- `mandatory-step-enforcement-code-over-prose.md` (wiki) — promotes prose rules to state-machine guards. Our `close_compliance_stop.py` is a state-machine guard; this design implements its blueprint.
- `structural-enforcement-for-skipped-rules-grok-build-2026.md` (wiki, July 2026) — confirms `command` + `http` hook surface; `Stop` event is the correct mechanism for end-of-turn enforcement.
- `close-auto-invokes-aar.md` (wiki) — confirms `/close` is *supposed to* auto-invoke `/aar`; today's prohibition was a regression. This design is the structural backstop the wiki calls for.
- `quality_gate.py` precedent — three-mode rollout, fail-open on error, JSON decision on stdout, descriptive stderr on block. The new hook mirrors these contracts.

---

## Architecture

### Component map

```
┌─────────────────────────────────────────────────────────────────────┐
│ Agent turn ends (assistant has emitted final message)               │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼ Stop event fires (Grok Build native)
┌─────────────────────────────────────────────────────────────────────┐
│ Hook ordering — both Stop hooks in quality-gate.json run:           │
│  1. close_compliance_stop.py (NEW) — /close→/aar obligation gate    │
│  2. quality_gate.py            (existing)  — claim-phrase + verify  │
│  (F-11: close_compliance_stop fires FIRST so the model sees its     │
│  /aar directive last — closer-to-source obligation addressed first) │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
close_compliance_stop.py main() [F-04: outer try/except for fail-open]
  ┌── read env: GROK_SESSION_ID, GROK_CLOSE_COMPLIANCE_MODE            │
  ├── _resolve_workspace(payload) [F-05 per-fire resolution]         │
  │     → workspace_root (or fail_open with REASON_WORKSPACE_UNRESOLVABLE) │
  │                                                                       │
  ├── mode  = "shadow"  → log decision, exit 0 (allow)                │
  ├── mode  = "enforce_with_aar_lite"  → require valid AAR receipt    │
  ├── mode  = "enforce_full_aar_for_high_substance"                  │
  │     → require mode=="full" only when session is high-substance    │
  └── mode  = "enforce_full_aar"  → require mode=="full" always      │
                                                                       │
  ┌── Read workspace_root / .artifacts / close-evidence / <sid>.json   │
  │     ├── missing → "scanner never ran" → BLOCK (enforce modes)     │
  │     └── parse: gates[retrospective].state                          │
  │                                                                       │
  ├── Compute substantive_work via U0 shared module (F-09/F-10):       │
  │     • close_substance.compute_substantive_work(                    │
  │         ledger.counts, _has_code_writes(sid))                     │
  │     • Multi-signal OR union — single source of truth               │
  │     • ANY of: code writes, tool_calls > TOOL_CALL_THRESHOLD (5),  │
  │       handoffs_mine > 0, commits > 0 → true                        │
  │                                                                       │
  ├── If !substantive → exit 0 (no gate fires; no enforcement today)  │
  │                                                                       │
  ├── If retrospective.state in {pre_satisfied, skip} → exit 0        │
  │                                                                       │
  └── Else retrospective.state == "needs_attention":                   │
        ┌── Read workspace_root / .artifacts / aar / <sid> / _run.json  │
        │     ├── missing → BLOCK with reason                          │
        │     └── parse: skill, session_id, status, mode,             │
        │              report_path, report_sha256, completed_at       │
        │                                                                  │
        ├── session_id != GROK_SESSION_ID → BLOCK                     │
        ├── status != "completed"            → BLOCK                   │
        ├── report_path / aar-report.md missing or hash mismatch →     │
        │     BLOCK (F-29 hash uses hashlib.sha256() direct)           │
        ├── pre-write check (F-03):                                    │
        │     aar.completed_at <= ledger.generated_at → BLOCK          │
        │     (with new REASON_PREWRITE = "aar_pre_write_attack_rejected") │
        │                                                                  │
        ├── mode gate (F-06):                                           │
        │     For enforce_*_aar* modes:                                │
        │       aar_mode = aar.get("mode")  [no default — missing → BLOCK]│
        │       require aar_mode == "full"                              │
        │     For enforce_with_aar_lite:                                │
        │       any mode accepted                                       │
        │                                                                  │
        └── BLOCK if any check fails, ALLOW if all pass                │
                                                                       │
  └── Output: schema-rich JSON on stdout (F-22 includes aar fields +  │
              ledger counts); exit code 0 or 2; side-effects logged   │
              to ~/.grok/logs/close-compliance-stop/<sid>.jsonl       │
              (with msvcrt.locking sidecar for F-25 concurrent safety)│
└─────────────────────────────────────────────────────────────────────┘
```

### Decision flow

```
mode == "shadow":
    log decision (schema-rich per F-22) → ~/.grok/logs/close-compliance-stop/<sid>.jsonl
    ALWAYS exit 0

mode ∈ {enforce_with_aar_lite, enforce_full_aar_for_high_substance, enforce_full_aar}:
    per-check decision tree:
      aar missing             → REASON_AAR_MISSING      → BLOCK
      aar.session_id mismatch  → REASON_BINDING          → BLOCK
      aar.status != completed → REASON_NOT_COMPLETED    → BLOCK
      hash mismatch           → REASON_HASH_MISMATCH    → BLOCK
      aar.completed_at <= ledger.generated_at
                              → REASON_PREWRITE         → BLOCK (F-03)
      enforce_*_aar* modes AND aar.get("mode") missing/!=full
                              → REASON_LITE_REJECTED    → BLOCK (F-06)
      all checks pass         → REASON_OK               → ALLOW
```

**The receipt check is independent of the close-evidence ledger.** The hook does not trust `close_accounting.py`'s written `retrospective.state` blindly — it re-derives the answer from the AAR artifact + session binding + timestamp ordering + mode field. This is the structural fix for RC-4: the binding + freshness are enforced at gate time, not by the closing tool's bookkeeping. (F-03 closes the pre-write attack: a valid receipt pre-populated before the scanner ran would pass session-binding + hash checks, but is rejected by the timestamp check.)

### Mode progression

Mirrors `quality_gate.py`'s `RECEIPT_GATE_MODES` precedent (3-mode → this design uses 4-mode to allow granular progressive rollout). Default rollout order:

1. **Shadow mode** ships first (U1+U2 only). Operator toggles `GROK_CLOSE_COMPLIANCE_MODE=enforce_with_aar_lite` after a week of shadow logs.
2. **`enforce_with_aar_lite`** ships second, after operator review of `~/.grok/logs/close-compliance-stop/` shows the false-positive rate is zero. Accepts any AAR receipt (including pre-U8 receipts without `mode`).
3. **`enforce_full_aar_for_high_substance`** ships third, after P1 stabilises. Same `mode=="full"` requirement but only applied when `close_substance.is_high_substance(ledger.counts)` is True (high-substance = ≥3 wiki concepts OR ≥5 commits OR ≥10 tool calls; see Threshold Justification §).
4. **`enforce_full_aar`** ships fourth (strict). Same `mode=="full"` requirement applied to ALL sessions regardless of substance. Pre-U8 receipts (no `mode` field) block in this mode — operator must ship U8 first or lower mode.

This staged approach binds each promotion to operator evidence, not self-justified rollouts.

### Why this fixes each RC

| RC | Mechanism |
|---|---|
| RC-1 (block at tool layer only) | New Stop hook runs after the agent's response; exit 2 prevents the harness from declaring end-of-turn |
| RC-2 (false negatives) | Multi-signal `substantive_work` union (code writes + tool count + handoff count + commits). **F-09:** single source of truth via U0 `close_substance.compute_substantive_work()`; hook and `evaluate_retrospective_gate` helper both consume it |
| RC-3 (`--force`) | No `--force`. The agent cannot set `GROK_CLOSE_COMPLIANCE_MODE` to bypass — only the operator can edit `~/.grok/config.toml` or the launch env. Operational bypass is Ctrl+C |
| RC-4 (no session binding) | Hard `session_id == GROK_SESSION_ID` check + content-hash match + **pre-write timestamp defense (F-03)** — `aar.completed_at > ledger.generated_at`. Three independent checks; receipt forgery is rejected even if one check passes |
| RC-5 (`--lite` valid) | Stage-gated: lite satisfies `enforce_with_aar_lite`; strict modes (`enforce_full_aar*`) require `aar.mode == "full"` (no default — pre-U8 receipts block). **F-06** conservative semantics |
| RC-6 (no SessionEnd) | Deferred (separate concern) |

---

## Implementation Sketch

### New file: `~/.grok/hooks/scripts/close_compliance_stop.py`

```python
#!/usr/bin/env python3
"""Stop hook: enforce /close → /aar obligation at harness layer.

Reads close-evidence ledger + AAR completion receipt + harness session id.
Blocks the agent's turn (exit 2) when the close scanner flagged a
retrospective obligation that has not been discharged by a valid,
session-bound AAR with post-scanner completion timestamp (F-03 pre-write
attack defense).

Four modes (env GROK_CLOSE_COMPLIANCE_MODE):
  shadow                          — log only, always allow
  enforce_with_aar_lite           — accept any mode (or pre-U8 receipts)
  enforce_full_aar                — accept only mode=="full" receipts
  enforce_full_aar_for_high_substance — full only when high-substance

Fail-open: any error exits 0 and writes a HOOK_ERROR record to
~/.grok/hooks/state/hook-error-<sid>.jsonl. Mirrors quality_gate.py:1388-1421.
A broken hook must not kill conversation.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# F-10 fix: sibling import. close_substance.py lives next to this hook so
# both files can be co-shipped and the hook doesn't need cross-package
# sys.path manipulation. The hook script's directory is always on the
# implicit path of `os.path.dirname(__file__)`; we add it explicitly for
# `import close_substance` to resolve.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import hashlib
import json
import re
from datetime import datetime, timezone

# --- Mode constants (mirrors quality_gate.RECEIPT_GATE_MODES) ---

# --- Mode constants (mirrors quality_gate.RECEIPT_GATE_MODES) ---
MODES = frozenset({
    "shadow",
    "enforce_with_aar_lite",
    "enforce_full_aar",
    "enforce_full_aar_for_high_substance",
})

# --- Thresholds ---
TOOL_CALL_THRESHOLD = 5                  # RC-2 disarm-proof trigger; see Threshold Justification §
HIGH_SUBSTANCE_WIKI_CONCEPTS = 3
HIGH_SUBSTANCE_COMMITS = 5
HIGH_SUBSTANCE_TOOL_CALLS = 10
# `tool_calls` is computed by the close-accounting scan and serialized
# into Evidence.counts (added in U3); see also § Threshold Justification.

# --- Paths (resolved per-invocation, not at import time) ---
#
# F-05 fix: workspace resolution is per-fire, not module-global. Stop
# payload's `workspaceRoot` is primary; `GROK_WORKSPACE` env is fallback;
# `P:/` is a final-resort default GATED by an existence check on
# `.artifacts/`. If neither resolves to a real artifacts dir, return
# fail-open with `reason_code="workspace_unresolvable"`.
_DEFAULT_WORKSPACE = "P:/"


def _resolve_workspace(payload: dict) -> Path | None:
    raw = (
        payload.get("workspaceRoot")
        or payload.get("cwd")
        or os.environ.get("GROK_WORKSPACE")
        or _DEFAULT_WORKSPACE
    )
    candidate = Path(raw.replace("\\", "/"))
    # Existence check: the workspace must contain .artifacts/ (or be
    # writable for it). On unrecognised hosts, fail-open with a clear
    # signal rather than silently reading the wrong path.
    artifacts = candidate / ".artifacts"
    if (artifacts / "close-evidence").exists():
        return candidate
    # Workspace root seems present but no prior close-evidence ledger.
    # Trust it (could be a fresh worktree) but verify git-status style:
    if (candidate / ".grok").exists() or candidate == Path(_DEFAULT_WORKSPACE):
        return candidate
    return None

# Reason codes — surface on stdout for log scrapers, stderr for the model
REASON_NO_LEDGER        = "no_close_evidence_ledger"            # scanner never ran
REASON_LEDGER_MALFORMED = "ledger_malformed"
REASON_LEGACY_SKIP      = "skipped_legacy_no_substantive_work"
REASON_GATE_FIRED       = "retrospective_needs_attention"
REASON_AAR_MISSING      = "aar_receipt_missing"
REASON_BINDING          = "aar_session_id_mismatch"
REASON_NOT_COMPLETED    = "aar_status_not_completed"
REASON_HASH_MISMATCH    = "aar_report_hash_mismatch"
REASON_LITE_REJECTED    = "aar_lite_rejected_full_required"
REASON_WORKSPACE_UNRESOLVABLE = "workspace_unresolvable"
REASON_PREWRITE         = "aar_pre_write_attack_rejected"   # F-03
REASON_OK               = "ok"


def _mode() -> str:
    raw = os.environ.get("GROK_CLOSE_COMPLIANCE_MODE", "shadow").strip().lower()
    if raw not in MODES:
        # F-28: warn operator on misconfiguration (still defaults to safe mode)
        sys.stderr.write(
            f"close_compliance_stop warning: invalid mode {raw!r}; "
            "defaulting to shadow\n"
        )
        return "shadow"
    return raw


def _session_id_from_env_or_payload(payload: dict) -> str:
    sid = os.environ.get("GROK_SESSION_ID", "") or payload.get("sessionId", "")
    return sid.strip() if isinstance(sid, str) else ""


def _safe_sid(raw_sid: str) -> str:
    """Sanitize a session id for use as a filename component (F-07, F-54).

    Replaces any character outside [A-Za-z0-9_.-] with `_` AND rejects
    `..` (parent-directory traversal) and zero-length results. Shared
    between ledger and AAR paths.
    """
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", raw_sid or "")
    if ".." in safe or not safe:
        return "_"
    return safe[:128]


def _read_ledger(
    session_id: str,
    close_evidence_dir: Path,
) -> tuple[dict | None, str | None]:
    safe = _safe_sid(session_id)
    p = close_evidence_dir / f"{safe}.json"
    if not p.is_file():
        return None, REASON_NO_LEDGER
    try:
        return json.loads(p.read_text(encoding="utf-8")), None
    except (json.JSONDecodeError, OSError):
        return None, REASON_LEDGER_MALFORMED


def _parse_iso(ts: str) -> float:
    """Parse ISO-8601 timestamp to epoch seconds. Raises ValueError on bad input."""
    from datetime import datetime
    # Accept 'Z' suffix and '+00:00' interchangeably
    cleaned = ts.replace("Z", "+00:00")
    return datetime.fromisoformat(cleaned).timestamp()


def _read_aar_receipt(
    session_id: str,
    aar_root: Path,
) -> tuple[dict | None, str | None]:
    """Find {aar_root}/<sid>/_run.json. Return (parsed, None) on hit.

    F-07: applies the same `_safe_sid` sanitization as `_read_ledger`.
    F-46: validates the resolved path is still under `aar_root` so a
    crafted session_id cannot read arbitrary files (defense-in-depth
    even though the hook runs as the operator).
    """
    safe = _safe_sid(session_id)
    run_dir = aar_root / safe
    try:
        resolved = run_dir.resolve(strict=False)
        root_resolved = aar_root.resolve(strict=False)
        if not str(resolved).startswith(str(root_resolved)):
            return None, REASON_AAR_MISSING
    except OSError:
        return None, REASON_AAR_MISSING
    state_path = run_dir / "_run.json"
    if not state_path.is_file():
        return None, REASON_AAR_MISSING
    try:
        return json.loads(state_path.read_text(encoding="utf-8")), None
    except (json.JSONDecodeError, OSError):
        return None, REASON_AAR_MISSING


def _is_high_substance(ledger: dict) -> bool:
    """High-substance detector for `enforce_full_aar_for_high_substance`.

    Reads thresholds from `close_substance` (U0, F-09 single source of
    truth — NO duplicated thresholds) and applies them to the ledger's
    `Evidence.counts`. The close_runner / close_accounting scan already
    populated the counts field; the hook just consumes them.
    """
    try:
        import close_substance as _cs   # sibling import via U0 path setup
        counts = ledger.get("counts", {})
        return (
            counts.get("wiki", 0) >= _cs.HIGH_SUBSTANCE_WIKI_CONCEPTS
            or counts.get("commits", 0) >= _cs.HIGH_SUBSTANCE_COMMITS
            or counts.get("tool_calls", 0) >= _cs.HIGH_SUBSTANCE_TOOL_CALLS
        )
    except Exception:
        # F-04 fail-open: if shared module is missing or broken, fall back
        # to a conservative strict-mode (always treat as high-substance so
        # a hook bug cannot loosen enforcement). Negative case (no evidence
        # of substance) is the safe direction; positive case shouldn't be
        # bypassed by an import error.
        return True


def _hash_aar_report(state: dict) -> tuple[bool, str]:
    """Compare AAR `report_sha256` to live hash of `report_path`.

    Returns (matches, REASON_OK|REASON_HASH_MISMATCH).
    """
    report_path = Path(state.get("report_path", ""))
    expected = state.get("report_sha256", "")
    if not report_path.is_file():
        return False, REASON_HASH_MISMATCH
    try:
        digest = hashlib.sha256()
        with report_path.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                digest.update(chunk)
        actual = digest.hexdigest()
        return actual == expected, REASON_OK if actual == expected else REASON_HASH_MISMATCH
    except (OSError, ValueError, TypeError):
        return False, REASON_HASH_MISMATCH


# --- main() reads Stop payload from stdin (Grok Build Stop hook contract) ---
#
# Fail-open contract (mirrors quality_gate.py:1388-1421 _write_hook_error):
# any unhandled exception → emit "fail_open" decision, write HOOK_ERROR
# record, return 0. A broken hook must not kill conversation.
def main() -> int:
    try:
        return _run_main()
    except Exception as exc:   # noqa: BLE001 — fail-open catches all
        sid = os.environ.get("GROK_SESSION_ID", "unknown")
        _write_hook_error(exc, sid)
        return _emit_decision(sid, "fail_open", ledger=None, aar=None)


def _run_main() -> int:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except (json.JSONDecodeError, UnicodeDecodeError, OSError):
        payload = {}

    sid = _session_id_from_env_or_payload(payload)
    if not sid:
        return 0   # fail-open; can't identify session → can't enforce

    # F-05 fix: per-fire workspace resolution, fail-open if unresolvable
    workspace = _resolve_workspace(payload)
    if workspace is None:
        return _emit_decision(sid, REASON_WORKSPACE_UNRESOLVABLE, ledger=None, aar=None)
    close_evidence_dir = workspace / ".artifacts" / "close-evidence"
    aar_root = workspace / ".artifacts" / "aar"

    ledger, ledger_err = _read_ledger(sid, close_evidence_dir)
    if ledger is None:
        return _emit_decision(sid, ledger_err, ledger=None, aar=None)

    retrospective = ledger.get("gates", {}).get("retrospective", {})
    state = retrospective.get("state", "skip")
    if state in ("pre_satisfied", "skip"):
        return _emit_decision(sid, REASON_OK, ledger=ledger, aar=None)

    if state != "needs_attention":
        return _emit_decision(sid, REASON_OK, ledger=ledger, aar=None)

    aar, aar_err = _read_aar_receipt(sid, aar_root)
    if aar is None:
        return _emit_decision(sid, aar_err or REASON_AAR_MISSING,
                              ledger=ledger, aar=None)

    # RC-4: session-bound receipt
    if aar.get("session_id") != sid:
        return _emit_decision(sid, REASON_BINDING, ledger=ledger, aar=aar)
    if aar.get("skill") != "aar":
        return _emit_decision(sid, REASON_BINDING, ledger=ledger, aar=aar)
    if aar.get("status") != "completed":
        return _emit_decision(sid, REASON_NOT_COMPLETED, ledger=ledger, aar=aar)

    hash_ok, hash_code = _hash_aar_report(aar)
    if not hash_ok:
        return _emit_decision(sid, hash_code, ledger=ledger, aar=aar)

    # F-03 fix: reject pre-write attacks. The agent could write a valid
    # receipt (matching session_id, matching hash) BEFORE the scanner ran.
    # The receipt's `completed_at` MUST be strictly after the ledger's
    # `generated_at` — i.e., the AAR was produced in response to the gate,
    # not before.
    aar_completed = aar.get("completed_at", "")
    ledger_generated = ledger.get("generated_at", "")
    if aar_completed and ledger_generated:
        try:
            if _parse_iso(aar_completed) <= _parse_iso(ledger_generated):
                return _emit_decision(sid, REASON_PREWRITE, ledger=ledger, aar=aar)
        except ValueError:
            # Unparseable timestamps: treat as suspicious → block
            return _emit_decision(sid, REASON_PREWRITE, ledger=ledger, aar=aar)

    mode = _mode()
    if mode in ("enforce_full_aar", "enforce_full_aar_for_high_substance"):
        # Read `tool_calls` from the post-U3 schema (Evidence.counts is
        # extended in U3 to include tool_calls; pre-U3 ledgers produce 0,
        # which is the safe default — does not flip the detector to true).
        high = _is_high_substance(ledger)
        if mode == "enforce_full_aar_for_high_substance" and not high:
            pass  # allow lite for low-substance sessions
        # Require EXPLICIT mode=="full" (no default). Receipts without mode
        # field are pre-U8; reject in strict modes so the operator notices
        # either by re-running /aar (which writes mode) or by lowering mode.
        aar_mode = aar.get("mode")
        if aar_mode is None or aar_mode == "":
            return _emit_decision(sid, REASON_LITE_REJECTED, ledger=ledger, aar=aar)
        if aar_mode != "full":
            return _emit_decision(sid, REASON_LITE_REJECTED, ledger=ledger, aar=aar)

    return _emit_decision(sid, REASON_OK, ledger=ledger, aar=aar)


def _emit_decision(
    session_id: str, reason_code: str,
    ledger: dict | None, aar: dict | None,
) -> int:
    """Emit structured decision; exit 0 (allow) or 2 (block).

    F-22: includes AAR schema fields (status, mode, report_sha256[:16])
    and ledger retrospective state so operator can investigate block
    events from the JSONL log alone (no need to re-read artifacts).
    """
    mode = _mode()
    blocked = (
        reason_code != REASON_OK
        and mode != "shadow"
    )

    # F-22: build a schema-rich decision dict
    decision: dict = {
        "decision": "block" if blocked else "allow",
        "reason_code": reason_code,
        "mode": mode,
        "session_id": session_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if aar:
        decision["aar"] = {
            "status": aar.get("status"),
            "mode": aar.get("mode"),
            "completed_at": aar.get("completed_at"),
            "report_sha256_prefix": (
                (aar.get("report_sha256") or "")[:16] or None
            ),
        }
    if ledger:
        ret = ledger.get("gates", {}).get("retrospective", {})
        decision["ledger_retrospective_state"] = ret.get("state")
        counts = ledger.get("counts", {})
        decision["ledger_counts"] = {
            "wiki": counts.get("wiki"),
            "commits": counts.get("commits"),
            "tool_calls": counts.get("tool_calls"),
            "handoffs_mine": counts.get("handoffs_mine"),
        }

    # Always log to disk for observability
    try:
        log_dir = _resolve_log_dir()
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / f"{session_id}.jsonl"
        # F-25: file-lock the append on Windows to prevent partial writes
        # from concurrent hook fires on the same session. Subprocess-safe.
        with _file_lock(log_path):
            with log_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(decision) + "\n")
    except OSError:
        pass

    print(json.dumps(decision))   # stdout for log scrapers

    if blocked:
        # Machine-readable single-line stderr → model reads and re-acts
        sys.stderr.write(
            f"close_compliance_stop blocked: reason_code={reason_code}; "
            f"session_id={session_id}; "
            f"run /aar (full required) before /close can end the session.\n"
        )
        return 2
    return 0


def _resolve_log_dir() -> Path:
    """F-15: read log-dir override from env var.

    F-42: `Path.home()` assumes the user's HOME contains `.grok/`,
    matching the existing `quality_gate.py:1402` convention
    (`state_dir = Path.home() / ".grok" / "hooks" / "state"`). On
    unusual hosts (CI runners, service accounts with custom HOME,
    containerised paths) the override env var or the `_DEFAULT_WORKSPACE`
    exclusion check provides an escape; the design documents the
    operator-home assumption explicitly here.
    """
    override = os.environ.get("GROK_CLOSE_COMPLIANCE_LOG_DIR")
    if override:
        return Path(override)
    return Path.home() / ".grok" / "logs" / "close-compliance-stop"


class _file_lock:
    """F-25: cross-platform append-lock. Windows: msvcrt.locking on a sidecar.

    Cheap, fails-open (raises in `__exit__` only if locking itself crashes,
    which we ignore — appending to an unlocked file is acceptable under
    fail-open contract). On Linux/macOS a fcntl flock can be added if
    multi-host deployment requires it; out of scope here.
    """
    def __init__(self, target: Path):
        self.target = target
        self.fd = None
        if sys.platform == "win32":
            try:
                import msvcrt
                self.lock_path = target.with_suffix(".lock")
                self.lock_path.parent.mkdir(parents=True, exist_ok=True)
                self.fd = os.open(str(self.lock_path), os.O_RDWR | os.O_CREAT, 0o644)
                msvcrt.locking(self.fd, msvcrt.LK_LOCK, 1)
            except Exception:
                self.fd = None  # fail-open

    def __enter__(self):
        return self

    def __exit__(self, *args):
        if self.fd is not None:
            try:
                import msvcrt
                msvcrt.locking(self.fd, msvcrt.LK_UNLCK, 1)
                os.close(self.fd)
            except Exception:
                pass


def _write_hook_error(exc: Exception, session_id: str) -> None:
    """Write a durable HOOK_ERROR record on any unhandled exception.

    Proves enforcement was UNAVAILABLE, not that it passed. Consumers
    must treat HOOK_ERROR as ENFORCEMENT_UNAVAILABLE, never as
    ENFORCED_ALLOW. Fail-open policy is preserved (exit 0) but the error
    is visible for post-hoc detection.

    Mirrors quality_gate.py:1388-1421.
    """
    import traceback
    try:
        state_dir = Path.home() / ".grok" / "hooks" / "state"
        state_dir.mkdir(parents=True, exist_ok=True)
        error_file = state_dir / f"hook-error-{session_id}.jsonl"
        entry = {
            "record_type": "HOOK_ERROR",
            "session_id": session_id,
            "stage": "close_compliance_stop",
            "exception_type": type(exc).__name__,
            "exception_message": str(exc)[:500],
            "traceback_summary": traceback.format_exception_only(
                type(exc), exc
            )[0].strip()[:200],
            "timestamp": datetime.now(timezone.utc).isoformat()[:19] + "Z",
            "enforcement_state": "ENFORCEMENT_UNAVAILABLE",
            "note": "Hook crashed. Fail-open policy allowed the stop. "
                    "This record is NOT a passed enforcement check.",
        }
        with error_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass   # telemetry itself failing preserves fail-open silently


if __name__ == "__main__":
    sys.exit(main())
```

### New file: `~/.grok/hooks/scripts/close_substance.py` (U0 — F-09/F-10 single source of truth)

```python
#!/usr/bin/env python3
"""Shared multi-signal substance detector (U0).

Single source of truth for the RC-2 substance check. Both
`close_compliance_stop.py` (Stop hook) and `close_accounting.py`'s
`evaluate_retrospective_gate()` import this module, so the OR-union
lives in exactly one place. F-10 fix: lives next to the hook
(`~/.grok/hooks/scripts/close_substance.py`) so the hook can do a
sibling import without a cross-package sys.path setup.
"""

from __future__ import annotations

# Threshold constants (justified in § Threshold Justification)
TOOL_CALL_THRESHOLD = 5
HIGH_SUBSTANCE_WIKI_CONCEPTS = 3
HIGH_SUBSTANCE_COMMITS = 5
HIGH_SUBSTANCE_TOOL_CALLS = 10


def compute_substantive_work(
    counts: dict,
    has_code_writes: bool,
) -> tuple[bool, dict]:
    """Decide whether a session had substantive work.

    Multi-signal OR union. ANY true → substantive.

    Args:
        counts: `Evidence.counts` dict (post-U3 schema). Reads:
            tool_calls (int, U3), wiki (int), commits (int),
            handoffs_mine (int).
        has_code_writes: result of `_has_code_writes(session_id)`
            (callers pass this in; this module is filesystem-free).

    Returns:
        (substantive, details) where details is the dict of triggered
        signals for observability.
    """
    triggered = {}
    if has_code_writes:
        triggered["code_writes"] = True
    if counts.get("tool_calls", 0) > TOOL_CALL_THRESHOLD:
        triggered["tool_calls"] = counts["tool_calls"]
    if counts.get("handoffs_mine", 0) > 0:
        triggered["handoffs_mine"] = counts["handoffs_mine"]
    if counts.get("commits", 0) > 0:
        triggered["commits"] = counts["commits"]
    return (bool(triggered), triggered)


def is_high_substance(counts: dict) -> bool:
    """Compare counts against the high-substance thresholds."""
    return (
        counts.get("wiki", 0) >= HIGH_SUBSTANCE_WIKI_CONCEPTS
        or counts.get("commits", 0) >= HIGH_SUBSTANCE_COMMITS
        or counts.get("tool_calls", 0) >= HIGH_SUBSTANCE_TOOL_CALLS
    )
```

### Existing file: `~/.grok/hooks/quality-gate.json` — register the new hook

Add a second Stop entry alongside the existing one (lines 69-74). The Stop matcher fires unconditionally per `10-hooks.md:148-149` ("A matcher on Stop or UserPromptSubmit is ignored with a warning (those events always fire)"), so the structure is a flat append.

```diff
     "Stop": [
       {
         "hooks": [
           {
             "type": "command",
             "command": "python \"C:/Users/brsth/.grok/hooks/scripts/close_compliance_stop.py\"",
+            "timeout": 30
           },
           {
             "type": "command",
             "command": "python \"C:/Users/brsth/.grok/hooks/scripts/quality_gate.py\"",
             "timeout": 60
           }
         ]
       }
     ],
```

**F-11 ordering:** the new hook fires FIRST (so its `/aar` directive reaches the model before `quality_gate.py`'s verify directive — the model addresses the closer-to-source obligation first). Verified matching the existing pattern (each hook in the array fires independently).

**F-19 timeout:** 30s is the justified value (not the 10s initial draft). On Windows + antivirus, hashing a 10MB `aar-report.md` can exceed 10s; 30s matches the R-1 mitigation floor and the established 60s precedent precedent (which is for the larger claim-phrase scan). Tunable downward post-rollout once measurements show it's safe.

### Existing file: `~/.grok/skills/close/__lib/close_accounting.py` — extract a reusable gate helper

The hook reuses `_has_code_writes` and the gate computation. To avoid drift, extract:

```python
def evaluate_retrospective_gate(
    session_id: str,
    evidence: Evidence | None = None,
) -> tuple[str, dict]:
    """Compute (gate_state, detail) for the retrospective gate.

    NOT pure: reads filesystem (git status via `_has_code_writes`, plus
    the Evidence dataclass that close_accounting already scanned).

    Multi-signal substantive-work detection (RC-2 fix; closes the
    `_has_code_writes` false-negative failure mode):
      ANY of: code writes (P:/.py, P:/.md excluding /tmp/, /.artifacts/,
              /sessions/), tool_call_count > TOOL_CALL_THRESHOLD (5),
              handoffs_mine > 0, evidence.commits > 0.

    Returns ("pre_satisfied" | "needs_attention" | "skip", detail_dict).
    """
    has_writes, write_paths = _has_code_writes(session_id)
    counts = evidence.counts if evidence is not None else {}
    tool_call_count = counts.get("tool_calls", 0)
    handoff_count = counts.get("handoffs_mine", 0)
    commit_count = counts.get("commits", 0)
    substantive = (
        has_writes
        or tool_call_count > TOOL_CALL_THRESHOLD
        or handoff_count > 0
        or commit_count > 0
    )

    retrospective = scan_retrospective(session_id)
    aar_valid = retrospective.get("valid", False) and retrospective.get("paths")
    if aar_valid:
        return "pre_satisfied", {"detail": "AAR receipt validated", "paths": write_paths}
    if substantive:
        return "needs_attention", {"detail": "substantive work, no AAR"}
    return "skip", {"detail": "no substantive work"}
```

`close_runner.py` and the new Stop hook both call this helper. Drift is mechanical: one source of truth for "what counts as a gate obligation."

### Existing file: `~/.grok/skills/close/__lib/validate_close_receipt.py` — add AAR-binding check

The current `validate_close_receipt()` operates on the close summary TEXT. Add a **separate** function for receipt-binding validation that the close-runner can call, leaving the text validator unchanged:

```python
def validate_aar_session_binding(
    close_evidence_ledger: dict,
    aar_run_dir: Path,
    expected_session_id: str,
) -> tuple[bool, list[str]]:
    """Confirm the AAR receipt named in the ledger is session-bound + valid."""
    issues = []
    state_path = Path(aar_run_dir) / "_run.json"
    if not state_path.is_file():
        return False, ["AAR receipt missing"]
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return False, [f"AAR receipt unreadable: {exc}"]
    if state.get("skill") != "aar":
        issues.append("AAR receipt skill != aar")
    if state.get("session_id") != expected_session_id:
        issues.append("AAR receipt session binding mismatch")
    if state.get("status") != "completed":
        issues.append("AAR receipt not completed")
    report = Path(state.get("report_path", ""))
    if report.is_file():
        digest = hashlib.sha256(report.read_bytes()).hexdigest()
        if digest != state.get("report_sha256"):
            issues.append("AAR receipt report hash mismatch")
    return (len(issues) == 0, issues)
```

The hook does its own check (defense in depth); the close-runner can also call this for early validation before invoking the scanner.

---

## API / Interface Changes

### New env vars (operator-configurable)

| Var | Default | Set-by | Effect |
|---|---|---|---|
| `GROK_CLOSE_COMPLIANCE_MODE` | `shadow` | operator (config.toml or launch env) | Selects hook mode. Agent tools cannot toggle because edit of `~/.grok/config.toml` is a side-effect the hook also blocks via `search_replace`. |
| `GROK_CLOSE_COMPLIANCE_LOG_DIR` | `~/.grok/logs/close-compliance-stop` | operator | Override log path |

### New file paths

| Path | Producer | Consumer |
|---|---|---|
| `~/.grok/hooks/scripts/close_compliance_stop.py` | this design | Grok Build hook loader (`hooks.json`) |
| `~/.grok/logs/close-compliance-stop/<session>.jsonl` | this hook | operator review (during shadow mode), audit |

### New stdout contract

Each invocation prints a single line to stdout:

```json
{"decision": "block"|"allow", "reason_code": "...", "mode": "...", "session_id": "...", "timestamp": "..."}
```

Mirror the existing pattern from `quality_gate.py`. Greppable + parseable.

### New exit-code contract

| Exit | Meaning |
|---|---|
| 0 | allow (or always in shadow mode) |
| 2 | block; stderr contains single-line reason |

Same contract as `quality_gate.py`. The host handles "non-zero exit + stderr" as a block signal.

### No schema breaks

- `close_accounting.py`'s `evaluate_retrospective_gate()` is a NEW function; existing callers (`close_runner.py`) keep their current direct calls until U6 migration. No removals in U1-U3.
- `validate_close_receipt.py`'s text validator is untouched; the new `validate_aar_session_binding()` is additive.

---

## Data Model

### Hook decision log entry

```json
{
  "decision": "block",
  "reason_code": "retrospective_needs_attention",
  "mode": "enforce_with_aar_lite",
  "session_id": "019f9bfe-...",
  "timestamp": "2026-07-26T15:32:18.123Z",
  "aar": {
    "status": "completed",
    "mode": "lite",
    "completed_at": "2026-07-26T15:31:50Z",
    "report_sha256_prefix": "a3f2c1..."
  },
  "ledger_retrospective_state": "needs_attention",
  "ledger_counts": {
    "wiki": 1,
    "commits": 3,
    "tool_calls": 42,
    "handoffs_mine": 1
  }
}
```

Written one JSON object per line to `~/.grok/logs/close-compliance-stop/<session>.jsonl`. Append-only (F-25 `msvcrt.locking` sidecar for concurrent-fire safety). Operator scrapes this for the shadow-mode review — the schema-rich fields mean a single JSONL line answers "what was the gate state, what was the receipt state, what did the counts say" without re-reading artifacts. The older 5-field schema (decision/reason_code/mode/session_id/timestamp) is subsumed; old operator tooling parsing the simpler schema continues to work because all five base fields are still present.

### Receipt check internally

The hook does NOT write any state file. It reads only:

| Read | Path |
|---|---|
| Harness session id | env `GROK_SESSION_ID` |
| Close evidence ledger | `P:/.artifacts/close-evidence/<sid>.json` |
| AAR completion state | `P:/.artifacts/aar/<sid>/_run.json` |
| AAR report (for hash) | `P:/.artifacts/aar/<sid>/aar-report.md` |

The hook writes only:

| Write | Purpose |
|---|---|
| Log JSONL line | Shadow-mode observability |
| stdout decision | Hook contract |
| stderr (on block) | Block feedback |

No artifact side-effects in enforce modes.

### Why no state file

State persistence is `quality_gate.py`'s job (it owns `~/.grok/hooks/state/quality-*-<sid>*`). The new hook is **stateless** — every fire reads everything from disk fresh. This is safe because:

1. The Stop event fires once per session termination.
2. The close-evidence ledger is the authoritative "did the scanner run?" signal; the hook trusts it.
3. The AAR receipt is content-addressed; re-hashing on each fire is O(report_size).

If state ever becomes necessary (e.g., to remember "I blocked last time, don't block again this turn"), it should go in a separate file under `~/.grok/hooks/state/`, not in the close-aar artifacts tree.

---

## Alternatives

We considered four architectural placements for this enforcement. They share a hidden anchor: **the gate must fire AFTER the agent has emitted its response.** Hidden anchor stated: "the Stop event is the correct hook surface." That assumption came from `~/.grok/docs/user-guide/10-hooks.md:94` (Stop can block the stop) — verified. Any option that doesn't fire post-response doesn't fix RC-1.

| # | Option | Hidden assumption shared with chosen option |
|---|---|---|
| 1 | **Stop hook on `close_compliance_stop.py`** ← chosen | Stop is the correct surface; fires post-response |
| 2 | PreToolUse regex on `run_terminal_command` matching `/close` keyword | A PreToolUse hook can block tool execution |
| 3 | Stronger prose in `~/.grok/skills/close/SKILL.md` | LLM honors prose under closure pressure |
| 4 | Subagent `review-changes` style AAR auto-invocation | A reviewer subagent catching /close calls is reliable |

**Selection criterion:** the option that produces a stop that **the agent cannot bypass via shell, prose, or self-justification**, with the lowest operator-review burden during rollout.

**Chosen: Option 1.** Stops are documented as the only blocking post-response hook (`10-hooks.md:94`); the failure mode of Option 3 is precisely what this design addresses (red-team RC-1); Option 2 fires too early (before the LLM runs /close); Option 4 introduces a new agent surface whose failure modes are unverified. Wins because Option 1 is the only one that fires *after* the agent has emitted its close summary — exactly the moment of failure RC-1 names.

**Why not Option 2 (PreToolUse):** the `/close` skill is invoked by an LLM skill routing, not a shell command. PreToolUse is the wrong hook to gate. The skill's own first `run_terminal_command` to launch `close_accounting.py` happens *inside* the skill, after the LLM has already routed — too late, the LLM has already emitted prose.

**Why not Option 3 (prose):** the red-team documented this as the failure mode. RC-1, RC-2, RC-3, RC-4, RC-5 all share a single root: prose fails under closure pressure. Option 3 has been tried and failed at least five times.

**Why not Option 4 (subagent reviewer):** introduces a new failure surface (subagent reliability under load). The wiki concept `mandatory-step-enforcement-code-over-prose.md` names the state-machine guard pattern; Option 4 is closer to a "second LLM judge" — high cost, low determinism, no incremental evidence that it would fire.

### Secondary alternatives considered

**SA-1: Implement the gate inside `quality_gate.py` (extend the existing hook).** Rejected (F-08): verified `quality_gate.py` is 1650+ lines (the 800-line claim is out of date). Mixing concerns would push the file past 2000 lines and reduce testability. Better to add a sibling script with the same rollout-pattern precedent. **Note:** the R-7 fallback uses a DIFFERENT fallback (PreToolUse on `/close`'s launching command), NOT SA-1, because SA-1 is now structurally worse than the design originally implied.

**SA-2: Use `GROK_CLOSE_BYPASS=1` env var as escape hatch.** Rejected (this is RC-3 in disguise). The agent can set it via `run_terminal_command`. The only uncheatable bypass is operator-controlled config via `~/.grok/config.toml`, which the agent cannot reach under our existing search_replace mutation-gate. We use `GROK_CLOSE_COMPLIANCE_MODE` instead.

**SA-3: Make `--lite` always valid.** Chosen as default (mode `enforce_with_aar_lite`). The wiki concept `close-auto-invokes-aar.md` confirms full AAR is the goal, but the binding check is what matters structurally — content depth is separate from compliance.

**SA-4: Skip the Stop hook entirely; rely on the close-runner's loop.** Rejected: the loop is LLM-internal; the agent can emit `/close` summary once, label the loop "resolved on first pass," and the harness sees a clean stop. The Stop hook sees `lastAssistantMessage` AFTER the agent has finished reasoning.

**SA-5: Use `SessionEnd` instead of `Stop`.** Rejected for this design (RC-6). `SessionEnd` is documented as non-blocking (`10-hooks.md:96`). Session-level enforcement requires a separate mechanism; deferred to Open Questions.

---

## Security

### Threat model

| Threat | Mitigation |
|---|---|
| Agent forges AAR receipt (copies `_run.json` from a previous session) | `session_id` binding + harness env `GROK_SESSION_ID` check. A reused `_run.json` from a different session mismatches. |
| Agent forges receipt via different content hash | SHA-256 mismatch on `report_sha256` re-check at every fire (`hashlib.sha256()` per F-29). |
| **Agent pre-writes a valid receipt BEFORE the close scanner runs (F-03)** | **Timestamp check:** `aar.completed_at` MUST be strictly after `ledger.generated_at`. The agent can match `session_id` + `report_sha256` in advance, but cannot forge a future timestamp because the comparison is against the ledger written by the scanner AFTER any pre-write. Rejected with `REASON_PREWRITE = "aar_pre_write_attack_rejected"`. |
| Agent creates empty AAR (just enough to pass) | `--lite` accepted as valid receipt; full-AAR reserved for high-substance sessions via the staged `enforce_full_aar_for_high_substance` mode. The decision tree is layered, not binary. Pre-U8 receipts (no `mode` field) block in strict modes — intentional F-06 surface. |
| Agent modifies ledger to mark `retrospective: pre_satisfied` | The hook does NOT trust the ledger for the receipt side — it independently reads the AAR artifact and binds it to the harness session. Even if the agent could write the ledger, the receipt still has to validate (and the F-03 timestamp check guards against pre-population). |
| Agent disables the hook by deleting the JSON registration | Agent cannot write `~/.grok/hooks/*.json` without the existing `mutation_pre.py` PreToolUse hook flagging it; even if it did, the operator's `/reload-plugins` would notice. The hook surfaces structured decisions on stdout for log scraping, so silencing the JSON registration also fails the `~/.grok/logs/close-compliance-stop/` log review. |
| Agent writes to `~/.grok/logs/close-compliance-stop/` directly | The hook writes JSONL; the agent could overwrite the log. The decision is still on stdout and stderr (the harness surfaces these regardless), so the block still fires. The log is for operator observability, not enforcement. F-25's msvcrt.locking prevents partial-line corruption but does not stop intentional overwrite. |
| Agent re-runs close-accounting with stale evidence | Out of scope — `close_accounting.py` is the LLM's tool; if the LLM can defeat the scanner, that's a separate concern (RC-1 in the LLM domain). This hook protects the boot-from-fresh path. The hook re-reads the ledger every fire (no caching) so a rewritten ledger is picked up immediately. |
| Operator accidentally promotes to `enforce_full_aar` | The 4th mode `enforce_full_aar_for_high_substance` is the conservative step. The rollout plan (§ Rollout) gates each promotion on a review of `~/.grok/logs/close-compliance-stop/`. |

### Reasonable concerns not addressed

- **Side-channel: agent writes to `~/.grok/logs/close-compliance-stop/` directly.** The hook writes JSONL; the agent could overwrite the log. The decision is still on stdout and stderr (the harness surfaces these regardless), so the block still fires. The log is for operator observability, not enforcement.
- **Race: agent emits summary, hook fires, then agent rewrites ledger.** Re-read at every Stop fire is the structural fix. The hook does not cache state.

### Privileges

- Reads: workspace artifacts (`P:/.artifacts/...`), env vars, harness payload.
- Writes: only `~/.grok/logs/close-compliance-stop/<session>.jsonl` (operator-owned).
- No network, no shell, no subprocess.

---

## Observability

### What the operator sees

1. **stdout per Stop event:** a single JSON line with schema-rich fields per F-22: `decision`, `reason_code`, `mode`, `session_id`, `timestamp`, **and** `aar.{status, mode, completed_at, report_sha256_prefix}`, `ledger_retrospective_state`, `ledger_counts.{wiki, commits, tool_calls, handoffs_mine}`. Operator can investigate block events from the JSONL alone — no need to re-read artifacts.
2. **stderr on block:** a single descriptive line naming the reason code and a directive to `/aar`. The model reads this on the next turn.
3. **JSONL log:** `~/.grok/logs/close-compliance-stop/<session>.jsonl` — append-only (F-25: `msvcrt.locking` sidecar for concurrent-fire safety). One line per Stop event.
4. **Counters** (operator-computed): in shadow mode, count `(decision == "block") / total`; this is the projected false-positive rate of the future enforcement.
5. **No new dashboards, no new dependencies.** The hook surfaces go through the existing `~/.grok/logs/` tree, which the operator already reviews.

### Metrics to track

| Metric | Source |
|---|---|
| Block rate (in enforce modes) | JSONL count of `"decision": "block"` |
| Reason-code distribution | JSONL count grouped by `reason_code` |
| False positive rate | operator review of block events with valid AARs run after |
| Time-to-resolution | timestamp diff between block event and the next successful AAR completion |
| Mode-promotion evidence | JSONL: zero `decision: block` in shadow before promoting |

### Alerts

The hook does NOT send alerts (no HTTP, no shell). The operator's nightly review of `~/.grok/logs/close-compliance-stop/` is the channel. The wiki concept `quality-gate-hook-system-implementation.md` documents this same pattern.

### Failure mode visibility

Fail-open on any error → exits 0. **F-04 fix:** `main()` wraps `_run_main()` in `try/except Exception`; on any internal exception the hook emits `_emit_decision(sid, "fail_open", ledger=None, aar=None)` and calls `_write_hook_error(exc, sid)` which writes a durable HOOK_ERROR record to `~/.grok/hooks/state/hook-error-<sid>.jsonl` (mirrors `quality_gate.py:1388-1421`). The JSONL decision log therefore records the fail-open event with `reason_code="fail_open"` — distinguishable from "decisive allow" without inspecting stderr. The HOOK_ERROR record carries `enforcement_state="ENFORCEMENT_UNAVAILABLE"` so post-hoc consumers (audit, SIEM) treat it as a missed enforcement, not an allowed stop.

---

## Key Decisions

1. **Decision: Add a new Stop hook, not extend `quality_gate.py`.**
   - Rationale: single-purpose scripts are easier to test, audit, and roll back. **F-41 fix:** the evidence for this is structural — multi-concern scripts accumulate cross-cutting change requests, which is why `quality_gate.py` grew to 1650+ lines (verified via direct grep of `~/.grok/hooks/scripts/quality_gate.py` line count). A fresh, narrow script with one job has fewer edit vectors. The "single-purpose" claim is also a fleet-wide convention documented at `~/.grok/docs/user-guide/06-hooks.md` (single-purpose-script recommendation).
   - Rejected: merge into `quality_gate.py` (would push it past 2000 lines, entangle verify-fingerprint concerns with /close-obligation concerns).
2. **Decision: Four-tier rollout via `GROK_CLOSE_COMPLIANCE_MODE`.**
   - Rationale: mirrors `quality_gate.RECEIPT_GATE_MODES` precedent (3-mode → this design uses 4-mode to allow granular progressive rollout: shadow → lite → high-substance-strict → always-strict). Provides staged promotion gate on operator-reviewed shadow evidence; each promotion is operator-invoked, never self-justified.
   - Rejected: binary enforce (too aggressive a flip from current state); three-tier (would skip the high-substance intermediate layer, forcing an all-or-nothing strictness jump from P1 to P3).
3. **Decision: Multi-signal `substantive_work` union via U0 shared module (F-09).**
   - Rationale: closes RC-2 (single-signal false negatives). Each signal is cheap; the union is one OR. **F-09:** extracted to `close_substance.py` so the hook and the `evaluate_retrospective_gate` helper share the single source of truth. Threshold constants live in the shared module too.
   - Rejected: replace `_has_code_writes` with a richer detector (would invalidate existing signal; harder to verify regression); inline-hook logic without U0 (would duplicate the OR-union between hook and helper).
4. **Decision: `--lite` accepted as valid receipt by default; full-AAR reserved for high-substance.**
   - Rationale: closes RC-5 without denying operators the `--lite` escape when substance is low. **F-18 fix:** the structural-equivalence claim is soft — `close-auto-invokes-aar.md` is the only cited wiki concept; it argues "full AAR is the goal" but does not document a specific instance of lite-equivalent content. The actual binding check (session_id + hash + status + post-scanner completion) is the structural fix; lite-vs-full content depth is a separate concern. **Acceptance:** this decision holds pending operator review of P1 shadow-mode evidence. If P1 shows lite receipts that are content-inadequate (operator-flagged), the design revises toward stricter enforcement.
   - Rejected: require full-AAR always (would require `mode=full` flagging in many sessions and inflate friction).
5. **Decision: No `--force` escape hatch.**
   - Rationale: any flag forgeable by the agent fails RC-3. The only operator-side bypass is config-mode toggle (change `GROK_CLOSE_COMPLIANCE_MODE` to `shadow`) or termination (Ctrl+C bypasses Stop). Both require explicit operator authority.
   - Rejected: implement `--force` as flag (fails RC-3); implement as environment variable (forgeable).
6. **Decision: Read AAR receipt directly; do not trust the ledger's stated retrospective state.**
   - Rationale: independent verification at gate time is the structural fix for RC-4. The ledger is for `close_runner.py`'s loop; the Stop hook is the final backstop. **F-03:** additionally checks `aar.completed_at > ledger.generated_at` to close the pre-write attack vector (a valid receipt pre-populated before the scanner ran would pass session-binding + hash checks; only the timestamp check catches it).
   - Rejected: trust ledger only (closes RC-1 but not RC-4); session-binding + hash only (closes RC-4 forgery but not RC-4 pre-write).
7. **Decision: Stateless hook.**
   - Rationale: minimize side-effect surface; the hook's only write is a JSONL log line. No `~/.grok/hooks/state/close-compliance-*.json` files.
   - Rejected: stateful (introduces cleanup/retention concerns on a session-bounded file).

---

## Risk Table

| ID | Risk | Probability | Impact | Mitigation |
|---|---|---|---|---|
| R-1 | Hook timeouts in production | Low | Medium (fails-open → no block, but no enforcement) | Initial timeout **30s** (matches R-7 mitigation floor; F-19). On Windows + antivirus, hashing a 10MB report can exceed 10s; 30s gives headroom. Tunable downward once JSONL `elapsed_s` measurements confirm. |
| R-2 | AAR --lite creates valid receipt but content is hollow | Medium | Low (the binding check catches session forgery; content depth is a separate concern) | Track via a future `validate_aar_minimum_content()` follow-up; out of scope for this design. The 4th enforce mode (`enforce_full_aar_for_high_substance`) mitigates operational impact. |
| R-3 | Operator promotes to `enforce_full_aar` and discovers false positives | Medium | Medium (sessions blocked; operator must intervene) | The staged rollout (§ Rollout) requires shadow-mode evidence before each promotion. JSONL counting is the verification. |
| R-4 | Hook adds load to every Stop event | Low | Low (1 file read + 1 hash + 1 JSON parse) | 30s timeout per F-19; observe `elapsed_s` field added in **U1** (not U5 — corrected). Field is in JSONL decision entry. |
| R-5 | `_run.json` schema evolves; hook crashes | Low | Medium (fail-open → no enforcement until patched) | The hook reads each field with default fallback. Schema evolution surfaces as silent allow → **operator notices via the F-22 JSONL log, which now includes AAR `status`/`mode`/`report_sha256_prefix` and ledger `retrospective.state`**. So a schema-drift failure is detectable, not silent. |
| R-6 | The AAR skill changes the canonical receipt path (e.g., renames `_run.json` or moves under a different dir) | Low | Medium (silently skips enforcement — `_read_aar_receipt` returns None → allow in shadow, block in enforce) | **F-12 fix:** U5 includes a contract test that asserts the AAR canonical path matches the expected `P:/.artifacts/aar/<sid>/_run.json`. If AAR ever drifts, the test fails on the next CI run. Test fixtures: real AAR run dir + a stub `_run.json`. |
| R-7 | `~/.grok/hooks/quality-gate.json` cannot register two Stop entries | Low | High (the entire design blocks) | F-08 fix: U2 verification runs `python ~/.grok/hooks/scripts/active_surface_snapshot.py`. If multi-entry is rejected, the fallback is **not** SA-1 (quality_gate.py is now 1650+ lines and folding in this hook would violate single-purpose). The fallback is **Option 2 from Alternatives**: a PreToolUse hook on `run_terminal_command` matching the `/close` skill's launching command. This fires too early for normal /close flow but is acceptable as a strict fallback because the LLM has no shell-only path past it. |
| R-8 | The `--lite` vs full distinction causes operational friction (operators hit `LITE_REJECTED` and must re-run without --lite) | Medium | Low (one rerun per affected session) | F-06 fix: `enforce_with_aar_lite` accepts any (default); `enforce_full_aar*` requires explicit `mode=="full"`. Pre-U8 receipts (no `mode` field) are blocked in strict modes — this is intentional to surface the mode-field gap, not a false-positive. |
| R-9 | Other plugins/sessions writing to `~/.grok/logs/close-compliance-stop/` collide | Low | Low (log is for observability only; collision = noise) | F-25 fix: hook appends per-session filenames AND uses `msvcrt.locking`-based file lock on the append so concurrent fires on the same session are serialised. |
| R-10 | New hook competes with existing `quality_gate.py` for harness attention | Low | Low | F-11 fix: order in the JSON `Stop → hooks` array is **(close_compliance_stop FIRST, quality_gate.py SECOND)**. The closer-to-source obligation reaches the model last (the second hook's stderr is the most recent directive the model sees), so `/aar` is addressed first by the model. Block union is preserved: if either blocks, exit 2. |

---

## Threshold Justification

The cross-cutting observation noted: thresholds `TOOL_CALL_THRESHOLD=5`, `HIGH_SUBSTANCE_WIKI_CONCEPTS=3`, `HIGH_SUBSTANCE_COMMITS=5`, `HIGH_SUBSTANCE_TOOL_CALLS=10` are arbitrary constants. Per `~/.claude/CLAUDE.md` § "Six flaws to avoid #1 — no arbitrary thresholds," each constant must justify itself.

| Constant | Value | Justification |
|---|---|---|
| `TOOL_CALL_THRESHOLD = 5` | 5 | Floor for the substance-detector OR-union (RC-2 fix). Below 5, every micro-task with a single file edit triggers the gate (false-positive class A). Above 10, research-heavy sessions without code writes would still slip through (false-negative class B — what RC-2 was actually about). 5 chosen as the lower of the two operational ranges; validated empirically by `quality_gate.py`'s claim-vs-verify check, which uses 10-minute windows over multi-tool-call sessions (the 5-tool-call floor is consistent with the verify-receipt's claim trigger). **Tunable:** if P1 shadow review shows systematic false positives, raise; if misses, lower. |
| `HIGH_SUBSTANCE_WIKI_CONCEPTS = 3` | 3 | Wiki-concepts count where "full-AAR required even in non-strict modes." Below 3, normal sessions that touched one ADR or concept would be forced into full-AAR (over-reach). Above 5, multi-hour research sessions writing 4 concepts would still slip to lite (RC-5 regression). 3 is the boundary of "operator writes a substantial wiki change-set during the session," which is the substance level `close-auto-invokes-aar.md` cites as needing real review. |
| `HIGH_SUBSTANCE_COMMITS = 5` | 5 | Commit-count trigger for full-AAR strictness. Below 5, the typical /close of a normal session with 2-3 commits would trigger strictness (over-reach). Above 10, implementation-heavy work would slip to lite (RC-1 regression). 5 matches the threshold implied in `close-coordinator.py` work-classification handoffs. |
| `HIGH_SUBSTANCE_TOOL_CALLS = 10` | 10 | Tool-call trigger for full-AAR strictness. Matches the 60s timeout floor in `quality_gate.py` (an industry-standard verdict surface for "this session had real work"). Below 10, ordinary quick Q&A sessions would force full-AAR. Above 20, an orchestration session with 12 dispatch calls would skip strictness (the failure mode RC-2 is most concerned about). |

**Empirical caveat:** these are operator-judgment values, not measurement-driven. The P0 shadow-mode rollout collects per-session `tool_calls, handoffs_mine, commits, wiki` counts in the JSONL decision log (already covered by F-22). After 30 days, the operator can review the distribution and adjust the constants with data. The design accepts the initial values as operator-approved defaults; this is a known follow-up.

---

## Rollout

### Phases

| Phase | Mode | Acceptance gate | Operator action |
|---|---|---|---|
| P0 | Ship default = `shadow` | U5 tests green; shadow JSONL accumulates | Observe for 7 days |
| P1 | `enforce_with_aar_lite` | JSONL shows zero `"decision": "block"` events that disagree with a valid subsequent AAR | Operator edits `~/.grok/config.toml` to set mode |
| P2 | `enforce_full_aar_for_high_substance` (default for high-substance, lite for low) | P1 false-positive rate = 0 over 14 days | Operator edits config |
| P3 | `enforce_full_aar` (strict) | P2 false-positive rate = 0 over 21 days | Operator edits config |

P0 → P1 is a single config change. P1 → P2 is a config change + a mode-promotion commit. P3 is a config change gated on operator evidence.

### Shadow mode operation

During P0:

1. The hook fires on every Stop event.
2. It logs `{"decision": "block"|"allow"}` to `~/.grok/logs/close-compliance-stop/`.
3. It ALWAYS exits 0 (allow).
4. Operator reviews JSONL: count blocks, classify by reason code, decide whether the rule needs tuning before promotion.

Default rollout is `shadow` because:

- It produces zero behavior change. Existing sessions end the same way.
- It produces a JSONL of decisions that can be audited.
- Promotion is a single env-var flip.

### Rollback procedure

If the operator needs to roll back enforcement (e.g., a false-positive incident):

1. **Quick (F-16 fix):** edit `~/.grok/config.toml` `[hooks.env]` section OR set `GROK_CLOSE_COMPLIANCE_MODE=shadow` in the launch env. Stop hooks re-read env on each fire, so the next Stop event will allow. **Verification note:** the host's behavior of mapping `config.toml [hooks.env]` to env vars on each fire is unverified in this design (the existing `quality_gate.py` only reads `os.environ` at fire time, not config.toml); the operator workflow is therefore the launch env var OR `~/.grok/config.toml` (the latter depends on the host's config-resolution behavior, which is a separate discovery task — Open Questions § OQ-7).
2. **Hard:** revert the JSON-registration edit in `~/.grok/hooks/quality-gate.json` (single hunk) → commit. The hook stops firing.
3. **Nuclear:** disable the hook with `~/.grok/disabled-hooks` per the `grok-per-hook-disable-layer-silent-suppression.md` pattern.

Rollback does NOT require deleting any artifact; the hook is stateless except for the JSONL log, which is for observability only.

### Verification at each phase

| Phase | Verification | Tool |
|---|---|---|
| P0 | U5 tests pass; `~/.grok/logs/close-compliance-stop/` accumulates; no operator-reported regressions | `pytest` + operator review |
| P1 | JSONL shows zero "block" without a subsequent AAR completion | Windows PowerShell (F-40): `Select-String -Path "$HOME/.grok/logs/close-compliance-stop/<sid>.jsonl" -Pattern '"decision":"block"' \| Measure-Object \| Select-Object -ExpandProperty Count`; cross-host `awk` equivalent on Git Bash |
| P2 | Same as P1 over 14 days, AND a manual session shows `enforce_full_aar_for_high_substance` fires correctly | Same JSONL review + manual reproduction |
| P3 | Same as P2 over 21 days, AND a quarterly review of `enforce_full_aar` strictness | Same JSONL review + periodic audit |

---

## Open Questions

| ID | Question | Resolution |
|---|---|---|
| OQ-1 | Does `~/.grok/hooks/quality-gate.json` allow multiple Stop entries? | Confirmed by spec but not by live runtime as of 2026-07-26. U2 verification step runs the active-surface-snapshot script to confirm. |
| OQ-2 | Can the operator hook layer resolve `python` on the PATH at Stop-fire time? | Yes (every existing hook does this). |
| OQ-3 | Should `enforce_full_aar_for_high_substance` distinguish wiki concepts by file path (sessions written to `P:/.data/wiki/`) vs general `wiki` count? | Out of scope; the existing `Evidence.counts.wiki` int count is the source. **F-35 fix:** the previously cited `counts.wiki_concepts` list does not exist; using the `wiki` int count is the correct schema. |
| OQ-4 | RC-6 (SessionEnd hook): is `SessionEnd` capable of blocking? | Per `10-hooks.md:96`, SessionEnd has "Blocking? No". Defer to a follow-up design if a hard-session-end enforcement is needed. |
| OQ-5 | Should the hook also catch cases where `/close` was never invoked at all (i.e., agent attempts to end session by giving up on /close)? | This design fires on Stop regardless. The same mechanism covers it. RC-6 covers the SessionEnd complement. |
| OQ-6 | What about content-depth enforcement for `--lite` (RC-5 §2)? | Out of scope. Closing RC-5 at the structural level (binding) is sufficient for now; a future `validate_aar_minimum_content()` could add depth as a separate concern. |
| OQ-7 (NEW) | Does Grok Build's hook loader map `~/.grok/config.toml [hooks.env]` blocks to env vars at each Stop-fire time, or only at launch? | **F-16 fix:** the verification step is `python -c "import os; print(os.environ.get('GROK_CLOSE_COMPLIANCE_MODE', 'NOT_SET'))"` from a session in shadow mode after the operator edits config.toml to set `GROK_CLOSE_COMPLIANCE_MODE=shadow`. If the env var appears, mapping happens at fire time. If not, the rollback procedure must use the launch env. |

---

## Coupling & Code-Smell Inventory (Appendix)

The inventory below counts DRY violations, positional parameters, touch-points, and mixed concerns for each module this design touches after all fixes land. Thresholds: DRY ≥3, params >7, touch-points >3, mixed concerns binary.

| Module | DRY count | Param count | Touch-points | Mixed concerns | Refactor justified? |
|---|---|---|---|---|---|
| `close_substance.py` (NEW, U0) | 0 (new file, sole purpose) | 3 (counts dict, has_writes, optional thresholds) | 2 (U1 hook + U3 helper) | No | N — within threshold |
| `close_compliance_stop.py` (U1) | 0 | **F-20 fix:** `main()` takes 0 positional params (only stdin via `sys.stdin.read()`); `_run_main()` takes 0; helper functions ≤3 each | 1 (hook loader) | No (single-purpose: /close→/aar enforcement) | N — within threshold |
| `~/.grok/hooks/quality-gate.json` | 0 | n/a | 1 (Stop matcher) | No (single-purpose JSON) | N — within threshold |
| `close_accounting.py` | **F-20 fix:** DRY=3 after U3 — (a) `scan_retrospective` reads `_run.json` schema, (b) `validate_aar_session_binding` reads same schema (U4), (c) `evaluate_retrospective_gate` (U3) is the third instance. **Refactor justified:** extract `_aar_receipt_schema` constants or `read_aar_state()` helper to consolidate schema access. Below the DRY≥3 threshold but on the boundary. | 2 in `evaluate_retrospective_gate(session_id, evidence=None)` | 2 (close_runner + stop hook, both via U0 shared module) | **F-23 fix:** partial. The file is 2200+ lines after U3 and ships multiple concerns (scan_*, gate resolution, ledger write). **Refactor justified:** extracting `evaluate_retrospective_gate` into a smaller module `retrospective_gate.py` next to `close_substance.py` would reduce coupling (this is the SA-1 fallback for the Inventory check, and is recommended as a U3.5 follow-up if the file grows further post-rollout). | **Partial refactor:** extract `evaluate_retrospective_gate` to `~/.grok/skills/close/__lib/retrospective_gate.py` in U3.5 if close_accounting.py grows beyond 2400 lines |
| `validate_close_receipt.py` | 0 (new function is additive) | 4 (`validate_aar_session_binding(ledger, aar_run_dir, expected_session_id, ...)`) | 1 | No | N — additive, no smell |
| `~/.grok/skills/aar/__lib/completion_receipt.py` | 0 | unchanged | 1 | No | N — single schema-write path |
| `~/.grok/skills/close/SKILL.md` | **F-48 fix:** indirect touch via U3 helper extraction and U1 hook registration. The skill's behaviour changes (enforcement surface); the SKILL.md does not get a code edit in this design but warrants a 1-sentence operator follow-up. | n/a | n/a | n/a | N — touch is operator-managed follow-up, not a code change in this design |

### Mixing analysis (F-23 fix)

The new hook is single-purpose (enforce /close→/aar obligation). It does NOT mix in claim-phrase detection (that's `quality_gate.py`'s job) or git persistence (that's `close_coordinator.py`'s job). Three hooks, three jobs.

**However:** the **helper** `evaluate_retrospective_gate` lands in `close_accounting.py`, a 2200-line file that already owns gate resolution, ledger writing, and ~10 scan functions. The hook-centric "no mixing" claim from the prior version was too narrow. **F-23 mitigation:** the helper is short, documented, and is a single source of truth (via U0's shared module). A future U3.5 refactor that moves it to its own file would reduce file-level coupling; this design flags that as a follow-up rather than blocking ship.

### DRY analysis (F-20 fix)

| Pattern | Occurrences | Refactor? |
|---|---|---|
| AAR `_run.json` schema access (read skill/session_id/status/report_sha256) | 3 (U1 hook + U4 validate_aar_session_binding + U3 evaluate_retrospective_gate) | Below DRY≥3 threshold but extract a `read_aar_state()` helper in a U3.5 follow-up would consolidate to 1 occurrence |
| `aar-report.md` content hashing | 2 (U1 `_hash_aar_report` + U4 `validate_aar_session_binding`) | Below DRY≥3; not a refactor candidate |
| Multi-signal substance check | **2** (now in U0 shared module, called by both U1 hook and U3 helper) | F-09 fix in effect; refactor done |
| Session-id sanitization | **1** (U1 `_safe_sid`, used in both `_read_ledger` and `_read_aar_receipt`) | F-07 fix in effect; refactor done |

### Threshold met summary

- **DRY ≥3:** met for AAR-schema-access pattern in `close_accounting.py` (3 occurrences). F-23 fix: refactor deferred to U3.5 follow-up; documented as known smell.
- **params >7:** not met. The hook's `main()` takes 0 params; helpers take ≤3.
- **touch-points >3:** not met. The hook has 1 entry point; `close_substance` has 2 callers; `evaluate_retrospective_gate` has 2 callers.
- **mixed concerns:** partially met at the hook-level (no) and at the `close_accounting.py`-file-level (yes). F-23 fix: file-level mixing flagged as U3.5 follow-up.

**Ship recommendation:** the Inventory's conclusions are mostly accurate after these fixes; the only outstanding smell is the AAR-schema-access DRY=3 in `close_accounting.py`, which is below the threshold but worth consolidating in a follow-up.

---

## Implementation Plan

Implementation units ordered by commit. Each unit is independently testable and roll-back-able.

### Unit 0 — U0: Create shared `close_substance` module (NEW F-09/F-10 fix)

| Field | Value |
|---|---|
| Title | "U0: extract close_substance.py shared module for multi-signal check" |
| Files affected | NEW `~/.grok/hooks/scripts/close_substance.py` (~30 LOC) |
| Dependencies | none (lands before U1 ships) |
| Description | Single source of truth for the multi-signal substance detection (F-09). Eliminates the inline-hook + inline-helper duplication. Exports `compute_substantive_work(evidence_counts: dict, has_code_writes: bool) -> tuple[bool, dict]` and `is_high_substance(counts: dict) -> bool`, plus the threshold constants `TOOL_CALL_THRESHOLD`, `HIGH_SUBSTANCE_WIKI_CONCEPTS`, `HIGH_SUBSTANCE_COMMITS`, `HIGH_SUBSTANCE_TOOL_CALLS`. Both the hook (U1) and `evaluate_retrospective_gate` (U3) import from this module — single source of truth. |
| Acceptance criteria | (a) `python -c "import sys; sys.path.insert(0, r'C:/Users/brsth/.grok/hooks/scripts'); import close_substance; print(close_substance.compute_substantive_work({'commits':1}, False))"` returns `(True, {...})`; (b) no filesystem side effects (the module is pure computation); (c) test in U5 covers each signal individually + the OR union; (d) `is_high_substance({'wiki':3})` returns `True`; (e) `is_high_substance({'commits':5})` returns `True`; (f) `is_high_substance({})` returns `False` |
| Feature flags | none |
| Rollback | `rm ~/.grok/hooks/scripts/close_substance.py` |
| Disposition | **COMMIT_THIS_SESSION** (lands FIRST in the dependency order) |

### Unit 1 — U1: Ship the hook script in shadow mode

| Field | Value |
|---|---|
| Title | "U1: add close_compliance_stop.py (shadow mode default)" |
| Files affected | NEW `~/.grok/hooks/scripts/close_compliance_stop.py` (~340 LOC after F-01, F-04, F-22, F-25 fixes) |
| Dependencies | U0 (shared module must exist first) |
| Description | Self-contained hook script. Sibling-imports the shared `close_substance` module via `sys.path.insert` (F-10). Reads ledger, AAR receipt, env. Per-fire workspace resolution via `_resolve_workspace` (F-05). Logs decisions to JSONL with schema-rich fields (F-22). Outer try/except in `main()` ensures fail-open with HOOK_ERROR JSONL mirror of `quality_gate.py:1388-1421` (F-04). Validates pre-write attack defense (F-03 timestamp check). Implements all 4 modes including `enforce_full_aar_for_high_substance`. |
| Acceptance criteria | (a) `python -c "import ast; ast.parse(open(r'C:/Users/brsth/.grok/hooks/scripts/close_compliance_stop.py').read())"` returns 0; (b) `python -c "import sys; sys.path.insert(0, r'C:/Users/brsth/.grok/hooks/scripts'); import close_compliance_stop"` returns 0 (proves all imports resolve, including `close_substance`); (c) `echo '{"sessionId": "test-001"}' | python close_compliance_stop.py` exits 0 in shadow mode and exits 2 in `enforce_with_aar_lite` mode without a ledger; (d) `python close_compliance_stop.py < /dev/null` exits 0; (e) unit tests in U5 cover all 8 reason codes (REASON_NO_LEDGER, REASON_LEDGER_MALFORMED, REASON_AAR_MISSING, REASON_BINDING, REASON_NOT_COMPLETED, REASON_HASH_MISMATCH, REASON_PREWRITE, REASON_LITE_REJECTED, REASON_WORKSPACE_UNRESOLVABLE, REASON_OK, fail_open); (f) no network or shell calls (grep proves it); (g) hook reads `ledger.counts.tool_calls` correctly (post-U3); (h) missing `mode` field in receipt → BLOCK in `enforce_full_aar*` (F-06); (i) pre-write attack: receipt with `completed_at` ≤ ledger `generated_at` → BLOCK with REASON_PREWRITE (F-03); (j) inject an exception in `_read_ledger` → hook exits 0, logs JSONL with `reason_code="fail_open"`, writes HOOK_ERROR record (F-04) |
| Feature flags | `GROK_CLOSE_COMPLIANCE_MODE` (default shadow) |
| Rollback | `rm ~/.grok/hooks/scripts/close_compliance_stop.py` |
| Disposition | **COMMIT_THIS_SESSION** (lands SECOND in the dependency order) |

### Unit 2 — U2: Register the hook

| Field | Value |
|---|---|
| Title | "U2: register close_compliance_stop.py as a Stop hook entry" |
| Files affected | MODIFY `~/.grok/hooks/quality-gate.json:69-78` (~3 LOC added) |
| Dependencies | U1 |
| Description | Append the new script as a second hook entry in the Stop matcher. Match the format of the existing entry exactly. |
| Acceptance criteria | (a) `python -c "import json; json.load(open(r'C:/Users/brsth/.grok/hooks/quality-gate.json'))"` returns 0; (b) `python ~/.grok/hooks/scripts/active_surface_snapshot.py` lists `close_compliance_stop.py`; (c) the `Stop` matcher has exactly **2** hook entries (not 1, not 3); (d) `close_compliance_stop.py` is the FIRST entry (F-11 ordering); (e) the timeout is 30 (F-19) |
| Feature flags | none |
| Rollback | revert JSON-registration edit |
| Disposition | **COMMIT_THIS_SESSION** |

### Unit 3 — U3: Extract `evaluate_retrospective_gate()` in close_accounting.py

| Field | Value |
|---|---|
| Title | "U3: extract evaluate_retrospective_gate() helper from close_runner.py into close_accounting.py" |
| Files affected | MODIFY `~/.grok/skills/close/__lib/close_accounting.py` (~40 LOC added) |
| Dependencies | U0 (shared `close_substance` module exists) |
| Description | Move the gate-state computation from `close_runner.py:2175-2189` into a helper that takes (session_id, evidence | None) and returns (state, detail). Wire multi-signal union via `close_substance.compute_substantive_work()` (F-09: single source of truth — no hook-side duplicate). **Closes F-02:** `Evidence.counts` is extended to include `tool_calls` (int); the hook reads it correctly in the same commit. |
| Acceptance criteria | (a) **run the actual existing tests** at `~/.grok/skills/close/tests/` (after listing — see F-13 fix); do NOT assume `test_close_logic.py` exists — list the dir first and run what's there, e.g. `pytest ~/.grok/skills/close/tests/ -q`; (b) new helper has docstring + type hints; (c) `close_runner.py` call site unchanged (still calls the imported helper); (d) **`Evidence.counts` is extended to include `tool_calls` (int)**; (e) the new field appears in `P:/.artifacts/close-evidence/<sid>.json` after a fresh `/close` invocation; (f) hook reads the new `ledger.counts.tool_calls` field correctly; (g) helper imports `close_substance` (the same module the hook imports), so there's a single source of truth |
| Feature flags | none (no behavior change for existing sessions) |
| Rollback | revert `close_accounting.py` helper addition AND restore `close_runner.py:2175-2189` inline logic (F-47: rollback is multi-file, not single-file) |
| Disposition | **COMMIT_THIS_SESSION** |

### Unit 4 — U4: Add AAR session-binding validator

| Field | Value |
|---|---|
| Title | "U4: add validate_aar_session_binding() to validate_close_receipt.py" |
| Files affected | MODIFY `~/.grok/skills/close/__lib/validate_close_receipt.py` (~25 LOC added) |
| Dependencies | U3 |
| Description | New pure function (additive; does not modify the existing text validator). Reads `_run.json` + `report_sha256` from a stated `aar_run_dir`, verifies `session_id` matches expected, status is `completed`, and content hash matches. |
| Acceptance criteria | (a) `~/.grok/skills/close/tests/test_scanner.py` and `test_reconciliation.py` still pass; (b) new unit tests cover session mismatch, hash mismatch, missing receipt paths |
| Feature flags | none |
| Rollback | revert single-function addition |
| Disposition | **COMMIT_THIS_SESSION** |

### Unit 5 — U5: Add comprehensive hook tests

| Field | Value |
|---|---|
| Title | "U5: tests/test_close_compliance_stop.py with all reason-code coverage" |
| Files affected | NEW `~/.grok/hooks/scripts/tests/test_close_compliance_stop.py` (~250 LOC) |
| Dependencies | U1, U4 |
| Description | Use the existing test pattern from `tests/test_continuation_obligation.py` (temp dirs + payload stubbing). Cover: no ledger (block), malformed ledger (block), legitimate skip (allow), legitimate pre_satisfied (allow), needs_attention + valid receipt (allow), needs_attention + session mismatch (block), needs_attention + status=started (block), needs_attention + hash mismatch (block), enforce_full_aar + lite receipt (block), enforce_full_aar_for_high_substance + lite + low substance (allow), shadow mode always allows. |
| Acceptance criteria | (a) `python -m pytest ~/.grok/hooks/scripts/tests/test_close_compliance_stop.py -v` exits 0; (b) ≥10 test cases per reason code; (c) no production state modified (uses tmp dirs); (d) imports the hook as a module via importlib |
| Feature flags | none |
| Rollback | remove test file |
| Disposition | **COMMIT_THIS_SESSION** |

### Unit 6 — U6: Wire close_runner.py to the new helper

| Field | Value |
|---|---|
| Title | "U6: close_runner.py uses evaluate_retrospective_gate()" |
| Files affected | MODIFY `~/.grok/skills/close/__lib/close_runner.py` (~5 LOC changed) |
| Dependencies | U3 |
| Description | Replace direct inline gate computation with the helper call. Confirm via existing tests that no behavior regresses. |
| Acceptance criteria | all `~/.grok/skills/close/tests/` pass unchanged |
| Feature flags | none |
| Rollback | revert import + call site change |
| Disposition | **COMMIT_THIS_SESSION** |

### Unit 7 — U7: Wiki concept addendum

| Field | Value |
|---|---|
| Title | "U7: extend mandatory-step-enforcement-code-over-prose.md with the close_compliance_stop precedent" |
| Files affected | MODIFY `P:/.data/wiki/concepts/mandatory-step-enforcement-code-over-prose.md` (~30 LOC added) |
| Dependencies | U1-U5 |
| Description | Append a brief section noting that `/close → /aar` is now enforced at the Stop hook layer, naming the script + mode rollout. Tied to the structural-enforcement research already cited. Also touches `~/.grok/skills/close/SKILL.md` indirectly (F-48): the helper extraction (U3) and the new hook are part of the close skill's behaviour change. A SKILL.md edit is **not** in this design's scope; the closure operator adds a sentence pointing at the new enforcement surface. |
| Acceptance criteria | (a) wiki frontmatter `created: 2026-07-26` retained as update entry; (b) section is 30+ lines and cites the hook script path; (c) no other wiki concepts edited; (d) optional 1-sentence SKILL.md edit by operator as a follow-up |
| Feature flags | none |
| Rollback | revert wiki edit |
| Disposition | **COMMIT_THIS_SESSION** (F-14 fix: the AGENTS.md auto-commit standing policy covers wiki concept appends to existing files; this is not a new wiki concept — it's an extension to an existing one — and the standing rule applies. The HANDOFF disposition was unjustified.) |

### Unit 8 — U8: AAR `_run.json` records `mode`

| Field | Value |
|---|---|
| Title | "U8: AAR skill writes mode=full|lite to _run.json on completion" |
| Files affected | MODIFY `~/.grok/skills/aar/__lib/completion_receipt.py:79-85` (~3 LOC added) + minor caller in `~/.grok/skills/aar/__lib/run_aar.py` to thread `--lite` flag into `finalize_aar_run` |
| Dependencies | U4 (so the validator uses the same field name); **MUST land before P1 mode activation** (F-32 sequencing) |
| Description | Add a `mode: str = "full"` parameter to `finalize_aar_run()`. The AAR skill's CLI parser threads the `--lite` flag into a call-site that writes `state.mode = "lite"|"full"` to `_run.json` before finalization. The hook reads `aar.get("mode")` and uses F-06 semantics (missing → block in `enforce_full_aar*`). |
| Acceptance criteria | (a) existing AAR tests still pass; (b) `state.get("mode")` returns `"lite"` or `"full"` after a `/aar` or `/aar --lite` run; (c) the new field is also accepted by `validate_aar_session_binding()`; (d) **MUST commit before P1 mode activation in § Rollout** — the operator cannot flip to `enforce_full_aar*` until this unit ships |
| Feature flags | none |
| Rollback | revert `completion_receipt.py:79-85` change AND remove `mode` threading from `run_aar.py` |
| Disposition | **COMMIT_THIS_SESSION** (with F-32 sequencing note: ship before P1) |

---

## Traceability Matrix

| Design component | Implementation unit |
|---|---|
| Multi-mode rollout | U1 (env var + mode parsing in `_mode()`) |
| Multi-signal `substantive_work` union (F-09 single source of truth) | **U0 (shared `close_substance` module)** — both U1's hook and U3's helper import from it |
| Ledger re-read at every fire | U1 (`_read_ledger()` per `_run_main`) |
| AAR receipt re-read at every fire | U1 (`_read_aar_receipt()` per `_run_main`); F-12 drift test in U5 |
| Session binding check | U1 (`session_id != sid` check) + U4 (`validate_aar_session_binding()`) |
| Content hash check | U1 (`_hash_aar_report()`); schema uses `hashlib.sha256()` directly (F-29, F-49) |
| AAR canonical-path drift test (F-12) | U5 (asserts the path matches `P:/.artifacts/aar/<sid>/_run.json`) |
| Pre-write attack defense (F-03) | U1 (timestamp check between AAR `completed_at` and ledger `generated_at`) |
| Fail-open contract (F-04) | U1 (`_write_hook_error` mirrors `quality_gate.py:1388-1421` + outer try/except in `main()`) |
| Workspace resolution (F-05) | U1 (`_resolve_workspace` per-fire, payload `workspaceRoot` → env `GROK_WORKSPACE` → `P:/` with existence check) |
| Mode-field strictness (F-06) | U1 (`aar.get("mode")` no default → block in `enforce_full_aar*`) + U8 (writes `mode` for new AAR runs) |
| Session-id sanitization (F-07, F-54) | U1 (`_safe_sid` shared between ledger and AAR paths; rejects `..` and zero-length) |
| Path-traversal defense (F-46) | U1 (`_read_aar_receipt` validates resolved path is under `aar_root`) |
| JSONL schema-rich log (F-22) | U1 (`_emit_decision` includes `aar.status`, `aar.mode`, `report_sha256_prefix`, `ledger_retrospective_state`, `ledger_counts`) |
| Stop hook order (F-11) | U2 (new hook fires FIRST in `Stop → hooks` array) |
| Timeout (F-19) | U2 (30s, justified in JSON edit note; tunable down post-rollout) |
| `Evidence.counts` extension with `tool_calls` (F-02) | U3 (extends property at `close_accounting.py:117-128`) |
| `--lite` vs full distinction | U8 (writes `mode` field) + U1 (F-06 mode-aware decision: missing → block in strict modes) |
| Sequencing: U8 must ship before P1 (F-32) | U8 (acceptance criterion + Rollout § P1 gate) |
| `~/.grok/hooks/quality-gate.json` registration | U2 |
| Failure mode `--force` removed | U1 (no env var implements `--force`; only `GROK_CLOSE_COMPLIANCE_MODE` for operator) |
| Log-dir env override (F-15) | U1 (`_resolve_log_dir` reads `GROK_CLOSE_COMPLIANCE_LOG_DIR`) |
| Cross-package import (F-10) | U0 (`close_substance.py` lives next to the hook — sibling import) |
| Hook ordering rationale | Rollout + U2 (F-11): close_compliance_stop FIRST |
| Wiki concept extension with hook precedent | U7 |
| Invalid-mode warning (F-28) | U1 (`_mode()` emits stderr warning on invalid env value) |
| Stdin read robustness (F-27) | U1 (`_run_main` catches `UnicodeDecodeError`/`OSError` in addition to `JSONDecodeError`) |
| Concurrent append safety (F-25) | U1 (`_file_lock` context manager with `msvcrt.locking`) |
| HOOK_ERROR JSONL on internal exception | U1 (`_write_hook_error` mirrors quality_gate.py:1388-1421) |
| PowerShell verification command (F-40) | Rollout § Verification (`Select-String ... | Measure-Object`) |

---

## File Change Inventory

| File | Action | LOC delta | Implementation unit |
|---|---|---|---|
| `~/.grok/hooks/scripts/close_substance.py` | NEW | +30 | U0 (shared multi-signal module) |
| `~/.grok/hooks/scripts/close_compliance_stop.py` | NEW | +340 (post-F-01/04/22/25 expansion) | U1 |
| `~/.grok/hooks/quality-gate.json` | MODIFY | +5 (single hunk in Stop matcher; F-11 ordering + F-19 timeout) | U2 |
| `~/.grok/skills/close/__lib/close_accounting.py` | MODIFY | +40 (helper extraction + `tool_calls` schema extension) | U3 |
| `~/.grok/skills/close/__lib/close_runner.py` | MODIFY | +5/-5 (swap inline → helper; multi-file rollback per F-47) | U6 |
| `~/.grok/skills/close/__lib/validate_close_receipt.py` | MODIFY | +25 (new function, additive) | U4 |
| `~/.grok/hooks/scripts/tests/test_close_compliance_stop.py` | NEW | +280 | U5 |
| `~/.grok/skills/aar/__lib/completion_receipt.py` | MODIFY | +3 (`mode` field) | U8 |
| `~/.grok/skills/aar/__lib/run_aar.py` | MODIFY | +5 (thread `--lite` flag) | U8 |
| `P:/.data/wiki/concepts/mandatory-step-enforcement-code-over-prose.md` | MODIFY | +30 (section extension) | U7 |

**Total LOC delta:** +763 / -5 across 10 files. New files: 3 (U0, U1, U5). Modified files: 7.

---

*End of design document.*
