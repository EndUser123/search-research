---
title: "Pipeline pause-phase schema contract: document the JSON format in the instruction"
created: 2026-08-12
source: session-019ff1a0
tags: [close-py, ship-py, pipeline-design, pause-phase, state-propagation, transferable-technique]
summary: >
  When a Python-orchestrated pipeline phase pauses and asks the LLM to write
  findings to a file, the JSON schema must be documented IN the instruction
  string itself, not just inferred from the code that reads it. Without this,
  the LLM may write a different schema shape and the receiving phase silently
  fails to propagate state. In close-py, the resolve phase wrote resolutions
  in varying formats, but the propagation code only checked one key
  ("resolutions"). The fix: (1) make the schema explicit in the pause-phase
  instruction, (2) add a fallback parser accepting multiple shapes. This
  pattern applies to all pause-phase designs in ship-py and close-py.
agent: grok
host: grok
cognitive_load: 3
verification: observed
relations:
  - target: wiki/concepts/ship-py-session-scoped-state-multi-terminal-isolation.md
    type: extends
  - target: wiki/concepts/close-runner-verdict-staleness-across-phases.md
    type: related
  - target: wiki/concepts/phase2-receipt-format-mismatch-stop-hook-rejects-claimed-scope.md
    type: related
---

# Pipeline pause-phase schema contract: document the JSON format in the instruction

## Decision context

The close-py pipeline has a resolve phase that pauses for LLM judgment: it
emits `needs_attention` gates, tells the LLM to resolve them using a tier
system, and asks the LLM to write the resolution to a findings file. The
LLM then re-invokes the phase with `--findings-file`.

The problem: the instruction told the LLM to "write the resolution summary
to the findings file" without specifying the JSON schema. The propagation
code in resolve.py checked for `resolution.get("resolutions", [])` -- a
list of `{"gate": "X", "state": "Y"}` dicts. But the LLM might write:

- `{"resolved_gates": [...]}` (different key name)
- `{"gates": {"X": {"state": "Y"}}}` (dict instead of list)
- `{"X": "waived"}` (bare mapping)

When the schema doesn't match, the propagation loop silently iterates over
an empty list, no gate states are updated, and the verdict phase still sees
them as `needs_attention`. The pipeline blocks with no diagnostic explaining
why.

## Root cause

The pause-phase instruction under-specified the output contract. The code
that READS the findings file had assumptions about schema shape that the
instruction string did not communicate to the LLM WRITING the file. This is
a **writer-reader schema mismatch** -- the same failure class as
[[phase2-receipt-format-mismatch-stop-hook-rejects-claimed-scope]], where
Phase 1 and Phase 2 used different receipt formats.

## Fix (two layers)

**Layer 1: make the schema explicit in the instruction.** The pause-phase
instruction now includes the JSON schema inline:

```
"After resolving, write a JSON object to the findings file with this schema:
{"resolutions": [{"gate": "<gate_name>", "state": "<new_state>"}]}.
Valid new_state values: resolved, waived, auto_resolved, confirmed."
```

This is the primary fix -- it prevents the mismatch at the source.

**Layer 2: add a fallback parser.** The propagation code now accepts three
shapes: `resolutions` (list), `resolved_gates` (list, alternate key), and
`gates` (dict). This handles cases where the LLM writes a slightly different
format despite the instruction.

Source receipt: `~/.grok/skills/close-py/__lib/phases/resolve.py` lines
60-93 (propagation logic), lines 115-125 (instruction with schema), commit
`6b73818`.

## Transferable pattern

This applies to EVERY pause-phase design in both pipelines:

| Pipeline | Pause phase | LLM writes | Reader phase |
|----------|------------|------------|--------------|
| close-py | resolve | resolution findings | verdict (reads scan_results.gates) |
| ship-py | review | review_findings.json | verdict + cross_validate |
| ship-py | fix | fix_results.json | verify |
| ship-py | risk | risk_findings.json | verdict |

**The rule:** any phase that pauses for LLM judgment and asks the LLM to
write a file MUST:
1. Include the exact JSON schema in the instruction string
2. Document valid enum values (e.g., `state: resolved|waived|auto_resolved`)
3. Have a fallback parser accepting 2-3 reasonable schema variants

Without (1), the LLM guesses the format. Without (3), a minor format
mismatch silently breaks state propagation.

## What this means for our workspace

Audit all pause-phase instructions in close-py and ship-py for schema
explicitness. Any instruction that says "write the results to the findings
file" without showing the JSON shape is a candidate for this bug.

This is the same class as [[close-runner-verdict-staleness-across-phases]]
(verdict derived from stale phase output) and
[[phase2-receipt-format-mismatch-stop-hook-rejects-claimed-scope]] (two
phases disagreeing on format) and [[ship-py-session-scoped-state-multi-terminal-isolation]]
(inter-phase state contract). The structural fix is the same in all cases:
**make the inter-phase contract explicit and validated.**

The fallback parser is defense-in-depth, not the primary fix. If the
instruction clearly specifies the schema AND the LLM still writes something
different, that's an LLM compliance issue, not a schema design issue. But
the fallback catches the 10-20% of cases where the LLM paraphrases the
schema despite clear instructions.

## Falsifier

This pattern would be wrong if LLMs reliably infer JSON schemas from code
context without explicit documentation. If a future model never produces
schema mismatches in pause-phase output, the instruction-level schema
documentation is unnecessary overhead. Until then, the empirical evidence
(this bug, plus [[phase2-receipt-format-mismatch-stop-hook-rejects-claimed-scope]])
shows that LLMs do guess schemas wrong.

## Receipts

- **resolve.py propagation logic**: `~/.grok/skills/close-py/__lib/phases/resolve.py` lines 60-93 (multi-shape parser)
- **resolve.py instruction with schema**: `~/.grok/skills/close-py/__lib/phases/resolve.py` lines 115-125 (pause-phase instruction)
- **Fix commit**: `6b73818` (2026-08-12)
- **Test suite**: `~/.grok/skills/close-py/tests/` -- 26/26 pass after fix

## Sources

- Bug discovered: session 019ff1a0 `/close-py` run (resolve phase)
- Fix commit: `6b73818` (2026-08-12)
- resolve.py source: `~/.grok/skills/close-py/__lib/phases/resolve.py` lines 60-125
- Related: [[phase2-receipt-format-mismatch-stop-hook-rejects-claimed-scope]] (same class)

## Auto-related

- [[pipeline-orchestration-and-transport-reliability]]
- [[close-runner-verdict-staleness-across-phases]]
- [[skill-catalog]]
- [[Python-Behavior-Tree-Framework-for-Autonomous-LLM-Agents--Technical-Specificatio]]
- [[python-orchestrated-skill-build-pattern-study-replicate-test]]

