# Code Review Report — doc-compiler Pipeline

**Target:** `P:/packages/.claude-marketplace/plugins/cc-skills-meta/skills/doc-compiler/`
**Date:** 2026-05-03
**Session:** 9cc5a8a4

## Summary

The doc-compiler pipeline has significant logic bugs that render core features non-functional, plus security, I/O, and performance issues. Two critical logic bugs — a broken CSS overlay and a hardcoded artifact path — need immediate attention. The HTML injection gap (SEC-004) is the most user-visible security risk.

**Health Score: 58%**
Calculated as: `100 - (CRITICAL×20 + HIGH×10 + MEDIUM×5 + LOW×2)`, capped at 0-100.

| Severity | Count |
|----------|-------|
| CRITICAL | 1 |
| HIGH | 7 |
| MEDIUM | 6 |
| LOW | 5 |

---

## Critical Issues

### 1. [CRITICAL] Style CSS overlay never loads — style-aware presentation broken

**File:** `stage_e3_assembler.py:72`
**Agent:** adversarial-logic

```python
# Style-specific CSS overlay (adds on top of shared)
if style and style in STYLE_CSS_MAP:
    for name in STYLE_CSS_MAP[style]:
        content, src = read_optional(name, style=None)  # BUG: style=None
```
`read_optional(name, style=None)` always reads the shared path, never the style-specific override. The entire CSS overlay mechanism is non-functional — `deepwiki.css`, `product.css`, `minimal.css` are never loaded when `style=style` is passed.

**Impact:** Style differences (font scale, card padding, decorative whitespace) never appear in output HTML despite being configured in presets and declared in `artifact-plan.json`.
**Fix:** Change `read_optional(name, style=None)` → `read_optional(name, style=style)` on lines 72 and 92.

**Falsification condition:** This is wrong if `read_optional` with `style=style` successfully finds a style-specific file. Verified by code inspection — the function checks `STYLES_DIR / style / name` when style is provided.

---

## High Priority

### 2. [HIGH] HTML injection in `fill_route_outs` — XSS risk

**File:** `stage_e2_binder.py:105`
**Agent:** adversarial-security

`target` and `description` inserted into HTML without `html.escape()`. If a source model contains `<script>` in a route-out target, it renders directly.

```python
items_html += f"<h4>{target}</h4>"  # no escaping
items_html += f"<p>{description}</p>"  # no escaping
```

`fill_steps` escapes `&,<,>` but `fill_route_outs` does not.

### 3. [HIGH] Hardcoded Windows artifact path with literal `{name}`

**File:** `stage_e2_binder.py:139`
**Agent:** adversarial-logic

```python
"index_path": f"P:/.claude/skills/{name}/index.html" if kind == "skill"
```

For `kind=skill`, the path is correct. For other kinds, the path contains literal `{name}` braces because the f-string uses single braces instead of double `{{}}`. However — the conditional `if kind == "skill"` hides this for skill-type sources but exposes it for non-skill types.

### 4. [HIGH] Duplicate `fill_proof_summary` definitions

**File:** `stage_e2_binder.py:132 and 147`
**Agent:** adversarial-logic

Two identical no-op definitions of `fill_proof_summary`. Python uses the second (line 147), but both are no-ops — the function intended to fill proof content does nothing.

### 5. [HIGH] `load_json` silently returns `{}` for missing files

**File:** `runtime/stage_c_diagram_strategy_router.py:34-37`, `runtime/stage_d_guide_loader.py:18-21`
**Agent:** adversarial-io-validation

When prerequisites aren't met, stages fail silently and continue with empty data rather than surfacing the error at the correct stage.

### 6. [HIGH] `extract_guide_sections` crashes on terminal heading with no body

**File:** `runtime/stage_d_guide_loader.py:29-31`
**Agent:** adversarial-logic

`parts[i+1]` accessed without bounds check causes `IndexError` when the last heading in a guide has no body text.

### 7. [HIGH] Sequential subprocess calls dominate runtime (~18s overhead)

**File:** `runtime/orchestrator.py:69-76`
**Agent:** adversarial-performance

12 stages × ~1.5s subprocess startup overhead = 18s baseline before actual work begins. For a pipeline meant to run on every skill documentation generation, this is severe.

### 8. [HIGH] Browser stage has 2-3s hard-coded sleep

**File:** `runtime/stage_j_runtime_validator.py:46`
**Agent:** adversarial-performance

`time.sleep(2)` + `time.sleep(0.5)` = ~7s sleep for 2 browser validator stages.

---

## Medium Priority

### 9. [MEDIUM] `generate_state` crashes on empty steps list

**File:** `runtime/stage_e_diagram_generator.py:151`
**Agent:** adversarial-logic

`step_names[-1]` accessed without checking if list is empty → `IndexError` for zero-step workflows.

### 10. [MEDIUM] `generate_sequence` misses non-adjacent actor interactions

**File:** `runtime/stage_e_diagram_generator.py:117-119`
**Agent:** adversarial-logic

Uses `zip(a, b)` which only captures adjacent pairs. With actors [A,B,C], only A→B and B→C shown, not A→C.

### 11. [MEDIUM] TOC item count inflated by counting all `href=#` in HTML

**File:** `runtime/stage_g_artifact_proof.py:226`, `runtime/stage_j_runtime_validator.py:261`
**Agent:** adversarial-logic

Counts all `href=#` anchors in entire HTML, not just those inside `nav#toc`. JS arrays or CSS examples inflate the count.

### 12. [MEDIUM] Template utility scripts use unsafe path construction

**File:** `templates/extract_templates.py:9,61-291`, `templates/rebuild_index.py:9,103`
**Agent:** adversarial-io-validation

No `pathlib.Path`, no existence checks before `open()`. Scripts fail with unhelpful errors if paths are wrong.

### 13. [MEDIUM] Stage C reads SOURCE at module import time without check

**File:** `stage_c_mermaid_design.py:14`
**Agent:** adversarial-io-validation

```python
model = json.loads(SOURCE.read_text(encoding="utf-8"))  # runs on import
```
If `source-model.json` doesn't exist, error is `JSONDecodeError` instead of a clear message.

### 14. [MEDIUM] `_pv()` doesn't sanitize CSS values from presets.ini

**File:** `stage_b_artifact_plan_builder.py:93`
**Agent:** adversarial-security

Values from `presets.ini` embedded into CSS without validating they contain only CSS-safe characters.

---

## Low Priority

### 15. [LOW] Hardcoded Windows `P:` path in `stage_e2_binder.py`

**File:** `stage_e2_binder.py:139`
**Agent:** adversarial-security

### 16. [LOW] `yaml` import inside function

**File:** `runtime/stage_a_source_extractor.py:35`
**Agent:** adversarial-performance

### 17. [LOW] `toc_items` counting imprecise

**File:** `runtime/stage_g_artifact_proof.py:226`
**Agent:** adversarial-logic

### 18. [LOW] `facts.html` may render with unfilled placeholders

**File:** `runtime/stage_b_doc_model_builder.py:89-91`
**Agent:** adversarial-logic

`enforcement` and `status` listed in `data_keys` but never added to `content_bindings`.

### 19. [LOW] Stage J browser harness has no retry on transient failure

**File:** `runtime/stage_j_runtime_validator.py:155-162`
**Agent:** adversarial-io-validation

---

## Recommendations

**Immediate (fix before next run):**
1. Fix `stage_e3_assembler.py:72,92` — `read_optional(name, style=None)` → `read_optional(name, style=style)` (makes style CSS functional)
2. Fix `stage_e2_binder.py` — add `html.escape()` to `fill_route_outs()` (closes XSS gap)
3. Remove duplicate `fill_proof_summary` at line 132

**Soon:**
4. Add bounds check to `extract_guide_sections` (`if i+1 < len(parts)`)
5. Add `html.escape()` for `name`/`description` in artifact path construction
6. Add existence check to `load_json()` variants or use `FileNotFoundError`
7. Add guard to `generate_state` for empty steps list

**When time permits:**
8. Replace subprocess calls in orchestrator with direct module calls
9. Reduce hard-coded sleep times in stage_j
10. Replace `f-string` paths with `pathlib.Path` in utility scripts

---

## Files Reviewed

- `stage_a_source_extractor.py`
- `stage_b_artifact_plan_builder.py`
- `stage_c_mermaid_design.py`
- `stage_d_mermaid_critic_review.py`
- `stage_e1_loader.py`
- `stage_e2_binder.py`
- `stage_e3_assembler.py`
- `stage_f_static_validator.py`
- `runtime/stage_c_diagram_strategy_router.py`
- `runtime/stage_d_guide_loader.py`
- `runtime/stage_e_diagram_generator.py`
- `runtime/stage_g_artifact_proof.py`
- `runtime/stage_j_runtime_validator.py`
- `templates/extract_templates.py`
- `templates/rebuild_index.py`
- `templates/base-shell.html`
