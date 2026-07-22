---
created: '2026-07-21'
sources:
- Session 019f8155-f901-79a2-9ba1-ac4614db5225 (2026-07-20/21)
- /red-team run on proposal-grounding-monitor (critic.json at P:\.claude\.artifacts\...)
summary: 'When a review flags a calibration concern (regex too broad, pattern too narrow), verify against real corpus data before acting. Theoretical concerns often produce 0 empirical FPs/FNs.'
tags:
- calibration
- empirical
- review
- false-positive
- false-negative
- lesson
verification: observed
cognitive_load: 3
host: grok
agent: grok
---

# Empirical calibration over theoretical review concerns

## The lesson

When a review (e.g., `/red-team`, `/review`) flags a calibration concern — "this regex is too broad," "this hedge suppresses real proposals," "this pattern produces false positives" — **verify the concern against real corpus data before acting on it**. Theoretical analysis identifies potential failure modes; only empirical testing tells you whether they actually fire.

## The incident

The `/red-team` run on `proposal-grounding-monitor` flagged two calibration items as REVISE:

1. **IA-004**: "PROVISIONAL_HEDGE_RE includes common words 'likely' and 'probably' — false-negative risk." The /red-team verified that `'It is likely that I recommend building an MCP server'` is suppressed by `'likely'` even though it contains a real proposal.
2. **GR-2**: "Proposal-detection regex fires on four classes of analytical/generic-procedural statements."

Both findings were **correct in theory** — the regex does over-match those patterns in isolation.

But when tested against **7306 real assistant responses** extracted from 469 session transcripts:

- **IA-004**: 370 responses were hedge-suppressed. **0** of those contained actual proposal patterns. The false-negative rate from over-broad hedging was **0%**. The theoretical concern did not manifest in practice.
- **GR-2**: 13 responses were flagged. **All 13** were false positives (status reports, retractions, inventories). Precision was **~0%**. The theoretical concern was confirmed, and the fix (dropping 2 patterns) reduced FPs by 46%.

## The pattern

Review findings come in two flavors:

| Type | What the review says | What to do |
|---|---|---|
| **Structural defect** | "This code path can produce wrong output" | Fix it — the concern is deterministic |
| **Calibration concern** | "This regex/pattern *might* over-match or under-match" | **Verify against real data first** |

Calibration concerns need empirical evidence because the actual FP/FN rate depends on the distribution of real inputs — something the reviewer cannot see from the code alone.

## How to verify

On Grok Build, session transcripts at `~/.grok/sessions/<encoded-cwd>/<session-id>/chat_history.jsonl` contain every assistant response from every session. These ARE the calibration corpus:

1. Extract assistant text responses (strip `<think>` blocks)
2. Run the regex/hedge check against each
3. Compute the actual FP/FN rate
4. Only tighten/loosen the regex if the empirical rate is unacceptable

The extraction script pattern is reusable — see `P:\tmp\extract_corpus_v2.py` for the template.

## Related

- [[plausible-narratives-substitute-for-verification]] — the general principle that narrative reasoning ≠ empirical evidence
- [[testing-methodology-both-outcomes-informative]] — both confirmations and refutations are valuable
- [[evidence-first-default-and-needless-confirmation]] — evidence-first stance
- proposal-grounding-monitor calibration handoff at `P:\docs\handoffs\pgm-calibration-and-monitoring-20260721\HANDOFF.md`

## Auto-related

- [[multi-agent-correlated-errors]]

