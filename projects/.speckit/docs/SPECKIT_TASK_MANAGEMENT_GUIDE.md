# Speckit Task Management System Guide

## Overview

The Speckit Task Management System provides a structured approach to tracking, managing, and executing development tasks using the TSK-### format. This system integrates seamlessly with the Speckit workflow and evidence-based development approach.

## Table of Contents

1. [Task Format and Structure](#task-format-and-structure)
2. [Task Lifecycle Management](#task-lifecycle-management)
3. [Task Creation Methods](#task-creation-methods)
4. [Task Operations](#task-operations)
5. [Evidence Integration](#evidence-integration)
6. [Automation Scripts](#automation-scripts)
7. [Best Practices](#best-practices)
8. [Advanced Features](#advanced-features)
9. [Troubleshooting](#troubleshooting)

## Task Format and Structure

### TSK-### Format

All tasks follow the format `TSK-XXX` where:
- `TSK`: Fixed prefix indicating a Speckit task
- `XXX`: Zero-padded three-digit sequential number (001-999)

**Examples**: `TSK-001`, `TSK-045`, `TSK-999`

### Task Schema

Each task is represented as a JSON object with the following structure:

```json
{
  "task_id": "TSK-001",
  "title": "User authentication system implementation",
  "description": "Implement OAuth2 authentication with secure password handling",
  "status": "active",
  "priority": "high",
  "category": "implementation",
  "created_date": "2025-01-25T10:00:00Z",
  "updated_date": "2025-01-25T15:30:00Z",
  "created_by": "developer-name",
  "assigned_to": "developer-name",
  "estimated_hours": 16,
  "actual_hours": 0,
  "progress_percentage": 0,
  "dependencies": ["TSK-000"],
  "blocking_tasks": [],
  "tags": ["security", "oauth2", "authentication"],
  "requirements": {
    "functional": ["User login", "Password reset", "Session management"],
    "non_functional": ["Security", "Performance", "Scalability"]
  },
  "acceptance_criteria": [
    "Users can authenticate using OAuth2",
    "Password security meets OWASP standards",
    "Session management is secure and efficient"
  ],
  "evidence_files": [
    "evidence/security_analysis.md",
    "evidence/implementation_plan.md",
    "evidence/test_results.md"
  ],
  "checklist": {
    "total_items": 12,
    "completed_items": 3,
    "items": [
      {
        "id": 1,
        "description": "Design OAuth2 flow",
        "status": "completed",
        "completed_date": "2025-01-25T11:00:00Z"
      },
      {
        "id": 2,
        "description": "Implement authentication service",
        "status": "in_progress",
        "completed_date": null
      }
    ]
  },
  "trust_score": 0.85,
  "quality_metrics": {
    "test_coverage": 0,
    "security_score": 0,
    "performance_score": 0
  },
  "metadata": {
    "feature_id": "user-auth",
    "epic_id": "security-module",
    "sprint_id": "sprint-12",
    "complexity": "medium",
    "risk_level": "low"
  }
}
```

### Task Status Values

Tasks can have the following status values:

| Status | Description | Typical Duration |
|--------|-------------|------------------|
| `planned` | Task is planned but not started | N/A |
| `active` | Task is currently being worked on | 1-7 days |
| `blocked` | Task is blocked by dependencies | Variable |
| `review` | Task is in review phase | 1-2 days |
| `completed` | Task is completed and verified | N/A |
| `archived` | Task is archived for reference | N/A |

### Priority Levels

| Priority | Description | Response Time |
|----------|-------------|---------------|
| `critical` | Blocks release or major functionality | Immediate |
| `high` | Important for current sprint | Within 1 day |
| `medium` | Standard priority | Within 3 days |
| `low` | Nice to have | Within 1 week |

## Task Lifecycle Management

### Lifecycle States

```
[PLANNED] → [ACTIVE] → [REVIEW] → [COMPLETED] → [ARCHIVED]
     ↓           ↓           ↓
  [BLOCKED] ← [BLOCKED] ← [BLOCKED]
```

### State Transitions

#### PLANNED → ACTIVE
- **Trigger**: Task is assigned and dependencies are met
- **Action**: Start working on the task
- **Evidence**: Create working directory, initial analysis

#### ACTIVE → REVIEW
- **Trigger**: Implementation is complete
- **Action**: Submit for code review and validation
- **Evidence**: Test results, implementation documentation

#### REVIEW → COMPLETED
- **Trigger**: Review passes and validation succeeds
- **Action**: Mark as completed, update metrics
- **Evidence**: Review feedback, validation reports

#### ACTIVE/BLOCKED → BLOCKED
- **Trigger**: Dependencies or issues block progress
- **Action**: Document blocking issues, notify stakeholders
- **Evidence**: Blocker documentation, impact analysis

#### BLOCKED → ACTIVE
- **Trigger**: Blockers are resolved
- **Action**: Resume work on task
- **Evidence**: Blocker resolution documentation

### Automatic Transitions

The system supports automatic transitions based on:

```json
{
  "automation": {
    "auto_complete_on_validation": true,
    "auto_block_on_dependency": true,
    "auto_assign_on_creation": false,
    "auto_archive_completion_days": 30
  }
}
```

## Task Creation Methods

### 1. Manual Task Creation

#### Using PowerShell Script
```powershell
# Create a new task manually
.\.speckit\scripts\powershell\manage-tasks.ps1 `
  -Action Create `
  -Title "Implement user authentication" `
  -Description "OAuth2 authentication system" `
  -Priority high `
  -Category implementation `
  -AssignedTo "developer-name" `
  -EstimatedHours 16 `
  -Tags "security,oauth2"
```

#### Using Bash Script
```bash
# Create a new task
./.speckit/scripts/bash/manage-tasks.sh \
  --action create \
  --title "API endpoint implementation" \
  --priority medium \
  --category implementation \
  --estimate 8
```

### 2. Specification-Based Task Creation

Create tasks from a feature specification:

```bash
# Generate tasks from specification
/speckit.specify "User authentication system" --auto-tasks

# Plan with task generation
/speckit.plan --generate-tasks --include-estimates

# Create task breakdown
/speckit.tasks --export-dag --auto-create
```

### 3. Template-Based Task Creation

Using predefined task templates:

```powershell
# Create from security task template
.\.speckit\scripts\powershell\manage-tasks.ps1 `
  -Action CreateFromTemplate `
  -Template security-audit `
  -Title "Security audit for auth module"

# Create from performance task template
.\.speckit\scripts\powershell\manage-tasks.ps1 `
  -Action CreateFromTemplate `
  -Template performance-optimization `
  -Title "Optimize database queries"
```

### 4. Bulk Task Creation

Create multiple tasks from a CSV or JSON file:

```powershell
# Create from CSV
.\.speckit\scripts\powershell\manage-tasks.ps1 `
  -Action BulkCreate `
  -SourceFile tasks.csv `
  -Format csv

# Create from JSON
.\.speckit\scripts\powershell\manage-tasks.ps1 `
  -Action BulkCreate `
  -SourceFile tasks.json `
  -Format json
```

**CSV Format**:
```csv
title,description,priority,category,estimate,tags
"User login","Implement login page",high,implementation,8,"frontend,auth"
"Password reset","Reset password functionality",medium,implementation,4,"auth,security"
```

**JSON Format**:
```json
[
  {
    "title": "User login",
    "description": "Implement login page",
    "priority": "high",
    "category": "implementation",
    "estimated_hours": 8,
    "tags": ["frontend", "auth"]
  }
]
```

## Task Operations

### 1. Viewing Tasks

#### List Active Tasks
```powershell
# List all active tasks
.\.speckit\scripts\powershell\manage-tasks.ps1 -Action List -Status active

# List tasks by priority
.\.speckit\scripts\powershell\manage-tasks.ps1 -Action List -Priority high,medium

# List tasks by assignee
.\.speckit\scripts\powershell\manage-tasks.ps1 -Action List -AssignedTo "developer-name"
```

#### Task Details
```powershell
# Get detailed task information
.\.speckit\scripts\powershell\manage-tasks.ps1 `
  -Action Details `
  -TaskId TSK-001

# Get task with evidence
.\.speckit\scripts\powershell\manage-tasks.ps1 `
  -Action Details `
  -TaskId TSK-001 `
  -IncludeEvidence
```

### 2. Updating Tasks

#### Status Updates
```powershell
# Update task status
.\.speckit\scripts\powershell\manage-tasks.ps1 `
  -Action Update `
  -TaskId TSK-001 `
  -Status in_progress

# Update progress
.\.speckit\scripts\powershell\manage-tasks.ps1 `
  -Action Update `
  -TaskId TSK-001 `
  -Progress 50

# Update actual hours
.\.speckit\scripts\powershell\manage-tasks.ps1 `
  -Action Update `
  -TaskId TSK-001 `
  -ActualHours 12
```

#### Content Updates
```powershell
# Update description
.\.speckit\scripts\powershell\manage-tasks.ps1 `
  -Action Update `
  -TaskId TSK-001 `
  -Description "Updated description"

# Add tags
.\.speckit\scripts\powershell\manage-tasks.ps1 `
  -Action Update `
  -TaskId TSK-001 `
  -AddTags "urgent,security"

# Update assignee
.\.speckit\scripts\powershell\manage-tasks.ps1 `
  -Action Update `
  -TaskId TSK-001 `
  -AssignedTo "new-developer"
```

### 3. Checklist Management

#### Update Checklist Items
```powershell
# Complete checklist item
.\.speckit\scripts\powershell\manage-tasks.ps1 `
  -Action UpdateChecklist `
  -TaskId TSK-001 `
  -ItemId 1 `
  -Status completed

# Add new checklist item
.\.speckit\scripts\powershell\manage-tasks.ps1 `
  -Action UpdateChecklist `
  -TaskId TSK-001 `
  -AddItem "New requirement" `
  -Status pending
```

#### Auto-Calculate Progress
```powershell
# Recalculate progress from checklist
.\.speckit\scripts\powershell\manage-tasks.ps1 `
  -Action CalculateProgress `
  -TaskId TSK-001
```

### 4. Dependencies Management

#### Add Dependencies
```powershell
# Add task dependency
.\.speckit\scripts\powershell\manage-tasks.ps1 `
  -Action AddDependency `
  -TaskId TSK-002 `
  -DependsOn TSK-001

# Remove dependency
.\.speckit\scripts\powershell\manage-tasks.ps1 `
  -Action RemoveDependency `
  -TaskId TSK-002 `
  -DependsOn TSK-001
```

#### Check Dependency Status
```powershell
# Check if task can be started
.\.speckit\scripts\powershell\manage-tasks.ps1 `
  -Action CheckDependencies `
  -TaskId TSK-002

# List blocking tasks
.\.speckit\scripts\powershell\manage-tasks.ps1 `
  -Action ListBlocking `
  -TaskId TSK-002
```

### 5. Evidence Management

#### Link Evidence Files
```powershell
# Add evidence file
.\.speckit\scripts\powershell\manage-tasks.ps1 `
  -Action AddEvidence `
  -TaskId TSK-001 `
  -EvidenceFile "evidence/test_results.md"

# Remove evidence file
.\.speckit\scripts\powershell\manage-tasks.ps1 `
  -Action RemoveEvidence `
  -TaskId TSK-001 `
  -EvidenceFile "evidence/old_analysis.md"
```

#### Generate Evidence Summary
```powershell
# Generate evidence summary for task
.\.speckit\scripts\powershell\manage-tasks.ps1 `
  -Action GenerateEvidenceSummary `
  -TaskId TSK-001 `
  -OutputFile "evidence/TSK-001_summary.md"
```

## Evidence Integration

### Automatic Evidence Collection

Speckit automatically generates and links evidence during task execution:

```bash
# During implementation
/speckit.execute --feature-dir ./auth --task TSK-001
# Generates: evidence/TSK-001_implementation.json

# During analysis
/speckit.analyze --task TSK-001 --write-report
# Generates: evidence/TSK-001_analysis.json

# During validation
/speckit.checklist --task TSK-001 --bundle security
# Generates: evidence/TSK-001_validation.json
```

### Evidence File Types

#### Implementation Evidence
```json
{
  "evidence_type": "implementation",
  "task_id": "TSK-001",
  "timestamp": "2025-01-25T15:30:00Z",
  "implementation_details": {
    "files_modified": ["auth_service.py", "auth_routes.py"],
    "lines_added": 245,
    "lines_removed": 12,
    "test_files_created": ["test_auth.py"],
    "test_coverage": 0.85
  },
  "quality_metrics": {
    "complexity": "medium",
    "maintainability": 0.78,
    "security_score": 0.92
  }
}
```

#### Validation Evidence
```json
{
  "evidence_type": "validation",
  "task_id": "TSK-001",
  "timestamp": "2025-01-25T16:00:00Z",
  "validation_results": {
    "security_check": {
      "status": "passed",
      "issues_found": 0,
      "critical_issues": 0
    },
    "performance_check": {
      "status": "passed",
      "response_time_ms": 150,
      "throughput_rps": 1000
    },
    "code_review": {
      "status": "approved",
      "reviewer": "senior-developer",
      "comments": 3
    }
  },
  "overall_trust_score": 0.88
}
```

### Evidence-Based Task Completion

Tasks can be automatically completed when evidence thresholds are met:

```json
{
  "completion_criteria": {
    "min_test_coverage": 0.80,
    "min_security_score": 0.85,
    "max_critical_issues": 0,
    "required_checklist_completion": 1.0,
    "min_trust_score": 0.75
  },
  "auto_completion": {
    "enabled": true,
    "validate_evidence": true,
    "require_approval": false
  }
}
```

## Automation Scripts

### PowerShell Scripts

#### Task Management Script
```powershell
# .speckit/scripts/powershell/manage-tasks.ps1
param(
  [Parameter(Mandatory=$true)]
  [string]$Action,

  [string]$TaskId,
  [string]$Title,
  [string]$Description,
  [string]$Priority = "medium",
  [string]$Category = "implementation",
  [int]$EstimatedHours = 0,
  [string]$AssignedTo,
  [string[]]$Tags,
  [string]$Status,
  [int]$Progress,
  [string]$SourceFile,
  [string]$Format,
  [string]$Template
)

function Get-NextTaskId {
  $config = Get-Content ".speckit/config/speckit_config.json" | ConvertFrom-Json
  $currentId = $config.task_management.global_counter.current_id
  $nextId = $currentId + 1

  # Update config
  $config.task_management.global_counter.current_id = $nextId
  $config | ConvertTo-Json -Depth 10 | Set-Content ".speckit/config/speckit_config.json"

  return "TSK-{0:D3}" -f $nextId
}

function New-TaskObject {
  param($TaskId, $Title, $Description, $Priority, $Category, $EstimatedHours, $AssignedTo, $Tags)

  return @{
    task_id = $TaskId
    title = $Title
    description = $Description
    status = "planned"
    priority = $Priority
    category = $Category
    created_date = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssZ")
    updated_date = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssZ")
    assigned_to = $AssignedTo
    estimated_hours = $EstimatedHours
    actual_hours = 0
    progress_percentage = 0
    dependencies = @()
    tags = @($Tags)
    evidence_files = @()
    checklist = @{
      total_items = 0
      completed_items = 0
      items = @()
    }
    trust_score = 0.0
  }
}

# Main execution logic
switch ($Action) {
  "Create" {
    $taskId = Get-NextTaskId
    $task = New-TaskObject -TaskId $taskId -Title $Title -Description $Description -Priority $Priority -Category $Category -EstimatedHours $EstimatedHours -AssignedTo $AssignedTo -Tags $Tags

    # Add to active tasks
    $activeTasks = @()
    if (Test-Path ".speckit/cache/active_tasks.json") {
      $activeTasks = Get-Content ".speckit/cache/active_tasks.json" | ConvertFrom-Json
    }
    $activeTasks += $task
    $activeTasks | ConvertTo-Json -Depth 10 | Set-Content ".speckit/cache/active_tasks.json"

    Write-Host "Task created: $taskId"
  }

  "List" {
    if (Test-Path ".speckit/cache/active_tasks.json") {
      $tasks = Get-Content ".speckit/cache/active_tasks.json" | ConvertFrom-Json
      $tasks | Format-Table task_id, title, status, priority, assigned_to, progress_percentage
    } else {
      Write-Host "No active tasks found."
    }
  }

  # Additional action implementations...
}
```

#### Task ID Generation Script
```powershell
# .speckit/scripts/powershell/generate-task-id.ps1
function New-TaskId {
  $config = Get-Content ".speckit/config/speckit_config.json" | ConvertFrom-Json
  $currentId = $config.task_management.global_counter.current_id
  $nextId = $currentId + 1

  # Update counter
  $config.task_management.global_counter.current_id = $nextId
  $config | ConvertTo-Json -Depth 10 | Set-Content ".speckit/config/speckit_config.json"

  return "TSK-{0:D3}" -f $nextId
}

$taskId = New-TaskId
Write-Output $taskId
```

### Bash Scripts

#### Task Management Script
```bash
#!/bin/bash
# .speckit/scripts/bash/manage-tasks.sh

ACTION=""
TASK_ID=""
TITLE=""
DESCRIPTION=""
PRIORITY="medium"
CATEGORY="implementation"
ESTIMATE=0

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --action)
      ACTION="$2"
      shift 2
      ;;
    --task-id)
      TASK_ID="$2"
      shift 2
      ;;
    --title)
      TITLE="$2"
      shift 2
      ;;
    --description)
      DESCRIPTION="$2"
      shift 2
      ;;
    --priority)
      PRIORITY="$2"
      shift 2
      ;;
    --category)
      CATEGORY="$2"
      shift 2
      ;;
    --estimate)
      ESTIMATE="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

get_next_task_id() {
  local config_file=".speckit/config/speckit_config.json"
  local current_id=$(jq -r '.task_management.global_counter.current_id' "$config_file")
  local next_id=$((current_id + 1))

  # Update config
  jq ".task_management.global_counter.current_id = $next_id" "$config_file" > "${config_file}.tmp" && mv "${config_file}.tmp" "$config_file"

  printf "TSK-%03d" $next_id
}

create_task() {
  local task_id=$(get_next_task_id)
  local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

  local task=$(cat <<EOF
{
  "task_id": "$task_id",
  "title": "$TITLE",
  "description": "$DESCRIPTION",
  "status": "planned",
  "priority": "$PRIORITY",
  "category": "$CATEGORY",
  "created_date": "$timestamp",
  "updated_date": "$timestamp",
  "estimated_hours": $ESTIMATE,
  "actual_hours": 0,
  "progress_percentage": 0,
  "dependencies": [],
  "evidence_files": [],
  "tags": [],
  "checklist": {
    "total_items": 0,
    "completed_items": 0,
    "items": []
  },
  "trust_score": 0.0
}
EOF
  )

  # Add to active tasks
  local active_tasks_file=".speckit/cache/active_tasks.json"
  if [[ -f "$active_tasks_file" ]]; then
    jq ". += [$task]" "$active_tasks_file" > "${active_tasks_file}.tmp" && mv "${active_tasks_file}.tmp" "$active_tasks_file"
  else
    echo "[$task]" > "$active_tasks_file"
  fi

  echo "Task created: $task_id"
}

list_tasks() {
  local active_tasks_file=".speckit/cache/active_tasks.json"
  if [[ -f "$active_tasks_file" ]]; then
    echo "Active Tasks:"
    jq -r '.[] | "\(.task_id)\t\(.title)\t\(.status)\t\(.priority)\t\(.progress_percentage)%"' "$active_tasks_file" | column -t
  else
    echo "No active tasks found."
  fi
}

# Main execution
case "$ACTION" in
  create)
    create_task
    ;;
  list)
    list_tasks
    ;;
  *)
    echo "Usage: $0 --action {create|list} [options]"
    exit 1
    ;;
esac
```

## Best Practices

### 1. Task Definition

#### Clear, Specific Titles
```
Good: "Implement OAuth2 authentication with JWT tokens"
Poor: "Auth work"
```

#### Comprehensive Descriptions
```
Include:
- What needs to be done
- Why it's important
- Acceptance criteria
- Technical requirements
- Dependencies
```

#### Realistic Estimates
```
Consider:
- Complexity of implementation
- Testing requirements
- Documentation needs
- Review and validation time
- Potential blockers
```

### 2. Task Sizing

#### Ideal Task Size
- **Duration**: 1-3 days of work
- **Complexity**: Single feature or fix
- **Dependencies**: Minimal external dependencies
- **Deliverable**: Clear, testable outcome

#### Task Breakdown Guidelines
```
If a task takes more than 3 days → Break it down
If a task is less than 2 hours → Consider combining
If a task has multiple deliverables → Split into separate tasks
```

### 3. Dependency Management

#### Best Practices
```
1. Minimize dependencies between tasks
2. Document clear dependency relationships
3. Use parallel tasks when possible
4. Plan for dependency resolution time
5. Update dependencies when plans change
```

#### Dependency Types
```
Hard Dependency: Task B cannot start until Task A is complete
Soft Dependency: Task B is enhanced by Task A completion
Shared Dependency: Multiple tasks depend on the same prerequisite
```

### 4. Progress Tracking

#### Meaningful Progress Updates
```
- Update progress when significant milestones are reached
- Mark checklist items as completed
- Add actual time spent
- Update blockers and dependencies
- Link relevant evidence files
```

#### Quality Gates
```
Don't mark tasks as complete until:
- All acceptance criteria are met
- Code is reviewed and approved
- Tests pass and coverage is adequate
- Documentation is updated
- Evidence is collected and validated
```

### 5. Evidence Management

#### Evidence Types to Collect
```
Implementation:
- Code changes and diffs
- Test results and coverage
- Performance measurements
- Security scan results

Validation:
- Code review feedback
- Quality assurance results
- User acceptance testing
- Integration test results

Documentation:
- Design decisions
- Implementation notes
- Lessons learned
- Best practices identified
```

#### Evidence Organization
```
.speckit/evidence/
├── TSK-001_implementation/
│   ├── code_changes.json
│   ├── test_results.json
│   └── performance_metrics.json
├── TSK-001_validation/
│   ├── security_scan.json
│   ├── code_review.json
│   └── uat_results.json
└── TSK-001_documentation/
    ├── design_decisions.md
    └── lessons_learned.md
```

## Advanced Features

### 1. Task Templates

#### Creating Custom Templates
```json
{
  "template_id": "security-audit",
  "name": "Security Audit Task",
  "description_template": "Perform security audit for {component}",
  "default_priority": "high",
  "default_category": "security",
  "estimated_hours": 8,
  "checklist_template": [
    "Review authentication mechanisms",
    "Analyze authorization controls",
    "Check for common vulnerabilities",
    "Review data encryption practices",
    "Validate input sanitization",
    "Test for injection flaws"
  ],
  "tags_template": ["security", "audit", "{component}"],
  "acceptance_criteria_template": [
    "Security assessment completed",
    "Vulnerabilities documented",
    "Remediation recommendations provided",
    "Security score calculated"
  ]
}
```

#### Using Templates
```powershell
# Create task from template
.\.speckit\scripts\powershell\manage-tasks.ps1 `
  -Action CreateFromTemplate `
  -Template security-audit `
  -Title "Security audit for authentication module" `
  -Parameters @{
    component = "authentication"
  }
```

### 2. Automated Task Generation

#### From Feature Specifications
```bash
# Generate tasks from feature spec
/speckit.specify "User authentication system" --generate-tasks

# Output: Creates TSK-001 through TSK-005 with appropriate breakdown
```

#### From Architecture Diagrams
```bash
# Generate tasks from architecture components
/speckit.plan --architecture-diagram ./docs/architecture.png --generate-tasks
```

#### From User Stories
```bash
# Generate tasks from user stories
/speckit.tasks --user-stories ./requirements/stories.md --auto-create
```

### 3. Task Analytics

#### Generate Task Reports
```powershell
# Productivity report
.\.speckit\scripts\powershell\manage-tasks.ps1 `
  -Action Report `
  -Type productivity `
  -Period last-30-days

# Quality metrics report
.\.speckit\scripts\powershell\manage-tasks.ps1 `
  -Action Report `
  -Type quality `
  -IncludeTrustScores

# Dependency analysis
.\.speckit\scripts\powershell\manage-tasks.ps1 `
  -Action Report `
  -Type dependencies `
  -IdentifyBottlenecks
```

#### Task Performance Metrics
```json
{
  "task_metrics": {
    "average_completion_time": "2.5 days",
    "task_completion_rate": 0.85,
    "average_estimate_accuracy": 0.78,
    "dependency_block_rate": 0.15,
    "quality_score_average": 0.82
  },
  "team_productivity": {
    "tasks_completed_per_week": 4.2,
    "average_story_points": 3.5,
    "velocity_trend": "increasing",
    "cycle_time": "3.2 days"
  }
}
```

### 4. Integration with External Systems

#### JIRA Integration
```json
{
  "jira_integration": {
    "enabled": true,
    "server_url": "https://company.atlassian.net",
    "project_key": "PROJ",
    "sync_direction": "bidirectional",
    "field_mapping": {
      "task_id": "customfield_10001",
      "title": "summary",
      "description": "description",
      "status": "status",
      "priority": "priority"
    }
  }
}
```

#### GitHub Integration
```json
{
  "github_integration": {
    "enabled": true,
    "repository": "owner/repo",
    "auto_create_issues": true,
    "link_pull_requests": true,
    "sync_status": true
  }
}
```

### 5. Intelligent Task Recommendations

#### AI-Powered Task Suggestions
```powershell
# Get task recommendations based on current work
.\.speckit\scripts\powershell\manage-tasks.ps1 `
  -Action GetRecommendations `
  -BasedOn TSK-001 `
  -Context security,performance

# Suggest related tasks
.\.speckit\scripts\powershell\manage-tasks.ps1 `
  -Action SuggestRelated `
  -TaskId TSK-001 `
  -MaxSuggestions 5
```

#### Predictive Task Estimation
```json
{
  "estimation_model": {
    "enabled": true,
    "factors": [
      "historical_completion_times",
      "task_complexity",
      "developer_experience",
      "dependency_complexity",
      "similar_task_patterns"
    ],
    "confidence_threshold": 0.75
  }
}
```

## Troubleshooting

### Common Issues

#### 1. Task ID Conflicts
**Problem**: Duplicate task IDs or counter issues

**Symptoms**:
- Multiple tasks with same ID
- Counter not incrementing
- Task creation failures

**Solutions**:
```powershell
# Validate task ID uniqueness
.\.speckit\scripts\powershell\manage-tasks.ps1 -Action ValidateTaskIds

# Reset task counter (use with caution)
.\.speckit\scripts\powershell\manage-tasks.ps1 -Action ResetCounter -NewId 100

# Merge duplicate tasks
.\.speckit\scripts\powershell\manage-tasks.ps1 -Action MergeTasks -TaskId TSK-001 -Duplicate TSK-001
```

#### 2. Dependency Cycles
**Problem**: Circular dependencies between tasks

**Symptoms**:
- Tasks stuck in "blocked" status
- Dependency resolution failures
- Workflow interruptions

**Solutions**:
```powershell
# Detect dependency cycles
.\.speckit\scripts\powershell\manage-tasks.ps1 -Action DetectCycles

# Break dependency cycle
.\.speckit\scripts\powershell\manage-tasks.ps1 -Action BreakCycle -TaskId TSK-003

# Visualize dependency graph
.\.speckit\scripts\powershell\manage-tasks.ps1 -Action VisualizeDependencies -OutputFile deps.png
```

#### 3. Evidence File Issues
**Problem**: Missing or corrupted evidence files

**Symptoms**:
- Broken evidence links
- Missing validation results
- Incomplete task history

**Solutions**:
```powershell
# Validate evidence files
.\.speckit\scripts\powershell\manage-tasks.ps1 -Action ValidateEvidence -TaskId TSK-001

# Regenerate missing evidence
.\.speckit\scripts\powershell\manage-tasks.ps1 -Action RegenerateEvidence -TaskId TSK-001

# Repair broken links
.\.speckit\scripts\powershell\manage-tasks.ps1 -Action RepairEvidenceLinks
```

#### 4. Performance Issues
**Problem**: Slow task operations or large file sizes

**Symptoms**:
- Slow task loading
- Large cache files
- Memory issues

**Solutions**:
```powershell
# Optimize task storage
.\.speckit\scripts\powershell\manage-tasks.ps1 -Action OptimizeStorage

# Archive old tasks
.\.speckit\scripts\powershell\manage-tasks.ps1 -Action Archive -OlderThan 90days

# Compress evidence files
.\.speckit\scripts\powershell\manage-tasks.ps1 -Action CompressEvidence -TaskId TSK-001
```

### Recovery Procedures

#### Task File Corruption Recovery
```powershell
# Restore from backup
.\.speckit\scripts\powershell\manage-tasks.ps1 -Action Restore -BackupFile backups/tasks_20250124.json

# Reconstruct from evidence
.\.speckit\scripts\powershell\manage-tasks.ps1 -Action Reconstruct -FromEvidence

# Manual task recreation
.\.speckit\scripts\powershell\manage-tasks.ps1 -Action Recreate -FromEvidence evidence/TSK-001/
```

#### Configuration Recovery
```powershell
# Reset to default configuration
.\.speckit\scripts\powershell\manage-tasks.ps1 -Action ResetConfig

# Validate configuration
.\.speckit\scripts\powershell\manage-tasks.ps1 -Action ValidateConfig

# Repair configuration
.\.speckit\scripts\powershell\manage-tasks.ps1 -Action RepairConfig
```

## Conclusion

The Speckit Task Management System provides a comprehensive, structured approach to managing development tasks with automatic evidence collection and integration with the broader Speckit workflow. By following the best practices and utilizing the automation scripts, teams can:

- **Improve Task Visibility**: Clear task status and progress tracking
- **Enhance Quality**: Evidence-based validation and completion criteria
- **Increase Efficiency**: Automated task creation and management
- **Ensure Consistency**: Standardized task formats and workflows
- **Enable Analytics**: Comprehensive task metrics and reporting

The system is designed to be flexible and extensible, supporting various task management methodologies while maintaining the core principles of evidence-based development and quality assurance.
