---
title: "Coupling inventory as mandatory design section — count, don't judge"
created: 2026-07-25
source: session-20260725 (/design edits, commits b39d97b + 55875d5 + faabb71)
tags: [design-skill, coupling, dyr, refactor-dismissal, mechanical-thresholds, agent-bias, decision]
summary: >
  AI agents dismiss real refactors as "gold-plating" under delivery pressure because judgment calls collapse into "it's fine." The structural defense: /design now mandates a Coupling & Code-Smell Inventory as a writer-produced appendix (DRY ≥3, params >7, touch-points >3, mixed concerns ≥2-of-3). For each threshold met, the writer must either refactor or cite a concrete technical constraint — not "delivery timeline." The writer's inventory table is the canonical source; the reviewer and critical friend reference it by name, not by redefinition. This is the /design skill operationalizing the [[raising-coding-best-practices-in-ai-agents]] wiki concept into a mechanical gate.
agent: grok
host: grok
cognitive_load: 3
verification: observed
sources:
  - session-20260725 (commits b39d97b, 55875d5, faabb71 on ~/.grok/skills/design/SKILL.md)
relations:
  - target: wiki/concepts/raising-coding-best-practices-in-ai-agents.md
    type: refines
  - target: wiki/concepts/subprocess-as-degradation-boundary.md
    type: related
  - target: wiki/concepts/cli-api-drift-in-skill-scripts.md
    type: related
---

# Coupling inventory as mandatory design section

## Decision context

**Why this decision was needed:** the [[raising-coding-best-practices-in-ai-agents]] wiki concept documented the failure mode — AI agents dismiss real refactors as gold-plating under delivery pressure, and the dismissal narrative substitutes for actual code-smell inventory. The concept named three mechanical thresholds (DRY ≥3, params >7, touch-points >3) as the fix. But the `/design` skill had no structural gate forcing the writer to actually count them. Without that gate, the documented rule lived only in AGENTS.md prose — and prose rules don't fire reliably under closure pressure (reference incident 2026-07-23: the `/close` scan/resolve extraction was dismissed as gold-plating despite 13 positional params, 3x DRY enumeration, 5 touch points).

The question: how do we make the threshold inventory *fire* on every design that touches existing code, rather than relying on the model to remember the rule?

## The decision

**Add a mandatory Coupling & Code-Smell Inventory section to the `/design` writer prompt, enforced by the reviewer and cross-referenced by the critical friend.** Three layers of enforcement:

1. **Writer** (Step 1) must produce a "## Coupling & Code-Smell Inventory" appendix with a per-module table: count DRY violations (≥3), positional params (>7), touch-points to add a field (>3), mixed-concerns (≥2-of-3 of {persistence, business logic, presentation}). For each threshold met: either include a refactor in the Implementation Plan OR cite a concrete technical constraint (performance=measured number, backwards-compat=named consumer, API=cited, migration=dated, security=cited standard). "Delivery timeline" is explicitly NOT a valid constraint — timeline says when, not why technically acceptable.

2. **Reviewer** (Step 2) BLOCKs if the inventory is missing when the design touches existing code. Checks each met threshold is either refactored or justified. Flags dismissal-bias (incremental patches over structural coupling) as a framing issue for the critical friend.

3. **Critical friend** (Step 5.5) domain 2 ("Optimal long-term vs simplicity") cross-references the inventory: if the inventory shows structural coupling the design perpetuates, the "simplest version" is under-engineering, not optimal — and "radical refactoring is on the table when ROI justifies it" (a developer preference) means the radical refactor is the correct answer when the inventory justifies it.

**Why three layers and not one:** a single-layer gate (writer-only) reproduces the original failure mode — the writer is the agent most likely to dismiss under delivery pressure, because the writer is the one producing the design under time cost. The reviewer adds independent enforcement (different subagent, no shared framing). The critical friend adds *framing* enforcement — it can challenge the premise that "incremental patch" is even the right shape, which the reviewer (checking the design against its own premises) cannot. Each layer catches a different failure mode: writer self-polices → reviewer blocks missing inventory → critical friend catches inventory-present-but-disregarded. Removing any layer leaves a gap.

## How the thresholds were calibrated

The four thresholds (DRY ≥3, params >7, touch-points >3, mixed-concerns ≥2-of-3) are not arbitrary. They come from the [[raising-coding-best-practices-in-ai-agents]] wiki concept, which itself derived them from the 2026-07-23 `/close` incident: `resolve_gates()` had 13 positional params, scan results were enumerated 3x, adding a new scan source required 5 touch points. Those were real coupling violations dismissed as gold-plating. The thresholds were set at the *lowest* values that would have flagged the `/close` case — not at aspirational values that would over-fire on healthy code. The mixed-concerns threshold uses a binary test (≥2-of-3 of {persistence, business logic, presentation}) rather than a count because mixed concerns genuinely aren't countable, but the test is still mechanical: it doesn't collapse into judgment.

## What people get wrong about coupling thresholds

Two failure modes the inventory is designed to avoid:

- **"Any coupling is bad coupling"** — the thresholds are floors, not ceilings. A function with 5 params and 2 touch-points is *not* a violation; it's normal code. The inventory fires only when the count crosses the documented threshold. Treating every signal as a violation is itself a failure mode (over-engineering in the name of purity).
- **"The threshold proves the refactor is right"** — meeting a threshold proves the coupling is *real*, not that any specific refactor is *correct*. The refactor still has to be designed. The inventory says "this needs to be addressed"; the Implementation Plan says how. Conflating the two leads to refactors that make the code worse while technically reducing the count.

The inventory's value is negative: it prevents dismissing real coupling as imaginary. It does not positively prove a specific refactor is the right one.

## How this connects to the workspace's enforcement patterns

The coupling inventory is one instance of a recurring pattern in this workspace: **behavioral rules fire at the moment of dismissal; review gates detect violations mechanically.** The pattern appears in:

- [[raising-coding-best-practices-in-ai-agents]] — the original instance (refactor dismissal gate)
- [[subprocess-as-degradation-boundary]] — same session (architectural principle made structural via the wiki_search shim)
- [[cli-api-drift-in-skill-scripts]] — same session (failure pattern documented + three structural fixes)
- This concept — the `/design` skill operationalizing the rule into writer/reviewer/critical-friend gates

The pattern itself is the workspace's answer to "models know the principles but dismiss them under pressure." Every instance translates a known-but-unreliable rule into a mechanical gate that fires regardless of pressure. The coupling inventory is the `/design`-skill instance of this pattern.

## Selection criterion + steelman

**Selection criterion:** durability against closure pressure. The chosen option had to make the inventory fire under delivery pressure, not just when the model happens to remember the rule.

**Steelman of the rejected alternative (prose rule in AGENTS.md only):** prose rules compose cleanly with the existing "Optimal long-term" developer preference; they require no skill changes; they work across all skills uniformly. The prose rule already existed (AGENTS.md § "Refactor dismissal gate") and was the source for the thresholds. Adding the skill-level gate introduces redundancy — the same rule now lives in three places (AGENTS.md, `/design` writer prompt, `/design` reviewer checklist).

**Why the steelman lost:** the prose rule was already present on 2026-07-23 when the `/close` extraction was wrongly dismissed. Its presence didn't prevent the failure. The failure class is *structural* (judgment collapses under pressure), not *knowledge* (the model knows the rule). A structural problem needs a structural fix — a gate the reviewer enforces, not a rule the writer might remember.

## Falsifier

This decision is wrong if, within 6 months:
- **The inventory never fires on a real design** (the "pure greenfield" definition is too loose and writers rationalize their way out). Mitigation: the operational definition (no existing files modified + no existing interfaces consumed + no existing patterns followed) is explicit; reviewer must BLOCK if any of these hold and the inventory is missing.
- **The inventory fires but writers successfully hand-wave past it** (the "concrete constraint" test is too soft). Mitigation: the test enumerates valid forms with required evidence and explicitly rejects "delivery timeline."
- **The inventory adds 15+ minutes to every design** for negligible quality gain. Mitigation: the inventory is appendix-only, fires only when touching existing code, and `--lite` mode skips it entirely.

## What this means for our workspace

- **The `/design` skill** now enforces the inventory across writer/reviewer/critical-friend. The thresholds are the canonical source — they live in the writer's table only; reviewer and critical friend reference them by name with values as reminder. If thresholds change, they change in ONE place.
- **`--lite` mode skips the inventory** — the inventory is a full-mode gate. `--lite` is for "add a config field, rename a variable" designs where the inventory is overhead. The skip is explicit in the skill, not a loophole.
- **The wiki concept `raising-coding-best-practices-in-ai-agents`** is the source for the thresholds and the dismissal-bias pattern. This concept refines it: it documents the *enforcement layer* that turns the documented rule into a structural gate.
- **Future skill changes** that touch the writer/reviewer/critical-friend prompts should preserve the canonical-source pattern (writer defines, reviewer + critical friend reference). Drift across the three locations is the maintainability risk this decision introduces; the canonical-source note makes drift a visible bug.
- **Audit existing skills for the same pattern** — `/review`'s maintainability lens already flags coupling as `risk` severity per the wiki concept. The `/design` inventory and the `/review` lens are complementary: `/design` prevents coupling from being designed in; `/review` catches it when it already exists. A future audit could check whether other skills (e.g., `/refine`, `/plan-writer`) need similar gates.

## Receipts

- **`~/.grok/skills/design/SKILL.md` Step 1 writer prompt** (lines ~510-524) — the mandatory Coupling & Code-Smell Inventory section with threshold table and concrete-constraint test. Directly inspected and edited across commits b39d97b, 55875d5, faabb71.
- **Reviewer checklist** (line ~585) — BLOCKs if inventory missing; references "see writer prompt" rather than redefining thresholds.
- **Critical friend domain 2** (line ~814) — cross-references "the Coupling & Code-Smell Inventory in the design doc" with threshold reminder.
- **`/check` verifier report** (session 019f9bfe, subagent 019f9ce4) — confirmed all 10 checklist items, threshold fidelity vs wiki, internal consistency, pre-existing changes preserved.
- **`/review` maintainability lens** (session 019f9bfe, subagent 019f9ce5) — surfaced 6 findings; all addressed in commits 55875d5 (F1+F2) and faabb71 (F3-F6).

## Sources

- [[raising-coding-best-practices-in-ai-agents]] — the wiki concept documenting the dismissal-bias pattern and the three mechanical thresholds. Source for the inventory content.
- [[subprocess-as-degradation-boundary]] — same session's architectural principle (subprocess preserves loose coupling); related because both decisions came from the same operator-asked-for coupling review.
- [[cli-api-drift-in-skill-scripts]] — same session's failure-pattern capture; related because the coupling inventory is the *fix* for the kind of skill-porting failure that caused the qmd CLI drift.
- Session transcript 019f9bfe — the `/why` → `/tp` → `/check` → `/review` chain that produced this decision.
