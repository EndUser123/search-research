---
name: keep
description: Alias for /note — add a deliberate entry to your constitutional knowledge system (CKS). Use when you want to remember a decision, pattern, correction, lesson, or insight. Same behavior as /note; "keep" reads more naturally for "I want to keep this."
---
workflow_steps: []
# Keep (`/keep`)

Deliberate write into CKS. Identical behavior to `/note`; this command exists because "keep" reads more naturally for "I want to keep this around." Both `/note` and `/keep` route to the same `note_writer.py` module.

Use either when you've made a decision worth remembering, spotted a pattern, want to flag a correction, or want to write an insight/memory into your searchable corpus. For everything else, just keep going — CKS auto-capture picks up incidental context.

## Entry types

Pick the one that best matches the content. The quality gate is strict; junk gets rejected.

| Type | Use for |
|------|---------|
| `memory` | Persistent context you want retrievable later (default) |
| `pattern` | A recurring shape / heuristic that applies to future work |
| `correction` | A specific mistake + the correct behavior (paired) |
| `insight` | A non-obvious connection or finding |
| `code` | A code-specific rule or convention |

## Quick Usage

```bash
/keep "Use the rename tail only when the new name is actually shorter" --type pattern
/keep "Decided: /find /web /all get dropped" --type decision
/keep --help
```

## Your Workflow

1. **Detect the trigger** - User says `/note` or `/keep` with content.
2. **Classify the entry type** - Pattern? Decision? Correction? Insight? Memory? (If unclear, default `memory`.)
3. **Generate the dry-run preview** - Title + body + entry type + tags. The script formats this as the CKS payload.
4. **Show the preview to the user** - 3-5 lines. The user sees exactly what will be ingested.
5. **Confirm with the user** - If they say "yes" / "do it" / "ingest", run the CKS add. If they push back, refine the title or body.
6. **Show the result** - CKS entry id, or the quality-gate rejection if it bounced.

## Validation Rules

- **Never invent module paths.** Use only the canonical path `core/cks/cks_add_cli.py` from the plugin cache root.
- **Always show the dry-run preview before ingesting.** No silent CKS writes.
- **If the quality gate rejects, surface the reason verbatim.** Don't soften or summarize the rejection.
- **Empty title or empty body is a no-op.** Don't auto-fill; ask the user to fill in.
- **Duplicate detection is the quality gate's job, not yours.** If it bounces a "duplicate," show the user the existing entry, don't override.

## Execution

Run from the cache-resolved plugin root:

```bash
cd "$(ls -d "$HOME/.claude/plugins/cache/local/search-research/"*/ | sort -V | tail -1)" && \
python -m skills.keep.note_writer --title "$title" --body "$body" --type "$entry_type"
```

`skills/keep/note_writer.py` is the same module as `skills/note/note_writer.py` — they're two command entry points to the same code. (Or, if Claude Code resolves `python -m <skill>`, you can import the shared logic from either.)

## Integration Points

- **CKS** - This is the write path. Existing read is `/find "pattern xyz"`.
- **`/find`** - The retrieval layer; use it to verify a new keep doesn't duplicate existing entries.
- **`/web`** / **`/all`** - Search before writing if the entry is a fact-check / correction.
