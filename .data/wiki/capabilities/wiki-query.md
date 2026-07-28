---
title: "wiki-query"
node_type: capability
created: 2026-07-28
domain: knowledge
---

# wiki-query

**Inputs:** `query` (string), `scope` (path, default `P:/.data/wiki/concepts/`)
**Outputs:** matching concepts `[{path, title, summary}]`, match count

## Procedure

```
grep pattern="<query>" path="P:/.data/wiki/concepts/" -i
```

For handoffs (intermediate knowledge not yet promoted to wiki):

```
rg -l "<query>" P:/docs/handoffs/
```

## Output shape

```
- <slug>.md — <one-line summary> (P:/.data/wiki/concepts/<slug>.md)
Gaps: <what was NOT found>
```
