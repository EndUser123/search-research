---
name: quadlet
description: Atomic quadlet operations with rollback for CSF NIP
version: 1.0.0
status: stable
category: orchestration
triggers:
  - /quadlet
aliases:
  - /quadlet

suggest:
  - /cwo
  - /workflow
  - /nse
---

# Quadlet Management

Atomic quadlet operations with rollback for CSF NIP.

## Purpose

Atomic quadlet operations with rollback capabilities for CSF NIP task management and orchestration.

## Project Context

### Constitution/Constraints
- Atomic operations with guaranteed rollback
- Solo-developer optimized (no distributed complexity)
- Follows CSF NIP orchestration standards

### Technical Context
- Integrates with TaskMaster for automatic task creation
- Works with CWO12 safety manager for atomic operations
- UnifiedStateManager for state persistence and recovery
- Quality Gates for validation and compliance

### Architecture Alignment
- Integrates with `/cwo` for workflow orchestration
- Works alongside `/workflow` for task coordination
- Suggests `/nse` for intelligent recommendations

## Your Workflow

1. **Create**: Define quadlet with type, priority, timeout
2. **Validate**: Verify definition without executing
3. **Run**: Execute with optional input data (sync or async)
4. **Monitor**: Check execution status
5. **Cleanup**: Delete or rollback as needed

### Quadlet Types
- **Atomic**: Single operations with rollback
- **Workflow**: Multi-step orchestration
- **Conditional**: Execution based on feature flags

## Validation Rules

### Prohibited Actions
- Do not create quadlets without proper rollback handlers
- Do not use always-running daemons (must have idle timeout)
- Do not execute async operations without status tracking

### Safety Levels
- **None**: No restrictions (development only)
- **Basic**: Input validation and resource limits
- **Strict**: Full sandboxing and security checks

## Actions

### create <name>
Create a new quadlet definition.

```bash
/quadlet create "my-quadlet" --type atomic --priority high --timeout 5000
```

### list
List registered quadlets with optional filtering.

```bash
/quadlet list                    # List all
/quadlet list --type workflow    # Filter by type
/quadlet list --status running   # Filter by status
```

### show <id>
Display detailed information about a specific quadlet.

```bash
/quadlet show "my-quadlet"
```

### run <id> [data]
Execute a quadlet with optional input data.

```bash
/quadlet run "my-quadlet" '{"input": "test"}'
/quadlet run "my-quadlet" --async    # Run asynchronously
```

### status <id>
Check the status of a quadlet execution.

```bash
/quadlet status "exec-12345"
```

### delete <id>
Remove a quadlet from the registry.

```bash
/quadlet delete "my-quadlet"
```

### validate <id>
Validate a quadlet definition without executing.

```bash
/quadlet validate "my-quadlet"
```

## Examples

### Creating Different Types

**Atomic Quadlet:**
```bash
/quadlet create "file-backup" --type atomic --description "Backup files atomically" --priority critical
```

**Workflow Quadlet:**
```bash
/quadlet create "deploy-service" --type workflow --description "Deploy with validation" --priority high
```

**Conditional Quadlet:**
```bash
/quadlet create "feature-flag" --type conditional --description "Execute based on feature flag"
```

### Running Quadlets

```bash
/quadlet run "data-processor" '{"data": [1,2,3]}'
/quadlet run "long-running-task" --async
/quadlet run "backup-task" --timeout 30000 --priority critical
```

## Integration

Integrates with:
- TaskMaster: Automatic task creation and progress tracking
- CWO12: Safety manager for atomic operations
- UnifiedStateManager: State persistence and recovery
- Quality Gates: Validation and compliance checking

## Safety and Security

- **None**: No restrictions (development only)
- **Basic**: Input validation and resource limits
- **Strict**: Full sandboxing and security checks
