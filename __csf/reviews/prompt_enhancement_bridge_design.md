# Prompt Enhancement Bridge - Design Review Package

**Date**: 2026-02-15
**Author**: Claude (Opus 4.6)
**Status**: Design Review - Pending Decision
**Related**: Competence Layer Part 2, Universal Clarification Pattern

---

## Executive Summary

Proposes a three-layer prompt enhancement architecture combining:
1. **Universal Clarification Hook** - Lightweight ambiguity detection
2. **Prompting Framework Integration** - Technique selection (Socratic, CoVe, Self-Refine)
3. **Competence Layer** - Task-type contracts (already implemented)

**Goal**: Reduce "I assumed X when you meant Y" errors while maintaining low overhead.

---

## Table of Contents

1. [Problem Statement](#problem-statement)
2. [Proposed Solution](#proposed-solution)
3. [Prompting Framework Analysis](#prompting-framework-analysis)
4. [Prompt Refiner Skill Analysis](#prompt-refiner-skill-analysis)
5. [Architecture Design](#architecture-design)
6. [Integration Strategy](#integration-strategy)
7. [Open Questions](#open-questions)
8. [Recommendations](#recommendations)

---

## Problem Statement

### Current Issue

From competence layer compliance logs, the most commonly missing fields are:
- `next_step_question` (36 occurrences)
- `recommendation` (26 occurrences)
- `sources` (18 occurrences)

**Root cause**: These missing fields indicate responses proceeded without sufficient clarification or context-gathering.

### User's Insight

> "Most missing: next_step_question, recommendation, sources, what does this mean?"
> "Since this seems universal, why not use it as a hook instead of per skill?"

The user recognized that `next_step_question` is a **universal conversation pattern**, not just a task-type-specific requirement.

### Gap Analysis

| Layer | Current State | Gap |
|-------|--------------|-----|
| Conversation quality | No universal clarification hook | Ambiguous prompts proceed unchecked |
| Output structure | Competence layer exists | Works but only for skill outputs |
| Prompt enhancement | /prompt_refiner exists | Not auto-triggered, requires manual invocation |

---

## Proposed Solution

### Three-Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: Universal Clarification (UserPromptSubmit hook)   │
│  - Detects ambiguity via lightweight heuristics              │
│  - Injects clarification questions when needed               │
│  - < 50ms overhead for simple prompts                        │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 2: Prompting Framework (complex/expert queries)      │
│  - Analyzes: domain, complexity, user_intent                 │
│  - Selects: Socratic, CoVe, Self-Refine, etc.                │
│  - Returns: Enhanced prompt with technique pattern           │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: Competence Layer (existing)                        │
│  - Task-type detection                                      │
│  - Contract template injection                              │
│  - Output validation at Stop hook                           │
└─────────────────────────────────────────────────────────────┘
```

### Key Design Principles

1. **Fail-open**: Enhancement errors never block the session
2. **Layered activation**: Simple prompts pass through; complex get full treatment
3. **Composable**: Each layer can work independently
4. **Observable**: Debug mode for understanding enhancement decisions

---

## Prompting Framework Analysis

### Location
`P:/packages/prompting-framework/`

### Capabilities

| Feature | Description |
|---------|-------------|
| **Technique Selection** | Chooses from 13 techniques based on context |
| **Context Models** | Domain, complexity, intent, evidence requirements |
| **Performance Optimization** | Caching, timeout guards, budget allocation |
| **Constitutional Compliance** | Evidence-based, anti-deception checks |

### Available Techniques

```
CHAIN_OF_THOUGHT       - Multi-step reasoning
TREE_OF_THOUGHTS       - Exploratory reasoning branches
REACT                  - Reasoning + Acting loops
SELF_CONSISTENCY       - Multiple sampling for consistency
FEW_SHOT              - Example-based prompting
ZERO_SHOT             - Direct instruction
STRUCTURED_PROMPTING  - Organized output format
COMPARATIVE_ANALYSIS  - Side-by-side evaluation
EVIDENCE_GATHERING    - Source collection
VERBALIZED_SAMPLING   - Explicit reasoning output
SELF_REFINE           - Iterative improvement
CHAIN_OF_VERIFICATION - Fact-checking pipeline
QUERY_FANOUT          - Parallel queries
SOCRATIC              - Systematic questioning (★ recommended)
```

### Integration Complexity

| Aspect | Assessment |
|--------|------------|
| **API surface** | Moderate - requires async handling in sync hook context |
| **Dependencies** | Framework is self-contained, no external deps |
| **Performance** | Needs timeout guard and graceful degradation |
| **Maintenance** | Framework is actively developed, follow updates |

### Critical Finding: Async Mismatch

The framework uses `async def` throughout:
```python
async def select_applicable_techniques(self, context: PromptingContext) -> list[TechniqueApplicability]
```

But Claude Code hooks run synchronously. We'd need:
```python
loop = asyncio.get_event_loop()
applicable = loop.run_until_complete(orchestrator.select_applicable_techniques(context))
```

**Risk**: Event loop conflicts if framework internally spawns async tasks.

---

## Prompt Refiner Skill Analysis

### Location
`P:/.claude/skills/prompt_refiner/`

### Purpose
Executable prompt specification system with constitutional compliance and cognitive techniques.

### Current Usage
Manual invocation via `/prompt_refiner analyze "your prompt here"`

### Key Features from SKILL.md

| Feature | Description |
|---------|-------------|
| **Triage Q1** | Reversibility → effort level (MIN-EFFORT to MAXIMUM-SAFETY) |
| **Triage Q2** | Dependencies → reasoning method (CoT, ToT, Multi-Agent) |
| **Triage Q3** | Evidence → confidence tier (95%, 75%, 50%) |
| **Tier system** | 1.0-2.0 quality levels with token-efficient triage |

### Comparison with Prompting Framework

| Aspect | /prompt_refiner | prompting-framework |
|--------|----------------|---------------------|
| **Invocation** | Manual skill | Auto via hook (proposed) |
| **Focus** | Prompt specification quality | Technique selection |
| **Cognitive load** | Higher (requires triage) | Lower (automatic) |
| **Integration** | Standalone skill | Package with Python API |
| **Best for** | Critical prompts, manual review | Every prompt, auto-enhancement |

### Potential Integration

**Option A**: Use /prompt_refiner as the heavy-lifting backend
- Hook does quick analysis
- If complexity ≥ expert, auto-invoke /prompt_refiner
- Returns optimized prompt pattern

**Option B**: Keep /prompt_refiner manual
- Hook handles 80% of cases (lightweight)
- User invokes /prompt_refiner for critical 20%
- Clear separation of concerns

**Recommendation**: Option B initially, can evolve to A if usage patterns justify.

---

## Architecture Design

### Hook Structure

```
.claude/hooks/
├── UserPromptSubmit_prompt_enhancement_bridge.py  # Standalone version
└── UserPromptSubmit/
    └── prompt_enhancement.py                       # Router module version
```

### Core Algorithm

```python
def enhance_prompt(prompt: str, cwd: str) -> str | None:
    # 1. Quick analysis (< 10ms)
    domain = detect_domain(prompt, cwd)
    complexity = assess_complexity(prompt)
    intent = detect_intent(prompt)
    needs_clarification = check_ambiguity(prompt)

    # 2. Route
    if complexity == "simple":
        return None  # Pass through

    if needs_clarification:
        return build_clarification_injection(prompt, domain)

    if complexity in ("complex", "expert"):
        return try_framework_enhancement(prompt, domain, complexity, intent)

    # Moderate
    return build_lightweight_guidance(domain, intent)
```

### Detection Patterns

**Domain detection**:
- Path hints: `/security/` → security domain
- Keywords: "vulnerability", "auth", "xss" → security
- Fallback: "general"

**Complexity assessment**:
- Word count + pattern matching
- Simple: ≤ 10 words or "what is X"
- Moderate: 10-30 words or "explain X"
- Complex: 30-60 words or "design/implement X"
- Expert: 60+ words or "framework/paradigm X"

**Ambiguity detection**:
- Unclear antecedents: "fix it", "check that" (without clear referent)
- Missing specifics: "implement this" (what?)
- Very brief: ≤ 3 words
- Ambiguous phrases: "make it better", "optimize", "clean up"

### Enhancement Levels

| Level | Trigger | Injection | Tokens |
|-------|---------|-----------|--------|
| **None** | Simple prompts | - | 0 |
| **Clarification** | Ambiguity detected | 1-3 targeted questions | ~100 |
| **Guidance** | Moderate complexity | Domain-specific response pattern | ~80 |
| **Framework** | Complex/expert | Technique-selected enhancement | ~200 |

---

## Integration Strategy

### Phase 1: Standalone Hook (Proof of Concept)

**File**: `UserPromptSubmit_prompt_enhancement_bridge.py`

**Registration**:
```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "python P:/.claude/hooks/UserPromptSubmit_prompt_enhancement_bridge.py",
            "timeout": 3
          }
        ]
      }
    ]
  }
}
```

**Pros**: Easy to test, can enable/disable via env var
**Cons**: Runs outside router, separate from other UserPromptSubmit modules

### Phase 2: Router Module (Integrated)

**File**: `UserPromptSubmit/prompt_enhancement.py`

**Registration**: Auto-registered via `registry.py`

**Pros**: Part of unified router, priority-based ordering
**Cons**: Requires router understanding

### Phase 3: Full Framework Integration

**Trigger**: When Phase 1/2 proves value and performance is acceptable

**Actions**:
- Enable prompting-framework technique selection
- Add performance monitoring
- Tune complexity thresholds

---

## Open Questions

### Technical

| Question | Options | Implications |
|----------|---------|--------------|
| **Async handling** | `run_until_complete` vs separate process | Event loop safety vs isolation |
| **Framework caching** | In-memory vs disk vs none | Performance vs stale data |
| **Fallback strategy** | Lightweight vs none vs aggressive | Reliability vs overhead |

### Product

| Question | Options | Implications |
|----------|---------|--------------|
| **Activation threshold** | MIN_COMPLEXITY=0.3 vs 0.5 vs 0.7 | More enhancements vs fewer |
| **Clarification mode** | Soft (inject) vs hard (block) | User experience vs safety |
| **Debug visibility** | Always visible vs opt-in vs hidden | Observability vs noise |

### Integration

| Question | Options | Implications |
|----------|---------|--------------|
| **Competence coordination** | Separate vs unified | Clean separation vs consistency |
| **/prompt_refiner role** | Auto-backend vs manual-only | Automation vs user control |
| **Metric collection** | Log all vs sampled vs none | Insights vs privacy |

---

## Recommendations

### Immediate (Ready to Decide)

1. **Start with Phase 1** (standalone hook)
   - Lowest risk, easy to iterate
   - Proves value before deeper integration

2. **Use soft clarification mode**
   - Inject questions, don't block
   - User can ignore if not relevant

3. **Set MIN_COMPLEXITY = 0.5**
   - Moderate+ complexity gets enhancement
   - Simple prompts pass through unchanged

### Short-term (After Validation)

1. **Add performance monitoring**
   - Track enhancement rate, overhead, timeout frequency
   - Use data to tune thresholds

2. **Integrate with competence layer**
   - Share domain/complexity analysis
   - Unified prompt context model

3. **Consider /prompt_refiner for expert mode**
   - Auto-invoke for complexity > 0.8
   - User can still invoke manually

### Long-term (Evolution)

1. **Learn from usage**
   - Which clarification patterns work best?
   - Which techniques are most valuable?

2. **Consider unified enhancement pipeline**
   - Single hook that coordinates all enhancement layers
   - Avoids multiple injections stacking

3. **Explore feedback loop**
   - Track if clarification questions improve outcomes
   - Adjust ambiguity detection based on results

---

## Alternatives Considered

### Alternative A: Just Add `next_step_question` to All Contracts

**Pros**: Simple, minimal changes
**Cons**: Doesn't address root cause (ambiguity), still reactive not proactive

### Alternative B: Use Only Prompting Framework

**Pros**: Comprehensive technique selection
**Cons**: Heavyweight for simple prompts, async complexity

### Alternative C: Manual /prompt_refiner Only

**Pros**: User control, no overhead
**Cons**: Requires user remember to invoke, no proactive help

### Selected: Layered Approach

Balances automation with simplicity, addresses ambiguity at source, provides graceful fallback.

---

## Appendix: Configuration Options

### Environment Variables

```bash
# Enable/disable enhancement
PROMPT_ENHANCEMENT_ENABLED=true

# Minimum complexity threshold (0.0-1.0)
PROMPT_ENHANCEMENT_MIN_COMPLEXITY=0.5

# Maximum tokens to add
PROMPT_ENHANCEMENT_MAX_TOKENS=500

# Timeout in milliseconds
PROMPT_ENHANCEMENT_TIMEOUT=2000

# Debug mode
PROMPT_ENHANCEMENT_DEBUG=false
```

### Registry Configuration (for router module)

```python
# In UserPromptSubmit/registry.py
HOOK_PRIORITY = {
    "prompt_enhancement": 8.0,  # Before most injectors, after gates
    # ...
}
```

---

## Document Metadata

- **Author**: Claude (Opus 4.6)
- **Created**: 2026-02-15
- **Status**: Design Review
- **Next Steps**: Await user decision on implementation approach
- **Related Documents**:
  - Competence Layer Implementation Plan
  - `/prompt_refiner` SKILL.md
  - `prompting-framework` README.md
