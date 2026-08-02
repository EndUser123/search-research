---
thread_id: workspace-health-chronic-019fa8f8
parent_handoff_path: P:/docs/handoffs/postsession-20260801/HANDOFF.md
current_session_id: 019fa8f8-7e86-77f0-8e81-a7609f3c8b14
current_terminal_id: grok-main
produced_at: 2026-08-02T21:30:00Z
status: open
handoff_type: improvement
accurate_as_of_head: f17b724e94333b998470cd4ab888c63ac2e370b9
---

# Handoff: Workspace health chronic remediation

## Objective

Address the chronic workspace-health issues identified by the session sweep: 1 registration failure, 10 syntax errors, 197 dangling paths, 578 state GC files, 201 duplicate skill names, 237 disabled skills, and 135 orphan script references.

## Status

OPEN — chronic issues identified, remediation deferred to a dedicated session.

## Producing context

- Session: 019fa8f8-7e86-77f0-8e81-a7609f3c8b14 (started 2026-07-28T07:44:45)
- hooks_audit.py scan results: 1 REGISTRATION failure, 10 SYNTAX errors, 197 DANGLING_PATHS, 578 STATE_GC files
- index_skills.py scan results: 657 total skills, 201 duplicate names, 237 disabled in Grok, 135 orphan references, 12 canonical .agents/skills
- These are chronic issues that recur across sessions and need systematic remediation

## Read-first list

1. `P:/.claude/scripts/hooks_audit.py` — the audit script
2. `P:/.data/wiki/scripts/index_skills.py` — the skills indexer
3. `P:/.data/wiki/concepts/workspace-script-fmea-concurrent-io-and-shell-injection-patterns.md` — FMEA patterns

## Verified facts

- [FACT] hooks_audit found 1 REGISTRATION failure (snapshot_PreCompact.py not via router.py) (source: sweep evidence, workspace-health FAIL)
- [FACT] hooks_audit found 10 SYNTAX errors (source: sweep evidence, workspace-health FAIL)
- [FACT] hooks_audit found 197 DANGLING_PATHS across dreaming_writer, refactor_validation, SessionStart_repo_map, Stop, tdd95_core, verify_visibility_guard_protection, and 172 more (source: sweep evidence, workspace-health FAIL)
- [FACT] hooks_audit found 578 STATE_GC files older than 30d threshold (source: sweep evidence, workspace-health FAIL)
- [FACT] index_skills found 201 duplicate names across scopes (source: sweep evidence, workspace-health WARN)
- [FACT] index_skills found 237 skills disabled in Grok (source: sweep evidence, workspace-health WARN)
- [FACT] index_skills found 135 orphan script references (source: sweep evidence, workspace-health WARN)

## Task packets

### T1: Fix hooks_audit REGISTRATION failure

- **id:** WH-T1
- **goal:** Fix the PreCompact plugin hook registration (not via router.py)
- **in scope:** snapshot_PreCompact.py and its hooks.json registration
- **out of scope:** other hook fixes
- **files / anchors:** P:/.claude/hooks/PreToolUse.py (dispatch chain)
- **acceptance:** snapshot_PreCompact.py is registered via router.py, not directly in hooks.json
- **falsifier:** if the hook still fires directly without router.py mediation
- **verification level required:** LIVE_BEHAVIOR
- **estimate:** 30 minutes

### T2: Fix SYNTAX errors in 10 files

- **id:** WH-T2
- **goal:** Fix the 10 syntax errors identified by hooks_audit
- **in scope:** analyze_reasoning_profiles.py, reasoning_quality_gate_monitor.py, _patch_stop.py, damage-control/test-damage-control.py, task_tracker_hook.py, test_debug_windows.py, test_debug_windows_simple.py, validate_pre_clarification_gate.py, _archived/StopHook_commitment_verifier.py, hook_base.py
- **out of scope:** other files
- **files / anchors:** each file listed above
- **acceptance:** `python -m py_compile` passes on all 10 files
- **falsifier:** if any file still has a syntax error
- **verification level required:** LIVE_BEHAVIOR
- **estimate:** 2 hours

### T3: Clean up 197 dangling paths

- **id:** WH-T3
- **goal:** Remove or fix the 197 dangling path references across hook scripts
- **in scope:** all files referenced by hooks_audit dangling paths
- **out of scope:** adding new paths
- **files / anchors:** hooks_audit output
- **acceptance:** hooks_audit DANGLING_PATHS count drops to 0
- **falsifier:** if dangling paths persist after cleanup
- **verification level required:** LIVE_BEHAVIOR
- **estimate:** 3 hours

### T4: State GC — clean up 578 stale state files

- **id:** WH-T4
- **goal:** Remove state files older than 30 days (logs, skill_context_*.json)
- **in scope:** P:/.claude/hooks/state/ and P:/.grok/state/ directories
- **out of scope:** active state files (less than 30 days old)
- **files / anchors:** files with LastWriteTime > 30 days
- **acceptance:** STATE_GC count drops to 0 or below threshold
- **falsifier:** if active state files are deleted or count remains above threshold
- **verification level required:** LIVE_BEHAVIOR
- **estimate:** 1 hour

### T5: Deduplicate 201 skill names

- **id:** WH-T5
- **goal:** Resolve the 201 duplicate skill names across scopes
- **in scope:** all skills with duplicate names
- **out of scope:** adding new skills
- **files / anchors:** index_skills.py output
- **acceptance:** no duplicate skill names across scopes
- **falsifier:** if duplicates persist
- **verification level required:** LIVE_BEHAVIOR
- **estimate:** 2 hours

## Open decisions

1. **Remediation order:** T1 (registration fix) is the most critical — it affects hook dispatch correctness. T2 (syntax errors) is next — it affects script reliability. T3-T5 are cleanup.
2. **Bulk vs incremental:** Should T3 (197 dangling paths) be fixed in one batch or per-directory? Leading: per-directory, matching the AGENTS.md auto-commit rule.

## Hard constraints

- AGENTS.md destructive-git ban: no force-push, no reset --hard, no rebase -i, no clean -fd
- AGENTS.md auto-commit: stage only files you changed; surgical git add
- All hook changes must be tested with real dispatch (not mocked), per .claude/rules/testing.md

## Cross-reference couplings

- `P:/.claude/scripts/hooks_audit.py` — the audit script
- `P:/.data/wiki/scripts/index_skills.py` — the skills indexer
- `P:/.data/wiki/concepts/workspace-script-fmea-concurrent-io-and-shell-injection-patterns.md` — FMEA patterns

## Resumption protocol

1. Fix T1 (registration failure) first — it affects hook dispatch
2. Fix T2 (syntax errors) next — it affects script reliability
3. T3-T5 are cleanup and can be done in any order
4. Re-run hooks_audit after each fix to verify

## Suggested next invocation

```
/go WH-T1 — fix PreCompact registration failure
```

## Last user message (verbatim)

> "Run the /handoff skill."

## Epistemic labels per claim

- "hooks_audit found 1 REGISTRATION failure" — [FACT] (source: sweep evidence, workspace-health FAIL)
- "hooks_audit found 10 SYNTAX errors" — [FACT] (source: sweep evidence, workspace-health FAIL)
- "hooks_audit found 197 DANGLING_PATHS" — [FACT] (source: sweep evidence, workspace-health FAIL)
- "hooks_audit found 578 STATE_GC files" — [FACT] (source: sweep evidence, workspace-health WARN)
- "index_skills found 201 duplicate names" — [FACT] (source: sweep evidence, workspace-health WARN)
- "index_skills found 237 disabled skills" — [FACT] (source: sweep evidence, workspace-health WARN)
- "index_skills found 135 orphan references" — [FACT] (source: sweep evidence, workspace-health WARN)

## Changelog

| Date | Session | Action |
|------|---------|--------|
| 2026-08-02T21:30 | 019fa8f8... | created |
