# External LLM Second-Opinion Review Format

## Overview

This specification defines a reusable packet format for soliciting structured second-opinion
reviews from external LLMs (GLM-5.2, MiniMax-M3, etc.) during review workflows like
`/improve` and `/red-team`.

**Purpose:** External LLMs serve as bounded critics or breadth reviewers, not as final
decision-makers. The primary orchestrator merges or rejects their feedback.

## Review Packet Schema

### Input Packet (sent to external LLM)

```json
{
  "review_packet_id": "UUID",
  "context": {
    "session_summary": "Brief context about what we're reviewing",
    "domain": "prompt-review|code-workflow|hook-plugin-audit|proposal-review|design-review",
    "relevant_rules": [
      "Rule 1: Stop-hook requires evidence before claiming performance issues",
      "Rule 2: Provenance tags must trace to FACT entries"
    ]
  },
  "artifacts_under_review": [
    {
      "type": "file|prompt|hook|skill|config",
      "identifier": "SKILL.md or Stop_hook.py or prompt template",
      "excerpt": "Relevant excerpt or full content",
      "location": "file:line or section reference"
    }
  ],
  "primary_findings": [
    {
      "id": "F-001",
      "severity": "critical|high|medium|low",
      "summary": "One-line summary",
      "evidence": "Supporting evidence"
    }
  ],
  "unresolved_assumptions": [
    {
      "assumption": "What we're assuming but haven't verified",
      "risk_if_wrong": "What breaks if this assumption is false"
    }
  ],
  "specific_questions": [
    {
      "id": "Q-001",
      "question": "Concrete question for external reviewer",
      "focus": "missed-risks|overclaim|duplicate-grouping|evidence-gaps"
    }
  ],
  "success_criteria": {
    "decision": "PROCEED|REVISE|BLOCK",
    "must_check": [
      "No critical findings without evidence",
      "All BLOCK findings have verification path"
    ],
    "optional_checks": [
      "Considered alternative framing",
      "Checked for duplicate mechanisms"
    ]
  },
  "falsification_condition": "What evidence would change our verdict",
  "required_output_shape": {
    "missed_risks": "List of risks we didn't identify",
    "overclaimed_findings": "Findings where we overreached evidence",
    "severity_disagreements": "Findings with wrong severity level",
    "duplicate_grouping_suggestions": "Findings that should be merged",
    "evidence_gaps": "Findings lacking concrete evidence"
  }
}
```

### External LLM Response Format

```json
{
  "review_packet_id": "UUID (must match input)",
  "reviewer_model": "glm-5.2|minimax-m3|other",
  "reviewer_session_id": "External session UUID",
  "generated_at": "2026-07-05T14:30:00Z",
  
  "missed_risks": [
    {
      "id": "R-001",
      "description": "Risk we didn't identify",
      "severity": "critical|high|medium|low",
      "evidence_needed": "What evidence would confirm this",
      "confidence": "high|medium|low"
    }
  ],
  
  "overclaimed_findings": [
    {
      "finding_id": "F-001",
      "reason": "Why this finding overreaches evidence",
      "suggested_revision": "How to fix the claim"
    }
  ],
  
  "severity_disagreements": [
    {
      "finding_id": "F-002",
      "current_severity": "critical",
      "suggested_severity": "medium",
      "rationale": "Why the level should change"
    }
  ],
  
  "duplicate_grouping_suggestions": [
    {
      "findings_to_merge": ["F-003", "F-007"],
      "merged_title": "Unified finding title",
      "rationale": "Why these are the same issue"
    }
  ],
  
  "evidence_gaps": [
    {
      "finding_id": "F-004",
      "missing_evidence": "What concrete evidence is missing",
      "suggested_check": "How to get the evidence"
    }
  ],
  
  "additional_notes": "Any other relevant observations"
}
```

## Model Routing by Role

### GLM-5.2: High-Trust Second Critic

**Use for:** Consequential `/red-team` or `/improve` reviews where accuracy matters more
than cost.

**When to route:**
- Proposal under review touches critical paths (gates, hooks, core workflows)
- High-stakes architecture or CLAUDE.md changes
- Reviews where false negatives (missed issues) are expensive

**Role:** 
- Deep reasoning on correctness, security, and failure modes
- High confidence in identifying missed risks and evidence gaps
- Expected to take 30-60 seconds for thorough analysis

**Command routing:** `--model glm-5.2` (via pi or external API)

### MiniMax-M3: Cheaper Breadth Reviewer

**Use for:** Rapid breadth reviews, duplicate finding, normalizer, or "what did we miss?"
passes when cost matters more than depth.

**When to route:**
- Routine code reviews where speed is prioritized
- Large-scale scans looking for obvious issues
- "What did we miss?" exploratory passes
- Duplicate normalization across many findings

**Role:**
- Fast identification of obvious issues and duplicates
- Breadth over depth
- Expected to complete in 10-20 seconds

**Command routing:** `--model minimax-m3` (via pi or external API)

### Calibration Status

**Note:** If no benchmark exists for a model's reviewing capability on this codebase,
the routing is **provisional**. A calibration task should be created to measure:

- Precision: % of flagged issues that are real (TP / (TP + FP))
- Recall: % of real issues caught (TP / (TP + FN))
- False positive rate
- Overclaim detection accuracy

Add a calibration task with acceptance criteria before treating model routing
as authoritative.

## Integration Contract

### How the Orchestrator Uses External Feedback

**DO:**

- **Merge selectively:** Incorporate missed risks that are supported by evidence
- **Downgrade overclaims:** Reduce severity or remove findings that external review flags
- **Consider groupings:** Merge duplicates if external suggestion makes sense
- **Fill evidence gaps:** Request additional verification before promoting findings

**DO NOT:**

- **Let external LLM decide final verdict:** The orchestrator owns PROCEED/REVISE/BLOCK
- **Blindly accept all feedback:** External review is evidence, not authority
- **Skip verification:** External findings still require evidence verification
- **Use external LLM for everything:** Reserve for cases where model diversity or
  cost-performance tradeoffs justify it

### Example Flow

1. **Orchestrator** prepares review packet with current findings and questions
2. **Dispatch** to external LLM (GLM-5.2 for critical reviews, M3 for breadth)
3. **External LLM** returns structured response
4. **Orchestrator**:
   - Adds `missed_risks` to finding set (with evidence verification)
   - Downgrades or removes `overclaimed_findings`
   - Adjusts `severity_disagreements` if rationale is sound
   - Groups `duplicate_grouping_suggestions` if agreed
   - Flags `evidence_gaps` for additional verification
5. **Final verdict** based on merged, validated findings

## Error Handling

### Timeout or Failure

If external LLM call times out or fails:

- **Log the failure:** Record attempt and failure reason
- **Fall back to internal review:** Proceed without external feedback
- **Do not block:** External review is advisory, not required

### Malformed Response

If external LLM returns invalid JSON or missing required fields:

- **Log the error:** Record what was malformed
- **Use what's valid:** Extract any usable partial responses
- **Request retry (optional):** For critical reviews, may retry with clearer prompt

## See Also

- Shared schema: `packages/.claude-marketplace/shared/schemas/promotion_opportunity.schema.json`
- `/improve mode=external-second-opinion` skill mode
- `/red-team` integration with external critics
