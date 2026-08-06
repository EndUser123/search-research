---
title: "Risk pattern: threat-model inflation in adversarial review"
created: 2026-08-06
source: session-20260805
tags: [risk-pattern, threat-model, adversarial-review, risk-assessment]
summary: >
  When a risk assessment or adversarial review lacks explicit host context
  (what agents operate, what trust model applies), critics default to the
  most adversarial threat model available and produce findings that don't
  match the actual system. The fix is mandatory host-context injection in
  every critic prompt.
agent: grok
host: grok
cognitive_load: 2
verification: observed
relations:
  - target: wiki/concepts/multi-model-ensemble-design-patterns-for-agent-skills.md
    type: extends
---

# Risk pattern: threat-model inflation in adversarial review

## Pattern

When cross-model critics assess a target without explicit host context (what kind of agents operate, what trust model applies), they default to adversarial analysis and produce findings about weaponization, trust injection, and deliberate evasion — even when the target is an unreliable-agent system where those threats don't apply.

## Evidence

- **Session 2026-08-05:** `/risk` v1 run on the LAEFS enforcement layer produced 3/14 findings with threat-model inflation (M1 broker weaponization, M3 trust injection, R1 deliberate evasion). The target is unreliable-agent (LLM agents making mistakes), not adversarial.
- **Fix applied:** P1 host-context requirement (every critic prompt MUST include host system context) + P6 threat-model classification (Phase 0 classifies the threat model, critics check findings against it).
- **Verification:** `/risk` v4 Run 2 on the same target produced zero adversarial findings from either critic. P6 works.

## What this means for our workspace

1. Every cross-model critic or specialist prompt MUST include host context: agent type (LLM, human, untrusted code), trust model (operator-authorized, autonomous, sandboxed), and the Phase 0 threat model classification.
2. Threat-model classification (P6) is a mandatory scan category for decision-type targets. Without it, the scan produces adversarial findings on unreliable-agent systems.
3. This pattern applies beyond `/risk` — `/review` and `/tp` critics can also produce threat-model-inflated findings without host context.

## Falsifier

If a critic produces adversarial findings on an unreliable-agent target AFTER receiving explicit host context and threat-model classification, the pattern is wrong (host context alone is insufficient). If no critic ever produces adversarial findings on a genuinely adversarial target, the classification is over-correcting.

## Related concepts

- [[multi-model-ensemble-design-patterns-for-agent-skills]] — P1 (host-context) and P6 (threat-model classification) are the patterns that fix this risk
- [[agent-failure-modes-2026]] — cold-start amnesia and other failure modes in LLM agent systems
- [[adaptive-expansion-evidence-triggered-conditional-steps]] — the pattern structure that makes threat-model classification adaptive

## Receipts

- Session 019fcdd2 Run 2 CRITIQUE panel: zero adversarial findings from or-ling-3-flash-free and glm-5-2
- Wiki concept: `multi-model-ensemble-design-patterns-for-agent-skills.md` § P1 (host-context) and P6 (threat-model classification)
