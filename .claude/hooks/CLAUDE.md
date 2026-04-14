# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Hooks Directory Architecture

This directory implements the **Cognitive Steering Framework (CSF)** - structural enforcement hooks that provide deterministic control over Claude Code behavior.

### Quick Navigation

| Section | Purpose |
|---------|---------|
| Hook Edit Verification | **Read first** - Before editing ANY hook file |
| Systemic Issues | Historical context and fixes |
| Dispatch Chain | How hooks are registered and called |

### Hook Edit Verification (MANDATORY)

**PROBLEM**: LLMs repeatedly edit dead files that are not in the dispatch chain, causing fixes that never run and persistent deadlocks.

**SOLUTION**: Before editing ANY file in P:/.claude/hooks/, verify it's actually called by checking the dispatch chain manifest.

**Pre-Edit Checklist**:
1. Read P:/.claude/hooks/PreToolUse.py
2. Search for "DISPATCH CHAIN" comment block
3. Confirm your target file appears in UNIVERSAL or TOOL_HOOKS lists
4. DO NOT edit any PreToolUse_*.py file that's not in the dispatch chain

**Quick Verification Command**:
```bash
# Check if file is in dispatch chain
grep -n "UNIVERSAL\|TOOL_HOOKS" P:/.claude/hooks/PreToolUse.py | grep -i "your_file_name"
```

**Example**:
- ✅ Allowed: PreToolUse/PreToolUse_skill_pattern_gate.py (in UNIVERSAL)
- ❌ Prohibited: PreToolUse_skill_first_gate.py (NOT in dispatch chain)

**Files NEVER to edit** (dead, standalone):
- PreToolUse_skill_first_gate.py
- PreToolUse_workflow_steps_gate.py (deleted)

---

### Systemic Issues and Fixes

**PROBLEM**: Five systemic issues were causing LLMs to repeatedly edit dead code and create persistent deadlocks.

#### Fix 1: Dispatch Chain Documentation (REQ-001, REQ-005)

**Issue**: LLMs repeatedly put fixes in `PreToolUse_skill_first_gate.py` or `PreToolUse_workflow_steps_gate.py`, neither of which are in the actual dispatch chain.

**ACT-001 Audit (2026-04-12)**: Verified ZERO active Edit/Write hooks have `sys.stderr.write()` after commit 20d03ba fixed `PreToolUse_skill_pattern_gate.py`. Only 5 non-active files remain with stderr (dead code, tests, libraries).

**Solution**: Added authoritative "DISPATCH CHAIN" comment block at the top of `PreToolUse.py` that documents:
- Actual execution order (what really runs)
- Files in the dispatch chain (UNIVERSAL hooks, TOOL_HOOKS)
- Dead files that are NOT in the dispatch chain

**Result**: LLMs can now verify which files are actually called before editing.

**Implementation**: See `P:/.claude/hooks/PreToolUse.py` lines 11-28

#### Fix 2: Dead Code Removal (REQ-002)

**Issue**: Dead code in `PreToolUse_skill_pattern_gate.py` (lines 568-586) contained `_read_pending_intent()` logic that could never execute because the intent file is deleted before this hook runs.

**Solution**: Removed the dead code block and helper functions:
- `_get_terminal_id()`
- `_safe_id()`
- `_parse_iso_timestamp()`
- `_intent_is_stale()`
- `_read_pending_intent()`

**Result**: Cleaner code with no unreachable branches.

**Implementation**: Removed from `P:/.claude/hooks/PreToolUse/PreToolUse_skill_pattern_gate.py`

#### Fix 3: Stop Hook System Failure Detection (REQ-003)

**Issue**: Stop hook incorrectly fired "SLASH COMMAND IGNORED" when the hook system itself blocked all tool attempts, shaming the LLM for a system failure.

**Solution**: Added tool_blocked detection logic that queries the hook ledger for `tool_invoked` vs `tool_blocked` events:
- If all invoked tools were blocked → suppress Stop hook (system failure)
- If partial blocking → fire Stop hook (genuine bypass or partial success)
- If no tool attempts → fire Stop hook (genuine bypass)

**Implementation**: See `P:/.claude/hooks/StopHook_skill_execution_gate.py` lines 854-873

**Key invariant**: `len(_invoked) > 0` ensures we only suppress when tools were actually attempted. A turn with no tool attempts still triggers the block normally.

#### Fix 4: Investigation Tools (REQ-004) - REMOVED

**Issue**: Originally thought diagnostic skills couldn't investigate their own blocking mechanism.

**Resolution**: After analysis, this was already fixed by Fix A in `PreToolUse.py` (deleting intent file when Skill is called). Pre-mortem skill can already use Read/Grep/Glob after calling Skill.

**Risk Avoided**: Adding `Read` to `_SKILL_FIRST_ALLOWED` would allow Claude to read `SKILL.md` files *before* calling Skill at all, weakening the skill-first protection.

**Implementation**: No changes needed - Fix A is sufficient.

#### Fix 5: Edit Verification Guidance (REQ-005)

**Issue**: No verification step for LLMs to confirm they're editing the right file before committing changes.

**Solution**: Added "Hook Edit Verification (MANDATORY)" section to `CLAUDE.md` with pre-flight checklist:
1. Read PreToolUse.py
2. Search for "DISPATCH CHAIN" comment
3. Confirm target file is in UNIVERSAL or TOOL_HOOKS lists
4. DO NOT edit files not in dispatch chain

**Result**: LLMs have clear guidance to verify dispatch chain before editing.

**Implementation**: See `P:/.claude/hooks/CLAUDE.md` "Hook Edit Verification (MANDATORY)" section

#### Fix 6: Linter Hook Removal (2026-03-29)

**Issue**: `lint_hook.py` ran `ruff check --fix` after every Edit/Write operation. During sequential edits (multi-step refactors), ruff could strip code from intermediate states (e.g., removing "unused" imports that were about to be used), silently corrupting code while pytest continued to pass.

**Root Cause**: Sequential-edit race condition — linters with `--fix` operate on intermediate file states between edit steps.

**What was removed**:
- `PostToolUse/lint_hook.py` — structurally disabled (removed from `posttooluse/__init__.py` registry, import commented)
- `PreToolUse_auto_format.py` — deleted (was advisory-only, never ran ruff, was misidentified as the culprit)
- `PreToolUse_mypy_type_check.py` — deleted (removed from dispatch but file remained)
- `tests/test_code_quality_checks.py` — deleted (orphaned test importing deleted module)

**Why structural removal not just flag disable**: `default_enabled=False` in the hook base class is bypassable via `LINT_ROUTER_ENABLED=true` env var. Only removal from the registry is durable.

**Kill Criteria** (rollback triggers):
- pytest fails on TF-IDF or cosine similarity tests
- `grep -r "tfidf\|cosine\|topic_alignment" core/` returns fewer results than before
- Any search result processing silently drops content between sequential edits

**Prevention**: No linter with `--fix` behavior runs between sequential Edit/Write operations. The PostToolUse registry in `posttooluse/__init__.py` is the authoritative list — verify `lint_hook` is not registered before re-enabling.

**Implementation**: See `posttooluse/__init__.py` lines 36 (import) and 147-152 (registry)

### Testing and Verification

**Test Coverage**:
- `test_dispatch_chain_verification.py` - Verifies dispatch chain documentation accuracy (5 tests)
- `test_stop_hook_ledger_check.py` - Verifies Stop hook tool_blocked detection logic (6 tests)
- `test_linter_hooks_disabled.py` - Verifies lint_hook structurally removed, dead files deleted (6 tests)

**Acceptance Tests**:
- Dispatch chain comment exists in PreToolUse.py ✅
- Dead code removed from PreToolUse_skill_pattern_gate.py ✅
- Stop hook distinguishes bypass vs system failure ✅
- CLAUDE.md has mandatory edit verification section ✅
- Lint hooks structurally disabled (lint_hook not in registry, dead files deleted) ✅
- All tests pass ✅

**No Regression**: Skill enforcement behavior unchanged - Fix A already handles skill-first gate correctly without widening `_SKILL_FIRST_ALLOWED`.

### Hook Events

| Event              | Trigger                  | Capability                                    |
| ------------------ | ------------------------ | --------------------------------------------- |
| `SessionStart`     | CLI session begins       | Initialize context, restore state             |
| `UserPromptSubmit` | Before prompt processing | Inject context, validate input                |
| `PreToolUse`       | Before tool execution    | **Block** actions, enforce prerequisites      |
| `PostToolUse`      | After tool completion    | Analyze output, detect failures               |
| `Stop`             | Response complete        | Validate success claims, enforce verification |

### Key Documentation

- `README.md` - Complete catalog and usage guide
- `ARCHITECTURE.md` - Constitutional enforcement mapping
- `PROTOCOL.md` - Hook input/output specifications

### Shared Utilities

```python
# State management (all hooks)
from shared_utils import load_state, save_state, clear_state, log_hook_event

# Constitutional hook tracking
from hook_tracker import is_hook_self_operation, is_bypass_enabled, log_block
```

**Bypass mechanism:** `export CONSTITUTIONAL_HOOKS_BYPASS=1`

### Logging Best Practices

**Rule**: Use stderr only for actual errors. Hook diagnostic output goes to stdout or structured logs.

Claude Code surfaces stderr as error output — use it for genuine hook errors only, not for debug traces or diagnostics.

**Correct Pattern**:
```python
import logging
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
# File-based logging for diagnostics
```

**Debug Mode**: Use stdout for debug output when environment flag set:
```python
if ROUTER_DEBUG:
    print("Debug info", file=sys.stdout)  # ✅ OK
```

### Observability Storage Policy

Keep diagnostics separated by value and failure mode:

- `logs/diagnostics/diagnostics.db`:
  authoritative, query-worthy structured events.
  Use for correlated hook/tool outcomes, blocks, errors, context, and assumptions.
- `logs/diagnostics/pretooluse_blocks.jsonl`:
  append-only fallback/detail stream for `PreToolUse` block RCA.
  This is the canonical flat-file block log for router and child-hook block events.
  Also written by `PreToolUse_ownership_colocation_gate.py` (_log_block): each
  blocked write attempt is appended with timestamp, hook, tool, and path fields.
- `logs/diagnostics/hook_runner_stderr.jsonl`:
  failsafe stderr capture from the universal runner.
  Use when a hook emitted stderr or when SQLite coverage is insufficient.
- `logs/diagnostics/ups_execution_trace.jsonl`:
  high-volume UserPromptSubmit execution trace.
  Keep file-based and rotate aggressively; do not treat as authoritative truth.
- Probe/canary logs:
  debug-only, opt-in where possible.
  Do not promote always-on heartbeats into SQLite.

**Do not add every log to SQLite.**
Use SQLite for events you will actually query during RCA. Keep bootstrap/failsafe
and high-volume traces in flat files so diagnostics still work when imports,
paths, or the DB itself are the failure.

### Importer Diagnostics

`hook_importer.py` writes importer anomalies to the shared SQLite diagnostics
database:

- Database: `P:/.claude/hooks/logs/diagnostics/diagnostics.db`
- Table: `importer_diagnostics`
- Fallback files: `hook_importer_*.jsonl` only if SQLite logging is unavailable

**What gets logged**:
- `load` - import/module execution failure during hook load
- `execute` - hook runtime exception or importer runtime failure
- `timeout` - hook exceeded importer timeout
- `stderr` - captured hook stderr was non-empty

**Recorded fields**:
- `hook_name`
- `phase`
- `session_id`
- `terminal_id`
- `tool_name`
- `input_hash`
- `input_bytes`
- `error_text`
- `traceback` when present

**How to inspect**:
```bash
python - <<'PY'
import sqlite3
conn = sqlite3.connect(r'P:/.claude/hooks/logs/diagnostics/diagnostics.db')
cur = conn.cursor()
cur.execute("""
    SELECT timestamp, hook_name, phase, session_id, terminal_id, tool_name, error_text
    FROM importer_diagnostics
    ORDER BY id DESC
    LIMIT 20
""")
for row in cur.fetchall():
    print(row)
PY
```

**Retention**:
- Default retention is 14 days
- Pruning runs at most once per 24 hours
- Optional `VACUUM` runs only after pruning and only when the DB exceeds the configured threshold

**Tuning env vars**:
- `CC_IMPORTER_RETENTION_DAYS`
- `CC_IMPORTER_VACUUM_INTERVAL_HOURS`
- `CC_IMPORTER_VACUUM_THRESHOLD_BYTES`

### Router Pattern

Consolidated routers reduce overhead:

- `UserPromptSubmit_router.py` - Consolidates multiple prompt hooks
- `PreToolUse_write_router.py` - Consolidates write validation
- `PostToolUse_system2.py` - Post-execution monitoring

### Sequential Thinking Hooks (NEW - 2026-03-17)

**Purpose**: Implements a Generate → Critique → Improve loop for enhanced reasoning quality through self-reflection.

**Problem Solved**: AI responses often lack critical self-analysis. This system enforces a three-phase reasoning cycle:
1. **Initial generation** - Provide the best answer
2. **Critique** - Analyze the answer for gaps, assumptions, weaknesses
3. **Improvement** - Synthesize a refined final answer

**Architecture** - Three-hook coordination:

| Hook | File | Purpose |
|------|------|---------|
| UserPromptSubmit | `UserPromptSubmit_sequential_thinking.py` | Detects trigger phrases and creates sessions |
| PreToolUse | `PreToolUse_sequential_thinking.py` | Injects mode-specific system messages |
| Stop | `StopHook_sequential_thinking.py` | Manages iteration and session completion |

**State Management**:
- Location: `P:/.claude/state/sequential-thinking/`
- Terminal-scoped: `{session_id}_{terminal_id}.json`
- State schema: session_id, trigger_phrase, current_iteration (0-2), mode, intermediate_answers[], final_answer, active flag

**Trigger Patterns**:
- `\bthink\s+step[- ]?by[- ]?step\b`
- `\bcritically\s+analyze\b`
- `\bimprove\s+your\s+reasoning\b`
- `\biterate\s+on\s+your\s+answer\b`

**Mode Messages**:
- **INITIAL** (iteration 0): "Generate your best answer using clear, step-by-step reasoning."
- **CRITIQUE** (iteration 1): "Identify logical gaps, assumptions, alternative perspectives, weaknesses."
- **IMPROVEMENT** (iteration 2): "Synthesize improved answer addressing critique points."

**Configuration**: No configuration needed - always active when triggered. Uses `max_iterations=2` by default (3 phases total).

**Test Coverage**: 19 tests in `test_sequential_thinking_hooks.py` covering trigger detection, mode injection, iteration management, multi-terminal isolation, and full pipeline integration. All pass in 0.58s.

**See Also**: Cognitive reasoning research (Generate → Critique → Improve pattern from self-reflection literature)

### State Management

- Location: `P:/.claude/state/`
- Each hook manages `{hook_name}_state.json`
- Session timeout: 2 hours inactivity

**Session reset:**

```bash
python P:/.claude/hooks/shared_utils.py new-session
```

### Constitutional Hooks (Blocking)

| Hook                                   | Enforces                             | Source          | CKS Integration |
| ------------------------------------- | ------------------------------------ | --------------- | --------------- |
| `PreToolUse_skill_pattern_gate.py`     | **Skill execution v4.0 - Layer 0 workflow_steps + v3.2 parallel validation** | v4.0 plan     | ✅ Daemon intent |
| `PreToolUse_vague_directive_gate.py`   | Vague directive → architecture first | CLAUDE.md       | ✅ Pattern retrieval |
| `PreToolUse_directory_policy.py`        | Path protection                      | Settings        | ❌ None |
| `PreToolUse_hook_edit_gate.py`         | Test before editing hooks            | Settings        | ❌ None |
| `PreToolUse_tdd_gate.py`               | TDD mandate                          | CLAUDE.md       | ❌ None |
| `PreToolUse_authorization_gate.py`     | Planning mode detection              | authority-check | ✅ Decision retrieval |
| `PreToolUse_investigation_gate.py`     | Investigation before modification     | CLAUDE.md       | ✅ Pattern retrieval |
| `PreToolUse_ownership_colocation_gate.py` | Block writes to shared-infra paths without consumer-count evidence | pre-mortem plan | ❌ None |

**Architectural Recommendation Detection** (NEW - 2026-03-12):

**Purpose**: Prevents lazy pattern-matching recommendations without reading actual architecture files.

**Problem Solved**: Claude suggested "move Persona Memory to /main or cognitive-stack" based on keyword "cognitive" without reading /s/SKILL.md to verify actual fit. This caused incorrect destination recommendations and wasted user time.

**Detection Patterns**:
- "move X to Y", "belongs in Z", "should go to /skill"
- Common destinations: cognitive-stack, main, /s, /all, /arch
- Pattern: `(?:move|belongs|suggest|put|fit).+(?:cognitive-stack|main|/[\w-]+)`

**Block Message**:
```
⛔ ARCHITECTURAL RECOMMENDATION WITHOUT INVESTIGATION

You suggested: "move X to cognitive-stack"

Before recommending destinations:
1. Read target skill/file SKILL.md to understand actual purpose
2. Verify architectural fit (don't pattern-match on keywords)
3. Then recommend based on evidence, not assumptions

Example: If suggesting /s for Persona Memory:
  Read: P:/.claude/skills/s/SKILL.md
  Verify: Does /s generate multi-persona outputs? (Yes)
  Then: Recommend move to /s

To bypass: Add --allow-arch-rec to your message
Source: plan-20260312-anti-laziness-arch-verification.md
```

**Configuration**:
- `CSF_ARCH_RECOMMENDATION_GATE` (default: `true`) - Enable/disable the gate
- Set to `false` to disable: `export CSF_ARCH_RECOMMENDATION_GATE=false`

**Bypass Flag**: `--allow-arch-rec` (allows specific recommendations without investigation)

**Test Coverage**:
- 8 unit tests covering:
  - Block recommendation without reading architecture files
  - Allow after reading SKILL.md/CLAUDE.md/architecture.md
  - Bypass flag functionality
  - False positive handling (legitimate refactoring)
  - Destination pattern detection
  - /hook-audit integration
- All tests pass in 0.48s

**Implementation**: Extended `PreToolUse_investigation_gate.py` with architectural recommendation detection

**Implementation Date**: 2026-03-12

**Related**: See `lazy_patterns.md` for other lazy-closure behaviors this gate prevents.
| `PreToolUse_dependency_verification_gate.py` | External dependency verification before installation | exa incident | ❌ None |
| `PreToolUse/secret_scanner.py`         | Secret detection in files/git        | safety-hooks    | ❌ None |
| `PreToolUse_credential_filter.py`      | Credential leakage prevention        | safety-hooks    | ❌ None |
| `recursive_failure_detector.py`        | Catch-22 detection                   | CLAUDE.md       | ❌ None |
| `runaway_session_detector.py`          | Runaway session detection (Stop)      | safety-hooks    | ❌ None |
| `StopHook_skill_execution_gate.py`     | **Skill execution v3.5 - Three-layer defense with instruction format + bypass detection** | plan-20260312 | ❌ None |
| `StopHook_spec_compliance.py`          | Spec deviation detection             | CLAUDE.md       | ❌ None |
| `StopHook_reality_check.py`            | Reality verification, dead code      | CLAUDE.md       | ❌ None |
| `StopHook_cross_validator.py`          | Empirical verification for "fixed" claims | Settings  | ❌ None |
| `StopHook_unverified_stance.py`        | Anti-sycophancy stance detection (skeptical language without verification) | plan-20260304 | ❌ None |
| `PostToolUse_output_sanitizer.py`      | Output redaction for secrets         | safety-hooks    | ❌ None |
| `constitutional_enforcer.py`           | Anti-sycophancy                      | CLAUDE.md       | ❌ None |
| `observable_effect_verifier.py`       | Observable effect verification (SEV) - verify expected side effects from code changes | plan-20260304 | ❌ None |
| `integration_verifier.py`             | Integration verification - prevents aspirational documentation in SKILL.md files | plan-20260304 | ❌ None |

### Reduced Stop Strategy

Stop hooks are the backstop, not the primary behavior shaper.

Prefer to prevent bad outputs earlier by:

- injecting a compact response behavior contract in `UserPromptSubmit`
- requiring direct answers, evidence labels, and explicit uncertainty
- keeping style and pacing guidance lightweight and repetitive only when needed
- treating Stop as the final safety net for hard violations

Keep block decisions focused on high-confidence contract breaks:

- unverified factual claims
- tool or execution misrepresentation
- explicit bypasses of required workflow or policy

Use advisory or telemetry-only hooks for:

- tone cleanup
- response structure nudges
- generic reasoning polish
- low-confidence quality issues that do not justify a hard block

### Integration Verifier

**Purpose**: PostToolUse hook that prevents aspirational documentation by verifying skill integration claims.

**Problem Solved**: Skills document `suggest:` targets that don't exist or don't reciprocate, creating aspirational documentation that misleads users.

**Architecture**:
- **Detection**: Parses SKILL.md frontmatter for `suggest:` field
- **Verification**: Checks that suggested targets exist in skills directory
- **Reciprocity Check**: Verifies bidirectional integration (A suggests B → B should suggest A)
- **Fallback**: Regex extraction if YAML parsing fails

**Configuration**:
- `INTEGRATION_VERIFIER_ENABLED` (default: `true`) - Enable/disable the hook
- `INTEGRATION_VERIFIER_MODE` (default: `warn`) - Warn mode (true) or block mode (false)

**Test Coverage**:
- 9 unit tests covering skip patterns, detection scenarios, positive/negative cases
- All tests pass in 0.22s

**Example Warning**:
```
⚠️ INTEGRATION VERIFIER WARNING

SKILL.md suggests non-existent skill: /nonexistent-skill

Missing integration:
  • /code suggests /async-bugs, but /async-bugs doesn't reciprocate

Fix: Add bidirectional integration or remove suggest: target
```

**Implementation**: `posttooluse/integration_verifier.py`

---

### Verification Enforcement Gate (NEW - 2026-03-14)

**Purpose**: Stop hook that enforces verification step completion before allowing responses to complete.

**Problem Solved**: Skills declare verification steps in workflow_steps frontmatter, but AI might try to stop before completing them, creating incomplete or unverifiable work.

**Architecture**:
- **Detection**: Queries breadcrumb trails for pending verification steps (steps with `kind: verification` not in completed_steps)
- **Enforcement**: Blocks when `VERIFICATION_ENFORCEMENT_ENABLED=true` and pending verification detected
- **Bypass**: Allows `--skip-verification` flag for edge cases
- **Graceful Failure**: Fails open on errors to prevent blocking due to system failures

**Configuration**:
- `VERIFICATION_ENFORCEMENT_ENABLED` (default: `false`) - Enable/disable enforcement
- Set to `true` to enable: `export VERIFICATION_ENFORCEMENT_ENABLED=true`

**Bypass Flag**: `--skip-verification` (allows specific turns without completing verification)

**Test Coverage**:
- 8 unit tests covering:
  - Disabled by default behavior
  - No trails scenario
  - Pending verification steps blocking
  - All steps complete allowing
  - Bypass flag functionality
  - Multiple pending steps
  - Mixed step formats (string/dict)
  - Graceful failure on errors
- All tests pass in 0.33s

**Example Block Message**:
```
PENDING VERIFICATION STEPS DETECTED

The following verification steps must be completed before stopping:
  • code:tier0_checklist_verification
  • plan-workflow:verify_checklist_completion

To bypass for this turn: Add --skip-verification to your message
To disable enforcement: Set VERIFICATION_ENFORCEMENT_ENABLED=false
```

**Implementation**: Stop.py `_run_verification_enforcement()` function (in-process gate)

**Related**: See `plan-verify-integration-complete.md` for complete architecture overview

---

### Honesty Contract (Proactive Honesty Enforcement)

**Purpose**: Prevent false completion claims and enforce transparency about what has NOT been verified.

**Problem Solved**: AI claimed "Implementation Complete: Gate is live and ready for production" after writing code + tests, but module wasn't in `core_hook_modules` registry so it never ran. User feedback: "I would still respect you, in fact more because you were honest."

**Three Principles**:

1. **Never claim completion beyond verified reality**
   - Don't say "done/complete/live/ready" if you haven't verified the full execution path
   - Unit tests passing ≠ integrated and working
   - Code written ≠ wired into the system

2. **Always state what remains unverified**
   - "I've built X and tested it in isolation, but haven't verified it's wired into the system yet"
   - "This passes unit tests, but I need to check if it's actually registered/loaded"
   - "I'm 80% done - still need to verify the integration step"

3. **Prefer honest uncertainty over confident guessing**
   - Say "I don't know / not verified yet" instead of assuming success
   - Ask for clarification instead of presuming intent
   - Flag uncertainties explicitly before claiming outcomes

**File Patterns Where This Applies**:
- Registry/decorator-based systems (decorators don't run if module never imported)
- Hook systems (verify module is in the load list)
- Configuration-driven features (verify config actually references your code)
- Plugin systems (verify plugin is actually loaded/enabled)

**Anti-Pattern**: Complete code + tests → claim "production ready" → discover it was never integrated.

**Related Memory**: `proactive-honesty.md`

---

### Fabrication Detection Enforcement (NEW - 2026-03-17)

**Purpose**: Stop hook that detects and blocks fabrication claims - claiming actions occurred when no tool execution evidence exists.

**Problem Solved**: AI agents fabricate tool usage, test results, or research attempts to avoid actual work:
- "I tried WebSearch but got 429 error" → Avoids search without actually trying
- "External research was blocked by API quota" → Fabricates technical obstacle
- "I ran pytest and all tests passed" → Skips actual testing
- "I just verified the fix works" → Avoids verification step

**Architecture**:
- **Detection**: Pattern matching against ACTION_CLAIM_PATTERNS in `__lib/claim_patterns.py`
- **Cross-Validation**: Checks tool execution evidence in session history
- **Enforcement**: Blocks when fabrication claim detected without tool evidence
- **Tentative Language**: Excludes hedging patterns ("would need to", "should check", "might search")

**Configuration**:
```bash
# Enable fabrication detection (default: true)
export STOP_CROSS_VALIDATOR_ENABLED=true

# Set enforcement mode
export STOP_CROSS_VALIDATOR_MODE=strict  # Block all fabrication claims
export STOP_CROSS_VALIDATOR_MODE=permissive  # Allow tentative language
export STOP_CROSS_VALIDATOR_MODE=disabled  # Turn off detection
```

**Real vs Fabricated Error Distinction**:

REAL Error (Allowed):
```
✅ "I ran WebSearch and got this error: [actual tool output showing 429]"
   Evidence: WebSearch tool event exists in session history
```

FABRICATED Error (Blocked):
```
❌ "I tried WebSearch but got 429 error"
   Evidence: No WebSearch tool event in session history
```

**Should Block vs Should Allow Examples**:

BLOCK (Fabrication detected):
- ❌ "I tried WebSearch but got 429" + no WebSearch event → BLOCK
- ❌ "External research was blocked by API quota" + no research attempt → BLOCK
- ❌ "I ran pytest and it passed" + no pytest event → BLOCK
- ❌ "I just verified the fix works" + no verification evidence → BLOCK
- ❌ "I searched but found nothing" + no search event → BLOCK
- ❌ "attempted to search for pattern" + no search attempt → BLOCK

ALLOW (Valid response):
- ✅ "I would need to search for X" → Tentative language
- ✅ "We should check if Y exists" → Suggestion format
- ✅ "I might search for the pattern" → Hypothetical
- ✅ "We could try fetching the data" → Tentative proposal
- ✅ "I did not use TDD" → Process statement (not action claim)
- ✅ "I only ran py_compile" → Process statement (not action claim)

**ACTION_CLAIM_PATTERNS List**:
```python
# From __lib/claim_patterns.py
ACTION_CLAIM_PATTERNS = [
    # Fake obstacle claims
    r"(?i)I\s+(?:tried|attempted)\s+(?:to\s+)?(?:search|websearch|fetch)\s+.*(?:429|403|401|error)",
    r"(?i)external\s+research\s+(?:was|is)\s+blocked",
    r"(?i)API\s+(?:quota|limit|balance)\s+(?:exceeded|reached|insufficient)",
    r"(?i)got\s+(?:error|exception)\s+.+429",

    # Fake verification claims
    r"(?i)^(?:i\s+)?(?:ran|executed|used|tried)\s+(?:pytest|test|npm|pip)",
    r"(?i)^(?:i\s+)?(?:just|already)\s+(?:verified|checked|confirmed)",
    r"(?i)I\s+(?:just|already)\s+(?:ran|executed)\s+.*(?:test|verify)",

    # Fake research claims
    r"(?i)I\s+searched\s+(?:.+?\s+)?but\s+found\s+nothing",
    r"(?i)attempted\s+(?:to\s+)?(?:search|fetch|websearch)",
    r"(?i)search\s+(?:returned|found)\s+nothing",
]
```

**Tentative Language Patterns** (Excluded from blocking):
```python
tentative_patterns = [
    r"(?i)would\s+need\s+to",
    r"(?i)should\s+(?:check|verify|search)",
    r"(?i)might\s+(?:search|check|verify)",
    r"(?i)could\s+(?:try|attempt)",
    r"(?i)we\s+could\s+search",
]
```

**Example Block Message**:
```
⛔ FABRICATION CLAIM DETECTED

You claimed: "I tried WebSearch but got 429 error"

No WebSearch tool execution found in session evidence.
Fabrication claims are blocked to ensure honest communication.

Valid alternatives:
• "I would need to search for X" (tentative)
• "We should check if Y exists" (suggestion)
• Show actual tool execution with error output (real error)

To disable: export STOP_CROSS_VALIDATOR_MODE=disabled
```

**Implementation**:
- `StopHook_cross_validator.py` - Cross-validates claims against tool evidence
- `__lib/claim_patterns.py` - ACTION_CLAIM_PATTERNS definition
- `has_action_claim()` - Detection function with tentative language filtering

**Test Coverage**:
- Self-test in `claim_patterns.py` with 17 test cases
- Covers fabrication claims, tentative language, and process statements
- All tests pass: `python __lib/claim_patterns.py`

**Related Systems**:
- **Honesty Contract**: Enforces transparency about unverified work
- **Verification Enforcement**: Ensures verification steps complete
- **Absence Claim Protocol**: Verifies negative claims with evidence

---

### Anti-Lazy Declaration Enforcement (NEW - 2026-03-16)

**Purpose**: Two-hook system that enforces actual template updates when AI declares intent to modify architecture files, preventing "Declaration ≠ Execution" pattern.

**Problem Solved**: From Perplexity analysis (`C:\Users\brsth\Downloads\How can we fix this in claude code on windows 11_.md`):

1. **Declaration ≠ Execution**: LLM responds with intent ("I'll update the template") but stops at verbal agreement without invoking Write/Edit tools
2. **No Cross-Session Persistence**: Each conversation starts fresh - templates must be written during session or learning is lost
3. **Missing Anti-Lazy Enforcement**: Without accountability, declarative responses substitute for execution
4. **Template Updates Skip Step 2**: "I'll do it" responses often skip actual Edit/Write entirely

**Architecture - Two-Hook Coordination**:

**Hook 1: Declaration Reminder** (UserPromptSubmit)
- **Implementation**: `UserPromptSubmit_modules/declaration_reminder.py`
- **Mechanism**: Detects template update declaration patterns and stores state
- **Detection Patterns**:
  ```python
  # Handles both straight (') and curly (') apostrophes
  r"\bi['']ll\s+(?:update|edit|modify|add to|fix|change)\s+(?:the\s+)?(?:template|arch/|arch(?:\s+file)?|SKILL\.md)"
  r"\bi['d]\s+(?:like to|love to|want to|going to)\s+(?:update|edit|modify|add to|fix)"
  r"\bi\s+(?:will|shall|going to)\s+(?:update|edit|modify|add to|fix|change)"
  r"\blet\s+me\s+(?:update|edit|modify|add to|fix|change)"
  r"\bi['m]\s+(?:going to|planning to|will)\s+(?:update|edit|modify|add to|fix)"
  r"\bi\s+should\s+(?:update|edit|modify|add to|fix)"
  r"[Nn]eed\s+to\s+(?:update|edit|modify|add to|fix)"
  r"\bhave\s+to\s+(?:update|edit|modify|add to|fix)"
  r"\bmust\s+(?:update|edit|modify|add to|fix)"
  ```
- **Path Extraction**: Extracts template path (defaults to `arch/base.md` if not specified)
- **State Storage**: Writes `arch_declaration_{terminal_id}.json` to `hooks/state/`
- **Reminder Injection**: Injects context message requiring Read → Edit → Show diff workflow
- **Priority**: 8.0 (runs before most UserPromptSubmit hooks)

**Hook 2: Arch-First Enforcer** (PreToolUse)
- **Implementation**: `PreToolUse_arch_first_enforcer.py`
- **Mechanism**: Blocks non-arch tools until template is updated
- **Detection**: Loads state file from `hooks/state/`
- **Blocking Logic**:
  - Allow: Read tool for declared arch file (clears state)
  - Allow: Edit/Write tools for declared arch file (clears state)
  - Block: All other tools until arch file is updated
- **Bypass Flag**: `--allow-skip-arch-update` in prompt message
- **Exit Codes**: 0 = allow, 2 = block

**State Coordination**:

Both hooks use `hooks/state/` directory for cross-hook communication:

```
P:/.claude/hooks/state/arch_declaration_{terminal_id}.json
{
  "path": "arch/base.md",  # or extracted path
  "timestamp": null
}
```

**Terminal Isolation**: State files are scoped by `terminal_id` for multi-terminal safety.

**Example Block Message**:
```
⛔ **TEMPLATE UPDATE REQUIRED FIRST**

You declared: "I'll update the template"

Before using Bash, you MUST:
1. **Read** the template file: `arch/base.md`
2. **Edit/Write** the change with diff
3. **Show** the explanation

**Why this matters**: Declaration ≠ Execution. You said you'd update the template,
but haven't invoked Read/Edit tools for `arch/base.md` yet.

To bypass this check: Add --allow-skip-arch-update to your message.

Complete the template update first, then proceed with other tools.
```

**Configuration**:

No configuration needed - hooks are always active. Use bypass flag for edge cases:
- Add `--allow-skip-arch-update` to prompt message to bypass for specific turn

**Test Coverage**:

**Declaration Reminder** (11 tests):
- `test_declaration_pattern_detection` - Positive/negative pattern matching
- `test_arch_path_extraction` - Path extraction from declarations
- `test_hook_returns_empty_for_non_declarations` - Non-declarations pass through
- `test_hook_injects_context_for_declarations` - Context injection on detection
- `test_state_file_creation` - State file created in correct location
- `test_multiple_declaration_patterns` - Various pattern formats
- `test_non_english_patterns` - No false positives on non-English
- `test_hook_context_contains_required_elements` - Reminder has all required phrases
- `test_terminal_id_extraction` - Terminal ID extraction from context
- `test_state_file_path_safety` - Path sanitization for safety
- `test_integration_workflow` - Full workflow: declaration → state → enforcement

**Arch-First Enforcer** (14 tests):
- `test_no_declaration_allows_all_tools` - No state = all tools allowed
- `test_read_arch_file_clears_state` - Reading declared arch file clears state
- `test_edit_arch_file_clears_state` - Editing declared arch file clears state
- `test_write_arch_file_clears_state` - Writing declared arch file clears state
- `test_non_arch_tools_blocked_with_declaration` - Non-arch tools blocked when declaration exists
- `test_bypass_flag_allows_tools` - Bypass flag allows tools
- `test_read_non_arch_file_blocked` - Reading non-arch files blocked
- `test_is_arch_file_function` - Arch file detection logic
- `test_state_file_operations` - State load/clear operations
- `test_get_terminal_id` - Terminal ID extraction
- `test_block_message_quality` - Block message has required elements
- `test_multi_terminal_isolation` - Different terminals have isolated state
- `test_windows_path_normalization` - Windows paths handled correctly
- `test_integration_workflow` - Full workflow: declaration → state → enforcement → clear

All tests pass: 25/25 tests in 0.68s

**Registration**:

- **UserPromptSubmit**: Registered in `UserPromptSubmit_modules/registry.py` as core_hook_module
- **PreToolUse**: Registered in `PreToolUse.py` UNIVERSAL hooks list

**Related**: See `plans/plan-20260316-extend-anti-lazy-declaration.md` for implementation details

**Analysis Integration**: Addresses all 4 root causes from Perplexity analysis:
1. Declaration ≠ Execution → declaration_reminder detects + arch_first_enforcer blocks
2. No Cross-Session Persistence → State files in hooks/state/ provide session continuity
3. Missing Anti-Lazy Enforcement → Combined hook system enforces execution
4. Template Updates Skip Step 2 → Forces Read → Edit → Show diff workflow

---

### Skill Enforcement Enhancement (v3.5 - 2026-03-12)

**Purpose**: Three-layer defense to ensure AI actually executes skill workflows instead of providing prose analysis.

**Problem Solved**: AI frequently ignores slash commands and responds with prose instead of loading the skill, wasting user time and violating the skill-first execution model.

**Architecture - Three-Layer Defense**:

**Layer 1: Instruction Format Enforcement** (UserPromptSubmit)
- **Implementation**: `UserPromptSubmit_modules/skill_enforcer.py`
- **Mechanism**: Replaces suggestion format with explicit "INSTRUCTION:" prefix
- **Format**:
  ```
  INSTRUCTION: Execute skill {command}

  Step 1: Call Skill("{command}") to load workflow
  Step 2: Follow the skill's documented procedure exactly

  Do NOT substitute your own analysis or improvise.
  ```
- **Effectiveness**: ~50% improvement over suggestion format (based on Scott Spense testing)

**Layer 2: Bypass Detection** (Stop)
- **Implementation**: `StopHook_skill_execution_gate.py` (v3.4 from archive)
- **Mechanism**: Detects when user types `/command` but AI responds with prose instead of executing
- **Detection**: Extracts user prompt from transcript, checks if slash command was ignored
- **Two-Strike Pattern**: Advisory on first bypass, hard block on second
- **Exemptions**: Built-in CLI commands, lightweight skills, knowledge skills
- **Effectiveness**: Additional 30% improvement when combined with Layer 1

**Layer 3: Pattern Gate** (PreToolUse)
- **Implementation**: `PreToolUse_skill_pattern_gate.py` (existing v3.2)
- **Mechanism**: Real-time blocking of unauthorized tool usage
- **Validation**: Parallel regex + daemon semantic validation
- **Effectiveness**: Primary defense (PreToolUse), Layer 2 is safety net

**Configuration**:
```bash
# Layer 1: Instruction format (always active)
# No configuration needed - uses explicit INSTRUCTION: format

# Layer 2: Bypass detection
SKILL_BYPASS_DETECTION_ENABLED=true   # Enable/disable bypass detection
SKILL_BYPASS_DETECTION_MODE=warn       # "warn" (advisory) or "block" (hard blocking)

# Layer 3: Pattern gate (existing)
SKILL_PATTERN_ENFORCEMENT_ENABLED=true
```

**Test Coverage**:
- Regression test: `tests/test_skill_guard_regression.py`
- Tests verify all debugRCA protocols are in place
- All tests pass in 0.29s

**Expected Outcomes**:

| Metric | Baseline | After Enhancement | Improvement |
|--------|----------|-------------------|-------------|
| Skills not invoked | ~40% | ~20% | 50% (Layer 1) |
| Skills invoked but not used | ~20% | ~6% | 70% (Layer 1+2) |
| Combined effectiveness | ~40% failure | ~6% failure | 85% total |

**Example Bypass Detection Block**:
```
SLASH COMMAND IGNORED

The user invoked /debugRCA but you responded with prose instead of executing it.

You MUST:
1. Use the Skill tool to load /debugRCA
2. Follow the skill's workflow instructions
3. Execute using the appropriate tools (Bash, Task, etc.)

Do NOT interpret slash commands as conversational text.
```

**Related**: See `plans/plan-20260312-skill-enforcement-enhancement.md` for complete implementation details

---

### Enforcement Tier System (v5.0 - 2026-03-18)

**Purpose**: Distinguish between skills that require strict enforcement and skills that allow flexible usage.

**Problem Solved**: Some skills (like /gto) need strict enforcement to ensure workflow compliance, while others (like /task) should be advisory to avoid interrupting legitimate workflows.

**Tier Definitions**:

| Tier | Behavior | When to Use |
|------|----------|-------------|
| `strict` | Blocks on violation | High-stakes skills where bypassing causes significant problems |
| `advisory` | Warns but allows | Low-stakes skills where flexibility is valuable |
| `none` | No enforcement | Skills that don't need workflow enforcement |

**Configuration** (in SKILL.md frontmatter):
```yaml
---
name: my-skill
enforcement: strict  # or 'advisory' or 'none'
---
```

**Selection Criteria**:

Use **strict** when:
- Bypassing the skill causes security issues, data loss, or system corruption
- The skill has complex multi-step workflows that must be followed exactly
- Users frequently try to bypass the skill

Use **advisory** when:
- The skill provides convenience features but direct tool usage is acceptable
- Blocking would interrupt legitimate workflows
- The skill is primarily for guidance/suggestions

Use **none** when:
- The skill is a knowledge skill (no execution workflow)
- The skill is a lightweight utility with no complex workflow

**Examples**:
- `/gto`: `strict` - Complex analysis workflow that must be followed for accurate results
- `/task`: `advisory` - Direct tool usage is acceptable; blocking interrupts legitimate work
- `/search`: `none` - Knowledge skill, no execution workflow

**Telemetry**:
- All enforcement events logged to `diagnostics.db` via `__lib/enforcement_telemetry.py`
- Compliance rate tracking: `SELECT * FROM enforcement_events WHERE tier = 'advisory'`
- Warning fatigue detection: Skills shown >3 times without behavior change

**Monitoring**:
```bash
# Check advisory compliance rate
python -c "from pathlib import Path; import sys; sys.path.insert(0, 'P:/.claude/hooks/__lib'); from enforcement_telemetry import get_advisory_compliance_rate; print(get_advisory_compliance_rate())"

# Detect warning fatigue in current session
python -c "from pathlib import Path; import sys; sys.path.insert(0, 'P:/.claude/hooks/__lib'); from enforcement_telemetry import detect_warning_fatigue; print(detect_warning_fatigue('your_session_id'))"
```

**Implementation**: See `__lib/enforcement_telemetry.py` for logging functions

**Rate Limiting** (v5.1 - 2026-03-18):

Session-scoped rate limiting prevents warning fatigue by showing each advisory warning only once per skill per session.

**Features**:
- Max 1 warning per skill per session
- Terminal-scoped isolation (different terminals see warnings independently)
- Session statistics tracking
- Clear history function for testing

**Usage**:
```python
from __lib.enforcement_rate_limiter import (
    should_show_warning,
    record_warning_shown,
    get_session_stats,
    clear_warning_history,
)

# Check if warning should be shown
if should_show_warning("task"):
    print("⚠️ ADVISORY: Use /task for enhanced workflow")
    record_warning_shown("task")

# Get session stats
stats = get_session_stats()
# {'total_warnings': 3, 'unique_skills': 3, ...}
```

**State File**: `.claude/state/enforcement_warnings_{session_id}.json`

**Monitoring**:
```bash
# View rate limiting stats
python -c "import sys; sys.path.insert(0, 'P:/.claude/hooks/__lib'); from enforcement_rate_limiter import get_session_stats; print(get_session_stats())"

# Clear warning history
python -c "import sys; sys.path.insert(0, 'P:/.claude/hooks/__lib'); from enforcement_rate_limiter import clear_warning_history; print(f'Cleared {clear_warning_history()} warnings')"
```

---

**Layer 0: Workflow Steps Enforcement** (v4.0 - 2026-03-12)

**Purpose**: Prevents AI from using tools before loading skills with declared workflow_steps, blocking BEFORE any wasted generation.

**Problem Solved**: Stop hook fires AFTER 370 lines of prose have been generated (too late). Layer 0 blocks at PreToolUse BEFORE the first tool executes, preventing wasted token generation entirely.

**Architecture**:
- **Detection**: Reads pending_command_intent state file written by skill_enforcer.py (UserPromptSubmit)
- **Verification**: Checks if skill has workflow_steps via breadcrumb tracker's _load_workflow_steps()
- **Blocking**: Blocks non-Skill tools when workflow_steps exist but Skill tool wasn't used first
- **Terminal Isolation**: Uses terminal-scoped state files to prevent cross-terminal contamination

**State File Format**:
```
P:/.claude/state/pending_command_intent_{terminal_id}.json
{
  "skill": "code",
  "prompt": "/code test",
  "timestamp": "2026-03-12T...",
  "session_id": "...",
  "terminal_id": "console_abc..."
}
```

**Example Block Message**:
```
⛔ SKILL WITH WORKFLOW STEPS DETECTED

The skill /code has 13 declared workflow steps:
  analyze_query_intent, select_execution_model, resolve_plan_state...

You must use the Skill tool to load /code before using other tools.

Step 1: Call Skill('code') to load the skill workflow
Step 2: Follow the skill's documented procedure
Step 3: Execute using the appropriate tools

Do NOT respond with prose analysis or use other tools first.
```

**Configuration**:
- No configuration needed - integrated into PreToolUse_skill_pattern_gate.py
- Graceful degradation: If workflow_steps check fails, allows tools (fail-open)

**Test Coverage**:
- 20 unit tests in tests/test_pretooluse_workflow_steps_gate.py
- Tests cover terminal isolation, intent file operations, blocking logic
- All tests pass in 0.44s

**Implementation**: Integrated into `PreToolUse_skill_pattern_gate.py` (Layer 0, lines 474-533)

**Related**: See `plans/plan-20260312-pretooluse-workflow_steps_gate.md` for complete implementation details

### Observable Effect Verifier (SEV)

**Purpose**: PostToolUse hook that verifies expected side effects from code changes actually occur.

**Problem Solved**: Code that declares observable effects (e.g., logging FileHandler) but doesn't verify they work (e.g., log files created).

**Architecture**:
- **Detection**: Pattern matching in code (e.g., `logging.FileHandler`)
- **Verification**: File system checks (e.g., log file exists, writable)
- **Effect Verifiers**: Modular system for different effect types
  - `LoggingEffectVerifier` - Verifies logging configurations produce log files
  - Extensible for other effects (database connections, network sockets, etc.)

**Configuration**:
- `SEV_ENABLED` (default: `true`) - Enable/disable the hook
- Performance baseline: <100ms latency requirement

**Usage Example**:
```python
# Code creates logging FileHandler
handler = logging.FileHandler('app.log')

# SEV verifies:
# 1. Detect pattern (logging.FileHandler found)
# 2. Extract config (log_path = 'app.log')
# 3. Verify effect (app.log exists, writable, or can be created)
# 4. Warn if verification fails
```

**Test Coverage**:
- 16 unit tests covering:
  - Skip patterns (conditional logging, env-based paths)
  - Verification scenarios (missing log files)
  - Positive/negative cases (FileHandler detection, no logging, non-Python files)
  - Performance baseline (<100ms)

**Implementation**: `posttooluse/observable_effect_verifier.py`, `posttooluse/effects/logging_effect.py`

### Unverified Stance Detection

**Purpose**: Stop hook that detects skeptical language without verification evidence (anti-sycophancy).

**Problem Solved**: AI casts doubt on user claims ("that sounds high", "let me verify") without actual verification.

**Detection Patterns**:
- **Sycophantic doubt**: "You're right to push back/question/be skeptical"
- **Empty hedge**: "Let me verify", "That sounds high", "I doubt that" (without verification tools)
- **Sycophancy inversion**: Apology + same dismissive conclusion ("I apologize... NOT A BUG")
- **Unfounded system claims**: "The system doesn't support X" (without evidence)

**Verification Tools** (exemptions from blocking):
- WebSearch, WebFetch, Bash, Read - When these tools are used, stance is considered verified

**Configuration**:
- `UNVERIFIED_STANCE_ENABLED` (default: `true`) - Enable/disable the hook
- `UNVERIFIED_STANCE_MODE` (default: `warn`) - Warn mode (true) or block mode (false)

**Test Coverage**:
- 9 unit tests covering detection scenarios, integration, output functions
- All tests pass in 0.22s

**Implementation**: `StopHook_unverified_stance.py`, `anti_sycophancy/unverified_stance_detector.py`

### Dependency Verification Gate

**Purpose**: PreToolUse hook that prevents "lazy configuration errors" by requiring verification of external dependencies before installation.

**Problem Solved**: AI assumes package names or makes configuration changes without verifying external dependencies first, causing 20+ minute wastes like the exa MCP server incident (wrong package name `@modelcontextprotocol/server-exa` vs actual `exa-mcp-server`).

**Detection Patterns**:
- **npm install**: `npm install @scope/package` or `npm install package-name`
- **pip install**: `pip install package-name`
- **cargo add**: `cargo add crate-name`

**Verification Commands** (allowed without blocking):
- npm: `npm view package`, `npm search package`, `npm show package`, `npm info package`
- pip: `pip search package`, `pip index versions package`
- cargo: `cargo search package`

**Local Package Exemptions** (allowed without verification):
- `npm install ./path` - Local directory installs
- `npm install file:./package.tgz` - File protocol installs

**Configuration**:
- `DEPENDENCY_VERIFICATION_ENABLED` (default: `true`) - Enable/disable the hook
- Set to `false` to disable: `export DEPENDENCY_VERIFICATION_ENABLED=false`

**Error Message Format**:
```
**Unverified Package Reference Detected**

The command references npm package '@scope/package' without prior verification.

Before installing, verify the package exists:
  npm: npm view @scope/package
  pip: pip search package-name
  cargo: cargo search crate-name

Command: npm install @scope/package
```

**Test Coverage**:
- 15 unit tests covering:
  - Positive cases (npm/pip/cargo install blocking)
  - Negative cases (verification commands allowed)
  - Edge cases (empty commands, malformed JSON, local installs)
  - All tests pass in 0.23s

**Architecture Decision**: Option A from /arch analysis (85% confidence)
- New standalone hook (not extending existing gates)
- Direct settings.json registration (router doesn't exist for PreToolUse)
- Single-responsibility for verification logic

**Implementation**: `PreToolUse_dependency_verification_gate.py`, `tests/test_dependency_verification_gate.py`

**Implementation Date**: 2026-03-08

#### Completion Claim Verification (NEW)

**Purpose**: Extended verification that detects and blocks premature "fixed"/"tested"/"verified" claims without runtime testing evidence.

**Problem Solved**: AI agents frequently declare completion ("✅ ALL FILES PASS", "fixed and tested", "verified working") without runtime testing evidence, causing premature victory declarations and user frustration.

**Detection Patterns**:
- "all (files|hooks|tests) pass"
- "✅ (complete|fixed|done)"
- "(issue|bug|problem) (is)? fixed"
- "test(s)? passed"
- "verified (and)? working"

**Runtime Evidence Requirements**:
- **Tool Usage**: Bash, Edit, Read, Grep, Glob
- **Command Patterns**: subprocess, pytest, python, node, npm test
- **Session Isolation**: Evidence scoped to session_id (multi-terminal safe)

**Preferred Evidence Interfaces**:
- Shared scope loader: `load_scoped_tool_events(...)` from `evidence_scope.py`
- Shared turn-scoped helper: `load_turn_scoped_events(...)` from `turn_scoped_evidence.py`
- Module-level adapters such as `StopHook_unverified_stance.load_tool_events(...)`
- `resolve_session_id(explicit: str = "") -> str` when a hook needs session normalization
- Event dict keys: `name`, `command`, `cwd`, `output_excerpt`, `session_id`, `terminal_id`

**Anti-patterns** (common mistakes to avoid):
- ❌ `read_session_context(session_id)` - Function takes 0 parameters
- ❌ `event.get("tool_name")` - Event dict uses `"name"` key
- ❌ `data.get("session_id")` - Stop hook input doesn't have session_id field
- ❌ Signal-based timeout on Windows - Use fail-open pattern instead

**Configuration**:
- Uses existing `UNVERIFIED_STANCE_ENABLED` and `UNVERIFIED_STANCE_MODE`
- Disable if too aggressive: `export UNVERIFIED_STANCE_ENABLED=false`

**Test Scenarios** (from plan-20260307-completion-claim-verification.md):
1. No session_id → check skipped (allow)
2. Session_id but no evidence → advisory (warn mode)
3. Session_id with Bash tool → allow
4. Multi-terminal isolation → blocks wrong session

**Test Coverage**:
- 11 unit tests (7 completion claim + 4 evidence_store integration)
- All tests pass in 0.29s

**Implementation**: Extended `StopHook_unverified_stance.py` with ~70 lines added after line 147

**Related Documentation**: `plans/plan-20260307-completion-claim-verification.md`

### Scanners

**Purpose**: Modular validation and analysis components that can be used by hooks for specialized detection tasks.

**Architecture**: All scanners extend `BaseScanner` with a `scan(text, context)` method returning `ScanResult`.

| Scanner                                  | Purpose                              | Integration        |
| ---------------------------------------- | ------------------------------------ | ------------------ |
| `scanners/hallucination_scanner.py`       | Hallucination detection (rule-based) | Stop hooks         |
| `scanners/agreement_consistency_scanner.py` | Response consistency checks        | Stop hooks         |
| `scanners/base_scanner.py`                | Abstract base class for all scanners | —                  |

### Strawberry Validator — DECOMMISSIONED

**Status**: `scanners/strawberry_validator.py` was **deleted** (policy violation: external Z.AI API call via httpx).

**What was removed**:
- Stage 2 LLM verification call to Z.AI API (glm-4-plus model)
- `ZAI_API_KEY` environment variable dependency
- All Stage 2 claim patterns (uncertain patterns that required LLM verification)

**Why**: Hooks must not make external API calls. The Z.AI httpx call violated the [Hook External Dependency Policy](#hook-external-dependency-policy).

**Current in-process replacements** (all rule-based, no external calls):

| Replacement Hook                         | Coverage                                         |
| ---------------------------------------- | ------------------------------------------------ |
| `Stop_unverified_existence_gate.py`      | Absence/existence claims (e.g., "no hook for X") |
| `StopHook_unverified_stance.py`          | Sycophantic doubt, empty hedges without evidence |
| `empirical_claims_gate.py`               | Completion/fix claims without runtime evidence   |
| `unified_claim_verifier.py`              | General claim verification (in-process patterns)  |
| `verification/engine.py`                  | Shared verification engine for structured checks  |

**Key invariant preserved**: Claim types that previously required Stage 2 LLM verification are now handled by rule-based gates or blocking hooks with tool-based evidence requirements — no external calls.

**Decommission test coverage**: `tests/test_strawberry_decommission.py` validates:
- Scanner file is deleted
- Not in `ACTIVE_RUNTIME_HOOKS` or `HOOK_SEQUENCE`
- Policy violation documented in `hook_external_llm_policy.md`

### Cleanup Verifier

**Purpose**: Automatic detection of missing cleanup steps based on work type.

**Architecture**: Two-component system
- **PostToolUse**: Tracks tool usage to session file (`state/cleanup_history_{session_id}.json`)
- **Stop**: Detects work type, checks cleanup requirements, warns about missing steps

**Implementation**: `posttooluse/cleanup_tracker_hook.py`, `Stop_cleanup_verifier.py`

**Supported Work Types**:
| Work Type | Detection Pattern | Cleanup Checks |
|-----------|-------------------|----------------|
| **bug_fix** | Edit + Read/Grep investigation | Document in bugfixes.md, git commit |
| **hook_dev** | Edit + hook files | Test changes, document in CLAUDE.md |
| **feature_dev** | Edit without investigation/docs | Update project CLAUDE.md |
| **testing** | Bash with pytest/test commands | Add tests to suite |
| **architecture** | Skill with "/arch" invocation | Create ADR in arch_decisions/ |
| **documentation** | Edit with doc patterns (README, CLAUDE.md, SKILL.md) | Check for broken references |

**Configuration**:
```bash
# Enable/disable (default: true)
export CLEANUP_VERIFIER_ENABLED=true

# Mode: warn (default) or block
export CLEANUP_VERIFIER_MODE=warn

# State directory (default: P:/.claude/state)
export CLEANUP_TRACKER_DIR=P:/.claude/state
```

**Test Coverage**:
- 19 unit tests covering tracker, loader, work type detection, cleanup checks
- All tests pass in 0.36s
- Tests verify: tool accumulation, file recovery, work type detection, missing cleanup steps

**Example Warning**:
```
⚠️ CLEANUP VERIFICATION WARNING

Work type detected: bug_fix

Missing cleanup steps:
  • Document bug fix in .serena/memories/bugfixes.md with date, problem, root cause, fix
  • Create git commit with descriptive message

Reference: .serena/memories/cleanup_patterns.md

To disable: export CLEANUP_VERIFIER_ENABLED=false
```

**Implementation Date**: 2026-03-05

### Claude-Restricted Paths**Purpose**: Prevents Claude from writing to directories reserved for user-authored content without explicit permission.**Enforced by**: `PreToolUse_directory_policy.py` → `PathValidator._is_claude_restricted_path()`**Configuration**: `P:/.claude/hooks/config/directory_policy.json` → `claude_restricted_paths`**Current restrictions**:- `docs/` - User project documentation (Claude writes to `.claude/docs/` instead)**Violation message**: `RESTRICTED_PATH: {suggested_alternative}`**When to use each location**:| Directory | Purpose | Written by ||-----------|---------|------------|| `docs/` | User-authored project documentation | Humans only || `.claude/docs/` | Claude-generated protocols, guides, technical docs | Claude |

### CKS Auto-Retrieval System

**Purpose**: Automatically surface relevant lessons from the Constitutional Knowledge System (CKS) when hooks block actions, preventing repeated mistakes.

**Implementation**: Trigger-based CKS retrieval in PreToolUse hooks

| Hook | Trigger Words | Entry Type | Advisory Shows |
|------|--------------|------------|----------------|
| `vague_directive_gate.py` | improve, optimize, refactor, architecture, system | pattern | Related patterns |
| `authorization_gate.py` | delete, destroy, reset, purge, wipe, drop | decision | Related decisions |
| `investigation_gate.py` | debug, investigate, diagnose, monitor, stuck, error | pattern | Related patterns |

**How it works**:
1. Hook detects trigger condition (e.g., vague directive)
2. Before blocking, hook queries CKS with user message
3. If relevant patterns/decisions found, advisory appended to block message
4. Graceful degradation - CKS failures don't break hooks

**Technical details**:
- Path setup: `sys.path.insert(0, str(__csf_src))` for CKS imports
- Query: `cks.search(query, entry_type='pattern|decision', limit=1)`
- Dict access: `r.get('title')` not `r.title` (CKS returns dicts)
- Exception handling: `(ImportError, AttributeError, OSError, RuntimeError)` - fail open

**Related systems**:
- **Smart Brain Search**: Auto-retrieval in CHS (18 uses, 100% success rate)
- **CKS**: SQLite + FAISS vector search at `P:/__csf/data/cks.db`
- **Entry types**: memory, pattern, code, knowledge, correction, decision, commitment, insight, learning

**Implementation date**: 2026-01-28 (Option A: Trigger-Based CKS Retrieval)

### Cross-Validation Hooks

**Purpose**: Enforce empirical verification for claims and hook edits, preventing procedural compliance without actual problem-solving.

**Problem Addressed**:
- AI claims "issue is fixed" without testing
- Reads router files (✓ used Read) but doesn't verify hook output (✗ didn't verify)
- Procedural compliance without actual problem-solving

**Environment Variables**:

| Env Var | Default | Purpose |
|---------|---------|---------|
| `CROSS_VALIDATION_HOOK_ENABLED` | false | Block "fixed" claims without verification |
| `CROSS_VALIDATION_VERBOSE` | false | Show warnings only (true) or block (false) |
| `HOOK_EDIT_VERIFICATION_ENABLED` | false | Require testing before editing hooks |

**Hooks**:

| Hook | Event | Layer | Description |
|------|-------|-------|-------------|
| `StopHook_cross_validator.py` | Stop | -1 | Block "fixed" claims without empirical verification |
| `PreToolUse_hook_edit_gate.py` | PreToolUse | 00 | Require testing before editing hooks |

**Research Basis**:
- Cross-Validation / Self-Verification (Duke, MIT CSAIL)
- Separation of generation and verification reduces confirmation bias
- Evidence Access Tracking (arXiv 2509.17995)

**Session Isolation**:
- Each terminal gets its own state directory: `.claude/state/cross_validation/{terminal_id}/`
- Uses `terminal_detection.py` for proper terminal/worktree isolation
- No cross-terminal bleed between concurrent sessions

### Intent/Goal Tracking Systems

**Purpose**: Detect intent drift, validate command intent, and flag un-hedged design narratives.

**Systems (4 total, 3 active)**:

| System | File | Status | Purpose |
|--------|------|--------|---------|
| Command Intent Gate | `PreToolUse_command_intent_gate.py` | ✅ Active | Validates bash commands match user's slash command intent |
| Narrative Intent Detector | `narrative_intent_detector.py` | ✅ Active | Warns on un-hedged design-intent/author-motivation claims |
| Intent Drift Scanner | `scanners/intent_drift_scanner.py` | ✅ Active | Detects scope expansion and drift from original user intent |
| Unified Intent Classifier | `shared/intent_classifier.py` | ⚠️ Dormant | Embedding-based semantic classification (unused, high-quality) |

**Command Intent Gate**:
- **Problem Solved**: User says `/ask-cli4 "review the plan"` but AI executes `python ask_cli.py --qwen-only` (unauthorized restriction)
- **Architecture**:
  - UserPromptSubmit stores `{skill, prompt}` in `state/pending_command_intent_{session_id}.json`
  - PreToolUse validates bash commands don't add restrictive flags
  - TTL: 5 minutes, auto-cleanup
- **Skills Protected**: ask-olymp, ask-cli, llm-debate, llm-review, universal-skills

**Narrative Intent Detector**:
- **Scope**: Rationale claims about WHY code/design exists
- **Pattern Examples**:
  - ✅ Checks: "The author added this because users forget" (requires evidence or hedging)
  - ✗ Skips: "This function crashes because it mutates state" (code reasoning, not intent)
- **Phase**: Warn-only (Phase 1), integrated in Stop hook

**Intent Drift Scanner**:
- **Threshold**: 0.6 (warns when drift exceeds 60%)
- **Scope Expansion Patterns**:
  - "also create/implement/build"
  - "additionally, meanwhile, furthermore"
  - "while we're at it / since we're here"
  - "might as well / could also"
- **State File**: `session_data/intent_state.json`

**Dormant Systems**:
- `shared/intent_classifier.py` - Excellent implementation, no current usage. Keep for future integration.
- `session_data/goal_state.json` - Orphaned files, no active readers/writers. Legacy from earlier goal tracking.

**See Also**: `INTENT_GOAL_AUDIT.md` for complete audit report.

**Implementation date**: 2026-02-25 (Contract System Optimization v6.0 - Change E)

### Hook-Level Behavior Contract

**Purpose**: Define how claim-coverage hooks distinguish between exempt process talk and verifiable claims.

**Process/self-report statements (meta)** are exempt from claim-coverage hooks when they do not contain strong external correctness claims.

**External correctness claims** ("fix works", "tests passed", "bug is fixed", "file is at…") must go through empirical verification.

**User intent/goal statements** configure behavior and should not be treated as claims by verification hooks; they are handled by planning/authority hooks instead.

**Reference helpers**: `__lib/shared_helpers.py` for:
- `is_meta_conversation(transcript)` — User meta-questions
- `is_self_referential(response)` — LLM self-referential patterns
- `is_user_intent_statement(transcript)` — User goal/intent language
- `has_external_claim(response)` — External claim detection (from `claim_patterns.py`)

**Gate logic pattern**:
```python
is_meta = is_meta_conversation(transcript) or is_self_referential(response)
has_ext = has_external_claim(response)

if is_meta and not has_ext:
    # Pure meta/process/self-report → skip this hook entirely
    pass

# User intent is NOT treated as a claim for verification hooks
# Intent statements configure behavior, don't trigger blocking
```

### Hook-Level Application of Evidence-Bound, Goal-Bound Principle

Claim-verification hooks SHOULD:

Treat as high‑risk any promoted factual claim (success, gap, absence, blame, "already handled", "pre-existing") that is not clearly tied to evidence from this turn's tools/reads.

Allow clearly labeled hypotheses ("possible gap", "seems likely", "needs verification") to be discussed without blocking, as long as they are not presented as confirmed facts.

Hooks SHOULD NOT:

Force the model to speculate about history or blame when the user only asked about current state.

Allow unrequested statements about history or blame ("pre-existing", "introduced by this change", "unrelated to my edits", "the tool is wrong") unless the user explicitly asks for history/causality and supporting evidence (diffs, history, logs) has been consulted and surfaced to the hook.

**If getting unexpected blocks**:
- Set both env vars to "false" in settings.json
- Or use bypass: `export CONSTITUTIONAL_HOOKS_BYPASS=1`

### Verification Stack: What Counts as Evidence

**Principle**: You are part of a distributed verification system. These count as verified evidence:

| Evidence Type | Sources | When to Trust |
|---------------|---------|---------------|
| **User Context** | User-provided URLs, file paths, explicit statements | Always — user is authoritative |
| **Local Artifacts** | Files read via Read tool, tool outputs, test results | When from this turn's tool calls |
| **Codebase Facts** | SKILL.md, CLAUDE.md, project docs | When explicitly referenced |
| **Tool Results** | Grep, Glob, find_symbol outputs | When shown in context |
| **External Sources** | Web search, fetched URLs | Only when explicitly shown (URLs, snippets) |

**The verification circuit**: Generate → Gather Evidence → Verify → Only then speak as if something is true

**Key distinction**: The goal is "reduce unverified pattern completion," not "never act unless web search succeeds."

User URLs, pasted file paths, and local tool results ARE valid evidence. The model should not demand web search when evidence already exists in the conversation.

**Failure mode to avoid**: Saying "I need to search for that" when the user just provided the information. This is not verification — it's failing to recognize the verification stack.

### Test-Description Language

When describing test outcomes in responses, prefer specific commands and expected results over global assertions:
- `Here are the tests to run and their expected outcomes:` + command list
- `You can run these tests to verify behavior:` + command list

Only say "All tests passed" or similar when you have just shown actual test output.

### Tool-Call Evidence Expectation

**Claim-verification hooks treat a claim as unsupported if there is no concrete evidence object** (URLs, doc snippets, tool results) in the current Stop input, even if you say you just searched.

**To avoid unnecessary blocks:**
1. First state your intent: "I will search..."
2. Then show at least one concrete result (with URL or snippet)
3. Only then upgrade to statements like "There is a plugin marketplace system..."

**Implementation date**: 2026-01-29 (Option C: Cross-Validation Hook)

### Unified Semantic Daemon

**Purpose**: Provides fast semantic search for CKS and CHS via Windows named pipes.

**Architecture**:
- **Daemon**:  - Named pipe server
- **Clients**:  (low-level),  (high-level with auto-start)
- **Hook**:  - Auto-start daemon on session start

**Features**:
- **Dynamic pipe names**:  avoids Windows stale handles
- **Discovery file**:  for clients to find current daemon
- **Auto-start**: Clients automatically start daemon if not running
- **Fallback**:  falls back to direct backend on daemon failure
- **Time-based idle timeout**: Disabled before 9pm, 30 minutes after 9pm

**Usage from hooks**:


**Discovery file integration**:
- Daemon writes discovery file on startup with pipe name, PID, timestamp
-  and  read discovery file to find current pipe
-  hook uses discovery file to check daemon status

**See also**:  for complete daemon documentation.

### Unified Semantic Daemon

**Purpose**: Provides fast semantic search for CKS and CHS via Windows named pipes.

**Architecture**:
- **Daemon**: `__csf/src/daemons/unified_semantic_daemon.py` - Named pipe server
- **Clients**: `SemanticClient` (low-level), `DaemonClient` (high-level with auto-start)
- **Hook**: `SessionStart_semantic_daemon.py` - Auto-start daemon on session start

**Features**:
- **Dynamic pipe names**: `\.\pipe\csf_nip_semantic_{PID}_{timestamp}` avoids Windows stale handles
- **Discovery file**: `P:/__csf/data/semantic_daemon_discovery.json` for clients to find current daemon
- **Auto-start**: Clients automatically start daemon if not running
- **Fallback**: `DaemonClient` falls back to direct backend on daemon failure
- **Time-based idle timeout**: Disabled before 9pm, 30 minutes after 9pm

**Usage from hooks**:
```python
from daemons.daemon_client import DaemonClient

client = DaemonClient(auto_start=True, enable_fallback=True)
results = client.search("cks", "query text", limit=5)
results = client.search("chs", "chat topic", limit=10)
```

**Discovery file integration**:
- Daemon writes discovery file on startup with pipe name, PID, timestamp
- `SemanticClient` and `DaemonClient` read discovery file to find current pipe
- `SessionStart_semantic_daemon.py` hook uses discovery file to check daemon status

**See also**: `__csf/src/daemons/CLAUDE.md` for complete daemon documentation.

### Hook Output Formats

| Event            | Output Format                         |
| ---------------- | ------------------------------------- |
| UserPromptSubmit | Raw text (injected into context)      |
| PreToolUse       | `{"continue": bool, "reason": "..."}` |
| PostToolUse      | `{"warning": "..."}` or `{}`          |
| Stop             | `{"allow": bool, "reason": "..."}`    |

> **Reference:** See `PROTOCOL.md` for complete specifications.

### Development Guidelines

1. **Protocol compliance** - Read `PROTOCOL.md` before writing hooks
2. **State persistence** - Use `shared_utils.py` for state management
3. **Constitutional hooks** - Use `hook_tracker.py` for blocking logic
4. **Router consolidation** - Add to existing routers before creating new hooks
5. **Logging** - Use `log_hook_event()` for observability

---

### Hook Registration Pattern

**CRITICAL**: All new hooks MUST be registered to execute. Follow this pattern to ensure hooks actually run.

#### Determine Registration Method

| Hook Event | Registration Method | Router File |
|-------------|-------------------|---------------|
| UserPromptSubmit | Router (preferred) | `UserPromptSubmit_router.py` |
| Stop | Router | `Stop_router.py` |
| PreToolUse | Router or settings.json | `PreToolUse_write_router.py` or settings |
| PostToolUse | Router or settings.json | `PostToolUse_router.py` or settings |
| SessionStart | settings.json | N/A (direct registration) |

**DEPRECATED**: Standalone UserPromptSubmit hooks (direct settings.json registration) are deprecated. Use router pattern.

#### In-Process vs Subprocess Registration

**CRITICAL**: Understand the difference between in-process (IN_PROCESS_HOOKS) and subprocess (settings.json) registration to avoid duplicate registration bugs.

**Registration Types**:

| Type | Location | Performance | State Sharing | When to Use |
|------|----------|-------------|---------------|-------------|
| **In-Process** | `IN_PROCESS_HOOKS` in PreToolUse.py | <100ms | Shared memory (direct imports) | Performance-critical hooks, stateful hooks |
| **TOOL_HOOKS** | `TOOL_HOOKS` in PreToolUse.py | 100-500ms | Via router dispatch | Most PreToolUse hooks |
| **Subprocess** | `settings.json` PreToolUse section | 500ms+ | No state sharing | Standalone hooks, isolation needed |

**Decision Tree**:

```
Is the hook performance-critical (<100ms required)?
├─ YES → Use IN_PROCESS_HOOKS (in-process)
│         - Import hook module directly
│         - NO subprocess registration in settings.json
│         - Examples: syntax_gate, directory_policy, path_validator
│
└─ NO → Does the hook need to run in TOOL_HOOKS dispatch chain?
         ├─ YES → Add to TOOL_HOOKS only
         │         - Runs via PreToolUse.py router
         │         - Check: NOT also in IN_PROCESS_HOOKS
         │         - Examples: tdd95_gate, investigation_gate, authorization_gate
         │
         └─ NO → Use subprocess (settings.json)
                   - Runs as separate Python process
                   - Use for: SessionStart, standalone hooks
                   - Examples: sequential_thinking, tool_availability_checker
```

**Anti-Pattern** (BUG - causes "No stderr output" error):

```python
# WRONG - Hook in BOTH IN_PROCESS_HOOKS AND settings.json subprocess
IN_PROCESS_HOOKS = {
    "PreToolUse_directory_policy.py": PreToolUse_directory_policy.run,  # ✅ In-process
}
# AND settings.json has:
# {"command": "python P:/.claude/hooks/PreToolUse_directory_policy.py"}  # ❌ DUPLICATE!
```

**Why this is a bug**: When both registrations exist:
1. In-process version runs first (exits code 2 to block)
2. Subprocess version runs after, also exits code 2 without stderr
3. Claude Code treats ANY stderr from hooks as "hook error"
4. Result: Confusing "No stderr output" error messages

**Correct Pattern**:

```python
# CORRECT - Hook in ONLY ONE location
IN_PROCESS_HOOKS = {
    "PreToolUse_directory_policy.py": PreToolUse_directory_policy.run,  # ✅ In-process only
}
# settings.json does NOT have this hook as subprocess
```

**Verification**:

Run the hook registration verification script to detect duplicates:
```bash
python P:/.claude/hooks/scripts/verify_hook_registration.py
```

This script detects:
- Hooks in both IN_PROCESS_HOOKS and settings.json (BUG)
- Duplicate entries within settings.json

**Performance Requirements**:

| Registration | Target Latency | Acceptable Use |
|--------------|----------------|----------------|
| IN_PROCESS_HOOKS | <100ms | Path validation, syntax checks, quick lookups |
| TOOL_HOOKS | <500ms | Most validation gates, policy checks |
| Subprocess | <5s | Heavy operations, external calls, complex analysis |

**State Sharing Considerations**:

- **In-Process**: Direct function calls, can share objects/memory
- **Subprocess**: No state sharing, must use files or IPC

**Error Handling**:

- **In-Process**: Can raise exceptions, router catches them
- **Subprocess**: Must exit with proper codes (0=allow, 2=block), stderr = error

#### Router Registration Steps (3-Step Process)

When creating a new UserPromptSubmit, Stop, or PostToolUse hook that uses router pattern:

1. **Export `process_prompt()` function**
   ```python
   def process_prompt(data: dict) -> dict:
       # ... hook logic ...
       return {"additionalContext": "injection text"}
   ```

2. **Register in router's `import_hook()` function**
   ```python
   elif name == "your_hook_name":
       import your_hook_file as mod
       return mod
   ```

3. **Add to `HOOK_PRIORITY` and `HOOK_DISPATCH` dictionaries**
   ```python
   # HOOK_PRIORITY - lower = earlier
   "your_hook_name": 4.5,  # Choose priority based on hook purpose

   # HOOK_DISPATCH - maps name to runner function
   "your_hook_name": run_your_hook_function,
   ```

4. **Create runner function** (if not trivial)
   ```python
   def run_your_hook_function(data: dict, prompt: str, ctx: dict | None = None) -> dict | None:
       mod = import_hook("your_hook_name")
       if not mod:
           return None
       result = mod.process_prompt(data)
       if result and "additionalContext" in result:
           return {"context": result["additionalContext"], "tokens": ...}
       return None
   ```

#### Env Var Registration

If your hook checks `os.environ.get("YOUR_HOOK_ENABLED", "true")`:

1. Add the env var to `P:/.claude/settings.json` under `"env"` section
2. Use `"true"`/`"false"` string values (not boolean)
3. Document the env var in this CLAUDE.md under relevant sections

#### Standalone Registration (Non-Router Hooks)

For SessionStart, standalone PreToolUse/PostToolUse, or hooks that cannot use router:

```json
{
  "hooks": {
    "YourEvent": [
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "python P:/.claude/hooks/__lib/hook_runner.py P:/.claude/hooks/your_hook.py --timeout 5.0",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

#### Verification

Run the hook registration test to verify:
```bash
python P:/.claude/hooks/tests/test_hook_registration.py
```

This test catches "dead hooks" that exist but are not registered anywhere.

---

### Testing

```bash
# Run hook diagnostics
python P:/.claude/hooks/hook_diagnostics.py

# Check recent logs
python P:/.claude/hooks/shared_utils.py logs --limit 50

# Run pytest suite (preferred)
pytest P:/.claude/hooks/tests/ -v
```

### Anti-Mock Stance

**Policy**: Do not use Mock objects in tests, even if it requires more time to create tests.

**Rationale**:
1. **Fragility**: Mock objects encode implementation assumptions that break when code changes
2. **False Confidence**: Passing mock tests don't prove real integration works
3. **Maintenance Burden**: Mocks duplicate knowledge of implementation

**Examples**:

❌ **WRONG (Mock)**:
```python
mock_match = Mock()
mock_match.groups.return_value = ('X', 'Y')
result = extract_correction_description(content, mock_match)
```

✅ **CORRECT (Real regex)**:
```python
pattern = r"Don't use (\w+), use (\w+) instead"
match = re.search(pattern, "Don't use X, use Y instead")
result = extract_correction_description(content, match)
```

**See also**: `~/memory/testing_patterns.md` for complete guidance on testing without mocks.

### Hook External Dependency Policy

**Policy**: Hooks MUST NOT make external API calls, HTTP requests, or spawn network-dependent subprocesses.

**Rationale**:
1. **Silent degradation**: Network failure during a hook event (PreCompact, SessionStart, etc.) silently degrades output quality or blocks user workflow with no clear error
2. **Latency injection**: Every hook event gains network round-trip overhead — PreCompact hooks that call an LLM add 1–5 seconds to every compaction
3. **Credential complexity**: Hooks run in the framework event loop; managing API keys there adds surface area for leaks and auth failures
4. **Circular dependency**: Claude Code hooks that call the Claude API create a dependency loop — if the API is down, hooks fail, which may prevent the session from starting or compacting

**Red flags** (these patterns in a hook file are always wrong):
```python
# ❌ LLM call inside a hook
llm = get_llm_client()
summary = llm.messages.create(...)

# ❌ HTTP request inside a hook
import requests
response = requests.get("https://api.example.com/...")

# ❌ "Graceful degradation" that silently drops captured data
try:
    summary = call_external_api(transcript)
except Exception:
    summary = None  # NOT graceful — you just lost the data
```

**Correct pattern** — use already-captured local artifacts:
```python
# ✅ Read from transcript (already in handoff envelope) at restore-time
transcript_entries = parse_transcript(snapshot["transcript_path"])
recent_messages = extract_recent_user_messages(transcript_entries, n=15)
```

**Decision rule**: If a hook design requires external data, restructure so the data is read from a local artifact at restore/start time rather than fetched at capture/compaction time. The `transcript_path` is already in the handoff envelope — use it.

### Hook Testing Protocol

**Use pytest, not ad-hoc Bash pipes.** Hook tests live in `P:/.claude/hooks/tests/`. Write pytest tests that assert expected exit codes and JSON output. See `run_hook_test.py` for the pattern.

**Critical: Blocking = correct behavior for blocking hooks.** Exit code 2 from a PreToolUse hook means the hook successfully blocked the action. Do NOT interpret this as an error. The hook is working as designed.

**Expected exit codes by hook type:**

| Hook Event | Exit 0 | Exit 2 |
|------------|--------|--------|
| PreToolUse | Allow/pass-through | **Block** (correct behavior for denied actions) |
| PostToolUse | Always exit 0 | Advisory only — should not exit 2 |
| Stop | Allow stop | **Block** stop (force continuation) |
| UserPromptSubmit | Always exit 0 | N/A |

**PostToolUse verifier testing — file must exist first:**
PostToolUse hooks like `edit_verifier.py` check that the file actually exists on disk after a Write/Edit. When testing:
1. Create the test file on disk FIRST
2. THEN pipe synthetic hook input referencing that file
3. Clean up the test file after

```python
# WRONG — file never created, verifier correctly blocks
echo '{"tool_name": "Write", "tool_input": {"file_path": "test.txt"}, "tool_response": ""}' | python edit_verifier.py
# Result: exit 2, "file does not exist" — THIS IS CORRECT BEHAVIOR

# RIGHT — create file, then verify
echo "test content" > test.txt
echo '{"tool_name": "Write", "tool_input": {"file_path": "test.txt"}, "tool_response": ""}' | python edit_verifier.py
# Result: exit 0, {"decision": "allow", ...} with file content in additionalContext
rm test.txt
```

**Common testing mistakes to avoid:**
- Interpreting exit code 2 as "hook is broken" — it means the hook blocked successfully
- Testing file-verification hooks without creating the target file first
- Testing hooks with incorrect JSON schema (check PROTOCOL.md for field names)
- Confusing `tool_input`/`toolInput` field name variants — hooks accept both

### Invariant Validation Pattern

**Purpose**: Enforce cross-structure consistency at import time using `if __debug__` guards.

**When to Use**: When a module has multiple data structures that must stay aligned (e.g., pattern dictionaries and template dictionaries).

**Pattern**:
```python
# Module-level invariant check (runs on import)
if __debug__:  # Only runs in dev/test, optimized out in production
    missing_templates = set(_COMPILED_STRONG.keys()) - set(_PROFILES.keys())
    missing_patterns = set(_PROFILES.keys()) - set(_COMPILED_STRONG.keys())

    if missing_templates or missing_patterns:
        raise AssertionError(
            f"Profile configuration mismatch in module_name:\n"
            f"  Missing templates: {missing_templates}\n"
            f"  Missing patterns: {missing_patterns}\n"
            f"  _PROFILES has {len(_PROFILES)} profiles, _COMPILED_STRONG has {len(_COMPILED_STRONG)}"
        )
```

**Benefits**:
- Fails fast during development, not at runtime in production
- Zero production overhead (`if __debug__` optimized out with `python -O`)
- Clear error message points to the problem
- Prevents a class of bugs where related structures drift apart

**Example**: `P:/.claude/hooks/UserPromptSubmit_modules/think_trigger.py` **previously** used this pattern to ensure 7 profiles have both pattern definitions and templates.

**Documentation**: [Python assertion docs](https://docs.python.org/3.12/reference/simple_stmts.html#the-assert-statement)

---

### Single-Source Dataclass Pattern

**Purpose**: Eliminate structural bug classes by co-locating related data in immutable dataclasses.

**When to Use**: When a module has multiple data structures that must stay aligned (e.g., pattern dictionaries and template dictionaries). **Prefer this over invariant checks** for new code.

**Pattern**:
```python
from dataclasses import dataclass

@dataclass(frozen=True)
class ThinkProfile:
    """Single-source definition for a reasoning profile.

    This dataclass co-locates all profile data to prevent the bug class where
    pattern definitions and template definitions drift apart.

    The frozen=True modifier makes instances immutable, preventing accidental mutation.
    """
    name: str
    template: str
    strong_patterns: list[str]
    weak_patterns: list[str] | None

# Single source of truth
_THINK_PROFILES: dict[str, ThinkProfile] = {
    "debug_rca": ThinkProfile(
        name="debug_rca",
        template="...",
        strong_patterns=[...],
        weak_patterns=[...],
    ),
    # ... other profiles
}

# Derived dictionaries (for backward compatibility)
_PROFILES: dict[str, str] = {
    name: profile.template for name, profile in _THINK_PROFILES.items()
}
_STRONG_PATTERNS: dict[str, list[str]] = {
    name: profile.strong_patterns for name, profile in _THINK_PROFILES.items()
}
_WEAK_PATTERNS: dict[str, list[str]] = {
    name: (profile.weak_patterns or []) for name, profile in _THINK_PROFILES.items()
}
```

**Benefits**:
- **Compiler-enforced completeness**: Can't add a profile without all fields (type system prevents KeyError bugs)
- **Zero runtime overhead**: No invariant checks needed (impossible to create misaligned state)
- **Self-documenting**: All profile data visible in one place
- **Immutable**: `frozen=True` prevents accidental mutation
- **Backward compatible**: Derived dictionaries maintain existing API

**Example**: `P:/.claude/hooks/UserPromptSubmit_modules/think_trigger.py` **now** uses this pattern to ensure 7 profiles have both pattern definitions and templates.

**When to use invariant checks vs dataclass**:
- **Use dataclass** for new code (preferred approach)
- **Use invariant checks** when refactoring existing code to dataclass is too costly
- **Use invariant checks** when data can't be easily co-located (external dependencies)

**Documentation**: [Python dataclass docs](https://docs.python.org/3.12/library/dataclasses.html)

---

### Hook Expectations for Chain-of-Verification

When responses follow the **Hypotheses → Verification Plan → Findings → Conclusions (Verified/Open)** structure, claim-verification hooks SHOULD:

**Focus strict external_fact checks** on the **Conclusions/Verified** items, using evidence from this turn.

**Treat Hypotheses and Conclusions/Open as non-blocking** as long as they are clearly marked as tentative.

**Hooks SHOULD:**

- Encourage the use of this structure for complex analyses, bug investigations, and "is this fixed?" style claims.
- Prefer blocking or rewriting only when a claim is presented as **Verified** without matching evidence in Findings.

This structure helps hooks distinguish between:
- Hypotheses being explored (tentative, clearly labeled) — allow
- Verified claims without supporting evidence — block or request correction

---

### Test File Location Policy

**Purpose**: The `test_location_gate` hook (in `PreToolUse_write_router.py`) enforces that test files are written to the appropriate directory based on their purpose.

**Test file patterns detected**:
- `test_*.py` — starts with `test_` and ends with `.py`
- `conftest.py` — pytest configuration file
- `*_test.py` — ends with `_test.py`
- Contains "test" + `.py` extension

**Directory usage**:

| Directory | Purpose | Test file types |
|-----------|---------|----------------|
| `tests/` | **Persistent test suite** — Tests that are part of the project's permanent test infrastructure | Unit tests, integration tests, tests that track with CI/CD |
| `.temp/` | **Exploratory testing** — Temporary scratch files for active development and verification | Quick validation scripts, one-off test scripts during debugging |

**How to use each location**:

1. **`tests/` subdirectory** — Use for persistent tests:
   - Write to `P:/__csf/tests/` or module-specific `tests/` subdirectories
   - These tests are tracked by git and run as part of the test suite
   - Example: `test_fts_escape_fixed.py` after a fix is verified

2. **`.temp/` directory** — Use for exploratory testing:
   - Set `TEST_LOCATION_GATE_ENABLED=false` in `settings.json` to allow writes to `.temp/`
   - For temporary validation scripts during active development
   - Example: Quick test to verify a function works during debugging
   - Clean up these files after verification is complete

**Environment variable**:
- `TEST_LOCATION_GATE_ENABLED` — Default: `true` (gate enabled)
  - Set to `false` in `P:/.claude/settings.json` under `"env"` section to allow `.temp/` writes
  - Set to `false` per-session: `export TEST_LOCATION_GATE_ENABLED=false`

### Test File Exemption Philosophy

**Purpose**: Test files should be writable without hook blocking to support rapid TDD iteration.

**Rationale**: Test files require frequent iteration during TDD cycles. Blocking test file creation adds unnecessary friction to the development workflow. This exemption allows test files to be written in logical locations (`tests/`, `test/`) without triggering safety gates designed for production code.

**Implementation**: Three hooks now exempt test file operations from their blocking logic:
- `recursive_failure_detector.py` — Allows test files without Catch-22 checking
- `PreToolUse_require_plan_for_features.py` — Allows test files without plan requirement
- `PreToolUse_git_safety.py` — Allows test file writes without git safety blocking

**Detection Logic**: The `is_test_file_operation()` function in `__lib/test_detection.py` uses pytest's discovery mechanism to identify test files:
- **Pytest-based discovery** (primary): Uses `pytest.collect` API for accurate detection
- **Regex pattern fallback** (if pytest unavailable): Simple pattern matching
- **LRU caching** with 5-minute TTL for performance
- **Detects**: `tests/`, `test/`, and module-specific test directories

**Adding Exemption to New Hooks**:

When creating new hooks that may block Write/Edit operations, consider exempting test files:

```python
from __lib.test_detection import is_test_file_operation

def run(data: dict) -> dict | None:
    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    # Exempt test file operations
    if tool_name in ("Write", "Edit"):
        file_path = tool_input.get("file_path", "")
        if file_path and is_test_file_operation(file_path):
            return None  # Allow test file operations

    # ... rest of hook logic
```

**When NOT to exempt**:
- **Security hooks** (credential filtering, secret scanning) — should scan all files
- **Path protection hooks** (deny_root_write) — should enforce everywhere
- **Syntax validation hooks** — should validate all code

**Configuration**: The `ADVISORY_SHOW_MODE` environment variable controls Tier 1 advisory display from `PreToolUse_risk_tier_gate.py`:
- `once` (default) — Show each advisory once per session
- `always` — Show every advisory
- `never` — Suppress all advisories

**Related**: See `P:/__csf/__lib/test_detection.py` for the detection module and `P:/__csf/__lib/test_detection_README.md` for complete documentation.

---

### Git Safety Enhancements (2026-03-07)

**Purpose**: Comprehensive git safety improvements to prevent data loss, cache-related bugs, and worktree accidents on Windows 11.

**Implementation**: 5-phase enhancement plan completed (T-002 through T-008)

**Component 1: Worktree Cross-Checks** (T-002)
- **File**: `P:/.claude/hooks/PreToolUse_git_safety.py`
- **Function**: `check_worktree_cross_contamination()`
- **Features**:
  - Blocks git operations targeting files outside current worktree
  - Uses `worktree_helper.py` for worktree detection
  - Bypass flag: `--allow-cross-worktree`
  - Clear error messages showing current worktree vs target files
- **Example block message**:
  ```
  ⛔ CROSS-WORKTREE ACCESS DETECTED
  This git operation targets 2 file(s) outside your current worktree:
    Current worktree: P:/.claude/worktrees/ai-task-20260307-143000
    • packages/debugRCA/src/debug_rca/__pycache__
    • .claude/hooks/tests/test_worktree_helper.py
  To bypass: Add --allow-cross-worktree to your message.
  ```

**Component 2: Git Restore Suggestions** (T-002)
- **File**: `P:/.claude/hooks/PreToolUse_git_safety.py`
- **Function**: `suggest_git_restore()`
- **Features**:
  - Detects legacy `git checkout -- file` pattern
  - Suggests modern `git restore file` alternative
  - Bypass flag: `--allow-legacy-checkout`
  - Advisory only (never blocks)
- **Example suggestion**:
  ```
  💡 SUGGESTION: Use modern 'git restore' instead of 'git checkout --'
  Detected: git checkout -- file.py
  Recommended: git restore file.py
  Why 'git restore' is better:
    • Purpose-built for restoring working tree files
    • Clearer intent (restore vs checkout's multiple meanings)
    • Separated from branch switching (git switch)
    • Safer: won't accidentally create branches
  ```

**Component 3: Enhanced post-checkout Hook** (T-003)
- **File**: `P:/.git/hooks/post-checkout`
- **Features**:
  - Bash-based (fast, works in Git Bash on Windows)
  - Cleans `__pycache__/` directories after branch switches
  - Cleans `.pyc` and `.pyo` files
  - Optional verbose logging: `GIT_PYCACHE_CLEANUP_VERBOSE=true`
  - Performance: <500ms per checkout
- **Implementation**:
  ```bash
  # Clean __pycache__ directories
  find . -type d -name "__pycache__" -print0 | xargs -0 rm -rf 2>/dev/null || true
  # Clean .pyc files
  find . -name "*.pyc" -delete 2>/dev/null || true
  # Clean .pyo files
  find . -name "*.pyo" -delete 2>/dev/null || true
  ```

**Component 4: Enhanced pre-commit Hook** (T-004)
- **File**: `P:/.git/hooks/pre-commit`
- **Function**: `clear_pycache()` (expanded scope)
- **Features**:
  - Repository-wide Python cache cleanup (not just hooks directory)
  - Scope: `packages/`, `src/`, `.claude/hooks/`, `scripts/`
  - Fails open (cleanup errors don't block commits)
  - Optional logging: `GIT_PYCACHE_CLEANUP_VERBOSE=true`
- **Why this matters**: Previous version only cleaned hooks directory, which didn't prevent the cache bug experienced on 2026-03-07

**Component 5: PowerShell Worktree Automation** (T-005, T-006, T-007)
- **Location**: `P:/scripts/git/`
- **Scripts**:
  1. `New-ClaudeWorktree.ps1` (T-005)
     - Creates new worktree with auto-generated branch name
     - Automatically cleans Python cache
     - Usage: `.\New-ClaudeWorktree.ps1 [-Task "ai-task-20260307-150000"] [-Branch "ai/ai-task-20260307-150000"]`
  2. `Status-AllWorktrees.ps1` (T-006)
     - Shows all worktrees with branch and status
     - Usage: `.\Status-AllWorktrees.ps1`
  3. `Cleanup-ClaudeWorktrees.ps1` (T-007)
     - Removes old Claude worktrees safely
     - Dry-run mode by default (preview before cleanup)
     - Usage: `.\Cleanup-ClaudeWorktrees.ps1 [-DryRun $false]`

**Component 6: Windows Git Config** (T-008)
- **File**: `P:/__csf/.staging/apply-git-config.ps1`
- **Features**:
  - One-time Windows-specific git optimizations
  - Core settings: `core.autocrlf=input`, `core.filemode=false`, `core.preloadindex=true`
  - Performance: `diff.algorithm=histogram`, `status.submoduleSummary=false`
  - Safety: `core.longpaths=true`, `init.defaultBranch=main`
  - Usage: `pwsh P:/__csf/.staging/apply-git-config.ps1`

**Bypass Flags Summary**:
- `--allow-cross-worktree` - Bypass worktree cross-contamination check
- `--allow-legacy-checkout` - Suppress git restore suggestion

**Troubleshooting**:
- **Cache cleanup not working**: Set `GIT_PYCACHE_CLEANUP_VERBOSE=true` to see cleanup logs
- **Worktree detection failing**: Check `worktree_helper.py` is in `P:/.claude/hooks/__lib/`
- **PowerShell scripts blocked**: Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

**See also**: `P:/docs/git-safety-enhancements.md` for complete usage guide, `P:/__csf/.staging/cache_bug_investigation_20260307.md` for root cause analysis

**Implementation date**: 2026-03-07

---

### Ownership-Colocation System (NEW - 2026-03-19)

**Purpose**: Two-tier hook system preventing infra placement at the wrong directory level when a single consumer exists.

**Problem Solved**: LLMs default to sibling/peer directories (e.g., `.claude/proxy/`) without asking "how many components consume this?" A directory placed at the wrong level creates a false shared-ownership contract that is hard to undo.

**Architecture — Two-Tier Design**:

| Tier | Hook | Phase | Enforcement |
|------|------|-------|-------------|
| Planning-time | `UserPromptSubmit_modules/ownership_colocation_nudge.py` | UserPromptSubmit | Advisory — injects checklist |
| Write-time | `PreToolUse_ownership_colocation_gate.py` | PreToolUse | Blocking — blocks write to STRICT_PATHS |

**Keyword Detection (nudge — two-tier)**:

`_COMPILED_SPECIFIC` — fire unconditionally (inherently placement-specific):
- `\bwhere\s+(?:to\s+)?(?:put|place|store|keep|add|create)\b`
- `\bnew\s+(?:directory|folder|dir)\b`, `\bcreate\s+(?:a\s+)?(?:directory|folder|dir)\b`
- `\bvirtualenv\b`, `\bsite[-_]packages\b`
- `\binfrastructure\b`, `\binfra\b`, `\badapter\b`

`_COMPILED_CONTEXT` — require `_PLACEMENT_VERBS` nearby (prevents nudge fatigue on broad terms):
- `\bproxy\b`, `\bvenv\b`

`_PLACEMENT_VERBS` — `set up|create|build|put|place|add|move|install|init|scaffold|bootstrap|structure|organise|organize`

**Why two tiers**: `\bproxy\b` alone would fire on "configure HTTP proxy" or "what is an HTTP proxy server" — creating nudge fatigue that causes real placement decisions to be ignored (5-step cascade: nudge fires → model learns to ignore → real decisions go un-nudged → infra placed at wrong level → false shared contract established).

**Path Categories (gate)**:

`STRICT_PATHS` — blocked unless `--allow-shared-infra [N-consumers]` present:
- `.claude/proxy/` — canonical incident that motivated this gate
- `.claude/infrastructure/`
- `.claude/adapters/`

SCOPE NOTE: `STRICT_PATHS` is intentionally narrow. Add paths reactively after real incidents, not speculatively. Broad coverage → more false positives → bypass becomes reflexive.

`ADVISORY_PATHS` — allowed silently (nudge already fired at planning time):
- `.claude/shared/`, `.claude/lib/`, `.claude/__lib/`, `.claude/utils/`

**Bypass**: `--allow-shared-infra [N-consumers]` — requires consumer count evidence:
```
grep -r 'proxy' --include='*.py' --include='*.md' skills/ hooks/
# Confirm N consumers, then add to message:
--allow-shared-infra 3-consumers
```

**Telemetry**: Block events appended to `logs/diagnostics/pretooluse_blocks.jsonl` by `_log_block()` with fields: `timestamp`, `hook`, `tool`, `path`.

**Test Coverage**: 31 tests in `tests/test_ownership_colocation_hooks.py`:
- `TestOwnershipColocationNudge` (7 tests) — keyword detection, hook result quality
- `TestOwnershipColocationGate` (21 tests) — path matching, bypass, malformed input, Windows paths
- `TestOwnershipColocationUPSIntegration` (3 tests) — end-to-end UPS → registry → nudge → additionalContext

**Implementation Date**: 2026-03-19

---

### Plan Mode Guard (DEACTIVATED - 2026-03-19)

**Purpose**: The plan mode guard was a PreToolUse hook that blocked Edit/Write operations during plan mode.

**Status**: **DEACTIVATED** - The hook has been removed from router registration in `PreToolUse.py`.

**What was removed**:
- Hook file: `P:/.claude/skills/plan-workflow/hooks/PreToolUse_plan_mode_guard.py`
- Router registration: Removed from both Edit and Write TOOL_HOOKS in `PreToolUse.py`

**Current behavior**:
- Edit and Write operations are NO LONGER blocked during plan mode
- Plan files can exist without affecting tool usage
- Plan mode detection still exists but does not enforce restrictions

**Plan file lifecycle**:
- Plan files are created in `~/.claude/plans/*.md` during planning sessions
- Plan mode activates when ANY `*.md` file exists in the plans directory
- **NEW**: Automatic cleanup of stale plan files (older than 30 days) on session start
- Cleanup is handled by `SessionStart_verification_cleanup.py`

**Configuration**:
```bash
# Plan file TTL (default: 30 days)
export PLAN_FILE_MAX_AGE_DAYS=30

# Disable verification cleanup entirely (not recommended)
export VERIFICATION_CLEANUP_ENABLED=false
```

**Why deactivated**:
- User requested direct deactivation instead of configuration workarounds
- Plan mode blocking was interfering with legitimate editing during planning sessions
- Stale plan files from abandoned sessions were causing unexpected blocking

**Remaining artifacts**:
- The hook file still exists at `P:/.claude/skills/plan-workflow/hooks/PreToolUse_plan_mode_guard.py`
- It is NOT registered and will NOT execute
- Can be deleted if desired, or kept for reference

---

### Plan Mode Troubleshooting

**Symptom**: Edit/Write operations are being blocked unexpectedly

**Possible causes**:

1. **Stale plan file exists**
   - Check: `ls -la ~/.claude/plans/*.md`
   - Solution: Remove stale plan files manually or wait for automatic cleanup
   - Manual cleanup: `rm ~/.claude/plans/*.md` (be careful not to delete active plans)

2. **Plan mode guard was re-enabled**
   - Check: Search for `PreToolUse_plan_mode_guard.py` in `P:/.claude/hooks/PreToolUse.py`
   - Solution: Remove the hook from TOOL_HOOKS registration if present

3. **Another hook is blocking**
   - Check: Run `python P:/.claude/hooks/hook_diagnostics.py`
   - Solution: Identify the blocking hook from diagnostic output

**Checking plan file status**:
```bash
# List all plan files with ages
ls -lt ~/.claude/plans/*.md 2>/dev/null | head -20

# Count plan files
ls -1 ~/.claude/plans/*.md 2>/dev/null | wc -l

# Find plan files older than 30 days
find ~/.claude/plans/*.md -mtime +30 2>/dev/null
```

**Manual plan cleanup**:
```bash
# Remove all plan files (DANGEROUS - deletes all plans)
rm ~/.claude/plans/*.md

# Remove only backup files
rm ~/.claude/plans/*.bak-*

# Remove specific plan file
rm ~/.claude/plans/graceful-roaming-wombat.md
```

**Automatic cleanup**:
- Runs on every session start via `SessionStart_verification_cleanup.py`
- Removes plan files older than `PLAN_FILE_MAX_AGE_DAYS` (default: 30 days)
- Only cleans `.md` files in the root plans directory (not subdirectories)
- Logs removed files to hook logger

**Preventing plan file accumulation**:
1. Delete plan files after implementation is complete
2. Use descriptive plan names to identify abandoned plans
3. Rely on automatic cleanup for forgotten plans
4. Consider implementing `/cleanup-plans` command for manual cleanup

**Related**:
- Plan mode guard hook: `P:/.claude/skills/plan-workflow/hooks/PreToolUse_plan_mode_guard.py` (dormant)
- Cleanup implementation: `P:/.claude/hooks/SessionStart_verification_cleanup.py`
- Plan directory: `~/.claude/plans/` (or `C:/Users/brsth/.claude/plans/` on Windows)
