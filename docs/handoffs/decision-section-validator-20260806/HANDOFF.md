# Handoff — Decision-section validator extension for wiki concepts

## Status
OPEN — design clear, implementation not started.

## Objective

Extend `validate_wiki_entry.py` to catch agent-fabricated architectural decisions
at write-time. The validator currently checks structure, cross-references, and
frontmatter — but does NOT check whether `## Decision` sections containing
imperative retirement/replacement language cite operator confirmation.

## Background

Session 2026-08-06 found that `ship-pipeline-enforcement-pretooluse-phase-state-hooks.md`
contained a fabricated `## Decision: "Retire ship-py and ship-rhai"` that the
operator had never made. The agent inferred the retirement from research
conclusions and promoted the inference to operator-level authority. 98 similar
"fabricated decision" signals exist in recent handoffs.

The field calls this "unauthorized authority" and considers it a primary risk
of agentic AI (NiteAgent 2026, Air Canada chatbot case). See
[[fleet-health-patterns-skill-bloat-sibling-conflicts-fabricated-decisions]] § Problem 3.

## Design

### What to add to `validate_wiki_entry.py`

Add a new check function: `_check_decision_authority(text)`.

**Logic:**
1. Scan the wiki concept text for `## Decision` sections (case-insensitive header match)
2. Within each Decision section, scan for imperative retirement/replacement language:
   - `retire`, `retired`, `retiring`
   - `replace`, `replaced`, `replacing`
   - `delete`, `deleted`, `deleting`
   - `remove`, `removed`, `removing`
   - `supersede`, `superseded`, `superseding`
   - `mark as dead`, `mark as deprecated`, `mark as superseded`
3. If imperative language found, check for operator-attribution citation:
   - Pattern: `operator directive`, `operator decision`, `operator confirmed`,
     `the operator said`, `operator, YYYY-MM-DD`
4. If NO operator attribution found:
   - Check for `[PROPOSED]` or `[INFERENCE]` label in the section
5. If neither attribution nor label: **FAIL** with message:
   "Decision section contains imperative language ('retire/replace/delete') 
   without operator attribution or [PROPOSED] label. Agent-fabricated decisions
   must be labeled. Add 'operator directive YYYY-MM-DD' or mark as [PROPOSED]."

### What NOT to block

- Decisions that use softer language ("we chose X over Y", "the approach is X")
  — these are design rationale, not retirement commands
- Decisions with operator attribution present
- Decisions explicitly labeled `[PROPOSED]` or `[INFERENCE]`

## Scope

- **In scope:** `~/.grok/skills/wiki/scripts/validate_wiki_entry.py` — add `_check_decision_authority()` function + wire into main validation loop
- **Out of scope:** modifying existing wiki concepts (they'll be caught organically on next edit/validation run)

## Acceptance criteria

1. Validator catches the "Retire ship-py and ship-rhai" pattern (imperative language, no attribution)
2. Validator allows decisions with operator attribution ("operator directive 2026-08-06")
3. Validator allows decisions labeled `[PROPOSED]`
4. Validator allows soft design rationale ("we chose X because Y") without flagging
5. Existing 950 concepts can be batch-validated to measure false-positive rate
6. Function has unit tests in the wiki scripts test directory

## Key files

- Validator: `~/.grok/skills/wiki/scripts/validate_wiki_entry.py`
- Research basis: `P:/.data/wiki/concepts/fleet-health-patterns-skill-bloat-sibling-conflicts-fabricated-decisions.md` § Problem 3
- Fragmentation pattern: `P:/.data/wiki/concepts/wiki-concept-fragmentation-sessions-add-without-reconciling.md`
- Fabricated decision example: commit `d0b794c` (the correction)

## Handoff is wrong if

- The validator produces >10% false positives on existing concepts (too broad)
- The validator misses imperative language variants it should catch (too narrow)
- The check adds >500ms to validation latency (regex scan should be <50ms)
