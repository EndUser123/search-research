# Implementation Plan: Discover Module Enhancements

## Overview

This plan implements AST-based pattern matching, Code Property Graphs, and hybrid call graph analysis for the `/discover` module.

## Implementation Sequence

### Phase 1: Foundation (Week 1)

#### Sprint 1.1: AST Pattern Matcher (Days 1-2)
**Goal:** Implement tree-sitter based pattern matching

**Tasks:**
1. Create `ast_pattern_matcher.py`
   - Implement `ASTPatternMatcher.__init__(language)`
   - Implement `find_pattern(code, pattern)` method
   - Implement `find_anti_patterns(code, patterns)` method

2. Add unit tests
   - Test Python function detection
   - Test class detection
   - Test import detection
   - Test anti-pattern detection

3. Integrate with ExplorerManager
   - Add `explore_type="ast_pattern"` option
   - Wire up pattern matching in exploration loop

**Deliverable:** Working AST pattern matching with 95%+ accuracy

---

#### Sprint 1.2: Code Property Graph (Days 3-5)
**Goal:** Build CPG for dependency analysis

**Tasks:**
1. Create `code_property_graph.py`
   - Implement `CodeNode` and `CodeEdge` dataclasses
   - Implement `CodePropertyGraph` class with NetworkX backend
   - Implement `add_node()` and `add_edge()` methods

2. Add query methods
   - `find_data_flow(start_var, max_depth)`
   - `find_unused_code()`
   - `detect_cycles()`

3. Build graph from AST
   - Parse Python files to extract nodes
   - Build edges for calls, defines, uses
   - Add data flow edges

4. Add unit tests
   - Test graph construction
   - Test data flow queries
   - Test unused code detection
   - Test cycle detection

**Deliverable:** Working CPG with dependency analysis

---

### Phase 2: Advanced Analysis (Week 2)

#### Sprint 2.1: Hybrid Call Graph (Days 6-8)
**Goal:** Combine static and dynamic analysis for accurate call graphs

**Tasks:**
1. Create `hybrid_call_graph.py`
   - Implement `CallSite` dataclass
   - Implement `HybridCallGraphAnalyzer` class

2. Static analysis
   - Implement `analyze_static(code, file_path)`
   - Use AST to find function calls
   - Extract caller-callee relationships

3. Dynamic analysis
   - Implement `analyze_dynamic(target_func)`
   - Use `sys.settrace()` for runtime tracing
   - Capture actual call sites

4. Merge results
   - Implement `merge_results()`
   - Combine static and dynamic with confidence scores
   - Handle discrepancies

5. Add unit tests
   - Test static analysis accuracy
   - Test dynamic tracing
   - Test merge logic

**Deliverable:** Hybrid call graph with 80-95% accuracy

---

#### Sprint 2.2: Incremental Parser (Days 9-10)
**Goal:** Add tree-sitter incremental parsing for watch-mode

**Tasks:**
1. Create `incremental_parser.py`
   - Implement `IncrementalParser` class
   - Implement tree-sitter language loading
   - Implement parse caching

2. Incremental updates
   - Implement `parse_incremental(file_path, new_content)`
   - Add edit detection using difflib
   - Apply tree edits efficiently

3. Add unit tests
   - Test full parsing
   - Test incremental parsing
   - Test cache hit/miss
   - Benchmark speedup

**Deliverable:** 10-100x faster re-parsing for changed files

---

### Phase 3: Integration (Week 2-3)

#### Sprint 3.1: Explorer Integration (Days 11-12)
**Goal:** Integrate new analyzers into existing explorer

**Tasks:**
1. Update `explorer_spec.py`
   - Import new modules
   - Add new exploration types
   - Wire up analyzers in `explore()` method

2. Update `ExplorationConfig`
   - Add `use_cpg` boolean option
   - Add `use_hybrid_cg` boolean option
   - Add `use_incremental` boolean option

3. Add integration tests
   - Test AST pattern exploration
   - Test CPG exploration
   - Test hybrid call graph exploration
   - Test incremental parsing

**Deliverable:** Fully integrated enhancements

---

#### Sprint 3.2: Documentation (Day 13)
**Goal:** Update documentation and examples

**Tasks:**
1. Update `DISCOVER_API_REFERENCE.md`
   - Document new exploration types
   - Add API examples
   - Update configuration options

2. Create examples
   - AST pattern matching examples
   - CPG query examples
   - Hybrid call graph examples

3. Update CHANGELOG
   - Document new features
   - Add migration notes

**Deliverable:** Complete documentation

---

## Testing Strategy

### Unit Tests
```bash
pytest __csf.nip/src/modules/discover/tests/test_ast_pattern_matcher.py
pytest __csf.nip/src/modules/discover/tests/test_code_property_graph.py
pytest __csf.nip/src/modules/discover/tests/test_hybrid_call_graph.py
pytest __csf.nip/src/modules/discover/tests/test_incremental_parser.py
```

### Integration Tests
```bash
pytest __csf.nip/src/modules/discover/tests/test_explorer_integration.py
```

### Performance Tests
```bash
pytest __csf.nip/src/modules/discover/tests/test_performance.py --benchmark
```

## Success Criteria

| Criterion | Target | Measure |
|-----------|--------|---------|
| Pattern detection accuracy | ≥95% | Test suite pass rate |
| Call graph accuracy | ≥80% | Benchmark vs manual |
| Incremental parsing speedup | ≥10x | Benchmark timing |
| Code coverage | ≥80% | pytest-cov |
| Documentation coverage | 100% | All APIs documented |

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Tree-sitter compilation fails | Provide pre-built binaries |
| Large graphs memory issues | Implement node limits |
| Dynamic tracing overhead | Make optional, cache results |
| Breaking changes | Add feature flags |

## Rollout Plan

1. **Alpha:** Internal testing (Week 3)
2. **Beta:** Feature flag release (Week 4)
3. **GA:** Full release (Week 5)

## Next Steps

1. Review and approve this plan
2. Create development branch
3. Start Sprint 1.1: AST Pattern Matcher
