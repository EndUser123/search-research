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

## Diagnostic decision tree (use this BEFORE reading dossiers)

The dossier directory may be **empty** even when the model is down. This happens when the launcher itself exited (not llama-server crashing). Follow this tree:

```
1. Is there a llama-server process?
   ├─ YES, running → check inference (HUNG path below)
   └─ NO, not running →
      ├─ Is there a run-ornith-server.ps1 (launcher) process?
      │  ├─ YES → launcher alive but llama-server died → check dossier + .err
      │  └─ NO → launcher also dead →
      │     ├─ Check .err log: does it end with an error line?
      │     │  ├─ YES (CUDA error, assertion) → llama-server crash
      │     │  └─ NO (ends mid-generation, no error) →
      │     │     → EXTERNAL KILL: launcher was killed (window closed, OS
      │     │       process kill, user llama-stop), finally block killed
      │     │       llama-server. NOT a crash — the model was healthy when
      │     │       killed. No dossier because the while-loop never detected
      │     │       the exit (the launcher process itself was dying).
      │     └─ Check .err archives for prior REAL crash signatures
```

## HUNG state (loaded but inference times out)

**Symptom:** `cc-ccr -start` reports `local model HUNG (loaded, inference failed:
The request was canceled due to the configured HttpClient.Timeout of 15 seconds
elapsing.)`. Port 8010 is bound, /health passes, /v1/models returns the model,
but actual inference requests hang.

**What this means:** the GGUF is loaded in VRAM, but the GPU compute is stuck.
Possible causes: CUDA deadlock (uncorrectable), KV cache corruption, or a
prior massive request consuming the single slot under --parallel 1 (the probe
queued behind it and timed out).

**What to do:**
1. Check the `.err` log tail — does it end mid-generation (no error)?
   That confirms a GPU hang, not a process crash.
2. `llama-stop; llama-start` — kills and restarts. The fresh process
   reloads the GGUF cleanly. GPU state resets.
3. If HUNG recurs rapidly (within minutes), the GPU may need a driver-level
   reset (`nvidia-smi -r` or system reboot). This is a hardware/driver issue,
   not a llama.cpp config issue.

**No dossier for HUNG:** the dossier fires on process EXIT. A HUNG model
hasn't exited — it's alive but not responding. The `.err` log is the only
evidence source. The watchdog doesn't detect HUNG either (it probes rungs
1-4 only, no inference, to avoid --parallel 1 slot contention). This is
a deliberate design choice (avoid killing a healthy busy server), but it
means HUNG requires manual detection via `cc-ccr -start` or `cc-ccr -usage`.

### Distinguishing BUSY, HUNG, and CRASH

A 15-second inference timeout does NOT by itself prove GPU deadlock. The
probe could simply be queueing behind a real request — exactly the race the
launcher and ccr-custom-router both deliberately avoid. Read the symptoms
before assuming the worst:

| State | Signal | Probe behavior | What it means | Recovery |
|---|---|---|---|---|
| **BUSY** | `is_processing: true` on `/slots` | `/slots` returns the slot as busy | A valid request is occupying the single slot (--parallel 1). Normal under load. | Wait. Do NOT kill. Do NOT escalate. The next request will get a free slot or the router will admit to cloud (ccr-custom-router admission control). |
| **HUNG** | `/health` + `/v1/models` OK, but inference produces 0 tokens OR probe times out | No meaningful progress AND inference is unresponsive after the configured stall threshold | GPU compute is stuck (CUDA deadlock, KV cache corruption, OOM with no exit). The `.err` log ends mid-generation with no error line. | Manual restart (`llama-stop; llama-start`). If recurrent within minutes → driver/hardware issue. |
| **CRASH** | `llama-server` process exits | Watchdog or external observer detects exit. Dossier written to `P:/.claude\state\local-model-crashes\`. | Process-level fault (CUDA error, OOM-killed, assertion, hard segfault). | Read the dossier. See "How to read a dossier" above. Restart handled by watchdog. |

**The 15s inference probe is NOT a HUNG oracle.** Under `--parallel 1`, the
probe queues behind whatever is in flight, so the same probe that reports
HUNG can succeed immediately after the in-flight request completes. Treat
15s timeouts as "investigate," not "GPU is dead." Check `/slots` first; if
`is_processing: true`, the model is BUSY, not HUNG. Only escalate to
HUNG/CRASH after the slot has been observed idle and inference still fails.

The CCR custom router (ccr-custom-router.js) gates automatic local-first
routing on `/health` + `/slots`: busy → admit to cloud fallback. So the
typical user-facing path under load is "request hits local successfully,
next request admitted to cloud, next request hits local again" — not
"queue of requests waiting for the slot."

## Symptom patches already shipped (NOT the root cause)

These make crashes less painful but don't prevent them:
- `finally` block kills orphaned llama-server on give-up (no zombie GPU process)
- `.err` archives to timestamped files (crash evidence survives)
- `Wait-LocalModelReady` no longer false-negatives on startup
- Crash dossier (this doc's companion)

## What we deliberately did NOT do

- **No config experiment yet.** We have zero crash dossiers. Changing variables before we can measure is guessing. Wait for the first real dossier, then pick the hypothesis it points at.
- **No "experiment matrix."** The candidate table above is consulted only after a dossier narrows the cause — not run as a blind sequence.
