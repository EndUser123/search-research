# Examples — /ai-pcli Invocation Patterns

## Basic Usage

```bash
/ai-pcli "What does this function do?" --context P:\path\to\file.py
```

## Output Modes

| Flag | Effect |
|------|--------|
| `--summary` | Brief key answers only |
| `--complete` | Full raw outputs from all CLIs |
| `--diff` | Side-by-side diff between CLI responses |
| `--quality-weighted` | Quality-weighted output with consensus analysis |
| `--aggregate` | Consensus view showing agreement/disagreement |

## Single-CLI Targeting

```bash
/ai-pcli "review /path/to/file.py" --gemini-only
/ai-pcli "review /path/to/file.py" --codex-only
/ai-pcli "review /path/to/file.py" --opencode-only
/ai-pcli "explain this code" --pi-model deepseek-v4-flash
```

## Config Query

```bash
/ai-pcli config
```
Displays saved recipe from `P:/.data/ai-pcli-recipe.json` (falls back to `ai-cli-recipe.json`).

## Timeout Override

```bash
/ai-pcli "long analysis task" --timeout 300
```
Default: 180s base + 1s per MB of context.

## JSON Output

```bash
/ai-pcli "review /path/to/file.py" --output-format json --output-file review.json
```
Saves datetime-suffixed JSON output with tiered YAML reports.

## Prompt Enhancement

```bash
/ai-pcli "review /path/to/file.py" --prompt-toolkit
```
Uses prompting-toolkit AutomaticEnhancementSystem instead of built-in templates.

```bash
/ai-pcli "review /path/to/file.py" --doc-review
```
Prepends document review questions to the prompt.

```bash
/ai-pcli "review /path/to/file.py" --hide-prompt
```
Suppresses the enhanced prompt display (shown by default).

## Routing

```bash
/ai-pcli "fix the null pointer" --route
```
Uses rule-based routing (from llm-route) to select CLI by task keywords.

## Quality-Weighted Output

```bash
/ai-pcli "review /path/to/file.py" --quality-weighted
```
Task-type-aware quality scoring with parallel subagent analysis. For code_review tasks:
- Structured responses score higher
- Evidence citations add bonus points
- CLI quality scores shown with framing/evidence/step markers
- Per-CLI subagent analysis extracts findings and validates citations
- Only runs subagent analysis on outputs >= 2KB (skips small outputs)

## Diff with Structural Comparison

```bash
/ai-pcli "review /path/to/file.py" --diff
```
Shows response differences with:
- Per-response structural markers (framing, steps, evidence)
- CLI approach comparison table
- Disagreement/consensus indicators

## Debug

```bash
/ai-pcli "review /path/to/file.py" -bash
```
Shows bash commands without executing (dry run).