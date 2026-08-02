---
title: "3 Unresolved Friction Items from Close-Check"
current_session_id: 019fbf26-08f9-7f12-ace1-15ce7541c140
source_session: [019f902a-621d-7711-9436-7c6003c57793, 019fbf26-08f9-7f12-ace1-15ce7541c140]
produced_at: 2026-08-01
status: OPEN — not started
priority: HIGH
tags: [friction, compaction, skill-catalog, session-start, hooks]
---

# 3 Unresolved Friction Items

Close-check /friction subagent identified 14 friction items across session
`019f902a`. 11 already have handoffs. These 3 do not.

## Item 1: Auto-compact `model_context_window_exceeded` serializer bug [HIGH]

**Root cause:** The compaction sampler doesn't recognize the `model_context_window_exceeded`
stop variant. When a session exceeds the context window, the compaction request fails with:
```
Compaction sampler build failed: compact failed: serialization error:
unknown variant 'model_context_window_exceeded', expected one of
'stop', 'length', 'tool_calls', 'content_filter', 'function_call'
```

**Evidence:**
- `compaction_requests/49f317bd-37f8-45f4-bf1c-e3bf04cb18ff.json` in session `019f902a`
- `updates.jsonl` final turn ends with `stop_reason: error, agent_result: "serialization error"`
- Session `019f902a` was frozen mid-turn by this failure

**Impact:** Every long-running session that hits the context window loses auto-compaction.
The transcript is intact but no `segment_*.md` files are produced, meaning `/friction`,
`/handoff`, `/recap-grok`, and `/close-check` all lose pre-compaction context.

**Resolution path:** This is likely an upstream Grok Build issue. The compaction sampler
needs to handle the `model_context_window_exceeded` stop reason. File a bug report or
patch the sampler if the code is accessible.

## Item 2: Skill catalog generator emits stale workspace-scope paths [HIGH]

**Root cause:** Skills were moved from workspace scope (`P:\.grok\skills\`) to user scope
(`~/.grok/skills/`), but the catalog generator still emits workspace-scope paths for them.

**Evidence:**
- Session `019f902a` hit `read_file` failures on `P:\.grok\skills\review\SKILL.md` and
  `P:\.grok\skills\refactor\SKILL.md` — both don't exist (skills moved to user scope)
- The system-reminder catalog at end of session still lists workspace-scope paths
- 9 stale references were fixed across 5 files in-session, but the root cause (catalog
  generator) was not addressed

**Impact:** Every session that trusts catalog paths without probing hits read failures.
Causes 46 re-reads per session as the agent works around the failures.

**Resolution path:** Fix `index_skills.py` or the catalog generation logic to only emit
workspace-scope paths for skills that actually exist at that path.

## Item 3: SessionStart hook failures (3 hooks, exit code 1) [MED]

**Root cause:** Unknown — three SessionStart hooks fail with exit code 1 at session start.

**Evidence:**
- Transcript start: `"global/SessionStart:session_start[0].hooks[0]" status: failed exit code 1`
- 3 hooks failed in the same batch (active-surface, drift-surface, qmd-patches)

**Impact:** SessionStart hooks provide the active-surface snapshot, drift detection, and
QMD patches. When they fail, the session starts without the enforcement and observability
context they provide.

**Resolution path:** Diagnose each hook individually. Check stderr output in
`~/.grok/hooks/.evidence/` or session events for the failure reason.

## Acceptance criteria

- [ ] Item 1: Either fix the compaction sampler or create a workaround + upstream bug report
- [ ] Item 2: Catalog generator only emits paths that resolve to actual files
- [ ] Item 3: All 3 SessionStart hooks pass with exit code 0 on a fresh session start

## Cross-references

- Session `019f902a` transcript: `C:\Users\brsth\Downloads\## Tools.txt`
- Close-check report: `~/.grok/sessions/.../wf_019fbf3c872070d3b0bba44facdfd293/scratch/pre-close-report.md`
- Wiki concept: `skill-catalog-scope-inconsistency-causes-cascading-read-failures.md`
