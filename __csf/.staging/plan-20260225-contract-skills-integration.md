# Plan: Contract System Skill Integration

**Plan ID**: plan-20260225-contract-skills-integration
**Created**: 2026-02-25
**Status**: DRAFT
**Phase**: Builder (Phase 0 complete)

---

## 1. Problem Statement

**Current Issue**: The contract enforcement system blocks legitimate skills from operating in new terminals due to over-constrained scoping (`session_id + terminal_id`).

**Impact**:
- Skills like `/review_bundle`, `/plan-workflow`, and 15+ others require per-terminal contract bootstrap
- Skills cannot declare their security requirements or trust level
- Investigation reads already exempt (Rule 1.7) but skills still blocked on Write
- Contract portability issue: Each new terminal requires manual bootstrap

**User Quote**: "This contract system is stupid. /review_bundle should always allow read and bash to gather info, and allow writing the file. Those are normal and intended operations for this skills."

**Root Cause**: Contract system designed for ad-hoc tasks without considering legitimate, pre-authorized skills with known security profiles.

---

## 2. Context Analysis

### Allowed APIs (Confirmed from Documentation Discovery)

**Contract State Management**:
```python
# P:\.claude\hooks\repositories\contract_state.py
load_contract(session_id: str, terminal_id: Optional[str]) -> dict
save_contract(session_id: str, contract: dict, terminal_id: Optional[str]) -> bool
```

**Bootstrap Creation**:
```python
# P:\.claude\hooks\repositories\bootstrap_contract.py
contract = {
    "type": "implementation",
    "task_id": _make_task_id(session_id, task),
    "status": "in_progress",
    "deliverables": [...],
    "created_at": datetime.now(timezone.utc).isoformat()
}
```

**Hook Registration**:
```python
# P:\.claude\settings.json (lines 102-113)
"PreToolUse": [
  {"type": "command", "command": "python .../PreToolUse_skill_pattern_gate.py"},
  {"type": "command", "command": "python .../PreToolUse_investigation_gate.py"},
  {"type": "command", "command": "python .../PreToolUse_contract_enforcer.py"}
]
```

### Anti-Patterns to Avoid

**❌ DO NOT attempt to**:
- Create `get_contract_by_user()` method (no user-scoped contracts exist)
- Implement global contract storage (violates terminal isolation design)
- Add contract modification APIs in enforcer (enforcer is read-only)
- Auto-create contracts without explicit user intent (violates bootstrap protocol)

**✅ Instead, work with**:
- Session-level scoping (remove terminal_id constraint)
- SKILL.md frontmatter for security declarations
- Trusted skills auto-bootstrap (explicit allowlist)
- Hook reordering for exemption gates

### Current Skill Authorization Landscape

**Existing Systems**:
1. **SKILL_EXECUTION_REGISTRY** (PreToolUse_skill_pattern_gate.py:79-158)
   - Maps skill names → allowed tools + patterns
   - Used for validation, not authorization

2. **First-Tool Coherence Gate** (PreToolUse_skill_pattern_gate.py:22-27)
   - Restricts initial tool based on skill type
   - Investigation tools vs execution tools

3. **Knowledge Skills List** (PreToolUse_skill_pattern_gate.py:161-166)
   - 15+ skills exempted from execution requirements
   - Special categorization for reference skills

4. **State-Transition Patterns** (agentic-validation/resources/state-transition-pattern.md)
   - Progressive tool access control
   - Phase-based authorization

**Gap**: No mechanism for skills to declare "I am trusted, allow my operations" or "I only use safe tools".

---

## 3. Existing Implementation Discovery

### Contract Scoping Implementation

**Terminal ID Detection**:
```python
# P:\.claude\hooks\repositories\contract_enforcer.py:534-541
from terminal_detection import detect_terminal_id
terminal_id = detect_terminal_id()
if not terminal_id:
    return {}

contract_state = ContractState(
    session_id=session_id,
    contracts_dir=_resolve_contracts_dir(),
    terminal_id=terminal_id  # ← Over-constrained scoping
)
```

**Contract Path Structure**:
```python
# P:\.claude\hooks\repositories\contract_state.py:148-150
state_path = (
    self.contracts_dir / "contracts" /
    self.session_id / session_id / f"{tid}.json"
)
# Result: .claude/state/contract_guard/contracts/{session_id}/{session_id}/{terminal_id}.json
```

### Bootstrap Workflow

**Bootstrap Detection**:
```python
# P:\.claude\hooks\repositories\contract_enforcer.py:341-361
def _is_bootstrap_action(tool_name: str, tool_input: dict) -> bool:
    if tool_name != "Bash":
        return False
    command = _as_text(tool_input.get("command"))
    bootstrap_markers = (
        "bootstrap_contract.py",
        "repositories/bootstrap_contract.py",
        "create contract",
        "establish contract",
    )
    return any(marker in command for marker in bootstrap_markers)
```

**One-Time Bootstrap Marker**:
```python
# P:\.claude\hooks\repositories\contract_enforcer.py:627-640
def _consume_one_time_bootstrap(session_id: str, tool_name: str, tool_input: dict) -> bool:
    marker_path = _bootstrap_marker_path(session_id)
    marker = {
        "timestamp": time.time(),
        "session_id": session_id,
        "tool_name": tool_name,
        "command": str(tool_input.get("command", ""))[:400],
    }
    marker_path.write_text(json.dumps(marker), encoding="utf-8")
    return True
```

### Investigation Exemption (Rule 1.7)

**Already Implemented**:
```python
# P:\.claude\hooks\PreToolUse\contract_enforcer.py:614-622
# Rule 1.7: Investigation intent exemption - allow read-only investigation without contract
if tool_name == "Bash":
    command = tool_input.get("command", "")
    if _is_read_only_bash_command(command):
        user_message = _get_user_message(input_data)
        if _is_investigation_intent(user_message):
            return {"allowed": True, "reason": ""}
```

**Helper Functions**:
- `_is_read_only_bash_command(command)` - Detects ls, cat, grep, head, etc.
- `_is_investigation_intent(message)` - Detects investigate, understand, analyze keywords
- `_get_user_message(input_data)` - Extracts user message from conversation context

### Skill Frontmatter Schema

**Current SKILL_SCHEMA.md** (from documentation discovery):
```yaml
---
name: skill-name
description: One line description
category: category-name
triggers:
  - /skill-name
aliases:
  - /skill-name
suggest:
  - /related-skill
execution:
  directive: |
    Execute instructions
  default_args: ""
  examples:
    - "/skill-name arg1"
---
```

**Gap**: No `security:` or `permissions:` section exists for skills to declare trust level.

---

## 4. Test Discovery

### Existing Contract Tests

**Test Files Found**:
1. `P:\.claude\hooks\UserPromptSubmit\tests\test_entrypoint_contract.py`
2. `P:\.claude\hooks\repositories\tests\test_contract_api.py`
3. `P:\.claude\hooks\repositories\tests\test_contract_enforcer_tdd_suggestion.py`
4. `P:\.claude\hooks\repositories\tests\test_contract_state.py`
5. `P:\.claude\hooks\repositories\tests\test_contract_tracker.py`

**Test Coverage**:
- Contract loading/saving
- Bootstrap workflow
- Block counter increment
- Recovery mode activation

### Existing Hook Tests

**Test Infrastructure**:
- `P:\.claude\hooks\tests\run_hook_test.py` - Test runner framework
- `P:\.claude\hooks\tests\test_hook_registration.py` - Registration verification

**Critical Test Pattern** (from CLAUDE.md):
```python
# Exit code 2 from PreToolUse hook = BLOCK (correct behavior)
# Exit code 0 = Allow/pass-through

# For file-verification hooks (PostToolUse):
# 1. Create test file FIRST
# 2. Pipe synthetic hook input
# 3. Clean up after
```

### Investigation Fix Test (Created Earlier)

**Location**: `P:\__csf\.staging\test_investigation_fix.py`

**Test Functions**:
- `test_read_only_command_detection()` - Verifies ls, cat, grep detection
- `test_investigation_intent_detection()` - Verifies keyword detection
- `test_combined_logic()` - Verifies command + intent combination

**Status**: Created but not executed (blocked by contract enforcement in new terminal)

### Tests to Add for This Plan

**Required Test Scenarios**:
1. **Phase 1 (Hook Reordering)**:
   - Test: investigation_gate runs before contract_enforcer
   - Test: Read-only commands bypass contract
   - Test: Substantive commands still require contract

2. **Phase 2 (Session-Level Scoping)**:
   - Test: Contract loads with session_id only (no terminal_id)
   - Test: Contract portable across terminals in same session
   - Test: New terminal inherits existing session contract

3. **Phase 3 (Skill-Aware Authorization)**:
   - Test: Trusted skill auto-bootstraps without manual authorization
   - Test: SKILL.md frontmatter `security: trusted` recognized
   - Test: Non-trusted skills still require contract
   - Test: Malicious skill cannot claim trusted status

---

## 5. Proposed Solution

**Three-Phase Implementation** (ordered by risk and complexity):

### Phase 1: Hook Reordering (Immediate Relief, 1 hour, Zero Risk)

**Problem**: Investigation gate runs AFTER contract enforcer, so Read operations work but Write is still blocked.

**Solution**: Reorder hooks in `settings.json` to move investigation_gate before contract_enforcer.

**Impact**:
- ✅ Investigation reads bypass contract (already works via Rule 1.7)
- ✅ Investigation writes bypass contract (NEW - fixes /review_bundle issue)
- ✅ Zero risk - just reordering, no code changes
- ⚠️  Still requires terminal-specific bootstrap for non-investigation work

**Implementation**:
```json
// P:\.claude\settings.json (lines 102-113)
"PreToolUse": [
  {"type": "command", "command": "python .../PreToolUse_skill_pattern_gate.py"},
  {"type": "command", "command": "python .../PreToolUse_investigation_gate.py"},  // ← Move before contract_enforcer
  {"type": "command", "command": "python .../PreToolUse_contract_enforcer.py"}
]
```

**Success Criteria**:
- `/review_bundle` can write files when gathering investigation info
- Rule 1.7 covers both Read and Write operations for investigation
- No regression in existing contract enforcement

### Phase 2: Session-Level Contract Scoping (Portability, 4-8 hours, Low Risk)

**Problem**: Contracts scoped to `session_id + terminal_id`, not portable across terminals.

**Solution**: Remove `terminal_id` from contract path, scope to `session_id` only.

**Impact**:
- ✅ Contract portable across terminals in same session
- ✅ Single bootstrap per session (not per terminal)
- ✅ Reduces user friction significantly
- ⚠️  Requires migration of existing contracts

**Implementation**:
```python
# P:\.claude\hooks\repositories\contract_state.py
# OLD: contracts/{session_id}/{session_id}/{terminal_id}.json
# NEW: contracts/{session_id}/contract.json

def _contract_path(self, session_id: str, terminal_id: Optional[str] = None) -> Path:
    # Ignore terminal_id, use session-level scoping
    return self.contracts_dir / "contracts" / session_id / "contract.json"
```

**Migration Strategy**:
1. Add migration function: `_migrate_to_session_level()`
2. On load, check for old path → copy to new path
3. Keep old path as fallback for 1 session
4. Log migration for debugging

**Success Criteria**:
- Contract loads in new terminal without re-bootstrap
- Existing contracts migrated successfully
- No data loss during migration

### Phase 3: Skill-Aware Authorization (Long-Term Solution, 16-24 hours, Medium Risk)

**Problem**: Skills cannot declare trust level or security requirements.

**Solution**: Extend SKILL.md frontmatter with `security:` section and auto-bootstrap trusted skills.

**Frontmatter Addition**:
```yaml
---
name: review_bundle
description: Create comprehensive context bundles
security:
  level: trusted  # trusted | standard | restricted
  allowed_tools:
    - Read
    - Grep
    - Glob
    - Bash  # read-only only
    - Write  # output only
  justification: |
    Review bundle is a read-only information gathering skill.
    It reads files, searches code, and writes a single output file.
    No modification of user code, no execution of untrusted commands.
    Skill is part of core infrastructure and has been manually audited.
---
```

**Implementation**:
```python
# P:\.claude\hooks\PreToolUse\contract_enforcer.py
def _is_skill_trusted(input_data: dict) -> bool:
    """Check if current skill is trusted and auto-bootstrap."""
    skill_name = input_data.get("skill_name")
    if not skill_name:
        return False

    skill_md = Path(f".claude/skills/{skill_name}/SKILL.md")
    if not skill_md.exists():
        return False

    content = skill_md.read_text()
    # Parse frontmatter
    if "security:" in content and "level: trusted" in content:
        return True
    return False

# In run() function:
if _is_skill_trusted(input_data):
    # Auto-bootstrap for trusted skills
    _auto_bootstrap_skill(session_id, skill_name)
    return {"allowed": True, "reason": "trusted_skill"}
```

**Allowlist Validation**:
```python
# P:\.claude\settings.json (add new env var)
"TRUSTED_SKILLS_ALLOWLIST": "review_bundle,plan-workflow,discover,arch,q,p,r,s,t"
```

**Security Safeguards**:
1. **Explicit allowlist only** - No auto-trust based on frontmatter alone
2. **Manual audit required** - Each skill added to allowlist manually reviewed
3. **Frontmatter as documentation** - Declares intent, not authorization
4. **Regular audit** - Quarterly review of trusted skills list

**Success Criteria**:
- Trusted skills work without manual bootstrap
- Non-trusted skills still require contract
- Allowlist enforced (no unauthorized trust)
- Frontmatter documents security requirements

---

## 6. Implementation Plan

### Phase 1: Hook Reordering (Immediate Relief)

**File**: `P:\.claude\settings.json`

**Steps**:
1. Read current PreToolUse hook order (line 102-113)
2. Move `PreToolUse_investigation_gate.py` before `PreToolUse_contract_enforcer.py`
3. Save updated settings.json
4. Test: Invoke `/review_bundle` and verify it can write output file

**Estimated Time**: 30 minutes

**Risk**: Zero - only reordering, no code changes

**Dependencies**: None

**Verification Command**:
```bash
# Test that investigation gate runs first
echo '{"tool_name": "Write", "tool_input": {"file_path": "test_output.md"}, "skill_name": "review_bundle"}' | python P:/.claude/hooks/PreToolUse_investigation_gate.py
```

### Phase 2: Session-Level Contract Scoping

**File**: `P:\.claude\hooks\repositories\contract_state.py`

**Steps**:
1. Modify `_contract_path()` to ignore `terminal_id`
2. Add migration function `_migrate_to_session_level()`
3. Update `load_contract()` to call migration
4. Add logging for migration events
5. Test: Create contract in terminal A, load in terminal B

**Estimated Time**: 4-6 hours

**Risk**: Low - isolated to contract state management, migration has fallback

**Dependencies**: None

**Verification Commands**:
```bash
# Create contract in terminal A
python P:/.claude/hooks/repositories/bootstrap_contract.py "test session contract"

# Load contract in terminal B (should work without re-bootstrap)
python -c "from repositories.contract_state import ContractState; cs = ContractState(session_id='test'); print(cs.load_contract('test'))"
```

### Phase 3: Skill-Aware Authorization

**Files**:
1. `P:\.claude\skills\SKILL_SCHEMA.md` - Add `security:` section documentation
2. `P:\.claude\hooks\PreToolUse\contract_enforcer.py` - Add `_is_skill_trusted()`
3. `P:\.claude\settings.json` - Add `TRUSTED_SKILLS_ALLOWLIST` env var

**Steps**:
1. Document `security:` frontmatter in SKILL_SCHEMA.md
2. Implement `_is_skill_trusted()` function
3. Implement `_auto_bootstrap_skill()` function
4. Add allowlist validation
5. Update contract_enforcer.py to check skill trust before blocking
6. Add security safeguards (allowlist enforcement, audit logging)
7. Test: Create test skill with `level: trusted`, verify auto-bootstrap

**Estimated Time**: 16-24 hours

**Risk**: Medium - touches core contract enforcement logic

**Dependencies**:
- Phase 2 complete (session-level scoping makes this easier)

**Verification Commands**:
```bash
# Test trusted skill auto-bootstrap
echo '{"tool_name": "Write", "skill_name": "review_bundle"}' | python P:/.claude/hooks/PreToolUse/contract_enforcer.py

# Test allowlist enforcement
echo '{"tool_name": "Write", "skill_name": "malicious_skill"}' | python P:/.claude/hooks/PreToolUse/contract_enforcer.py
```

### Test Implementation

**Test Files to Create**:
1. `P:\.claude\hooks\tests\test_phase1_investigation_order.py`
2. `P:\.claude\hooks\tests\test_phase2_session_scoping.py`
3. `P:\.claude\hooks\tests\test_phase3_skill_trust.py`

**Test Framework**: Use existing `run_hook_test.py` pattern

---

## 7. Risks, Success Criteria, Dependencies

### Risks

**Phase 1 Risks**:
- ❌ None identified - zero-risk change

**Phase 2 Risks**:
- ⚠️  **Risk**: Migration fails, existing contracts lost
  - **Mitigation**: Keep old path as fallback for 1 session, add extensive logging
  - **Rollback**: Revert `_contract_path()` change, fallback still works

**Phase 3 Risks**:
- ⚠️  **Risk**: Malicious skill claims `level: trusted`
  - **Mitigation**: Explicit allowlist in settings.json, frontmatter is documentation only
  - **Rollback**: Remove `_is_skill_trusted()` check, disable env var

- ⚠️  **Risk**: Auto-bootstrap bypasses user consent
  - **Mitigation**: Allowlist is opt-in, manual audit required for each skill
  - **Rollback**: Clear allowlist, require manual bootstrap for all skills

### Success Criteria

**Phase 1 Success**:
- ✅ `/review_bundle` can write files without manual bootstrap
- ✅ Investigation writes bypass contract (Rule 1.7 extended)
- ✅ No regression in existing contract enforcement

**Phase 2 Success**:
- ✅ Contract portable across terminals in same session
- ✅ Single bootstrap per session (not per terminal)
- ✅ Existing contracts migrated without data loss

**Phase 3 Success**:
- ✅ Trusted skills work without manual bootstrap
- ✅ Allowlist enforced (no unauthorized trust)
- ✅ Frontmatter documents security requirements

### Dependencies

**Phase 1**:
- None (can proceed immediately)

**Phase 2**:
- None (independent of Phase 1)

**Phase 3**:
- Phase 2 recommended (session-level scoping simplifies implementation)
- SKILL_SCHEMA.md update required

### Rollback Strategy

**Phase 1 Rollback**:
- Revert settings.json hook order

**Phase 2 Rollback**:
- Revert `_contract_path()` change
- Old path still works as fallback

**Phase 3 Rollback**:
- Set `TRUSTED_SKILLS_ALLOWLIST=""` to disable
- Remove `_is_skill_trusted()` check

---

## Top Risks

1. **Phase 2 Migration Failure** (Medium probability, High impact)
   - **Mitigation**: Extensive logging, fallback path, test migration in dev first

2. **Phase 3 Allowlist Bypass** (Low probability, High impact)
   - **Mitigation**: Explicit allowlist only, no auto-trust, manual audit required

## Next Actions

1. **Immediate** (Phase 1): Reorder hooks in settings.json (30 minutes)
   ```bash
   # Edit P:\.claude\settings.json, move investigation_gate before contract_enforcer
   ```

2. **Short-term** (Phase 2): Implement session-level scoping (4-6 hours)
   ```bash
   # Modify contract_state.py, add migration function
   ```

3. **Long-term** (Phase 3): Implement skill-aware authorization (16-24 hours)
   ```bash
   # Extend SKILL_SCHEMA.md, add trust checking
   ```

4. **Testing**: Create test suite for all phases
   ```bash
   # Write test files in P:\.claude\hooks\tests\
   ```

---

**Plan Path**: `P:\__csf\.staging\plan-20260225-contract-skills-integration.md`
**Summary**: Three-phase solution to fix contract system friction with skills - Phase 1 (hook reordering, 1hr), Phase 2 (session-level scoping, 4-8hrs), Phase 3 (skill-aware authorization, 16-24hrs)
**Top Risks**: Phase 2 migration failure, Phase 3 allowlist bypass
**Next Actions**: 1) Reorder hooks in settings.json (30min), 2) Implement session-level scoping, 3) Implement skill-aware authorization
