---
name: validate_spec
description: Validate implementation against specification (specify.md)
version: "1.0.0"
status: stable
category: quality
triggers:
  - /validate-spec
aliases:
  - /validate-spec

suggest:
  - /specify
  - /build
  - /comply
---

# Specification Compliance Check

Checks if requirements defined in specify.md are implemented in the codebase.

## Project Context

### Constitution / Constraints

- Spec compliance: Follow specifications exactly
- Evidence-first: Verify implementation against spec

### Technical Context

- SpecValidator checks coverage
- Severity levels: NOMINAL, MINOR, MAJOR, CRITICAL
- Coverage thresholds determine recommendations

### Architecture Alignment

- Quality gate: Validate spec-to-implementation alignment
- Drift detection: Identify when code diverges from specification

## Your Workflow

1. Locate specification and implementation files
2. Run SpecValidator to check coverage
3. Display Coverage Report with percentage and severity
4. Recommend next steps based on coverage

## Validation Rules

### Severity Thresholds

- 95-100%: NOMINAL - Ready to ship
- 80-94%: MINOR - Add final implementation/tests
- 50-79%: MAJOR - Return to Phase 2 (ALIGN)
- <50%: CRITICAL - Significant spec drift detected

### Next Steps

- Nominal: Proceed to /verify --tier 3 and commit
- Major/Critical: Re-evaluate specification or implementation


## Usage

```
/validate-spec [--spec path/to/spec.md] [--impl path/to/src]
```

## Example

```
/validate-spec --spec specify.md --impl src/
```

## Execution

1. Locate the specification and implementation files
2. Run the SpecValidator to check coverage
3. Display the Coverage Report showing:
   - Percentage of requirements implemented
   - Drift Severity (NOMINAL/MINOR/MAJOR/CRITICAL)
   - List of implemented vs missing requirements

## Severity Thresholds

| Coverage | Severity    | Recommendation                  |
| -------- | ----------- | ------------------------------- |
| 95-100%  | NOMINAL  | Ready to ship                   |
| 80-94%   | MINOR    | Add final implementation/tests  |
| 50-79%   | MAJOR    | Return to Phase 2 (ALIGN)       |
| <50%     | CRITICAL | Significant spec drift detected |

## Next Steps

- Nominal: Proceed to /verify --tier 3 and then commit
- Major/Critical: Re-evaluate specification or implementation
