---
title: "Tool-mismatch confabulation: using one tool's output to claim another tool's behavior"
created: 2026-08-09
source: session-019fdf3c
tags: [confabulation, receipt-discipline, tool-resolution, windows, debugging]
summary: >
  A specific sub-type of fabricated causal claim where evidence from one tool
  (PowerShell's Get-Command) is used to make claims about another tool's
  behavior (Python's shutil.which). The evidence is real but transferred to
  the wrong context, making the claim sound verified when it isn't. This
  pattern is distinct from pure confabulation (no evidence at all) because
  the agent DID run a diagnostic — just the wrong one.
agent: grok
host: grok
cognitive_load: 2
verification: observed
sources:
  - P:/tmp/diagnose_pi.py (session 019fdf3c, 2026-08-09) — shutil.which("pi") = pi.CMD
  - P:/tmp/diagnose_pi2.py (session 019fdf3c, 2026-08-09) — subprocess.run([pi.CMD, ...]) = exit 0
relations:
  - target: wiki/concepts/causal-mechanism-claims-require-source-receipts-before-durable-write.md
    type: refines
  - target: wiki/concepts/agent-fabricated-architectural-decisions-in-wiki-concepts.md
    type: related
---

# Tool-mismatch confabulation

## Decision context

During a ship-py v2.5 run, the trace phase failed with `"reason": "pi_not_found"`.
Investigating why, I ran `Get-Command pi` in PowerShell, which returned
`pi.ps1`. I then claimed that `shutil.which("pi")` in Python resolves to
`.ps1` and that `subprocess.run` cannot execute `.ps1` files. The operator
provided a sibling session's analysis showing this was wrong: `shutil.which`
returns `pi.CMD`, which subprocess CAN execute.

The question: why did the receipt-discipline rule (which explicitly covers
"fabricated explanation for unobservable system state") fail to prevent this
claim? The answer: I DID run a diagnostic — just the wrong one. The evidence
was real (Get-Command really does return .ps1) but transferred to the wrong
tool context (shutil.which is not Get-Command).

## The pattern

**Tool-mismatch confabulation** is a sub-type of receipt-discipline failure
where:

1. The agent runs a diagnostic in one tool (PowerShell, shell, file read)
2. The diagnostic returns real, verifiable evidence about THAT tool's behavior
3. The agent transfers the evidence to a DIFFERENT tool's context without
   running the second tool's equivalent diagnostic
4. The claim sounds verified because evidence exists — but the evidence is
   from the wrong source

This is harder to catch than pure confabulation (no evidence at all) because:
- A hook checking "did you run a diagnostic?" would see the Get-Command call
- The evidence is factually correct (Get-Command DOES return .ps1)
- The error is in the TRANSFER, not the evidence itself

## Concrete instance

| Step | What happened | What should have happened |
|------|---------------|--------------------------|
| 1 | Ran `Get-Command pi` in PowerShell → returned `pi.ps1` | Should have run `python -c "import shutil; print(shutil.which('pi'))"` → would return `pi.CMD` |
| 2 | Claimed `shutil.which("pi")` resolves to `.ps1` | Should have verified with the actual Python function |
| 3 | Proposed `shell=True` fix (introduces injection risk) | Should have verified the existing `_PI_BINARY` resolution works before proposing changes |

## Why PowerShell and Python resolve differently

- **PowerShell's `Get-Command`** searches PATH and prefers `.ps1` files when both `.ps1` and `.cmd` exist (PowerShell-native extension preference)
- **Python's `shutil.which`** searches PATH using `PATHEXT` environment variable ordering, which on Windows puts `.CMD` before `.PS1`
- Both are correct for their respective ecosystems; the mismatch only causes errors when one tool's result is transferred to another tool's context

## What this means for our workspace

1. **When debugging subprocess failures**, always run the Python diagnostic
   (`shutil.which`, `os.environ`, `sys.path`) — not the PowerShell equivalent
   (`Get-Command`, `$env:PATH`). They resolve differently.

2. **The confabulation_gate hook** catches this pattern when the claim is
   stated as fact without any receipt. But it would NOT catch the case where
   a receipt exists from the wrong tool — that's a harder detection problem
   requiring semantic understanding of tool equivalence.

3. **The receipt-discipline rule** covers this case in principle ("a causal
   claim without a verification tool call does not ship as [FACT]"). The
   structural gap is that the agent considers the Get-Command call to BE
   the verification — it doesn't recognize that Get-Command is not the right
   verifier for a shutil.which claim.

## Falsifier

This concept is wrong if:
- PowerShell and Python path resolution are actually identical on this host (they aren't — verified)
- The pattern never recurs (if it only happened once and the sub-type doesn't generalize, it doesn't need its own concept)
- The existing receipt-discipline rule is sufficient to prevent recurrence without naming the sub-type (possible — the rule is already comprehensive)

## Sources

- `P:/tmp/diagnose_pi.py` (session 019fdf3c, 2026-08-09) — confirmed `shutil.which("pi")` = `C:\Users\brsth\AppData\Roaming\npm\pi.CMD`
- `P:/tmp/diagnose_pi2.py` (session 019fdf3c, 2026-08-09) — confirmed `subprocess.run([pi.CMD, "--version"])` = exit 0, stdout "0.82.1"
- Sibling session analysis (provided by operator, 2026-08-09) — identified the tool-mismatch and confirmed `_PI_BINARY` resolution works correctly

## Receipts

- `C:/Users/brsth/.grok/skills/ship-py/__lib/dispatch_base.py:36` — `_PI_BINARY = shutil.which("pi") or "pi"` (the resolution that works correctly)
- `P:/tmp/diagnose_pi.py` lines 8-10 — `shutil.which("pi")` = `C:\Users\brsth\AppData\Roaming\npm\pi.CMD` (verified this session)
- `P:/tmp/diagnose_pi2.py` lines 6-12 — `subprocess.run([pi.CMD, "--version"])` = exit 0, stdout "0.82.1" (verified this session)

## Related

- [[causal-mechanism-claims-require-source-receipts-before-durable-write]] — the general rule this refines
- [[agent-fabricated-architectural-decisions-in-wiki-concepts]] — another instance of the confabulation pattern
- [[asserting-runtime-behavior-from-memory-not-testing]] — the broader "don't claim without testing" pattern
- /confabulation-gate-stop-hook — the hook that catches pure confabulation (but not tool-mismatch)

## Auto-related

- [[skill-catalog]]
- [[model-tool-calling-capability-matrix]]
- [[claude-code-external-tool-integration-via-mcp]]
- [[I'm-going-to-create-a-hook-to-enforce-discovery-be]]
- [[router-proxy-tool-calling-normalization-patterns]]

