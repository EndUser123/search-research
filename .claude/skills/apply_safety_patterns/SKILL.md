---
name: apply_safety_patterns
description: Constitutionally compliant safety pattern application with proven success rates
version: "1.0.0"
status: stable
category: safety
triggers:
  - /apply-safety-patterns
  - "safety patterns"
  - "apply safety patterns"
aliases:
  - /apply-safety-patterns

suggest:
  - /comply
  - /bug-hunt
  - /validate-safety-patterns
---

# /apply-safety-patterns - Safety Pattern Application

## Purpose

Apply proven safety patterns to resolve systematic issues with full developer control and immediate file-based effects.

## Project Context

### Constitution/Constraints
- **Singular Decision Authority** - Developer maintains 100% control
- **No Background Services** - All functionality is command-driven
- **No Required Consensus** - No organizational decision requirements
- **Direct File Editing** - All changes are immediate file modifications
- **User Control** - Opt-out available for all features

### Technical Context
- Main documentation: `P:/__csf/src/csf/cli/nip/apply_safety_patterns.md`
- Success rates: database (95%), path (90%), json (98%), import (92%), hook (100%)
- Automatic backup creation before changes

### Architecture Alignment
- Part of safety and compliance skill family
- Integrates with /comply and /bug-hunt
- Supports /validate-safety-patterns for verification

## Your Workflow

1. **Issue Detection** - Automatic detection with evidence scoring
2. **Pattern Recommendation** - Evidence-based recommendations with success rates
3. **Interactive Approval** - User must approve each individual change
4. **Backup Creation** - Automatic backup before modifications
5. **Pattern Application** - Apply safety patterns to target files
6. **Validation and Reporting** - Comprehensive validation and reporting

## Validation Rules

### Prohibited Actions
- **NEVER apply changes without user approval** - interactive mode required
- **NEVER skip backup creation** - always preserve original state
- **NEVER claim fix without evidence** - show success rate data

### Required Output
- List detected issues with severity
- Show recommended patterns with success rates
- Confirm user approval before applying
- Report validation results after application

**Main documentation:** `P:/__csf/src/csf/cli/nip/apply_safety_patterns.md`

## Quick Start

```bash
# Apply all safety patterns with interactive approval
/apply-safety-patterns --interactive

# Apply specific category with user confirmation
/apply-safety-patterns --category=database --confirm

# Apply with dry-run to preview changes
/apply-safety-patterns --dry-run --verbose
```

## Safety Categories

| Category | Success Rate | Pattern | Issues Resolved |
|----------|-------------|---------|-----------------|
| database | 95% | `ensure_database()` before operations | `sqlite3.OperationalError` |
| path | 90% | Cross-platform path normalization | Windows/Unix path inconsistencies |
| json | 98% | `safe_parse_json()` with error handling | `json.JSONDecodeError` |
| import | 92% | Robust import handling | `ModuleNotFoundError` |
| hook | 100% | Clean JSON input handling | PostToolUse execution failures |

## Usage Examples

### Basic Pattern Application
```bash
/apply-safety-patterns --interactive
/apply-safety-patterns --category=database --confirm
/apply-safety-patterns --dry-run --verbose
```

### Targeted Application
```bash
/apply-safety-patterns --category=database --files="*.py" --backup
/apply-safety-patterns --category=json --evidence-report
/apply-safety-patterns --directory="src/hooks" --recursive
```

### Safe Application Mode
```bash
/apply-safety-patterns --safe-mode --validate-after --rollback-on-error
/apply-safety-patterns --evidence-threshold=0.8 --verbose --report
```

## Constitutional Compliance

- Singular Decision Authority - Developer maintains 100% control
- No Background Services - All functionality is command-driven
- No Required Consensus - No organizational decision requirements
- Direct File Editing - All changes are immediate file modifications
- User Control - Opt-out available for all features

## Application Workflow

1. **Issue Detection** - Automatic detection with evidence scoring
2. **Pattern Recommendation** - Evidence-based recommendations with success rates
3. **Interactive Approval** - User must approve each individual change
4. **Validation and Reporting** - Comprehensive validation and reporting
