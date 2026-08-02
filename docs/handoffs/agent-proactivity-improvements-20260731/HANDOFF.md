---
thread_id: agent-proactivity-improvements-20260731
parent_handoff_path: none
current_session_id: 019fb177-e5d5-7520-92f5-0158f87639c9
current_terminal_id: 3c773c60-e09f-490c-a96b-b14fa5208849
produced_at: 2026-07-31T05:10:00Z
status: open
handoff_type: investigation
accurate_as_of_head: 32395cc
---

# Handoff — Agent proactivity improvements (meta-checkpoint, cold-read audit, wiki marker scanner)

## Objective

Make the agent proactive at the meta-level: generalize lessons, self-audit, anticipate the next step, and map ideas across the skill graph — without the operator having to ask for each one.

## Status

OPEN — three structural fixes built. PROACT-01 (/close integration) BUILT (commit 01366cc). Meta-checkpoint AGENTS.md rule accidentally deleted in full-file rewrite (e7da24f, 2026-08-01) — RESTORED session 019fc318 (2026-08-02) with Q1 reworded from capture to escalation framing. See [[symptom-to-abstraction-escalation]]. Three priority integrations remain.

## Read-first list

1. `~/.grok/AGENTS.md` — § "Meta-checkpoint before claiming DONE" (4 questions) and § "Skill edit cold-read audit"
2. `~/.grok/skills/wiki/scripts/wiki_marker_scan.py` — mechanical detection of transferable-knowledge patterns in commit messages
3. `~/.grok/skills/skill-dev/SKILL.md` — Mode 2 Step 7 (graph-projection technique)
4. `P:/.data/wiki/concepts/meta-level-proactivity-three-fixes-skill-graph-mapping.md` — full mapping of fixes to skill graph
5. `P:/.data/wiki/concepts/skill-usability-audit-cold-read-critique.md` — cold-read technique
6. `P:/.data/wiki/concepts/dual-path-hazard-delete-manual-when-adding-mechanical.md` — transferable failure pattern

## Verified facts

- [FACT] Meta-checkpoint rule in AGENTS.md has 4 questions: generalize, audit, anticipate, map-across-graph (commit `6a58fa2`)
- [FACT] Cold-read audit rule in AGENTS.md fires after significant skill edits (commit `6a58fa2`)
- [FACT] wiki_marker_scan.py scans commit messages for 7 transferable-knowledge patterns (commit `a446b72`)
- [FACT] /skill-dev Mode 2 Step 7 graph-projection: scans skill catalog, scores integration value, outputs projection table (commit `6a58fa2`)
- [FACT] The /tp cold-read critique caught 3 HIGH-severity issues the author's self-review missed (subagent 019fb6a2, 72s, 10 findings)

## Current state

**Done (committed):**
- AGENTS.md: meta-checkpoint (4 questions, Q1 reworded to escalation framing), cold-read audit gate, symptom-to-abstraction retrieval gate
- wiki_marker_scan.py: mechanical pattern detection
- /skill-dev Step 7: graph-projection technique
- /close meta_checkpoint gate (PROACT-01): built commit 01366cc — blocks CLOSE COMPLETE until 4 questions answered

**NOT done (priority integrations — identified in wiki concept):**
1. ~~`/close` meta-checkpoint integration~~ — ✅ DONE (commit 01366cc)
2. `/create-skill` cold-read audit — add as final step before declaring ready
3. `/handoff` cold-read audit — post-write check on cold-consumed artifacts
4. `/harvest` marker scanner integration — add as unrealized-value detection layer

## Task packets

### PROACT-01: /close meta-checkpoint integration

- **goal:** Add the 4 meta-checkpoint questions to /close's summary template so they fire mechanically at session boundary
- **acceptance:** close_accounting.py generate_summary() includes the 4 questions as mandatory fields in the summary output
- **falsifier:** the questions appear in output but the agent ignores them (ceremony, not enforcement)

### PROACT-02: /create-skill cold-read audit

- **goal:** Add cold-read audit as the final step in /create-skill before declaring the skill ready
- **acceptance:** /create-skill SKILL.md Step N says "spawn explore subagent to cold-read the skill for LLM-followability"

### PROACT-03: /handoff cold-read audit

- **goal:** Add post-write cold-read check to /handoff (can a cold agent pick up this handoff?)
- **acceptance:** /handoff SKILL.md includes a cold-read verification step after the inline critic-friend review

### PROACT-04: /harvest marker scanner

- **goal:** Wire wiki_marker_scan.py into /harvest as a detection layer for unrealized knowledge value
- **acceptance:** /harvest SKILL.md references the scanner as an input source

### OPP-05: Removal protocol workspace-wide grep fix (from pre-compaction session)

- **goal:** `P:/.claude/rules/removal-protocol.md` needs the "grep the ENTIRE workspace" rule added — currently only greps the package directory, missing cross-package references
- **problem:** when removing a module, the audit greps only the local package. Cross-package imports (e.g., a hook imported by skills in a different package) are missed, leading to broken imports after removal
- **acceptance:** removal-protocol.md Step 1 and verification Steps 9-11 say "grep the entire workspace, not just the package directory"
- **blocked by:** permissions (was read-only for the agent path in the pre-compaction session — may be resolved now)

## Resumption protocol

1. Read the wiki concept `meta-level-proactivity-three-fixes-skill-graph-mapping.md` for full details
2. Start with PROACT-01 (/close) — highest leverage, fires once per session
3. Each task is a 5-15 line SKILL.md edit + commit

## Suggested next invocation

```
/go add the 4 meta-checkpoint questions to /close's summary template — see PROACT-01 in agent-proactivity-improvements-20260731 handoff
```
