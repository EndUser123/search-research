# TSK-251228-QUALITY: Architecture

## Current Architecture (Before Refactoring)

```
┌─────────────────────────────────────────────────────────────────┐
│                     CSF NIP Quality System                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌──────────────┐ │
│  │   Orchestrator │    │Unified Analyzer │    │Quality Engs  │ │
│  │ (477 lines)    │    │(1,436 lines)    │    │(134KB total) │ │
│  │ - Semgrep/ESLint│    │- Ruff/Mypy/     │    │- Engines     │ │
│  │ - Multi-language│    │- Bandit/Security│    │- Phases      │ │
│  │ - Auto-fix      │    │- CKS Patterns   │    │- Parallel    │ │
│  └─────────────────┘    └─────────────────┘    └──────────────┘ │
│           │                     │                     │        │
│           │                     │                     │        │
│  ┌─────────────────┐    ┌─────────────────┐    ┌──────────────┐ │
│  │Config Files    │    │CKS Integration │    │DUF Plugins   │ │
│  │-.semgrep.yml    │    │- Patterns/Anti- │    │- 22 Domains  │ │
│  │-.eslint.config │    │- Pattern checks │    │- Modular     │ │
│  │                │    │- Database       │    │- Extensible  │ │
│  └─────────────────┘    └─────────────────┘    └──────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

**Issues:**
- Monolithic UnifiedAnalyzer (1,436 lines)
- Multiple overlapping orchestrators
- No unified configuration
- Sequential execution only
- No caching
- Scattered error handling

## Target Architecture (After Refactoring)

```
┌─────────────────────────────────────────────────────────────────┐
│                  Refactored Quality System                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    QualityOrchestrator                   │  │
│  │  - analyze(), analyze_and_fix(), verify_fixes()          │  │
│  │  - ParallelExecutor for concurrent tool runs             │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           │                                     │
│         ┌─────────────────┼─────────────────┐                 │
│         │                 │                 │                 │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐           │
│  │   Analyzers  │ │    Core      │ │   Plugins    │           │
│  │ ┌──────────┐ │ │ ┌──────────┐ │ │ ┌──────────┐ │           │
│  │ │Ruff      │ │ │ │BaseAnalyzer│ │ │BasePlugin│ │           │
│  │ │Mypy      │ │ │ │Registry   │ │ │          │ │           │
│  │ │Bandit    │ │ │ │Config     │ │ │          │ │           │
│  │ │Semgrep   │ │ │ │Cache      │ │ │          │ │           │
│  │ │ESLint    │ │ │ │Errors     │ │ │          │ │           │
│  │ │CKS Patts │ │ │ │Metrics    │ │ │          │ │           │
│  │ └──────────┘ │ │ └──────────┘ │ │ └──────────┘ │           │
│  └──────────────┘ └──────────────┘ └──────────────┘           │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                   UnifiedAnalyzer (Facade)               │  │
│  │  - Maintains backward compatibility                       │  │
│  │  - Delegates to QualityOrchestrator                      │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

**Improvements:**
- Modular analyzers (<300 lines each)
- Single unified orchestrator
- Centralized QualityConfig
- Parallel execution support
- File hash-based caching
- Standardized error handling
- Plugin architecture

## Module Structure

```
src/quality/
├── core/                        # NEW: Core framework
│   ├── __init__.py
│   ├── base_analyzer.py         # Abstract BaseAnalyzer interface
│   ├── analyzer_registry.py     # Plugin registration
│   ├── config.py                # QualityConfig dataclass
│   ├── cache.py                 # AnalysisCache
│   ├── errors.py                # QualityError hierarchy
│   └── metrics.py               # MetricsCollector
├── analyzers/                   # NEW: Extracted tool analyzers
│   ├── __init__.py
│   ├── ruff_analyzer.py         # RuffAnalyzer
│   ├── mypy_analyzer.py         # MypyAnalyzer
│   ├── bandit_analyzer.py       # BanditAnalyzer
│   ├── semgrep_analyzer.py      # SemgrepAnalyzer
│   ├── eslint_analyzer.py       # ESLintAnalyzer
│   ├── cks_pattern_analyzer.py  # CKSPatternAnalyzer (consolidated)
│   └── contract_analyzer.py     # ContractAnalyzer
├── orchestration/               # NEW: Unified orchestration
│   ├── __init__.py
│   ├── orchestrator.py          # QualityOrchestrator
│   ├── parallel.py              # ParallelExecutor (asyncio)
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
└── [existing modules remain]
```

## Design Patterns

| Pattern | Usage | Location |
|---------|-------|----------|
| Strategy | Tool-specific analyzers | `analyzers/` |
| Registry | Dynamic analyzer discovery | `core/analyzer_registry.py` |
| Facade | Backward compatibility | `unified_analyzer.py` |
| Factory | Analyzer instantiation | `core/analyzer_registry.py` |
| Cache | Result caching | `core/cache.py` |
| Observer | Metrics collection | `core/metrics.py` |
| Plugin | Extensibility | `plugins/base_plugin.py` |

## Data Flow

```
User Request
    │
    ▼
UnifiedAnalyzer.analyze() (Facade)
    │
    ▼
QualityOrchestrator.analyze()
    │
    ├──► AnalyzerRegistry.get_analyzers_for_files()
    │       │
    │       └──► Returns [RuffAnalyzer, MypyAnalyzer, ...]
    │
    ├──► AnalysisCache.get() (check cache)
    │       │
    │       ├──► Hit? Return cached result
    │       └──► Miss? Continue to execution
    │
    └──► ParallelExecutor.execute_all()
            │
            ├──► asyncio.gather(*analyzers)
            │       │
            │       ├──► RuffAnalyzer.analyze()
            │       ├──► MypyAnalyzer.analyze()
            │       └────► ... (parallel)
            │
            └──► Returns [AnalyzerResult, ...]
    │
    ├──► AnalysisCache.set() (store results)
    │
    └──► MetricsCollector.record_tool_run()
```

## Integration Points

### External Tools
- **Ruff**: Fast Python linter
- **Mypy**: Static type checker
- **Bandit**: Security linter
- **Semgrep**: Pattern-based security
- **ESLint**: JavaScript/TS linter

### Internal Systems
- **CKS**: Pattern database, anti-pattern definitions
- **TaskMaster**: Workflow tracking
- **DUF Plugins**: Domain-specific analysis plugins

### Configuration
- `.semgrep.yml`: Semgrep rules
- `eslint.config.mjs`: ESLint rules (9.x flat config)
- `quality_config.py`/`.toml`/`.yaml`: Unified config (NEW)
