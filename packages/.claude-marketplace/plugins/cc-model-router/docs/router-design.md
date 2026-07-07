# Model Router Design Note

## Routing pipeline

```
UserPromptSubmit
    │
    ▼
classify.py (Python subprocess)
    ├─ Stage 0: Deterministic overrides (git/build commands → background;
    │           short mechanical edits → local-coding via NON_TRIVIALITY_EXCLUSIONS)
    ├─ TF-IDF semantic scoring → {background, coding, reasoning} cosine scores
    ├─ Stage A: background wins head-to-head (margin > threshold) → background
    ├─ Stage B: reasoning vs coding head-to-head → reasoning or coding
    ├─ Stage C: coding subtype (≤15 words + mechanical verb + not excluded) → local-coding
    └─ writes ccr-routing-hint.json (taskType, confidence, top_2, margin, lowConfidence)

ccr-custom-router.js (per-request in CCR process)
    ├─ Pin override → route to pinned model, skip semantic logic
    ├─ Read hint + local-model-state + config.tokenBudgets
    ├─ Background hint → fall through to CCR Router.background
    ├─ Reasoning hint → GLM-5.2 (with token-budget check: if tokenCount > budget → M3 fallback)
    ├─ Coding hint → local-first (aggressive) or M3-first (conservative)
    └─ returns route string to CCR default Router (which picks the provider)
```

## How doc-search vs plan-evaluation routes

| Prompt pattern | Stage A | Stage B | Final | Route |
|---|---|---|---|---|
| "find the refactoring plan in Downloads" | active-work | coding | coding | M3 (or local) |
| "analyze the architecture and tradeoffs" | active-work | reasoning | reasoning | GLM-5.2 |
| "git commit and push" | — | — | background (override) | Router.background |
| "ok" | — | — | local-coding (override) | local/llama |
| "Given the architecture tradeoffs, does that make sense?" | active-work | reasoning | reasoning | GLM-5.2 |

Doc-search prompts with paths (`C:\...`, `P:\...`), file-lookup verbs ("find", "look for"), or info-gathering language ("I think we have docs on...") score higher in coding exemplars (which include `look for the refactoring plan in the Downloads folder and list the files`). Architecture/tradeoff prompts score higher in reasoning exemplars. The TF-IDF marginal difference between the classes determines the outcome.

## Token budgets as context management, not content control

Token budgets are treated as a constraint, not a gating decision. The router does not truncate or block large requests — it routes them to a model that can handle them. The key facts:

- `req.tokenCount` is precomputed by CCR (from `tokenizerService.countTokens({messages, system, tools})`) and attached to the request object before the custom router runs.
- The router compares `tokenCount` against `config.tokenBudgets[route]` — a per-model ceiling.
- If `tokenCount > budget`, the request is routed to a safer model (e.g., M3 for coding) and the `ccr-route-state.json` records `token-budget` as the reason.
- No large-request rejection occurs: the budget check is a *steering* mechanism, not a gate.
- Configuration fields: `config.tokenBudgets.{route}` for per-model limits, `config.tokenBudgets.defaultFallback` for unspecified routes. Both in tokens.

## Context window management

Context is treated as a budget, not "append everything":

- For local models: `maxContextTokens` comes from `local-model-state.json`, which is populated by `run-ornith-server.ps1` parsing the llama-server stdout log for `n_ctx_slot` (the effective runtime value, not just the `-c` flag).
- For cloud models: `tokenBudgets` in `config.json` provides ceilings.
- The routing margin-based logic does NOT check token budgets — only the reasoning path has an explicit budget check (overflows from reasoning → M3, never blocking the request).
- A prompt exceeding `maxContextTokens` in aggressive mode triggers escalation to M3 without losing the request.

## Upgrade path (TF-IDF → persistent semantic)

The `SemanticScorer` abstraction isolates the scoring backend from the pipeline. To swap:

1. Create `__lib/classifier/embedding_backend.py` implementing `SemanticScorer.score()`.
2. Change `classifier.backend` from `"tfidf"` to `"embedding-daemon"` in `claude-model-router.json`.
3. Pipeline, observability, hint schema, evaluation harness are unchanged.
4. The embedding backend would call a local HTTP endpoint (e.g., the existing semantic daemon) instead of computing TF-IDF in-process.

## Known limitations (honest)

- TF-IDF cosine scores are low-magnitude (~0.00–0.38); thresholds are margin-based, not absolute-score-gated.
- The 60-word `opus_word_count` threshold (200) is the old regex classifier's logic and is no longer used by the margin-based pipeline — it remains only for backward compat in the config schema.
- Token-budget values are approximate — they use CCR's tokenizer count, not the local model's tokenizer. For English+code workloads, the difference is ~10-15%; the safety margin absorbs it.
