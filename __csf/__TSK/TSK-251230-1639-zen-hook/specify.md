# Specification: Zen Suggestion Hook

## Goal
Implement a behavioral hook that deterministically suggests zen commands at critical decision points without relying on LLM memory.

## Why

### Problem Statement
From `zen-hook-complete.md`:
> "I (the LLM) will naturally forget to suggest zen commands after a few interactions."

**Business Value:**
- Ensures zen commands are suggested consistently
- Prevents drift from analytical best practices
- No reliance on LLM memory (deterministic)

**User Impact:**
- Timely reminders for debate, meditation, code-review
- Better decision-making through structured analysis
- Reduced cognitive load (system reminds, not user)

**Technical Necessity:**
- LLM memory is unreliable across sessions
- Pattern detection alone was too noisy
- Need deterministic execution with selective output

## What

### Functional Requirements

**FR-001:** Hook executes on 100% of UserPromptSubmit events
- **Verification:** Log all executions
- **Success:** Zero missed decision points

**FR-002:** Output appears on ~20-30% of messages (selective)
- **Verification:** Check suggestion rate in logs
- **Success:** Signal value maintained, no spam

**FR-003:** Tier 1 patterns trigger HIGH confidence suggestions
- **Architecture decisions:** "should I X or Y?" + keywords
- **Stuck/Unclear:** "stuck" + "how/what/why"
- **Code review:** "review" + code context

**FR-004:** Tier 2 patterns trigger MEDIUM confidence suggestions
- **High complexity:** "complex" + multiple factors
- **Critical decisions:** "critical/production" + decision

**FR-005:** Context fallback analyzes last 2-3 messages
- **Circular discussion:** Same question 3+ ways
- **Architecture refinement:** Previous "should I" + current refines

**FR-006:** Suggestion cache prevents repetition
- **Cache size:** 5 suggestions
- **Duration:** 30 seconds or last 5 messages

**FR-007:** Non-blocking exit (workflow safety)
- **Exit code:** Always 0
- **Error handling:** Log to stderr, continue

### Non-Functional Requirements

**NFR-001:** Execution time < 100ms
- **Target:** 50ms average
- **Method:** Regex compilation cached

**NFR-002:** Memory footprint minimal
- **No context accumulation**
- **Query discovery.db on-demand

**NFR-003:** Configurable without code changes
- **Patterns in JSON config**
- **Enable/disable flag**

**NFR-004:** Observable and debuggable
- **Append-only JSON logging**
- **JQ-analyzable logs**

## All Needed Context

### Files
- `C:/Users/brsth/Downloads/zen-hook-complete.md` - Complete design specification
- `C:/Users/brsth/Downloads/github-repos-reference.md` - Implementation patterns
- `P:/.claude/hooks/HOOK_FIXES_SITREP.md` - Current hook architecture
- `P:/.claude/settings.json` - Hook registration

### APIs
- **UserPromptSubmit Hook:** Receives JSON from Claude Code
  ```python
  {"prompt": "...", "context_messages": [...], "message": "..."}
  ```

### Existing Patterns
```python
# From PostToolUse_system2.py
def classify_severity(output: str) -> str:
    # Tiered classification pattern (HIGH/MEDIUM/LOW)
    if re.search(r"exit code [1-9]", output_lower):
        return "CRITICAL"
    if "warning:" in output_lower:
        return "WARNING"
    return "IGNORE"
```

### Gotchas
- **String escaping:** Use hex escapes (`\x5cn`) for literal backslash-n
- **Non-blocking:** Always `sys.exit(0)` even on errors
- **JSON I/O:** `sys.stdin.read()` for input, `print()` for output
- **Hook timeout:** 1000ms default in settings.json

## Implementation Blueprint

### 1. ZenSuggestionHook Class
```python
class ZenSuggestionHook:
    def __init__(self, config_path=".claude/config/zen_suggestions.json"):
        self.config = self._load_config()
        self.suggestion_cache = deque(maxlen=5)
        self.log_file = Path(".claude/logs/zen_suggestions.json")

    def detect_zen_patterns(self, message: str) -> Optional[str]:
        # Check Tier 1 (HIGH confidence)
        for pattern in self.config.get("patterns", {}).get("tier1", []):
            if self._matches_pattern(message, pattern):
                return pattern["suggestions"][0]
        # Check Tier 2 (MEDIUM confidence)
        for pattern in self.config.get("patterns", {}).get("tier2", []):
            if self._matches_pattern(message, pattern):
                return pattern["suggestions"][0]
        return None

    def analyze_context(self, messages: List[str]) -> Optional[str]:
        # Circular discussion detection
        if self._is_circular_discussion(messages):
            return "/zen-meditate"
        # Architecture refinement detection
        if self._is_architecture_refinement(messages):
            return "/zen-debate"
        return None
```

### 2. Configuration Structure
```json
{
  "enabled": true,
  "min_confidence": "HIGH",
  "patterns": {
    "tier1": [
      {"name": "architecture_decision", "regex": "(should|whether to).*(microservices|monolith)", "suggestions": ["/zen-debate"]},
      {"name": "stuck_blocked", "regex": "(stuck|blocked|unclear).*(how|what|why)", "suggestions": ["/zen-meditate"]},
      {"name": "code_review", "regex": "(review|look at).*(code|changes)", "suggestions": ["/zen-code-review"]}
    ],
    "tier2": [
      {"name": "high_complexity", "regex": "(complex|multiple factors|trade-off)", "suggestions": ["/zen-thinkdeep"]},
      {"name": "critical_decision", "regex": "(critical|production).*(decision|choice)", "suggestions": ["/zen-debate --comprehensive"]}
    ]
  }
}
```

### 3. Hook Registration
```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "python .claude/hooks/zen_suggestion.py",
            "timeout_ms": 1000,
            "exit_code_error_handling": "non_blocking"
          }
        ]
      }
    ]
  }
}
```

## Validation Loop

- **Level 1 (Syntax):** `python -m py_compile zen_suggestion.py`
- **Level 2 (Unit):** `python test_zen_suggestion.py`
- **Level 3 (Integration):** Test with real messages via stdin

## BDD Scenarios

**Scenario 1: Architecture Decision**
```
Given user asks "Should I use microservices or monolith?"
When UserPromptSubmit hook fires
Then output "💡 Zen suggestion: /zen-debate"
```

**Scenario 2: Stuck/Unclear**
```
Given user says "I'm stuck on how to proceed"
When UserPromptSubmit hook fires
Then output "💡 Zen suggestion: /zen-meditate"
```

**Scenario 3: Generic Message (No Output)**
```
Given user says "What's in this directory?"
When UserPromptSubmit hook fires
Then no output (silent)
```

**Scenario 4: Circular Discussion**
```
Given last 3 messages contain questions about architecture
And current message refines the same question
When UserPromptSubmit hook fires
Then output "💡 Zen suggestion: /zen-meditate"
```
