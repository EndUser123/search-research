# Auto-Triggering Design for `/all` Skill

## Overview

The `/all` skill is the **default search handler** for all search and research queries. It intelligently routes between local and web sources using auto mode (checks local first, expands to web if needed). This document explains the design, rationale, and implementation.

## Problem Statement

Previously, users had to choose between three search tools:
- `/search` for local-only
- `/research` for web-only
- `/all` for unified

This created cognitive load and friction. Since `/all` already implements intelligent routing via auto mode (local first, web if needed), it should be the default entry point for all search queries.

## Solution

### Frontmatter Changes

**Before:**
```yaml
description: Universal search across your local data AND the web - truly unified results with three-layer filtering
triggers:
  - /all
  - 'search all'
  - 'search everywhere'
```

**After:**
```yaml
description: **ALWAYS use this skill for search and research queries** - unified search with intelligent source selection
triggers:
  - /all
  - 'search for'
  - 'find'
  - 'look for'
  - 'what do we know about'
  - 'search'
  - 'find information'
```

### Key Changes

1. **Broad "ALWAYS" directive**: `/all` is now the default for ALL search queries
2. **Broader triggers**: Catches generic search intent ("find X", "search for X")
3. **Simplified guardrails**: Removed tool-specific `do_not` entries (auto mode handles routing)
4. **Preserved specialized tools**: `/search` and `/research` still available for explicit use

## Trigger Logic

### Auto-Triggering Scenarios

The skill auto-triggers for virtually all search queries:

| Query Pattern | Intent | Action |
|---------------|--------|--------|
| "find User class" | Code search | `/all` (via GrepBackend) |
| "what did we discuss" | Local knowledge | `/all` (via local backends) |
| "research best practices" | Web documentation | `/all` (auto mode expands to web) |
| "find information about async patterns" | Multi-source | `/all` |
| "search for authentication patterns" | Generic search | `/all` |

### Specialized Tool Use (Explicit Invocation)

Users can still explicitly invoke specialized tools:

| When to Use | Tool | Why |
|-------------|------|-----|
| "I only want local results, fast" | `/search` | Explicit local-only, guaranteed <1s |
| "I only want web results" | `/research` | Explicit web-only, no local clutter |

**Note:** These are explicit user choices, not auto-routing decisions.

## Design Rationale

### Why Broad "ALWAYS" Directive?

**Before (Scoped):**
```yaml
description: **ALWAYS use when user needs BOTH local and web sources**
```
- **Problem**: User must predict intent before asking
- **Result**: Cognitive load, tool selection paralysis

**After (Broad):**
```yaml
description: **ALWAYS use this skill for search and research queries**
```
- **Benefit**: Single entry point, auto mode handles routing
- **Result**: Simpler mental model, auto mode optimizes performance

### How Auto Mode Prevents Unnecessary Web Calls

The key insight: `/all`'s `auto` mode already implements smart routing:

1. **Step 1:** Search local backends (CDS, CKS, RLM, Grep) → <1s
2. **Step 2:** Check result quality (score, count, relevance)
3. **Step 3:** If quality is poor → Trigger web search → +5-10s
4. **Step 4:** Merge and rank results from all sources

**Result:** Fast local queries don't pay web latency penalty.

## Tool Boundaries

The design establishes clear use cases for each tool:

```
Query Type                    │ Tool      │ When to Use
──────────────────────────────────────────────────────────────
Any search/research query     │ /all      │ Default (auto-routing)
Explicit local-only request   │ /search   │ "I only want local, fast"
Explicit web-only request     │ /research │ "I only want web results"
```

**Key Change:** `/all` is now the default entry point. `/search` and `/research` become specialized tools for explicit user preferences, not auto-routing decisions.

## Performance Implications

### Local-Only Queries (Fast Path)
- User: "what did we discuss about auth"
- Action: `/all` auto mode → local backends → quality check passes → no web search
- Cost: <1s (same as `/search`)
- Benefit: Single tool, no mental overhead

### Code Search Queries (Fast Path)
- User: "find User class"
- Action: `/all` auto mode → GrepBackend → returns class definition
- Cost: <500ms (AST indexing is fast)
- Benefit: No need for separate code search tool

### Web-Required Queries (Slower Path)
- User: "research latest React patterns"
- Action: `/all` auto mode → local backends → poor quality → web search
- Cost: 1-10s (unavoidable, needs web)
- Benefit: Automatic, user didn't need to specify "web"

## Testing Strategy

### Positive Tests (Should Auto-Trigger)

All of these should invoke `/all` automatically:

```bash
# Code search
"find User class"
"search for process_data function"
"where is authenticate defined"

# Local knowledge
"what did we discuss about auth"
"find our decision on JWT"
"look for previous discussions"

# Web research
"research latest React patterns"
"find current best practices for async"
"search for documentation on pandas"

# Multi-source
"find information about microservices"
"what do we know about authentication"
"search everything about testing"
```

### Specialized Tool Tests (Explicit Invocation)

These require explicit user choice:

```bash
# User explicitly wants local-only
"/search 'what did we discuss'"  # Guaranteed local-only

# User explicitly wants web-only
"/research 'React patterns'"     # Guaranteed web-only
```

## Fallback Behavior

If `/all` auto-triggers but results are poor:
1. User can explicitly invoke `/search` or `/research`
2. Skill routing respects explicit tool invocation
3. No permanent state change from auto-triggering

## Monitoring

### Metrics to Track

1. **Auto-trigger rate**: How often `/all` activates without explicit `/all`
2. **Fallback rate**: How often users switch to `/search` or `/research` after auto-trigger
3. **User satisfaction**: Implicit via low fallback rate

### Success Indicators

- High auto-trigger rate + low fallback rate = Good triggering
- Low auto-trigger rate = Trigger phrases too restrictive
- High fallback rate = Over-triggering, need narrower scope

## Evolution Path

If monitoring shows issues:

| Issue | Symptom | Fix |
|-------|---------|-----|
| Under-triggering | Low auto-trigger rate | Add more trigger phrases |
| Over-triggering | High fallback to `/search` | Narrow "ALWAYS" directive scope |
| Code-search collision | Users confused with `/serena` | Add "do_not use for code" in description |

## Comparison with Serena

| Aspect | /serena | /all |
|--------|---------|-----|
| Domain | Code semantic analysis | Multi-source information |
| "ALWAYS" scope | "ALWAYS use for semantic code analysis" | "ALWAYS use when user needs BOTH local and web" |
| Over-trigger risk | Low (code-specific) | Medium (generic queries) |
| Mitigation | Clear domain boundary | Scoped "ALWAYS" + guardrails |

## References

- Original SKILL.md: `skills/all/SKILL.md`
- Serena SKILL.md (reference): `.claude/skills/serena/SKILL.md`
- Three-layer filtering: `skills/all/SKILL.md` (Implementation Details section)
