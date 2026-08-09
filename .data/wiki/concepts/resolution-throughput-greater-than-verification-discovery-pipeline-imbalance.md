---
title: "Resolution throughput > verification discovery: the pipeline imbalance pattern"
created: 2026-08-09
source: session-019fe403 (/tp {3} panel, agy lens core reframing)
tags: [pipeline-design, resolution-throughput, verification-discovery, imbalance, accumulation-problem, ship-py]
host: grok
agent: grok
verification: observed
relations:
  - target: wiki/concepts/accumulation-problem-resolution-rate-binding-constraint.md
    type: extends — names the specific imbalance between discovery and resolution
  - target: wiki/concepts/code-orchestrates-model-judges-skill-scale.md
    type: applies — the pattern that produces the imbalance
summary: >
  Adding more verification checks to a pipeline without increasing
  auto-remediation throughput worsens the existing discovery-to-resolution
  mismatch. The binding constraint is not finding problems (discovery) but
  fixing them (resolution). Pipeline design should weight items that reduce
  friction (auto-fixing, concurrency safety, flow control) over items that
  add more gates.
---

# Resolution throughput > verification discovery

## The pattern

When a ship pipeline adds more verification phases (FMEA, secret-scan,
design-check, etc.), each new phase discovers more findings. But unless
the pipeline also increases its ability to RESOLVE those findings (auto-fix
coverage, fix-loop efficiency, cumulative knowledge), the backlog grows.
The discovery-to-resolution ratio gets worse with every gate added.

## The reframing

This was agy's (Gemini 3.5 Flash) core contribution to the /tp {3} panel
on ship-py improvements. The panel was asked "what should ship-py be enhanced
with?" — the expected answer was "more checks." The correct framing was:
"what makes the pipeline more effective at its job?" — which includes
reducing friction, not just adding gates.

## Evidence

- The workspace wiki concept `accumulation-problem-resolution-rate-binding-constraint`
  documents the general pattern: the binding constraint on system improvement
  is resolution rate, not discovery rate.
- Session 019fe403: the /todo scanner found 197 dangling paths and 572 stale
  state files across the workspace. These are accumulated unresolved findings.
- The FMEA scan on ship-py found 38 failure modes — 37 pre-existing. Adding
  them as findings without auto-remediation increases the backlog.

## Implications for pipeline design

| Approach | Effect on ratio | Recommendation |
|---|---|---|
| Add more check phases | Increases discovery, ratio worsens | Weight lower than auto-fix |
| Extend auto-fix to more phases | Increases resolution, ratio improves | Weight higher |
| Add cumulative knowledge (/why in fix) | Increases resolution quality per fix | Weight higher |
| Add concurrency safety (hook sync) | Reduces false-positive findings | Weight higher |

## Falsifier

This pattern would be wrong if the pipeline's resolution rate already
exceeds its discovery rate — i.e., if findings are being resolved faster
than they're found. In that case, adding more discovery is correct because
the pipeline can absorb the new findings.
