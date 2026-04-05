# ADR-20260317: Optimal-First Solution Proposal via Comparative Analysis

**Status:** Accepted
**Date:** 2026-03-17
**Context:** Suboptimal solutions appear first instead of optimal ones during architecture/design decisions.

---

## Decision

Adopt **Option 2: Comparative Analysis First (Optimal-Last Swap)** as the mandatory cognitive pattern for all decisions with multiple viable approaches.

**Core Pattern**: "Search → Evaluate → Implement" — Generate 2-3 diverse candidates first, analyze tradeoffs, then select optimal.

---

## Rationale

**Root Cause**: Suboptimal-first occurs because current process generates first idea, then checks quality. This is reactive.

**Fix**: Invert the process — generate diverse options FIRST (Verbalized Sampling with K=3), then select optimal based on:
- Native/platform-native > Custom code bias
- Prompting/pattern-matching > Script/automation bias
- Discovery-first (check existing implementations before building)

**Why this approach:**
1. **Prevents** suboptimal-first (vs detecting after generation like Options 1/3)
2. **Aligns** with existing patterns: `discovery_patterns.md`, `questioning_patterns.md`
3. **Proven**: Industry standard (ATAM tradeoff analysis, architecture decision frameworks)
4. **Platform-native**: Uses prompting, not scripts/automation

---

## Tradeoffs

| Quality | Improved | Degraded |
|---------|----------|----------|
| Solution Quality | Optimal appears first | N/A |
| Decision Latency | Higher quality | ~10-30% latency increase |
| Cognitive Load | Systematic process | Multi-option tracking |

**ISO 25010**: +Quality, +Maintainability, -Performance Efficiency (latency)

---

## Multi-Terminal Safety

- **Safe**: Cognitive pattern, no stateful code
- **No shared state**: Per-terminal execution, no coordination needed
- **Concurrency-safe**: Independent terminals can execute same pattern

---

## Implementation

**For ANY problem with multiple solution approaches:**

### Step 1: Generate 2-3 diverse candidates (Verbalized Sampling)
- At least K=3 options before selecting
- Distribute across probability bands: [0.5, 0.8], [0.3, 0.5], [0.05, 0.3]
- Ensure structural diversity (min Jaccard distance 0.4)

### Step 2: Analyze tradeoffs of each candidate
- Apply 8 architectural lenses (value, consolidation, dependency, contract, multi-terminal, evidence, systems, tradeoff)
- Evaluate against questioning_patterns.md:
  1. "Why this specific value?" (arbitrary threshold check)
  2. "Does this work with concurrent execution?" (race condition check)
  3. "Is this necessary or nice-to-have?" (over-engineering check)

### Step 3: Select optimal based on context
- Native/platform-native > Custom code
- Prompting/pattern-matching > Script/automation
- Discovery-first (check existing patterns before building new)

### Integration Points
- **/code** (SKILL.md line 1428+): Add comparative analysis before implementation suggestions
- **/arch** (base.md): Already implements VS (Stage 0.8) — reinforce DEFAULT path
- **/plan**: Add "alternatives considered" section to plan output

### Memory File Updates
- **questioning_patterns.md**: Add "Search → Evaluate → Implement" as Question 0
- **discovery_patterns.md**: Link to VS generation step explicitly
- **working_principles.md**: Add "Compare before committing" as principle 6

---

## Testing Approach

1. **Verification**: Use /arch on 3-5 recent decisions to verify pattern would have produced optimal-first
2. **Regression**: Monitor for "suboptimal-first" incidents in future work
3. **Metrics**: Track % of decisions where VS generates >1 candidate before selection

---

## Rollback Strategy

If latency proves too heavy:
1. Reduce K from 3 to 2 candidates for simple decisions
2. Add "fast path" exception for trivial cases (< 5 min decisions)
3. Revert to pre-output questioning (Option 1) as fallback

---

## Consequences

### Positive
- Prevents suboptimal-first at root cause level
- Aligns with ATAM tradeoff analysis (industry standard)
- Integrates existing memory patterns (discovery, questioning, working principles)
- Platform-native (no new scripts/automation)

### Negative
- 10-30% latency increase per decision (mitigated by quality improvement)
- Requires discipline to always generate multiple options (enforced via VS protocol)

### Mitigations
- Fast path exception for trivial decisions (< 5 min)
- K=2 for straightforward cases (vs K=3 for complex)
- Latency acceptable given quality improvement

---

## Edge Cases

1. **Overhead for trivial decisions**: 5-line fix doesn't need 3 candidates
   - *Mitigation*: Complexity gate — only apply VS for decisions with >1 viable approach

2. **Illusion of diversity**: 3 candidates that are effectively the same
   - *Mitigation*: Enforce minimum Jaccard distance (0.4) per VS protocol

3. **Paralysis by analysis**: Endless comparing without committing
   - *Mitigation*: Time-box evaluation — 5 min max for tradeoff analysis

4. **Integration with existing skills**: /code, /loop-code, /refactor may lack VS
   - *Mitigation*: Add "alternatives considered" section, even if 1 candidate

5. **User fatigue**: Seeing 3 options when user wants "the answer"
   - *Mitigation*: Present options in appendix, lead with recommended option

---

## Evidence Sources

- **Internal**: `questioning_patterns.md`, `discovery_patterns.md`, `working_principles.md`, `reasoning_flaws.md`
- **Web Research**: "LLM metacognition requires explicit reasoning chains" (tavily search)
- **Framework**: ATAM (Architecture Tradeoff Analysis Method) — industry standard
- **Existing**: /arch already implements VS (Stage 0.8) with K=3-4 candidates

---

## Related Decisions

- **Supersedes**: Implicit "generate-first, check-later" pattern
- **Aligns with**: `questioning_patterns.md` (Q0: "Search → Evaluate → Implement")
- **Implements**: `discovery_patterns.md` principle (search before build)

---

*End of ADR-20260317*
