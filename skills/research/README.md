# Canonical research workflow

This directory owns the single implementation used by `/research` and the
compatibility wrapper `/all`. It contains the existing three-layer execution
surface plus the proven Phase 1 evidence path.

Run from the plugin root:

```bash
python -m skills.research.orchestration "question" --mode auto
```

`skills/all` contains compatibility entrypoints only; do not add research
logic there.
