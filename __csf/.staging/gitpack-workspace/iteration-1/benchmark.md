# Skill Benchmark: gitpack

**Model**: claude-sonnet-4-6
**Date**: 2026-04-21T23:05:28Z
**Evals**: 0 (local-dir), 1 (remote-repo), 2 (full-fidelity) (1 run each per configuration)

## Summary

| Metric | With Skill | Without Skill | Delta |
|--------|------------|---------------|-------|
| Pass Rate | 100% ± 0% | 80% ± 20% | +0.20 |
| Time | 418.3s ± 70.3s | 782.3s ± 399.3s | -364.0s |
| Tokens | 0 ± 0 | 0 ± 0 | +0 |

## Per-Eval Breakdown

| Eval | With Skill | Without Skill | Time (with) | Time (without) |
|------|-----------|---------------|-------------|----------------|
| local-dir | 5/5 (100%) | 4/5 (80%) | 481.5s | 595.1s |
| remote-repo | 5/5 (100%) | 3/5 (60%) | 432.1s | 480.7s |
| full-fidelity | 5/5 (100%) | 5/5 (100%) | 341.2s | 1271.2s |

## Analyst Notes

- **Discriminating evals**: local-dir and remote-repo clearly differentiate skill from baseline
- **Non-discriminating**: full-fidelity passes 5/5 for both, but time delta is extreme (3.7x faster with skill)
- **Remote repo gap**: Baseline failed to clone GitHub repo (read files via web tools instead) and didn't clean up — produces analysis summary, not distilled code
- **Local dir gap**: Baseline discovered aid MCP tools but didn't achieve compression (0% vs 93%)
- **Time variance**: Baseline shows high variance (stddev 399s) driven by full-fidelity outlier at 1271s
