---
name: solo_dev_mappings
description: Terminology mappings to translate enterprise patterns to solo dev equivalents.
version: "1.0.0"
status: beta
enforcement: advisory
category: strategy
---
# Solo Dev Terminology Mappings

CONTEXT: Solo developer workflow. No enterprise infrastructure.

## Terminology Mappings

| Enterprise Term | Solo Dev Equivalent |
| --------------- | ------------------- |
| deployment | implementation |
| production | development environment |
| staging | (omit) |
| rollout | immediate availability |
| pipeline | workflow |

## Usage

When these terms appear ambiguous, use the solo dev equivalent:
- "Deploy to production" → "Implement in development environment"
- "Rollout the feature" → "Make immediately available"
- "Staging pipeline" → "workflow"

## Enhanced Commit Messages

This file demonstrates the enhanced commit message format with WHY/WHAT/VERIFICATION sections.

This prevents enterprise terminology from triggering inappropriate patterns.
