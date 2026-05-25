---
description: "Schema-and-evidence discipline, source binding, attribution, retrospective claims"
alwaysApply: true
---

# Provenance

## Schema-and-Evidence Discipline

Before trusting any artifact (file, API response, log entry):
1. **Verify the producer** — who wrote it, with what authority
2. **Inspect the artifact** — read the actual content, don't trust the label
3. **Align producer/consumer** — ensure the schema the producer writes matches what the consumer expects
4. **Distinguish intermediate vs terminal** — intermediate artifacts (caches, temp files) can be stale; terminal artifacts (committed files, API responses) are more reliable

## Source Binding

Claims about documents, APIs, or external systems must cite a specific source:
- `"The API returns X"` → cite the response or documentation URL
- `"The file contains Y"` → cite the file path and line number
- `"We decided Z"` → cite the conversation turn, wiki page, or CLAUDE.md section

## Attribution Claims

When claiming someone (or some process) did something:
- `git blame` / `git log` for code changes
- CKS entries (`cks_search`) for decisions
- Wiki pages for architectural decisions
- Never attribute without evidence

## Retrospective Claims

Claims about past events require evidence from the relevant time period.
A current file state does not prove what the file contained last week.
Use `git log --before <date>` for historical state.
