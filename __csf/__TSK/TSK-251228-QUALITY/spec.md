# Quality System Refactoring - Technical Specification

**Task ID**: TSK-251229-QUALITY-REFACTOR
**Status**: Draft
**Version**: 1.0
**Created**: 2025-12-29

---

## Executive Summary

The CSF NIP Quality System requires architectural refactoring to address technical debt accumulated through organic growth. The primary issue is a monolithic `unified_analyzer.py` (1,436 lines) with multiple overlapping orchestrators, scattered configuration, and missing performance optimizations.

**Scope**: Refactor the quality system architecture while maintaining all existing functionality and improving maintainability, testability, and performance.

**Impact**: High - affects all quality analysis workflows in the CSF NIP ecosystem.

---

## Current State Analysis

### File Structure

```
P:/__csf.nip/src/quality/
├── unified_analyzer.py          # 1,436 lines - MONOLITHIC (primary issue)
├── orchestrator.py              # 477 lines - Semgrep/ESLint orchestrator
├── auto_fix.py                  # Auto-fix with confirmation
├── integration_contract_validator.py
├── test_detector.py
├── anti_pattern_detector.py
├── architectural_analyzer.py
├── compliance_intelligence.py
├── quality_gate_validator.py
├── zen_review_adapter.py
├── qual-foundation.py
├── qual-duplicates.py
├── verify_cost_tracking.py
├── duf_plugins/                 # 22 plugin domains
├── quality_engines/             # Separate orchestrator system
│   ├── engines.py              # 74KB
│   ├── orchestrator.py         # 12KB
│   ├── phases.py               # 23KB
│   ├── tool_registry.py        # 10KB
│   ├── config.py               # 5KB
│   └── parallel_manager.py     # 4KB
├── agent_validation/
├── documentation/
├── tests/                       # 5,107 lines
└── _archive_redundant/
```

### Key Issues Identified

| Priority | Issue | Impact | Effort |
|----------|-------|--------|--------|
| P0 | Monolithic unified_analyzer.py (1,436 lines) | High maintainability burden | High |
| P0 | Sequential tool execution | Poor performance | Medium |
| P0 | Insufficient test coverage for core modules | Regression risk | Medium |
| P1 | Scattered configuration management | Configuration complexity | Medium |
| P1 | Inconsistent error handling | Poor resilience | Low |
| P1 | No caching layer | Poor performance | Medium |
| P2 | Non-standard integration interfaces | Integration complexity | Medium |
| P2 | No performance monitoring | Lack of observability | Low |
| P2 | Missing documentation examples | Poor usability | Low |

---

## Target Architecture

### Design Principles

1. **Separation of Concerns**: Each module has a single, well-defined responsibility
2. **Plugin Architecture**: Extensible tool registration via standard interface
3. **Configuration as Code**: Centralized, type-safe configuration
4. **Fail-Safe**: Graceful degradation when tools unavailable
5. **Observable**: Built-in metrics and performance tracking

### Proposed Structure

```
P:/__csf.nip/src/quality/
├── core/                        # NEW: Core framework
│   ├── __init__.py
│   ├── base_analyzer.py         # Abstract base class
│   ├── analyzer_registry.py     # Plugin registration
│   ├── config.py                # Centralized configuration
│   ├── cache.py                 # Caching layer
│   ├── errors.py                # Error types and handlers
│   └── metrics.py               # Performance monitoring
├── analyzers/                   # NEW: Extracted tool analyzers
│   ├── __init__.py
│   ├── ruff_analyzer.py
│   ├── mypy_analyzer.py
│   ├── bandit_analyzer.py
│   ├── semgrep_analyzer.py
│   ├── eslint_analyzer.py
│   ├── cks_pattern_analyzer.py  # Consolidated CKS checks
│   └── contract_analyzer.py
├── orchestration/               # NEW: Unified orchestration
│   ├── __init__.py
│   ├── orchestrator.py          # Single orchestrator
│   ├── parallel.py              # Parallel execution
│   └── workflow.py              # Workflow definitions
├── plugins/                     # NEW: Standardized plugins
│   ├── __init__.py
│   └── base_plugin.py           # Plugin interface
├── utils/                       # NEW: Shared utilities
│   ├── __init__.py
│   ├── file_utils.py
│   └── path_utils.py
├── unified_analyzer.py          # REFACTORED: Facade only (<200 lines)
├── orchestrator.py              # REFACTORED: Uses new core
├── [existing modules remain]    # Other modules unchanged
└── tests/
    ├── test_core/
    ├── test_analyzers/
    ├── test_orchestration/
    └── integration/
```

---

## Detailed Requirements

### R1: Core Framework (P0)

#### R1.1 Base Analyzer Interface

All analyzers MUST implement the `BaseAnalyzer` interface:

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional

@dataclass
class AnalyzerResult:
    """Standard result format for all analyzers."""
    tool_name: str
    status: str  # "success", "error", "skipped"
    files_analyzed: int
    issues_found: int
    issues_fixed: int  # if auto-fix applied
    duration_ms: float
    details: Dict[str, Any]
    errors: List[str]

class BaseAnalyzer(ABC):
    """Abstract base class for all quality analyzers."""

    @property
    @abstractmethod
    def tool_name(self) -> str:
        """Name of the analysis tool."""

    @property
    @abstractmethod
    def file_extensions(self) -> set[str]:
        """Supported file extensions."""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if tool is installed and available."""

    @abstractmethod
    def analyze(self, targets: List[Path], **kwargs) -> AnalyzerResult:
        """Run analysis on targets."""

    @abstractmethod
    def autofix(self, targets: List[Path], **kwargs) -> AnalyzerResult:
        """Apply auto-fixes to targets."""
```

#### R1.2 Analyzer Registry

- Dynamic registration of analyzer plugins
- Discovery by file extension
- Capability queries (autofix support, severity levels)
- Tool availability checking

```python
class AnalyzerRegistry:
    """Registry for managing analyzer plugins."""

    def register(self, analyzer: BaseAnalyzer) -> None: ...
    def get_analyzers_for_files(self, files: List[Path]) -> List[BaseAnalyzer]: ...
    def get_analyzer(self, name: str) -> Optional[BaseAnalyzer]: ...
    def list_available(self) -> List[str]: ...
    def list_by_capability(self, capability: str) -> List[BaseAnalyzer]: ...
```

#### R1.3 Caching Layer

- File hash-based cache keys
- TTL-based invalidation
- Configurable cache backend (memory, file, Redis)
- Cache statistics

```python
class AnalysisCache:
    """Cache for analysis results."""

    def get(self, key: str) -> Optional[AnalyzerResult]: ...
    def set(self, key: str, value: AnalyzerResult, ttl: Optional[int] = None): ...
    def invalidate(self, pattern: str): ...
    def get_stats(self) -> Dict[str, Any]: ...
    def clear(self): ...
```

### R2: Extracted Analyzers (P0)

#### R2.1 Tool-Specific Analyzers

Extract each tool from `unified_analyzer.py` into separate modules:

| Analyzer | Source Method | Responsibilities |
|----------|---------------|------------------|
| `RuffAnalyzer` | `analyze_ruff()` | Linting, style checks |
| `MypyAnalyzer` | `analyze_mypy()` | Type checking |
| `BanditAnalyzer` | `analyze_bandit()` | Security scanning |
| `SemgrepAnalyzer` | orchestrator Semgrep | Pattern-based security |
| `ESLintAnalyzer` | orchestrator ESLint | JavaScript/TS linting |
| `CKSPatternAnalyzer` | 20+ `_check_*` methods | Pattern validation |
| `ContractAnalyzer` | `analyze_integration_contract()` | Contract validation |

#### R2.2 CKS Pattern Consolidation

The 20+ `_check_*` methods in `unified_analyzer.py` MUST be consolidated into `CKSPatternAnalyzer` with:

- Data-driven pattern definitions
- Unified execution interface
- Configurable severity levels
- Extensible pattern registration

```python
@dataclass
class PatternRule:
    id: str
    name: str
    severity: str
    check_func: Callable
    description: str

class CKSPatternAnalyzer(BaseAnalyzer):
    """Consolidated CKS pattern checking."""

    def __init__(self):
        self.patterns: Dict[str, PatternRule] = {}
        self._register_patterns()

    def _register_patterns(self) -> None:
        """Register all pattern checks."""
        # Register circular_imports, length, async_requests, etc.
```

### R3: Unified Orchestration (P0)

#### R3.1 Single Orchestrator

Consolidate `orchestrator.py` and `quality_engines/orchestrator.py`:

```python
class QualityOrchestrator:
    """Unified orchestration for all quality analysis."""

    def __init__(
        self,
        config: QualityConfig,
        registry: AnalyzerRegistry,
        cache: Optional[AnalysisCache] = None
    ):
        self.config = config
        self.registry = registry
        self.cache = cache
        self.executor = ParallelExecutor(config.parallel)

    def analyze(
        self,
        targets: List[Path],
        analyzers: Optional[List[str]] = None,
        parallel: bool = True
    ) -> OrchestratorResult: ...

    def analyze_and_fix(
        self,
        targets: List[Path],
        analyzers: Optional[List[str]] = None
    ) -> OrchestratorResult: ...

    def verify_fixes(self, result: OrchestratorResult) -> VerificationResult: ...
```

#### R3.2 Parallel Execution

- Async-based parallel tool execution
- Configurable worker pool
- Progress reporting
- Error isolation (one tool failure doesn't stop others)

```python
class ParallelExecutor:
    """Execute analyzers in parallel."""

    async def execute_all(
        self,
        analyzers: List[BaseAnalyzer],
        targets: List[Path]
    ) -> List[AnalyzerResult]: ...
```

### R4: Configuration Management (P1)

#### R4.1 Centralized Configuration

```python
@dataclass
class QualityConfig:
    """Centralized quality system configuration."""

    # Tool paths
    semgrep_path: Optional[Path] = None
    eslint_path: Optional[Path] = None
    ruff_path: Optional[Path] = None
    mypy_path: Optional[Path] = None

    # Configuration files
    semgrep_config: Path = Path(".semgrep.yml")
    eslint_config: Path = Path("eslint.config.mjs")

    # Execution
    parallel: bool = True
    max_workers: int = 4
    timeout_seconds: int = 300

    # Caching
    cache_enabled: bool = True
    cache_ttl_seconds: int = 3600
    cache_backend: str = "memory"  # "memory", "file", "redis"

    # Behavior
    autofix: bool = False
    fail_on_error: bool = False
    severity_threshold: str = "INFO"

    @classmethod
    def from_file(cls, path: Path) -> "QualityConfig": ...
    @classmethod
    def from_env(cls) -> "QualityConfig": ...
```

### R5: Error Handling (P1)

#### R5.1 Standardized Error Types

```python
class QualityError(Exception):
    """Base exception for quality system."""

class AnalyzerNotFoundError(QualityError):
    """Requested analyzer not found."""

class ToolNotAvailableError(QualityError):
    """Tool not installed or not in PATH."""

class ConfigurationError(QualityError):
    """Invalid configuration."""

class AnalysisTimeoutError(QualityError):
    """Analysis timed out."""
```

#### R5.2 Error Recovery Strategy

- Missing tools: Skip with warning (not error)
- Tool failures: Log and continue with other tools
- Timeout: Cancel and report partial results
- Invalid config: Fail fast with clear message

### R6: Performance Monitoring (P2)

#### R6.1 Metrics Collection

```python
@dataclass
class AnalysisMetrics:
    """Performance metrics for analysis runs."""

    total_duration_ms: float
    tool_durations: Dict[str, float]
    files_per_second: float
    cache_hit_rate: float
    parallel_efficiency: float  # speedup vs sequential

class MetricsCollector:
    """Collect and report performance metrics."""

    def record_tool_run(self, tool: str, duration: float, files: int): ...
    def get_metrics(self) -> AnalysisMetrics: ...
    def reset(self): ...
```

### R7: Integration Interface (P2)

#### R7.1 Unified Entry Point

```python
# Primary interface for external integration
def analyze_quality(
    targets: str | List[str] | Path | List[Path],
    config: Optional[QualityConfig] = None,
    **kwargs
) -> OrchestratorResult:
    """
    Main entry point for quality analysis.

    Args:
        targets: Files/directories to analyze
        config: Optional configuration
        **kwargs: Override config options

    Returns:
        OrchestratorResult with all findings
    """
```

---

## Non-Functional Requirements

### NFR1: Maintainability

- Target module size: <500 lines per file
- Cyclomatic complexity: <10 per method
- Test coverage: >80% for new code
- Documentation: All public APIs documented

### NFR2: Performance

- Parallel execution must achieve >2x speedup with 4 workers
- Cache hit rate target: >50% for incremental runs
- Cold start time: <5 seconds for full analysis

### NFR3: Backward Compatibility

- Existing `unified_analyzer.py` API MUST remain functional
- Existing `orchestrator.py` API MUST remain functional
- Command-line interface MUST NOT change

### NFR4: Extensibility

- New analyzers MUST be addable without core changes
- Plugin registration MUST be discoverable
- Configuration MUST support overrides without code changes

---

## Implementation Phases

### Phase 1: Foundation (Week 1)

**Tasks**:
1. Create `core/` module structure
2. Implement `BaseAnalyzer` interface
3. Implement `AnalyzerRegistry`
4. Create `QualityConfig` dataclass
5. Add unit tests for core components

**Deliverables**:
- `src/quality/core/` directory
- Core interfaces and classes
- Test suite for core

**Acceptance**:
- All core tests pass
- Interfaces documented
- No breaking changes to existing code

### Phase 2: Analyzer Extraction (Week 2)

**Tasks**:
1. Extract `RuffAnalyzer` from `unified_analyzer.py`
2. Extract `MypyAnalyzer` from `unified_analyzer.py`
3. Extract `BanditAnalyzer` from `unified_analyzer.py`
4. Create `CKSPatternAnalyzer` with consolidated patterns
5. Migrate `SemgrepAnalyzer` and `ESLintAnalyzer` to new interface
6. Add unit tests for each analyzer

**Deliverables**:
- `src/quality/analyzers/` directory
- Individual analyzer modules
- Test suite for each analyzer

**Acceptance**:
- All analyzer tests pass
- Each analyzer <300 lines
- Implements `BaseAnalyzer` interface
- No functionality lost

### Phase 3: Orchestration Unification (Week 3)

**Tasks**:
1. Create `orchestration/` module
2. Implement `ParallelExecutor`
3. Create unified `QualityOrchestrator`
4. Migrate existing orchestrator functionality
5. Add integration tests

**Deliverables**:
- `src/quality/orchestration/` directory
- Unified orchestrator
- Integration test suite

**Acceptance**:
- All tests pass
- Parallel execution working
- Existing APIs still functional

### Phase 4: Caching and Performance (Week 4)

**Tasks**:
1. Implement `AnalysisCache` with memory backend
2. Add file-based cache backend
3. Integrate cache into orchestrator
4. Implement `MetricsCollector`
5. Add performance benchmarks

**Deliverables**:
- `src/quality/core/cache.py`
- `src/quality/core/metrics.py`
- Benchmark suite

**Acceptance**:
- Cache improves performance on repeated runs
- Metrics reported correctly
- Cache invalidation working

### Phase 5: Documentation and Examples (Week 5)

**Tasks**:
1. Update API documentation
2. Add usage examples
3. Create plugin development guide
4. Update troubleshooting guide
5. Add architecture diagrams

**Deliverables**:
- Updated `docs/quality/` directory
- Example scripts
- Plugin development guide

**Acceptance**:
- All public APIs documented
- Examples tested and working
- Architecture approved

---

## Testing Strategy

### Unit Tests

- Each analyzer: Mock tool output, test parsing
- Core components: Test in isolation
- Configuration: Test loading and validation
- Cache: Test hit/miss, invalidation, TTL

### Integration Tests

- End-to-end analysis workflow
- Multi-tool coordination
- Parallel execution
- Cache integration

### Performance Tests

- Benchmark sequential vs parallel
- Cache effectiveness measurement
- Memory usage profiling

### Backward Compatibility Tests

- Existing API calls work unchanged
- Old configuration files still work
- Command-line interface unchanged

---

## Migration Path

### Step 1: Parallel Development

- Create new structure alongside existing code
- No modifications to existing modules
- New code in `core/`, `analyzers/`, `orchestration/`

### Step 2: Facade Pattern

- Refactor `unified_analyzer.py` to use new components
- Maintain existing API as facade
- Internally delegate to new architecture

### Step 3: Gradual Migration

- Move users to new API over time
- Deprecate old API (not remove)
- Provide migration guide

### Step 4: Cleanup

- Remove `_archive_redundant/` after validation
- Consolidate duplicate orchestrators
- Final documentation update

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Breaking existing workflows | Medium | High | Facade pattern, comprehensive tests |
| Performance regression | Low | Medium | Benchmarks before/after |
| Tool compatibility issues | Medium | Medium | Graceful degradation, extensive testing |
| Configuration migration | Low | Low | Auto-migration script |
| Incomplete test coverage | Medium | Medium | Coverage targets, test requirements |

---

## Success Criteria

### Must Have (P0)

1. [ ] `unified_analyzer.py` reduced to <200 lines (facade only)
2. [ ] All tool analyzers extracted to separate modules
3. [ ] Parallel execution implemented and working
4. [ ] Test coverage >80% for new code
5. [ ] All existing tests still pass
6. [ ] No breaking changes to public APIs

### Should Have (P1)

1. [ ] Centralized configuration management
2. [ ] Caching layer implemented
3. [ ] Standardized error handling
4. [ ] Metrics collection
5. [ ] Plugin development documentation

### Nice to Have (P2)

1. [ ] Redis cache backend
2. [ ] Performance dashboard
3. [ ] Plugin marketplace
4. [ ] Auto-configuration discovery

---

## Dependencies

### External Dependencies

- Python 3.12+
- Existing tools (ruff, mypy, bandit, semgrep, eslint)
- asyncio (standard library)
- pytest (testing)

### Internal Dependencies

- CKS database for pattern analyzer
- TaskMaster for workflow tracking
- Configuration management system

---

## Open Questions

1. **Cache Backend**: Should we support Redis backend or stick with file-based?
2. **Plugin Discovery**: Auto-discovery via entry points or manual registration?
3. **Metrics Storage**: Where should metrics be stored and for how long?
4. **Deprecation Timeline**: When can old APIs be removed?

---

## Approval

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Architect | | | |
| Developer | | | |
| QA | | | |
| Product Owner | | | |

---

**Document Version History**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-29 | Claude Code | Initial specification |
