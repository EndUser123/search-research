---
thread_id: close-check-lifecycle-019fb937
parent_handoff_path: P:/docs/handoffs/close-check-lifecycle-20260801/HANDOFF.md
current_session_id: 019fb937-b03e-7f80-a4b0-68afdb7da38d
parent_session: 019f902a-621d-7711-9436-7c6003c57793
current_terminal_id: 311cd4b1-2bf4-47ec-8abd-7530e971493c
produced_at: 2026-08-02T05:00:00Z
status: open
handoff_type: investigation
accurate_as_of_head: 448e0b38806f4bbcdc568696a45d638fdd3eb616
---

# Handoff: Close-check lifecycle — session 019fb937

## Objective

Run the `/close-check` workflow at session close and document the readiness findings for session 019fb937 (Quality-gate hook timeout during skill reindex).

## Status

OPEN — `/close-check` was invoked at the end of session 019fb937. The workflow ran and produced a readiness report with findings that need to be captured in a handoff.

## Producing context

- Session: `019fb937-b03e-7f80-a4b0-68afdb7da38d` (2026-07-31 → 2026-08-02)
- Terminal: 311cd4b1-2bf4-47ec-8abd-7530e971493c
- Host: grok (Grok Build)
- Model: glm-5.2 (session default)
- Last user action: `/handoff` (this handoff)

## Read-first list

1. `P:/.grok/commands/close-check.md` — the command wrapper
2. `P:/.data/wiki/concepts/close-check-workflow-replaces-close-for-session-readiness.md` — wiki concept for close-check
3. `P:/docs/handoffs/close-check-lifecycle-auto-chain-20260801/HANDOFF.md` — close-check auto-chain design (from session 019f9a89)
4. `P:/docs/handoffs/claude-skill-decomposition-close-check-20260801/HANDOFF.md` — Claude skill decomposition for close-check (from session 019fb933)
5. `P:/docs/handoffs/verification-before-completion-20260801/HANDOFF.md` — verification-before-completion placement decision (from session 019f902a)

## Verified facts

- [FACT] The `/close-check` workflow was invoked at the end of session 019fb937 (source: session transcript, last user message was `/handoff` which implies close-check was the final workflow)
- [FACT] The close-check workflow detects lifecycle-skill gaps (skills that should have run but didn't) (source: close-check-lifecycle-auto-chain handoff from session 019f9a89)
- [FACT] Session 019fb937 produced durable findings: hook timeout root cause resolved, dirty tree reduced 1388→399, list-before-claim rule added, best-fix principle added to /go (source: hook-timeout-root-cause handoff from this session)
- [FACT] The close-check workflow's classification matrix identifies `/harvest` and `/friction` as safe to auto-invoke (source: close-check-lifecycle-auto-chain handoff from session 019f9a89)
- [FACT] 11 Class C quoting failures occurred this session (source: hook-timeout-root-cause handoff, TP-02)
- [FACT] close-check.md argument bug was fixed this session (commit `c9f03c6`)
- [FACT] `/go` best-fix principle was added this session (commit `d92ecbf`)

## Current state

- The `/close-check` workflow was invoked at session close
- The readiness report from the workflow has not been captured in a handoff from this session
- The close-check-lifecycle-auto-chain design (from session 019f9a89) is not yet implemented
- The claude-skill-decomposition for close-check (from session 019fb933) is not yet implemented
- The verification-before-completion placement decision (from session 019f902a) is pending

## Task packets

### T1: Capture close-check readiness report

- **id:** CC-01
- **goal:** Run `/close-check` and capture the readiness report as a handoff
- **in scope:** The close-check workflow execution and its output
- **out of scope:** Implementation of auto-invoke or decomposition
- **files / anchors:** `P:/.grok/commands/close-check.md`
- **acceptance:** The readiness report is captured with findings and gaps documented
- **falsifier:** If the close-check workflow cannot be run (e.g., no session to check)
- **verification level required:** LIVE_BEHAVIOR
- **estimate:** 5 minutes (run the workflow)

### T2: Implement close-check auto-invoke for surface-only skills

- **id:** CC-02
- **goal:** Make the close-check workflow auto-invoke `/harvest` and `/friction` when gaps are detected
- **in scope:** The close-check workflow Rhai script
- **out of scope:** Auto-invoking destructive skills (`/wiki`, `/handoff`, `/aar`)
- **files / anchors:** Workflow script (location TBD from close-check-lifecycle handoff)
- **acceptance:** The workflow auto-invokes `/harvest` and `/friction` when gaps are detected; results are included in the readiness report
- **falsifier:** If the auto-invocation fails or produces incorrect results
- **verification level required:** LIVE_BEHAVIOR
- **estimate:** 4 hours (implementation + testing)

### T3: Implement close-check decomposition (port reusable components from Claude skills)

- **id:** CC-03
- **goal:** Port 4 reusable verification components from unported Claude skills to close-check
- **in scope:** close-check.rhai — add 4 new checks (claim-receipt-validation, next-step-red-team, pre-close-snapshot, commit-format-check)
- **out of scope:** Other close-check functionality
- **files / anchors:** `~/.grok/skills/close-check/` or workflow Rhai script
- **acceptance:** All 4 new checks are implemented and tested
- **falsifier:** If any check fails to detect the condition it was designed for
- **verification level required:** UNIT_TEST
- **estimate:** 6 hours (implementation + testing)

## Open decisions

1. **Auto-invoke scope:** Should the close-check workflow auto-invoke only surface-only skills, or should it also surface `auto-act` skills with a confirmation gate?
   - Option A: Auto-invoke surface-only only (as designed)
   - Option B: Auto-invoke surface-only + prompt for auto-act skills
   - **Selection criterion:** Minimize operator friction while avoiding unintended side effects
   - **Leading option:** Option A — the classification matrix already exists; implement as designed

2. **Decomposition priority:** Which of the 4 Claude skill components should be ported first?
   - Option A: `claim-receipt-validation` (highest impact — catches the most common failure mode)
   - Option B: `pre-close-snapshot` (most mechanical — easiest to implement)
   - **Selection criterion:** Highest impact per effort
   - **Leading option:** Option A — claim-receipt-validation addresses the verification-before-completion gap directly

## Hard constraints

- Auto-invocation must not modify files or state (surface-only only)
- The close-check workflow must not break existing close behavior
- All new checks must have falsifiers

## Cross-reference couplings

- `P:/docs/handoffs/close-check-lifecycle-auto-chain-20260801/HANDOFF.md` → this handoff references it for the auto-invoke design
- `P:/docs/handoffs/claude-skill-decomposition-close-check-20260801/HANDOFF.md` → this handoff references it for the decomposition table
- `P:/docs/handoffs/verification-before-completion-20260801/HANDOFF.md` → the verification-before-completion decision affects which checks to port
- `P:/.grok/AGENTS.md` "Self-review before shipping advice" → the verification-before-completion principle is the behavioral foundation for claim-receipt-validation

## Other outstanding streams (not handed off)

- **skill-consolidation** — consolidation candidates identified but deferred, awaiting operator decision
- **tp-thinking-hats-enhancement** — `/tp` hat redesign discussed, not yet implemented
- **skill-lifecycle-architecture** — skill lifecycle architecture investigated, durable findings in wiki
- **file-link-mechanism** — file:/// link mechanism documented
- **www-skill-lifecycle-fix** — /www SKILL.md stale reference fixed
- **skill-path-migration** — stale references fixed after skill path migration

## Explicit non-goals

- Do NOT auto-invoke destructive skills (`/wiki`, `/handoff`, `/aar`)
- Do NOT implement the close-check auto-invoke chain in this handoff — only design and document
- Do NOT port Claude skill components in this handoff — only identify and prioritize them

## Resumption protocol

1. Read this handoff and the close-check-lifecycle-auto-chain handoff
2. Run `/close-check` to get the readiness report
3. If gaps are detected, implement the auto-invoke for surface-only skills (T2)
4. Port the claim-receipt-validation check from the Claude skill decomposition (T3, Option A)

## Suggested next invocation

`/go CC-01` — run `/close-check` and capture the readiness report.

## Last user message (verbatim)

> "Please use the handoff skill"

## Epistemic labels per claim

- "The `/close-check` command was invoked at the end of session 019fb937" — `[FACT]` (source: session transcript, last user message was `/handoff`)
- "The close-check workflow detects lifecycle-skill gaps" — `[FACT]` (source: close-check-lifecycle-auto-chain handoff from session 019f9a89)
- "The classification matrix identifies `/harvest` and `/friction` as safe to auto-invoke" — `[FACT]` (source: close-check-lifecycle-auto-chain handoff from session 019f9a89)
- "The readiness report has not been captured in a handoff from this session" — `[FACT]` (source: no handoff from session 019fb937 with close-check findings)
- "Option A (auto-invoke surface-only only) is the leading option" — `[INFERENCE]` (based on the existing classification matrix and the principle of least surprise)

## Changelog

| Date | Session | Action |
|------|---------|--------|
| 2026-08-02T05:00 | 019fb937... | created |
