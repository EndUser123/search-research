# Review Bundle: Cognitive Enhancement System

**Generated**: 2026-03-17
**Scope**: Cognitive Enhancement System (hooks + constitutional guidance)
**File Count**: 7 core files
**Execution Mode**: Single-agent

---

## 1. PROJECT CONTEXT

### Domain & Purpose
The Cognitive Enhancement System is a meta-cognitive framework that injects structured reasoning patterns into AI responses to prevent common reasoning flaws (availability heuristic bias, arbitrary thresholds, over-engineering). It operates at two levels:

1. **Hook Level** (enforced when UserPromptSubmit fires): Configurable enhancer injection via `cognitive_enhancers.py`
2. **Constitutional Level** (all conversations): Working Principle 8 in `working_principles.md`

**Who uses it**: Solo developers using Claude Code CLI tool on Windows 11
**Why critical**: Prevents suboptimal-first solutions, enforces "Search → Evaluate → Implement" workflow

### Scale Metrics
- **LOC**: ~600 lines (cognitive_enhancers.py) + ~250 lines (config JSON) + ~300 lines (memory files)
- **Subsystems**: 3
  - Intent detection (regex-based)
  - Enhancer selection (topic-based routing)
  - Conflict arbitration (token budget + mode overrides)
- **Deployment scope**: C:\Users\brsth\.claude\hooks\ (local development environment)
- **Change frequency**: Moderate (recently enhanced with comparative_analysis enhancer #10 and Working Principle 8)

### Your Environment
- **OS**: Windows 11 Pro
- **Shell**: bash (POSIX-compliant tools)
- **Languages**: Python 3.12+ (hooks), JSON (config)
- **Framework**: Claude Code hook system (UserPromptSubmit event)
- **External services**: None (stdlib-only)

---

## 2. ARCHITECTURE OVERVIEW

```
User Prompt
    ↓
UserPromptSubmit Event
    ↓
[Optional Mode Check] → #fast, #deep, #rca
    ↓
cognitive_enhancers.py
    ├→ Intent Detection (_detect_intent)
    │   ├→ implementation (regex: build, create, implement)
    │   ├→ diagnostic (regex: debug, investigate, diagnose)
    │   ├→ decomposition (long vague prompts)
    │   └→ implementation_diagnostic (combo)
    ↓
    ├→ Topic-Based Routing (_select_enhancers)
    │   ├→ implementation → 3 enhancers max
    │   ├→ diagnostic → 2 enhancers max
    │   ├→ meta_rca → 2 enhancers max
    │   ├→ decomposition → 4 enhancers max
    │   └→ implementation_diagnostic → 3 enhancers max
    ↓
    ├→ Conflict Arbitration (resolve_conflict)
    │   ├→ Token budget: 500 tokens
    │   ├→ Fast mode: disable all
    │   └→ Per-topic limits
    ↓
    └→ Injection Builder (_build_injection)
        ├→ Tag header: [COG] Active Frameworks: X, Y, Z
        ├→ Rationale: "Why: {intent_topic}"
        └→ Framework injections: 2-4 enhancers

Enhanced Prompt → Claude Model
```

### Major Subsystems

#### 1. Intent Detection Engine
- **File**: `C:\Users\brsth\.claude\hooks\UserPromptSubmit_modules\cognitive_enhancers.py`
- **Purpose**: Classify user prompts into topics (implementation, diagnostic, meta_rca, decomposition)
- **Mechanism**: Regex pattern matching with negation handling
- **Entry point**: `_detect_intent(prompt: str) -> dict[str, bool]`
- **Dependencies**: None (stdlib `re`)
- **Critical invariants**:
  - Negation regex scoped to implementation verbs only
  - Quality guidance ("don't forget to test") doesn't block implementation intent

#### 2. Enhancer Selection Router
- **File**: `C:\Users\brsth\.claude\hooks\UserPromptSubmit_modules\cognitive_enhancers.py`
- **Purpose**: Map intent topics to appropriate cognitive enhancers
- **Mechanism**: Topic-based routing with configurable per-topic limits
- **Entry point**: `_select_enhancers(intent: dict, config: dict) -> list[Enhancer]`
- **Dependencies**: Intent detection output, config JSON
- **Critical invariants**:
  - Max enhancers per topic: implementation(3), diagnostic(2), meta_rca(2), decomposition(4)
  - Each enhancer must have matching topic in enhancer definition

#### 3. Constitutional Working Principles
- **File**: `C:\Users\brsth\.claude\projects\P--\memory\working_principles.md`
- **Purpose**: Broad engineering heuristics that influence ALL conversations (not just hook-triggered)
- **Principle 8**: "Comparative Analysis First (Optimal-First Generation)"
- **Entry point**: Memory file (auto-loaded in session context)
- **Dependencies**: None
- **Critical invariants**:
  - Applies to ALL solution proposals, regardless of skill/hook invocation
  - Prevents suboptimal-first suggestions at constitutional level

---

## 3. EXECUTION AND DATA FLOW

### Execution Sequence

```
1. User types prompt → Claude Code CLI
2. SessionStart hook fires → Initialize context
3. UserPromptSubmit hook fires (priority 11.0)
   a. cognitive_enhancers.process_prompt() called
   b. Intent detection runs (<5ms)
   c. Enhancer selection runs (<5ms)
   d. Conflict arbitration runs (<10ms)
   e. Injection text built
   f. Returns {"context": injection_text, "tokens": token_count, "priority": 11.0}
4. Hook router merges all hook contexts
5. Enhanced prompt sent to Claude model
6. Model response includes [COG] tag if cognitive frameworks active
```

### Mandatory Ordering Constraints
- Intent detection MUST run before enhancer selection
- Conflict arbitration MUST run after enhancer selection
- Mode overrides (#fast, #deep, #rca) MUST be checked before intent detection

### State Management
- **State stores**: None (stateless hook)
- **Configuration**: `cognitive_reasoning_config.json` (loaded on each invocation)
- **Consistency model**: Fail-open (if config invalid, use defaults)
- **Isolation boundaries**: Per-terminal (no cross-terminal state)

### Error Handling
- **Fail-open policy**: If config JSON invalid, use `_DEFAULT_CONFIG`
- **Validation warnings**: Emitted to stdout, never stderr (Claude Code treats stderr as error)
- **Performance**: <60ms max detection time (configurable via `max_detection_ms`)

---

## 4. COMPONENT INVENTORY

### Core Logic Components

#### `cognitive_enhancers.py`
- **Path**: `C:\Users\brsth\.claude\hooks\UserPromptSubmit_modules\cognitive_enhancers.py`
- **Key functions**:
  - `_detect_intent(prompt: str) -> dict[str, bool]`: Intent classification
  - `_select_enhancers(intent: dict, config: dict) -> list[Enhancer]`: Topic-based routing
  - `_build_injection(enhancers: list[Enhancer], intent: dict) -> str`: Build injection text
  - `cognitive_enhancers(context: HookContext) -> HookResult`: Main hook entry point
- **Responsibility**: Route intent to appropriate cognitive enhancers
- **Inputs**: User prompt, hook context
- **Outputs**: Hook result with context injection text
- **Known limitations**:
  - Regex-based intent detection (no embeddings/semantic search)
  - No learning from past interactions (static patterns)
  - Token budget estimation is rough (chars // 4)

#### 10 Cognitive Enhancers
1. **assumption_surfacing**: Surface unstated assumptions before work begins
2. **outcome_anchoring**: Define "done" criteria before starting
3. **inversion_prompting**: "What would make this fail?"
4. **chestertons_fence**: Understand existing code before changing it
5. **calibrated_confidence**: Force confidence labeling on claims (HIGH/MEDIUM/LOW)
6. **socratic_decomposition**: Break vague mega-prompts into sub-questions
7. **cynefin_classification**: Problem domain classification (Clear/Complicated/Complex/Chaotic)
8. **hanlons_razor**: Distinguish malice from stupidity (bugs before blame)
9. **devils_advocate**: Stress-test proposals with counterarguments
10. **comparative_analysis**: "Search → Evaluate → Implement" workflow (NEW)

### Configuration Components

#### `cognitive_reasoning_config.json`
- **Path**: `C:\Users\brsth\.claude\hooks\cognitive_reasoning_config.json`
- **Purpose**: Master configuration for cognitive reasoning system
- **Structure**:
  - `cognitive_frameworks.frameworks.*`: Enable/disable individual enhancers
  - `cognitive_frameworks.max_enhancers_by_topic.*`: Per-topic limits
  - `reasoning_modes.*`: Sequential/multi-agent/reflective/analytical modes
  - `think_profiles.profiles.*`: Profile-based routing (debug_rca, refactor_plan, etc.)
  - `questioning_patterns.patterns.*`: Meta-cognitive questioning patterns
- **Responsibility**: Centralized configuration for all cognitive features
- **Inputs**: JSON file (read on each hook invocation)
- **Outputs**: Dict consumed by cognitive_enhancers.py
- **Known limitations**:
  - No runtime validation (fails open on errors)
  - No schema enforcement (manual edits required)

### Memory/Guidance Components

#### `working_principles.md`
- **Path**: `C:\Users\brsth\.claude\projects\P--\memory\working_principles.md`
- **Purpose**: Constitutional-level engineering heuristics
- **Principle 8**: "Comparative Analysis First" - prevents suboptimal-first suggestions
- **Pre-proposal checklist**:
  1. Did I generate 2-3 diverse candidates FIRST?
  2. Did I search for existing implementations BEFORE suggesting new code?
  3. Did I consider native/platform-native solutions BEFORE custom scripts?
  4. Is this the BEST option after comparison, or just the FIRST option I thought of?
- **Responsibility**: Constitutional guidance for ALL conversations (not just hook-triggered)
- **Inputs**: Read from memory during session initialization
- **Outputs**: Text loaded into system context
- **Known limitations**:
  - No enforcement mechanism (guidance only)
  - Relies on model adherence

#### `questioning_patterns.md`
- **Path**: `C:\Users\brsth\.claude\projects\P--\memory\questioning_patterns.md`
- **Purpose**: Meta-cognitive questions to catch reasoning flaws during design
- **Pattern 0**: "Comparative Analysis First" - Same as Working Principle 8
- **Pattern 1**: "Why this specific value?" - Detects arbitrary thresholds
- **Pattern 2**: "Are you sure about concurrency?" - Detects race conditions
- **Pattern 3**: "Is this optimal or over-engineering?" - Detects over-engineering
- **Pattern 4**: "What happens at scale?" - Detects swiss cheese maintenance
- **Pattern 5**: "Debugging Cognition" - Entry point first, parallel diagnostics
- **Responsibility**: Document meta-cognitive patterns for design-time self-correction
- **Inputs**: Read from memory during session initialization
- **Outputs**: Text loaded into system context
- **Known limitations**:
  - No enforcement mechanism (guidance only)
  - Relies on model adherence

### Infrastructure Components

#### `observability.py` (imported)
- **Path**: `C:\Users\brsth\.claude\hooks\UserPromptSubmit_modules\observability.py`
- **Purpose**: Logging for cognitive enhancer selection
- **Key function**: `log_cognitive_selection(enhancers, intent, tokens, rationale)`
- **Responsibility**: Emit observability data for debugging
- **Inputs**: Selected enhancers, intent dict, token count, rationale
- **Outputs**: JSON log entry to stdout (never stderr)
- **Known limitations**:
  - No structured log aggregation (stdout only)
  - No metrics dashboard

---

## 5. DESIGN INTENT AND NON-NEGOTIABLES

### Architectural Pillars
1. **Fail-Open**: Invalid config → use defaults, never block prompt processing
2. **Stdout Only**: Never write to stderr (Claude Code treats stderr as error)
3. **Per-Topic Limits**: Different cognitive loads for different task types (implementation=3, diagnostic=2, decomposition=4)
4. **Tag Emission**: Model MUST prepend `[COG]` tag when cognitive frameworks active
5. **Two-Level Enforcement**:
   - Hook level: Forced injection when UserPromptSubmit fires
   - Constitutional level: Working Principle 8 applies to ALL conversations

### Technology Constraints
- **Python 3.12+**: Type hints required (enforced by code review)
- **stdlib-only**: No external dependencies (no numpy, pandas, etc.)
- **JSON config**: Human-editable, no schema validation (fail-open on parse errors)
- **Windows 11**: POSIX-compliant tools via bash (Git Bash or WSL)

### Performance SLAs
- **Max detection time**: 60ms (configurable via `max_detection_ms`)
- **Token budget**: 500 tokens max injection (configurable)
- **Slow detection threshold**: 30ms (logs warnings if exceeded)

### Things That Must NOT Change
1. **Fail-open policy**: Invalid config must NEVER block prompt processing
2. **Stdout-only logging**: stderr writes are treated as errors by Claude Code
3. **Tag emission format**: `[COG] Active Frameworks: X, Y, Z\nWhy: {rationale}\n\n` is required
4. **Per-topic limits**: implementation(3), diagnostic(2), meta_rca(2), decomposition(4)
5. **Working Principle 8**: Constitutional-level "Comparative Analysis First" pattern

---

## 6. KNOWN ISSUES

### Issue 1: Hook-Only Enforcement (CRITICAL - PARTIALLY FIXED)
- **Scenario**: User asks "Should I use Python or prompting for X?" in free-form conversation
- **Expected**: Comparative analysis pattern applies (2-3 options generated first)
- **Actual**: Hook doesn't fire (no skill invocation), pattern not enforced
- **Impact**: Suboptimal-first suggestions still occur in general conversation
- **Workaround**: Added Working Principle 8 to `working_principles.md` (constitutional level)
- **Status**: PARTIALLY FIXED - Hook level + Constitutional level now in place
- **Remaining gap**: Constitutional guidance has no enforcement mechanism (relies on model adherence)

### Issue 2: Hard-Coded Magic Number (FIXED)
- **Scenario**: `max_enhancers_per_prompt: 3` was universal hard cap
- **Expected**: Quality-based per-topic limits
- **Actual**: All topics capped at 3 enhancers regardless of cognitive load
- **Impact**: Decomposition tasks need 4 enhancers, diagnostic tasks need 2
- **Fix**: Added `max_enhancers_by_topic` configuration with per-topic limits
- **Status**: FIXED - Now uses quality-based per-topic configuration

### Issue 3: No Semantic Intent Detection (ACCEPTABLE)
- **Scenario**: User says "The system is slow, diagnose the issue"
- **Expected**: Diagnostic intent detected
- **Actual**: Regex pattern matching only (no embeddings/semantic search)
- **Impact**: False negatives on intent classification
- **Workaround**: None (acceptable tradeoff for performance/simplicity)
- **Status**: ACCEPTABLE - Regex-based detection is fast (<5ms) and sufficient

### Issue 4: Token Budget Estimation is Rough (ACCEPTABLE)
- **Scenario**: Injection text is 1200 chars, counted as 300 tokens
- **Expected**: Accurate token count
- **Actual**: Rough estimate (chars // 4)
- **Impact**: Token budget may be slightly exceeded
- **Workaround**: Set token limit to 500 (conservative buffer)
- **Status**: ACCEPTABLE - Claude models can handle slight overages

---

## 7. INTEGRATION POINTS

### Where New Enhancers Can Plug In

#### Adding a New Cognitive Enhancer
1. **Define enhancer** in `cognitive_enhancers.py`:
   ```python
   Enhancer(
       name="new_enhancer",
       injection="**New Enhancer**: {injection text}",
       topics=["implementation", "diagnostic"],  # Which intents trigger this
   )
   ```
2. **Add to config JSON**:
   ```json
   "cognitive_frameworks.frameworks.new_enhancer": true
   ```
3. **Add to default config** in `_DEFAULT_CONFIG` dict
4. **Test**: Trigger intent topic, verify enhancer fires

#### Adding a New Topic
1. **Define topic logic** in `_detect_intent()`:
   ```python
   intent["new_topic"] = bool(_NEW_RE.search(prompt))
   ```
2. **Add enhancers for topic** (assign `topics=["new_topic"]` to enhancers)
3. **Configure per-topic limit** in config JSON:
   ```json
   "max_enhancers_by_topic.new_topic": 3
   ```

#### Adding a New Questioning Pattern
1. **Add pattern** to `questioning_patterns.md`:
   ```markdown
   ## Pattern N: "Question Name" (Detection Trigger)

   **Detection trigger**: When to apply this pattern
   **Generalized pattern**: What question to ask yourself
   **Detection trigger**: Concrete trigger condition
   ```
2. **Register in config JSON**:
   ```json
   "questioning_patterns.patterns.new_pattern.enabled": true
   ```

### Invocation Model
- **Event-driven**: UserPromptSubmit hook fires on every prompt
- **Priority**: 11.0 (runs early in hook chain)
- **Registration**: `UserPromptSubmit_modules/registry.py` as core_hook_module
- **Bypass**: Export `CONSTITUTIONAL_HOOKS_BYPASS=1` to disable

### Data Exchange Contracts
- **Input**: `HookContext` object with `prompt` field
- **Output**: `HookResult` object with `context` (injection text), `tokens` (count), `priority`
- **Side effects**: None (stateless hook)

---

## 8. APPENDIX: SAMPLE RUNS / LOGS

### Sample 1: Implementation Intent Detection
```python
# Input prompt
"Implement a Python script to generate summaries"

# Intent detection
intent = {
    "implementation": True,  # _IMPL_RE matched "Implement"
    "diagnostic": False,
    "meta_rca": False,
    "decomposition": False,
    "implementation_diagnostic": False,
}

# Enhancer selection (implementation topic, max 3)
selected = [
    Enhancer("assumption_surfacing", topics=["implementation"]),
    Enhancer("outcome_anchoring", topics=["implementation"]),
    Enhancer("comparative_analysis", topics=["implementation", "decision_analysis"]),
]

# Injection text
"""
[COG] Active Frameworks: Assumption Surfacing, Outcome Anchoring, Comparative Analysis
Why: implementation intent detected

**TAG EMISSION REQUIRED**: Begin your response with '[COG]' tag...

**Assumption Check**: Before proceeding, explicitly state your key assumptions...

**Outcome Anchor**: Before starting, define what 'done' looks like...

**Comparative Analysis First**: Before suggesting any solution, follow 'Search → Evaluate → Implement'...
"""
```

### Sample 2: Fast Mode Bypass
```python
# Input prompt
"Fix the bug #fast"

# Mode override detection
mode_match = _MODE_RE.search("#fast")
# Returns: <re.Match object>

# Mode application from config
modes = config.get("modes", {})
fast_config = modes["fast"]  # {"disable_all": True}

# Result: All enhancers bypassed
selected = []  # Empty list

# Injection text
""  # No injection (empty string)
```

### Sample 3: Per-Topic Limit Enforcement
```python
# Input prompt (long, vague)
"Can you help me understand the architecture and figure out how all these components work together and what might be causing the performance issues we're seeing in production?"

# Intent detection
intent = {
    "implementation": False,
    "diagnostic": True,  # "figure out", "causing"
    "meta_rca": False,
    "decomposition": True,  # Length >= 200 chars, no specific references
    "implementation_diagnostic": False,
}

# Per-topic limit selection
detected_topics = ["diagnostic", "decomposition"]
max_enhancers = config["max_enhancers_by_topic"]["diagnostic"]  # 2

# All matching enhancers (5 total)
all_matching = [
    Enhancer("calibrated_confidence", topics=["diagnostic"]),
    Enhancer("cynefin_classification", topics=["diagnostic", "meta_rca"]),
    Enhancer("hanlons_razor", topics=["diagnostic"]),
    Enhancer("socratic_decomposition", topics=["decomposition"]),
    Enhancer("comparative_analysis", topics=["implementation", "decision_analysis"]),
]

# Limited to first 2 (per diagnostic topic limit)
selected = all_matching[:2]  # [calibrated_confidence, cynefin_classification]
```

---

## CONFIGURATION REFERENCE

### Enable/Disable Individual Enhancers
```json
{
  "cognitive_frameworks.frameworks.assumption_surfacing": true,
  "cognitive_frameworks.frameworks.outcome_anchoring": true,
  "cognitive_frameworks.frameworks.inversion_prompting": true,
  "cognitive_frameworks.frameworks.chestertons_fence": true,
  "cognitive_frameworks.frameworks.calibrated_confidence": true,
  "cognitive_frameworks.frameworks.socratic_decomposition": true,
  "cognitive_frameworks.frameworks.cynefin_classification": true,
  "cognitive_frameworks.frameworks.hanlons_razor": true,
  "cognitive_frameworks.frameworks.devils_advocate": true,
  "cognitive_frameworks.frameworks.comparative_analysis": true
}
```

### Per-Topic Max Enhancers
```json
{
  "max_enhancers_by_topic": {
    "implementation": 3,
    "diagnostic": 2,
    "meta_rca": 2,
    "decomposition": 4,
    "implementation_diagnostic": 3
  }
}
```

### Mode Overrides
```json
{
  "modes": {
    "rca": {"topic": "meta_rca"},
    "deep": {"topic": "implementation"},
    "fast": {"disable_all": true}
  }
}
```

### Questioning Patterns
```json
{
  "questioning_patterns.patterns": {
    "comparative_analysis_first": {
      "enabled": true,
      "trigger_question": "Did I generate 2-3 options before selecting?",
      "detection_trigger": "Any proposal to implement, create, build, or add solution"
    },
    "arbitrary_threshold": {
      "enabled": true,
      "trigger_question": "Why this specific value?",
      "detection_trigger": "Any time I catch myself thinking 'that seems reasonable' without data"
    }
  }
}
```

---

## VERIFICATION CHECKLIST

### To Verify Hook Is Working
1. Trigger UserPromptSubmit event with skill invocation (e.g., `/code "test"`)
2. Check for `[COG]` tag in model response
3. Verify enhancer names appear in tag: `[COG] Active Frameworks: X, Y, Z`
4. Verify rationale appears: `Why: {intent_topic}`

### To Verify Constitutional Guidance
1. Read `working_principles.md` Principle 8
2. Check that Pre-proposal checklist is present
3. Verify MEMORY.md references Principle 8

### To Verify Per-Topic Limits
1. Read `cognitive_reasoning_config.json`
2. Check `max_enhancers_by_topic` section
3. Verify limits: implementation(3), diagnostic(2), meta_rca(2), decomposition(4)

### To Verify Comparative Analysis Integration
1. Check `_ENHANCERS` list in `cognitive_enhancers.py` (line 299-309)
2. Verify `comparative_analysis` enhancer exists
3. Check topics include `["implementation", "decision_analysis"]`
4. Verify config JSON has `"comparative_analysis": true`

---

## END OF REVIEW BUNDLE

**Document status**: Complete
**Coverage**: Core cognitive enhancement system (hooks + constitutional guidance)
**Date**: 2026-03-17
**Next review**: After major system changes or 6 months
