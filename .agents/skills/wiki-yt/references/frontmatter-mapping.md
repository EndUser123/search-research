# Frontmatter mapping

How `nlm-to-wiki` maps NotebookLM extraction output to wiki SCHEMA-compliant
frontmatter. See `P:/.data/wiki/SCHEMA.md` §2-3 for the schema.

## Target schema (required by validate_wiki_entry.py)

```yaml
---
title: <string>           # from concept title
created: YYYY-MM-DD       # sync date
source: nlm-sync-YYYY-MM-DD
tags: [nlm-synced, <cluster-keyword>]   # nlm-synced always; cluster kw when --from-clusters
summary: >                # from concept definition (truncated 300 chars)
  <text>
agent: grok
host: both
cognitive_load: 3         # fixed; nlm-extracted concepts are mid-load by default
verification: single-source-verified  # extracted from one notebook; refine on multi-source
sources:                  # all sources that contributed to this concept
  - <notebook citation>
  - <source citations from data-table>
---
```

## Provenance extension (non-SCHEMA, wiki-yt-specific)

Appended after `sources:`:

```yaml
provenance:
  chain:
    - level: concept
      id: <slug>
    - level: notebook
      id: <notebook-uuid>
      title: <notebook-title>
      url: https://notebooklm.google.com/notebook/<uuid>
    - level: cluster           # present when --from-clusters used
      id: <cluster-id>
      name: <cluster-name>
      source_path: <path>
```

This is the 4-hop chain. A reader can click from concept → notebook →
cluster → original source URL. The cluster level is only present when
`sync.py --from-clusters clusters.json` was used; without it, the chain
stops at notebook.

## Relations

Two cases:

### New concept (no qmd match above threshold)

Relations are speculative — generated from the Report's "Related concepts"
list, capped at 3, with `type: related`. Targets may not exist yet (that's
fine — speculative links seed future pages).

### Refines an existing concept (qmd match ≥ threshold)

```yaml
relations:
  - target: wiki/concepts/<existing-slug>.md
    type: refines
```

The new page documents the same concept from a different source/notebook;
both pages survive. The reader sees the dialogue.

## Body sections

The page body follows the wiki skill's entry template:

| Section | Source |
|---|---|
| `# Title` | Concept title |
| `## Decision context` | Definition + notebook citation |
| `## Operational details` | Report bullet list (parsed from numbered items) |
| `## Verifiable values` | Data-Table values, formatted as a table |
| `## Related concepts` | `[[wikilinks]]` generated from report's "related" list |
| `## Citations` | Per-claim `{claim, source_id, expanded_context}` |
| `## What this means for our workspace` | Boilerplate pointing back to provenance chain |
| `## Falsifier` | Re-sync comparison |
| `## Sources` | Notebook link + Studio artifact note |

## Validator gate

`validate_wiki_entry.py` requires:

- ≥80 lines (research entry default)
- ≥3 `[[wikilinks]]`
- ≥2 quality sections (Decision Context, Key Findings, Implications, etc.)
- Required frontmatter fields

`write_pages.py` runs the validator after every page write. Pages that fail
are reported in the staging dir; the sync does NOT mark the notebook as
synced unless all pages pass. Failures need investigation — usually a
parse failure (no definition, no body) or insufficient cross-references.

## Known validator-failure causes

| Cause | Fix |
|---|---|
| Concept body had no `## ` sections in the Report | Improve REPORT_PROMPT; re-extract |
| Fewer than 3 `[[wikilinks]]` because related list was empty | Add `[[nlm-synced]]` and `[[notebooklm-cli-operational-gotchas]]` as defaults |
| Definition was empty (parse failure) | Inspect `concepts.json` staging output; tweak `parse_report.py` section detection |
| Line count < 80 | Concept was too thin; consider raising `REPORT_PROMPT`'s minimum section count |
