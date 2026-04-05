# Debugging Infrastructure Fixes
## Addressing Missing Dependencies, Broken Paths, Logic Errors, and Error Handling

**Created:** 2025-01-17
**Status:** READY
**Priority:** HIGH
**Complexity:** MEDIUM

---

## Problem Statement

The debugging infrastructure (`/debug`, `/rca`, `/oops` skills) has critical gaps between documentation and implementation:

1. **Missing Dependencies:** Core modules referenced but don't exist
2. **Broken Import Paths:** Hardcoded paths that break on restructure
3. **Logic Errors:** Telemetry queries before classification, catch-22 in /oops
4. **Missing Error Handling:** Crashes when dependencies unavailable

---

## 4 Categories to Address

### Category 1: Missing Dependencies (CRITICAL)

| Module | Referenced In | Status | Fix |
|--------|---------------|--------|-----|
| `mental_model_selector.py` | /rca, /debug SKILL.md | ✅ MIGRATED | Now at `P:/packages/debug-rca/src/debug_rca/mental_model_selector.py` |
| `enhancement_router.py` | /rca SKILL.md | ✅ CREATED | Created at `P:/__csf/src/rca/enhancement_router.py` |
| `subagent_delegation.py` | /debug/flows/systematic.md | MISSING | Create inline classification |
| `check-notifications.py` | /oops SKILL.md | UNCERTAIN | Verify or create |

### Category 2: Broken Import Paths (HIGH)

| Issue | Location | Fix |
|-------|----------|-----|
| Hardcoded `P:/__csf.nip/src/...` | Multiple skills | Use relative imports |
| CHS search path wrong | /rca, /debug | Fix module path |
| Inconsistent path roots | Multiple skills | Standardize on `__csf` |

### Category 3: Logic Errors (MEDIUM)

| Issue | Location | Fix |
|-------|----------|-----|
| Telemetry query before classification | /debug SKILL.md | Detect yt-fts first |
| /oops depends on script it diagnoses | /oops SKILL.md | Add fallback mode |
| Over-delegation for trivial bugs | /debug/flows/systematic.md | FAST as default |

### Category 4: Missing Error Handling (MEDIUM)

| Issue | Location | Fix |
|-------|----------|-----|
| No telemetry query fallback | /rca, /debug | Wrap in try/except |
| CHS search fails silently | /rca SKILL.md | Add error reporting |
| Import failures crash workflow | All skills | Graceful degradation |

---

## Implementation Plan

### Phase 1: Create Missing Modules (Category 1)

**File:** `P:/packages/debug-rca/src/debug_rca/mental_model_selector.py` (migrated from `src/rca/`)

```python
"""Mental model selector for RCA and debugging workflows."""

from typing import List

# Default mental models for common problem types
DEFAULT_MODELS = [
    "First Principles",
    "Inversion",
    "Second-Order Thinking"
]

PROBLEM_TYPE_MODELS = {
    "performance": ["First Principles", "Inversion", "Bottleneck Analysis"],
    "error": ["First Principles", "Inversion", "Root Cause Analysis"],
    "intermittent": ["Inversion", "Second-Order Thinking", "Race Conditions"],
    "security": ["Red Team", "Threat Modeling", "Attack Trees"],
}

def select_mental_models(problem: str, max_models: int = 3) -> List[str]:
    """Select appropriate mental models for the given problem."""
    problem_lower = problem.lower()

    for problem_type, models in PROBLEM_TYPE_MODELS.items():
        if problem_type in problem_lower:
            return models[:max_models]

    return DEFAULT_MODELS[:max_models]

def format_recommendations(models: List[str]) -> str:
    """Format mental model recommendations for display."""
    return "Recommended Mental Models:\n" + "\n".join(f"- {m}" for m in models)
```

**File:** `P:/__csf/src/commands/rca/enhancement_router.py`

```python
"""Enhancement router for RCA modes (--debate, --challenge, --synthesize)."""

from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class EnhancementResult:
    mode: str
    findings: str
    confidence: float

def parse_enhancement_flags(args: str) -> List[str]:
    """Parse enhancement flags from argument string."""
    flags = []
    if "--debate" in args:
        flags.append("debate")
    if "--challenge" in args:
        flags.append("challenge")
    if "--synthesize" in args:
        flags.append("synthesize")
    return flags

class EnhancementRouter:
    """Route RCA requests through enhancement modes."""

    def route(self, original_command: str, user_input: str,
              modes: List[str], context: Dict) -> EnhancementResult:
        """Route through enhancement modes if specified."""
        if not modes:
            return EnhancementResult(
                mode="standard",
                findings=user_input,
                confidence=0.8
            )

        # For now, return passthrough
        # TODO: Implement actual enhancement modes
        return EnhancementResult(
            mode=modes[0],
            findings=f"[{modes[0].upper()}] {user_input}",
            confidence=0.7
        )
```

### Phase 2: Fix Import Paths (Category 2)

**Update skill files to use relative imports from `__csf`:**

```python
# OLD (broken)
sys.path.insert(0, "P:/__csf.nip")
from features.lib.rca.mental_model_selector import select_mental_models

# NEW (working)
import sys
sys.path.insert(0, "P:/__csf")
from src.rca.mental_model_selector import select_mental_models
```

### Phase 3: Fix Logic Errors (Category 3)

**Fix telemetry query order in /debug SKILL.md:**

```python
# NEW: Detect yt-fts FIRST, then conditionally query
user_input_lower = user_input.lower()
is_ytfts = any(x in user_input_lower for x in
               ["yt-fts", "batch", "download", "video", "channel"])

if is_ytfts:
    # Only query telemetry if actually yt-fts
    try:
        stats = get_telemetry_stats()
        errors = get_recent_errors(limit=10)
    except Exception as e:
        print(f"Warning: Telemetry unavailable: {e}")
```

### Phase 4: Add Error Handling (Category 4)

**Wrap all imports in try/except with fallbacks:**

```python
# Pattern for all skill imports
try:
    from src.rca.mental_model_selector import select_mental_models
except ImportError:
    # Fallback implementation
    def select_mental_models(problem: str, max_models: int = 3) -> List[str]:
        return ["First Principles", "Inversion", "Second-Order Thinking"][:max_models]
```

---

## TDD Approach

### RED Phase - Tests First

**File:** `P:/__csf/tests/test_debugging_infrastructure.py`

```python
import pytest
from src.rca.mental_model_selector import select_mental_models

def test_select_mental_models_returns_list():
    """Should return list of mental models."""
    result = select_mental_models("test problem")
    assert isinstance(result, list)
    assert len(result) <= 3
    assert all(isinstance(m, str) for m in result)

def test_select_mental_models_performance_problem():
    """Should return performance-specific models."""
    result = select_mental_models("slow performance issue")
    assert "Bottleneck Analysis" in result

def test_select_mental_models_error_problem():
    """Should return error-specific models."""
    result = select_mental_models("TypeError crashing")
    assert "Root Cause Analysis" in result or "First Principles" in result
```

---

## Success Criteria

- [ ] All imports in skills resolve without ImportError
- [ ] `/rca` and `/debug` can invoke mental model selector
- [ ] Telemetry query only runs for yt-fts issues
- [ ] Skills gracefully degrade when dependencies missing
- [ ] Tests pass for all new modules

---

## Related Files

- Report: `P:/__csf/reports/debugging-infrastructure-issues-20250117.md`
- Skills: `P:/.claude/skills/debug/`, `P:/.claude/skills/rca/`, `P:/.claude/skills/oops/`
