---
title: "verified-findings-on-disk"
node_type: capability
created: 2026-07-28
domain: review
---

# verified-findings-on-disk

**Inputs:** specialist outputs (JSON per lens)
**Outputs:** FINDINGS.md + findings.json with verification status per finding

## Procedure

Spawn independent verifier. Re-read source at current HEAD. Confirm or refute each finding.
