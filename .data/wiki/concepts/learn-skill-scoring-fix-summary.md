---
title: "/learn Skill Scoring Breakdown Fix - Summary"
created: 2026-04-10
tags:
  - learn-skill
  - fix
  - scoring
sources:
  - path: sources/other/learn_fix_summary.md
    mtime: "2026-04-09T09:23:39"
    type: file
summary: "Fixed /learn skill to display promised scoring breakdown. Implementation lost scoring details during extraction; solution returns ScoredLesson objects directly."
---

# /learn Skill Scoring Breakdown Fix - Summary

## Problem Identified

From the interrupted session in `reflect.txt`:

1. **Documentation promises scoring breakdown**: The `/learn` SKILL.md shows verbose output with individual dimension scores:
   ```
   Novelty: 2/2 (new to CKS)
   Complexity: 2/2 (RCA required)
   Pattern: 2/2 (repeatable)
   Impact: 1/2 (saves time)
   Total: 7/8 ✓ STORE
   ```

2. **Implementation lost scoring details**: The `lesson_extractor.py` had `ScoredLesson` class with full scoring, but the `extract()` method returned simplified `Lesson` objects (only lesson, category, confidence).

3. **Result**: The `/learn` skill couldn't display the promised scoring breakdown because the details were discarded during extraction.

## Root Cause

In `lesson_extractor.py:extract()` method:
- Created `ScoredLesson` objects with full scoring (line 563-570)
- But then converted them back to `Lesson` objects before returning (lines 763-776)
- This discarded all the scoring details

## Solution Implemented

### 1. Updated `lesson_extractor.py`
- Changed `extract()` return type from `List[Lesson]` to `List[ScoredLesson]`
- Removed the conversion step that created `Lesson` objects
- Now returns `ScoredLesson` objects directly with full scoring breakdown

### 2. Updated `retrospective_common.py`
- Added `ScoredLesson` import
- Updated `ExtractionResult` dataclass to use `List[ScoredLesson]`
- Fixed display logic to handle both `ScoredLesson` and legacy `Lesson` objects
- Removed unused `text_lower` variable (linter warning)

### 3. Verified Integration
- The verbose mode display logic already existed (lines 572-575)
- It checks for `lesson.novelty`, `lesson.complexity`, etc. attributes
- Now works correctly with `ScoredLesson` objects

## Test Results

```
Extracted 2 lessons
Type: ScoredLesson
Score: 4/8 (novelty=1, complexity=1, pattern=1, impact=1)
```

## What's Now Possible

With `--verbose` flag, `/learn` will now show:
```
/learn --verbose

Candidate: "Terminal detection path mismatch"
  Novelty: 2/2 (new to CKS)
  Complexity: 2/2 (RCA required)
  Pattern: 2/2 (repeatable)
  Impact: 1/2 (saves time)
  Total: 7/8 ✓ STORE
```

## Next Steps

1. Test `/learn --verbose` with a real transcript
2. Update documentation if needed (SKILL.md already shows correct format)
3. Consider updating the `/learn` skill to use verbose mode by default or add a `--scoring` flag

## Files Modified

1. `P:/__csf/src/core/lesson_extractor.py`
   - `extract()` now returns `List[ScoredLesson]` instead of `List[Lesson]`
   - Removed conversion step that discarded scoring details

2. `P:/__csf/src/core/retrospective_common.py`
   - Added `ScoredLesson` import
   - Updated `ExtractionResult` to use `List[ScoredLesson]`
   - Fixed display logic to handle `ScoredLesson` objects
   - Removed unused `text_lower` variable

## Related
