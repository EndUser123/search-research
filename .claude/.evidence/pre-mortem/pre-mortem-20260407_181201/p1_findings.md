# Phase 1 Findings: cognitive_guardrails.py

## Triage Classification
**hook** — UserPromptSubmit hook module implementing cognitive guardrails via regex detection and context injection

## Dispatched Specialists
- **adversarial-security**: Regex ReDoS risk, env var handling, input validation
- **adversarial-compliance**: Hook registration, exit codes, FRAMEGUARD pattern
- **adversarial-logic**: Detection pattern logic, boolean conversions, edge cases

## Specialist Findings Summary

### adversarial-security
**Domain:** Security vulnerabilities, ReDoS attacks, input validation
**Key findings:**
- [MEDIUM] ReDoS risk with .{0,100}? quantifier (cognitive_guardrails.py:31)
- [LOW] Env var parsing only accepts 'true' string (cognitive_guardrails.py:25)
- [INFO] No input length validation (cognitive_guardrails.py:69)

### adversarial-compliance
**Domain:** Hook registration compliance, exit codes, pattern adherence
**Key findings:**
- No significant issues found - hook registration compliant, exit handling correct

### adversarial-logic
**Domain:** Pure logic errors, off-by-one, conditionals
**Key findings:**
- [LOW] str(None) converts to 'None' not '' (cognitive_guardrails.py:69) - no false positive impact
- [LOW] HookResult.is_empty() treats {} as falsy (base.py:41-43) - not a bug for this hook

## Consolidated Findings

### Logical Gaps & Inconsistencies
1.1. [LOW] (source: adversarial-logic) — str(None) = 'None' creates literal string instead of empty (cognitive_guardrails.py:69). Verified: No false positives because regex patterns don't match 'None'.

### Hidden Assumptions & Fragile Dependencies
2.1. [MEDIUM] (source: adversarial-security) — Assumes user input length is reasonable. No truncation before regex matching (cognitive_guardrails.py:69).

### Missing Obvious Actions / Best Practices
3.1. [MEDIUM] (source: adversarial-security) — Regex quantifier {0,100} larger than needed. Frameguard_classifier.py uses {0,200} but could be {0,50} for same coverage (cognitive_guardrails.py:31).
3.2. [LOW] (source: adversarial-security) — Env var parsing only accepts 'true'. Values like '1', 'yes', 'on' would disable unexpectedly (cognitive_guardrails.py:25).

### Risks and Edge Cases
4.1. [MEDIUM] (source: adversarial-security) — ReDoS attack via crafted input with alternating word boundaries within 100-char window (cognitive_guardrails.py:31).
4.2. [INFO] (source: adversarial-security) — Memory exhaustion from extremely large prompts (>10MB) with no length limit (cognitive_guardrails.py:69).

### Concrete Recommendations
5.1. [Reduce regex quantifier] (source: adversarial-security) — Change .{0,100}? to .{0,50}? in all DESIGN_INTENT_PATTERNS (cognitive_guardrails.py:29-38).
5.2. [Add input length limit] (source: adversarial-security) — Add MAX_QUERY_LENGTH = 10000 and truncate with warning log (cognitive_guardrails.py:69).
5.3. [Improve bool parsing] (source: adversarial-security) — Accept '1', 'yes', 'on' as truthy values or document exact 'true' requirement (cognitive_guardrails.py:25).
5.4. [Precompile regex] (source: adversarial-security) — Use re.compile() at module load for performance (cognitive_guardrails.py:29-38).

### Open Questions / Unknowns
6.1. [LOW] (source: adversarial-logic) — Is str(None)='None' behavior intentional? Works but inelegant.
6.2. [LOW] (source: adversarial-logic) — Should HookResult.is_empty() distinguish None vs empty dict?
