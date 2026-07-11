---
name: simplify-enhanced
description: Wrapper around the built-in /simplify that adds a false-positive-resistant code-reuse pass. Invokes the built-in first (reuse + simplification + efficiency + altitude + apply), then runs a discrimination-scale duplicate detector the built-in cannot guarantee.
version: 3.0.0
status: stable
category: quality
enforcement: advisory
triggers:
  - /simplify-enhanced
workflow_steps:
  - builtin_simplify
  - enhanced_reuse_pass
  - apply
---

# simplify-enhanced

Thin wrapper over the harness-native `/simplify`. Delegates the bulk review to the
built-in and adds **one** thing it cannot guarantee: a reuse pass engineered to suppress
the false-positive "duplicate code" flags that naive (grep-driven) reuse review produces.

## Phase 1: Delegate to the built-in

Invoke the built-in `/simplify` (Skill tool, name `simplify`). Let it run to completion —
it reviews the changed code for reuse, simplification, efficiency, and altitude cleanups,
and applies its own fixes. Do not duplicate that work here.

If the built-in is unavailable or errors, fall back to reviewing `git diff` (or
`git diff HEAD`) manually for the same four dimensions; do not abort.

## Phase 2: Enhanced reuse pass (the only thing this skill adds)

After the built-in finishes, run ONE additional reuse-duplicate pass over the diff using
the discrimination scale below. The built-in's reuse review is keyword/semantic similarity;
this pass exists to stop the false positives that similarity produces.

**CRITICAL: semantic analysis, not keyword grep.** For each change:

1. **Classify the pattern type** before searching:
   - **DEFINING** a function/variable (behavior is born here) → cross-file search for duplicates
   - **USING** a function/variable → check whether an existing utility already covers it (correct usage, not a duplicate)
   - **MENTION** (reference, import, type hint) → not a duplicate candidate; skip

2. **Cross-file duplicate detection only** (not same-file):
   - Flag only where the SAME PATTERN is actually **defined** in multiple places.
   - Do NOT flag: imports, test usage of production code, wrapper functions calling a shared utility, legitimate cross-references.

3. **Evidence verification before reporting:**
   - Before reporting "N files define this," count actual **definitions** by reading the code — not grep hit count.
   - Keyword matches ≠ definitions. If grep finds N matches but only M are definitions (M < N), report M.

**Discrimination scale:**

| Type | Meaning | Action |
|------|---------|--------|
| DEFINES | Another file also defines this same pattern | Flag as duplicate |
| MENTIONS | References the pattern without defining it | Skip |
| USES_IN_CONTEXT | Calls an existing utility | Skip (correct usage) |
| TEST_USAGE | Test file exercises production code | Skip |
| CROSS_FAMILY | Hook uses a skill utility (or similar cross-boundary) | Skip (legitimate) |

**Verification checklist before reporting any duplicate:**
- [ ] Read the actual code in matched files (don't trust grep output alone)
- [ ] Count only DEFINITIONS, not mentions/usages
- [ ] Distinguish same-family vs cross-family usage
- [ ] Report "M definitions across N files," never "N keyword matches"

## Phase 3: Apply

Apply only the confirmed duplicates from Phase 2 (consolidate into the shared utility).
Skip false positives without arguing — note them and move on. Do not re-review the
dimensions the built-in already covered.

Summarize what Phase 2 added on top of the built-in (or confirm the reuse was already clean).
