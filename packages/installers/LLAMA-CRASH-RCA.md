# llama-server Crash RCA Runbook

**When to open this:** the launcher gave up (`3 rapid crashes — giving up`), OR a new file appeared in `P:\.claude\state\local-model-crashes\`, OR the user says "llama crashed again."

**Goal context:** maximizing local-model use. Crashes = local downtime = traffic spills to external providers. Fixing the crash-loop is the highest-leverage move for cost.

## What we know (verified 2026-07-09)

- **Hardware:** RTX 5070 (Blackwell, sm_120), 12GB VRAM, CUDA 12.8
- **Model:** Ornith-1.0-9B Q4_K_M (Qwen3.5-arch)
- **Launcher args:** `-ngl 99 -c 65536 -t 6 --parallel 1 -fa on -ctk q4_0 -ctv q4_0 -b 2048 -ub 1024 --reasoning-preserve --jinja --temp 0.6 --top-p 0.95 --top-k 20`
- **No speculative decoding** (no `--spec-type` / draft / mtp flag). MTP-crash issues (#23210, #23500, #22867) are ruled out.
- **Observed pattern (from user terminal, not crash logs):** uptime decreased 3.3h → 12m → startup-fail → 10s. Consistent with accumulating state, NOT a one-shot trigger.
- **VRAM at ~95%** (11.4GB / 12GB measured via system_watch.log). This is NOT headroom — it points at VRAM pressure, not away from it.

## The crash dossier

Each exit writes `P:\.claude\state\local-model-crashes\<timestamp>.json`. Fields:

| Field | What it tells you |
|---|---|
| `exit_code` | **Read first.** 0 = clean exit (watchdog killed it). 137 = OOM-killed. Nonzero/`null` = crash (CUDA fault, SIGSEGV). `null` often means a hard fault with no flush. |
| `gpu_snapshot` | VRAM used/total at crash moment. If `vram_used` ≈ `vram_total` → VRAM exhaustion. If GPU was faulted, this may be null/hang. |
| `vram_trajectory` | Last 5 watch samples. Was VRAM climbing into the crash? Flat trajectory + crash = not VRAM. |
| `windows_events` | **PRIMARY for GPU/driver faults.** EventID 4101 (Display, TDR recovery), 153 (driver error), 41/6008 (kernel power / unexpected shutdown). If these fired at the crash timestamp → it's a driver/OS-level fault, not a llama.cpp config issue. |
| `last_local_requests` | Last 3 requests that hit local. Was a 60k-token prompt the trigger? |
| `err_tail` | Last 50 lines of llama-server stderr. **Secondary** — may be empty/truncated on hard crash (process died before flush). |
| `args` | The exact config at crash (so experiment configs are self-documenting). |
| `uptime_s` | How long this run lasted before crashing. Compare across dossiers. |

## How to read a dossier (in order)

1. **`exit_code` + `windows_events`** — classify the failure: driver/OS fault vs llama.cpp-internal vs OOM. This single step determines whether config changes can help at all.
2. **`gpu_snapshot` + `vram_trajectory`** — was VRAM the pressure? If `vram_used` was at the ceiling and climbing → VRAM hypothesis.
3. **`err_tail`** — any CUDA error string, assertion, or "out of memory" line. Often empty for hard faults.
4. **`last_local_requests`** — was there a pattern (huge prompt, rapid sequence)?
5. **`uptime_s`** across dossiers — if uptime is decreasing run-over-run → accumulating-state hypothesis. If random → external trigger.

## After reading: form ONE hypothesis, change ONE variable

Do not change multiple things at once. Each experiment needs the new logging to compare.

**Candidate variables (only pursue the one the dossier points at):**

| If dossier shows... | Try... | Why |
|---|---|---|
| VRAM at ceiling + climbing | `-c 32768` (halve context) | Less VRAM pressure; fits the 95%-utilization measurement |
| VRAM at ceiling + climbing | drop `-ctk q4_0 -ctv q4_0` (default f16 KV) | **WARNING:** f16 uses MORE VRAM — only if halving context first leaves room |
| windows_events has TDR/driver errors | update NVIDIA driver / CUDA toolkit | It's a driver fault, not a config issue — config changes won't help |
| err_tail has CUDA assertion | rebuild llama.cpp from latest master | Upstream fix may have landed |
| uptime decreasing, no VRAM pressure | drop `--reasoning-preserve` | Reasoning-buffer accumulation (unverified hypothesis) |

**Decision rule:** if a config runs >24h without crash → probable fix, keep it. If 3 crashes under a config show no uptime improvement → that variable isn't the cause, revert and move to the next hypothesis.

## Falsification

This whole approach is wrong if the crash is **external** (power blip, Windows update, thermal shutdown, GPU hardware fault). Check `windows_events` for `Kernel-Power` (41) or thermal events before assuming it's a llama.cpp config issue. If those are present, no config change will fix it — it's a hardware/environment problem.

## Symptom patches already shipped (NOT the root cause)

These make crashes less painful but don't prevent them:
- `finally` block kills orphaned llama-server on give-up (no zombie GPU process)
- `.err` archives to timestamped files (crash evidence survives)
- `Wait-LocalModelReady` no longer false-negatives on startup
- Crash dossier (this doc's companion)

## What we deliberately did NOT do

- **No config experiment yet.** We have zero crash dossiers. Changing variables before we can measure is guessing. Wait for the first real dossier, then pick the hypothesis it points at.
- **No "experiment matrix."** The candidate table above is consulted only after a dossier narrows the cause — not run as a blind sequence.
