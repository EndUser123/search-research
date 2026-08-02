---
thread_id: verification-before-completion-20260801
parent_handoff_path: none
current_session_id: 019f902a-621d-7711-9436-7c6003c57793
current_terminal_id: grok-build-019f902a
produced_at: 2026-08-01T21:15:00Z
status: open
handoff_type: investigation
accurate_as_of_head: f47a7540ef5b11a5eb6fb08c61fe60177ed30f4e
---

# Verification-before-completion — Where does it belong?

## Objective

Determine whether verification-before-completion should be rolled into `/check` or remain a separate behavioral rule, and document the decision with a concrete implementation plan.

## Status

OPEN — analysis complete from session 019f902a, no implementation yet.

## Producing context

- Session: `019f902a-621d-7711-9436-7c6003c57793` (2026-07-23 → 2026-08-01)
- Terminal: Grok Build on Windows 11
- Model: glm-5.2 (session default)

## Read-first list

1. `P:/.grok/skills/check/SKILL.md` — current `/check` skill definition
2. `P:/.grok/skills/tp/SKILL.md` — `/tp` skill (critical friend lens)
3. `P:/.data/wiki/concepts/verification-before-completion-principle.md` — wiki concept for the principle
4. `P:/.data/wiki/concepts/agentic-sdlc-skill-lifecycle-architecture.md` — lifecycle context
5. `P:/docs/handoffs/session-observations-20260723/HANDOFF.md` — session observations from this session

## Verified facts

- [FACT] The `/check` skill currently does multi-concern session verification with PASS/FAIL verdict (source: `P:/.grok/skills/check/SKILL.md`).
- [FACT] The verification-before-completion principle is an always-on behavioral rule loaded as part of the system prompt, not invoked as a slash command (source: `~/.grok/AGENTS.md`, "Self-review before shipping advice" section).
- [FACT] Session 019f902a discussed whether verification-before-completion can be rolled into `/check` or should go somewhere else (turns 319, 322, 330, 332, 335).
- [FACT] The operator pushed back on the claim that `/go` invokes `/grok-verify`, asking for evidence (turn 332). The evidence was not provided — this remains `[INFERENCE]` until verified.
- [FACT] The `/check` skill currently does NOT invoke verification-before-completion as a sub-step (source: `P:/.grok/skills/check/SKILL.md`).

## Current state

- The verification-before-completion principle exists as a behavioral rule in `~/.grok/AGENTS.md` ("Self-review before shipping advice").
- It is NOT a standalone skill — it is loaded as an always-on instruction.
- The question of whether it should be a `/check` sub-step or remain a behavioral rule was discussed but not resolved in this session.
- The `/tp` critical friend review (turns 527-532) caught framing issues in the `/tp` redesign but did not address the verification-before-completion placement question.

## Task packets

### T1: Determine placement of verification-before-completion

- **id:** VBC-01
- **goal:** Decide whether verification-before-completion rolls into `/check` or stays as a behavioral rule
- **in scope:** The `/check` skill's workflow and the verification-before-completion principle
- **out of scope:** Changes to `/tp`, `/review`, `/close`, or other skills
- **files / anchors:** `P:/.grok/skills/check/SKILL.md`, `~/.grok/AGENTS.md` "Self-review before shipping advice" section
- **acceptance:** A decision is documented with rationale; if `/check` is chosen, the SKILL.md is updated to include the verification step
- **falsifier:** If `/check` already includes verification-before-completion and the claim that it doesn't is wrong, the handoff is obsolete
- **verification level required:** STATIC_INSPECTION
- **estimate:** 1 hour (decision + possible SKILL.md edit)

### T2: If rolling into `/check`, add the verification step

- **id:** VBC-02
- **goal:** Add verification-before-completion as a sub-step in `/check` SKILL.md
- **in scope:** The `/check` skill workflow
- **out of scope:** Other skills, wiki concepts, handoffs
- **files / anchors:** `P:/.grok/skills/check/SKILL.md`
- **acceptance:** The `/check` skill includes a verification-before-completion step; running `/check` on a proposal catches claims without receipts
- **falsifier:** If the step doesn't catch claims without receipts when tested
- **verification level required:** UNIT_TEST
- **estimate:** 2 hours (implementation + test)

## Open decisions

1. **Placement:** Should verification-before-completion be a `/check` sub-step or remain an always-on behavioral rule?
   - Option A: Roll into `/check` — makes it explicit, testable, and part of the formal verification gate
   - Option B: Keep as behavioral rule — simpler, no skill modification, works across all phases
   - Option C: New `/verify` skill — dedicated skill for verification-before-completion
   - **Selection criterion:** Which option requires the least maintenance overhead while catching the most unverified claims?
   - **Leading option:** Option A (roll into `/check`) — the principle already fires as a behavioral rule; making it explicit in `/check` adds testability without changing the operator's workflow

## Hard constraints

- The verification-before-completion principle must catch claims without receipts — this is non-negotiable
- Any change to `/check` must not break existing PASS/FAIL behavior
- The handoff must be verifiable: a fresh session must be able to act on it without re-deriving the decision

## Cross-reference couplings

- `P:/.grok/skills/check/SKILL.md` → if verification-before-completion is added as a sub-step, all existing `/check` tests must still pass
- `~/.grok/AGENTS.md` "Self-review before shipping advice" → if `/check` absorbs the principle, the AGENTS.md rule becomes redundant but should not be deleted (safety net)
- `P:/.data/wiki/concepts/verification-before-completion-principle.md` → this wiki concept documents the principle; it should reference the final placement decision

## Other outstanding streams (not handed off)

- **skill-consolidation** — consolidation candidates identified but deferred, awaiting operator decision
- **tp-thinking-hats-enhancement** — `/tp` hat redesign discussed, not yet implemented
- **close-check-lifecycle** — close-check auto-invoke design identified, implementation deferred (see `close-check-lifecycle-auto-chain-20260801` handoff from session 019f9a89)
- **claude-skill-decomposition** — reusable verification components from Claude skills identified for close-check (see `claude-skill-decomposition-close-check-20260801` handoff from session 019fb933)

## Explicit non-goals

- Do NOT modify `/tp`, `/review`, `/close`, or other skills in this handoff
- Do NOT create a new `/verify` skill unless the decision explicitly calls for it
- Do NOT auto-invoke any skills as part of this handoff

## Resumption protocol

1. Read this handoff and the `/check` SKILL.md
2. Decide on placement (Option A, B, or C)
3. If Option A: edit `/check` SKILL.md to add verification-before-completion as a sub-step
4. Run `/check` on the handoff itself to verify the new step works
5. Update the wiki concept `verification-before-completion-principle.md` with the decision

## Suggested next invocation

`/go VBC-01` — decide on placement of verification-before-completion, then implement if Option A is chosen.

## Last user message (verbatim)

> "where does verification-before-completion go?"

## Epistemic labels per claim

- "The `/check` skill currently does multi-concern session verification" — `[FACT]` (source: `P:/.grok/skills/check/SKILL.md`)
- "Verification-before-completion is an always-on behavioral rule" — `[FACT]` (source: `~/.grok/AGENTS.md`)
- "The `/check` skill does NOT invoke verification-before-completion as a sub-step" — `[INFERENCE]` (source: reading `/check` SKILL.md; not explicitly stated as absent, but the workflow does not include it)
- "Option A (roll into `/check`) is the leading option" — `[INFERENCE]` (based on the principle already firing as a behavioral rule; making it explicit adds testability)
