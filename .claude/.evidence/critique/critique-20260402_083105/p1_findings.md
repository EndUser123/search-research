## Triage Classification

hook — PreToolUse_directory_policy.py is a PreToolUse hook enforcing external path access policy. Target is the `is_allowed_external_path()` function (lines 177-256).

## Dispatched Specialists

- adversarial-compliance: Schema and API contract compliance for `is_allowed_external_path()`
- adversarial-io-validation: Path validation, boundary checks, file operations
- adversarial-logic: Off-by-one, inverted conditionals, wrong operators in the fix
- adversarial-security: Lock timeout fail-closed behavior, thread safety

## Specialist Findings Summary

### adversarial-compliance
**Domain:** Schema/API contract compliance
**Key findings:**
- No significant issues found in is_allowed_external_path(). Function correctly implements exact-path matching and fnmatch pattern matching. Separator validation correctly prevents child vs sibling path confusion.

### adversarial-io-validation
**Domain:** Path validation and I/O assumptions
**Key findings:**
- [MEDIUM] IO-001: Boundary check uses exact_path.lower() for prefix comparison but original exact_path length for indexing — claim is that `.lower()` changes length (FALSE — see adversarial-logic rebuttal)
- [LOW] IO-002: Early return of False when both patterns and exact_paths are empty — silent failure indistinguishable from loaded-but-restrictive allowlist
- [LOW] IO-003: Lock acquisition timeout (1s) returns False (deny) under contention — deliberate fail-safe design

### adversarial-logic
**Domain:** Pure logic correctness
**Key findings:**
- No logical issues found. The inverted startswith bug (exact_path.startswith(normalized)) was correctly fixed to normalized.startswith(exact_path.lower()). The separator boundary check and fallback for no-trailing-slash case are both logically sound.

**LOGIC-001 VERDICT — IO-001 Precision Failure (REBUTTAL):**
The adversarial-io-validation claim that `.lower()` changes string length is factually incorrect. Python's `str.lower()` preserves string length: `len("ABC") == len("abc") == 3`. Therefore `normalized[len(exact_path)]` after `exact_path.lower()` is always a valid index — no off-by-one exists. IO-001 is a precision failure (false positive).

### adversarial-security
**Domain:** Data access, auth, thread safety
**Key findings:**
- [LOW] SEC-001: Lock timeout of 1s causes fail-closed behavior (return False) on high lock contention. This is a deliberate design trade-off — fail-safe deny on timeout rather than fail-open. Not a security bug but a potential availability issue under extreme contention.

## Consolidated Findings

### Logical Gaps & Inconsistencies

1.1. [MEDIUM] (source: adversarial-io-validation → adversarial-logic rebuttal) — IO-001 is a precision failure. The claim that `normalized[len(exact_path)]` causes off-by-one for uppercase paths is false. Python's `str.lower()` preserves length: `len("ABC") == len("abc") == 3`. Therefore the indexing is always correct. IO-001 should be DOWNGRADED to informational. `PreToolUse_directory_policy.py:220,226`

### Hidden Assumptions & Fragile Dependencies

2.1. [LOW] (source: adversarial-security) — The 1-second lock timeout on `_ALLOWED_EXTERNAL_PATTERNS_LOCK` assumes lock acquisition completes within 1 second even under high concurrent contention. If 50+ terminals simultaneously validate external paths, the lock may not be acquired in time, causing all contested requests to return False (deny). `PreToolUse_directory_policy.py:182-191`

2.2. [LOW] (source: adversarial-io-validation) — Empty allowlist (`exact_paths=[]` and `patterns=[]`) is indistinguishable from a loaded-but-restrictive allowlist. No diagnostic is emitted to indicate the external path policy failed to initialize. `PreToolUse_directory_policy.py:210-211`

### Missing Obvious Actions / Best Practices

3.1. [MEDIUM] (source: adversarial-io-validation) — Lock contention metrics are tracked (`_lock_contention_count`, `_lock_wait_total`) but not surfaced to operators. Under high contention, the fail-closed behavior could cause user-visible blocking without any alerting.

### Risks and Edge Cases

4.1. [MEDIUM] (source: adversarial-security) — Fail-closed on lock timeout could cause denial of service during concurrent external path validation sessions. Not a security vulnerability but an availability risk. Likelihood: low (requires extreme contention), Impact: medium.

4.2. [LOW] (source: adversarial-io-validation) — Mixed-case paths in exact_paths config (e.g., uppercase `P:/.STAGING`) would work correctly since `.lower()` is applied before comparison — but this is not documented, so future config editors may not know case-insensitivity is handled.

### Concrete Recommendations

5.1. [MEDIUM] (source: adversarial-logic rebuttal) — IO-001 should be marked as a false positive/precision failure. The finding is withdrawn. No code change needed. Add precision note to adversarial-io-validation agent to prevent recurrence of language behavior misclaims.

5.2. [LOW] (source: adversarial-io-validation) — Consider emitting a debug log or warning when `is_allowed_external_path` returns False due to empty allowlists, to distinguish from legitimate denial.

5.3. [LOW] (source: adversarial-security) — Document the fail-closed-on-timeout design decision in code comments, and ensure lock contention telemetry is reviewed if user reports of blocked legitimate operations are received.

## Open Questions / Unknowns

6.1. [LOW] (source: adversarial-security) — Has the lock timeout issue manifested in practice? Telemetry tracking exists (`_lock_contention_count`, `_lock_wait_total`) but has not been reviewed. Uncertainty: whether 1s timeout is sufficient under peak load.

6.2. [LOW] (source: adversarial-io-validation) — Are mixed-case paths in `allowed_external_paths.exact_paths` a supported configuration? Current config shows lowercase only, but the code handles uppercase correctly. Uncertainty: whether to document this as a supported feature.
