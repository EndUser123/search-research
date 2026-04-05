---
name: command-enhance
description: Enhance existing commands with strategic gap analysis and MVP compliance
category: development
version: 1.0.0
status: stable
triggers:
  - /command-enhance
aliases:
  - /command-enhance

suggest:
  - /command-create
  - /analyze
  - /nse
---

# Enhance Command

Transform existing commands into modern CSF NIP workflows.

## Purpose

Enhance existing commands with strategic gap analysis and MVP compliance, transforming them into modern CSF NIP workflows.

## Project Context

### Constitution/Constraints
- **Best Long-Term Solution First** - Proper enhancement over quick patches
- **Read-Before-Write** - Analyze existing command before modification
- **Complete Solutions** - No partial enhancements or TODOs

### Technical Context
- **Dual-Layer Architecture**:
  - Layer 1: Slash Command Entry (`.claude/commands/`) - Minimal, <50 lines
  - Layer 2: Full Implementation (`__csf/src/features/commands/`) - Complete logic
- Discovery, analysis, and enhancement phases
- Optional backup before modifications

### Architecture Alignment
- Works with `/command-create`, `/analyze`, `/nse`
- Follows CSF NIP command enhancement standards

## Your Workflow

### Step 1: Discovery
```bash
python src/features/commands/cb/enhance_command.py --discover command-name
```
- Locate command files
- Identify current structure
- Check for existing implementation

### Step 2: Analysis
```bash
python src/features/commands/cb/enhance_command.py --analyze command-name
```
- Perform gap analysis
- Check MVP compliance
- Identify constitutional violations

### Step 3: Enhancement
```bash
python src/features/commands/cb/enhance_command.py command-name --mode superset --backup
```
- Create backup if requested
- Apply enhancements in superset mode
- Validate against CSF NIP standards

## Validation Rules

### Prohibited Actions

- Do NOT enhance without reading existing command first
- Do NOT modify without creating backup (unless user explicitly opts out)
- Do NOT skip analysis phase
- Do NOT leave partial implementations

## Quick Start

```bash
/command-enhance my-command                    # Standard enhancement
/command-enhance my-command --analyze-only     # Analysis only
/command-enhance my-command --backup           # With backup
```

## Workflow

### Step 1: Discovery
```bash
python src/features/commands/cb/enhance_command.py --discover command-name
```

### Step 2: Analysis
```bash
python src/features/commands/cb/enhance_command.py --analyze command-name
```

### Step 3: Enhancement
```bash
python src/features/commands/cb/enhance_command.py command-name --mode superset --backup
```

## Dual-Layer Architecture

**Layer 1: Slash Command Entry** (`.claude/commands/`)
- Minimal entry point
- Target: <50 lines

**Layer 2: Full Implementation** (`__csf/src/features/commands/`)
- Complete operational logic
- Constitutional compliance
