# Implementation Plan - /analyze Consolidation

## Phase 1: Decomposition ✅ COMPLETE

**Completed**: 2025-01-01 01:00

All 5 shared library modules created and verified:
- `context.py` - 311 lines
- `files.py` - 267 lines
- `constitution.py` - 355 lines
- `llm.py` - 250 lines
- `prompts.py` - 480 lines

## Phase 2: Refactor analyze_backends.py

**File**: `P:/__csf.nip/src/commands/co/analyze_backends.py` (1179 lines)

### Tasks

1. **Replace context collection**
   - Remove `_collect_context()` method (lines 1058-1118)
   - Import `ContextCollector` from `analyze_lib.context`
   - Use `collect_context()` for all context needs

2. **Replace file collection**
   - Remove `_collect_file_contents()` method (lines 166-245)
   - Import `FileCollector` from `analyze_lib.files`
   - Use `FileCollector.collect()` for file needs

3. **Replace constitution checking**
   - Remove `_load_constitution()` method (lines 790-807)
   - Remove `_check_constitutional_compliance()` method (lines 809-865)
   - Remove `_check_rule_against_file()` method (lines 867-940)
   - Remove `_extract_keywords()` method (lines 942-948)
   - Import `ConstitutionChecker` from `analyze_lib.constitution`
   - Use `ConstitutionChecker.check_files()` for compliance

4. **Replace LLM provider**
   - Remove `_load_provider_config()` method (lines 46-60)
   - Remove `_get_default_provider()` method (lines 63-99)
   - Remove `_create_llm_provider()` method (lines 102-127)
   - Remove `_get_llm_provider()` method (lines 473-477)
   - Import `LLMProvider` from `analyze_lib.llm`
   - Use `LLMProvider.generate()` for LLM calls

5. **Replace prompt building**
   - Remove `_build_analysis_prompt()` method (lines 279-408)
   - Import `PromptBuilder` from `analyze_lib.prompts`
   - Use `PromptBuilder.build_file_analysis_prompt()` for prompts

6. **Update BackendDispatcher**
   - Simplify `__init__` to use shared library
   - Update `_pmgoa_analyze()` to use new APIs
   - Update `_intel_analyze()` if needed
   - Update `_quality_analyze()` if needed

**Expected Reduction**: 1179 → ~400 lines (65% reduction)

## Phase 3: Add Missing Features

### From Intel Command

1. **Framework Detection**
   - Import `get_framework_for_keywords()` from intel
   - Add `--detect-framework` option
   - Auto-detect framework from analyzed files

2. **Strategic Intelligence**
   - Import `generate_strategic_intel()` from intel
   - Add `--strategic` option
   - Generate competitive insights

### Missing Input Sources

1. **Question Mode**
   - Accept question as input (already works)
   - Generate answer based on codebase context

2. **Stdin Mode**
   - Accept input from stdin pipe
   - Useful for chaining commands

3. **Git Ref Mode**
   - Analyze specific commit/ref
   - Compare against current state

### Missing Focus Lenses

Add these lenses from quality gates:
- `testing` - Test coverage and quality
- `documentation` - Doc completeness
- `debt` - Technical debt assessment
- `dependencies` - Dependency analysis
- `apis` - API design review

## Phase 4: Deprecation

1. **Mark `/quality` deprecated**
   - Add deprecation notice
   - Redirect to `/analyze --focus quality`

2. **Mark `/intel` deprecated**
   - Add deprecation notice
   - Redirect to `/analyze --mode council`

3. **Mark `/pmgoa` deprecated**
   - Add deprecation notice
   - Redirect to `/analyze`

## Testing Checklist

- [ ] Quick mode with git diff
- [ ] Standard mode with file target
- [ ] Deep mode with directory
- [ ] Council mode (intel)
- [ ] All focus lenses (risk, gaps, opportunities, quality, security, performance, architecture, cognitive)
- [ ] Constitution integration
- [ ] Session-based scoping
- [ ] JSON output format
- [ ] Interactive (fzf) output format
- [ ] Report output format
- [ ] Checklist output format

## Rollback Plan

If issues arise:
1. Keep original `analyze_backends.py` as `analyze_backends.py.bak`
2. Test thoroughly before removing backup
3. Can revert by restoring backup
