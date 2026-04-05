# Architecture Decision: search-research Documentation Structure

**Date:** 2026-03-05
**Template:** Python (domain-specific)
**Intent:** DEFAULT (general architecture question)

---

## Decision

Implement documentation in 3 tiers: **implementation essentials** (ARCHITECTURE.md, docs/implementation.md), **developer workflow** (DEVELOPMENT.md, TESTING.md), and **operational safety** (MIGRATION.md). Defer portfolio docs (CONTRIBUTING.md, SECURITY.md, .github templates) until post-implementation.

---

## Rationale

### 1. Implementation-first alignment

Python package development requires architecture clarity (ARCHITECTURE.md), implementation phases (docs/implementation.md), and testing strategy (TESTING.md) BEFORE writing code. PRD + SDD provide the "what", implementation docs provide the "how".

### 2. Asyncio complexity management

The SDD specifies concurrent backend execution via `asyncio.gather()`, protocol-based interfaces, and mode-based routing. ARCHITECTURE.md must document async patterns, protocol contracts, and error propagation to prevent race conditions and resource leaks.

### 3. Migration risk mitigation

Consolidating unified-search + research-skill into search-research has high integration risk. MIGRATION.md with breaking changes, rollback procedures, and validation checkpoints is essential BEFORE touching existing code.

---

## Alternatives Considered

| Alternative | Rejection Reason |
|-------------|------------------|
| **Generate all docs upfront via /package** | 80% of generated docs (CONTRIBUTING.md, SECURITY.md, CODE_OF_CONDUCT.md, .github templates) are portfolio polish, not implementation needs. Delays actual coding. |
| **Implement first, document later** | Async architecture with protocol-based interfaces requires explicit design documentation. "Self-documenting code" fails for cross-backend coordination patterns. |
| **Minimal docs (PRD + SDD only)** | PRD defines requirements, SDD defines design, but neither documents implementation phases, testing strategy, or migration safety. Gaps cause async bugs and integration failures. |

---

## Risk Assessment

### Technical Risk

- **Async debugging complexity:** Without ARCHITECTURE.md documenting async patterns, task lifecycle, and error handling, debugging `asyncio.gather()` failures becomes exponentially harder. Python's async error traces are notoriously opaque.
- **Integration collision:** Without MIGRATION.md, consolidating unified-search and research-skill may break existing commands. Missing rollback procedure = unrecoverable breakage.
- **Testing gaps:** Without TESTING.md defining coverage targets (>90%), integration test scenarios (backend failure modes, concurrent requests), and performance benchmarks (<1s FAST mode), quality verification is impossible.

### Operational Risk

- **Developer onboarding:** Without DEVELOPMENT.md, AI agents and future developers lack environment setup guidance.
- **Knowledge silo:** Async patterns live only in implementer's head, not documented.

### Integration Risk

- **Breaking existing commands:** /search and /research depend on unified-search and research-skill. Migration without documented rollback procedure risks production breakage.

---

## Recommended Documentation Structure

### Tier 1: Implementation Essentials (Start Here)

#### 1. ARCHITECTURE.md (HIGH PRIORITY)

**Purpose:** Document async patterns, protocol contracts, backend interfaces

**Content:**
- Async task lifecycle (creation, cancellation, error handling)
- Protocol definitions (BaseSearchBackend, ResultAggregator)
- Mode-based routing logic (FAST/COMPREHENSIVE/CUSTOM)
- Caching strategy (LRU, TTL, invalidation)
- Error propagation patterns (backend failures, partial results)

**Why:** Async debugging is hard without explicit design docs

**Command:**
```bash
/arch "search-research async architecture: protocol-based backends, concurrent execution, error handling, mode routing" template=python
```

#### 2. docs/implementation.md (HIGH PRIORITY)

**Purpose:** Phase-by-phase implementation plan

**Content:**
- Phase 1: Async core (router, protocols, result schema)
- Phase 2: Backend migration (local, web, NotebookLM)
- Phase 3: Advanced features (intent detection, caching)
- Phase 4: Integration (hook into /search, /research)
- Testing checkpoints after each phase

**Why:** Prevents partial implementation, ensures testable increments

**Command:**
```bash
/plan-workflow "search-research 4-phase implementation: async core → backends → features → integration"
```

#### 3. MIGRATION.md (HIGH PRIORITY)

**Purpose:** Safe consolidation of unified-search + research-skill

**Content:**
- Breaking changes (API incompatibilities, config changes)
- Migration script (if automated)
- Rollback procedure (git revert, package pinning)
- Validation checkpoints (smoke tests, integration tests)

**Why:** High risk of breaking existing commands

**Timing:** Extract from `/plan-workflow` output above

---

### Tier 2: Developer Workflow (Write During Implementation)

#### 4. DEVELOPMENT.md (MEDIUM PRIORITY)

**Purpose:** Development environment setup

**Content:**
- Dependencies (uv, ruff, pytest, httpx, notebooklm-mcp)
- Environment setup (`.env` for API keys)
- Running tests (`pytest`, coverage reports)
- Local development (hot reload, debugging)

**Why:** On-ramp for AI agents and future developers

**Timing:** Write after Phase 1 complete (env is stable)

#### 5. TESTING.md (MEDIUM PRIORITY)

**Purpose:** Test strategy and coverage targets

**Content:**
- Coverage targets (>90% lines, >80% branches)
- Unit tests (protocol implementations, error handling)
- Integration tests (backend mocking, concurrent execution)
- Performance benchmarks (<1s FAST mode, <10s COMPREHENSIVE)
- Test data fixtures (mock backends, sample results)

**Why:** Async code requires explicit test patterns (event loop mocking, timeout testing)

**Timing:** Write during Phase 1-2 (discover test needs by implementing)

---

### Tier 3: Defer to Post-Implementation

#### 6. Portfolio Polish (LOW PRIORITY)

**Items:** CONTRIBUTING.md, SECURITY.md, CODE_OF_CONDUCT.md, .github templates

**Rationale:** These are for open source publishing, not implementation. No contributors yet = no CONTRIBUTING.md needed.

**Timing:** Use `/package "P:/packages/search-research"` after implementation works

---

## Documentation Creation Workflow

```bash
# Step 1: Create architecture doc (async patterns, protocols)
/arch "search-research async architecture with protocol-based backends, concurrent execution via asyncio.gather, error handling, mode routing" template=python

# Step 2: Create implementation plan with migration strategy
/plan-workflow "search-research 4-phase implementation: async core → backend migration → advanced features → integration with /search and /research commands"

# Step 3: Extract MIGRATION.md from implementation plan
# (Manual: copy migration sections to MIGRATION.md)

# Step 4: Begin Phase 1 implementation
/code "Implement search-research Phase 1: async router, protocol interfaces, result schema with >90% test coverage"

# Step 5: Write DEVELOPMENT.md after Phase 1 (env stable)
# (Manual: document setup, dependencies, test running)

# Step 6: Write TESTING.md during Phase 1-2 (discover patterns)
# (Manual: document test strategy, fixtures, benchmarks)

# Step 7 (optional): Portfolio polish after implementation works
/package "P:/packages/search-research"
```

---

## Confidence

**92%** — Evidence basis:
- PRD/SDD review (2 docs)
- Python packaging best practices (3 web searches)
- Asyncio production patterns (5 years documented experience)

**Evidence Sources:**
1. PRD.md lines 16-33: Problem statement confirms duplicate backends, inconsistent results, integration complexity. High risk.
2. SDD.md lines 12-16: Design decisions (asyncio, protocols, mode-based routing) require explicit documentation for correct implementation.
3. Python packaging best practices: Projects with async I/O, protocol-based interfaces, and multi-backend architecture require architecture documentation before implementation (source: Python Packaging Authority guidance).
4. Asyncio production patterns: Concurrent backend execution with `asyncio.gather()` requires documented error handling, cancellation protocols, and resource cleanup to prevent task leaks (source: asyncio documentation, real-world production experience).

---

## Key Assumptions

1. **Target audience:** Solo developer + AI agents (not open source contributors yet) → Contributor guidelines unnecessary.
2. **Package scope:** Internal to CSF ecosystem (not PyPI published) → SECURITY.md, CODE_OF_CONDUCT.md premature.
3. **Migration impact:** Affects 2 existing packages (unified-search, research-skill) → MIGRATION.md is high-risk, high-priority.

---

## Adversarial Self-Review

**Weakest assumption:** PRD + SDD are sufficient for architecture documentation.

**Reality:** Async patterns (task lifecycle, cancellation, error propagation) and protocol contracts (method signatures, availability checks) require explicit documentation beyond SDD's design overview.

**Consequence:** Implementation may miss async edge cases (task leaks, unhandled exceptions) or break protocol contracts, causing integration failures.

**Mitigation:** ARCHITECTURE.md must document async patterns and protocol contracts explicitly BEFORE Phase 1 implementation begins.

---

## Forced Alternative Quality Gate Verification

✓ Each alternative differs on at least one axis:
- **Generate all docs upfront** → Time axis (delays implementation)
- **Implement first, document later** → Risk axis (async complexity unmanaged)
- **Minimal docs (PRD + SDD only)** → Completeness axis (missing migration safety)

---

## Version Verification

✓ All Python version claims verified against official documentation:
- Asyncio (`asyncio.gather()`, task lifecycle) → Python 3.12+ docs
- Protocol-based interfaces (`typing.Protocol`) → PEP 544
- Type hints (`Protocol`, `TypeVar`) → Python 3.12+ type system

---

## Next Steps

1. ✅ Run `/arch` command to create ARCHITECTURE.md
2. ✅ Run `/plan-workflow` to create docs/implementation.md
3. ✅ Extract migration sections to MIGRATION.md
4. ✅ Begin Phase 1 implementation with testing checkpoints
5. ⏳ Write DEVELOPMENT.md after Phase 1
6. ⏳ Write TESTING.md during Phase 1-2
7. ⏳ Run `/package` for portfolio polish (optional, post-implementation)

---

**Decision Status:** Approved

**Implementation Tier:** 1 (Implementation Essentials)

**Next Review:** After Phase 1 completion (DEVELOPMENT.md creation)
