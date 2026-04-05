# Implementation Plan: Zen Suggestion Hook

## Task: TSK-251230-1639-zen-hook
**Date**: 2025-12-30
**Status**: Implementation Plan Complete

---

## 1. Implementation Strategy

### 1.1 Phased Approach

```
PHASE 1: Core Hook (Days 1-2)
├─ Create configuration file with initial patterns
├─ Implement ZenSuggestionHook class
├─ Implement Tier 1 pattern detection
├─ Register hook in settings.json
└─ Verify basic functionality

PHASE 2: Refinement (Days 3-5)
├─ Add Tier 2 patterns
├─ Implement context fallback analysis
├─ Add suggestion caching
├─ Implement logging
└─ Fine-tune regex patterns

PHASE 3: Production (Week 2)
├─ Monitor logs for actual usage patterns
├─ Adjust patterns based on real behavior
├─ Document in .claude/CLAUDE.md
└─ Finalize pattern library
```

### 1.2 Development Order

```
1. Configuration File
   └─ Reason: Defines data structure, drives code design

2. Hook Class (Core)
   ├─ __init__
   ├─ _load_config
   ├─ detect_zen_patterns
   └─ main entry point

3. Pattern Matching
   ├─ _matches_pattern
   └─ Tier 1 patterns

4. Context Analysis
   ├─ analyze_context
   ├─ _is_circular_discussion
   └─ _is_architecture_refinement

5. Suggestion Cache
   ├─ should_skip_suggestion
   └─ record_suggestion

6. Logging
   └─ log_event

7. Hook Registration
   └─ settings.json modification

8. Testing
   ├─ Unit tests
   ├─ Integration tests
   └─ Manual verification
```

---

## 2. File Creation Plan

### 2.1 Files to Create

| File | Purpose | Lines (est) |
|------|---------|-------------|
| `P:/.claude/config/zen_suggestions.json` | Pattern library | ~60 |
| `P:/.claude/hooks/zen_suggestion.py` | Hook implementation | ~250 |
| `P:/.claude/tests/test_zen_suggestion.py` | Unit tests | ~80 |

### 2.2 Files to Modify

| File | Modification | Lines (change) |
|------|--------------|----------------|
| `P:/.claude/settings.json` | Hook registration | +15 |

---

## 3. Detailed Implementation Tasks

### Task 3.1: Create Configuration File

**File**: `P:/.claude/config/zen_suggestions.json`

**Actions**:
1. Create directory if needed: `P:/.claude/config/`
2. Create JSON file with structure:
   - `enabled`: true
   - `min_confidence`: "HIGH"
   - `context_lookback_turns`: 3
   - `recent_suggestion_cache_seconds`: 30
   - `patterns`: { tier1: [...], tier2: [...] }

**Tier 1 Patterns** (initial set):
```json
[
  {
    "name": "architecture_decision",
    "regex": "(should|whether to).*(microservices|monolith|sql|nosql|sync|async|rest|grpc)",
    "suggestion": "/zen-debate",
    "confidence": "HIGH"
  },
  {
    "name": "stuck_blocked",
    "regex": "(stuck|blocked|unclear|unsure|uncertain).*(how|what|where|why)",
    "suggestion": "/zen-meditate",
    "confidence": "HIGH"
  },
  {
    "name": "code_review",
    "regex": "(review|examine|look at|check).*(code|changes|diff|logic)",
    "suggestion": "/zen-code-review",
    "confidence": "HIGH"
  },
  {
    "name": "architecture_choice",
    "regex": "(architecture|design|pattern|system).*(decision|choice|approach)",
    "suggestion": "/zen-debate",
    "confidence": "HIGH"
  }
]
```

**Tier 2 Patterns** (initial set):
```json
[
  {
    "name": "high_complexity",
    "regex": "(complex|multiple factors|trade-off|tradeoff|many considerations)",
    "suggestion": "/zen-thinkdeep",
    "confidence": "MEDIUM"
  },
  {
    "name": "critical_decision",
    "regex": "(critical|production|urgent|blocking).*(decision|choice|change)",
    "suggestion": "/zen-debate --comprehensive",
    "confidence": "MEDIUM"
  }
]
```

### Task 3.2: Create Hook Implementation

**File**: `P:/.claude/hooks/zen_suggestion.py`

**Structure**:
```python
#!/usr/bin/env python3
"""
Zen Suggestion Hook - Suggests zen commands at decision points
Event: UserPromptSubmit
Behavior: Non-blocking, outputs suggestion if pattern matches
"""

import json
import re
import sys
from collections import deque
from datetime import datetime, UTC
from pathlib import Path
from typing import Optional, List

# Constants
DEFAULT_CONFIG_PATH = "P:/.claude/config/zen_suggestions.json"
LOG_FILE = Path("P:/.claude/logs/zen_suggestions.json")
CACHE_SIZE = 5
CACHE_COOLDOWN_SECONDS = 30


class ZenSuggestionHook:
    """Detects decision points and suggests zen commands."""

    def __init__(self, config_path: str = DEFAULT_CONFIG_PATH):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.suggestion_cache = deque(maxlen=CACHE_SIZE)
        self.suggestion_timestamps = {}
        self._compiled_patterns = {}
        if self.config.get("enabled", False):
            self._compile_patterns()

    def _load_config(self) -> dict:
        """Load configuration with fallback to defaults."""
        # Implementation...

    def _compile_patterns(self):
        """Pre-compile regex patterns for performance."""
        # Implementation...

    def detect_zen_patterns(self, message: str) -> Optional[str]:
        """Detect high-confidence zen patterns in current message."""
        # Implementation...

    def _matches_pattern(self, text: str, pattern_config: dict) -> bool:
        """Check if text matches pattern."""
        # Implementation...

    def analyze_context(self, messages: List[str]) -> Optional[str]:
        """Analyze last 2-3 messages for weak signals."""
        # Implementation...

    def _is_circular_discussion(self, messages: List[str]) -> bool:
        """Detect if same question is being asked multiple ways."""
        # Implementation...

    def _is_architecture_refinement(self, messages: List[str]) -> bool:
        """Check if previous turns discussed architecture."""
        # Implementation...

    def should_skip_suggestion(self, suggestion: str) -> bool:
        """Check if suggestion was recently given."""
        # Implementation...

    def record_suggestion(self, suggestion: str):
        """Record that a suggestion was made."""
        # Implementation...

    def log_event(self, prompt: str, suggestion: Optional[str], tier: str = "none"):
        """Log all zen suggestion attempts."""
        # Implementation...

    def process_message(
        self,
        message: str,
        context_messages: Optional[List[str]] = None
    ) -> Optional[str]:
        """Main entry point - returns suggestion or None."""
        # Implementation...


def main():
    """Hook entry point - receives JSON from Claude Code."""
    # Implementation...


if __name__ == "__main__":
    main()
```

### Task 3.3: Register Hook

**File**: `P:/.claude/settings.json`

**Action**: Add to `UserPromptSubmit` hooks array:

```json
{
  "matcher": ".*",
  "hooks": [
    {
      "type": "command",
      "command": "python P:/.claude/hooks/zen_suggestion.py",
      "timeout": 1,
      "layer": "1f_zen_suggestions",
      "critical": false,
      "description": "Layer 1f: Suggest zen commands at decision points",
      "exit_code_error_handling": "non_blocking"
    }
  ]
}
```

**Location**: After Layer 1e (debug_guidance), at the end of UserPromptSubmit array

### Task 3.4: Create Unit Tests

**File**: `P:/.claude/tests/test_zen_suggestion.py`

**Test Cases**:
```python
def test_architecture_decision():
    """Verify architecture decision triggers /zen-debate."""
    hook = ZenSuggestionHook()
    result = hook.detect_zen_patterns("Should I use microservices or monolith?")
    assert result == "/zen-debate"

def test_stuck_unclear():
    """Verify stuck/unclear triggers /zen-meditate."""
    hook = ZenSuggestionHook()
    result = hook.detect_zen_patterns("I'm stuck on how to proceed")
    assert result == "/zen-meditate"

def test_code_review():
    """Verify code review triggers /zen-code-review."""
    hook = ZenSuggestionHook()
    result = hook.detect_zen_patterns("Can you review my code changes?")
    assert result == "/zen-code-review"

def test_no_match_generic():
    """Verify generic queries don't trigger."""
    hook = ZenSuggestionHook()
    result = hook.detect_zen_patterns("What's in this directory?")
    assert result is None

def test_context_circular():
    """Verify circular discussion detection."""
    hook = ZenSuggestionHook()
    messages = ["Should I use X?", "What about Y?", "How do I decide?"]
    result = hook.analyze_context(messages)
    assert result == "/zen-meditate"

def test_cache_prevents_repetition():
    """Verify cache prevents suggestion repetition."""
    hook = ZenSuggestionHook()
    hook.record_suggestion("/zen-debate")
    assert hook.should_skip_suggestion("/zen-debate") == True
```

---

## 4. Validation Checklist

### 4.1 Pre-Deployment Validation

```
[ ] Syntax Check
    [ ] python -m py_compile zen_suggestion.py passes
    [ ] JSON validation for zen_suggestions.json

[ ] Configuration
    [ ] Config file loads without errors
    [ ] All regex patterns compile successfully
    [ ] Default config used when file missing

[ ] Pattern Detection
    [ ] Architecture decision → /zen-debate
    [ ] Stuck/unclear → /zen-meditate
    [ ] Code review → /zen-code-review
    [ ] Generic query → None (silent)

[ ] Context Analysis
    [ ] Circular discussion detected
    [ ] Architecture refinement detected
    [ ] Cache prevents repetition

[ ] Hook Registration
    [ ] Hook registered in settings.json
    [ ] Layer ordering correct (1f)
    [ ] Timeout set to 1000ms
    [ ] Non-blocking exit configured

[ ] Logging
    [ ] Log file created on first execution
    [ ] JSON entries are parseable by jq
    [ ] Timestamps in ISO format
    [ ] Both matched and unmatched events logged

[ ] Performance
    [ ] Execution time < 100ms (average)
    [ ] Regex patterns cached
    [ ] No memory leaks

[ ] Error Handling
    [ ] Invalid JSON input handled gracefully
    [ ] Missing config file handled gracefully
    [ ] Invalid regex skipped with warning
    [ ] All errors go to stderr, never block
```

### 4.2 Post-Deployment Validation

```
[ ] Functional Testing
    [ ] Hook executes on every UserPromptSubmit
    [ ] Suggestions appear for matched patterns
    [ ] No output for unmatched patterns
    [ ] Exit code always 0

[ ] Integration Testing
    [ ] Works alongside existing hooks
    [ ] Doesn't interfere with CKS integration
    [ ] Doesn't interfere with debug guidance

[ ] User Acceptance
    [ ] Suggestions are helpful (not spam)
    [ ] Suggestion rate ~20-30%
    [ ] Easy to disable if needed
```

---

## 5. Rollout Plan

### 5.1 Phase 1 Rollout (Immediate)

1. Create configuration file
2. Implement hook with Tier 1 patterns only
3. Register hook
4. Test with 20 sample messages
5. Monitor logs for suggestion rate

**Success Criteria**:
- Hook loads without errors
- Tier 1 patterns trigger correctly
- No false positives on generic queries

### 5.2 Phase 2 Rollout (Days 3-5)

1. Add Tier 2 patterns
2. Implement context analysis
3. Add suggestion caching
4. Test with 50+ messages
5. Fine-tune regex patterns

**Success Criteria**:
- Context analysis catches weak signals
- Cache prevents repetition
- Suggestion rate remains ~20-30%

### 5.3 Phase 3 Rollout (Week 2)

1. Monitor logs in real usage
2. Adjust patterns based on behavior
3. Add new patterns as discovered
4. Document in CLAUDE.md

**Success Criteria**:
- 80%+ of zen moments captured
- Minimal false positives
- Easy pattern evolution

---

## 6. Risk Mitigation

### 6.1 Identified Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Pattern too broad | Medium | High | Start conservative, monitor logs |
| Syntax errors | Low | High | Verify with py_compile before use |
| Hook timeout | Low | Medium | Cache regex, limit lookback |
| False positives | Medium | Medium | Require multiple keywords |
| Cache too aggressive | Low | Low | Tunable cooldown parameter |

### 6.2 Rollback Plan

**If issues occur**:

1. **Immediate disable**: Set `"enabled": false` in config
2. **Comment out**: Remove hook from settings.json
3. **Delete file**: Graceful degradation (hook not found)

**No service disruption**: Non-blocking exit ensures CC continues working

---

## 7. Success Metrics

### 7.1 Quantitative Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Suggestion rate | 20-30% | `jq -s 'map(select(.matched)) | length / length' logs` |
| Execution time | < 100ms | Manual timing during development |
| Hook load success | 100% | No stderr errors on startup |
| Pattern coverage | 80%+ | Manual review of zen moments |

### 7.2 Qualitative Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Signal value | High | No spam complaints |
| Coverage | Broad | Most zen moments captured |
| Usability | Easy | Can disable/modify without code |

---

## 8. Dependencies

### 8.1 Internal Dependencies

- `P:/.claude/settings.json` - Hook registration
- Existing hook patterns (for consistency)
- Python 3.11+ runtime

### 8.2 External Dependencies

- None (stdlib only)

---

## 9. Timeline

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| Phase 1 | Days 1-2 | Core hook with Tier 1 patterns |
| Phase 2 | Days 3-5 | Full hook with context + cache |
| Phase 3 | Week 2 | Production refinement + docs |

**Total Estimated Time**: 7-10 days for complete implementation

---

## Implementation Plan Status

| Section | Status |
|---------|--------|
| Implementation Strategy | ✅ |
| File Creation Plan | ✅ |
| Detailed Implementation Tasks | ✅ |
| Validation Checklist | ✅ |
| Rollout Plan | ✅ |
| Risk Mitigation | ✅ |
| Success Metrics | ✅ |
| Dependencies | ✅ |
| Timeline | ✅ |

**Implementation Plan**: ✅ COMPLETE

**Ready for**: Step 6 - Task Decomposition

---
