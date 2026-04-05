# Development Intelligence Integration for dualllm-v2

## Pre-Task Intelligence Check
```bash
# Search memory bank for relevant patterns
python ..\.brain/memory_bank/tools/search_engine.py "your-topic" --projects dualllm-v2

# Check for related issues
python ..\.brain/tools/intelligence_search.py --project dualllm-v2 --query "your-topic"

# Look for cross-project insights
python ..\.brain/memory_bank/tools/search_engine.py "your-topic" --tags cross-project
```

## During Work
- **Document insights** that meet memory bank criteria
- **Reference related issues** and memory entries
- **Note cross-project applications** of your solutions

## Post-Task Intelligence Update
```bash
# Check if issue should create memory entry
python ..\.brain/integration/memory_issue_bridge.py suggest --project dualllm-v2 --issue-id your-issue-id

# Create memory entry if significant insights
python ..\.brain/memory_bank/tools/memory_manager.py create --type lesson_learned --title "Your Insight" --projects dualllm-v2 --tags relevant,tags --llm-id your-id

# Link memory entry and issue
python ..\.brain/integration/memory_issue_bridge.py link --project dualllm-v2 --issue-id your-issue-id --memory-id memory-entry-id
```

## dualllm-v2 Specific Guidelines
- Always include `dualllm-v2` tag in memory entries
- Add domain-specific tags relevant to this project
- Check for cross-project patterns that could apply here
- Link to related issues when creating memory entries

## Intelligence Decision Criteria
- ✅ Non-obvious solutions that took effort to discover
- ✅ Patterns that could apply to other projects
- ✅ Important decisions and their reasoning
- ✅ Performance insights and optimizations
- ❌ Routine operations and basic syntax
- ❌ Well-documented features from official docs
