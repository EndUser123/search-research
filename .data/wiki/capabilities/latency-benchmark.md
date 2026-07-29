---
title: "latency-benchmark"
node_type: capability
created: 2026-07-28
domain: fleet-ops
---

# latency-benchmark

**Inputs:** model slugs, prompt set
**Outputs:** latency results (wall-clock per model per prompt)

## Procedure

Send standardized prompts to each fleet model in parallel. Record wall-clock.
