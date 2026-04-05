# Minimum Viable Architecture (MVA) Template

**Purpose**: Standard structure for architectural proposals. External LLMs MUST complete ALL sections before suggesting implementation. Mark incomplete sections as "NEEDS CLARIFICATION" and explain what's missing.

**Usage**: Attach this template when requesting architecture from external LLMs. Reject proposals that leave sections vague or incomplete.

---

## 1. Context Understanding

### Existing Systems
- **CKS** (Constitutional Knowledge System): `P:/src/knowledge/systems/cks/`
  - 492 memory entries, SQLite + FAISS vector search
  - Semantic retrieval of lessons, patterns, fixes
  - Accessed via `/cks` skill
- **CHS** (Chat History Search): `P:/src/knowledge/systems/chs/`
  - Semantic search over prior conversations
  - SQLite + embeddings
  - Answers "what did we do before" queries
- **Cognitive Hooks**: `P:/.claude/hooks/`
  - UserPromptSubmit: cognitive framework injection
  - Start: reasoning mode selection
  - Conflict arbiter: framework coexistence rules
  - Observability: JSONL logging
- **Skills**: `P:/.claude/skills/`
  - Workflow: /plan-workflow, /code, /arch
  - Knowledge: /research, /cks, /chs
  - 200+ skills total

### Constraints
- **Solo Development**: Single developer, Director + AI workforce model
- **Platform**: Windows 11, Python 3.12+, no Docker, no cloud services
- **Persistence**: File-based (JSONL, SQLite) only, no databases
- **Anti-Bloat Philosophy**: "One powerful engine + slim adapters"
- **Consolidation**: Prune duplicate mechanisms, don't accumulate frameworks
- **Testing**: TDD, pytest, >80% coverage required
- **Hooks**: Stateless by design (no session memory)
- **Planning**: Separate workflow skills (/plan-workflow), NOT a reasoning mode

### Architectural Patterns
- **Memory**: CKS/CHS provide persistent knowledge; hooks are stateless
- **Planning**: Workflow skills handle multi-step tasks; cognitive frameworks enhance thinking
- **Conflict Arbiter**: Enforces max 3 enhancers, token budgets, fast-mode gating
- **Observability**: JSONL logging of selections for metrics-driven tuning
- **Tag Emission**: [COG] for frameworks, [SEQ]/[MAS]/[2ST]/[GRAPH] for modes

### Common Pitfalls (DO NOT SUGGEST)
- ❌ "Add memory/case recall" → We have CKS/CHS
- ❌ "Planner reasoning mode" → We have /plan-workflow skill
- ❌ Multi-terminal coordination → Solo dev
- ❌ Cloud services → Platform constraint
- ❌ Complex infrastructure → Keep lean, stdlib-only

---

## 2. Proposed Solution

### Component: [Name]
**Purpose**: [What problem this solves, why it's needed]

**Dependencies**:
- [What existing systems this needs]
- [What new code this requires]

**Integration Points**:
- [Where this connects to existing code]
- [What hooks/config files change]
- [Data flows: input → processing → output]

---

## 3. Implementation

### Files That Change
[List exact file paths that will be modified or created]

### New Code Required
- [Estimate lines of code for each new module]
- [Key functions/classes with brief descriptions]

### Configuration Changes
- [Exact config files and keys to add/modify]
- [Default values and their rationale]

### Breaking Changes
- **YES/NO**: Will this break existing behavior?
- **What breaks**: [If YES, what specific features/flows break]
- **Migration path**: [How existing users/data transition]

---

## 4. Validation

### Test Strategy
[How we verify this works]

**Test Cases**:
1. [Test case 1]: Given [input], assert [output]
2. [Test case 2]: Given [input], assert [output]
3. [Edge case]: [boundary condition to test]

**Coverage Target**: [% coverage for new code, >80% required]

### Acceptance Criteria
- [Concrete pass/fail conditions: what MUST work for this to be "done"]
- [Observable behaviors: what user sees when this works]
- [Performance bounds: token limits, latency, etc.]

### Rollback Plan
- **Config-level kill switch**: [What setting disables this feature instantly]
- **Code rollback**: [How to revert code changes if needed]
- **Data migration**: [How to handle any persisted data if rolled back]
- **Clean-up**: [What to remove after 30-60 day trial if abandoned]

---

## 5. Observability

### Metrics to Collect
- [What we measure to validate this works]
- [How we measure: logs, counters, user feedback]

### Success Signals
- [What indicates this is working well]
- [Quantitative thresholds if applicable]

### Failure Signals
- [What indicates this should be rolled back]
- [Thresholds that trigger kill switch]

---

## 6. Risk Assessment

### What Could Break
- [Concrete failure modes: what goes wrong]
- [Impact: who/what is affected]

### False Positive Rate
- [How often this triggers inappropriately]
- [Consequence of false positives]

### False Negative Rate
- [How often this misses when needed]
- [Consequence of false negatives]

### Performance Impact
- [Token cost per invocation]
- [Latency added to workflow]
- [Resource usage: CPU, memory, disk]

### Integration Risks
- [What existing systems this could destabilize]
- [Mitigation: how we prevent destabilization]

---

## 7. Completeness Checklist

Before submitting this proposal, verify:

- ✅ References CKS/CHS correctly (not "add memory")
- ✅ Specifies exact files to change
- ✅ Includes concrete test cases
- ✅ Defines rollback procedure
- ✅ Quantifies thresholds (kill switch, trigger rates)
- ✅ Addresses token budget impact
- ✅ Respects platform constraints (no Docker/cloud)
- ✅ Aligns with anti-bloat philosophy

**If any item above is incomplete, mark section as "NEEDS CLARIFICATION" and explain what's missing before proposing implementation.**
