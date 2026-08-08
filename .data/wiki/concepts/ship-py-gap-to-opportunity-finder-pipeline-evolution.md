---
title: "Ship-py as gap-to-opportunity finder — pipeline evolution from gate to gate-plus-opportunity"
created: 2026-08-08
source: session-019fdf3d
tags: [ship-py, pipeline-design, opportunity-discovery, verification, architectural-decision, ci-cd]
summary: >
  Ship-py's current design is a verify-and-publish GATE — every phase either
  blocks or passes. The evolution: ship-py should also be a gap-to-opportunity
  FINDER for its target code. Non-blocking findings (P2 dead code, doc WARNs,
  missing tests) should be structured as ranked opportunities, not just counted.
  The verdict should include an opportunity landscape. /close handles session-
  level gap discovery; ship-py handles target-level gap discovery. This mirrors
  the field's evolution from binary pass/fail to risk-weighted quality signals.
agent: grok
host: grok
cognitive_load: 3
verification: multi-source-verified
sources:
  - https://www.sdettech.com/blogs/what-modern-qa-teams-measure-beyond-pass-fail (SDET Tech, Jun 2025)
  - https://medium.com/@briancolfer/beyond-pass-fail-rethinking-ci-cd-decisions-with-graded-logic-568275106719 (Colfer, Apr 2026)
  - https://github.com/clay-good/OpenLore (OpenLore, 2026)
  - https://arxiv.org/html/2505.16339v1 (arXiv, May 2025)
relations:
  - target: wiki/concepts/check-and-fix-skills-verification-skills-should-fix-what-they-can.md
    type: extends
  - target: wiki/concepts/pipeline-session-scoping-each-layer-independently.md
    type: complements
  - target: wiki/concepts/narrative-sufficiency-awareness-enforcement-gap-2026.md
    type: related
---

# Ship-py as gap-to-opportunity finder

## Decision context

Ship-py currently answers one question: "can we ship?" Each phase is a gate —
it blocks (P0, critical bugs, FAIL) or passes (advisory findings are counted
but don't drive action). The operator pointed out: ship-py should ALSO answer
"what could be better about this code?" — surfacing improvement opportunities
for the target, not just blocking findings.

This is the /aar principle applied to the pipeline level: **an opportunity
does not require a failure.** A successful ship (all gates pass) can still
reveal unnecessary effort, missed leverage, dead code worth pruning, and
coupling worth reducing. See [[mechanical-enforcement-over-behavioral-reminder]]
for the underlying principle: mechanical systems should surface what matters,
not just gate.

The boundary with /close: `/close` is the gap-to-opportunity finder for the
**session** (what did we miss, what's unfinished, what knowledge is leaving).
Ship-py is the gap-to-opportunity finder for the **target** (what could be
better about THIS specific code change). This mirrors the separation between
[[check-and-fix-skills-verification-skills-should-fix-what-they-can]] (fix what
you can) and this concept (surface what you could improve).

## What the field does (2025-2026 research)

### 1. Graded logic over binary pass/fail (Colfer 2026)

"CI/CD pipelines are supposed to give us confidence in what we ship. But most
pipelines only answer one question: Did everything pass? That's not confidence.
That's compliance." The shift: from binary gate decisions to **graded** quality
signals that tell the operator how much confidence they should have, not just
whether the bar was cleared.

Ship-py already has partial graded logic (WARN vs BLOCK), but the WARNs are
unstructured — they're recorded in the receipt but don't drive action or rank
by ROI.

### 2. Risk-based coverage (SDET 2025)

Mature QA teams measure coverage not by raw numbers but by **probability and
impact of failure** in each system area. Test tagging by risk profile,
real-time coverage auditing, and threat-modeling integration. The pipeline
maps "what's meaningfully tested" not just "what's tested."

Ship-py's refactor-scan reports `dead_code: 160` and `test_gaps: 48` but
doesn't rank them by risk or impact. A dead-code item in a hot path is higher
ROI to prune than one in a dormant module.

### 3. Advisory-by-default with opt-in blocking (OpenLore 2026)

OpenLore's design: "Advisory by default; you opt into blocking per finding.
Value Scorecard — does it pay for itself?" This inverts the default from
"block everything" to "advise everything, block only what the operator
opts into." The value scorecard tracks whether advisory findings led to
action — if they consistently don't, the advisory is noise.

Ship-py's phases are blocking-by-default (P0 blocks, failures block, FAIL
blocks). The advisory findings exist but don't have a value scorecard.

### 4. Pipeline as quality oracle (SDET 2025)

"CI/CD pipelines are not merely a vehicle for deployments — they are real-time
observability tools for software quality." Pipeline pressure metrics,
deployment gate success ratios, rollback signal analysis, canary deviation
indices. The pipeline IS the quality dashboard, not just the gate.

Ship-py's pipeline output is a ship receipt (DONE/BLOCKED). It doesn't produce
a quality dashboard for the target code.

## What ship-py should add (the opportunity layer)

### Design: two verdict modes

| Mode | Question | Output |
|---|---|---|
| **SHIP verdict** (current) | Can we ship? | SHIP DONE / SHIP VERIFIED / SHIP BLOCKED |
| **OPPORTUNITY verdict** (new) | What could be better? | Ranked opportunity landscape from advisory findings |

Both modes run on every pipeline invocation. The ship verdict gates; the
opportunity verdict informs. The operator sees both at the end.

### Opportunity sources (already collected, not yet structured)

| Source | Current treatment | Opportunity treatment |
|---|---|---|
| refactor-scan P2 dead-code | Counted: "160 P2 findings" | Ranked by: file path (hot vs dormant module), line count (prune effort), downstream dependency count |
| refactor-scan test gaps | Counted: "48 test gaps" | Ranked by: function complexity (high-complexity untested = high risk), call-site count (widely-called untested = high blast radius) |
| doc-check WARNs | Counted in receipt | Structured as improvement suggestions: "add trigger phrases to description", "add ADR for dispatch change" |
| skill-dev warnings | Counted: "N warnings" | Ranked by: which skill, which check, whether it's a recurring pattern across sessions |
| review nits/needs_attention | Recorded but not surfaced | Ranked by: fix effort (S/M/L), whether the finding recurs across sessions |

### Opportunity tracking (the value scorecard)

Record which opportunities were acted on across sessions. Compute an
**opportunity-action rate**: of N opportunities surfaced, how many led to
code changes, doc updates, or skill edits within 7 days?

- High action rate → opportunities are valuable; keep surfacing
- Low action rate → opportunities are noise; tighten the bar or stop surfacing
- This is the OpenLore "value scorecard" principle applied to ship-py
- Connects to [[narrative-sufficiency-awareness-enforcement-gap-2026]]: the
  field's shift from prose rules to structural enforcement applies here too —
  the opportunity layer must be mechanically tracked, not just reported

### Target-specific opportunity scan (the missing phase)

Currently ship-py checks the target (does it pass?). It could ALSO scan for
what the target COULD be:
- **Missing tests** — functions touched in the diff but not covered by any test file
- **Missing docs** — new functions/classes without docstrings (already checked by ruff --select D, but as a WARN not an opportunity)
- **Dead code introduced** — new code that duplicates existing functionality (detected by refactor-scan, but as P2 not as an opportunity)
- **Coupling increased** — the diff adds imports that tighten coupling (detected by breaking-change check, but as a structural finding not an opportunity)
- **Skill-graph gap** — if the target is a skill, does it reference capabilities that don't exist? Does it miss techniques that sibling skills use?

## What this means for our workspace

Ship-py v2.4 (or v3.0) should add:
1. **Opportunity verdict block** in the receipt — after SHIP DONE/VERIFIED, emit a ranked opportunity landscape
2. **ROI ranking** on refactor-scan P2 findings — not just count, but effort × impact
3. **Opportunity tracking** in the state file — record opportunities, check action rate on next run
4. **Target-specific scan** — a new pre-review phase that scans the target for what it COULD be, not just what's wrong

This is additive to the current pipeline — the gate still gates, the fix phase
still fixes. The opportunity layer is advisory output that the operator
reviews post-ship and routes to `/handoff` or `/todo` if actionable.

## Steelman of the rejected alternative (gate-only)

The gate-only design is simpler and faster. Adding an opportunity layer
increases pipeline runtime and output volume. The operator might not act on
the opportunities, making the layer pure noise. The cognitive load of
reviewing opportunities after every ship may exceed the value.

**Why the steelman loses here:** the opportunities are already collected —
they're just unstructured. Refactor-scan already reports P2 counts; doc-check
already reports WARNs. The cost is not "run more checks" but "structure the
existing advisory output as ranked opportunities." The runtime cost is ~0
(just JSON formatting + ranking). The cognitive load is mitigated by ranking
(top 5 opportunities, not 160 unstructured findings) and by the value
scorecard (if the operator consistently ignores opportunities, the bar
tightens automatically).

## Falsifier

This design is wrong if: (a) the operator consistently ignores the opportunity
landscape → opportunities are noise, remove the layer; (b) the ranking is too
noisy to be actionable → improve the ranking algorithm or reduce the surface;
(c) the opportunity layer adds latency without value → defer to a separate
`/opportunity` skill that runs post-ship rather than inline.

## Sources

- [SDET: What Modern QA Teams Measure Beyond Pass/Fail](https://www.sdettech.com/blogs/what-modern-qa-teams-measure-beyond-pass-fail) (SDET Tech, Jun 2025) — risk-based coverage, pipeline as quality oracle, defect leakage analytics
- [Beyond Pass/Fail: Graded Logic](https://medium.com/@briancolfer/beyond-pass-fail-rethinking-ci-cd-decisions-with-graded-logic-568275106719) (Colfer, Apr 2026) — graded decisions in CI/CD (article paywalled; framing confirmed from search result)
- [OpenLore](https://github.com/clay-good/OpenLore) (2026) — advisory-by-default with opt-in blocking + value scorecard
- [Rethinking Code Review with LLM Assistance](https://arxiv.org/html/2505.16339v1) (arXiv, May 2025) — identifying opportunities for AI in code review

## Receipts

- `ship_orchestrator.py:cmd_refactor_scan` — P2 dead-code findings counted but not ranked by ROI (line ~1040)
- `ship_receipt.py:derive_verdict` — verdict is DONE/BLOCKED, no opportunity landscape (line ~1265)
- `doc-check/scripts/check.py:main` — WARN findings recorded but not structured as improvement suggestions (line ~560)
- `pipeline-session-scoping-each-layer-independently.md` — the session-scoping pattern that this concept extends with opportunity ranking

## Auto-related

- [[skill-graph]]
- [[ship-rhai-performance-optimization-techniques]]
- [[stop-hook-state-file-keyword-trap]]
- [[ship-pipeline-enforcement-pretooluse-phase-state-hooks]]
- [[skill-step-enforcement-architecture-grok-build]]

