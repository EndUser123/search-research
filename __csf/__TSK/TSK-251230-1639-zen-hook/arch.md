# Architecture Analysis: Zen Suggestion Hook

## Task: TSK-251230-1639-zen-hook
**Date**: 2025-12-30
**Status**: Architecture Complete

---

## 1. System Overview

### 1.1 Purpose

The Zen Suggestion Hook is a behavioral pattern detection system that suggests zen commands at critical decision points in user-AI conversations. It operates deterministically on every message while maintaining selective output to avoid spam.

### 1.2 Design Philosophy

| Principle | Implementation |
|-----------|----------------|
| **Deterministic Execution** | Hook runs on 100% of UserPromptSubmit events |
| **Selective Output** | Suggestions appear on only 20-30% of messages |
| **Non-Blocking** | Always exits with code 0, never interrupts workflow |
| **Configuration-Driven** | Patterns defined in JSON, not hardcoded |
| **Observable** | All executions logged to JSON for analysis |

### 1.3 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER SUBMITS MESSAGE                        │
└──────────────────────────────────────┬──────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    CLAUDE CODE HOOK SYSTEM                          │
│                     UserPromptSubmit Event                          │
└──────────────────────────────────────┬──────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     LAYER 0-1E: EXISTING HOOKS                      │
│  [Diagnostics] → [Prompt Tracker] → [Command Directive]            │
│  → [Goal Anchor] → [ADF Trigger] → [Anti-Sycophancy]               │
│  → [CKS Integration] → [Debug Guidance]                             │
└──────────────────────────────────────┬──────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  LAYER 1F: ZEN SUGGESTION HOOK                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  1. INPUT PARSING                                           │   │
│  │     - Read JSON from stdin                                  │   │
│  │     - Extract prompt, context_messages                      │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│                              ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  2. CONFIG LOADING                                          │   │
│  │     - Load zen_suggestions.json                            │   │
│  │     - Fallback to defaults if missing                       │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│                              ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  3. PRIMARY ANALYSIS (Current Message)                      │   │
│  │     ┌──────────────────────────────────────────────┐        │   │
│  │     │ Tier 1 Patterns (HIGH confidence)            │        │   │
│  │     │ - Architecture decision: should + (micro|mono)│        │   │
│  │     │ - Stuck/Unclear: stuck + (how|what|why)       │        │   │
│  │     │ - Code review: review + code                 │        │   │
│  │     │ - Architecture choice: architecture + decision│        │   │
│  │     └──────────────────────────────────────────────┘        │   │
│  │                       │ Match?                              │   │
│  │                       ├─ YES → Return suggestion            │   │
│  │                       └─ NO → Continue                      │   │
│  │     ┌──────────────────────────────────────────────┐        │   │
│  │     │ Tier 2 Patterns (MEDIUM confidence)          │        │   │
│  │     │ - High complexity: complex + multiple        │        │   │
│  │     │ - Critical decision: critical + decision     │        │   │
│  │     └──────────────────────────────────────────────┘        │   │
│  │                       │ Match?                              │   │
│  │                       ├─ YES → Return suggestion            │   │
│  │                       └─ NO → Continue to fallback          │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│                              ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  4. CONTEXT FALLBACK (Last 2-3 messages)                    │   │
│  │     ┌──────────────────────────────────────────────┐        │   │
│  │     │ Circular Discussion Detection                │        │   │
│  │     │ - Same question 3+ ways                       │        │   │
│  │     │ - Returns: /zen-meditate                     │        │   │
│  │     └──────────────────────────────────────────────┘        │   │
│  │     ┌──────────────────────────────────────────────┐        │   │
│  │     │ Architecture Refinement Detection             │        │   │
│  │     │ - Previous "should I" + current refinement    │        │   │
│  │     │ - Returns: /zen-debate                        │        │   │
│  │     └──────────────────────────────────────────────┘        │   │
│  │     ┌──────────────────────────────────────────────┐        │   │
│  │     │ Cache Check (Prevent repetition)             │        │   │
│  │     │ - Suggestion given in last 30 seconds?        │        │   │
│  │     │ - Skip if recently suggested                  │        │   │
│  │     └──────────────────────────────────────────────┘        │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│                              ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  5. OUTPUT GENERATION                                       │   │
│  │     ┌──────────────────────────────────────────────┐        │   │
│  │     │ IF suggestion found:                          │        │   │
│  │     │   print "💡 Zen suggestion: /zen-command"    │        │   │
│  │     │   log_event(matched=True)                     │        │   │
│  │     │                                                │        │   │
│  │     │ ELSE (no suggestion):                          │        │   │
│  │     │   log_event(matched=False)                    │        │   │
│  │     │   silent exit (no stdout)                      │        │   │
│  │     └──────────────────────────────────────────────┘        │   │
│  │                                                              │   │
│  │  ALWAYS: sys.exit(0)  # Non-blocking                         │   │
│  └─────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────┬──────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      USER SEES SUGGESTION (or nothing)              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Component Architecture

### 2.1 Component: ZenSuggestionHook

**File**: `P:/.claude/hooks/zen_suggestion.py`

**Responsibilities**:
- Load configuration from JSON
- Execute tiered pattern matching
- Analyze conversation context
- Generate suggestions or remain silent
- Log all execution attempts

**Interface**:
```python
class ZenSuggestionHook:
    def __init__(self, config_path: str = "P:/.claude/config/zen_suggestions.json")
    def detect_zen_patterns(self, message: str) -> Optional[str]
    def analyze_context(self, messages: List[str]) -> Optional[str]
    def should_skip_suggestion(self, suggestion: str) -> bool
    def process_message(self, message: str, context_messages: List[str]) -> Optional[str]
    def log_event(self, prompt: str, suggestion: Optional[str])
```

### 2.2 Component: Configuration

**File**: `P:/.claude/config/zen_suggestions.json`

**Responsibilities**:
- Store pattern definitions (regex + suggestion mapping)
- Control hook behavior (enabled, min_confidence)
- Configure cache parameters

**Schema**:
```json
{
  "enabled": true,
  "output_format": "concise",
  "min_confidence": "HIGH",
  "allow_multiple_suggestions": false,
  "context_lookback_turns": 3,
  "recent_suggestion_cache_seconds": 30,
  "patterns": {
    "tier1": [...],
    "tier2": [...]
  }
}
```

### 2.3 Component: Logger

**File**: `P:/.claude/logs/zen_suggestions.json` (auto-created)

**Responsibilities**:
- Record all hook executions
- Track suggestion matches vs misses
- Enable post-hoc analysis with `jq`

**Entry Schema**:
```json
{
  "timestamp": "2025-12-30T12:34:56Z",
  "prompt": "User message (first 200 chars)",
  "suggestion": "/zen-debate",
  "matched": true,
  "tier": "tier1"
}
```

---

## 3. Data Flow

### 3.1 Input Flow

```
stdin (JSON)
    │
    ├─ prompt (string): User's current message
    ├─ context_messages (array): Last 2-3 messages
    ├─ message (string): Alternative field
    └─ content (string): Alternative field
    │
    ▼
ZenSuggestionHook.process_message()
    │
    ├─ Normalize input (check prompt/message/content)
    ├─ Validate enabled status
    └─ Begin pattern matching
```

### 3.2 Processing Flow

```
┌─ PRIMARY ANALYSIS ─────────────────┐
│ 1. Compile regex patterns (cached) │
│ 2. Check Tier 1 patterns           │
│    ├─ Match found → Return         │
│    └─ No match → Continue          │
│ 3. Check Tier 2 patterns           │
│    ├─ Match found → Return         │
│    └─ No match → Fallback          │
└────────────────────────────────────┘
               │ No match
               ▼
┌─ CONTEXT FALLBACK ────────────────┐
│ 1. Analyze last 2-3 messages       │
│ 2. Check circular discussion      │
│ 3. Check architecture refinement  │
│ 4. Verify cache not triggered      │
└────────────────────────────────────┘
```

### 3.3 Output Flow

```
┌─ SUGGESTION FOUND ────────────────┐
│ 1. Check suggestion cache         │
│ 2. If not cached:                 │
│    ├─ Print "💡 Zen suggestion: X"│
│    ├─ Add to cache                │
│    └─ Log matched event           │
│ 3. If cached: Skip (silent)       │
└────────────────────────────────────┘

┌─ NO SUGGESTION ───────────────────┐
│ 1. Log unmatched event            │
│ 2. Silent exit (no stdout)        │
└────────────────────────────────────┘
```

---

## 4. Pattern Matching Architecture

### 4.1 Tier Hierarchy

```
┌─ TIER 1 (HIGH CONFIDENCE) ──────────────────────────────────┐
│ Trigger: Direct patterns in current message                 │
│ Priority: Immediate return (no further analysis)            │
│                                                              │
│ Architecture Decision:                                      │
│   (should|whether to).*(microservices|monolith|sql|nosql)   │
│   → /zen-debate                                             │
│                                                              │
│ Stuck/Unclear:                                              │
│   (stuck|blocked|unclear|unsure|uncertain).*(how|what|why)  │
│   → /zen-meditate                                           │
│                                                              │
│ Code Review:                                                │
│   (review|examine|look at|check).*(code|changes|diff|logic) │
│   → /zen-code-review                                        │
│                                                              │
│ Architecture Choice:                                        │
│   (architecture|design|pattern|system).*(decision|choice)   │
│   → /zen-debate                                             │
└──────────────────────────────────────────────────────────────┘
                           │ No match
                           ▼
┌─ TIER 2 (MEDIUM CONFIDENCE) ───────────────────────────────┐
│ Trigger: Contextual patterns in current message            │
│ Priority: Return if Tier 1 didn't match                    │
│                                                              │
│ High Complexity:                                            │
│   (complex|multiple factors|trade-off|tradeoff)            │
│   → /zen-thinkdeep                                          │
│                                                              │
│ Critical Decision:                                          │
│   (critical|production|urgent|blocking).*(decision|change)  │
│   → /zen-debate --comprehensive                             │
└──────────────────────────────────────────────────────────────┘
                           │ No match
                           ▼
┌─ TIER 3 (CONTEXT FALLBACK) ────────────────────────────────┐
│ Trigger: Weak signals across recent messages               │
│ Priority: Last resort, requires 2-3 messages               │
│                                                              │
│ Circular Discussion:                                        │
│   Question count >= 2 in last 3 messages                   │
│   → /zen-meditate                                           │
│                                                              │
│ Architecture Refinement:                                    │
│   Previous architecture keywords + current refinement       │
│   → /zen-debate                                             │
└──────────────────────────────────────────────────────────────┘
```

### 4.2 Regex Compilation Strategy

```python
class ZenSuggestionHook:
    def __init__(self, config_path: str):
        # ... load config ...
        self._compiled_patterns = {}
        self._compile_patterns()

    def _compile_patterns(self):
        """Pre-compile regex patterns for performance."""
        for tier in ["tier1", "tier2"]:
            for pattern in self.config.get("patterns", {}).get(tier, []):
                name = pattern.get("name")
                regex = pattern.get("regex")
                if name and regex:
                    try:
                        self._compiled_patterns[name] = re.compile(
                            regex, re.IGNORECASE
                        )
                    except re.error as e:
                        print(f"Invalid regex for {name}: {e}", file=sys.stderr)
```

---

## 5. State Management

### 5.1 Suggestion Cache

**Purpose**: Prevent repetition of recent suggestions

**Implementation**:
```python
from collections import deque
from time import time

class ZenSuggestionCache:
    def __init__(self, max_size: int = 5, cooldown_seconds: int = 30):
        self.cache = deque(maxlen=max_size)
        self.timestamps = {}
        self.cooldown_seconds = cooldown_seconds

    def should_skip(self, suggestion: str) -> bool:
        """Check if suggestion was recently made."""
        if suggestion in self.timestamps:
            elapsed = time() - self.timestamps[suggestion]
            return elapsed < self.cooldown_seconds
        return False

    def add(self, suggestion: str):
        """Record a new suggestion."""
        self.cache.append(suggestion)
        self.timestamps[suggestion] = time()
```

### 5.2 Session State

**Design Decision**: No persistent session state needed

**Rationale**:
- Hook is stateless per execution
- Cache is in-memory (resets on restart)
- All state is in configuration (patterns) and logs (history)

---

## 6. Error Handling Architecture

### 6.1 Error Categories

| Error Type | Handling Strategy | User Impact |
|------------|-------------------|-------------|
| Config missing | Use defaults, log to stderr | None (hook still works) |
| Config invalid | Use defaults, log to stderr | None |
| Invalid regex | Skip pattern, log to stderr | None |
| Cache error | Reset cache, continue | None |
| Logging error | Silent continue (never block) | None |

### 6.2 Error Handling Pattern

```python
def main():
    """Hook entry point - receives JSON from Claude Code."""
    try:
        # Read input
        data = json.loads(sys.stdin.read())

        # Initialize hook (with internal error handling)
        hook = ZenSuggestionHook()

        # Process
        suggestion = hook.process_message(...)

        # Output
        if suggestion:
            print(f"💡 Zen suggestion: {suggestion}")

        sys.exit(0)  # Always exit 0

    except json.JSONDecodeError as e:
        print(f"Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(0)  # Non-blocking

    except Exception as e:
        print(f"Error in zen_suggestion hook: {e}", file=sys.stderr)
        sys.exit(0)  # Non-blocking
```

---

## 7. Performance Considerations

### 7.1 Execution Budget

| Component | Budget (ms) | Strategy |
|-----------|-------------|----------|
| Config load | 10 | File cached in memory |
| Pattern matching | 20 | Pre-compiled regex |
| Context analysis | 30 | Lookback limited to 3 |
| Logging | 10 | Append-only, async-safe |
| **Total** | **<100** | Well under 1000ms timeout |

### 7.2 Optimization Strategies

1. **Regex Compilation**: Patterns compiled once at init
2. **Early Returns**: Exit at first Tier 1 match
3. **Limited Lookback**: Only 2-3 messages for context
4. **Cache First**: Check cache before pattern matching
5. **Lazy Loading**: Context analysis only if primary patterns fail

---

## 8. Integration Points

### 8.1 Hook Registration

**File**: `P:/.claude/settings.json`

**Location**: Layer 1f (after other context hooks)

```json
{
  "hooks": {
    "UserPromptSubmit": [
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
    ]
  }
}
```

### 8.2 Configuration Creation

**File**: `P:/.claude/config/zen_suggestions.json`

**Action**: Create new file with initial pattern set

### 8.3 Log File Location

**File**: `P:/.claude/logs/zen_suggestions.json`

**Action**: Auto-created on first execution

---

## 9. Security Considerations

### 9.1 Input Validation

| Input | Validation | Sanitization |
|-------|------------|--------------|
| JSON from stdin | Parse with error handling | N/A (read-only) |
| Prompt text | Truncate to 200 chars for logs | No code execution |
| Context messages | Limit to last 3 | No code execution |

### 9.2 Code Safety

- **No eval()**: All pattern matching via regex only
- **No subprocess**: Hook doesn't execute external commands
- **No file writes**: Only append to log file
- **Read-only input**: Hook never modifies input_data

---

## 10. Extensibility

### 10.1 Adding New Patterns

**Action**: Edit `zen_suggestions.json`

```json
{
  "patterns": {
    "tier1": [
      {
        "name": "performance_optimization",
        "regex": "(optimize|improve performance).*(code|algorithm)",
        "suggestion": "/zen-thinkdeep",
        "confidence": "HIGH"
      }
    ]
  }
}
```

**No code changes required**

### 10.2 Adding New Tiers

**Action**: Extend hook code + config

```python
# In detect_zen_patterns():
for pattern in self.config.get("patterns", {}).get("tier3", []):
    if self._matches_pattern(message, pattern):
        return pattern["suggestion"]
```

### 10.3 Custom Suggestions

**Action**: Map patterns to any zen command

```json
{
  "name": "testing_strategy",
  "regex": "how.*test",
  "suggestion": "/zen-tdd"  # Custom zen command
}
```

---

## 11. Testing Architecture

### 11.1 Unit Tests

**File**: `P:/.claude/tests/test_zen_suggestion.py`

```python
def test_architecture_pattern():
    """Verify architecture decision pattern."""
    hook = ZenSuggestionHook()
    result = hook.detect_zen_patterns("Should I use microservices or monolith?")
    assert result == "/zen-debate"

def test_no_match_generic():
    """Verify generic queries don't trigger."""
    hook = ZenSuggestionHook()
    result = hook.detect_zen_patterns("What's in this directory?")
    assert result is None
```

### 11.2 Integration Tests

```bash
# Manual test via stdin
echo '{"prompt":"Should I use microservices?","context_messages":[]}' \
  | python P:/.claude/hooks/zen_suggestion.py

# Expected output:
# 💡 Zen suggestion: /zen-debate
```

### 11.3 Log Analysis

```bash
# Check suggestion rate
jq -s 'map(select(.matched==true)) | length' \
  P:/.claude/logs/zen_suggestions.json

# Check suggestion breakdown
jq -r '.suggestion' P:/.claude/logs/zen_suggestions.json | sort | uniq -c
```

---

## 12. Deployment Architecture

### 12.1 Deployment Steps

1. Create `P:/.claude/config/zen_suggestions.json`
2. Create `P:/.claude/hooks/zen_suggestion.py`
3. Register hook in `P:/.claude/settings.json`
4. Verify syntax: `python -m py_compile zen_suggestion.py`
5. Test manually via stdin
6. Restart Claude Code

### 12.2 Rollback Strategy

If hook causes issues:
1. Set `"enabled": false` in config (immediate disable)
2. Or comment out hook in settings.json
3. Or delete hook file (graceful degradation)

---

## Architecture Status

| Component | Status | Notes |
|-----------|--------|-------|
| Hook entry point | ✅ Defined | Based on existing patterns |
| Configuration | ✅ Defined | JSON-driven, tiered patterns |
| Pattern matching | ✅ Defined | 3-tier hierarchy |
| Context analysis | ✅ Defined | 2-3 message lookback |
| Suggestion cache | ✅ Defined | 30-second cooldown |
| Logging | ✅ Defined | Append-only JSON |
| Error handling | ✅ Defined | Non-blocking always |
| Testing | ✅ Defined | Unit + integration |

**Architecture**: ✅ COMPLETE

**Ready for**: Step 5 - Implementation Planning

---
