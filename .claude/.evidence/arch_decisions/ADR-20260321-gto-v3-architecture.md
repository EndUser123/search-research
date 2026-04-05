# ADR-20260321: GTO v3 Architecture

**Status:** Proposed
**Date:** 2026-03-21
**Context:** Gap/Task/Opportunity (GTO) skill redesign

---

## Context

### Problem Statement

The existing `/gto` skill (now `gto_old`) has documented gaps:
1. **No Recommended Next Steps generation** — Documented in SKILL.md but not implemented
2. **GapFinder lacks line numbers** — Detects errors but doesn't capture file paths or line numbers
3. **No learning opportunity detection** — Documented but not implemented
4. **No unfinished business tracking** — Open tasks, questions, deferred items not tracked
5. **No code marker scanning** — TODO/FIXME markers not detected
6. **No presence checking** — Test/docs/dependency files not validated

### Current State

- **gto_old/**: ~3,400 lines of Python
- Components: gto_orchestrator.py, health_scoring.py, lib/subagents.py, hooks/
- Architecture: Claude invokes Python script, which runs 3 subagents (GapFinder, GitContext, HealthCalculator)
- Artifacts written to .evidence/ (gap_finder_*.md, git_context_*.md, health_*.md)
- Output: Compact snapshot with health score, gap count, git status, artifact paths

---

## Decision

Implement **GTO v3** with full pipeline:

**Architecture: Three-layer separation**

1. **Python (Deterministic Layer)** — Do what code does best:
   - Data extraction (transcript parsing, file scanning)
   - Pattern matching (regex, deterministic rules)
   - JSON artifacts (structured, machine-readable)
   - State management (atomic writes, cross-session tracking)
   - Deterministic next steps (grouping, sorting, formatting)

2. **Agents/AI (Reasoning Layer)** — Do what AI does best:
   - Critical thinking (`/reflect` skill)
   - Adversarial validation (`adversarial-critic` agent)
   - Learning recommendations (`/learn` skill)

3. **Claude (Orchestrator Layer)** — Simple coordination:
   - Read SKILL.md
   - Invoke Python script
   - Invoke agents as needed
   - Format final output

### Key Principle

> **Push as much work into deterministic Python as useful. Use agents as much as is useful. Minimize duplication of effort. Each part provides max value that it is best suited for.**

---

## Alternatives Considered

### Alternative 1: Incremental Approach (Rejected)

**Proposal:** Implement in 3 phases over 4-7 days, starting with documented fixes only.

**Pros:**
- Lower risk
- Faster initial value
- Easier to test

**Cons:**
- Requires multiple rewrites of same components
- Delayed implementation of valuable features
- Higher total effort (context switching overhead)
- Doesn't address architectural gaps

**Rejection Rationale:** The full v3 architecture is coherent. Incremental would add complexity by requiring multiple refactors of the same components. Full implementation is more efficient.

### Alternative 2: Pure Python Implementation (Rejected)

**Proposal:** All reasoning logic in Python, no AI agents.

**Pros:**
- Faster execution (no agent invocation overhead)
- More predictable output

**Cons:**
- Loses AI reasoning benefits
- Requires coding complex logic that AI does naturally
- Can't leverage existing adversarial tools
- Reimplements `/reflect`, `/learn`, `adversarial-critic` capabilities

**Rejection Rationale:** Existing agents provide proven capabilities. Reimplementing them is wasteful and loses specialized adversarial analysis.

### Alternative 3: Pure AI/Prompt-Based Implementation (Rejected)

**Proposal:** All analysis via Claude prompts, minimal Python.

**Pros:**
- Fast to prototype
- Flexible for iterative refinement

**Cons:**
- Not deterministic (same transcript may produce different outputs)
- Expensive (token-intensive)
- Hard to test reliably
- Can't leverage efficient pattern matching

**Rejection Rationale:** Gap detection is fundamentally a pattern-matching problem. Python is better suited for deterministic, efficient scanning of transcripts and files.

---

## Consequences

### Positive

**Capability Gains:**
- Unfinished business tracking (open tasks, questions, deferred items)
- Code marker scanning (TODO, FIXME, HACK, etc.)
- Test/docs/dependency presence validation
- Line number extraction for errors
- Recommended Next Steps generation (fixes documented gap)
- Cross-session recurrence tracking
- Critical thinking via `/reflect`
- Adversarial validation via `adversarial-critic`
- Learning recommendations via `/learn`

**Architectural Benefits:**
- Clear separation: Python (deterministic) vs AI (reasoning)
- Leverages existing tools (`/reflect`, `/learn`, `adversarial-critic`)
- Multi-terminal safe via StateManager
- Atomic state writes prevent corruption
- JSON artifacts enable tool integration

**Quality Improvements:**
- Grounded findings (every gap references real artifacts)
- Confidence scoring on all findings
- Deduplication prevents redundant reporting
- Recurrence tracking highlights persistent issues

### Negative

**Complexity:**
- ~4,000+ new lines of code
- 3-4 week implementation timeline
- More moving parts to debug
- Higher maintenance burden

**Performance:**
- Agent invocation adds latency
- File scanning (CodeMarkerScanner) adds overhead
- Handoff chain traversal still expensive

**Risk:**
- Ambitious scope may lead to abandoned features
- Agent integration points need careful testing
- Multi-terminal safety requires thorough validation

---

## Implementation Plan

### Phase 1: Python Engine (Week 1-2)

**Starting point:** Copy `gto_old/` to `gto/` (fresh start)

**Components to add:**
1. **UnfinishedBusinessDetector** — Pattern matching for open tasks/questions
2. **CodeMarkerScanner** — File scanning for TODO/FIXME markers
3. **TestPresenceChecker** — Check for test files and test commands
4. **DocsPresenceChecker** — Check for README.md, CLAUDE.md
5. **DependencyChecker** — Check requirements.txt, lock files
6. **format_recommended_next_steps()** — Deterministic next steps generation
7. **StateManager** — Atomic state writes, multi-terminal safe
8. **ResultsBuilder** — Deduplication, enrichment, consolidation

**Components to enhance:**
- GapFinderSubagent — Add line number extraction regex
- HealthCalculatorSubagent — Integrate presence checkers

**New reference files:**
- `references/unfinished-patterns.md`
- `references/health-thresholds.md`
- `references/output-template.md`
- `references/critical-thinking-questions.md`

### Phase 2: Agent Integration (Week 2-3)

**Integration points:**
1. **CriticalThinkingEvaluator** → `/reflect` skill
   - Call `/reflect` with transcript context
   - Parse output for CT findings
   - Merge into results JSON

2. **GroundingValidator** → `adversarial-critic` agent
   - Call agent with refined_next_steps and deep_dives
   - Parse output for UNGROUNDED items
   - Filter or demote based on feedback

3. **LearningAdvisor** → `/learn` skill
   - Call `/learn` with learning opportunities
   - Suggest CLAUDE.md entries or prompts

### Phase 3: Testing & Refinement (Week 3-4)

**Test coverage:**
- Integration tests for each detector
- Multi-terminal safety tests
- Agent integration tests
- Performance benchmarks

**Documentation:**
- Update SKILL.md with new workflow
- Create ADR for this decision
- Update review bundle with new architecture

---

## Related Decisions

- **ADR-20260321**: Initial GTO v3 architecture proposal
- Previous GTO review bundle (`P:/__csf/.staging/review_bundle_gto_20260321.md`)

---

## Next Steps

1. ✅ Create this ADR to document the decision
2. **PLANNING:** Create detailed implementation plan with task breakdown
3. **PHASE 1:** Begin Python engine implementation
4. **PHASE 2:** Integrate agents
5. **PHASE 3:** Test and refine

---

**Sign-off:** Architecture decision captured. Ready for planning phase.
