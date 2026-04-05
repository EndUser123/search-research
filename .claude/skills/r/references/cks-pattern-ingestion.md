# CKS Pattern Ingestion

`/r` stores discovered patterns and learnings to CKS for cross-session knowledge accumulation.

## Query CKS Before Analysis

Before running deterministic checks, query relevant patterns from CKS:

```python
from cks.migrations.create_findings_table import query_findings

try:
    # Query relevant patterns from previous /r passes
    relevant_patterns = query_findings(
        source="r",                    # Patterns from /r skill
        finding_type="PATTERN",        # Pattern learnings
        limit=20                      # Most recent 20 patterns
    )

    # Also query REFACTOR suggestions from debugRCA
    refactor_suggestions = query_findings(
        source="debugrca",
        finding_type="REFACTOR",
        limit=10
    )

    # Incorporate into analysis
    for pattern in relevant_patterns:
        context_from_cks += f"Historical pattern: {pattern['message']}\n"

except Exception as e:
    # Graceful degradation - continue without CKS context
    print(f"CKS query unavailable: {e} - proceeding with fresh analysis")
```

## Store Patterns to CKS

After completing `/r` analysis, store high-value patterns for future sessions:

```python
from cks.migrations.create_findings_table import upsert_finding

try:
    # Store forgotten items as patterns
    for item in forgotten_items[:5]:  # Top 5 most important
        upsert_finding(
            finding_type="PATTERN",
            source="r",
            message=f"Forgotten: {item['description']}",
            file_path=item.get('file_path'),
            line_number=item.get('line_number'),
            severity=item.get('severity', 'medium'),
            metadata={
                'category': item.get('category'),
                'why_forgotten': item.get('rationale'),
                'prevention': item.get('prevention_strategy')
            }
        )

    # Store deterministic improvements as REFACTOR patterns
    for improvement in deterministic_improvements[:5]:
        upsert_finding(
            finding_type="REFACTOR",
            source="r",
            message=improvement['description'],
            file_path=improvement.get('file_path'),
            line_number=improvement.get('line_number'),
            severity=improvement.get('severity', 'medium'),
            metadata={
                'rationale': improvement.get('rationale'),
                'suggested_action': improvement.get('action'),
                'value_level': improvement.get('value_level')
            }
        )

    # Store solo-dev compliance violations as DEBT
    for violation in solo_dev_violations:
        upsert_finding(
            finding_type="DEBT",
            source="r",
            message=f"SLC violation: {violation['check']}",
            file_path=violation.get('file_path'),
            severity='medium',
            metadata={
                'check_name': violation['check'],
                'why_matters': violation.get('explanation'),
                'fix_guidance': violation.get('remediation')
            }
        )

    print(f"Stored {len(forgotten_items) + len(deterministic_improvements)} patterns to CKS")

except Exception as e:
    # Graceful degradation - analysis complete, storage is optional
    print(f"CKS storage unavailable: {e} - patterns not persisted")
```

## Pattern Categories for /r

| Finding Type | Usage | Example |
|--------------|-------|---------|
| `PATTERN` | Forgotten items, omissions | "Missing error handling in API endpoint" |
| `REFACTOR` | Code improvement opportunities | "Extract duplicate validation to shared utility" |
| `DEBT` | Compliance violations, technical debt | "SLC: Complexity not justified by value" |
| `DOC` | Documentation gaps | "Missing function docstring for exported API" |
| `OPT` | Optimization opportunities | "N+1 query in user list endpoint" |

## Metadata Schema

```python
metadata = {
    # For PATTERN (forgotten items)
    'category': 'error_handling|testing|documentation|validation',
    'why_forgotten': 'Root cause of omission',
    'prevention': 'How to prevent recurrence',

    # For REFACTOR (improvements)
    'rationale': 'Why this improvement matters',
    'suggested_action': 'Specific fix recommendation',
    'value_level': 'HIGH|MEDIUM|LOW',

    # For DEBT (compliance)
    'check_name': 'Name of violated check',
    'why_matters': 'Business/technical impact',
    'fix_guidance': 'Remediation steps',

    # For DOC (documentation)
    'missing_content': 'What documentation is lacking',
    'audience': 'developers|users|api_consumers',

    # For OPT (optimizations)
    'current_performance': 'Baseline measurement',
    'expected_improvement': 'Anticipated gain',
    'complexity_cost': 'Tradeoff analysis'
}
```

## Error Handling

```python
# Always wrap CKS operations in try-except
try:
    from cks.migrations.create_findings_table import query_findings, upsert_finding

    # Query historical patterns
    patterns = query_findings(source="r", limit=20)

    # ... analysis using patterns ...

    # Store new patterns
    upsert_finding(
        finding_type="PATTERN",
        source="r",
        message="Valuable pattern learned",
        severity="medium",
        metadata={'context': '...'}
    )

except ImportError:
    # CKS module not available
    print("CKS unavailable - running without historical patterns")

except Exception as e:
    # Database error, permission issue, etc.
    print(f"CKS error: {e} - degrading gracefully")
    # Continue analysis - CKS is enhancement, not requirement
```

## Best Practices

1. **Query before analyze**: Load relevant patterns from CKS before running deterministic checks
2. **Store high-value items only**: Prioritize actionable patterns with clear file references
3. **Avoid noise**: Don't store trivial findings or context-specific one-offs
4. **Use severity levels**: `critical` for blockers, `high` for important patterns, `medium` for improvements, `low` for nice-to-haves
5. **Include prevention guidance**: For forgotten items, document how to prevent recurrence
6. **Idempotent storage**: Same pattern can be stored multiple times - CKS updates timestamp instead of duplicating
7. **Graceful degradation**: Always proceed with analysis even if CKS unavailable
