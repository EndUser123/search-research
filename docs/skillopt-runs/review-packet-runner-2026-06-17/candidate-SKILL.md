---
name: review-packet-runner
description: Turn review, assessment, critique, validation, gap-analysis, and second-opinion requests into evidence-grounded review packets instead of narrative answers. Use when the user asks Codex to review or assess code, plans, docs, PRs, implementation summaries, transcript excerpts, or another model's feedback and wants a grounded verdict with severity, confidence, and next actions.
---

# Review Packet Runner

Convert free-form review requests into structured evidence packets. Separate what is proven from what is inferred, verify important claims against available sources, and turn critique into a scoped action queue.

## Declared Skill Type

This is a review skill. Use `rubric.yaml` as the review rubric overlay when benchmarking, validating, or optimizing this skill.

## Optimization Metadata

- skill_class: review
- rubric: rubric.yaml
- optimize_with: skillopt
- evidence_sources:
  - Codex session transcripts
  - human review feedback
  - held-out review prompts

## When to Use

Use this skill when all of the following are true:

- The user is asking to review, assess, critique, validate, sanity-check, or give feedback on something.
- The target is specific: code, a PR, a plan, a design doc, a transcript excerpt, an LLM response, or another model's feedback.
- The user cares about correctness, risk, gaps, or next steps, not just a summary or restatement.

Do not use this skill when:

- The user only wants a summary, rewrite, brainstorming, or idea generation.
- There is no concrete artifact or feedback to review.
- The user explicitly asks for implementation changes without any request for review.

## Review Modes

Determine the review mode up front and state it in the packet:

- Artifact review: review the artifact itself, such as code, plan, doc, PR, or transcript excerpt.
- Second-opinion review: review another model's feedback, critique, summary, or gaps-and-opportunities analysis.
- Proposal review: review a plan or proposal against stated goals, constraints, and risks.

Adjust emphasis based on the mode, but always follow the same evidence discipline.

## Operating Rules

1. Identify the target artifact and review lens.
2. Inspect the actual artifact before judging it when local access is available.
3. Extract concrete claims from the artifact, user prompt, and any third-party or model feedback.
4. Classify important claims as fact, inference, unsupported, contradicted, or open question.
5. Prioritize verification of claims that affect correctness, safety, security, user harm, major cost, or the verdict.
6. Use concrete evidence such as file paths, line numbers, command output, test results, log snippets, transcript locations, or specific doc sections.
7. Do not agree with critiques until key claims have been checked against evidence.
8. Never convert thin or mixed evidence into confident prose.
9. Separate severity from confidence: severity is potential impact if real; confidence is evidence strength.
10. Keep recommendations tied to the specific artifact and review lens.
11. If the user asks for a verdict, provide it after the evidence packet.

## Reviewing Another Model's Feedback

Treat every statement from another model or tool as a claim to check, not as ground truth.

Make clear which claims were verified, which were contradicted, and which remain unverified. Call out hallucinated, overstated, or under-justified claims explicitly.

## Evidence Standard

Prefer verifiable, local evidence:

- Source code
- Configuration
- Tests and their results
- Logs
- Docs in the repo
- Concrete transcript spans

When evidence is unavailable, state:

- What evidence is missing
- What was checked instead
- How the missing evidence limits confidence

Use "insufficient evidence to conclude" when that is the accurate answer.

## Output Shape

Use this structure unless the user requests a different format. Keep content concise but specific.

```markdown
## Review Packet

### Target
- Artifact:
- Review mode: (artifact / second-opinion / proposal)
- Review lens:
- Evidence inspected:

### Findings
| Severity | Finding | Evidence | Risk | Confidence | Action |
|---|---|---|---|---|---|

### Facts
- ...

### Inferences
- ...

### Unsupported Or Contradicted Claims
- ...

### Open Questions
- ...

### Verdict
- ...

### Recommended Next Actions
1. ...
2. ...
```

## Severity Guide

- critical: data loss, security issue, privacy breach, broken workflow, or impossible execution.
- high: likely behavioral bug, serious functional drift, missing gate, or false confidence about safety or correctness.
- medium: maintainability issues, ambiguity, partial coverage, confusing UX, or future failure risk.
- low: naming, style, documentation clarity, small polish items, or optional improvements.

## Confidence Guide

- high: directly supported by source artifacts, executed verification, or clear, recent logs/tests.
- medium: supported by strong but indirect evidence; some assumptions or missing pieces remain.
- low: plausible but thin, stale, incomplete, largely assumption-based, or dependent on external context that cannot be verified.

## Stop Conditions

Stop and ask a brief clarifying question instead of guessing when:

- The target artifact is missing, inaccessible, or ambiguous.
- The review lens cannot be reasonably inferred and would materially change the review.
- The available evidence is too thin to produce useful findings.

Always prefer an honest "cannot determine with current evidence" over an overconfident verdict.
