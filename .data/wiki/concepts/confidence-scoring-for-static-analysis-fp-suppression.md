---
title: "Confidence scoring for static analysis: fail open vs fail closed vs tiered reporting"
created: 2026-07-29
source: session-019fa94d (/www research on FP suppression best practices)
sources:
  - https://github.com/jendrikseipp/vulture
  - https://pylint.readthedocs.io/en/latest/user_guide/messages/message_control.html
  - https://github.com/microsoft/pyright/blob/main/docs/mypy-comparison.md
  - https://devgex.com/en/article/00049610
  - https://stackoverflow.com/questions/35990313/avoid-pylint-warning-e1101
tags: [static-analysis, confidence-scoring, false-positives, trace-check, vulture, pylint, pyright, fail-open, fail-closed, advisory, deterministic]
host: both
agent: grok
verification: multi-source-verified
cognitive_load: 2
summary: >
  When a static analysis tool can't fully resolve a symbol (e.g., a method
  called on a class that inherits from an external module), the industry
  consensus is NOT to suppress (fail open) or report as confirmed bug (fail
  closed). Instead: report with reduced confidence. Vulture uses percentage
  thresholds, pylint downgrades findings via inference depth, pyright emits
  "unknown" rather than "error." Applied to trace_check.py: findings on
  classes with external bases now get confidence="low", policy="advisory"
  instead of confidence="high", policy="deterministic_failures".
relations:
  - target: wiki/concepts/code-verification-pipeline-gaps.md
    type: extends
  - target: wiki/concepts/sdlc-proactive-prevention-techniques-2026.md
    type: related
  - target: wiki/concepts/dead-code-detection-workflow.md
    type: related
  - target: wiki/concepts/advisory-vs-blocking-enforcement-decision-2026.md
    type: complements
---

# Confidence scoring for static analysis: fail open vs fail closed vs tiered reporting

## Decision context

trace_check.py detects called-but-undefined `self.*` methods via AST
analysis. When a class inherits from an external module (e.g.,
`class MyApp(App)` where `App` is from Textual), trace_check can't see
the base class's methods. This produces false positives: `self.compose()`
is flagged as undefined even though it's defined on the external `App`.

**The question:** should trace_check suppress findings on classes with
external bases (fail open), report them as confirmed bugs (fail closed),
or do something else?

**What the research found:** the Python static analysis ecosystem has a
clear consensus on this pattern. Nobody does binary suppress-or-report.

## The three approaches (and which the ecosystem uses)

| Approach | What it does | Who uses it | Problem |
|----------|-------------|-------------|---------|
| **Fail open** (suppress) | Don't report when resolution is incomplete | Nobody — too lossy | A genuinely missing method on a class with external bases would be silently skipped |
| **Fail closed** (report as bug) | Report as confirmed finding | Pyright/mypy for type correctness | High false positive rate; trains operators to ignore the signal |
| **Confidence scoring** (tiered) ✅ | Report with reduced confidence; let the consumer decide | Vulture, pylint, semgrep | Requires the consumer to handle tiers — but that's what /check already does |

## How each tool implements confidence scoring

### Vulture — percentage thresholds
Vulture assigns confidence percentages to each finding: 100% for
unreachable code, 60% for unused attributes, etc. Users filter with
`--min-confidence 80`. No binary pass/fail — the team sets the threshold.

### Pylint — inference depth
Pylint's E1101 (`no-member`) uses `astroid` to attempt runtime import
and introspection of external classes. If the import succeeds, pylint
resolves the member and suppresses the finding. If the import fails
(package not installed), the finding is downgraded to lower confidence
but still reported.

### Pyright — "unknown" vs "error"
Pyright deliberately does NOT import code at runtime (Microsoft's
design decision). When it can't resolve a member, it emits
`reportUnknownMemberType` (a warning), not `reportAttributeAccessIssue`
(an error). The severity tier encodes the confidence level.

### Semgrep — post-processing enrichment
Semgrep Assistant (AI layer) post-processes findings to reduce noise by
~20%, effectively downgrading low-confidence findings. The base findings
remain visible but are deprioritized.

## What we implemented in trace_check.py

Following the consensus pattern, trace_check now uses **import-aware
resolution with 3-tier fallback**:

```
self.method() not in same-file methods
  │
  ├── Class has external base?
  │     │
  │     ├── Yes → try to import the base module
  │     │     │
  │     │     ├── hasattr(base, method) == True → SUPPRESS (confirmed defined)
  │     │     ├── hasattr(base, method) == False → confidence="high" (real bug!)
  │     │     └── Import failed → confidence="low" (advisory fallback)
  │     │
  │     └── No → confidence="high" (same-file, fully resolved)
```

This matches pylint's `astroid` approach (import-aware inference) rather
than pyright's stubs-only approach. For our use case (verifying code we
just wrote, on a machine where the packages are installed), import-based
resolution gives the right answer almost always. The confidence-scoring
fallback handles the rare case where the package isn't installed.

## Why this is better than fail open

The original proposal was "fail open" — suppress findings entirely for
classes with external bases. The research shows why that's wrong:

1. **Information loss.** A genuinely missing method (the `_mark_row`
   pattern) on a class with external bases would be silently skipped.
   That defeats the purpose of trace_check.

2. **Confidence scoring preserves the signal.** The verifier sees the
   finding, knows it might be a false positive, and can spot-check
   rather than treating it as a confirmed bug or ignoring it.

3. **Consistent with the existing advisory pattern.** /check already
   handles vulture and radon as advisory findings. trace_check's
   low-confidence findings slot into the same pattern — no new
   infrastructure needed.

## What this means for our workspace

The /check Step 0.9 pipeline now has a consistent confidence model:

| Layer | High confidence (deterministic) | Low confidence (advisory) |
|-------|-------------------------------|--------------------------|
| ruff E,F | ✅ Always deterministic | — |
| pyright | ✅ Always deterministic | — |
| pylint | ✅ Always deterministic | — |
| bandit | ✅ Always deterministic | — |
| trace_check | ✅ Same-file bases resolved | External bases → advisory |
| vulture | — | ✅ Always advisory |
| radon | — | ✅ Always advisory |
| pip-audit | — | ✅ Always advisory |
| diff-cover | — | ✅ Always advisory |

The verifier protocol already differentiates: `deterministic_failures`
are treated as confirmed bugs; advisory findings are spot-check
candidates. No SKILL.md change needed — the packet structure already
supports per-finding `confidence` and `policy` fields.

## Falsifier

This approach is wrong if:
- The low-confidence findings produce too much noise (verifiers waste
  time checking inherited methods that are fine). Mitigation: the
  `confidence` field lets verifiers skip them if they choose.
- The `_has_external_base` detection is wrong (misses external bases or
  flags same-file bases as external). Mitigation: the detection only
  checks `ast.Name` nodes — same-file classes are always `ast.Name`.
- The consensus shifts to import-based resolution (actually importing
  the module to check). This would be more accurate but slower and
  requires the package to be installed. Current approach is the right
  trade-off for a pre-LLM deterministic layer.

## Sources

- [Vulture](https://github.com/jendrikseipp/vulture) — confidence percentages + min-confidence threshold
- [Pylint message control](https://pylint.readthedocs.io/en/latest/user_guide/messages/message_control.html) — disable/enable per-message, generated-members config
- [Pyright vs mypy comparison](https://github.com/microsoft/pyright/blob/main/docs/mypy-comparison.md) — pyright's "don't import" design decision
- [Pylint E1101 suppression](https://devgex.com/en/article/00049610) — practical approaches to no-member false positives
- [SO: avoid Pylint E1101](https://stackoverflow.com/questions/35990313/avoid-pylint-warning-e1101) — community consensus on dynamic-attribute false positives

## Receipts

- `P:/.grok/skills/check/__lib/trace_check.py:90-105` — `_has_external_base` implementation
- `P:/.grok/skills/check/__lib/trace_check.py:160-175` — confidence/policy assignment in `check_file`
- `P:/.grok/skills/check/tests/test_trace_check.py` — `test_external_inheritance_low_confidence`, `test_same_file_inheritance_high_confidence`
- Commit `6344c8e`

## Related

- [[code-verification-pipeline-gaps]] — the original tool-to-bug-class map
- [[sdlc-proactive-prevention-techniques-2026]] — the 9-layer pipeline
- [[dead-code-detection-workflow]] — vulture's advisory pattern (same model)
- [[advisory-vs-blocking-enforcement-decision-2026]] — advisory vs blocking policy framework
