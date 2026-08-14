---
name: all
description: "Compatibility wrapper for the canonical /research workflow; preserves the historical /all invocation."
workflow_steps: []
---
# `/all` compatibility

`/all` is retained for compatibility and delegates to the canonical
`search-research:/research` execution substrate. It performs no independent
research, routing, provider selection, source assessment, or artifact logic.

Use `/research` for new research requests. Existing `/all` callers retain
their behavior and are recorded with caller identity `search-research:/all`.
