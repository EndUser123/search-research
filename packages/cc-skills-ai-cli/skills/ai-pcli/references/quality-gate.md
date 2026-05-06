# Quality Gate — 4-Layer Filter System Integration

## Overview

`/ai-pcli` integrates with the 4-Layer Filter System (from the cc-skills-sdlc package) to validate LLM outputs before aggregation.

## Layer 4: Confidence Threshold

Use `--quality-gate` to filter findings by confidence >= 80%:

```bash
/ai-pcli "review /path/to/file.py" --quality-gate
```

This applies Layer 4 filtering to the aggregated output, suppressing low-confidence findings.

## Filter System Layers

| Layer | Focus | Applied By |
|-------|-------|------------|
| Layer 1 | Fact extraction | `_extract_text_findings_all()` |
| Layer 2 | Pattern classification | `ai_cli.py` aggregation |
| Layer 3 | Structural validation | `_process_llm_results()` |
| Layer 4 | Confidence threshold | `--quality-gate` flag |

## Quality-Weighted Output

For outputs with evidence validation and consensus analysis:

```bash
/ai-pcli "review /path/to/file.py" --quality-weighted
```

This weights each model's contribution by its reliability score and cross-references claims against available evidence.

## Aggregate Mode

Show agreement and disagreement across models:

```bash
/ai-pcli "review /path/to/file.py" --aggregate
```

Highlights where models consensus vs diverge, helping identify high-confidence consensus vs contested claims.

## Post-Run Critic

The `ai-cli-critic` subagent (run by default unless `--no-critic`) checks the combined output for:
- Unsupported claims
- Contradictions between models
- Overconfidence in low-evidence findings
- Missing evidence for critical claims