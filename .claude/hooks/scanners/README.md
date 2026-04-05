# Scanners

Modular validation and analysis components for Claude Code hooks.

## Overview

Scanners are specialized validation modules that extend `BaseScanner` to provide consistent interfaces for detecting specific patterns or issues in text, tool outputs, and context.

## Base Architecture

All scanners extend the `BaseScanner` abstract base class:

```python
from scanners.base_scanner import BaseScanner, ScanResult, ScanStatus

class CustomScanner(BaseScanner):
    name = "custom_scanner"

    def scan(self, text: str, context: dict = None) -> ScanResult:
        # Validate text
        if issue_detected:
            return ScanResult(
                ScanStatus.FAIL,
                self.name,
                reason="Issue detected",
                severity="HIGH",
                matched_text="..."
            )
        return ScanResult(ScanStatus.PASS, self.name)
```

## Available Scanners

### Intent Drift Scanner

**File**: `intent_drift_scanner.py`

**Purpose**: Detects scope expansion and drift from original user intent.

**Detection Capabilities**:
- Scope expansion patterns ("also create/implement/build")
- Unintended feature additions
- Mission creep indicators

**Usage**:
```python
from scanners.intent_drift_scanner import IntentDriftScanner

scanner = IntentDriftScanner(enabled=True, threshold=0.6)
result = scanner.scan(current_response, original_intent=user_prompt)
```

---

### Hallucination Scanner

**File**: `hallucination_scanner.py`

**Purpose**: Detects hallucinated tool calls, commands, and API references.

**Detection Capabilities**:
- Non-existent tool mentions
- Invalid command invocations
- Fabricated API references

**Usage**:
```python
from scanners.hallucination_scanner import HallucinationScanner

scanner = HallucinationScanner(enabled=True)
result = scanner.scan(response_text, available_tools=tool_list)
```

---

### PII Scanner

**File**: `pii_scanner.py`

**Purpose**: Detects personally identifiable information in text.

**Detection Capabilities**:
- Email addresses
- Phone numbers
- Credit card numbers
- Social security numbers
- API keys and tokens

**Usage**:
```python
from scanners.pii_scanner import PIIScanner

scanner = PIIScanner(enabled=True)
result = scanner.scan(text_to_check)
```

---

### Agreement Consistency Scanner

**File**: `agreement_consistency_scanner.py`

**Purpose**: Validates consistency between agreements and implementations.

**Detection Capabilities**:
- Specification violations
- Contract breaches
- Promise tracking

---

### Reflexion Validator

**File**: `reflexion_validator.py`

**Purpose**: Validates reflexion patterns for self-correction and learning.

---

## ScanResult Structure

All scanners return a `ScanResult` object:

```python
@dataclass
class ScanResult:
    status: ScanStatus          # PASS, FAIL, SKIP
    scanner_name: str           # Name of the scanner
    reason: str = ""            # Explanation of result
    severity: str = "MEDIUM"     # LOW, MEDIUM, HIGH
    matched_text: str = ""      # Text that triggered the result
    suggestion: str = ""        # Suggested fix (for FAIL status)
```

## ScanStatus Enum

- `PASS`: No issues detected
- `FAIL`: Issue found that should block action
- `SKIP`: Scanner disabled or not applicable

## Integration Pattern

To integrate a scanner into a hook:

```python
from scanners.intent_drift_scanner import IntentDriftScanner
from scanners.base_scanner import ScanStatus

class MyHook:
    def __init__(self):
        self.scanner = IntentDriftScanner(enabled=True)

    def validate_response(self, response: str, context: dict) -> dict:
        result = self.scanner.scan(response, context)

        if result.status == ScanStatus.FAIL:
            return {
                "allow": False,
                "reason": result.reason,
                "suggestion": result.suggestion
            }

        return {"allow": True}
```

## Testing

Run scanner tests:

```bash
# Test all scanners
pytest P:\.claude\hooks\tests\ -v

# Test specific scanner
pytest P:\.claude\hooks\tests\test_intent_drift_scanner.py -v
```

## Creating New Scanners

1. Extend `BaseScanner`
2. Implement `scan(text, context)` method
3. Return `ScanResult` with appropriate status
4. Add unit tests in `../tests/`
5. Document in this README

**Template**:

```python
from scanners.base_scanner import BaseScanner, ScanResult, ScanStatus

class NewScanner(BaseScanner):
    """Description of what this scanner detects."""

    name = "new_scanner"

    def __init__(self, enabled: bool = True, **kwargs):
        super().__init__(enabled)
        # Custom initialization

    def scan(self, text: str, context: dict = None) -> ScanResult:
        if not self.enabled:
            return ScanResult(ScanStatus.SKIP, self.name)

        # Detection logic here
        if issue_found:
            return ScanResult(
                ScanStatus.FAIL,
                self.name,
                reason="Issue detected",
                severity="HIGH",
                suggestion="Fix suggestion"
            )

        return ScanResult(ScanStatus.PASS, self.name)
```

## Performance Guidelines

- **Fast checks**: Target <10ms for rule-based validation
- **LLM checks**: Target <500ms for API-based verification
- **Fail-open**: Graceful degradation when external services unavailable
- **Caching**: Cache expensive operations when appropriate

## See Also

- `../CLAUDE.md` - Hooks directory architecture
- `../ARCHITECTURE.md` - Constitutional enforcement mapping
- `../PROTOCOL.md` - Hook input/output specifications
