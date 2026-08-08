---
title: "Design-doc conformance check: verify proposal claims against the actual codebase"
created: 2026-08-08
source: session-2026-08-08
tags: [design-review, conformance-check, tp, risk, skill-composition, verification, procedure, reusable-component]
host: grok
agent: grok
cognitive_load: 2
verification: directly-verified
relations:
  - target: wiki/concepts/adhd-parallel-frame-divergent-ideation-integration.md
    type: complements
  - target: wiki/concepts/evidence-driven-model-router-architecture.md
    type: related
  - target: wiki/concepts/narrative-as-signal.md
    type: refines
summary: >
  A reusable verification procedure that extracts behavioral claims from a design
  proposal, checks each against the actual codebase, and labels the gap. Neither
  /tp nor /risk does this mechanically today — /tp critiques framing, /risk scans
  for failure modes, but neither diffs the proposal's "the system does X" against
  the code that actually implements X. The procedure was extracted from a session
  where the highest-value review findings came from a subagent reading the code
  (p50 vs p90, golden-vectors skeleton, 4-tuple identity already exists) — exactly
  the claims a prose-only review would have missed.
---

# Design-doc conformance check: verify proposal claims against the actual codebase

## Decision context

During a `/tp review` of a cross-host model-selection proposal, the highest-value findings came not from the critique's reasoning but from the subagent **reading the actual code** the proposal described. The proposal said "uses p90 latency" — the code uses p50. The proposal said "shared golden vectors" — the Python verifier is SKELETON, the JS verifier doesn't exist. The proposal described the 4-tuple evidence identity as novel — it already exists in `EvidenceIdentity`.

None of these findings required critical reasoning. They required looking at the code and comparing. That's a mechanical procedure, not a reasoning task — and neither `/tp` nor `/risk` does it mechanically. This is the structural complement to [[narrative-as-signal]]: the narrative-as-signal rule says "treat plausible stories as signals to read docs"; the conformance check is the mechanical execution of that reading.

## The procedure

```
1. EXTRACT CLAIMS
   - Scan the design doc for behavioral assertions: "uses X", "shares Y",
     "the system does Z", "evidence is segmented by W"
   - Each assertion is a claim with an implicit source (the codebase)

2. VERIFY EACH CLAIM
   - For each claim, grep/read the actual implementation
   - Label each claim:
     VERIFIED     — code confirms the claim (cite file:line)
     ASPIRATIONAL — code does not have this capability
     PARTIAL      — code has a subset (name what's missing)
     CONTRADICTED — code does the opposite

3. REPORT
   - Sorted by impact: CONTRADICTED > ASPIRATIONAL > PARTIAL > VERIFIED
   - Each finding cites the proposal line and the code line
```

## What this catches that prose review misses

| Finding type | Example from this session | Why prose review misses it |
|---|---|---|
| Metric mismatch | "proposal says p90; code uses p50" | The reviewer assumes the proposal is describing the system correctly |
| Missing infrastructure | "proposal says shared golden vectors; JS verifier doesn't exist" | The reviewer can't check file existence without reading the filesystem |
| Restatement-as-design | "proposal describes 4-tuple identity as novel; it already exists" | The reviewer doesn't know what already exists unless they read the code |
| Dead references | "proposal says 'current system uses pct < 10 gate'; no such gate exists" | The reviewer trusts the proposal's characterization of the current state |

## What this means for our workspace

- **Extract this as a shared reference doc** at `~/.grok/skills/references/design-doc-conformance-check.md`. Both `/tp` and `/risk` load it when the target is a design proposal. Neither skill needs to merge or gain a new mode — they just load the procedure and execute it as a step.

- **`/tp` loads it before the critique subagent runs.** The conformance check is the evidence the critique needs: "here's what the proposal claims, here's what the code actually does — now critique the gap." Without it, the critique can only challenge framing, not verify claims.

- **`/risk` loads it before the specialist scan.** Risk specialists need to know which claims are ASPIRATIONAL (higher risk — the design depends on something that doesn't exist) vs VERIFIED (lower risk — the design extends something proven).

- **`/design` Step 0.8 (Premise Verification) already does a version of this** — it extracts premises and labels them [FACT]/[INFERENCE]/[UNKNOWN]. The conformance check is the same pattern applied to reviewing an external proposal rather than preparing one. The labeling scheme is compatible: VERIFIED = [FACT], ASPIRATIONAL/PARTIAL = [INFERENCE], CONTRADICTED = [CONTRADICTED]. The [[adhd-parallel-frame-divergent-ideation-integration]] concept already mapped the overlap between `/tp`, `/design`, `/risk`, and `/brain` — this procedure is the missing shared component.

## Falsifier

If the conformance check takes longer than 5 minutes for a typical proposal (≤500 lines), it's over-scoped. The check is mechanical extraction + grep, not deep reasoning. If it requires reasoning, the claim is ambiguous and should be labeled PARTIAL with a note, not debated.

If the conformance check produces only VERIFIED findings for a proposal, either the proposal is perfect (unlikely) or the extraction missed claims. Re-run with broader patterns.

## Receipts

- Session 2026-08-08 `/tp review` of `docs/designs/2026-08-08-common-model-selection-policy-for-codex-and-grok.md`
- The review subagent (id `019fe192`) read 6 source files and produced 22 labeled findings
- [[adhd-parallel-frame-divergent-ideation-integration]] — already mapped the /tp, /design, /risk, /brain overlap
- `/design` Step 0.8 (Premise Verification) at `~/.grok/skills/design/SKILL.md` — compatible labeling scheme
- [[evidence-driven-model-router-architecture]] — the router architecture the proposal describes (and partly restates)

## Auto-related

- [[skill-graph]]
- [[skill-catalog]]
- [[scope-matching-verification-discipline]]
- [[premature-closure-narrative-sufficiency-external-approaches]]
- [[I'm-going-to-create-a-hook-to-enforce-discovery-be]]

