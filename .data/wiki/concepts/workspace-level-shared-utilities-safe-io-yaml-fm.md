---
title: "Workspace-level shared utilities for atomic write, file locking, and frontmatter manipulation"
created: 2026-08-03
source: session-019fba58
tags: [shared-utility, atomic-write, file-locking, frontmatter, dry, multi-agent, concurrency, safe-io, yaml-fm]
summary: >
  The workspace had 43+ independent reimplementations of tmp+os.replace for
  atomic writes, 8+ reimplementations of msvcrt/fcntl file locking, and
  bespoke frontmatter parsers in every skill that touched YAML. Each
  reimplementation drifted: some lacked locking, some leaked file descriptors,
  some corrupted frontmatter. The fix: two shared modules at ~/.grok/__lib/
  (safe_io.py + yaml_fm.py) that centralize these primitives. Every caller
  migrates to use them. This eliminates the recurring bug class at its root.
agent: grok
host: grok
cognitive_load: 3
verification: observed
relations:
  - target: wiki/concepts/coupling-inventory-as-mandatory-design-section.md
    type: related
  - target: wiki/concepts/consistency-drift-as-waste-source-in-iterative-refinement.md
    type: related
  - target: wiki/concepts/invariants-beat-environment-comfort.md
    type: related
  - target: wiki/concepts/design-skill-preflight-gap.md
    type: related
  - target: wiki/concepts/raising-coding-best-practices-in-ai-agents.md
    type: related
---

# Workspace-level shared utilities for atomic write, file locking, and frontmatter

## Decision context

**Why this was needed:** a specialist correctness review of 6 changed files found 30 findings. Clustering by root cause revealed that 18 of 30 were symptoms of two root causes: (R1) duplicated low-level primitives (atomic write, file locking) reimplemented in 43+ locations, each drifting differently; (R2) bespoke frontmatter/regex manipulation with no typed API. The `/design` run on these 30 findings confirmed that fixing each finding individually would preserve the duplication class and guarantee recurrence.

The operator's directive: "fix all 30 findings as a coordinated system, not individual patches." The coordinated fix required shared utilities so that every caller uses the same tested primitive instead of reinventing it. This is the [[coupling-inventory-as-mandatory-design-section]] pattern applied at the workspace level — the DRY threshold (≥3 violations) was met 14x over.

## What was built

### `~/.grok/__lib/safe_io.py`

Centralizes three primitives:

1. **`atomic_write_text(path, content)`** — writes to a PID + random-suffixed tmp file, then `os.replace`. Retries on `PermissionError` (antivirus/Defender file holds) with exponential backoff (7 attempts, ~7.8s worst case). Cleans up tmp file in `finally` block.

2. **`atomic_write_json(path, data)`** — wraps `atomic_write_text` with consistent JSON formatting (`indent=2`, `ensure_ascii=False`).

3. **`file_lock(lock_path, timeout_s=10.0, blocking=False)`** — cross-process advisory lock using `msvcrt.locking` on Windows, `fcntl.flock` on POSIX. Two-mode: `blocking=True` uses OS-level scheduling (LK_LOCK); `blocking=False` uses non-blocking + retry with backoff. NOT re-entrant (documented).

4. **`read_json_or(path, default=_MISSING)`** — safe JSON read. Uses a sentinel object so `default=None` is distinguishable from "no default provided." Returns default on missing file or parse error; raises `ValueError` only when no default is given.

### `~/.grok/__lib/yaml_fm.py`

Centralizes frontmatter manipulation:

1. **`parse_frontmatter(text)`** — returns `(fm_text, fields_dict, body)`. Skips comment lines (`#`-prefixed). Strips inline comments only when not inside quotes.

2. **`get_field(text, field)`** — returns value or empty string. Does NOT return values from commented-out fields.

3. **`set_field(text, field, value)`** — replaces existing field or inserts before closing `---`. Preserves commented lines verbatim. Creates frontmatter block if absent.

4. **`remove_field(text, field)`** — removes both active and commented occurrences (strips all leading `#` markers for matching).

5. **`append_changelog_row(text, session, action)`** — appends to existing changelog table or creates one. Uses second-precision timestamps.

6. **`utc_now_iso(precision)`** — configurable precision: minute, second, microsecond.

## Key decisions

### Decision 1: Workspace-level `~/.grok/__lib/` instead of skill-scoped

**Chosen:** `~/.grok/__lib/` — a new workspace-level shared library directory.

**Steelman (rejected alternative):** skill-scoped `__lib/` (e.g., `skills/handoff/__lib/`). This avoids cross-skill dependencies and keeps each skill self-contained.

**Why workspace-level wins:** hooks (at `~/.grok/hooks/`) are not inside any skill. They need atomic writes and locks too. A skill-scoped utility would require either (a) hooks importing from a skill (inverted dependency), or (b) hooks reimplementing the primitive (the exact pattern we're eliminating). Workspace-level is the only location visible to both hooks and skills without `sys.path` gymnastics.

**Falsifier:** if the `__lib` directory creates import problems on a fresh install or after a Python upgrade, the workspace-level location was wrong. The bootstrap pattern (`sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "__lib"))`) must work from any hook or skill location.

### Decision 2: Two-mode file_lock (blocking parameter)

**Chosen:** `blocking: bool = False` parameter on `file_lock`.

**Steelman (rejected alternative):** single mode (always non-blocking + retry). Simpler API, one code path.

**Why two-mode wins:** `fleet_quota` uses `LK_LOCK` (blocking) for read-mostly cache operations where long waits are acceptable. `claim_handoff` uses `LK_NBLCK` (non-blocking) where promptness matters. Forcing both into one mode either burns CPU (non-blocking polling for fleet_quota) or blocks indefinitely (blocking for claim_handoff). The `blocking` parameter lets each caller choose the right behavior.

**Falsifier:** if callers consistently pass the wrong mode and deadlock or starve, the two-mode API added complexity without value. Monitor for `TimeoutError` frequency from fleet_quota callers.

### Decision 3: DRY personas reference SKILL.md as source of truth

**Chosen:** persona TOML files reference `/design SKILL.md` for mandatory sections and review checklist instead of duplicating the lists.

**Why:** the persona files had drifted — they referenced "Risk Table" (renamed to "Failure Mode & Edge Case Analysis") and "14 mandatory sections" (now 16+). Each time the skill changed, both persona files needed manual updates that were forgotten. Referencing SKILL.md eliminates the drift.

## Migration map

20 caller files were identified for migration. The highest-priority (new/changed files) were migrated this session:

| File | Primitive used | Old pattern | New pattern |
|------|---------------|-------------|-------------|
| `PreToolUse_skill_staleness.py` | atomic_write_json + file_lock | raw tmp.replace + no lock | safe_io primitives |
| `claim_handoff.py` | atomic_write_text + file_lock + yaml_fm | raw write_text + bespoke frontmatter | safe_io + yaml_fm |
| `PreToolUse_spawn_model_gate.py` | msvcrt.locking (inline) | raw msvcrt | inline msvcrt for escalation reset (partial migration) |

Remaining 17 files use the old pattern but were not migrated this session. They should be swept in a follow-up — each migration is mechanical (replace `tmp.replace` with `atomic_write_*`, replace `_cache_file_lock` with `file_lock`).

## What this means for our workspace

1. **New hooks and skills should import from `~/.grok/__lib/`** — never reimplement atomic write or file locking. The bootstrap pattern is: `sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "__lib"))` then `from safe_io import ...`.

2. **The grep enforcement** (`rg "os\.replace|tmp\.replace" ~/.grok/hooks ~/.grok/skills`) catches new reimplementations. Run it after any new file is added that writes shared state. This is the [[consistency-drift-as-waste-source-in-iterative-refinement]] pattern applied as a workspace invariant.

3. **The `file_lock` two-mode API** is the canonical locking pattern. Use `blocking=True` for read-mostly operations where waiting is fine. Use `blocking=False` for operations where promptness matters. This follows the [[invariants-beat-environment-comfort]] principle — the invariant (serialized access) is enforced structurally, not via behavioral rules.

4. **`yaml_fm` replaces bespoke frontmatter regex** in every skill that touches handoff YAML. The old `_set_field`/`_get_field`/`_parse_frontmatter` pattern was buggy (corrupted frontmatter on new fields, returned commented-out values). This is a [[raising-coding-best-practices-in-ai-agents]] response — mechanical thresholds for coupling, not judgment calls.

## Falsifier

This approach is wrong if, within 6 months:
- The `__lib` import path breaks on a Python upgrade or workspace relocation
- New files continue to reimplement `tmp + os.replace` despite the shared utility existing (grep check fails)
- The two-mode `file_lock` causes deadlocks or CPU contention that the single-mode approach wouldn't have
- `yaml_fm`'s regex-based frontmatter parsing breaks on valid YAML that the bespoke parsers handled (e.g., multi-line values, nested structures)

## Receipts

- `~/.grok/__lib/safe_io.py` — full implementation, lines 1-195. `atomic_write_text` (lines 40-64), `atomic_write_json` (lines 67-72), `read_json_or` (lines 79-97), `file_lock` (lines 100-195).
- `~/.grok/__lib/yaml_fm.py` — full implementation, lines 1-175. `parse_frontmatter` (lines 48-85), `get_field` (lines 88-93), `set_field` (lines 96-128), `remove_field` (lines 131-155), `append_changelog_row` (lines 158-175).
- `~/.grok/hooks/PreToolUse_skill_staleness.py` — migrated caller, uses `safe_io.atomic_write_json` + `safe_io.file_lock`. Bootstrap at lines 17-21.
- `~/.grok/skills/handoff/__lib/claim_handoff.py` — migrated caller, uses `safe_io.atomic_write_text` + `safe_io.file_lock` + `yaml_fm.*`. Bootstrap at lines 22-26.
- grep `os.replace|tmp.replace` across `~/.grok/` — 51 matches confirmed across 18 files (pre-migration baseline).
- `/design` run 100e606b — 121KB design doc with 13 implementation units, critical friend verdict REVISE (7 items, all addressed).
- `/review` run session-019fba58-20260802-232702 — 21 findings (0 critical, 4 major, 11 minor, 6 nit). All 4 major + 5 minor fixed.

## Sources

- Session 019fba58 specialist review (30 findings across 6 files)
- `/design` run 100e606b (121KB design doc with 13 implementation units)
- `/review` session 019fba58-20260802-232702 (21 findings, 9 fixed)
- grep across `~/.grok/` for `os.replace|tmp.replace` (51 matches across 18 files)

## Auto-related

- [[claude-code-external-tool-integration-via-mcp]]
- [[claude-code-cli-agent-configuration-and-workflow-patterns]]
- [[claude-code-skills-and-mcp-integration]]
- [[opentelemetry-structured-logging-patterns]]
- [[context-management-in-claude-code]]

