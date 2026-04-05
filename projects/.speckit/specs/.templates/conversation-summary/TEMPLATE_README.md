# Conversation Summary Template

## Overview
This template provides a standardized structure for creating conversation summary TSKs in the CSF NIP ecosystem. It ensures consistent quality, constitutional compliance, and rapid deployment.

## Template Structure

### Core Files
- **PLAN.md** - High-level planning and strategy (109 lines)
- **TASKS.md** - Detailed task decomposition with TDD cycles (98 lines)
- **DATA_MODEL.md** - Data architecture and relationships (100 lines)

### Extended Files
- **SPECIFY.md** - Technical specifications and requirements (86 lines)
- **IMPLEMENT.md** - Implementation guide and examples (157 lines)
- **IMPLEMENTATION_EVIDENCE.md** - Execution evidence and learnings (25 lines)

## Usage

### Quick Start
```bash
cd .speckit/specs/.templates/conversation-summary
./clone_template.sh TSK-XXX "Task Name" 2025-11-04 SESSION-ID Medium High
```

### Parameters
- **TASK_ID**: Sequential TSK number (e.g., TSK-021)
- **TASK_NAME**: Descriptive task name
- **DATE**: Creation date (YYYY-MM-DD)
- **SESSION_ID**: Session identifier
- **COMPLEXITY**: Low/Medium/High/Very High
- **PRIORITY**: Low/Medium/High/Critical

## Placeholder Variables

The template automatically substitutes these placeholders:
- `[TASK_ID]` - Task identifier
- `[TASK_NAME]` - Task name
- `[DATE]` - Creation date
- `[SESSION_ID]` - Session identifier
- `[COMPLEXITY]` - Complexity level
- `[PRIORITY]` - Priority level

## TDD Workflow

All tasks in the template follow the RED→GREEN→REFACTOR cycle:

### RED Phase
- Write failing tests
- Define expected behavior
- Document test cases

### GREEN Phase
- Implement minimal code
- Make tests pass
- Focus on functionality

### REFACTOR Phase
- Improve code quality
- Optimize performance
- Enhance maintainability

## Quality Gates

The template includes integrated quality gates:

### Structure Validation
- All required files exist
- File sizes > 0 bytes
- Proper directory structure

### TDD Compliance
- RED phases documented
- GREEN phases documented
- REFACTOR phases documented

### Constitutional Compliance
- CSF NIP Constitution v4.1 references
- Evidence markers present
- Quality gate integration

## Success Metrics

### Expected Outcomes
- **Setup Time**: < 2 minutes (vs 30 minutes manual)
- **Quality Score**: 100% (structure + TDD + constitutional)
- **Reusability Score**: 85%
- **Error Rate**: 0%

### Validation Checklist
- [ ] All files created
- [ ] Placeholders substituted
- [ ] TDD workflow included
- [ ] Quality gates integrated
- [ ] Constitutional compliance validated

## Template Features

### Pattern-Based Design
- Extracted from TSK-020 successful implementation
- Proven patterns for rapid deployment
- CSF NIP Constitution compliant

### Customization Hooks
- Easy placeholder substitution
- Flexible section structure
- Adaptable to various task types

### Quality Assurance
- Automated validation
- Built-in quality gates
- Constitutional compliance checks

## Best Practices

1. **Always use the template** for new conversation summary tasks
2. **Customize placeholders** with actual values
3. **Follow TDD workflow** for all implementation tasks
4. **Run quality gates** before completion
5. **Document learnings** in IMPLEMENTATION_EVIDENCE.md

## Examples

### Example 1: Create new TSK
```bash
./clone_template.sh TSK-021 "Feature Analysis" 2025-11-04 FEATURE-ANALYSIS High High
```

### Example 2: Validate cloned template
```bash
python -c "from pathlib import Path; tsk_dir = Path('../TSK-021-Feature-Analysis'); \
files = ['PLAN.md', 'TASKS.md', 'DATA_MODEL.md']; \
all_exist = all((tsk_dir / f).exists() and (tsk_dir / f).stat().st_size > 0 for f in files); \
print('✅ PASS' if all_exist else '❌ FAIL')"
```

## Troubleshooting

### Placeholders Not Substituted
- Check script permissions: `chmod +x clone_template.sh`
- Verify all parameters provided
- Ensure bash is available

### Files Not Created
- Check directory permissions
- Verify disk space
- Review script output for errors

### Quality Gates Failing
- Review file content
- Check TDD phases present
- Validate constitutional compliance

## Integration

### CWO Workflow
The template is designed to work with the CWO 7-step workflow:
1. Constitutional Pre-Check
2. Automatic Plan Enhancement
3. Advisory Analysis
4. Task Decomposition
5. Sub-Agent Integration
6. Evidence-Based Execution
7. Knowledge System Integration

### Knowledge System
Patterns stored in CSF NIP knowledge base for:
- Future reference
- Pattern matching
- Organizational learning

## Version History

### v1.0 (2025-11-04)
- Initial template creation
- 5 core files (PLAN, TASKS, DATA_MODEL, SPECIFY, IMPLEMENT)
- Automated cloning script
- Quality gate integration
- 100% TDD compliance
- CSF NIP Constitution v4.1 compliant

## Support

For issues or improvements:
1. Check this README
2. Review template examples
3. Validate with quality gates
4. Document findings

---
**Template Version**: 1.0
**Created**: 2025-11-04
**Source**: TSK-020-conversation-summary
**Compliance**: CSF NIP Constitution v4.1
**Status**: Production Ready
