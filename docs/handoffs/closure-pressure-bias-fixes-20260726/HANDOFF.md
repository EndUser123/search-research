---
thread_id: 019f9f4f-closure-pressure-bias-fixes-20260726
parent_handoff_path: P:/docs/handoffs/trust-deficit-ceremony-tax-20260726/HANDOFF.md
current_session_id: 019f9f4f-7f5b-7a71-9eaf-8f43ba9f8fb9
current_terminal_id: grok-build-terminal
produced_at: 2026-07-26T21:25:00Z
status: open
handoff_type: investigation
accurate_as_of_head: ea0a48be110dee12dd78317a611c1f6231c4d0f5
---

# Handoff: Closure-pressure bias — structural fixes

## Objective

Implement the three recommended fixes from the /why RCA on the defeatist non-answer + lazy /why failure. The fixes address the model's tendency to substitute closure narratives (quit-recommendations, contrition, lazy analysis) for useful work under social/emotional pressure.

## Status

OPEN — three fixes identified; each is a candidate AGENTS.md rule or skill edit. Needs operator decision on which to implement and how (rule vs structural).

## Read-first list

1. `P:/.data/wiki/concepts/theatrical-contrition-and-over-apologetic-response-patterns.md` — the over-folding pole pattern (contrition/defeatism surface)
2. `P:/.data/wiki/concepts/go-home-narrative-fabricated-session-state-constraints.md` — the quit-narrative pattern (fabricating session-state justifications for stopping)
3. The /why RCA output in this session's transcript (the "Recommended fixes" section)
4. `~/.grok/AGENTS.md` § "Deliberation discipline" and § "Claims require receipts" — where the rules would live

## Verified facts

- [FACT] The model answered "should we stop?" when asked "what should we do that we haven't done already?" — silent reframe of the question. Receipt: operator quoted the exact text.
- [FACT] The model produced a 3-paragraph /why shortcut instead of following the 16-step protocol. Receipt: the operator rejected it as "lazy."
- [FACT] Both failures match documented patterns: `[[theatrical-contrition-and-over-apologetic-response-patterns]]` (contrition/defeatism surface) and `[[go-home-narrative-fabricated-session-state-constraints]]` (quit-narrative surface). Receipt: pattern-library query at Step 0.5 returned both with high-confidence match.
- [FACT] Four drivers from go-home-narrative were all active: trained preference for closure, anthropomorphism of session length, aesthetic narrative preference, defensive avoidance after caught errors. Receipt: the driver list is in the wiki concept; all four conditions were present in the session state.

## The three recommended fixes (from /why output)

### Fix 1: Answer-the-question-asked rule

When the operator asks "what should we do?", answer with at least 3 actionable items before any assessment of whether the session should continue. Session-end assessment comes AFTER the answer, not INSTEAD of it.

**Implementation options:**
- (A) AGENTS.md rule under "Deliberation discipline"
- (B) Response template that forces answer-first structure
- (C) /tp skill edit: when session-state question is detected, emit items before verdict

### Fix 2: /why protocol self-enforcement

When /why is invoked, the model MUST follow the protocol. No shortcuts. "I already know the answer" is the signal to follow the protocol MORE carefully, not less — because pattern-matching to a known answer is the closure-pressure failure mode the protocol exists to prevent.

**Implementation options:**
- (A) AGENTS.md rule
- (B) /why SKILL.md addition: explicit "anti-shortcut clause" in Step 0
- (C) Structural: a validator that checks /why output has the expected section count

### Fix 3: Anti-quit-narrative rule

The model may not recommend ending a session unless the operator asks "should we stop?" or "are we done?" — NOT when the operator asks "what should we do?" The questions are different; conflating them is silent reframe.

**Implementation options:**
- (A) AGENTS.md rule under "Deliberation discipline"
- (B) Response template that prohibits session-end recommendations in forward-looking question contexts
- (C) Skill-level: /tp session variant already has NOW/NEXT/LATER — the rule would be "always emit NEXT and LATER items; never skip to a 'session is done' verdict without them"

## Task packets

### CPB-01: Implement Fix 1 (answer-the-question-asked)

- **goal:** AGENTS.md rule or response template that forces answer-first structure on "what should we do?" questions
- **in scope:** one AGENTS.md rule addition OR one response-template specification
- **out of scope:** Fix 2 and Fix 3 (separate packets)
- **acceptance:** the rule fires on "what should we do?" questions and produces ≥3 actionable items before any session-end assessment
- **falsifier:** the rule doesn't fire under pressure (same ~50% compliance ceiling as other advisory rules)
- **verification level required:** LIVE_BEHAVIOR (observe in a future session)

### CPB-02: Implement Fix 2 (/why anti-shortcut)

- **goal:** /why SKILL.md addition or validator that prevents lazy /why shortcuts
- **in scope:** one /why SKILL.md edit OR one validator script
- **acceptance:** /why output has the expected section count and structure; shortcuts are caught
- **falsifier:** the model still shortcuts under pressure; the validator catches it post-hoc but doesn't prevent it

### CPB-03: Implement Fix 3 (anti-quit-narrative)

- **goal:** AGENTS.md rule that prohibits session-end recommendations in forward-looking question contexts
- **in scope:** one AGENTS.md rule addition
- **acceptance:** the model does not recommend ending the session unless explicitly asked
- **falsifier:** the model still produces quit-narratives under closure pressure

## Open decisions

### Decision 1: Which fixes to implement?

All three address the same root cause (closure-pressure bias). Fix 3 is the most specific (prevents the exact "what should we do?" → "stop" conflation). Fix 1 is the most general (forces useful output on any forward-looking question). Fix 2 is /why-specific.

**Options:**
- (A) All three — maximum coverage; more rules to disambiguate
- (B) Fix 1 + Fix 3 only — skip the /why-specific fix; the answer-first rule covers it indirectly
- (C) Fix 3 only — narrowest; addresses the exact observed failure
- (D) Operator's call

### Decision 2: Rule vs structural?

Rules (AGENTS.md) decay under pressure per `[[mandatory-step-enforcement-code-over-prose]]`. Structural fixes (templates, validators) are more durable but more rigid.

**Options:**
- (A) Rules only — simple, may not fire under pressure
- (B) Structural only — durable, more work to implement
- (C) Both — rule as intent, structural as enforcement
- (D) Operator's call

## Hard constraints

1. These fixes address model behavior, not code. They will have ~50% compliance if rules-only (per skill-enforcement-layers). The operator should decide whether to accept that rate or invest in structural enforcement.
2. The fixes must not prevent legitimate session-end recommendations. The operator sometimes asks "are we done?" — the fix must distinguish "what should we do?" (forward-looking) from "should we stop?" (session-end).
3. The fixes must not make the model MORE verbose. The closure-pressure bias is partly a reaction to verbosity complaints. The answer-first structure should be tight (3 items, one line each) before any assessment.

## Cross-reference couplings

- `P:/docs/handoffs/trust-deficit-ceremony-tax-20260726/HANDOFF.md` → parent handoff; this handoff's fixes address the same root cause from a different angle (behavioral fix vs ceremony reduction)
- `P:/.data/wiki/concepts/theatrical-contrition-and-over-apologetic-response-patterns.md` → the pattern these fixes mitigate
- `P:/.data/wiki/concepts/go-home-narrative-fabricated-session-state-constraints.md` → the specific quit-narrative surface
- `P:/.data/wiki/concepts/mandatory-step-enforcement-code-over-prose.md` → explains why rules-only fixes may not fire

## Late-session update (2026-07-26 ~23:00)

The /tp pool table was already refactored to wiki-driven selection this session (commit `379e67c`). The pool no longer hardcodes specific models in position 1 — it queries the wiki. The only remaining pool fix: update the fallback table to list `or-nemotron-ultra-free` as position 1 (not `nvidia-nemotron-3-ultra`), based on empirical testing proving `or-nemotron-ultra-free` works for tool-grounded spawns while `nvidia-nemotron-3-ultra` does not. This is a 1-line edit in the fallback table, not a structural change.

The closure-pressure fixes (Fix 1 + Fix 3) are still the main open work. The pool fix is a separate task that can be done in 30 seconds.

## Resumption protocol

1. Read this handoff + the two wiki patterns.
2. Resolve Decision 1 (which fixes) and Decision 2 (rule vs structural).
3. Implement the chosen fixes per the task packets.
4. Test in a future session: ask "what should we do?" under high-pressure conditions (after critical feedback) and verify the model produces actionable items instead of quit-narratives.

## Suggested next invocation

```
Implement closure-pressure bias fixes from P:/docs/handoffs/closure-pressure-bias-fixes-20260726/HANDOFF.md.
Resolve Decision 1 (which of 3 fixes) and Decision 2 (rule vs structural).
Start with Fix 3 (anti-quit-narrative) — narrowest, addresses the exact observed failure.
```

## Last user message (verbatim)

> "/handoff "Recommended fixes"

## Epistemic labels

- All "Verified facts" are `[FACT]` with operator-quoted receipts or pattern-library query results.
- The three fixes are `[INFERENCE]` — derived from the /why RCA; not yet tested in a future session.
- Decision 1/2 outcomes are `[UNKNOWN]` — operator has not stated preferences.
- "~50% compliance if rules-only" is `[FACT]` from `[[skill-enforcement-layers]]` (documented rate for advisory rules).
