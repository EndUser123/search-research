---
thread_id: 019fe7e9-cd04-7a63-9436-1b446826024a
parent_handoff_path: none
current_session_id: 019fe7e9-cd04-7a63-9436-1b446826024a
current_terminal_id: grok-build-019fe7e9
produced_at: 2026-08-10T02:00:00Z
status: open
handoff_type: investigation
accurate_as_of_head: HEAD
---

# Verification receipt: declarative manifest + anti-gaming (Fix C)

## Objective

Complete and harden the verification-receipt-manifest system that lets verification scripts declare their scope/capability via comment headers. The core fix shipped; the anti-gaming layer shipped; known residual risks remain.

## Status

PARTIALLY_DONE — declarative manifest + anti-gaming verification shipped and tested. Residual risks (R1, R2 from /risk scan) are LOW and documented but not fixed.

## Producing context

2026-08-10, session 019fe7e9. The Stop hook blocked 4 times on verification receipts because `_detect_verifier` in `verification_receipt_writer.py` couldn't see inside verification scripts — it classified by filename (`verify_*.py` → `unit_behavior`) instead of by content (`ast.parse` → `syntax`). Root cause: the receipt writer inspects command text only, not script contents. The /www research validated that the industry-standard fix is explicit declaration (Bazel BUILD deps, GitHub Actions paths-filter), not content inspection. Implemented Fix C (declarative manifest), then /tp caught a gaming vector (2nd-order effect), fixed with anti-gaming verification.

## Read-first list

1. `C:/Users/brsth/.grok/hooks/scripts/verification_receipt_writer.py` lines 258-370 — the declarative manifest functions (`_read_declared_manifest`, `_resolve_declared_to_observed`, `_extract_script_references`)
2. `C:/Users/brsth/.grok/hooks/scripts/quality_gate/obligation_manager.py` line ~530 — `DECLARED_MANIFEST` added to approved `scope_basis` set
3. `C:/Users/brsth/.grok/hooks/scripts/verification_receipt_writer.py` lines 189-237 — `_VERIFIER_PATTERNS` (the pattern-based fallback when no manifest is present)

## Verified facts

- [FACT] The declarative manifest works: scripts with `# VERIFIER_CAPABILITY: syntax` and `# VERIFIES: file1.py, file2.py` headers get `scope_basis: DECLARED_MANIFEST` with the correct capability. Tested: 5/5 functional tests pass (commit `7a9abf9`).
- [FACT] The anti-gaming check works: scripts that declare VERIFIES but don't reference the files in actual code (outside comments) are rejected. Tested: 4/4 anti-gaming tests pass (commit `0f72c61`).
- [FACT] `DECLARED_MANIFEST` is in the obligation manager's approved scope_basis set (commit on obligation_manager.py).
- [INFERENCE] The comment-stripping regex (`re.sub(r"^\s*#.*$", "", ...)`) handles full-line comments but not inline comments (`x = 1 # scan_transcript.py`). This is R2 (LOW severity) — deliberate construction required to exploit.

## Current state

**Done:**
- `_read_declared_manifest()` — reads `# VERIFIER_CAPABILITY:` and `# VERIFIES:` from script's first 2000 chars
- Anti-gaming: strips comments, checks declared files appear in code via imports, open(), or path references
- `_resolve_declared_to_observed()` — matches declared filenames to observed modified paths
- `_extract_script_references()` — extracts import + open() references for the anti-gaming check
- `DECLARED_MANIFEST` in obligation manager approved set
- Manifest headers added to existing test scripts (`verify_syntax.py`, `test_improvements.py`)

**Not done (residual risks from /risk scan):**
- R1: variable-name bypass — naming a variable `scan_transcript` satisfies the reference check without importing
- R2: inline-comment bypass — `re.sub` strips full-line comments but not inline comments
- R6: the AGENTS.md 2nd-order-effects checklist is prose (needs a hook to be structural)

## Task packets

### VRM-01: Tighten anti-gaming against variable-name bypass (R1)
- **goal:** Prevent the anti-gaming check from being satisfied by variable names that match declared files without actual imports
- **in scope:** `_read_declared_manifest` or `_extract_script_references` — require that declared files appear in `import` or `from...import` statements specifically, not just anywhere in code
- **out of scope:** R2 (inline comments) — LOW severity, separate fix
- **files:** `C:/Users/brsth/.grok/hooks/scripts/verification_receipt_writer.py`
- **acceptance:** a script with `scan_transcript = "fake"` (no import) is rejected; a script with `import scan_transcript` is accepted
- **falsifier:** legitimate verification scripts that reference files only via subprocess or string paths get rejected (false positive)
- **verification level:** RUNTIME
- **note:** LOW priority — R1 requires deliberate construction and the current check already catches the most common gaming vector (comment-only declarations)

### VRM-02: Make 2nd-order-effects checklist a hook (R6)
- **goal:** Convert the AGENTS.md 5-question checklist from prose (50% compliance ceiling) to a Stop hook that fires when enforcement/gate/hook changes are detected
- **in scope:** new Stop hook that detects changes to `hooks/`, `quality_gate/`, or enforcement-related files and requires the 5 questions to be answered in the response
- **out of scope:** the checklist content itself (already in AGENTS.md)
- **files:** new `C:/Users/brsth/.grok/hooks/Stop_second_order_effects_gate.py`
- **acceptance:** hook fires when verification_receipt_writer.py or obligation_manager.py is modified; blocks if the 5 questions are not answered in the response
- **falsifier:** the hook fires on every code change (too broad) or never fires (too narrow)
- **verification level:** RUNTIME

## Open decisions

- **VRM-01 priority:** is R1 worth fixing now, or is the current anti-gaming floor sufficient? The most common gaming (comment-only) is caught. Variable-name gaming requires deliberate construction. **Status: operator's call — recommend deferring unless gaming is observed.**

## Hard constraints

- The anti-gaming check must not reject legitimate verification scripts (false-positive cost is higher than false-negative — it blocks real work)
- The manifest pattern must stay backwards-compatible (scripts without manifest headers fall through to pattern-based detection)

## Cross-reference couplings

- The fleet-hygiene handoff (FLEET-01) covers the scanner path-coverage bug that produces ~50 false-positive spec-drift findings — related but independent
- The error-prevention handoff (ERR-PREVENT-01) covers the gate-log audit — related because both investigate whether existing gates fire correctly

## Explicit non-goals

- Fixing R2 (inline-comment bypass) — LOW severity, requires deliberate construction, not worth the complexity
- Replacing the pattern-based detection entirely — the manifest is an enhancement layer, not a replacement

## Resumption protocol

1. Read this handoff + the read-first files
2. VRM-01 is LOW priority — only fix if gaming is observed in production
3. VRM-02 (R6 hook) is the higher-value item — it makes the 2nd-order-effects discipline structural instead of prose

## Suggested next invocation

`/handoff claim P:/docs/handoffs/verification-receipt-declarative-manifest-20260810` then assess whether VRM-01 is worth fixing or deferring.

## Last user message (verbatim)

> /handoff

## Epistemic labels

- Declarative manifest functionality is `[FACT]` — tested via 5/5 functional tests
- Anti-gaming functionality is `[FACT]` — tested via 4/4 anti-gaming tests
- R1 (variable-name bypass) is `[FACT]` — verified by reading the check logic; a variable named `scan_transcript` satisfies `decl_stem in script_refs`
- R2 (inline-comment bypass) is `[INFERENCE]` — the comment-stripping regex `^\s*#.*$` matches full-line comments only; inline comments are not stripped. Not directly tested but inferred from regex semantics.
- R6 (checklist as hook) is `[INFERENCE]` — the 50% compliance ceiling for prose rules is documented in the wiki; making it a hook is the structural fix, but the hook itself is not yet built
