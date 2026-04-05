# Cross-Category Pattern Analysis (2026-03-15)

## Methodology
- **Data source**: `P:/__csf/data/cks.db`
- **Time range**: Last 30 days (2026-02-13 to 2026-03-15)
- **Entry types analyzed**: `pattern`, `correction`
- **Total entries analyzed**: 2,744 pattern entries
- **Analysis approach**: Extracted combinations of frameworks, modes, and profiles appearing together in CKS entries, sorted by frequency

## Top Cross-Category Combinations

### 1. AST + Regex + Batch
- **Occurrences**: 21
- **Evidence**:
  > "refactor_plan_review.md: Refactor Plan-and-Review Enhancement (2026-03-14): # Refactor Plan-and-Review Enhancement (2026-03-14) **Problem**: The `/re..."
  >
  > "refactor_plan_review.md: How This Prevents The Original Failure: **Original failure**: Session ID consolidation plan: - Approach: Regex-based batc..."
- **Why it matters**: This combination appears in refactor planning workflows where AST-based analysis is combined with regex pattern matching for batch operations. The synergy suggests that batch refactoring needs both structural (AST) and pattern-based (regex) validation.
- **Current gap**: No dedicated enhancement for AST+regex batch operations. System treats these as separate concerns.
- **Priority**: HIGH (21 occurrences)

### 2. Git + Multi-terminal
- **Occurrences**: 16
- **Evidence**:
  > "reasoning_flaws.md: Flaw 2: Ignoring Concurrency Constraints: **The pattern**: Proposing solutions that don't work in concurrent/multi-terminal enviro..."
  >
  > "questioning_patterns.md: Pattern 2: 'Are You Sure About Concurrency?' (Shared State Detection): **Your question**: 'Are you sure Git is better in a mu..."
- **Why it matters**: Git operations in multi-terminal environments require special handling due to shared state risks. Users repeatedly encounter this as a reasoning flaw pattern.
- **Current gap**: Multi-terminal detection exists but doesn't trigger specialized Git workflow warnings or state isolation guidance.
- **Priority**: HIGH (16 occurrences)

### 3. AST + Verify + Parallel
- **Occurrences**: 8
- **Evidence**:
  > "questioning_patterns.md: Pattern 5: 'Debugging Cognition' (Meta-Cognitive Debugging): **User's feedback**: 'why didn't you figure that out before? why..."
- **Why it matters**: Parallel verification workflows involving AST analysis appear in debugging cognition patterns. Suggests users want faster, parallel verification of code changes.
- **Current gap**: Verification enhancement doesn't specialize for AST-based parallel workflows.
- **Priority**: MEDIUM (8 occurrences)

### 4. Git + Pytest + Regex + Verify + Batch
- **Occurrences**: 8
- **Evidence**:
  > "process_improvements.md: Batch Refactoring Validation System (2026-03-14): **Problem**: Batch refactoring scripts introduced 8 syntax errors that pers..."
- **Why it matters**: This is the full testing stack for batch refactoring. Users need comprehensive validation that combines Git state, pytest execution, regex patterns, and verification gates.
- **Current gap**: No integrated enhancement that coordinates all four layers in batch workflows.
- **Priority**: HIGH (8 occurrences, high complexity)

### 5. AST + Regex + Verify + Batch
- **Occurrences**: 8
- **Evidence**:
  > "integration_verification.md: Process Fix: ### 1. Integration Verification Checklist (MANDATORY) **Add to skill development workflow:**..."
- **Why it matters**: AST+regex verification in batch contexts appears in integration verification checklists. This is about ensuring refactoring tools don't break integration.
- **Current gap**: Verification enhancement doesn't prioritize AST+regex patterns in batch mode.
- **Priority**: MEDIUM (8 occurrences)

### 6. Verify + Batch
- **Occurrences**: 8
- **Evidence**:
  > "hooks_operational_guide.md: Troubleshooting: ### Hook Not Running 1. **Check frontmatter syntax**: YAML must be valid, indentation matters 2. **Verif..."
- **Why it matters**: Generic verification in batch workflows. This is foundational for any batch operation safety.
- **Current gap**: Verify enhancement doesn't have batch-specific guidance or warnings.
- **Priority**: LOW (8 occurrences, but generic)

### 7. AST + Parallel
- **Occurrences**: 7
- **Evidence**:
  > "tool_usage_patterns.md: Agent Tool Model Parameter (2026-03-09): **Pattern**: Use `model="haiku"` with Agent tool for fast parallel subagents **Why**..."
- **Why it matters**: AST-based operations in parallel contexts, specifically for Agent tool usage patterns.
- **Current gap**: AST enhancement doesn't provide parallel execution guidance.
- **Priority**: MEDIUM (7 occurrences)

### 8. AST + Git + Pytest + Regex + Batch
- **Occurrences**: 7
- **Evidence**:
  > "refactor_plan_review.md: Implementation: ### Step 4.5: Create Refactoring Plan **File**: `P:\.claude\skills\refactor\lib\refactor_plan.py`..."
- **Why it matters**: Four-layer stack for refactoring planning. Combines code structure (AST), version control (Git), testing (pytest), and patterns (regex) in batch workflows.
- **Current gap**: No unified enhancement that coordinates all four layers for refactoring.
- **Priority**: HIGH (7 occurrences, high complexity)

### 9. AST + Git + Regex + Batch
- **Occurrences**: 7
- **Evidence**:
  > "refactor_plan_review.md: Usage Example: **Dry run**: `/refactor P:/.claude/hooks/ --dry-run` **Output**: === REFACTORING PLAN === ## O..."
- **Why it matters**: Core refactoring stack without pytest layer. AST+Git+regex in batch mode is the minimal safe refactoring combination.
- **Current gap**: Refactoring workflows don't get specialized cognitive enhancement for this combination.
- **Priority**: MEDIUM (7 occurrences)

### 10. AST + Git + Search + Verify + Multi-terminal
- **Occurrences**: 5
- **Evidence**:
  > "learning_patterns.md: High-Signal Examples: ### Event timing confusion **Pattern**: confusing when a hook or lifecycle event fires. **Correct respon..."
- **Why it matters**: Complex multi-terminal scenario involving code search, verification, and Git operations. Appears in learning patterns around event timing.
- **Current gap**: Multi-terminal enhancement doesn't coordinate with search/verify/git stacks.
- **Priority**: MEDIUM (5 occurrences, high complexity)

### 11. AST + Git + Parallel
- **Occurrences**: 4
- **Evidence**:
  > "constitution.md: Professional Quality Standards (Appropriate Patterns): These patterns are **appropriate and encouraged** for professional solo dev + ..."
- **Why it matters**: AST and Git operations in parallel contexts. Appears in constitution documentation as appropriate patterns.
- **Current gap**: No parallel-specific guidance for AST+Git workflows.
- **Priority**: LOW (4 occurrences)

### 12. Git + Parallel
- **Occurrences**: 4
- **Evidence**:
  > "constitution.md: Professional Quality Standards (Appropriate Patterns): These patterns are **appropriate and encouraged** for professional solo dev + ..."
- **Why it matters**: Git operations in parallel contexts. Foundational pattern for concurrent version control workflows.
- **Current gap**: Git enhancement doesn't address parallel execution risks or patterns.
- **Priority**: LOW (4 occurrences)

## Summary Statistics
- **Total unique combinations found**: 12
- **High-frequency combinations (>10 occurrences)**: 2
- **Medium-frequency combinations (5-9 occurrences)**: 8
- **Low-frequency combinations (3-4 occurrences)**: 2
- **Most common frameworks**: AST (10/12 combos), Git (8/12 combos)
- **Most common modes**: Batch (9/12 combos), Parallel (6/12 combos)
- **Most common profiles**: Verification (5/12 combos)

## Recommendations

### 1. Initial Matrix Entries to Prioritize

**Phase 1 (Immediate) - High-Value, High-Frequency**:
- `ast + regex + batch` → Add batch validation guidance to AST/regex enhancements
- `git + multi-terminal` → Add state isolation warnings to Git enhancement in multi-terminal contexts
- `git + pytest + regex + verify + batch` → Create integrated batch refactoring enhancement

**Phase 2 (Short-term) - Medium-Frequency, High-Impact**:
- `ast + verify + parallel` → Add parallel verification workflow guidance
- `ast + git + pytest + regex + batch` → Create four-layer refactoring stack enhancement
- `ast + git + search + verify + multi-terminal` → Create multi-terminal search/verify coordination

**Phase 3 (Long-term) - Specialized Patterns**:
- `ast + regex + verify + batch` → Integration verification focus
- `ast + git + regex + batch` → Minimal refactoring stack enhancement
- `ast + parallel` → Parallel AST operations guidance
- `git + parallel` → Concurrent Git workflow patterns

### 2. High-Value Combinations (>5 occurrences)
All combinations with 5+ occurrences should be added to the compatibility matrix:
1. `ast + regex + batch` (21)
2. `git + multi-terminal` (16)
3. `ast + verify + parallel` (8)
4. `git + pytest + regex + verify + batch` (8)
5. `ast + regex + verify + batch` (8)
6. `verify + batch` (8) - but low priority due to generic nature
7. `ast + parallel` (7)
8. `ast + git + pytest + regex + batch` (7)
9. `ast + git + regex + batch` (7)
10. `ast + git + search + verify + multi-terminal` (5)

### 3. Low-Value Combinations to Skip or Defer
- `verify + batch` - Too generic, doesn't need specialized handling
- `git + parallel` - Low frequency (4), can be handled by existing Git enhancement
- `ast + git + parallel` - Low frequency (4), overlap with other patterns

## Implementation Notes

### Pattern Clustering
The combinations reveal three distinct clusters:

1. **Batch Refactoring Cluster** (9 combinations)
   - Core pattern: `ast + regex + batch`
   - Extended with: Git, pytest, verify
   - All 9 combinations should be handled by a unified "batch refactoring" enhancement

2. **Multi-Terminal Cluster** (2 combinations)
   - Core pattern: `git + multi-terminal`
   - Extended with: ast, search, verify
   - Requires state isolation and coordination guidance

3. **Parallel Verification Cluster** (3 combinations)
   - Core pattern: `ast + verify + parallel`
   - Extended with: git, search
   - Requires parallel workflow optimization

### Data Quality Notes
- All evidence comes from CKS `pattern` entries (no `correction` entries found in date range)
- Evidence is strong: patterns are documented in learning and memory files
- Time distribution: Most entries from 2026-03-15, with some from 2026-03-14
- Some data duplication exists (same content at different timestamps) - counts may be slightly inflated

### Next Steps
1. Implement Phase 1 matrix entries (3 combinations)
2. Add detection for batch refactoring cluster (9 combinations share common enhancement)
3. Add detection for multi-terminal cluster (2 combinations)
4. Create integration tests for new matrix entries
5. Monitor CKS for new cross-category patterns over next 30 days
