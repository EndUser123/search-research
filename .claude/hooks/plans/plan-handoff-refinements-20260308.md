# Implementation Plan: Refined Per-Terminal Handoff System

**Date:** 2026-03-08
**Status:** READY-FOR-IMPLEMENTATION
**Priority:** HIGH
**Complexity:** MEDIUM
**Estimated Effort:** 7-9 hours

---

## Executive Summary

Implement refined per-terminal handoff system with three key improvements:
1. **Semantic `do_not_revisit` array** - Separate from decisions, captures settled/expensive constraints
2. **Improved `canonical_goal` extraction** - Work backwards from transcript end, skip meta-instructions and side-threads
3. **Deterministic checksums** - `sort_keys=True` for consistent serialization, hash `handoff_internal` only

These refinements improve session restoration quality by:
- Preventing reconsideration of settled architectural decisions
- Extracting the actual substantive task (not side questions)
- Ensuring checksum consistency across Python versions and terminals

---

## 1. Documentation Discovery

### Current Implementation Analysis

**Files Reviewed:**
- `P:\packages\handoff\src\handoff\hooks\PreCompact_handoff_capture.py` (930 lines)
- `P:\packages\handoff\src\handoff\hooks\SessionStart_handoff_restore.py` (573 lines)
- `P:\packages\handoff\src\handoff\hooks\__lib\transcript.py` (1627 lines)
- `P:\packages\handoff\src\handoff\hooks\__lib\handoff_store.py` (1050 lines)

**Current State:**
- `do_not_revisit` does NOT exist as separate field (currently merged into decisions)
- `canonical_goal` exists but extraction logic is basic (line 267-311 in PreCompact)
- Checksums use `json.dumps()` without explicit `sort_keys=True` (line 356 in handoff_store.py)
- Transcript parsing via `TranscriptParser` class with helper methods
- Session boundaries detection not implemented
- Context gathering stops at first topic change, not session boundary

**Test Patterns:**
- Tests use synthetic transcripts with `json.dumps(entry) + "\n"` format (JSONL)
- Test fixtures in `tests/test_last_user_message.py`, `tests/test_transcript_extract.py`
- Integration tests in `tests/test_integration_e2e.py`
- 476+ tests covering session detection, handoffs, checkpoint chains

**Architecture Constraints:**
- Pure stdlib, Python 3.9+ (no external dependencies)
- Atomic writes, SHA256 checksum validation
- Per-terminal isolation (one `active_session` per terminal)
- No cross-terminal fallback in automatic path

---

## 2. Implementation Strategy

### Phase 1: `do_not_revisit` Separation (2 hours)

**Objective:** Extract high-signal settled constraints into separate array

**Implementation Steps:**

1. **Add `do_not_revisit` field to `handoff_internal` structure**
   - Location: `PreCompact_handoff_capture.py`, line 787-814
   - Add to continuation dict: `"do_not_revisit": []`
   - Field position: After `"decisions"`, before transcript_path

2. **Implement `build_do_not_revisit()` helper function**
   - Location: `PreCompact_handoff_capture.py`, after `extract_session_decisions()` (line 422)
   - Selection criteria:
     - Constraints with strong language: "must", "must not", "never", "always"
     - Final decisions marked as expensive/architecture-level
     - Max 2-4 items (high-signal subset)
   - Input: `decisions` list, `transcript` string
   - Output: List of decision dicts with `topic`, `rationale`, `reason`

3. **Update extraction logic in `main()`**
   - Call `build_do_not_revisit()` after `extract_session_decisions()`
   - Add to `handoff_internal["continuation"]["do_not_revisit"]`
   - Log extraction: `logger.info(f"[PreCompact] do_not_revisit: {len(do_not_revisit)} items")`

4. **Update restoration message in `SessionStart_handoff_restore.py`**
   - Location: `build_quick_reference()`, line 29-235
   - Add new section after "Decisions So Far" (line 147-162)
   - Section header: "Settled Decisions (Do Not Revisit)"
   - Display format: Same as decisions, but with warning icon ⚠️

**Example Output:**
```
Settled Decisions (Do Not Revisit)
- ⚠️ Architecture: Use pure stdlib only (no external dependencies)
- ⚠️ Security: Must validate terminal_id to prevent path traversal
```

### Phase 2: Improved `canonical_goal` Extraction (2 hours)

**Objective:** Extract substantive task, skip meta-instructions and side-threads

**Current Implementation (PreCompact, line 267-311):**
- Removes meta-prefixes ("can you", "please")
- Extracts first sentence
- Removes trailing filler words
- Truncates to 220 chars

**Problems:**
- Works forward from transcript start
- Doesn't skip meta-instructions ("thanks", "summarize")
- Doesn't detect session boundaries
- Doesn't handle side-threads

**Implementation Steps:**

1. **Add helper functions to `transcript.py`**
   - **PRE-IMPLEMENTATION CHECK**: Verify these function names don't already exist
   - `extract_last_substantive_user_message(transcript_path)` - NEW
   - `is_meta_instruction(message)` - NEW
   - `detect_session_boundary(entry, prev_entry)` - NEW
   - `is_same_topic(message1, message2)` - NEW
   - If conflicts exist, use alternative names or integrate with existing functions

2. **Implement `extract_last_substantive_user_message()`**
   - Work backwards from transcript end
   - Skip messages matching meta patterns:
     - "thanks", "thank you", "summarize", "explain", "revert", "rollback"
     - "that's all", "done", "finish"
     - System continuation markers
   - Stop at session boundary:
     - `session_chain_id` change
     - New task markers (explicit "new task" in content)
     - Topic shift detection (semantic similarity threshold)
   - Return first substantive message on current topic

3. **Implement `is_meta_instruction()`**
   - Pattern matching against known meta-instruction keywords
   - Check for system markers (compaction continuation, etc.)
   - Returns: True if message is meta-instruction

4. **Implement `detect_session_boundary()`**
   - Check for `session_chain_id` field changes
   - Look for explicit "new task" indicators
   - Detect topic shifts using simple keyword overlap
   - Returns: True if boundary detected between entries

5. **Implement `is_same_topic()`**
   - Use simple keyword overlap algorithm (pure stdlib)
   - Tokenize both messages on whitespace/punctuation
   - Calculate: intersection / union ratio
   - Return True if overlap > 30%
   - Rationale: No external dependencies, fast computation

6. **Update `derive_canonical_goal()` in PreCompact**
   - Replace forward-scanning logic with `extract_last_substantive_user_message()`
   - Keep existing normalization (meta-prefix removal, truncation)
   - Add logging: Which message was selected, why

**Test Scenarios:**
```python
# Case 1: Last message is meta-instruction
# Result: Skip "thanks", extract previous substantive message

# Case 2: Side question before task completion
# Result: Skip side question, extract main task

# Case 3: Session boundary in middle of transcript
# Result: Only gather messages after last session boundary
```

### Phase 3: Deterministic Checksums (1 hour)

**Objective:** Ensure consistent checksums across Python versions and terminals

**Current Implementation (handoff_store.py, line 356):**
```python
original_data = json.dumps(data, indent=2)
```

**Problem:** No `sort_keys=True`, so dictionary key order varies across Python versions

**Implementation Steps:**

1. **Update checksum computation in `handoff_store.py`**
   - Location: `atomic_write_with_validation()`, line 332-413
   - Line 356: Add `sort_keys=True`
   - Scope: Hash `handoff_internal` dict only (not wrapper metadata)

2. **Document checksum scope clearly**
   - Add comment: "Checksum covers handoff_internal only (not wrapper fields like quality_score)"
   - Explain why: Wrapper fields are computed and vary across runs

3. **Add checksum validation helper**
   - `compute_handoff_checksum(handoff_internal)` - NEW
   - Returns: SHA256 hex string
   - Used by both capture and restore hooks

**Code Changes:**
```python
# Before (line 356)
original_data = json.dumps(data, indent=2)

# After
original_data = json.dumps(data, indent=2, sort_keys=True)
```

**Scope Clarification:**
- Hash `handoff_internal` dict (session_info, task, context, continuation, transcript_path)
- Exclude wrapper metadata (quality_score, checkpoint_id, chain_id)
- Document in code comments

### Phase 4: Context Gathering with Session Boundaries (2 hours)

**Objective:** Gather messages until topic change OR session boundary

**Current Implementation:**
- Context gathering logic scattered across multiple functions
- No session boundary detection
- No topic shift detection

**Implementation Steps:**

1. **Add `gather_context_with_boundaries()` to `transcript.py`**
   - Input: `transcript_path`, `max_messages=50`
   - Work backwards from transcript end
   - Stop conditions:
     - Session boundary detected
     - Topic shift detected
     - Max messages reached
   - Returns: List of message entries

2. **Update context gathering in `PreCompact_handoff_capture.py`**
   - Replace existing transcript scanning logic
   - Use `gather_context_with_boundaries()`
   - Log stopping condition (boundary, topic shift, or limit)

3. **Update `extract_session_decisions()` to use bounded context**
   - Pass `gather_context_with_boundaries()` result
   - Only scan messages within current session/topic

**Stopping Conditions:**
```python
def gather_context_with_boundaries(transcript_path, max_messages=50):
    entries = load_transcript_entries(transcript_path)

    context = []
    for entry in reversed(entries[-max_messages:]):
        if detect_session_boundary(entry, entries[-1]):
            logger.info("Context gathering stopped: session boundary detected")
            break

        if context and not is_same_topic(entry["content"], context[0]["content"]):
            logger.info("Context gathering stopped: topic shift detected")
            break

        context.append(entry)

    return list(reversed(context))
```

---

## 3. Prevention Checklist

### Integration Points to Verify

- [ ] `do_not_revisit` field added to `handoff_internal` structure (PreCompact, line 787-814)
- [ ] `build_do_not_revisit()` helper function implemented (PreCompact, after line 422)
- [ ] Restoration message updated to display `do_not_revisit` section (SessionStart, line 147-162)
- [ ] `extract_last_substantive_user_message()` added to transcript.py
- [ ] `derive_canonical_goal()` updated to use new extraction (PreCompact, line 267-311)
- [ ] Checksum computation uses `sort_keys=True` (handoff_store.py, line 356)
- [ ] Checksum scope documented (handoff_internal only, not wrapper)
- [ ] `gather_context_with_boundaries()` added to transcript.py
- [ ] Context gathering uses bounded logic (PreCompact, main function)
- [ ] All new functions have docstrings following Google style
- [ ] Import paths verified (no relative imports)
- [ ] Logging added for all new extraction steps

### Import Paths

- `from handoff.hooks.__lib.transcript import TranscriptParser` ✓ (existing)
- `from handoff.hooks.__lib.handoff_store import HandoffStore` ✓ (existing)
- New imports to add:
  - `from handoff.hooks.__lib.transcript import extract_last_substantive_user_message`
  - `from handoff.hooks.__lib.transcript import gather_context_with_boundaries`

### Backward Compatibility

- [ ] Old handoffs without `do_not_revisit` field handled gracefully (default to empty list)
- [ ] Old handoffs without `canonical_goal` handled gracefully (fallback to `user_message`)
- [ ] Old checksums without `sort_keys=True` don't break restoration (recompute on load)
- [ ] Migration path documented in code comments

### Error Handling

- [ ] `extract_last_substantive_user_message()` returns "Unknown task" if no substantive message found
- [ ] `build_do_not_revisit()` returns empty list if no strong constraints found
- [ ] `gather_context_with_boundaries()` returns empty list if transcript missing/corrupt
- [ ] All new functions have try/except blocks with logging

---

## 4. Measurable Success Criteria

### Functional Requirements

**FR1: `do_not_revisit` Extraction**
- [ ] `do_not_revisit` field present in all new handoffs
- [ ] Contains 2-4 items max (high-signal subset)
- [ ] Items marked with strong language ("must", "must not", "never")
- [ ] Expensive/architecture decisions included
- [ ] Displayed in restoration message with ⚠️ icon

**FR2: `canonical_goal` Extraction**
- [ ] Extracts substantive task (not meta-instructions)
- [ ] Skips "thanks", "summarize", "explain", "revert", "rollback"
- [ ] Stops at session boundaries (session_chain_id change)
- [ ] Stops at topic shifts (semantic similarity < 30%)
- [ ] Guards against last message being side question

**FR3: Deterministic Checksums**
- [ ] Checksum uses `sort_keys=True` in json.dumps()
- [ ] Hash covers `handoff_internal` only (not wrapper metadata)
- [ ] Same handoff produces same checksum across Python versions
- [ ] Checksum scope documented in code comments

**FR4: Context Gathering with Boundaries**
- [ ] Context gathering stops at session boundaries
- [ ] Context gathering stops at topic shifts
- [ ] Max 50 messages gathered per session
- [ ] Stopping condition logged

### Quality Metrics

- [ ] Test coverage > 80% for new functions
- [ ] All existing tests pass (no regressions)
- [ ] New tests added for each feature (see Test Matrix below)
- [ ] Code review approval from handoff package maintainer
- [ ] Documentation updated (README.md, HANDOFF_STRUCTURE.md)

### Performance Requirements

- [ ] `extract_last_substantive_user_message()` completes in < 100ms for 1000-entry transcript
- [ ] `build_do_not_revisit()` completes in < 50ms
- [ ] `gather_context_with_boundaries()` completes in < 200ms
- [ ] Checksum computation time unchanged (< 10ms)

---

## 5. Explicit Rollback Strategy

### If Implementation Fails

**Trigger Conditions:**
- Test覆盖率 < 80%
- Critical bugs in production (handoff corruption)
- Performance regression > 2x
- Backward compatibility broken

**Rollback Steps:**

1. **Revert code changes**
   ```bash
   cd P:/packages/handoff
   git revert HEAD  # Assuming single commit for all changes
   git push
   ```

2. **Restore symlinks**
   ```bash
   cd P:/.claude/hooks
   # Symlinks will automatically point to reverted code
   ```

3. **Verify handoff system works**
   - Trigger compaction in Claude Code
   - Verify handoff captured
   - Verify restoration works

4. **Document rollback**
   - Add entry to CHANGELOG.md
   - Document reason for rollback
   - File issue for re-implementation

**Safe Rollback Features:**
- Backward compatible design (old handoffs still work)
- No database migrations (JSON files only)
- Symlink architecture allows instant reversion
- Graceful degradation (fallback to old behavior if new fields missing)

### Mitigation Strategies

**Pre-Implementation:**
- Feature flags in code (enable/disable via environment variable)
- Extensive testing in staging before production
- Beta testing with small user group

**During Implementation:**
- Incremental rollout (Phase 1 → Phase 2 → Phase 3 → Phase 4)
- Monitor logs for errors
- Performance profiling after each phase

**Post-Implementation:**
- Monitor handoff quality scores
- User feedback collection
- Regression testing suite

---

## 6. Top 3 Risks

### Risk 1: Backward Compatibility Breakage (Severity: HIGH)

**Description:** Changes to handoff structure may break old handoffs or restoration logic.

**Mitigation:**
- Default values for missing fields (`do_not_revisit=[]`, `canonical_goal=user_message`)
- Test with old handoff files (use existing test fixtures)
- Migration path documented in code comments
- Graceful degradation (fallback to old extraction logic if new fails)

**Probability:** LOW (design is backward compatible)

**Impact:** HIGH (would break all existing handoffs)

### Risk 2: Performance Regression (Severity: MEDIUM)

**Description:** New extraction logic (`extract_last_substantive_user_message`, `gather_context_with_boundaries`) may slow down handoff capture.

**Mitigation:**
- Performance profiling before/after
- Lazy loading of transcript entries (TranscriptLines class)
- Limit scan range (max 100 messages from end)
- Early exit on session boundary detection

**Probability:** MEDIUM (more parsing logic)

**Impact:** MEDIUM (slower compaction, user-visible delay)

### Risk 3: Test Coverage Gaps (Severity: MEDIUM)

**Description:** Complex logic (session boundaries, topic detection) may have edge cases not covered by tests.

**Mitigation:**
- Comprehensive test matrix (8 scenarios, see below)
- Synthetic transcripts for edge cases
- Integration tests with real transcripts
- Mutation testing to verify test quality

**Probability:** MEDIUM (complex logic)

**Impact:** MEDIUM (bugs in production, handoff quality issues)

---

## 7. Next Actions

### Pre-Implementation Checks (Complete Before Starting)

1. **Verify existing function names in transcript.py**
   - Check if `extract_last_substantive_user_message()` already exists
   - Check if `gather_context_with_boundaries()` already exists
   - If conflicts exist, rename new functions or use existing ones
   - Location: `P:\packages\handoff\src\handoff\hooks\__lib\transcript.py`

2. **Add performance baseline test**
   - Create test with 1000-entry synthetic transcript
   - Measure baseline extraction time (current implementation)
   - Verify performance target: < 100ms for new implementation
   - Test file: `tests/test_performance_canonical_goal.py`

3. **Add backward compatibility test**
   - Create test fixture for old handoff JSON (pre-do_not_revisit)
   - Verify restoration defaults `do_not_revisit=[]`
   - Verify no errors when field is missing
   - Test file: `tests/test_backward_compatibility.py`

4. **Specify semantic similarity algorithm**
   - Use simple keyword overlap (not embeddings) for is_same_topic()
   - Algorithm: Tokenize both messages, calculate intersection/union ratio
   - Threshold: > 30% keyword overlap = same topic
   - Rationale: Pure stdlib, no external dependencies

### Immediate Actions (Today)

1. **Create test fixtures for new features**
   - Synthetic transcript with meta-instructions
   - Transcript with session boundary
   - Transcript with topic shift
   - Handoff with strong constraints for `do_not_revisit`

2. **Implement Phase 1: `do_not_revisit` separation**
   - Add `build_do_not_revisit()` function
   - Update handoff structure
   - Update restoration message
   - Write tests (scenarios A-D from test matrix)

3. **Code review Phase 1**
   - Verify implementation matches spec
   - Check test coverage
   - Approve for merge

### This Week

4. **Implement Phase 2: Improved `canonical_goal` extraction**
   - Add helper functions to transcript.py
   - Update `derive_canonical_goal()`
   - Write tests (scenarios E-H from test matrix)

5. **Implement Phase 3: Deterministic checksums**
   - Add `sort_keys=True`
   - Document checksum scope
   - Write tests (same checksum across Python versions)

6. **Implement Phase 4: Context gathering with boundaries**
   - Add `gather_context_with_boundaries()`
   - Update context gathering logic
   - Write tests (session boundary, topic shift)

### Next Week

7. **Integration testing**
   - Test with real transcripts from production
   - Performance profiling
   - Backward compatibility testing

8. **Documentation updates**
   - Update README.md with new features
   - Update HANDOFF_STRUCTURE.md
   - Add examples to docs/

9. **Code review and merge**
   - Final code review
   - Merge to main branch
   - Deploy to production

---

## Test Matrix

### Scenario A: Happy Path - Substantive Task Extraction
**Input:** Transcript ending with "Fix the authentication bug"
**Expected:** `canonical_goal` = "Fix the authentication bug"
**Test:** `test_canonical_goal_substantive_task()`

### Scenario B: Meta-Instruction Skip
**Input:** Transcript ending with "Thanks for your help"
**Expected:** `canonical_goal` = Previous substantive message (e.g., "Run the tests")
**Test:** `test_canonical_goal_skips_thanks()`

### Scenario C: Side Question Detection
**Input:** "Quick question: what's the weather?" then "Continue debugging"
**Expected:** `canonical_goal` = "Continue debugging" (most recent substantive task)
**Test:** `test_canonical_goal_ignores_side_question()`

### Scenario D: Session Boundary Detection
**Input:** Transcript with `session_chain_id` change at position 50
**Expected:** `canonical_goal` extracted from messages after position 50 only
**Test:** `test_canonical_goal_respects_session_boundary()`

### Scenario E: Topic Shift Detection
**Input:** Messages about "auth bug" then messages about "UI design"
**Expected:** Context gathering stops at topic shift, returns only "auth bug" messages
**Test:** `test_context_gathering_stops_at_topic_shift()`

### Scenario F: Strong Constraint Extraction
**Input:** Decision with "must use pure stdlib"
**Expected:** Included in `do_not_revisit`
**Test:** `test_do_not_revisit_includes_strong_constraints()`

### Scenario G: Checksum Determinism
**Input:** Same handoff data, Python 3.9 vs 3.12
**Expected:** Same checksum
**Test:** `test_checksum_deterministic_across_python_versions()`

### Scenario H: Missing File Handling
**Input:** Transcript file doesn't exist
**Expected:** Graceful fallback, return "Unknown task"
**Test:** `test_canonical_goal_missing_transcript()`

---

## Appendix: Code Snippets

### A. `build_do_not_revisit()` Function

```python
def build_do_not_revisit(decisions: list[dict], transcript: str) -> list[dict]:
    """Build do_not_revisit list from strong constraints and expensive decisions.

    Selection criteria:
    - Constraints with strong language ("must", "must not", "never", "always")
    - Final decisions marked as expensive/architecture-level
    - Max 4 items (high-signal subset)

    Args:
        decisions: List of decision dicts from extract_session_decisions()
        transcript: Full transcript string for context

    Returns:
        List of decision dicts with topic, rationale, reason fields
    """
    do_not_revisit = []
    strong_language_patterns = [
        r"\bmust\b", r"\bmust not\b", r"\bnever\b", r"\balways\b",
        r"\brequirement\b", r"\bmandatory\b"
    ]

    for decision in decisions[:10]:  # Check most recent 10 decisions
        if not isinstance(decision, dict):
            continue

        rationale = decision.get("rationale", "")
        topic = decision.get("topic", "")

        # Check for strong language
        has_strong_language = any(
            re.search(pattern, rationale, re.IGNORECASE)
            for pattern in strong_language_patterns
        )

        # Check for expensive/architecture markers
        is_expensive = any(
            keyword in rationale.lower()
            for keyword in ["architecture", "design", "expensive", "requires approval"]
        )

        if has_strong_language or is_expensive:
            do_not_revisit.append({
                "topic": topic,
                "rationale": rationale,
                "reason": "strong_constraint" if has_strong_language else "expensive_decision"
            })

        if len(do_not_revisit) >= 4:
            break

    return do_not_revisit
```

### B. `extract_last_substantive_user_message()` Function

```python
def extract_last_substantive_user_message(
    transcript_path: str | Path,
    max_messages: int = 100
) -> str:
    """Extract last substantive user message, skipping meta-instructions and side-threads.

    Works backwards from transcript end, skipping:
    - Meta-instructions ("thanks", "summarize", "explain", "revert", "rollback")
    - System continuation markers
    - Side questions (detected by topic shift)

    Stops at:
    - Session boundary (session_chain_id change)
    - Topic shift (semantic similarity < 30%)

    Args:
        transcript_path: Path to transcript JSONL file
        max_messages: Maximum messages to scan from end

    Returns:
        Last substantive user message, or "Unknown task" if not found
    """
    parser = TranscriptParser(transcript_path)
    entries = list(parser._parse_entries())  # Get all entries

    # Work backwards from end
    for entry in reversed(entries[-max_messages:]):
        if entry.get("type") != "user":
            continue

        content = entry.get("message", {}).get("content", [])
        if not content or not isinstance(content, list):
            continue

        # Extract text content (skip dict items like tool_result)
        message_text = ""
        for item in content:
            if isinstance(item, str):
                message_text += item + " "

        message_text = message_text.strip()

        # Skip meta-instructions
        if is_meta_instruction(message_text):
            continue

        # Skip too-short messages
        if len(message_text) < 10:
            continue

        # Check for session boundary (compare session_chain_id)
        if "session_chain_id" in entry:
            current_chain_id = entry["session_chain_id"]
            if hasattr(parser, "_last_session_chain_id"):
                if current_chain_id != parser._last_session_chain_id:
                    # Session boundary detected
                    break
            parser._last_session_chain_id = current_chain_id

        # Found substantive message
        return message_text

    return "Unknown task"
```

### C. Restoration Message Update

```python
# In build_quick_reference(), after "Decisions So Far" section (line 162)

# Do Not Revisit Section (NEW)
lines.append("Settled Decisions (Do Not Revisit)")
do_not_revisit = continuation.get("do_not_revisit", [])
if do_not_revisit:
    for dnr in do_not_revisit:
        if isinstance(dnr, dict):
            topic = dnr.get("topic", "Decision")
            rationale = dnr.get("rationale", "").strip()
            if rationale:
                lines.append(f"- ⚠️ {topic}: {rationale}")
            else:
                lines.append(f"- ⚠️ {topic}")
        else:
            lines.append(f"- ⚠️ {dnr}")
else:
    lines.append("- No settled decisions recorded.")
lines.append("")
```

---

## Verification Review Improvements (2026-03-08)

**Status:** 4 improvements applied during plan verification

**Changes Applied:**

1. **Added Pre-Implementation Checks** (Priority 2, Effort: M)
   - Verify existing function names in transcript.py before creating new ones
   - Add performance baseline test for 1000-entry transcript
   - Add backward compatibility test for old handoffs
   - Specify semantic similarity algorithm (keyword overlap, not embeddings)

2. **Updated Implementation Steps** (Priority 2, Effort: S)
   - Phase 2, Step 1: Added pre-implementation check for function name conflicts
   - Phase 2, Step 5: Specified keyword overlap algorithm for is_same_topic()
   - Rationale: Prevent integration conflicts, ensure pure stdlib approach

3. **Updated Plan Status** (Priority 2, Effort: S)
   - Changed from DRAFT → READY-FOR-IMPLEMENTATION
   - Updated estimated effort: 6-8h → 7-9h

4. **Added Risk Mitigations** (Priority 2, Effort: M)
   - Performance baseline before implementing extract_last_substantive_user_message()
   - Backward compatibility test for missing do_not_revisit field
   - Semantic similarity algorithm specified (keyword overlap > 30%)

**Verification Summary:**
- Total findings: 4 improvements
- Critical issues: 0
- High priority: 0
- Medium priority: 4
- Plan status: READY-FOR-IMPLEMENTATION

---

## References

- **Package README:** `P:/packages/handoff/README.md`
- **Structure Documentation:** `P:/packages/handoff/HANDOFF_STRUCTURE.md`
- **Test Suite:** `P:/packages/handoff/tests/`
- **Review Bundle:** `P:/packages/handoff/review_bundle_handoff_20260308.md`

---

**Document Status:** DRAFT - Ready for review
**Next Review:** After Phase 1 implementation
**Owner:** Handoff Package Maintainer
