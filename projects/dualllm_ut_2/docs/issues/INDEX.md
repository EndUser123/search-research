# Project Issues & Changes Index (dualllm-v2)

| ID  | Type    | Status      | Description           | Assigned To |
|-----|---------|-------------|-----------------------|-------------|

## Issue Types
- **bug** - Something that's broken and needs fixing
- **feature** - New functionality to implement
- **change** - Modification to existing functionality
- **task** - General work item or maintenance
- **research** - Investigation or analysis needed

## Status Options
- **open** - Ready to work on
- **in_progress** - Currently being worked on
- **resolved** - Work completed, awaiting verification
- **closed** - Verified complete
- **blocked** - Cannot proceed due to dependencies

## Integration with Development Intelligence
- **Memory Bank**: Significant issue resolutions should create memory bank entries
- **Cross-Project**: Tag issues that might have cross-project implications
- **Pattern Recognition**: Look for patterns across issues that could become memory entries

## Quick Commands
```bash
# Search for related memory bank entries
python ../dev_intelligence/memory_bank/tools/search_engine.py "issue-topic" --projects dualllm-v2

# Suggest memory bank entry from issue
python ../dev_intelligence/integration/memory_issue_bridge.py suggest --project dualllm-v2 --issue-id issue-id

# Find related intelligence
python ../dev_intelligence/tools/intelligence_search.py --project dualllm-v2 --query "issue-topic"
```
