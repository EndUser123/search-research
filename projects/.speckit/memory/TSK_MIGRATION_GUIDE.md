# TSK Migration Transition Guide

## Migration Complete (Phase 3)
The workspace has successfully migrated from consolidated TSK-LEGACY to project-specific TSK structure.

## What Changed

### Before: Consolidated Structure
- Single TSK-LEGACY with 106 tasks
- Mixed project types in one database
- No project-specific governance

### After: Project-Specific Structure
- 6 project TSKs with focused scope
- Data-task linking with validation
- Project-specific constitutions
- Enhanced task organization

## New Project TSKs

### TSK-CSF-NIP-MAIN (11 tasks)
- **Focus**: Security, validation, infrastructure
- **Switch**: `/tsk.set TSK-CSF-NIP-MAIN`
- **Governance**: `constitution.md`

### TSK-SPECKIT-MAIN (79 tasks) - [ACTIVE]
- **Focus**: Task management, commands, workflows
- **Switch**: `/tsk.set TSK-SPECKIT-MAIN`
- **Governance**: `constitution.md`

### TSK-TESTING-MAIN (4 tasks)
- **Focus**: Testing framework, QA automation
- **Switch**: `/tsk.set TSK-TESTING-MAIN`
- **Governance**: `constitution.md`

### TSK-HOOKS-MAIN (3 tasks)
- **Focus**: Session management, hook system
- **Switch**: `/tsk.set TSK-HOOKS-MAIN`
- **Governance**: `constitution.md`

### TSK-DOCUMENTATION-MAIN (2 tasks)
- **Focus**: Documentation, guides, standards
- **Switch**: `/tsk.set TSK-DOCUMENTATION-MAIN`
- **Governance**: `constitution.md`

### TSK-MISC-MAIN (7 tasks)
- **Focus**: Miscellaneous tasks, utilities
- **Switch**: `/tsk.set TSK-MISC-MAIN`
- **Governance**: `constitution.md`

## How to Use New Structure

### Daily Workflow
1. **Set Active TSK**: `/tsk.set <project-tsk-id>`
2. **List Tasks**: `/task list`
3. **Work on Tasks**: `/task update <id> --status in_progress`
4. **Plan Work**: `/planning add "New task description"`
5. **Execute Work**: `/exec validate` (validates current TSK)

### Switching Projects
```bash
# Work on Speckit system
/tsk.set TSK-SPECKIT-MAIN

# Work on security tasks
/tsk.set TSK-CSF-NIP-MAIN

# Work on testing
/tsk.set TSK-TESTING-MAIN
```

### Task Operations
All `/task`, `/planning`, and `/exec` commands work on the currently active TSK.

## Data-Task Linking

### New Features
- **Entities**: Tasks reference data entities
- **Validation Rules**: Tasks include validation requirements
- **Automatic Validation**: 100% validation success rate achieved
- **Data Model Integration**: Consistent across all project TSKs

### Task Structure
```json
{
  "id": "task-id",
  "title": "Task title",
  "entities": ["Entity1", "Entity2"],
  "validation_rules": ["RULE-NAME"],
  "migration_info": {
    "source_tsk": "TSK-LEGACY",
    "target_tsk": "TSK-PROJECT-MAIN"
  }
}
```

## Governance

### Workspace Constitution
- **Location**: `P:/.speckit/memory/constitution.md`
- **Scope**: Base rules for all projects

### Project Constitutions
- **Location**: `.speckit/memory/TSK-<project>-MAIN/constitution.md`
- **Scope**: Project-specific rules and standards
- **Inheritance**: Projects inherit from workspace constitution

## Troubleshooting

### Common Issues
1. **Wrong Active TSK**: Use `/tsk.set` to switch projects
2. **Task Not Found**: Check you're in the correct project TSK
3. **Validation Failures**: Review data model in project TSK

### Getting Help
- Review project constitution for specific rules
- Check `plan.md` in each project TSK
- Use `/task help` for command assistance

## Archive Access

### TSK-LEGACY Archive
- **Location**: `P:/.speckit/memory/ARCHIVED-TSK-LEGACY/`
- **Status**: Read-only reference
- **Content**: Original 106 tasks and structure

### Access for Reference
```bash
# View archive contents
ls P:/.speckit/memory/ARCHIVED-TSK-LEGACY/

# Read archive documentation
cat P:/.speckit/memory/ARCHIVED-TSK-LEGACY/ARCHIVE_README.md
```

## Success Metrics

### Migration Results
- ✅ 106 tasks successfully migrated
- ✅ 6 project TSKs created
- ✅ 100% data-task linking validation
- ✅ 6 project constitutions created
- ✅ Enhanced organization and governance

### Performance
- ✅ Sub-millisecond task operations
- ✅ Improved task relevance (project-scoped)
- ✅ Enhanced data validation
- ✅ Better maintainability

## Next Steps

### For Users
1. Explore project TSKs using `/tsk.set` commands
2. Review project constitutions for standards
3. Use data-task linking for new tasks
4. Follow project-specific workflow rules

### For Development
1. Monitor new system performance
2. Collect user feedback
3. Refine data models as needed
4. Maintain governance documents

---
**Migration Completed Successfully** ✅
*System now uses project-specific TSK structure with enhanced governance and data validation.*
