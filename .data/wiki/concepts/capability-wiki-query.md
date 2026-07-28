---
title: "Capability: wiki-query"
created: 2026-07-28
source: session-2026-07-28
tags: [capability-node, wiki, query, reusable, skill-graph, phase-2]
summary: >
  Reusable capability node for querying the wiki vault. Used by 24 skills.
  Defines the I/O contract for "search existing wiki concepts." Skills
  reference this node instead of re-describing how to grep concepts.
node_type: capability
inputs:
  - name: query
    type: string
    description: "Keywords or pattern to search for"
    required: true
  - name: scope
    type: path
    description: "Default: P:/.data/wiki/concepts/. Can narrow to subdirectory."
    default: "P:/.data/wiki/concepts/"
outputs:
  - name: concepts
    type: list[{path, title, summary}]
    description: "Matching wiki concepts with paths and one-line summaries"
  - name: match_count
    type: integer
    description: "Number of hits (0 = no prior coverage)"
consumers:
  - aar
  - close
  - crawl4ai
  - create-skill
  - debrief
  - design
  - dream
  - go
  - grok-safe-git
  - handoff
  - maintain
  - model-benchmark
  - notice
  - plan-writer
  - prompt-patterns
  - refactor
  - refine
  - review
  - skill-dev
  - todo
  - tp
  - wargame
  - why
  - www
relations:
  - target: wiki/concepts/capability-wiki-write.md
    type: complementary
  - target: wiki/concepts/skill-graph.md
    type: grounds
---

# Capability: wiki-query

## What this node provides

A standard interface for searching the local wiki vault. Any skill that
needs to check existing knowledge before acting references this node
instead of re-describing the grep procedure.

## How to invoke

```powershell
# Use the built-in grep tool: search wiki concepts
grep pattern="<query keywords>" path="P:/.data/wiki/concepts/" -i
```

Or for broader coverage:

```powershell
# Also check open handoffs (intermediate knowledge layer)
rg -l "<keywords>" P:/docs/handoffs/
```

## Output contract

Return a structured summary:

```
**Wiki coverage:**
- `concept-slug.md` — one-line summary (path: P:/.data/wiki/concepts/concept-slug.md)
- ...

**Gaps:** <what the query did NOT find — specific questions for follow-up>
```

## When to use

| Trigger | Action |
|---------|--------|
| Before proposing a solution | Query wiki for prior art |
| Before writing a new concept | Retirement check (does it supersede/contradict?) |
| Before investigating a failure | Pattern-library match (known failure shapes?) |
| When the operator asks "what do we know about X" | Direct query |

## Glue notes (per-skill customization)

Skills add their own context around this capability:
- `/why` Step 0.5: queries for failure-pattern keywords, emits visible receipt
- `/www` Phase 1: queries for topic coverage, identifies gaps + retirement candidates
- `/tp` Step 0.5: queries for critique-matching patterns
- `/review` Step 0.5: queries for known bug patterns matching target domain
- `/close`: queries for wiki gates (concept coverage, log entries)

The capability node defines WHAT to do (grep concepts, return matches + gaps).
The glue defines WHY (what to do with the results in this skill's context).

## Falsifier

This node is obsolete when the wiki vault is replaced by a different
knowledge store (e.g., a vector database, a graph database). The I/O
contract (query in, concepts out) stays; the implementation changes.
