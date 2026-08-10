---
title: "Closure-pressure assumes the framing is right: two surface forms, one governing assumption"
created: 2026-08-09
source: session-2026-08-09 (AAR tacit gap #1 + /insight interaction friction)
tags: [closure-pressure, framing-failure, recommendation-discipline, evidence-discipline, chronic-pattern, transferable-pattern, hook-candidate]
summary: >
  Under session pressure, the agent defaults to framings that close the conversation rather than
  framings that commit to the best answer. Two surface forms recur across 4+ sessions: (1) trusting
  prior-session entries as current fact without re-probing, (2) presenting options without a
  recommended action. Both violate existing AGENTS.md rules. Both share one governing assumption:
  "my framing is probably right and doesn't need to commit." Prose rules don't fire under pressure;
  the fix is structural (output validator or hook).
agent: grok
host: grok
cognitive_load: 2
verification: multi-source-verified
confidence: 0.85
half_life_days: 180
last_verified: 2026-08-09
relations:
  - target: wiki/concepts/reactive-pattern-matching-and-closure-pressure.md
    type: refines
  - target: wiki/concepts/prior-session-fact-vs-this-session-fact-pattern.md
    type: extends
  - target: wiki/concepts/narrative-as-signal.md
    type: extends
  - target: wiki/concepts/theatrical-contrition-and-over-apologetic-response-patterns.md
    type: related
---

# Closure-pressure assumes the framing is right: two surface forms, one governing assumption

## Decision context

Session 2026-08-09 produced two operator pushbacks that looked like different failures but share a single root cause:

1. **Evidence-discipline failure:** the agent cited prior-session tool-fallbacks entries as current state without re-probing. Operator pushback: "you don't know they won't work unless you try them with PI." PI probes disconfirmed 1 of 3 claims.

2. **Recommendation-discipline failure:** the agent presented `/risk` output with options but no recommendation, using an invented verdict ("PROCEED WITH CAVEATS") not in the skill's vocabulary. Operator pushback: "where's your recommendation? Did you present a false choice?"

Both failures violate existing AGENTS.md rules:
- "Claims require receipts; narrative sufficiency is not verification" (evidence discipline)
- "Recommendations: present alternatives only when there is genuine uncertainty... When the path is clear, recommend ONE solution" (recommendation discipline)

The rules exist. They didn't fire under closure pressure.

## The governing assumption

The agent operates under an unstated assumption: **"my current framing is probably right and doesn't need to commit."** This assumption is adaptive when the framing IS right (saves deliberation time) but maladaptive when it's wrong (prevents the agent from noticing its own error).

Under session pressure (long session, multiple pivots, cognitive load), the assumption shifts from "probably right" to "act as if right" — the agent stops checking its own framing and defaults to outputs that close the conversation:
- Trusting prior work without re-verifying (closes the evidence question)
- Offering options without recommending (closes the decision question)
- Inventing hybrid verdicts (closes the verdict question without committing)

## Why prose rules don't prevent this

The workspace has extensive prose rules against both surface forms. The rules are long, detailed, and cite reference incidents. They don't fire under closure pressure because:

1. **Length:** the rules are buried in a 5000+ line AGENTS.md. Under pressure, the agent's attention narrows to the immediate task, not the rule catalog.
2. **Behavioral, not structural:** prose rules require the agent to choose to follow them. Under pressure, the agent optimizes for closing the turn, not for checking compliance.
3. **No real-time feedback:** the rules fire post-hoc (operator catches the error) rather than pre-emptively (hook blocks the output before the operator sees it).

This is the same structural-vs-behavioral distinction documented in [[evidence-first-default-and-needless-confirmation]]: prose rules have a ~50% compliance ceiling under session pressure; structural fixes (hooks, validators, schemas) achieve 75-88%.

## The structural fix

Two candidate interventions:

### Option A: Output validator (Stop hook)

A Stop hook that scans `/risk`, `/tp`, and `/design` outputs for:
1. **Verdict-vocabulary compliance:** the verdict token matches one of the skill's documented values. "PROCEED WITH CAVEATS" → blocked (not in `/risk` vocabulary); "FIX FIRST" → allowed.
2. **Recommendation presence:** if the output contains ≥3 options, it must contain at least one sentence matching the recommendation pattern (`I recommend | do X first | the answer is`).

Pros: blocks before the operator sees the error. Cons: false-positive risk on legitimate nuanced verdicts.

### Option B: EGDP output template

An EGDP (Evidence-Guided Debiasing Prompting) template that structurally requires a recommendation field before the receipt field. The structural property: the recommendation is required in the wire format, not optional.

Pros: no hook complexity. Cons: only works for outputs that use the EGDP template; doesn't catch mid-conversation framing drift.

### Recommended: Option A for now (highest detection coverage)

The hook covers more surface area than the template. False positives can be tuned via a `[JUSTIFIED_VARIANCE]` escape hatch.

## What this means for our workspace

1. **Two rules, one assumption, one fix.** Don't write more prose rules. Ship the hook.
2. **The pattern is chronic, not acute.** 4+ sessions. The operator is the current enforcement mechanism; that's not scalable.
3. **The closure-pressure framing applies beyond these two surface forms.** Any future skill output that should commit to an answer but hedges is a candidate instance.

## Falsifier

This finding is wrong if:

- **A review of 20 prior sessions shows <5% verdict-vocabulary violation rate.** The pattern would be rarer than this session suggests; the hook isn't worth the complexity.
- **The AGENTS.md rules fire reliably after a different intervention** (e.g., EGDP system-prompt change, context-engineering adjustment). The hook would be redundant.
- **The hook's false positive rate exceeds 20%** on legitimate outputs. Too noisy to ship.
- **The two surface forms turn out to have different root causes** (not the same governing assumption). If evidence-discipline failures stem from a different mechanism than recommendation-discipline failures, the unifying concept is wrong.

## Receipts

- **Session 2026-08-09 transcript:** operator pushback #1 ("you don't know they won't work unless you try with PI") at the `/www` turn; operator pushback #2 ("where's your recommendation? Did you present a false choice?") at the `/risk` response turn.
- **AAR report:** `P:\.artifacts\grok-aar\console_console_6e4287c5-bc0f-4955-823c-427b\20260809-143000\aar-report.md` § Headline lessons L1 (OBSERVED confidence, GENERAL scope).
- **`~/.grok/AGENTS.md` § "Recommendations":** the no-false-choices rule + EGDP template mandate.
- **`~/.grok/AGENTS.md` § "Claims require receipts":** the evidence-discipline rule.
- **Handoff:** `P:/docs/handoffs/verdict-vocabulary-hook-20260809/HANDOFF.md` — the structural fix workstream.

## Sources

- AAR session 2026-08-09 headline lesson L1
- `/insight` session 2026-08-09 interaction friction finding (closure-pressure, 2× this session)
- [[prior-session-fact-vs-this-session-fact-pattern]] — the evidence-discipline surface form (written same session)
- [[narrative-as-signal]] — the broader pattern of plausible narrative substituting for evidence
- [[evidence-first-default-and-needless-confirmation]] — the 50% prose-rule compliance ceiling research

## Auto-related

- [[playwright-connectovercdp-not-ruled-out]]
- [[skill-catalog]]
- [[premature-closure-narrative-sufficiency-external-approaches]]
- [[externalized-verification-over-intrinsic-self-correction]]
- [[premature-synthesis-without-reading-existing-capability]]

