---
thread_id: challenge-skill-design-20260727
parent_handoff_path: none
current_session_id: 019fa5a1-0446-7e02-9766-bd2457ee58c3
current_terminal_id: grok-build-primary
produced_at: 2026-07-27T17:30:00Z
status: open
handoff_type: design
accurate_as_of_head: ac63013e8a17b30995e22f887142c2046f873659
---

# Handoff — /challenge skill: default-fire assumption-auditing at claim/verdict gates

## Objective

Design and build a `/challenge` skill that fires assumption-audit techniques
MECHANICALLY at specific decision points, rather than relying on the agent to
remember to invoke /tp or /red-team. This is the structural fix for the
"techniques exist but don't fire under closure pressure" problem documented in
the wiki concept `assumption-auditing-and-unknown-unknown-discovery.md`.

## Why this exists

Session 019fa5a1 exhibited three failures where existing techniques (/tp,
/wargame, AGENTS.md "Could You Be Wrong?" rule) existed but didn't fire:

1. **CooperBench overgeneralization:** cited "solo beats fleet ~2×" without
   checking external validity (benchmark tested interdependent tasks, not our
   independent streams)
2. **"PROVEN" verdict on standalone module:** no adversarial pass before
   declaring enforcement proven
3. **"Zero regressions" without baseline:** assumed the baseline rather than
   running it

Each would have been caught by a 30-second inline check at the claim point.
The workspace has the techniques; it lacks default-firing.

## Proposed design (for operator decision)

### Trigger points (fire mechanically)

| Decision point | Technique | Question |
|---|---|---|
| Before citing an external study/benchmark | External-validity audit | "What population was tested? Does my context match on key axes?" |
| Before declaring "PROVEN" / "done" / "verified" | Adversarial framing + premortem | "Imagine this is wrong — name 3 reasons why" |
| Before claiming "zero regressions" / "no failures" | Base-rate + reference-class | "What is the baseline? Did I run it?" |
| Before recommending an approach | Steelman | "What is the strongest version of the rejected alternative?" |

### Architecture options

**Option A: Standalone skill (`/challenge <claim>`)** — the operator or agent
invokes it before shipping a verdict. Pro: explicit, auditable. Con: still
opt-in.

**Option B: Inline gate (fires automatically in /go, /check, /review)** —
the claim-gate fires when the agent emits specific verdict tokens ("PROVEN",
"zero regressions", "done"). Pro: default-fire, can't be skipped. Con: adds
latency to every verdict; may fire when not needed.

**Option C: Hybrid** — inline gate for the 3 highest-signal triggers
(external citation, verdict claim, regression claim); `/challenge` skill for
on-demand deeper audit. Pro: covers both default and explicit cases.

### Relationship to existing skills

- `/tp` is the deep version (fresh subagent, two-lens, 10min). `/challenge`
  is the 30-second inline version that fires BEFORE deciding whether to
  escalate to /tp.
- `/red-team` is referenced but doesn't exist (see wiki concept). `/challenge`
  could absorb the /red-team contract or /red-team could be built separately.
- `/wargame` is the move-schema version for hard-to-reverse plans. `/challenge`
  is the claim-schema version for verdicts and citations.

## Read-first list

1. `P:/.data/wiki/concepts/assumption-auditing-and-unknown-unknown-discovery.md` — the research
2. `P:/.data/wiki/concepts/reactive-pattern-matching-and-closure-pressure.md` — why opt-in fails
3. `P:/.data/wiki/concepts/mandatory-step-enforcement-code-over-prose.md` — the enforcement principle
4. `~/.grok/skills/tp/SKILL.md` — the deep version this would be the fast version of
5. `~/.grok/AGENTS.md` § "Could You Be Wrong?" — the prose rule this would mechanize

## Open questions

1. Should the gate fire in the agent's own response (prompt-time) or as a
   hook (post-response)? Prompt-time is stronger but adds latency to every turn.
2. What are the exact trigger tokens? ("PROVEN", "verified", "done", "zero
   regressions", "no failures", "works", "confirmed"...)
3. Should /red-team be built as a separate skill, or should /challenge absorb
   its advertised contract?
4. Is 30 seconds per gate acceptable, or does it need to be faster?

## Suggested next

Design the skill via `/design` or `/tp` on the proposed architecture. The
research is complete; the remaining work is skill-author decision (trigger
mechanism, token set, integration points).

---

## Revision 1 — 2026-07-27T22:30:00Z (session 019fa5a1)

**Trigger:** auto-update — new wiki concept adds a trigger point the original design didn't include.

### New trigger point: enforcement-code verdict gate

The wiki concept `P:/.data/wiki/concepts/maker-checker-required-for-enforcement-work.md` (written this session) documents the three-role conflict (implementer + tester + threat actor) for agent-authored enforcement code. Empirically confirmed by INTG-1 (forgeable AAR receipts) and INTG-2 (validator ignores gate content) in the close-authority review.

**Added trigger for the /challenge design:**

| Decision point | Technique | Question |
|---|---|---|
| Before declaring enforcement/security code "PROVEN" | Independent verification gate | "Did an external reviewer (not the implementer) verify this? If not, the verdict is COMPONENT_PROVEN at best." |

This is the claim-schema analog of `/wargame`'s move-schema. It complements the original 4 trigger points (external citation, verdict claim, regression claim, approach recommendation) by adding the enforcement-specific case where the maker-checker violation is structurally guaranteed.

### Related: AGENTS.md rule already shipped

The self-verification prohibition rule (AGENTS.md, commits dd4b2c4 + 71304e3) already enforces this at the prose level for reversibility ≤1.5. The /challenge skill would mechanize the same principle at the verdict-emission point — firing the independent-verification gate before the verdict token is emitted, not after.

### Status update

Design unchanged. The new trigger point is additive to the original architecture options (A/B/C). Open questions 1-4 remain the same.
