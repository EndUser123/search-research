---
title: "Prior-session facts vs this-session facts: re-probe before asserting as current state"
created: 2026-08-09
source: session-2026-08-09 (deepseek-v4-flash correction incident)
tags: [epistemic-discipline, tool-fallbacks, evidence-first, re-probe, transferable-pattern, anti-narrative-sufficiency]
summary: >
  Tool-fallbacks entries and other "known-broken" wiki rows are [PRIOR_SESSION_FACT], not
  [THIS_SESSION_FACT]. When asserting a model/tool is currently broken, re-probe via the
  same access path the wiki entry used. Re-probing flipped the answer on 2026-08-09:
  zen-deepseek-v4-flash-free was documented "serde-broken" but actually WORKS via direct PI
  (only Grok Build spawn_subagent transport is broken). The "all three DeepSeek V4 Flash
  slugs are broken" claim was wrong because it trusted prior-session entries without
  re-probing. Receipts from this session always beat narratives from prior sessions.
agent: grok
host: grok
cognitive_load: 1
verification: directly-verified
confidence: 0.95
half_life_days: 365
last_verified: 2026-08-09
relations:
  - target: wiki/concepts/tool-fallbacks.md
    type: refines
  - target: wiki/concepts/deepseek-region-optin-failure-pattern.md
    type: extends
  - target: wiki/concepts/narrative-as-signal.md
    type: extends
---

# Prior-session facts vs this-session facts: re-probe before asserting as current state

## Decision context

On 2026-08-09, the operator hit a 403 RegionError selecting `go-deepseek-v4-flash`. I summarized the situation as "all three DeepSeek V4 Flash slugs are now in some state of broken" — citing `tool-fallbacks.md` entries for `zen-deepseek-v4-flash-free` (serde-broken) and `nim-deepseek-ai-deepseek-v4-flash` (EOL), plus the new `go-*` region error.

The operator pushed back: *"you don't know they won't work unless you try them with PI."*

I ran direct PI probes on all three slugs. Results:

| Slug | Wiki said | PI probe result |
|---|---|---|
| `go-deepseek-v4-flash` | (new failure) | 403 RegionError — wiki was right |
| `nim-deepseek-ai-deepseek-v4-flash` | EOL 2026-08-07 (HTTP 410) | 410 Gone — wiki was right |
| `zen-deepseek-v4-flash-free` | serde-broken | **Exit 0, response "OK" in 32.4s — wiki was WRONG** |

The wiki entry for zen actually said "Works via PI and direct HTTP" — I had missed that nuance and treated "serde-broken" as "fully broken." The serde-broken label is specific to the Grok Build spawn_subagent transport, not a universal failure. My "all three are broken" claim conflated two transports (spawn_subagent vs PI direct).

## The pattern

**Wiki/tool-fallbacks entries are [PRIOR_SESSION_FACT].** They were verified by a prior session at a point in time. Conditions change:

- Models EOL and recover (NVIDIA brought deepseek-v4-flash back once before)
- Serde incompatibilities get fixed (Grok Build updates its deserializer)
- Region policies shift (the China-hosted toggle incident)
- Quota states cycle (trial keys reset, subscriptions renew)

**Before asserting a wiki entry as current state**, re-probe via the same access path the wiki entry used. The probe cost is low (seconds to tens of seconds). The cost of asserting a stale entry as fact is high: the operator gets a wrong answer and has to push back, burning a turn.

## How to apply

When you find yourself about to state "X is broken" or "X doesn't work" based on a wiki entry:

1. **Check the entry's verification field.** `verification: directly-verified` means the prior session actually ran the probe. `verification: inferred` means it didn't.
2. **Check the entry's last_verified date.** If >30 days ago for a fast-moving category (model routing, quota, region policy), treat as [PRIOR_SESSION_FACT] pending re-probe.
3. **Re-probe if the claim is load-bearing.** "Load-bearing" = the operator will make a decision based on it. If you're just context-setting, no probe needed.
4. **Label honestly.** "Wiki says X (verified YYYY-MM-DD); not re-probed this session" is honest. "X is broken" without that qualifier is overclaiming.

## What this means for our workspace

1. **tool-fallbacks.md entries need a `last_verified` field** that agents check before citing. Many entries have receipts but no date; the date is the load-bearing signal for staleness.

2. **The convergence of two facts is the warning sign.** When you're about to claim "X is broken AND Y is broken AND Z is broken" (multiple independent prior-session entries, no re-probe), treat the conjunction as suspicious — each entry may be narrowly true under specific conditions that don't hold for your current claim.

3. **Transport-specific failures (serde-broken, spawn_broken) are NOT universal failures.** Always ask: "broken under what transport? PI direct? spawn_subagent? CLI? HTTP?" The wiki entry should specify; if it doesn't, the entry is under-specified and the agent should re-probe on the relevant transport.

4. **The I-CALM framing applies.** Stating an unverified claim as fact = -2 penalty. Abstaining ("wiki says X but I haven't verified this session") = +0. Re-probing and stating correctly = +2.

## Reference incident

**Session 2026-08-09, the deepseek-v4-flash correction:** I claimed "all three DeepSeek V4 Flash slugs are broken" based on tool-fallbacks entries. The operator pushed back. Direct PI probes showed zen works via PI. The wiki entry for zen had documented this ("Works via PI and direct HTTP") but I had missed the nuance. The correction produced stronger output (RFC 9110 receipts, fleet-models.json receipts, verbatim error text with the opt-in URL the operator had missed).

The pattern: I treated prior-session entries as this-session facts without re-probing. The fix: re-probe before asserting, especially when the claim is a conjunction across multiple entries.

## Falsifier

This finding is wrong if:

- Re-probing tool-fallbacks entries produces the same answer ≥95% of the time (the entries are reliably current; re-probing is wasted effort). If a 20-entry sample shows ≥19 still accurate, the pattern is weaker than claimed.
- The workspace adopts a different staleness signal (e.g., automatic `last_verified` refresh on every successful probe) that makes the manual re-probe rule unnecessary. If the tooling closes the gap, this concept becomes obsolete.

## Sources

- Session 2026-08-09 transcript — operator pushback "you don't know they won't work unless you try them with PI"
- `P:/.data/wiki/concepts/tool-fallbacks.md` — entries for `zen-deepseek-v4-flash-free`, `nim-deepseek-ai-deepseek-v4-flash`, `go-deepseek-v4-flash` (post-correction)
- `P:/.data/wiki/concepts/deepseek-region-optin-failure-pattern.md` — the corrected entry with PI probe receipts
- [[narrative-as-signal]] — the broader pattern: plausible narrative substituting for reading the actual evidence

## Auto-related

- [[skill-catalog]]
- [[sdlc-workflow-improvements-from-session-019fdf3d]]
- [[skill-graph]]
- [[tool-fallbacks]]
- [[model-quota-contention-coordination-fleet-rate-limiting]]

