---
title: "Tool fallbacks as index, not authority — quick-reference tables cross-reference wiki"
slug: tool-fallbacks-as-index-not-authority
created: 2026-07-31
source: session-20260731
tags: [tool-fallbacks, model-pool, groq, structural-pattern, knowledge-management, operator-correction]
summary: >
  Known-broken model exclusions lived in 4 wiki concepts but were absent from
  the tool-fallbacks.md quick-reference table, causing 3 failed Groq spawn
  dispatches. The fix: tool-fallbacks.md should be a concise index (1-line
  symptom + 1-line workaround + wiki authority link), not a duplicate of
  wiki root-cause detail. The pattern generalizes: fast-decision tables point
  to wiki authority; wiki concepts hold the evidence.
agent: grok
host: grok
cognitive_load: 2
verification: observed
relations:
  - target: wiki/concepts/groq-free-tier-tpm-limit-6000.md
    type: related
  - target: wiki/concepts/coding-model-pool-tier-1-tier-2.md
    type: related
  - target: wiki/concepts/model-benchmark-testing-quirks.md
    type: related
  - target: wiki/concepts/wiki-integrated-skills-query-save-pattern.md
    type: extends
---

# Tool fallbacks as index, not authority

## Decision context

**The problem:** The operator dispatched 3 subagents to `model=groq-gpt-oss-120b`
for a `/www` research task. All 3 failed instantly (0.7s each) with HTTP 413
TPM limit — Groq's free tier caps at 8,000 tokens per minute, but Grok Build's
system prompt alone is ~54,000 tokens.

**The operator's correction:** "I thought we took groq out of the pool because
of the rate limit problems."

They had. The Groq exclusion was documented in **four separate wiki concepts**:
`[[groq-free-tier-tpm-limit-6000]]`, `[[coding-model-pool-tier-1-tier-2]]`,
`[[fleet-benchmark-results-2026-07-29]]`, and `[[model-benchmark-testing-quirks]]`
Quirk 5. But `tool-fallbacks.md` — the file agents consult before dispatching —
had **no Groq entry at all**.

## The structural pattern

**Fast-decision tables and wiki authority serve different purposes:**

| Layer | Purpose | Shape | When consulted |
|---|---|---|---|
| `tool-fallbacks.md` | Fast pre-dispatch check | 1-line symptom + 1-line workaround + wiki link | Before every spawn_subagent |
| Wiki concepts | Root cause, evidence, verification history | Full analysis with receipts, dates, test results | When the table's 1-line summary is insufficient |

**The failure mode:** when the fast-decision table duplicates wiki detail
instead of referencing it, two problems emerge:
1. **Staleness** — the table and wiki drift apart as one is updated and the other isn't
2. **Absence** — new exclusions get added to wiki (where the investigation happens) but never propagate to the table (which requires a separate edit)

The fix is structural: the table should **only** contain the minimum needed
for a fast decision (symptom, workaround, authority link), and should
explicitly cross-reference the wiki concept(s) that hold the detail.

## The restructured tool-fallbacks.md

After the fix, `tool-fallbacks.md` was restructured into:

- **CLI fallback table** (unchanged — built-in tool failures)
- **spawn_subagent exclusions** — models that CANNOT be spawned, with 1-line symptom + wiki authority
- **spawn_subagent limitations** — models that spawn but have constraints
- **web_search rate limiting** — per-model rate limit patterns
- **CLI caller errors** — not model bugs

Each entry has exactly: symptom (1 line), workaround (1 line), wiki authority
link. The wiki concepts hold the root cause, test results, and evidence.

**Key additions:**
- Groq exclusion entry with links to 4 wiki concepts
- Step 6 in usage instructions: "Before assigning `model=`, read `[[coding-model-pool-tier-1-tier-2]]`"

## Why this generalizes

This pattern applies to any two-layer knowledge system where:
- A fast-decision layer exists (checklist, table, quick-reference)
- A deep-knowledge layer exists (wiki, documentation, analysis)
- The two layers can drift apart

The rule: **the fast layer indexes; the deep layer authorizes.** When they
disagree, the deep layer wins — update the fast layer.

This is the same principle as `[[wiki-integrated-skills-query-save-pattern]]`:
skills query the wiki at runtime rather than hardcoding knowledge. The
tool-fallbacks table is the manual equivalent — it should point to wiki, not
duplicate it.

## What this means for our workspace

1. **`tool-fallbacks.md` is now an index.** 13 wiki cross-references added;
   stale duplicate detail removed.
2. **Before dispatching subagents, check the spawn_subagent exclusions table.**
   It's organized by failure type for fast scanning.
3. **When a new model exclusion is discovered**, add it to BOTH the wiki
   concept (root cause) AND the tool-fallbacks table (1-line entry + wiki link).
4. **The pattern applies to other fast-decision tables** — any quick-reference
   that duplicates wiki detail should be refactored to cross-reference instead.

## Falsifier

This pattern is wrong if:
- The wiki cross-references in tool-fallbacks.md become stale (wiki concepts
  renamed or deleted without updating the table).
- Agents consistently need to read the full wiki concept anyway (the 1-line
  summary is insufficient for decisions).
- A different structure (e.g., auto-generated table from wiki metadata) would
  be more reliable than manual cross-referencing.

## Receipts

- **Groq dispatch failure:** 3 subagents spawned to `groq-gpt-oss-120b`,
  all failed with HTTP 413 TPM limit (0.7s each, 0 tool calls). Session 019fba58.
- **Wiki concepts with Groq exclusion:** 4 concepts found via grep — all
  documented the exclusion but none were consulted before dispatch.
- **tool-fallbacks.md before fix:** 0 wiki cross-references, 0 Groq entry.
- **tool-fallbacks.md after fix:** 13 wiki cross-references, Groq entry with
  links to all 4 concepts. Committed `efd8930`.

## Auto-related

- [[skill-graph]]
- [[portable-ai-brain-pattern]]
- [[skill-catalog]]
- [[router-proxy-tool-calling-normalization-patterns]]
- [[model-tool-calling-capability-matrix]]

