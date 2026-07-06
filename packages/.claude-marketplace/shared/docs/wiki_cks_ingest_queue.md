# Wiki/CKS Ingest Queue Specification

## Overview

Review workflows (`/improve`, `/red-team`, `/gto`, `/debrief`) may propose notes for long-term
preservation in the wiki (QMD) or Constitutional Knowledge System (CKS). This specification
defines the queue artifact format and consumption contract.

## Queue Location

```
.claude/.artifacts/wiki_ingest/proposed_notes/{session_id}.jsonl
```

Each session writes its own `{session_id}.jsonl` file. Multiple sessions can write
concurrently without lock contention.

## Entry Format (JSONL)

Each line is a JSON object conforming to the promotion opportunity schema:

```json
{
  "id": "OPP-001",
  "source_workflow": "improve|red-team|gto|debrief",
  "observation": "What was observed",
  "evidence": "file:line or tool output or citation",
  "reusable_lesson": "The pattern or lesson to preserve",
  "promotion_target": "skill|hook|prompt|config|test|docs|cks_or_wiki|task|backlog|reject",
  "uniqueness": "new|strengthens_existing|duplicate|rejected",
  "confidence": "high|medium|low",
  "proposed_action": "Concrete action to take",
  "validation_signal": "How to verify it worked",
  "falsification_condition": "What would prove this wrong",
  "related_opportunities": ["OPP-002"],
  "metadata": {
    "session_id": "uuid",
    "timestamp": "2026-07-05T14:30:00Z",
    "tags": ["pattern", "gate", "performance"]
  }
}
```

## Promotion Target Semantics

| Target | Meaning | Example Action |
|---------|---------|----------------|
| `skill` | Update or create a skill | "Add failure mode to /red-team security specialist" |
| `hook` | Update or create a hook | "Add validation to Stop hook" |
| `prompt` | Update a prompt template | "Improve prompt to avoid ambiguous framing" |
| `config` | Update configuration | "Add setting to control threshold" |
| `test` | Add or improve tests | "Add regression test for this path" |
| `docs` | Update documentation | "Document this edge case in CLAUDE.md" |
| `cks_or_wiki` | Knowledge preservation | "Capture this pattern in wiki/CKS" |
| `task` | Create a task | "Add to tasks.json queue" |
| `backlog` | Defer indefinitely | "Keep for future consideration" |
| `reject` | Discard | "Not worth pursuing" |

## Uniqueness Values

| Value | Meaning |
|-------|---------|
| `new` | This is a new opportunity not seen before |
| `strengthens_existing` | This strengthens or refines an existing opportunity (cite the ID) |
| `duplicate` | Exact duplicate of existing opportunity (cite the ID) |
| `rejected` | Explicitly rejected after review (state why in `proposed_action`) |

## Validation Rules

1. **Evidence required**: Every entry must have `evidence` field with concrete citation
2. **No raw web snippets**: Summarize lessons from web sources; don't paste raw content
3. **No user-specific preferences without intent**: Only generalize personal workflows
   when explicitly intended
4. **Falsification required**: Every entry must state what would prove it wrong

## Consumption Contract

### Dedicated Ingest Workflow

A dedicated `/wiki-ingest` or similar workflow should:

1. **Lock-free read**: Process JSONL files atomically (read entire file, process, move to `processed/`)
2. **Duplicate detection**: Before ingesting, search existing wiki/CKS for similar entries
   - Use CKS search: `cks_search` or `cks_search_semantic` with query
   - Use wiki search: `/wiki search` or QMD backend search
   - If match found >80% similarity, mark as `duplicate` and cite the existing entry
3. **Quality gate**: Apply LLM quality gate (same as CKS quality gate) to reject
   low-quality or noise entries
4. **Write only on explicit approval**: Do not silently write to wiki/CKS
   - Queue for review
   - Require user approval: `/wiki-ingest approve OPP-001`
   - Write only after approval

### Default Behavior for `/improve` and `/red-team`

- **May propose notes**: Workflows can emit entries to the queue
- **Do not write directly**: No automatic wiki/CKS writes from review workflows
- **User-controlled ingestion**: A separate explicit command/approval performs writes

## Example Entry

```json
{
  "id": "OPP-042",
  "source_workflow": "red-team",
  "observation": "Stop-hook firing on 'performance' prose when no quantitative measurement is present",
  "evidence": "red-team session 2026-07-05, finding SEC-003, file:Stop_hook_performance.py:145",
  "reusable_lesson": "Stop-hook should distinguish qualitative ROI language from quantitative performance attribution. Only flag 'performance' claims when actual timing/telemetry/profiling evidence is cited.",
  "promotion_target": "hook",
  "uniqueness": "new",
  "confidence": "high",
  "proposed_action": "Update Stop-hook to require evidence tool citation before flagging 'UNVERIFIED PERFORMANCE ATTRIBUTION' on ROI prose alone",
  "validation_signal": "Stop-hook no longer fires on qualitative ROI statements without measurements",
  "falsification_condition": "If legitimate performance bugs are missed because they lack measurements, this rule is too strict",
  "related_opportunities": [],
  "metadata": {
    "session_id": "2d173c3b-b55a-4b7c-9029-aced741e985a",
    "timestamp": "2026-07-05T14:30:00Z",
    "tags": ["stop-hook", "performance-attribution", "quality-gate"]
  }
}
```

## Falsification Conditions (Examples)

**Good falsification conditions:**
- "If this pattern appears in >3 sessions without causing problems, reject as noise"
- "If removing this gate causes a regression that was previously caught, the rule is too strict"
- "If this lesson is already documented in CLAUDE.md at line X, mark as duplicate"

**Weak falsification conditions (avoid):**
- "If someone disagrees" — not testable
- "If it doesn't work" — too vague
- "If it's not a good idea" — subjective

## Integration Notes

If a better CKS/wiki ingestion path already exists in the repo, use that instead of
creating a duplicate. This queue format is designed to be compatible with existing
ingestion workflows by following the shared promotion opportunity schema.

## See Also

- Shared schema: `packages/.claude-marketplace/shared/schemas/promotion_opportunity.schema.json`
- CKS search: `cks_search` and `cks_search_semantic` MCP tools
- Wiki search: `/wiki` command and QMD backend search APIs
