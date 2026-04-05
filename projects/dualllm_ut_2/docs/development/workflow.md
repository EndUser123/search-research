# dualllm-v2 Development Workflow

## Development Intelligence Integration

This project uses the unified Development Intelligence system for knowledge management, issue tracking, and AI-assisted development.

### Before Starting Work
1. **Search intelligence systems** for relevant knowledge
2. **Check for related issues** and their resolutions
3. **Review memory bank** for applicable patterns

```bash
# Comprehensive intelligence search
python ..\.brain/tools/intelligence_search.py --project dualllm-v2 --query "your-topic"

# Memory bank search
python ..\.brain/memory_bank/tools/search_engine.py "your-topic" --projects dualllm-v2
```

### During Development
1. **Follow AI-assisted development guides** in `..\.brain/development/guides/`
2. **Document significant insights** as you discover them
3. **Reference related issues** and memory entries in your work
4. **Note cross-project applications** of your solutions

### After Completing Work
1. **Resolve issues** with detailed resolution notes
2. **Check for memory-worthy insights** using the bridge tool
3. **Create memory entries** for significant lessons learned
4. **Link issues and memory entries** bidirectionally

```bash
# Check if issue should create memory entry
python ..\.brain/integration/memory_issue_bridge.py suggest --project dualllm-v2 --issue-id your-issue-id

# Create memory entry if significant
python ..\.brain/memory_bank/tools/memory_manager.py create --type lesson_learned --title "Your Insight" --projects dualllm-v2 --tags relevant,tags --llm-id your-id
```

## dualllm-v2 Specific Guidelines

### Memory Bank Tags
- `dualllm-v2` (always include)
- Add domain-specific tags relevant to your project area
- Use `cross-project` for insights that apply broadly

### Issue Management
- Reference memory bank entries in issue resolutions
- Tag issues that might have cross-project implications
- Create memory entries for significant issue resolutions

### Quality Standards
- Follow development guides in `..\.brain/development/guides/`
- Use AI-assisted testing approaches from `..\.brain/development/standards/`
- Maintain integration with development intelligence systems

## Quick Reference

### Intelligence Search
```bash
python ..\.brain/tools/intelligence_search.py --project dualllm-v2 --query "topic"
```

### Memory Bank Operations
```bash
python ..\.brain/memory_bank/tools/search_engine.py "query" --projects dualllm-v2
python ..\.brain/memory_bank/tools/memory_manager.py create --type lesson_learned --title "Title" --projects dualllm-v2 --tags tag1,tag2 --llm-id your-id
```

### Issue-Memory Bridge
```bash
python ..\.brain/integration/memory_issue_bridge.py suggest --project dualllm-v2 --issue-id issue-id
python ..\.brain/integration/memory_issue_bridge.py link --project dualllm-v2 --issue-id issue-id --memory-id memory-id
```
