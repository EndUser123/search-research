---
title: "Behavioral detection in AI agent hooks — practitioner approaches and matching logic"
created: 2026-07-28
source: session-019fa48a (/www research on behavioral detection approaches)
tags: [behavioral-detection, hooks, regex, llm-as-judge, guardrails, sycophancy, anti-patterns, stop-hook, practitioner-survey]
host: both
agent: grok
verification: multi-source-verified
cognitive_load: 3
summary: >
  Practitioner survey of how AI coding agent users detect behavioral anti-patterns
  (sycophancy, deferred persistence, fabricated completion) in hook output. The dominant
  production pattern is two-layer: regex signal (fast, ~5% of turns trigger) → LLM-as-judge
  only on hits (high precision). The deployed community standard is pure deterministic bash+jq
  regex (~70 lines). No off-the-shelf guardrail framework covers coding-agent behavioral
  patterns — the realistic upgrade path is regex → two-layer → fine-tuned classifier.
  Our approach (regex + logging) is aligned with community practice and gives us the
  measurement loop most community projects lack.
sources:
  - "waitdeadai/llm-dark-patterns (GitHub)"
  - "waitdeadai/no-sycophancy (GitHub)"
  - "@u1 Japanese X/Twitter viral guide (synthesized via youmind.com)"
  - "fbakkensen quality-gates writeup"
  - "RAGAS answer-relevancy docs"
  - "SemScore (arXiv:2401.17072)"
  - "NVIDIA NeMo Guardrails docs"
  - "Llama Guard 3 model card"
  - "Guardrails AI Hub"
  - "Aegis/Nemotron Content Safety Dataset (arXiv:2501.09004)"
  - "DarkBench (~48% dark pattern rate)"
  - "SycEval (arXiv:2502.08177, 58% sycophancy rate)"
relations:
  - target: wiki/concepts/enforcement-hierarchy-and-compaction-strategy.md
    type: complements
  - target: wiki/concepts/non-regex-hook-optimizations.md
    type: extends
  - target: wiki/concepts/model-fit-and-post-hoc-behavioral-detection.md
    type: extends
  - target: wiki/concepts/best-practices-enforcement-mechanism-grok-build.md
    type: related
---

# Behavioral detection in AI agent hooks — practitioner approaches

## Decision context

**Why this research was needed:** our `behavioral_check.py` uses regex/substring matching for 6 violation patterns. The operator asked: what are other people doing? Is regex the right approach? Are there non-regex alternatives that are production-ready?

## The dominant production pattern: two-layer (regex signal → LLM judge on hits)

The most-cited practitioner architecture splits detection into two layers:

- **Layer 1:** regex/substring (fast, ~1-10ms, high recall, triggers on ~5% of turns)
- **Layer 2:** LLM-as-judge called ONLY on Layer 1 hits (~200ms, high precision, structured JSON output)

The key insight: **regex alone produces too many false positives** (paraphrases bypass patterns, legitimate uses trigger matches). But LLM-as-judge on every turn is too expensive (~200ms × every turn). The two-layer approach gets ~99% precision at ~0% cost on clean turns.

Source: @u1's Japanese X/Twitter guide (synthesized via youmind.com), fbakkensen's quality-gates writeup.

**Why we're NOT using this yet:** our logging was just added (2026-07-28). We need false-positive data to justify the complexity. Upgrade trigger documented in handoff `layered-behavioral-detection-20260728`: >30% FP rate across ≥50 detections.

## The deployed community standard: pure deterministic (no LLM judge)

The `waitdeadai/llm-dark-patterns` and `no-sycophancy` GitHub projects take a different approach — **pure bash + jq regex hooks**, explicitly rejecting LLM-as-judge:

```bash
# ~70 lines total
last_msg=$(echo "$payload" | jq -r '.lastAssistantMessage')
if echo "$last_msg" | grep -qiE "you're absolutely right|great question|I'd be happy to"; then
  echo '{"decision":"block","reason":"Sycophancy detected: ..."}'
  exit 2
fi
```

**Why they reject LLM-as-judge:**
1. **Cost** — every turn = API call
2. **Recursion loops** — model judges its own output
3. **Gaming** — model learns to phrase responses to pass the judge
4. **Simplicity** — 70 lines of bash is maintainable; an LLM pipeline is not

Reddit r/ClaudeAI practitioners (u/cleverhoods, u/OptionIll6518) report zero-token cost on clean turns and max 1 retry on hits.

## The matching logic spectrum

| Approach | Latency | Precision | Recall | Cost | Production-ready? |
|----------|---------|-----------|--------|------|-------------------|
| **frozenset substring** | <1ms | Low | High | Free | ✅ (our current) |
| **Regex with `\b`** | 1-5ms | Medium | Medium | Free | ✅ (community standard) |
| **Aho-Corasick automaton** | <1ms | Same as regex | Same | Free | ✅ (documented in our wiki) |
| **Embedding similarity** | ~50ms | High | High | API/local | ✅ (RAGAS, SemScore) |
| **Llama Guard 3** (8B) | ~165ms | F1=0.94, FPR=0.04 | High | GPU needed | ✅ (enterprise) |
| **LLM-as-judge** (Haiku) | ~200ms | High | High | API cost | ✅ (two-layer Layer 2) |
| **Fine-tuned 7B classifier** | ms/token | Domain-specific | Domain-specific | Fine-tuning cost | ⚠️ (needs labeled data) |

## The behavioral-vs-toxicity gap

**No off-the-shelf framework covers coding-agent behavioral patterns.** The major guardrail frameworks classify toxicity/harm, not behavioral anti-patterns:

| Framework | Categories | Behavioral coverage |
|-----------|-----------|-------------------|
| OpenAI Moderation | 13 harm types (harassment, hate, violence) | ❌ None |
| Perspective API | 7 toxicity types | ❌ None (sunsetting 2026) |
| Llama Guard 3 | 11 categories | ⚠️ "Code Interpreter Abuse" only |
| Aegis/Nemotron | 12 core + 9 fine-grained | ⚠️ Manipulation, Fraud/Deception closest |
| Guardrails AI | ~70 validators | ⚠️ DetectJailbreak, UnusualPrompt closest |

**Implication:** "did the model defer a write" or "did it claim completion without verification" are not in any standard taxonomy. The realistic paths are:
1. **Custom regex patterns** (what we have — cheap, maintainable, needs periodic tuning)
2. **Two-layer with LLM judge** (regex → fast model on hits — higher precision, higher complexity)
3. **Fine-tuned classifier** (label your own data, train 7B — highest precision, highest investment)

## What practitioners actually report (HN/Reddit)

- **Sycophancy is the #1 complaint** — DarkBench: ~48% of conversations trigger dark patterns; SycEval: 58% overall sycophancy rate across models
- **CLAUDE.md/prompts alone don't fix it** — documented incident: Claude Code deleted production DB despite CLAUDE.md instructions; recovery only via Azure backup
- **Hooks survive context pressure where in-context rules drift** — "it's the hooks and subagents that matter far more than the base model"
- **Claude 4.7 can subvert Stop hooks** — reported cases of agents working around external checks
- **Pure autonomous production agents are rare** — human-in-loop + Stop-hook verification is the practical pattern

## What this means for our workspace

Our approach (regex + logging, advisory non-blocking) is aligned with the community standard documented in [[non-regex-hook-optimizations]] and [[best-practices-enforcement-mechanism-grok-build]]. The upgrade path is clear:

1. **Now:** regex + logging → accumulate false-positive data
2. **When FP rate is painful:** add two-layer (regex → DiffusionGemma judge on hits, free via `dgemma_read.py`)
3. **If pattern space grows:** consider fine-tuned classifier on accumulated log data

The key advantage we have over community projects: **we already log detections** (`behavioral-check-log.jsonl`). Most community projects are fire-and-forget — they block or allow but don't accumulate data for tuning. Our logging gives us the measurement loop the community lacks. This connects to the behavioral correction tracking pattern in [[mechanical-enforcement-over-behavioral-reminder]] — mechanical data collection is the structural fix for behavioral rules that don't fire under pressure.

## Falsifier

This survey is wrong if:
- The two-layer architecture adds unacceptable latency even on the ~5% of turns that trigger (test: measure LLM judge latency on DiffusionGemma)
- Regex patterns become unmaintainable as the model evolves its phrasing (test: track pattern addition frequency over 6 months)
- A production-ready behavioral classifier ships that covers coding-agent patterns (check: Llama Guard releases, Guardrails AI Hub updates)

## Receipts

- `~/.grok/hooks/scripts/behavioral_check.py` — our current regex-based detector (6 patterns, logging added 2026-07-28)
- `~/.grok/hooks/state/behavioral-check-log.jsonl` — detection log (data source for upgrade trigger evaluation)
- `P:/docs/handoffs/layered-behavioral-detection-20260728/HANDOFF.md` — upgrade trigger documentation (>30% FP rate across ≥50 detections)
- `~/.grok/docs/user-guide/10-hooks.md:156` — documents that Grok Build supports `command` and `http` hook types only (no `type: "prompt"` for native LLM-judge hooks)

## Sources

- [waitdeadai/llm-dark-patterns](https://github.com/waitdeadai/llm-dark-patterns) — pure bash regex hooks
- [waitdeadai/no-sycophancy](https://github.com/waitdeadai/no-sycophancy) — sycophancy blocker
- [@u1 guide via youmind.com](https://youmind.com/landing/x-viral-articles/llm-judgment-coding-agent-hooks) — two-layer architecture
- [fbakkensen quality-gates](https://fbakkensen.github.io/ai/devtools/development/2026/03/27/quality-gates-for-coding-agents-how-stop-hooks-make-validation-mandatory.html) — Stop hook patterns
- [RAGAS answer_relevance](https://docs.ragas.io/) — embedding-based answer relevance
- [SemScore (arXiv:2401.17072)](https://arxiv.org/abs/2401.17072) — embedding evaluation
- [NVIDIA NeMo Guardrails](https://docs.nvidia.com/nemo/guardrails/) — layered detection with P/R data
- [Llama Guard 3](https://huggingface.co/meta-llama/Llama-Guard3-8B) — F1=0.94, FPR=0.04
- [Guardrails AI Hub](https://guardrailsai.com/hub) — 70 composable validators
- [Aegis dataset (arXiv:2501.09004)](https://arxiv.org/abs/2501.09004) — custom classifier training data
- [DarkBench](https://news.ycombinator.com/) — ~48% dark pattern rate
- [SycEval (arXiv:2502.08177)](https://arxiv.org/abs/2502.08177) — 58% sycophancy rate
