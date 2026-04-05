# ADR-20260322-gto-self-verifying: Self-Verifying GTO Skill Architecture

**Status:** Accepted
**Date:** 2026-03-22
**Context:** Design a self-verifying GTO skill that prevents false "done" states by enforcing completion criteria via hooks and binary assertions.

### Decision

Implement a 4-component self-verification system for GTO:
1. `gto-assertions.py` — Binary verification criteria (executable)
2. `gto-failure-capture.py` — PostToolUseFailure hook for failure classification
3. `gto-verify.sh` — Stop hook gate blocking incomplete runs
4. SKILL.md update — Embedded verification clause

### Rationale

GTO currently produces markdown artifacts but has no executable success criteria. The Stop hook gate pattern (exit 2 = block/continue) is the correct mechanism to prevent Claude from claiming completion before verification passes. This aligns with constitutional principles: fail-fast, evidence-first, no graceful degradation.

### Alternatives Considered

| Option | Description | Pros | Cons | Why Rejected |
|--------|-------------|------|------|--------------|
| **Chosen** | Hook-based verification + assertions script | Deterministic, composable, local-only | Requires 4 new files | Optimal — matches pattern doc |
| Markdown-only | Keep current markdown output | No new files | Not self-verifying, no enforcement | Fails constitutional verification principle |
| LLM-based verification | Call LLM to verify output | Handles complexity | External API in hook (violates constraint), latency | Hook constraint prohibits external calls |

### Tradeoffs

| Quality | Improved | Degraded |
|---------|----------|----------|
| Reliability | Verification prevents false done | Assertion maintenance burden |
| Maintainability | Clear success criteria | Regex fragility if format changes |
| Operational Excellence | Stop hook enforces completion | Exit 2 behavior needs user docs |

### Multi-Terminal Safety

- **Safe** — Each terminal writes to `.evidence/gto-{terminal_id}/`
- No shared mutable state between terminals
- Circuit breaker already prevents infinite loops (MAX_CHAIN_DEPTH=50)

### Implementation

**Phase 1: Binary Assertions (highest priority)**
- File: `P:/.claude/evals/gto-assertions.py`
- 5 assertions: artifact existence, health ≥80%, no critical gaps, git context valid, no circuit breaker trips
- Runs via `python3 .claude/evals/gto-assertions.py --terminal $TERMINAL_ID`
- Exit 0 = pass, Exit 1 = fail

**Phase 2: Failure Classification Hook**
- File: `P:/.claude/hooks/gto-failure-capture.py`
- PostToolUseFailure hook classifying gto-related failures
- Categories: subagent-timeout, handoff-chain-break, terminal-isolation-violation, import-error
- Writes to `.claude/failure-patterns/gto-*.json`

**Phase 3: Stop Hook Gate**
- File: `P:/.claude/hooks/gto-verify.sh`
- Stop hook invoking assertions
- Exit 0 = pass (allow stop), Exit 2 = block (continue session)
- Registered via settings.json

**Phase 4: SKILL.md Update**
- Add verification clause to Steps section
- Mandate running assertions before claiming completion
- Reference failure-patterns for remediation

**Testing approach:**
1. Run `/gto` — verify artifacts created
2. Delete one artifact — verify assertion fails
3. Run `/gto` again — verify session continues (not blocked)

**Rollback:** Remove hook registrations from settings.json, delete 3 new files.

### Consequences

- **Positive:** Claude cannot claim "done" without passing assertions; failure patterns enable faster debugging
- **Negative:** Maintenance burden for assertion regex; Exit 2 behavior may confuse users initially
