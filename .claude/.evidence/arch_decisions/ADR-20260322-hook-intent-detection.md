# ADR-20260322: Hook Intent Detection Architecture

**Status:** Proposed
**Date:** 2026-03-22
**Decomposed by:** N/A
**Context:** Cognitive enhancers hook fails to emit tags when prompts don't match rigid regex patterns.

---

## Decision

**Replace regex-only intent detection with a dual-layer architecture using:**

1. **Pattern-based layer** (regex — zero cost, pure Python)
2. **Session-based LLM layer** (emit classification prompt to current Claude session — zero external API cost)
3. **Feature flag** (`use_llm_classification`) to toggle between layers
4. **Graceful degradation** (fallback to regex if LLM layer disabled)

---

## Rationale

**Current problem:** Regex patterns are too rigid — legitimate implementation prompts that don't contain trigger words (e.g., "enhance the session resume mechanism") get no cognitive framework tags, reducing the value of the cognitive enhancers system.

**How "prompt" hooks actually work:**
- UserPromptSubmit hooks inject context into the **current Claude session**
- Claude is already present in the session — no external API call needed
- The hook emits a prompt prefix/suffix that Claude processes as part of the conversation
- **This is free and fast** — uses the existing session, not a separate API call

**Why dual-layer works better:**
- **Pattern layer** provides deterministic, zero-cost classification for obvious cases
- **LLM layer** handles nuance and context that regex cannot (uses current session, not external API)
- **Feature flag** allows users to choose based on their needs
- **Graceful degradation** maintains system integrity (regex fallback if LLM disabled)

---

## Tradeoffs

| Quality | LLM Layer (Session) | Regex Layer |
|---------|---------------------|-------------|
| **Coverage** | High — semantic understanding | Medium — keyword matching only |
| **Performance** | Fast — uses current session, no API call | Fastest — pure Python |
| **Cost** | Free — part of session | Free — no LLM |
| **Complexity** | Higher — prompt injection | Lower — regex only |
| **Reliability** | Depends on Claude following instruction | Deterministic — pattern match |
| **Maintainability** | Clear separation of concerns | Simple, well-tested |

---

## Multi-Terminal Safety

- **Safe** — Both layers are stateless and read-only
- No shared mutable state
- Each terminal runs detection independently
- No stale data risk
- No concurrency concerns

---

## Implementation

### Core Architecture

```python
# Modified: .claude/hooks/UserPromptSubmit_cognitive_enhancers.py

import re
from typing import Optional

def userpromptsubmit_cognitive_enhancements(prompt: str, context: dict) -> str:
    """Emit cognitive framework tags based on detected intent."""

    config = load_cognitive_config()
    if not config.get("enabled", False):
        return ""

    if is_suppressed(context):
        return ""

    # Feature flag: LLM layer vs regex-only
    use_llm = config.get("use_llm_classification", False)

    if use_llm:
        # LLM layer: Emit classification prompt to current session
        # Claude will process this as part of the current conversation
        return _emit_llm_classification_prompt(prompt, config)
    else:
        # Regex layer: Pure Python, zero LLM involvement
        return _classify_by_regex(prompt, config)


def _emit_llm_classification_prompt(prompt: str, config: dict) -> str:
    """Emit a prompt that Claude (current session) will classify."""

    classification_instruction = f"""
[INTENT CLASSIFICATION REQUEST]
Classify this prompt's intent: "{prompt}"

Respond ONLY with cognitive framework tags if intent matches:
- Implementation: [ASUM] [INV] [CAL]
- Diagnostic: [ANCH] [FENC] [DADV]
- Decomposition: [SOC] [CYNE] [RAZR]

If unclear or unknown, emit NO tags.
[/INTENT CLASSIFICATION]
"""

    # This gets injected into Claude's prompt — Claude classifies as part of this session
    return classification_instruction


def _classify_by_regex(prompt: str, config: dict) -> str:
    """Pure regex classification — no LLM involvement."""

    patterns = {
        "implementation": re.compile(
            r'\b(build|create|implement|refactor|optimize|add|write|develop|code|make|set up|configure|change|modify|update|fix|replace|rewrite|convert|migrate|hook up|wire up|integrate|extend|extract)\b',
            re.IGNORECASE
        ),
        "diagnostic": re.compile(
            r'\b(debug|investigate|diagnose|analyze|explain why|root cause|figure out|what\'s wrong|what caused|troubleshoot|why does|why is|why did|how does|what happens)\b',
            re.IGNORECASE
        ),
    }

    intent_to_tags = {
        "implementation": "[ASUM] [INV] [CAL]",
        "diagnostic": "[ANCH] [FENC] [DADV]",
        "decomposition": "[SOC] [CYNE] [RAZR]",
    }

    for intent, pattern in patterns.items():
        if pattern.search(prompt):
            return " " + intent_to_tags[intent] + " "

    return ""  # No match
```

### Configuration

```json
// .claude/settings.local.json
{
  "hooks": {
    "cognitive_enhancers": {
      "enabled": true,
      "use_llm_classification": false,  // Feature flag: false = regex-only (default)
      "confidence_threshold": 0.7
    }
  }
}
```

### Testing Approach

```python
# New file: .claude/hooks/__lib/tests/test_intent_classifier.py

import pytest
from hooks.UserPromptSubmit_cognitive_enhancers import _classify_by_regex

def test_regex_implementation():
    """Regex should catch implementation keywords."""
    result = _classify_by_regex("implement a new feature", {})
    assert "[ASUM]" in result
    assert "[INV]" in result
    assert "[CAL]" in result

def test_regex_diagnostic():
    """Regex should catch diagnostic keywords."""
    result = _classify_by_regex("debug this issue", {})
    assert "[ANCH]" in result
    assert "[FENC]" in result
    assert "[DADV]" in result

def test_regex_no_match():
    """Regex should return empty string for non-matching prompts."""
    result = _classify_by_regex("some random prompt", {})
    assert result == ""

def test_llm_layer_emits_prompt():
    """LLM layer should emit classification prompt."""
    from hooks.UserPromptSubmit_cognitive_enhancers import _emit_llm_classification_prompt

    result = _emit_llm_classification_prompt("enhance session resume", {})
    assert "[INTENT CLASSIFICATION REQUEST]" in result
    assert "enhance session resume" in result
```

---

## Rollback Strategy

**If this causes issues:**
1. Set `use_llm_classification: false` in config to disable LLM layer
2. System falls back to existing regex-only behavior
3. No data migration needed (detection is stateless)

**Revert entirely:**
- Restore original `cognitive_enhancers.py` from git
- Remove test file `test_intent_classifier.py`

---

## Consequences

### Positive
- **Better coverage with LLM layer**: Semantic understanding catches non-keyword prompts
- **Backward compatible**: Regex layer preserves existing behavior
- **Configurable**: Feature flag allows user control
- **Zero external API cost**: LLM layer uses current session, not separate API call
- **Testable**: Clear unit tests for regex layer
- **Constitutional compliant**: No external API calls (uses session-based prompting)

### Negative
- **LLM layer reliability**: Depends on Claude following classification instructions
- **Complexity**: More moving parts than regex-only approach
- **LLM layer overhead**: Adds prompt injection (though minimal cost)

### Mitigations
- **Default to regex**: More predictable behavior out of the box
- **Feature flag**: Users can enable LLM layer if they want semantic coverage
- **Graceful degradation**: LLM layer failures fall back to regex

---

## Recommendation

**Default: `use_llm_classification: false`** (regex-only)
- More predictable behavior
- No dependency on Claude following classification instructions
- Sufficient for most common prompts

**Enable LLM layer for nuanced prompts:**
- If user frequently uses non-standard phrasing
- If semantic intent matters more than keyword matches
- Set `use_llm_classification: true` in config

---

## Evidence Sources

- **Regex limitations**: Current patterns fail on "enhance session resume" (no trigger words)
- **Hook architecture**: UserPromptSubmit hooks inject into current session, not external API
- **Multi-layered pattern**: Industry standard for intent detection (fast path + smart fallback)
- **Constitutional compliance**: Session-based prompting respects "no external API calls" constraint

---

## Related Decisions

- N/A (first decision on hook intent detection architecture)
