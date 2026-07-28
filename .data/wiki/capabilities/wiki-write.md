---
title: "wiki-write"
node_type: capability
created: 2026-07-28
domain: knowledge
---

# wiki-write

**Inputs:** `title` (string), `body` (markdown), `tags` (list), `sources` (list, optional), `content_type` (finding|decision|reference), `relations` (list, optional)
**Outputs:** `concept_path`, `validation_result` (pass|fail), `log_appended` (bool)

## Step 1: Retirement check

```
grep pattern="<title keywords>" path="P:/.data/wiki/concepts/" -i
```

Supersede → set `status: superseded` + `superseded_by:`. Contradict → flag conflict. Refine → add `relations` entry.

## Step 2: Write concept

Path: `P:/.data/wiki/concepts/<slug>.md`

Minimum frontmatter:

```yaml
---
title: "<title>"
created: YYYY-MM-DD
source: <session-ID or URL>
tags: [<tags>]
summary: >
  <2-4 sentences for discoverability>
agent: grok
host: grok
verification: <multi-source-verified|observed|inferred|local-only>
---
```

Minimum body sections: Decision Context, Main Content, What This Means, Falsifier.

Full spec: `P:/.data/wiki/SCHEMA.md` §2-4.

## Step 3: Validate (mandatory)

```bash
python ~/.grok/skills/wiki/scripts/validate_wiki_entry.py "<path>"
```

Exit 0 = pass. Exit 1 = fix before done.

## Step 4: Log

```bash
python P:/.data/wiki/scripts/append_log.py "<slug>" "<title>"
```
