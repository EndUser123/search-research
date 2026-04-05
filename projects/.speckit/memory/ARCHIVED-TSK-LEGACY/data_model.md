# TSK-LEGACY Data Model Specification

## Task Object Structure

```json
{
  "id": "string",                    // Unique task identifier
  "title": "string",                 // Human-readable task title
  "description": "string",           // Detailed task description
  "status": "string",                // Task status (ACTIVE, COMPLETED, PENDING, etc.)
  "priority": "string",              // Priority level (CRITICAL, HIGH, MEDIUM, LOW)

  // Legacy system fields (from task completion tracker)
  "phase": "string|null",           // Development phase
  "task_type": "string|null",       // Task categorization
  "assigned_to": "string|null",     // Assignment information
  "estimated_duration": "integer|null",  // Estimated time in minutes
  "actual_duration": "integer|null",      // Actual time spent in minutes

  // Timestamp tracking
  "created_at": "string|null",      // Creation timestamp
  "started_at": "string|null",      // Work start timestamp
  "completed_at": "string|null",    // Completion timestamp
  "last_activity": "string|null",   // Last activity timestamp

  // Workflow metadata
  "source": "string|null",          // Source system identifier
  "workflow_feature_id": "string|null",  // Workflow association
  "parent_task_id": "string|null",  // Parent task reference
  "tags": "string|null",            // Comma-separated tags

  // Quality and verification
  "acceptance_criteria": "string|null",     // Definition of done
  "verification_status": "string|null",     // Verification state
  "completion_percentage": "number",        // Progress percentage (0-100)

  // Conversation analysis tasks specific fields
  "category": "string|null",        // Task category (documentation, code_quality, etc.)
  "metadata": "object|null",        // JSON metadata with context
  "estimated_effort": "integer|null",       // Estimated effort in minutes
  "impact_score": "number|null",    // Impact score (0.0-1.0)

  // Migration metadata
  "migration_date": "string"        // When task was migrated to TSK-LEGACY
}
```

## Task Container Structure

```json
{
  "tsk_id": "TSK-LEGACY",
  "description": "Interim canonical tasks database - consolidated from multiple sources",
  "created_date": "2025-11-29T...",
  "total_tasks": 106,
  "tasks": [Task Object Array]
}
```

## Status Values

### Primary Statuses
- **ACTIVE**: Currently being worked on
- **COMPLETED**: Successfully finished
- **PENDING**: Not yet started
- **BLOCKED**: Waiting on dependencies

### Legacy Statuses
- **UNKNOWN**: Status not specified in source system

## Priority Levels

### Standard Priority Hierarchy
1. **CRITICAL**: System-breaking issues, security vulnerabilities
2. **HIGH**: Important features, user-facing bugs
3. **MEDIUM**: Standard development tasks, improvements
4. **LOW**: Nice-to-have features, cleanup tasks

## Task Categories

### Development Categories
- **feature**: New feature implementation
- **bug_fix**: Bug resolution and patches
- **infrastructure**: System setup and configuration
- **documentation**: Documentation and guides

### Conversation Analysis Categories
- **documentation**: Documentation improvements and consolidation
- **code_quality**: Code improvements and standardization
- **bug_fix**: Process and system fixes
- **research**: Analysis and investigation tasks

## Source Systems

### Primary Sources
- **task_completion_tracker**: Main workflow tracking system (91 tasks)
- **conversation_analysis**: Identified development issues (15 tasks)

### Migration Tracking
- **migration_date**: ISO timestamp when task was consolidated
- **source**: Original system identifier
- **original_id**: Maintains reference to source system

## Validation Rules

### Required Fields
- `id`: Must be unique string
- `title`: Must be non-empty string
- `status`: Must be valid status value
- `priority`: Must be valid priority value
- `migration_date`: Required for all migrated tasks

### Optional Fields
- All other fields are optional and may be null
- `completion_percentage` defaults to 0.0 if not specified

## Query Patterns

### Common Queries
```bash
# High priority active tasks
jq '.tasks[] | select(.priority == "CRITICAL" or .priority == "HIGH") | select(.status == "ACTIVE")'

# Recently created tasks
jq '.tasks[] | select(.created_at != null) | sort_by(.created_at) | reverse'

# Tasks by category
jq '.tasks[] | select(.category == "code_quality")'

# Conversation analysis tasks
jq '.tasks[] | select(.source == "conversation_analysis")'
```

## Index Structure

Tasks are indexed by:
- Primary: `id` (unique identifier)
- Secondary: `status`, `priority`, `created_at`
- Searchable: `title`, `description`, `tags`

## Access Patterns

### Read Operations
- Full task list: `tasks` array
- Single task: Filter by `id`
- Filtered views: Filter by status, priority, category

### Update Operations
- Direct modification of task objects in array
- Maintains array order for consistency
- Update `last_activity` timestamp on modifications

### Migration Operations
- Preserve original `id` from source system
- Add `migration_date` timestamp
- Maintain all source system fields for continuity