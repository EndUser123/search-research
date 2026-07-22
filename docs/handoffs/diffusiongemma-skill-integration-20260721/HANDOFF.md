---
thread_id: 0265f516-dcb1-4080-a68b-98135cbda750
parent_handoff_path: none
current_session_id: 019f821c-854e-76c1-a755-add284838bdf
current_terminal_id: console
produced_at: 2026-07-21T23:30:00Z
status: open
handoff_type: implementation
assigned_to: unassigned
accurate_as_of_head: 13f19d20c70f3e09dd26e08b414b4335154847ed
source_transcript: C:\Users\brsth\.grok\sessions\P%3A%5C\019f821c-854e-76c1-a755-add284838bdf\chat_history.jsonl
---

# Handoff: DiffusionGemma integration into skills

## 1. Objective (one sentence)

Wire the verified-working `diffusiongemma_read.py` (single, enhanced, and batch modes) into `/www`, `scan_techniques.py`, and other skills that do bulk file reads, replacing parent-inherited model calls for mechanical breadth-pass reads.

## 2. Status

**Task A COMPLETE (2026-07-21). Task B/C still open.**

| Component | Built? | Tested? | Integrated into skills? |
|---|---|---|---|
| `diffusiongemma_read.py` (single) | ✅ | ✅ T1 | ✅ (/www Phase 1 fallback) |
| `diffusiongemma_read.py` (--enhanced) | ✅ | ✅ T4 blind (20/20) | ❌ |
| `diffusiongemma_read.py` (--batch) | ✅ | ✅ multi-path fix + 2-file re-test 2026-07-21 | ✅ (/www Phase 1 step 3) |
| `scan_techniques.py` (regex breadth) | ✅ | ✅ 968 skills in 17s | ❌ (Task B — note: dir mode now needs `--pattern SKILL.md`) |
| AGENTS.md model-tiering rules | ✅ | ✅ | ✅ (documented) |
| tool-fallbacks.md | ✅ | ✅ | ✅ (documented) |

**2026-07-21 update (Task A shipped):**
- `/www` Phase 1 step 3 now invokes `diffusiongemma_read.py <paths...> --batch --json` as the default breadth-reader, with automatic fallback to parent-model reads if the endpoint is unavailable.
- Script fix required: argparse changed from single `path` to `paths` (nargs="+") so it accepts the multiple concept files qmd returns; dir-mode glob made configurable (`--pattern`, default `*.md`) so it works on wiki concepts, not just SKILL.md trees. Verified: 2 concepts → 1 API call → 4.8s, both summarized correctly.
- **Backward-compat note for Task B:** the technique-scan dir-mode caller must now pass `--pattern SKILL.md` explicitly (was hardcoded before).

## 3. What's verified (all from 2026-07-21 testing)

**DiffusionGemma works via direct API, fails via spawn_subagent:**
- Root cause: spawn_subagent sends parameters that conflict with thinking mode (thinking ON by default; disabling produces empty content)
- Direct API (Python urllib) works perfectly: 1-7s per call, valid content, 256K context

**Performance characteristics:**
- Single read: ~1-2s, accurate summaries
- Enhanced (3-perspective parallel fan-out + merge): ~2.4s, 20/20 blind quality (matches ccr-ornith)
- Batch (20 files in one call): ~6.5s, 20/20 files summarized correctly
- Context window: 262K tokens (verified in config.toml:393)
- Concurrency: 3 parallel requests work (1.7x speedup over sequential)
- Cost: free (Nvidia-hosted endpoint)

**Model provenance:**
- Model provider: Google (DiffusionGemma 26B A4B IT)
- Inference provider: Nvidia (integrate.api.nvidia.com)
- Gateway: opencode.ai/zen (routes to Nvidia)
- Config: `config.toml:386-393`

## 4. What needs to be built (integration tasks)

### Task A: `/www` Phase 1 integration (~15 min)
In `/www` Phase 1, when reading wiki concepts to identify gaps, use `diffusiongemma_read.py --batch` to batch-read the related concepts instead of reading them one at a time with the parent model.

**Current flow:** `qmd search` → manually read top 3 concepts with parent model
**Target flow:** `qmd search` → batch-read top 5-10 concepts via `diffusiongemma_read.py --batch` → use summaries to identify gaps

### Task B: `scan_techniques.py` LLM pass (~20 min)
After the regex scan identifies high-density skills (technique_count >= 5), use `diffusiongemma_read.py --batch` to get semantic summaries of those skills.

**Current flow:** regex scan → JSON output with technique counts → manual deep-read of top N
**Target flow:** regex scan → DiffusionGemma batch-read of top 50 high-density skills → enriched output with 1-sentence summaries

### Task C: `/aar` preprocessor integration (~30 min, future)
Batch-read session segments via DiffusionGemma before the LLM analyzes them. This is lower priority — the preprocessor already handles mechanical extraction.

## 5. What NOT to integrate

- ❌ `/www` Phase 2 synthesis — use parent-inherited model (quality gap on reasoning)
- ❌ `/tp` Step 2 critique — use parent-inherited or ccr-ornith (needs fresh context, tool access)
- ❌ Any skill requiring tool use — DiffusionGemma can't use tools through the gateway
- ❌ spawn_subagent — use ccr-ornith for subagent reads (DiffusionGemma fails through framework)

## 6. Resumption protocol

1. Read `P:/.data/wiki/scripts/diffusiongemma_read.py` — the working script with single/enhanced/batch modes
2. Read `P:/.data/wiki/concepts/diffusiongemma-4-tier-integration.md` — the verified 4-tier architecture
3. Read `P:/.data/wiki/concepts/diffusiongemma-optimal-usage-dos-and-donts.md` — the full optimal-usage guide
4. Read `C:/Users/brsth/.grok/skills/www/SKILL.md` Phase 1 and Phase 2 — identify where DiffusionGemma fits
5. Implement Task A (batch-read in `/www` Phase 1)
6. Test by running `/www <topic>` and verifying it uses DiffusionGemma for concept reads

## 7. Related artifacts

- Script: `P:/.data/wiki/scripts/diffusiongemma_read.py`
- Scan script: `P:/tmp/scan_techniques.py`
- Wiki concepts: `diffusiongemma-4-tier-integration.md`, `diffusiongemma-optimal-usage-dos-and-donts.md`, `compensating-for-weaker-models-ensemble-multi-pass.md`
- Config: `C:/Users/brsth/.grok/config.toml:386-393` (DiffusionGemma config)
- Tool fallbacks: `C:/Users/brsth/.grok/tool-fallbacks.md`
- AGENTS.md: "Code-first breadth scan" and "Model tiering" sections

## 8. Open questions

- Should DiffusionGemma batch reads be cached to avoid re-reading on subsequent `/www` runs? (The www-ledger already covers this for research, but not for wiki concept reads.)
- Should the batch mode support custom prompts per file (not just 1-sentence summaries)?
- Should scan_techniques.py be promoted from P:/tmp/ to P:/.data/wiki/scripts/?
