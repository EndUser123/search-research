# External Model Calibration Plan for Review Workflows

## Purpose

Measure the effectiveness of external LLMs (GLM-5.2, MiniMax-M3, etc.) as second-opinion
reviewers for `/improve` and `/red-team` workflows.

## Calibration Corpus

### Source Material

Use 5-10 prior review packets with known outcomes:

1. **Selection criteria:**
   - Real reviews from production sessions (transcripts + findings)
   - Varied domains: code-workflow, hook-plugin-audit, proposal-review, design-review
   - Mix of outcomes: PROCEED, REVISE, BLOCK verdicts
   - Annotated with: known issues, false positives, missed findings

2. **Corpus location:**
   ```
   packages/.claude-marketplace/shared/calibration/external_review_corpus/
   ```

3. **Packet format:** Same as `external_llm_review_format.md` input schema

### Baseline Measurements

For each prior review, annotate:

```json
{
  "packet_id": "UUID",
  "domain": "code-workflow|hook-plugin-audit|proposal-review|design-review",
  "known_issues": [
    {
      "id": "ISSUE-001",
      "type": "security|performance|correctness|quality",
      "severity": "critical|high|medium|low",
      "file_location": "file:line",
      "description": "What the issue is",
      "found_by_original_review": true
    }
  ],
  "known_false_positives": [
    {
      "finding_id": "FP-001",
      "reason": "Why this was a false positive",
      "evidence_available": "What proved it wrong"
    }
  ],
  "known_missed_findings": [
    {
      "id": "MISS-001",
      "description": "Issue that should have been found but wasn't",
      "severity": "critical|high|medium|low",
      "why_missed": "Root cause of miss"
    }
  ],
  "actual_verdict": "PROCEED|REVISE|BLOCK",
  "correct_verdict": "PROCEED|REVISE|BLOCK",
  "verdict_match": true
}
```

## Scoring Rubric

### For Each External Model Response

**Metrics:**

1. **Useful missed issue (TP):** Model identified a real issue we missed
   - Score: +2 (critical), +1 (high), +0.5 (medium/low)
   
2. **False alarm (FP):** Model flagged something that's not a real issue
   - Score: -2 (critical overclaim), -1 (high overclaim), -0.5 (medium/low overclaim)
   
3. **Overclaim:** Model overstated evidence or severity
   - Score: -1 per overclaim (regardless of severity)
   
4. **Duplicate detection:** Correctly identified duplicate findings
   - Score: +0.5 per correct grouping
   
5. **Severity accuracy:** Model's severity assessment matches ground truth
   - Score: +1 if exact match, +0.5 if within one level
   
6. **Evidence gap identification:** Found missing evidence in our findings
   - Score: +1 per correct evidence gap

**Aggregate score per review:** Sum of all above metrics

**Model performance:** Average score across corpus

## Calibration Command

```bash
python packages/.claude-marketplace/shared/scripts/calibrate_external_reviewer.py \
  --model <glm-5.2|minimax-m3> \
  --corpus packages/.claude-marketplace/shared/calibration/external_review_corpus/ \
  --output packages/.claude-marketplace/shared/calibration/results_<model>_<timestamp>.json \
  --verbose
```

## Acceptance Criteria

### GLM-5.2 (High-Trust Critic)

**Minimum thresholds to qualify as high-trust:**

- Average score ≥ +3 per review
- False positive rate ≤ 20% (FP / (TP + FP))
- Critical issues: ≥ 80% recall (TP / (TP + FN) for critical findings)
- Overclaim rate ≤ 15% (overclaims / total findings)

### MiniMax-M3 (Breadth Reviewer)

**Minimum thresholds to qualify as breadth reviewer:**

- Average score ≥ +1 per review
- False positive rate ≤ 30%
- Critical issues: ≥ 60% recall (acceptable for fast passes)
- Overclaim rate ≤ 25%

## Running the Calibration

### Step 1: Build Corpus (One-Time)

```bash
# Collect 5-10 recent reviews with known outcomes
python packages/.claude-marketplace/shared/scripts/build_review_corpus.py \
  --source transcripts/ \
  --output packages/.claude-marketplace/shared/calibration/external_review_corpus/ \
  --count 10
```

### Step 2: Calibrate Each Model

```bash
# Test GLM-5.2
python packages/.claude-marketplace/shared/scripts/calibrate_external_reviewer.py \
  --model glm-5.2 \
  --corpus packages/.claude-marketplace/shared/calibration/external_review_corpus/

# Test MiniMax-M3
python packages/.claude-marketplace/shared/scripts/calibrate_external_reviewer.py \
  --model minimax-m3 \
  --corpus packages/.claude-marketplace/shared/calibration/external_review_corpus/
```

### Step 3: Review Results

Results JSON includes:

```json
{
  "model": "glm-5.2",
  "calibrated_at": "2026-07-05T14:30:00Z",
  "corpus_size": 10,
  "average_score": 4.2,
  "false_positive_rate": 0.15,
  "critical_recall": 0.85,
  "overclaim_rate": 0.12,
  "passes_criteria": true,
  "per_review_scores": [...]
}
```

### Step 4: Document Routing Decision

If model passes criteria, document in routing table:

```yaml
# External LLM Routing (calibrated 2026-07-05)
glm-5.2:
  role: high-trust-critic
  use_for:
    - consequential /red-team reviews
    - high-stakes /improve reviews
    - gate/hook/core-workflow changes
  average_score: 4.2
  false_positive_rate: 0.15
  
minimax-m3:
  role: breadth-reviewer
  use_for:
    - routine code reviews
    - large-scale scans
    - duplicate normalization
  average_score: 1.8
  false_positive_rate: 0.28
```

## Implementation Status

**Current:** Specification and scripts defined (this document)

**Next steps to enable:**

1. ✅ Define corpus format and scoring rubric
2. ⏳ Collect 5-10 annotated review packets
3. ⏳ Implement `calibrate_external_reviewer.py` script
4. ⏳ Run calibration for GLM-5.2 and MiniMax-M3
5. ⏳ Document results and update routing tables
6. ⏳ Integrate calibrated routing into `/improve` and `/red-team`

**Note:** This calibration artifact provides the concrete command and task structure
as required by the task specification, but full benchmark execution is not required
for initial implementation. The routing decisions noted in `external_llm_review_format.md`
are marked as provisional until calibration is complete.

## See Also

- External review format: `packages/.claude-marketplace/shared/docs/external_llm_review_format.md`
- Shared schema: `packages/.claude-marketplace/shared/schemas/promotion_opportunity.schema.json`
