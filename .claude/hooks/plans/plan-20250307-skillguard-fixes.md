# Plan: Fix skill-guard Issues and Add Brownfield Documentation

**Created**: 2025-03-07
**Status**: READY-FOR-IMPLEMENTATION
**Objective**: Fix all critical issues in skill-guard before brownfield plugin conversion, and enhance /package skill with brownfield next steps guidance

---

## 1. Problem Statement

skill-guard is a Python library that auto-discovers Claude skills from filesystem, used by hooks to enforce skill execution patterns. It needs conversion from Python library (`src/` structure) to Claude Code plugin (`core/` structure).

**Current Issues**:
- 5 critical issues that will break after plugin conversion (hardcoded paths, fragile parsing, silent failures, missing plugin structure, wrong documentation)
- 3 medium-priority issues (configurability, test coverage, type hints)
- /package skill lacks brownfield conversion guidance after PHASE 1.5 detection

**Impact**: Without fixes, the converted plugin will be non-portable, fragile, and difficult to debug. Without documentation, users won't know how to proceed after brownfield detection.

---

## 2. Context Analysis

### Current skill-guard Structure
```
skill-guard/
├── pyproject.toml          # Python library manifest
├── src/skill_guard/        # Python package (will migrate to core/)
│   ├── __init__.py
│   └── skill_auto_discovery.py  # 240 lines, main implementation
├── tests/                  # 2 test files, minimal coverage
├── README.md               # Documents as pip-installable library
└── scripts/                # Utility scripts
```

### Target plugin Structure
```
skill-guard/
├── .claude-plugin/
│   └── plugin.json         # Plugin manifest
├── core/                   # Migrated from src/skill_guard/
│   ├── __init__.py
│   └── skill_auto_discovery.py
├── hooks/
│   └── hooks.json          # Hook configuration
├── tests/                  # Expanded test suite
├── README.md               # Updated for plugin installation
└── CHANGELOG.md            # Migration documentation
```

### Allowed APIs (Documentation Discovery)

**Confirmed from skill-guard codebase**:
- `pathlib.Path` - File path operations
- `re.match()` - Currently used for YAML (will replace with `yaml.safe_load()`)
- `yaml.safe_load()` - pyyaml is in dependencies but not used

**Anti-patterns to Avoid**:
- Hardcoded paths like `"P:/.claude/skills"` - not portable
- Regex-based YAML parsing - fragile, use `yaml.safe_load()` instead
- Silent exception handling - prevents debugging

---

## 3. Existing Implementation Discovery

### skill_guard Package Analysis

**Current exports** (`src/skill_guard/__init__.py`):
```python
from .skill_auto_discovery import (
    KNOWLEDGE_SKILLS,
    discover_all_skills,
    get_skill_config,
)
```

**Main functions** (`skill_auto_discovery.py`):
- `discover_all_skills(skills_dir="P:/.claude/skills")` - Scans skill directories
- `_parse_skill_frontmatter(skill_md)` - Extracts YAML config from SKILL.md
- `get_skill_config(skill_name, explicit_registry)` - Returns skill config with fallback
- `_detect_script_pattern(skill_name)` - Finds run_heavy.py or similar

**Critical defects**:
1. Line 46: `skills_dir: str | Path = "P:/.claude/skills"` - Windows-specific
2. Line 103: `re.match(r"^---\n(.*?)\n---")` - Fragile YAML parsing
3. Line 138: `except Exception: return None` - Silent failures
4. Lines 25-41: `KNOWLEDGE_SKILLS = {...}` - Hardcoded set
5. Line 110: Manual YAML parsing instead of using pyyaml dependency

### /package Skill Structure

**Current brownfield detection** (PHASE 1.5):
- Detects `src/` + `pyproject.toml`
- Prompts user: "Convert to plugin?"
- Sets `PACKAGE_TYPE="brownfield-plugin"`

**Missing**: Next steps guidance after detection

---

## 4. Test Discovery

### Existing Tests

**test_auto_discovery_integration.py** (33 lines):
- Tests module imports
- Tests `discover_all_skills()` returns results
- Tests knowledge skills have no tools

**Missing test coverage**:
- Edge cases (malformed YAML, missing files, special characters)
- Error handling (parse errors, permission errors)
- Script pattern detection
- Path resolution
- Environment variable overrides

### Required Test Additions

**Unit tests needed**:
1. Test `_parse_skill_frontmatter()` with valid/invalid YAML
2. Test `discover_all_skills()` with non-existent directory
3. Test environment variable path override
4. Test KNOWLEDGE_SKILLS override mechanism
5. Test logging output for parse errors

**Integration tests needed**:
1. Test with real skill directory structure
2. Test migration from `src/` to `core/` imports
3. Test hook imports after conversion

---

## 5. Proposed Solution

### Part A: Fix skill-guard Critical Issues

**Fix 1: Portable Path Resolution**
```python
# Replace hardcoded path
import os
from pathlib import Path

default_skills_dir = Path(
    os.getenv("CLAUDE_SKILLS_DIR",
              os.path.expanduser("~/.claude/skills"))
)

def discover_all_skills(
    skills_dir: str | Path = default_skills_dir,
) -> dict:
```

**Fix 2: Use pyyaml for Parsing**
```python
import yaml
import logging

logger = logging.getLogger(__name__)

def _parse_skill_frontmatter(skill_md: Path) -> dict | None:
    try:
        content = skill_md.read_text(encoding="utf-8")

        if not content.startswith("---"):
            return None

        # Proper YAML parsing
        _, yaml_content, _ = content.split("---", 2)
        frontmatter = yaml.safe_load(yaml_content)

        if not frontmatter:
            return None

        config = {"name": skill_md.parent.name}

        # Extract fields from parsed YAML
        for key in ["name", "category", "description", "has_execution"]:
            if key in frontmatter:
                config[key] = frontmatter[key]

        return config

    except (IOError, OSError) as e:
        logger.error(f"File access error: {skill_md}: {e}")
        return None
    except yaml.YAMLError as e:
        logger.warning(f"YAML parse error in {skill_md}: {e}")
        return None
    except Exception as e:
        logger.warning(f"Unexpected error parsing {skill_md}: {e}")
        return None
```

**Fix 3: Configurable KNOWLEDGE_SKILLS**
```python
DEFAULT_KNOWLEDGE_SKILLS = {
    "standards",
    "constraints",
    # ... (existing set)
}

def get_knowledge_skills() -> set:
    """Get KNOWLEDGE_SKILLS with optional environment override."""
    env_override = os.getenv("SKILL_GUARD_KNOWLEDGE")
    if env_override:
        return set(skill.strip() for skill in env_override.split(","))
    return DEFAULT_KNOWLEDGE_SKILLS

# Use in _parse_skill_frontmatter:
knowledge_skills = get_knowledge_skills()
if config["name"] in knowledge_skills or category in ("knowledge", "meta"):
    config["has_execution"] = False
```

**Fix 4: Complete Type Hints**
```python
from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    class SkillConfig(TypedDict):
        name: str
        category: str
        description: str
        has_execution: bool
        allowed_first_tools: list[str]
        default_tools: list[str]

def discover_all_skills(
    skills_dir: str | Path = default_skills_dir,
) -> dict[str, SkillConfig]:
    # ...
```

### Part B: Expand Test Coverage

**New test file**: `tests/test_skill_auto_discovery.py`
```python
# Test path resolution
def test_discover_with_env_override():
    os.environ["CLAUDE_SKILLS_DIR"] = "/tmp/test-skills"
    # ... create test structure
    skills = discover_all_skills()
    assert len(skills) == expected_count

# Test YAML parsing
def test_parse_valid_yaml():
    # ... create SKILL.md with valid frontmatter
    config = _parse_skill_frontmatter(skill_md)
    assert config is not None
    assert config["name"] == "test-skill"

def test_parse_invalid_yaml():
    # ... create SKILL.md with malformed YAML
    config = _parse_skill_frontmatter(skill_md)
    assert config is None  # Should handle gracefully

# Test error handling
def test_parse_missing_file():
    config = _parse_skill_frontmatter(Path("/nonexistent/file.md"))
    assert config is None

# Test KNOWLEDGE_SKILLS override
def test_knowledge_skills_override():
    os.environ["SKILL_GUARD_KNOWLEDGE"] = "custom1,custom2"
    skills = get_knowledge_skills()
    assert "custom1" in skills
    assert "custom2" in skills
```

### Part C: Add Brownfield Documentation to /package

**New section**: `references/brownfield-next-steps.md`

```markdown
# Brownfield Conversion Next Steps

## After PHASE 1.5 Detection

When PHASE 1.5 detects a Python library suitable for conversion:

### Pre-Conversion Checklist

Before running brownfield conversion:

1. **Fix Hardcoded Paths**
   - Search codebase for absolute paths (e.g., `/Users/...`, `P:/...`, `C:/...`)
   - Replace with environment variables or relative paths
   - Common patterns:
     - `os.getenv("VAR_NAME", default_value)`
     - `Path.home() / ".claude/skills"`
     - `CLAUDE_PLUGIN_ROOT` (for plugins)

2. **Fix Platform-Specific Code**
   - Windows-only scripts: add .bat/.ps1 alternatives
   - Unix-only scripts: add Windows equivalents
   - Use `sys.platform` or `platform.system()` for conditional logic

3. **Add Error Handling and Logging**
   - Replace silent failures with logging
   - Add `import logging; logger = logging.getLogger(__name__)`
   - Log errors with context: `logger.error(f"Failed: {file}: {e}")`

4. **Verify Dependencies**
   - Check all imports exist in target environment
   - Remove unused dependencies from pyproject.toml
   - Document required system tools (e.g., Python >= 3.10)

5. **Expand Test Coverage**
   - Add unit tests for edge cases
   - Test error handling paths
   - Verify tests pass before conversion

### Running the Conversion

1. **Run /package with detection**:
   ```bash
   /package P:/packages/your-library
   ```

2. **Confirm conversion prompt**:
   - PHASE 1.5 will ask: "Convert to plugin? (y/n)"
   - Type `y` to proceed

3. **Review conversion plan**:
   - Backup created: `.backup-before-plugin-{timestamp}/`
   - Migration: `src/` → `core/`
   - Removal: `pyproject.toml`
   - Addition: `.claude-plugin/plugin.json`, `hooks/hooks.json`

4. **Execute conversion**:
   - /package will automatically:
     - Create backup
     - Migrate files
     - Update imports
     - Create plugin structure
     - Update README

### Post-Conversion Validation

1. **Test imports work**:
   ```python
   # In Python REPL
   from core.skill_auto_discovery import discover_all_skills
   skills = discover_all_skills()
   assert len(skills) > 0
   ```

2. **Verify hooks can import**:
   - Test hook scripts import from `core` not `src`
   - Check all import paths updated

3. **Run test suite**:
   ```bash
   pytest tests/ -v
   ```

4. **Test plugin installation**:
   ```bash
   # Local development
   mklink /J "%USERPROFILE%\.claude\plugins\your-plugin" "P:/packages\your-plugin"
   /reload-plugins
   ```

### Rollback

If conversion fails:
1. Restore from backup: `.backup-before-plugin-{timestamp}/`
2. Delete new plugin structure
3. Run: `cp -r .backup-before-plugin-{timestamp}/* .`
```

**Update /package SKILL.md PHASE 1.6**:
```markdown
## PHASE 1.6: Brownfield Conversion (2min) — ONLY IF `PACKAGE_TYPE=brownfield-plugin`

**IMPORTANT**: Review `references/brownfield-next-steps.md` **before** running conversion.

**Quick checklist**:
- [ ] Fixed hardcoded paths?
- [ ] Added error handling and logging?
- [ ] Expanded test coverage?
- [ ] Verified dependencies?

**See `references/brownfield-conversion.md`** for complete workflow.

**See `references/brownfield-next-steps.md`** for pre-conversion checklist and validation steps.
```

---

## 6. Implementation Plan

### Step 1: Fix skill-guard Code Issues (Priority: CRITICAL)

**Task 1.1**: Fix hardcoded path in `skill_auto_discovery.py`
- **File**: `P:/packages/skill-guard/src/skill_guard/skill_auto_discovery.py`
- **Line**: 46
- **Change**: Replace `"P:/.claude/skills"` with environment variable
- **Acceptance**: Path resolution works on Windows, macOS, Linux
- **Verification**: Test with `CLAUDE_SKILLS_DIR` environment variable

**Task 1.2**: Replace regex YAML with pyyaml
- **File**: `P:/packages/skill-guard/src/skill_guard/skill_auto_discovery.py`
- **Lines**: 89-139
- **Change**: Use `yaml.safe_load()` instead of regex
- **Acceptance**: Parses complex YAML (lists, multiline strings)
- **Verification**: Unit tests with various YAML formats

**Task 1.3**: Add logging for error handling
- **File**: `P:/packages/skill-guard/src/skill_guard/skill_auto_discovery.py`
- **Lines**: 138-139
- **Change**: Replace silent exception with logger calls
- **Acceptance**: Parse errors log with context
- **Verification**: Trigger parse error, check logs

**Task 1.4**: Make KNOWLEDGE_SKILLS configurable
- **File**: `P:/packages/skill-guard/src/skill_guard/skill_auto_discovery.py`
- **Lines**: 25-41, 126
- **Change**: Add `get_knowledge_skills()` function with env override
- **Acceptance**: `SKILL_GUARD_KNOWLEDGE` env variable works
- **Verification**: Set env variable, test override

**Task 1.5**: Complete type hints
- **File**: `P:/packages/skill-guard/src/skill_guard/skill_auto_discovery.py`
- **Lines**: 18-21
- **Change**: Add SkillConfig TypedDict
- **Acceptance**: All functions have complete type annotations
- **Verification**: Run mypy type checker

### Step 2: Expand Test Coverage (Priority: HIGH)

**Task 2.1**: Create comprehensive unit tests
- **File**: `P:/packages/skill-guard/tests/test_skill_auto_discovery.py` (NEW)
- **Content**: 10+ test cases covering edge cases
- **Acceptance**: 80%+ code coverage
- **Verification**: `pytest --cov=src/skill_guard`

**Task 2.2**: Add error handling tests
- **File**: `P:/packages/skill-guard/tests/test_skill_auto_discovery.py`
- **Content**: Test malformed YAML, missing files, permission errors
- **Acceptance**: All error paths tested
- **Verification**: `pytest tests/test_skill_auto_discovery.py -v`

**Task 2.3**: Add integration tests
- **File**: `P:/packages/skill-guard/tests/test_conversion.py` (NEW)
- **Content**: Test `src/` → `core/` import migration
- **Acceptance**: Tests verify post-conversion imports work
- **Verification**: Run tests after conversion

### Step 3: Add Brownfield Documentation (Priority: MEDIUM)

**Task 3.1**: Create brownfield next steps guide
- **File**: `P:/.claude/skills/package/references/brownfield-next-steps.md` (NEW)
- **Content**:
  ```markdown
  # Brownfield Conversion Next Steps

  ## After PHASE 1.5 Detection

  When PHASE 1.5 detects a Python library suitable for conversion to a plugin:

  ### Pre-Conversion Checklist (CRITICAL)

  Before running brownfield conversion, fix these common issues:

  1. **Fix Hardcoded Paths** (CRITICAL)
     - Search: `grep -r "P:/" src/` (Windows-specific)
     - Search: `grep -r "/Users/" src/` (macOS-specific)
     - Replace with: `os.getenv("VARIABLE", default_value)`
     - Common patterns:
       ```python
       # Bad (hardcoded)
       skills_dir = "P:/.claude/skills"

       # Good (portable)
       default_skills_dir = Path(
           os.getenv("CLAUDE_SKILLS_DIR",
                     os.path.expanduser("~/.claude/skills"))
       )
       ```

  2. **Fix Platform-Specific Code** (CRITICAL)
     - Windows-only scripts (`.sh`): Add `.bat`/`.ps1` alternatives
     - Use: `sys.platform == "win32"` for conditional logic
     - Test on: Windows, macOS, Linux

  3. **Add Error Handling and Logging** (CRITICAL)
     - Replace: `except: return None` (silent failure)
     - Add: `import logging; logger = logging.getLogger(__name__)`
     - Log errors: `logger.error(f"Failed: {file}: {e}")`

  4. **Use Proper Dependencies** (HIGH)
     - Replace regex YAML parsing with `yaml.safe_load()`
     - Verify all imports exist in target environment
     - Remove unused dependencies from pyproject.toml

  5. **Expand Test Coverage** (HIGH)
     - Add unit tests for edge cases
     - Test error handling paths
     - Verify tests pass before conversion

  ### Running the Conversion

  1. Run `/package <your-library-path>`
  2. When PHASE 1.5 prompts, confirm conversion
  3. Review backup location: `.backup-before-plugin-{timestamp}/`
  4. Verify migration: `src/` → `core/`

  ### Post-Conversion Validation

  1. Test imports: `from core.module import function`
  2. Run tests: `pytest tests/ -v`
  3. Verify plugin structure: `.claude-plugin/`, `core/`, `hooks/`
  4. Test plugin installation locally

  ### Rollback if Needed

  ```bash
  # Restore from backup
  cp -r .backup-before-plugin-{timestamp}/* .
  rm -rf .backup-before-plugin-{timestamp}/
  ```

  ## Common Issues and Fixes

  ### Issue: Import Errors After Conversion
  **Symptom**: `ModuleNotFoundError: No module named 'src.package_name'`
  **Fix**: Update all imports from `src.package_name` to `core.package_name`

  ### Issue: Tests Fail with New Structure
  **Symptom**: Tests can't find modules
  **Fix**: Update test imports, run `pytest tests/ -v` to identify issues

  ### Issue: Hooks Can't Import Plugin Code
  **Symptom**: Hook scripts fail with import errors
  **Fix**: Use `CLAUDE_PLUGIN_ROOT` in hook paths:
    ```json
    {
      "command": "python CLAUDE_PLUGIN_ROOT/core/module.py"
    }
    ```
  ```
- **Acceptance**: Comprehensive guide covering all 5 critical fixes with examples
- **Verification**: Use guide to validate skill-guard fixes are complete

**Task 3.2**: Update /package SKILL.md PHASE 1.6
- **File**: `P:/.claude/skills/package/SKILL.md`
- **Lines**: PHASE 1.6 section (currently has summary + reference to brownfield-conversion.md)
- **Change**:
  ```markdown
  ## PHASE 1.6: Brownfield Conversion (2min) — ONLY IF `PACKAGE_TYPE=brownfield-plugin`

  **CRITICAL**: Review `references/brownfield-next-steps.md` **before** proceeding with conversion.

  **Pre-Conversion Checklist** (must complete all 5):
  - [ ] 1. Fixed hardcoded paths? (Search for `P:/`, `/Users/`, `C:/`)
  - [ ] 2. Fixed platform-specific code? (.sh scripts need .bat alternatives)
  - [ ] 3. Added error handling and logging? (No silent failures)
  - [ ] 4. Verified dependencies? (Use proper YAML parsing, not regex)
  - [ ] 5. Expanded test coverage? (Test edge cases and error paths)

  **What happens during conversion**:
  - Backup created: `.backup-before-plugin-{timestamp}/`
  - Migration: `src/{{NAME}}/` → `core/`
  - Python imports updated: `from {{NAME}}` → `from core`
  - Removed: `pyproject.toml` (plugins don't need pip packaging)
  - Created: `.claude-plugin/plugin.json`, `hooks/hooks.json`
  - Updated: README.md (migration notice + plugin installation)

  **See `references/brownfield-conversion.md`** for complete workflow.

  **See `references/brownfield-next-steps.md`** for pre-conversion checklist and validation steps.
  ```
- **Acceptance**: PHASE 1.6 has clear checklist, references both documentation files
- **Verification**: Read PHASE 1.6, confirm all 5 checklist items are listed

**Task 3.3**: Update /package Bundled Resources section
- **File**: `P:/.claude/skills/package/SKILL.md`
- **Section**: Bundled Resources (near top of file after "Additional References")
- **Change**: Add to the list:
  ```markdown
  **Additional References** (`references/`):
  - `brownfield-conversion.md` - Python library to plugin conversion
  - `brownfield-next-steps.md` - Pre-conversion checklist and validation (NEW)
  - `plugin-environment.md` - CLAUDE_PLUGIN_ROOT usage guide
  ```
- **Acceptance**: All reference files including new one are documented
- **Verification**: Check that Bundled Resources section lists all 3 files

### Step 4: Validate Before Conversion (Priority: CRITICAL)

**Task 4.1**: Run full test suite
- **Command**: `pytest P:/packages/skill-guard/tests/ -v --cov=src/skill_guard`
- **Acceptance**: All tests pass, 80%+ coverage
- **Verification**: Review test output

**Task 4.2**: Verify code quality
- **Command**: `ruff check src/skill_guard/` and `mypy src/skill_guard/`
- **Acceptance**: No critical lint errors
- **Verification**: Review lint output

**Task 4.3**: Test portable path resolution
- **File**: `P:/packages/skill-guard/src/skill_guard/skill_auto_discovery.py`
- **Commands**:
  - Windows: `python -c "from src.skill_guard import discover_all_skills; discover_all_skills()"` (with default path)
  - macOS/Linux: `CLAUDE_SKILLS_DIR=/tmp/test python -c "from src.skill_guard import discover_all_skills; discover_all_skills()"`
- - Cross-platform: `pytest tests/ -v -k "test_discover_with_env_override or test_path_resolution"`
- **Acceptance**: Path resolution works on all platforms with environment variable override
- **Verification**: Run above commands on Windows, macOS, Linux

### Step 5: Execute Brownfield Conversion (Priority: CRITICAL)

**Task 5.1**: Run /package brownfield conversion
- **Command**: `/package P:/packages/skill-guard`
- **Action**: Confirm conversion when prompted
- **Acceptance**: Backup created, `src/` → `core/` migration complete
- **Verification**: Check `core/` directory exists

**Task 5.2**: Verify plugin structure
- **Files**: `.claude-plugin/plugin.json`, `hooks/hooks.json`, `README.md`
- **Acceptance**: All plugin files created
- **Verification**: `ls -la P:/packages/skill-guard/`

**Task 5.3**: Test imports from core/
- **Command**: `python -c "from core.skill_auto_discovery import discover_all_skills"`
- **Acceptance**: Import works without errors
- **Verification**: Test in Python REPL

**Task 5.4**: Run post-conversion tests
- **Command**: `pytest P:/packages/skill-guard/tests/ -v`
- **Acceptance**: All tests pass with new structure
- **Verification**: Review test output

**Task 5.5**: Create compatibility shim for existing hooks
- **File**: `P:/packages/skill-guard/src/skill_guard/__init__.py` (NEW after conversion)
- **Content**:
  ```python
  """
  Compatibility shim for v1.0 → v2.0 plugin migration.

  Allows existing hooks using `from skill_guard import ...` to continue working
  after conversion to plugin structure.

  Deprecated: Import from `core` directly instead.
  """

  import warnings
  warnings.warn(
      "Importing from skill_guard is deprecated. Use 'from core.skill_auto_discovery import ...' instead.",
      DeprecationWarning,
      stacklevel=2
  )

  # Redirect to core module
  from core.skill_auto_discovery import (
      KNOWLEDGE_SKILLS,
      discover_all_skills,
      get_skill_config,
  )

  __all__ = [
      "KNOWLEDGE_SKILLS",
      "discover_all_skills",
      "get_skill_config",
  ]
  ```
- **Acceptance**: Old import path works, deprecation warning shown
- **Verification**: Test `python -c "from skill_guard import discover_all_skills"` shows warning but works

### Step 6: Update Documentation (Priority: MEDIUM)

**Task 6.1**: Update skill-guard README
- **File**: `P:/packages/skill-guard/README.md`
- **Sections**: Installation, Usage
- **Change**: Replace pip install with plugin installation
- **Acceptance**: README describes plugin installation
- **Verification**: Read README, check accuracy

**Task 6.2**: Create CHANGELOG.md
- **File**: `P:/packages/skill-guard/CHANGELOG.md` (NEW)
- **Content**: Migration from library to plugin
- **Acceptance**: Documents all changes and breaking changes
- **Verification**: Review CHANGELOG

**Task 6.3**: Add migration notice to README
- **File**: `P:/packages/skill-guard/README.md`
- **Section**: Migration Notice (new section at top)
- **Content**: Explain v1.0 → v2.0 plugin migration
- **Acceptance**: Clear migration path for existing users
- **Verification**: README has migration section

---

## 7. Risks, Success Criteria, Dependencies

### Risks

**Risk 1: Breaking Existing Hook Imports**
- **Severity**: HIGH
- **Impact**: Hooks using `from skill_guard import ...` will break after `src/` → `core/` migration
- **Mitigation**: Document breaking change in CHANGELOG, provide migration guide
- **Contingency**: Create compatibility shim in old location

**Risk 2: Test Failures After Conversion**
- **Severity**: MEDIUM
- **Impact**: Tests may reference `src/skill_guard` paths
- **Mitigation**: Update all test imports before conversion
- **Contingency**: Fix tests post-conversion before declaring success

**Risk 3: pyyaml Not Available in Plugin Environment**
- **Severity**: LOW
- **Impact**: Plugin can't use pyyaml if not available
- **Mitigation**: Verify pyyaml is available or add to dependencies
- **Contingency**: Fall back to regex if pyyaml unavailable

**Risk 4: Environment Variable Not Set in Hook Context**
- **Severity**: MEDIUM
- **Impact**: `CLAUDE_SKILLS_DIR` may not be set when hooks run
- **Mitigation**: Provide sensible default (`~/.claude/skills`)
- **Contingency**: Document required environment variables

### Success Criteria

1. **All Critical Issues Fixed**: Hardcoded paths, regex parsing, silent failures resolved
2. **Test Coverage >= 80%**: Unit and integration tests cover edge cases
3. **Plugin Structure Valid**: `.claude-plugin/`, `core/`, `hooks/` all present
4. **Imports Work**: `from core.skill_auto_discovery import ...` succeeds
5. **Tests Pass**: Full test suite passes with new structure
6. **Documentation Complete**: README updated, CHANGELOG created, brownfield guide added to /package
7. **Portable**: Works on Windows, macOS, Linux without hardcoded paths

### Dependencies

**Internal Dependencies**:
- `/package` skill must support brownfield conversion (PHASE 1.5)
- Test fixtures must exist for skill directories

**External Dependencies**:
- `pyyaml` must be available (already in pyproject.toml)
- Python >= 3.10 (already specified)

**Blocked By**:
- None (can proceed immediately)

**Blocking**:
- skill-guard plugin conversion (cannot convert until fixes applied)
- /package brownfield documentation (needed for user guidance)

---

## Next Actions

This plan will be executed in the following order:

1. **Implement skill-guard fixes** (Steps 1-2): Fix all 5 critical issues and expand test coverage

2. **Update /package skill** (Step 3): Add brownfield next steps documentation and update PHASE 1.6

3. **Validate and convert** (Steps 4-6): Run validation, execute brownfield conversion, update documentation

**To proceed**: Run `/plan-workflow flow P:/.claude/hooks/plans/plan-20250307-skillguard-fixes.md` to create detailed task breakdown

**After task breakdown**: Execute tasks sequentially, running `/plan-workflow review` after each step to validate completion
