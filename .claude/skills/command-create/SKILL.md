---
name: command_create
description: Create CSF NIP-compliant custom commands using the MVP pattern with integrated validation
category: development
version: 1.0.0
status: stable
triggers:
  - /command-create
aliases:
  - /command-create

suggest:
  - /command-enhance
  - /standards
  - /build
---

# Command Create

Create CSF NIP-compliant custom commands using the MVP (Minimum Viable Pattern) pattern with integrated validation.

## Purpose

Create CSF NIP-compliant custom commands with MVP pattern structure, integrated validation, and auto-scaffolding.

## Project Context

### Constitution/Constraints
- **Best Long-Term Solution First** - Implement proper command structure from the start
- **Spec Compliance** - Follow CSF NIP command standards exactly
- **Complete Solutions** - Generate full structure, not TODOs

### Technical Context
- **MVP Pattern Structure**:
  ```
  .claude/commands/<name>/
  ├── command.md       # Main command documentation
  ├── validation.py    # Validation logic
  └── examples/        # Usage examples
  ```
- CSF NIP validation for constitution compliance
- Auto-scaffolding with interactive prompts

### Architecture Alignment
- Works with `/command-enhance`, `/standards`, `/build`
- Follows CSF NIP command standards

## Your Workflow

1. Parse command name (kebab-case required)
2. Generate MVP directory structure
3. Create command.md with proper frontmatter
4. Create validation.py with compliance checks
5. Create examples directory with usage samples
6. Validate generated command against CSF NIP standards
7. Report completion with command path

## Validation Rules

### Required Fields

- `name`: kebab-case command identifier
- `description`: Short summary of command purpose
- `category`: Command category (development, utility, etc.)
- `triggers`: List of trigger phrases
- `aliases`: Command alias list

### Prohibited Actions

- Do NOT create commands without proper frontmatter
- Do NOT skip validation step
- Do NOT generate TODOs - create complete structure

## Usage

```bash
/command-create <name> [--category <cat>] [--description <desc>]
```

## Parameters

| Parameter | Description | Required |
|-----------|-------------|----------|
| `name` | Command name (kebab-case) | Yes |
| `--category` | Command category | No |
| `--description` | Short description | No |

## Examples

### Basic command creation
```bash
/command-create my-feature
```

### With category and description
```bash
/command-create data-pipeline --category utilities --description "Process data pipelines"
```

## MVP Pattern Structure

Created commands follow the MVP pattern:

```
.claude/commands/<name>/
├── command.md       # Main command documentation
├── validation.py    # Validation logic
└── examples/        # Usage examples
```

## Features

- **MVP Compliance**: Follows Minimum Viable Pattern
- **CSF NIP Validation**: Integrated constitution compliance checking
- **Auto-scaffolding**: Generates complete command structure
- **Category Organization**: Groups related commands
- **Interactive Prompts**: Guides through creation process

## Validation

Created commands are validated for:
- CSF NIP constitution compliance
- MVP pattern adherence
- Naming conventions
- Required field presence
