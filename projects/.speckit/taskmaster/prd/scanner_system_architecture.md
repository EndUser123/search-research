# Scanner System Architecture

## Overview

The scanner system provides fast, layered validation for the constitutional enforcer hook. It implements a 3-tier architecture that balances performance with comprehensive coverage.

## Directory Structure

```
P:/.claude/hooks/
├── constitutional_enforcer.py    # Main hook (v2.0.0 with scanner integration)
└── scanners/
    ├── __init__.py               # Module exports
    ├── base_scanner.py           # Abstract base class
    ├── pii_scanner.py            # PII and credential detection
    ├── reflexion_validator.py    # Multi-round validation
    ├── hallucination_scanner.py  # Ungrounded claim detection
    └── intent_drift_scanner.py   # Goal alignment tracking
```

## Base Scanner Pattern

All scanners inherit from `BaseScanner`:

```python
class BaseScanner(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def scan(self, text: str, context: dict = None) -> ScanResult: ...
```

### ScanResult Format

```python
@dataclass
class ScanResult:
    status: ScanStatus      # PASS, FAIL, SKIP
    scanner_name: str
    matched_text: str = ""
    reason: str = ""
    severity: str = "MEDIUM"  # HIGH, MEDIUM, LOW
    suggestion: str = ""
```

## Scanner Details

### 1. PII Scanner (`pii_scanner.py`)

**Purpose:** Detect credentials and personal data leakage

**Patterns detected:**
- API keys (OpenAI, Anthropic, GitHub, AWS, Slack, Aliyun)
- Bearer tokens and JWT
- Generic tokens, API keys, secrets
- Passwords
- Email addresses (optional)
- IP addresses (optional)
- SSN/SIN patterns
- Credit card numbers
- Database connection strings
- Private key PEM headers

**Performance:** ~1ms per scan (compiled regex)

**Configuration:**
```python
PIIScanner(
    enabled=True,
    exclude_low_severity=True  # Skip emails, IPs
)
```

### 2. Reflexion Validator (`reflexion_validator.py`)

**Purpose:** Multi-round validation to reduce false positives by ~40%

**Rounds:**
1. **Argument Round** - Checks if detected violation is true positive
   - Detects skeptical user prompts
   - Checks for sycophantic agreement
   - Identifies false positive patterns

2. **Audit Round** - Validates against constitutional principles
   - Checks for TRUTH violations (sycophancy, excuses)
   - Applies higher-level constitutional principles

**Performance:** ~100ms total (2 rounds)

**Configuration:**
```python
ReflexionValidator(
    enabled=True,
    max_rounds=2
)
```

### 3. Hallucination Scanner (`hallucination_scanner.py`)

**Purpose:** Detect ungrounded claims using NLI principles

**Patterns detected:**
- "should work" without execution evidence
- "ought to succeed" predictions
- Overconfident claims ("obviously", "clearly")
- Unverified generalizations
- File claims without verification
- Scope inflation ("all tests pass" without counts)

**Performance:** ~1ms per scan (regex + context checks)

**Configuration:**
```python
HallucinationScanner(
    enabled=True,
    strict_mode=False  # If True, flag more potential issues
)
```

### 4. Intent Drift Scanner (`intent_drift_scanner.py`)

**Purpose:** Track goal alignment and detect scope creep

**Metrics tracked:**
- Primary goal from context or session state
- Action history with timestamps
- Drift score per action (0.0 = aligned, 1.0 = drifted)

**Drift components:**
- Type drift (goal action vs current action)
- Scope drift (scope expansion patterns)
- New topic drift (unrelated topics introduced)

**Performance:** ~2ms per scan + file I/O for state

**Configuration:**
```python
IntentDriftScanner(
    enabled=True,
    threshold=0.6  # Block when drift > 0.6
)
```

## Integration Pattern

### In `constitutional_enforcer.py`:

```python
class ScannerValidator:
    def __init__(self):
        self.scanners = []  # Fast scanners
        self.reflexion_validator = None

    def validate_fast_scanners(self, response: str, context: dict) -> list:
        violations = []
        for scanner_name, scanner in self.scanners:
            result = scanner.scan(response, context)
            if not result.is_valid():
                violations.append({...})
        return violations

    def validate_reflexion_rounds(self, response: str, context: dict) -> list:
        # Multi-round validation
        ...
```

## Context Format

Scanners receive context dict with:

| Key | Type | Purpose |
|-----|------|---------|
| `prompt` | str | Original user prompt |
| `primary_goal` | str | Current session goal |
| `tools_used` | list | Tools called in response |
| `mentioned_files` | list | Files referenced |
| `command_outputs` | list | Execution outputs |
| `test_results` | list | Test results |

## Environment Variables

| Variable | Default | Effect |
|----------|---------|--------|
| `PII_SCANNER_ENABLED` | true | Enable/disable PII scanning |
| `REFLEXION_VALIDATOR_ENABLED` | true | Enable/disable multi-round validation |
| `HALLUCINATION_SCANNER_ENABLED` | true | Enable/disable ungrounded claim detection |
| `INTENT_DRIFT_SCANNER_ENABLED` | false | Enable/disable intent drift tracking |

## State Management

### Intent Drift State (`P:/.claude/session_data/intent_state.json`)

```json
{
  "primary_goal": "Fix the login bug",
  "goal_set_at": "2025-12-25T10:00:00Z",
  "action_history": [
    {
      "timestamp": "2025-12-25T10:05:00Z",
      "action": {"text": "Reading login.py", "action_type": "analyze"},
      "drift_score": 0.0
    }
  ]
}
```

## Adding New Scanners

1. Create scanner class inheriting from `BaseScanner`
2. Implement `name` property and `scan()` method
3. Return `ScanResult` with appropriate status
4. Add to `scanners/__init__.py` exports
5. Wire up in `ScannerValidator.__init__()`
6. Add environment variable control

Example:

```python
# scanners/my_scanner.py
from .base_scanner import BaseScanner, ScanResult, ScanStatus

class MyScanner(BaseScanner):
    @property
    def name(self) -> str:
        return "MyScanner"

    def scan(self, text: str, context: dict = None) -> ScanResult:
        if "bad_pattern" in text.lower():
            return ScanResult(
                status=ScanStatus.FAIL,
                scanner_name=self.name,
                matched_text="bad_pattern",
                reason="Bad pattern detected",
                severity="MEDIUM",
                suggestion="Remove the bad pattern"
            )
        return ScanResult(ScanStatus.PASS, self.name)
```
