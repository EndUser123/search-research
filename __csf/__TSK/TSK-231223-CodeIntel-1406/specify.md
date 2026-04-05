# Specification: Next-Generation Code Intelligence System

**TSK:** TSK-231223-CodeIntel-1406
**Created:** 2025-12-23 14:06 UTC
**Status:** Draft
**Priority:** High

---

## Executive Summary

Build a hybrid code intelligence system combining **LSP integration**, **ast-grep pattern matching**, and **graph database relationships** to surpass current `/discover` capabilities. This system will provide semantic code understanding, structural pattern matching, and repository-level relationship analysis.

**Motivation:** Leading tools (Sourcegraph, CodeGraph, ast-grep) all use this hybrid approach. Current `/discover` system lacks LSP integration, has no cross-repository search, and uses hardcoded tool registry.

---

## Problem Statement

### Current `/discover` System Limitations

**Strengths:**
- ✅ Integrates multiple tools (Tree-sitter, Ctags, HDMA, GPU acceleration)
- ✅ CKS knowledge base with coding standards
- ✅ Intelligent caching with 71.4% hit rate
- ✅ Constitutional compliance and quality gates

**Critical Gaps:**
1. **No LSP Integration** - Semantic understanding limited to AST parsing only
2. **No Cross-Repository Search** - Single codebase limitation
3. **Hardcoded Tool Registry** - Not dynamic discovery
4. **Manual Knowledge Updates** - No automatic indexing
5. **No Real-Time Intelligence** - Static snapshots only

### Market Leaders Analysis

| Tool | LSP | AST | Graph | Cross-Repo | Real-Time |
|------|-----|-----|-------|-----------|-----------|
| **Sourcegraph** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **CodeGraph** | ❌ | ✅ | ✅ | ❌ | ⚠️ |
| **ast-grep** | ❌ | ✅ | ❌ | ❌ | ❌ |
| **Current /discover** | ❌ | ✅ | ❌ | ❌ | ⚠️ |

**Key Insight:** All market leaders use **hybrid approaches** combining multiple technologies.

---

## Vision

### Target State

A code intelligence system that:

1. **Understands Code Semantically** - LSP provides type information, definitions, references
2. **Matches Structural Patterns** - ast-grep finds AST patterns across codebases
3. **Tracks Relationships** - Graph database connects functions, classes, dependencies
4. **Searches Everywhere** - Cross-repository indexing
5. **Learns Automatically** - Continuous knowledge integration from CKS

### User Experience

```bash
# Semantic code search (LSP-powered)
/codeintel "find all functions that call User.authenticate"
→ Returns: 12 functions across 3 repositories with type signatures

# Structural pattern matching (ast-grep)
/codeintel "find all async functions with bare except clauses"
→ Returns: 8 functions with exact AST pattern matches

# Relationship queries (graph database)
/codeintel "show inheritance hierarchy for BaseController"
→ Returns: Interactive graph with 47 classes

# Cross-repository search
/codeintel "find JWT validation implementations"
→ Returns: 23 implementations across 8 repos with diffs
```

---

## Requirements

### Functional Requirements

#### FR-1: LSP Integration
**Priority:** P0 (Critical)

The system MUST integrate Language Server Protocol for semantic code understanding:

- **FR-1.1:** Support Python LSP (python-lsp-server, pyright)
- **FR-1.2:** Support TypeScript LSP (typescript-language-server, vtsls)
- **FR-1.3:** Provide go-to-definition functionality
- **FR-1.4:** Provide find-references functionality
- **FR-1.5:** Provide semantic diagnostics (type errors, unused variables)
- **FR-1.6:** Cache LSP results for performance

**Acceptance Criteria:**
- LSP queries return results <500ms for cached, <2s for uncached
- Support for at least 3 languages (Python, TypeScript, JavaScript)
- Integration with existing CKS knowledge base

**Success Metric:**
- 40% reduction in token usage vs. text-based search (validated by LSP research)

---

#### FR-2: ast-grep Integration
**Priority:** P0 (Critical)

The system MUST integrate ast-grep for structural code search:

- **FR-2.1:** Parse code using tree-sitter grammars
- **FR-2.2:** Search by AST patterns (not text)
- **FR-2.3:** Support multi-language queries
- **FR-2.4:** Provide automated rewriting suggestions
- **FR-2.5:** Integrate with existing `/discover` workflow

**Acceptance Criteria:**
- ast-grep queries execute <1s for single repo, <5s for multi-repo
- Support for 10+ languages via tree-sitter
- Pattern library with 50+ common patterns

**Success Metric:**
- 95%+ accuracy on pattern detection (vs. 60% for regex)

---

#### FR-3: Graph Database Integration
**Priority:** P1 (High)

The system MUST build and query code relationship graphs:

- **FR-3.1:** Extract code entities (classes, functions, variables)
- **FR-3.2:** Build relationship edges (calls, imports, inherits)
- **FR-3.3:** Store in graph database (Neo4j or RocksDB)
- **FR-3.4:** Provide Cypher-like query interface
- **FR-3.5:** Visualize relationships (optional)

**Acceptance Criteria:**
- Graph build time <30s for 10K LOC
- Query response <100ms for simple traversals
- Support for 10K+ nodes, 100K+ edges

**Success Metric:**
- Enable relationship queries impossible with text search (e.g., "find all functions calling database operations")

---

#### FR-4: Cross-Repository Search
**Priority:** P1 (High)

The system MUST search across multiple repositories:

- **FR-4.1:** Index multiple git repositories
- **FR-4.2:** Deduplicate results across repos
- **FR-4.3:** Show repository context for each result
- **FR-4.4:** Support incremental updates (git hooks)

**Acceptance Criteria:**
- Index 10 repos (100K LOC) in <5 minutes
- Search across all repos <2s
- Automatic reindex on git commit

**Success Metric:**
- Discover patterns across entire code estate, not just current repo

---

#### FR-5: Real-Time Updates
**Priority:** P2 (Medium)

The system SHOULD update indexes automatically:

- **FR-5.1:** Watch filesystem for changes
- **FR-5.2:** Rebuild affected indexes incrementally
- **FR-5.3:** Invalidate stale cache entries
- **FR-5.4:** Support manual reindex command

**Acceptance Criteria:**
- Incremental updates <1s for single file change
- No stale results >5 minutes old

---

#### FR-6: CKS Integration
**Priority:** P2 (Medium)

The system MUST integrate with existing CKS knowledge base:

- **FR-6.1:** Store code patterns as CKS entries
- **FR-6.2:** Retrieve coding standards during analysis
- **FR-6.3:** Enforce standards via LSP diagnostics
- **FR-6.4:** Learn from user feedback

**Acceptance Criteria:**
- Automatic pattern extraction from code analysis
- Standards enforcement with 90%+ precision

---

### Non-Functional Requirements

#### NFR-1: Performance
- LSP queries: <500ms (cached), <2s (uncached)
- ast-grep queries: <1s (single repo), <5s (multi-repo)
- Graph queries: <100ms (simple), <1s (complex)
- Full reindex: <5min (10 repos, 100K LOC)

#### NFR-2: Scalability
- Support 100K+ LOC across 10+ repositories
- Handle 10K+ graph nodes, 100K+ edges
- Cache 100K+ code patterns

#### NFR-3: Usability
- CLI interface matching existing `/discover` syntax
- Intuitive query language for patterns
- Clear, actionable results

#### NFR-4: Maintainability
- Modular architecture (LSP, ast-grep, graph separate)
- Comprehensive test coverage (>80%)
- Clear documentation

#### NFR-5: Compatibility
- Python 3.11+
- Linux, macOS, Windows (WSL2)
- Existing CKS database format
- Existing `/discover` workflow

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Code Intelligence CLI                    │
│                    (unified interface)                      │
└───────────────────────────┬─────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│  LSP Module  │   │ ast-grep     │   │ Graph DB     │
│              │   │ Module       │   │ Module       │
├──────────────┤   ├──────────────┤   ├──────────────┤
│ • pyright    │   │ • Tree-sitter│   │ • Neo4j      │
│ • tsserver   │   │ • Patterns   │   │ • RocksDB    │
│ • clangd     │   │ • Rewriting  │   │ • Queries    │
└──────────────┘   └──────────────┘   └──────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            ▼
                 ┌──────────────────────┐
                 │   CKS Knowledge      │
                 │   Integration        │
                 └──────────────────────┘
```

### Data Flow

```
User Query → CLI Router → Module Selection → Parallel Execution
                                                │
                                                ▼
                                        Results Aggregation
                                                │
                                                ▼
                                        CKS Context Enrichment
                                                │
                                                ▼
                                        Output Formatting
```

---

## Success Criteria

### Technical Metrics
- ✅ LSP integration working for 3+ languages
- ✅ ast-grep pattern library with 50+ patterns
- ✅ Graph database with 10K+ nodes
- ✅ Cross-repository search across 5+ repos
- ✅ <2s query response time (95th percentile)

### User Metrics
- ✅ 40% reduction in context tokens needed
- ✅ 95%+ accuracy on pattern detection
- ✅ Enable new query types (impossible before)
- ✅ Positive user feedback on usability

### Quality Metrics
- ✅ 80%+ test coverage
- ✅ Zero critical bugs in production
- ✅ Documentation complete

---

## Open Questions

1. **Graph Database Choice:** Neo4j (full-featured) vs. RocksDB (lightweight)?
   - **Trade-off:** Neo4j requires separate service, RocksDB embedded

2. **LSP Server Management:** Spawn per session vs. persistent daemon?
   - **Trade-off:** Performance vs. resource usage

3. **Index Storage:** Where to store indexes (SQLite vs. separate files)?
   - **Trade-off:** Simplicity vs. performance

4. **Cross-Repo Scope:** How to discover repositories to index?
   - **Options:** Manual config, auto-discovery, monorepo detection

---

## Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| LSP server complexity | High | Medium | Start with 1-2 languages, add more |
| Graph database setup | Medium | Low | Use embedded RocksDB initially |
| Performance at scale | High | Medium | Implement caching early |
| Integration complexity | High | High | Modular architecture, phased rollout |

---

## Timeline Estimate

**Phase 1 (Foundation):** 3-4 weeks
- LSP integration for Python + TypeScript
- ast-grep CLI integration
- Basic graph schema

**Phase 2 (Features):** 2-3 weeks
- Graph database integration
- Pattern library (50+ patterns)
- Cross-repository indexing

**Phase 3 (Polish):** 1-2 weeks
- Performance optimization
- Documentation
- Testing

**Total:** 6-9 weeks

---

## References

- [ast-grep GitHub](https://github.com/ast-grep/ast-grep)
- [LSP Specification](https://microsoft.github.io/language-server-protocol/)
- [Sourcegraph Cody](https://sourcegraph.com/github.com/sourcegraph/cody)
- [CodeGraph MCP](https://www.pulsemcp.com/servers/jakedismo-codegraph-rust)
- [CODEXGRAPH Paper](https://aclanthology.org/2025.naacl-long.7.pdf)
