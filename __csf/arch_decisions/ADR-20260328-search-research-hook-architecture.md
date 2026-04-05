# ADR-20260328: Search-Research Hook Architecture

**Date**: 2026-03-28
**Status**: Accepted
**Source**: Investigation following ADR-20260327 question-relevance gate implementation

---

## Context

After implementing the question-relevance gate (ADR-20260327), a question arose about whether that gate belonged in `packages/search-research/hooks/` instead of `P:/.claude/hooks/`. This led to a root-cause investigation of how hooks are actually loaded in this codebase.

Two hook loading mechanisms exist:

1. **`@register_hook` + `core_hook_modules`** (active): Hooks in `P:/.claude/hooks/` are registered via the `@register_hook` decorator and enumerated in the `core_hook_modules` list in `UserPromptSubmit_modules/registry.py`. This is the **authoritative** loading mechanism.

2. **`hooks.json` manifest** (unused scaffolding): Each package may have a `hooks/hooks.json` file with event handler configuration. This follows the Claude Code plugin structure pattern. However, **the registry never reads `hooks.json`** — it was created as scaffolding but never wired up.

The `packages/search-research/hooks/hooks.json` file contains all empty arrays:
```json
{
  "PreToolUse": [],
  "PostToolUse": [],
  "SessionStart": [],
  "PreCompact": [],
  "UserPromptSubmit": [],
  "ToolResponseReceived": []
}
```

---

## Decision

**There are no hooks to migrate to `packages/search-research/hooks/` at this time.**

The investigation confirmed:

1. **Question-relevance gate is CSF infrastructure**, not a search-research package hook. It enforces a constitutional rule (responses must address the user's stated question focus) and correctly lives in `.claude/hooks/` alongside other CSF enforcement hooks.

2. **No hooks in `.claude/hooks/` are package-derived** from `search-research`. The grep hits for `search.research|unified_router|quality_checker|mcp_server` were all false positives:
   - `tool_availability_checker.py` — has a generic `_check_mcp_server_available()` function, unrelated to `search-research`'s `mcp_server.py`
   - The other two hits are test files

3. **`packages/search-research/hooks/` has no Python hook files** — only the empty `hooks.json` scaffolding

---

## Implications

### For `hooks.json`

The `hooks.json` scaffolding should be maintained as the **future registration point** for any package-derived hooks that belong to `search-research`. When/if such hooks are created:

1. Place Python hook files in `packages/search-research/hooks/`
2. Register them in `packages/search-research/hooks/hooks.json`
3. Do **not** add them to `core_hook_modules` in `registry.py`

### For Question-Relevance Gate (ADR-20260327)

The Layer 1 implementation (word-boundary regex on `constraint_noun`) is complete and verified (11/11 tests pass). The gate is correctly located at `P:/.claude/hooks/UserPromptSubmit_modules/user_directive_obligation.py` and `P:/.claude/hooks/stop/StopHook_directive_obligation.py`.

---

## Options Considered

### Option A: Do Nothing (Selected)

Keep current architecture. `hooks.json` remains empty scaffolding. When package hooks are needed, they can be properly registered.

**Pros**: No changes needed, no migration risk
**Cons**: `hooks.json` remains unused

### Option B: Wire Up `hooks.json`

Modify `registry.py` to also read `hooks.json` from packages and load those hooks.

**Pros**: `hooks.json` becomes functional, follows plugin pattern
**Cons**: Adds complexity, maintenance burden, risk of breaking existing hook loading

### Option C: Deprecate `hooks.json`

Remove `hooks.json` and document that all hooks use `@register_hook` + `core_hook_modules`.

**Pros**: Removes dead scaffolding
**Cons**: Loses plugin-structure compatibility if packages are ever distributed as plugins

---

## Verification

```bash
# Confirm no search-research hooks in .claude/hooks/
grep -r "search.research\|unified_router\|quality_checker" P:/.claude/hooks/**/*.py

# Confirm hooks.json is empty
cat packages/search-research/hooks/hooks.json

# Confirm no Python hook files in search-research hooks/
ls packages/search-research/hooks/
```

All checks confirm: zero hooks to migrate.

---

## Future Work: Operationalization Options

Topic-alignment checking belongs in `search-research` as a result-quality gate, not as CSF hooks checking LLM prose. Academic framing: **"answer plausibility"** (PlausibleQA, arxiv 2403.06326). The question-relevance gate was an early attempt at this concept but operated at the wrong abstraction level.

### Layer 1 — Word-Boundary Regex on `constraint_noun`
- **What**: Detect presence of question's constraint noun in LLM response text using word-boundary regex
- **Status**: Implemented and removed (ADR-20260327)
- **Verdict**: **Rejected** — wrong abstraction level (checks LLM prose, not search result content)
- **Rationale**: LLMs can produce topic-inappropriate responses without the regex failing; the check caught absence of a word in prose, not absence of topic alignment in results

### Layer 2 — TF-IDF Cosine Similarity (Question Focus vs Answer)
- **What**: Vectorize question focus terms and answer text; compute cosine similarity as plausibility score
- **Complexity**: Medium
- **Pros**: Fast, interpretable, no external API calls, works with stdlib (`sklearn` or manual TF-IDF)
- **Cons**: Surface-level lexical overlap; misses semantic drift (same topic, wrong angle)
- **Solo-dev suitability**: **High** — pip-installable, local-only, controllable
- **Hook placement**: Would live in `search-research` as a result-quality filter, not CSF hooks

### Layer 3 — Embedding Similarity via Sentence-Transformers
- **What**: Encode question and answer into dense vectors; compute cosine similarity as plausibility score
- **Complexity**: High (model download, GPU optional but recommended, runtime overhead)
- **Pros**: Semantic understanding catches topical drift that TF-IDF misses
- **Cons**: External model dependency, latency per query, memory footprint, startup cost
- **Solo-dev suitability**: **Medium** — feasible if GPU available; CPU fallback is slow
- **Hook placement**: Would live in `search-research` as a result-quality filter

### Recommended Direction for Solo-Dev Environment

**Pursue Layer 2 (TF-IDF) first**, with Layer 3 as a future optional enhancement if Layer 2 proves insufficient.

Rationale:
1. **No external API calls** — satisfies constitutional hook constraints if placed in `search-research`
2. **Local-only** — no GPU required, no model serving
3. **Interpretable** — similarity score is human-readable
4. **Incremental** — Layer 2 is a natural extension of Layer 1's intent with actual semantic grounding
5. **Test corpus available** — real user queries from session history can build the test set

Layer 3 (embeddings) can be revisited if TF-IDF cosine similarity produces too many false positives/negatives in practice.

---

## Related Decisions

- **ADR-20260327**: Question-relevance gate Layer 1 implementation (word-boundary regex)
- **ADR-20260328-search-quality-improvements**: Search quality bug fixes (8 changes, all implemented)

---

## Status Update: 2026-03-28 (Removal Executed)

The question-relevance gate hooks have been **removed** from `.claude/hooks/` on 2026-03-28.

**Rationale**: The hooks checked whether AI prose contained `constraint_noun`, not whether search results actually addressed the query's stated focus. The abstraction level was wrong — checking LLM text rather than result content. User confirmed LLMs do sometimes produce topic-inappropriate responses without the hooks blocking them.

**Removed files**:
- `UserPromptSubmit_modules/user_directive_obligation.py`
- `stop/StopHook_directive_obligation.py`
- `test_question_relevance.py`
- `UserPromptSubmit_modules/tests/test_user_directive_obligation.py`
- `stop/tests/test_stopHook_directive_obligation.py`

**Deregistrations**:
- `registry.py:616`: Removed `"user_directive_obligation"` from `core_hook_modules`
- `Stop_router.py:155-160`: Removed `StopHook_directive_obligation` tuple from `HOOK_SEQUENCE`
- `Stop_router.py:215`: Removed from `STOP_HOOKS` list

**Future direction**: Topic-alignment checking belongs in `search-research` as a result-quality gate (checking result content against query focus), not as CSF hooks checking LLM prose. Academic framing: "answer plausibility" (PlausibleQA, arxiv 2403.06326).
