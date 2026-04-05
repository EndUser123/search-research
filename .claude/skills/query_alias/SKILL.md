---
name: query_alias
description: Knowledge base queries - backward compatibility alias for unified research
version: 1.0.0
status: stable
category: research
triggers:
  - /query
aliases:
  - /query

suggest:
  - /cks
  - /search
  - /research
---

# Query Command (Backward Compatibility)

Backward compatibility alias for unified research command in knowledge retrieval mode.

## Purpose

Knowledge base query command providing backward compatibility alias for unified research system.

## Project Context

### Constitution/Constraints
- Legacy command support for existing workflows
- Automatic routing to `/research --mode knowledge`
- Maintains exact CKS RAG functionality

### Technical Context
- Alias automatically adds `--mode knowledge` flag
- Routes to unified research backend
- Preserves CKS RAG query behavior

### Architecture Alignment
- Integrates with `/cks` for Constitutional Knowledge System
- Works alongside `/search` for unified search
- Migrates to `/research` as primary command

## Your Workflow

1. **Receive Query**: Accept search term from user
2. **Add Flag**: Automatically append `--mode knowledge`
3. **Route**: Forward to `/research` command
4. **Return Results**: Display knowledge retrieval output

## Validation Rules

### Migration Path
- **Current usage**: `/query <search term>`
- **New equivalent**: `/research <search term>` (auto-detects knowledge mode)
- The alias maintains exact CKS RAG functionality during transition

### Prohibited Actions
- Do not modify the query content when routing
- Do not add additional flags beyond `--mode knowledge`

## Usage

```bash
# All these are automatically routed to: /research --mode knowledge
/query "existing authentication patterns"
/query "previous database optimizations"
/query "React performance solutions"
```

## Migration Path

**Current usage:** `/query <search term>`
**New equivalent:** `/research <search term>` (auto-detects knowledge mode)

The alias automatically adds `--mode knowledge` to maintain exact CKS RAG functionality.
