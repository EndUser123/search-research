---
title: "Three-tier hedge detection: regex + structural parser + NLTK POS for Stop hooks"
created: 2026-08-13
source: session-20260813
tags: [uncertainty, hedging, hook-design, nltk, pos-tagging, regex, stop-hook, architectural-decision]
summary: >
  Architectural decision for the uncertainty_gate Stop hook: three-tier pipeline
  (regex candidate detection + markdown structural filtering + NLTK POS
  disambiguation) instead of pure regex or spaCy/LLM. The regex layer finds
  candidates instantly; structural filtering suppresses code blocks, tables,
  and examples; NLTK POS tags resolve polysemy and run only when candidates
  exist (~50-100ms, zero cost on clean turns). spaCy was rejected because its
  200-2000ms cold-start penalty is unacceptable for a per-turn Stop hook
  subprocess. LLM-based detection was rejected for latency + cost.
agent: grok
host: grok
cognitive_load: 3
verification: tested
relations:
  - target: wiki/concepts/llm-uncertainty-hedging-detection-research-landscape.md
    type: refines
  - target: wiki/concepts/grok-hook-command-env-var-preflight.md
    type: related
  - target: wiki/concepts/claims-require-receipts.md
    type: extends
---

# Three-tier hedge detection for Stop hooks

## Decision context

The uncertainty_gate Stop hook catches hedging adjacent to factual claims in
agent output — the linguistic signal that the agent is inferring rather than
verifying. The original implementation used pure regex with context-window
suppression patterns. Three gaps surfaced in session 20260813:

1. **Pattern gap:** standalone "likely" + verb ("Grok likely ignores it") was
   not caught — only "likely because" (hedge + causal connector) matched.
2. **Quoted-example false positives:** when the agent quoted what the regex
   catches ("catches 'maybe 5 RPM'"), the hook fired on its own examples.
3. **Context blindness:** regex can't tell whether "likely" is assertive
   ("likely broken") or exploratory ("we should likely consider").

The question: what architecture replaces pure regex without adding the latency
of spaCy (200-2000ms cold start) or an LLM call (500ms-4s)?

## The decision: three-tier pipeline

### Tier 1 — Structural filtering (instant, runs on every message)

A single-pass line walker tags every character offset with its markdown
context type: `code_block`, `blockquote`, `table`, `example`, or `prose`.
Matches inside non-prose contexts are suppressed before any further analysis.

This replaces the old approach of stripping code blocks with regex (which
left inline code, tables, and example lists unhandled).

### Tier 2 — Regex candidate detection (instant, runs on every message)

Four regex patterns find hedge-word candidates:
- `HEDGE_PLUS_NUMBER` — hedge + bare number ("maybe 5 RPM")
- `HEDGE_PLUS_CAUSAL` — hedge + causal connector ("likely because")
- `HEDGE_PLUS_FACTUAL` — first-person hedge + factual assertion ("I think this is a problem")
- `HEDGE_PLUS_VERB` (added in this revision) — standalone hedge + verb ("likely ignores", "probably isn't")

If no candidates exist after structural filtering, the hook exits — NLTK
never loads. This is the fast path for clean turns.

### Tier 3 — NLTK POS disambiguation (~50-100ms, only when candidates exist)

When tiers 1+2 produce candidates in prose context, NLTK's averaged perceptron
POS tagger resolves polysemy:
- "about" as `RB` (adverb = approximator hedge) vs `IN` (preposition = topic)
- "may" as `MD` (modal = hedge) vs `NN` (noun = month)
- "pretty" as `RB` (adverb = hedge) vs `JJ` (adjective = not hedge)

NLTK 3.9.2 was already installed with `punkt` and `averaged_perceptron_tagger`
data packages. No additional dependencies needed.

Additionally, a full-sentence `INLINE_EXAMPLE` check scans for markers
("catches", "for instance", "similarly", "would trigger", "would match")
that indicate the hedge word is being discussed rather than asserted. This
catches the false-positive class from session 20260813 where the agent
described what the regex catches.

## Steelman: why not spaCy?

spaCy with `en_core_web_sm` is the production-grade NLP choice. It provides
dependency parsing (scope detection), better POS accuracy, and `Matcher`/
`DependencyMatcher` for complex patterns. The CoNLL-2010 literature shows
shallow linguistic features (POS + dependency) with classifiers achieve
strong F1 (~0.88) on hedge detection.

**Why rejected:** spaCy cold-loads in 200-2000ms. The Stop hook spawns a new
Python subprocess per invocation, so every call is a cold load. Adding
200ms-2s of latency to every turn end is unacceptable. A persistent worker
process (like claude-mem's worker) would solve this, but adding worker
infrastructure for a Stop hook is more complexity than the problem warrants.

**When to revisit:** if the hook moves to a persistent-process architecture
(HTTP endpoint instead of subprocess), spaCy becomes viable and the NLTK tier
should be upgraded to spaCy for dependency-based scope detection.

## Steelman: why not pure regex with better patterns?

Adding more regex patterns (the v2 approach) closes individual gaps but
doesn't fix the structural problem: regex can't do polysemy resolution or
sentence-purpose classification. Each new hedge phrasing needs a new regex.
The INLINE_EXAMPLE list grows unboundedly. The maintenance burden increases
with every session as the agent's language varies.

**Why rejected as sole approach:** structurally limited. But regex is still
the right choice for tier 2 (candidate detection) because it's instant and
catches surface patterns reliably. The regex layer stays — it just can't be
the only layer.

## What this means for our workspace

- The hook at `~/.grok/hooks/scripts/uncertainty_gate.py` now uses three-tier
  detection. Backups: `.bak` (original pure-regex), `.bak2` (v2 regex+structural).
- Test suite at `P:/tmp/test_uncertainty_v3.py` — 17 tests across 6 groups.
- The NLTK dependency is already satisfied (3.9.2 + data packages).
- Other hooks on this host that need linguistic analysis should consider the
  same three-tier pattern: regex for speed, structural for context, NLP for
  disambiguation.
- The `[[groq-free-tier-tpm-limit-6000]]` concept documents the Groq free-tier
  constraint that is relevant to any hook considering LLM-based detection.
- Connects to `[[claims-require-receipts]]` — the uncertainty gate is the
  enforcement layer for the receipt principle at the linguistic level.
- Related to `[[narrative-as-signal]]` — hedge words are the linguistic
  signal that a narrative is being constructed rather than verified.

## Receipts

- `~/.grok/hooks/scripts/uncertainty_gate.py` — the three-tier implementation.
  Key functions: `build_context_map()` (tier 1), `detect_hedge_claim()` with
  4 regex patterns (tier 2), `_get_pos_tags()` + `POS_DISAMBIGUATION` dict
  (tier 3). Verified via test suite `P:/tmp/test_uncertainty_v3.py` (17/17
  passing, session 20260813).
- `~/.grok/hooks/scripts/uncertainty_gate.py.bak` — original pure-regex version
  (single `IN_CODE_BLOCK.sub()` strip, 3 regex patterns, context-window
  suppression). This is what failed in session 20260813.
- NLTK availability verified: `python P:/tmp/check_nltk.py` returned "NLTK
  3.9.2", "punkt: OK", "averaged_perceptron_tagger: OK".

## Falsifier

This architecture is wrong if:
1. NLTK POS tags are too inaccurate for disambiguation (high false-negative
   rate on real agent output). Test: run the hook against 50 real turns and
   measure precision/recall.
2. The 50-100ms NLTK load time is perceptible to the operator on every turn
   with a hedge candidate. Test: measure wall-clock time from Stop event to
   hook exit on turns with and without candidates.
3. A future Grok update adds async hook execution, making spaCy's cold-start
   penalty irrelevant. If so, upgrade tier 3 to spaCy.

## Sources

- Prince et al. (1982) hedge taxonomy — the linguistic foundation for hedge
  word categorization used in the regex patterns.
- CoNLL-2010 Shared Task (Farkas et al.) — benchmark showing shallow
  linguistic features (POS, lemmas, chunks) with SVM/CRF achieve strong F1
  on hedge detection without deep learning.
- Wall (UWL thesis) — spaCy POS + dependency + Decision Tree for hedge
  disambiguation, achieving ~0.88 F1.
- [[llm-uncertainty-hedging-detection-research-landscape]] — prior research
  synthesis that informed this implementation.

## Auto-related

- [[sdlc-workflow-improvements-from-session-019fdf3d]]
- [[parameter-aware-benchmark-tier-system]]
- [[predictable-enforcement-for-recommendation-commitment]]
- [[compaction-inherited-recommendation-decoupling]]
- [[skill-graph]]

