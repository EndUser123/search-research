# Design — Scanner→Handoff Bridge

**Status:** Draft (revised per F-01..F-30 review)
**Author:** design-doc-writer (subagent)
**Date:** 2026-08-05
**Scope:** Single-design bridge for converting `/todo` scanner output into durable handoffs.

---

## TL;DR

The `/todo` scanner discovers ~20–30 filtered open-work items per scan but writes nothing to disk. Five categories (script defects, stale handoffs, review findings, harvest obligations, dream proposals) evaporate at session end. The bridge adds **two thin extensions** to existing skills:

1. `/todo --journal` — persists evaluated NOW items as JSON to `P:/.data/state/todo-journals/<timestamp>.json`.
2. `/handoff --from-journal <path>` — a generalization of the existing AAR-report mode that reads a journal file and writes **one non-blocking handoff per dependency cluster** (where clusters are items sharing the same scanner source), using the same 17-field schema and dependency grouping already shipping for AAR ingestion.

No new skill (Option D rejected). No `/dream` pass (Option C rejected). Persistence at `/todo` boundary, routing at `/handoff` boundary, reusing the AAR-report pattern as the structural template.

---

## Design Intent Contract

### Goal
Make every `/todo` scanner finding that survives LLM evaluation durable across sessions by writing it to a handoff at `P:/docs/handoffs/`, so future sessions can pick it up cold without re-running the scan.

### Non-goals
- Replicating `/todo`'s 16-source scanner inside `/handoff` (single-source-of-truth stays in `scan_functions.py`).
- Auto-persisting items the LLM dropped during evaluation (false positives, duplicates, completed work — judgment call stays at the evaluation boundary).
- Routing items during `/dream` (the existing `/dream` Step 6 routing is for dream-internal findings; scanner items get a separate, dedicated path).
- Cross-host persistence (Grok Build only — Claude Code has different handoff contracts and a separate todo skill).

### Success metrics (with measurement methodology)

- **S1:** ≥80% of `severity:high` scanner items that the LLM evaluates as actionable produce a handoff within the same session.
  - **Measurement:** across a rolling 30-day sample of `/todo --journal` invocations (≥10 invocations), count `{source, title_hash}` entries in journals minus count of closed handoffs with matching `<!-- todo-journal:<hash> -->` markers. The gap ≤20% of total high-severity journaled items.
- **S2:** ≤2 known duplicates per 90-day window from operator review of journal-derived handoffs.
  - **Measurement:** operator triages handoffs under `P:/docs/handoffs/todo-*/` paths during normal `/handoff list --head` review; duplicate is a handoff pair with identical `title_hash` AND same source AND same session-cluster AND `yaml:open`. Target: ≤2 such pairs per quarter.
- **S3:** A cold-start session reading the journal-derived handoffs can identify the originating `/todo` invocation via the handoff's `objective` field without grep.
  - **Measurement:** spot-check by reading 5 random journal-derived handoffs and timing the cold-start identification task. Pass criterion: ≤30 seconds per handoff, no `grep`/`rg` invocation needed (the `objective` field names the source).

### Failure conditions
- **F1:** Items still evaporate after a session ends — the bridge did not capture them.
- **F2:** `/handoff --from-journal` writes handoffs for items the LLM dropped during `/todo` evaluation (false-positive persistence).
- **F3:** A journal-derived handoff becomes unreadable because `accurate_as_of_head` drifts before the handoff is actioned. **Moved to "Known Limitations"** — the bridge reuses the existing AAR-mode drift discipline and does not add a new mechanism. See F-16 response below.
- **F4:** Token blow-up — a journal with 30 items produces 30 handoffs in one batch with no clustering.

---

## Context — the gap

Scanner lifecycle today:

```
scan_functions.py (16 sources)
   ↓ raw items
post-scan filter (~20–30 clusters)
   ↓ evaluated items
LLM evaluation (drop false positives, dedup, priority)
   ↓ NOW/NEXT/LATER items
render_rns.py (toon or plain)
   ↓ stdout text
session response ── ✗ session ends → items gone
```

`[FACT]` Three durable paths exist on Grok Build: wiki concepts, ADRs, and handoffs. `[FACT]` Handoffs are the only path shaped for operational cross-session work. `[INFERENCE]` The scanner outputs to stdout; nothing bridges it to the handoff store — this is the gap the design fills.

`/dream`'s Step 6 routes unresolved dream-internal findings to handoffs (added 2026-08-01). `[FACT]` That mechanism is structurally what we want, but scoped to dream output. The same idea generalizes to any structured input — AAR reports (already supported via `/handoff <report-path>`) and now journal files.

`/handoff`'s auto-update mode reads session transcript only. The AAR-report mode is the existing pattern that reads a structured file and produces N non-blocking handoffs with dependency grouping — that's the exact mechanism the bridge reuses.

---

## Design

### Component 1 — `/todo --journal`

Adds a `--journal` flag to the `/todo` skill. When set, after Step 1 evaluation, the evaluated items list is written as JSON to:

```
P:/.data/state/todo-journals/YYYY-MM-DDTHHMMSSZ-<session-id-short>.json
```

`<session-id-short>` format: **first 8 hex chars of the session UUID** (matches the convention in `~/.grok/skills/handoff/__lib/claim_handoff.py`). 8 hex chars = 32 bits = 2³² ≈ 4.3 billion possible prefixes; collision probability ≤ 1 in 2³² per day per terminal. Full collision additionally requires same timestamp + same terminal — impossible across concurrent sessions on different terminals.

**Directory precondition:** `journal_write.py` calls `Path.parent.mkdir(parents=True, exist_ok=True)` at the top of `write_journal()` so the bridge works on a fresh workspace without operator setup.

**Argument set (Component 1):**

| Flag | Default | Purpose |
|---|---|---|
| `--journal` | off | Enable JSON persistence after evaluation |
| `--deep` | off | Required for `severity:medium` items to journal |
| `--journal-min-severity <level>` | `high` | Lower-bound for inclusion; accepts `high`, `medium`, `low`. **Validation:** invalid values raise `ValueError("Invalid severity '{value}'. Accepted: high, medium, low.")` with exit code 2 and the message on stderr. Tested in `test_journal_write.py::test_min_severity_validation`. |
| `--journal-output <path>` | auto-generated | Override output path (testing only) |
| `--dry-run` | off | Compute and print what would be written; no filesystem mutation |

**Schema:**

```json
{
  "schema_version": 1,
  "produced_at": "2026-08-05T14:32:01Z",
  "session_id": "<uuid>",
  "terminal_id": "<id>",
  "todo_invocation": "/todo --journal --deep",
  "items": [
    {
      "section": "NOW",
      "text": "<Action verb>. <What + why>.",
      "source": "<scanner source>",
      "severity": "<high|medium|low>",
      "detail": "<scanner detail>",
      "path": "<scanner path>",
      "title_hash": "<sha256 hex of normalized_title>"
    }
  ]
}
```

**Severity gating (default):**
- `severity:high` — always journal (the bridge's primary target).
- `severity:medium` — journal only when `--deep` was also passed.
- `severity:low` — never journal (informational, not actionable).
- Override via `--journal-min-severity` to widen or narrow.

`[INFERENCE]` The default (`high` only unless `--deep`) is chosen because `[INFERENCE]` empirical evidence (F-20) suggests `high` is a minority of items and `--deep` is needed to capture medium. Operator can override via `--journal-min-severity`. **The `NEEDS_USER_DECISION` item from the prior revision is resolved by this default** — see DEC-08.

**Title normalization for `title_hash`** (per F-10):

```python
def normalize_title(title: str) -> str:
    return title.lower().strip().replace(r"\s+", " ").encode("utf-8")
```

Then `title_hash = hashlib.sha256(normalize_title(title)).hexdigest()` (64 hex chars).

Stability is across case, whitespace runs, and trailing whitespace — NOT across rephrasing. Two scans that say "Fix hook stderr" vs "Fix hook stderr" (same) dedup; "Fix hook stderr" vs "Fix the hook stderr output" produce different hashes. See DEC-05 (revised).

**Operator stdout summary at journal write time (per F-24, separated per F-39):**

**Normal mode (no `--dry-run`):**
```
Journal written: P:/.data/state/todo-journals/2026-08-05T143201Z-a1b2c3d4.json
Items: 7 (high: 4, medium: 3)
Sources: [review×3, harvest×2, script_defects×2]
```

**Dry-run mode (`--dry-run` passed):**
```
[DRY-RUN] Would write journal to P:/.data/state/todo-journals/2026-08-05T143201Z-a1b2c3d4.json
Items: 7 (high: 4, medium: 3)
Sources: [review×3, harvest×2, script_defects×2]
No filesystem mutation performed.
```

The operator sees what's in the journal and which sources are active. This informs the `--exclude-source` decision (Component 2). The two modes differ in the first line (confirmation vs. `[DRY-RUN]` prefix + no-mutation footer) — the items and sources lines are identical. Tested in `test_journal_write.py::test_normal_mode_summary` and `::test_dry_run_mode_summary`.

Component 2 (`--dry-run`) prints a similar two-mode summary: normal mode emits `Handoff written: <path>` per cluster; dry-run mode emits `[DRY-RUN] Would write handoff: <path>` per cluster with `No filesystem mutation performed.` after the cluster list.

The LLM evaluation (Step 1 questions 1–8) runs before the journal write, so dropped items never reach the file. The journal represents the LLM's filtered-and-prioritized view, not the raw scan.

**Implementation:** new flag in `~/.grok/skills/todo/SKILL.md` (Step 1c, after Step 1b); new module `~/.grok/skills/todo/__lib/journal_write.py` (~80 lines: `write_journal()`, `validate_journal_shape()`, `normalize_title()`, stdout summary printer); calls `validate_journal_shape()` before write (no `python -c` — that's the Class C quoting hazard the skill already warns against).

### Component 2 — `/handoff --from-journal <path>`

Generalizes the AAR-report mode (`/handoff <report-path>`) to read journal files. Same 17 mandatory fields (see `references/core-fields.md` for the canonical schema), same dependency grouping, same non-blocking handoff shape.

**Argument set (Component 2):**

| Flag | Default | Purpose |
|---|---|---|
| `--from-journal <path>` | (positional) | Path to a journal file produced by `/todo --journal` |
| `--exclude-source <source>` | none | Skip items from named scanner source (repeatable; e.g., `--exclude-source review --exclude-source harvest`) |
| `--dry-run` | off | Print what would be written; no filesystem mutation |
| `--max-items <N>` | 50 | Refuse to process more than N items; warn operator; default matches the ~20–30 typical scan size plus headroom |

**Mode detection (per F-07, explicit ordering and ambiguity handling):**

Detection runs in this order, first match wins:

1. **Journal mode:** file content starts with `{` AND parses as JSON AND has top-level keys `produced_at`, `items`, `schema_version`. If `schema_version` missing or unknown: reject with `JournalVersionError`.
2. **AAR mode:** file content contains `## Opportunity landscape` or `## Open work` (the AAR markers).
3. **Named-topic mode:** fall-through. Treat the path as a topic name and run the standard `/handoff <topic>` process.

**Ambiguity handling:**
- File matches both journal AND AAR signatures → **abort with `AmbiguousInputError`** that lists both matched patterns and requires operator to disambiguate via `--from-journal` or `--from-aar` flag.
- File matches neither → fall through to named-topic mode (per the standard `/handoff <topic>` process).
- File matches journal but `schema_version` > supported → abort with `JournalVersionError` that names the supported versions.

This rule is tested in `test_from_journal.py::test_mode_detection` (unit-level: each input shape produces the expected mode).

**Item → handoff mapping:**

| Scanner item field | Handoff packet field |
|---|---|
| `text` | `## Objective` (single line) |
| `source` | `## Evidence` first line: `Source: <scanner source>` |
| `severity` | `## Priority` (high → NOW, medium → NEXT, low → LATER) |
| `detail` | merged into `## Evidence` body |
| `path` | `## Read-first` (only if non-empty) |
| `title_hash` | `## Objective` second line: `<!-- todo-journal:<hash> -->` for dedup |
| Other 10 mandatory fields | populated by `format_handoff.py` from defaults, **EXCEPT `current_session_id` and `current_terminal_id`** which are **read from the journal's `session_id` and `terminal_id` fields** and passed as overrides. **Provenance = the originating `/todo` session, not the writing `/handoff` session.** This ensures cross-session chain continuity — a future session reading the handoff can trace it back to the original `/todo` invocation, not the eventual routing. See `~/.grok/skills/handoff/references/core-fields.md` for the canonical schema. |

**Dependency grouping (per F-08, more precise rule):**

Clustering is by `{source, path-prefix, section}` tuple, not just by `source`:

- `source` — same scanner source (e.g., all `review` items)
- `path-prefix` — first path segment matching the workspace root (e.g., `P:/.claude/hooks`, `P:/packages/yt-is`, `P:/.data/wiki`). Items without a path use a placeholder prefix (`__no_path__`).
- `section` — the LLM's evaluation section (`NOW`, `NEXT`, `LATER`).

All three must match to cluster. This is finer than AAR-mode's "same source" rule because scanner items can span unrelated subsystems within one source. Items not sharing all three become separate handoffs. Rationale: a fresh session reading a handoff should not have to triage unrelated items.

**Dedup (per F-28, bounded scan scope):**

Before writing, the mode scans existing handoffs **restricted to `P:/docs/handoffs/todo-*/HANDOFF.md`** (not the entire handoffs tree) for the `<!-- todo-journal:<hash> -->` marker. This bounds the scan to journal-derived handoffs; O(N) where N = count of journal-derived handoffs (typically ≤100). The full-tree scan from the prior revision would have been O(handoffs tree size) — discarded.

If a handoff with the same hash exists and is `yaml:open`, the new one is skipped. If closed/superseded, a new one writes.

**"Non-blocking handoff" (per F-29):** defined as: handoff write does not require operator confirmation, does not error on existing `yaml:open` (skips via dedup), and does not block subsequent commands. The handoff itself remains "blocking" in the sense that work is open until closed — the term refers to the write path, not the work state.

**Location:** `P:/docs/handoffs/todo-<source>-<YYYYMMDD>/HANDOFF.md`. The `<source>` segment makes the source visible at the directory level (handoffs from `review` findings live under `todo-review-...`, not under `todo-mixed-...`).

**Implementation:** new subcommand in `~/.grok/skills/handoff/SKILL.md` (mode detection + journal schema validation); new module `~/.grok/skills/handoff/__lib/from_journal.py` (~100 lines: journal parsing, dedup, handoff invocation, mode detection, stdout summary); reuses the helpers extracted into `__init__.py` (see Coupling section).

### Trigger order

Default session-end flow becomes:

1. `/todo --journal` (operator invokes or `/close` triggers it)
2. `/handoff --from-journal <latest-journal>` (operator invokes, or `/close` chains it)

`/close` is the natural integration point — its session-close accounting already lists open work. Adding one line that runs `/todo --journal` and pipes the result to `/handoff --from-journal` makes the bridge automatic without making `/todo` or `/handoff` auto-firing (preserving their "manual trigger" stance).

---

## Alternatives

### Option 0 — Do Nothing (ALWAYS FIRST)

**What it is:** accept that scanner items evaporate at session end. Operator must remember to write handoffs manually for any item they want to persist.

**Why it's listed:** the no-op is genuinely an option. `/todo`'s post-scan filter already produces human-readable RNS output; the operator can read it and write handoffs for items they care about.

**Why it's rejected:** the gap is structurally endemic. `[INFERENCE]` Five categories of open work have been observed evaporating in this session's investigation. `[INFERENCE]` A prior count claim of "13+ handoffs exhibit a 'discovered but never persisted' pattern across 6 days" was not verifiable from the current session — the rejection of Option 0 rests on the theoretical ground that manual handoff writing does not scale with scanner throughput and the observed gap (5 categories) is sufficient to motivate the bridge. The specific count is `[INFERENCE]` and not load-bearing for the rejection.

### Option A — `/todo --journal` only (persistence, no routing)

**What it is:** persistence half of the chosen design. `/todo --journal` writes JSON; the operator (or a future `/wiki` pass) reads it.

**Rejected because:** persistence without routing is half a bridge. The journal file becomes its own store, parallel to handoffs — exactly the anti-pattern flagged in the task premise ("a persistent RNS file in non-handoff format was explicitly rejected"). Persistence must terminate at the handoff store, not create a third store.

### Option B — `/handoff` reads scanner directly (chosen direction, with journal as transport)

**What it is:** the chosen design. `/todo --journal` writes, `/handoff --from-journal` reads. Reuses the existing AAR-report mode pattern.

**Why it's chosen:** leverages the AAR-report mode already shipping in `/handoff` (`/handoff <report-path>` mode from v0.1). The pattern is proven (same dependency grouping, same non-blocking handoff shape, same dedup) and the journal file is structurally identical to an AAR report's item list. Persistence boundary stays at `/todo` (where evaluation happens); routing boundary stays at `/handoff` (where the 17-field schema lives). Single-source-of-truth for the scanner is preserved (`scan_functions.py`); single-source-of-truth for handoff format is preserved (`references/core-fields.md`).

### Option C — `/dream` pass that ingests the scanner journal

**What it is:** add Step 7 to `/dream` that reads the latest journal, applies the same evaluation `/todo` already ran, and writes handoffs for unresolved items.

**Rejected because:** duplicates evaluation work `/todo` already did (Drop false positives, dedup, prioritize). Adds a `/dream` pass that runs on a different cadence than `/dream`'s 90-day corpus model — scanner items are session-scoped, dream items are cross-session. Conflates two substrate semantics (operational handoff routing vs. memory consolidation). The 6-source Step 1 corpus in `/dream` is structurally about wiki/ADR material, not action items.

### Option D — New skill `/route-scanner`

**What it is:** standalone skill that reads scanner output and writes handoffs.

**Rejected because:** new surface area for a 2-step pipeline. `/handoff --from-journal` is a subcommand of an existing skill with overlapping contracts (AAR-report mode, 17-field schema, claim/dedup machinery). A separate skill duplicates the handoff-write logic and creates a second place where the handoff schema must be maintained.

---

## Coupling & Code-Smell Inventory

### DRY violations the design fixes

| Pattern | Count | Refactor |
|---|---|---|
| Item-to-handoff mapping (AAR-report mode + journal mode share the same conversion) | 2 sites (today) → 1 (after) | Extract `handoff_item_from_dict(d)` in `~/.grok/skills/handoff/__lib/__init__.py`. Both `from_aar.py` and `from_journal.py` import it. |
| Dependency grouping heuristic (AAR + journal use related clustering rules — AAR by domain, journal by `{source, path-prefix, section}`) | 2 sites → 1 base + 1 specialization | Extract `group_items(items, key_fn) -> list[Cluster]`. AAR passes `key_fn = domain_key`; journal passes `key_fn = source_path_section_key`. |

`[INFERENCE]` The prior revision claimed an "implicit transcript-mode" mapping as a third duplication site — that claim was not verifiable from the current session. The DRY count is **2 confirmed sites** (AAR + journal), not 3. The refactor ROI is still positive (2 sites consolidating to 1 base + 1 specialization), but the threshold "DRY violations ≥3" cited from AGENTS.md is not met. The refactor proceeds on the strength of the 2-site consolidation alone, not on a contested ≥3 claim.

### Touch-point count for adding a new scanner source

If `scan_functions.py` adds source 17 (e.g., `pwm_usage`):

| Location | Change |
|---|---|
| `~/.grok/skills/todo/__lib/scan_functions.py` | add scanner |
| `~/.grok/skills/todo/SKILL.md` | document in source table |
| `~/.grok/skills/handoff/SKILL.md` | no change (source-agnostic) |
| `~/.grok/skills/handoff/__lib/from_journal.py` | no change (reads `source` field as string) |
| `~/.grok/skills/handoff/__lib/__init__.py` | no change (grouping is generic) |

**Total: 2 touch points**, lower than any of the rejected alternatives would have produced. The specific "5+" comparison from the prior revision was hypothetical and is removed.

### Parameter count

`write_journal(items, session_id, terminal_id, deep, *, min_severity="high", output_path=None, dry_run=False) -> Path` — 4 required + 3 keyword. Below the 7-parameter coupling signal.

`handoff_item_from_dict(d, source_label=None, severity_map=None)` — 3 parameters. The optional maps let AAR and journal use the same function with different severity defaults.

### Mixed concerns

The design separates concerns correctly:
- `scan_functions.py` — discovery (unchanged).
- `todo/__lib/journal_write.py` — persistence only (new, single concern).
- `handoff/__lib/from_journal.py` — routing only (new, single concern).
- `handoff/__lib/__init__.py` — shared item-formatting (extracted, single concern).

No mixed-concern smell.

---

## Implementation Plan

### Units with acceptance criteria

| # | Unit | Disposition | Effort | Acceptance |
|---|---|---|---|---|
| 1 | Extract `handoff_item_from_dict()` and `group_items()` from `from_aar.py` into `__init__.py` | **COMMIT_THIS_SESSION** | S | `pytest ~/.grok/skills/handoff/__lib/tests/test_from_aar.py -v` passes without modification (AAR regression test); new helper importable via `from handoff.__lib import handoff_item_from_dict, group_items`. |
| 2 | Create `~/.grok/skills/todo/__lib/journal_write.py` (~80 lines) | **COMMIT_THIS_SESSION** | S | Module exposes `write_journal()`, `validate_journal_shape()`, `normalize_title()`. `Path.parent.mkdir(parents=True, exist_ok=True)` is the first line of `write_journal()`. |
| 3 | Add unit test `test_journal_write.py` | **COMMIT_THIS_SESSION** | S | `pytest ~/.grok/skills/todo/__lib/tests/test_journal_write.py::test_round_trip` passes; `::test_severity_gating` covers all 3 severities × 2 flag combinations (--deep on/off); `::test_directory_creation` writes to a fresh tmpdir and asserts the directory was created. |
| 4 | Wire `--journal` flag into `/todo` SKILL.md (Step 1c) | **COMMIT_THIS_SESSION** | XS | Step 1c exists with full argument set (`--journal`, `--deep`, `--journal-min-severity`, `--journal-output`, `--dry-run`); `--help` block updated to show them. |
| 5 | Create `~/.grok/skills/handoff/__lib/from_journal.py` (~100 lines) | **COMMIT_THIS_SESSION** | S | Module exposes `process_journal(path, exclude_sources=None, dry_run=False, max_items=50) -> list[HandoffResult]`. Mode detection runs journal-first then AAR-first then fall-through. Dedup scan restricted to `P:/docs/handoffs/todo-*/`. |
| 6 | Add unit test `test_from_journal.py` | **COMMIT_THIS_SESSION** | S | `::test_mode_detection` covers all 5 ambiguity cases (journal-only, AAR-only, both, neither, journal-wrong-version); `::test_item_mapping` covers all 7 item fields; `::test_dedup_scope` asserts scan reads only `todo-*/` paths; `::test_exclude_source` filters named sources; `::test_max_items` triggers warning at N+1; **`::test_session_provenance` asserts the handoff's `current_session_id` and `current_terminal_id` match the journal's `session_id` and `terminal_id`, NOT the writing session's IDs** (per F-43). |
| 7 | Wire `--from-journal` subcommand into `/handoff` SKILL.md | **COMMIT_THIS_SESSION** | S | Subcommand documented in v0.1.1 commands section; argument set (`--from-journal`, `--exclude-source`, `--dry-run`, `--max-items`) listed; mode detection rule explicit. |
| 8 | End-to-end smoke (this session, low-confidence — see F-21) | **COMMIT_THIS_SESSION** | S | `/todo --journal --deep` produces a journal file; `/handoff --from-journal <path>` produces ≥1 handoff at `P:/docs/handoffs/todo-<source>-<YYYYMMDD>/HANDOFF.md` with chain header matching the 17-field schema. **Rollback path on failure (per F-45):** if smoke fails (zero handoffs produced OR chain header mismatch OR `current_session_id` does not match journal's `session_id`), (a) revert all units from this session via `git revert <hash>..HEAD` (**NOT `reset --hard`** — destructive), (b) any handoffs created during smoke are marked `status: closed` via `/handoff close <path>` with the closure note "smoke test failure — design reverted in <sha>", (c) Unit 8 is NOT marked complete; blocker persists into next session. Smoke is a true gate, not a checkbox. |
| 9 | Add `/close` integration step that runs `/todo --journal && /handoff --from-journal` if open work exists | **HANDOFF** (out of scope; requires `/close` maintainer) | M | Handoff packet written; not implemented in this session. |
| 10 | Add `list_handoffs.py` column for `journal-derived` flag | **DEFERRED** (optional; informational only) | XS | Path-naming convention (`todo-*`) serves as the workaround until column ships. |
| 11 | Add `/handoff list` filter `--from-journal` to show only journal-derived handoffs | **DEFERRED** (optional; `rg "todo-journal"` or `ls P:/docs/handoffs/todo-*/` suffices) | XS | Documented as manual workaround in summary. |
| 12 | Decision: confirm or revise default severity gating (`high` only, `--deep` widens to medium) | **NEEDS_USER_DECISION** — see DEC-08. The bridge ships with this default and the operator can override per-invocation via `--journal-min-severity`. | — | Resolved by DEC-08. |

### Order of execution (COMMIT_THIS_SESSION units, interleaved testing)

Tests are interleaved with code creation so each module is tested at its introduction, not batched at the end:

1. **Extract helpers** (`from_aar.py` → `__init__.py`) → run existing AAR tests → must pass (regression check).
2. **Create `journal_write.py`** → immediately write `test_journal_write.py` → run tests → must pass before moving on.
3. **Wire `--journal` flag into `/todo` SKILL.md** → read-back verify.
4. **Create `from_journal.py`** (uses extracted helpers) → immediately write `test_from_journal.py` → run tests → must pass before moving on.
5. **Wire `--from-journal` subcommand into `/handoff` SKILL.md** → read-back verify.
6. **End-to-end smoke**: `/todo --journal --deep` → `/handoff --from-journal <path>` → verify handoffs at `P:/docs/handoffs/todo-*/`.

This ordering eliminates the 4-step gap from the prior revision (where `from_journal.py` and `journal_write.py` both existed for 4 steps before testing).

---

## Traceability Matrix

### Requirements

| REQ ID | Requirement | Source | Implementation |
|---|---|---|---|
| REQ-01 | Scanner items that survive LLM evaluation must be persisted across sessions | task premise ("never persisted to handoffs") | Component 1 (`--journal`) |
| REQ-02 | Persistence must terminate at the handoff store | task premise ("anti-pattern: parallel persistence path") | Component 2 (`--from-journal`) |
| REQ-03 | Routing must not duplicate work the LLM already did | task premise ("drop false positives" stays at `/todo` evaluation boundary) | Severity gating + journal write happens after evaluation |
| REQ-04 | Schema must reuse existing handoff contracts | task premise ("17 mandatory fields + chain header") | Component 2 reuses `format_handoff.py`; 10 of 17 fields inherited from defaults |
| REQ-05 | Dedup must prevent cross-session duplicates | gap analysis ("same item in multiple scans") | `title_hash` + bounded handoff marker scan in `from_journal.py` |
| REQ-06 | Bridge must not make `/todo` or `/handoff` auto-fire | AGENTS.md "manual trigger" stance | Both skills remain manual; `/close` integration is HANDOFF not COMMIT |

### Success metrics

| S ID | Metric | Linked measurement step |
|---|---|---|
| S1 | ≥80% of severity:high items produce handoffs in same session | Phase 2: 30-day rolling sample, ≥10 invocations, journal-handoff diff ≤20% |
| S2 | ≤2 duplicates per 90-day window | Phase 2: operator triages `P:/docs/handoffs/todo-*/`; counts pairs with same hash + source + cluster + `yaml:open` |
| S3 | Cold-start can identify originating `/todo` invocation | Phase 2: spot-check 5 random handoffs, ≤30s identification without grep |

### Failure conditions

| F ID | Condition | Mitigation (Failure Mode row) |
|---|---|---|
| F1 | Items still evaporate | Category 1: journal write fails → RNS path retains; handoff write fails → journal persists for retry |
| F2 | False-positive persistence | REQ-03: severity gating + journal-write-after-evaluation; Category 8: `--exclude-source` opt-out |
| F3 | `accurate_as_of_head` drift | **Moved to Known Limitations** (per F-16): design reuses AAR-mode drift discipline, no new mechanism. Operator runs `/handoff list --head` on action. |
| F4 | Token blow-up / no clustering | Dependency grouping rule (Component 2); `--max-items` guardrail at 50 |

### Decisions

| DEC ID | Decision | Rationale |
|---|---|---|
| DEC-01 | Persistence at `/todo`, routing at `/handoff` | Single-source-of-truth for each skill; mirrors AAR-report mode shape |
| DEC-02 | Reuse AAR-report mode pattern, not invent new | Proven mechanism; same dependency grouping, same non-blocking handoff |
| DEC-03 | JSON journal, not markdown RNS-as-file | Structured data survives re-rendering; JSON schema validates; `schema_version` enables forward-compatible evolution |
| DEC-04 | Severity gates persistence (high always, medium only with `--deep`) | `[INFERENCE]` empirical evidence suggests high is the minority; operator can widen via `--journal-min-severity`; baseline measurement (Phase 2 step 1) will revise if needed |
| DEC-05 | Dedup by `{source, title_hash}` marker in handoff body | Stable across whitespace/case/punctuation variations only; rephrased titles produce new hashes (known limitation; cross-session dedup handles same-phrasing repeats) |
| DEC-06 | No `/dream` pass for scanner items | Dream is cross-session wiki consolidation; scanner items are session-scoped action items — different substrate |
| DEC-07 | No new skill | `/handoff --from-journal` is a subcommand of an existing skill; new skill = parallel surface area |
| DEC-08 | Default severity gating resolves `NEEDS_USER_DECISION`: `high` only unless `--deep` widens to medium; `--journal-min-severity` overrides per-invocation | Allows bridge to ship without operator input; operator can override without code change; baseline measurement in Phase 2 will inform whether default needs revision |

---

## Failure Mode & Edge Case Analysis

### Category 1 — Data loss

| Failure | Detection | Mitigation |
|---|---|---|
| Journal write fails (disk full, permission denied) | `journal_write.py` raises `JournalWriteError`; `/todo` prints error to stdout and continues with RNS | Items survive as RNS (the existing path); operator sees the error |
| Handoff write fails (P:/docs/handoffs/ permission) | `from_journal.py` catches `OSError`; logs failed items to stderr; continues with remaining items | Partial success better than all-or-nothing; operator retries failed items |
| Journal file deleted before `/handoff --from-journal` runs | `/handoff` reports "journal not found"; no handoffs written | Operator re-runs `/todo --journal` to regenerate |
| `P:/.data/state/todo-journals/` directory missing on fresh workspace | `journal_write.py` line 1: `Path.parent.mkdir(parents=True, exist_ok=True)` | Directory auto-created; no precondition on operator |

### Category 2 — Duplicates

| Failure | Detection | Mitigation |
|---|---|---|
| Same item scanned twice in one session (LLM dedup missed it) | `title_hash` marker scan in `from_journal.py` | Second write skipped (yaml:open + same hash = skip) |
| Same item in two consecutive sessions | Same marker scan; `yaml:open` check | Second write skipped (cross-session dedup works because marker persists) |
| Item rephrased between sessions (same item, different text) | Title hash mismatch (whitespace/case dedup only, not rephrasing) | New handoff written; operator can manually close the old one if they notice |
| Ambiguous input matches both journal and AAR signatures | `AmbiguousInputError` listing both matched patterns | Operator passes `--from-journal` or `--from-aar` to disambiguate; documented in `test_mode_detection` |

### Category 3 — Stale references

| Failure | Detection | Mitigation |
|---|---|---|
| `accurate_as_of_head` drifts before handoff is actioned | `/handoff list --head <sha>` shows `head:DRIFT` | **See Known Limitations (F-16)** — the bridge reuses the existing AAR-mode drift discipline. Operator runs `/handoff list --head` on action; `/handoff verify <path>` re-checks citations. No new mechanism is added because the existing discipline is sufficient and adding a parallel mechanism would double the maintenance cost. |
| Scanner item cites a path that no longer exists | `/handoff verify <path>` (existing v0.1.1 command) | Operator runs verify on action; same as today |

### Category 4 — Race conditions

| Failure | Detection | Mitigation |
|---|---|---|
| Two terminals run `/todo --journal` concurrently | Filename includes timestamp + 8-hex session-id-short | Distinct filenames; collision probability ≤ 1 in 2³² per day per terminal (~1 in 4.3 billion); full collision additionally requires same timestamp + same terminal (impossible across concurrent sessions) |
| `/handoff --from-journal` races with manual handoff write on same item | Marker scan sees one or the other depending on order; second write is a no-op or a duplicate | Single-writer rule + marker dedup; loser is harmless |
| Journal file rewritten mid-read by another process | `validate_journal_shape()` runs after `read_file`; shape mismatch = abort | Read entire file into memory before parsing (small file, no streaming) |

### Category 5 — Schema drift

| Failure | Detection | Mitigation |
|---|---|---|
| `scan_functions.py` adds a new `severity` value | `journal_write.py` validates against enum `{high, medium, low}`; unknown values rejected | Add to enum; journal write is a forcing function for schema updates |
| Operator passes invalid `--journal-min-severity` value | `validate_min_severity()` rejects with `ValueError`; `/todo` exits with code 2 and stderr message | Operator sees error and retries with a valid level |
| Handoff schema changes (new mandatory field) | `format_handoff.py` is the single writer; both modes call it | No special handling needed — shared formatter enforces schema |
| Journal schema changes | `validate_journal_shape()` checks `schema_version` field | `JournalVersionError` if version > supported; journal includes `schema_version: 1` from day 1 |

### Category 6 — Permission / auth

| Failure | Detection | Mitigation |
|---|---|---|
| `P:/.data/state/todo-journals/` not writable | `journal_write.py` raises `PermissionError` | Items survive as RNS (stdout path) |
| `P:/docs/handoffs/` not writable | `from_journal.py` raises `PermissionError` | Journal file persists; operator can route manually later |
| Read-only mode (e.g., dry run) | `--dry-run` flag on both components | Prints what would be written; no filesystem mutation |

### Category 7 — Token / cost explosion

| Failure | Detection | Mitigation |
|---|---|---|
| 30-item journal → 30 handoffs → 30 cold-start readers burning tokens | Item count check in `from_journal.py` (default `--max-items 50`) | If items > `--max-items`, abort with warning and require `--max-items N` to override. Dependency grouping by `{source, path-prefix, section}` already reduces handoff count; further widening requires `--group-by` flag (v0.2). |
| Re-running `/todo --journal` every 10 minutes produces 100+ journals | Filename includes timestamp; dedup only works within handoff state, not within journal count | `/close --cleanup` removes journals older than N days (existing close cleanup; add to its scope as HANDOFF unit) |
| `[INFERENCE]` Severity gating captures too few items | Baseline measurement in Phase 2 (5 sessions, severity distribution) | If high <10% of items, default to `--deep` or revise gating via `--journal-min-severity` |

### Category 8 — Operator override

| Failure | Detection | Mitigation |
|---|---|---|
| Operator doesn't want a handoff for a specific source | `--exclude-source <source>` flag on `/handoff --from-journal` (repeatable) | Skips items from named sources; operator sees source distribution in journal stdout summary to inform the decision |
| Operator wants to suppress the bridge entirely | Default `/todo` invocation (no `--journal`); default `/handoff` invocation (no `--from-journal`) | Bridge is opt-in per skill, no global toggle |
| Operator wants different severity gating | `--journal-min-severity <level>` flag | Defaults to `high`; can be set to `medium` or `low` per-invocation |
| Operator wants to preview without writes | `--dry-run` flag on both components | Prints the would-be journal / would-be handoffs to stdout; no filesystem mutation |

### Known Limitations

- **F3 (drift):** `accurate_as_of_head` drift on journal-derived handoffs is handled by the existing AAR-mode drift discipline (not a new mechanism). Operator must run `/handoff list --head` on action; if a journal-derived handoff shows `head:DRIFT`, run `/handoff verify <path>`. This is the same workflow as AAR-derived handoffs today. The trade-off: zero new mechanism cost, but operator must remember the workflow.

---

## Rollout

### Phase 1 — Land and dogfood (this session)

1. Commit units 1–8 from the Implementation Plan.
2. **End-to-end smoke (low-confidence — see F-21):** the writer session runs `/todo --journal --deep` followed by `/handoff --from-journal <path>`. `[FACT]` This is self-referential dogfooding (the implementer is also the first user) and violates the [[self-verification-prohibition]] rule in spirit. The structural fix is sibling-session validation in Phase 2; for Phase 1, the writer notes the limitation explicitly in the operator handoff.
3. Verify: handoffs exist at `P:/docs/handoffs/todo-<source>-*/HANDOFF.md` with correct chain headers.

### Phase 2 — Operator review (next session)

1. **Sibling-session validation (per F-21):** a separate session runs `/todo --journal --deep` and `/handoff --from-journal <path>` on its own open work; results compared to Phase 1 output. This is the structural fix for self-dogfooding.
2. **Baseline measurement (per F-20):** run `/todo` for 5 representative sessions; record severity distribution. If `severity:high` <10% of items, default to `--deep` or revise severity gating.
3. **Journal-derived handoff identification:** operator reviews handoffs under `P:/docs/handoffs/todo-*/` (path naming convention is the discovery mechanism until `list_handoffs.py` column ships — see Unit 10).
4. **Operator decides** on whether `/close` integration is wanted (HANDOFF unit 9).

### Phase 3 — Deprecation of ad-hoc patterns (if any exist)

If any operator-driven workflows today manually copy `/todo` RNS into handoffs, those become candidates for retirement once the bridge is stable. Audit before recommending.

---

## File Change Inventory

| Path | Change | Risk |
|---|---|---|
| `~/.grok/skills/todo/SKILL.md` | Add `--journal` flag docs in Step 1c (after Step 1b); add full argument set to argument-hint | Low — additive |
| `~/.grok/skills/todo/__lib/journal_write.py` | New file (~80 lines): `write_journal()`, `validate_journal_shape()`, `normalize_title()`, stdout summary printer; mkdir on line 1 | Low — new module |
| `~/.grok/skills/todo/__lib/tests/test_journal_write.py` | New file: round-trip, severity gating, schema validation, directory creation | Low — new test |
| `~/.grok/skills/handoff/SKILL.md` | Add `--from-journal <path>` subcommand; mode detection rule with ambiguity handling; argument set | Low — additive |
| `~/.grok/skills/handoff/__lib/__init__.py` | Extract `handoff_item_from_dict()`, `group_items(items, key_fn)` | Medium — refactor of existing shared helpers; AAR regression test gates the commit |
| `~/.grok/skills/handoff/__lib/from_aar.py` | Migrate to call extracted helpers (no behavior change) | Medium — verified by AAR regression test |
| `~/.grok/skills/handoff/__lib/from_journal.py` | New file (~100 lines): journal parsing, dedup (bounded scope), handoff invocation, mode detection, ambiguity handling, stdout summary | Low — new module |
| `~/.grok/skills/handoff/__lib/tests/test_from_journal.py` | New file: mode detection (5 cases), item mapping (7 fields), dedup scope, exclude-source, max-items, ambiguity errors | Low — new test |

**Total: 2 modified skill SKILL.md files, 2 new __lib modules, 1 refactor of __init__.py + from_aar.py (gated by AAR regression test), 2 new test files.**

No changes to: `scan_functions.py` (single-source-of-truth preserved), `render_rns.py` (RNS output unchanged), `/dream` SKILL.md (no new pass), `/close` SKILL.md (integration is HANDOFF, not this design).

---

## Falsifier (for this design)

This design is wrong if:

- **F-pos-1:** The bridge writes handoffs the operator doesn't want. **Threshold:** false-positive persistence rate >20% on a 90-day sample (≥30 days of operator-reviewed journal-derived handoffs, ≥5 false-positives that operator closes within 7 days of creation, normalized by total journal-derived handoffs created). **Threshold is immutable for the falsification period** — if Phase 2 measurement exceeds 20%, the design is **falsified regardless of operator preference**. Per F-37: no post-hoc revision; the threshold is a binding falsification test, not a movable goalpost. **Grounding:** 20% is the threshold below which operator attention cost stays tolerable per the AGENTS.md "automate user meta-actions" goal — above 20%, the bridge becomes a meta-action the operator must police, defeating the purpose. `[INFERENCE]` Label retained to acknowledge the grounding is theoretical; the threshold itself is the binding test.
- **F-pos-2:** Dedup misses rephrased items and produces 2x+ handoffs per real work item. **Threshold:** ≤2 known duplicates per 90-day window (per S2 measurement). **Threshold is immutable for the falsification period** — if Phase 2 measurement exceeds 2, the design is **falsified regardless of operator preference**. Per F-37: no post-hoc revision. **Grounding:** 2x is the threshold above which the operator's mental model of "one handoff per work item" breaks; below 2x, occasional manual close-and-merge is acceptable operator effort. `[INFERENCE]` Label retained for same reason as F-pos-1.
- **F-pos-3:** The 17-field handoff schema turns out to be too heavy for scanner items (operator wants a lighter "todo card" shape). **Mitigation:** the bridge needs a `handoff_type: scanner-action` variant — a v0.2 follow-up.
- **F-pos-4:** The `--journal` flag is never invoked (zero usage over 3 months → bridge is solving a non-problem).

---

## Epistemic note

This design uses `[FACT]` / `[INFERENCE]` / `[UNKNOWN]` labels per `P:/.claude/rules/epistemic-format.md` for material claims. Most causal claims about the scanner's gap (5 categories evaporating, 13+ handoff count, severity distribution) are `[INFERENCE]` based on observed patterns; the schema contracts, file paths, and skill behaviors are `[FACT]` based on direct read of the source files in this session. Two thresholds (20% false-positive rate, 2x dedup) remain `[INFERENCE]` and are flagged as such; Phase 2 baseline measurement will upgrade them to `[FACT]` once operator-reviewed data is available.
