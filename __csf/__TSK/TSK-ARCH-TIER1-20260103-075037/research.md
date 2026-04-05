# Tier 1 Architecture Frameworks - Research

**TSK ID:** TSK-ARCH-TIER1-20260103-075037
**Created:** 2026-01-03T07:50:37Z

---

## Research: Industry-Standard Frameworks

### Tyree-Akerman ADR Template

**Source:** github.com/joelparkerhenderson/architecture-decision-record

**Key Sections:**
1. Title and Status
2. Context (background, problem statement)
3. Decision (the choice made)
4. Rationale (why this decision)
5. Consequences (positive, negative, risks)

**Standard Format:**
```markdown
# ADR-001: Use Event-Driven Architecture for User Notifications

## Status
Decided

## Context
We need a user notification system that can handle multiple channels (email, SMS, push)
and must be scalable to millions of users.

## Decision
Use event-driven architecture with a message broker (RabbitMQ) and event bus pattern.

## Rationale
- Decouples notification sending from business logic
- Allows adding new notification channels without modifying core code
- Proven pattern at scale (used by Uber, Netflix)

## Consequences

### Positive
- Easy to add new notification types
- Business logic doesn't depend on notification services
- Can retry failed notifications asynchronously

### Negative
- Adds infrastructure complexity (RabbitMQ cluster)
- Event ordering can be tricky
- Debugging is harder than synchronous calls

### Risks
- Message broker becomes single point of failure (mitigate: cluster)
- Event schema changes require coordination (mitigate: versioned events)
```

**Used By:** Google, Amazon, open-source projects

---

### IBIS (Issue-Based Information System)

**Source:** Dialog Mapping methodology, fasterthan20.com

**Purpose:** Capture complex reasoning, prevent re-litigation of settled questions

**Structure:**
- **Issue:** The main question being decided
- **Ideas:** Proposals for solving the issue
- **Arguments:** Pro (+) and Con (-) for each idea

**Example:**
```
Issue: Should we use REST or GraphQL for our API?

├─ Idea 1: REST
│  ├─ (+) Simpler, widely understood
│  ├─ (+) Easy caching with HTTP
│  └─ (-) Over-fetching / under-fetching
│
└─ Idea 2: GraphQL
   ├─ (+) Exact data per query
   ├─ (+) Single endpoint
   └─ (-) Steeper learning curve
```

**Benefits:**
- Traceable reasoning
- Prevents re-litigation of settled questions
- Captures why decisions were made

---

### Quality Attribute Utility Tree

**Source:** ATAM (Architecture Tradeoff Analysis Method), CMU SEI

**Purpose:** Hierarchically organize quality attributes driving decisions

**Structure:**
```
Quality Attributes
├─ Performance (0.9) - CRITICAL
│  ├─ Response time < 100ms
│  └─ Throughput > 1000 req/s
├─ Security (0.9) - CRITICAL
│  ├─ Authentication required
│  └─ Data encryption at rest
├─ Maintainability (0.8) - HIGH
│  ├─ Code clarity
│  └─ Modular design
└─ Scalability (0.7) - MEDIUM
   ├─ Horizontal scaling
   └─ Database sharding
```

**Benefits:**
- Explicit prioritization
- Trade-off analysis becomes quantitative
- Specialists understand what matters most

---

## Research: Existing Infrastructure

### enhancement_router.py Analysis

**Current Capabilities:**
- Multi-provider debate council (7+ models)
- Enhancement modes: debate, challenge, brainstorm, synthesize
- Provider health tracking with exponential backoff
- Cost-aware routing (free tier preference)

**Integration Points:**
```python
# Line ~34: AsyncMultiProviderDebateCouncil import
from src.commands.rca.async_optimal_debate_council import (
    AsyncMultiProviderDebateCouncil,
    DebateMode as CouncilDebateMode,
)

# Line ~49: EnhancementMode enum
class EnhancementMode(Enum):
    DEBATE = "debate"
    CHALLENGE = "challenge"
    BRAINSTORM = "brainstorm"
    SYNTHESIZE = "synthesize"
```

**New SPECIALIST_ROLES Needed:**
```python
"adr_documentation": {
    "primary": "meta-llama/llama-3.3-70b@groq",
    "framework": "Tyree-Akerman ADR Template",
    "role": "Generate standard decision records",
    "complexity_level": 1,  # All levels
}
```

---

## Research: LLM Provider Capabilities

### Groq (Free Tier)
- **Model:** Llama 3.3 70B
- **Strength:** Fast inference, suitable for templating
- **Use Case:** ADR formatting (not reasoning)
- **Cost:** Free
- **Reliability:** Generally good, occasional rate limits

### Anthropic Claude 3.5 Sonnet
- **Strength:** Complex reasoning, long context
- **Use Case:** Complexity detection, architecture analysis
- **Cost:** ~$0.003/1K tokens (input), ~$0.015/1K tokens (output)
- **Reliability:** Excellent

### Google Gemini 2.0 Flash
- **Strength:** Fast, security-focused
- **Use Case:** Risk analysis (if Tier 2)
- **Cost:** Competitive
- **Reliability:** Good

---

## Research: Windows Path Handling

**Issue:** Backslashes in Windows paths cause problems in bash/python

**Solution:** Always use forward slashes
```python
# BAD (backslashes)
path = "P:\__csf.nip\adr\file.md"

# GOOD (forward slashes)
path = "P:/__csf.nip/adr/file.md"

# BEST (pathlib)
from pathlib import Path
path = Path("P:/__csf.nip/adr/file.md")
# Use str(path) when passing to external tools
```

**For YAML/config files:** Always convert backslashes to forward slashes

---

## Research: Measurement Methodology

### Baseline Confidence Measurement

**Challenge:** How to measure "decision confidence"?

**Approach:** Define objective criteria:

| Criterion | Points | Max |
|-----------|--------|-----|
| Trade-offs documented | +20 | 20 |
| Risks explicitly categorized | +15 | 15 |
| ADR generated | +15 | 15 |
| Bias detection run | +10 | 10 |
| Multi-specialist agreement | +20 | 20 |
| Quality attributes prioritized | +20 | 20 |
| **TOTAL** | | **100** |

**Measurement Process:**
1. Run `/arch` decision WITHOUT Tier 1 frameworks
2. Score based on criteria above
3. Run `/arch` decision WITH Tier 1 frameworks
4. Score based on criteria above
5. Calculate improvement: `(tier1_score - baseline_score) / baseline_score`

**Target:** ≥ 20% improvement

---

## Research: Cost Estimation

### Tier 1 Cost Per Decision

| Component | Provider | Tokens (est) | Cost |
|-----------|----------|--------------|------|
| Complexity detection | Claude 3.5 | 1K input + 500 output | ~$0.01 |
| Quality tree extraction | Groq (free) | 500 + 500 | $0 |
| Debate council | Multiple | 5K total | ~$0.02 |
| ADR generation | Groq (free) | 1K + 1K | $0 |
| IBIS serialization | Local | 0 | $0 |
| **TOTAL** | | | **~$0.03** |

**Buffer:** Target ≤ $0.10 per decision (3x buffer)

---

## Research: Testing Strategy

### Unit Tests
- Complexity detector: 20 test prompts, expect >85% accuracy
- ADR formatter: Compare output to Tyree-Akerman examples
- IBIS serializer: Validate JSON schema
- Utility tree: Test extraction on known prompts

### Integration Tests
- Full pipeline: prompt → complexity → specialists → ADR
- Parallel execution: Verify timing (<5s overhead)
- Provider fallback: Simulate Groq outage

### Manual Validation
- 10 ADRs reviewed by human expert
- 5 complexity levels validated against expert judgment

---

## Sources Referenced

1. Tyree-Akerman ADR: github.com/joelparkerhenderson/architecture-decision-record
2. ATAM Framework: CMU SEI Technical Note
3. IBIS: Dialog Mapping, fasterthan20.com
4. enhancement_router.py: P:/__csf.nip/src/lib/enhancement_router.py
5. arch.md: P:/__csf.nip/src/commands/nip/arch.md

---

## Research Summary

**Key Findings:**
1. Tyree-Akerman ADR is industry standard (Google, Amazon use it)
2. IBIS is well-documented for dialogue capture
3. Quality utility trees are core to ATAM methodology
4. Existing infrastructure supports all required capabilities
5. Cost is well within budget ($0.03 per decision vs $0.10 target)

**Risks:**
1. Baseline confidence measurement is subjective (need objective criteria)
2. Provider reliability unknown until tested
3. Windows path handling requires care

**Recommendation:** Proceed with Tier 1 implementation

---

**Status:** Research complete
