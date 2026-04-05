---
name: "/speckit.implement"
category: "Speckit Workflow"
purpose: "Execute the implementation plan by processing and executing all tasks defined in tasks.md"
entry_point: "primary"
---

# Speckit Implement - Task Execution Management
n
### **MANDATORY: Tools Registry & Knowledge System Integration**

Before ANY task execution, the implement command MUST:

1. **Tools Registry Check**: Query available tools before creating new utilities
   ```bash
   cd "C:_Python_Projects__csf.nip" && python src/lib/core_utils/tools_registry_validator.py --test tools
   ```

2. **Knowledge System Search**: Find existing implementation patterns
   ```bash
   cd "C:_Python_Projects__csf.nip" && python scripts/knowledge_interface.py search --type implementation --limit 10
   ```

3. **Pattern Application**: Use proven patterns from knowledge system
4. **Tool Registration**: Register new tools for future reuse

**ENFORCEMENT**: No implementation may proceed without these checks.

Execute the implementation plan by systematically processing and completing all tasks defined in tasks.md. This command manages the implementation workflow, tracks progress, handles dependencies, and ensures quality standards throughout the development process.

## 🚀 Quick Start

### Execute All Tasks Sequentially
```bash
/speckit.implement
```

### Execute with Parallel Processing
```bash
/speckit.implement "parallel:true, max-concurrent:4"
```

### Execute Specific Task Range
```bash
/speckit.implement "tasks:TSK-001-TSK-010, focus:core_functionality"
```

### Execute with Quality Gates
```bash
/speckit.implement "quality-gates:true, testing:comprehensive, review:required"
```

## ⚙️ Command Options

Implementation execution accepts various parameters for workflow control:

| Parameter | Values | Description |
|-----------|--------|-------------|
| **Execution Mode** | `sequential`, `parallel`, `mixed` | Task execution strategy |
| **Task Range** | `TSK-001-TSK-010`, `TSK-005`, `core` | Specific tasks or phases to execute |
| **Max Concurrent** | Number | Maximum parallel tasks (default: 4) |
| **Quality Gates** | `true`, `false` | Enable quality gate validation |
| **Testing Level** | `basic`, `comprehensive`, `full` | Testing requirements intensity |
| **Review Required** | `true`, `false` | Require code review before task completion |
| **Continue on Error** | `true`, `false` | Continue execution when tasks fail |
| **Dry Run** | `true`, `false` | Validate tasks without executing |
| **Focus Areas** | `core`, `ui`, `api`, `testing`, `documentation` | Priority focus areas |

## 📋 Use Cases

### When to Use /speckit.implement

- **Implementation Phase**: After planning and task breakdown completion
- **Development Sprints**: Execute structured development workflows
- **Team Coordination**: Manage distributed development efforts
- **Quality Assurance**: Ensure consistent implementation standards
- **Progress Tracking**: Monitor implementation progress and completion

### When NOT to Use /speckit.implement

- **Planning Phase**: Use `/speckit.plan` for design and architecture
- **Research Phase**: Use `/speckit.research` for investigation
- **Task Creation**: Use `/speckit.tasks` for task breakdown

## 🔧 Prerequisites

### Required Artifacts
1. **Complete Task List**: `tasks.md` with all implementation tasks and dependencies
2. **Implementation Plan**: `plan.md` with technical design decisions
3. **Feature Specification**: `spec.md` with requirements and constraints
4. **Development Environment**: Ready development environment with required tools

### Validation Commands
```bash
# Verify required artifacts exist
cd /path/to/feature
ls -la | grep -E "(tasks\.md|plan\.md|spec\.md)"

# Check task dependencies
grep -A 5 "Dependencies:" /path/to/feature/tasks.md

# Validate development environment
cd "C:\_Python\_Projects\.speckit"
python scripts/speckit_execute.py --validate-environment
```

## 🔧 Troubleshooting

### Common Issues and Solutions

**❌ "tasks.md not found or incomplete"**
```bash
# Solution: Generate tasks first
/speckit.tasks
```

**❌ "Circular dependencies detected"**
```bash
# Solution: Review and fix task dependencies
grep -B 2 -A 2 "Dependencies:" /path/to/feature/tasks.md
# Remove or restructure circular dependencies
```

**❌ "Missing prerequisites for task execution"**
```bash
# Solution: Check and install missing dependencies
cd /path/to/feature
python -m pip install -r requirements.txt
# Set up development environment
```

**❌ "Task execution failed"**
```bash
# Solution: Review failure details and continue
/speckit.implement "continue-on-error:true, focus:failed_tasks"
```

### Execution Issues

**Parallel Execution Conflicts**
- Reduce concurrent task count
- Use sequential mode for conflicting tasks
- Review task dependencies and resource usage

**Environment Setup Issues**
- Validate development environment setup
- Check required tools and dependencies
- Ensure proper configuration files exist

**Quality Gate Failures**
- Review quality criteria and standards
- Address specific quality issues
- Adjust quality thresholds if appropriate

## 🧠 Complete Operational Logic

The implementation process follows this systematic workflow:

### 1. Environment Validation and Setup
Validate development environment and prerequisites:
- **Artifact Availability**: Ensure tasks.md, plan.md, spec.md exist
- **Tool Requirements**: Verify required development tools are available
- **Configuration Setup**: Validate environment configuration
- **Dependency Installation**: Install required dependencies

### 2. Task Analysis and Dependency Resolution
Analyze tasks and resolve execution dependencies:
- **Task Parsing**: Extract tasks, dependencies, and priorities from tasks.md
- **Dependency Graph**: Build task dependency graph for execution ordering
- **Parallel Identification**: Identify tasks suitable for parallel execution
- **Critical Path**: Determine critical path for project completion

### 3. Execution Planning and Scheduling
Create execution plan based on parameters:
- **Execution Mode**: Sequential, parallel, or mixed execution strategy
- **Resource Allocation**: Assign tasks based on available resources
- **Quality Gates**: Plan quality validation checkpoints
- **Progress Tracking**: Setup progress monitoring and reporting

### 4. Task Execution Management
Execute tasks with comprehensive management:
- **Sequential Execution**: Execute tasks in dependency order
- **Parallel Processing**: Execute independent tasks concurrently
- **Error Handling**: Manage task failures and recovery
- **Progress Monitoring**: Track completion status and progress

### 5. Quality Assurance and Validation
Ensure implementation quality throughout:
- **Code Quality**: Apply coding standards and best practices
- **Testing Validation**: Execute required testing activities
- **Review Process**: Conduct code reviews when required
- **Quality Gates**: Validate quality criteria before task completion

### 6. Integration and System Testing
Validate integrated system functionality:
- **Component Integration**: Test component interactions
- **System Testing**: Validate end-to-end functionality
- **Performance Testing**: Validate performance requirements
- **Security Testing**: Validate security implementation

### 7. Documentation and Completion
Finalize implementation with documentation:
- **Documentation Updates**: Update technical documentation
- **Implementation Summary**: Create implementation completion report
- **Lessons Learned**: Document implementation insights and improvements
- **Handover Preparation**: Prepare for deployment and maintenance

## 📝 Execution Workflow Structure

```markdown
# Implementation Execution

## Phase 1: Foundation (TSK-001 to TSK-005)
### TSK-001: Database Schema Implementation
**Status**: ✅ Completed
**Duration**: 2 hours
**Quality Gates**: ✅ Passed

### TSK-002: Data Access Layer
**Status**: 🔄 In Progress
**Duration**: 1.5 hours (estimated)
**Dependencies**: TSK-001

## Phase 2: Core Features (TSK-006 to TSK-015)
### TSK-006: API Endpoints [P]
**Status**: ⏳ Waiting
**Dependencies**: TSK-002

### TSK-007: Authentication System [P]
**Status**: ⏳ Waiting
**Dependencies**: TSK-002

## Progress Summary
- **Total Tasks**: 20
- **Completed**: 5 (25%)
- **In Progress**: 1 (5%)
- **Waiting**: 14 (70%)
- **Failed**: 0 (0%)

## Quality Metrics
- **Code Quality Score**: 8.5/10
- **Test Coverage**: 85%
- **Documentation Coverage**: 90%
```

## 📊 Execution Categories and Examples

### Sequential Execution
- **Database Schema**: Foundation tasks that must complete first
- **Core Services**: Services depending on database and infrastructure
- **User Interface**: Frontend components depending on backend services

### Parallel Execution
- **Component Development**: Independent UI components
- **Service Development**: Parallel API endpoint development
- **Testing Preparation**: Test setup while implementation progresses

### Quality Gates
- **Code Review**: Peer review before task completion
- **Testing**: Unit tests, integration tests validation
- **Documentation**: Required documentation completion
- **Performance**: Performance criteria validation

## 🚨 Critical Constraints

**Dependency Resolution**: All task dependencies must be resolved before execution

**Quality Standards**: Implementation must meet defined quality criteria

**Progress Validation**: Continuous progress monitoring and validation

**Error Recovery**: Robust error handling and recovery mechanisms

**Resource Management**: Efficient resource allocation and utilization

**Integration Validation**: System integration testing and validation

**Documentation Completion**: Technical documentation must be kept current

## 📁 File Management

**Location**: Executes from feature directory root

**Progress Tracking**: Creates and updates implementation progress files

**Quality Records**: Maintains quality validation records and metrics

**Integration Logs**: Creates integration testing and validation logs

## 🔗 Related Commands

- **Before**: `/speckit.tasks` (task breakdown)
- **During**: `/speckit.checklist` (quality validation)
- **After**: `/speckit.analyze` (final validation)
- **Quality Gate**: `/speckit.execute` (comprehensive workflow execution)
