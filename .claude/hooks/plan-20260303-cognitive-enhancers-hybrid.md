# Plan: Hybrid Cognitive Enhancers Architecture

**Plan Date:** 2026-03-03
**Author:** AI Assistant
**Status:** DRAFT

---

## Summary

Split `cognitive_enhancers.py` into hybrid architecture: keep sentence-transformers embeddings for high-value FAP detection only, migrate other 6 cognitive enhancers to lightweight config-driven regex system. This eliminates the 56-second timeout issue while preserving detection accuracy for critical failure-analysis prompts.

**Files Changed:** 3 created, 1 modified, 1 updated
**Estimated Effort:** Medium (2-3 hours)
**Rollback:** Single git revert

---

## 1. Problem Statement

### Current Issue
`cognitive_enhancers.py` (660 lines) uses sentence-transformers embeddings for all intent detection, causing:
- **56-second timeout** when API call to claude-haiku-4.5 fails (line 549)
- **~500ms model loading** overhead on every hook execution
- **Dependency on external packages** (sentence-transformers, numpy, anthropic)

### Root Cause
Medium-similarity edge cases (0.65-0.82 similarity) escalate to LLM API classifier with broken timeout mechanism. The threading-based timeout (`t.join(timeout=3.0)`) doesn't work correctly on Windows, causing hangs.

### Stakeholder Impact
- **Users**: 56-second delay before prompt processing resumes
- **System**: Hook timeout blocks entire UserPromptSubmit event
- **Reliability**: Timeout occurs intermittently based on prompt similarity

### Business Value
- **Performance**: Reduce hook execution from ~600ms to ~100ms (6x faster)
- **Reliability**: Eliminate timeout failures entirely
- **Maintainability**: Config-driven behavior easier to tune than code

---

## 2. Context Analysis

### Allowed APIs

**Hook Registration** (Source: `registry.py:38-57`)
```python
from UserPromptSubmit.registry import register_hook
from UserPromptSubmit.base import HookResult, HookContext

@register_hook("hook_name", priority=5.0)
def hook_function(context: HookContext) -> HookResult:
    return HookResult(context="text", tokens=10)
```

**HookResult API** (Source: `base.py`)
- `HookResult.empty()` — No injection
- `HookResult(context="text", tokens=10, priority=5.0)` — Text injection
- `HookResult(context={"suppress": ["hook_name"]})` — Suppress downstream hooks

**Config Loading** (Source: `shared_utils.py:158-189`)
```python
def load_config(config_path: Path) -> dict:
    """Load JSON config with fail-open defaults."""
    if config_path.exists():
        try:
            with open(config_path) as f:
                return json.load(f)
        except Exception:
            pass
    return default_config()
```

### Anti-Patterns to Avoid

**❌ Don't block on missing config**
```python
# WRONG: Config errors crash hook
with open("config.json") as f:
    config = json.load(f)
```

**❌ Don't use bare except:**
```python
# WRONG: Catches KeyboardInterrupt
except:
    return {}
```

**❌ Don't hardcode priorities**
```python
# WRONG: Priority scattered in code
@register_hook("my_hook", priority=11.5)  # Magic number
```

### Current Architecture

**Current Priority Order** (registry.py:70-79)
```
coach_note_reader: 5.0
analysis_protocol_gate: 11.2
socratic_decomposition: 11.3
outcome_anchoring: 11.4
assumption_surfacing: 11.5
inversion_prompting: 11.6
chestertons_fence: 11.7
calibrated_confidence: 11.8
```

**Current Detection Logic**
- FAP: Regex + sentence-transformers (lines 405-552)
- Other enhancers: Regex patterns only (no embeddings)

---

## 3. Existing Implementation Discovery

### Current File Structure

**`cognitive_enhancers.py` (583 lines)** contains:
- 8 registered hooks (7 cognitive + 1 coach note)
- 12 utility functions
- Sentence-transformers model loading (lines 376-400)
- FAP prototype embeddings (lines 438-451)
- Cosine similarity calculation (lines 470-473)
- LLM classifier with broken timeout (lines 476-518)

### Dependencies

**External packages:**
- `sentence-transformers` — Semantic embeddings
- `numpy` — Vector operations
- `anthropic` — Haiku API classifier (unused after our fix)

**Internal modules:**
- `.base` — HookContext, HookResult
- `.registry` — @register_hook decorator
- `Stop_advisory` — Coach note persistence

### Key Functions to Preserve

**`_should_inject_fap()`** (lines 521-552)
- Two-layer detection: regex → semantic similarity
- Thresholds: `_HIGH_SIM = 0.82`, `_MID_SIM = 0.65`
- Returns: bool (fire FAP or not)

**`_load_config()`** (lines 63-72)
- Path: `PARENT_DIR / "cognitive_enhancers_config.json"`
- Fail-open design (return defaults on error)
- Used by all hooks for per-hook enable/disable

**`_extract_skill_name()`** (lines 117-121)
- Detects slash commands: `/commit` → "commit"
- Used to blacklist operational commands

### Current Config Schema

**`cognitive_enhancers_config.json`:**
```json
{
  "enabled": true,
  "analysis_protocol_gate": true,
  "assumption_surfacing": true,
  "outcome_anchoring": true,
  "inversion_prompting": true,
  "chestertons_fence": true,
  "calibrated_confidence": true,
  "socratic_decomposition": true,
  "socratic_min_length": 200,
  "min_prompt_length": 30,
  "enhance_skills": true,
  "skip_skills": ["commit", "push", "search", ...]
}
```

---

## 4. Test Discovery

### Test Scenarios

**Scenario 1: FAP Detection**
- Input: "perform root cause analysis of system failure"
- Expected: FAP injection fires (regex match)
- Verification: Check output contains "Failure Analysis Protocol active"

**Scenario 2: High Similarity FAP**
- Input: "why did the production deployment fail?"
- Expected: FAP injection fires (similarity ≥0.82)
- Verification: Check output contains FAP checklist

**Scenario 3: Non-FAP Implementation**
- Input: "create a new user authentication module"
- Expected: No FAP, may get assumption_surfacing
- Verification: No FAP in output

**Scenario 4: Config Override**
- Set `"assumption_surfacing": false` in config
- Input: "implement feature X"
- Expected: No assumption_surfacing injection
- Verification: Output lacks "Assumption Check"

**Scenario 5: Priority Ordering**
- Input: "debug why the refactored login fails" (diagnostic + implementation)
- Expected: Both calibrated_confidence AND assumption_surfacing
- Verification: Both injections present

**Scenario 6: Skill Blacklist**
- Input: "/commit"
- Expected: No cognitive enhancement (skip_skills)
- Verification: Empty hook output

**Scenario 7: Timeout Fix**
- Input: Prompt with 0.75 similarity (was medium band)
- Expected: No timeout, completes in <5 seconds
- Verification: Hook execution time <5s

### Test Commands

```bash
# Test FAP detection
echo '{"prompt": "perform root cause analysis", "session_id": "test", "terminal_id": "test"}' | \
  timeout 10 python P:\.claude\hooks\UserPromptSubmit.py

# Test config disable
# Edit config.json: {"assumption_surfacing": false}
echo '{"prompt": "implement feature", "session_id": "test", "terminal_id": "test"}' | \
  python P:\.claude\hooks\UserPromptSubmit.py

# Test timeout fix
echo '{"prompt": "medium similarity prompt", "session_id": "test", "terminal_id": "test"}' | \
  time python P:\.claude\hooks\UserPromptSubmit.py
```

---

## 5. Proposed Solution

### Architecture Overview

Split monolithic `cognitive_enhancers.py` into three files:

```
cognitive_enhancers.py (660 lines)
    ↓ Split into:
├── analysis_protocol_gate.py (NEW, ~250 lines)
│   - Sentence-transformers embeddings for FAP only
│   - Priority: 11.8 (highest cognitive enhancer)
│   - Config: fap_semantic_enabled (default: true)
├── cognitive_enhancers.py (REFACTORED, ~400 lines)
│   - Config-driven regex-based routing
│   - 6 enhancers: assumption_surfacing, outcome_anchoring, etc.
│   - Priority: 11.0 (lower than FAP gate)
│   - Config: topics, enhancers, modes, max_enhancers_per_prompt
└── coach_note_reader.py (MOVED, ~50 lines)
    - Unchanged logic
    - Priority: 5.0 (earliest)
```

### Priority Ordering

```
coach_note_reader: 5.0 (unchanged)
cognitive_enhancers (config-driven): 11.0
analysis_protocol_gate (embeddings): 11.8
```

**Rationale:** FAP gate runs before config-driven enhancers to prevent topic-gating conflicts.

### Detection Strategy

**FAP Detection** (analysis_protocol_gate.py)
1. Layer 1: Regex fast path (lines 405-430)
2. Layer 2: Semantic similarity (lines 432-552)
   - `sim >= 0.82`: Auto-fire FAP
   - `sim < 0.82`: Skip (removed API call)

**Other Enhancers** (cognitive_enhancers.py)
1. Regex-based intent detection
2. Config-driven topic mapping
3. Multi-topic combo support (implementation_diagnostic)
4. User modes (#rca, #fast, #deep)

---

## 6. Implementation Plan

### Phase 1: Create analysis_protocol_gate.py

**File:** `P:\.claude\hooks\UserPromptSubmit\analysis_protocol_gate.py`

**Extract from cognitive_enhancers.py:**
- `_RCA_PATTERN`, `_META_PRINCIPLE_PATTERN`, `_CORRECTION_PATTERN` (lines 405-407)
- `_FAP_PROTOTYPES` (lines 438-449)
- `_load_config()` (lines 63-72)
- `_load_fap_model()`, `_prewarm_fap_model()` (lines 376-400)
- `_get_proto_embeddings()`, `_cosine_max()` (lines 455-473)
- `_should_inject_fap()` (lines 521-552, with API call removed)
- `analysis_protocol_gate` hook function (lines 566-581)

**Add new config option:**
```python
"fap_semantic_enabled": true  # Master toggle for embeddings
"fap_similarity_threshold": 0.85  # Configurable threshold
```

**Priority:** 11.8 (higher than cognitive_enhancers)

**Acceptance Criteria:**
- [ ] File compiles without errors
- [ ] All imports resolve (sentence-transformers, numpy, .base, .registry)
- [ ] Hook registered in registry
- [ ] FAP detection works for test prompts
- [ ] Config option `fap_semergic_enabled: false` disables embeddings

### Phase 2: Refactor cognitive_enhancers.py

**File:** `P:\.claude\hooks\UserPromptSubmit\cognitive_enhancers.py`

**Remove from current file:**
- FAP-related code (lines 351-581)
- Embedding model loading
- LLM classifier functions
- Sentence-transformers imports

**Add new implementation:**
- `_DEFAULT_CONFIG` dataclass with topics/enhancers/modes
- `Enhancer` dataclass
- `_DETECTED_INTENT` patterns (regex only, no embeddings)
- `_detect_intent()` function (regex + heuristics)
- `_select_enhancers()` function (topic-based routing)
- `_build_injection()` function
- Unified `cognitive_enhancers()` hook (priority 11.0)

**Config schema:**
```json
{
  "enabled": true,
  "topics": {
    "implementation": true,
    "diagnostic": true,
    "meta_rca": true,
    "decomposition": true,
    "implementation_diagnostic": true  // Multi-topic combo
  },
  "enhancers": {
    "assumption_surfacing": true,
    "outcome_anchoring": true,
    "inversion_prompting": true,
    "chestertons_fence": true,
    "calibrated_confidence": true,
    "socratic_decomposition": true
  },
  "max_enhancers_per_prompt": 3,
  "min_prompt_length": 30,
  "socratic_min_length": 200,
  "enhance_skills": true,
  "skip_skills": ["commit", "push", ...],
  "modes": {
    "rca": {"topic": "meta_rca"},
    "deep": {"topic": "implementation"},
    "fast": {"disable_all": true}
  }
}
```

**Acceptance Criteria:**
- [ ] No sentence-transformers imports
- [ ] All 6 enhancers work via config
- [ ] Multi-topic combos work (e.g., "refactor and debug")
- [ ] User modes work (#rca, #fast)
- [ ] Config-driven enable/disable works
- [ ] Hook executes in <100ms average

### Phase 3: Move coach_note_reader

**File:** `P:\.claude\hooks\UserPromptSubmit\coach_note_reader.py`

**Move from cognitive_enhancers.py:**
- `coach_note_reader()` function (lines 333-348)
- `_load_config()` call (keep as-is)

**Priority:** 5.0 (unchanged)

**Acceptance Criteria:**
- [ ] File compiles
- [ ] Coach note injection works
- [ ] Config option `coach_note_reader` controls it

### Phase 4: Update registry.py

**File:** `P:\.caaude\hooks\UserPromptSubmit\registry.py`

**Change import list (lines 141-155):**
```python
from . import (
    active_command_writer,
    analysis_protocol_gate,  # NEW
    anti_sycophancy_injector,
    cognitive_enhancers,  # Will be refactored
    coach_note_reader,    # NEW (moved from cognitive_enhancers)
    competence_injector,
    continuation_spine,
    diagnostic_guard,
    edit_consent,
    operating_rules,
    plan_injector,
    skill_enforcer,
    think_trigger,
    turn_marker,
    unified_injector,
)
```

**Acceptance Criteria:**
- [ ] All three files import successfully
- - [ ] No import errors
- [ ] Registry loads all hooks
- [ ] Hooks execute in correct priority order

### Phase 5: Update config schema

**File:** `P:\.claude\hooks\cognitive_enhancers_config.json`

**Add new sections:**
```json
{
  "fap_semantic_enabled": true,
  "fap_similarity_threshold": 0.85,
  "topics": {
    "implementation": true,
    "diagnostic": true,
    "meta_rca": true,
    "decomposition": true,
    "implementation_diagnostic": true
  },
  "max_enhancers_per_prompt": 3,
  "modes": {
    "rca": {"topic": "meta_rca"},
    "deep": {"topic": "implementation"},
    "fast": {"disable_all": true}
  }
}
```

**Acceptance Criteria:**
- [ ] Config is valid JSON
- [ ] Old config files still work (backward compatibility)
- [ ] Missing keys use sensible defaults

---

## 7. Risks, Success Criteria, Dependencies

### Top Risks

**Risk 1: Breaking FAP Detection**
- **Likelihood:** Medium
- **Impact:** High (failure analysis prompts don't get protocol)
- **Mitigation:** Keep sentence-transformers logic unchanged, add `fap_semantic_enabled` toggle for rollback
- **Test:** Verify FAP fires for "root cause analysis" prompts

**Risk 2: Priority Collision**
- **Likelihood:** Low
- **Impact:** Medium (wrong execution order)
- **Mitigation:** Set analysis_protocol_gate priority to 11.8 (higher than cognitive_enhancers 11.0)
- **Test:** Verify FAP runs before other enhancers

**Risk 3: Config Migration**
- **Likelihood:** Low
- **Impact:** Medium (user config breaks)
- **Mitigation:** Shallow merge pattern with defaults, document new config sections
- **Test:** Test with missing/empty config file

**Risk 4: Detection Accuracy Regression**
- **Likelihood:** Medium
- **Impact:** Medium (more false negatives on semantic prompts)
- **Mitigation:** Keep embeddings for FAP, use soft scaffolds ("if appropriate") for other enhancers
- **Test:** Compare before/after on 50 sample prompts

**Risk 5: Import Errors**
- **Likelihood:** Low
- **Impact:** High (all UserPromptSubmit hooks fail)
- **Mitigation:** Test all imports before committing, graceful degradation on import failure
- **Test:** Import all three modules in fresh Python session

### Success Criteria

**Functional:**
- [ ] All 8 hooks load and execute successfully
- [ ] FAP detection triggers for failure-analysis prompts (regex + semantic)
- [ ] Non-FAP enhancers trigger via config-driven routing
- [ ] User modes (#rca, #fast) override routing correctly
- [ ] Multi-topic combos work (e.g., "debug the refactored login")
- [ ] Hook execution time <5 seconds (was 56 seconds)
- [ ] No dependencies on anthropic API

**Performance:**
- [ ] Average hook execution: <100ms (down from ~600ms)
- [ ] No model loading delay (first prompt still loads model)
- [ ] Config reload: <10ms

**Compatibility:**
- [ ] Old cognitive_enhancers_config.json still works (backward compatible)
- [ ] Missing config uses sensible defaults
- [ ] No breaking changes to hook function signatures

**Quality:**
- [ ] All ruff checks pass (no linting errors)
- [ ] All type hints valid (no mypy errors)
- [ ] Code follows existing patterns (shared_utils config loading)
- [ ] Documentation updated (README.md, ARCHITECTURE.md)

### Dependencies

**Blockers (must resolve before starting):**
- None identified

**Required:**
- `sentence-transformers` package (keep for FAP)
- `numpy` package (keep for FAP)
- Python 3.12+ (existing requirement)

**Optional:**
- Test coverage reports (nice-to-have, not blocking)

### Rollback Strategy

**Single Git Commit:**
```bash
git add P:\.claude\hooks\UserPromptSubmit\*.py
git commit -m "Refactor cognitive_enhancers into hybrid architecture"

# If issues arise:
git revert HEAD  # Single command rollback
```

**Alternative: Keep backup**
```bash
cp cognitive_enhancers.py cognitive_enhancers.py.backup
# ... implement changes ...
# If problems:
cp cognitive_enhancers.py.backup cognitive_enhancers.py
```

---

## Next Actions

1. **Review this plan** — Confirm architecture and approach
2. **Run `/plan-workflow review P:\.claude\hooks\plan-20260303-cognitive-enhancers-hybrid.md`** — Validate plan quality
3. **Address any HALT conditions** from verifier
4. **Begin implementation** — Follow Phase 1-5 sequence
5. **Test thoroughly** — Run all 7 test scenarios
6. **Commit changes** — Single atomic commit for easy rollback
