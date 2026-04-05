# Implementation Plan: Observable Effect Verification System

**Date**: 2026-03-04
**Status**: DRAFT
**Version**: 1.0

---

## 1. Problem Statement

### Root Cause Analysis

**Incident**: Strawberry validator (`StopHook_strawberry_validator.py`) had `structlog.configure()` configured (lines 57-67) but no `FileHandler` was actually added to write logs to disk. The code appeared correct but produced no observable effect.

**Symptom**: Code passes all verification checks:
- ✅ Syntax validation (fix_validator.py)
- ✅ Import availability (imports resolve)
- ✅ Code runs without errors
- ❌ **Side effect doesn't occur** (no log file created)

**Root Problem**: **Code Verification ≠ Behavior Verification**

We verify that code *compiles* but not that it *works as intended*. This is a fundamental gap in the verification stack.

### Scope of Problem

This isn't just about logging. The broader issue:
1. **Side effect verification gap**: Code may have intended side effects (file creation, state changes, process spawning) that don't actually occur
2. **Unverified skeptical stance**: AI casts doubt on user claims or hedges ("let me verify") without actually doing verification
3. **No observable effect measurement**: We have no systematic way to verify "did this code change produce its documented effect?"

---

## 2. Context Analysis

### Allowed APIs (Verified from Documentation)

**Standard Library**:
- `ast` - AST parsing for code analysis ✅
- `hashlib` - File hash computation ✅
- `pathlib.Path` - File path operations ✅
- `re` - Regex matching ✅
- `logging` / `structlog` - Logging (following LOGGING_STANDARD.md) ✅
- `subprocess` - External tool spawning ✅
- `datetime`, `time` - Timestamps and performance tracking ✅

**Hook System APIs**:
- `posttooluse.base.PostToolUseHook` - Base class for PostToolUse hooks ✅
- `posttooluse.base.HookRegistry` - Registry management ✅
- `scanners.base_scanner.BaseScanner` - Base class for scanners ✅
- `evidence_store` - Tool event tracking ✅

**External APIs** (conditional):
- LLM APIs (Z.AI glm-4-plus) - Used in strawberry_validator.py for hallucination detection ✅
- Semantic search (CKS/CHS via DaemonClient) - Documented in CLAUDE.md ✅

### Anti-Patterns to Avoid

1. **stderr for success**: Never write success messages to stderr (causes false "hook error")
2. **Blocking in PostToolUse**: PostToolUse hooks are advisory-only, cannot block
3. **Cross-process state leaks**: Always create fresh registry per invocation
4. **Un-documented external API calls**: Must document use case in plan
5. **Silent failures**: Must log errors and fail open gracefully

### Architecture Context

**PostToolUse Router Pattern**:
- **Location**: `P:\.claude\hooks\PostToolUse_router.py`
- **Consolidates**: 25 hooks in-process (~5-10ms vs 184ms subprocess)
- **Registration**: 3-step process in `posttooluse/__init__.py`:
  1. Import hook class
  2. Register in `create_registry()` function
  3. Registry.run_all() executes all hooks

**Scanner Pattern**:
- **Base**: `scanners/base_scanner.py` with `BaseScanner` abstract class
- **Method**: `scan(text, context) -> ScanResult`
- **Integration**: Used by Stop hooks (e.g., strawberry_validator)

**Existing Verification Infrastructure**:
- **fix_validator.py**: AST-based syntax/undefined method validation
- **reflexion_verifier.py**: Reads files back after Edit/Write (zero-trust)
- **falsification_assessor.py**: Verification reminders
- **unverified_stance_detector.py**: Detects skeptical doubt without verification

### Key Integration Points

1. **PostToolUse Registry**: `P:\.claude\hooks\posttooluse/__init__.py` (line 64-117)
2. **Stop Hook**: `P:\.claude\hooks\StopHook_strawberry_validator.py` (for LLM-based detection)
3. **Evidence Store**: `P:\.claude\hooks\evidence_store.py` (turn-scoped verification)
4. **Unverified Stance Detector**: `P:\.claude\hooks\anti_sycophancy\unverified_stance_detector.py` (existing pattern to extend)

---

## 3. Existing Implementation Discovery

### PostToolUse Hook Patterns

**File**: `P:\.claude\hooks\posttooluse\__init__.py`

**Current Registration** (lines 64-117):
```python
def create_registry() -> HookRegistry:
    registry = HookRegistry()
    # 25 hooks registered:
    # - fix_validator, reflexion_verifier, falsification_assessor
    # - semantic_compress, error_attribution_tracker, skill_execution_tracker
    # - ... (25 total)
    return registry
```

**Pattern** (from `posttooluse/base.py`):
```python
class PostToolUseHook(ABC):
    env_var = "HOOK_ENABLED"           # Environment variable toggle
    default_enabled = True              # Default state
    tool_matcher = {"Edit", "Write"}     # Which tools to intercept

    @abstractmethod
    def process(self, tool_name: str, tool_input: dict, tool_response: dict) -> dict:
        return {"injection": str, "passed": bool}
```

### Scanner Base Class

**File**: `P:\.claude\hooks\scanners\base_scanner.py`

**Interface**:
```python
class BaseScanner(ABC):
    @abstractmethod
    def scan(self, text: str, context: dict = None) -> ScanResult:
        """Returns ScanResult(status, scanner_name, matched_text, reason, severity, suggestion)"""
```

**ScanResult**:
```python
@dataclass
class ScanResult:
    status: ScanStatus          # PASS, FAIL, SKIP
    scanner_name: str
    matched_text: str = ""
    reason: str = ""
    severity: str = "MEDIUM"    # LOW, MEDIUM, HIGH
    suggestion: str = ""
```

### Unverified Stance Detector (Existing)

**File**: `P:\.claude\hooks\anti_sycophancy\unverified_stance_detector.py`

**Detection Logic** (lines 180-234):
```python
def detect_unverified_stance(response: str, data: dict) -> StanceMatch | None:
    # 1. Extract tools_used from data
    # 2. Extract user message from transcript
    # 3. Check if user made factual claim
    # 4. Check if response has sycophantic doubt or empty hedge
    # 5. Return match only if ALL conditions met AND no verification tools used
```

**Patterns** (lines 35-54):
- **SYCOPHANTIC_DOUBT**: "you're right to push back/question/be skeptical"
- **EMPTY_HEDGE**: "let me verify", "that sounds high", "i doubt that"
- **VERIFICATION_TOOLS**: WebSearch, WebFetch, Bash

**This is the pattern we will extend for unverified stance detection.**

### StopHook_reality_check.py (Archived)

**File**: `P:\.claude\hooks\_archive\StopHook_reality_check.py`

**Status**: ARCHIVED (not currently active)

**Purpose**: Detects:
1. Mechanical repetition of code references without verifying reality
2. Incomplete solutions leaving dead/orphaned code

**Patterns** (lines 39-86):
- **CODE_REFERENCE_PATTERNS**: "the code checks for X", "this file is at Y"
- **VERIFICATION_PATTERNS**: "doesn't exist", "verified X doesn't exist"
- **INCOMPLETE_REMOVAL_PATTERNS**: "removed X but Y still exists"

**This hook needs to be reactivated and extended for unverified stance detection.**

---

## 4. Test Discovery

### Test Infrastructure Location

**Directory**: `P:\.claude\hooks\tests\`

**Test Files**:
- `test_hook_base.py` - Hook base class testing
- `test_strawberry_validator.py` - Scanner integration (34 tests, all passing)
- `test_falsification_verification.py` - Falsification testing

### Test Scenarios Required

**For Observable Effect Verifier**:
1. **Logging Effect Detection**:
   - ✅ Detects `FileHandler("file.log")` pattern
   - ✅ Detects `structlog.configure()` with FileHandler setup
   - ✅ Skips conditional logging (if DEBUG: log...)
   - ✅ Skips environment-based paths (os.getenv("LOG_PATH"))
   - ✅ Warns when structlog configured but no FileHandler added

2. **Effect Verification**:
   - ✅ Warns when logging configured but log file not created
   - ✅ Passes when log file exists after code runs
   - ✅ Handles missing log directory gracefully

3. **Integration Tests**:
   - ✅ Hooks registered in router run correctly
   - ✅ Warn-only mode doesn't block responses
   - ✅ Env var `SEV_ENABLED=false` disables hook

**For Unverified Stance Detector**:
1. **Skeptical Pattern Detection**:
   - ✅ Detects "that sounds high/low" without verification tool
   - ✅ Detects "i doubt that" without verification tool
   - ✅ Allows stance when WebSearch/WebFetch/Bash used
   - ✅ Skips when user asks question (not factual claim)

2. **Unfounded System Behavior Claims** (NEW - addresses your scenario):
   - ✅ Detects "since the hook blocks X" without verification
   - ✅ Detects "because the gate won't allow X" without verification
   - ✅ Detects "due to limitation on X" without verification
   - ✅ Checks for verification tools before flagging
   - ✅ Warns with context about what needs verification
   - Example: *"Since the PreToolUse hook blocks direct config.json access..."*
     → Pattern matches, no verification tools used → Warning injected

2. **Stop Hook Integration**:
   - ✅ Warning injected via additionalContext
   - ✅ Doesn't block in warn-only mode
   - ✅ Env var `UNVERIFIED_STANCE_MODE=warn|block`

### Testing Strategy

**Unit Tests** (pytest):
```bash
pytest P:\.claude\hooks\tests\test_observable_effect_verifier.py -v
pytest P:\.claude\hooks\tests\test_unverified_stance_hook.py -v
```

**Integration Tests** (synthetic hook input):
```python
# Test SEV with synthetic hook input
echo '{"tool_name": "Write", "tool_input": {"file_path": "test.py"}, "tool_response": {}}' | \
  python P:\.claude\hooks\posttooluse\observable_effect_verifier.py
```

**Manual Verification**:
1. Create test file with structlog but no FileHandler
2. Run Edit operation
3. Verify warning appears
4. Add FileHandler
5. Verify no warning

---

## 5. Proposed Solution

### Architecture: Observable Effect Verification (SEV) System

**Goal**: Systematic verification that code changes produce their documented observable effects.

**Design Principle**: Extensible effect registry - start with logging, add state/process/API effects later.

#### Two-Track Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Observable Effect Verification             │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Track 1: PostToolUse SEV (Effect Verification)              │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ ObservableEffectVerifier                             │    │
│  │  - Detects effects in modified files                 │    │
│  │  - Runs effect-specific verifiers                    │    │
│  │  - Warns when effects don't materialize              │    │
│  └──────────────────────────────────────────────────────┘    │
│           │                                                 │
│           ├─► LoggingEffectVerifier                       │
│           │   - Detect: FileHandler("file.log")          │
│           │   - Verify: FileHandler added to logger       │
│           │   - Check: Log file created after code runs   │
│           │                                                 │
│           ├─► StateEffectVerifier (FUTURE)                │
│           ├─► ProcessEffectVerifier (FUTURE)              │
│           └─► APIEffectVerifier (FUTURE)                  │
│                                                               │
└───────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────┐
│                 Track 2: Stop Hook (Stance Detection)          │
├───────────────────────────────────────────────────────────────┤
│  StopHook_unverified_stance.py                                │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ Extended unverified_stance_detector.py                 │   │
│  │  - Existing: sycophantic doubt, empty hedge           │   │
│  │  - NEW: skeptical stance patterns                      │   │
│  │  - Check: Did response cast doubt without evidence?   │   │
│  └────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────┘
```

### Component Specifications

#### 1. Base Effect Verifier (`posttooluse/effects/base_effect.py`)

**Abstract interface** for all effect verifiers:

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class EffectVerificationResult:
    """Result from effect verification."""
    effect_type: str              # "logging", "state", "process", "api"
    detected: bool                # Effect was detected in code
    verified: bool                # Effect works as intended
    matched_config: Dict[str, Any] # Detected configuration
    warning_message: str | None    # Warning if detected but not verified
    suggestion: str | None         # How to fix

class BaseEffectVerifier(ABC):
    """Abstract base class for effect verifiers."""

    @classmethod
    @abstractmethod
    def detect(cls, content: str, file_path: str) -> Dict[str, Any] | None:
        """Detect if this effect type exists in the file.

        Returns:
            Effect configuration dict if detected, None otherwise
        """
        pass

    @classmethod
    @abstractmethod
    def verify(cls, effect_config: Dict[str, Any], file_path: str) -> EffectVerificationResult:
        """Verify that the effect works as intended.

        Args:
            effect_config: Configuration extracted from detect()
            file_path: Path to file being verified

        Returns:
            EffectVerificationResult with verification outcome
        """
        pass
```

#### 2. Logging Effect Verifier (`posttooluse/effects/logging_effect.py`)

**Tight detection patterns** (warn-only mode):

```python
import re
from pathlib import Path

from .base_effect import BaseEffectVerifier, EffectVerificationResult

class LoggingEffectVerifier(BaseEffectVerifier):
    """Verifies logging configuration produces actual log files."""

    # TIGHT PATTERNS - Only exact patterns used in production
    FILE_HANDLER_PATTERNS = [
        # From strawberry_validator.py - exact pattern
        re.compile(r'FileHandler\(["\']([^"\']+)["\']\)'),
        # Variant with Path object
        re.compile(r'FileHandler\(Path\(["\']([^"\']+)["\']\)\)'),
    ]

    SKIP_PATTERNS = [
        # Conditional logging - user explicitly disabled
        re.compile(r'if\s+.*:\s*.*log', re.IGNORECASE),
        # Environment-based paths - dynamic configuration
        re.compile(r'os\.getenv\(["\']LOG', re.IGNORECASE),
        # Commented out examples
        re.compile(r'#.*FileHandler', re.IGNORECASE),
    ]

    @classmethod
    def detect(cls, content: str, file_path: str) -> Dict[str, Any] | None:
        """Detect logging configuration in file."""
        # Skip non-code files
        if not file_path.endswith(('.py',)):
            return None

        # Check skip patterns first
        for pattern in cls.SKIP_PATTERNS:
            if pattern.search(content):
                return None

        # Detect FileHandler patterns
        for pattern in cls.FILE_HANDLER_PATTERNS:
            matches = pattern.finditer(content)
            for match in matches:
                log_path = match.group(1)
                return {
                    "effect_type": "logging",
                    "log_path": log_path,
                    "pattern_matched": match.group(0),
                    "line_number": content[:match.start()].count('\n') + 1,
                }

        return None

    @classmethod
    def verify(cls, effect_config: Dict[str, Any], file_path: str) -> EffectVerificationResult:
        """Verify log file is created and configured correctly."""
        log_path = effect_config.get("log_path", "")

        if not log_path:
            return EffectVerificationResult(
                effect_type="logging",
                detected=True,
                verified=False,
                matched_config=effect_config,
                warning_message="Logging configuration detected but log path not found",
                suggestion="Ensure FileHandler has explicit path argument"
            )

        # Resolve relative path
        hooks_dir = Path(file_path).parent
        full_log_path = hooks_dir / log_path

        # Check if log file exists
        if not full_log_path.exists():
            return EffectVerificationResult(
                effect_type="logging",
                detected=True,
                verified=False,
                matched_config=effect_config,
                warning_message=f"Logging configured for {log_path} but file doesn't exist",
                suggestion=f"1. Run code that writes logs\n2. Verify file created at {full_log_path}\n3. Check structlog.configure() includes FileHandler"
            )

        # Check file has recent content (modified in last hour)
        import time
        age_seconds = time.time() - full_log_path.stat().st_mtime
        if age_seconds > 3600:
            return EffectVerificationResult(
                effect_type="logging",
                detected=True,
                verified=False,
                matched_config=effect_config,
                warning_message=f"Log file exists but stale (last modified {age_seconds//60} minutes ago)",
                suggestion="Run code that writes logs to verify logging works"
            )

        # All checks passed
        return EffectVerificationResult(
            effect_type="logging",
            detected=True,
            verified=True,
            matched_config=effect_config,
            warning_message=None,
            suggestion=None
        )
```

#### 3. Observable Effect Verifier (`posttooluse/observable_effect_verifier.py`)

```python
from posttooluse.base import PostToolUseHook
from pathlib import Path
import os

class ObservableEffectVerifier(PostToolUseHook):
    """Post-implementation verification that code changes produce intended effects."""

    env_var = "SEV_ENABLED"
    default_enabled = True
    tool_matcher = {"Edit", "Write"}  # Only check code modifications

    def __init__(self):
        super().__init__()
        # Register effect verifiers (extensible)
        self.effect_verifiers = {
            "logging": LoggingEffectVerifier,
            # Future: "state": StateEffectVerifier,
            # Future: "process": ProcessEffectVerifier,
            # Future: "api": APIEffectVerifier,
        }

    def process(self, tool_name: str, tool_input: dict, tool_response: dict) -> dict:
        """Process tool use and verify effects."""
        file_path = tool_input.get("file_path", "")

        if not file_path:
            return {"passed": True, "tracked": False}

        # Read file content
        try:
            content = Path(file_path).read_text()
        except Exception:
            return {"passed": True, "tracked": False}

        warnings = []

        # Check each effect verifier
        for effect_type, verifier_class in self.effect_verifiers.items():
            # Detect effect
            effect_config = verifier_class.detect(content, file_path)

            if effect_config:
                # Verify effect works
                result = verifier_class.verify(effect_config, file_path)

                if result.detected and not result.verified:
                    warnings.append({
                        "effect_type": result.effect_type,
                        "warning": result.warning_message,
                        "suggestion": result.suggestion,
                        "config": result.matched_config,
                    })

        if warnings:
            # Return warning message
            warning_lines = ["⚠️ Observable Effect Verification Warnings:\n"]
            for w in warnings:
                warning_lines.append(f"\n**{w['effect_type'].upper()} Effect:**")
                warning_lines.append(f"{w['warning']}")
                if w['suggestion']:
                    warning_lines.append(f"\nSuggestion:\n{w['suggestion']}")

            injection = "\n".join(warning_lines)
            return {
                "passed": False,
                "tracked": True,
                "injection": injection
            }

        return {"passed": True, "tracked": True}
```

#### 4. Unverified Stance Hook (`StopHook_unverified_stance.py`)

**Extension of existing unverified_stance_detector.py**:

```python
#!/usr/bin/env python3
"""
StopHook_unverified_stance.py - Detects skeptical stance without verification.

Extends anti_sycophancy/unverified_stance_detector.py with skeptical patterns.

NEW PATTERNS (warn-only mode):

**Skeptical Stance Patterns** (doubt/hedging without verification):
- "That sounds high/low/unlikely" - Doubting quantities without verification
- "I doubt that's accurate" - Casting doubt without evidence
- "Let me verify" - Empty hedging without actual verification
- "I'm not sure that's correct" - Uncertainty without checking

**Unfounded System Behavior Claims** (confident factual assertions without verification):
- "Since the PreToolUse hook blocks X" - Claiming hook behavior without verification
- "Because the hook won't allow X" - Asserting restrictions without checking
- "Due to the limitation on X" - Citing limitations as fact without evidence
- "Can't access X because of Y" - Blocking claims without verification

**This second category** catches the exact failure mode from your scenario:
- ❌ "Since the PreToolUse hook blocks direct config.json access, I need to..."
- ✅ Pattern matches: `r"since (the )?(pretooluse|hook|system|gate) (blocks|prevents|restricts|denies)"`
- ✅ No verification tools (Read, Grep, Glob) used in current turn
- ✅ Warning injected: "Your response contains an unverified claim about system behavior"

INTEGRATION:
- Extends: unverified_stance_detector.py
- Adds: Skeptical stance patterns (beyond sycophantic doubt)
- Output: additionalContext injection (warn-only mode)
"""

import json
import os
import re
import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).parent
sys.path.insert(0, str(HOOKS_DIR))

from anti_sycophancy.unverified_stance_detector import (
    detect_unverified_stance,
    StanceMatch,
    VERIFICATION_TOOLS,
)

# NEW: Skeptical stance patterns (beyond existing detector)
SKEPTICAL_PATTERNS = [
    r"that sounds (high|low|unlikely|unreasonable)",
    r"i doubt (that|this|those)",
    r"i can't confirm (that|this)",
    r"i'm not sure (that|this) is (accurate|correct|right)",
    r"seems (unlikely|off|wrong)",
    r"appears (inflated|wrong|incorrect)",
]

# NEW: Unfounded system behavior claims (confident factual assertions without verification)
# These catch cases where AI states "X blocks Y" or "due to Z restriction" without actually checking
UNFOUNDED_SYSTEM_CLAIM_PATTERNS = [
    # "Since the PreToolUse hook blocks X"
    r"since (the )?(pretooluse|hook|system|gate) (blocks|prevents|restricts|denies)",
    # "Because the hook won't allow X"
    r"because (the )?(hook|gate|validator|restriction) (won'?t allow|blocks|prevents)",
    # "Due to the limitation on X"
    r"due to (the )?(limitation|restriction|block|gate) (on|for|of)",
    # "Can't access X because of Y"
    r"can('t|cannot) access .+ (because|due to) (the )?(hook|system|restriction)",
]

# Combined pattern set for detection
ALL_UNVERIFIED_PATTERNS = SKEPTICAL_PATTERNS + UNFOUNDED_SYSTEM_CLAIM_PATTERNS

# Configuration
ENABLED = os.environ.get("UNVERIFIED_STANCE_ENABLED", "true").lower() == "true"
MODE = os.environ.get("UNVERIFIED_STANCE_MODE", "warn")  # "warn" or "block"

def _check_skeptical_stance(response: str) -> str | None:
    """Check for skeptical stance and unfounded system claim patterns."""
    normalized = ' '.join(response.lower().split())

    for pattern in ALL_UNVERIFIED_PATTERNS:
        if re.search(pattern, normalized):
            return pattern

    return None

def _distinguish_valid_explanation(response: str, tools_used: list) -> bool:
    """
    Distinguish between valid technical explanations and unfounded claims.

    This function prevents false positives where AI explains technical constraints
    after having verified them.

    VALID examples (should NOT flag - verification tools were used):
    - "The hook checks for X in the config file, as shown in the Read above"
    - "Due to the architecture limitation shown in Grep results, we need to..."
    - "Because the system uses Y (verified in Read), we must..."

    INVALID examples (SHOULD flag - no verification tools used):
    - "Since the hook blocks X, I need to..." (assertion without Read/Grep)
    - "Because the gate won't allow access" (assertion without checking)
    - "Due to the limitation on X" (citing limitation as fact without evidence)

    Key distinction:
    - EXPLANATION: Describes why/how something works, WITH verification evidence present
    - ASSERTION: States behavior as fact WITHOUT verification tools used

    Args:
        response: The AI's response text
        tools_used: List of tool names used this turn (e.g., ["Read", "Grep", "Glob"])

    Returns:
        True if this is a valid explanation (verification tools present), False otherwise
    """
    # If verification tools were used, this is likely a valid explanation
    verification_tools = {"Read", "Grep", "Glob", "WebSearch", "WebFetch", "Bash"}
    has_verification = any(tool in tools_used for tool in verification_tools)

    if has_verification:
        return True  # Verified explanation is valid

    # No verification tools used - this is an unfounded assertion
    return False

def generate_verdict(match: StanceMatch | None, skeptical_match: str | None) -> dict:
    """Generate verdict from stance detection."""
    if not match and not skeptical_match:
        return {"allow": True}

    message = "⚠️ UNVERIFIED STANCE DETECTED\n\n"

    if match:
        message += f"Pattern: {match.matched}\n\n"
        message += match.self_prompt
    elif skeptical_match:
        # Determine if this is a system claim or skeptical stance
        is_system_claim = any(
            pattern.search(skeptical_match)
            for pattern in UNFOUNDED_SYSTEM_CLAIM_PATTERNS
        )

        if is_system_claim:
            # Unfounded system behavior claim
            message += f"Your response contains an **unverified claim about system behavior**:\n\n"
            message += f"\"{skeptical_match}\"\n\n"
            message += "But you used no verification tools (Read, Grep, Glob, WebSearch, WebFetch, Bash) this turn.\n\n"
            message += "**This is a confident factual assertion about how the system works.**\n\n"
            message += "1. Did you actually verify this claim (e.g., Read the hook file, Grep for the restriction)?\n"
            message += "2. If you don't know, say \"I'll check if that's true\" — don't state assumptions as facts.\n"
            message += "3. If you want to proceed, verify first, then explain.\n\n"
            message += "**Example correct pattern**:\n"
            message += "- ❌ \"Since the hook blocks access, I need to...\" [UNVERIFIED]\n"
            message += "- ✅ \"Let me check if the hook actually blocks access...\" [GOOD]\n"
            message += "- ✅ \"The hook checks for X (shown in Read), so I need to...\" [VERIFIED]"
        else:
            # Skeptical stance (doubt/hedge)
            message += f"Your response contains a skeptical stance: \"{skeptical_match}\"\n\n"
            message += "But you used no verification tools (WebSearch, WebFetch, Bash) this turn.\n\n"
            message += "1. Did you actually check this claim, or are you hedging?\n"
            message += "2. If you don't know, say \"I don't know\" — don't imply the user is wrong.\n"
            message += "3. If you want to verify, actually call verification tools first.\n\n"
            message += "The user's claim may be correct. Don't cast doubt without evidence."

    if MODE == "warn":
        return {"allow": True, "reason": message}
    else:
        return {"allow": False, "reason": message}

def main():
    """Main hook entry point."""
    if not ENABLED:
        print(json.dumps({"allow": True, "reason": "Hook disabled"}))
        sys.exit(0)

    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        print(json.dumps({"allow": True, "reason": "Invalid JSON"}))
        sys.exit(0)

    # Extract response and context
    response = input_data.get("response", "")
    transcript = input_data.get("transcript", [])
    tools_used = [t.get("name", "") for t in input_data.get("toolUse", []) if isinstance(t, dict)]

    # Run existing detector
    data = {
        "transcript": transcript,
        "tools_used": tools_used,
    }
    match = detect_unverified_stance(response, data)

    # Check for skeptical stance or unfounded system claims
    skeptical_match = _check_skeptical_stance(response)

    # Additional check: Is this a valid technical explanation?
    # If verification tools were used, this is likely valid (not unfounded)
    is_valid_explanation = _distinguish_valid_explanation(response, tools_used)

    # Generate verdict (skip if valid explanation detected)
    if skeptical_match and is_valid_explanation:
        # Pattern matched but verification tools present - this is OK
        skeptical_match = None  # Clear the match

    verdict = generate_verdict(match, skeptical_match)

    print(json.dumps(verdict))

    if not verdict["allow"]:
        print(verdict["reason"], file=sys.stderr)
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
```

---

## 6. Implementation Plan

### Phase 1: Foundation (Logging Effect Only)

**Goal**: Implement SEV system with logging effect verifier in warn-only mode.

#### Task 1: Create base effect verifier infrastructure
**File**: `P:\.claude\hooks\posttooluse\effects\base_effect.py`

**Actions**:
1. Create `effects/` subdirectory under `posttooluse/`
2. Create `base_effect.py` with `BaseEffectVerifier` abstract class
3. Define `EffectVerificationResult` dataclass

**Acceptance Criteria**:
- Abstract base class defined with `detect()` and `verify()` methods
- `EffectVerificationResult` dataclass with all required fields
- Follows existing scanner pattern from `scanners/base_scanner.py`

**Verification Command**:
```bash
python -c "from posttooluse.effects.base_effect import BaseEffectVerifier, EffectVerificationResult; print('✓ Base classes imported')"
```

#### Task 2: Implement logging effect verifier
**File**: `P:\.claude\hooks\posttooluse\effects\logging_effect.py`

**Actions**:
1. Implement `LoggingEffectVerifier` class extending `BaseEffectVerifier`
2. Add tight detection patterns (FileHandler with string literals)
3. Add skip patterns (conditional logging, env vars)
4. Implement `verify()` method to check log file existence

**Acceptance Criteria**:
- Detects `FileHandler("file.log")` pattern
- Skips conditional logging (if DEBUG: log...)
- Checks log file exists after code runs
- Checks log file has recent content (<1 hour old)
- Returns structured `EffectVerificationResult`

**Verification Command**:
```bash
python -c "
from posttooluse.effects.logging_effect import LoggingEffectVerifier
content = 'handler = FileHandler(\"test.log\")'
result = LoggingEffectVerifier.detect(content, 'test.py')
print(f'Detected: {result}')
"
```

#### Task 3: Implement observable effect verifier hook
**File**: `P:\.claude\hooks\posttooluse\observable_effect_verifier.py`

**Actions**:
1. Create `ObservableEffectVerifier` class extending `PostToolUseHook`
2. Register logging effect verifier
3. Implement `process()` method to detect and verify effects
4. Generate warning messages for failed verifications

**Acceptance Criteria**:
- Extends `PostToolUseHook` base class
- Reads file content after Edit/Write operations
- Runs all registered effect verifiers
- Returns warning via `additionalContext` for failed effects
- Env var `SEV_ENABLED` controls hook

**Verification Command**:
```bash
echo '{"tool_name": "Write", "tool_input": {"file_path": "test.py"}, "tool_response": {}}' | \
  python P:\.claude\hooks\posttooluse\observable_effect_verifier.py
```

#### Task 4: Register SEV in PostToolUse router
**File**: `P:\.claude\hooks\posttooluse\__init__.py`

**Actions**:
1. Import `ObservableEffectVerifier`
2. Register in `create_registry()` function
3. Set priority (after reflexion_verifier, before lint)

**Acceptance Criteria**:
- Hook registered in router
- Runs on Edit/Write operations
- Appears in hook execution logs

**Verification Command**:
```bash
python -c "
from posttooluse import create_registry
registry = create_registry()
print(f'Registered hooks: {len(registry._hooks)}')
print('observable_effect_verifier' in registry._hooks)
"
```

### Phase 2: Unverified Stance Detection (Stop Hook)

**Goal**: Extend unverified stance detection with skeptical patterns.

#### Task 5: Create unverified stance Stop hook
**File**: `P:\.claude\hooks\StopHook_unverified_stance.py`

**Actions**:
1. Create Stop hook extending `unverified_stance_detector.py`
2. Add skeptical stance patterns (beyond sycophantic doubt)
3. Implement warn/block modes via env var
4. Inject warning via additionalContext

**Acceptance Criteria**:
- Detects "that sounds high/low" without verification
- Detects "i doubt that" without verification
- Allows stance when verification tools used
- Warn-only mode by default (`UNVERIFIED_STANCE_MODE=warn`)
- Env var `UNVERIFIED_STANCE_ENABLED` controls hook

**Verification Command**:
```bash
echo '{"response": "That sounds high.", "toolUse": [], "transcript": []}' | \
  python P:\.claude\hooks\StopHook_unverified_stance.py
```

#### Task 6: Register unverified stance Stop hook
**File**: `P:\.claude\settings.json` (or Stop router)

**Actions**:
1. Add hook to Stop hooks list in settings.json
2. Set default mode to warn
3. Enable hook by default

**Acceptance Criteria**:
- Hook runs on Stop event
- Warns about skeptical stance without verification
- Doesn't block in warn mode

**Verification Command**:
```bash
# Check settings.json has Stop hook registered
grep -A5 '"Stop"' P:\.claude\settings.json | grep "unverified_stance"
```

### Phase 3: Testing and Documentation

**Goal**: Comprehensive test coverage and documentation.

#### Task 7: Create unit tests for SEV
**File**: `P:\.claude\hooks\tests\test_observable_effect_verifier.py`

**Actions**:
1. Test logging effect detection
2. Test effect verification (pass/fail scenarios)
3. Test skip patterns (conditional, env vars)
4. Test router integration

**Acceptance Criteria**:
- 15+ tests covering all scenarios
- All tests pass
- Test synthetic hook input

**Verification Command**:
```bash
pytest P:\.claude\hooks\tests\test_observable_effect_verifier.py -v
```

#### Task 8: Create unit tests for unverified stance hook
**File**: `P:\.claude\hooks\tests\test_unverified_stance_hook.py`

**Actions**:
1. Test skeptical stance detection
2. Test verification tool exception
3. Test warn vs block modes
4. Test integration with existing detector

**Acceptance Criteria**:
- 10+ tests covering all scenarios
- All tests pass
- Tests verify warning messages

**Verification Command**:
```bash
pytest P:\.claude\hooks\tests\test_unverified_stance_hook.py -v
```

#### Task 9: Update documentation
**Files**:
- `P:\.claude\hooks\CLAUDE.md` (add SEV section)
- `P:\.claude\hooks\README.md` (update hooks catalog)
- `P:\.claude\hooks\scanners\README.md` (document SEV pattern)

**Actions**:
1. Document SEV architecture in CLAUDE.md
2. Add hook to README.md catalog
3. Document extensible effect pattern
4. Add troubleshooting section

**Acceptance Criteria**:
- CLAUDE.md has SEV section with architecture diagram
- README.md lists both hooks
- scanners/README.md documents extensible pattern

---

## 7. Risks, Success Criteria, Dependencies

### Risks and Mitigations

#### Risk 1: False Positives (SEV warns on working code)

**Likelihood**: Medium
**Impact**: Medium
**Risk Score**: 6

**Prevent**:
- Start with **tight detection patterns** (only exact patterns actually used)
- Warn-only mode initially (don't block work)
- User can disable via `SEV_ENABLED=false`

**Warning**: Monitor logs for false positive patterns
**Owner**: Implementation team

#### Risk 2: Performance Overhead (PostToolUse slowdown)

**Likelihood**: Low
**Impact**: Medium
**Risk Score**: 3

**Prevent**:
- In-process execution via router (~5-10ms)
- File reading only on Edit/Write operations
- Skip detection with tool_matcher

**Warning**: Router latency >20ms
**Owner**: Implementation team

#### Risk 3: Noisy Warnings (Unverified stance over-detects)

**Likelihood**: Medium
**Impact**: Medium
**Risk Score**: 6

**Prevent**:
- Tight pattern matching (exact phrases, not broad)
- Check for verification tools before flagging
- Warn-only mode initially

**Warning**: User complaints about noise
**Owner**: Implementation team

#### Risk 4: State Corruption (Multi-terminal file access)

**Likelihood**: Low
**Impact**: High
**Risk Score**: 6

**Prevent**:
- Use terminal/session isolation from `evidence_store.py`
- No cross-process state in SEV hook
- Fresh registry per invocation

**Warning**: Evidence store corruption
**Owner**: Implementation team

### Success Criteria

**Functional Requirements**:
- ✅ SEV detects logging configuration without FileHandler
- ✅ SEV warns when log file doesn't exist
- ✅ Unverified stance detects skeptical patterns
- ✅ Both hooks in warn-only mode by default
- ✅ Env vars control both hooks

**Quality Requirements**:
- ✅ Zero false positives on tight patterns
- ✅ <10ms latency for SEV (in-process)
- ✅ 25+ tests with 100% pass rate
- ✅ Documentation updated in CLAUDE.md

**Integration Requirements**:
- ✅ SEV registered in PostToolUse router
- ✅ Unverified stance in Stop hooks
- ✅ No blocking in warn mode
- ✅ Graceful failure (hook errors don't crash router)

### Dependencies

**Internal**:
- `posttooluse.base.PostToolUseHook` - Base class for PostToolUse hooks
- `anti_sycophancy.unverified_stance_detector` - Existing stance detector
- `evidence_store` - Session/terminal isolation

**External**:
- None (no new dependencies)

**Environment Variables**:
- `SEV_ENABLED=true|false` - Enable SEV hook
- `SEV_MODE=warn|block` - SEV mode (warn-only initially)
- `UNVERIFIED_STANCE_ENABLED=true|false` - Enable unverified stance hook
- `UNVERIFIED_STANCE_MODE=warn|block` - Stance detection mode (warn-only initially)

### Rollback Strategy

**If SEV causes issues**:
1. Set `SEV_ENABLED=false` to disable
2. Remove from router registry
3. Delete `posttooluse/observable_effect_verifier.py`

**If unverified stance causes issues**:
1. Set `UNVERIFIED_STANCE_ENABLED=false` to disable
2. Remove from settings.json Stop hooks
3. Delete `StopHook_unverified_stance.py`

**Rollback Time**: <5 minutes (env var change)

---

## Implementation Timeline

**Phase 1** (Foundation): Tasks 1-4 - ~4 hours
- Task 1: Base infrastructure (30 min)
- Task 2: Logging effect verifier (2 hours)
- Task 3: Observable effect verifier (1 hour)
- Task 4: Router registration (30 min)

**Phase 2** (Stance Detection): Tasks 5-6 - ~2 hours
- Task 5: Unverified stance hook (1.5 hours)
- Task 6: Stop hook registration (30 min)

**Phase 3** (Testing & Docs): Tasks 7-9 - ~3 hours
- Task 7: SEV tests (1.5 hours)
- Task 8: Stance detection tests (1 hour)
- Task 9: Documentation (30 min)

**Total Estimated Time**: ~9 hours

---

## Pre-Mortem Analysis

**Imagine**: 6 months from now, the SEV system has failed. Why?

### Potential Failure Modes

1. **False Positives Killed Adoption**:
   - **Cause**: Warned too much on valid code, users disabled it
   - **Prevention**: Start with tight patterns, warn-only mode, monitor false positive rate
   - **Warning Sign**: >30% warnings are false positives

2. **Performance Degradation**:
   - **Cause**: File I/O on every Edit/Write slowed down workflow
   - **Prevention**: In-process execution, tool_matcher filtering, performance monitoring
   - **Warning Sign**: Router latency >20ms

3. **Noisy Stance Detection**:
   - **Cause**: Over-detection of skeptical language, user complaints
   - **Prevention**: Tight pattern matching, verification tool check, warn-only mode
   - **Warning Sign**: User reports "too many false warnings"

4. **Integration Conflicts**:
   - **Cause**: SEV conflicted with other PostToolUse hooks
   - **Prevention**: Fresh registry per invocation, isolated state
   - **Warning Sign**: Hook crashes or router failures

### Monitoring Plan

**Metrics to Track**:
- False positive rate (warnings that are incorrect)
- Router latency (should stay <20ms)
- Warning frequency (should decrease over time)
- User complaints (qualitative)

**Review Cadence**: Weekly for first month, then monthly

---

**Next Actions** (in order):
1. Review and approve this plan
2. Run `/plan-workflow review P:\.claude\hooks\plans\plan-20260304-observable-effect-verification.md`
3. Address any verifier feedback (HALT conditions)
4. Begin Phase 1 implementation when plan is READY-FOR-IMPLEMENTATION
