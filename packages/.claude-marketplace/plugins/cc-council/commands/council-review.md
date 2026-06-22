---
name: council-review
description: Review council session metadata and artifacts
version: 1.0.0
---

# /council-review - Session Review

Inspect a previous council session's metadata, drafts, reviews, and synthesis.

## Usage

```
/council-review <session_id>
```

## Behavior

- Retrieves session from SQLite state database
- Displays full deliberation history
- Shows all drafts with anonymized labels
- Shows review rankings and critiques
- Displays synthesis and contradiction notes

## Examples

```
/council-review 550e8400-e29b-41d4-a716-446655440000
```

## Output

Markdown-formatted review with:
- Session metadata (state, duration, models)
- All draft responses
- Review rankings and critiques
- Synthesis result
- Provenance and contradictions