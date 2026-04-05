# CLI Usage Reference

Complete CLI command reference for `pwm` (perplexity-web-mcp-cli).

## Querying

```bash
pwm ask "What is quantum computing?"
```

Choose a specific model with `-m`:
```bash
pwm ask "Compare React and Vue" -m gpt54
pwm ask "Explain attention mechanism" -m claude_sonnet
```

Enable extended thinking with `-t`:
```bash
pwm ask "Prove sqrt(2) is irrational" -m claude_sonnet --thinking
```

Focus on specific sources with `-s`:
```bash
pwm ask "review this code for bugs" -s none            # Model only, no web search
pwm ask "transformer improvements 2025" -s academic   # Scholarly papers
pwm ask "best mechanical keyboard" -s social           # Reddit/Twitter
pwm ask "Apple revenue Q4 2025" -s finance             # SEC EDGAR filings
pwm ask "latest AI news" -s all                        # All sources
```

Output options:
```bash
pwm ask "What is Rust?" --json            # JSON (for piping)
pwm ask "What is Rust?" --no-citations    # Answer only, no URLs
```

Combine flags:
```bash
pwm ask "protein folding advances" -m gemini_pro -s academic --json
```

## Deep Research

Uses a separate monthly quota. Produces in-depth reports with extensive sources.

```bash
pwm research "agentic AI trends 2026"
pwm research "climate policy impact" -s academic
pwm research "NVIDIA competitive landscape" -s finance --json
```

## Authentication

```bash
pwm login                                                # Interactive
pwm login --check                                        # Check status
pwm login --email user@example.com                       # Send code
pwm login --email user@example.com --code 123456         # Complete
```

## Usage

```bash
pwm usage                   # Cached limits
pwm usage --refresh         # Force-refresh from server
```

## Common Patterns

### Quick web search
```bash
pwm ask "What happened in AI today?"
```

### Model-only query (no web search)
```bash
pwm ask "Explain the visitor pattern in OOP" -s none
pwm ask "Write a Python decorator for retry logic" -m claude_sonnet -s none
```

### Specific model
```bash
pwm ask "Compare React and Vue" -m gpt54
```

### Model with thinking
```bash
pwm ask "Prove sqrt(2) is irrational" -m claude_sonnet -t
```

### Academic research
```bash
pwm ask "transformer improvements 2025" -m gemini_pro -s academic
```

### Financial analysis
```bash
pwm ask "Apple revenue Q4 2025" -s finance
```

### Launch Claude Code seamlessly (Integration)
```bash
pwm hack claude
```

### Deep research pipeline
```bash
pwm research "quantum computing breakthroughs 2026" --json > research.json
```

### Check everything before heavy use
```bash
pwm login --check && pwm usage
```

### Re-authenticate (non-interactive, for AI agents)
```bash
pwm login --email user@example.com
# wait for email, then:
pwm login --email user@example.com --code 123456
```
