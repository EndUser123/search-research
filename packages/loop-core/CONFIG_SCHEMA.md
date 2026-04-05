# loop-core Configuration Schema

## Overview

The `.claude/loop/config.yaml` file controls the behavior of Ralph-style autonomous loops in the loop-core plugin. This configuration schema provides centralized control over exit policies, verification behavior, plan management, and logging.

## Configuration File Location

```
.claude/loop/config.yaml
```

The configuration file is located at the root of your project, in the `.claude/loop/` directory.

## Configuration Structure

### Version

```yaml
version: 1
```

- **Type**: Integer
- **Default**: `1`
- **Description**: Configuration version. Do not modify manually. Used for future migration support.

### Exit Policy

```yaml
exit_policy:
  min_completion_indicators: 2
  require_exit_signal: true
  require_all_tasks_complete: true
  require_verification_pass: true
```

The exit policy controls when the autonomous loop should exit.

#### `min_completion_indicators`

- **Type**: Integer (>= 1)
- **Default**: `2`
- **Description**: Minimum number of completion indicators before considering exit
- **Purpose**: Completion indicators are heuristic signals that work may be complete. Requiring multiple indicators reduces false positives.
- **Example**: Set to `3` for more conservative exit behavior

#### `require_exit_signal`

- **Type**: Boolean
- **Default**: `true`
- **Description**: Require explicit `EXIT_SIGNAL: true` in plan file's RALPH_STATUS section
- **Purpose**: This is the LLM's explicit assertion that all work is complete and verified. Strongly recommended to prevent premature exit.
- **Example**: Set to `false` for faster development iterations (not recommended for production)

#### `require_all_tasks_complete`

- **Type**: Boolean
- **Default**: `true`
- **Description**: Require all tasks in the plan to be marked as complete
- **Purpose**: Ensures no incomplete tasks are left behind
- **Example**: Set to `false` for partial completion scenarios

#### `require_verification_pass`

- **Type**: Boolean
- **Default**: `true`
- **Description**: Require verification pass before exit
- **Purpose**: Ensures quality before completion by running the configured verification skill
- **Example**: Set to `false` to bypass verification (not recommended)

### Verification

```yaml
verification:
  enabled: true
  skill: prd-verifier
  write_report: .claude/loop/verification-report.md
```

Verification configuration controls quality checks before loop exit.

#### `enabled`

- **Type**: Boolean
- **Default**: `true`
- **Description**: Enable or disable verification
- **Purpose**: Verification is strongly recommended for production use
- **Example**: Set to `false` for faster iteration during development

#### `skill`

- **Type**: String (non-empty)
- **Default**: `"prd-verifier"`
- **Description**: Name of the verification skill to run
- **Purpose**: This skill will be invoked before loop exit
- **Example**: Use `"custom-verifier"` for project-specific verification

#### `write_report`

- **Type**: String (non-empty)
- **Default**: `.claude/loop/verification-report.md`
- **Description**: Path to write verification report
- **Purpose**: Report will be in Markdown format for human review
- **Example**: Use `"docs/verification.md"` to store reports in documentation

### Plans

```yaml
plans:
  default_plan: plan.md
  allow_per_terminal_plan: true
```

Plan configuration controls plan file management.

#### `default_plan`

- **Type**: String (non-empty)
- **Default**: `"plan.md"`
- **Description**: Default plan file to use if none specified
- **Purpose**: Can be overridden in `/loop-code` command
- **Example**: Use `"docs/development-plan.md"` for custom location

#### `allow_per_terminal_plan`

- **Type**: Boolean
- **Default**: `true`
- **Description**: Allow each terminal to have its own plan file
- **Purpose**: When true, terminals can use `plan-{terminal_id}.md`. Useful for parallel development on different features.
- **Example**: Set to `false` to enforce single plan across all terminals

### Logging

```yaml
logging:
  decision_log: decision.log
  verifier_log: verifier.log
```

Logging configuration controls loop execution logging.

#### `decision_log`

- **Type**: String (non-empty)
- **Default**: `"decision.log"`
- **Description**: Path to decision log file
- **Purpose**: Records loop exit/continue decisions with rationale. Relative to state directory.
- **Example**: Use `"decisions/exit-log.txt"` for custom location

#### `verifier_log`

- **Type**: String (non-empty)
- **Default**: `"verifier.log"`
- **Description**: Path to verifier log file
- **Purpose**: Records verification skill execution results. Relative to state directory.
- **Example**: Use `"logs/verification.txt"` for custom location

## Usage Examples

### Basic Usage

```python
from scripts.config_schema import ConfigSchema

# Load configuration from default location
config = ConfigSchema.load_from_file(".claude/loop/config.yaml")

# Access configuration values
print(f"Version: {config.version}")
print(f"Min completion indicators: {config.exit_policy.min_completion_indicators}")
print(f"Verification enabled: {config.verification.enabled}")
```

### Get Default Configuration

```python
from scripts.config_schema import ConfigSchema

# Get default configuration
config = ConfigSchema.get_default()

# Use defaults
print(config.exit_policy.min_completion_indicators)  # 2
```

### Create Configuration Programmatically

```python
from scripts.config_schema import ConfigSchema, ExitPolicyConfig, VerificationConfig, PlansConfig, LoggingConfig

# Create custom configuration
config = ConfigSchema(
    version=1,
    exit_policy=ExitPolicyConfig(
        min_completion_indicators=3,
        require_exit_signal=True,
        require_all_tasks_complete=True,
        require_verification_pass=True,
    ),
    verification=VerificationConfig(
        enabled=True,
        skill="custom-verifier",
        write_report="docs/verification.md",
    ),
    plans=PlansConfig(
        default_plan="docs/plan.md",
        allow_per_terminal_plan=False,
    ),
    logging=LoggingConfig(
        decision_log="logs/decisions.log",
        verifier_log="logs/verifier.log",
    ),
)

# Convert to dictionary
config_dict = config.to_dict()
```

### Validate Configuration

```python
from scripts.config_schema import ConfigSchema, ConfigError

try:
    config = ConfigSchema.load_from_file("config.yaml")
    print("Configuration is valid!")
except ConfigError as e:
    print(f"Configuration error: {e}")
```

## Configuration Validation

The configuration schema performs comprehensive validation:

### Type Validation
- All fields must be of the correct type (int, bool, str)
- Type mismatches raise `ConfigError`

### Value Validation
- `version` must be >= 1
- `min_completion_indicators` must be >= 1
- String fields cannot be empty
- All required sections must be present

### Schema Validation
- All top-level sections are required
- All subsection fields are required
- Missing fields raise `ConfigError`

## Integration with loop-core

The configuration schema is used by:

1. **TerminalStateManager**: For exit policy decisions
2. **Plan Parser**: For default plan resolution
3. **Verification Skills**: For verification behavior
4. **Logging System**: For log file paths

## Migration and Versioning

Current version: `1`

Future versions will maintain backward compatibility through migration paths. Configuration files with older versions will be automatically migrated to the latest schema.

## Best Practices

1. **Keep defaults for production**: The default values are designed for safe production use
2. **Document custom values**: If you change defaults, document why in comments
3. **Use version control**: Commit your config.yaml to track changes
4. **Test configuration changes**: Validate configuration before deploying
5. **Monitor logs**: Check decision and verifier logs to understand loop behavior

## Troubleshooting

### Configuration Not Found

```
ConfigError: Config file not found: .claude/loop/config.yaml
```

**Solution**: Create the configuration file in the correct location.

### Invalid YAML

```
ConfigError: Failed to parse config file .claude/loop/config.yaml
```

**Solution**: Check YAML syntax. Use a YAML validator.

### Missing Required Fields

```
ConfigError: Missing required config sections: verification, plans
```

**Solution**: Ensure all required sections are present in your config file.

### Validation Errors

```
ConfigError: min_completion_indicators must be >= 1, got 0
```

**Solution**: Fix the invalid value in your configuration file.

## See Also

- [ARCHITECTURE.md](ARCHITECTURE.md) - Technical architecture
- [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md) - Usage examples
- [README.md](README.md) - Project overview
