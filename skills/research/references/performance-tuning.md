# Performance Tuning

## For faster searches (priority: speed)

```bash
# Local-only mode (no web APIs)
/all "query" --mode local-only

# Disable Layer 2
/all "query" --no-context-filter

# Lower result limit
/all "query" --limit 20

# Skip web search even if local quality is low
/all "query" --mode local-only --min-score 0.3
```

**Expected performance:**
- Local-only: <1 second
- With Layer 2: +0.05-0.1 ms overhead
- No web APIs: 5-10 seconds saved

---

## For comprehensive results (priority: coverage)

```bash
# Force Layer 2 distillation
/all "query" --force-context-filter

# Increase result limit
/all "query" --limit 40

# Lower quality threshold
/all "query" --min-score 0.3 --min-results 5

# Unified mode (always search both sources)
/all "query" --mode unified
```

**Expected performance:**
- Layer 2: 0.05-0.1 ms overhead
- Tokens: 2000-4000 (well under 8000 limit)
- Web search: 5-10 seconds (if enabled)

