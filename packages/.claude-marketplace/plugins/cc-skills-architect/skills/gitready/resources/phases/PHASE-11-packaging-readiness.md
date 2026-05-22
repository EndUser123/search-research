# PHASE 11: Packaging Readiness (5min)

**Objective**: Validate plugin is ready for distribution as a standalone package.

**Trigger**: `--check-packaging` flag OR when packaging validation is requested.

---

## Step 1: Manifest Completeness

Validates `plugin.json` has required fields.

```python
import json
from pathlib import Path

def check_manifest(target_dir: Path) -> tuple[bool, list[str]]:
    """Check plugin.json exists and has required fields."""
    errors = []
    manifest = target_dir / ".claude-plugin" / "plugin.json"

    if not manifest.exists():
        errors.append("Missing .claude-plugin/plugin.json")
        return False, errors

    try:
        data = json.load(open(manifest, encoding="utf-8"))
    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON in plugin.json: {e}")
        return False, errors

    if "name" not in data:
        errors.append("plugin.json missing required 'name' field")

    if not errors:
        return True, []
    return False, errors
```

**Minimal passing manifest**:
```json
{ "name": "plugin-name" }
```

**Recommended complete manifest**:
```json
{
  "name": "plugin-name",
  "version": "1.0.0",
  "description": "What this plugin does",
  "author": { "name": "Your Name" }
}
```

---

## Step 2: Path Portability Scan

Scans all Python files for hardcoded paths. Uses `${CLAUDE_PLUGIN_ROOT}` portability.

```python
import re
from pathlib import Path

HARDCODE_PATTERNS = [
    r'P:\\\\+',      # P:\\ or P:\\\\\
    r'P:',           # P: (in some contexts)
    r'C:\\\\+',      # C:\\ or higher
    r'/Users/',      # macOS home
    r'/home/',       # Linux home
    r'~'             # home shortcut
]

def check_paths(target_dir: Path) -> tuple[bool, list[str]]:
    """Check all Python files for hardcoded paths."""
    errors = []
    py_files = list(target_dir.rglob("*.py"))
    py_files = [f for f in py_files if "__pycache__" not in str(f)]

    for py_file in py_files:
        try:
            content = py_file.read_text(encoding="utf-8")
            for pat in HARDCODE_PATTERNS:
                matches = re.findall(pat, content)
                if matches:
                    # Filter out false positives (e.g., string formatting)
                    for m in matches:
                        errors.append(f"{py_file.relative_to(target_dir)}: hardcoded path '{m}'")
        except Exception:
            pass

    # Remove duplicates while preserving order
    seen = set()
    unique = []
    for e in errors:
        if e not in seen:
            seen.add(e)
            unique.append(e)

    return len(unique) == 0, unique
```

**Fix**: Replace hardcoded paths with `${CLAUDE_PLUGIN_ROOT}`:
```python
# WRONG
path = "P:\\packages\my-plugin\scripts"

# CORRECT
path = "${CLAUDE_PLUGIN_ROOT}/scripts"
```

---

## Step 3: Bundle Contents

Validates bundle excludes forbidden files.

```python
EXCLUDED_PATTERNS = [
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "__pycache__",
    "*.pyc",
    "*.pyo",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    ".git",
    "dist",
    "build",
    "*.egg-info",
    ".env",
    "*.log",
    ".coverage",
    "coverage.json",
    "*.backup",
    "*.old",
    "*.bak"
]

ALWAYS_REQUIRED = [
    ".claude-plugin/plugin.json",
    "README.md",
    "LICENSE"
]

def check_bundle(target_dir: Path) -> tuple[bool, list[str]]:
    """Check bundle contents and exclusions."""
    errors = []

    # Check required files exist
    for required in ALWAYS_REQUIRED:
        if not (target_dir / required).exists():
            errors.append(f"Missing required bundle file: {required}")

    # Check excluded files do not exist
    for py_file in target_dir.rglob("*.py"):
        if "__pycache__" not in str(py_file):
            continue
        errors.append(f"Found excluded file: {py_file.relative_to(target_dir)}")

    # Check for pyproject.toml (plugins should not have it)
    if (target_dir / "pyproject.toml").exists():
        errors.append("Found pyproject.toml — plugins should use .claude-plugin/, not pip packaging")

    # Check for core/ (non-standard)
    if (target_dir / "core").exists():
        errors.append("Found core/ directory — should be scripts/ (see PLUGIN_STANDARDS.md)")

    return len(errors) == 0, errors
```

---

## Step 4: Smoke Test

Runs plugin validation script if present.

```python
import subprocess
import sys
from pathlib import Path

def smoke_test(target_dir: Path) -> tuple[bool, list[str]]:
    """Run smoke test on plugin bundle."""
    errors = []
    script = target_dir / "scripts" / "validate_plugin_bundle.py"

    if script.exists():
        result = subprocess.run(
            [sys.executable, str(script), "--smoke-test", str(target_dir)],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            errors.append(f"Smoke test failed: {result.stderr}")
            return False, errors
    else:
        # Fallback: basic import check
        scripts_dir = target_dir / "scripts"
        if scripts_dir.exists():
            init_py = scripts_dir / "__init__.py"
            if init_py.exists():
                try:
                    import py_compile
                    py_compile.compile(str(init_py), doraise=True)
                except py_compile.PyCompileError as e:
                    errors.append(f"Import test failed: {e}")
                    return False, errors

    return len(errors) == 0, errors
```

---

## Output: PACKAGING_READINESS_REPORT.md

```markdown
# Packaging Readiness Report

**Target**: `{{TARGET_DIR}}`
**Date**: {{TIMESTAMP}}
**Result**: {{PASS/FAIL}}

## Manifest Completeness

{{PASS/FAIL}} - {{errors or "All required fields present"}}

## Path Portability

{{PASS/FAIL}} - {{errors or "No hardcoded paths found"}}

## Bundle Contents

{{PASS/FAIL}} - {{errors or "All required files present, no excluded files"}}

## Smoke Test

{{PASS/FAIL}} - {{errors or "Smoke test passed"}}

## Summary

| Check | Status |
|-------|--------|
| Manifest | {{PASS/FAIL}} |
| Paths | {{PASS/FAIL}} |
| Bundle | {{PASS/FAIL}} |
| Smoke | {{PASS/FAIL}} |

**Overall**: {{PASS/FAIL}}
```

---

## Track Completion

```bash
python resources/phases/track_phases.py {{TARGET_DIR}} --write 11
```

---

## Integration

- **PHASE 1.7**: Path portability scan complements PHASE 1.7 plugin standards validation
- **PHASE 2.5**: Hook-system-to-plugin conversion should run before PHASE 11
- **Reference**: `references/packaging-checklist.md` — full bundle validation checklist

---

## See Also

- `scripts/validate_plugin_bundle.py` — standalone CI-usable validation script
- `references/packaging-checklist.md` — detailed packaging checklist
- `resources/PLUGIN_STANDARDS.md` — authoritative plugin structure reference