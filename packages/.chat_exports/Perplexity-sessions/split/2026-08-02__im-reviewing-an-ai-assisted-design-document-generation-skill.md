---
title: "I'm reviewing an AI-assisted design document generation skill called /design. It orchestrates subagents to produce desig"
date: "2026-08-02"
mode: "COPILOT"
uuid: "907beb8e-efa7-4ea8-8d51-95299888251f"
entry_count: 1
---

## Human

I'm reviewing an AI-assisted design document generation skill called /design. It orchestrates subagents to produce design documents. Please review its architecture and suggest improvements across features, decisions, assumptions, and implementation.## Current ArchitectureThe /design skill orchestrates a write-review-revise loop:1. Pre-write steps (conditional): Context firewall, Domain research, Codebase inventory, Premise verification2. Write: Writer subagent produces design doc with mandatory sections3. Review: Reviewer checks implementability, completeness, consistency4. Revise: Writer addresses all findings5. Consistency sweep: Automated drift checker6. Re-review: Loop until 0 open issues7. Critical friend: Fresh subagent challenges premises (5 domains: framing, optimal-vs-simple, falsifiability, anchoring, pre-mortem)8. Summary + key decisions promotion to wiki## Key Features- Failure Mode & Edge Case Analysis: 6 categories per component (concurrency, edge cases, error paths, state transitions, resource exhaustion, multi-agent)- Coupling & Code-Smell Inventory: DRY (>=3), params (>7), touch-points (>3)- Persona injection from TOML files. No iteration cap. Temp lifecycle.- Lite and Fast modes## Key Decisions1. Design docs are scaffolding, not durable. 2. Separate subagents for each role. 3. Fresh subagent for critical friend. 4. Optimal long-term over minimal-diff. 5. Meaningful alternatives.## Questions1. What features are missing? 2. What assumptions might be wrong? 3. What decisions would you challenge? 4. What patterns improve quality/cost? 5. What failure modes exist?

## Assistant

Your /design architecture already has a solid generator-critic backbone, but I would change its center of gravity from “produce a polished doc through repeated critique” to “produce a decision record with explicit evidence, uncertainty, and closure conditions.” The biggest gaps are assumption management, termination/control, evidence traceability, and calibration of when multi-agent complexity is actually worth it.[1][2][3][4]

## Missing features

The most important missing feature is a first-class RAIDC layer: risks, assumptions, issues, dependencies, and constraints, with owner, evidence, impact-if-false, and closure status for each assumption. Architecture standards explicitly treat assumptions as items to validate and track to closure, because an unvalidated assumption that fails later becomes a risk or issue; your current “premise verification” is useful, but it is not the same as a persistent assumption ledger threaded through the whole document and review loop.[2]

I would also add:
- Decision traceability: every major recommendation should carry “why this option won,” rejected alternatives, and what evidence would overturn the choice, which aligns with ADR-style governance.[2]
- Exit criteria and loop budget: your current no-cap loop improves quality in theory, but multi-agent patterns add coordination cost and failure modes, so the system needs bounded stopping conditions such as max iterations, diminishing-return thresholds, severity-weighted reopen rules, and escalation to human review.[3][4]
- Evidence map: each section should declare its evidence basis as FACT, CONSENSUS, or SPECULATION, plus source class and freshness, so the doc does not present weak premises with the same confidence as verified constraints. This fits your stated preference for explicit uncertainty and would reduce false precision.

## Wrong assumptions

I would challenge the assumption that more iteration monotonically improves quality. Research on LLM critics shows common judge failures such as missing errors, low-quality suggestions, incorrect critiques, and revisions that only partially follow feedback, so extra loops can entrench reviewer mistakes rather than fix them.[5]

I would also question:
- “Separate subagents per role is always better.” Multi-agent systems are recommended when tasks are clearly distinct or need separate contexts/security boundaries, but guidance from Databricks and Azure says to start simpler and justify orchestration overhead rather than assume it.[4][3]
- “Fresh subagent means better critical challenge.” Fresh context helps reduce anchoring, but it does not guarantee better critique quality; critics can still miss errors or over-flag correct content. A fresh critic should therefore be paired with a rubric, adversarial prompts, and disagreement resolution, not treated as inherently trustworthy.[5]
- “Optimal long-term over minimal diff” as a default. That can be right for greenfield or architectural dead-ends, but your own reuse-first preference suggests the default should be conditional: reuse > refactor > rebuild unless quantified evidence shows local optimization is a trap.[6]

## Decisions to challenge

I would most strongly challenge the combination of “design docs are scaffolding, not durable” and “summary + key decisions promotion to wiki.” If decisions are important enough to promote, then at least the decision core is durable and should be structured like lightweight ADRs with status, rationale, assumptions, supersession rules, and links to evidence, rather than being a byproduct of an ephemeral draft.[2]

I would also revisit these decisions:

| Decision | Challenge | Better default |
|---|---|---|
| No iteration cap | Can create unbounded cost, latency, and oscillation with little quality gain. [3][4] | Cap by severity and convergence, for example 2-3 main loops plus explicit escalation. |
| Separate reviewer only | Reviewer may inherit rubric blind spots and become a single point of epistemic failure. [5] | Use one implementability reviewer plus one targeted verifier for assumptions/feasibility. |
| Mandatory meaningful alternatives | Good in principle, but often produces performative options. | Require alternatives only for high-impact or irreversible decisions, with a “why not” threshold. [2] |
| Optimal long-term bias | Can encourage unnecessary redesign and duplicate infrastructure. [6] | Default to smallest durable change that preserves strategic direction. |
| 6 failure categories per component | Broad coverage, but still misses governance and observability failure classes. | Add rollback/recovery, detectability, security/privacy, human-ops burden, and dependency volatility. [2][4] |

## Quality and cost patterns

The highest-leverage pattern is to split “thinking roles” from “verification roles.” Industry guidance distinguishes sequential refinement, concurrent analysis, and coordinator patterns; for your case, quality usually improves when independent checks run in parallel only where they bring orthogonal signal, not everywhere.[7][8][4]

A better cost/quality architecture would be:
1. Deterministic preflight: inventory, dependency scan, existing-design reuse scan, assumption extraction, and document skeleton generation. Deterministic chains are easier to audit for well-defined tasks.[3]
2. Single writer pass: produce the doc once with explicit uncertainty tags and open questions.
3. Parallel targeted reviewers, not one monolithic reviewer: implementability, evidence/assumptions, and operational risk. Concurrent specialization is useful when analyses are independent, but needs a conflict-resolution step.[4]
4. Judge aggregator: synthesize reviewer findings, dedupe overlaps, assign severity, and decide reopen vs accept.
5. One bounded revise pass, then critical friend only on unresolved or high-impact decisions.

That pattern reduces redundant token spend, preserves traceability, and matches your preference for structured reviews and more findings when they are actually orthogonal.

## Failure modes

Your current design is exposed to several failure modes beyond the ones you listed. The biggest one is rubric gaming: the writer learns to satisfy reviewer phrasing instead of improving the underlying architecture, especially when reviewer criteria are static. Critic literature shows common failure modes including missed errors, inaccurate critiques, and revisions that do not truly implement the feedback.[5]

Other important failure modes:
- Oscillation: writer and reviewer alternate preferences with no convergence because no tie-break rule exists.[4]
- False closure: “0 open issues” can still hide untested assumptions, because issue count is not the same as design validity. Architecture governance guidance treats assumptions and risks as separate tracked objects for this reason.[2]
- Evidence laundering: a speculative claim gets repeated across stages until it looks authoritative.
- Agent over-segmentation: too many role splits create prompt drift, coordination overhead, and debugging difficulty without adding distinct signal.[3][4]
- Premature optimization bias: “optimal long-term” can systematically overshoot real constraints and implementation appetite, producing docs teams will not execute.
- Fresh-agent inconsistency: the critical friend may challenge framing well but miss codebase realities unless it receives a compact evidence pack rather than the full noisy draft.
- Wiki pollution: promoting decisions without confidence, status, and supersession metadata can fossilize tentative judgments into pseudo-policy.[2]

My #1 recommendation is to reframe /design around a **decision-contract pipeline**: every major claim must declare evidence, confidence, impact-if-wrong, owner, and verification path; every loop must be bounded; and every promoted decision must become a lightweight ADR rather than a summary bullet. That keeps the strong parts of your architecture while making it more durable, auditable, and cheaper to run.[3][4][2]

Would you like a concrete revised /design architecture with agent roles, state objects, stop conditions, and a recommended prompt contract for each subagent?
