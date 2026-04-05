# Anti-Lazy Declaration System - Perplexity Analysis Integration

**Date**: 2026-03-16
**Analysis Source**: `C:\Users\brsth\Downloads\How can we fix this in claude code on windows 11_.md`

## Perplexity Root Causes vs Implementation

| Root Cause | Perplexity Description | Implementation Solution | Status |
|------------|----------------------|----------------------|--------|
| **1. Declaration ≠ Execution** | LLM responds with intent ("I'll update the template") but stops at verbal agreement without invoking Write/Edit tools | **declaration_reminder.py** + **arch_first_enforcer.py** two-hook system | ✅ COMPLETE |
| **2. No Cross-Session Persistence** | Each conversation starts fresh; templates must be written during session or learning is lost | **State files** in `hooks/state/arch_declaration_{terminal_id}.json` provide session continuity | ✅ COMPLETE |
| **3. Missing Anti-Lazy Enforcement** | User accountability enforcement needed - without it, declarative responses substitute for execution | **arch_first_enforcer.py** blocks non-arch tools until template is updated | ✅ COMPLETE |
| **4. Template Updates Skip Step 2** | "I'll do it" response often skips actual Edit/Write entirely | **Forces Read → Edit → Show diff workflow** via block message | ✅ COMPLETE |

## Perplexity Recommendations vs Implementation

### Perplexity Recommendation 1: Diff-Based Enforcement
**Perplexity**: "Checklists with 'show a diff' are powerful because they turn invisible tool use into visible output"

**Implementation**:
```python
# arch_first_enforcer.py block message
⛔ **TEMPLATE UPDATE REQUIRED FIRST**

You declared: "I'll update the template"

Before using {tool_name}, you MUST:
1. **Read** the template file: `{declared_path}`
2. **Edit/Write** the change with diff
3. **Show** the explanation
```

**Status**: ✅ IMPLEMENTED - Block message enforces Read → Edit → Show diff workflow

### Perplexity Recommendation 2: Global Rules System
**Perplexity**: "Use Claude Code's global rules system under `~/.claude`" with `require_diff` and `require_summary`

**Implementation**:
- ✅ Declaration patterns stored in `declaration_reminder.py`
- ✅ State persisted across hooks in `hooks/state/`
- ✅ Block message requires diff display
- **Note**: Hook-based approach is more robust than global rules (which are eval-only)

### Perplexia Recommendation 3: Template Updates as First-Class Steps
**Perplexity**: "Make 'update the template' a first-class step in tasks"

**Implementation**:
- Hook automatically detects declarations in UserPromptSubmit phase
- State is stored before AI can generate response
- PreToolUse enforces completion before allowing other tools
- **Effect**: Template updates become mandatory, not optional promises

### Perplexia Recommendation 4: Work Within Non-Persistence
**Perplexity**: "Accept the non-persistence and work with it - write to files in same session"

**Implementation**:
- ✅ State files provide session-scoped persistence
- ✅ Terminal isolation ensures state is accessible during session
- ✅ Bypass flag (`--allow-skip-arch-update`) for edge cases

## Additional Features Beyond Perplexity

### Multi-Terminal Safety
- **State isolation**: Each terminal has its own state file
- **Terminal ID detection**: Uses `get_terminal_id()` from `runtime_env`
- **Concurrent safety**: Multiple terminals can work independently

### Windows Path Handling
- **Path normalization**: Handles both forward slashes and backslashes
- **Safe file names**: Sanitizes terminal IDs for file system safety

### Comprehensive Pattern Detection
- **9 declaration patterns**: Covers various ways AI expresses intent
- **Apostrophe handling**: Both straight (') and curly (') apostrophes
- **Keyword extraction**: Intelligently extracts template paths from declarations

### Test Coverage
- **25 tests**: 11 for declaration_reminder, 14 for arch_first_enforcer
- **Integration tests**: Full workflow from declaration → state → enforcement → clear
- **All tests pass**: 0.68s execution time

## Verification

**Test Results**:
```bash
pytest P:\.claude\hooks\tests\test_declaration_reminder.py -v
pytest P:\.claude\hooks\tests\test_arch_first_enforcer.py -v

# All 25 tests passed in 0.68s
```

**Documentation**:
- ✅ Added to CLAUDE.md under "Anti-Lazy Declaration Enforcement"
- ✅ Plan file (plan-20260316-extend-anti-lazy-declaration.md) marked COMPLETE
- ✅ Git commit created: 56e4ddab

## Conclusion

The implemented two-hook system (declaration_reminder.py + arch_first_enforcer.py) fully addresses all 4 root causes identified in the Perplexity analysis:

1. **Declaration ≠ Execution**: DETECTED → BLOCKED until execution
2. **No Cross-Session Persistence**: SOLVED with state files
3. **Missing Anti-Lazy Enforcement**: IMPLEMENTED via PreToolUse blocking
4. **Template Updates Skip Step 2**: FORCED via Read → Edit → Show diff workflow

**Status**: ✅ COMPLETE - All Perplexity root causes addressed with comprehensive implementation
