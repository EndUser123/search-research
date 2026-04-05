# Architecture Decision: original_user_request in Checkpoint Metadata

## Context
After compaction, LLM was inferring wrong task from loaded files instead of continuing original work.

## Decision
Add `original_user_request` field to checkpoint metadata to preserve task intent across compaction.

## Implementation
- **File:** `PreCompact_checkpoint_capture.py`
- **Change:** Persist extracted `last_user_message` to checkpoint_metadata
- **File:** `SessionStart_checkpoint_restore.py`
- **Change:** Display `## Original Request: {message}` at top of restoration prompt

## Alternatives Considered
1. Conversation summary (rejected: adds LLM call latency)
2. Structured task intent (rejected: over-engineering for solo-dev)

## Confidence
85% — Tests pass, minimal change, leverages existing extraction

## Mitigation
If last message ≠ task intent, add `first_user_request` field as well.
