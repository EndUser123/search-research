---
title: "Decision: /wiki captures decisions by default, not just findings"
created: 2026-07-25
source: session-2026-07-25-wiki-decisions-default
tags: [decision, wiki, knowledge-management, decisions, findings, schema, convention, quality-gate]
summary: >
  Decision (2026-07-25): the wiki captures two content types by
  default — findings (something learned about the world) and decisions
  (a design/architectural choice made with rationale). Previously the
  wiki was findings-only; decisions were captured ad-hoc and held to
  the wrong quality bar. SCHEMA.md §4 split into §4a (findings gate)
  and §4b (decisions gate). Decisions require: architectural +
  selection-criterion + rationale + steelman + falsifier + durable +
  distinct. Operator instruction: "make sure /wiki captures decisions
  by default."
agent: grok
host: both
cognitive_load: 2
verification: observed
sources:
  - session-019f9a89 (operator instruction + implementation, 2026-07-25)
  - P:/.data/wiki/SCHEMA.md (§4a findings gate, §4b decisions gate, §4c failure-mode note)
  - C:/Users/brsth/.grok/skills/wiki/SKILL.md (description + "Findings vs decisions" section)
relations:
  - target: wiki/concepts/synchronous-review-direct-write-pattern.md
    type: produced-by — that decision was the type case that surfaced the missing decisions gate
  - target: wiki/concepts/inline-conditional-over-dispatch-for-skill-design.md
    type: produced-by — same; held to §4b retrospectively
  - target: wiki/concepts/multi-producer-cross-model-synthesis.md
    type: produced-by — same
  - target: wiki/concepts/nemotron-tp-pool-demote-decision.md
    type: sibling — first decision captured under the new §4b gate prospectively
---

# Decision: /wiki captures decisions by default, not just findings

## Decision context

**The problem:** the operator instructed "make sure /wiki captures decisions by default." Investigation found the wiki's quality gate (SCHEMA.md §4) named only findings. Decisions were being written to the wiki (3 decision concepts had been captured earlier in the same session) but held to the findings standard ("is it verified?") instead of a decision-specific standard ("does it have a steelman + falsifier?"). Decision quality discipline was missing.

The 3 decision concepts captured earlier (`multi-producer-cross-model-synthesis`, `inline-conditional-over-dispatch-for-skill-design`, `synchronous-review-direct-write-pattern`) had steelmen and falsifiers — but only because the model happened to include them, not because a gate required them. Future decision concepts without those fields would have shipped incomplete.

## The decision

**Two content types are wiki-worthy by default:**

| Type | What it is | Quality gate |
|------|-----------|--------------|
| **Finding** | Something learned about how the system/library/world behaves | §4a: non-obvious + verified + durable + distinct + host-tagged + scoped-generalizations |
| **Decision** | A design/architectural choice made with rationale | §4b: architectural + has-selection-criterion + has-rationale + has-steelman + has-falsifier + durable + distinct |

**Routine tactical choices are NOT decisions** ("used list not tuple", "split into 3 files"). Only architectural choices that shape the system's structure and that a future session might re-litigate belong in the wiki.

## Selection criterion

**Decision quality over time.** Decisions without rationale get re-litigated by future sessions (the same argument re-derived, the same conclusion reached or a worse one chosen). Decisions without steelmen are suspect — they mean alternatives weren't considered. Decisions without falsifiers can't be retired — future sessions can't tell when the decision is obsolete. The §4b gate enforces all three.

## Rationale

1. **Findings and decisions have different quality bars.** A finding is judged by verification (did you confirm it?); a decision is judged by consideration (did you weigh alternatives? did you state when you'd be wrong?). Conflating them means decisions get verified (irrelevant) and findings get steelmanned (unnecessary).
2. **The wiki is the right home for both.** Both are durable, both are reusable, both outlive the session. Splitting them into different stores (e.g., ADRs for decisions, wiki for findings) creates two query surfaces and drift risk.
3. **The §4b gate catches what self-assessment misses.** The 2026-07-25 session's first 3 decision concepts happened to include steelmen/falsifiers, but only by luck. The gate makes it structural.

## Steelman of the rejected alternative (keep wiki findings-only)

**Argument for findings-only:** the wiki's purpose is "durable findings." Decisions are a different artifact type (closer to ADRs). Adding decisions dilutes the wiki's focus and creates a mixed-quality corpus where finding-pages and decision-pages have different shapes, making the vault harder to scan.

Additionally, decisions are often better captured in the artifact they govern (a decision about `/tp` pool order belongs in the `/tp` SKILL.md, not in a separate wiki concept). Duplicating them to the wiki creates two sources of truth that can drift.

**Why rejected:**
- The 3 decision concepts captured earlier in the session were already in the wiki and were among the highest-value pages (they captured reusable design principles). Removing them would lose value.
- ADRs are a heavier format (full solo-ADR template per `solo_operator_adr_best_practices`). Most workspace decisions don't warrant that weight; the §4b concept format is lighter and sufficient.
- Two stores (wiki + ADR dir) means two query surfaces; future sessions would have to check both. One store with two gates (§4a + §4b) is simpler.
- The "dilution" concern is addressed by the §4b gate itself — low-quality decisions (no steelman, no falsifier) are rejected, so the corpus doesn't actually dilute.
- The "two sources of truth" concern is real but manageable: the wiki concept links to the implementation (commit, SKILL.md section); the implementation links to the wiki concept. Drift is detected by the wiki health-check's external-reference scan.

## Falsifier

This decision is wrong, or has been resolved, if:

- **The §4b gate produces no decision concepts over 6 months.** Either no decisions are being made (unlikely for this workspace), or the gate is too strict, or decisions are being captured elsewhere (then update this concept to point there).
- **The §4b gate admits low-quality decisions** (no steelman, tautological falsifier, routine tactical choice). Then the gate needs tightening — perhaps a validator that checks for steelman and falsifier sections the way it checks for Receipts.
- **Decision concepts consistently cannot be distinguished from findings** — the two gates collapse into one. Then the split was unnecessary and §4 should revert to a single gate.
- **Operators consistently override §4b** (capture decisions without steelman/falsifier because "it's faster"). Then the gate is ceremony; consider whether the discipline is worth the friction. The fix would be either to lower the bar or to accept that some decisions ship thin.

## What this means for our workspace

- **`/wiki` invocations now treat decisions as first-class.** The skill description, the SKILL.md "Findings vs decisions" section, and SCHEMA.md §4 all reflect this.
- **When writing a wiki concept, first ask: "is this a finding or a decision?"** The gates differ. Findings: §4a. Decisions: §4b. Writing a decision through the §4a gate loses the steelman/falsifier; writing a finding through §4b adds unnecessary ceremony.
- **The §4b gate is the decision quality filter.** Without it, decisions ship as preference statements; future sessions can't tell whether to re-litigate. With it, every decision carries its own retirement criteria (the falsifier).
- **Existing decision concepts pass §4b retrospectively** (the 3 from earlier in the session). Future ones must pass prospectively.
- **The "Findings vs decisions" table in the wiki SKILL.md** is the quick-reference for operators and agents deciding which gate applies. When in doubt, ask: "would a future session benefit from knowing why this was chosen?" If yes, it's a decision; apply §4b.

## Methodology roots

- Operator instruction 2026-07-25: "make sure /wiki captures decisions by default"
- Implemented in commit `1ca97f4` (SCHEMA §4 split) and `7ab98b7` (wiki SKILL.md)
- The 3 decision concepts that motivated the split ([[multi-producer-cross-model-synthesis]], [[inline-conditional-over-dispatch-for-skill-design]], [[synchronous-review-direct-write-pattern]]) were the type cases
- The first decision captured prospectively under §4b is [[nemotron-tp-pool-demote-decision]]
- The principle that decisions need a different gate than findings extends [[verify-against-existing-state-before-defensive-mechanisms]] — both ask "what does this content type actually need?"
- Related to [[synchronous-review-direct-write-pattern]] — that decision's quality (steelman + falsifier) is what §4b generalizes as the requirement for all decisions

## Receipts

- **SCHEMA.md §4 split:** `P:/.data/wiki/SCHEMA.md` §4a (findings gate) and §4b (decisions gate). Receipt: commit `1ca97f4` — the split added §4b with 7 criteria (architectural, selection-criterion, rationale, steelman, falsifier, durable, distinct).
- **Wiki SKILL.md "Findings vs decisions" section:** `C:/Users/brsth/.grok/skills/wiki/SKILL.md` lines 24-36. Receipt: commit `7ab98b7` — the section distinguishes the two content types with a table and examples.
- **The 3 decision concepts that were the type cases:** authored earlier in session-019f9a89, all happened to include steelman + falsifier (by luck, not gate). Receipt: commit `0a6850b`.
- **Validator enforcement of the Receipts section:** `C:/Users/brsth/.grok/skills/wiki/scripts/validate_wiki_entry.py` — the validator that enforces mechanism claims require receipts. This is the mechanical enforcement behind §4b's "has rationale" criterion. [Receipt: direct invocation multiple times this session]
- **The §4c failure-mode note:** documents why the split exists — the 2026-07-25 session's 3 decision concepts were initially treated as findings. [Receipt: SCHEMA.md §4c, authored this session]
