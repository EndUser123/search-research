# Architecture Decision: think_trigger.py Validation Gap - Optimal Solution

**Date:** 2026-03-08
**Template:** python.md
**Intent:** IMPROVE_SYSTEM (optimize/harden existing hooks validation)
**Status:** Approved

---

## Decision

Implement hybrid approach: **Import-time assertions (immediate) + Single-source dataclass refactor (long-term)**

---

## Rationale

### Problem
- `think_trigger.py` has 3 separate dictionaries: `_PROFILES`, `_STRONG_PATTERNS`, `_WEAK_PATTERNS`
- No structural relationship enforced between them
- Runtime `KeyError: 'security_review'` when profile detected but template missing
- 200+ line separation between pattern and template definitions

### Solution Structure
1. **Import-time assertions** - Immediate protection, minimal effort, zero production overhead
2. **Expanded health check** - CI/CD validation, tests all code paths
3. **Single-source refactor** - Permanent elimination of this bug class

### Python-Specific Benefits
- `if __debug__` guard optimized out in production (`python -O`)
- `@dataclass(frozen=True)` provides type-safe, immutable single source
- Fails fast on import during development, not at runtime in production

---

## Implementation

### Phase 1: Immediate (Today)

**File:** `P:/.claude/hooks/UserPromptSubmit_modules/think_trigger.py`

**Add after line 321:**
```python
# Module-level invariant check (runs on import)
if __debug__:  # Only runs in dev/test, optimized out in production
    missing_templates = set(_COMPILED_STRONG.keys()) - set(_PROFILES.keys())
    missing_patterns = set(_PROFILES.keys()) - set(_COMPILED_STRONG.keys())

    if missing_templates or missing_patterns:
        raise AssertionError(
            f"Profile configuration mismatch in think_trigger.py:\n"
            f"  Missing templates: {missing_templates}\n"
            f"  Missing patterns: {missing_patterns}\n"
            f"  _PROFILES has {len(_PROFILES)} profiles, _COMPILED_STRONG has {len(_COMPILED_STRONG)}"
        )
```

**File:** `P:/.claude/hooks/comprehensive_hook_health_check.py`

**Add test function:**
```python
def test_think_trigger_profile_consistency() -> dict:
    """Test that all think_trigger profiles have both patterns and templates."""
    try:
        from UserPromptSubmit_modules.think_trigger import _PROFILES, _COMPILED_STRONG

        template_keys = set(_PROFILES.keys())
        pattern_keys = set(_COMPILED_STRONG.keys())

        if template_keys != pattern_keys:
            missing_templates = pattern_keys - template_keys
            missing_patterns = template_keys - pattern_keys
            return {
                "status": "error",
                "reason": f"Profile mismatch: missing_templates={missing_templates}, "
                         f"missing_patterns={missing_patterns}"
            }

        return {"status": "success", "profiles_tested": len(pattern_keys)}

    except Exception as e:
        return {"status": "error", "reason": str(e)}
```

### Phase 2: Validation (This Week)
1. Run `comprehensive_hook_health_check.py` - should pass
2. Test removing a template - import should fail
3. Verify CI/CD runs health check before merge
4. Monitor for "hook error" reports (should be zero)

### Phase 3: Structural Refactor (Next Sprint)

**Refactor to single-source dataclass:**
```python
from dataclasses import dataclass

@dataclass(frozen=True)
class ThinkProfile:
    """Single source of truth for a thinking profile."""
    name: str
    template: str
    strong_patterns: list[str]
    weak_patterns: list[str] | None = None

_THINK_PROFILES: dict[str, ThinkProfile] = {
    "debug_rca": ThinkProfile(
        name="debug_rca",
        template="""THINK PROFILE: DEBUG / ROOT CAUSE ANALYSIS...""",
        strong_patterns=[r"flaky", r"intermittent(?:ly)?", ...],
        weak_patterns=[_stem("bug", "s|gy"), ...]
    ),
    # ... all 7 profiles co-located
}

# Derive dictionaries from single source
_PROFILES: dict[str, str] = {
    name: profile.template for name, profile in _THINK_PROFILES.items()
}
```

---

## Alternatives Considered

| Alternative | Rationale for Rejection |
|-------------|------------------------|
| Runtime check in `_detect_profile()` | Fails at runtime (after user experiences bug), not development |
| Expand `_PROFILES` only | Doesn't add validation for future additions |
| `TypedDict` instead of `@dataclass` | No runtime enforcement, only type-checker validation |
| Property-based testing (Hypothesis) | Complementary, not replacement for import-time checks |

**Forced Alternative Quality Gate Applied:** Each alternative differs on at least one axis (timing, enforcement, coverage).

---

## Risk Assessment

| Option | Technical Risk | Integration Risk | Performance Risk |
|--------|----------------|------------------|------------------|
| Import-time assertions | Very Low | None | None |
| Expanded health check | Very Low | None | Negligible |
| Dataclass refactor | Medium | Low | Negligible |

**Version Verification:** All Python features verified against 3.12+ documentation (`if __debug__`, `@dataclass(frozen=True)`).

---

## Confidence

**85%** - Evidence basis:
- Codebase analysis: think_trigger.py structure (lines 1-334)
- Confirmed bug: KeyError at line 332
- Test infrastructure: comprehensive_hook_health_check.py reviewed
- Python best practices: Import-time invariants standard (Django, SQLAlchemy)

**Key assumptions:**
1. Python 3.12+ environment
2. Development workflow includes importing modules
3. Health check runs in CI/CD
4. Team can coordinate refactor without merge conflicts

---

## Adversarial Self-Review

**Weakest assumption:** "Import-time assertions will catch misalignment during development."

**Challenge:** If team only tests hooks via subprocess (never imports directly), assertion won't trigger.

**Consequence:** Bug survives until health check expansion deployed.

**Mitigation:** Deploy Option 1 and Option 2 together as single fix.

---

## References

- Original bug analysis: Previous conversation transcript
- File: `P:/.claude/hooks/UserPromptSubmit_modules/think_trigger.py`
- File: `P:/.claude/hooks/comprehensive_hook_health_check.py`
- Python dataclasses: https://docs.python.org/3.12/library/dataclasses.html
- Python assertion docs: https://docs.python.org/3.12/reference/simple_stmts.html#the-assert-statement

---

**Persisted as:** `P:/.claude/arch_decisions/2026-03-08_python_think-trigger-validation-gap-optimal-solution.md`
