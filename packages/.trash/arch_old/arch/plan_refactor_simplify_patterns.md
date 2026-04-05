# Plan: Transfer /simplify Patterns to /refactor

## Overview

Add three transferable patterns from `/simplify` to the `/refactor` skill specification to prevent unnecessary extractions and catch efficiency issues. This is a documentation-only change to the skill's workflow specification.

## Architecture

**Module structure:** Single file modification
- `P:/.claude/skills/refactor/SKILL.md` — Add new agent specifications

**Key components:**
1. Agent 5 (code-reuse) — New agent for existing utility detection
2. Agent 2 extension — Add concurrency analysis scope
3. Agent 1 extension — Add TOCTOU pattern detection

## Data Flow

```
User invokes /refactor
    ↓
DISCOVER phase launches agents (now 5 agents total)
    ├─ Agent 1: adversarial-compliance (+ TOCTOU detection)
    ├─ Agent 2: adversarial-performance (+ concurrency analysis)
    ├─ Agent 3: adversarial-quality
    ├─ Agent 4: python-simplifier
    └─ Agent 5: code-reuse (NEW)
    ↓
Findings aggregated
    ↓
CONSTITUTIONAL FILTER applied
    ↓
TDD → TEST → AUDIT → TRACE → DONE
```

## Error Handling

**Documentation changes only** — No runtime code to handle. The skill specification is a markdown document that guides execution; errors would occur during skill invocation (handled by Claude Code runtime).

## Test Strategy

**Documentation validation:**
- Positive: Verify new agent specifications are present and complete
- Negative: Verify no contradictions with existing /refactor patterns
- Edge cases: Constitutional filter interaction with new agents

**Since this is documentation-only:**
- No executable tests needed
- Verification via grep/read of updated file
- Manual review of specification consistency

## Standards Compliance

**Markdown documentation:**
- Follow existing /refactor SKILL.md formatting
- Maintain consistent indentation and structure
- Use existing agent specification format

**No code standards apply** (documentation change)

## Ramifications

**Impact on existing code:** None (documentation-only change)

**Breaking changes:** None (additive only)

**Backwards compatibility:** Full — existing /refactor workflows unchanged

**Future considerations:** These patterns guide future /refactor implementations

## Pre-Mortem Analysis

**Failure Mode 1: New agents conflict with constitutional filter**
- Root cause: Agent recommendations violate solo-dev constraints
- Prevention: Add explicit constitutional filter note to each new agent
- Test: Review each new agent against SOLO_DEV_CONSTRAINTS

**Failure Mode 2: Agent 5 (code-reuse) not actionable**
- Root cause: Agent finds existing utilities but provides no clear migration path
- Prevention: Specify agent outputs "use existing utility X" with file paths
- Test: Manual review of agent specification for clarity

**Failure Mode 3: Concurrency analysis misses obvious opportunities**
- Root cause: Agent 2 scope too narrow, misses async/await patterns
- Prevention: Explicitly include "async/await, ThreadPoolExecutor, ProcessPoolExecutor" in scope
- Test: Review python codebase for common concurrency patterns

## Observability Planning

**What to monitor:**
- How often Agent 5 (code-reuse) triggers vs. extraction suggestions
- Concurrency findings rate vs. total findings
- TOCTOU detection rate in Python file operations

**Where to look:**
- Manual /refactor invocations (review findings)
- Agent specification review (validate patterns are actionable)

**Alert thresholds:** None (manual skill invocation only)

## Tasks

### Task 1: Add Agent 5 (code-reuse) Specification
**Location:** Line ~230 in SKILL.md (after Agent 4 specification)

**Add new agent section:**
```markdown
   - **For Python**: Add `python-simplifier` (assessment mode) as Agent 4 for Python-specific standards. Runs in parallel with the other 3 agents.
   - **Agent 5 (NEW)**: `code-reuse` — Searches for existing utilities and helpers before suggesting extraction
```

**Full specification in Agent prompt section:**
- Purpose: Check existing utilities before recommending new abstractions
- Scope: Search utility directories, shared modules, adjacent files
- Output format: "Use existing utility: `path/to/module.py:function_name`"

### Task 2: Extend Agent 2 with Concurrency Analysis
**Location:** Line ~230 in SKILL.md (Agent 2 specification)

**Extend Agent 2 scope:**
- Add to adversarial-performance agent responsibilities:
  - "Missed concurrency: independent operations run sequentially when they could run in parallel"
  - "Sequential file operations that could use asyncio/aiofiles"
  - "Loop iterations that could use concurrent.futures"

### Task 3: Extend Agent 1 with TOCTOU Detection
**Location:** Line ~228 in SKILL.md (Agent 1 specification)

**Extend Agent 1 scope:**
- Add to adversarial-compliance agent responsibilities:
  - "Unnecessary existence checks: pre-checking file/resource existence before operating (TOCTOU anti-pattern)"
  - "Race conditions from separate exists() + read/write operations"

## Implementation Order

1. **Task 1** — Add Agent 5 specification (highest value, prevents duplicate utilities) ✅ COMPLETE
2. **Task 2** — Extend Agent 2 with concurrency analysis (enables performance refactorings) ✅ COMPLETE
3. **Task 3** — Extend Agent 1 with TOCTOU detection (removes race conditions) ✅ COMPLETE

**Estimated effort:** 30 minutes (documentation review + edits)

## Implementation Status

✅ **ALL TASKS COMPLETE**

**Changes made to `P:/.claude\skills\refactor\SKILL.md`:**

1. **Agent 5 (code-reuse) added** — Searches for existing utilities before suggesting extraction
   - Searches: Standard library, project utils/, adjacent modules, existing abstractions
   - Output format: "Use existing utility: `path/to/module.py:function_name`"
   - Constitutional filter: Must verify utility exists, must not suggest creating new shared modules

2. **Agent 2 extended** — Added concurrency analysis to adversarial-performance scope
   - Detects: Sequential file I/O in loops, serial API calls, CPU-bound loops
   - Recommends: `asyncio.gather()`, `ThreadPoolExecutor`, `ProcessPoolExecutor`
   - Constitutional filter: Must prefer built-in concurrency, no background services

3. **Agent 1 extended** — Added TOCTOU pattern detection to adversarial-compliance scope
   - Detects: `os.path.exists()` + `open()` race conditions, pre-checks before operations
   - Recommends: Exception handling (try/except) over existence checks
   - Priority: All TOCTOU findings are P0 (security/safety issues)

**Verification:**
- Modified DISCOVER phase agent list from "3 parallel Task agents" to "5 parallel Task agents"
- Added inline scope descriptions for TOCTOU (Agent 1) and concurrency (Agent 2)
- Maintains constitutional filter compliance throughout
- No breaking changes (additive only)
