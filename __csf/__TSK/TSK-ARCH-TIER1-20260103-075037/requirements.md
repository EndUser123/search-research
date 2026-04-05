# Tier 1 Architecture Frameworks - Requirements Analysis

**TSK ID:** TSK-ARCH-TIER1-20260103-075037
**Created:** 2026-01-03T07:50:37Z

---

## Functional Requirements

### FR-1: Complexity Detection
The system MUST automatically detect the complexity level (1-4) from user prompt.

**Acceptance Criteria:**
- [ ] LEVEL 1 detected for prompts containing "should we X?", "versus", "which one"
- [ ] LEVEL 2 detected for prompts containing "design", "architecture", "API"
- [ ] LEVEL 3 detected for prompts containing "redesign", "system-wide"
- [ ] LEVEL 4 detected for prompts containing "choose between", "vs", "tournament"
- [ ] Detection accuracy > 85% on test dataset

### FR-2: Quality Attribute Extraction
The system MUST extract quality attributes from user prompt with weights.

**Acceptance Criteria:**
- [ ] Detects "solo dev" → maintainability with weight 1.0
- [ ] Detects "performance" → performance with weight 0.9
- [ ] Detects "security" → security with weight 0.9
- [ ] Detects "scale" → scalability with weight 0.8
- [ ] Attributes sorted by weight (descending)

### FR-3: ADR Generation
The system MUST generate Architecture Decision Records in Tyree-Akerman format.

**Acceptance Criteria:**
- [ ] ADR contains all required sections (Status, Context, Decision, Rationale, Consequences)
- [ ] ADR includes quality attributes in priority order
- [ ] ADR includes confidence score percentage
- [ ] ADR saved to `P:/__csf.nip/adr/` directory
- [ ] ADR filename follows pattern `ADR-XXXX-slugified-title.md`
- [ ] ADR IDs are sequential (ADR-0001, ADR-0002, ...)

### FR-4: IBIS Dialogue Capture
The system MUST serialize debate results to IBIS JSON format.

**Acceptance Criteria:**
- [ ] Issue (main question) extracted from prompt
- [ ] Ideas (proposals) grouped by recommendation
- [ ] Arguments (pro/con) extracted from debate
- [ ] JSON saved to `P:/__csf.nip/data/ibis/` directory
- [ ] Retrievable by decision ID or timestamp

### FR-5: Parallel Execution
The system MUST execute all framework specialists in parallel.

**Acceptance Criteria:**
- [ ] Total execution time ≤ longest specialist time (not sum)
- [ ] Overhead < 5 seconds for routing and aggregation
- [ ] Graceful degradation if specialist fails

---

## Non-Functional Requirements

### NFR-1: Performance
- [ ] LEVEL 1 analysis: < 30 seconds total
- [ ] LEVEL 2 analysis: < 180 seconds total
- [ ] Framework overhead: < 5 seconds

### NFR-2: Reliability
- [ ] Provider success rate: ≥ 99%
- [ ] Fallback mechanism tested
- [ ] Graceful degradation on failure

### NFR-3: Cost
- [ ] Cost per decision: ≤ $0.10 (Tier 1)
- [ ] Free tier preferred where possible (Groq for templating)

### NFR-4: Compatibility
- [ ] Windows 11 file paths handled correctly
- [ ] Forward slashes used in all paths
- [ ] Python 3.14+ compatible

### NFR-5: Testability
- [ ] Unit test coverage: ≥ 90%
- [ ] Integration tests for all components
- [ ] Mock providers for reliable testing

---

## Technical Requirements

### TR-1: Complexity Detector Module
```python
# File: P:/__csf.nip/src/lib/complexity_detector.py

class ComplexityDetector:
    LEVEL_SIGNALS = {
        1: ["should we", "use X?", "versus", "which one"],
        2: ["design", "architecture", "API", "layer"],
        3: ["complete redesign", "system-wide", "migration"],
        4: ["choose between", "vs", "compare", "tournament"]
    }

    QUALITY_PATTERNS = {
        "solo dev": ("maintainability", 1.0),
        "performance": ("performance", 0.9),
        "security": ("security", 0.9),
        "scale": ("scalability", 0.8),
        # ...
    }

    def detect_level(self, prompt: str) -> ComplexityLevel:
        pass

    def extract_quality_attributes(self, prompt: str) -> UtilityTree:
        pass
```

### TR-2: ADR Formatter Module
```python
# File: P:/__csf.nip/src/lib/adr_formatter.py

class ADRFormatter:
    TEMPLATE = """# ADR-{id}: {title}
## Status
{status}
## Context
{context}
...
"""

    def generate_from_analysis(self, analysis_result, quality_attributes,
                              debate_results, risk_analysis) -> str:
        pass

    def save_adr(self, adr_content: str, decision_title: str) -> str:
        pass
```

### TR-3: IBIS Serializer Module
```python
# File: P:/__csf.nip/src/lib/ibis_serializer.py

class IBISSerializer:
    def serialize_debate_to_ibis(self, debate_results) -> IBIS:
        pass

    def save_ibis(self, ibis: IBIS, decision_title: str) -> str:
        pass
```

### TR-4: Utility Tree Extractor
```python
# File: P:/__csf.nip/src/lib/utility_tree_extractor.py

class UtilityTreeBuilder:
    PATTERNS = {
        "solo dev|solo developer": ("maintainability", 1.0),
        # ...
    }

    def extract_from_prompt(self, prompt: str) -> UtilityTree:
        pass

    def format_for_specialists(self, tree: UtilityTree) -> str:
        pass
```

---

## Data Requirements

### DR-1: ADR Storage Location
- Directory: `P:/__csf.nip/adr/`
- Filename pattern: `ADR-XXXX-slugified-title.md`
- Index file: `P:/__csf.nip/adr/index.md`

### DR-2: IBIS Storage Location
- Directory: `P:/__csf.nip/data/ibis/`
- Filename pattern: `ibis-{decision_slug}-{timestamp}.json`
- Index by decision ID and timestamp

### DR-3: Configuration
- File: `P:/__csf.nip/src/config/arch-defaults.yaml`
- Contains: default levels, frameworks, providers, output preferences

---

## Constraints

### C-1: Timeline
- Tier 1 implementation: 2-4 weeks (20-24 hours)
- Decision gate at Week 2 determines Tier 2+

### C-2: Resources
- Solo developer (no team coordination)
- Existing infrastructure must be leveraged
- No budget for paid provider tiers (use free tiers)

### C-3: Constitutional
- No background autonomous execution
- User-initiated only (/arch command)
- Graceful degradation on provider failure
- File I/O only on user action

---

## Dependencies

### External Dependencies
- Groq (free tier): Llama 3.3 70B for ADR templating
- Anthropic Claude 3.5 Sonnet: Complexity detection, specialist
- OpenRouter: Fallback for GPT-4 if needed

### Internal Dependencies
- `src/lib/enhancement_router.py`: Must be updated
- `src/lib/llm_providers/`: Provider management
- `src/commands/nip/arch.md`: Command interface

---

## Success Metrics

### Primary Metric: Confidence Improvement
- Baseline: Current decision confidence (~60-70%)
- Target: Tier 1 delivers ≥ 20% improvement
- Measurement: Compare 20 decisions with/without Tier 1

### Secondary Metrics
- ADR generation rate: 100% of LEVEL 2+ decisions
- Provider success rate: ≥ 99%
- Cost per decision: ≤ $0.10
- User satisfaction: Positive feedback

---

## Open Questions

1. **Q1:** How to establish baseline confidence retroactively?
   - **A1:** Use prospective baseline instead (measure next 10 decisions)

2. **Q2:** What if confidence improvement is only 10-15%?
   - **A2:** Extend measurement to 40 decisions, then decide

3. **Q3:** Should Tier 1 include bias detection?
   - **A3:** Bias detection moved to Tier 2 (requires LLM, higher risk)

4. **Q4:** How to handle provider outages during development?
   - **A4:** Mock providers in unit tests, graceful degradation in prod

---

**Status:** Ready for implementation (pending approval)
