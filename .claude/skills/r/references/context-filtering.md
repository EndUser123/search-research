# Context-Aware Filtering (Step 15.5)

**CRITICAL:** After collecting all findings (from deterministic checks, CKS queries, AID passes), apply solo-dev context filter to remove enterprise-style findings.

## Context Filter Implementation

```python
from pathlib import Path
import yaml

def apply_context_filter_to_all_findings(forgotten_items, deterministic_improvements, solo_dev_violations):
    """Filter all collected findings against .claude/config/solo-dev-context.yaml"""
    context_path = Path('.claude/config/solo-dev-context.yaml')

    # If no context file exists, return findings unchanged (backward compatible)
    if not context_path.exists():
        return forgotten_items, deterministic_improvements, solo_dev_violations

    try:
        with open(context_path) as f:
            context = yaml.safe_load(f)

        forbidden = context.get('constraints', {}).get('forbidden', [])

        def filter_list(items, list_name):
            filtered = []
            count = 0
            for item in items:
                # Check if item contains any forbidden pattern
                item_text = str(item.get('description', '')).lower()
                if any(pattern in item_text for pattern in forbidden):
                    count += 1
                else:
                    filtered.append(item)
            if count > 0:
                print(f"[Context Filter] Removed {count} {list_name} not applicable to solo-dev")
            return filtered

        # Apply filter to each finding category
        filtered_forgotten = filter_list(forgotten_items, "forgotten items")
        filtered_improvements = filter_list(deterministic_improvements, "improvements")
        filtered_violations = filter_list(solo_dev_violations, "violations")

        return filtered_forgotten, filtered_improvements, filtered_violations

    except Exception as e:
        # Fallback-safe: if filtering fails, return original findings
        print(f"[Context Filter] Failed: {e}. Using all findings.")
        return forgotten_items, deterministic_improvements, solo_dev_violations

# Apply to all collected findings before generating output
forgotten_items, deterministic_improvements, solo_dev_violations = \
    apply_context_filter_to_all_findings(forgotten_items, deterministic_improvements, solo_dev_violations)
```

## Filtering Behavior

- **Backward Compatible:** If `.claude/config/solo-dev-context.yaml` doesn't exist, no filtering occurs
- **Graceful Degradation:** If YAML parsing fails, all findings pass through with warning
- **Transparent:** Reports how many findings were filtered per category

## Categories Filtered

- `forgotten_items` - Omissions that include enterprise patterns
- `deterministic_improvements` - Suggestions that involve team/enterprise workflows
- `solo_dev_violations` - Normally filtered through SLC checks, double-filtered here

## Metrics Logging (Optional Enhancement)

Track filter statistics to CKS for data-driven pattern refinement:

```python
def log_r_filter_statistics(original_counts, filtered_counts, context_file_path):
    """Log /r filter statistics to CKS for metrics tracking"""
    try:
        from cks.migrations.create_findings_table import upsert_finding
        import yaml
        from datetime import datetime
        import uuid

        session_id = str(uuid.uuid4())[:8]  # Short session ID

        # Load context to get patterns for metadata
        with open(context_file_path) as f:
            context = yaml.safe_load(f)

        forbidden_patterns = context.get('constraints', {}).get('forbidden', [])

        # Calculate totals
        total_original = sum(original_counts.values())
        total_filtered = sum(filtered_counts.values())

        upsert_finding(
            finding_type="METADATA",  # Metadata, not a code issue
            source="context_filter_r",
            message=f"/r filter: {total_filtered}/{total_original} findings removed ({total_filtered/total_original*100:.1f}%)",
            severity="low",  # Informational only
            metadata={
                'session_id': session_id,
                'timestamp': datetime.now().isoformat(),
                'forbidden_pattern_count': len(forbidden_patterns),
                'filter_ratio': total_filtered / total_original if total_original > 0 else 0,
                'total_findings': total_original,
                'filtered_findings': total_filtered,
                'by_category': {
                    'forgotten_items': {
                        'original': original_counts.get('forgotten_items', 0),
                        'filtered': filtered_counts.get('forgotten_items', 0)
                    },
                    'deterministic_improvements': {
                        'original': original_counts.get('deterministic_improvements', 0),
                        'filtered': filtered_counts.get('deterministic_improvements', 0)
                    },
                    'solo_dev_violations': {
                        'original': original_counts.get('solo_dev_violations', 0),
                        'filtered': filtered_counts.get('solo_dev_violations', 0)
                    }
                }
            }
        )
    except Exception as e:
        # Optional enhancement - don't break workflow if logging fails
        print(f"[15.5] Filter statistics logging unavailable: {e}")

# Track counts before filtering
original_counts = {
    'forgotten_items': len(forgotten_items),
    'deterministic_improvements': len(deterministic_improvements),
    'solo_dev_violations': len(solo_dev_violations)
}

# Apply filter (from code above)
forgotten_items, deterministic_improvements, solo_dev_violations = \
    apply_context_filter_to_all_findings(forgotten_items, deterministic_improvements, solo_dev_violations)

# Track counts after filtering
filtered_counts = {
    'forgotten_items': len(forgotten_items),
    'deterministic_improvements': len(deterministic_improvements),
    'solo_dev_violations': len(solo_dev_violations)
}

# Calculate actual filtered amounts
actual_filtered = {
    'forgotten_items': original_counts['forgotten_items'] - filtered_counts['forgotten_items'],
    'deterministic_improvements': original_counts['deterministic_improvements'] - filtered_counts['deterministic_improvements'],
    'solo_dev_violations': original_counts['solo_dev_violations'] - filtered_counts['solo_dev_violations']
}

# Log the statistics if file existed
if context_path.exists():
    log_r_filter_statistics(original_counts, actual_filtered, context_path)
```
