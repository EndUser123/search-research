---
title: "Reviewer-classification gate — structural enforcement for reviewer-as-hypothesis"
status: OPEN
created: 2026-08-08
last_updated_at: 2026-08-08T23:59:00Z
assignee: grok
session_origin: 019fdf3d-a0bd-7062-abc4-24dcf064ae49
---

# Reviewer-classification gate: structural enforcement for reviewer-as-hypothesis

## Context

The reviewer-as-hypothesis rule exists in AGENTS.md and `/tp` protocol.md.
It was violated 9 times in session 019fdf3d — the implementing LLM adopted
every external-LLM recommendation without classifying any as
CONFIRMED/PARTIAL/REJECTED. This proves prose enforcement is insufficient.

The psychological-narrative gate (`Stop_psychological_narrative_gate.py`)
addresses one symptom (psychological confession without process-failure
translation). The full enforcement requires a classification artifact.

## The invariant to enforce

> No correction may be adopted merely because the reviewer sounds persuasive.
> Before changing a consequential conclusion, decompose the critique into
> individual claims, identify evidence capable of resolving each, inspect
> that evidence, and classify as CONFIRMED / PARTIAL / REJECTED / UNKNOWN.

## Proposed mechanism (same pattern as decision-contract gate)

### Artifact: `<review-classification>`

When processing external criticism (operator-pasted LLM critique, code review,
peer review), emit:

```xml
<review-classification>
review_source: "<who/what provided the critique>"
points:
  - id: 1
    claim: "<what the reviewer asserted>"
    classification: CONFIRMED | PARTIAL | REJECTED | UNKNOWN
    receipt: "<tool call, file citation, or command output>"
    action: adopt | revise | reject | defer
  - id: 2
    ...
</review-classification>
```

### Validator

Check that:
1. Every substantive critique point has a classification
2. Each classification has a receipt (tool call, file citation, command output)
3. No point is adopted without classification
4. REJECTED points include a reason

### Hook

`Stop_reviewer_classification_gate.py` — detects when the response is
processing external review (signals: "the reviewer", "the other LLM",
"the critique", pasted critique patterns) and requires the
`<review-classification>` artifact.

## Scope decision: NOT built in session 019fdf3d

Session 019fdf3d has been compacted once and is very long. Building a
new gate subsystem under context pressure risks the same bypass-surface
defects that the decision-contract gate required a remediation round to
fix. Fresh-session build.

The psychological-narrative gate IS built in this session because it is
narrower (one detection pattern, one check) and less likely to have
bypass-surface defects.

## Files

- AGENTS.md rule: "Reviewer feedback is a hypothesis" (line ~743)
- AGENTS.md rule: "Psychological narratives are not root-cause endpoints" (line ~755)
- `/tp` protocol.md Step A: reviewer-as-hypothesis section
- Psychological-narrative hook: `~/.grok/hooks/Stop_psychological_narrative_gate.py`
- Wiki: `[[psychological-narrative-vs-observable-process-failure]]`
- Wiki: `[[correction-response-discipline-anti-binary-swing]]` (existing)
