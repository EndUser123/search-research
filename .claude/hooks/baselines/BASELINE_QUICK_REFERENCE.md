# Baseline Quick Reference: 3D Compatibility Matrix

## Baseline Summary (2026-03-15)

| Metric | Baseline | Target | Status |
|--------|----------|--------|--------|
| **M1**: Cross-category usage | 0.0% | 15% | ⏸️ Not deployed |
| **M2**: Performance overhead | 0.001ms | <5ms | ✅ PASS |
| **M3**: Matrix entries | 19 | <50 | ✅ PASS |
| **S1**: CKS queries/day | 0.0 | -20% | ⏸️ No data |

## Key Statistics

### Performance (M2)
- **Average**: 0.001ms (5,000x better than target)
- **P95**: 0.001ms
- **Max**: 0.007ms
- **Samples**: 100 iterations

### Matrix Distribution (M3)
- **Frameworks**: 8 total (socratic: 4, chestertons: 4, assumption: 2, outcome: 3, inversion: 2, calibrated: 2, hanlons: 1, devils: 1)
- **Modes**: 4 total (sequential: 8, multi_agent: 7, two_stage: 2, graph: 2)
- **Profiles**: 7 total (architecture: 4, multi_file: 4, risk: 3, debug_rca: 3, tradeoff: 2, security: 2, performance: 1)

## How to Re-Measure

```bash
cd P:/.claude/hooks
python baselines/measure_cross_category_baseline.py
```

This will:
1. Measure all 4 metrics (M1, M2, M3, S1)
2. Generate updated JSON file
3. Print summary comparison to baseline

## Monitoring Queries

### M1: Cross-Category Usage Rate
```sql
SELECT
    COUNT(*) FILTER (WHERE json_extract(detection_result, '$.compatible_combinations') IS NOT NULL) * 100.0 / COUNT(*) as usage_percent
FROM detection_metrics
WHERE timestamp > datetime('now', '-7 days');
```

### M2: Performance Overhead
```sql
SELECT
    AVG(detection_latency_ms) as avg_ms,
    percentile_cont(0.95) WITHIN GROUP (ORDER BY detection_latency_ms) as p95_ms
FROM performance_metrics
WHERE timestamp > datetime('now', '-7 days');
```

### M3: Matrix Entry Count
```python
# Python
from UserPromptSubmit_modules.unified_detection import _COMPATIBILITY_MATRIX
print(f"Total entries: {len(_COMPATIBILITY_MATRIX)}")
```

### S1: CKS Query Rate
```sql
SELECT
    COUNT(*) * 1.0 / 7 as queries_per_day
FROM detection_metrics
WHERE detection_system LIKE '%cks%'
AND timestamp > datetime('now', '-7 days');
```

## Success Criteria

- ✅ M1: 0% baseline (not deployed yet)
- ✅ M2: <5ms (currently 0.001ms)
- ✅ M3: <50 entries (currently 19)
- ⏸️ S1: Baseline unavailable (system not initialized)

## Files

- **Measurement Script**: `baselines/measure_cross_category_baseline.py`
- **Baseline Data**: `baselines/cross_category_baseline_20260315.json`
- **Full Report**: `baselines/TASK-008_BASELINE_REPORT.md`
- **Implementation**: `UserPromptSubmit_modules/unified_detection.py`

## Post-Deployment Checklist

- [ ] Deploy 3D matrix to production
- [ ] Wait 7 days for data collection
- [ ] Re-run baseline measurement script
- [ ] Compare M1 adoption rate (target: 15%)
- [ ] Validate M2 performance (target: <5ms)
- [ ] Calculate S1 reduction (target: -20%)
- [ ] Update matrix entries based on usage patterns
