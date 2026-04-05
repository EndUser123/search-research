# Speckit v2.0 - Comprehensive User Guide

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Core Components](#core-components)
4. [Command Reference](#command-reference)
5. [Task Management System](#task-management-system)
6. [Workflow Integration](#workflow-integration)
7. [Configuration Management](#configuration-management)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)
10. [Advanced Features](#advanced-features)

## Overview

### What is Speckit?

Speckit is a comprehensive development framework that provides a structured, evidence-based approach to software development. It combines requirements gathering, research, planning, implementation, and validation into a unified workflow that ensures high-quality, maintainable code.

### Key Benefits

- **Evidence-Based Development**: Every decision is backed by research and validation
- **Structured Workflows**: Clear, repeatable processes for development tasks
- **Task Management**: Built-in TSK-### format task tracking and management
- **Quality Assurance**: Integrated validation gates and trust scoring
- **Knowledge Integration**: Leverages existing patterns and best practices
- **Scalability**: Works for projects of all sizes

### Architecture

```
.speckit/
├── config/          # Configuration files
├── templates/       # Command templates
├── memory/          # Constitution and project memory
├── scripts/         # PowerShell and Bash scripts
├── cache/           # Task and evidence storage
├── docs/           # Documentation
└── evidence/       # Generated evidence
```

## Quick Start

### Installation and Setup

1. **Initialize Speckit in your project**:
```powershell
# Copy the central framework to your project
Copy-Item "C:\_Python\_Projects\.speckit" ".speckit" -Recurse
```

2. **Configure your project**:
```powershell
# Create project configuration
.\.speckit\scripts\powershell\create-new-feature.ps1 -ProjectName "YourProject"
```

3. **Validate setup**:
```bash
# Run constitution validation
/speckit.constitution --validate
```

### Your First Workflow

1. **Define Requirements**:
```bash
/speckit.specify "User authentication system with OAuth2"
```

2. **Clarify Requirements**:
```bash
/speckit.clarify
```

3. **Research Best Practices**:
```bash
/speckit.research --spike "OAuth2 security patterns"
```

4. **Create Implementation Plan**:
```bash
/speckit.plan --pattern-validation
```

5. **Generate Tasks**:
```bash
/speckit.tasks --export-dag
```

6. **Execute Implementation**:
```bash
/speckit.execute --feature-dir ./auth-system --engine dev6
```

## Core Components

### 1. Constitution System

The constitution defines project standards, principles, and constraints.

**Location**: `.speckit/memory/constitution.md`

**Purpose**:
- Establish project standards and values
- Define architectural principles
- Set quality requirements and constraints

**Usage**:
```bash
# Validate project compliance
/speckit.constitution --validate

# Update constitution
/speckit.constitution --update
```

### 2. Template System

Speckit uses templates for consistent documentation and artifacts.

**Templates Available**:
- `spec-template.md`: Feature specifications
- `plan-template.md`: Implementation plans
- `tasks-template.md`: Task breakdowns
- `checklist-template.md`: Quality checklists
- `agent-file-template.md`: Agent configuration

**Usage**:
```bash
# Create from template
/speckit.specify "Feature description" --template custom
```

### 3. Task Management System

Built-in task tracking with TSK-### format.

**Features**:
- Automatic task ID generation
- Status tracking (active, completed, archived)
- Evidence linking
- Progress monitoring

**Storage**:
- `cache/active_tasks.json`: Current tasks
- `cache/completed_tasks.json`: Completed tasks
- `cache/task_history.json`: Task history

### 4. Script Integration

Cross-platform scripts for automation.

**PowerShell Scripts** (Windows):
- `create-new-feature.ps1`: Feature setup
- `update-agent-context.ps1`: Context management
- `manage-tasks.ps1`: Task operations
- `setup-plan.ps1`: Plan initialization

**Bash Scripts** (Linux/Mac):
- `generate-task-id.sh`: Task ID generation
- `manage-tasks.sh`: Task management

## Command Reference

### Core Commands

#### `/speckit.constitution`
```bash
# Validate project compliance
/speckit.constitution --validate

# Update constitution
/speckit.constitution --update

# Check specific standards
/speckit.constitution --check security,performance
```

#### `/speckit.specify`
```bash
# Basic specification
/speckit.specify "Feature description"

# With knowledge context
/speckit.specify "Feature" --knowledge-context

# From template
/speckit.specify "Feature" --template web-application
```

#### `/speckit.clarify`
```bash
# Clarify current specification
/speckit.clarify

# Focus on specific aspects
/speckit.clarify --focus security,performance

# Interactive clarification
/speckit.clarify --interactive
```

#### `/speckit.research`
```bash
# Full research phase
/speckit.research

# Spike research on specific topic
/speckit.research --spike "OAuth2 patterns"

# With knowledge synthesis
/speckit.research --knowledge-synthesis

# Research with sources
/speckit.research --sources --max-sources 10
```

#### `/speckit.plan`
```bash
# Create implementation plan
/speckit.plan

# With pattern validation
/speckit.plan --pattern-validation

# Include threat modeling
/speckit.plan --threat-model

# Architecture validation
/speckit.plan --arch-validation
```

#### `/speckit.tasks`
```bash
# Generate task breakdown
/speckit.tasks

# Export as DAG
/speckit.tasks --export-dag

# With knowledge guidance
/speckit.tasks --knowledge-guidance

# Include time estimates
/speckit.tasks --time-estimates
```

#### `/speckit.checklist`
```bash
# Generate quality checklist
/speckit.checklist

# Bundle specific checklists
/speckit.checklist --bundle security,perf,ux

# Custom checklist items
/speckit.checklist --custom items.txt
```

#### `/speckit.analyze`
```bash
# Analyze project state
/speckit.analyze

# Write detailed report
/speckit.analyze --write-report

# Knowledge benchmarking
/speckit.analyze --knowledge-benchmark

# Include metrics
/speckit.analyze --metrics
```

#### `/speckit.execute`
```bash
# Basic execution
/speckit.execute --feature-dir ./feature

# With specific engine
/speckit.execute --engine dev6 --feature-dir ./feature

# Orchestrated mode
/speckit.execute --mode orchestrated --feature-dir ./feature

# Custom trust thresholds
/speckit.execute --trust-threshold 0.8 --feature-dir ./feature

# Enable specialist coordination
/speckit.execute --enable-specialist-coordination --feature-dir ./feature
```

#### `/speckit.flow`
```bash
# Run complete flow
/speckit.flow

# Start at specific phase
/speckit.flow --start-at research

# Skip validation (development mode)
/speckit.flow --skip-validation

# Continuous mode
/speckit.flow --continuous
```

### Advanced Commands

#### `/speckit.implement`
```bash
# Implementation-focused execution
/speckit.implement --task TSK-001

# Batch implementation
/speckit.implement --batch tasks.txt

# With validation
/speckit.implement --validate --task TSK-001
```

#### `/speckit.flow` (Complete Pipeline)
```bash
# Run complete speckit pipeline
/speckit.flow

# With custom configuration
/speckit.flow --config custom.json

# Evidence-based flow
/speckit.flow --evidence-first
```

#### `/speckit.execute` (Enhanced)
```bash
# Dev6 engine execution
/speckit.execute --engine dev6 --feature-dir ./feature

# With trust validation
/speckit.execute --trust-threshold 0.8 --feature-dir ./feature

# Knowledge-guided execution
/speckit.execute --knowledge-guidance --feature-dir ./feature
```

## Task Management System

### TSK-### Format

Tasks are automatically numbered in the format `TSK-XXX` where XXX is a zero-padded three-digit number.

**Example**: `TSK-001`, `TSK-002`, `TSK-003`

### Task Structure

Each task has the following structure:

```json
{
  "task_id": "TSK-001",
  "title": "User authentication implementation",
  "status": "active",
  "priority": "high",
  "created_date": "2025-01-25T10:00:00Z",
  "updated_date": "2025-01-25T15:30:00Z",
  "description": "Implement OAuth2 authentication system",
  "requirements": ["security", "scalability", "performance"],
  "dependencies": [],
  "estimated_hours": 16,
  "actual_hours": 12,
  "assignee": "developer-name",
  "evidence_files": [
    "evidence/security_analysis.md",
    "evidence/implementation_plan.md"
  ],
  "checklist": {
    "completed": 8,
    "total": 12
  },
  "trust_score": 0.85
}
```

### Task Operations

#### Creating Tasks
```powershell
# Create new task
.\.speckit\scripts\powershell\manage-tasks.ps1 -Action Create -Title "New feature" -Priority high

# Create from specification
.\.speckit\scripts\powershell\manage-tasks.ps1 -Action CreateFromSpec -SpecPath spec.md
```

#### Managing Tasks
```powershell
# Update task status
.\.speckit\scripts\powershell\manage-tasks.ps1 -Action Update -TaskId TSK-001 -Status completed

# List active tasks
.\.speckit\scripts\powershell\manage-tasks.ps1 -Action List -Status active

# Archive completed tasks
.\.speckit\scripts\powershell\manage-tasks.ps1 -Action Archive -OlderThan 30days
```

#### Task Integration with Commands

Many speckit commands automatically create or update tasks:

```bash
# Creates implementation tasks
/speckit.tasks --export-dag

# Updates task status during execution
/speckit.execute --task TSK-001

# Links evidence to tasks
/speckit.analyze --link-evidence --task TSK-001
```

## Workflow Integration

### Dev6 Integration

Speckit seamlessly integrates with the Dev6 development framework.

**Key Integration Points**:
- Knowledge-first development enforcement
- Trust validation scoring
- Specialist agent coordination
- Evidence-based validation

### Evidence Collection

All speckit commands generate evidence that is stored and linked:

```
feature/.taskmaster/evidence/
├── constitution_validation.json
├── requirements_analysis.json
├── research_synthesis.json
├── architecture_validation.json
├── implementation_tasks.json
├── quality_checklist.json
└── project_analysis.json
```

### Knowledge System Integration

Speckit integrates with the CSF NIP knowledge system:

```bash
# Search knowledge base before specification
cd "C:\_Python\_Projects\__csf.nip" && python scripts/knowledge_interface.py search --keywords "authentication patterns"

# Use knowledge-guided planning
/speckit.plan --knowledge-guidance

# Contribute lessons learned
cd "C:\_Python\_Projects\__csf.nip" && python scripts/knowledge_interface.py add --type lessons_learned
```

## Configuration Management

### Speckit Configuration

**File**: `.speckit/config/speckit_config.json`

**Key Settings**:
```json
{
  "task_management": {
    "global_counter": {
      "current_id": 6,
      "format": "TSK-%03d"
    },
    "workflow": {
      "auto_increment": true,
      "preserve_completed": true
    }
  },
  "speckit_framework": {
    "version": "2.0.0",
    "enhanced_templates": true,
    "task_management_enabled": true
  },
  "paths": {
    "templates": "templates/",
    "memory": "memory/",
    "scripts": "scripts/",
    "config": "config/",
    "docs": "docs/",
    "cache": "cache/"
  }
}
```

### Project Configuration

**File**: `.speckit/project-config.json`

**Purpose**: Project-specific settings and preferences.

**Example**:
```json
{
  "project_name": "MyApplication",
  "project_type": "web-application",
  "standards": {
    "security_level": "high",
    "performance_targets": {
      "response_time": "200ms",
      "throughput": "1000rps"
    }
  },
  "preferences": {
    "default_engine": "dev6",
    "trust_threshold": 0.75,
    "auto_save_evidence": true
  }
}
```

## Best Practices

### 1. Knowledge-First Development

**Always consult the knowledge system before making decisions**:

```bash
# Before specification
cd "C:\_Python\_Projects\__csf.nip" && python scripts/knowledge_interface.py search --keywords "your topic"

# Before planning
cd "C:\_Python\_Projects\__csf.nip" && python scripts/knowledge_interface.py search --type architecture

# Before implementation
cd "C:\_Python\_Projects\__csf.nip" && python scripts/knowledge_interface.py search --type implementation
```

### 2. Evidence-Based Workflow

**Generate and link evidence at every stage**:

```bash
# Each command generates evidence
/speckit.specify "Feature" --evidence-first
/speckit.research --document-sources
/speckit.plan --validation-evidence
/speckit.execute --save-evidence
```

### 3. Quality Gates

**Never skip validation gates**:

```bash
# Always validate constitution
/speckit.constitution --validate

# Use checklists for quality
/speckit.checklist --bundle security,perf,ux

# Analyze before completion
/speckit.analyze --write-report
```

### 4. Task Management

**Keep tasks focused and trackable**:

```bash
# Generate specific tasks
/speckit.tasks --time-estimates

# Update status regularly
./scripts/manage-tasks.ps1 -Update -TaskId TSK-001 -Status in_progress

# Link evidence to tasks
/speckit.analyze --link-evidence --task TSK-001
```

### 5. Continuous Integration

**Use speckit in CI/CD pipelines**:

```yaml
# Example GitHub Actions
- name: Speckit Validation
  run: |
    /speckit.constitution --validate
    /speckit.analyze --metrics --exit-on-failure
```

## Troubleshooting

### Common Issues

#### 1. Constitution Validation Fails
**Problem**: Constitution validation fails with errors

**Solution**:
```bash
# Check specific standards
/speckit.constitution --check specific-standard

# Update constitution to match project
/speckit.constitution --update

# Review validation report
cat .speckit/evidence/constitution_validation.json
```

#### 2. Task ID Conflicts
**Problem**: Duplicate task IDs or numbering issues

**Solution**:
```powershell
# Reset task counter
.\.speckit\scripts\powershell\manage-tasks.ps1 -Action ResetCounter

# Validate task storage
.\.speckit\scripts\powershell\manage-tasks.ps1 -Action Validate

# Backup and restore
.\.speckit\scripts\powershell\manage-tasks.ps1 -Action Backup
```

#### 3. Knowledge System Integration Fails
**Problem**: Knowledge system queries fail

**Solution**:
```bash
# Check knowledge system health
cd "C:\_Python\_Projects\__csf.nip" && python scripts/knowledge_interface.py status

# Rebuild knowledge index
cd "C:\_Python\_Projects\__csf.nip" && python scripts/knowledge_interface.py rebuild

# Fallback to offline mode
/speckit.plan --offline-mode
```

#### 4. Evidence Files Not Generated
**Problem**: Commands don't generate expected evidence files

**Solution**:
```bash
# Check evidence directory permissions
ls -la .speckit/evidence/

# Enable evidence generation
/speckit.execute --save-evidence --verbose

# Manually create evidence structure
mkdir -p .speckit/evidence/working
```

### Debug Mode

Enable debug mode for troubleshooting:

```bash
# Run with debug output
/speckit.execute --debug --feature-dir ./feature

# Verbose evidence generation
/speckit.analyze --verbose --write-report

# Check system health
/speckit.flow --health-check
```

### Getting Help

**Resources**:
- Documentation: `.speckit/docs/`
- Integration Guide: `docs/SPECKIT_V6_INTEGRATION_GUIDE.md`
- Knowledge Base: CSF NIP knowledge system
- Issue Tracking: Project-specific task management

**Commands for Help**:
```bash
# Get command help
/speckit.command --help

# Check system status
/speckit.flow --status

# Validate setup
/speckit.constitution --validate --verbose
```

## Advanced Features

### 1. Custom Templates

Create project-specific templates:

```markdown
<!-- .speckit/templates/custom-api-feature.md -->
# Feature Specification: {{FEATURE_NAME}}

## Overview
{{DESCRIPTION}}

## API Endpoints
{{API_ENDPOINTS}}

## Security Requirements
{{SECURITY_REQUIREMENTS}}

## Performance Targets
{{PERFORMANCE_TARGETS}}
```

**Usage**:
```bash
/speckit.specify "New API feature" --template custom-api-feature
```

### 2. Automated Workflows

Create automated speckit workflows:

```powershell
# .speckit/scripts/workflows/security-review.ps1
param($FeatureDir)

# Run security-focused speckit workflow
/speckit.research --spike "security patterns"
/speckit.plan --threat-model
/speckit.checklist --bundle security
/speckit.execute --feature-dir $FeatureDir --enable-security-validation
```

### 3. Integration with External Tools

**IDE Integration**:
```json
// VS Code tasks.json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Speckit Validate",
      "type": "shell",
      "command": "/speckit.constitution",
      "args": ["--validate"]
    }
  ]
}
```

**Git Hooks**:
```bash
#!/bin/sh
# .git/hooks/pre-commit
/speckit.analyze --quick-check
if [ $? -ne 0 ]; then
  echo "Speckit validation failed"
  exit 1
fi
```

### 4. Custom Validators

Create custom validation logic:

```python
# .speckit/scripts/validators/custom_validator.py
def validate_custom_standards(feature_dir):
    """Custom validation logic"""
    # Implementation here
    return {"valid": True, "issues": []}
```

### 5. Metrics and Reporting

Generate detailed reports:

```bash
# Comprehensive project report
/speckit.analyze --write-report --metrics --include-evidence

# Task completion metrics
.\.speckit\scripts\powershell\manage-tasks.ps1 -Action Report

# Quality metrics dashboard
/speckit.flow --metrics-dashboard
```

## Conclusion

Speckit provides a comprehensive, evidence-based development framework that ensures high-quality, maintainable software development. By following the structured workflows and leveraging the integrated tools, teams can:

- **Improve Quality**: Built-in validation and trust scoring
- **Increase Efficiency**: Automated workflows and task management
- **Ensure Compliance**: Standards enforcement and evidence collection
- **Enable Knowledge Sharing**: Integration with knowledge systems
- **Support Scalability**: Works for projects of all sizes

The framework is designed to be flexible and extensible, allowing customization while maintaining the core principles of evidence-based development and quality assurance.

For additional information:
- See the integration guide for advanced setup
- Consult the knowledge system for best practices
- Review the evidence files for project insights
- Use the troubleshooting guide for common issues
