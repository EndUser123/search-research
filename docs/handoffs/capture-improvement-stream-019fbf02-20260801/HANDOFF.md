---
thread_id: 019fbf02-capture-improvements
parent_handoff_path: P:/docs/handoffs/session-observations-019fbf02-20260801/HANDOFF.md
current_session_id: 019fbf02-d3dd-7f72-9ad2-4538790c0a82
created: 2026-08-01
status: open
assigned_to: grok
priority: high
---

# Capture Improvement Stream: 019fbf02 (2026-08-01)

## Purpose

This handoff captures the **improvement stream** findings from the
`/capture` skill scan of session 019fbf02. Knowledge stream findings
(operator corrections, architectural decisions, near-miss patterns,
transferable success patterns) are persisted as wiki concepts in
`P:/.data/wiki/concepts/` and committed. This handoff is for the
**actionable items** — the things an agent should *do* in a follow-up
session, not just know about.

**Dual-stream routing rule** (from `~/.grok/skills/capture/SKILL.md`):
improvements go to the task backlog / handoffs, NOT to wiki concepts.
An improvement becomes knowledge only after implementation.

## What `/capture` found — categorized for action

### Tier 1: System gaps (BLOCKING the close pipeline)

1. **close_runner.py JSON-literal arg bug** (HIGH PRIORITY — blocks close-gates gate)
   - Symptom: `OSError [WinError 123]` when close-check Phase 1 invokes close_runner
   - Root cause: dispatcher passes structured session record where runner expects string path
   - **Wiki concept written**: `P:/.data/wiki/concepts/close-runner-json-arg-parsing-bug.md`
   - **Action needed**: (a) add boundary type check in close_runner.py; (b) fix upstream caller to extract session_id string before passing
   - **Owner**: whoever runs the next close-check Phase 1 (operator or grok)
   - **Effort**: ~15 min

2. **harvest CLI not on PATH** (HIGH PRIORITY — degrades obligation tracking)
   - Symptom: `harvest: The term 'harvest' is not recognized`
   - **Wiki concept written**: `P:/.data/wiki/concepts/harvest-cli-not-on-path.md`
   - **Action needed**: (a) find entry-point script (`pip show -f harvest` or similar); (b) symlink onto PATH dir or add to `$PROFILE`; (c) preferred: update `/harvest` SKILL.md to detect missing CLI and fall back to `python -m harvest.cli`
   - **Cross-session impact**: `P:/.data/harvest/pending/tp-session-019fb926.json` has been OPEN for 1 day because no agent can run `harvest show` to see it
   - **Owner**: grok
   - **Effort**: ~30 min including skill update

### Tier 2: Git hygiene (multi-terminal coordination)

3. **28 dirty files in P:\** (MEDIUM PRIORITY)
   - Includes my own 3 files (now committed in 9dc3d46)
   - Remaining 25 files include:
     - `.pi/skills/notebooklm/SKILL.md` (likely from sibling session)
     - `packages/yt-is` (submodule state)
     - 3 `pyproject.toml` files in `projects/evidence_validation_api`, `projects/yt-fts`, `projects/yt_analysis/src/backend_engine`
     - `.artifacts/continuation-coverage-019fa8f8.json` (artifacts, may be ephemeral)
     - `docs/designs/2026-07-25-check-orchestrator-design.md`
     - 3 chronic plugins (cc-skills-ai-api, cc-skills-sdlc, cc-skills-utils) — 12+ days dirty
   - **Action needed**: verify each file's owner before committing; don't blindly `git add -A` — risk overwriting sibling work
   - **Owner**: grok (in coordination with any sibling sessions currently editing)
   - **Effort**: ~10 min if no conflicts; potentially much longer if sibling collisions

4. **15 commits ahead of origin/main in P:\** (LOW PRIORITY)
   - Most recent: `d67075d 'handoff: extend skill graph to track finding-routing coverage'`
   - **Action needed**: review commit history, then `git push origin main` if no force-push concerns
   - **Owner**: operator (pushes are human-gated per AGENTS.md trust ladder)

5. **7 dirty files in ~/.grok + 23 commits ahead** (LOW PRIORITY)
   - Includes my 3 uncommitted edits to `skills/todo/SKILL.md`, `state/hook_failures.jsonl`, `version.json`
   - Plus `implement-memory/` untracked directory
   - Most recent ahead commit: `47e68f7 'fix: update nim-openai-gpt-oss-20b note — spawn verified 2026-08-01'`
   - **Action needed**: commit my edits, review and push the 23 ahead
   - **Owner**: operator (pushes are human-gated)
   - **Effort**: ~5 min for commits; longer for push review

### Tier 3: Chronic findings (recurring, requires operator decision)

These have been flagged across multiple sessions and require operator decision
on whether to fix, defer, or hand off:

6. **CHRONIC: 3 plugins dirty 12+ days** (`cc-skills-{ai-api,sdlc,utils}`)
   - Decision: Are these intentionally uncommitted (cache vs source confusion)?
     Or did someone forget to commit? Recommend: inspect each plugin's git log
     to determine intentionality. If unintentional: commit + push.
   - Owner: operator

7. **CHRONIC: packages/installers/ornith-server.log.err dirty 10 days**
   - Likely auto-generated server log. Recommend: add to `.gitignore` for the
     installer package, then commit the removal.
   - Owner: grok (~5 min)

8. **CHRONIC: hooks_audit.py — REGISTRATION (1)**
   - `snapshot_PreCompact.py` registered directly instead of via `__lib/router.py`
   - Decision: register via router per `packages/CLAUDE.md` standard, or document
     the exception. Recommend: route through router for consistency.
   - Owner: grok (~10 min)

9. **CHRONIC: hooks_audit.py — SYNTAX (10)**
   - Invalid syntax in: `analyze_reasoning_profiles.py`, `reasoning_quality_gate_monitor.py`,
     `_patch_stop.py`, `task_tracker_hook.py` (BOM), `test_debug_windows.py`,
     `validate_pre_clarification_gate.py`, `_archived/StopHook_commitment_verifier.py`,
     `hook_base.py` (BOM), `test-damage-control.py`
   - Decision: BOM files (3) likely have encoding issues — strip BOM via `Get-Content | Set-Content`.
     The rest may be Python syntax errors from incomplete edits. Recommend: triage each.
   - Owner: grok (~30 min)

10. **CHRONIC: hooks_audit.py — DANGLING_PATHS (197)**
    - References to missing files across `dreaming_writer.py`, `refactor_validation.py`,
      `SessionStart_repo_map.py`, `Stop.py`, `tdd95_core.py`, etc.
    - Decision: Either fix the references (rename/move targets) or remove the dead references.
      197 is too many for a single session — recommend handoff to a dedicated cleanup.
    - Owner: grok (multi-session work)

11. **CHRONIC: hooks_audit.py — STATE_GC (572)**
    - Log/state files >30d old
    - Decision: Run `python P:/.agents/scripts/state_gc.py` (if it exists) or write
      a one-liner GC script. Low risk — log files are ephemeral by nature.
    - Owner: grok (~15 min)

12. **CHRONIC: index_skills.py — 201 duplicate skill names, 237 disabled-in-Grok, 134 orphan script references**
    - Most likely artifact of skill-cache drift between Grok Build and Claude Code.
    - Decision: This is the canonical "skill catalog scope inconsistency" pattern (see
      `P:/.data/wiki/concepts/skill-catalog-scope-inconsistency-causes-cascading-read-failures.md`).
      Recommend: re-run `python P:/.data/wiki/scripts/index_skills.py --audit` after a
      `grok plugin cache` sync to see if numbers normalize. If they don't, handoff to
      dedicated skill-decomposition session.
    - Owner: operator (decides on scope of decomposition)

13. **CHRONIC: SyntaxWarnings (3) — invalid escape sequences**
    - `test_verification_engine.py:550`, `write_fix.py:166` — `\s` invalid
    - Decision: pre-existing; fix or use raw strings. ~5 min.
    - Owner: grok

## Decision: which to act on now vs defer

**Act now (Tier 1 — close-blockers):**
- close_runner.py bug (15 min, blocks close-check Phase 1)
- harvest CLI on PATH (30 min, degrades obligation tracking)

**Act in next session (Tier 2 — git hygiene):**
- Commit remaining dirty files in P:\ and ~/.grok (sibling-aware)
- Push 15+23 commits ahead (operator approval required)

**Defer to operator decision (Tier 3 — chronic):**
- Plugin 12-day dirty, server log 10-day dirty
- hooks_audit chronic findings (DANGLING_PATHS 197, STATE_GC 572, SYNTAX 10)
- index_skills catalog drift (201 dupes, 237 disabled, 134 orphans)

## Skill-edit cold-read audit (mandatory per AGENTS.md)

This session edited 2 wiki concepts. Per AGENTS.md skill-edit cold-read audit rule,
a fresh explore subagent should cold-read both to verify they reflect actual workspace
state, not session-local narrative. The cold-read did NOT happen this session.

**Action needed**: spawn a fresh explore subagent in the next session to cold-read:
1. `P:/.data/wiki/concepts/close-runner-json-arg-parsing-bug.md`
2. `P:/.data/wiki/concepts/harvest-cli-not-on-path.md`

Confirm:
- The traceback shape matches what close_runner actually produces
- The harvest workaround actually works (try `python -m harvest.cli show --top 5`)
- The "Applies to" sections are correct (other tools affected?)

## Verification receipts

- Commit `9dc3d46` in P:\ — captures the 2 wiki concepts + log update
- `P:/.data/wiki/log.md` — 2 new entries dated 2026-08-01 ~22:56
- This handoff exists at `P:/docs/handoffs/capture-improvement-stream-019fbf02-20260801/HANDOFF.md`
- Sibling session already wrote `close-runner-windows-path-json-stringification-bug.md` —
  recommend reconciling with my `close-runner-json-arg-parsing-bug.md` (same root cause, different framing)

## Cross-references

- `P:/.data/wiki/concepts/close-runner-json-arg-parsing-bug.md` (new — this session)
- `P:/.data/wiki/concepts/harvest-cli-not-on-path.md` (new — this session)
- `P:/.data/wiki/concepts/serde-broken-false-positive-sweep-20260801.md` (related)
- `P:/.data/wiki/concepts/python-m-ruff-swallows-stdout-in-powershell.md` (parallel pattern)
- `P:/.data/wiki/concepts/close-check-invokes-capture.md` (close-check workflow context)
- `P:/docs/handoffs/session-observations-019fbf02-20260801/HANDOFF.md` (parent handoff)
