---
title: "Capability: wiki-write"
created: 2026-07-28
source: session-2026-07-28
tags: [capability-node, wiki, write, persist, reusable, skill-graph, phase-2]
summary: >
  Reusable capability node for persisting knowledge to the wiki vault.
  Used by 18 skills. Defines the I/O contract for "write a wiki concept
  that passes quality validation." Skills reference this node instead of
  re-describing frontmatter format, validation, and logging.
node_type: capability
inputs:
  - name: title
    type: string
    required: true
    description: "Descriptive title for the concept"
  - name: body
    type: markdown
    required: true
    description: "Full concept body including Decision Context, findings, falsifier"
  - name: tags
    type: list[string]
    required: true
    description: "Topic tags for discoverability"
  - name: sources
    type: list[{url, author, date}]
    required: false
    description: "External sources cited. Required for research entries."
  - name: content_type
    type: enum[finding, decision, reference]
    default: finding
    description: "Determines quality gate (decision needs steelman + falsifier)"
  - name: relations
    type: list[{target, type}]
    required: false
    description: "Links to related concepts (extends, complements, refines, etc.)"
outputs:
  - name: concept_path
    type: path
    description: "P:/.data/wiki/concepts/<slug>.md"
  - name: validation_result
    type: enum[pass, fail]
    description: "Result of validate_wiki_entry.py"
  - name: log_appended
    type: boolean
    description: "Whether append_log.py recorded the write"
consumers:
  - aar
  - close
  - crawl4ai
  - debrief
  - design
  - dream
  - go
  - handoff
  - maintain
  - model-benchmark
  - notice
  - refine
  - review
  - skill-dev
  - tp
  - wargame
  - why
  - www
relations:
  - target: wiki/concepts/capability-wiki-query.md
    type: complementary
  - target: wiki/concepts/skill-graph.md
    type: grounds
  - target: P:/.data/wiki/SCHEMA.md
    type: authoritative-spec
---

# Capability: wiki-write

## What this node provides

A standard interface for persisting durable knowledge to the wiki vault.
Any skill that produces findings, decisions, or reference material
references this node instead of re-describing frontmatter format,
validation, retirement checks, and logging.

## How to invoke

### Step 1: Retirement check (mandatory)

Before writing, query existing concepts for overlap:

```
# Use capability-wiki-query: grep for the new concept's title keywords
grep pattern="<title keywords>" path="P:/.data/wiki/concepts/" -i
```

If a concept is superseded: update its frontmatter (`status: superseded`,
`superseded_by:`). If contradicted: flag the conflict. If refined: add a
`relations` entry.

### Step 2: Write the concept

Use the mandatory template (floor, not ceiling):

```markdown
---
title: "<descriptive title>"
created: YYYY-MM-DD
source: <session-YYYYMMDD or URL>
tags: [<topic>, <sub-topic>, <category>]
summary: >
  <2-4 sentence summary for future discoverability>
agent: grok
host: grok
cognitive_load: 1-5
verification: multi-source-verified | single-source-verified | observed | inferred | local-only
sources:
  - <URL> (Author/Org, Date)
relations:
  - target: wiki/concepts/<related-slug>.md
    type: extends | complements | related | supersedes | refines
---

# <Title>

## Decision context
<Why this was needed — the problem, not the topic>

## <Main content>
<Synthesis with reasoning, evidence, connections>

## What this means for our workspace
<Actionable connection to our infrastructure>

## Falsifier
<What would make this wrong or obsolete>
```

Full spec: `P:/.data/wiki/SCHEMA.md` §2-3 (frontmatter), §4 (quality gate).

### Step 3: Validate (mandatory)

```bash
python "$env:USERPROFILE/.grok/skills/wiki/scripts/validate_wiki_entry.py" "<concept-path>"
```

Exit 0 = passes quality bar. Exit 1 = fix before declaring done.

### Step 4: Log

```bash
python P:/.data/wiki/scripts/append_log.py "<slug>" "<title>"
```

Records the write in `P:/.data/wiki/log.md` for audit trail.

### Step 5: Auto-link (optional but recommended)

```bash
python P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/wiki/scripts/wiki_after_write.py "<concept-path>"
```

Injects `[[wikilinks]]` to related concepts automatically.

## Quality gate by content type

| Content type | Required fields | Quality bar |
|--------------|----------------|-------------|
| **Finding** | title, created, tags, summary, sources | Non-obvious + verified + durable + distinct |
| **Decision** | + selection criterion + rationale + steelman + falsifier | Architectural + re-litigatable |
| **Reference** | title, created, tags, summary | Accurate + durable + structured |

Minimum line count: research ≥80, reference ≥40, default ≥50.

## Glue notes (per-skill customization)

Skills add their own pre/post logic around this capability:
- `/why` Step 15: gates the write behind synchronous cross-model review (3 questions)
- `/www` Phase 3: adds decision-context capture + research ledger update
- `/review` Step 6: writes FINDINGS.md to wiki if systemic patterns found
- `/aar`: promotes headline lessons to wiki concepts
- `/close`: checks wiki gates as part of session close accounting

The capability node defines WHAT to do (write concept, validate, log).
The glue defines WHEN and WHY (what triggers the write in this skill's context).

## Falsifier

This node is obsolete when the wiki vault is replaced by a different
persistence layer. The I/O contract (concept in, path + validation out)
stays; the implementation changes.

## Receipts

- `P:/.data/wiki/SCHEMA.md` §2-4 — frontmatter spec, quality gate, template
- `~/.grok/skills/wiki/scripts/validate_wiki_entry.py` — validator implementation
- `P:/.data/wiki/scripts/append_log.py` — log appender
- 18 skills reference wiki write in their `depends_on` frontmatter
