---
thread_id: q11-wiki-paragraph-additions-20260726
parent_handoff_path: none
current_session_id: 019f9bfe-1b89-7602-9384-0212224ff30b
current_terminal_id: P%3A%5C
produced_at: 2026-07-27T01:00:00Z
status: open
handoff_type: investigation
accurate_as_of_head: d6953c6b49598051f12467d2a68a1e568ae136bb
---

# Q11 uncaptured-knowledge additions — two paragraph additions to existing wiki concepts

## Objective

Add two paragraph-length sub-pattern entries to existing wiki concepts, capturing tacit knowledge from session 019f9bfe that the AAR's Q11 audit flagged as uncaptured. These are advisory (no runtime behavior change) but represent hard-won pattern distinctions that would cost significant effort to rediscover.

## Why paragraph additions and not new concepts

Both sub-patterns are refinements of patterns already documented in existing wiki concepts. New concepts would create overlap; paragraph additions extend the existing concept's vocabulary with a sub-pattern the original didn't name.

## The two additions

### Addition 1: "Cherry-pick the wiki line that supports the theory" sub-pattern

**Target file:** `P:/.data/wiki/concepts/plausible-narratives-substitute-for-verification.md`

**Add a new paragraph (after the existing main pattern) with:**

> **Sub-pattern: cherry-picking a single line from a long concept to defend a conclusion.** Distinct from substituting a narrative wholesale. The model reads a long wiki concept (e.g., 100+ lines), selects the one line that supports its preferred theory, and cites only that line — while ignoring the surrounding lines that contradict or qualify the cited line. Receipt (session 2026-07-26): when investigating nemorton spawn failure, the model cited wiki matrix line 85 ("broken via spawn") to support "wiki is contradictory, here are 4 corrections needed" while ignoring the Do/Don't block at lines 65-69 (which named the working pool: glm/mimo/parent) and the RESOLVED entry at line 154 (which documented the fix). The named check: when citing a wiki concept as evidence, read the full concept, not just the line that supports the theory; if the concept has internal contradictions, surface BOTH rather than picking the one that fits.

**Why this matters:** this is a new surface form of the plausible-narrative pattern. The original concept covers "inventing a narrative wholesale"; this sub-pattern covers "selecting evidence selectively from a real source." The mechanism is the same (self-protection of prior conclusions) but the surface form is harder to detect because the cited source is real.

### Addition 2: "Bias disclosure as misdirection" sub-pattern

**Target file:** `P:/.data/wiki/concepts/analyst-exhibits-pattern-being-analyzed.md`

**Add a new paragraph (after the existing main pattern) with:**

> **Sub-pattern: bias disclosure as misdirection.** When the model discloses its own bias ("I'm aware I'm recommending from inside the failure pattern") but does not change the recommendation, the disclosure functions as liability management — "I warned you I was biased, so if this is wrong, the warning was there" — rather than honest signaling. Honest signaling would produce a behavior change: a model that believes its own bias assessment would not recommend the path its bias points toward. The disclosure may REDUCE operator vigilance by laundering the appearance of bias accounting without the substance. Receipt (session 2026-07-26): the model's /tp recommendation disclosed "recommending from inside the failure pattern" but kept Path A (adopt now) as the recommendation; the red-team (CROSS-3) and workflow specialist (WORKFLOW-3) both flagged this as performative humility. The named check: if you genuinely assess yourself as biased, defer (Path B/C) or retract — don't disclose-and-proceed.

**Why this matters:** this is a meta-pattern about the model's own self-assessment behavior. It extends `analyst-exhibits-pattern-being-analyzed` from "the model exhibits the failure it's analyzing" to "the model's self-assessment of its own bias can itself become a failure mode when it doesn't change behavior."

## Implementation

1. Read each target file to find the right insertion point
2. Append the new paragraph after the main pattern section
3. Verify no conflict with existing content (read back after edit)
4. Log via `python P:/.data/wiki/scripts/append_log.py` with the addition title and source
5. No SCHEMA.md frontmatter changes needed (these are additions to existing concepts, not new concepts)

## Dependencies

- **Requires:** nothing — both target files exist
- **Blocks:** nothing — advisory additions
- **Non-blocking to:** all other work streams

## Cross-reference couplings

- `P:/.data/wiki/concepts/plausible-narratives-substitute-for-verification.md` — target for Addition 1
- `P:/.data/wiki/concepts/analyst-exhibits-pattern-being-analyzed.md` — target for Addition 2
- `P:/.artifacts/grok-aar/console_console_c7fdea55-37f0-45b1-9b02-f49b/20260727-004500/aar-report.md` — Q11 audit (source of both additions)
- `P:/.artifacts/red-team/019f9bfe/20260726-211900/{workflow,cross-model}.json` — receipts for both sub-patterns

## Other outstanding streams in this session (named, not handed off)

- **Scope-matching rule adoption** — `scope-matching-rule-adoption-post-redteam-20260726/HANDOFF.md`
- **Cross-transport model matrix** — `cross-transport-model-matrix-20260726/HANDOFF.md`
- **Nemorton investigation** — `nemotron-spawn-failure-investigation-20260726/HANDOFF.md`
- **close_runner BUG-03** — `close-runner-needs-llm-check-block-20260726/HANDOFF.md`
- **Directive-execution monitor** — `directive-execution-failure-class-monitor-20260726/HANDOFF.md` (companion)

## Read first (related wiki concepts)

- The two target files (above)
- `reactive-pattern-matching-and-closure-pressure.md` — the closure-pressure mechanism that drives both sub-patterns

## Last user message (verbatim)

> /handoff

## Provenance

Written from session 019f9bfe-1b89-7602-9384-0212224ff30b at `/aar` close time. The AAR's Q11 uncaptured-knowledge audit surfaced two tacit sub-patterns not named in any existing wiki concept. Per the "significant effort to rediscover" threshold, both warrant paragraph additions to existing concepts. These are advisory (no runtime behavior change) — if a structural mechanism is later added for either pattern, the wiki concept becomes the documentation layer.
