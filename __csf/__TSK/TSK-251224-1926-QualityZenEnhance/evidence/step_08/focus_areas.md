# Focus Area Mapping Feature Documentation

**Feature**: Focus Area Expansion with Backward Compatibility
**Version**: 1.1.0
**Date**: 2024-12-24
**Status**: ✅ Implemented (Q1-Q2 Complete)

---

## Overview

The Focus Area Mapping feature enables transparent backward compatibility between the legacy quality system (3 focus areas) and the enhanced zen review system (12 categories). This allows existing configurations to work unchanged while enabling access to all available review categories.

---

## Background

### Legacy System (Pre-1.1.0)
The quality system originally used 3 focus areas for Gate 6 code review:
- `design` - Code design and architecture
- `clarity` - Code clarity and readability
- `reasoning` - Logic and reasoning quality

### Enhanced Zen System (1.1.0+)
The zen code review system supports 12 comprehensive review categories:
- `security` - Security vulnerabilities and risks
- `bugs` - Bug detection and potential issues
- `error_handling` - Exception handling quality
- `configuration` - Configuration management
- `performance` - Performance optimization
- `concurrency` - Concurrent programming issues
- `code_quality` - General code quality
- `testing` - Test coverage and quality
- `api_design` - API interface design
- `type_safety` - Type hinting and safety
- `dependencies` - Dependency management
- `documentation` - Documentation quality
- `architecture` - Architecture patterns (added)

---

## Focus Area Mapping

### Mapping Table

| Legacy Category | Zen Category | Description |
|----------------|--------------|-------------|
| `design` | `code_quality` | Code design and quality standards |
| `clarity` | `documentation` | Code clarity and documentation |
| `reasoning` | `architecture` | Logic and architectural patterns |
| `security` | `security` | Security vulnerabilities (no mapping needed) |
| `performance` | `performance` | Performance issues (no mapping needed) |
| `bugs` | `bugs` | Bug detection (no mapping needed) |
| `architecture` | `architecture` | Architecture patterns (no mapping needed) |
| `api_design` | `api_design` | API design (no mapping needed) |
| `testing` | `testing` | Testing quality (no mapping needed) |
| `type_safety` | `type_safety` | Type safety (no mapping needed) |
| `error_handling` | `error_handling` | Error handling (no mapping needed) |
| `configuration` | `configuration` | Configuration (no mapping needed) |
| `dependencies` | `dependencies` | Dependencies (no mapping needed) |
| `concurrency` | `concurrency` | Concurrency (no mapping needed) |
| `code_quality` | `code_quality` | Code quality (no mapping needed) |
| `documentation` | `documentation` | Documentation (no mapping needed) |

### Implementation

The mapping is implemented in `enhanced_execution.py`:

```python
FOCUS_AREA_MAPPING = {
    # Legacy categories (3 original focus areas)
    'design': 'code_quality',          # Legacy 'design' → zen 'code_quality'
    'clarity': 'documentation',        # Legacy 'clarity' → zen 'documentation'
    'reasoning': 'architecture',       # Legacy 'reasoning' → zen 'architecture'

    # Direct mappings (zen categories available natively)
    'security': 'security',
    'bugs': 'bugs',
    'error_handling': 'error_handling',
    'configuration': 'configuration',
    'performance': 'performance',
    'concurrency': 'concurrency',
    'code_quality': 'code_quality',
    'testing': 'testing',
    'api_design': 'api_design',
    'type_safety': 'type_safety',
    'dependencies': 'dependencies',
    'documentation': 'documentation',
    'architecture': 'architecture',
}
```

---

## Usage

### Legacy Configuration (Backward Compatible)

Existing `.qual-gate.json` files continue to work:

```json
{
  "gates": {
    "code_review": {
      "review_mode": "mid",
      "focus_areas": ["design", "clarity", "reasoning"]
    }
  }
}
```

**Result**: Automatically translated to `["code_quality", "documentation", "architecture"]`

### New Zen Categories

Use all 12 categories directly:

```json
{
  "gates": {
    "code_review": {
      "review_mode": "mid",
      "focus_areas": [
        "security",
        "bugs",
        "error_handling",
        "configuration",
        "performance"
      ]
    }
  }
}
```

**Result**: Reviews use exact categories specified

### Mixed Legacy and Zen

Mix legacy and new categories:

```json
{
  "gates": {
    "code_review": {
      "review_mode": "mid",
      "focus_areas": ["design", "security", "clarity", "performance"]
    }
  }
}
```

**Result**: Translated to `["code_quality", "security", "documentation", "performance"]`

### CLI Usage

```bash
# Legacy focus areas (translated automatically)
qual-gate --focus-areas design clarity reasoning

# New zen categories
qual-gate --focus-areas security bugs error_handling configuration performance

# Mixed (legacy and zen)
qual-gate --focus-areas design security performance
```

---

## Behavior

### Translation Process

1. **Load Configuration**: Focus areas loaded from CLI, config file, or environment variables
2. **Apply Mapping**: Each focus area translated through `FOCUS_AREA_MAPPING`
3. **Deduplicate**: Remove duplicates while preserving order
4. **Log Translation**: Display translation if any legacy categories used

### Example Output

```
📋 Gate 6 Config: mode=mid, focus=['design', 'clarity', 'reasoning']
  🔄 Focus area mapping: design→code_quality, clarity→documentation, reasoning→architecture
```

### Edge Cases

- **Invalid Categories**: Pass through unchanged (zen adapter handles validation)
- **Empty List**: Uses defaults (`['design', 'clarity', 'reasoning']` → translated)
- **Duplicates**: Removed after translation
- **Case Sensitivity**: Categories are case-sensitive

---

## Testing

The focus area mapping feature has comprehensive TDD test coverage:

```bash
# Run all focus area tests
cd P:\__csf.nip\src\quality
pytest tests/test_enhanced_execution_focus_areas.py -v
```

### Test Coverage

- ✅ Mapping dictionary exists with all 12 categories
- ✅ Legacy category translations work correctly
- ✅ Executor applies focus area mapping
- ✅ All 12 zen categories supported
- ✅ Mixed legacy and zen categories work
- ✅ Config file loading with legacy focus areas
- ✅ Default focus areas are translated
- ✅ Invalid focus areas handled gracefully
- ✅ Empty focus areas use defaults

**Test Results**: 9/9 passed (100%)

---

## Migration Guide

### For Existing Users

No action required! Existing configurations work unchanged.

### To Enable New Categories

1. **Option 1: Update Config File**

   Edit `.qual-gate.json`:
   ```json
   {
     "gates": {
       "code_review": {
         "review_mode": "mid",
         "focus_areas": [
           "security", "bugs", "error_handling",
           "configuration", "performance"
         ]
       }
     }
   }
   ```

2. **Option 2: Use CLI**

   ```bash
   qual-gate --focus-areas security bugs error_handling configuration performance
   ```

3. **Option 3: Environment Variables**

   ```bash
   export QUAL_GATE_FOCUS_AREAS="security,bugs,error_handling,configuration,performance"
   qual-gate
   ```

---

## Review Modes

The zen system supports 3 review modes with default focus areas:

| Mode | Description | Default Focus Areas |
|------|-------------|---------------------|
| `chill` | Quick review (2 categories) | Security, Bugs |
| `mid` | Balanced review (5 categories) | Security, Bugs, Error Handling, Configuration, Performance |
| `chad` | Thorough review (12 categories) | All categories |

**Note**: The quality system defaults to `chill` mode. Use `--review-mode` to change.

---

## Future Enhancements

- [ ] Update default focus areas to use zen categories (currently uses legacy defaults)
- [ ] Add focus area validation with helpful error messages
- [ ] Add focus area aliases (e.g., `sec` → `security`)
- [ ] Add focus area groups (e.g., `basic` → security, bugs, error_handling)

---

## Related Documentation

- **Quality System Overview**: `P:\__csf.nip\src\quality\README.md`
- **Zen Code Review**: `P:\__csf.nip\docs\ZEN_USER_GUIDE.md`
- **TDD Tests**: `P:\__csf.nip\src\quality\tests\test_enhanced_execution_focus_areas.py`
- **Implementation Plan**: `.speckit/memory/TSK-251224-1926-QualityZenEnhance/plan.md`

---

## Questions?

For questions or issues:
1. Check test file for usage examples
2. Review implementation in `enhanced_execution.py:172-214`
3. Consult zen documentation for category details

---

**Document Version**: 1.0
**Last Updated**: 2024-12-24
**Status**: Production Ready ✅
