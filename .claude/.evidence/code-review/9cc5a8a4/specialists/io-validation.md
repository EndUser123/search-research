# I/O Validation Review: doc-compiler Pipeline

## Scope
All Python files in `P:/packages/.claude-marketplace/plugins/cc-skills-meta/skills/doc-compiler/`

## Summary
The doc-compiler pipeline has several I/O validation gaps. Most stages use proper pathlib-based file operations with existence checks, but there are notable issues in template utility scripts and external service calls.

---

## Findings

### IO-001: extract_templates.py and rebuild_index.py Use Unsafe Path Construction
**Severity:** HIGH
**Location:** `templates/extract_templates.py:9,61-291` and `templates/rebuild_index.py:9,103`

**Problem:** Both template utility scripts use hardcoded string paths with f-string interpolation instead of `pathlib.Path`. No existence checks before `open()` calls.

**Adversarial Scenario:**
- `extract_templates.py:9` - no existence check before read: `with open(f"{BASE}/index.html", "r")` crashes if BASE/index.html missing
- `rebuild_index.py:103` - no existence check before write: silently overwrites if BASE not writable

**Impact:** If working directory changes or paths are wrong, these scripts fail with unhelpful errors.

**Recommendation:** Replace f-string paths with `pathlib.Path(BASE) / name` and add existence checks.

---

### IO-002: load_json() Silently Returns Empty Dict for Missing Files
**Severity:** MEDIUM
**Location:** `runtime/stage_c_diagram_strategy_router.py:34-37`, `runtime/stage_d_guide_loader.py:18-21`, `runtime/stage_g_artifact_plan_builder.py:22-25`, `runtime/stage_e_diagram_generator.py:26-29`

**Problem:** The pattern `load_json(p)` returns `{}` when file does not exist, masking prerequisite failures.

```python
def load_json(p: Path) -> dict:
    if not p.exists():
        return {}  # Silent failure - caller has no indication file was missing
    return json.loads(p.read_text(encoding="utf-8"))
```

**Adversarial Scenario:** If Stage C runs before Stage B completes, `doc-model.json` is missing. The `load_json` returns `{}`, causing subsequent code to operate on empty data rather than failing fast.

**Impact:** Pipeline continues with corrupted state; error surfaces far from root cause.

**Recommendation:** Add `raise FileNotFoundError(p)` variant or separate `try_load_json()` that indicates failure.

---

### IO-003: stage_c_mermaid_design.py Reads SOURCE at Module Level Without Existence Check
**Severity:** MEDIUM
**Location:** `stage_c_mermaid_design.py:14`

```python
model = json.loads(SOURCE.read_text(encoding="utf-8"))  # runs on import, not in main()
```

**Problem:** File read happens at module import time, not inside `main()`. If `source-model.json` does not exist when the module is imported, the error is a cryptic JSON decode error on an empty string.

**Adversarial Scenario:** User runs `python stage_c_mermaid_design.py` without first running Stage A/B. Script crashes with `json.JSONDecodeError: Expecting value` instead of a clear "source-model.json not found".

**Recommendation:** Move the read inside `main()` after an existence check.

---

### IO-004: stage_d_guide_loader.py Does Not Check GUIDES_DIR Existence
**Severity:** MEDIUM
**Location:** `runtime/stage_d_guide_loader.py:15,75-78`

**Problem:** `GUIDES_DIR` is assumed to exist. If the `references/guides/` directory is missing, the stage silently proceeds with empty guide content, producing diagrams without guide-based critique.

**Impact:** Diagrams bypass quality gates because guides appear empty rather than failing.

**Recommendation:** Add explicit check: `if not GUIDES_DIR.exists(): print(f"ERROR: {GUIDES_DIR} not found"); sys.exit(1)`

---

### IO-005: stage_j_runtime_validator.py No Retry on Browser Harness Failure
**Severity:** LOW
**Location:** `runtime/stage_j_runtime_validator.py:155-162`

**Problem:** Single attempt with 120s timeout. If browser-harness daemon is slow to start or transiently unavailable, the validation fails rather than retrying.

**Impact:** Pipeline fails on transient infrastructure issues.

**Recommendation:** Consider 2-3 retries with exponential backoff for production use.

---

### IO-006: extract_templates.py Reads index.html Without Existence Check
**Severity:** LOW
**Location:** `templates/extract_templates.py:9`

**Problem:** `extract_templates.py` assumes `index.html` exists without checking first. If run on an empty doc-compiler directory, fails with `FileNotFoundError`.

**Recommendation:** Add existence check with descriptive error message.

---

### IO-007: Stage H External Critics Use 600s Timeout Without Retry
**Severity:** LOW
**Location:** `runtime/stage_k_external_critic.py:165`, `stage_h_external_critic.py:57`

**Problem:** Single attempt with long timeout. If claude command hangs or network issues occur, no retry mechanism.

**Impact:** Pipeline halts on single external service hiccup.

---

## I/O Operations Inventory

| Operation | Locations | Risk |
|-----------|-----------|------|
| `Path.read_text()` | Many stages | HIGH if no existence check first |
| `Path.write_text()` | Many stages | LOW - overwrites are intentional |
| `json.loads(p.read_text())` | stage_c_mermaid_design.py:14 | CRITICAL - module-level, no check |
| `open(path, 'r')` | extract_templates.py, rebuild_index.py | HIGH - no existence check |
| `subprocess.run(claude --print)` | stage_d, stage_k, stage_h | MEDIUM - timeout but no retry |
| `subprocess.run(uv run python)` | stage_j | MEDIUM - timeout but no retry |
| `GUIDES_DIR / guide_file` | stage_c:206, stage_d:75 | MEDIUM - derived path |

---

## What Is Done Well

1. **Most stages check file existence before reading:** `orchestrator.py`, `stage_a_source_extractor.py`, `stage_b_artifact_plan_builder.py`, `stage_f_static_validator.py`, `stage_i_emit_proof_metadata.py` all check `if not PATH.exists()` before proceeding.

2. **Proper use of pathlib:** The runtime/ stages consistently use `pathlib.Path` for all file operations.

3. **Descriptive error messages:** When checks fail, error messages clearly indicate which file is missing and which stage should run first.

4. **Timeout on external calls:** All `subprocess.run` calls have timeouts preventing indefinite hangs.

---

## Open Questions

1. **references/guides/ directory structure:** It is unclear if this directory is auto-created or must exist beforehand. If auto-created, which stage does it?

2. **GUIDES_DIR path derivation:** `guide_file` comes from `diagram-guides.json` produced by Stage C. Is there any validation that `guide_file` values are safe (no path traversal) before being used to construct `GUIDES_DIR / guide_file`?

3. **extract_templates.py and rebuild_index.py purpose:** Are these one-time migration scripts or part of ongoing pipeline operation? If latter, they need I/O validation fixes.
