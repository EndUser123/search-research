# Plan: Finish Fleet Benchmarking Properly

**Created:** 2026-08-12
**Session:** 019fdf47
**Status:** ready-to-implement

## Goal

Complete the R5b/R5g certification matrix for all fleet providers: every provider tested across all 3 capabilities (tool-loop, reasoning, mechanical) via both HTTP and PI methods, with clean data (no false zeros), and models promoted where warranted.

## Current state

| Provider | HTTP tool-loop | PI tool-loop | HTTP reasoning | PI reasoning | HTTP mechanical | PI mechanical |
|---|---|---|---|---|---|---|
| NVIDIA | ✅ 60% | ✅ 69% | ✅ 84% | ✅ 81% | ✅ 86% | ✅ 80% |
| MiniMax | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ |
| ZAI | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ |
| OpenRouter | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ |
| OpenCode Go | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Cohere | ❌ (quota) | ❌ | ❌ | ❌ | ❌ | ❌ |
| Zen | ❌ (dead) | ❌ (dead) | ❌ | ❌ | ❌ | ❌ |

**Blockers:**
- Cohere: trial key 1,000 calls/month exhausted. Reset: September 1, 2026.
- Zen: only `big-pickle` alive. All other Zen free models disabled by provider.

## Phase 1: Fill PI certification gaps (MiniMax, ZAI, OpenRouter)

**Why first:** these 3 providers have proven HTTP capability (all 3 capabilities pass). The PI path just needs to confirm the models work under the agent harness. Low risk — we expect most models to pass.

### Task 1.1: MiniMax PI reasoning + mechanical
```powershell
cd C:\Users\brsth\.grok\skills\model-benchmark\scripts
python pool_test.py --provider minimax --capability reasoning --method pi --probe
python pool_test.py --provider minimax --capability mechanical --method pi --probe
```
**Acceptance:** both complete with real scores (not all-zeros). Auto-diagnose runs on any zeros. MiniMax concurrency ceiling = 2.
**Time:** ~30 min total

### Task 1.2: ZAI PI reasoning + mechanical
```powershell
python pool_test.py --provider z.ai --capability reasoning --method pi --probe
python pool_test.py --provider z.ai --capability mechanical --method pi --probe
```
**Acceptance:** both complete with real scores. ZAI concurrency ceiling = 7.
**Time:** ~20 min total

### Task 1.3: OpenRouter PI reasoning + mechanical
```powershell
python pool_test.py --provider openrouter --capability reasoning --method pi --probe --free-only
python pool_test.py --provider openrouter --capability mechanical --method pi --probe --free-only
```
**Acceptance:** both complete with real scores. OR concurrency ceiling = 8.
**Time:** ~40 min total

## Phase 2: Test OpenCode Go (18 subscription models)

**Why:** high-value gap. 18 models on a $10/month subscription — never tested. These are known-good coding models (GLM-5.2, Grok 4.5, DeepSeek V4, Kimi K3, etc.) that should score well.

### Task 2.1: OpenCode Go — add to PI config
PI needs an `opencode-go` provider section in `~/.pi/agent/models.json`. The auth.json already has the key (added this session). The models.json section already exists at line 1702.

**Verify:** `pi -p --provider opencode-go --model glm-5.2 --no-session --mode text "Say OK"` returns OK.

### Task 2.2: OpenCode Go HTTP tool-loop
```powershell
python pool_test.py --provider opencode-go --capability tool-loop --probe
```
**Acceptance:** runs against 18 models. Exclusion filter + auto-diagnose both fire.
**Time:** ~45 min

### Task 2.3: OpenCode Go HTTP reasoning + mechanical
```powershell
python pool_test.py --provider opencode-go --capability reasoning --probe
python pool_test.py --provider opencode-go --capability mechanical --probe
```
**Time:** ~30 min total

### Task 2.4: OpenCode Go PI (all 3 capabilities)
```powershell
python pool_test.py --provider opencode-go --capability tool-loop --method pi --probe
python pool_test.py --provider opencode-go --capability reasoning --method pi --probe
python pool_test.py --provider opencode-go --capability mechanical --method pi --probe
```
**Time:** ~60 min total

## Phase 3: Zen big-pickle (quick test)

### Task 3.1: Test big-pickle across all capabilities
```powershell
python pool_test.py --model zen-big-pickle --capability tool-loop
python pool_test.py --model zen-big-pickle --capability reasoning
python pool_test.py --model zen-big-pickle --capability mechanical
```
**Acceptance:** real scores. If big-pickle scores well, it's a promotable free model.
**Time:** ~15 min

## Phase 4: Promote qualified models

### Task 4.1: Run promote_models.py
```powershell
python C:/Users/brsth/.grok/skills/model-quota/scripts/promote_models.py --dry-run --verbose
```
**Review:** check which models meet the promotion threshold (N≥10 + Wilson lower-bound floor ≥0.75).
**Then:** run without `--dry-run` to activate.

### Task 4.2: Verify promotion results
- Check fleet-models.json for updated `lifecycle: "active"` fields
- Run `pick_model.py --list` to verify newly promoted models appear in the pool
- Test a spawn_subagent on a newly promoted model to verify end-to-end

## Phase 5: Final coverage report

### Task 5.1: Run the certification matrix report
```powershell
python P:/tmp/cert_coverage.py
```
**Acceptance:** every non-blocked provider shows data in all 6 cells. Blocked providers (Cohere) have a documented reason.

### Task 5.2: Generate discrimination report
```powershell
python pool_test.py --report
```
**Acceptance:** report shows which problems discriminate between models (good test suite signal).

## Sequencing

```
Phase 1 (PI gaps) ────────────┐ ~90 min
Phase 2 (OpenCode Go) ────────┤ ~135 min (can overlap with Phase 1 — different rate pools)
Phase 3 (Zen big-pickle) ─────┤ ~15 min
                               ↓
Phase 4 (Promotion) ──────────┤ ~5 min (depends on 1-3 completing)
                               ↓
Phase 5 (Final report) ───────┘ ~5 min
```

Phases 1, 2, and 3 can run in parallel (different providers = independent rate pools). Phase 4 depends on 1-3. Phase 5 depends on 4.

## Exclusions in effect

These models are excluded and won't be tested (saving time):

| Model | Excluded from | Reason |
|---|---|---|
| `nvidia/nemotron-mini-4b-instruct` | tool-loop | 4B — too small |
| `meta/llama-3.2-3b-instruct` | tool-loop, reasoning | 3B — too small |
| `nvidia/llama-3.1-nemotron-nano-vl-8b-v1` | all 3 | PI dispatch empty consistently |
| `deepseek-v4-flash-free` | * | Model disabled by provider |
| `liquid/lfm-2.5-2.6b:free` | tool-loop, reasoning | 2.6B — too small |
| `north-mini-code-free` | * | Disabled by OpenCode Zen |
| `longcat-2.0-free` | * | Disabled by OpenCode Zen |
| `ling-3.0-flash-free` | * | Disabled by OpenCode Zen |

## Deferred (not in this plan)

- **Cohere native testing:** blocked until September 1 quota reset. Use OpenRouter `or-cohere-north-mini-code-free` meanwhile.
- **Research-before-test (capability pre-filtering):** design-level change needs `/design` scoping. The exclusion mechanism covers the most common waste case (known-dead models).
- **NIM PI testing:** NIM is the same NVIDIA endpoint; NIM data likely duplicates NVIDIA. Not worth separate testing.

## Risk

- **OpenCode Go PI may fail:** PI's opencode-go section may have compat issues (supportsDeveloperRole etc.). If PI tests produce zeros, auto-diagnose will classify them and suggest fixes.
- **OpenRouter free-tier rate limits:** OR may 429 under parallel PI testing. If so, reduce `--max-parallel` to 2-4.
- **MiniMax concurrency:** ceiling = 2. PI tests will be slow. Expected.
