# [TASK_ID]: Data Model - [TASK_NAME]

## Entity Definitions

### [Entity 1] Entity
```yaml
[FIELD_1]: "[VALUE_1]"
[FIELD_2]: "[VALUE_2]"
[FIELD_3]: [VALUE_3]
[FIELD_4]: [VALUE_4]
```

### [Entity 2] Entity
```yaml
[FIELD_1]: "[VALUE_1]"
[FIELD_2]: "[VALUE_2]"
[FIELD_3]: [VALUE_3]
[FIELD_4]: [VALUE_4]
```

## Data Relationships

### Task → [Component]
```
[TASK_ID]
  └─→ contains
      └─→ [FILE_PATH]
          └─→ implements
              └─→ [Class/Function] class
                  └─→ maps
                      └─→ [RELATIONSHIP]
```

## Data Flow

### 1. [Process Name] Flow
```
[Input]
  ↓
[Step 1]
  ↓
[Step 2]
  ├─→ [Branch A] → [Outcome A]
  └─→ [Branch B] → [Outcome B]
  ↓
[Output]
```

## Quality Metrics

### Performance Metrics
```yaml
[COMPONENT]:
  [METRIC_1]: [VALUE]
  [METRIC_2]: [VALUE]
  [METRIC_3]: [VALUE]
  [METRIC_4]: [VALUE]
```

### Compliance Metrics
```yaml
CSF NIP Constitution v4.1:
  [SECTION_1]: compliant
  [SECTION_2]: compliant
  [SECTION_3]: compliant
  [SECTION_4]: compliant
```

## Integration Points

### [System 1] Integration
```yaml
[INTEGRATION_POINT_1]: "[DESCRIPTION]"
[INTEGRATION_POINT_2]: "[DESCRIPTION]"
```

## Data Validation Rules

### [Validation Category]
```yaml
rule_1: "[DESCRIPTION]"
rule_2: "[DESCRIPTION]"
rule_3: "[DESCRIPTION]"
rule_4: "[DESCRIPTION]"
```

## Conclusion

The [TASK_ID] data model provides a comprehensive framework for understanding all entities, relationships, flows, and metrics related to [TASK_NAME]. This structured documentation ensures:

1. **[Guarantee 1]**: [Description]
2. **[Guarantee 2]**: [Description]
3. **[Guarantee 3]**: [Description]

---
**Data Model Version**: 1.0
**Date Created**: [DATE]
**Associated Task**: [TASK_ID]-[TASK_NAME]
**Compliance**: CSF NIP Constitution v4.1
**Status**: In Progress
