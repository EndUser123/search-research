# Code Review & Adversarial Analysis: Pattern Comparison

**Date**: 2026-03-16
**Purpose**: Analyze patterns across implementations that informed `/uci` (Unified Code Inspection)

---

## Executive Summary

| Implementation | Agents | Key Strength | Unique Feature |
|----------------|--------|--------------|----------------|
| **HAMY LABS** | 9 | 75% useful suggestions | Test execution + Simplification focus |
| **/uci** | 3-11+ | Unified inspection | Mode-based operation + Consolidated |
| **Audit Code** | 5+ | Two-pass workflow | Tie-breaker lead |
| **Production Readiness** | 6+ | Meta-skill orchestration | Readiness tiers (L1/L2/L3) |

**Note**: `/review` and `/adversarial-review` were consolidated into `/uci` with mode-based operation. |

---

## 1. HAMY LABS: 9 Parallel Agents (Source of Innovation)

### Architecture
```
User → Main Agent → 9 Parallel Subagents → Synthesis → Verdict
```

### The 9 Agents

| Agent | Focus | Key Question |
|-------|-------|--------------|
| **Test Runner** | Execute tests | Do tests pass? What failed? |
| **Linter & Static Analysis** | Run linters, IDE diagnostics | Any warnings, type errors? |
| **Code Reviewer** | 5 concrete improvements | Impact vs Effort? |
| **Security Reviewer** | Injection, auth, secrets | Error handling leaks? |
| **Quality & Style** | Complexity, dead code | Follows conventions? |
| **Test Quality** | Coverage ROI | Behavior vs implementation? |
| **Performance** | N+1, blocking, memory | Hot paths optimized? |
| **Dependency & Deployment** | Migration safety | Observable? Rollback safe? |
| **Simplification** | "Could this be simpler?" | Cognitive load justified? |

### Key Innovations

#### Impact/Effort Matrix
```
[HIGH/MED/LOW Impact, HIGH/MED/LOW Effort]
```
- Helps prioritize what to fix first
- Low effort + high impact = quick wins
- High effort + low impact = skip

#### Three-Tier Verdict
- **Ready to Merge**: Tests pass, no critical/high
- **Needs Attention**: Medium issues worth addressing
- **Needs Work**: Critical/high or failing tests

#### Scope Detection Priority
1. User-specified scope (branch, commit, PR, files)
2. Feature branch → `git diff main...HEAD`
3. Main with staged → `git diff --staged`
4. Main, nothing staged → `git show HEAD`

#### Test Quality ROI Focus
- Not all code needs equal coverage
- Critical paths (auth, payments) = high coverage
- Low-risk code = diminishing returns awareness

---

## 2. Audit Code: Two-Pass Multidisciplinary

### Architecture
```
First Pass → 5 Perspectives → Tie-Breaker Lead → Prioritized Report
```

### Key Innovation: Tie-Breaker Lead
- Meta-reviewer that resolves conflicts
- Final decision authority
- Produces consolidated report

---

## 3. Production Readiness: Meta-Skill Orchestration

### Architecture
```
Meta-Skill → Delegates to Specialized Skills → Synthesis
```

### Key Innovation: Readiness Tiers
| Tier | Scope | Requirements |
|------|-------|--------------|
| **L1 (MVP)** | Health check, basic logging, unit tests | Minimum viable |
| **L2** | Structured logging, error handling, manual deploy | Standard |
| **L3** | Full observability, blue-green/canary | Production |

---

## 4. /uci: Unified Code Inspection (3-11+ Agents) ✅ IMPLEMENTED

### Architecture
```
Scope Detection → Intelligent Mode Detection → Parallel Agents → Aggregator → Verdict → Output
```

### Implementation Location
- **Skill**: `P:\.claude\skills\uci\SKILL.md`
- **Library**: `P:\.claude\skills\uci\lib\*.py`
- **Tests**: `P:\.claude\skills\uci\tests\test_*.py`

### Intelligent Mode Detection (NEW - March 16, 2026)
The system now automatically selects the appropriate mode based on context signals:

| Signal | Impact | Example |
|--------|--------|---------|
| **Risk indicators** | High | `src/auth.py` → deep mode |
| **File count** | Medium | 1-2 files → triage, 15+ → deep |
| **Line count** | Medium | <100 → triage, 2000+ → comprehensive |
| **File types** | Low | `.md` only → triage |
| **Change type** | Medium | bug fix → standard |

**Override Flags:**
- `--lite`: Force triage mode (3 agents)
- `--full`: Force comprehensive mode (11+ agents)

### Mode-Based Operation
| Mode | Agents | Duration | Use Case |
|------|--------|----------|----------|
| **triage** | 3 | 5-10 min | Small doc changes, 1-2 files, low risk |
| **standard** | 4 | 10-15 min | Typical code changes, 3-10 files |
| **deep** | 8 | 20-30 min | Security code, large changes, bug fixes |
| **comprehensive** | 11+ | 30-45 min | Auth/payments, 50+ files, infrastructure |

### Core Agents (triage mode)
- **logic** (`adversarial-logic`): Logical errors, edge cases, incorrect reasoning
- **tests** (`adversarial-testing`): Missing test scenarios, coverage gaps
- **security** (`adversarial-security`): Data leaks, access control, injection vectors

### Extended Agents (standard/deep modes)
- **performance** (`adversarial-performance`): N+1 patterns, bottlenecks, async issues
- **conventions**: Code style violations, pattern consistency
- **quality**: Maintainability risks, technical debt
- **compliance**: Spec/schema validation
- **qa** (`qa-engineer`): Test coverage gaps, missing scenarios

### Comprehensive Agents (comprehensive mode only)
- **simplification** (`code-simplifier`): Cognitive load, premature abstractions, change atomicity
- **rca** (`adversarial-rca`): Root cause analysis with multi-agent reasoning
- **failure-modes** (`adversarial-failure-modes`): Domain-aware anti-patterns with web research
- **deployment-safety**: Migration concerns, observability, rollback safety
- **python-modernization** (`python-simplifier`): Python 3.12+ idioms, type hints, modern patterns
- **test-quality-roi**: ROI-focused coverage analysis

### Key Innovations (All Implemented ✅)

#### Intelligent Mode Detection (NEW - March 16, 2026)
- Auto-selects mode based on context signals (file count, risk, lines, file types, change type)
- Risk-aware: auth/security/payment files trigger deeper review
- Override flags: `--lite` forces triage, `--full` forces comprehensive
- Users no longer need to remember explicit mode flags

#### Mode-Based Flexibility
- Four modes: triage/standard/deep/comprehensive with 3-11+ agents per mode
- Backward compatibility removed (old skills deleted, use `/uci` directly)

#### Constitutional Filter ✅
- Module: `constitutional_filter.py`
- Filters out team collaboration patterns (PR review workflows, etc.)
- Solo-dev compliance enforced
- Returns: (approved_findings, violations)

#### Consensus Detection ✅
- Module: `cross_agent_validation.py`
- Groups findings by file:line location (LocationKey)
- Counts agreement level
- Multiple agents confirming same location = higher priority

#### Impact/Effort Matrix ✅
- Module: `impact_effort.py`
- **Impact**: HIGH (crashes, data loss) / MED (degraded UX) / LOW (style)
- **Effort**: HIGH (days) / MED (hours) / LOW (minutes)
- Sorts findings by priority

#### Three-Tier Verdict ✅
- Module: `verdict.py`
- **Ready to Merge**: No blockers/high, tests pass
- **Needs Attention**: Medium issues worth addressing
- **Needs Work**: Blockers/high or failing tests

#### Scope Detection Priority ✅
- Module: `scope_detector.py`
1. User-specified scope
2. Feature branch → `git diff main...HEAD`
3. Staged changes → `git diff --staged`
4. Latest commit → `git show HEAD`

#### Pre-Existing Issue Detection ✅
- Module: `pre_existing.py`
- Distinguishes between issues in your diff vs pre-existing problems
- Labels findings as "MUST FIX BEFORE MERGE" vs "PRE-EXISTING ISSUES"

### Multi-Terminal Concurrency Support ✅
- Module: `orchestrator.py`
- Per-terminal state isolation
- File locking for `api_responses_log.jsonl`
- 30-day log rotation with API key sanitization
- Safe concurrent access from multiple terminals

### LLM Provider Resilience ✅
- Module: `circuit_breaker.py`
- Health monitoring for each provider
- Automatic failover on failures
- Degraded mode handling when all providers unavailable

### Memory Integration (CKS Cross-Session Learning) ✅
- Module: `memory_integration.py`
- **Bidirectional CKS integration**:
  - **Context retrieval**: Queries CKS before review for similar findings, patterns, and corrections
  - **Finding storage**: Stores high-confidence findings (severity ≥ high, confidence ≥ 80%) for future sessions
- **MemoryContext**: Holds retrieved context (similar_findings, known_patterns, past_corrections)
- **Quality filtering**: Only stores findings with location evidence and high confidence
- **Graceful degradation**: Automatically disables if CKS unavailable

---

## Pattern Comparison Matrix

| Pattern | HAMY | Audit Code | Production Ready | /uci (unified) |
|---------|------|------------|------------------|---------------|
| Parallel execution | ✅ 9 agents | ✅ 5+ agents | ❌ Delegates | ✅ 3-11+ agents |
| Severity ranking | ✅ 3-tier | ✅ Prioritized | ✅ L1/L2/L3 | ✅ 3-tier verdict |
| Mode-based operation | ❌ | ❌ | ❌ | ✅ 4 modes |
| Token constraints | ❌ | ❌ | ❌ | ✅ Yes |
| Constitutional filter | ❌ | ❌ | ❌ | ✅ Yes |
| Consensus detection | ❌ | ❌ | ❌ | ✅ Yes |
| Test execution | ✅ Real | ❌ | ❌ | ❌ |
| Impact/Effort matrix | ✅ Yes | ❌ | ❌ | ✅ Yes |
| Simplification focus | ✅ Yes | ❌ | ❌ | ✅ Yes (comprehensive) |
| ROI-focused testing | ✅ Yes | ❌ | ❌ | ✅ Yes (comprehensive) |
| Deployment safety | ✅ Yes | ❌ | ✅ Delegates | ✅ Yes (comprehensive) |
| Observability checks | ✅ Yes | ❌ | ✅ Delegates | ✅ Yes (comprehensive) |
| Tie-breaker meta | ❌ | ✅ Yes | ❌ | ❌ |
| Meta-skill delegation | ❌ | ❌ | ✅ Yes | ❌ |
| CKS integration | ❌ | ❌ | ❌ | ✅ Yes |
| Memory Integration (CKS cross-session learning) | ❌ | ❌ | ❌ | ✅ Yes |
| Scope auto-detection | ✅ Yes | ❌ | ❌ | ✅ Yes |
| Pre-existing detection | ❌ | ❌ | ❌ | ✅ Yes |

---

## Recommendations

### High Priority ✅ ALL COMPLETED

#### 1. ✅ Impact/Effort Matrix (from HAMY) - IMPLEMENTED
- Module: `impact_effort.py`
- Calculates HIGH/MED/LOW impact and effort
- Sorts findings by priority
```markdown
### LOGIC-001: Null pointer dereference
- **Impact**: HIGH (runtime crash)
- **Effort**: LOW (add null check)
- **Location**: src/auth.py:45
```

#### 2. ✅ Scope Detection Priority (from HAMY) - IMPLEMENTED
- Module: `scope_detector.py`
- Priority: user-specified > feature branch > staged > latest commit
```python
def detect_scope(user_input, git_state):
    # Priority 1: User specified
    if user_input.scope:
        return user_input.scope
    # Priority 2: Feature branch
    if git_state.branch not in ["main", "master"]:
        return f"git diff main...HEAD"
    # Priority 3: Staged changes
    if git_state.has_staged:
        return "git diff --staged"
    # Priority 4: Latest commit
    return "git show HEAD"
```

#### 3. ✅ Three-Tier Verdict (from HAMY) - IMPLEMENTED
- Module: `verdict.py`
- Verdict levels: Ready to Merge / Needs Attention / Needs Work
```markdown
### Verdict: Needs Attention
- **Reason**: 1 high security issue, 2 medium performance concerns
- **Next**: Address security issue before merge
```

### Medium Priority ✅ ALL COMPLETED

#### 4. ✅ Simplification Agent (from HAMY) - IMPLEMENTED
- Agent: `simplification` (comprehensive mode)
- "Could this be simpler?" lens
- Check for premature abstractions
- Change atomicity review

#### 5. ✅ Deployment Safety Checks (from HAMY) - IMPLEMENTED
- Agent: `deployment-safety` (comprehensive mode)
- Migration concerns
- Observability (logs, metrics, alerts)

#### 6. ⏸️ Tie-Breaker Meta-Reviewer (from Audit Code) - DEFERRED
- Could be added as optional meta-reviewer
- Currently consensus detection provides similar functionality

### Lower Priority (Future Considerations)

#### 7. Consider Test/Linter Execution (from HAMY)
- Would require actual test framework integration
- Could add as optional mode flag

#### 8. Consider Meta-Skill Delegation (from Production Readiness)
- Could delegate to specialized skills for specific checks
- Current unified approach preferred for consistency

---

## Implementation Status (March 16, 2026)

### Completed Core Modules

The UCI implementation includes the following library modules in `P:\.claude\skills\uci\lib\`:

| Module | Purpose | Status |
|--------|---------|--------|
| `agent_registry.py` | MODE_AGENTS mapping, agent metadata | ✅ Implemented |
| `scope_detector.py` | Git scope detection with priority | ✅ Implemented |
| `intelligent_mode_detector.py` | Context-aware mode detection (NEW) | ✅ Implemented |
| `impact_effort.py` | Impact/Effort matrix calculation | ✅ Implemented |
| `verdict.py` | Three-tier verdict synthesis | ✅ Implemented |
| `formatter.py` | Multi-format output generation | ✅ Implemented |
| `assessment_mode.py` | Dry-run mode with 6-check validation | ✅ Implemented |
| `orchestrator.py` | Parallel agent orchestration | ✅ Implemented |
| `circuit_breaker.py` | LLM provider circuit breaker | ✅ Implemented |
| `constitutional_filter.py` | Solo-dev compliance filtering | ✅ Implemented |
| `cross_agent_validation.py` | Consensus detection by location | ✅ Implemented |
| `practicality_filter.py` | Finding practicality assessment | ✅ Implemented |
| `pre_existing.py` | Pre-existing issue detection | ✅ Implemented |
| `memory_integration.py` | CKS cross-session learning (MemoryContext, MemoryIntegration) | ✅ Implemented |

### Test Coverage

Comprehensive test suite created in `P:\.claude\skills\uci\tests\`:

| Test File | Coverage | Status |
|-----------|----------|--------|
| `test_compat.py` | Backward compatibility wrappers | ✅ 19 tests |
| `test_modes.py` | Agent mode integration | ✅ 18 tests |
| `test_core.py` | Core layer unit tests | ✅ 15 tests |
| `test_concurrency.py` | Multi-terminal concurrency | ✅ 12 tests |

### Implementation Notes

1. **Intelligent Mode Detection (NEW)**: Auto-selects mode based on context signals (file count, risk, lines, file types, change type)
2. **Override Flags**: `--lite` forces triage mode, `--full` forces comprehensive mode
3. **Constitutional Filter**: Solo-dev compliance enforced, filters team collaboration patterns
4. **Consensus Detection**: Groups findings by LocationKey (file:line), counts agreement
5. **Multi-terminal Isolation**: Per-terminal state directories, file locking for concurrent access
6. **Log Rotation**: 30-day retention for `api_responses_log.jsonl`, API key sanitization
7. **Circuit Breaker**: Health monitoring, automatic failover, degraded mode handling
8. **Memory Integration**: CKS cross-session learning — retrieves context before review, stores high-confidence findings after

---

## Action Items

### Immediate ✅ COMPLETED
1. ✅ Document comparison findings
2. ✅ Consolidate `/review` and `/adversarial-review` into `/uci`
3. ✅ Implement mode-based operation (triage/standard/deep/comprehensive)
4. ✅ Add Impact/Effort matrix
5. ✅ Add scope detection priority
6. ✅ Add three-tier verdict synthesis
7. ✅ Add pre-existing issue detection

### Short Term ✅ COMPLETED
1. ✅ Add Test Quality ROI focus (comprehensive mode)
2. ✅ Create Simplification agent specification
3. ✅ Add Deployment Safety checks
4. ✅ Integrate constitutional filter
5. ✅ Integrate consensus detection
6. ✅ Integrate Memory Integration for CKS cross-session learning

### Long Term (Future Considerations)
1. Consider Test/Linter execution integration
2. Explore Meta-skill delegation patterns
3. Build Tie-breaker meta-reviewer

---

## Migration Notes

**March 16, 2026**: `/review` and `/adversarial-review` have been consolidated into `/uci` (Unified Code Inspection). The old skills now delegate to `/uci` with appropriate mode flags for backward compatibility:

- `/review` → `/uci --mode=triage` (3 core agents)
- `/adversarial-review` → `/uci --mode=deep` (8 agents)

The old skill directories have been removed. Update any scripts or documentation to use `/uci` directly.

---

## References

- **HAMY LABS Blog**: https://hamy.xyz/blog/2026-02_code-reviews-claude-subagents
- **HAMY LABS Video**: https://www.youtube.com/watch?v=tGmMItyRaRM
- **/uci skill**: P:\.claude\skills\u\ci\SKILL.md
- **Session Notes**: P:\.claude\docs\adversarial-review-session-notes.md
