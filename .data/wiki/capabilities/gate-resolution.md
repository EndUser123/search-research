---
title: "gate-resolution"
node_type: capability
created: 2026-07-28
domain: lifecycle
---

# gate-resolution

**Inputs:** session state (handoffs, wiki, git, temp files)
**Outputs:** gate states (pass/needs_attention/needs_llm_check) + close summary

## Procedure

close_accounting.py scans all gates mechanically. Emits pre-computed summary.
