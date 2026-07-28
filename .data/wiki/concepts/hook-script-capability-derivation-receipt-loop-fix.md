---
title: Hook Script Capability Derivation — Receipt Loop Fix
created: 2026-07-28
tags: [verification, receipt-system, hooks, bug-fix, root-cause]
sources:
  - quality_gate.py _derive_required_capability (lines 709-755)
  - verification_receipt_writer.py _map_pytest_file_to_sources (implemented 2026-07-28)
  - Session 019fa48a receipt-loop incident
---

# Hook Script Capability Derivation — Receipt Loop Fix

## Problem

Every edit to a hook script file under `~/.grok/hooks/scripts/*.py` triggered an
infinite `NO_COVERING_RECEIPT` loop in the Stop hook verification gate. The agent
would edit the file, run `pytest` to verify, and the Stop hook would block because
"no covering receipt" existed — no matter how many times the verification ran.

## Root Cause

`_derive_required_capability` in `quality_gate.py` classified ALL files under
`~/.grok/hooks/` as requiring `runtime_hook` capability (rank 5 in the capability
hierarchy):

```python
# BEFORE (broken):
if any("/.grok/hooks/" in p or p.endswith("/.grok/hooks") for p in normalized):
    return "runtime_hook", "hook_or_enforcement_path"
```

This path check matched both:
- **Hook JSON registrations** (`~/.grok/hooks/behavioral-check.json`) — genuinely need
  runtime verification (is the hook discovered and fired?)
- **Hook scripts** (`~/.grok/hooks/scripts/behavioral_check.py`) — just Python code
  that unit tests can verify

Meanwhile, `pytest` is classified as `unit_behavior` (rank 3) by `_detect_verifier`.
Since `3 < 5`, the capability check in `_check_obligation_satisfied` always failed:

```python
receipt_rank (3) < required_rank (5)  # → continue (skip this receipt)
# No receipt satisfies → NO_COVERING_RECEIPT → block
```

## Fix

Narrowed the `runtime_hook` path match to exclude `hooks/scripts/` and `hooks/state/`:

```python
# AFTER (fixed):
hook_registration_paths = [
    p for p in normalized
    if ("/.grok/hooks/" in p or p.endswith("/.grok/hooks"))
    and "/.grok/hooks/scripts/" not in p
    and "/.grok/hooks/state/" not in p
]
if hook_registration_paths:
    return "runtime_hook", "hook_registration_path"
```

Hook scripts now fall through to the existing `/scripts/` check → `static_analysis`
(rank 2). Since pytest provides `unit_behavior` (rank 3 ≥ 2), the capability check passes.

## Secondary Fix: File-Level Scope Mapping

The scope matching had a second limitation: running `pytest test_hooks.py` (a file)
didn't map to the source file (`behavioral_check.py`) because only directory-level
mapping existed (`_map_pytest_directory_to_sources`).

Implemented `_map_pytest_file_to_sources` to handle individual pytest file arguments:
- Extracts the test file path from the command
- Reads the test file and checks import references via AST
- Falls back to regex matching when the test file has SyntaxError
- Maps observed source files that the test explicitly imports

This makes `pytest test_hooks.py` correctly claim coverage of `behavioral_check.py`
when the test imports it.

## Verification

- `_derive_required_capability` now returns correct capabilities for all path types
- 6 pytest tests pass, 8 smoke tests pass, 10 behavioral hook tests pass
- Direct capability check: hook script → `static_analysis`, hook JSON → `runtime_hook`

## Design Principle

The capability hierarchy should classify based on **what kind of evidence is needed**,
not on **what directory the file is in**. A hook script is Python code — its correctness
is verifiable by unit tests. The runtime discovery question (does the JSON registration
cause the hook to fire?) is a separate concern that belongs to JSON registration files,
not to the script implementations.

## Related

- [[verification-receipt-systems-design-landscape]] — multi-source receipt policy
- [[verification-claim-admissibility]] — PROVEN vs COMPONENT_PROVEN vocabulary
- Handoff: `verification-protocol-design-20260728` (updated: receipt-loop resolved)

## Addendum (2026-07-28): lastAssistantMessage payload bug

While verifying the behavioral hooks produce correct output, discovered that both
`behavioral_check.py` and `wiki_persistence_check.py` used the wrong field name
to extract the response text from the Stop hook payload. They checked `response`,
`messages`, and `transcript_path` — but the Grok Build Stop hook provides
`lastAssistantMessage` (documented at `user-guide/10-hooks.md:262`).

Without this fix, both hooks would have been **permanently silent in production** —
the `extract_response_text` function returned empty string for every real payload,
causing the hooks to exit immediately with no output.

The existing hooks (`dbr_language_check.py`, `quality_gate.py`) already used the
correct field. The bug was introduced because the new hooks were modeled on
generic hook templates rather than the existing working hooks on this host.

**Lesson:** when writing hooks for Grok Build, model the payload extraction on
existing WORKING hooks on the same host, not on generic templates. The
`lastAssistantMessage` field is documented but easy to miss.
