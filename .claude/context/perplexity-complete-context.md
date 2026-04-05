# Complete Architecture Context for Perplexity

**Purpose**: This single file contains everything Perplexity needs to provide complete, well-architected solutions for your system.

**Last Updated**: 2026-03-12

---

# INSTRUCTIONS FOR PERPLEXITY

## MANDATORY READING

1. **Read the System Context section below** - Assume everything in it is TRUE and COMPLETE
2. **Use the MVA Template structure** - Your response MUST follow this format
3. **Complete ALL sections** - Mark incomplete sections as "NEEDS CLARIFICATION"

## CRITICAL RULES

- **DO NOT** suggest anything that violates "Common Pitfalls" in System Context
- **DO NOT** suggest implementation until ALL MVA sections are complete
- **DO** reference existing systems (CKS, CHS, hooks, skills) correctly
- **If you violate these rules**: Your response will be rejected and you'll be asked to re-read System Context

## COMPLETENESS CHECKLIST

Before submitting your proposal, verify:
- ✅ References CKS/CHS correctly (not "add memory")
- ✅ Specifies exact files to change
- ✅ Includes concrete test cases
- ✅ Defines rollback procedure
- ✅ Quantifies thresholds (kill switch, trigger rates)
- ✅ Addresses token budget impact
- ✅ Respects platform constraints (no Docker/cloud)
- ✅ Aligns with anti-bloat philosophy

---

# SYSTEM CONTEXT

## Existing Systems

### Knowledge Systems

#### CKS (Constitutional Knowledge System)
- **Location**: `P:/src/knowledge/systems/cks/`
- **Purpose**: Persistent knowledge storage and retrieval
- **Technology**: SQLite database with FAISS vector search
- **Content**: 492 memory entries (lessons learned, patterns, fixes, constitutional rules)
- **Access**: `/cks` skill, used by `/research` and other skills
- **Key Features**:
  - Semantic search via embeddings
  - Stores structured memories (question → answer → pattern type)
  - Single source of truth for institutional knowledge

#### CHS (Chat History Search)
- **Location**: `P:/src/knowledge/systems/chs/`
- **Purpose**: Semantic search across conversation history
- **Technology**: SQLite with vector embeddings
- **Content**: Past chat transcripts indexed for retrieval
- **Access**: Semantic search for "what did we do about X?" queries
- **Key Features**:
  - Find past conversations by semantic similarity
  - Supports context-aware queries
  - Complements CKS with conversational episodes

### Cognitive Control Layer

#### Hooks
- **Location**: `P:/.claude/hooks/`
- **UserPromptSubmit Hook**: Injects cognitive frameworks based on intent/topic
- **Start Hook**: Selects reasoning modes (SEQ/MAS/2ST/Graph)
- **Conflict Arbiter**: Enforces rules about framework coexistence
- **Observability**: JSONL logging of selections with metrics

#### Current Enhancers (9 total)
1. Cynefin Framework
2. Hanlon's Razor
3. Devil's Advocate
4. Calibrated Confidence
5. Socratic Decomposition
6. Assumption Surfacing
7. Outcome Anchoring
8. Inversion Prompting
9. [Others - see `cognitive_enhancers_config.json`]

#### Reasoning Modes (4 total)
- Sequential (SEQ): Step-by-step reasoning
- Multi-Agent (MAS): Parallel agent coordination
- Two-Stage (2ST): Draft + refine approach
- Graph (GRAPH): Graph-of-Thoughts reasoning

### Workflow & Skills Layer

#### Planning Skills
- `/plan-workflow`: Build and verify implementation plans
- `/code`: AI-assisted feature development
- `/arch`: Architecture advisor with templates
- **Key Point**: Planning is a SEPARATE workflow, not a cognitive framework

#### Knowledge Skills
- `/research`: Web research with multiple providers
- `/cks`: Query Constitutional Knowledge System
- `/chs`: Search chat history
- `/all`: Unified intelligent search

#### Total Skills: 200+
- **Location**: `P:/.claude/skills/`
- **Categories**: Workflow, knowledge, testing, development, ops

---

## Constitutional Constraints

### Development Philosophy
- **Anti-Bloat**: "One powerful engine + slim adapters"
- **Consolidation**: Prune duplicate mechanisms, don't accumulate frameworks
- **Lean Systems**: Prefer strengthening existing systems over adding new ones

### Development Context
- **Solo Development**: Single developer, Director + AI workforce model
- **No Team Collaboration**: All commits are by solo developer
- **Code Review**: Self-reflection only

### Platform Constraints
- **OS**: Windows 11
- **Python**: 3.12+
- **Infrastructure**: No Docker, no cloud services, no background daemons
- **Persistence**: File-based only (JSONL, text files, SQLite)
- **Databases**: No external databases, SQLite allowed

### Testing Requirements
- **Methodology**: TDD (Test-Driven Development)
- **Framework**: pytest
- **Coverage**: >80% required for new code
- **Isolation**: Tests must be isolated and clean up after themselves

---

## Architectural Patterns

### Memory vs. Stateless Design
- **Hooks are stateless**: No session memory to manage
- **Memory lives in CKS/CHS**: Persistent knowledge is separate
- **Implication**: Don't suggest "add memory to hooks" - integrate with CKS/CHS instead

### Planning vs. Cognitive Enhancement
- **Planning = Workflow Skills**: `/plan-workflow`, `/code`, `/arch` handle multi-step tasks
- **Cognitive Frameworks = Mental Models**: Enhancers improve thinking quality
- **Implication**: Don't suggest "planner reasoning mode" - use existing workflow skills

### Conflict Arbiter Patterns
- **Max 3 Enhancers**: Prevents framework explosion
- **Token Budget Enforcement**: Keeps injections lean
- **Fast-Mode Gating**: Verbose frameworks suppressed in fast mode
- **Override Modes**: `#deep`, `#rca` allow exceptions to standard rules

### Observability Patterns
- **JSONL Logging**: All selections logged with timestamps
- **Metrics-Driven Tuning**: Use data to adjust defaults and arbiter rules
- **30-Day Kill Switch**: Trial features evaluated with rollback plan

---

## Common Pitfalls (DO NOT DO)

### ❌ "Add Memory/Case Recall"
**Reality**: We have CKS (492 entries) and CHS (chat search)
**Correct Approach**: "Integrate with existing CKS/CHS systems"

### ❌ "Add Planner Reasoning Mode"
**Reality**: We have `/plan-workflow`, `/code`, `/arch` skills for planning
**Correct Approach**: "Enhance existing workflow skills" or "add planning-specific patterns to cognitive enhancers"

### ❌ "Multi-Terminal/Team Features"
**Reality**: Solo development, no team collaboration
**Correct Approach**: Focus on individual productivity patterns

### ❌ "Cloud Services/Docker/Kubernetes"
**Reality**: Windows 11, Python 3.12+, file-based persistence only
**Correct Approach**: Use SQLite, JSONL, text files; no cloud dependencies

### ❌ "Add New Framework for X"
**Reality**: Anti-bloat philosophy - consolidate before expanding
**Correct Approach**: Check if existing enhancers cover 70%+ of use case; enhance them instead

---

# MVA TEMPLATE (YOUR RESPONSE MUST FOLLOW THIS)

## 1. Context Understanding

### Existing Systems Involved
- **Which systems this affects**: [CKS, CHS, hooks, skills, etc.]
- **How it integrates**: [Connection points to existing code]

### Constraints to Respect
- **Platform**: [Windows 11, Python 3.12+, file-based only]
- **Testing**: [TDD, pytest, >80% coverage]
- **Anti-bloat**: [Consolidate before expanding]

### Problem We're Solving
- **Gap**: [What's missing or broken]
- **Goal**: [What success looks like]

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
[List exact file paths with Windows paths like `P:\.claude\hooks\file.py`]

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

Before submitting this proposal, I verify:

- ✅ References CKS/CHS correctly (not "add memory")
- ✅ Specifies exact files to change (with Windows paths)
- ✅ Includes concrete test cases
- ✅ Defines rollback procedure
- ✅ Quantifies thresholds (kill switch, trigger rates)
- ✅ Addresses token budget impact
- ✅ Respects platform constraints (no Docker/cloud)
- ✅ Aligns with anti-bloat philosophy

**If any item above is incomplete, I mark the section as "NEEDS CLARIFICATION" and explain what's missing.**

---

# ADDITIONAL CONTEXT FILES (IF NEEDED)

For specific questions about cognitive frameworks, also reference:
- `P:\.claude\hooks\cognitive_enhancers_config.json` - Current cognitive framework configuration
- `P:\.claude\hooks\UserPromptSubmit_modules\cognitive_enhancers.py` - Current implementation
- `P:\.claude\hooks\conflict_arbiter.py` - Conflict resolution logic
- `P:\.claude\hooks\observability.py` - Logging and metrics

---

# USAGE EXAMPLE

## How to Query Perplexity

```
Read this file: P:\.claude\context\perplexity-complete-context.md

MY QUESTION:
I want to add a 5W1H cognitive enhancer for context gathering.
How should this integrate with existing Socratic Decomposition?
What files need to change?
How do we validate this works?

CONTEXT:
- Current cognitive frameworks: Cynefin, Socratic, Devil's Advocate
- Conflict arbiter enforces max 3 enhancers
- Hooks are stateless, CKS/CHS provide memory
- Target: diagnostic and design prompts that lack context

REQUIRED OUTPUT FORMAT:
Complete MVA template with all sections filled.
```

---

**Remember**: The goal is FEWER iterations with MORE complete specs. Enforce the template, mark incomplete sections, and provide concrete, implementable solutions.
