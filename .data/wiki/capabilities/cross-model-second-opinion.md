---
title: "cross-model-second-opinion"
node_type: capability
created: 2026-07-28
domain: cross-model
---

# cross-model-second-opinion

**Inputs:** `prompt` or task, `target_model` (agy|codex|mmx)
**Outputs:** run record with outcome label (MATERIAL_DELTA, CONFIDENCE_GAIN, etc.)

## Procedure

Dispatch via /agy, /codex, or /mmx skill. Normalize result. Label outcome.
