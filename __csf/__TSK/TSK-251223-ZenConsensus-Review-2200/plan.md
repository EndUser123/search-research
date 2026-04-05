# Implementation Plan: Extend zen-consensus for Code Review

**TSK-ID**: TSK-251223-ZenConsensus-Review-2200
**Created**: 2025-12-23 15:30:00
**Status**: Ready for Implementation

## Architecture Summary

**Approach**: Extend zen-consensus with code review modes (chill/mid/chad)
**Complexity**: +3 (well under +5 threshold)
**Code Reuse**: 80% (leverages existing zen* infrastructure)
**Implementation Time**: 4-6 hours

## Implementation Phases

### Phase 1: Git Integration Layer (1.5 hours)

**Tasks**:
1. Create `diff_generator.py` module
   - `get_git_diff(repo_path, commit_range, context_lines)` function
   - Subprocess-based git execution
   - Error handling (not a git repo, no changes, invalid commits)

2. Create `diff_parser.py` module
   - Parse unified diff format
   - Extract files, hunks, line numbers, context
   - Handle edge cases (renames, binary files, merge conflicts)

3. Create `diff_formatter.py` module
   - Format diff for LLM prompts
   - Add file metadata, language detection
   - Context window management (chunk large diffs)

**Files**:
- `P:/__csf.nip/src/zen/lib/diff_generator.py` (NEW)
- `P:/__csf.nip/src/zen/lib/diff_parser.py` (NEW)
- `P:/__csf.nip/src/zen/lib/diff_formatter.py` (NEW)

### Phase 2: Prompt Templates (1 hour)

**Tasks**:
1. Create template directory structure
   - `P:/__csf.nip/src/zen/templates/code_review/`
   - Templates: chill.md, mid.md, chad.md
   - Focus-specific prompts: security.md, performance.md, bugs.md, style.md

2. Implement `review_prompt_builder.py`
   - `build_review_prompt(diff, mode, focus_areas)` function
   - Template injection with context
   - Structured output requirements (JSON format)

**Templates**:
- **chill.md**: Quick review, free/fast models, focus on critical issues
- **mid.md**: Balanced review, standard models, comprehensive analysis
- **chad.md**: Deep review, best models, thorough analysis with alternatives

**Files**:
- `P:/__csf.nip/src/zen/templates/code_review/chill.md` (NEW)
- `P:/__csf.nip/src/zen/templates/code_review/mid.md` (NEW)
- `P:/__csf.nip/src/zen/templates/code_review/chad.md` (NEW)
- `P:/__csf.nip/src/zen/templates/code_review/security.md` (NEW)
- `P:/__csf.nip/src/zen/templates/code_review/performance.md` (NEW)
- `P:/__csf.nip/src/zen/templates/code_review/bugs.md` (NEW)
- `P:/__csf.nip/src/zen/templates/code_review/style.md` (NEW)
- `P:/__csf.nip/src/zen/lib/review_prompt_builder.py` (NEW)

### Phase 3: Mode Integration (1.5 hours)

**Tasks**:
1. Extend zen-consensus command argument parser
   - Add `--git-diff` flag with optional commit range
   - Add `--mode code_review_chill|code_review_mid|code_review_chad`
   - Add `--focus` flag for focus areas (security, performance, bugs, style)

2. Create `code_review_orchestrator.py`
   - `execute_code_review(diff, mode, focus, providers)` function
   - Mode-specific provider selection
   - Integration with zen-provider-manager
   - Parallel execution support

3. Update zen-consensus CLI routing
   - Detect code review mode
   - Route to code_review_orchestrator
   - Maintain backward compatibility

**Files**:
- `P:/__csf.nip/src/zen/orchestrator/code_review_orchestrator.py` (NEW)
- `P:/__csf.nip/src/zen/commands/zen_consensus.py` (MODIFY - add routing)

### Phase 4: Enhanced Consensus (1 hour)

**Tasks**:
1. Extend consensus aggregator for code review
   - Extract findings from LLM responses
   - Group findings by (file, line, category)
   - Calculate agreement levels (unanimous, strong, moderate, weak)
   - Resolve contradictions (highest severity wins)

2. Implement severity calculator
   - Weight severity by provider confidence
   - Aggregate severity across agreeing LLMs
   - Priority ranking (Critical > High > Medium > Low > Info)

3. Create output formatter
   - Markdown report with severity sections
   - JSON output for programmatic access
   - Consensus statistics and approval status

**Files**:
- `P:/__csf.nip/src/zen/lib/finding_aggregator.py` (NEW)
- `P:/__csf.nip/src/zen/lib/severity_calculator.py` (NEW)
- `P:/__csf.nip/src/zen/lib/review_output_formatter.py` (NEW)

### Phase 5: Testing (1 hour)

**Tasks**:
1. Unit tests
   - Test diff generation (various git scenarios)
   - Test diff parsing (edge cases)
   - Test prompt building (all modes and focus areas)
   - Test finding aggregation (consensus scenarios)

2. Integration tests
   - Test full code review workflow
   - Test multi-LLM consensus
   - Test provider fallbacks
   - Test error handling

3. E2E tests
   - Test with real git repos
   - Test various commit ranges
   - Test all modes (chill, mid, chad)
   - Validate output formats

**Files**:
- `P:/__csf.nip/tests/zen/test_code_review.py` (NEW)
- `P:/__csf.nip/tests/zen/test_diff_generation.py` (NEW)
- `P:/__csf.nip/tests/zen/test_finding_aggregation.py` (NEW)

## Mode Mappings

### Chill Mode (Quick Review)
- **Providers**: Mixtral, Llama 3.1, Gemma (free/fast)
- **Cost**: ~$0.001/review
- **Focus**: Critical security issues, obvious bugs
- **Output**: Brief findings, high confidence only

### Mid Mode (Standard Review)
- **Providers**: Claude 3.5 Sonnet, Gemini 1.5, Llama 3.1
- **Cost**: ~$0.01-0.02/review
- **Focus**: Security, performance, bugs, style (all areas)
- **Output**: Comprehensive findings with recommendations

### Chad Mode (Deep Review)
- **Providers**: Claude 3.5 Sonnet, GPT-4, Gemini, Mixtral 8x22b
- **Cost**: ~$0.05-0.10/review
- **Focus**: Deep analysis, alternative solutions, architectural review
- **Output**: Thorough findings with multiple options and rationale

## Integration Points

```
User CLI
  ↓
zen-consensus (argument parser)
  ↓
code_review_orchestrator (NEW)
  ↓
  ├─→ diff_generator (NEW)
  ├─→ review_prompt_builder (NEW)
  ├─→ zen-provider-manager (EXISTING)
  ├─→ multi-model-orchestrator (EXISTING)
  └─→ finding_aggregator (NEW)
      ↓
  review_output_formatter (NEW)
      ↓
  User Output (Markdown + JSON)
```

## Error Handling

| Error Type | Detection | Handling |
|------------|-----------|----------|
| Not a git repo | subprocess.CalledProcessError | Print error, exit gracefully |
| No git changes | Empty diff output | Inform user, exit with message |
| Invalid commit | Git returns error | Suggest valid commits, exit |
| Diff too large | Token count exceeds limit | Chunk by file, review separately |
| Provider API fails | API error/timeout | Fallback to backup provider |
| LLM response parse fails | Invalid JSON/malformed | Log error, use raw response |

## Success Criteria

- [ ] `/zen-consensus --git-diff HEAD~1` executes successfully
- [ ] Code review prompts generate high-quality reviews
- [ ] Consensus aggregation provides meaningful synthesis
- [ ] Chill/mid/chad modes work as specified
- [ ] Error handling graceful for all failure modes
- [ ] Tests pass (unit, integration, E2E)
- [ ] Documentation complete and clear

## Rollback Plan

If implementation fails or quality is insufficient:
1. Remove `--git-diff` flag from zen-consensus
2. Delete new modules (diff_*, review_*, finding_*)
3. Restore original zen-consensus.py from git
4. Document lessons learned

**Rollback Time**: <5 minutes (git revert)

## Configuration

**Default Settings** (in `P:/__csf.nip/config/zen-code-review.yml`):
```yaml
modes:
  chill:
    providers: ["mixtral", "llama-3.1", "gemma"]
    focus: ["security", "bugs"]
    context_lines: 3
    cost_target: 0.001

  mid:
    providers: ["claude-3.5-sonnet", "gemini-1.5", "llama-3.1"]
    focus: ["security", "performance", "bugs", "style"]
    context_lines: 5
    cost_target: 0.015

  chad:
    providers: ["claude-3.5-sonnet", "gpt-4", "gemini", "mixtral-8x22b"]
    focus: ["security", "performance", "bugs", "style", "architecture"]
    context_lines: 10
    cost_target: 0.075

consensus:
  agreement_threshold: 0.5  # 50% agreement for finding inclusion
  severity_mode: "highest"   # Use highest severity from agreeing LLMs
  tie_breaker: "confidence"  # Use confidence score for ties

git:
  default_range: "HEAD~1"
  context_lines: 5
  exclude_binary: true
  max_diff_size: 100000  # bytes
```

## Documentation

**User Documentation**:
- `P:/.claude/commands/zen-code-review.md` (NEW) - User-facing command docs
- Usage examples for all modes
- Configuration guide
- Troubleshooting section

**Developer Documentation**:
- Architecture diagrams
- API documentation for new modules
- Testing strategy
- Contributing guidelines

## Timeline

| Phase | Tasks | Duration | Dependencies |
|-------|-------|----------|--------------|
| 1 | Git Integration Layer | 1.5h | None |
| 2 | Prompt Templates | 1h | None (parallel) |
| 3 | Mode Integration | 1.5h | Phase 1, 2 |
| 4 | Enhanced Consensus | 1h | Phase 1, 2 |
| 5 | Testing | 1h | Phase 3, 4 |
| **Total** | | **6h** | |

## Next Steps

1. ✅ Review and approve this implementation plan
2. ⏭️ Execute Step 7: Task Decomposition (/quadlet)
3. ⏭️ Begin implementation (Step 8)

---

**Ready for task decomposition and implementation execution.**
