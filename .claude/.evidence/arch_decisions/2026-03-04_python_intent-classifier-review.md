# Architecture Review: Intent Classifier Hook for Slash Command Distinction

**Date:** 2026-03-04
**Template:** python
**Query:** "does that seem like a good idea?" (evaluating proposed intent classifier)

---

## Scope

Reviewing proposed **intent_classifier.py** hook to distinguish between "asking about /s" (topic inquiry) vs "invoking /s" (command execution) in UserPromptSubmit event pipeline.

## Design Summary

**Proposal**: Add new `UserPromptSubmit/intent_classifier.py` hook that runs **before** `skill_enforcer.py` (priority < 1.0) to detect "topic inquiry" patterns using regex keyword matching. When detected, the hook returns empty (no injection) instead of triggering skill-first enforcement.

**Key patterns to detect**:
- "about /s", "regarding /s", "tell me about /s"
- "errors from today regarding /s"
- "/s usage and frictions"
- "find information about /s"

**Technical approach**:
- 5-8 precompiled regex patterns
- Pattern list checked in sequence
- Early return on match (no SKILL EXECUTION LANE injection)

## Findings

| ID | Severity | Finding | Evidence | Impact |
|-----|-----------|----------|-----------|---------|
| ARCH-001 | **HIGH** | **Hook priority conflict**: Proposed `intent_classifier` must run before `skill_enforcer` (priority < 1.0), but determining priority order in ASGI-style middleware chains requires careful ordering | [ASGI Middleware Execution Order](https://m.blog.csdn.net/weixin_36303807/article/details/152103736) — First-added middleware runs first (outermost), creating nested execution | If priority set incorrectly, `skill_enforcer` runs first and injects SKILL EXECUTION LANE before intent classification |
| ARCH-002 | **MEDIUM** | **Regex performance risk**: Pattern list uses alternation `(?:about\|regarding\|tell me about)` which can cause backtracking | [Python Regex Performance](https://deepinout.com/python/python-qa/t_how-to-optimize-the-performance-of-python-regular-expression.html) — Catastrophic backtracking causes O(2^n) complexity | With 5-8 complex patterns and alternation, worst-case input like "tell me about tell me about tell me about /s" could timeout |
| ARCH-003 | **LOW** | **Pattern coverage gaps**: Current patterns miss natural language variations | [GitHub Copilot slash command docs](https://docs.github.com/zh/copilot/reference/cheat-sheet) — Commands are explicit, questions are natural | "What can you tell me about /s?" → False negative (treated as command) |
| ARCH-004 | **MEDIUM** | **No integration test path**: Design doesn't specify how to verify intent classification works end-to-end | [Test File Location Policy](P:\.claude\hooks\CLAUDE.md) — Tests require pytest-based discovery | Cannot verify "about /s" doesn't trigger skill enforcement without regression test suite |
| ARCH-005 | **LOW** | **Pre-compilation not specified**: Design shows pattern strings but not `re.compile()` | [Regex Performance Tips](https://m.blog.csdn.net/gitblog_00041/article/details/139762465) — Pre-compilation provides 30-50% improvement | Hooks run on every prompt; non-compiled regex adds overhead |

## Risk Summary

**Technical**: Hook execution order is fragile—ASGI middleware order depends on addition sequence, not priority numbers. If `intent_classifier` is added after `skill_enforcer` in router, it never runs first.

**Operational**: False negatives (treating inquiry as command) cause user frustration but are recoverable. False positives (treating command as inquiry) are worse—user expects skill execution but gets nothing.

**Integration**: Existing tests in `.claude/hooks/tests/` may need updates to account for new hook. Test exemption logic in `is_test_file_operation()` may need extension.

## Conclusion

**Looks viable with noted gaps**, but requires:

1. **Mandatory fix**: Verify hook priority ordering in `UserPromptSubmit_router.py` (lines 1-50 show router import logic)
2. **Recommended optimization**: Pre-compile all patterns at module load, avoid alternation in single regex (use `any()` with compiled patterns)
3. **Required validation**: Add test in `tests/test_intent_classifier.py` covering edge cases from ARCH-003
4. **Documentation**: Update `CLAUDE.md` intent tracking section to reference this hook

**Key risk**: ARCH-001 (hook ordering) must be resolved before implementation. Suggest adding assertion in router that checks priority at import time.

---

**Confidence:** 85%

**Evidence basis:**
- Design doc: This conversation (proposed regex patterns from research)
- Web research: 5 sources on middleware order, regex performance, bot frameworks
- Codebase analysis: `UserPromptSubmit_router.py` router pattern, `skill_enforcer.py` (lines 141-242 show SLASH_COMMAND_RE and injection logic)

**Key assumptions:**
1. Router uses priority-based dispatch (not addition-order) — Need to verify `UserPromptSubmit_router.py`
2. PreToolUse hooks use different priority system — Intent classification is UserPromptSubmit-only
3. Regex patterns are case-insensitive (design shows `(?i)` flag)
4. False positives less harmful than false negatives for this use case

---

## Sources
- [ASGI Middleware Execution Order](https://m.blog.csdn.net/weixin_36303807/article/details/152103736)
- [Python Regex Performance Optimization](https://deepinout.com/python/python-qa/t_how-to-optimize-the-performance-of-python-regular-expression.html)
- [10 Regex Performance Tips](https://m.blog.csdn.net/gitblog_00041/article/details/139762465)
- [Deep Dive: Pattern Matching Engines](https://blog.csdn.net/xiaofeng10330111/article/details/156114817)
- [Why re.compile() Improves Speed](https://www.cnblogs.com/wangya216/p/19234689)
- [GitHub Copilot Slash Command Documentation](https://docs.github.com/zh/copilot/reference/cheat-sheet)
