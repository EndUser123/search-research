---
title: "Skill lifecycle toolkit: create, audit, improve, and retire skills on Grok Build"
created: 2026-07-22
source: session-019f8a66 (skill consolidation analysis + /tp review)
status: superseded
superseded_by: wiki/concepts/skill-development-portfolio.md
superseded_date: 2026-07-27
superseded_reason: "Techniques 13-18 merged into skill-development-portfolio.md to consolidate the single source of truth. The portfolio now has all 18 techniques + the DEPRECATED convention + the routing table."
sources:
  - P:/docs/handoffs/skill-consolidation-20260722/HANDOFF.md
  - P:/.data/wiki/concepts/skill-development-portfolio.md
  - P:/.data/wiki/concepts/skill-authoring-patterns-dos-and-donts.md
  - C:/Users/brsth/.grok/skills/create-skill/SKILL.md
  - P:/packages/.claude-marketplace/plugins/cc-skills-architect/skills/skill-write/SKILL.md
  - P:/packages/.claude-marketplace/plugins/cc-skills-analysis/skills/skill-audit/SKILL.md
  - C:/Users/brsth/.grok/installed-plugins/superpowers-21e2a56d/skills/writing-skills/SKILL.md
  - C:/Users/brsth/.codex/skills/skillopt/SKILL.md
tags: [skill-design, skill-lifecycle, consolidation, grok-build, deprecation-convention, tdd-for-skills, eval-loop, held-out-validation]
host: grok
agent: grok
verification: cross_referenced_to_actual_skills
cognitive_load: 3
summary: "The skill lifecycle on Grok Build: which skill to use for each job (create, audit, improve, retire), the DEPRECATED-description convention for retiring skills, and 5 transferable techniques extracted from disabled Claude plugins and third-party skills. Self-contained — each technique is documented inline, not just linked."
---

# Skill lifecycle toolkit

> **⚠️ SUPERSEDED (2026-07-27):** This concept's 5 transferable techniques (TDD for skills, held-out validation, description optimization, pressure testing, rationalization tables) + the DEPRECATED convention have been merged into [[skill-development-portfolio]] (Techniques 13-18). This file is preserved as reference but the portfolio is now the single source of truth for skill-development techniques. Do not update this file — update the portfolio instead.

## Decision context

```
CREATE --------------- AUDIT --------------- IMPROVE --------------- RETIRE
(from scratch)         (quality check)      (iterate from evidence)  (DEPRECATED-description)
```

## Routing table — which skill to use for each job

On Grok Build, the cc-* plugins are **disabled**. Their skills are discoverable
via compat scan (`claude.skills: ON`) but their hooks, routers, and scripts are
inactive. Only Grok-native skills at `~/.grok/skills/` are fully functional.

| If you want to... | Use | Active on Grok? |
|---|---|---|
| Create a new skill (simple scaffolding) | `/create-skill` | YES (Grok-native) |
| Create a new skill (advanced, with eval loop) | `/skill-dev create` (when built — see handoff WI-2) | PLANNED |
| Audit an existing skill for quality | `/skill-dev audit` (when built) or `/skill-audit` (discoverable) | PLANNED / discoverable |
| Improve a skill iteratively | `/skill-dev improve` (when built) or `/skill-write` (discoverable) | PLANNED / discoverable |
| Find duplicate/overlapping skills | `/skill-similarity` (discoverable) or `/skill-audit prune` | discoverable |
| Convert docs/URLs to skill | `/skill-from-docs` (discoverable, scripts may not work) | discoverable |
| Document a skill as HTML | `/skill-to-page` (discoverable) | discoverable |
| Retire a skill | DEPRECATED-description convention (see below) | YES (manual edit) |
| TDD discipline for skills | See "TDD for skills" technique below | YES (manual) |

**Source:** `P:/docs/handoffs/skill-consolidation-20260722/HANDOFF.md`

---

## The DEPRECATED-description convention for retiring skills

### The pattern

When retiring a Grok-native skill, **do not move or delete the SKILL.md file.**
Instead, edit the frontmatter `description` field to prepend:

```
DEPRECATED — use /<replacement> instead.
```

Keep the body intact as fallback reference.

### Existing examples

- `~/.grok/skills/check-work/SKILL.md` — "DEPRECATED — use /check instead"
- `~/.grok/skills/code-review/SKILL.md` — "DEPRECATED — use `/review --focus maintainability` instead"

### Why DEPRECATED-description, not Move-Item archiving

| Criterion | DEPRECATED-description | Archive (Move-Item) |
|---|---|---|
| Multi-terminal isolation | ✅ frontmatter edit is atomic, non-locking | ❌ Windows file-lock IOException risk on open handles |
| Catalog scanner | ✅ works WITH the scanner — entry stays visible with redirection | ❌ `index_skills.py` has no path-exclusion logic; archived files may still appear |
| Existing convention | ✅ matches `check-work` and `code-review` pattern | ❌ new pattern, deviates from established convention |
| Stale-data immunity | ✅ body stays as fallback; if replacement is missing, original still readable | ❌ if replacement is missing, the skill is gone with no fallback |
| Recoverability | ✅ revert the frontmatter edit | ✅ move back (but requires knowing the archive path) |

### When to use this convention

- Retiring a skill whose functionality is absorbed by a superset skill
- Retiring a skill that is no longer needed
- Marking a skill as replaced by a better alternative

### When NOT to use

- The skill is in a **third-party plugin** (superpowers, firecrawl, etc.) — not yours to edit
- The skill is in a **disabled plugin** on Grok Build — deprecating gains nothing (the plugin is already inactive); leave as reference material unless you're explicitly consolidating (see handoff WI-5)
- The skill body contains **load-bearing content** that no replacement captures — in this case, do NOT deprecate; instead, capture the content in a wiki concept first, THEN deprecate

### Procedural checklist

1. Verify the replacement skill exists and covers the retired skill's capabilities
2. Edit the `description` frontmatter field: prepend `DEPRECATED — use /<replacement> instead.`
3. Keep the body unchanged (fallback reference)
4. Grep for references to the old skill name in other skills' Suggest blocks
5. Update any routing references found
6. Verify the edit persisted (read back)

---

## 5 transferable techniques

These techniques are extracted from disabled Claude plugins and third-party
skills. Each is documented **inline** (self-contained) so it remains valid even
if the source skill drifts or is removed.

### Technique 1: TDD for skills (RED-GREEN-REFACTOR)

**Source:** superpowers `writing-skills` (ENABLED on Grok Build)

**Core principle:** if you didn't watch an agent fail without the skill, you
don't know if the skill teaches the right thing. Skill creation IS TDD applied
to process documentation.

**The cycle:**

| TDD phase | Skill creation equivalent |
|---|---|
| RED (write failing test) | Run a pressure scenario with a subagent WITHOUT the skill. Document what fails. |
| GREEN (write minimal code) | Write the skill addressing those specific failures. |
| REFACTOR (close loopholes) | Find new rationalizations the agent uses to skip the skill. Add counters. Re-test. |

**Pressure scenario design:**
- For discipline-enforcing skills: combine 3+ pressures (time, sunk cost, authority, exhaustion)
- For technique skills: test application to a new scenario, not just recognition
- For reference skills: test retrieval (can the agent find the right info?) + application

**Rationalization table:**

Capture every excuse the agent makes when skipping the skill. Each gets a
counter in the skill body:

| Excuse | Reality |
|---|---|
| "Too simple to test" | Simple code breaks. Test takes 30 seconds. |
| "I'll test after" | Tests-after = "what does this do?" Tests-first = "what should this do?" |

**Form-matches-failure guide:**

| Baseline failure | Right form | Wrong form |
|---|---|---|
| Skips rule under pressure | Prohibition + rationalization table | Soft guidance ("prefer...") |
| Output has wrong shape | Positive recipe (state what the output IS) | Prohibition list ("don't X") |
| Omits required element | Structural: REQUIRED field in template | Prose reminders |

### Technique 2: Held-out validation

**Source:** `skillopt` (Codex-native skill)

**Core principle:** only accept a skill improvement if it wins on examples
that were NOT used to drive the edit. This prevents overfitting to specific
test cases.

**The procedure:**
1. Split available evidence into **training examples** (used to identify failure modes and draft edits) and **held-out examples** (used only for validation)
2. Score the baseline skill on BOTH sets
3. Apply the edit
4. Score the candidate skill on BOTH sets
5. Accept the candidate ONLY if:
   - It improves on at least one meaningful quality dimension
   - It does not regress on others
   - The gain is supported by held-out examples, not just training examples
   - The resulting skill is still simpler, clearer, or equally maintainable

**Why this matters:** without held-out validation, you can always make a skill
"better" on the examples you edited for. The question is whether it generalizes.

### Technique 3: Description optimization

**Source:** `skill-write` (cc-skills-architect, DISABLED) and `skill-creator` (Anthropic marketplace)

**Core principle:** the `description` frontmatter field is the ONLY signal the
model sees at selection time. Optimize it for trigger accuracy using a train/test split.

**The procedure:**
1. Generate 20 eval queries — a mix of should-trigger (8-10) and should-not-trigger (8-10) cases
2. Make queries realistic (concrete, with file paths, personal context, casual speech)
3. Split into 60% train / 40% held-out test
4. Evaluate current description (run each query 3x for reliability)
5. Propose improved descriptions based on failures
6. Re-evaluate on both train and test
7. Select the best description by TEST score (not train — avoids overfitting)
8. Iterate up to 5 times

**Grok Build caveat:** the automated backend (`run_loop.py` using `claude -p`
CLI) does NOT work on Grok Build — `claude -p` is Claude Code only. The
methodology above is the manual procedure. On Grok Build, run eval cases
manually with and without the skill, compare outputs, iterate.

**Key insight:** Claude has a tendency to under-trigger skills. Descriptions
should be slightly "pushy" — explicitly name the trigger contexts and signal
phrases, not just describe what the skill does.

### Technique 4: Pressure testing for discipline skills

**Source:** superpowers `writing-skills` (ENABLED on Grok Build)

**Core principle:** discipline-enforcing skills (TDD, verification, design-before-coding)
need to resist rationalization. Test them under pressure, not in neutral conditions.

**Pressure types:**
- **Time pressure:** "we need to ship this now, skip the review"
- **Sunk cost:** "we've already spent 2 hours on this approach, don't restart"
- **Authority:** "the senior dev said to do it this way"
- **Exhaustion:** "we've been at this for 6 hours, just commit it"

**Testing protocol:**
1. Write a pressure scenario that combines 2-3 pressures
2. Run the scenario with a subagent that HAS the skill loaded
3. Observe: does the agent comply with the skill, or rationalize skipping it?
4. If the agent rationalizes: capture the rationalization verbatim, add a counter to the skill
5. Re-test until the agent complies under maximum pressure

**Micro-testing (faster than full scenarios):**
1. One fresh-context sample per call (raw API or single-shot subagent)
2. Always include a no-guidance control (if control doesn't fail, there's nothing to fix)
3. 5+ reps per variant (single samples lie)
4. Manually read every flagged match (automated counts overstate)

### Technique 5: Rationalization tables

**Source:** superpowers `writing-skills` (ENABLED on Grok Build)

**Core principle:** agents are smart and find loopholes when under pressure.
Capture every rationalization explicitly and counter it in the skill body.

**Construction:**
1. During RED phase (baseline testing), note every excuse the agent makes verbatim
2. For each excuse, write a one-line reality check
3. Add the table to the skill body
4. During REFACTOR phase, look for NEW rationalizations and add them

**Template:**

```markdown
| Excuse | Reality |
|--------|---------|
| "Too simple to test" | Simple code breaks. Test takes 30 seconds. |
| "I'll test after" | Tests-after = "what does this do?" Tests-first = "what should this do?" |
| "It's about spirit not ritual" | Violating the letter IS violating the spirit. |
```

**Red flags list** (companion to the table):

```markdown
## Red Flags - STOP and Start Over
- Code before test
- "I already manually tested it"
- "This is different because..."
```

**Why this works:** the table pre-counters the most common rationalizations
before the agent encounters them. When the agent hits the pressure and reaches
for the excuse, the counter is already in context.

---

## Cross-references

- [[skill-development-portfolio]] — full inventory of skill-writing/improving skills
- [[skill-authoring-patterns-dos-and-donts]] — industry best practices (Anthropic, generativeprogrammer)
- [[compound-skill-improvement-patterns]] — patterns for compound/orchestrator skills
- [[skill-catalog]] — auto-generated index of all skills
- `P:/docs/handoffs/skill-consolidation-20260722/HANDOFF.md` — consolidation plan with WI-1 through WI-5

## Regeneration

This concept is **curated**, not auto-generated. Update when:
- The consolidation plan's work items are implemented (skill-dev created, skills deprecated)
- A new transferable technique is identified
- The DEPRECATED-description convention is applied to additional skills
- The routing table changes (new active skills on Grok Build)
