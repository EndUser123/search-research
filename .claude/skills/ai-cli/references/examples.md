# Example Invocations

## Basic Usage

```bash
# Basic query (runs 5 CLIs by default, or 6 if ZAI_API_KEY is set)
python "P:\.claude\skills\ai-cli\ai_cli.py" "what is 12 + 12?"

# With file context (RECOMMENDED for investigations)
python "P:\.claude\skills\ai-cli\ai_cli.py" "investigate the bypass" --context path/to/hook.py

# With target flag (filters session context to specific file)
python "P:\.claude\skills\ai-cli\ai_cli.py" "investigate this issue" --target path/to/file.py
```

## Output Modes

```bash
# Get consensus view
python "P:\.claude\skills\ai-cli\ai_cli.py" "explain recursion" --aggregate

# JSON output
python "P:\.claude\skills\ai-cli\ai_cli.py" "explain" --output-format json
```

## Specific LLMs

```bash
# Specific LLM only
python "P:\.claude\skills\ai-cli\ai_cli.py" "debug this" --qwen-only

# GLM-4.7-Flash only
python "P:\.claude\skills\ai-cli\ai_cli.py" "explain" --glm-flash-only

# OpenCode with model alias (Kimi K2.5 - 256K context)
python "P:\.claude\skills\ai-cli\ai_cli.py" "analyze this codebase" --opencode-model kimi

# OpenCode with model alias (MiniMax M2.1 - SOTA coding)
python "P:\.claude\skills\ai-cli\ai_cli.py" "review this code" --opencode-model minimax
```

## Advanced

```bash
# With 4-Layer Filter System (Quality Gate)
python "P:\.claude\skills\ai-cli\ai_cli.py" "review this code" --context file.py --quality-gate

# Use rule-based routing (from llm-route)
python "P:\.claude\skills\ai-cli\ai_cli.py" "implement REST API" --route

# Document review mode (from llm-doc_review)
python "P:\.claude\skills\ai-cli\ai_cli.py "review this document" --doc-review --context README.md

# Enable Quality Gate globally via environment variable
set LLM_CLI_QUALITY_GATE=true
/ai-cli "investigate this" --context file.py  # Quality gate applied automatically
```
