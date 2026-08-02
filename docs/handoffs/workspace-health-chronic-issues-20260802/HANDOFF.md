---
thread_id: workspace-health-chronic-issues-20260802
parent_handoff_path: none
current_session_id: 019fa111-5dcb-7ff1-a4f5-415ad29bbe9e
current_terminal_id: console
produced_at: 2026-08-02T05:00:00Z
status: open
handoff_type: investigation
accurate_as_of_head: e4cd4ed1ff84dc18a0957ef04be53162765ac4ce
---

# Handoff: Workspace health chronic issues — 2026-08-02 session sweep

## Objective

Address the chronic workspace-health issues identified in the session 019fa111 sweep: invalid syntax files, dangling path references, stale state files, duplicate skill names, and disabled skills in Grok.

## Status

OPEN — chronic issues identified, triage needed to prioritize fixes.

## Producing context

Session 019fa111 sweep (2026-08-02) identified the following chronic workspace-health findings:

### Syntax errors (10 files)
- `analyze_reasoning_profiles.py`
- `reasoning_quality_gate_monitor.py`
- `_patch_stop.py`
- `damage-control/test-damage-control.py` (mismatched brackets)
- `task_tracker_hook.py` (U+FEFF BOM)
- `test_debug_windows.py`
- `test_debug_windows_simple.py`
- `validate_pre_clarification_gate.py`
- `archived StopHook_commitment_verifier.py`
- `hook_base.py` (U+FEFF BOM)

### Dangling paths (197 references)
References to missing files including: `Stop_router.py`, `SessionEnd_cleanup.py`, `dreaming-insights.md`, `repo_map.generated.*`, `critical_hooks.json`, `PreToolUse_tdd95_gate.py`, `validators/debug_v2_validator.py`, etc.

### Stale state files (572 files)
State files older than 30 days threshold: `skill_context_*`, `logs/*`

### Skill index issues
- 201 duplicate skill names
- 237 skills disabled in Grok
- 134 orphan script references
- No session breakage currently

### Registration issue
PreCompact plugin hook registered directly (should route via `__lib/router.py`)

## Read-first list

1. `P:/.data/wiki/concepts/skill-catalog.md` — current skill index state
2. `P:/.claude/hooks/PreToolUse.py` — dispatch chain (for PreCompact routing)
3. `P:/packages/.claude-marketplace/plugins/` — plugin source for hook registration

## Verified facts

- [FACT] 10 files with invalid syntax found in workspace scan (source: session 019fa111 sweep)
- [FACT] 197 dangling path references found (source: session 019fa111 sweep)
- [FACT] 572 state files older than 30 days (source: session 019fa111 sweep)
- [FACT] PreCompact plugin hook registered directly instead of via `__lib/router.py` (source: session 019fa111 sweep)

## Task packets

### T1: Fix PreCompact hook registration

- **id:** WH-01
- **goal:** Route PreCompact plugin hook via `__lib/router.py` instead of direct registration
- **in scope:** Hook registration in settings.json or hooks.json
- **out of scope:** Other hook types
- **acceptance:** PreCompact hook fires through the router dispatch chain; direct registration removed
- **falsifier:** PreCompact hook still fires directly after fix (then investigate router configuration)
- **verification level:** STATIC_INSPECTION + LIVE_BEHAVIOR

### T2: Fix U+FEFF BOM in hook_base.py and task_tracker_hook.py

- **id:** WH-02
- **goal:** Remove BOM from affected files
- **in scope:** `hook_base.py`, `task_tracker_hook.py`
- **out of scope:** Other files
- **acceptance:** Files read cleanly without BOM; `file` command shows no BOM marker
- **falsifier:** BOM still present after fix
- **verification level:** STATIC_INSPECTION

### T3: Fix mismatched brackets in damage-control/test-damage-control.py

- **id:** WH-03
- **goal:** Fix syntax error from mismatched brackets
- **in scope:** `damage-control/test-damage-control.py`
- **out of scope:** Other syntax issues
- **acceptance:** Python can parse the file without SyntaxError
- **falsifier:** SyntaxError persists after fix
- **verification level:** STATIC_INSPECTION

### T4: Clean up stale state files (572 files)

- **id:** WH-04
- **goal:** Remove or archive state files older than 30 days
- **in scope:** `skill_context_*`, `logs/*` under `~/.grok/`
- **out of scope:** Active state files within threshold
- **acceptance:** No state files older than 30 days remain; active files preserved
- **falsifier:** Active state files deleted or stale files remain
- **verification level:** LIVE_BEHAVIOR

### T5: Resolve dangling path references (197 references)

- **id:** WH-05
- **goal:** Either fix or remove references to missing files
- **in scope:** All 197 dangling references identified in sweep
- **out of scope:** References that are intentionally dead (documented as deprecated)
- **acceptance:** Zero dangling references remaining, or each is documented as intentional
- **falsifier:** Dangling references persist after fix
- **verification level:** STATIC_INSPECTION

## Hard constraints

- Do NOT delete state files that are actively referenced by running hooks
- Do NOT modify plugin cache files (`~/.claude/plugins/cache/`)
- All fixes must be verified with the appropriate verification level before closing

## Cross-reference couplings

- `P:/.data/wiki/concepts/hook-development.md` — hook registration standards
- `P:/.claude/rules/hook-development.md` — hook development rules
- `P:/docs/handoffs/close-runner-windows-path-bug-fix-20260802/HANDOFF.md` — related close-runner work

## Suggested next invocation

```
/go WH-01 -- fix PreCompact hook registration via __lib/router.py
```

## Last user message (verbatim)

> "Run the /handoff skill. Read ~/.grok/skills/handoff/SKILL.md for the workflow format, then execute auto-update mode using the pre-packed evidence below."

## Epistemic labels per claim

- "10 files with invalid syntax" — `[FACT]` (source: session 019fa111 sweep)
- "197 dangling path references" — `[FACT]` (source: session 019fa111 sweep)
- "572 state files older than 30 days" — `[FACT]` (source: session 019fa111 sweep)
- "PreCompact hook registered directly" — `[FACT]` (source: session 019fa111 sweep)
- "No session breakage currently" — `[FACT]` (source: session 019fa111 sweep)
- "BOM removal will fix syntax" — `[INFERENCE]` (BOM is a known cause of Python syntax errors)
- "Stale state files can be safely cleaned" — `[INFERENCE]` (30-day threshold is the policy; active files are within threshold)
