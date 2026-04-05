# Implementation Plan: Automated Script Quality Assessment for Explainer Videos

**Generated**: 2026-03-15
**Status**: DRAFT
**Priority**: MEDIUM

---

## Problem Statement

**Current Challenge**: Need automated quality assessment for explainer video scripts without human review step.

**Specific Issue**: Video production pipeline includes compliance verification (forbidden word detection via faster-whisper), but lacks automated quality assessment to determine if compliant scripts are "great" and will resonate with users.

**Impact**: Without automated quality assessment, unable to systematically evaluate script quality before investing in video production (TTS audio generation, ffmpeg track replacement).

**Constraints**:
- Solution must be FULLY AUTOMATED - no human review step
- Must evaluate scripts BEFORE video production (text-only input)
- Should correlate with user's subjective assessment of "greatness"

---

## Context Analysis

**Research Findings** (from /research execution, 2026-03-15):

**LLM-as-a-Judge Validated**:
- ICC 0.818 correlation with human judgments for text quality evaluation
- Multiple frameworks available: DeepEval, RAGAs, UpTrain, G-Eval
- G-Eval uses step-by-step evaluation prompts with rubrics

**Readability Metrics Established**:
- Flesch-Kincaid Grade Level
- Flesch Reading Ease
- Gunning Fog Index
- SMOG (Simple Measure of Gobbledygook)
- Automated Readability Index

**Research Gap Identified**:
- VIDEO quality assessment: Well-explored (analyzing produced videos)
- SCRIPT quality assessment: Limited research (evaluating scripts before production)

**Existing Artifacts**:
- `P:/packages/handoff/assets/scripts/handoff_compliant_script.txt` (334 words, 164s audio)
- `P:/packages/handoff/assets/scripts/handoff_deep_dive_compliant_script.txt` (482 words, 231s audio)
- Both scripts pass compliance verification (0 forbidden words)
- Need to validate quality scores align with subjective assessment

---

## Existing Implementation Discovery

**Compliance Verification Pipeline** (already implemented):

1. **Script Generation**: Create script from brief
2. **Compliance Check**: faster-whisper transcription + forbidden word detection
3. **TTS Audio Generation**: Text-to-speech conversion
4. **Video Production**: ffmpeg track replacement

**Gap**: No quality assessment between steps 1-2. Script proceeds to production if compliant, regardless of quality.

**Quality Assessment Components** (NOT yet implemented):
- No LLM-based evaluation rubric
- No readability metric calculation
- No composite scoring algorithm
- No validation against subjective "greatness" assessment

---

## Test Discovery

**Test Coverage Requirements**:

1. **Unit Tests**:
   - Rubric scoring accuracy (test with known good/bad scripts)
   - Readability metric calculations (validate against known values)
   - LLM evaluation prompt testing (ensure structured JSON output)
   - Composite scoring algorithm (verify weight distribution)

2. **Integration Tests**:
   - End-to-end script evaluation pipeline
   - LLM API integration (Claude API for evaluation)
   - Multi-metric aggregation (readability + LLM scores)

3. **Validation Tests**:
   - Test on existing compliant scripts (2 scripts available)
   - Compare scores against user's subjective assessment
   - Iterate rubric until alignment achieved

**Test Data Sources**:
- Existing compliant scripts (handoff_compliant_script.txt, handoff_deep_dive_compliant_script.txt)
- Synthetic test cases (known good/bad scripts for validation)
- User's subjective "greatness" assessment (to be collected during validation)

---

## Proposed Solution

**Approach**: LLM-based Quality Scoring with Multi-Dimensional Rubric

**Architecture**:

```
Script Input
    ↓
┌─────────────────────────────────────────┐
│  Objective Metrics Calculation         │
│  - Flesch-Kincaid Grade Level           │
│  - Words per minute (speech rate)       │
│  - Sentence length distribution         │
│  - Vocabulary complexity                │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│  LLM Evaluation (G-Eval Pattern)       │
│  - Technical Accuracy (0-10)            │
│  - Clarity & Conciseness (0-10)         │
│  - Audience Appropriateness (0-10)      │
│  - Engagement Potential (0-10)          │
│  - Compliance Adherence (0-10)          │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│  Composite Scoring                     │
│  - Weighted combination (objective +    │
│    subjective LLM scores)               │
│  - Final score (0-100)                  │
│  - Dimension breakdown                  │
└─────────────────────────────────────────┘
    ↓
Quality Report (JSON + human-readable)
```

**Quality Rubric Definition** (5 dimensions, 0-10 each):

1. **Technical Accuracy** (0-10):
   - Factual correctness of technical claims
   - Accurate terminology and concepts
   - No misleading or ambiguous statements

2. **Clarity & Conciseness** (0-10):
   - Clear, direct language
   - Appropriate sentence length
   - Minimal jargon (or well-explained jargon)
   - No redundant explanations

3. **Audience Appropriateness** (0-10):
   - Matches target audience expertise level
   - Appropriate complexity for technical depth
   - Respectful tone, not condescending

4. **Engagement Potential** (0-10):
   - Compelling narrative flow
   - Interesting examples or analogies
   - Avoids boring/repetitive patterns

5. **Compliance Adherence** (0-10):
   - Follows brief requirements
   - Respects constraints (tone, length, format)
   - No forbidden words (verified separately)

**Composite Scoring Formula**:
```
Final Score (0-100) =
  (LLM Dimensions Average × 0.6) +
  (Readability Score × 0.2) +
  (Speech Rate Score × 0.2)
```

**Implementation Strategy**: Prototype → Validate → Iterate

---

## Implementation Plan

### Phase 1: Core Infrastructure (2-3h)

**TASK-001**: Create project structure and dependencies
- **File**: `P:/packages/script-quality-evaluator/` (new package)
- **Action**: Initialize Python project structure with requirements.txt
- **Dependencies**: `anthropic`, `textstat`, `python-dotenv`
- **Acceptance**:
  - Package structure created
  - Dependencies installable via pip
  - Basic README with usage instructions
- **Effort**: S (1h)
- **Prerequisites**: T-000

**TASK-002**: Implement readability metrics calculator
- **File**: `P:/packages/script-quality-evaluator/readability.py`
- **Action**: Create module using `textstat` library for metrics
- **Acceptance**:
  - Calculates Flesch-Kincaid Grade Level
  - Calculates Flesch Reading Ease
  - Calculates Gunning Fog Index
  - Returns normalized score (0-100)
- **Effort**: S (1h)
- **Prerequisites**: T-001

**TASK-003**: Implement objective metrics calculator
- **File**: `P:/packages/script-quality-evaluator/metrics.py`
- **Action**: Calculate speech rate, sentence length, vocabulary complexity
- **Acceptance**:
  - Words per minute calculation (from script word count)
  - Sentence length distribution (mean, median, max)
  - Vocabulary complexity (unique word ratio, syllable count)
  - Returns normalized score (0-100)
- **Effort**: M (2h)
- **Prerequisites**: T-002

### Phase 2: LLM Evaluation System (3-4h)

**TASK-004**: Design LLM evaluation prompt (G-Eval pattern)
- **File**: `P:/packages/script-quality-evaluator/prompts.py`
- **Action**: Create structured prompt for Claude API with rubric
- **Acceptance**:
  - Prompt includes 5-dimension rubric with scoring guidelines
  - Prompt requests structured JSON output
  - Prompt includes step-by-step evaluation instructions
  - Tested with manual API call to verify JSON parsing
- **Effort**: M (2h)
- **Prerequisites**: T-001

**TASK-005**: Implement LLM evaluation client
- **File**: `P:/packages/script-quality-evaluator/llm_evaluator.py`
- **Action**: Create Claude API client for script evaluation
- **Acceptance**:
  - Calls Claude API with evaluation prompt
  - Parses JSON response with error handling
  - Returns dimension scores with reasoning
  - Handles API errors and retries
- **Effort**: M (2h)
- **Prerequisites**: T-004

### Phase 3: Composite Scoring (1-2h)

**TASK-006**: Implement composite scoring algorithm
- **File**: `P:/packages/script-quality-evaluator/scoring.py`
- **Action**: Combine LLM scores with objective metrics
- **Acceptance**:
  - Applies weight distribution (60% LLM, 20% readability, 20% speech rate)
  - Normalizes all scores to 0-100 range
  - Returns final score with dimension breakdown
  - Includes confidence interval based on component variance
- **Effort**: S (1h)
- **Prerequisites**: T-003, T-005

**TASK-007**: Create quality report generator
- **File**: `P:/packages/script-quality-evaluator/reporting.py`
- **Action**: Generate human-readable + JSON quality reports
- **Acceptance**:
  - Outputs JSON with scores, dimensions, confidence interval
  - Outputs human-readable markdown report
  - Includes recommendations for improvement (low-scoring dimensions)
  - Saves reports to output directory with timestamp
- **Effort**: S (1h)
- **Prerequisites**: T-006

### Phase 4: Integration & CLI (1-2h)

**TASK-008**: Create CLI interface
- **File**: `P:/packages/script-quality-evaluator/cli.py`
- **Action**: Implement command-line interface for script evaluation
- **Acceptance**:
  - Accepts script file path as input
  - Outputs quality report to stdout and file
  - Supports JSON output mode for programmatic use
  - Includes --verbose flag for detailed dimension breakdown
- **Effort**: S (1h)
- **Prerequisites**: T-007

**TASK-009**: Write integration tests
- **File**: `P:/packages/script-quality-evaluator/tests/test_integration.py`
- **Action**: Test end-to-end evaluation pipeline
- **Acceptance**:
  - Tests with existing compliant scripts (2 scripts)
  - Validates all components integrate correctly
  - Checks output format (JSON + markdown)
  - Measures execution time (< 30s per script)
- **Effort**: M (2h)
- **Prerequisites**: T-008

### Phase 5: Validation & Iteration (2-3h)

**TASK-010**: Validate on existing compliant scripts
- **File**: Validation script (one-off)
- **Action**: Run evaluator on handoff_compliant_script.txt and handoff_deep_dive_compliant_script.txt
- **Acceptance**:
  - Both scripts evaluated successfully
  - Quality scores generated with dimension breakdown
  - Execution time < 30s per script
  - Reports saved to output directory
- **Effort**: S (1h)
- **Prerequisites**: T-009

**TASK-011**: Collect user's subjective assessment
- **File**: Comparison report (one-off)
- **Action**: Compare automated scores against user's subjective "greatness" assessment
- **Acceptance**:
  - User reviews quality reports for both scripts
  - User provides subjective assessment (0-100) for each script
  - Calculate correlation between automated and subjective scores
  - Document gap analysis and iteration recommendations
- **Effort**: M (2h)
- **Prerequisites**: T-010

**TASK-012**: Iterate rubric based on validation (OPTIONAL)
- **File**: Update prompts.py with refined rubric
- **Action**: Adjust rubric weights or scoring guidelines based on user feedback
- **Acceptance**:
  - Updated rubric reflects user's quality priorities
  - Re-run validation on existing scripts
  - Improved correlation with subjective assessment
  - Document iteration decisions for reproducibility
- **Effort**: L (3h)
- **Prerequisites**: T-011

### Phase 6: Documentation & Deployment (1h)

**TASK-013**: Write README and usage documentation
- **File**: `P:/packages/script-quality-evaluator/README.md`
- **Action**: Document installation, usage, and rubric definition
- **Acceptance**:
  - Installation instructions (pip install)
  - Usage examples (CLI command)
  - Rubric definition (all 5 dimensions with scoring guidelines)
  - Integration examples (how to use in video production pipeline)
- **Effort**: S (1h)
- **Prerequisites**: T-012

---

## Risks, Success Criteria, Dependencies

**Top Risks**:

1. **LLM evaluation may not correlate with subjective "greatness"**: LLM scores might not align with user's assessment, requiring multiple rubric iterations
   - **Mitigation**: Prototype first on existing scripts, validate early, iterate rubric before full integration

2. **API rate limits and costs**: Claude API calls for every script evaluation may hit rate limits or become costly at scale
   - **Mitigation**: Implement caching for repeated evaluations, batch evaluations where possible, monitor usage

3. **Readability metrics may not capture technical writing quality**: Standard readability metrics (Flesch-Kincaid) designed for general text, may not accurately assess technical explainer scripts
   - **Mitigation**: Weight readability metrics lower (20%) compared to LLM evaluation (60%), validate on technical scripts specifically

**Success Criteria**:

1. **Automated quality scores correlate with user assessment**: ≥ 0.7 correlation coefficient between automated scores and user's subjective "greatness" assessment
2. **Evaluation completes in < 30 seconds per script**: End-to-end evaluation from script input to quality report generation
3. **Quality reports provide actionable insights**: Dimension breakdown identifies specific areas for improvement (low-scoring dimensions)
4. **System integrates with existing compliance pipeline**: Can be inserted into video production workflow between compliance check and TTS generation

**Dependencies**:

- **Claude API access**: API key for anthropic.claude.com (already have from existing usage)
- **Python environment**: Python 3.14+ with pip package management
- **Existing compliant scripts**: Test data for validation (already available: handoff_compliant_script.txt, handoff_deep_dive_compliant_script.txt)
- **User's subjective assessment**: Time to review quality reports and provide "greatness" scores for validation

**Integration Points**:

- **Video Production Pipeline**: Insert between compliance check and TTS generation
  - Current: Script → Compliance Check → TTS → Video
  - New: Script → Compliance Check → **Quality Assessment** → TTS → Video
- **CLI Integration**: Can be called as standalone tool or imported as Python module
- **Output Formats**: JSON (programmatic) + Markdown (human-readable)

**Rollback Strategy**:

- **If automated scores don't correlate with subjective assessment**: Revert to manual quality review, use automated scores as one input among many
- **If API costs/rate limits become prohibitive**: Implement caching aggressively, consider local LLM alternatives (Ollama, etc.)
- **If system doesn't provide actionable insights**: Iterate rubric definition with user feedback, add/remove dimensions as needed

---

## Next Steps

1. Review plan for completeness and feasibility
2. Run verification (auto_verify.py) to check for missing components
3. Begin implementation with Phase 1 (Core Infrastructure)
4. Validate on existing compliant scripts after Phase 4 completion
5. Iterate rubric based on user feedback (Phase 5)

---

**Total Estimated Effort**: 12-18 hours
**Critical Path**: T-001 → T-004 → T-005 → T-006 → T-007 → T-008 → T-009 → T-010 → T-011
**Potential Parallelization**: T-002, T-003 can run in parallel after T-001 completes
