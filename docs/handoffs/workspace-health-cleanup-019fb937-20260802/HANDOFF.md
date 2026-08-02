---
thread_id: workspace-health-cleanup-019fb937
parent_handoff_path: none
current_session_id: 019fb937-b03e-7f80-a4b0-68afdb7da38d
current_terminal_id: 311cd4b1-2bf4-47ec-8abd-7530e971493c
produced_at: 2026-08-02T05:15:00Z
status: open
handoff_type: investigation
accurate_as_of_head: 963c0aff7cb1f5a5ecd83a76e1844b1890049218
---

# Handoff: Workspace health cleanup — session 019fb937

## Objective

Resolve chronic workspace-health findings from the close-check report: 10 hook syntax errors, 197 dangling path references, 572 stale state files (>30d), 201 duplicate skill names, and 134 orphan script references.

## Status

OPEN — chronic workspace-health issues accumulated across multiple sessions. No cleanup action was taken during session 019fb937.

## Producing context

- Session: `019fb937-b03e-7f80-a4b0-68afdb7da38d` (2026-07-31 → 2026-08-02)
- Terminal: 311cd4b1-2bf4-47ec-8abd-7530e971493c
- Host: grok (Grok Build)

## Read-first list

1. `P:/.data/wiki/concepts/hook-evidence-collection-cost-vs-timeout-tradeoff.md` — hook timeout RCA
2. `P:/.data/wiki/concepts/skill-catalog.md` — durable skill registry (657 skills indexed)
3. `P:/.claude/scripts/hooks_audit.py` — the audit script that produced these findings

## Verified facts

- [FACT] 10 hook syntax errors across 10 files (source: hooks_audit.py output)
  - analyze_reasoning_profiles.py:1, reasoning_quality_gate_monitor.py:1, _patch_stop.py:12, damage-control/test-damage-control.py:387, task_tracker_hook.py:1 BOM, test_debug_windows.py:10, test_debug_windows_simple.py:19, validate_pre_clarification_gate.py:19, _archived/StopHook_commitment_verifier.py:102, __lib/hook_base.py:1 BOM
- [FACT] 1 registration error — snapshot_PreCompact.py registered directly instead of via __lib/router.py (source: hooks_audit.py output)
- [FACT] 197 dangling path references — hooks reference files that don't exist (source: hooks_audit.py output)
- [FACT] 572 state GC entries — hook state files >30d old in state/logs/, state/skill_context/, state/local_summary_guidance/ (source: hooks_audit.py output)
- [FACT] 657 total skills indexed, 201 duplicate names across scopes, 237 disabled in Grok, 134 orphan script references (source: index_skills.py --audit)
- [FACT] 12 canonical skills in .agents/skills (source: index_skills.py --audit)
- [FACT] Specific orphans: close missing scripts/git_state_check.py, scripts/dirty_age.py, scripts/index_skills.py; dream missing scripts/append_log.py (3x); go missing scripts/capabilities.py (2x), scripts/close_coordinator.py, scripts/ddgs_search.py, scripts/fmea_scan.py, scripts/log_spawn.py; harvest missing scripts/wiki_marker_scan.py (source: index_skills.py --audit)

## Current state

### Chronic findings by severity

| Category | Count | Status |
|----------|-------|--------|
| Hook syntax errors | 10 | FAIL — blocks hook dispatch for affected files |
| Registration errors | 1 | FAIL — snapshot_PreCompact.py bypasses router |
| Dangling paths | 197 | FAIL — hooks reference non-existent files |
| Stale state files | 572 | WARN — >30d accumulation in state/ |
| Duplicate skill names | 201 | WARN — across scopes |
| Disabled skills (Grok) | 237 | WARN — indexed but not active |
| Orphan script references | 134 | WARN — skills reference missing scripts |

### Specific orphan scripts (highest priority)

1. **close** — missing git_state_check.py, dirty_age.py, index_skills.py (3 missing scripts)
2. **dream** — missing append_log.py (3 missing references)
3. **go** — missing capabilities.py, close_coordinator.py, ddgs_search.py, fmea_scan.py, log_spawn.py (5 missing scripts)
4. **harvest** — missing wiki_marker_scan.py (1 missing script)

## Task packets

### T1: Fix 10 hook syntax errors

- **id:** WH-01
- **goal:** Resolve all 10 hook syntax errors so hooks_audit.py returns 0 SYNTAX failures
- **in scope:** The 10 files listed in the verified facts
- **out of scope:** Hook dispatch chain architecture (working as designed)
- **files / anchors:** Each of the 10 files listed above
- **acceptance:** `python P:/.claude/scripts/hooks_audit.py --packages P:/packages/.claude-marketplace/plugins` returns 0 SYNTAX failures
- **falsifier:** Same or more syntax errors after fixes
- **verification level required:** LIVE_BEHAVIOR (re-run hooks_audit.py)
- **estimate:** 2 hours (10 files, most are single-line fixes)

### T2: Resolve 197 dangling path references

- **id:** WH-02
- **goal:** Eliminate dangling path references in hook registrations
- **in scope:** All 197 dangling paths from hooks_audit.py output
- **out of scope:** Intentional placeholder references (if any exist)
- **files / anchors:** Hook registration files (hooks.json, settings.json, router.py)
- **acceptance:** hooks_audit.py returns 0 DANGLING_PATHS failures
- **falsifier:** Same or more dangling paths after cleanup
- **verification level required:** LIVE_BEHAVIOR (re-run hooks_audit.py)
- **estimate:** 3 hours (197 entries, need to classify each as real-missing vs intentional-placeholder)

### T3: GC 572 stale state files (>30d)

- **id:** WH-03
- **goal:** Remove hook state files older than 30 days from state/logs/, state/skill_context/, state/local_summary_guidance/
- **in scope:** All 572 state files >30d old
- **out of scope:** State files <30d old
- **files / anchors:** ~/.grok/hooks/state/ (logs/, skill_context/, local_summary_guidance/)
- **acceptance:** hooks_audit.py returns 0 STATE_GC failures; state directory size reduced
- **falsifier:** Same or more stale state files after GC
- **verification level required:** LIVE_BEHAVIOR (re-run hooks_audit.py + check directory size)
- **estimate:** 30 minutes (bulk delete with verification)

### T4: Resolve orphan script references

- **id:** WH-04
- **goal:** Create or remove references to the 134 orphan scripts (close: 3, dream: 3, go: 5, harvest: 1 = 12 specific orphans; remainder are across other skills)
- **in scope:** 134 orphan script references from index_skills.py --audit
- **out of scope:** Skills with no orphan references
- **files / anchors:** Skill SKILL.md files and their script references
- **acceptance:** index_skills.py --audit reports 0 orphan references
- **falsifier:** Same or more orphan references after cleanup
- **verification level required:** LIVE_BEHAVIOR (re-run index_skills.py --audit)
- **estimate:** 2 hours (134 references, need to assess each)

## Hard constraints

- Do NOT delete hook files that are still referenced by active registrations
- Do NOT remove state files that may be in-use by a running session
- All fixes must be verified by re-running hooks_audit.py or index_skills.py --audit
- Fix syntax errors before fixing dangling paths (syntax errors may mask real path issues)

## Cross-reference couplings

- `P:/.claude/scripts/hooks_audit.py` — the audit script that produces these findings
- `P:/.data/wiki/concepts/skill-catalog.md` — durable skill registry
- `~/.grok/skills/` — skill files that may contain orphan references
- `P:/packages/.claude-marketplace/plugins/` — plugin hook files with syntax errors

## Other outstanding streams

- **git-state** — 27 uncommitted files, 17 unpushed commits (separate handoff)
- **close-gates** — session close readiness gaps (separate handoff)
- **lifecycle-skill-coverage** — skills not invoked during session (separate handoff)
- **critical-code-trace** — code edited without /trace (separate handoff)

## Explicit non-goals

- Do NOT refactor the hook dispatch chain — it's working as designed
- Do NOT remove disabled skills from the catalog — they may be re-enabled
- Do NOT create new hooks or skills — only fix existing issues

## Resumption protocol

1. Run hooks_audit.py to confirm current state (WH-01 first)
2. Fix syntax errors (WH-01)
3. Fix registration error (WH-01, sub-item)
4. Clean dangling paths (WH-02)
5. GC stale state files (WH-03)
6. Resolve orphan script references (WH-04)
7. Re-run both audit scripts to verify all findings are resolved

## Suggested next invocation

```
/maintain — run workspace-health cleanup on the chronic items from the close-check report
```

## Last user message (verbatim)

> "Please use the handoff skill"

## Epistemic labels per claim

- [FACT] 10 hook syntax errors — sourced from hooks_audit.py output (10 file:line entries)
- [FACT] 1 registration error — sourced from hooks_audit.py output
- [FACT] 197 dangling paths — sourced from hooks_audit.py output
- [FACT] 572 state GC entries — sourced from hooks_audit.py output
- [FACT] 657 skills, 201 duplicates, 237 disabled, 134 orphans — sourced from index_skills.py --audit
- [INFERENCE] No cleanup action was taken during this session — based on absence of cleanup commands in session evidence

## Changelog

| Date | Session | Action |
|------|---------|--------|
| 2026-08-02T05:15 | 019fb937... | created |
