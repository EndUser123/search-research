# /handoff ROADMAP — v0.2 and beyond

This file captures the design work that went beyond v0.1 scope. Each section is a candidate for a future version with the rationale for deferral.

**Principle:** ship v0.1 thin, validate it on real sessions, then add features that the validation proves are needed. Do not add features because the design document describes them.

## What v0.1 does

- `/handoff new <topic>` (or just `/handoff`) — one handoff for the stream the user asks about
- Reads `compaction/segment_*.md` for within-session compaction recovery
- Writes `P:\docs\handoffs\<topic>-<YYYYMMDD>\HANDOFF.md`
- Chain header with `thread_id` + `parent_handoff_path`
- 16 mandatory fields (Investigation shape)
- Notes other outstanding streams; does not write them
- Manual `parent_handoff_path` escape hatch for explicit cross-session continuation

## v0.2 candidates (reprioritized 2026-07-20 based on H-3 evidence)

**H-3 evidence (4 real sessions):** stream_count=1/4 (all single-stream); handoff_type=investigation/4 (all Investigation); fields_missing=0/4 (contract followable); validators caught 2 real issues.

This evidence deprioritizes multi-stream detection and type-specific templates, and keeps cross-session chain traversal as the top v0.2 priority.

### Continue, update, close, status variants

- `/handoff continue <path>` — recover prior context, inherit `thread_id`
- `/handoff update <path>` — append revision block (never mutate)
- `/handoff close <path>` — mark closed, promote decisions to ADRs
- `/handoff status` — survey open threads

**Deferred because:** v0.1 needs to prove the basic handoff works before adding lifecycle operations. The manual `parent_handoff_path` escape hatch covers the urgent case (user explicitly continues prior work).

**Evidence note (H-3):** the 4 handoffs written against historical sessions produced heavy `[UNKNOWN]` labels for outcome/state because retroactive handoffs can't read the full transcript. This is direct evidence that `/handoff continue` with `/aar` preprocessor integration would produce materially better handoffs — it's the top v0.2 priority.

### Cross-session chain traversal via /aar

Run `/aar`'s `run_full_preprocessor` against the `originating_session_id` named in a prior handoff. Recovers the full conversation chain including pre-compaction context.

**Deferred because:**
1. The `/aar` preprocessor is import-only (no CLI `__main__` block). Calling it requires a small Python wrapper.
2. The preprocessor's interpreted outputs (`signals.json`) are AAR-shaped (user-correction detection, recommendation-reversal detection). Only its raw outputs (`canonical-events.jsonl`, `active-timeline.json`) are reusable for handoff purposes. The integration needs to consume only the raw layer.
3. Within-session compaction recovery (reading `segment_*.md` directly) covers the most common case. Cross-session is less frequent.

**Verified `/aar` API (as of 2026-07-20, for v0.2 implementation):**

```python
# P:\.grok\skills\aar\__lib\session_resolver.py
def resolve_session_dir(
    *, session_id: str | None, workspace_encoded: str | None,
    sessions_root: str | Path = GROK_SESSIONS_ROOT,
    env: dict[str, str] | None = None,
) -> SessionBinding  # .status: IdentityStatus (VERIFIED | UNVERIFIED | SUPPLIED_INVALID)

def verify_session_identity(
    session_id: str, session_dir: str | Path, *, authority: str = "argument",
) -> SessionBinding

# P:\.grok\skills\aar\__lib\transcript_parser.py
def parse_transcript(path: str | Path) -> Transcript
def classify_source(transcript_path: str | Path) -> SourceStatus
def extract_session_id_from_path(path_str: str) -> str | None

# P:\.grok\skills\aar\__lib\full_preprocessor.py  (import-only, NO CLI)
def run_full_preprocessor(
    *, session_id: str, workspace_encoded: str, run_dir: str | Path,
    sessions_root: str | Path = "C:/Users/brsth/.grok/sessions",
    env: dict[str, str] | None = None, cutoff: str | None = None,
    max_signals: int = 30, max_total_events: int = 120,
) -> PreprocessResult  # .ok, .status_label, .packet_dir, .source_status, ...
```

**v0.2 plan:** add `__lib/session_tools.py` as a thin anti-corruption layer wrapping these imports. If `/aar`'s API changes, only that file updates.

### Multi-stream detection — DEPRIORITIZED

Currently v0.1 defaults to the stream the user asks about and names other obvious streams. v0.2 could automate stream segmentation across a session's full chain.

**Deprioritized because (H-3 evidence):** all 4 real sessions were single-stream (stream_count=1/4). The manual rule ("write what the user asked for; note others") is sufficient until evidence shows otherwise. Building an automated detector now would be solving a problem that hasn't appeared in practice.

**v0.2 plan:** only build a detector if v0.1 usage shows the user frequently wants multiple handoffs from one session and the manual process is painful. The threshold: if >25% of sessions produce >1 handoff via manual request, automate.

### Handoff types beyond Investigation — DEPRIORITIZED

Five types were designed: Investigation, Implementation, Diagnostic, Architectural, Retrospective. Each selects optional blocks.

**Deprioritized because (H-3 evidence):** all 4 real sessions fit Investigation naturally (type=investigation/4). Investigation covers ~70%+ of real handoffs observed in the workspace. Forcing type selection adds ceremony for the common case. v0.1 uses Investigation shape with per-section optionality ("include this if the work warrants").

**v0.2 plan:** add types when v0.1 usage shows the Investigation shape is genuinely inadequate for a recurring work category. The threshold: if >25% of handoffs would benefit from a different mandatory-block set, add that type. The type system is documented below for reference but not enforced in v0.1.

#### Type catalog (reference for v0.2)

| Type | When | Mandatory optional blocks |
|---|---|---|
| Investigation | Findings reported, no changes | Failure-mode catalog (if failures found) |
| Implementation | Code changed, work remains | Evidence packet, bounded delegation defaults |
| Diagnostic | Issue diagnosed | Failure-mode catalog, layered root-cause |
| Architectural | Decision made | Options table, ADR template |
| Retrospective | Lessons are the output | Value accounting, lesson calibration |

### PLAN.md / DECISIONS.md / per-terminal status.jsonl

The three-artifact split (handoff = context, plan = ordered items, status = per-item state) is the right model for multi-stream programs.

**Deferred because:** most handoffs are single-stream and don't need the split. The handoff file alone is enough. Adding PLAN.md and status.jsonl prematurely adds ceremony without value.

**v0.2 plan:** add when a real multi-stream program needs parallel terminal updates to a shared plan. The per-terminal status.jsonl pattern is documented in the original multi-terminal-contract design (preserved below for reference).

## Original design material (preserved for v0.2 reference)

The detailed designs for the above are preserved in git history. The key sections that v0.2 implementers should review:

### Multi-terminal contract (6 rules, still load-bearing for v0.1)

1. Terminal-scoped writes (Pattern A shared-read/single-writer; Pattern B per-terminal/multi-writer)
2. Authority bound at claim time as `(session_id, terminal_id, run_id, allowed_path_list)` lease
3. No `LATEST-*` pointers, no newest-timestamp discovery
4. Verbatim last-user-message preservation (ADR-006)
5. Single-writer per handoff; append-only for status
6. Reads are deep copies; writes pass through owner check

v0.1 enforces rules 1, 3, 4, 5 directly. Rules 2 and 6 (formal lease + StateView pattern) are v0.2 when status.jsonl and multi-writer plans appear.

### Three-artifact architecture

```
P:\docs\handoffs\<topic>-<YYYYMMDD>\HANDOFF.md       # context, single-writer
P:\docs\handoffs\<topic>-<YYYYMMDD>\PLAN.md           # ordered items, single-writer
P:\docs\handoffs\<topic>-<YYYYMMDD>\DECISIONS.md      # durable choices, promoted to ADR on close
P:\.artifacts\<termSafe>\plan-<planId>\status.jsonl   # per-item state, multi-writer across terminals
```

Each artifact has one writer pattern, one update cadence, one purpose. v0.1 ships HANDOFF.md only; others are added when the work warrants.

### Per-terminal status event schema (v0.2)

```jsonl
{"ts":"2026-07-20T12:34:56Z","terminal_id":"A","session_id":"<id>","item_id":"X","event":"started","note":"..."}
{"ts":"2026-07-20T13:01:02Z","terminal_id":"A","session_id":"<id>","item_id":"X","event":"blocked","note":"..."}
{"ts":"2026-07-20T14:00:00Z","terminal_id":"B","session_id":"<id>","item_id":"Y","event":"started","note":"..."}
```

Events are append-only. Current state derived by replaying the log for each item. Multiple terminals each have their own file. Reader aggregates all terminals' files for fleet-wide status.

### Cross-terminal continuation semantics

When work crosses terminals, the chain header surfaces it explicitly:

```yaml
originating_terminal_id: terminal-A
current_terminal_id: terminal-B
```

A reader sees the terminal change. Rule: this terminal never writes to `.artifacts/terminal-A/`. Only to `.artifacts/terminal-B/`.

v0.1 does not enforce this because it does not write per-terminal status. v0.2 will.

## What would justify pulling a v0.2 feature forward

- **Cross-session continuation is requested frequently** → pull in `/aar` integration + `/handoff continue` — **already top priority based on H-3 evidence**
- **Real multi-stream programs appear** → pull in PLAN.md + status.jsonl
- **Handoffs are being used for architectural decisions often** → pull in ADR promotion
- **Type confusion causes bad handoffs** → pull in type-specific templates

Each of these is evidence-driven. Do not pre-build.

## `/aar` SHARED_API.md marker — DEFERRED (D2, 2026-07-20)

**Decision:** defer until `/handoff` v0.2 imports from `/aar`.

**Rationale:** rule of three. `/aar/__lib/` currently has one consumer (`/aar` itself). `/handoff` v0.1 does not import `/aar` at all — it reads `compaction/segment_*.md` directly. So the "shared API" is shared with zero external consumers right now. Documenting an API with no external caller is premature.

**When to land:** when `/handoff` v0.2 implements `/handoff continue` and actually imports from `/aar/__lib/session_resolver.py`, `transcript_parser.py`, and `full_preprocessor.py`. At that point the marker has a purpose: documenting the contract the external consumer depends on.

**Falsifier for deferral:** if `/aar`'s internal refactoring breaks a future `/handoff` v0.2 integration because the API surface was never documented. Low risk — `/aar` is mature (30+ tests, stable for weeks).

## Test coverage roadmap

v0.1 ships behavior + mutation tests for:
- Chain header parsing and validation
- Compaction segment enumeration
- Field-presence validation (16 mandatory fields)
- Multi-stream-default rule (user-asked stream wins; others noted, not written)
- Verbatim message preservation

v0.2 adds:
- Cross-session chain traversal (when `/aar` integration lands)
- Multi-writer status replay (when status.jsonl lands)
- Revision append (when `/handoff update` lands)
- Type-specific optional blocks (when types land)

See `tests/README.md` for the current test inventory and how to extend it.
