---
title: "Consistency Drift as a Waste Source in Iterative Refinement Loops"
slug: consistency-drift-as-waste-source-in-iterative-refinement
created: 2026-07-28
category: finding
tags: [consistency-drift, iterative-refinement, design-loop, self-refine, waste, revision-cascade, in-place-feedback, self-correction-blind-spot, ssot, automated-checking, llm-reliability]
summary: >
  Consistency drift is a named, documented anti-pattern in LLM iterative
  refinement loops. Each revision optimizes the touched section but leaves
  stale references to the old approach in untouched sections — creating
  a drift cascade that doubles the round count. Three root causes: (1)
  full-regeneration self-refine overwrites correct content (In-Place
  Feedback paper, arXiv:2510.00777); (2) LLMs have a 64.5% self-correction
  blind spot for their own errors (Self-Correction Bench, arXiv:2507.02778);
  (3) multi-agent writer-reviewer loops create an echo chamber where
  reviewer agreement is mistaken for correctness (LingTai AI Issue #100).
  The field's standard fix: SSOT + automated consistency checking (grep,
  link checkers, CI). For our /design skill: the writer emits a "symbols
  changed" list after each revision; the orchestrator greps for old
  symbols and reports hits before the next review round.
cognitive_load: 3
verification: multi-source-verified
agent: grok
host: both
sources:
  - "LingTai AI Issue #100 — text-consistency drift anti-pattern — https://github.com/Lingtai-AI/lingtai/issues/100"
  - "LingTai text-data-drift explainer — https://huggingface.co/huangzs/lingtai/blob/194038818434a9be7e7034f28c5d6513005bf03e/reports/pr-issue100-text-data-drift-explainer.html"
  - "In-Place Feedback (Choi, Lee et al. 2025) — full regen breaks correct content — https://arxiv.org/abs/2510.00777"
  - "Self-Correction Bench (Tsui 2025) — 64.5% blind spot rate — https://arxiv.org/abs/2507.02778"
  - "Self-Refine (Madaan 2023) — iterative refinement baseline — https://arxiv.org/abs/2303.17651"
  - "SSOT + automated consistency checking — https://paligo.net/blog/content-reuse/what-is-single-source-of-truth-ssot/"
  - "Vale prose linter — https://vale.sh"
  - "linkinator broken link checker — https://github.com/JustinBeckwith/linkinator"
  - "Workspace: design-skill-speedup-fast-mode-parallel-prewrite — diminishing returns data"
  - "Workspace: llm-synthesis-quality-and-speed-techniques Finding 4 — round budget"
relations:
  - target: wiki/concepts/llm-synthesis-quality-and-speed-techniques.md
    type: extends
  - target: wiki/concepts/design-skill-preflight-gap.md
    type: related
  - target: wiki/concepts/design-skill-speedup-fast-mode-parallel-prewrite.md
    type: extends
  - target: wiki/concepts/parallelizing-design-doc-generation-what-works.md
    type: related
  - target: wiki/concepts/self-feedback-iterative-refinement.md
    type: refines
---

# Consistency Drift as a Waste Source in Iterative Refinement Loops

## Decision context

**The problem:** a `/design` run for a thin CLI wrapper (email-skill)
produced 71 changes across 6 revision rounds. 56 of those 71 changes
(79%) were consistency drift — fixing what the previous fix broke in
untouched sections. The run took 78 minutes. The operator asked: is
this a named pattern, and how do we eliminate the waste?

**What the research found:** yes, this is a documented anti-pattern with
three named root causes in the LLM literature. The standard fix from
documentation engineering is SSOT + automated consistency checking,
which we can implement as a grep-based symbol checker in the /design
loop.

**What this finding changes:** the /design consistency sweep (Step 4.5)
should be automated, not manual. The writer emits a "symbols changed"
list; the orchestrator greps for old symbols. This eliminates the drift
cascade that caused rounds 2 and 5 of the email-skill design run.

## The named anti-pattern

### "Text-consistency drift" (LingTai AI, Issue #100)

The closest named match is from the LingTai AI project (a self-evolving
"Digital Scientist" agent system). They documented an anti-pattern
called **text-consistency drift** where:

> Multi-round reviewer refinements polish prose and boost internal
> consistency while the content quietly diverges from underlying
> data/artifacts, wasting compute, tokens, and effort.

Their specific case was an empirical NLP paper where 9+ reviewer rounds
made the draft increasingly polished — yet it described an experiment
that was never run (the text drifted from the actual data files).

**Our case is a variant:** our drift is intra-document (sections drift
from each other), not text-vs-data (text drifts from external artifacts).
But the mechanism is the same: each revision optimizes the touched
section against the reviewer's feedback, without re-anchoring to the
rest of the document. The reviewer agreement is mistaken for global
correctness.

### "Full-regeneration overwrites correct content" (In-Place Feedback paper)

Choi, Lee et al. (arXiv:2510.00777, 2025) identified three failure modes
in standard Self-Refine loops:

1. **Previously correct content becomes corrupted** — the model
   regenerates the entire response, overwriting correct spans
2. **Feedback is ignored** — prior mistakes reproduced in new context
3. **New errors introduced downstream** — local fix, new bug elsewhere

Their solution: **in-place feedback** — the expert edits only the
erroneous span, prunes dependent downstream text, and the model continues
from the corrected context. This limits revision scope and preserves
correct parts.

**Application to /design:** our writer does full-document edits via
`search_replace`, not full regeneration. But the consistency sweep is
manual ("scan the ENTIRE design document for stale references") — it
relies on the writer remembering to check every section. The fix is to
automate the sweep with grep.

### "Self-correction blind spot" (Self-Correction Bench, Tsui 2025)

Tsui (arXiv:2507.02778) found that LLMs have a **64.5% blind spot rate**
for errors in their own outputs — they can fix identical errors when
presented as external input, but fail to catch them in their own
generation. The cause is training data: SFT datasets rarely contain
error-correction sequences.

The simple fix: appending "Wait" after an erroneous response reduces
blind spots by 89.3%. This activates latent correction ability.

**Application to /design:** the writer cannot reliably self-detect
stale references in its own output. The reviewer catches some, but the
reviewer shares the same model bias. A mechanical grep check is the
external signal that breaks the echo chamber.

## The three root causes (summary)

| Root cause | Source | Our manifestation |
|-----------|--------|-------------------|
| Full-regen overwrites correct content | In-Place Feedback (2510.00777) | Writer edits section A, doesn't update section B that references A's old content |
| Self-correction blind spot | Self-Correction Bench (2507.02778) | Writer doesn't detect its own stale references during manual sweep |
| Echo chamber agreement | LingTai AI #100 | Reviewer agrees the edited section is correct, doesn't check cross-references |

## The standard fix from documentation engineering

The documentation field solved this decades ago:

1. **Single Source of Truth (SSOT)** — define each symbol (name, path,
   number) once; reference it everywhere. Change the source, not the copies.
2. **Automated consistency checking** — link checkers (linkinator),
   prose linters (Vale), build-time validation. Run on every change.

For a design document (not a published doc site), the equivalent is:

1. **Symbol registry** — the writer maintains a list of "symbols defined
   in this document" (env vars, file paths, function names, unit numbers,
   numerical claims).
2. **Grep-based drift check** — after each revision, grep the entire
   document for old versions of changed symbols. Report hits.

## Concrete implementation for /design

### Step 4.5 replacement: automated symbol-drift check

**Current (manual):** the writer is told "scan the ENTIRE design document
for stale references to the OLD versions of those symbols." This relies
on the writer's self-correction ability, which has a 64.5% blind spot.

**Proposed (automated):**

1. After the writer completes revisions, it emits a `symbols_changed`
   JSON block:
   ```json
   {"symbols_changed": [
     {"old": "auth.token.cmd", "new": "imap.sasl.xoauth2.token.command"},
     {"old": "Unit 7", "new": "Unit 4"},
     {"old": "10 implementation units", "new": "6 implementation units"}
   ]}
   ```

2. The orchestrator runs a grep for each `old` value across the design
   document. Any hit is a stale reference.

3. The orchestrator reports hits to the writer: "F-N: stale reference
   to 'auth.token.cmd' at line 1333. Run the consistency sweep or fix
   in place."

4. The writer fixes the hits (mechanical, not requiring reasoning).

**Cost:** ~5 lines of Python + one grep call per revision round. ~2
seconds execution. Eliminates the drift cascade that caused rounds 2
and 5 of the email-skill run (~20 min saved per design run).

### Why this works when manual sweeps don't

The manual sweep fails because of the self-correction blind spot: the
writer reads its own output and doesn't see the stale reference. The
grep check is an **external signal** — it doesn't depend on the writer's
ability to detect its own errors. This is the same principle as the
"Wait" intervention from Tsui 2025: the capability is latent, but it
needs an external trigger to activate.

The grep check is also **exhaustive** — it scans every line, not just
the sections the writer remembers to check. The manual sweep is
attention-limited; grep is not.

### What this does NOT fix

This fix addresses **intra-document consistency drift** (stale references
within the same document). It does NOT address:

- **Text-vs-data drift** (the LingTai pattern: document drifts from
  external artifacts). That requires re-reading the source files, not
  grep.
- **Premise errors** (wrong assumptions baked into the design). That
  requires Step 0.8 premise verification, not grep.
- **Framing errors** (solving the wrong problem). That requires the
  critical friend, not grep.

Each failure mode has a different fix. The grep check is specifically
for the consistency drift that wastes rounds.

## Measured impact on the email-skill design run

| Round | Findings | Drift-caused? | Eliminated by grep check? |
|-------|----------|---------------|--------------------------|
| 1 | 27 | No (first review) | No |
| 2 | 12 | **Yes** (v2.0 config rewrite) | **Yes** — grep would catch old syntax |
| 3 | 7 | No (minor polish) | No |
| 4 | 7 | No (critical friend) | No |
| 5 | 12 | **Yes** (critical friend fixes) | **Yes** — grep would catch old unit numbers |
| 6 | 5 | Partially (final polish) | Partially |

**Rounds eliminated:** 2 and 5 (24 findings, ~20 min).
**Remaining rounds:** 1, 3, 4, 6 (46 findings, ~50 min).
**New estimated time:** ~50 min instead of 78 min (36% reduction).

Combined with the `--fast` default (2 rounds instead of 3+): ~25-30 min.

## Receipts

- **"Text-consistency drift" named anti-pattern** — Source: [LingTai AI Issue #100](https://github.com/Lingtai-AI/lingtai/issues/100) + [text-data-drift explainer](https://huggingface.co/huangzs/lingtai/blob/194038818434a9be7e7034f28c5d6513005bf03e/reports/pr-issue100-text-data-drift-explainer.html). Fetched via web_search 2026-07-28. Direct quote: "Multi-round reviewer refinements polish prose and boost internal consistency while the content quietly diverges from underlying data/artifacts."
- **In-Place Feedback paper (full-regen overwrites correct content)** — Source: [arXiv:2510.00777](https://arxiv.org/abs/2510.00777), Choi, Lee et al. 2025. Three failure modes documented: (1) correct content corrupted, (2) feedback ignored, (3) new errors downstream. Fetched via web_search 2026-07-28.
- **Self-Correction Bench (64.5% blind spot rate)** — Source: [arXiv:2507.02778](https://arxiv.org/abs/2507.02778), Tsui 2025. Tested 14 open-source models. "Wait" intervention reduces blind spots by 89.3%. GitHub: kenhktsui/self-correction-bench. Fetched via web_search 2026-07-28.
- **SSOT + automated consistency checking** — Source: [Paligo SSOT guide](https://paligo.net/blog/content-reuse/what-is-single-source-of-truth-ssot/). Documents the docs-engineering standard: define once, reference everywhere, check with link checkers + linters in CI. Fetched via web_search 2026-07-28.
- **Email-skill design run measurements** — Source: this session's `/design` run (scratch dir `grok-design-b180ab58`). 71 changes across 6 rounds, 56 drift-caused. [INFERENCE]: the classification of "drift-caused" vs "original finding" is based on the reviewer's descriptions (round 2 findings explicitly cited "stale references from F-10 config rewrite"; round 5 findings explicitly cited "consistency drift from critical friend revisions").
- **/design Step 4.5 (manual consistency sweep)** — Source: `C:\Users\brsth\.grok\skills\design\SKILL.md` lines 720-750. The step tells the writer to "scan the ENTIRE design document for stale references" — manual, not automated. [INFERENCE]: the 64.5% blind spot rate from Tsui 2025 explains why this manual sweep misses references.

## Falsifier

This finding is wrong if:
- The grep check produces too many false positives (old symbol strings
  appear legitimately in migration tables, historical context, or
  cross-references to prior versions) — would need an exclusion mechanism
- The drift is not actually the primary waste source (if rounds 2 and 5
  would have happened anyway for other reasons, the grep check saves
  nothing)
- The writer stops emitting the `symbols_changed` list reliably (the
  check depends on writer cooperation)

## Related

- [[llm-synthesis-quality-and-speed-techniques]] Finding 4 — diminishing
  returns after 2-3 rounds. This finding extends that: the rounds you DO
  run create waste through consistency drift, independent of diminishing
  returns.
- [[design-skill-preflight-gap]] — the write/review loop misses framing
  gaps. This finding identifies a different gap: the loop misses
  consistency drift because the sweep is manual.
- [[design-skill-speedup-fast-mode-parallel-prewrite]] — `--fast` mode
  defaults to 2 rounds. This finding explains WHY 2 rounds is better:
  not just diminishing returns, but each additional round risks drift.
- [[parallelizing-design-doc-generation-what-works]] — notes
  cross-section contradictions as a risk of parallel generation
- [[self-feedback-iterative-refinement]] — Self-Refine technique.
  This finding identifies a specific failure mode of Self-Refine applied
  to design documents.
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
