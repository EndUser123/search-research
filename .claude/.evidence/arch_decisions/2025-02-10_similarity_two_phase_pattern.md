# Architecture Decision: Two-Phase Pattern for /similarity Skill

**Date:** 2025-02-10
**Template:** python
**Status:** Accepted

## Decision

Keep `/similarity` as a single-phase PROCEDURE skill. Add optional `--deep` flag for LLM-enhanced re-ranking instead of a mandatory two-phase review.

## Context

User asked whether `/similarity` should use a two-phase pattern:
1. Phase 1: LLM reviews and updates similarity code/prompt
2. Phase 2: Execute improved version

## Analysis

### Current State
- `/similarity` is a PROCEDURE-type skill that runs `similarity.py`
- Fixed algorithm: keyword extraction + category + dependency matching
- Test run on `/evolve` produced reasonable results (`/p --phase=1` at 0.70 score)
- Execution time: ~2 seconds for 233 skills

### Proposed Two-Phase Pattern
```
Phase 1: LLM reviews skill → updates code
Phase 2: Execute improved version
```

### Concerns Identified
| Concern | Impact |
|---------|--------|
| Execution overhead | +30-60 seconds latency for LLM review |
| Circular dependency | Who reviews the reviewer? |
| State drift | Code changes each run = no reproducibility |
| Trust boundary | LLM-generated code needs validation |

## Rationale

1. **Current algorithm works** — Keyword frequency + category + dependencies produce sensible similarity scores

2. **Wrong layer for adaptation** — Improvements should be algorithmic:
   - Add semantic similarity (embeddings)
   - Learn optimal weights from feedback
   - Add domain-specific scoring profiles

3. **Hybrid pattern preferred** — Better approach:
   ```
   Phase 1 (Fast): Keyword-based scoring (always runs)
   Phase 2 (Optional): LLM re-ranking on top-N results (--deep flag)
   ```

## Implementation Sketch

```python
def main():
    # Phase 1: Fast keyword-based scoring (current)
    baseline_results = run_keyword_similarity(target)

    # Phase 2: Optional LLM refinement
    if "--deep" in sys.argv:
        top_n = baseline_results[:10]
        refined_results = llm_semantic_rerank(target, top_n)
        output = refined_results
    else:
        output = baseline_results
```

## Alternatives Considered

| Alternative | Decision | Reason |
|-------------|----------|--------|
| Two-phase mandatory review | Rejected | Latency, reproducibility concerns |
| Self-modifying code | Rejected | Trust boundary, testing complexity |
| Hybrid baseline + optional deep | **Accepted** | Preserves fast path, enables enhancement |

## Risks

- Adding `--deep` flag requires LLM API integration (not currently present)
- Need to define re-ranking criteria
- Potential user confusion about when to use `--deep`

## References

- Test output: `P:/.claude/skills/similarity/evolve_report.json`
- Source code: `P:/.claude/skills/similarity/similarity.py`
