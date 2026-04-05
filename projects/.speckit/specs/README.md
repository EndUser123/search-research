# Speckit Executable Specifications

This directory contains executable specifications that operationalize the speckit workflow methodology. The system combines the comprehensive SPECKIT_WORKTREE_COMPLETE_WORKFLOW.md guide with practical, automated templates and tools.

## Overview

The speckit executable specifications system provides:

- **Template-based specifications**: Pre-built templates for different work types
- **Worktree management**: Isolated development environments for each project
- **Flow Orchestrator integration**: Seamless connection to the 7-phase Flow Orchestrator
- **Quality validation**: Automated specification validation and quality gates
- **Knowledge system integration**: Leverages organizational knowledge throughout the workflow

## Directory Structure

```
.speckit/specs/
├── .templates/                    # Template system
│   ├── feature-development/       # Feature development templates
│   │   ├── SPECIFY.md            # Specification template
│   │   ├── PLAN.md              # Architecture planning template
│   │   ├── TASKS.md             # TDD-driven task breakdown
│   │   └── IMPLEMENT.md         # Implementation execution template
│   ├── bug-fix/                 # Bug fix templates
│   │   ├── SPECIFY.md            # Bug analysis and specification
│   │   ├── PLAN.md              # Fix strategy template
│   │   ├── TASKS.md             # Fix implementation tasks
│   │   └── IMPLEMENT.md         # Fix execution and validation
│   ├── rca/                     # Root Cause Analysis templates
│   ├── research/                # Research project templates
│   ├── performance/             # Performance optimization templates
│   └── security/                # Security assessment templates
├── active/                       # Currently active projects
├── TSK-XXX-project-name/         # Individual project specifications
│   ├── SPECIFY.md               # Project specification
│   ├── PLAN.md                  # Architecture and planning
│   ├── TASKS.md                 # Task breakdown
│   ├── IMPLEMENT.md             # Implementation tracking
│   ├── worktree_config.json     # Worktree configuration
│   └── flow_session.json        # Flow Orchestrator session state
└── README.md                     # This file
```

## Quick Start

### 1. Create a New Feature Development Project

```bash
# Create a new worktree with feature development templates
cd C:\_Python\_Projects\.speckit
python scripts/worktree_manager.py create TSK-001 feature-development "user authentication system"

# This creates:
# - ../feature-development-TSK-001-user-authentication-system/ (git worktree)
# - specs/TSK-001-user-authentication-system/ (project specifications)
```

### 2. Set Up Development Environment

```bash
# Navigate to the new worktree
cd ../feature-development-TSK-001-user-authentication-system

# Run the automated setup script
./setup_dev_env.sh
```

### 3. Start the Flow Orchestrator

```bash
# Create a Flow Orchestrator session from your specifications
cd C:\_Python\_Projects\.speckit
python scripts/flow_orchestrator_integration.py create-session --spec-dir specs/TSK-001-user-authentication-system

# Execute Phase 1: Constitution Orchestration
python scripts/flow_orchestrator_integration.py execute-phase "Phase 1" --spec-dir specs/TSK-001-user-authentication-system
```

### 4. Validate Your Specifications

```bash
# Validate all specification files
python scripts/specification_validator.py specs/TSK-001-user-authentication-system

# Get detailed validation report
python scripts/specification_validator.py specs/TSK-001-user-authentication-system --output validation_report.json
```

## Available Work Types

### Feature Development
- **Purpose**: New feature implementation with comprehensive TDD approach
- **Templates**: SPECIFY, PLAN, TASKS, IMPLEMENT
- **TDD Integration**: Full test-driven development workflow
- **Knowledge Integration**: Leverages existing patterns and best practices

### Bug Fix
- **Purpose**: Systematic bug resolution with root cause analysis
- **Templates**: SPECIFY, PLAN, TASKS, IMPLEMENT
- **Focus**: Root cause analysis, regression prevention
- **Quality Gates**: Comprehensive testing to prevent regressions

### Root Cause Analysis (RCA)
- **Purpose**: Deep investigation of systemic issues
- **Templates**: Customized for investigation workflows
- **Method**: Structured analysis and corrective action planning

### Research
- **Purpose**: Knowledge discovery and documentation
- **Templates**: Research methodology and documentation
- **Output**: Actionable findings and recommendations

### Performance Optimization
- **Purpose**: System performance improvement
- **Templates**: Performance analysis and optimization planning
- **Focus**: Benchmarking, profiling, optimization

### Security Assessment
- **Purpose**: Security vulnerability assessment and remediation
- **Templates**: Security analysis and remediation workflows
- **Compliance**: Security standards and best practices

## Template Features

### Knowledge System Integration
All templates include:
- **Knowledge Discovery**: Automated search for relevant patterns
- **Best Practices**: Integration with organizational knowledge base
- **Lessons Learned**: Documentation of discoveries for future use
- **Pattern Recognition**: Identification of reusable solutions

### TDD Integration
Development templates include:
- **Test Pyramid Strategy**: Comprehensive testing approach
- **Red-Green-Refactor Cycles**: Structured TDD workflow
- **Quality Gates**: Automated validation at each phase
- **Test Coverage**: Requirements for comprehensive test coverage

### Quality Assurance
Built-in quality features:
- **Acceptance Criteria**: Clear success metrics
- **Validation Checkpoints**: Phase-based quality gates
- **Evidence Collection**: Comprehensive evidence tracking
- **Compliance Checking**: Standards and governance validation

## Worktree Management

### Creating Worktrees
```bash
# Basic worktree creation
python scripts/worktree_manager.py create TSK-002 feature-development "payment processing"

# With custom base branch
python scripts/worktree_manager.py create TSK-003 bug-fix "login issue" --base-branch develop

# List all worktrees
python scripts/worktree_manager.py list

# Sync worktree with latest changes
python scripts/worktree_manager.py sync feature-development-TSK-002-payment-processing

# Remove worktree when complete
python scripts/worktree_manager.py remove feature-development-TSK-002-payment-processing
```

### Worktree Features
- **Isolated Environments**: Each project has its own git worktree
- **Template Integration**: Automatic template population
- **Development Setup**: Automated environment configuration
- **Session Management**: Track worktree sessions and state

## Flow Orchestrator Integration

### Session Management
```bash
# Create session from existing specifications
python scripts/flow_orchestrator_integration.py create-session --spec-dir specs/TSK-001-project-name

# Execute specific phases
python scripts/flow_orchestrator_integration.py execute-phase "Phase 1" --spec-dir specs/TSK-001-project-name
python scripts/flow_orchestrator_integration.py execute-phase "Phase 2" --spec-dir specs/TSK-001-project-name

# Check progress
python scripts/flow_orchestrator_integration.py status --spec-dir specs/TSK-001-project-name
```

### Phase Execution
The system supports all 7 phases of the Flow Orchestrator:
1. **Phase 1**: Constitution Orchestration
2. **Phase 2**: Knowledge-Guided Specification
3. **Phase 3**: Specification Refinement (conditional)
4. **Phase 4**: TDD-Enhanced Architecture & Planning
5. **Phase 5**: Implementation
6. **Phase 6**: Analysis & Validation
7. **Phase 7**: Final Verification & Completion

## Validation and Quality

### Specification Validation
```bash
# Validate single file
python scripts/specification_validator.py specs/TSK-001-project-name/SPECIFY.md

# Validate entire project
python scripts/specification_validator.py specs/TSK-001-project-name

# Set quality threshold
python scripts/specification_validator.py specs/TSK-001-project-name --threshold 80.0

# Save detailed report
python scripts/specification_validator.py specs/TSK-001-project-name --output quality_report.json
```

### Quality Gates
The system enforces quality gates at multiple levels:
- **Structure**: Document organization and completeness
- **Content**: Quality and completeness of content
- **Knowledge Integration**: Proper use of organizational knowledge
- **TDD Compliance**: Test-driven development requirements
- **Standards Compliance**: Alignment with project standards

## Configuration

### Worktree Configuration
Each project has a `worktree_config.json`:
```json
{
  "project_id": "TSK-001",
  "work_type": "feature-development",
  "feature_name": "user authentication system",
  "worktree_name": "feature-development-TSK-001-user-authentication-system",
  "worktree_path": "../feature-development-TSK-001-user-authentication-system",
  "base_branch": "main",
  "created_at": "1635724800",
  "session_id": "uuid-v4"
}
```

### Flow Session Configuration
Each project tracks Flow Orchestrator state in `flow_session.json`:
```json
{
  "session_id": "uuid-v4",
  "project_id": "TSK-001",
  "project_name": "user authentication system",
  "work_type": "feature-development",
  "phase_state": {
    "current_phase": "Phase 1",
    "phase_status": {
      "phase_1": {"status": "completed", "duration": 15, "success_criteria_met": true},
      "phase_2": {"status": "pending"}
    },
    "workflow_state": "active"
  },
  "evidence": {
    "base_dir": "evidence",
    "collected": ["constitution_compliance.json"],
    "phase_evidence": {"phase_1": ["constitution_compliance.json"]}
  }
}
```

## Best Practices

### Template Usage
1. **Complete All Sections**: Fill in all template sections completely
2. **Replace Placeholders**: Ensure all [placeholders] are replaced with actual content
3. **Knowledge Integration**: Always search and integrate relevant organizational knowledge
4. **TDD Approach**: Follow the test-driven development methodology strictly

### Worktree Management
1. **Clean Worktrees**: Remove worktrees when projects are complete
2. **Regular Syncs**: Keep worktrees synchronized with main branch
3. **Isolated Development**: Use worktrees for isolation, not for long-term divergence
4. **Documentation**: Keep project documentation updated in the spec directory

### Quality Assurance
1. **Early Validation**: Validate specifications early and often
2. **Quality Gates**: Don't proceed to next phase without meeting quality gates
3. **Evidence Collection**: Collect and organize evidence throughout the process
4. **Continuous Improvement**: Contribute lessons learned back to knowledge system

## Integration with Existing Systems

### CSF NIP Integration
- **Knowledge System**: Templates integrate with CSF NIP knowledge base
- **Agent Orchestration**: Flow Orchestrator uses CSF NIP agents
- **Standards Compliance**: Aligns with CSF NIP development standards
- **Evidence Collection**: CSF NIP evidence patterns applied

### Git Workflow Integration
- **Worktree Management**: Standard git worktree commands
- **Branch Strategy**: Integrates with existing branching strategies
- **Commit Patterns**: Supports semantic commit messages
- **Merge Strategies**: Compatible with existing merge workflows

### CI/CD Integration
- **Quality Gates**: Automated validation in CI/CD pipelines
- **Test Execution**: Automated test execution and reporting
- **Security Scanning**: Integrated security validation
- **Deployment Preparation**: Automated deployment readiness checks

## Troubleshooting

### Common Issues

**Worktree Creation Fails**
- Ensure you're in the correct project directory
- Check git repository status
- Verify base branch exists

**Template Population Issues**
- Check template directory structure
- Verify template files exist
- Check file permissions

**Flow Orchestrator Integration Issues**
- Verify flow session exists
- Check project specification directory
- Validate JSON configuration files

**Validation Failures**
- Review validation report for specific issues
- Check placeholder replacement
- Verify required sections are complete

### Getting Help
- Check the validation reports for detailed feedback
- Review the original SPECKIT_WORKTREE_COMPLETE_WORKFLOW.md guide
- Consult the Flow Orchestrator documentation
- Check CSF NIP documentation for integration patterns

## Contributing

To contribute improvements to the speckit executable specifications system:

1. **Template Improvements**: Enhance templates for better usability
2. **New Work Types**: Add templates for additional work types
3. **Validation Rules**: Improve validation logic and rules
4. **Integration Enhancements**: Improve integration with other systems
5. **Documentation**: Update and improve documentation

All contributions should follow the existing patterns and maintain compatibility with the current system.
