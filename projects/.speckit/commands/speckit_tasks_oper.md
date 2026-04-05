---
name: "/speckit.tasks"
category: "Speckit Workflow"
purpose: "Generate an actionable, dependency-ordered tasks.md for the feature based on available design artifacts"
entry_point: "primary"
---

# Speckit Tasks - Implementation Task Generation

Transform feature specifications and design artifacts into actionable, dependency-ordered implementation tasks. This command creates comprehensive task breakdowns that guide the development process with clear dependencies, priorities, and acceptance criteria.

## 🚀 Quick Start

### Generate Basic Task Breakdown
```bash
/speckit.tasks
```

### Generate Tasks with Specific Focus
```bash
/speckit.tasks "focus:security, priority:high, include:testing"
```

### Generate Tasks for Complex Feature
```bash
/speckit.tasks "parallel:true, max-tasks:20, include:documentation, deployment"
```

## ⚙️ Command Options

Tasks generation accepts various parameters for customization:

| Parameter | Values | Description |
|-----------|--------|-------------|
| **Focus Areas** | `security`, `performance`, `testing`, `documentation`, `deployment` | Emphasize specific task categories |
| **Priority Level** | `high`, `medium`, `low`, `critical` | Filter tasks by priority |
| **Parallel Execution** | `true`, `false` | Mark tasks suitable for parallel development |
| **Max Tasks** | Number | Limit total number of tasks generated |
| **Include** | `testing`, `documentation`, `deployment`, `review` | Additional task categories to include |
| **Exclude** | `documentation`, `testing`, `deployment` | Categories to exclude from generation |

## 📋 Use Cases

### When to Use /speckit.tasks

- **Implementation Planning**: After completing specification and design phases
- **Team Coordination**: Create clear task assignments for development team
- **Project Estimation**: Provide basis for effort estimation and timeline planning
- **Quality Assurance**: Ensure comprehensive coverage of all implementation aspects
- **Dependency Management**: Identify and manage task dependencies and sequencing

### When NOT to Use /speckit.tasks

- **Requirements Gathering**: Use `/speckit.specify` for specification creation
- **Technical Design**: Use `/speckit.plan` for architecture and design planning
- **Task Execution**: Use `/speckit.implement` for actual task execution

## 🔧 Prerequisites

### Required Artifacts
1. **Complete Specification**: `spec.md` with all requirements and constraints
2. **Technical Design**: `plan.md` with architecture and implementation decisions
3. **Plan TSK Context**: Parent plan with TSK-### identifier for task grouping
4. **Feature Directory**: Valid speckit plan directory structure under `.speckit/specs/TSK-###-plan-name/`
5. **Task Templates**: Speckit task templates available

### Multi-Project Task Coordination
Tasks must coordinate with existing multi-project infrastructure:
- **Plan-Level Context**: Tasks belong to a parent TSK-### plan
- **Cross-Project Dependencies**: Tasks may depend on other plans' completion
- **TaskMaster Integration**: Coordinate with existing task management to prevent conflicts
- **Resource Allocation**: Consider resource constraints across multiple active plans

### CSF NIP Development Standards Integration
All task generation follows established CSF NIP development standards:
- **TaskMaster Anti-Duplication Rule**: Never create duplicate functionality
- **Infrastructure Usage Protocol**: Validate all tool usage before execution
- **Evidence-Based Task Definition**: Each task has clear acceptance criteria with evidence
- **Quality Assurance Integration**: Testing and documentation tasks included for all implementation
- **Lib-First Pattern**: Check existing solutions before creating new components or tasks

### Validation Commands
```bash
# Verify plan context and TSK assignment
cd "C:\_Python\_Projects\.speckit"
ls -la specs/ | grep "TSK-"
cd specs/TSK-XXX-plan-name
ls -la | grep -E "(spec\.md|plan\.md)"

# Check cross-plan dependencies
cd "C:\_Python\_Projects\.speckit"
cat registry/tsk_registry.json | jq '.[] | select(.dependencies != null)'

# Check prerequisites
cd "C:\_Python\_Projects\.speckit"
powershell -ExecutionPolicy Bypass -File ".\scripts\powershell\check-prerequisites.ps1" -Json

# Verify template availability
ls "C:\_Python\_Projects\.speckit\templates\tasks-template.md"

# Validate TaskMaster coordination (if applicable)
cd "C:\_Python\_Projects\__csf.nip"
python tsk.py --check-conflicts TSK-XXX
```

## 🚨 MANDATORY Standards Compliance Integration [BLOCKING GATE]

**CRITICAL**: Task generation is BLOCKED until ALL standards compliance requirements below are completed

### CSF NIP Standards Validation (REQUIRED)
All task generation MUST include these mandatory validation steps:

#### 1. System Discovery Protocol Enforcement (MANDATORY)
- [ ] **Complete System Discovery**: Run full System Discovery Protocol from `docs/standards/processes/SYSTEM_DISCOVERY_PROTOCOL.md`
- [ ] **Evidence Collection**: Document all existing solutions found during discovery with file paths and evidence
- [ ] **Component Analysis**: Search `src/lib/core_utils/` for existing solutions BEFORE generating new tasks
- [ ] **Library Standards Check**: Apply Library Usage Protocol for ALL external libraries mentioned in tasks
- [ ] **Architecture Verification**: Apply Evidence-Based Answers Standard to all task decisions

#### 2. Evidence-Based Task Definition (MANDATORY)
- [ ] **Implementation Evidence**: Every task must be based on actual research, not assumptions
- [ ] **Standards Evidence**: Cite specific standards sections applicable to each task category
- [ ] **Architecture Evidence**: Provide evidence for all architectural decisions in task breakdown
- [ ] **Risk Evidence**: Document potential risks and mitigation strategies for complex tasks

#### 3. Library Standards Integration (MANDATORY)
- [ ] **Deprecation Checks**: Include deprecation warning checks for all mentioned libraries
- [ ] **Best Practices**: Add standards compliance steps to relevant tasks
- [ ] **Alternative Analysis**: Document analysis of alternative libraries considered
- [ ] **Standards Validation**: Validate all library choices against Library Usage Protocol

#### 4. Knowledge System Integration (MANDATORY)
- [ ] **Pattern Search**: Search CSF NIP knowledge system for relevant implementation patterns
- [ ] **Knowledge Storage**: Store task generation findings in CSF NIP knowledge system
- [ ] **Lessons Learned**: Document lessons learned during task generation process
- [ ] **Pattern Application**: Apply existing patterns from knowledge base to task structure

### Standards Enforcement Gates
**Task generation is BLOCKED until**:
- [ ] System Discovery Protocol completed with documented evidence
- [ ] All relevant standards identified and cited in task structure
- [ ] Existing solutions researched and documented with file paths
- [ ] Evidence collected for all major task decisions
- [ ] Library standards validation completed for all mentioned libraries
- [ ] Knowledge system integration completed with patterns stored

### Compliance Validation Commands
```bash
# MANDATORY: Run System Discovery Protocol
cd "C:\_Python\_Projects\__csf.nip"
python src/modules/orchestration/discovery_engine.py discover --project [current-feature]

# MANDATORY: Check Library Standards
python src/lib/core_utils/library_knowledge_extractor.py check --libs [libraries-in-tasks]

# MANDATORY: Search Knowledge System
python scripts/knowledge_interface.py search --query "[feature-type] patterns"

# MANDATORY: Validate Evidence Collection
python src/lib/core_utils/evidence_verifier.py validate --artifacts discovery,evidence,standards
```

**PROCEED**: Only after completing ALL validation steps above may task generation continue

## 🔧 Troubleshooting

### Common Issues and Solutions

**❌ "spec.md not found or incomplete"**
```bash
# Solution: Generate specification first
/speckit.specify "your feature description"
```

**❌ "plan.md not found"**
```bash
# Solution: Generate technical design first
/speckit.plan
```

**❌ "Too many tasks generated"**
```bash
# Solution: Limit task count and focus areas
/speckit.tasks "max-tasks:15, focus:core functionality"
```

**❌ "No dependencies identified"**
```bash
# Solution: Check plan.md for implementation sequence
cat /path/to/feature/plan.md
# Ensure plan includes implementation ordering
```

### Task Quality Issues

**Tasks Too Large**
- Break down complex tasks into smaller, manageable units
- Use granular acceptance criteria

**Missing Dependencies**
- Review technical design for implementation dependencies
- Consider data model, API, and UI dependencies

**Unclear Acceptance Criteria**
- Add specific, measurable success criteria
- Include validation steps and expected outcomes

## 🧠 Complete Operational Logic

The task generation follows this systematic process:

### 1. Context Discovery and Prerequisites Validation
Run prerequisite checker to identify:
- Available design artifacts (spec.md, plan.md, checklist.md, research.md)
- Feature context and constraints
- Template structure and formatting requirements

### 2. Artifact Analysis and Content Extraction
Analyze available artifacts to extract:
- **Specification Requirements**: Functional and non-functional requirements
- **Technical Design Decisions**: Architecture, technologies, and implementation approaches
- **User Stories and Acceptance Criteria**: Detailed user scenarios
- **Constraints and Dependencies**: Technical and business limitations
- **Risk Areas**: Complex implementation challenges

### 3. Task Identification and Categorization
Identify tasks across multiple categories:
- **Core Functionality**: Primary feature implementation tasks
- **Data Model and Database**: Schema, migrations, data access tasks
- **API Development**: Endpoint implementation and integration tasks
- **User Interface**: Frontend component and interaction tasks
- **Testing**: Unit, integration, and end-to-end testing tasks
- **Documentation**: Technical documentation and user guides
- **Deployment and Infrastructure**: Setup and deployment tasks
- **Security and Performance**: Specialized implementation tasks

### 4. Dependency Analysis and Sequencing
Determine task dependencies through:
- **Technical Dependencies**: Database schema before data access, API before UI
- **Logical Dependencies**: Core functionality before advanced features
- **Integration Dependencies**: Component integration points
- **Testing Dependencies**: Implementation before testing tasks

### 5. Task Estimation and Prioritization
Assign priority and complexity estimates:
- **Critical Path**: Tasks blocking other implementation work
- **High Priority**: Core functionality and security requirements
- **Medium Priority**: Important features and improvements
- **Low Priority**: Nice-to-have features and optimizations

### 6. Parallel Execution Planning
Identify tasks suitable for parallel development:
- **Independent Modules**: Components with minimal dependencies
- **Frontend/Backend Split**: Parallel UI and API development
- **Testing Preparation**: Test setup while implementation progresses

### 7. Task Generation and Formatting
Generate structured task list with:
- **Plan Context**: Tasks grouped under parent TSK-### plan
- **Sequential IDs**: Task-001, Task-002, etc. (distinct from plan TSK IDs)
- **Descriptive Titles**: Clear, action-oriented task names
- **Detailed Descriptions**: Implementation guidance and context
- **Acceptance Criteria**: Specific, measurable completion criteria
- **Dependencies**: Links to prerequisite tasks and cross-plan dependencies
- **Priority Markers**: Critical, high, medium, low priority indicators
- **Parallel Markers**: [P] for tasks suitable for parallel execution
- **Cross-Plan References**: Dependencies on other TSK-### plans when applicable

## 📝 Generated Tasks Structure

```markdown
# Implementation Tasks for TSK-[PLAN-ID]: [Plan Name]

## Phase 1: Foundation
### Task-001: [Task Title] [Priority]
**Description**: [Detailed task description and implementation guidance]

**Dependencies**: None

**Acceptance Criteria**:
- [ ] [Specific, measurable criterion]
- [ ] [Additional criteria]

**Estimated Effort**: [Complexity/Time estimate]

### Task-002: [Task Title] [Priority]
**Description**: [Task description]

**Dependencies**: Task-001

**Acceptance Criteria**:
- [ ] [Criterion]
- [ ] [Criterion]

**Estimated Effort**: [Estimate]

## Phase 2: Core Features
### Task-005: [Task Title] [P] [Priority]
**Description**: [Parallel executable task]

**Dependencies**: Task-001, Task-003

**Cross-Plan Dependencies**: TSK-XXX (if applicable)

**Acceptance Criteria**:
- [ ] [Criterion]

**Estimated Effort**: [Estimate]

## Cross-Plan Dependencies
- **TSK-XXX**: [Description of dependency on another plan]
- **TSK-YYY**: [Description of dependency on another plan]
```

## 📊 Task Categories and Examples

### Core Functionality Tasks
- **TSK-001**: Implement user authentication system
- **TSK-003**: Create data access layer
- **TSK-005**: Build core API endpoints

### Data Model Tasks
- **TSK-002**: Design and implement database schema
- **TSK-004**: Create data migration scripts
- **TSK-007**: Implement data validation logic

### User Interface Tasks
- **TSK-006**: Develop responsive layout components
- **TSK-009**: Implement user interaction flows
- **TSK-012**: Create error handling UI

### Testing Tasks
- **TSK-008**: Set up unit testing framework
- **TSK-011**: Write integration tests for API endpoints
- **TSK-014**: Create end-to-end test scenarios

### Documentation Tasks
- **TSK-010**: Write API documentation
- **TSK-013**: Create user guide documentation
- **TSK-015**: Document deployment procedures

## 🚨 Critical Constraints

**Dependency Integrity**: All task dependencies must be valid and complete

**Actionable Tasks**: Every task must have clear acceptance criteria

**Realistic Scoping**: Tasks should be manageable units of work (1-3 days typical)

**Coverage Completeness**: Tasks must cover all functional and non-functional requirements

**Traceability**: Tasks should reference source requirements and design decisions

**Quality Inclusion**: Testing and documentation tasks must be included

**Parallel Execution**: Identify and mark tasks suitable for parallel development

## 📁 File Management

**Location**: `.speckit/specs/TSK-###-plan-name/tasks.md`

**Backup**: Previous tasks.md files are backed up to `evidence/` directory before generation

**Version Control**: Track changes through git for collaboration and rollback

**Integration**: Tasks integrate with `/speckit.implement` for execution management

**Plan Context**: Tasks are linked to parent TSK-### plan in registry

**Cross-Plan References**: Dependencies on other plans tracked in TSK registry

## 🔗 Related Commands

- **Before**: `/speckit.plan` (technical design and architecture)
- **After**: `/speckit.implement` (execute implementation tasks)
- **Optional**: `/speckit.checklist` (validate task completeness)
- **Quality Gate**: `/speckit.analyze` (validate artifact consistency)
