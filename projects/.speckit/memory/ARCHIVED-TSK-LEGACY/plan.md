# TSK-LEGACY: Interim Canonical Tasks Management

## Overview
TSK-LEGACY serves as the interim canonical tasks database, consolidating 106 tasks from multiple sources including the main task completion tracker and conversation analysis. This provides a single source of truth for all task management during the migration period.

## Scope
- **Total Tasks**: 106 tasks consolidated from multiple databases
- **Sources**:
  - Main task completion tracker (91 tasks with full workflow data)
  - Conversation analysis tasks (15 high-impact development tasks)
- **Status**: Interim canonical source until proper migration to project-based TSKs

## Migration Strategy
### Phase 1: Consolidation ✅
- Extract all tasks from scattered databases
- Consolidate into single canonical tasks.json
- Create unified data model accommodating all task types

### Phase 2: Analysis & Planning (Next)
- Analyze tasks by project, initiative, and scope
- Identify natural groupings for migration
- Plan TSK structure per project/initiative

### Phase 3: Migration (Future)
- Create project-specific TSKs (TSK-<proj>-<id>)
- Migrate tasks to appropriate project TSKs
- Maintain task continuity and traceability

## Task Categories in Legacy
- **Development tasks**: Feature implementation, bug fixes, API work
- **Infrastructure**: Security, authentication, deployment
- **Documentation**: Architecture docs, guides, specifications
- **Quality**: Testing, validation, code review
- **Conversation analysis**: Process improvements, organizational issues

## Data Model
Each task includes:
- Core fields: id, title, description, status, priority
- Workflow fields: phase, assigned_to, duration tracking
- Metadata: source, tags, acceptance criteria
- Migration metadata: migration_date, source_system

## Access Protocol
- **Read**: All LLMs should read from `.speckit/memory/TSK-LEGACY/tasks.json`
- **Write**: No writes to repo root task databases
- **Updates**: Modify tasks.json directly during interim period
- **Evidence**: Per-task evidence in `docs/<task-id>` or `reports/<task-id>` subfolders

## Next Steps
1. Complete triplet files (tasks.md, data_model.md)
2. Create taskmaster index.json
3. Provide clear LLM guidance documentation
4. Plan project-based TSK migration structure