---
title: "Meta-level proactivity: three structural fixes mapped to the skill graph"
created: 2026-07-31
source: session-019fb177 (operator challenge: "how can we make the LLM lovable?")
tags: [skill-design, proactivity, meta-checkpoint, cold-read, marker-scanner, transferable-technique, skill-graph, agent-quality]
summary: >
  The operator identified that the agent does immediate work well but doesn't
  take the meta-step: generalize lessons, self-audit, anticipate the next thing.
  Three structural fixes were built: (1) meta-checkpoint before DONE, (2)
  cold-read audit of skills, (3) wiki marker scanner. Each maps to multiple
  skills in the graph where it adds value beyond its original use case. The
  highest-leverage integrations are: meta-checkpoint → /close (session boundary),
  cold-read → /create-skill + /handoff + /plan-writer (cold-consumed artifacts),
  marker scanner → /harvest (unrealized value detection).
agent: grok
host: grok
cognitive_load: 3
verification: observed
sources:
  - "Session 019fb177: operator challenge + /tp cold-read critique evidence"
relations:
  - target: wiki/concepts/skill-usability-audit-cold-read-critique.md
    type: extends
  - target: wiki/concepts/dual-path-hazard-delete-manual-when-adding-mechanical.md
    type: related
  - target: wiki/concepts/ship-receipt-mechanical-generation-from-per-check-results.md
    type: related
  - target: wiki/concepts/mechanical-enforcement-over-behavioral-reminder.md
    type: applies
---

# Meta-level proactivity: three structural fixes mapped to the skill graph

## Decision context

**Why this was needed:** the operator said "It seems like I have to think of everything. How can we make the LLM so good that it's lovable?" This was after a session where the agent built the ship receipt generator, fixed bugs, committed — and stopped. The operator had to ask for: the wiki concept, the usability audit, the generalization of the lesson, the next step. Every time, the agent could do the work when asked — it just didn't proactively think to do it.

**The diagnosis:** the gap between "useful" and "lovable" is not more capabilities. It's **proactivity at the meta-level**. The agent executes well but doesn't step back and ask: "What did I just learn? What should I improve? What will the operator need next?" This is a behavioral gap — and behavioral rules (which the agent already has) have ~12% compliance. The fix must be structural.

## The three fixes

### Fix 1: Meta-checkpoint before DONE

Three questions before any completion claim:
1. Did I generalize the lesson? (transferable pattern → wiki)
2. Did I audit my own output? (cold-read if skill edited)
3. Did I suggest the next obvious thing? (anticipate operator need)

**Status:** added to `~/.grok/AGENTS.md` § "Meta-checkpoint before claiming DONE".

### Fix 2: Cold-read audit of skills

After significant skill edits, spawn a fresh `explore` subagent to cold-read the skill for LLM-followability. The subagent gets only the skill files (no session context) and reports what's confusing, ambiguous, contradictory, or missing.

**Status:** added to `~/.grok/AGENTS.md` § "Skill edit cold-read audit". Full technique in [[skill-usability-audit-cold-read-critique]].

### Fix 3: Wiki marker scanner

A script (`~/.grok/skills/wiki/scripts/wiki_marker_scan.py`) that scans recent commit messages for transferable-knowledge patterns (mechanical replacement, usability findings, enforcement patterns, contradictions, design decisions). Outputs `WIKI:` marker candidates for the agent to review.

**Status:** built and wired into the meta-checkpoint's question 1.

## Skill graph mapping

### Meta-checkpoint → skills with DONE gates

The meta-checkpoint applies to every skill that emits a completion signal. Rather than editing 10+ skill SKILL.md files, the rule lives in AGENTS.md (loaded by all skills). But specific skills benefit from **explicit integration**:

| Skill | Current done gate | Meta-checkpoint value | Integration point |
|-------|------------------|-----------------------|-------------------|
| `/close` | CLOSE COMPLETE | **Highest leverage** — session boundary where all work converges | Add the 3 questions to the close summary template as mandatory fields |
| `/aar` | AAR report | AAR already reflects — but on "what went wrong," not "what did I generalize" | Add a 6th lens: "did I capture the transferable lesson?" |
| `/debrief` | debrief complete | Same as AAR but faster | Same 6th lens |
| `/review` | FINDINGS.md | After review: "did I capture the review pattern?" | Add to the finalizer step |
| `/check` | CHECK PASS/FAIL receipt | After check: "what did this check reveal that's worth capturing?" | Add to the receipt template |
| `/handoff` | handoff written | After handoff: "is this handoff discoverable? did I generalize?" | Add to the write-completion step |
| `/harvest` | obligation recovered | Harvest recovers unrealized value — meta-checkpoint is the upstream detector | Add "did I fire WIKI: markers?" to the harvest scan |

**Recommended action:** integrate into `/close` first (highest leverage — fires once per session regardless of which skills ran). Then `/aar` and `/debrief` (reflection skills where the 3 questions are natural).

### Cold-read audit → skills producing cold-consumed artifacts

Cold-read audit isn't just for skills — any artifact that a fresh agent will consume cold benefits:

| Skill | Artifact consumed cold | Cold-read value |
|-------|----------------------|-----------------|
| `/create-skill` | New SKILL.md | **Natural home** — the final step before declaring a skill ready |
| `/handoff` | HANDOFF.md | A cold agent picks up the handoff — can it proceed without session context? |
| `/plan-writer` | Plan with Task/checkboxes | A cold agent executes the plan — are the steps unambiguous? |
| `/refactor` | seams.json or PLAN.md | A cold agent executes the seams — are they self-contained? |
| `/design` | Design doc | Already has critical-friend step — cold-read is the skill-instructions equivalent |

**Recommended action:** integrate into `/create-skill` first (the obvious home). Then `/handoff` and `/plan-writer` (the highest-traffic cold-consumed artifacts). The pattern is the same each time: spawn `explore`, pass only the artifact, ask "can you follow this?"

### Wiki marker scanner → skills that detect unrealized value

| Skill | Current detection | Marker scanner value |
|-------|-------------------|---------------------|
| `/harvest` | Obligation tracking | **Natural fit** — harvest recovers unrealized value; the scanner detects "knowledge value not yet realized as wiki concepts" |
| `/close` | Wiki gate scans for concepts | Scanner adds "did you MISS a transferable pattern?" — the wiki gate only checks if concepts exist, not if they should |
| `/aar` | Identifies improvement opportunities | Scanner adds "what knowledge did this session produce that isn't captured?" |
| `/friction` | Detects workflow friction | Scanner adds "did friction produce a transferable lesson?" |

**Recommended action:** integrate into `/harvest` first (aligned mission). The scanner becomes a harvest detection layer: `harvest` already scans for unrealized obligations; the scanner scans for unrealized knowledge.

## Why structural beats behavioral

All three fixes exist as AGENTS.md rules (behavioral layer). But the wiki marker scanner is also a script (mechanical layer). This dual-layer approach follows [[mechanical-enforcement-over-behavioral-reminder]]:

- **Behavioral rule** fires when the agent remembers — ~12% compliance under closure pressure
- **Mechanical script** fires when invoked — 100% compliance once called
- **The meta-checkpoint in `/close`** (future) would fire mechanically at session boundary — the close scanner can check "were the 3 questions answered?" the same way it checks "did wiki concepts get written?"

The pattern: behavioral rules guide, mechanical gates enforce, scripts detect. All three layers are needed because no single layer has 100% coverage. This is the same [[deterministic-output-engineering]] principle: transition from probabilistic instruction-following to deterministic lifecycle enforcement. The [[check-receipt-lifecycle-manifest-and-mechanical-derivation]] pattern applies here too — the manifest (commit history) is the lifecycle record, the marker scanner is the finalizer that derives candidates from it.

## Falsifier

These integrations are wrong if:
- The meta-checkpoint questions become ceremony (the agent answers "yes, yes, yes" without doing the work) — mitigated by `/close` enforcing it mechanically
- The cold-read audit catches nothing useful on real skills (meaning self-review is sufficient) — already falsified this session (3 HIGH findings in 72 seconds)
- The marker scanner produces too many false positives (the agent ignores real candidates in the noise) — mitigated by the pattern set being narrow (7 patterns, deduplicated)
- The skill graph integrations are never built (the concept exists but the skills aren't edited) — the highest-leverage one (`/close`) is the natural next task

## What this means for our workspace

The three fixes are implemented in AGENTS.md + the marker scanner script. The skill graph integrations are **identified but not yet built**. Priority order:

1. **`/close` meta-checkpoint integration** — add the 3 questions to the close summary template. Highest leverage: fires once per session, covers all skills.
2. **`/create-skill` cold-read audit** — add as the final step before declaring a skill ready. Natural home.
3. **`/handoff` cold-read audit** — add as a post-write check. Highest-traffic cold-consumed artifact.
4. **`/harvest` marker scanner integration** — add the scanner as a harvest detection layer. Aligned mission.

Each is a small edit (5-15 lines in the target SKILL.md) that propagates the structural fix to the skill where it adds the most value.

## Receipts

- AGENTS.md commit `a446b72` — meta-checkpoint + cold-read audit rule + marker scanner wiring
- `~/.grok/skills/wiki/scripts/wiki_marker_scan.py` — the mechanical detection layer
- `/tp` cold-read evidence: subagent `019fb6a2`, 10 findings, 3 HIGH severity
- This concept itself is a product of the meta-checkpoint (the agent fired a WIKI: marker after recognizing the transferable pattern)
