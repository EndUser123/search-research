---
title: "Operator model routing directives — confirmed preferences"
created: 2026-07-27
source: session-019fa48a (/why on missed opencode/PI preference)
tags: [operator-directive, routing, model-selection, policy, nemotron, opencode, openrouter, capture-failure-fix]
summary: >
  Confirmed operator directives on model routing, transport selection, and
  provider preference. Every routing recommendation MUST check this concept
  first. Extracted from session transcripts by extract_operator_directives.py
  and curated by the operator. The structural fix for "why didn't you know
  something you should have known" — operator preferences stated in sessions
  are promoted here so future sessions find them without transcript mining.
cognitive_load: 1
verification: operator-confirmed
host: both
agent: grok
sources:
  - "session-019fa48a (operator directive 2026-07-27)"
  - "session-019f9bfe (cross-transport test directive 2026-07-26)"
  - "session-019f9f48 (operator directive 2026-07-26)"
  - "P:/.agents/scripts/extract_operator_directives.py (mechanical extraction)"
relations:
  - target: wiki/concepts/model-tool-calling-capability-matrix.md
    type: companion
  - target: wiki/concepts/model-pool-selection-policy-speed-quota-diversity.md
    type: related
---

# Operator model routing directives

> **Before recommending ANY model routing, transport, or provider default,
> query this concept first.** If a directive exists here, honor it. If not,
> ask the operator before recommending — do not assume "no directive" means
> "any option is fine."

## Decision context

Session 019fa48a: the operator said "I told you that before" when I recommended
OpenRouter for Nemotron routing. The preference (use opencode/PI, avoid
OpenRouter) had been stated in prior sessions but was never promoted to a
durable artifact. I couldn't find what wasn't captured. This concept is the
structural fix (see [[mechanical-enforcement-over-behavioral-reminder]] for the
architectural decision behind it): it is the single place where confirmed
operator routing directives live, queryable by qmd, loadable by any session.
It complements [[model-tool-calling-capability-matrix]] (technical capability)
and [[model-pool-selection-policy-speed-quota-diversity]] (cost/quota routing).

**The capture mechanism:** `P:/.agents/scripts/extract_operator_directives.py`
scans prior session transcripts for operator-stated preference/directive
language and outputs candidates for promotion. Run it after major routing
decisions or periodically to catch directives that haven't been promoted yet:

```bash
python P:/.agents/scripts/extract_operator_directives.py --days 90 --min-score 2
# Output: P:/tmp/operator-directive-candidates.md (review for promotion)
```

## Confirmed directives

### D1: Nemotron routing — opencode → PI → OpenRouter (last resort)

**Directive (operator, 2026-07-27):** "We are not tied to spawn_subagent. We
should use opencode and PI when needed. We should not use OR unless we have
to or I explicitly ask."

**Routing order:**
1. **opencode CLI** — `opencode run -m opencode/nemotron-3-ultra-free "<prompt>"`
2. **PI CLI** — `pi -p --provider nvidia --model nvidia/nemotron-3-ultra-550b-a55b --thinking off --no-session "<prompt>" --mode json`
3. **OpenRouter via spawn** — `spawn_subagent(model="or-nemotron-ultra-free")` — **last resort, explicit operator approval only**

**Never for spawn:** `nvidia-nemotron-3-ultra` (serde broken), `zen-nemotron-3-ultra-free` (serde broken).

**Underlying principle:** prefer direct provider relationships over intermediary proxies. OpenRouter adds a dependency layer; opencode and PI reach Nvidia's inference directly.

### D2: Kimi K3 — NOT in any auto-pool

**Directive (operator, 2026-07-26):** K3 is not in any auto-pool. Manual/deliberate tasking only.

**Reasons:** (1) cost — single spawn test = ~20% of monthly OpenCode-Go quota; (2) reliability — spawn-path failure unresolved.

**Status (2026-07-27):** root cause was wrongly attributed to `top_p`; actual cause is transport/header level. Testing deferred until ~2026-08-07 (operator directive — quota preservation).

### D3: Prefer direct provider over intermediary (general principle)

**Directive (operator, 2026-07-27):** "I'd prefer to not use OpenRouter as the primary choice. I'd rather use nvidia as the inference provider over OpenRouter."

**Application:** when multiple transports reach the same model, prefer the one with the fewest intermediaries. Direct API > provider CLI > proxy/spawn. This applies broadly, not just to Nemotron.

## How to add new directives

1. Operator states a preference in a session
2. At session close (`/close`) or when the preference is recognized, promote it here
3. Format: `### D<N>: <topic> — <one-line summary>` + the verbatim quote + the routing order/constraint
4. Run the extractor periodically to catch anything missed: `python P:/.agents/scripts/extract_operator_directives.py`

## Falsifier

This concept is wrong if:
- A directive here is overturned by a newer operator statement (update immediately)
- The extractor consistently misses real directives (tighten the scoring patterns)
- A directive here is so stale it no longer applies (e.g., Grok Build fixes the serde bug and the Nemotron routing order changes)
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
