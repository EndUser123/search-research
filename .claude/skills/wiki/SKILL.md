---
name: wiki
description: Persistent knowledge system using Obsidian wiki + QMD search
version: 1.0.0
type: skill
enforcement: none
workflow_steps:
  - ingest: Accept source (file/URL/text) and write wiki page with YAML frontmatter
  - query: Accept question, search wiki via QMD_WIKI backend, synthesize answer
  - lint: Health-check wiki for contradictions, orphans, missing cross-refs
  - index: Rebuild index.md catalog from current wiki state
  - new: Scan ~/Downloads for new markdown files with usefulness indicators
---

# /wiki — Obsidian Wiki + QMD Search Skill

## Purpose

Persistent knowledge management: LLM maintains an Obsidian wiki (ingest/synthesize/lint), searchable via QMD CLI, exposed as `search-research` backend `QMD_WIKI`.

## Operations

### Ingest
Accept source (file path, URL, or text blob) → LLM reads source → writes/updates wiki page with YAML frontmatter → **searches vault for related pages → injects `[[wikilinks]]` into page body** → appends entry to `log.md`

**Auto-linking phase**: After writing the page, query QMD for semantically similar existing pages using the new page's title and summary. Inject `[[Page Name]]` links to top-K (default K=5) related pages into the new page's body under a `## Related` section.

**Speculative linking**: When ingesting, if the content references pages that don't exist yet, create `[[wikilinks]]` to those pages anyway — they become "red links" in Obsidian. This is intentional: future ingest of those pages will resolve the links automatically. Never suppress a link because the target doesn't exist.

**Typed wikilinks**: For explicit relationships, use typed wikilink syntax:
- `[[Page]]@supports` — Page provides supporting evidence
- `[[Page]]@contradicts` — Page contradicts this one
- `[[Page]]@refines` — Page refines or clarifies this one
- `[[Page]]@supersedes` — Page supersedes this one
- `[[Page]]@related` — general relationship

When using typed wikilinks, also record the relationship in the page's frontmatter under `relations:`:
```yaml
relations:
  - target: wiki/entities/SomePage
    type: supports
    reciprocal: contradicts  # the other page references this one
```

Usage: `/wiki ingest <source>`

### Query
Accept question → `search-research --backend QMD_WIKI` → LLM synthesizes answer

**Auto-save high-value results**: If the synthesized answer is substantive (non-trivial insight, new connection, resolved ambiguity, or decision-relevant synthesis), save it directly to the wiki without asking. Write to `wiki/concepts/<slug>.md` with YAML frontmatter. Only ask the user if the synthesis is uncertain or incomplete.

Usage: `/wiki query <question>`

### Lint
Health-check wiki: contradictions, orphan pages, missing cross-references, stale claims

**Automated periodic linting**: `/wiki lint` is included in the `/main` health check workflow. It runs on every `/main` invocation.

Usage: `/wiki lint`

### Index
Rebuild `index.md` catalog from current wiki state

Usage: `/wiki index`

### New — Scan Downloads for New Files
Scan `~/Downloads` for markdown files added since last check. Present a selectable list with usefulness indicators so you can choose which to ingest.

**Workflow:**
1. `find ~/Downloads -name "*.md" -newer <last_check_file>` — list new files
2. For each file, show: filename, size, usefulness keywords (hooks, testing, architecture, agents, etc.)
3. Present numbered list — user selects which to ingest
4. Ingest selected files via the Ingest workflow above

**Usefulness keywords:**
- `claude code`, `hook`, `stop`, `pretool`, `posttool`, `userprompt` → hooks-related
- `test`, `pytest`, `flaky`, `timeout` → testing
- `session`, `transcript`, `jsonl`, `compact`, `history` → session-management
- `arch`, `adr`, `design`, `architecture` → architecture
- `subagent`, `agent`, `multi-agent` → agents
- `discovery`, `search`, `explore` → discovery patterns
- `python`, `windows` → python/windows

**Selection format:**
```
/wiki new
[1] Are there repos or solutions to claude code gettin.md (23kb, hooks,testing)
[2] I'm going to create a hook to enforce discovery be.md (15kb, hooks,discovery)
[3] session-chain-tracer.md (8kb, session-management)
[4] ✳ transcript.py analysis.txt (44kb, session-management,transcript)
Select files to ingest (e.g. 1,2 or all): _
```

Usage: `/wiki new`

## Configuration

Settings in `settings.json`:
```json
{
  "OBSIDIAN_VAULT_PATH": "~/.obsidian/vaults/personal-wiki",
  "QMD_WIKI_SOURCES": "sources/",
  "QMD_WIKI_SCOPE": "wiki/"
}
```

## Schema Conventions

Wiki pages stored under `vault/wiki/`:
- `wiki/entities/` — entity pages
- `wiki/concepts/` — concept pages
- `wiki/comparisons/` — comparison pages
- `sources/` — immutable raw sources (never modified by LLM)

Every wiki page has YAML frontmatter:
```yaml
---
tags: []
created: YYYY-MM-DD
sources: []
summary:
---
```

## Vault Log

Append-only log at `vault/log.md`:
```
## [YYYY-MM-DD] ingest | Title
```

## Graceful Degradation

If `qmd` CLI is unavailable, falls back to glob+grep search.

## Security

- All frontmatter written using `yaml.safe_dump` — never `yaml.load` with unsafe loader
- User-controlled content (sources, tags) sanitized before insertion