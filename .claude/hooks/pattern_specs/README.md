# Pattern Specifications

**Purpose:** Semantic definitions and validation rules for pattern-based constitutional hooks.

## Overview

Pattern specifications provide machine-readable documentation of regex patterns used in hooks. Each spec file (`*_spec.py`) defines:

- **Semantic definition** - What the pattern detects and why it matters constitutionally
- **Positive examples** - Examples that SHOULD trigger the pattern (10+ required)
- **Negative examples** - Examples that should NOT trigger (5+ required)
- **Patterns** - The actual regex patterns with names
- **Validation rules** - Minimum requirements for spec quality
- **WHY category** - Constitutional principle the pattern enforces

## Specification Format

Each `*_spec.py` file must export a `PATTERN_SPEC` dict:

```python
PATTERN_SPEC = {
    "pattern_name": "short_identifier",
    "semantic_definition": """
        Multi-line description of what the pattern detects,
        constitutional significance, and edge cases.
    """,

    "positive_examples": [
        "Example triggering pattern 1",
        "Example triggering pattern 2",
        # ... 10+ examples required
    ],

    "negative_examples": [
        "Example that should NOT trigger (whitelined)",
        "Example of legitimate similar phrase",
        # ... 5+ examples required
    ],

    "patterns": [
        (r"regex_pattern", "pattern_name"),
        # ... pattern list
    ],

    "validation_rules": {
        "min_positive_examples": 10,
        "min_negative_examples": 5,
        "max_pattern_complexity": 5,
        "require_semantic_definition": True,
        "require_pattern_name": True,
    },

    "whitelist_patterns": [
        r"exception_pattern_1",
        r"exception_pattern_2",
    ],

    "notes": """
        Implementation notes, constitutional alignment,
        integration points, and edge case handling.
    """,
}
```

## Validation Rules

Specs must meet these criteria to be considered valid:

| Rule | Requirement | Purpose |
|------|-------------|---------|
| `min_positive_examples` | ≥10 | Ensure pattern is well-tested |
| `min_negative_examples` | ≥5 | Prevent false positives |
| `max_pattern_complexity` | ≤5 | Keep regex maintainable |
| `require_semantic_definition` | True | Document constitutional WHY |
| `require_pattern_name` | True | Enable traceability |

**Complexity scoring:**
- 1 point per capturing group `(...)`
- 1 point per lookahead/lookbehind `(?=...)` / `(?<=...)`
- 1 point per nested quantifier `(?:...)+`
- Maximum score: 5 (simple, maintainable patterns)

## WHY Categories

Pattern specs must reference their constitutional alignment:

| Category | Description | Example Pattern |
|----------|-------------|-----------------|
| `Solo-Dev Authority` | Claude can't decide to skip work | scope_reduction |
| `Truthfulness` | Detect speculation or fabrication | empirical_claims_gate |
| `TDD Compliance` | Enforce test-first development | tdd_gate |
| `Path Protection` | Prevent destructive operations | deny_root_write |
| `Investigation First` | Require diagnosis before solution | speculation_gate |

## Available Specifications

### `scope_reduction_spec.py`

**Pattern Count:** 8 patterns
**WHY Category:** Solo-Dev Authority
**Constitutional Principle:** Complete all stages unless user explicitly requests otherwise

**Patterns:**
1. `skip_with_effort_reason` - Skipping stages due to time/effort
2. `time_consuming_claim` - Claiming a stage is too time-consuming
3. `premature_satisfaction` - Claiming current results are "enough"
4. `unauthorized_continuation` - Proceeding without user approval
5. `unauthorized_omission` - Omitting work to save time/effort
6. `unauthorized_deferral` - Deferring work without user request
7. `sufficiency_judgment` - Claiming something "should be sufficient"
8. `unauthorized_deferral_alt` - "Rest can be done later" without user context

**Integration:** `StopHook_scope_reduction.py`

## Creating New Specifications

When adding pattern-based hooks:

1. **Create spec file** in `pattern_specs/` directory
2. **Follow format** - Export `PATTERN_SPEC` dict with all required fields
3. **Test examples** - Include 10+ positive, 5+ negative examples
4. **Document WHY** - Reference constitutional category and principle
5. **Validate** - Run `PreToolUse_pattern_sanity_check.py` to verify

**Example:**

```python
# pattern_specs/my_pattern_spec.py
PATTERN_SPEC = {
    "pattern_name": "my_pattern",
    "semantic_definition": "Detects...",
    "positive_examples": [...],  # 10+
    "negative_examples": [...],  # 5+
    "patterns": [(r"pattern", "name")],
    "validation_rules": {...},
    "notes": "Constitutional alignment: ...",
}
```

## Dynamic Loading

Pattern specs are automatically discovered by `PreToolUse_pattern_sanity_check.py`:

```python
# Automatically loads all *_spec.py files in pattern_specs/
import glob
for spec_file in glob.glob("pattern_specs/*_spec.py"):
    spec_module = __import__(f"pattern_specs.{Path(spec_file).stem}")
```

**Benefits:**
- Extensible: Add new specs without modifying hook code
- Self-documenting: Specs are executable documentation
- Testable: Examples serve as test cases

## Validation Hook

`PreToolUse_pattern_sanity_check.py` validates specs when pattern-based hooks are used:

**Checks:**
- Semantic definition exists
- Minimum example counts met
- Pattern complexity within limits
- Pattern names are unique
- Patterns match their positive examples
- Patterns don't match negative examples

**Failure Mode:** Blocks the tool use with detailed error message

## Development Workflow

```bash
# 1. Create new spec
vim pattern_specs/new_pattern_spec.py

# 2. Test pattern matches (optional)
python -c "
from pattern_specs.new_pattern_spec import PATTERN_SPEC
import re
for pattern, name in PATTERN_SPEC['patterns']:
    print(f'{name}: {len([ex for ex in PATTERN_SPEC['positive_examples'] if re.search(pattern, ex)])} / {len(PATTERN_SPEC['positive_examples'])} matches')
"

# 3. Verify with hook
echo '{"toolInput": {"name": "Write", "path": "pattern_specs/new_pattern_spec.py"}}' | python PreToolUse_pattern_sanity_check.py

# 4. Run test suite
python tests/test_pattern_sanity.py
```

## Constitutional Alignment

All pattern specs must:

1. **Reference WHY category** - Link to constitutional principle
2. **Document enforcement** - Explain how pattern is enforced
3. **Fail fast** - No graceful degradation for violations
4. **Traceable** - Pattern names appear in block messages

**Example:**

```python
"notes": """
    Constitutional Alignment:
    - WHY: Solo-Dev Authority (Claude cannot decide to skip work)
    - Fails fast: Blocks immediately upon pattern match
    - No graceful degradation: Scope reduction is a hard violation
    - Integration: StopHook_scope_reduction.py blocks completion
"""
```

## See Also

- `StopHook_scope_reduction.py` - Pattern usage example
- `PreToolUse_pattern_sanity_check.py` - Validation hook
- `tests/test_pattern_sanity.py` - Test suite
- `ARCHITECTURE.md` - Constitutional enforcement mapping
- `PROTOCOL.md` - Hook input/output specifications
