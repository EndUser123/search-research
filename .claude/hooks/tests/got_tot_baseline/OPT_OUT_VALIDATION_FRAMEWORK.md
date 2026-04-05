# Opt-Out Flag Independence Validation Framework

**Purpose**: Validate that GoT and ToT opt-out flags work independently across all 9 target skills in the GoT/ToT integration plan.

**Reference Implementation**: `P:\.claude\skills\code\tests\test_opt_out_flags.py`

---

## Validation Checklist

For each target skill, verify the following:

### 1. Default Behavior (Quality-First Design)

- [ ] **GoT enabled by default** (if skill uses GoT)
  - Enhancement runs without explicit flag
  - No user action required to activate

- [ ] **ToT enabled by default** (if skill uses ToT)
  - Enhancement runs without explicit flag
  - No user action required to activate

### 2. Flag Functionality

- [ ] **`--no-got` flag disables GoT** (GoT skills only)
  - Flag presence detected correctly
  - Enhancement skipped when flag present
  - Traditional approach used instead

- [ ] **`--no-tot` flag disables ToT** (ToT skills only)
  - Flag presence detected correctly
  - Enhancement skipped when flag present
  - Traditional approach used instead

### 3. Flag Independence

- [ ] **Flags work independently**
  - `--no-got` does not affect ToT behavior
  - `--no-tot` does not affect GoT behavior
  - Both flags can be used simultaneously

- [ ] **All flag combinations tested**
  - No flags: both enhancements active (default)
  - `--no-got` only: GoT disabled, ToT active
  - `--no-tot` only: GoT active, ToT disabled
  - Both flags: both enhancements disabled

### 4. Flag Parsing

- [ ] **Command-line argument parsing works**
  - Flags detected in args list
  - Parsing logic: `'--no-got' not in args`
  - Environment variable support: `SKILL_NO_GOT=true`, `SKILL_NO_TOT=true`

### 5. Integration Points

- [ ] **Enhancement integrates into skill workflow correctly**
  - GoT: Architecture analysis phase (or equivalent)
  - ToT: Trace/scenario generation phase (or equivalent)
  - No workflow disruption when disabled

---

## Target Skills Matrix

| Skill | GoT | ToT | Validation Status |
|-------|-----|-----|-------------------|
| /trace | ❌ | ✅ | ⏳ Pending |
| /t | ❌ | ✅ | ⏳ Pending |
| /debugRCA | ❌ | ✅ | ⏳ Pending |
| /arch | ✅ | ❌ | ⏳ Pending |
| /plan-workflow | ✅ | ✅ | ⏳ Pending |
| /p | ❌ | ✅ | ⏳ Pending |
| /q | ✅ | ✅ | ⏳ Pending |
| /r | ✅ | ✅ | ⏳ Pending |
| /s | ✅ | ✅ | ⏳ Pending |

**Legend**:
- ✅ = Enhancement applies to this skill
- ❌ = Enhancement does not apply
- ⏳ Pending = Validation not yet performed
- ✅ Complete = Validation passed
- ⚠️ Issues = Validation found issues

---

## Test Pattern Templates

### Template 1: Default Behavior Test

```python
def test_{enhancement}_enabled_by_default(self, sample_input):
    """Test that {enhancement} is enabled by default (opt-out design)"""
    # Simulate default behavior (no flag)
    enhancement_enabled = True  # Default

    if enhancement_enabled:
        # Should run enhancement when enabled
        result = run_enhancement(sample_input)
        assert enhancement_detected_in_result(result)
```

### Template 2: Flag Functionality Test

```python
def test_no_{enhancement}_flag_disables(self, sample_input):
    """Test that --no-{enhancement} flag disables {enhancement}"""
    # Simulate --no-{enhancement} flag
    enhancement_enabled = False

    if not enhancement_enabled:
        # Should use traditional approach
        result = run_traditional_approach(sample_input)
        assert enhancement_NOT_detected_in_result(result)
```

### Template 3: Independence Test

```python
def test_no_got_does_not_affect_tot(self, sample_input):
    """Test that --no-got flag does not affect ToT behavior"""
    got_enabled = False
    tot_enabled = True

    # ToT should still work independently
    if tot_enabled:
        result = run_tot_enhancement(sample_input)
        assert tot_detected_in_result(result)
```

### Template 4: Flag Parsing Test

```python
def test_flag_parsing(self):
    """Test command-line flag parsing logic"""
    args = []  # No flags

    got_enabled = '--no-got' not in args
    tot_enabled = '--no-tot' not in args

    # Default: both enabled
    assert got_enabled is True
    assert tot_enabled is True

    # Test with --no-got
    args = ['--no-got']
    got_enabled = '--no-got' not in args
    tot_enabled = '--no-tot' not in args

    assert got_enabled is False
    assert tot_enabled is True
```

---

## Environment Variable Support

### Pattern

```python
import os

# Check environment variables
got_enabled = os.getenv('SKILL_NO_GOT', 'false').lower() != 'true'
tot_enabled = os.getenv('SKILL_NO_TOT', 'false').lower() != 'true'

# Default: both enabled (env vars not set or set to 'false')
assert got_enabled is True
assert tot_enabled is True

# Test with SKILL_NO_GOT=true
os.environ['SKILL_NO_GOT'] = 'true'
got_enabled = os.getenv('SKILL_NO_GOT', 'false').lower() != 'true'

assert got_enabled is False
```

### Environment Variable Names by Skill

| Skill | GoT Env Var | ToT Env Var |
|-------|-------------|-------------|
| /trace | N/A | `TRACE_NO_TOT` |
| /t | N/A | `T_NO_TOT` |
| /debugRCA | N/A | `DEBUGRCA_NO_TOT` |
| /arch | `ARCH_NO_GOT` | N/A |
| /plan-workflow | `PLAN_WORKFLOW_NO_GOT` | `PLAN_WORKFLOW_NO_TOT` |
| /p | N/A | `P_NO_TOT` |
| /q | `Q_NO_GOT` | `Q_NO_TOT` |
| /r | `R_NO_GOT` | `R_NO_TOT` |
| /s | `S_NO_GOT` | `S_NO_TOT` |

---

## Validation Protocol

### Step 1: SKILL.md Review

For each target skill:
1. Read `P:\.claude\skills\<skill>\SKILL.md`
2. Search for enhancement documentation
3. Verify opt-out flag documentation exists
4. Check for environment variable documentation

### Step 2: Implementation Check

For each target skill:
1. Locate enhancement integration point in skill
2. Verify flag parsing logic exists
3. Verify default behavior (enhancement enabled without flag)
4. Verify enhancement skips when flag present

### Step 3: Test Creation (if needed)

If test coverage is missing:
1. Use test pattern templates above
2. Create skill-specific test file
3. Test all flag combinations
4. Verify independence

### Step 4: Constitutional Hook Integration

**SEC-001**: Opt-out flags must NOT bypass constitutional safety checks

Verify that:
- Opt-out flags disable enhancements only
- Constitutional hooks still run regardless of opt-out flags
- No security shortcuts when enhancements disabled

---

## Validation Results Template

```markdown
## Skill: /skill-name

**Enhancement Types**: GoT, ToT, or Both

**SKILL.md Documentation**:
- [ ] GoT enhancement documented
- [ ] ToT enhancement documented
- [ ] Opt-out flags documented (--no-got, --no-tot)
- [ ] Environment variables documented (SKILL_NO_GOT, SKILL_NO_TOT)

**Implementation Verification**:
- [ ] Default behavior: both enhancements enabled
- [ ] --no-got flag disables GoT
- [ ] --no-tot flag disables ToT
- [ ] Flags work independently
- [ ] Environment variable support works

**Test Coverage**:
- [ ] Default behavior tests pass
- [ ] Flag functionality tests pass
- [ ] Independence tests pass
- [ ] Flag parsing tests pass

**Constitutional Compliance**:
- [ ] Opt-out flags do NOT bypass safety checks
- [ ] Constitutional hooks still active
- [ ] No security shortcuts

**Status**: ✅ Complete / ⚠️ Issues / ❌ Failed

**Issues Found**:
- List any issues discovered during validation

**Recommendations**:
- List any recommendations for improvement
```

---

## Success Criteria

Task 0.6 is complete when:

1. **All 9 skills validated** against the checklist above
2. **Test coverage exists** for each skill's opt-out flag behavior
3. **Independence verified** - flags work independently in all skills
4. **Constitutional compliance confirmed** - opt-out flags do not bypass safety checks
5. **Documentation complete** - SKILL.md files document opt-out flags correctly

**Estimated Time**: 4-6 hours

**Next Task**: Phase 1, Task 1.1 - /trace ToT Integration (8-12 hours)
