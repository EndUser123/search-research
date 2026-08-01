---
title: "Trusted exit-status fallacy: pipeline ground truth is the artifact, not the exit code"
created: 2026-07-26
source: dream-2026-07-26
tags: [verification, pipeline, ground-truth, exit-status, silent-failure, tooling-trust]
agent: grok
host: both
cognitive_load: 2
summary: >
  When a downstream consumer (tool, skill check, or model) trusts a pipeline's
  exit-0 or summary field without reading the actual artifact, silent failures
  propagate undetected. The pipeline no-op'd, stale-cached, scanned the wrong
  window, or queried the wrong path — but reported success. Ground truth is
  always the artifact on disk. Five independent instances across sessions
  019f94c9, 019f9b00, 019f9bfe. Structural fix: downstream checks grep the
  artifact directly; never trust a summary field as a proxy for artifact state.
---

# Trusted exit-status fallacy

## Decision context

**Problem:** multiple workspace tools report success via exit codes or summary
fields. Downstream consumers — other tools, skill phase checks, or the model
itself — trust those signals. When the upstream tool silently no-ops, scans
the wrong window, or queries the wrong registration path, the downstream
consumer propagates the false success. The failure is invisible until the
operator catches a downstream symptom (missing wiki log entry, wrong
transcript loaded, false "hooks not firing" conclusion).

**Root shape:** exit-status and summary fields are *proxies* for artifact
state. They are cheap to produce and cheap to consume, which is why tools use
them. But proxies degrade silently — the upstream tool has no incentive to
report its own failure accurately when the failure path itself is the bug
(the 200-line scan window, the wrong config path, the mtime race).

## Key findings

### The failure shape (5 instances, 3 sessions)

| Instance | Upstream tool | False signal | Downstream consumer | Ground truth |
|---|---|---|---|---|
| wiki_log_append silent skip | `wiki_log_append.py` | `{"ok": True, "skipped": "..."}` | `wiki_ingest.py` reports `5_log_append: ok` | grep `log.md` for the slug |
| /close Phase 8.5 | recency heuristic | "all clear" | model emits close summary | grep `log.md` for concept filename |
| /aar Phase 8.5 | same recency heuristic | "all clear" | model skips log-backfill | same |
| receipt_shadow_evaluation | config-path check | `hook_registration_status: not_registered` | agent concludes "hooks not firing" | glob `verification-receipts.json` |
| /check transcript discovery | mtime sort | "found transcript" | model reads wrong session | deterministic path from session ID |

### Why exit-status trust is structurally unreliable here

1. **The upstream tool's failure IS the bug.** The 200-line window in
   `wiki_log_append.py` is not a reported error — it's a silent design limit.
   The tool has no way to signal "I couldn't verify because my window is too
   small." It returns ok-skip.
2. **Summary fields are write-cheap, read-cheap, verify-expensive.** The
   downstream consumer would have to re-do the work to verify the summary.
   The economic pressure is toward trust.
3. **Concurrent activity breaks recency heuristics.** On a multi-agent host,
   "the last log entry is recent" does not mean "the concept I just created
   was logged" — another agent may have logged something else in the same
   minute.

### Structural fix

Downstream checks must grep the artifact directly. The pattern:

- **Wrong:** "did the pipeline report ok?" → trust exit-0
- **Wrong:** "is the last log entry recent?" → trust recency
- **Right:** "does `log.md` contain a line matching `<concept-slug>` in the
  last N lines?" → grep the artifact
- **Right:** "do `verification-receipts.json` files exist?" → glob the
  artifact, don't check config registration

This is the tooling-level analog of `verification-state-tracking-content-
identity-vs-temporal-proxies` (which covers content-hash vs mtime for
verification tracking). That concept covers *how to track* verification
state; this concept covers *what to trust* as ground truth.

## Related

- [[verification-state-tracking-content-identity-vs-temporal-proxies]] — content hash vs mtime (adjacent)
- [[scope-matching-verification-discipline]] — self-verification ceiling (adjacent)
- [[documented-deferral-substitutes-for-action]] — model stated intent (different class)
- [[causal-mechanism-claims-require-source-receipts-before-durable-write]] — receipt discipline

## Falsifier

This finding is wrong if: the 5 instances above are actually instances of 5
different root causes (not one pattern), OR if a single structural fix (e.g.,
making all tools return structured artifacts instead of exit codes) would not
have caught all 5. Test: propose one fix and check whether it covers all 5.

## Receipts

- `P:/docs/handoffs/wiki-log-append-silent-skip-20260726/HANDOFF.md:34-60` — wiki_log_append.py 200-line scan window, silent skip returns ok
- `P:/docs/handoffs/multi-terminal-auto-commit-20260725/HANDOFF.md` — receipt_shadow_evaluation config-path check vs actual receipt files (receipt-system corrected state)
- `P:/.grok/skills/close/__lib/close_accounting.py:1708-1714` — retrospective gate sets needs_attention; `:2179-2189` — loop.needed computation
- `P:/.grok/skills/close/__lib/receipt_shadow_evaluation.py:228` (now fixed) — `"registered" if receipt_records else "not_registered"` per-session proxy for workspace-level invariant
- `P:/.grok/skills/check/SKILL.md` Step 0.9 — transcript race fix (deterministic path from session ID replaces mtime sort)
- Session 019f94c9 receipt-system investigation (compaction summary) — 31 receipt files existed despite "not_registered" report

## Sources

- `P:/docs/handoffs/wiki-log-append-silent-skip-20260726/HANDOFF.md:34-60`
- `P:/docs/handoffs/multi-terminal-auto-commit-20260725/HANDOFF.md` (receipt-system corrected state)
- Session 019f94c9 compaction summary (receipt-system investigation + /check transcript race)
- `P:/.grok/skills/check/SKILL.md` Step 0.9 (transcript race fix)
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
