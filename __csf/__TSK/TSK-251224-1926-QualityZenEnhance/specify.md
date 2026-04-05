# Specification: Enhance /quality System with Updated zen* and llm* Capabilities

## Project Overview

**TSK-ID**: TSK-251224-1926-QualityZenEnhance
**Date**: 2024-12-24
**Status**: In Progress

## Objective

Enhance the `/quality` (qual-gate) system to fully leverage updated zen* and llm* capabilities, including 12 review categories, universal verification, actionable classification, cost optimization, and code compression.

## Current State Analysis

### Quality System (qual-gate)
- **8 Quality Gates**: structure, governance, architecture, security, apis_services, code_review (Gate 6), performance, final_check (Gate 8)
- **Gate 6 Configuration**:
  - Default mode: `chill` (quick review)
  - Default focus: `['design', 'clarity', 'reasoning']` (only 3 of 12 categories)
  - Hybrid config system: CLI > config file > env vars > defaults
  - ZenCodeReviewAdapter integration via `enhanced_execution.py`

### Available Zen/LLM Capabilities
- **12 Review Categories**: security, bugs, error_handling, configuration, performance, concurrency, code_quality, testing, api_design, type_safety, dependencies, documentation
- **3 Review Modes**: chill (2 cats), mid (5 cats), chad (12 cats)
- **47+ Models** across 7+ providers with cost optimization
- **Finding Verifier**: Eliminates false positives by checking against actual source code
- **Actionability Classifier**: Distinguishes autonomous fixes (🤖 Claude) vs user decisions (👤)
- **Code Compression**: 89% token savings via aid tool
- **Multi-model Consensus**: Agreement-based finding aggregation

## Gap Analysis

### Critical Gaps
1. **Limited Focus Areas**: Only using 3/12 categories (design, clarity, reasoning) in Gate 6
2. **Verification Limited**: Only enabled for security reviews (Gate 8)
3. **No Actionability Integration**: Findings not classified for autonomous vs user decisions
4. **Cost Optimization Missing**: Not leveraging free provider prioritization
5. **No Code Compression**: Large projects reviewed at full token cost
6. **Consensus Mechanism Unused**: Not leveraging multi-model agreement for quality
7. **Focus Area Mismatch**: quality system uses 'design' but zen has 'code_quality', 'api_design'

## Requirements

### Functional Requirements

#### FR1: Focus Area Expansion
- Expand Gate 6 from 3 to all 12 available review categories
- Maintain backward compatibility via focus area mapping
- Default to mid-mode categories: security, bugs, error_handling, configuration, performance

#### FR2: Universal Verification
- Enable finding verification for all review types (not just security)
- Add configuration option: verify_findings (default: False)
- Add CLI flag: --verify
- Verify findings against actual source code to eliminate false positives

#### FR3: Actionability Classification
- Integrate ActionabilityClassifier for all reviews
- Classify findings as autonomous (🤖) or user decisions (👤)
- Display metrics in quality reports
- Add CLI flags: --classify (default), --no-classify

#### FR4: Cost Optimization
- Implement provider selection strategy prioritizing free/low-cost models
- Strategies: aggressive (100% free), balanced (70% free), quality_first (50% free)
- Add CLI flag: --cost-optimize {aggressive,balanced,quality_first}
- Target: 50%+ cost reduction

#### FR5: Code Compression
- Enable AI Distiller code compression for large projects
- Auto-compress when project > 10,000 lines (configurable)
- Add CLI flags: --compress, --compress-threshold N
- Target: 89% token savings

#### FR6: Consensus Quality Metrics
- Expose consensus quality scores from orchestrator
- Display agreement metrics: high (≥2 models), medium (1 model), low (dissenting)
- Calculate consensus quality score (0.0-1.0)
- Help users trust high-agreement findings

### Non-Functional Requirements

#### NFR1: Backward Compatibility
- Existing `.qual-gate.json` configs must work unchanged
- Focus area mapping for legacy configs
- All enhancements opt-in via CLI/config
- Defaults unchanged (verify=False, classify=True)

#### NFR2: Performance
- No significant degradation in execution time
- Code compression should not add >5 seconds overhead
- Verification should complete in <30 seconds for typical projects

#### NFR3: Deterministic Gates
- Gates 1-5 must remain deterministic (no LLM dependency)
- Only Gates 6-8 use LLM-enhanced analysis
- LLM unavailability should not break Gates 1-5

#### NFR4: Configuration Simplicity
- Sensible defaults for all new features
- Clear documentation
- Intuitive CLI arguments
- Comprehensive examples

## Architecture Constraints

1. **No Breaking Changes**: Must maintain backward compatibility
2. **Gate Separation**: Gates 1-5 deterministic, Gates 6-8 LLM-enhanced
3. **Adapter Pattern**: Use ZenCodeReviewAdapter as interface
4. **Hybrid Config**: Maintain CLI > config > env > defaults priority

## Success Criteria

- [ ] All 12 review categories available in Gate 6
- [ ] Verification filters >80% of false positives
- [ ] >30% of findings classified as autonomous
- [ ] 50%+ cost reduction via optimization
- [ ] 89% token savings for large projects
- [ ] >70% high-agreement findings in chad mode
- [ ] 100% backward compatibility maintained
- [ ] All tests pass (TDD approach)

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking changes | High | Backward compatibility mapping, opt-in defaults |
| Performance degradation | Medium | Async execution, smart timeouts |
| Cost increase | Medium | Free provider prioritization |
| Configuration complexity | Medium | Sensible defaults, clear docs |
| LLM dependency | Low | Gates 1-5 remain deterministic |

## Next Steps

1. ✅ Specification (this document)
2. ⏳ Requirement Analysis (/ask)
3. ⏳ Research Intelligence (/research)
4. ⏳ Architecture Analysis (/arch)
5. ⏳ Implementation Planning (/plan)
6. ⏳ Task Decomposition (/quadlet)
7. ⏳ Implementation with TDD
8. ⏳ Quality Gate Validation
9. ⏳ Results Synthesis
10. ⏳ Documentation & Closure
