---
title: Raising Coding Best Practices in AI Agents (DRY, Separation of Concerns, Coupling)
created: 2026-07-23
tags: [code-quality, DRY, coupling, separation-of-concerns, AI-agent, enforcement, anti-pattern, refactor]
sources:
  - https://arxiv.org/html/2606.05608v1 (2026 — "senior implementers, junior designers" training bias)
  - https://www.janeasystems.com/blog/ai-and-refactoring-part-2 (2025–2026 — vibe-then-verify, multi-agent quality)
  - https://www.okoone.com/spark/technology-innovation/why-ai-coding-agents-still-cant-handle-real-world-software/ (2026 — dismissal bias)
  - https://pub.towardsai.net/stop-letting-your-ai-agents-loop-the-sdd-playbook-for-engineers-cafb1f20500a (2025 — SDD playbook, persona + rules)
  - https://arxiv.org/abs/2602.03712 (2026 — SWE-Refactor benchmark, multi-agent +32% success)
  - https://labs.scale.com/leaderboard/sweatlas-refactoring (2026 — SWE Atlas refactoring leaderboard)
---

# Raising Coding Best Practices in AI Agents

## Problem

AI coding agents have a documented training bias: they contain far more
warnings against premature abstraction than guidance on sustainable
technical debt management. They default to "YAGNI," "KISS," or
"over-engineering" when asked to reduce coupling, eliminate DRY
violations, or separate concerns — even when the violations are real
(arXiv 2606.05608, 2026: "senior implementers, junior designers").

This is not a knowledge gap. The models know SOLID, DRY, separation of
concerns. The problem is a **dismissal bias**: under delivery pressure,
the agent constructs a plausible narrative ("it's just aesthetics,"
"they're already independent functions") that substitutes for actual
code-smell inventory.

## Reference failure (2026-07-23)

A `/close` format-layer extraction was proposed. The agent dismissed the
scan/resolve extraction as "gold-plating" because the functions were
"already independent." The operator pushed back. The code actually had:
- **13 positional parameters** on `resolve_gates()` (coupling)
- **3x enumeration** of scan results (return values + counts dict + evidence dict — DRY)
- **5 touch points** for adding a new scan source (extensibility cost)

All three were real coupling violations. The dismissal narrative was
wrong — the same class of plausible-story-substituting-for-evidence that
narrative-as-signal exists to catch.

## What doesn't work

- **Vague "improve this" prompts** — the agent optimizes for the smallest
  change that "looks improved"
- **Asking "is this optimal?"** — the agent says "yes" because its
  training bias says "don't over-engineer"
- **Hoping the agent cares about quality** — the default is dismissal,
  not advocacy

## What works (2025–2026 research consensus)

### 1. Quantitative thresholds, not judgment calls

Replace "is this over-engineered?" with mechanical counts:

| Signal | Threshold | Why |
|---|---|---|
| DRY violations (same data enumerated) | ≥3 | Change requires N edits; easy to miss one |
| Positional parameter count | >7 | High coupling; param swaps cause silent bugs |
| Touch-point count for new field | >3 | Structural coupling; extension cost compounds |
| Mixed concerns in one function | Any | Highest-churn layer coupled to most stable |

**Before dismissing a refactor**, the agent must enumerate these counts.
If any threshold is met, the refactor has positive ROI unless each
violation is specifically justified. "It works fine as-is" is not a
reason. (Source: janeasystems 2025–2026; okoone 2026; SDD playbook 2025)

### 2. Two-phase workflow (build fast, then refactor smart)

Phase 1 (feature implementation): accept temporary duplication, focus on
correctness. Phase 2 (dedicated refactor session): fresh context with
quality persona, run smell analysis first, then execute refactors to
standards. Fresh context prevents the agent from anchoring to its own
quick-and-dirty choices. (Source: janeasystems Part 2, 2025–2026)

### 3. Deterministic quality gates (vibe-then-verify)

The agent generates; a deterministic gate verifies. Tests + static
analysis + AST-based checks. The gate won't accept low-quality output
regardless of what the agent claims. SWE-Refactor (arXiv 2602.03712,
2026) showed multi-agent reviewer loops raise success from ~40% to ~53%
(+32% relative), with post-verification correctness reaching 96–99%.

### 4. Persistent quality rules in project config

A `QUALITY_MANIFESTO.md` or equivalent in the repo with explicit
thresholds, banned lazy defaults, and few-shot examples of past
successful refactors labeled "this was correct, not over-engineering."
Agents become less likely to dismiss patterns they see treated as
non-negotiable in the project's own history. (Source: towardsai SDD
playbook, 2025)

### 5. Multi-agent quality advocate role

A dedicated agent argues FOR refactoring, quantifies debt, and challenges
dismissal narratives. Paired with a pragmatist who challenges genuine
over-engineering. The debate calibrates better than any single agent.
(Source: arXiv 2606.05608, 2026; SWE-Refactor multi-agent evaluation)

## What this workspace implemented (2026-07-23)

Three-layer enforcement modeled on the research:

1. **AGENTS.md "Refactor dismissal gate"** (behavioral) — before
   dismissing as gold-plating, inventory DRY (≥3), params (>7),
   touch-points (>3). If any met, positive ROI.
2. **`/review` maintainability lens** (detection) — concrete coupling
   signals flagged as `risk` severity, not nit. Mechanical checks
   (grep signatures, count params).
3. **`/tp` failure mode 9** (critique) — "Refactor dismissal" as a
   named failure mode in the diagnostic vocabulary. Same class as
   fabricated causal chain, inverted: dismisses a cause without evidence
   instead of claiming a cause without evidence.

## Key insight from the research

> "The fundamental shift is moving from hoping the agent cares about
> quality to enforcing quality through protocol, persistent rules,
> metrics, verification layers, and multi-agent debate."
> — janeasystems, 2025–2026

The models know the principles. The enforcement has to be structural
because the dismissal bias is structural. Behavioral rules fire at the
moment of dismissal; review gates detect the violations mechanically;
critique modes name the pattern so it can be diagnosed.

## SWE-Refactor benchmark data (context for calibration)

- Single-agent refactoring success on real-world tasks: ~40% (GPT-4o-mini)
- Multi-agent with reviewer loop: ~53% (+32% relative)
- Compound/cross-file refactoring: ~40% ceiling even with scaffolding
- Post-verification correctness: 96–99% achievable with good gates
- Top 2026 systems (Claude Opus 4.7 + Claude Code): ~49% on SWE Atlas

The gap between "the model knows SOLID" and "the model refactors
correctly" is exactly the gap that enforcement patterns close.
## Falsifier

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory Falsifier section. State what observation or evidence would make this
concept wrong or obsolete. If the concept is purely descriptive (not a claim),
state that explicitly: "This is a reference document, not a claim — no falsifier applies."
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
