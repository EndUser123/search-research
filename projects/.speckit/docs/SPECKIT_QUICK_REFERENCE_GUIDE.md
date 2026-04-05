# Speckit v2.0 - Quick Reference Guide

## Overview

This quick reference guide provides essential Speckit commands, workflows, and patterns for daily use. Keep this guide handy for rapid reference during development.

## Table of Contents

1. [Essential Commands](#essential-commands)
2. [Common Workflows](#common-workflows)
3. [Task Management](#task-management)
4. [Evidence Collection](#evidence-collection)
5. [Troubleshooting](#troubleshooting)
6. [Configuration](#configuration)
7. [Integration Commands](#integration-commands)

## Essential Commands

### Basic Speckit Commands

```bash
# Validate project setup
speckit constitution --validate

# Create new specification
speckit specify "Feature description" --knowledge-context

# Clarify requirements
speckit clarify

# Research best practices
speckit research --spike "topic" --knowledge-synthesis

# Create implementation plan
speckit plan --pattern-validation

# Generate task breakdown
speckit tasks --export-dag

# Quality checklist
speckit checklist --bundle security,performance,ux

# Project analysis
speckit analyze --write-report

# Execute implementation
speckit execute --feature-dir ./feature --engine dev6

# Complete workflow
speckit flow
```

### Task Management Commands

```bash
# List active tasks
speckit tasks list --status active

# Create new task
speckit tasks create --title "Task title" --priority high

# Update task status
speckit tasks update --task-id TSK-001 --status in_progress

# Assign task
speckit tasks assign --task-id TSK-001 --assignee "developer"

# View task details
speckit tasks show --task-id TSK-001

# Generate task report
speckit tasks report --period last-30-days
```

### Evidence Commands

```bash
# Generate evidence summary
speckit evidence summary --task-id TSK-001

# Validate evidence completeness
speckit evidence validate --required

# Archive old evidence
speckit evidence archive --older-than 90days

# Search evidence
speckit evidence search --keyword "security" --date-range 30days
```

## Common Workflows

### New Feature Development Workflow

```bash
# 1. Start with knowledge research
cd "C:\_Python\_Projects\__csf.nip" && python scripts/knowledge_interface.py search --keywords "your feature" --limit 10

# 2. Create specification
speckit specify "User authentication system" --knowledge-context

# 3. Clarify requirements
speckit clarify --focus security,performance

# 4. Research implementation patterns
speckit research --spike "authentication patterns" --knowledge-synthesis

# 5. Create implementation plan
speckit plan --pattern-validation --threat-model

# 6. Generate tasks
speckit tasks --export-dag --time-estimates

# 7. Quality checklist
speckit checklist --bundle security,performance,ux

# 8. Execute implementation
speckit execute --feature-dir ./auth-system --engine dev6 --trust-threshold 0.8

# 9. Final analysis
speckit analyze --write-report --comprehensive
```

### Bug Fix Workflow

```bash
# 1. Document bug
speckit bug report --title "Issue description" --severity high

# 2. Root cause analysis
speckit debug --analyze --evidence-collection --task-id TSK-BUG-001

# 3. Create fix plan
speckit plan --bug-fix --root-cause "identified issue" --task-id TSK-BUG-001

# 4. Implement fix
speckit execute --task TSK-BUG-001 --mode focused --regression-testing

# 5. Validate fix
speckit test --regression --affected-modules affected-component
```

### Quick Task Workflow

```bash
# Quick task creation and execution
speckit specify "Quick fix" --minimal
speckit plan --simple --task-id TSK-QUICK-001
speckit execute --task TSK-QUICK-001 --mode fast-track
```

## Task Management

### Task Status Values

| Status | Description | When to Use |
|--------|-------------|-------------|
| `planned` | Task is planned but not started | Initial task creation |
| `active` | Task is being worked on | When work begins |
| `blocked` | Task is blocked by dependencies | When blocked |
| `review` | Task is in review phase | When implementation complete |
| `completed` | Task is completed and verified | When fully done |
| `archived` | Task is archived for reference | After completion |

### Priority Levels

| Priority | Description | Response Time |
|----------|-------------|---------------|
| `critical` | Blocks release or major functionality | Immediate |
| `high` | Important for current sprint | Within 1 day |
| `medium` | Standard priority | Within 3 days |
| `low` | Nice to have | Within 1 week |

### Task Management Quick Commands

```powershell
# PowerShell task management
.\.speckit\scripts\powershell\manage-tasks.ps1 -Action List
.\.speckit\scripts\powershell\manage-tasks.ps1 -Action Create -Title "New task" -Priority high
.\.speckit\scripts\powershell\manage-tasks.ps1 -Action Update -TaskId TSK-001 -Status completed

# Bash task management
./.speckit/scripts/bash/manage-tasks.sh --action list
./.speckit/scripts/bash/manage-tasks.sh --action create --title "New task" --priority high
./.speckit/scripts/bash/manage-tasks.sh --action update --task-id TSK-001 --status completed
```

## Evidence Collection

### Evidence Types

| Type | Description | When Generated |
|------|-------------|----------------|
| `requirements` | Requirements analysis | During specification |
| `research` | Research findings | During research phase |
| `implementation` | Code changes | During implementation |
| `testing` | Test results | During testing |
| `validation` | Quality validation | During validation |
| `review` | Code review | During review process |

### Evidence Management

```bash
# Generate evidence summary
speckit evidence summary --format markdown

# Link evidence to task
speckit evidence link --task-id TSK-001 --evidence-file evidence.json

# Validate evidence completeness
speckit evidence validate --required --task-id TSK-001

# Archive evidence
speckit evidence archive --task-id TSK-001 --reason completed
```

## Troubleshooting

### Common Issues and Solutions

#### Speckit Command Not Found
```bash
# Check installation
which speckit
speckit --version

# Reinstall if needed
pip install --upgrade speckit-cli

# Check Python path
echo $PATH
```

#### Constitution Validation Fails
```bash
# Check specific issues
speckit constitution --validate --verbose

# Update constitution
speckit constitution --update --interactive

# Reset to defaults
speckit constitution --reset --backup
```

#### Task Management Issues
```bash
# Validate task storage
speckit tasks validate --check-integrity

# Reset task counter
speckit tasks reset-counter --confirm

# Backup and restore
speckit tasks backup --output backup.json
speckit tasks restore --input backup.json
```

#### Evidence Issues
```bash
# Check evidence directory
speckit evidence check --directory .speckit/evidence

# Repair broken links
speckit evidence repair --auto-fix

# Clean up orphaned files
speckit evidence cleanup --orphaned
```

## Configuration

### Essential Configuration Files

```
.speckit/
├── config/
│   ├── speckit_config.json          # Main configuration
│   ├── project-config.json          # Project-specific settings
│   ├── team.json                    # Team configuration
│   └── quality-gates.json           # Quality gate settings
├── memory/
│   └── constitution.md              # Project constitution
└── templates/                       # Workflow templates
```

### Common Configuration Commands

```bash
# Set project name
speckit config set project.name "My Project"

# Set default engine
speckit config set default.engine dev6

# Configure notifications
speckit config set notifications.enabled true
speckit config set notifications.channel slack

# Set quality thresholds
speckit config set quality.gates.threshold 0.8

# View configuration
speckit config show --all
speckit config show --section project
```

### Reset Configuration

```bash
# Reset to defaults (safe)
speckit config reset --safe

# Full reset (use with caution)
speckit config reset --full --backup

# Validate configuration
speckit config validate --strict
```

## Integration Commands

### Git Integration

```bash
# Install Git hooks
speckit git-hooks install

# Validate branch
speckit git validate-branch --current

# Create feature branch
speckit git create-feature-branch --task-id TSK-001

# Sync with remote
speckit git sync --validate-before-push
```

### IDE Integration

```bash
# VS Code integration
speckit ide setup --vscode

# Generate VS Code tasks
speckit ide generate-tasks --output .vscode/tasks.json

# Validate IDE setup
speckit ide validate --vscode
```

### CI/CD Integration

```bash
# Generate GitHub Actions
speckit cicd generate --platform github-actions --output .github/workflows/

# Validate CI/CD setup
speckit cicd validate --platform github-actions

# Test CI/CD locally
speckit cicd test-local --platform github-actions
```

## Keyboard Shortcuts (VS Code)

Add to `.vscode/keybindings.json`:

```json
[
  {
    "key": "ctrl+shift+s v",
    "command": "speckit.validate",
    "args": ["constitution"]
  },
  {
    "key": "ctrl+shift+s a",
    "command": "speckit.analyze",
    "args": ["--file", "${file}"]
  },
  {
    "key": "ctrl+shift+s t",
    "command": "speckit.tasks",
    "args": ["--current-feature"]
  },
  {
    "key": "ctrl+shift+s e",
    "command": "speckit.execute",
    "args": ["--feature-dir", "${workspaceFolder}"]
  }
]
```

## Quick Templates

### Feature Specification Template
```markdown
# Feature: {{FEATURE_NAME}}

## Overview
{{DESCRIPTION}}

## Requirements
- [ ] Functional requirement 1
- [ ] Functional requirement 2

## Acceptance Criteria
- [ ] Criteria 1
- [ ] Criteria 2

## Technical Notes
{{TECHNICAL_NOTES}}
```

### Task Template
```json
{
  "task_id": "TSK-XXX",
  "title": "Task title",
  "description": "Task description",
  "status": "planned",
  "priority": "medium",
  "estimated_hours": 0,
  "acceptance_criteria": [
    "Criteria 1",
    "Criteria 2"
  ],
  "dependencies": [],
  "tags": ["tag1", "tag2"]
}
```

## Performance Tips

### Speed Up Speckit Operations

```bash
# Enable parallel processing
speckit config set performance.parallel true
speckit config set performance.workers 4

# Optimize cache
speckit optimize cache --aggressive

# Use fast mode for quick operations
speckit analyze --quick-check --fast-mode
```

### Memory Optimization

```bash
# Limit memory usage
speckit config set performance.memory_limit 512

# Enable garbage collection
speckit config set performance.gc_auto true

# Monitor performance
speckit monitor performance --real-time
```

## Help and Support

### Getting Help

```bash
# General help
speckit --help

# Command-specific help
speckit specify --help
speckit tasks --help

# Check system health
speckit doctor

# Troubleshooting mode
speckit --verbose --debug
```

### Common Help Commands

```bash
# Show current status
speckit status

# Show version information
speckit --version

# List available commands
speckit commands list

# Show configuration
speckit config show
```

### Support Resources

- **Documentation**: `.speckit/docs/`
- **Templates**: `.speckit/templates/`
- **Examples**: `.speckit/examples/`
- **Integration Guides**: `.speckit/docs/integration/`

## Quick Start Checklist

### New Project Setup

```bash
☐ Copy .speckit framework to project
☐ Configure project settings
☐ Create project constitution
☐ Set up team configuration
☐ Install Git hooks
☐ Configure IDE integration
☐ Validate setup with `speckit doctor`
☐ Create first test feature
☐ Train team members
```

### Daily Workflow

```bash
☐ Start day with `speckit status`
☐ Review active tasks
☐ Update task progress
☐ Generate evidence for work completed
☐ Run quality checks before commits
☐ End day with `speckit analyze --quick-check`
```

---

## Emergency Commands

### System Recovery

```bash
# Full system reset
speckit emergency reset --confirm

# Restore from backup
speckit emergency restore --backup latest

# Validate system integrity
speckit emergency validate --full
```

### Data Recovery

```bash
# Recover lost tasks
speckit emergency recover-tasks --from-evidence

# Repair corrupted data
speckit emergency repair --auto-fix

# Export emergency backup
speckit emergency backup --full --compress
```

---

**Tip**: Bookmark this guide for quick access during development. For detailed information, refer to the comprehensive documentation in `.speckit/docs/`.
