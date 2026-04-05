# Review Bundle: Unverified Artifact Claims Detection

**Generated**: 2026-03-05
**Scope**: Unverified artifact claims detection system (Stop gate + helper module)
**File Count**: 4 files (271 LOC implementation + 241 LOC tests)
**Execution Mode**: Single-agent (focused scope)

---

## 1. PROJECT CONTEXT

### Bundle Metadata

This bundle covers the **unverified artifact claims detection system** — a new Stop hook gate that enforces evidence-based claims about specific files and artifacts.

**Components**:
- `artifact_claims.py` - Claim extraction and observation detection module (271 LOC)
- `_run_unverified_artifact_claims` gate in `Stop.py` - Verification logic (in-process)
- `test_artifact_claims.py` - Unit tests (241 LOC, 100% coverage)
- `__lib/shared_helpers.py` - Meta-conversation/self-referential detection (reused)

### Domain & Purpose

**Purpose**: Prevent AI from making strong claims about specific artifacts (files, hooks, configs) without both:

1. **Tool verification** - Using a verification tool (Read, Grep, Bash) on the artifact
2. **Concrete observation** - Citing specific details (line numbers, function names, test results)

**Problem Solved**: AI frequently makes claims like "I fixed the bug in config.json" or "The root cause is in Stop.py" without:
- Reading the file to verify
- Providing concrete evidence (line numbers, specific errors, test output)

**Who uses it**: All Claude Code sessions in the P:\ workspace (Stop hook runs for every response)

**Why it's critical**: This is a **constitutional enforcement gate** that prevents hallucination and speculation about code artifacts, ensuring claims are grounded in actual verification.

### Scale Metrics

- **LOC**: 512 total (271 implementation + 241 tests)
- **Major subsystems**: 2 (claim extraction, verification logic)
- **Deployment scope**: Workspace-wide (all sessions)
- **Change frequency**: Low (constitutional gate, stable patterns)

### Your Environment

- **OS and shell**: Windows 11, Bash (Git for Windows)
- **Primary languages**: Python 3.10+ (dataclasses, regex, type hints)
- **Package managers**: None (stdlib only, zero dependencies)
- **Databases/external services**: None (pure regex + logic)

---

## 2. ARCHITECTURE OVERVIEW

### System Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     RESPONSE GENERATED                       │
│  AI generates response text + tool calls (Read/Edit/etc.)   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              STOP HOOK ROUTER (Stop.py)                      │
│  IN_PROCESS_GATES sequence:                                  │
│  1. safety_gate                                              │
│  2. skill_first_stop_gate                                    │
│  3. behavior_audit                                           │
│  4. **unverified_artifact_claims** ← NEW GATE (position 4)  │
│  5. behavior_gates_agreement                                 │
│  ... (remaining gates)                                       │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│        _run_unverified_artifact_claims() GATE                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Phase 1: Exclusion checks (fail-fast)                │  │
│  │ • Env var disabled? → return None                     │  │
│  │ • No response? → return None                          │  │
│  │ • Meta-conversation? → return None                    │  │
│  │ • Self-referential? → return None                     │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                   │
│                          ▼                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Phase 2: Claim extraction (artifact_claims.py)       │  │
│  │ • Split response into sentences                      │  │
│  │ • Exclude meta/self-ref sentences                    │  │
│  │ • Detect claim types: fix, root_cause, characterization │  │
│  │ • Extract artifact references (files, hooks, configs) │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                   │
│                          ▼                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Phase 3: Tool parsing (_uac_parse_tool_calls)        │  │
│  │ • Normalize tool_calls format (list or XML string)   │  │
│  │ • Extract tool names + inputs (file_path, command)   │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                   │
│                          ▼                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Phase 4: Verification check (for each claim)         │  │
│  │ • _uac_tool_touches_artifact(tool_calls, claim)      │  │
│  │ • find_concrete_observation(response, claim)         │  │
│  │ • Block if: no tool AND no observation               │  │
│  │ • Block if: tool used but no concrete observation    │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                   │
│                          ▼                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Phase 5: Output                                      │  │
│  │ • No violations? → return None (allow)               │  │
│  │ • Violations? → build block reason (max 5 claims)    │  │
│  │ • Return {"decision": "block", "reason": "..."}      │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Subsystem Details

#### artifact_claims.py (Helper Module)

**Location**: `P:\.claude\hooks\artifact_claims.py`

**Purpose**: Extract strong claims about artifacts from response text

**Architecture**: **Regex-based, stdlib-only, tunable patterns**

**Key components**:

1. **Dataclass**: `ArtifactClaim(text, target_artifact, claim_type)`
   - `text`: The sentence containing the claim
   - `target_artifact`: File path / hook / config name (or None for outcome-only)
   - `claim_type`: "fix", "root_cause", or "characterization"

2. **Claim Detection Patterns**:
   - **Fix patterns**: "fixed", "resolved", "now works", "bug is fixed"
   - **Root cause patterns**: "root cause is", "caused by", "due to", "the issue is that"
   - **Characterization patterns**: "generic", "stock", "broken", "misconfigured", "unused", "outdated"

3. **Artifact Token Extraction** (`_ARTIFACT_TOKEN_RE`):
   - File paths with extensions: `.py`, `.js`, `.json`, `.yaml`, `.md`, etc.
   - Hook files: `Stop*.py`, `Pre*.py`, `Post*.py`, `Session*.py`
   - Config references: `config`, `settings`, `.env`, `CLAUDE.md`

4. **Sentence Splitting** (`_split_sentences()`):
   - **Protects file extensions**: Replaces `.` in `file.py` with `\x00` before splitting
   - **Protects URLs**: Replaces `.` in `https://example.com` with `\x00`
   - **Protects ellipsis**: Replaces `...` with `\x01\x01\x01`
   - **Splits on `. ` / `! ` / `? `**: Standard sentence boundaries
   - **Restores placeholders**: Replaces `\x00` → `.`, `\x01` → `.`

5. **Meta-Conversation Exclusion** (`_is_meta_or_self_ref()`):
   - **Meta patterns**: "if you want", "the approach would be", "for example", "typically"
   - **Self-ref patterns**: "I did this because", "my reasoning was", "I apologize", "I misread"
   - **Returns**: `True` if sentence should be excluded from claim extraction

6. **Public API**:
   - `extract_artifact_claims(text)` → `list[ArtifactClaim]`
   - `find_concrete_observation(full_text, claim)` → `str | None`

**Dependencies**: None (stdlib only: `re`, `dataclasses`)

**Known limitations**:
- Regex-based (may miss edge cases or have false positives)
- English only (patterns are hardcoded)
- No learning mechanism (patterns are static)

---

#### Stop.py Gate Integration

**Location**: `P:\.claude\hooks\Stop.py` (lines 704-767)

**Purpose**: In-process gate that verifies artifact claims against tool usage

**Gate position**: #4 in `IN_PROCESS_GATES` (after `behavior_audit`, before `behavior_gates_agreement`)

**Architecture**: **In-process function call** (no subprocess overhead)

**Key functions**:

1. **`_run_unverified_artifact_claims(data)`** - Main gate logic
   - Input: `data` dict (response, tool_calls, transcript, session metadata)
   - Output: `dict` with `decision`, `reason`, `blocking_hook` or `None`
   - Killswitch: `UNVERIFIED_ARTIFACT_CLAIMS_DISABLED=true`

2. **`_uac_parse_tool_calls(data)`** - Normalize tool format
   - Handles both `tools_used` (list of dicts) and `tool_calls` (XML string)
   - Extracts tool names + inputs (file_path, command, pattern, url)
   - Returns: `list[dict]` with `name` and optional `input` fields

3. **`_uac_tool_touches_artifact(tool_calls, claim)`** - Check verification
   - **Artifact-specific claims**: Checks if tool input matches artifact path
   - **Outcome-only fix claims**: Requires `Bash` specifically (not just any tool)
   - **Outcome-only root_cause/characterization**: Any verification tool counts
   - Returns: `True` if tool touches artifact, `False` otherwise

**Verification logic** (for each claim):

```python
has_tool = _uac_tool_touches_artifact(tool_calls, claim)
has_obs = find_concrete_observation(response, claim) is not None

if not has_tool and not has_obs:
    blocked.append((claim, "no verification tool AND no concrete observation"))
elif not has_tool:
    blocked.append((claim, "no verification tool touched this artifact this turn"))
elif not has_obs:
    blocked.append((claim, "tool used but response lacks concrete observation"))
```

**Block reason format**:
```
UNVERIFIED_ARTIFACT_CLAIMS:

Strong claims about artifacts/outcomes without verification evidence.
For each claim: use a verification tool on the artifact AND cite a concrete observation.

- "The bug in config.json is fixed."
  Artifact: config.json
  Issue: no verification tool touched this artifact this turn

- "The root cause is a missing import in validator.py."
  Artifact: validator.py
  Issue: tool used but response lacks concrete observation (file:line, specific value, etc.)
```

**Fail-open policy**: Exceptions print to stderr and return `None` (allow)

**Dependencies**:
- `artifact_claims.py` (claim extraction)
- `__lib/shared_helpers.py` (meta-conversation/self-referential detection)

**Known limitations**:
- Only checks current turn's tool calls (not historical)
- Requires tool_calls in Stop input (may be missing in some cases)
- No whitelist for exempt claims

---

#### shared_helpers.py (Meta-Conversation Detection)

**Location**: `P:\.claude\hooks\__lib\shared_helpers.py`

**Purpose**: Detect meta-conversations and self-referential content (reused by gate)

**Key functions**:

1. **`is_meta_conversation(transcript)`** - Check if user asks meta-questions
   - Patterns: "why did you make|do|say|use", "what was your (reason|thinking)"
   - Scope: Last 5 messages, user role only
   - Returns: `True` if meta-conversation detected

2. **`is_self_referential(response)`** - Check if AI response is about itself
   - Patterns: "I did this because", "my reasoning was", "I apologize", "I misread"
   - Scope: Response text only
   - Returns: `True` if self-referential

**Critical distinction**: Does NOT filter external claims like "The file is at C:\path" or "The bug is in line 42"

**Dependencies**: None (stdlib only: `re`, `typing`)

---

## 3. EXECUTION AND DATA FLOW

### Gate Execution Sequence

```
1. Stop.py receives JSON input via stdin
   - response (str)
   - tool_calls (str or list)
   - transcript (list of dict)
   - session_id, terminal_id (str)

2. _run_unverified_artifact_claims(data) called

3. Phase 1: Exclusion checks (fail-fast)
   - Env var disabled? → return None
   - No response? → return None
   - Meta-conversation? → return None
   - Self-referential? → return None

4. Phase 2: Claim extraction
   - extract_artifact_claims(response) → list[ArtifactClaim]
   - No claims? → return None

5. Phase 3: Tool parsing
   - _uac_parse_tool_calls(data) → list[dict] (normalized)
   - Empty tools? → continue (may still block)

6. Phase 4: Verification check (for each claim)
   - _uac_tool_touches_artifact(tool_calls, claim) → bool
   - find_concrete_observation(response, claim) → str or None
   - Both must be True to allow

7. Phase 5: Output
   - No violations? → return None (allow)
   - Violations? → build block reason (max 5 claims)
   - Return {"decision": "block", "reason": "...", "blocking_hook": "Stop.py:unverified_artifact_claims"}

8. Stop.py handles return value
   - None → continue to next gate
   - Block dict → print JSON, exit 2 (STOP)
```

### Claim Type Handling

| Claim Type | Artifact Specified | Tool Requirement | Observation Requirement |
|------------|-------------------|------------------|------------------------|
| **fix** | Yes (e.g., "config.json is fixed") | Any verification tool touching the artifact | Concrete detail about that artifact |
| **fix** | No (e.g., "The bug is fixed") | **Bash specifically** (test run) | Concrete detail (test results) |
| **root_cause** | Yes (e.g., "Root cause in validator.py") | Any verification tool touching the artifact | Concrete detail about that artifact |
| **root_cause** | No (e.g., "The root cause is missing imports") | Any verification tool | Concrete detail about any artifact |
| **characterization** | Yes (e.g., "config.json is broken") | Any verification tool touching the artifact | Concrete detail about that artifact |
| **characterization** | No (e.g., "The config is broken") | Any verification tool | Concrete detail about any artifact |

**Key distinction**: Outcome-only fix claims require `Bash` (test execution), not just any tool. This prevents "I fixed it" claims without actually running tests.

### Concrete Observation Detection

**Definition**: Sentence contains BOTH:
1. **Mention of the artifact** (if target_artifact specified)
2. **Detail tokens**: Line numbers, function names, specific values, error messages

**Detail token regex** (`_DETAIL_RE`):
- Function calls: `foo(`
- Line numbers: `line 42`
- Error indicators: `error`, `exception`, `traceback`
- Return values: `returns True`, `= "value"`
- Code blocks: ``` \w*
- Test results: `15 tests passed`, `all 15 tests`

**Example observations**:
- ✅ "Found the issue at line 42 where the key was missing." (line number)
- ✅ "The `validate_input()` function was missing a null check." (function call)
- ✅ "All 15 tests passed." (test results)
- ❌ "I looked at it and found the issue." (no detail tokens)
- ❌ "The file looks correct now." (no detail tokens)

**Search scope**: Claim sentence ± 2 sentences (checks nearby context for observations)

---

## 4. COMPONENT INVENTORY

### Core Logic

#### artifact_claims.py

- **Path**: `P:\.claude\hooks\artifact_claims.py`
- **Key functions**:
  - `extract_artifact_claims(text)` - Extract strong claims about artifacts
  - `find_concrete_observation(full_text, claim)` - Check for concrete observations
  - `_split_sentences(text)` - Sentence splitting without breaking file paths
  - `_is_meta_or_self_ref(sentence)` - Exclude meta/self-ref content
  - `_find_artifact_in_text(text)` - Extract artifact reference
  - `_has_concrete_detail(sentence, target)` - Check for detail tokens
- **Responsibility**: Parse response text, extract claims, detect observations
- **Inputs**: Response text (str)
- **Outputs**: `list[ArtifactClaim]` or `str` (observation sentence)
- **Known limitations**:
  - Regex-based (may miss edge cases)
  - English only
  - No learning mechanism

#### Stop.py Gate

- **Path**: `P:\.claude\hooks\Stop.py` (lines 704-767)
- **Key functions**:
  - `_run_unverified_artifact_claims(data)` - Main gate logic
  - `_uac_parse_tool_calls(data)` - Normalize tool format
  - `_uac_tool_touches_artifact(tool_calls, claim)` - Check verification
- **Responsibility**: Verify claims against tool usage + observations
- **Inputs**: `data` dict (response, tool_calls, transcript)
- **Outputs**: `dict` (block) or `None` (allow)
- **Known limitations**:
  - Only checks current turn's tools
  - Requires tool_calls in input
  - No whitelist for exempt claims

### Utilities/Helpers

#### shared_helpers.py (Meta-Conversation Detection)

- **Path**: `P:\.claude\hooks\__lib\shared_helpers.py`
- **Key functions**:
  - `is_meta_conversation(transcript)` - Detect user meta-questions
  - `is_self_referential(response)` - Detect AI self-reflection
- **Responsibility**: Exclude meta/self-ref from claim detection
- **Inputs**: Transcript (list) or response (str)
- **Outputs**: `bool` (True if should exclude)
- **Known limitations**:
  - Regex-based (may have false positives)
  - English only

### Configuration

#### Environment Variables

- **`UNVERIFIED_ARTIFACT_CLAIMS_DISABLED`** (default: false)
  - Set to `"true"` to disable the gate
  - Used for testing or debugging

**No configuration files** - gate is self-contained in Stop.py

### Infrastructure

#### Test Coverage

- **Path**: `P:\.claude\hooks\tests\test_artifact_claims.py`
- **Test classes**:
  - `TestSentenceSplitting` - File path/URL preservation
  - `TestMetaExclusion` - Meta/self-ref filtering
  - `TestExtractClaims` - Claim extraction by type
  - `TestConcreteObservation` - Observation detection
  - `TestGateIntegration` - End-to-end gate tests
- **Coverage**: 100% of public API
- **Known limitations**:
  - Tests are English-only
  - No performance benchmarks

---

## 5. DESIGN INTENT AND NON-NEGOTIABLES

### Architectural Pillars

1. **Evidence-Based Verification** - Claims require both tool usage AND concrete observations
2. **Fail-Open Policy** - Gate errors allow responses (additive, not safety-critical)
3. **Stdlib-Only** - Zero external dependencies (regex, dataclasses only)
4. **Meta-Exclusion** - Meta-conversations and self-referential content are excluded
5. **In-Process Execution** - Direct function call (no subprocess overhead)

### Technology Constraints

1. **Python 3.10+** - Uses dataclasses with type hints
2. **Regex-based** - All patterns are regex (no NLP/ML)
3. **English only** - Patterns are hardcoded for English
4. **No external services** - Pure logic, no API calls
5. **File-based state** - No database (Stop input is dict)

### Performance SLAs

1. **Gate latency**: <100ms per response (regex + simple logic)
2. **Claim extraction**: <50ms for typical response (100-200 words)
3. **Tool parsing**: <20ms (regex-based XML extraction)
4. **Memory usage**: <1MB per call (no large data structures)

### Things That Must NOT Change

1. **Fail-open policy** - Gate errors must allow responses (not block)
2. **In-process execution** - No subprocess calls (performance requirement)
3. **Stdlib-only** - No external dependencies (portability requirement)
4. **Meta-exclusion** - Must exclude meta-conversations and self-referential content
5. **Dual verification** - Claims require BOTH tool usage AND concrete observation

---

## 6. KNOWN ISSUES

### Issue 1: Regex-Based Detection May Miss Edge Cases

**Scenario**: Complex sentence structures or unusual phrasing

**Expected vs Actual**:
- Expected: All strong claims detected
- Actual: Some claims may be missed if they don't match regex patterns

**Impact**: Low - Gate is additive, misses are acceptable (fail-open)

**Current workaround**: Tune regex patterns in `artifact_claims.py` based on real usage

---

### Issue 2: English-Only Patterns

**Scenario**: Non-English responses or mixed-language content

**Expected vs Actual**:
- Expected: Claims detected in any language
- Actual: Patterns are English-only

**Impact**: Low - Workspace is English-only

**Current workaround**: None needed (English-only workspace)

---

### Issue 3: No Historical Tool Context

**Scenario**: Claim about artifact verified in previous turn

**Expected vs Actual**:
- Expected: Gate recognizes previous verification
- Actual: Only checks current turn's tool calls

**Impact**: Medium - May require re-verification in same turn

**Current workaround**: Re-run verification tool in same response

---

### Issue 4: XML Tool Parsing May Fail on Malformed Input

**Scenario**: tool_calls string has malformed XML

**Expected vs Actual**:
- Expected: Graceful handling of malformed XML
- Actual: Regex extraction may miss tools

**Impact**: Low - Fail-open policy allows responses

**Current workaround**: Gate fails open on parsing errors

---

### Issue 5: No Whitelist for Exempt Claims

**Scenario**: Legitimate claims about known-good artifacts

**Expected vs Actual**:
- Expected: Whitelist for exempt claims
- Actual: All claims require verification

**Impact**: Low - Verification is always appropriate

**Current workaround**: None needed (verification is good practice)

---

## 7. INTEGRATION POINTS

### Where New Solutions Can Plug In

#### Adding a New Claim Type

**Interface**: Add regex pattern to `artifact_claims.py`

```python
# In artifact_claims.py
_MY_NEW_CLAIM_PATTERNS = [
    re.compile(r"\b(?:my_pattern_here)\b", re.I),
]

# In extract_artifact_claims()
if any(p.search(s) for p in _MY_NEW_CLAIM_PATTERNS):
    claim_type = "my_new_type"
```

**Invocation model**: Automatic (called by `extract_artifact_claims()`)

**Data exchange**:
- Input: Response text (str)
- Output: Claim type added to `ArtifactClaim.claim_type`

---

#### Adding a New Artifact Pattern

**Interface**: Add regex to `_ARTIFACT_TOKEN_RE`

```python
# In artifact_claims.py
_ARTIFACT_TOKEN_RE = re.compile(
    r"""
    # ... existing patterns ...
    |
    # My new artifact type
    (?P<my_type>
        [A-Za-z0-9_\-./\\]+\.(?:my_ext)
    )
    """,
    re.I | re.VERBOSE,
)
```

**Invocation model**: Automatic (called by `_find_artifact_in_text()`)

**Data exchange**:
- Input: Sentence text (str)
- Output: Artifact token extracted (str or None)

---

#### Adding a New Detail Token Pattern

**Interface**: Add regex to `_DETAIL_RE`

```python
# In artifact_claims.py
_DETAIL_RE = re.compile(
    r"""
    # ... existing patterns ...
    |
    # My new detail token
    (?:my_pattern_here)
    """,
    re.I | re.VERBOSE,
)
```

**Invocation model**: Automatic (called by `_has_concrete_detail()`)

**Data exchange**:
- Input: Sentence text (str), target artifact (str)
- Output: `bool` (True if detail found)

---

### Hook Integration Points

#### Stop Hook Registration

**Purpose**: Gate is registered in `IN_PROCESS_GATES` list

**Registration**:
```python
IN_PROCESS_GATES = [
    ("safety_gate", _run_safety_gate),
    ("skill_first_stop_gate", _run_skill_first_stop_gate),
    ("behavior_audit", _run_behavior_audit),
    ("unverified_artifact_claims", _run_unverified_artifact_claims),  # ← Position 4
    ("behavior_gates_agreement", _run_behavior_gates_agreement),
    # ... remaining gates ...
]
```

**Gate position**: After `behavior_audit`, before `behavior_gates_agreement`

**Rationale**: Gate should run after behavioral audit but before agreement checks

---

#### Shared Helpers Integration

**Purpose**: Reuse meta-conversation/self-referential detection

**Integration**:
```python
# In Stop.py
from __lib.shared_helpers import is_meta_conversation, is_self_referential

# In _run_unverified_artifact_claims()
if is_meta_conversation(transcript):
    return None

if is_self_referential(response):
    return None
```

**Benefit**: Avoids duplicate pattern definitions, ensures consistency

---

## 8. APPENDIX: SAMPLE RUNS / LOGS

### Sample 1: Block - No Tool, No Observation

**Scenario**: AI claims fix without verification

**Stop input**:
```json
{
  "response": "The bug in config.json is fixed.",
  "tool_calls": "[]"
}
```

**Stop output**:
```json
{
  "decision": "block",
  "reason": "UNVERIFIED_ARTIFACT_CLAIMS:\n\nStrong claims about artifacts/outcomes without verification evidence.\nFor each claim: use a verification tool on the artifact AND cite a concrete observation.\n\n- \"The bug in config.json is fixed.\"\n  Artifact: config.json\n  Issue: no verification tool touched this artifact this turn\n",
  "blocking_hook": "Stop.py:unverified_artifact_claims"
}
```

**Exit code**: 2 (block)

---

### Sample 2: Block - Tool Without Observation

**Scenario**: AI reads file but provides no concrete details

**Stop input**:
```json
{
  "response": "The bug in config.json is fixed.",
  "tools_used": [
    {"name": "Read", "input": {"file_path": "config.json"}}
  ]
}
```

**Stop output**:
```json
{
  "decision": "block",
  "reason": "UNVERIFIED_ARTIFACT_CLAIMS:\n\nStrong claims about artifacts/outcomes without verification evidence.\nFor each claim: use a verification tool on the artifact AND cite a concrete observation.\n\n- \"The bug in config.json is fixed.\"\n  Artifact: config.json\n  Issue: tool used but response lacks concrete observation (file:line, specific value, etc.)\n",
  "blocking_hook": "Stop.py:unverified_artifact_claims"
}
```

**Exit code**: 2 (block)

---

### Sample 3: Allow - Tool + Observation

**Scenario**: AI reads file and cites line number

**Stop input**:
```json
{
  "response": "I found the issue at line 42 where the api_key was missing. The bug in config.json is fixed.",
  "tools_used": [
    {"name": "Read", "input": {"file_path": "config.json"}}
  ]
}
```

**Stop output**:
```json
{
  "decision": "allow"
}
```

**Exit code**: 0 (allow)

---

### Sample 4: Block - Outcome-Only Fix Without Bash

**Scenario**: AI claims "bug is fixed" without running tests

**Stop input**:
```json
{
  "response": "The bug is fixed and everything works now.",
  "tools_used": [
    {"name": "Read", "input": {"file_path": "some_file.py"}}
  ]
}
```

**Stop output**:
```json
{
  "decision": "block",
  "reason": "UNVERIFIED_ARTIFACT_CLAIMS:\n\nStrong claims about artifacts/outcomes without verification evidence.\nFor each claim: use a verification tool on the artifact AND cite a concrete observation.\n\n- \"The bug is fixed and everything works now.\"\n  Issue: no verification tool AND no concrete observation\n",
  "blocking_hook": "Stop.py:unverified_artifact_claims"
}
```

**Exit code**: 2 (block)

---

### Sample 5: Allow - Outcome-Only Fix With Bash

**Scenario**: AI runs tests and cites results

**Stop input**:
```json
{
  "response": "I ran the test suite and all 15 tests passed. The bug is fixed and everything works now.",
  "tools_used": [
    {"name": "Bash", "input": {"command": "pytest tests/"}}
  ]
}
```

**Stop output**:
```json
{
  "decision": "allow"
}
```

**Exit code**: 0 (allow)

---

### Sample 6: Allow - Meta-Conversation Excluded

**Scenario**: User asks "why did you do that?"

**Stop input**:
```json
{
  "response": "I used that pattern because it's more maintainable.",
  "transcript": [
    {"role": "user", "content": "Why did you use a factory pattern?"}
  ]
}
```

**Stop output**:
```json
{
  "decision": "allow"
}
```

**Exit code**: 0 (allow)

**Reason**: `is_meta_conversation()` returned `True`, gate skipped

---

### Sample 7: Allow - Self-Referential Excluded

**Scenario**: AI apologizes for mistake

**Stop input**:
```json
{
  "response": "I apologize, I misread the file. Let me check again.",
  "transcript": []
}
```

**Stop output**:
```json
{
  "decision": "allow"
}
```

**Exit code**: 0 (allow)

**Reason**: `is_self_referential()` returned `True`, gate skipped

---

### Sample 8: Block - Root Cause Without Verification

**Scenario**: AI claims root cause without reading code

**Stop input**:
```json
{
  "response": "The root cause is a missing import in validator.py.",
  "tool_calls": "[]"
}
```

**Stop output**:
```json
{
  "decision": "block",
  "reason": "UNVERIFIED_ARTIFACT_CLAIMS:\n\nStrong claims about artifacts/outcomes without verification evidence.\nFor each claim: use a verification tool on the artifact AND cite a concrete observation.\n\n- \"The root cause is a missing import in validator.py.\"\n  Artifact: validator.py\n  Issue: no verification tool touched this artifact this turn\n",
  "blocking_hook": "Stop.py:unverified_artifact_claims"
}
```

**Exit code**: 2 (block)

---

### Sample 9: Block - Characterization Without Evidence

**Scenario**: AI claims file is "generic" without verification

**Stop input**:
```json
{
  "response": "The logo.png is generic and should be replaced.",
  "tool_calls": "[]"
}
```

**Stop output**:
```json
{
  "decision": "block",
  "reason": "UNVERIFIED_ARTIFACT_CLAIMS:\n\nStrong claims about artifacts/outcomes without verification evidence.\nFor each claim: use a verification tool on the artifact AND cite a concrete observation.\n\n- \"The logo.png is generic and should be replaced.\"\n  Artifact: logo.png\n  Issue: no verification tool AND no concrete observation\n",
  "blocking_hook": "Stop.py:unverified_artifact_claims"
}
```

**Exit code**: 2 (block)

---

### Sample 10: Allow - Multiple Claims With Verification

**Scenario**: AI makes multiple claims, all verified

**Stop input**:
```json
{
  "response": "I checked validator.py and found the missing import at line 15. The root cause is a missing import in validator.py. I ran the tests and all 15 tests passed. The bug is fixed now.",
  "tools_used": [
    {"name": "Read", "input": {"file_path": "validator.py"}},
    {"name": "Bash", "input": {"command": "pytest tests/"}}
  ]
}
```

**Stop output**:
```json
{
  "decision": "allow"
}
```

**Exit code**: 0 (allow)

**Reason**: All claims have both tool verification AND concrete observations

---

## END OF BUNDLE

**Next steps for LLM question-answering**:

1. **For architectural questions**: Consult Section 2 (Architecture Overview) and Section 5 (Design Intent)
2. **For behavioral questions**: Consult Section 3 (Execution and Data Flow) and Section 4 (Component Inventory)
3. **For integration questions**: Consult Section 7 (Integration Points)
4. **For debugging**: Consult Section 6 (Known Issues) and Section 8 (Sample Runs)

**Critical constraints to remember**:
- Claims require BOTH tool usage AND concrete observation
- Fail-open policy (errors allow responses)
- In-process execution (no subprocess)
- Meta-conversations and self-referential content are excluded
- Outcome-only fix claims require Bash (test execution)
