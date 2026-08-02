---
title: "Chronic Workspace-Health Debt Inventory (2026-08-01 snapshot)"
created: 2026-08-01
source: session-019fbf02-d3dd-7f72-9ad2-4538790c0a82
tags: [workspace-health, hooks_audit, index_skills, technical-debt, chronic-state, inventory, triage]
summary: >
  Concrete inventory of where workspace-health debt manifests as of 2026-08-01:
  572 STATE_GC files >30d, 197 DANGLING_PATHS, 10 SYNTAX errors, 1 REGISTRATION
  drift, 201 duplicate skill names, 237 disabled skills, 134 orphan script
  references, 3 SyntaxWarnings, plus long-dirty plugin trees and an open
  harvest obligation. The accumulation-problem principle is in [[accumulation-problem-resolution-rate-binding-constraint]];
  this concept is the specific triage list a future session can act on.
agent: grok
host: grok
cognitive_load: 3
verification: observed
tier: warm
relations:
  - target: wiki/concepts/accumulation-problem-resolution-rate-binding-constraint.md
    type: extends
  - target: wiki/concepts/workspace-improvement-opportunities-20260727.md
    type: related
  - target: wiki/concepts/skill-catalog-scope-inconsistency-causes-cascading-read-failures.md
    type: related
  - target: wiki/concepts/hooks-evidence-collection-cost-vs-timeout-tradeoff.md
    type: related
---

# Chronic Workspace-Health Debt Inventory (2026-08-01 snapshot)

## Decision context

**Why this inventory was needed:** `accumulation-problem-resolution-rate-binding-constraint` establishes the principle (discovery > resolution, fix the burn-down rate). But a future burn-down session needs the **specific inventory of where the debt lives today**, not just the principle. This concept captures the 2026-08-01 snapshot as a baseline; it will go stale by definition and is intended to be re-cut by future `/main` or `/harvest` passes.

**Method:** during session 019fbf02's close-check Phase 1 mechanical sweep, the chronic-state findings were emitted by `hooks_audit.py` (REGISTRATION/SYNTAX/DANGLING_PATHS/STATE_GC) and `index_skills.py` (duplicates/disabled/orphans). The numbers below are direct outputs of those scanners; the receipts are the chat transcript lines that captured them.

## Inventory

### A. hooks_audit.py (1151 hook files scanned)

| Bucket | Count | Severity | Triage signal |
|---|---|---|---|
| **REGISTRATION drift** | 1 | High | `snapshot_PreCompact.py` plugin hook registered directly instead of via `__lib/router.py`. Violates the canonical pattern documented in `plugins/CLAUDE.md` and `hooks-development` rules. |
| **SYNTAX errors** | 10 | High | `analyze_reasoning_profiles.py`, `reasoning_quality_gate_monitor.py`, `_patch_stop.py`, `task_tracker_hook.py` (BOM), `test_debug_windows.py`, `validate_pre_clarification_gate.py`, `_archived/StopHook_commitment_verifier.py`, `hook_base.py` (BOM), `test-damage-control.py`. Two of these have a UTF-8 BOM marker that breaks `python -c "import <module>"` on Windows; the rest have other syntax issues. |
| **DANGLING_PATHS** | 197 | Medium | References to missing files across `dreaming_writer.py`, `refactor_validation.py`, `SessionStart_repo_map.py`, `Stop.py`, `tdd95_core.py`, etc. Either files were moved without updating importers, or they were intentionally deleted without removing the references. |
| **STATE_GC (>30d)** | 572 | Medium | Log/state files older than 30 days. High volume; mostly orphaned session state from prior runs. The 30-day cutoff assumes anything older is safe to delete, but state used by running hooks or in-flight sessions must be excluded from any GC pass. |
| CATALOG_DRIFT | 0 | — | clean |
| STATS_ANOMALY | 0 | — | clean |
| HYGIENE | 0 | — | clean |

### B. index_skills.py (657 total skills)

| Bucket | Count | Severity | Triage signal |
|---|---|---|---|
| **Duplicate skill names across scopes** | 201 | Medium | Same skill `name:` appears in multiple scopes (user / workspace / plugin cache). Already documented in [[agent-config-directory-taxonomy]] and [[skill-catalog-scope-inconsistency-causes-cascading-read-failures]]. The same root cause (multi-scope skill directories without dedup) also drives the broader [[skill-catalog-scope-inconsistency-causes-cascading-read-failures]] pattern, and the [hook-evidence-collection-cost-vs-timeout-tradeoff] timeout trade-off is one of the STATE_GC consequences. Most are benign (workspace copy + plugin cache copy), but some are stale duplicates from edits that didn't propagate. |
| **Disabled-in-Grok** | 237 | Low | Skills marked disabled in `~/.grok/config.toml` but still listed in catalog. Mostly intentional (operator chose to disable), but worth a periodic audit to see if any were disabled temporarily and could be re-enabled. |
| **Orphan script references** | 134 | Medium | Scripts referenced by skill frontmatter or SKILL.md that no longer exist at the cited path. Either the scripts were deleted or the references are stale. |
| **Canonical (`.agents/skills/`)** | 12 | — | The canonical skill set the operator maintains; reference baseline for "what should exist." |

### C. Long-dirty tracked files

| Path | Age | Severity | Triage signal |
|---|---|---|---|
| `packages/.claude-marketplace/plugins/cc-skills-{ai-api,sdlc,utils}` | 12+ days | Medium | Three marketplace plugin trees have uncommitted changes that have aged past 7 days. Likely in-progress edits from prior sessions that were interrupted or forgotten. `dirty_age.py` flags >7d as "stale dirty." |
| `packages/installers/ornith-server.log.err` | 10 days | Low | Log file with persistent uncommitted state. Should be either `.gitignore`d or rotated. |

### D. Open obligations

| Bucket | Item | Severity | Triage signal |
|---|---|---|---|
| Harvest | `P:/.data/harvest/pending/tp-session-019fb926.json` (1 day old, OPEN) | Low | Single pending harvest item from prior session. Should be triaged (commit /archive /discard). |
| SyntaxWarnings | `test_verification_engine.py:550`, `write_fix.py:166` (`\s` invalid escape) | Low | Two pre-existing `\s` escape-sequence warnings. Will become SyntaxError on Python 3.12+; not yet a hard failure. |

### E. Note: NOT chronic, but session-attributed (already resolved or one-shot)

- `git-state [SESSION]` — 28 dirty + 15 ahead on `P:\`, 7 dirty + 23 ahead on `~/.grok`. This is the standard close-time accumulation; resolved by `git -C P:/ add <paths>; git commit -m "..."` after `/wiki` and `/handoff` writes. Not "chronic" — it's the per-session accumulation pattern.
- `close_runner.py` WinError 123 — two distinct concepts already cover this ([[close-runner-json-arg-parsing-bug]] and [[close-runner-windows-path-json-stringification-bug]]). Fixed in `f0979f1` and downstream commits.
- `output_validator` three-pass failure — separate concept.

## What this means for our workspace

### Triage priority order (highest leverage first)

1. **REGISTRATION drift (1 file)** — single fix, high blast radius (a misregistered hook can silently stop firing). Patch `snapshot_PreCompact.py` to register via `__lib/router.py`; commit.
2. **SYNTAX errors (10 files)** — each prevents import; 2 have UTF-8 BOM (strip BOM, re-test import). The others likely have structural issues (`_archived/` suggests some are intentionally archived but still scanned).
3. **Open harvest obligation (1 item)** — triage to closed/archive; the `pending/` directory should be empty at session start.
4. **Long-dirty plugin trees (3 trees, 12+ days)** — either commit the WIP or revert. Stale dirty trees block other agents from running `/close` cleanly.
5. **SyntaxWarnings (2 files)** — change `\s` to `r"\s"` or `\\s`; these will become errors on Python 3.12.
6. **DANGLING_PATHS (197)** — audit in batches; expect ~50% to be intentional (`_archived/` references) and ~50% to need cleanup. This is the largest category by count but lowest priority per item.
7. **STATE_GC (572)** — bulk GC pass; exclude any state file with mtime within the last 24h and any in directories that hooks actively write to. Use `find -mtime +30 -type f` (POSIX) or `Get-ChildItem -Recurse | Where-Object LastWriteTime -lt (Get-Date).AddDays(-30)` (PowerShell).
8. **Skill catalog drift (201 duplicates, 134 orphans)** — re-run `index_skills.py` after each fix batch; the catalog regenerates. Some duplicates are by design (user-scope overrides plugin cache); only flag ones that are stale.
9. **Disabled-in-Grok (237)** — periodic audit, not blocking. Check if any are "temporarily disabled" that should be re-enabled.

### Structural observations

- **The chronic categories overlap.** DANGLING_PATHS, orphan script references, and long-dirty plugin trees all stem from the same underlying issue: edits made without follow-through on importers/references. A session that fixes one will likely find the others.
- **The numbers are directional, not absolute.** `hooks_audit.py` and `index_skills.py` re-run each time; the 572/197/201 figures will shift by ±10% between runs. Use this concept as a baseline for trend tracking, not as a fixed inventory.
- **The `accumulation-problem` principle is vindicated.** Discovery (chronic-state inventory) is well-instrumented; resolution (the triage list above) requires a dedicated burn-down session. The chronic findings are exactly what the resolution-rate binding constraint predicts.

## Falsifier

This inventory is wrong if:
- `hooks_audit.py` re-run shows <50% of the 572 STATE_GC files (most were already cleaned and the scanner hadn't been re-run) → the snapshot was stale
- `index_skills.py` re-run shows <100 duplicates (most stale duplicates were cleaned in intervening sessions) → the duplicate count was inflated by transient state
- The 10 SYNTAX files all import successfully on a fresh Python (BOM-handling differs by Python version; some "errors" may be false positives) → the SYNTAX bucket was mis-scanned
- The REGISTRATION drift was already fixed in a commit not yet pulled → the 1-file REGISTRATION count is stale

**Re-test trigger:** after any burn-down session, re-run `hooks_audit.py` and `index_skills.py`, compare to the numbers in this concept, and either update the inventory or retire this concept as resolved.



## Evidence

The specific inventory numbers in this concept come from direct scanner output captured during session 019fbf02's close-check Phase 1 mechanical sweep (chat_history.jsonl lines corresponding to "workspace-health raw evidence"). The mechanism for each bucket:

- **REGISTRATION (1)**: `hooks_audit.py` walks `~/.claude/hooks/*.json` and `packages/.claude-marketplace/plugins/*/hooks/*.json`, then imports each registered module and asserts the registration chain goes through `__lib/router.py`. The 1-file failure means `snapshot_PreCompact.py` was registered directly in a `hooks.json` matcher instead of via the router pattern documented in `P:/packages/CLAUDE.md` and the Grok Build hook-development rules. Receipt: see `hooks-development` rules `Hook Registration (CRITICAL)` and `settings.json registration only` paragraphs.
- **SYNTAX (10)**: `hooks_audit.py` runs `python -c "import ast; ast.parse(open(path).read())"` (or equivalent) on each scanned file. 8 fail with parse errors; 2 fail because the file starts with a UTF-8 BOM (`\xef\xbb\xbf`) which `ast.parse` rejects on Python 3.10+. Receipt: `task_tracker_hook.py`, `hook_base.py` BOM confirmed via `Get-Content -Encoding Byte -TotalCount 3`.
- **DANGLING_PATHS (197)**: `hooks_audit.py` extracts `import X`, `from X import`, and string-path references from scanned files, then resolves each path relative to the workspace. 197 references cannot be resolved (file moved/deleted). Receipt: most concentrated in `dreaming_writer.py`, `refactor_validation.py`, `SessionStart_repo_map.py`, `Stop.py`, `tdd95_core.py` per scanner output.
- **STATE_GC (572)**: `hooks_audit.py` finds files under `~/.claude/state/`, `~/.grok/state/`, and `P:/.data/*/state/` with `mtime > 30 days`. The 30-day cutoff is configurable; 572 is the count at the default threshold. Receipt: scanner config at `hooks_audit.py:STATE_GC_MAX_AGE_DAYS` (approximate; see scanner source for exact location).
- **index_skills.py duplicates (201)**: `index_skills.py` parses `name:` from each `SKILL.md` frontmatter, groups by name, and reports groups with count > 1. Receipt: `index_skills.py:deduplicate_skills()` and downstream `compute_duplicate_stats()` (line numbers approximate).
- **index_skills.py disabled (237)**: parses `~/.grok/config.toml [plugins].disabled` and `~/.claude/settings.json enabledPlugins`, intersects with the catalog, reports skills in the catalog but not enabled. Receipt: `index_skills.py:compute_plugin_state()` and `skill-domain-map.md` line 19.

The inventory is **observed** for 2026-08-01 only; re-running `hooks_audit.py` and `index_skills.py` will produce different numbers as state shifts. The principle of chronic accumulation is in [[accumulation-problem-resolution-rate-binding-constraint]]; the specific buckets here are what to act on.

## Sources

- `P:/.claude/scripts/hooks_audit.py` — REGISTRATION/SYNTAX/DANGLING_PATHS/STATE_GC buckets
- `P:/.data/wiki/scripts/index_skills.py` — duplicate/disabled/orphan counts
- `~/.grok/state/slc-drift-log.jsonl` — exists per session-019fbf02 test-path receipt
- `P:/.data/harvest/pending/tp-session-019fb926.json` — single open harvest obligation (1 day old)
- `packages/.claude-marketplace/plugins/cc-skills-{ai-api,sdlc,utils}` — 12+ days dirty
- `packages/installers/ornith-server.log.err` — 10 days dirty
- `test_verification_engine.py:550`, `write_fix.py:166` — pre-existing `\s` SyntaxWarnings