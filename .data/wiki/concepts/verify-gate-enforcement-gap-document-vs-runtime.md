---
title: "VERIFY gate enforcement gap: documentation vs. runtime invocation"
created: 2026-08-01
source: session-019f902a-621d-7711-9436-7c6003c57793
tags: [verify-gate, grok-verify, h6-pack, agentic-sdlc, enforcement-gap, prose-vs-invocation, session-2026-07-23]
summary: >
  The verify-before-done principle in our Agentic SDLC is documented across
  multiple skills (verification-before-completion, /grok-verify, /go's H6
  pack, /check) but in practice has no observable runtime enforcement on
  this host. Transcript evidence: 38 mentions of "grok-verify" in one
  transcript, all prose mentions inside /go's SKILL.md, none as actual
  skill invocations. The operator confirmed they do not invoke /grok-verify
  in practice. The chain that should make "done" claims costly is currently
  chain-of-advisory-references: each link is itself a skill document, so
  each link has the same ~50-77% Layer-1 compliance ceiling as any other
  prose instruction. The agentic-sdlc-skill-lifecycle-architecture.md
  recommendation to keep verify granularity holds as a *principle*, but
  the *implementation* has a structural gap that warrants either (a) a
  Stop-hook-based structural replacement, (b) honest labeling in AGENTS.md,
  or (c) deprecation of /grok-verify until instrumentation exists.
agent: grok
host: grok
cognitive_load: 3
verification: observed
sources:
  - /opt/grok/sessions/P:/019f902a-621d-7711-9436-7c6003c57793/chat_history.jsonl (session transcript; prompt_index 28-32 captures the operator pushback)
  - ~/.grok/skills/grok-verify/SKILL.md (the lightweight procedural skill)
  - ~/.grok/skills/go/SKILL.md lines 5, 95, 482-484 (H6 verify pack prose)
  - ~/.grok/skills/check/SKILL.md (heavy multi-concern verifier)
  - ~/.agents/skills/verification-before-completion/SKILL.md (always-on rule form)
  - wiki/concepts/agentic-sdlc-skill-lifecycle-architecture.md (existing principle capture)
  - wiki/concepts/rule-not-fired-vs-rule-doesnt-exist.md (related enforcement-layer rule)
  - wiki/concepts/skill-enforcement-layers.md (the ~50-77% Layer-1 ceiling)
relations:
  - target: wiki/concepts/agentic-sdlc-skill-lifecycle-architecture.md
    type: refines
  - target: wiki/concepts/rule-not-fired-vs-rule-doesnt-exist.md
    type: extends
  - target: wiki/concepts/skill-enforcement-layers.md
    type: related
  - target: wiki/concepts/llm-judgment-hooks.md
    type: related
  - target: wiki/concepts/operator-collaboration-style-and-leverage.md
    type: extends
  - target: wiki/concepts/skill-catalog-scope-inconsistency-causes-cascading-read-failures.md
    type: related
  - target: wiki/concepts/tp-hat-selection-gate-content-driven-hat-choice.md
    type: related
---

# VERIFY gate enforcement gap: documentation vs. runtime invocation

## Decision context

**Why this matters:** The agentic-sdlc-skill-lifecycle-architecture concept recommends a 6-layer verify hierarchy (grok-verify inline gate + /check + /review + /refactor + Stop hooks + /aar retrospective) as the principled response to Carnegie Mellon data showing agents cause +30% code warnings and +41% complexity. The recommendation stands as design. **But during a session examining the chain, the operator revealed that the rule documented as the inline first layer - "Execute grok-verify" - does not actually fire.** The /go SKILL.md says "Execute grok-verify" at line 484, but /go is itself a prose skill document; it cannot structurally invoke grok-verify. The chain dissolves into prose-from-prose-from-prose.

**The specific evidence:** The operator said "we never use grok-verify" (prompt_index 28). Reading this as plain language: nobody invokes it. The assistant at first inflated it to "it never fires" - a stronger, double-loaded claim conflating operator behavior with model behavior. The operator pushed back ("'but you're telling me it never actually fires.' that's not what I said."), then asked where the evidence would be. We then grepped 20 transcripts: the highest-hit transcript has 38 mentions of "grok-verify", all of which are prose references inside /go's SKILL.md (which the model reads), not skill invocations (which would appear as `{"type": "user", "content": "/grok-verify ..."}` patterns or as `read_file "~/.grok/skills/grok-verify/SKILL.md"` calls triggered by /go's instructions).

**What this changes:** the VERIFY phase in our SDLC has a structural gap between the *documented* and *running* layers. The principle is right, but the implementation does not match the principle. Until instrumentation is added (Stop hooks or equivalent), the verify-before-done principle is ceremonial here. The agentic-sdlc-skill-lifecycle-architecture.md entry should not be removed - it correctly identifies the *why* and the *what* - but the implementation gap is a separate finding that future sessions need to discover quickly.

## Key findings

### 1. The chain is prose-from-prose-from-prose

| Layer | Form | Actual invocation path |
|-------|------|------------------------|
| `verification-before-completion` (superpowers) | Always-on rule | Model reads SKILL.md on demand; ~50-77% Layer-1 compliance per [[skill-enforcement-layers]] |
| `/grok-verify` (on-demand skill) | Procedural skill | Operator never invokes. Possibly loaded during /go runs as prose, but no transcript evidence of structured invocation. |
| `/check` (slash-invoked) | Heavy session verifier | Only when operator types `/check`. Auto-escalates from /go... but only after a `done` claim has already been made. |
| H6 verify pack inside `/go` | Prose instruction | "/go" loads its SKILL.md (which contains "Execute grok-verify"), but loading prose isn't invoking another skill. The model may or may not follow Step 3. |
| Stop hooks (`StopHook_unverified_stance`, `Stop_fake_done_detector`) | Structural | Path exists; firing is `[UNKNOWN]` at time of this writing. **This is the only candidate for actual runtime enforcement.** |

The chain looks defended on paper. In practice every layer except possibly the Stop hooks is advisory.

### 2. Transcript evidence is dispositive

A scan of 20 recent transcripts for the substring "grok-verify" returned 38 hits in one transcript and 1-6 hits per transcript in 6 others. Sampling these hits: every single one was the model *reading /go's SKILL.md* or *narrating H6 phase announcements*, not invoking `/grok-verify`. There is no transcript-level evidence of /grok-verify firing under its own name.

This is what receipt-bearing evidence looks like for a negative claim. Without running this grep, the assistant's "it never fires" claim would have been another fabrication; with it, the gap is observable.

### 3. The operator's "we never use grok-verify" is a plain-language statement

The assistant initially re-read this as "it never fires." That's a stronger claim that conflates operator behavior with model invocation paths. The operator's correction:

> "'but you're telling me it never actually fires.' that's not what I said."

This is the same inflation pattern documented in [[trust-over-believability]] and [[narrative-as-signal]] applied to user statements: take the safest/cautious reading, then inflate it into a stronger claim. The assistant added false confidence to a well-grounded observation.

### 4. /grok-verify may still have a role

The skill is useful *as a procedural reference* - future skill authors can read it as a 6-step checklist - even if no one invokes it today. The role is "documentation of the principle" not "active enforcement." Honest labeling would distinguish these; current AGENTS.md does not.

## What this means for our workspace

1. **Add a structural enforce layer (Stop hook with LLM judge) or stop documenting /grok-verify as if it fires.** The [[llm-judgment-hooks]] concept already proposes the structural fix (Layer 1 regex detects "done/fixed/verified/shipped" claims → Layer 2 LLM judge classifies block/allow/fail-open). Until that hook is built and proven to fire, the verify-before-done principle has no working implementation. Either ship the hook, or remove the prose reference to "Execute grok-verify" from /go's H6 pack.

2. **Update [[agentic-sdlc-skill-lifecycle-architecture.md]] with a "compliance status" column.** Add a column to the verify-hierarchy table noting which layers are *documented* vs *actually invoked*. This makes the gap visible without requiring future sessions to rediscover it.

3. **Treat any future "instrumented verification" skill as load-bearing.** If we ship a Stop hook or similar mechanism that observes done-claims and gates them, that's load-bearing infrastructure. It deserves its own wiki concept (per [[concept-priority-tier-rules]]) and its own session-test before claiming PROVEN status. Without that, the principle remains aspirational.

4. **Don't recommend `/grok-verify` in user-facing material without empirical observation.** When recommending a verify mechanism in handoffs or plans, the recommendation should cite a transcript where it was observed firing (a `[FACT]` with a receipt), not a SKILL.md that says it should.

## Receipts

- `C:/Users/brsth/.grok/sessions/P:/019f902a-621d-7711-9436-7c6003c57793/chat_history.jsonl` - prompt_index 28-32 contain the operator's "we never use grok-verify" pushback sequence; transcript reads show 38 hits of "grok-verify" in one transcript, all prose mentions, no invocations
- `~/.grok/skills/go/SKILL.md` line 95 (Step 0.5 loading instructions) and lines 482-484 ("H6 - Verify Pack ... Execute grok-verify. Non-trivial writes also check-work. No PASS without") confirm /go documents but does not structurally call grok-verify
- `~/.grok/skills/grok-verify/SKILL.md` confirms the skill exists with a 6-step procedure
- `~/.grok/skills/check/SKILL.md` confirms /check is a separate heavy session verifier, auto-escalating from /review
- `~/.agents/skills/verification-before-completion/SKILL.md` (matched file size 4201) is the always-on rule form
- `P:/.data/wiki/concepts/agentic-sdlc-skill-lifecycle-architecture.md` is the prior concept asserting verify granularity is the principled response
- `P:/.data/wiki/concepts/rule-not-fired-vs-rule-doesnt-exist.md` documents the broader pattern of documented-but-unenforced rules

## Related

- [[agentic-sdlc-skill-lifecycle-architecture]] - the existing architecture concept this refines (now showing the implementation gap)
- [[rule-not-fired-vs-rule-doesnt-exist]] - the broader pattern about documented-but-unfiring enforcement
- [[skill-enforcement-layers]] - the ~50-77% Layer-1 compliance ceiling that bounds all prose rules
- [[llm-judgment-hooks]] - proposed structural replacement (Layer 1 regex + Layer 2 LLM judge)
- [[operator-collaboration-style-and-leverage]] - the operator pattern that surfaced the gap (Sample R2: "manual narration is faster than reading status file")

## Auto-related

- [[skill-graph]]
- [[skill-catalog]]
- [[code-orchestrates-model-judges-skill-scale]]
- [[intg2-resolved-gate-state-set-needs-llm-check]]
- [[lexical-vs-semantic-verification-gap]]

## Falsifier

This concept is wrong if:
- A transcript exists where /grok-verify fires as an observable skill invocation (not prose mention). Run the same 20-transcript grep but for `{"type":"user","content":[{"type":"text","text":"/grok-verify` or similar structural patterns and observe invocation.
- A Stop hook is built, instrumented, and observed firing on actual `done`/`fixed`/`verified` claims - then the verify gate has working structural enforcement, and the gap closes.
- The chain is replaced by a real mechanism (e.g., a tool call to a verification subagent that the model cannot skip). Then the prose-from-prose concern is moot.
- /grok-verify becomes a callable tool (not a skill document). Same as above.

This concept is *also* wrong if: the operator's statement "we never use grok-verify" is itself not meant literally, and they do invoke it in sessions this evidence didn't reach. The falsifier would be: an instrumented session showing /grok-verify invoked under direct operator command.

## What this means for our workspace (recap)

The verify-before-done principle is right; the implementation has a gap. Closing the gap requires either (a) a structural mechanism (Stop hook or callable tool), (b) honest labeling that distinguishes documented-from-active enforcement, or (c) deprecation of /grok-verify until instrumentation exists. Without one of these, every "done" claim in this fleet is one Step-3 interpretation away from succeeding unverified.
