# 4-Layer Filter System Integration

**/ai-cli integrates Layer 4 (Quality Gate) from /v's validation pipeline.**

## What is the 4-Layer Filter System?

From `/v` (Sequential Validation Pipeline), the 4-layer filtering system removes false positives from adversarial findings:

| Layer | Function | Type | Description |
|-------|----------|------|-------------|
| **Layer 1** | Change Delta Gate | Python module | Filters to changed files only |
| **Layer 2** | Architectural Pillar Enforcer | Python module | Filters against architectural pillars |
| **Layer 3** | Aggregation | Python module | Deduplicates findings across agents |
| **Layer 4** | Quality Gate | Subagent | Filters by confidence >= 80% |

## How /ai-cli Uses Layer 4

When `--quality-gate` is enabled (or `LLM_CLI_QUALITY_GATE=true`):

1. **Extract findings** from all LLM outputs (qwen, gemini, codex, vibe, opencode, glm)
2. **Apply confidence filter** (>= 80%) - removes low-confidence findings
3. **Return filtered results** - only high-confidence findings shown

**Benefits:**
- Reduces false positives from LLM hallucinations
- Focuses on high-confidence, actionable findings
- Consistent with /v's validation methodology

## Usage

```bash
# Enable via flag
/ai-cli "review this code" --context file.py --quality-gate

# Enable globally via environment variable
export LLM_CLI_QUALITY_GATE=true  # Linux/Mac
set LLM_CLI_QUALITY_GATE=true     # Windows
```

## Output

```
[Quality Gate Layer 4] Input: 15 findings, Output: 8 findings (>= 80% confidence)
```
