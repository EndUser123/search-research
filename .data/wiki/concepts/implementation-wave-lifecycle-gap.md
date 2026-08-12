---
title: "Implementation-wave lifecycle gap: artifact drift and scope collapse between session and code gates"
created: 2026-08-11
source: session-019ff2aa (/why root-cause + /www field research + /tp synthesis + historical measurement)
tags: [definition-of-done, implementation-wave, artifact-drift, scope-collapse, lifecycle-gate, revision-invalidation, self-correction-blind-spot, post-implementation, trailing-edge]
agent: grok
host: both
cognitive_load: 3
verification: multi-source-verified
summary: >
  Workspace gates are scoped to session lifecycle (/close) and code lifecycle
  (/check) but not implementation-wave lifecycle. An implementation wave — the
  unit between "I started changing this feature" and "this feature change is
  fully closed out" — introduces trailing-edge obligations (update derived
  artifacts, track proposed alternatives, document operational layer) that no
  gate checks. Two failure clusters result: artifact drift (wiki concepts,
  tests, docs go stale after implementation changes) and scope collapse
  (proposed alternatives silently dropped, production concerns unaddressed).
  Historical measurement: 697 wiki commits across 1146 concepts (0.6
  avg/concept) confirms most wiki concepts are write-once — the revision-
  invalidation pattern is systemic. The Self-Correction Bench (arXiv:2507.02778)
  64.5% blind-spot rate explains why prose-level meta-checkpoints have a ceiling.
  The optimal long-term fix: a PostImplementation gate with mechanical checks
  (derived-artifact grep, test-location check, unpushed-alternatives scan) +
  LLM judgment layer (scope-specific obligation generation from the commit diff).
relations:
  - target: wiki/concepts/consistency-drift-as-waste-source-in-iterative-refinement.md
    type: companion — consistency drift is the intra-revision instance; this concept is the inter-revision instance
  - target: wiki/concepts/compaction-inherited-recommendation-decoupling.md
    type: adjacent — the session that produced this concept also exhibited the pattern (wiki concept went stale after v2/v3)
  - target: wiki/concepts/post-edit-skill-re-read-before-use.md
    type: related — both about derived artifacts going stale after edits
  - target: wiki/concepts/close-runner-verdict-staleness-across-phases.md
    type: related — both about verdicts/artifacts going stale when later work invalidates them
---

# Implementation-wave lifecycle gap

## Decision context

**Why this knowledge was needed:** session 019ff2aa shipped a three-version feature (stale-recommendation detection: v1 keyword list → v2 regex → v3 LLM classifier). After v3 shipped, a /tp "did we forget anything?" pass identified 6 forgotten items: wiki concept stale, tests in ephemeral storage, proposed alternative silently dropped, LLM production concerns unaddressed, no monitoring guidance, no end-to-end test. The operator asked: what's the root cause, and what's the optimal long-term fix?

**The measurement:** historical session scan found 12/4662 sessions (0.3%) with explicit "did we forget" language, but with clustering (one session had 12 matches — the operator catching items repeatedly within one session). Wiki update frequency: 697 commits across 1146 concepts (0.6 avg/concept) — the vast majority of concepts are write-once, never updated after initial creation. This confirms artifact drift is systemic, not session-specific.

## The two failure clusters

### Cluster A: Artifact drift

When implementation changes, derived artifacts (wiki concepts, tests, docs, handoffs) are not mechanically invalidated. The revision-invalidation rule in AGENTS.md is scoped to *research artifacts*, not *code artifacts*.

| Symptom | Root cause |
|---------|-----------|
| Wiki concept describes v1 after v3 ships | No gate checks "does the wiki still match the code?" after implementation changes |
| Tests in P:/tmp/ (ephemeral) | No gate checks "are tests persisted in the right location?" |
| Existing pipeline test not extended | No gate checks "was the test suite updated for new behavior?" |

### Cluster B: Scope collapse

When scope expands mid-implementation (adding features, discovering alternatives), the expanded scope's trailing-edge obligations are not captured.

| Symptom | Root cause |
|---------|-----------|
| Proposed Fix 3 silently dropped | Alternatives proposed in prose ("Confidence: MEDIUM") never become tracked items |
| LLM production concerns unaddressed | "It works" (live-fire test) used as proxy for "production-ready" |
| No monitoring guidance | Telemetry shipped as data feature without interpretation layer |

## The unified root cause

Both clusters share one structural origin: **the workspace's gates are scoped to the wrong lifecycle granularity.**

| Gate | Granularity | What it checks |
|------|-------------|----------------|
| /close | Session | Handoffs, git state, AAR receipts |
| /check | Code | Tests pass, runtime works |
| /review | Code | Defects, design issues |
| Meta-checkpoint (prose) | Session (behavioral) | "Did you escalate the symptom?" etc. |
| **Missing** | **Implementation wave** | **Derived artifacts updated? Alternatives tracked? Operational layer documented?** |

An implementation wave is smaller than a session and larger than a commit. It's the unit between "I started changing this feature" and "this feature change is fully closed out." No gate fires at that boundary.

## Why prose-level fixes have a ceiling

The Self-Correction Bench (arXiv:2507.02778, Tsui 2025) found LLMs have a **64.5% self-correction blind spot** — they fail to detect their own errors at nearly twice the rate they catch them. The existing meta-checkpoint rule (5 questions before "DONE") is a prose-level behavioral rule with a ~50% compliance ceiling under session pressure ([[false-choices-parallel-branch-framing]]).

This is why the operator consistently catches forgotten items that the agent misses: the agent cannot reliably self-detect the gap because the same model that forgot to update the wiki cannot reliably ask "did I forget to update the wiki?"

## What the field knows

The agile world solved this as the **Definition of Done (DoD)** — a checklist that must pass before work is declared complete. The 2026 Atlassian and Scrum.org guidance: "done" must be a shared, measurable standard that includes testing, documentation, integration, and operational readiness — not just "code written."

The documentation engineering world solved this as **SSOT + automated consistency checking** — grep-based symbol checkers, link validators, CI gates that mechanically verify derived artifacts match the source.

The key insight: the definition of done must be **dynamic, expanding with scope.** A static checklist cannot anticipate that adding an LLM classifier creates an obligation to document API failure modes. The scope-specific obligations must be generated from the diff.

## The optimal long-term fix: PostImplementation gate

A two-stage hybrid gate that fires at the implementation-wave boundary (after commit, before declaring the wave done):

### Stage 1: Mechanical checks (deterministic, <2s)

| Check | How | What it catches |
|---|---|---|
| Derived-artifact grep | For each file in the commit, grep wiki concepts and handoffs for references to that filename or its symbols. Report hits as "potentially stale." | Cluster A: wiki/docs stale |
| Test location check | Check if test files exist in P:/tmp/ or ephemeral dirs. Report as "needs promotion." | Cluster A: tests ephemeral |
| Test coverage delta | For each changed module, check if existing test files that import that module were modified. Report untouched test files. | Cluster A: tests not extended |
| Unpushed-alternatives scan | Grep session transcript for "Fix N" or numbered proposals not in any handoff or todo. Report as "proposed-but-not-tracked." | Cluster B: alternatives dropped |

### Stage 2: LLM judgment (scope-dependent, ~5s)

Send the commit diff + changed capabilities to a classifier: "Given these changes, what trailing-edge artifacts should exist but might not? Consider: operational guidance, production readiness, monitoring interpretation, failure mode documentation." The LLM generates scope-specific checklist items the mechanical checks can't predict.

## Measurement grounding

Historical session scan (session 019ff2aa):
- **Session count:** 4662 total sessions
- **Explicit "did we forget" mentions:** 12 sessions (0.3%) — but with clustering (one session had 12 matches)
- **Wiki update frequency:** 697 commits across 1146 concepts (0.6 avg/concept) — most concepts are write-once
- **Most-updated concepts:** operational registries (skill-catalog: 50 commits, tool-fallbacks: 34) — maintenance files, not knowledge concepts

**Interpretation:** the 0.3% explicit-mention rate undercounts the problem because (a) the operator has ADHD and doesn't always ask the question explicitly, (b) the meta-checkpoint rule exists because the problem is chronic, and (c) the wiki write-once pattern (0.6 avg commits/concept) shows artifact drift is systemic even when no one notices.

## Falsifier

This pattern is wrong if:
- **The existing meta-checkpoint rule catches most forgotten items.** Test: compare forgotten-items count before and after the rule was added (2026-07-27). If the rate dropped significantly, the prose rule may be sufficient.
- **Artifact drift is rare in practice.** Test: sample 20 wiki concepts that describe code artifacts; check whether the code matches the concept. If most match, drift is not systemic.
- **The PostImplementation gate produces noise.** Test: run the gate on 5 implementation waves; measure false-positive rate of the mechanical checks.

## Related concepts

- [[consistency-drift-as-waste-source-in-iterative-refinement]] — the intra-revision instance (within one design loop); this concept is the inter-revision instance (across implementation waves)
- [[post-edit-skill-re-read-before-use]] — both about derived artifacts going stale after edits
- [[close-runner-verdict-staleness-across-phases]] — both about verdicts going stale when later work invalidates them
- [[false-choices-parallel-branch-framing]] — the 50% prose-compliance ceiling
- [[trusted-exit-status-fallacy-pipeline-ground-truth]] — "shipped ≠ complete" is the same principle as "exit-0 ≠ artifact correct"
