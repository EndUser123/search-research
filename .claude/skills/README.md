# Skill System Documentation

This directory contains the definitions for all skills available to Claude. The system is designed to be self-documenting, maintainable, and verifiable.

## 1. System Overview

The skill system is built around a **Single Source of Truth**: the `SKILL.md` file located in each skill's directory.

*   **Registry (`skill_registry.py`)**: The central Python module that loads, validates, and provides access to all skill metadata. It parses the YAML frontmatter from `SKILL.md` files.
*   **UI Metadata (`skills_metadata.js`)**: Data generated for the SDLC Tech Tree UI, derived directly from the registry.

## 2. Skill Structure (`SKILL.md`)

Each skill must have a `SKILL.md` file. This file contains two parts:
1.  **YAML Frontmatter**: Machine-readable metadata and execution directives.
2.  **Markdown Body**: Human-readable documentation (Verification, User Guide, etc.).

### Frontmatter Schema

See [SKILL_SCHEMA.md](./SKILL_SCHEMA.md) for the complete definition.

```yaml
---
name: my-skill
description: Do something amazing
category: Category Name
triggers:
  - /my-skill
  - /alias
execution:
  directive: |
    Detailed instructions for Claude on how to perform the skill.
  default_args: "--default"
  examples:
    - "/my-skill target"
do_not:
  - summarize the output
---
```

## 3. Implementation Guide

### Adding a New Skill

1.  **Create Directory**: `P:/.claude/skills/<skill-name>/`
2.  **Create File**: `SKILL.md`
3.  **Define Metadata**: Add YAML frontmatter with `name`, `description`, `category`, and `execution` rules.
4.  **Add Documentation**: Write the "User Guide" and "Verification" sections in standard Markdown below the frontmatter.

### best Practices

*   **Atomic execution**: The `execution.directive` should be clear and concise.
*   **Self-Contained**: The skill directory can contain helper scripts (`_tools/`) or resources (`resources/`) if necessary.
*   **Unique Name**: Ensure the `name` does not conflict with existing skills.

## 4. Maintenance

### UI Metadata

If the SDLC Tech Tree UI doesn't show your new skill:
```bash
python P:/.claude/docs/sdlc_tech_tree/extract_skills.py
```
Updates: `P:/.claude/docs/sdlc_tech_tree/data/skills_metadata.js`
