# Plan: Skill Existence Claim Validation Gate

**Created:** 2026-03-06
**Status:** REVISED (addressing PR-001 through PR-007)
**Priority:** MEDIUM
**Last Review:** 2026-03-06 - REVISION-REQUIRED → Revised with all action items applied

## Summary

Implement validation gate to prevent unverified claims about skill existence/names in AI responses.

## 1. Problem Statement

**Root Cause:** AI claimed "/library is NOT a real skill" without verification. The actual skill is `/library-first` (with hyphen), but no hook validated this claim before it was stated.

**Current Gap:**
- `skill_enforcer.py` only validates when slash command IS used (regex: `^/([a-z0-9-]+)`)
- `strawberry_validator.py` absence patterns don't catch name mismatches
- No requirement to verify skill existence before claiming it doesn't exist
- Claims about external facts (skill existence) don't require evidence

**Impact:**
- Users receive incorrect information about available skills
- Erodes trust in AI responses
- Creates confusion about actual skill names

## 2. Context Analysis

### Allowed APIs (Confirmed from Documentation Discovery)

**Stop Hook Integration Points:**
- **Input format:** `{"response": "text", "toolResults": [...], "toolUse": [...]}`
- **Tool results access:** `data.get("toolResults", [])`
- **Blocking mechanism:** Exit code 2 with JSON output
- **File locations:** `P:/.claude/hooks/StopHook_*.py`

**Skill Registry Access:**
- **Directory:** `P:/.claude/skills/`
- **Validation:** Check for `{command}/SKILL.md` files
- **Existing logic:** `skill_enforcer.py` lines 243-256 (`extract_command_name`, `is_command_directive`)

**Strawberry Validator Patterns (lines 486-513):**
- Absence claims: `"no hook", "doesn't exist", "lacks feature"`
- Template claims: `"/arch template has no X"`
- Process claims: `"already searched", "just verified"`

### Anti-Patterns to Avoid

**DO NOT:**
- Create a separate skill registry cache (unnecessary complexity)
- Use LLM verification for simple file system checks (overkill, slow)
- Block all skill name mentions (false positives on conversational references)
- Require evidence for "no problem", "not surprisingly" (conversational idioms)

**DO:**
- Use direct file system checks (fast, reliable)
- Add patterns to existing `strawberry_validator.py` (consolidated logic)
- Distinguish claims from conversational references (context-aware)
- Follow existing test patterns from `test_strawberry_validator.py`

## 3. Existing Implementation Discovery

**File: `P:/.claude/hooks/scanners/strawberry_validator.py`**

**Relevant Methods:**
- `_extract_claims()` (lines 435-514): Extracts verifiable claims from text
- `_stage1_rule_check()` (lines 169-203): Fast pattern matching
- `_build_evidence_pack()` (lines 516-546): Extracts evidence from tool results

**Current Absence Claim Patterns:**
```python
absence_patterns = [
    r'\b(?:no|not|doesn\'t|isn\'t|aren\'t)\s+(?:hook|test|function|feature|module|file|class|method)\b',
    r'\b(?:lacks|missing|without)\s+[\w\s]+?\b',
]
```

**Evidence Extraction Logic:**
```python
tool_results = context.get("toolResults", [])
for result in tool_results:
    if result.get("name") == "Bash":
        command = result.get("command", "")
        output = result.get("stdout", "") + result.get("stderr", "")
```

**File: `P:/.claude/hooks/UserPromptSubmit/skill_enforcer.py`**

**Skill Detection Logic:**
```python
SLASH_COMMAND_RE = re.compile(r'^/([a-z0-9-]+)(?:\s+(.*))?$', re.IGNORECASE)

def extract_command_name(prompt: str) -> str | None:
    normalized = _normalize_prompt_for_command_detection(prompt)
    match = SLASH_COMMAND_RE.match(normalized)
    if match:
        return match.group(1)
    return None
```

**Skills Directory Check:**
```python
skills_dir = Path("P:/.claude/skills")
skill_file = skills_dir / command / "SKILL.md"
if skill_file.exists():
    # Skill exists
```

## 4. Test Discovery

**Test File: `P:/.claude/hooks/tests/test_strawberry_validator.py`**

**Test Pattern for Claim Detection:**
```python
def test_absence_claim_detection(self):
    """Test that absence claims are detected."""
    text = "There is no hook for validating JSON"
    context = {"toolResults": []}  # No evidence

    result = self.validator.scan(text, context)

    assert result.status == ScanStatus.FAIL
    assert "absence claim" in result.reason.lower()
```

**Test Pattern for Evidence Building:**
```python
def test_build_evidence_pack_from_tool_results(self):
    """Test that evidence is built from tool results."""
    context = {
        "toolResults": [
            {
                "name": "Bash",
                "command": "ls P:/.claude/skills/",
                "stdout": "library-first\narch\n"
            }
        ]
    }

    evidence = self.validator._build_evidence_pack(context)
    assert "Command: ls" in evidence
    assert "library-first" in evidence
```

**Mock Data Structure:**
```python
{
    "response": "test text",
    "toolResults": [
        {"name": "Bash", "command": "...", "stdout": "...", "stderr": "..."},
        {"name": "Grep", "pattern": "...", "matches": ["..."]}
    ],
    "toolUse": [...]
}
```

## 5. Proposed Solution

**Architecture:** Extend `strawberry_validator.py` with skill-specific claim patterns

**Three-Stage Detection:**

**Stage 1: Pattern Detection (Fast, <10ms)**
- Detect claims about skill existence
- Patterns: `"/X is not a real skill"`, `"no skill called X"`, `"skill /X doesn't exist"`
- Extract skill name from claim

**Stage 2: Evidence Check (Fast, <50ms)**
- Check if `toolResults` contains Bash/Grep/Read evidence
- Look for skill directory listing (`ls P:/.claude/skills/`)
- Look for skill file reads (`Read library-first/SKILL.md`)

**Stage 3: Fuzzy Match Suggestion (Fast, <20ms)**
- If claimed skill doesn't exist but similar skill exists
- Suggest: `"Did you mean /library-first?"`
- Uses difflib for approximate string matching
- **False Positive Logging:** Log blocked claims with context to `state/logs/skill_claim_blocks.log` for monitoring
  - Format: `TIMESTAMP | CLAIM | EVIDENCE_COUNT | SIMILAR_SKILL`
  - Opt-out via `SKILL_CLAIM_LOGGING=false` environment variable

**Integration Point:**
- Add to `strawberry_validator.py` `_extract_claims()` method
- New pattern category: `SKILL_EXISTENCE_CLAIMS`
- Reuse existing `_build_evidence_pack()` for evidence extraction

**Why Fuzzy Matching > Alias System:**
- **Aliases** require maintaining mapping table (e.g., `/library` → `/library-first`)
- **Symlinks** require file system changes and git tracking
- **Fuzzy matching** with difflib:
  - No maintenance overhead
  - Handles future skills automatically
  - Similarity threshold (>80%) prevents noise
  - Works across skill renames
- **Decision:** Fuzzy matching chosen for low maintenance and automatic adaptation

## 6. Implementation Plan

**Task Breakdown:**

**T-000: Measure baseline performance**
- **File:** `P:/.claude/hooks/tests/test_strawberry_validator_performance.py`
- **Action:** Measure current strawberry_validator latency before changes
- **Steps:**
  1. Run existing test suite with timing measurements
  2. Profile `_stage1_rule_check()` and `_extract_claims()` methods
  3. Record baseline: Stage 1 latency, Stage 2 latency (if triggered), total latency
- **Acceptance Criteria:**
  - Baseline Stage 1 latency <10ms
  - Baseline Stage 2 latency <500ms
  - Document baseline in test file

**T-001: Add skill claim patterns to strawberry_validator.py**
- **File:** `P:/.claude/hooks/scanners/strawberry_validator.py`
- **Action:** Add new pattern category in `_extract_claims()` method (after line 513)
- **Patterns to add:**
  ```python
  # NEW: Skill existence claims
  skill_patterns = [
      r'/[\w-]+\s+(?:is|does not|doesn't|not a)\s+(?:real skill|valid skill|exist)',
      r'no skill called\s+["\']?/[\w-]+["\']?',
      r'skill\s+["\']?/[\w-]+["\']?\s+(?:does not exist|is not real)',
      r'there is no (?:skill called\s+)?/[\w-]+\s+skill',
  ]
  ```
- **Acceptance Criteria:**
  - Patterns detect "/library is not a real skill"
  - Patterns detect "no skill called /xyz"
  - Patterns don't match conversational "no problem"

**T-002: Implement skill name validation logic**
- **File:** `P:/.claude/hooks/scanners/strawberry_validator.py`
- **Action:** Add new method `_validate_skill_claim(claim, context)`
- **Logic:**
  1. Extract skill name from claim (regex: `/([\w-]+)`)
  2. Check `toolResults` for evidence (Bash `ls skills/`, Grep for skill name)
  3. If no evidence: return `ValidationResult(is_valid=False, reason="...")`
  4. If evidence exists but skill not found: suggest similar skills
- **Acceptance Criteria:**
  - Validates claim against tool results
  - Returns FAIL when no evidence provided
  - Suggests similar skills when applicable

**T-003: Integrate skill validation into scan() method**
- **File:** `P:/.claude/hooks/scanners/strawberry_validator.py`
- **Action:** Modify `scan()` method to call `_validate_skill_claim()` for skill claims
- **Location:** After line 159 (after `_stage1_rule_check()`)
- **Acceptance Criteria:**
  - Skill claims trigger validation
  - Blocking with reason when no evidence
  - Suggestion provided when similar skill exists

**T-004: Create unit tests for skill claim detection**
- **File:** `P:/.claude/hooks/tests/test_strawberry_validator_skill_claims.py`
- **Action:** Create test file with comprehensive coverage
- **Test cases:**
  1. Claim without evidence → BLOCK
  2. Claim with Bash evidence showing skill exists → ALLOW
  3. Claim with Bash evidence showing skill doesn't exist → ALLOW
  4. Similar skill suggestion ("library" → "library-first")
  5. Conversational "no problem" → SKIP (negative test)
  6. Path-like strings (e.g., "/usr/bin/lib") → SKIP (negative test)
  7. Conversational "not surprisingly" → SKIP (negative test)
- **Acceptance Criteria:**
  - All tests pass
  - Coverage >90% for new code
  - Negative tests prevent false positives

**T-005: Create integration test with Stop hook**
- **File:** `P:/.claude/hooks/tests/test_skill_claim_integration.py`
- **Action:** Test end-to-end Stop hook behavior
- **Test scenario:**
  1. Mock Stop input with claim but no evidence
  2. Run strawberry_validator via Stop hook
  3. Verify exit code 2 (block)
  4. Verify JSON output contains reason
- **Acceptance Criteria:**
  - Stop hook blocks unverified claims
  - JSON output format correct
  - Performance <100ms

**T-006: Update documentation**
- **File:** `P:/.claude/hooks/CLAUDE.md`
- **Action:** Add "Skill Existence Claims" section to claim verification documentation
- **Content:**
  - Describe skill claim patterns
  - Explain evidence requirements
  - Provide examples
- **Acceptance Criteria:**
  - Documentation clear and concise
  - Examples cover common cases

## 7. Risks, Success Criteria, Dependencies

**Risks:**

| Risk | Impact | Mitigation |
|------|--------|------------|
| False positives on conversational references | Medium | Exclude idioms ("no problem"), require explicit skill syntax |
| Performance degradation (<500ms requirement) | Low | File system checks are fast, Stage 1 filters most cases |
| Pattern miss (new claim formats not detected) | Medium | Monitor logs, add patterns iteratively |
| Similar skill suggestion noise | Low | Only suggest when similarity >80% (difflib ratio) |

**Success Criteria:**
1. ✅ Blocks unverified skill existence claims (exit code 2)
2. ✅ Allows claims with Bash/Grep evidence (exit code 0)
3. ✅ Suggests similar skills when applicable
4. ✅ Performance <100ms for Stage 1 + Stage 2
5. ✅ Test coverage >90%
6. ✅ False positive rate <5% (with monitoring via logging)

**Dependencies:**
- **Required:** None (uses existing infrastructure)
- **Optional:** `difflib` for fuzzy matching (stdlib, always available)
- **Integration:** Works with existing Stop hook registration

**Rollback Strategy:**
- Remove new patterns from `strawberry_validator.py`
- Delete test files
- No breaking changes (additive only)

**Pattern Review and Evolution Process:**
- **Weekly Review:** Check `state/logs/skill_claim_blocks.log` for false positive patterns
- **Pattern Addition Process:**
  1. Identify recurring false positive pattern from logs
  2. Add exclusion regex to `skill_patterns` (negative lookbehind/lookahead)
  3. Add test case to T-004 for the exclusion
  4. Verify false positive rate <5%
- **Monthly Audit:** Review all skill claim patterns for:
  - Stale patterns (no matches in 30 days)
  - Coverage gaps (new claim formats not detected)
  - Performance regression (Stage 1 latency increase)
- **Cadence:** Weekly automated review, monthly manual audit

---

## 8. Comparison with AI Coding Assistants

### How AI Coding Assistants Handle Verification

**GitHub Copilot:**
- **Approach**: RAG (Retrieval-Augmented Generation) over indexed codebase
- **Mechanism**: Indexes files, embeddings for semantic search, retrieves relevant context
- **Verification**: Post-generation - no pre-response blocking
- **Scope**: Broad (all code suggestions), but no explicit claim verification

**Cursor Windsurf:**
- **Approach**: Real-time codebase indexing + context awareness
- **Mechanism**: Continuously indexes open files, provides context-aware suggestions
- **Verification**: User must verify suggestions manually
- **Scope**: File-level context, no claim validation

**Sourcegraph Cody:**
- **Approach**: Code graph + embeddings + LLM
- **Mechanism**: Builds graph of code relationships, retrieves context
- **Verification**: Post-generation review, no blocking
- **Scope**: Cross-repository context, but trusts AI output

### Key Differences: Our Approach vs. AI Assistants

| Aspect | AI Assistants (RAG-based) | Our Solution (Pre-response Blocking) |
|--------|---------------------------|-------------------------------------|
| **Timing** | Post-generation (verify after) | **Pre-generation** (block before) |
| **Verification** | Retrieve context, generate, hope for accuracy | **Require tool evidence** before claim |
| **Scope** | Broad codebase indexing | **Narrow claim types** (skill existence) |
| **Enforcement** | User reviews suggestions | **Stop hook blocks** response |
| **Latency** | High (indexing + retrieval) | **Low** (<100ms pattern match) |
| **Accuracy** | Hallucinations common (RAG misses context) | **Evidence-based** (require tools) |

### Why RAG Doesn't Solve Our Problem

**RAG approach** (used by Copilot, Cursor, Cody):
1. Index codebase (embeddings, vector search)
2. Retrieve relevant context for query
3. Generate response based on retrieved context
4. **Problem**: Still hallucinates when retrieval misses relevant files

**Our approach**:
1. Detect claim pattern ("/xyz is not a real skill")
2. **Require tool evidence** (Bash `ls skills/`, Grep, Read)
3. Block if no evidence provided
4. **Advantage**: Explicit verification requirement vs. implicit retrieval

### Why Our Approach Works for This Use Case

**Narrow scope enables strict enforcement:**
- **Skill existence claims** are easily verifiable (file system check)
- **Pattern detection** is reliable (specific syntax)
- **Evidence requirement** is clear (tool results in context)
- **Low false positive rate** achievable with focused patterns

**Would NOT scale to general code suggestions:**
- Too expensive to verify every code suggestion
- RAG is better for broad codebase context
- Our approach is **claim-specific**, not **content-specific**

---

## 9. Extending the Pattern to Other Claim Types

### Potential Extensions

**File Existence Claims:**
- **Pattern**: `"file X doesn't exist"`, `"no file at path Y"`
- **Verification**: Require `Read` or `Glob` tool evidence
- **Implementation**: Add to `strawberry_validator.py` absence patterns

**API Availability Claims:**
- **Pattern**: `"module X has no Y function"`, `"API doesn't support Z"`
- **Verification**: Require library documentation or `Read` of source
- **Implementation**: Extend with import/docs checking

**Test Coverage Claims:**
- **Pattern**: `"no tests for X"`, `"lacks test coverage"`
- **Verification**: Require `Glob` test pattern search (`**/test_*.py`)
- **Implementation**: Add test discovery patterns

**Configuration Claims:**
- **Pattern**: `"setting X is not configured"`, `"no Y option"`
- **Verification**: Require `Read` of config files or `settings.json`
- **Implementation**: Add config file validation

### Extension Strategy

**Phase 1: Implement Skill Claims (This Plan)**
- Focus on skill existence validation
- Measure false positive rate
- Build pattern tuning infrastructure

**Phase 2: Extend to File Existence**
- Add file path claim patterns
- Implement file system verification
- Reuse `toolResults` evidence framework

**Phase 3: Extend to API/Module Claims**
- Add import/module claim patterns
- Integrate with `context7` for docs verification
- Build knowledge base of available APIs

**Phase 4: Extend to Test/Config Claims**
- Add test coverage patterns
- Add config validation patterns
- Full claim verification ecosystem

### Shared Infrastructure

All extensions can reuse:
- **Evidence extraction**: `_build_evidence_pack()` from `strawberry_validator.py`
- **Tool result checking**: `context.get("toolResults", [])` pattern
- **Pattern detection**: `_extract_claims()` framework
- **Blocking mechanism**: Stop hook exit code 2
- **Logging**: False positive logging system
- **Monitoring**: Weekly pattern review process

### Risk Management for Extensions

**Risk: Scope Creep**
- **Mitigation**: Implement one claim type at a time
- **Measure**: Track false positive rate per claim type
- **Threshold**: Only add new claim type when existing <5% FP rate

**Risk: Performance Degradation**
- **Mitigation**: Pattern matching is fast (<10ms), scale linearly
- **Monitor**: Add timing metrics for each claim type
- **Limit**: Max 10 claim types before refactoring to optimized engine

**Risk: Pattern Complexity**
- **Mitigation**: Keep patterns specific and narrow
- **Test**: Comprehensive negative test cases for each claim type
- **Review**: Monthly audit for pattern simplification opportunities
