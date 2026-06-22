---
name: council-plan
description: Manual council invocation for planning tasks
version: 1.0.0
---

# /council-plan - Manual Council Invocation

Manually invoke the council deliberation process for planning tasks.

## Usage

```
/council-plan <prompt>
```

## Behavior

- Forces council execution regardless of gating rules
- Uses default models from provider
- Returns council deliberation result

## Examples

```
/council-plan Analyze the tradeoffs between REST vs GraphQL for a new API
```

## Output

JSON result with provenance metadata including:
- session_id
- models_used
- consensus_ratio
- duration_ms
- contradictions (if any)