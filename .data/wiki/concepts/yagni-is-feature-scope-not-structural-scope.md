---
title: "YAGNI is feature-scope, not structural-scope — a type error in AI agent reasoning"
created: 2026-08-12
source: session-20260812 (/www research + /tp critique)
tags: [yagni, refactor-dismissal, feature-scope, structural-scope, type-error, harness-engineering, fowler, rule-of-three, agent-bias]
summary: >
  YAGNI ("You Aren't Gonna Need It") applies only to presumptive features —
  capabilities built for anticipated future needs. It explicitly does NOT apply
  to refactoring, coupling reduction, or malleability work (Fowler 2015, the
  canonical definition). When AI agents dismiss structural refactors as "YAGNI,"
  they commit a type error: answering "do we need this feature?" when the
  question is "how should this code be organized?" The fix is not to teach the
  agent better taxonomy — it's mechanical enforcement at the harness layer
  (linters, structural tests, delegation contracts), per the 2026 harness-
  engineering consensus.
agent: grok
host: both
cognitive_load: 3
verification: multi-source-verified
tier: 1
sources:
  - "https://martinfowler.com/bliki/Yagni.html" (Fowler, 2015 — canonical YAGNI definition)
  - "https://martinfowler.com/articles/designDead.html" (Fowler, ~2000/2004 — "Does Refactoring Violate YAGNI?")
  - "https://sandimetz.com/blog/2016/1/20/the-wrong-abstraction" (Metz, 2016 — duplication > wrong abstraction)
  - "https://en.wikipedia.org/wiki/Rule_of_three_(computer_programming)" (Rule of Three — XP origins)
  - "https://openai.com/index/harness-engineering/" (OpenAI, 2026 — mechanical enforcement at scale)
  - "https://arxiv.org/html/2606.17099v1" (2026 — delegation contracts, evidence bundles)
relations:
  - target: wiki/concepts/raising-coding-best-practices-in-ai-agents.md
    type: refines
  - target: wiki/concepts/coupling-inventory-as-mandatory-design-section.md
    type: related
  - target: wiki/concepts/minimal-fix-and-root-cause.md
    type: related
---

# YAGNI is feature-scope, not structural-scope

## Decision context

**The problem:** AI coding agents have a documented dismissal bias (arXiv
2606.05608, 2026: "senior implementers, junior designers"). When asked to
reduce coupling, consolidate modules, or separate concerns, they default to
"YAGNI," "KISS," or "over-engineering" — even when the violations are real.
The workspace's own [[raising-coding-best-practices-in-ai-agents]] concept
documents this with the 2026-07-23 `/close` incident (13 positional params,
3× DRY, 5 touch points — all dismissed as "gold-plating").

**The question this entry answers:** WHY is the dismissal wrong? The answer
isn't "the agent doesn't know SOLID" — the agent does know. The answer is a
**category error**: the agent applies a feature-scope principle (YAGNI) to a
structural-scope question (module organization). Understanding the type error
is the prerequisite to fixing the enforcement.

## The canonical definition (Fowler 2015)

Martin Fowler's bliki entry on YAGNI — the definitive reference cited by all
subsequent work — states explicitly:

> "Yagni only applies to capabilities built into the software to support a
> presumptive feature, it does not apply to effort to make the software easier
> to modify. Yagni is only a viable strategy if the code is easy to change, so
> expending effort on refactoring isn't a violation of yagni because refactoring
> makes the code more malleable. ... Yagni requires (and enables) malleable
> code."

This creates a clean two-domain partition:

| Decision type | Example | YAGNI applies? | Valid rejection basis |
|---|---|---|---|
| **Feature-scope** | "Should we build this capability for a future need?" | ✅ YES | "Not needed" with evidence of what specifically wouldn't work |
| **Structural-scope** | "Should we consolidate these modules / reduce coupling / extract this abstraction?" | ❌ NO | Coupling evidence: DRY count, parameter count, touch-point count, or concrete technical constraint |

When an agent says "YAGNI" to reject a module consolidation, it's answering
"do we need this feature?" — but nobody asked that. The question was "how
should this code be organized?" That's a structural question governed by
coupling, cohesion, and depth — not by whether the feature is needed.

## Why AI agents make this type error

Two converging causes:

1. **Training bias** (arXiv 2606.05608): LLM training data contains far more
   warnings against premature abstraction than guidance on sustainable
   technical debt management. "YAGNI" and "don't over-engineer" are
   over-represented relative to "refactor for malleability."

2. **Effort-aversion under delivery pressure**: structural work takes time.
   The agent constructs a plausible narrative ("it's just aesthetics," "they're
   already independent") that substitutes for actual code-smell inventory.
   The narrative is feature-scope-shaped because "not needed" is the easiest
   rejection to construct.

The type error isn't a knowledge gap — the models know the principles. It's a
**dismissal bias** that manifests as misclassification: the agent treats
structural decisions as feature decisions because YAGNI is the fastest
rejection available.

## What doesn't work (proven by this workspace)

- **Prose rules in AGENTS.md** — the "Refactor dismissal gate" rule was present
  on 2026-07-23 when the `/close` extraction was wrongly dismissed. Its presence
  didn't prevent the failure. Prose rules don't fire under closure pressure.
- **Asking the agent to self-classify** ("is this feature-scope or
  structural-scope?") — same agent, same framing anchor, same pressure. The
  agent that wants to dismiss will classify the decision as feature-scope to
  justify YAGNI.
- **More /tp critique** — catches the pattern after the fact but doesn't
  prevent it at the moment of dismissal.

## What works: mechanical enforcement at the harness layer

The 2026 practitioner consensus (OpenAI harness engineering, Martin Fowler,
arXiv 2606.17099 delegation contracts) converged on **mechanical gates** that
fire regardless of how the agent classifies the decision:

1. **Structural linters** — count DRY violations, parameter counts, and
   touch-points on the code. The linter doesn't ask "is this over-engineered?"
   — it counts. If the count exceeds the threshold, the gate fires regardless
   of the agent's classification.

2. **The Rule of Three** (Extreme Programming, Sandi Metz) — tolerate
   duplication for the first two instances, abstract on the third. This is
   the ONE threshold with decades of independent practitioner consensus
   (unlike param count and touch-point thresholds, which are calibrated from
   single incidents and have circular validation).

3. **Delegation contracts with evidence bundles** — when spawning a subagent,
   the task packet requires coupling counts for any modified module. The
   subagent can't close without producing the numbers.

4. **The py_compile verification gate** — when a model-validated pipeline
   phase claims a code defect, run mechanical verification before accepting
   the finding. This catches fabricated findings from weaker models without
   requiring the model to self-classify.

The key insight: **the decision-type distinction is the diagnosis, not the
treatment.** Understanding WHY YAGNI misfires (type error) explains the
failure. But the fix is mechanical enforcement — external to the agent's
reasoning — not teaching the agent better taxonomy.

## Operator directive: surface=1, block=3

Per operator directive (2026-08-12), this workspace uses two tiers:

- **Surface (advisory):** report any refactor opportunity (>0). The human
  filters. This follows the /completeness-over-curation principle — surface
  everything, don't pre-judge.
- **Block (gate):** enforce at ≥3 coupling signals. This is grounded in the
  Rule of Three — the one threshold with real backing. The gate blocks and
  requires either a refactor or a concrete technical constraint (not "effort"
  or "timeline").

The block threshold of 3 is NOT a magic number — it's the Rule of Three,
which has decades of practitioner consensus from Extreme Programming, Sandi
Metz, and Martin Fowler. The surface threshold of 1 is the operator's
preference for visibility over filtering.

## What this means for our workspace

- **The coupling inventory in `/design`** ([[coupling-inventory-as-mandatory-design-section]])
  is the right structural gate — but it only fires during formal design. It
  needs extending to the skills where rejections actually happen (`/go`
  ALTERNATIVES GATE, `/refine` acceptance criteria, `/brain` option evaluation).
- **The refactor-scan in ship-py** (code_analysis.py) currently runs as
  advisory. The surface=1/block=3 directive needs wiring into it as
  enforcement. The scanner exists; it needs coupling detection (DRY, params,
  touch-points) added before the thresholds can fire.
- **AGENTS.md prose rules remain as documentation**, not enforcement. They
  explain WHY the linter blocks, so operators understand the gate. But the
  enforcement is the linter, not the prose.

## Falsifier

This entry is wrong if:
- Fowler's feature/structural distinction doesn't map cleanly to real
  rejections (test: classify 10 past rejections; if >30% are ambiguous, the
  taxonomy isn't crisp enough to enforce)
- Mechanical enforcement produces worse outcomes than agent self-classification
  (test: track whether linter-blocked refactors were genuinely needed vs
  false positives over 6 months)
- The Rule of Three turns out to be the wrong threshold for this workspace's
  codebase (test: measure whether code with DRY=2 genuinely produces lower
  maintenance cost than code with DRY=3+)

## Sources

- [Martin Fowler, "Yagni"](https://martinfowler.com/bliki/Yagni.html) (2015) — the canonical definition; explicitly states YAGNI does not apply to refactoring/malleability
- [Martin Fowler, "Is Design Dead?" § "Does Refactoring Violate YAGNI?"](https://martinfowler.com/articles/designDead.html) (~2000/2004) — the original treatment of the distinction
- [Sandi Metz, "The Wrong Abstraction"](https://sandimetz.com/blog/2016/1/20/the-wrong-abstraction) (2016) — duplication > wrong abstraction; the Rule of Three context
- [Rule of Three (computer programming)](https://en.wikipedia.org/wiki/Rule_of_three_(computer_programming)) — XP origins of the one well-grounded threshold
- [OpenAI, "Harness Engineering"](https://openai.com/index/harness-engineering/) (2026) — mechanical enforcement at scale; custom linters, structural tests, architecture invariants
- [arXiv 2606.17099](https://arxiv.org/html/2606.17099v1) (2026) — delegation contracts with evidence bundles; harness templates
- [[raising-coding-best-practices-in-ai-agents]] — the workspace's original concept documenting dismissal bias with calibrated thresholds
- [[coupling-inventory-as-mandatory-design-section]] — the /design skill's structural gate enforcing the thresholds
- [[minimal-fix-and-root-cause]] — the "optimal long-term, not minimal fix" developer preference

## Receipts

- **AGENTS.md "Refactor dismissal gate"** (`P:/AGENTS.md`, ~/.grok/AGENTS.md) — prose rule with DRY ≥3, params >7, touch-points >3 thresholds. Present but not enforced under pressure (reference incident 2026-07-23).
- **coupling-inventory-as-mandatory-design-section.md** (`P:/.data/wiki/concepts/coupling-inventory-as-mandatory-design-section.md`) — documents the /design skill's three-layer writer/reviewer/critical-friend enforcement gate. Contains the operator directive for surface=1/block=3 thresholds.
- **refactor_scan.py** (`~/.grok/skills/ship-py/__lib/phases/refactor_scan.py`) — runs `code_analysis.py` on changed code directories. Currently maps cycles → P1, dead_code → P2. Does NOT yet detect coupling signals (DRY, params, touch-points) — that extension is deferred.
- **check_dispatch.py** (`~/.grok/skills/ship-py/__lib/check_dispatch.py`) — contains the py_compile verification gate (`_verify_syntax_claims` function, lines 148-240) that mechanically verifies model-claimed syntax errors before accepting a FAIL verdict.

## Auto-related

- [[skill-graph]]
- [[scope-matching-verification-discipline]]
- [[skill-catalog]]
- [[tool-fallbacks]]
- [[Python-Behavior-Tree-Framework-for-Autonomous-LLM-Agents--Technical-Specificatio]]

