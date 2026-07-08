---
name: chs-eval
description: Run golden-case retrieval evaluation against the CHS database and report per-case + mean recall
enforcement: strict
workflow_steps:
  - Parse arguments (--db, --min-recall, --mode, --cases)
  - Connect to CHS database
  - Load golden cases from JSONL
  - Run search for each case query
  - Compute per-case and mean recall
  - Print results table
  - Exit nonzero if mean recall below threshold
---
# CHS Golden-Case Evaluation (/chs-eval)

## Purpose

Runs the golden-case retrieval evaluation against the configured CHS database.
Reports per-case recall and mean recall. Exits nonzero when mean recall falls
below the threshold — suitable for CI and manual verification alike.

## Usage

```
/chs-eval                          # Uses default DB and golden_cases.jsonl
/chs-eval --db <path>              # Override DB path
/chs-eval --min-recall 0.8         # Set failure threshold (default: 0.8)
/chs-eval --mode fts               # FTS mode (default: fts)
```

## How it works

1. Connects to the CHS database (default: `P:/.data/chat_history.db`).
2. Loads golden cases from `core/chs/eval/golden_cases.jsonl` (or `--cases` override).
3. Runs `search_fts_messages` (FTS mode) or `search_semantic_sessions` (semantic mode)
   for each case query.
4. Computes recall@k per case: fraction of `required_session_keys` found in top-k results.
5. Prints per-case results and mean recall.
6. Exits with code 1 if mean recall < `--min-recall`.

## Output format

```
case                      recall  found  req  missing
case-001                   1.000      1    1  [PASS] -
case-002                   0.000      0    1  [MISS] abc123...

Cases: 26  perfect: 24  mean recall: 0.923
OK: mean recall 0.923 >= threshold 0.800
```

## Regenerating golden cases

The golden cases are generated from real chat history sessions:

```bash
python -m core.chs.eval.generate_golden_cases --db <path>
```

Re-run when the transcript corpus changes significantly.

## Files

- **Eval harness**: `core/chs/eval/retrieval_eval.py`
- **Golden cases**: `core/chs/eval/golden_cases.jsonl`
- **Generator**: `core/chs/eval/generate_golden_cases.py`
- **Status**: `core/chs/eval/DURABILITY_STATUS.md`
