# Investigation Intent Implementation Summary

## Problem

When users asked about "errors from today regarding /s usage", the search system would:
- Search only code/files/hooks (web sources default)
- Not automatically search chat history (CHS) or conversation transcripts
- Require manual flags (`--source chat --source all --time-filter today`)
- Force users to be backend experts instead of natural language

**Root cause:** Missing "investigation" intent type that triggers comprehensive search.

## Solution

Added "investigation" intent detection with automatic comprehensive backend search.

### Changes Made

#### 1. `query_intent.py` - Added Investigation Intent Type

**File:** `P:/__csf/src/knowledge/search/query_intent.py`

**Changes:**
- Added `QueryIntent.INVESTIGATION` to enum
- Added investigation trigger patterns:
  - Temporal: "errors from today", "issues from yesterday", "problems from this week"
  - Investigation keywords: "what happened", "what went wrong", "friction", "stuck", "broken"
  - Debug keywords: "investigate", "diagnose", "debugging"
- Mapped investigation intent to all backends: `["CHS", "CKS", "CDS", "GREP", "DOCS", "SKILLS"]`
- Priority order: INVESTIGATION > CHS > KNOWLEDGE > CODE > GREP

#### 2. `search_enhanced.py` - Auto-Apply Comprehensive Search

**File:** `P:/__csf/src/cli/nip/search_enhanced.py`

**Changes:**
- Import `QueryIntentDetector`
- Detect investigation intent before routing
- Auto-select all backends for investigation queries
- Auto-apply temporal filter ("today" = 24 hours) for time-based investigation queries
- Verbose output shows detected intent and actions

### Behavior

**Before:**
```bash
/search "errors from today regarding /s usage"
# Searched: CDS, GREP, CKS (web sources default)
# Missed: CHS (chat history), logs, transcripts
```

**After:**
```bash
/search "errors from today regarding /s usage"
# 🔍 Investigation intent detected - searching all backends
# Searching backends: CHS, CKS, CDS, GREP, SKILLS
# ⏰ Auto-detected temporal filter: today (24 hours)
```

### Investigation Trigger Patterns

The system automatically detects investigation intent from these patterns:

**Temporal + Error Keywords:**
- "errors from today"
- "issues from yesterday"
- "problems from this week"

**Investigation Keywords:**
- "what happened today"
- "what went wrong"
- "friction with /s"
- "stuck on task"

**Debugging Keywords:**
- "investigate authentication"
- "diagnose crash"
- "debugging slow request"

### Test Coverage

**File:** `P:/__csf/src/knowledge/search/tests/test_investigation_intent.py`

**Tests:**
- ✅ `test_errors_from_today_pattern` - Verifies "errors from today" triggers investigation
- ✅ `test_issues_from_yesterday` - Verifies temporal variants work
- ✅ `test_what_happened_today` - Verifies "what happened" patterns
- ✅ `test_friction_keyword` - Verifies "friction" keyword detection
- ✅ `test_investigation_backend_mapping` - Verifies all backends selected
- ✅ `test_non_investigation_query` - Ensures normal queries unchanged
- ✅ `test_code_query_remains_code` - Ensures code queries stay CODE intent

**Result:** All 7 tests pass ✅

## Impact

### User Experience
- **Before:** Users had to specify `--source all --source chat --time-filter today`
- **After:** Users just say "errors from today" - system figures out the rest

### Backend Priority for Investigation
1. **CHS** - Chat history (highest priority - what actually happened)
2. **CKS** - Knowledge base (known patterns, solutions)
3. **CDS** - Code documentation (API references)
4. **GREP** - Code patterns (function names, implementations)
5. **SKILLS** - Skill documentation

### Temporal Auto-Detection
- "today" → 24 hours
- "yesterday" → 48 hours
- "this week" → 168 hours
- "this month" → 720 hours
- No time keyword → defaults to "today" for investigation queries

## Reversibility

**Score:** 1.2 (Low risk, easy to revert)

**Rollback if needed:**
1. Remove `QueryIntent.INVESTIGATION` from enum
2. Remove investigation patterns from `_investigation_patterns`
3. Remove investigation mapping from `_intent_to_backends`
4. Remove intent detection logic from `search_enhanced.py`

## Future Enhancements

### Potential Improvements
1. **Learn from user feedback:** Add patterns that users try but don't work
2. **Smarter temporal detection:** "recent" → 1-3 days based on query context
3. **Backend priority tuning:** Adjust priority based on query type
4. **Multi-hop investigation:** Auto-suggest related queries ("What broke?", "When did it start?")

### Integration Points
- **/search skill:** Update SKILL.md with investigation intent examples
- **/rca skill:** Integrate investigation intent for RCA workflows
- **Hook alerts:** Auto-trigger investigation search on repeated failures

## Verification

To test the implementation:

```bash
# Test investigation intent
python P:/__csf/src/cli/nip/search_enhanced.py "errors from today" --verbose

# Test temporal detection
python P:/__csf/src/cli/nip/search_enhanced.py "what happened yesterday" --verbose

# Run tests
pytest P:/__csf/src/knowledge/search/tests/test_investigation_intent.py -v
```

## Principle Addressed

**"Find everything relevant to X" should be the default, not require explicit flags.**

This fix implements the principle that:
- User's natural language ("errors from today") should map to comprehensive search
- System should figure out which backends to search
- Temporal filtering should be auto-detected from query context
- Users shouldn't need to be backend experts to find what they need
