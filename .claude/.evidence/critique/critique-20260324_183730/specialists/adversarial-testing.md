# Adversarial Testing Review: next_steps_formatter.py

## Focus
Functions: `_detect_batch_groups()` (lines 347-494) and `format_rsn_from_gaps()` (lines 497-528)

---

## FINDING: TEST-001 — Severity Case Mismatch Causes All Batches to Report LOW Severity

**Severity:** HIGH

**File:** `P:/.claude/skills/gto/lib/next_steps_formatter.py`

**Lines:** 388-390, 445-447

**Function:** `_detect_batch_groups()`

### Description

`_detect_batch_groups()` uses an uppercase-keyed `severity_order` dict, but `Gap` dataclass (`results_builder.py:31`) produces lowercase severity values: `"critical"`, `"high"`, `"medium"`, `"low"`. The `min()` call with `key=lambda s: severity_order.get(s, 99)` always returns `99` for every severity, making `aggregate_severity` always resolve to `"LOW"` regardless of actual batch contents.

### Evidence

```python
# Line 388-390 — Strategy 1 batch severity aggregation
severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}  # UPPERCASE KEYS
severities = [g.get("severity", "LOW") for g in batch_gaps]
# If severities == ["high", "medium"], all get() calls return 99
aggregate_severity = min(severities, key=lambda s: severity_order.get(s, 99))
# Result: "LOW" because all fall through to default 99
```

Same pattern at line 445-447 for Strategy 2 (`# type: ignore`) batches.

```python
# results_builder.py:31 — Gap dataclass uses lowercase
severity: str  # defaults to "medium", values are "critical", "high", "medium", "low"
```

### Impact

- **Business consequence:** Batches of CRITICAL-severity gaps are displayed as LOW, suppressing urgent findings
- **Customer visible:** Yes — RSN output shows wrong severity for all batched findings

### Recommendation

Normalize severity to uppercase before lookup:
```python
severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
severities = [g.get("severity", "LOW").upper() for g in batch_gaps]
aggregate_severity = min(severities, key=lambda s: severity_order.get(s, 99))
```

Or use the same lowercase-keyed `PRIORITY_ORDER` that `NextStepsFormatter.format()` uses:
```python
PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}
```

### Confidence: HIGH

---

## FINDING: TEST-002 — Zero Test Coverage for `_detect_batch_groups()` and `format_rsn_from_gaps()`

**Severity:** HIGH

**File:** `P:/.claude/skills/gto/tests/lib/test_next_steps_formatter.py`

**Lines:** 1-66 (entire file)

### Description

The existing test file contains only smoke tests: one for formatter instantiation and one for empty gap list formatting. Neither `_detect_batch_groups()` (the core batch detection logic with 3 strategies) nor `format_rsn_from_gaps()` (the public RSN bridge function) is exercised at all.

The test file imports `next_steps_formatter` but only tests `NextStepsFormatter` and `format_recommended_next_steps`, not the GTO-specific functions added at lines 347-528.

### Evidence

```python
# test_next_steps_formatter.py — only tests existing formatter, not the new GTO functions
from lib.next_steps_formatter import (
    FormattedNextSteps,
    NextStep,
    NextStepsFormatter,
    format_recommended_next_steps,  # Only this is tested
)
# _detect_batch_groups and format_rsn_from_gaps are NOT imported or tested
```

What is NOT tested:
1. Strategy 1 (location batching with 70% effort multiplier)
2. Strategy 2 (`# type: ignore` batching with 50% effort multiplier)
3. Strategy 3 (individual gap passthrough)
4. Severity aggregation in batch groups
5. `format_rsn_from_gaps()` end-to-end with `RSNFormatter`

### Impact

**Business consequence:** Any regression in batch detection (e.g., severity case mismatch, strategy application order, effort multiplier) will not be caught. The severity case mismatch (TEST-001) is currently undetected precisely because there are no tests.

### Recommendation

Add tests for:
```python
def test_detect_batch_groups_strategy1_same_location():
    """Two gaps at same (file_path, line_number) should batch with 70% effort."""
    gaps = [
        {"id": "G1", "file_path": "foo.py", "line_number": 10, "severity": "high",
         "message": "Issue 1", "effort_estimate_minutes": 10},
        {"id": "G2", "file_path": "foo.py", "line_number": 10, "severity": "critical",
         "message": "Issue 2", "effort_estimate_minutes": 10},
    ]
    results = _detect_batch_groups(gaps)
    assert len(results) == 1
    assert results[0]["is_batch"] == True
    assert results[0]["batch_count"] == 2
    assert results[0]["severity"] == "CRITICAL"  # Would fail with current code
    assert results[0]["effort_minutes"] == 14    # 20 * 0.7 = 14

def test_detect_batch_groups_strategy2_type_ignore():
    """Multiple # type: ignore gaps should batch with 50% effort."""
    gaps = [
        {"id": "G1", "message": "# type: ignore [unused-import] missing 'requests'", "severity": "high"},
        {"id": "G2", "message": "# type: ignore [unused-import] missing 'requests'", "severity": "medium"},
    ]
    results = _detect_batch_groups(gaps)
    # ...

def test_format_rsn_from_gaps_end_to_end():
    """format_rsn_from_gaps should produce RSN text with batched findings."""
    gaps = [...]
    output = format_rsn_from_gaps(gaps, intent_summary="test")
    assert "Recommended Next Steps" in output
    # ...
```

### Confidence: HIGH

---

## FINDING: TEST-003 — Batch ID Format Produces Malformed String When `line_number` Is None

**Severity:** MEDIUM

**File:** `P:/.claude/skills/gto/lib/next_steps_formatter.py`

**Lines:** 403, 407

### Description

At line 403, `file_ref` construction handles the `None` case:
```python
file_ref = f"{file_path}:{line_number}" if line_number else file_path
```
But at line 407, the batch `id` is built as:
```python
"id": f"BATCH-LOC-{file_path}:{line_number}",
```
When `line_number` is `None`, this produces `BATCH-LOC-foo.py:None` — a semantically misleading ID string that shows `None` as a line number.

### Evidence

```python
# Line 371-373 — None line_number produces None key
ln = gap.get("line_number")
key = (fp, ln)  # key = ("foo.py", None)
# Line 376 — When this group is processed:
# file_ref = "foo.py" (None case handled)
# but id = "BATCH-LOC-foo.py:None" (None NOT handled)
```

### Impact

- Malformed batch IDs appear in RSN output and downstream processing
- No functional breakage since the id is primarily for display/traceability

### Recommendation

Handle `None` in batch ID construction:
```python
"id": f"BATCH-LOC-{file_path}:{line_number if line_number else 'NOLINE'}",
```

### Confidence: MEDIUM

---

## FINDING: TEST-004 — Strategy 1 Batch Skips Partial Overlap Incorrectly

**Severity:** MEDIUM

**File:** `P:/.claude/skills/gto/lib/next_steps_formatter.py`

**Lines:** 376-380

### Description

When a location group has some (but not all) of its indices already used by a prior batch, the entire group is skipped. This means if indices `[0, 1, 2]` exist at a location, and a previous batch used index `0`, the remaining indices `1` and `2` are silently dropped — not batched, not even emitted as individual findings.

```python
for (file_path, line_number), indices in location_groups.items():
    if len(indices) < 2:
        continue
    if any(i in used_indices for i in indices):  # If ANY index used, skip ALL
        continue
```

### Impact

- Gaps are silently lost when their location overlaps with an already-batched gap
- For example: if 3 gaps exist at `foo.py:42` but one was already batched in a previous strategy, the other 2 are silently dropped

### Recommendation

Either process partial groups (batch the unused indices separately) or emit them as individual findings:
```python
if any(i in used_indices for i in indices):
    # Emit unused indices as individual findings instead of skipping
    unused = [i for i in indices if i not in used_indices]
    for i in unused:
        # emit as individual
```

### Confidence: MEDIUM

---

## FINDING: TEST-005 — Domain Routing Inconsistency Between `format()` and `format_rsn_from_gaps()`

**Severity:** LOW

**File:** `P:/.claude/skills/gto/lib/next_steps_formatter.py`

**Lines:** 413, 476-477

### Description

`_detect_batch_groups()` hardcodes `domain="code_quality"` for Strategy 1 batches (line 413) and `domain="import"` for Strategy 2 (line 460), regardless of the original gap types. Meanwhile, `NextStepsFormatter._map_category()` and `RSNFormatter._categorize_findings()` use the gap `type` to determine domain.

For GTO batches produced by `_detect_batch_groups()`, the domain is set to `"code_quality"` or `"import"` rather than the original gap type's domain. This means batched findings route to different RSN sections than equivalent non-batched findings.

### Evidence

```python
# Strategy 1 batch result (line 413)
"domain": "code_quality",  # Hardcoded, ignores original gap type

# GTO_TYPE_TO_RSN_DOMAIN mapping (line 327-333)
GTO_TYPE_TO_RSN_DOMAIN = {
    "test_gap": "test",
    "doc_gap": "docs",
    "code_quality": "quality",
    ...
}
```

A batch of `test_gap` gaps would route to `code_quality` section instead of `test` section.

### Impact

- Batched findings appear under different RSN sections than non-batched equivalents
- Mild user confusion about where findings appear

### Confidence: LOW

---

## FINDING: TEST-006 — `GapFinding.to_dict()` Missing `effort_estimate_minutes`

**Severity:** LOW

**File:** `P:/.claude/skills/gto/subagents/gap_finder_subagent.py`

**Lines:** 33-47

### Description

`GapFinding.to_dict()` (which produces the gap dicts passed to `_detect_batch_groups()`) does not include `effort_estimate_minutes`. The `GapFinding` dataclass itself has no `effort_estimate_minutes` field.

When `_detect_batch_groups()` calls `gap.get("effort_estimate_minutes", 5)`, it always gets the default of 5, regardless of actual effort.

Note: The `Gap` dataclass in `results_builder.py` does have `effort_estimate_minutes`, and the orchestrator sets it from `gap_data.get("effort_estimate_minutes", 5)` at `gto_orchestrator.py:202`. But `GapFinding` (the subagent output) doesn't populate this field.

### Impact

- `GapFinderSubagent` gaps always get 5-minute effort estimate when batched
- Only gaps processed through the orchestrator's `Gap` creation (line 193-205) get meaningful effort values

### Recommendation

Either add `effort_estimate_minutes` to `GapFinding` or add a mapping in the orchestrator that translates gap types to effort estimates before calling `_detect_batch_groups()`.

### Confidence: LOW

---

## Summary Table

| ID | Severity | Issue | Impact |
|----|----------|-------|--------|
| TEST-001 | HIGH | Severity case mismatch — all batches report LOW | Urgent findings suppressed in RSN |
| TEST-002 | HIGH | Zero test coverage for `_detect_batch_groups()` and `format_rsn_from_gaps()` | Regression risk; TEST-001 is undetected |
| TEST-003 | MEDIUM | Batch ID `BATCH-LOC-foo.py:None` when line_number is None | Malformed IDs in output |
| TEST-004 | MEDIUM | Partial location overlap silently drops gaps | Silent data loss in batch detection |
| TEST-005 | LOW | Domain hardcoded for batches vs. derived from gap type | Section routing inconsistency |
| TEST-006 | LOW | `GapFinding` missing `effort_estimate_minutes` | All subagent gaps get default 5-min effort |

---

## Coverage Assessment

**Existing test file:** `P:/.claude/skills/gto/tests/lib/test_next_steps_formatter.py`

| Function | Lines | Test Coverage |
|----------|-------|---------------|
| `NextStepsFormatter.format()` | 156-247 | Smoke test only |
| `NextStepsFormatter.format_markdown()` | 249-293 | None |
| `NextStepsFormatter._map_category()` | 93-102 | None |
| `NextStepsFormatter._format_step()` | 118-154 | None |
| `_detect_batch_groups()` | 347-494 | **None** |
| `format_rsn_from_gaps()` | 497-528 | **None** |
| `_format_effort()` | 104-116 | None |

**Critical path not tested:** `GapFinderSubagent` -> `Gap.to_dict()` -> `update_gap_recurrence()` -> `_detect_batch_groups()` -> `RSNFormatter` -> RSN text output.
