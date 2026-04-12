# Phase 1 Findings — claim_patterns.py behavioral assertion enforcement

## Triage Classification
code — Python module implementing claim detection patterns for hook enforcement

## Dispatched Specialists
- adversarial-logic: analyzed claim_patterns.py for logic errors in pattern design
- adversarial-quality: found no significant issues
- adversarial-testing: analyzed claim_patterns.py test coverage gaps
- adversarial-io-validation: analyzed related hook files for I/O validation issues

## Specialist Findings Summary

### adversarial-logic
**Domain:** Pattern logic, regex correctness, categorical consistency
**Key findings:**
- LOGIC-002 [HIGH] (source: adversarial-logic): Severity format inconsistency in agent spec (uppercase vs lowercase enum)
- LOGIC-004 [MEDIUM] (source: adversarial-logic): Redundant example entries in agent spec
- LOGIC-005 [LOW] (source: adversarial-logic): Cross-platform path detection ambiguity in agent spec
- Note: LOGIC-001 is about the agent specification itself, not claim_patterns.py

### adversarial-quality
**Domain:** Tech debt, maintainability, code structure
**Key findings:**
- No significant issues found in claim_patterns.py

### adversarial-testing
**Domain:** Test coverage, missing scenarios, test quality
**Key findings:**
- TEST-001 [HIGH] (source: adversarial-testing): VERIFICATION_LANGUAGE_PATTERNS has line-start anchor bug causing false positives
- TEST-002 [MEDIUM] (source: adversarial-testing): DOCUMENT_CLAIM_PATTERNS missing plural forms
- TEST-003 [MEDIUM] (source: adversarial-testing): ACTION_CLAIM_PATTERNS passive voice gap allows bypass
- TEST-004 [LOW] (source: adversarial-testing): has_action_claim() conflates fabrication vs behavioral assertion types
- TEST-005 [LOW] (source: adversarial-testing): Behavioral test cases have overlap risk on grammatical variants

### adversarial-io-validation
**Domain:** Path validation, file operations, external calls
**Key findings:**
- IO-001 [HIGH] (source: adversarial-io-validation): PreCompact.py float() conversion crash on non-numeric env var
- IO-002 [MEDIUM] (source: adversarial-io-validation): Bash tool file extraction incomplete in investigation gate
- IO-003 [MEDIUM] (source: adversarial-io-validation): _csf_src.exists() check insufficient for sys.path insertion
- IO-004 [HIGH] (source: adversarial-io-validation): input_data None guard missing in investigation gate
- IO-005 [LOW] (source: adversarial-io-validation): Path extraction uses implicit falsy check

## Consolidated Findings

### Logical Gaps & Inconsistencies
1.1. [HIGH] (source: adversarial-testing) — VERIFICATION_LANGUAGE_PATTERNS `^i` line-start anchor at claim_patterns.py:250 causes mid-paragraph verification statements to not be detected as verification language, producing false positive behavioral assertion blocks. Fix: change `^i` to `\bi` for word-boundary match.

### Hidden Assumptions & Fragile Dependencies
2.1. [MEDIUM] (source: adversarial-testing) — DOCUMENT_CLAIM_PATTERNS only handles singular forms of document/file references, missing "documents", "files", "PDFs", "docs"
2.2. [MEDIUM] (source: adversarial-io-validation) — _csf_src.exists() check at PreToolUse_investigation_gate.py:103 doesn't verify is_dir(), allowing non-directory paths into sys.path
2.3. [LOW] (source: adversarial-testing) — has_action_claim() returns True for both fabrication claims and behavioral assertions, preventing differentiated enforcement handling
2.4. [LOW] (source: adversarial-io-validation) — Path extraction uses implicit falsy check rather than explicit None/type validation

### Missing Obvious Actions / Best Practices
3.1. [MEDIUM] (source: adversarial-testing) — ACTION_CLAIM_PATTERNS lacks passive voice detection; "pytest was run" bypasses fabrication detection
3.2. [HIGH] (source: adversarial-io-validation) — PreCompact.py:25 float() conversion of PRECOMPACT_HOOK_TIMEOUT has no error handling for non-numeric values
3.3. [HIGH] (source: adversarial-io-validation) — PreToolUse_investigation_gate.py:96-103 input_data is assumed non-None but load_state() can return None, causing AttributeError on .get() calls

### Risks and Edge Cases
4.1. [LOW] (source: adversarial-testing) — VERIFICATION_LANGUAGE patterns only cover subject-verb order ("the system was verified"), missing object-first constructions ("verified the system")
4.2. [LOW] (source: adversarial-logic) — Cross-platform path detection in agent spec uses literal Windows path pattern that may not match Unix paths

### Concrete Recommendations
5.1. [HIGH] (source: adversarial-testing) — Change `r"(?i)^i\s+(?:have\s+)?"` to `r"(?i)\bi\s+(?:have\s+)?"` in VERIFICATION_LANGUAGE_PATTERNS first pattern at claim_patterns.py:250
5.2. [MEDIUM] (source: adversarial-testing) — Add passive voice pattern `r"(?i)(?:pytest|tests?)\s+(?:was|were)\s+(?:ran|executed|run)"` to ACTION_CLAIM_PATTERNS
5.3. [MEDIUM] (source: adversarial-testing) — Add plural forms to DOCUMENT_CLAIM_PATTERNS: `(?:documents?|files?|PDFs?|docs?)`
5.4. [HIGH] (source: adversarial-io-validation) — Wrap float() conversion in PreCompact.py with try/except ValueError
5.5. [HIGH] (source: adversarial-io-validation) — Add `if input_data is None: return False` guard in PreToolUse_investigation_gate.py

### Open Questions / Unknowns
6.1. [LOW] (source: adversarial-io-validation) — Whether ASK_ROUTING_DECIDED env var is set by Claude Code harness or another component (PreToolUse_ask_first_tool_gate.py)
6.2. [LOW] (source: adversarial-testing) — Whether TEST-004 (conflated claim types) warrants separate public functions or is acceptable as-is
