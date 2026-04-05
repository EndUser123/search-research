# Tier 1 Architecture Frameworks - Specification

**TSK ID:** TSK-ARCH-TIER1-20260103-075037
**Created:** 2026-01-03T07:50:37Z
**Status:** Active
**Version:** 1.0

---

## Executive Summary

Implement Tier 1 architectural decision frameworks for the `/arch` command to improve decision confidence through structured analysis, standardized documentation, and cognitive bias detection.

**Scope:** Tier 1 only (4 components, 20-24 hours)
**Approach:** Measure → Validate → Decide on Tier 2+

---

## Problem Statement

The current `/arch` command has:
- 60-70% decision confidence (single perspective, narrative reasoning)
- No cognitive bias detection (solo developers lack peer review)
- Hidden trade-offs (decisions are narrative, not quantified)
- Informal risk management
- No decision history (past reasoning lost)

**Desired State:**
- 80-90% decision confidence (20-30% improvement)
- Automatic bias detection
- Standardized ADR documentation
- Explicit quality attribute prioritization
- Traceable reasoning (IBIS format)

---

## Tier 1 Components

### 1. Complexity Detector (3-4 hours)
**File:** `P:/__csf.nip/src/lib/complexity_detector.py`

**Purpose:** Auto-detect required analysis depth (LEVEL 1-4)

**Responsibilities:**
- Detect complexity level from prompt patterns
- Extract quality attributes with weights
- Estimate execution duration
- Route to appropriate specialist set

**Interface:**
```python
class ComplexityDetector:
    def detect_level(self, prompt: str) -> ComplexityLevel
    def extract_quality_attributes(self, prompt: str) -> UtilityTree

@dataclass
class ComplexityLevel:
    level: int  # 1-4
    frameworks: List[str]
    estimated_duration: int  # seconds
    reason: str
```

**Success Criteria:**
- >85% accuracy on 20 test prompts
- All 4 levels correctly identified
- Quality attributes extracted with weights

---

### 2. ADR Formatter (6-8 hours)
**File:** `P:/__csf.nip/src/lib/adr_formatter.py`

**Purpose:** Generate Tyree-Akerman standard Architecture Decision Records

**Responsibilities:**
- Format decision results as ADR
- Save to git-ready markdown files
- Include all required sections (Status, Context, Decision, Rationale, Consequences)

**Template:**
```markdown
# ADR-{id}: {title}

## Status
Decided

## Context
{context}

Quality Attributes (Priority Order):
{quality_attributes}

## Decision
{chosen_architecture}

## Rationale
{debate_summary}

Confidence Score: {confidence}%

## Consequences

### Positive Outcomes
{benefits}

### Trade-offs & Constraints
{tradeoffs}

### Risks & Mitigations
{risks}
```

**Success Criteria:**
- ADRs match Tyree-Akerman standard
- Compatible with git version control
- Windows paths handled correctly
- Sequential ADR IDs

---

### 3. Quality Utility Tree (3-4 hours)
**File:** `P:/__csf.nip/src/lib/utility_tree_extractor.py`

**Purpose:** Extract and prioritize quality attributes driving the decision

**Responsibilities:**
- Pattern-based attribute extraction from prompt
- Weight calculation from signal keywords
- Hierarchical attribute organization
- Format for specialist prompt injection

**Quality Attributes:**
| Pattern | Attribute | Weight |
|---------|-----------|--------|
| solo dev / individual developer | maintainability | 1.0 |
| changing requirements / evolving | maintainability | 0.8 |
| scale / users / concurrent | scalability | 0.8 |
| performance / latency / throughput | performance | 0.9 |
| security / compliance | security | 0.9 |
| cost / budget | cost | 0.6 |
| available / uptime / reliability | availability | 0.8 |

**Success Criteria:**
- Correctly identifies attributes from test prompts
- Weights align with user intent
- Output format ready for specialist injection

---

### 4. IBIS Serializer (5-6 hours)
**File:** `P:/__csf.nip/src/lib/ibis_serializer.py`

**Purpose:** Capture structured reasoning (Issues → Ideas → Arguments)

**Responsibilities:**
- Serialize debate results to IBIS JSON structure
- Save for historical reference
- Enable retrieval for decision context

**Schema:**
```json
{
  "issue": "Should we use REST or event-driven?",
  "ideas": [
    {
      "id": "idea_1",
      "proposal": "REST API + async paths",
      "provider": "Architecture specialist",
      "arguments": [
        {"type": "pro", "text": "Simple, well-understood"},
        {"type": "con", "text": "Doesn't scale to high throughput"}
      ]
    }
  ],
  "timestamp": "2026-01-03T07:50:37Z",
  "decision_id": "ADR-001"
}
```

**Success Criteria:**
- Valid JSON output
- Debate results correctly structured
- Retrieval works for historical queries

---

## Integration Points

### enhancement_router.py Updates

```python
# Add to SPECIALIST_ROLES in enhancement_router.py
SPECIALIST_ROLES = {
    # ... existing roles ...

    # Tier 1 Framework Specialists
    "adr_documentation": {
        "primary": "meta-llama/llama-3.3-70b@groq",
        "framework": "Tyree-Akerman ADR Template",
        "role": "Generate standard decision records",
        "complexity_level": 1  # All levels
    },
}

# Add to route_enhanced()
async def route_enhanced(self, prompt: str, config: dict) -> dict:
    # Step 1: Detect complexity
    complexity = detect_complexity(prompt)
    quality_attrs = extract_quality_attributes(prompt)

    # Step 2: Select active specialists
    active_specialists = get_specialists_for_level(complexity.level, config)

    # Step 3: Execute in parallel
    results = await asyncio.gather(*[
        self._call_specialist(s, prompt, quality_attrs)
        for s in active_specialists
    ])

    # Step 4: Generate ADR if configured
    if config.get("include_adr"):
        adr_path = generate_adr(results, quality_attrs)

    return results
```

### arch.md Updates

Add new output sections:
1. Decision Matrix (if LEVEL 2+)
2. Risk Analysis (if LEVEL 2+)
3. Identified Biases (if detected)
4. Quality Attributes (always)
5. ADR Documentation (if generated)
6. Next Steps

---

## Out of Scope (Tier 2+)

These are NOT part of Tier 1:
- DCAR Decomposition (atomic decision breakdown)
- Decision Matrix with auto-scoring
- Risk Analyzer Enhancement (ATRAM severity)
- ATAM Scenarios (scenario-driven evaluation)
- Framework Consensus Analyzer
- Multi-Round Debate orchestration

---

## Success Criteria (Tier 1)

### Functional
- [ ] Complexity detector returns accurate levels (>85%)
- [ ] ADRs generated in Tyree-Akerman format
- [ ] Quality attributes extracted and weighted
- [ ] IBIS dialogue captured and retrievable
- [ ] All components run in parallel (<5s overhead)

### Operational
- [ ] Zero provider failures during 2-week testing
- [ ] Windows file paths handled correctly
- [ ] All unit tests passing (100%)
- [ ] Integration tests passing (100%)
- [ ] Speed within SLA (<30s for LEVEL 1, <180s for LEVEL 2)

### Business Value
- [ ] **Measured confidence improvement: 20%+**
- [ ] ADRs usable in actual git repo
- [ ] Cost per decision: <$0.10
- [ ] User feedback: Positive

---

## Decision Gate (Week 2)

Before proceeding to Tier 2, must validate:

1. **Confidence Improvement ≥ 20%?**
   - Measure baseline vs Tier 1 on 20 decisions
   - If < 20%: Debug and refine before proceeding

2. **Provider Reliability Proven?**
   - 99%+ success rate during testing
   - Fallback mechanisms tested

3. **Complexity Detector Accurate?**
   - >85% accuracy on diverse prompts
   - False positive rate acceptable

4. **ADR Quality Acceptable?**
   - Matches Tyree-Akerman standard
   - Ready for git repo

**If 3+ of 4 are YES → Proceed to Tier 2**
**If 2 or fewer are YES → Pause, refine, re-measure**

---

## References

- Original spec: `C:\Users\brsth\Downloads\arch-frameworks-implementation.md`
- Revised plan: `C:\Users\brsth\Downloads\arch-implementation-revised.md`
- Current /arch: `P:/__csf.nip/src/commands/nip/arch.md`
- Enhancement router: `P:/__csf.nip/src/lib/enhancement_router.py`
- ADF skill: `P:/.claude/skills/architecture-decision-framework/SKILL.md`

---

**Next Steps:**
1. Review specification with stakeholder
2. Establish baseline confidence measurement
3. Begin implementation with Complexity Detector
