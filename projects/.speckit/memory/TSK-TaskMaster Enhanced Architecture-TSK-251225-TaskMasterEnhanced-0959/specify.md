# Specification: TaskMaster Enhanced Architecture

**TSK:** TSK-251225-TaskMasterEnhanced-0959
**Created:** 2025-12-25T09:59:00Z
**Status:** Draft

## Overview

Enhance TaskMaster with 36-programmatic tools borrowed from eyaltoledano/claude-task-master research, implementing PRD integration and comprehensive task management capabilities. All tools accessed programmatically via Python functions (NOT MCP server).

**Context:** This enhancement fills the gap between business requirements (PRD) and developer implementation by providing automated task generation, natural language interface, and full traceability from requirements to code.

## Requirements

### Functional Requirements

#### FR-1: PRD Integration
- **FR-1.1:** Parse PRD.md files with FR-XXX/NF-XXX requirement format
- **FR-1.2:** Automatically generate TaskMaster tasks from PRD requirements
- **FR-1.3:** Store PRD requirements in separate `prd_requirements` table
- **FR-1.4:** Link tasks to source PRD requirements via `source` and `source_id` columns
- **FR-1.5:** Track PRD completion percentage with validation

**Acceptance Criteria:**
- Given a valid PRD.md file, when `/prd import <project>` is executed, then all FR/NF requirements are parsed and stored in TaskMaster database

#### FR-2: 36-Tool Programmatic Architecture
- **FR-2.1:** Implement 7 core tools (get_tasks, next_task, set_task_status, create_task, delete_task, expand_task)
- **FR-2.2:** Implement 8 standard tools (analyze_project_complexity, parse_prd, move_tasks, etc.)
- **FR-2.3:** Implement 21 advanced tools (bulk operations, dependency visualization, AI-powered suggestions)
- **FR-2.4:** Organize tools into 3 modules: core_tools.py, standard_tools.py, advanced_tools.py
- **FR-2.5:** Provide tool registry with lazy loading

**Acceptance Criteria:**
- Given a tool name, when `registry.get_tool(tool_name)` is called, then the tool function is returned with lazy loading

#### FR-3: Token Optimization
- **FR-3.1:** Implement 3 loading modes: core (7 tools), standard (15 tools), all (36 tools)
- **FR-3.2:** Lazy load tools only when accessed (not imported at startup)
- **FR-3.3:** Context-aware tool selection based on operation type
- **FR-3.4:** Achieve 70% context reduction with "core" mode vs "all" mode

**Acceptance Criteria:**
- Given token budget constraints, when mode="core", then only 7 tools are loaded (5K tokens vs 21K tokens for all)

#### FR-4: Database Schema Extensions
- **FR-4.1:** Add `prd_requirements` table (id, prd_name, title, category, description, acceptance_criteria, success_metrics)
- **FR-4.2:** Add `source` column to tasks table ('prd', 'spec', 'manual')
- **FR-4.3:** Add `source_id` column to tasks table (FR-003, TSK-251222, etc.)
- **FR-4.4:** Add `prd_requirement_id` foreign key to tasks table
- **FR-4.5:** Add `success_metrics` table for tracking PRD completion

**Acceptance Criteria:**
- Given database migration script, when executed, then all new tables and columns are added without data loss

#### FR-5: Natural Language Interface (Phase 3)
- **FR-5.1:** Parse natural language commands ("What's the next task?", "Parse my PRD")
- **FR-5.2:** Map natural language to tool calls with regex patterns
- **FR-5.3:** Support conversational task management
- **FR-5.4:** Maintain command-based interface as primary

**Acceptance Criteria:**
- Given natural language input, when parsed, then appropriate tool is called with correct parameters

### Non-Functional Requirements

#### NFR-1: Performance
- **NFR-1.1:** Tool lazy loading overhead < 100ms
- **NFR-1.2:** PRD parsing for 100 requirements < 2 seconds
- **NFR-1.3:** Database query response time < 500ms

#### NFR-2: Compatibility
- **NFR-2.1:** Maintain compatibility with existing `/tsk.new`, `/tsk.set` commands
- **NFR-2.2:** Work with consolidated database at `P:/.speckit/taskmaster/tasks.db`
- **NFR-2.3:** Python 3.8+ compatibility

#### NFR-3: Maintainability
- **NFR-3.1:** Clear separation of concerns (tools, registry, database)
- **NFR-3.2:** Comprehensive error handling for all tools
- **NFR-3.3:** Type hints throughout codebase

#### NFR-4: Scalability
- **NFR-4.1:** Support 1000+ tasks without performance degradation
- **NFR-4.2:** Support 100+ concurrent PRD requirements
- **NFR-4.3:** Token-efficient for large projects

## User Stories

### US-1: PRD Import
**As a** product manager
**I want** to import PRD requirements into TaskMaster automatically
**So that** I don't manually create tasks for each requirement

**Acceptance Criteria:**
- [ ] Given PRD.md with FR-XXX format, `/prd import` creates tasks automatically
- [ ] Tasks linked to source PRD requirement
- [ ] Traceability from PRD → TaskMaster → code

### US-2: Token Optimization
**As a** developer
**I want** to load only essential tools for quick operations
**So that** I don't waste context on unused functionality

**Acceptance Criteria:**
- [ ] Given mode="core", only 7 tools loaded
- [ ] Token usage reduced by 70%
- [ ] Performance improved for simple queries

### US-3: Programmatic Tool Access
**As a** developer
**I want** to call TaskMaster tools from Python code
**So that** I can build custom workflows

**Acceptance Criteria:**
- [ ] Given tool name, `registry.get_tool(name)` returns function
- [ ] Tools invoked programmatically without MCP server
- [ ] All 36 tools accessible via Python API

## Scope

### In Scope
- PRD parsing and import functionality
- 36 tools organized in 3 modules
- Tool registry with lazy loading
- Token optimization modes
- Database schema extensions
- Traceability system (PRD → TaskMaster → code)
- Natural language interface (Phase 3)

### Out of Scope
- MCP server implementation (excluded by design)
- AI IDE integration (Cursor, Windsurf, VS Code)
- Multi-model provider support (use existing CSF NIP providers)
- Real-time collaboration features
- Web UI or React frontend

## Success Criteria

- ✅ `/prd import` command successfully parses PRD files
- ✅ All 36 tools accessible programmatically
- ✅ Token optimization reduces context by 70% with core mode
- ✅ Traceability chain working: PRD → TaskMaster → code
- ✅ Database migration successful with no data loss
- ✅ Existing commands still working (/tsk.new, /tsk.set)

## Technical Considerations

### Research-Based Design
- Architecture borrowed from eyaltoledano/claude-task-master (GitHub research)
- 36 tools organized by complexity (core: 7, standard: 15, advanced: 21)
- Lazy loading pattern for token optimization
- Programmatic access (NOT MCP server)

### Database Schema
```sql
-- New tables
CREATE TABLE prd_requirements (
    id TEXT PRIMARY KEY,  -- FR-001, NF-001
    prd_name TEXT,
    title TEXT,
    category TEXT,
    description TEXT,
    acceptance_criteria TEXT,  -- JSON
    success_metrics TEXT,  -- JSON
    created_at TEXT,
    FOREIGN KEY (prd_name) REFERENCES projects(name)
);

-- Existing table extensions
ALTER TABLE tasks ADD COLUMN source TEXT;  -- 'prd', 'spec', 'manual'
ALTER TABLE tasks ADD COLUMN source_id TEXT;
ALTER TABLE tasks ADD COLUMN prd_requirement_id TEXT;

CREATE TABLE success_metrics (
    id TEXT PRIMARY KEY,
    task_id TEXT,
    metric_name TEXT,
    target_value REAL,
    current_value REAL,
    measurement_unit TEXT,
    status TEXT,
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);
```

### Tool Organization
```
P:/.speckit/taskmaster/
├── tools/
│   ├── core_tools.py (7 tools)
│   ├── standard_tools.py (8 tools)
│   └── advanced_tools.py (21 tools)
├── prd/
│   ├── parser.py
│   └── importer.py
├── registry.py (tool registry with lazy loading)
└── db.py (consolidated database module)
```

## Open Questions

- [Q1] Should we implement subtasks table for better hierarchy management?
- [Q2] Should we add project complexity analysis metrics from eyaltoledano?
- [Q3] What's the priority order for implementing the 21 advanced tools?
- [Q4] Should we add dependency validation and circular dependency detection?

## References

- Research: `P:/__csf.nip/docs/TASKMASTER_REPOS_ANALYSIS.md`
- Architecture: `P:/__csf.nip/docs/TASKMASTER_ENHANCED_ARCHITECTURE.md`
- PRD Analysis: `P:/__csf.nip/docs/PRD_VS_SPEC_ANALYSIS.md`
- Workflow: `P:/__csf.nip/docs/CWO12_PRD_INTEGRATION_WORKFLOW.md`
- Consolidation ADF: `P:/__csf.nip/docs/TASKMASTER_CONSOLIDATION_ADF.md`
