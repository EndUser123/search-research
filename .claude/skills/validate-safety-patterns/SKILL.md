---
name: validate-safety-patterns
description: Safety pattern validation with evidence-based reporting
version: "1.0.0"
status: stable
category: quality
triggers:
  - /validate-safety-patterns
aliases:
  - /validate-safety-patterns

suggest:
  - /comply
  - /bug-hunt
  - /apply_safety-patterns
---

# Validate Safety Patterns

Validate safety patterns with evidence-based reporting.

## Project Context

### Constitution / Constraints

- Safety compliance: Validating constitutional safety patterns
- Evidence-based reporting: Show actual pass/fail results

### Technical Context

- Categories: Database (95% success), JSON (98%), Path (90%), Import (92%), Hook (100%)
- Integration with /apply_safety_patterns, /bug-hunt

### Architecture Alignment

- Quality gate pattern: Pre-commit validation
- Pattern-based validation: Category-specific rules

## Your Workflow

1. Run safety pattern validation
2. Check each category for compliance
3. Generate evidence-based report
4. Show success rates by category

## Validation Rules

### Categories Validated

- Database: 95% success rate
- JSON: 98% success rate
- Path: 90% success rate
- Import: 92% success rate
- Hook: 100% success rate


## Usage

/validate-safety-patterns
/validate-safety-patterns --comprehensive
/validate-safety-patterns --category=database

## Categories

- Database (95% success)
- JSON (98% success)
- Path (90% success)
- Import (92% success)
- Hook (100% success)
