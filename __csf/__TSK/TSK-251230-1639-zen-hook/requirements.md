# Requirements Analysis: Zen Suggestion Hook

## Task: TSK-251230-1639-zen-hook
**Date**: 2025-12-30
**Status**: Requirements Analysis Complete

---

## 1. Domain Analysis

### 1.1 Primary Domain: Behavioral Pattern Detection

**Core Function**: Detect decision points in user messages and suggest zen commands.

**Key Characteristics**:
- **Deterministic**: Must execute on 100% of UserPromptSubmit events
- **Selective**: Output only on 20-30% of messages (high confidence patterns)
- **Non-blocking**: Never interrupt workflow, always exit(0)

### 1.2 Secondary Domain: Conversation Context Analysis

**Core Function**: Analyze recent conversation for weak decision signals.

**Key Characteristics**:
- **Lookback window**: 2-3 messages only (memory efficiency)
- **Fallback only**: Activates only when primary patterns weak
- **Pattern detection**: Circular discussion, architecture refinement

### 1.3 Tertiary Domain: Configuration Management

**Core Function**: Pattern library without code changes.

**Key Characteristics**:
- **JSON-driven**: All patterns in config file
- **Tiered structure**: Tier 1 (HIGH) > Tier 2 (MEDIUM) > Tier 3 (context)
- **Hot-reload**: Changes apply without restarting CC

---

## 2. Functional Requirements (FRs)

### FR-001: Deterministic Execution
**Priority**: CRITICAL
**Description**: Hook must execute on every UserPromptSubmit event.
**Verification**: Log all executions with timestamp.
**Success Criterion**: Zero missed decision points.

### FR-002: Selective Output
**Priority**: CRITICAL
**Description**: Output suggestions only on high-confidence matches (~20-30% of messages).
**Verification**: Monitor suggestion rate in logs.
**Success Criterion**: Signal value maintained, no spam.

### FR-003: Tier 1 Pattern Detection
**Priority**: HIGH
**Description**: HIGH confidence patterns trigger immediate suggestions.
**Patterns**:
- Architecture decision: `"(should|whether to).*(microservices|monolith|sql|nosql)"` → `/zen-debate`
- Stuck/Unclear: `"(stuck|blocked|unclear|unsure|uncertain).*(how|what|where|why)"` → `/zen-meditate`
- Code review: `"(review|examine|look at|check).*(code|changes|diff|logic)"` → `/zen-code-review`
- Architecture choice: `"(architecture|design|pattern|system).*(decision|choice|approach)"` → `/zen-debate`

### FR-004: Tier 2 Pattern Detection
**Priority**: MEDIUM
**Description**: MEDIUM confidence patterns trigger suggestions if Tier 1 doesn't match.
**Patterns**:
- High complexity: `"(complex|multiple factors|trade-off|tradeoff|many considerations)"` → `/zen-thinkdeep`
- Critical decision: `"(critical|production|urgent|blocking).*(decision|choice|change)"` → `/zen-debate --comprehensive`

### FR-005: Context Fallback Analysis
**Priority**: MEDIUM
**Description**: Analyze last 2-3 messages for weak signals when primary patterns don't match.
**Patterns**:
- Circular discussion: Same question asked 3+ ways → `/zen-meditate`
- Architecture refinement: Previous "should I" + current refinement → `/zen-debate`
- Multi-perspective seeking: Multiple "from another angle" requests → `/zen-thinkdeep`

### FR-006: Suggestion Cache
**Priority**: MEDIUM
**Description**: Prevent repetition of recent suggestions.
**Specs**:
- Cache size: 5 suggestions
- Duration: 30 seconds or last 5 messages
- Purpose: Avoid spamming same suggestion repeatedly

### FR-007: Non-Blocking Exit
**Priority**: CRITICAL
**Description**: Never interrupt workflow even on errors.
**Behavior**:
- Exit code: Always 0
- Error handling: Log to stderr, continue execution

### FR-008: One-Line Output
**Priority**: HIGH
**Description**: Output format is single line with suggestion.
**Format**: `💡 Zen suggestion: /zen-command`
**Never output**: Explanations, multiple suggestions, verbose reasoning

---

## 3. Non-Functional Requirements (NFRs)

### NFR-001: Execution Time
**Target**: < 100ms average
**Method**: Regex compilation cached, minimal I/O
**Timeout**: 1000ms in settings.json (hard limit)

### NFR-002: Memory Footprint
**Target**: Minimal
**Constraints**:
- No context accumulation beyond lookback window
- Query discovery.db on-demand only
- Cache limited to 5 suggestions

### NFR-003: Configurability
**Target**: No code changes for pattern evolution
**Implementation**:
- Patterns in JSON config
- Enable/disable flag
- Min confidence threshold

### NFR-004: Observability
**Target**: Debuggable without code inspection
**Implementation**:
- Append-only JSON logging
- JQ-analyzable logs
- Timestamp + prompt + suggestion + matched flag

### NFR-005: Platform Compatibility
**Target**: Windows (current), cross-platform desirable
**Constraints**:
- Forward slashes in paths
- Python 3.11+ compatibility
- No OS-specific hardcoded paths

---

## 4. Technical Constraints

### TC-001: Hook System Integration
**Event**: UserPromptSubmit
**Input**: JSON via stdin
**Output**: stdout (suggestion) or silent
**Exit**: Always 0 (non-blocking)

### TC-002: File Structure
```
.claude/
├── config/
│   └── zen_suggestions.json    # Pattern library
├── hooks/
│   └── zen_suggestion.py        # Hook implementation
├── logs/
│   └── zen_suggestions.json    # Execution logs
└── settings.json                # Hook registration
```

### TC-003: String Escaping (Critical)
**Known Issue**: Windows line endings + Python string escaping = syntax errors
**Solution**: Use hex escapes (`\x5cn`) for literal backslash-n

### TC-004: Regex Engine
**Engine**: Python `re` module with IGNORECASE flag
**Limitation**: No lookbehind for variable-length patterns
**Mitigation**: Use lookahead or simple alternation

---

## 5. Data Models

### 5.1 Configuration Structure
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

### 5.2 Log Entry Structure
```json
{
  "timestamp": "2025-12-30T12:34:56Z",
  "prompt": "User message (first 200 chars)",
  "suggestion": "/zen-debate",
  "matched": true
}
```

### 5.3 Hook Input Schema
```json
{
  "prompt": "User message text",
  "context_messages": ["msg1", "msg2", "msg3"],
  "message": "Alternative field"
}
```

---

## 6. Acceptance Criteria

### AC-001: Pattern Detection
- **Given**: User asks "Should I use microservices or monolith?"
- **When**: UserPromptSubmit hook fires
- **Then**: Output "💡 Zen suggestion: /zen-debate"

### AC-002: No False Positives
- **Given**: User says "What's in this directory?"
- **When**: UserPromptSubmit hook fires
- **Then**: No output (silent)

### AC-003: Context Analysis
- **Given**: Last 3 messages contain architecture questions
- **And**: Current message refines the same question
- **When**: UserPromptSubmit hook fires
- **Then**: Output "💡 Zen suggestion: /zen-debate"

### AC-004: Error Handling
- **Given**: Config file is missing or malformed
- **When**: UserPromptSubmit hook fires
- **Then**: Silent exit (no error shown to user), error in stderr

### AC-005: Cache Prevention
- **Given**: Suggestion just given in last message
- **When**: Same pattern detected in current message
- **Then**: Skip suggestion to avoid repetition

---

## 7. Complexity Assessment

### 7.1 Technical Complexity: **MEDIUM**

**Reasoning**:
- Well-defined problem with clear patterns
- No complex state management
- Minimal external dependencies
- String escaping is known gotcha

### 7.2 Domain Complexity: **LOW**

**Reasoning**:
- Pure behavioral analysis
- No business logic
- Self-contained (no external APIs)

### 7.3 Integration Complexity: **LOW**

**Reasoning**:
- Single hook integration point
- No external service dependencies
- Standard hook protocol

### Overall: **LOW-MEDIUM COMPLEXITY**

**Estimated Implementation Time**:
- Phase 1 (core hook): 2-3 hours
- Phase 2 (refinement): 3-5 hours
- Phase 3 (production): 5+ hours (ongoing)

---

## 8. Risk Analysis

### Risk-001: Pattern Too Broad
**Probability**: MEDIUM
**Impact**: HIGH (spam, alert fatigue)
**Mitigation**: Start conservative, test with 20+ messages, monitor logs

### Risk-001: Pattern Too Narrow
**Probability**: LOW
**Impact**: MEDIUM (missed opportunities)
**Mitigation**: Context fallback captures weak signals

### Risk-003: String Escaping Errors
**Probability**: MEDIUM
**Impact**: HIGH (hook doesn't load)
**Mitigation**: Use hex escapes, verify with py_compile

### Risk-004: Performance Degradation
**Probability**: LOW
**Impact**: MEDIUM (sluggish responses)
**Mitigation**: Regex caching, minimal I/O, 1000ms timeout

---

## 9. Dependencies

### Internal Dependencies
- `.claude/settings.json` - Hook registration
- Existing hook patterns from HOOK_FIXES_SITREP.md
- Python 3.11+ runtime

### External Dependencies
- None (stdlib only: `json`, `sys`, `re`, `datetime`, `pathlib`, `collections`)

### Reference Implementations
- `disler/claude-code-hooks-mastery` - Hook structure
- `decider/claude-hooks` - Configuration patterns
- `Ido-Levi/claude-code-tamagotchi` - Behavioral analysis

---

## 10. Success Metrics

### Quantitative Metrics
- **Suggestion Rate**: 20-30% of messages (target)
- **Execution Time**: < 100ms average
- **Hook Load Success**: 100% (no syntax errors)
- **Cache Hit Rate**: < 10% (avoiding repetition)

### Qualitative Metrics
- **Signal Value**: No spam complaints
- **Coverage**: 80%+ of genuine zen moments captured
- **Usability**: Easy to disable/modify patterns

---

## Requirements Status

| Category | Count | Complete |
|----------|-------|----------|
| Functional Requirements | 8 | ✅ |
| Non-Functional Requirements | 5 | ✅ |
| Technical Constraints | 4 | ✅ |
| Acceptance Criteria | 5 | ✅ |
| Data Models | 3 | ✅ |

**Requirements Analysis**: ✅ COMPLETE

---

**Next Step**: Step 3 - Research Intelligence (gather implementation patterns from existing hooks)
