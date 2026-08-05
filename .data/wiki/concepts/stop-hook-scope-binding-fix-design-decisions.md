---
title: "Stop hook scope-binding fix — design decisions"
created: 2026-07-26
source: session-2026-07-25 (/design --lite on Stop hook scope-binding problem)
sources:
  - C:\Users\brsth\AppData\Local\Temp\grok-design-4e4629f7\grok-design-doc-4e4629f7.md (design doc, temp — will be reaped)
  - P:/.artifacts/risks/019f9b6f-98fc-7883-9d5f-cf570a0b3812/20260725-182300/ (red-team + tp + why artifacts)
  - C:/Users/brsth/.grok/hooks/scripts/quality_gate.py (Stop hook source)
  - C:/Users/brsth/.grok/hooks/scripts/verification_receipt_writer.py (receipt writer source)
tags: [design-decision, verification-receipt, scope-binding, stop-hook, auto-inference, error-messages, adr]
summary: >
  Three design decisions for fixing the Stop hook scope-binding problem where pytest
  commands referencing test directories (not modified source files) produce receipts
  with empty scope, causing repeated NO_COVERING_RECEIPT blocks. Decision D1: extend
  the scope_basis registry with TEST_FILE_TO_SOURCE_INFERENCE (not replace). Decision
  D3: conservative inference requiring explicit imports in test files (AST primary,
  regex fallback). Decision D5: security model preserved — observed_state_refs is
  never auto-promoted to claimed_scope_refs; inference only adds source files that
  are already in observed_paths. These decisions were made after /why RCA, /risks,
  /tp critique, and /design --lite review (18 findings, all addressed, 0 open).
agent: grok
host: grok
cognitive_load: 3
verification: design-reviewed
relations:
  - target: wiki/concepts/code-orchestrates-model-judges-skill-scale
    type: related — documents the receipt system at meso level
  - target: wiki/concepts/designing-harnesses-that-make-good-behavior-the-path-of-least-resistance
    type: related — validators > advisory rules principle
  - target: wiki/concepts/fabricated-causal-chain-receipt-required
    type: related — receipt-first principle
  - target: wiki/concepts/best-practices-enforcement-mechanism-grok-build
    type: related — structural enforcement over prose rules
---

# Stop hook scope-binding fix — design decisions

## Decision context

**Why this design was needed:** the Stop hook blocked the agent 5 times in one
session with `NO_COVERING_RECEIPT` despite running pytest successfully each
time. The root cause (from `/why` RCA): the receipt writer binds scope ONLY
from explicit path arguments in the verification command text. `pytest tests/`
binds `tests/` to scope but not `validators.py`. The obligation requires the
modified file in `claimed_scope_refs`, so the receipt is rejected.

The deeper root cause: the scope-binding contract is documented in Python code
comments, not in agent-facing instructions. And the hook's error message
("NO_COVERING_RECEIPT") doesn't explain which check failed or what would
satisfy it. This is the same failure class documented in
[[designing-harnesses-that-make-good-behavior-the-path-of-least-resistance]]:
advisory rules don't fire under pressure, and the system's own error output
doesn't guide correction.

**What the design changed:** a 3-layer fix — (A) auto-inference of source
files from test file imports, (B) per-reason-code error messages with concrete
remediation, (C) agent-facing documentation of the scope-binding contract.
The receipt system itself is documented at meso level in
[[code-orchestrates-model-judges-skill-scale]]. The receipt-first principle
that motivates the conservative scope-binding design is documented in
[[fabricated-causal-chain-receipt-required]]. The broader enforcement
mechanism context is in
[[best-practices-enforcement-mechanism-grok-build]].

## D1: Extend the scope_basis registry, do not replace it

**Decision:** Add `TEST_FILE_TO_SOURCE_INFERENCE` as a fifth value in the
existing `scope_basis` enum. The existing values are: `EXPLICIT_PATH_ARGUMENT`,
`TEST_TO_SOURCE_MAPPING`, `REPOSITORY_WIDE_VERIFIER`, `OPERATOR_DECLARED_SCOPE`.

**Selection criterion:** durability + lowest future maintenance cost.

**Why this wins:** `[FACT]` `_check_obligation_satisfied` in `quality_gate.py:815-821`
maintains an allow-list of approved basis values. Adding a new value is a
one-line change. The alternative — changing `scope_basis` to a richer structure —
would require changes in `verification_receipt_writer.py`, `quality_gate.py`,
the receipt schema, and all test fixtures. The new value follows the existing
`TEST_TO_SOURCE_MAPPING` precedent (directory-level mapping already exists;
this adds file-level mapping).

**Rejected alternatives:**
- Replace scope_basis with a richer structure (too much churn for the gain)
- Remove scope_basis entirely and use only `claimed_scope_refs` (loses the
  basis-quality signal that distinguishes explicit from inferred)

**Falsifier:** if a future need arises for non-test-related auto-inference
(e.g., a static analyzer that covers specific source files), a richer
structure would be needed. The current design holds as long as all known
verifier patterns are test runners or static analyzers.

## D3: Conservative inference — require explicit imports in the test file

**Decision:** The file-level mapper requires the test file to `import` the
source module (parsed via `import` / `from … import` AST, with regex fallback
for SyntaxError cases).

**Selection criterion:** security model preservation + false-positive prevention.

**Why this wins:** `[FACT]` the existing directory-level mapper
(`_map_pytest_directory_to_sources`) uses regex text matching
(`re.search(rf"\b{re.escape(stem)}\b", combined_tests)`). The file-level mapper
should be stricter because it operates on a single file with higher confidence
available: the test file's imports are the explicit contract of what it tests.

**Conservative inference gates (all must hold):**
1. The test file exists and is readable
2. The AST/regex parse succeeded
3. The candidate source file exists on disk
4. The candidate source file is in `observed_paths` (was modified this session —
   defense against false coverage of unrelated files)

Gate 4 is the security-critical one: it means the inference can NEVER claim
coverage for a file the agent didn't modify. This is what preserves the
security model.

**Rejected alternatives:**
- Loose inference (any file the test mentions by name) — too many false
  positives; a test that mentions `validators.py` in a docstring would
  falsely claim coverage
- No inference (documentation only) — doesn't fix the core defect; advisory
  rules don't fire under pressure

**Falsifier:** if a test file uses runtime imports (`__import__("foo")`), string-based
lookups, or `importlib.import_module`, the inference will miss it. The
conservative choice is to require the explicit form and document the gap. The
agent can always fall back to `pytest` (no args) for repository-wide coverage.

## D5: Security model preserved — observed_state_refs never auto-promoted

**Decision:** The new `TEST_FILE_TO_SOURCE_INFERENCE` only adds the source
file to `claimed_scope_refs` if the source file is in `observed_paths` (already
modified this session). The hook still never auto-promotes
`observed_state_refs` to `claimed_scope_refs`.

**Selection criterion:** don't weaken the existing security guarantee.

**Why this matters:** `[FACT]` `_check_obligation_satisfied` explicitly
distinguishes `claimed_scope_refs` (line 805-810 — the only set checked for
scope coverage) from `observed_state_refs` (checked only for fingerprint
freshness). The new scope_basis is *more permissible* than
`EXPLICIT_PATH_ARGUMENT` (it allows inference) but it is *not* equivalent to
observed-state-as-coverage. The inference adds to `claimed_scope_refs` only
when the test file's import proves the relationship AND the source was
modified this session.

**Falsifier:** if a malicious test file imports a source module from a
different package, the new mapper would falsely claim coverage. The defensive
layer is gate 4 (source file must be in `observed_paths`). The threat is
bounded to files the agent already modified.

## Receipts

- `[FACT]` `_check_obligation_satisfied` at `quality_gate.py:751-845` — receipt: read this turn during /why investigation
- `[FACT]` `_extract_explicit_paths` at `verification_receipt_writer.py:149-180` — receipt: read this turn during /why investigation
- `[FACT]` `_map_pytest_directory_to_sources` at `verification_receipt_writer.py:210-265` — receipt: cited in design doc
- `[FACT]` CAPABILITY_HIERARCHY at `quality_gate.py:777` allows higher ranks to satisfy lower requirements — receipt: read this turn
- `[FACT]` The 5 blocking iterations occurred — receipt: obligation file at `~/.grok/hooks/state/quality-obligation-019f9b6f...json`, status PENDING, nonce 6ee39b99...
- `[INFERENCE]` the design doc's auto-inference will work for the common case (`pytest tests/test_foo.py`) — not yet implemented; will be verified post-implementation
- `[UNKNOWN]` whether the AST/regex cascade handles all import patterns in the workspace's test files — needs post-implementation testing

## Falsifier for the overall design

The 3-layer fix is wrong if:
- Auto-inference produces false positives at >10% rate (measured by shadow-log
  analysis over 10 sessions post-deployment). Would require tightening the
  inference gates.
- The error-message reason codes don't actually help agents self-correct
  (measured by counting re-blocks per obligation: if average re-blocks drops
  from 5 to <2, the fix works). 30-day post-deployment review.
- The documentation (AGENTS.md rule) is never read by agents in practice,
  making Layer C useless. This is why Layers A and B are structural; Layer C
  is the durability layer.
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
