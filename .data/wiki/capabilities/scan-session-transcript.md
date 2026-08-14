---
title: "scan-session-transcript"
node_type: capability
created: 2026-08-13
domain: lifecycle
---

# scan-session-transcript

**Inputs:** session transcript (chat_history.jsonl), compaction segments
**Outputs:** improvement opportunities, unactioned items, tacit knowledge, friction findings

## Procedure

Read session transcript. Scan for categories of opportunity (corrections,
decisions, gaps, friction, near-misses, unactioned items, unverified
assertions). Route findings to persistence (wiki, handoff, task).

## Providers

- `/todo` Step 0.5 (via `/insight` + `/aar` parallel subagents)
- `/insight` (standalone, 10-category scan, dual-stream routing)
- `/aar` (standalone, evidence-grounded reconstruction, always deep mode)
- `/triage` (category-bounded review of session output)
