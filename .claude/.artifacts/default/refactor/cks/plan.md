# Refactor Plan: core/cks

## Status
- DISCOVER: Complete (130 findings, 8 agents)
- CLASSIFY_DEBT: Complete (P0=17, P1=0, P2=37, P3=16)
- PRIORITIZE: Complete
- PLAN: In Progress

## P0 Bugs FIXED (4/4)
| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 1 | `hyde.py` | 76 | `query.lower()` result not assigned | `query = query.lower()` ✓ |
| 2 | `quality.py` | 198 | SQL: `thumbs_down > (thumbs_up OR 0)` | `COALESCE(thumbs_up, 0)` ✓ |
| 3 | `unified.py` | 915 | Regex typo: `r"([^aeiou])'{2,}"` | `r"([^aeiou]){2,}"` ✓ |
| 4 | `performance_optimizer.py` | 391 | Class name `CKSPreformanceOptimizer` | `CKSPerformanceOptimizer` ✓ |

## P1: Error Handling (Pending)

| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 5 | `quality.py` | 76 | Bare `except:` in datetime parsing | `except Exception:` |
| 6 | `unified.py` | 2574 | Empty except block | Add logging or specific exception |
| 7 | `storage_manager.py` | 562 | Lock holding during I/O | Release lock before commit |
| 8 | `gpu_manager.py` | 881 | Dict created but never assigned | Remove or assign |

## P2: DRY Consolidation (Pending)

**Issue**: 4 nearly identical `_create_*_graph_schema` methods in `storage_manager.py`

**Approach**: Extract common schema creation to a helper:

```python
def _create_graph_schema(self, graph_type: str) -> None:
    """Create common graph schema for a given graph type."""
    cursor = self._db_connection.cursor()
    node_table = f"{graph_type}_nodes"
    edge_table = f"{graph_type}_edges"
    
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {node_table} (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            content TEXT NOT NULL,
            metadata JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # ... edges and indexes
```

## P3: Test Coverage (Pending)

| Class | File | Lines | Status |
|-------|------|-------|--------|
| `CKS` | `unified.py` | ~4000 | ZERO tests |
| `CKSQueryInterface` | `cks_query_interface.py` | 510 | NO tests |
| `DecisionExtractor` | `decision_extractor.py` | ~200 | NO tests |
| `MultiGraphEngine` | `core/multi_graph_engine.py` | ~800 | Cross-graph untested |

**Approach**: Add focused characterization tests for `unified.py` and `cks_query_interface.py` — the two main entry points.

## Tiny Commits Plan

```
[commit 1] fix(hyde): assign query.lower() result
[commit 2] fix(quality): use COALESCE instead of OR in SQL
[commit 3] fix(unified): fix regex typo for consonant matching
[commit 4] fix(performance_optimizer): correct CKSPerformanceOptimizer spelling
[commit 5] fix(quality): replace bare except with except Exception
[commit 6] refactor(storage_manager): consolidate _create_graph_schema methods
[commit 7] test(unified): add CKS class characterization tests
[commit 8] test(cks_query_interface): add CKSQueryInterface tests
```

## Out of Scope
- `storage_manager_optimized.py` and `storage_manager_original.py` removal (high risk, would break callers)
- Dataclass `slots=True` migration (Python 3.12+ optimization, not critical)
- GPU manager refactoring (working, tested in production)
- Multi-graph engine cross-graph operations (untested but functional)

## Verification
- All fixes compile: `python -m py_compile core/cks/*.py core/cks/**/*.py`
- ruff check passes
- Existing tests pass (if any)
