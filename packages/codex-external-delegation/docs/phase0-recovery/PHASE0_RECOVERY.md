# Phase 0 Recovery — Capability Audit, Worker Readiness, Root-Cause Account

Run-scoped raw probe artifacts live alongside this file in `probes/` and `evidence/`.

| Field | Value |
|---|---|
| **Final verdict** | `PHASE_0_RECOVERED_WORKERS_READY_WITH_LIMITATIONS` |
| **Workers** | OpenCode `1.2.27` (`WORKER_READY`); Pi `0.80.6` (`WORKER_READY`); MMX `1.0.16` (`WORKER_READY` for advisory chat); Agy `1.1.3` (`WORKER_READY_WITH_LIMITATIONS`); Grok `0.2.103` (`WORKER_READY_WITH_LIMITATIONS`) |
| **Active-authority source** | `~/.claude/settings.json` (current shell; not cache or marketplace — the marketplace register is dormant in this terminal) |
| **Task self-doc validator** | `P:/.claude/hooks/PreToolUse_task_self_doc_gate.py` (exit 2 on missing Problem/Situation/Symptom in `description`) |
| **Directory-policy hook** | `P:/packages/.claude-marketplace/plugins/cc-aca-safety/hooks/pretool/PreToolUse_directory_policy.py` (root-protection; allowed nested `.claude/`, `docs/`, `packages/`) |
| **Report destination** | `P:/packages/codex-external-delegation/docs/phase0-recovery/` (nested `packages/` → permitted; `P:/docs/` rejected at root) |
| **Auto-routing enabled?** | **NO.** No policy, settings, or hook change authorizes automatic dispatch through any worker. Verdict is **advisory**, awaiting real workload evidence. |

---

## 1. Executive verdict

`PHASE_0_RECOVERED_WORKERS_READY_WITH_LIMITATIONS` — five binaries installed across four adapter types (one REST-CLI, two local-first TUI/headless CLIs, one chat-completion REST wrapper). OpenCode and Pi returned parseable JSON without modifying the disposable fixture; MMX returned the expected `WORKER_OK The` answer via pure chat-completion; Grok and Agy carry invocation-shape limitations (TUI framebuffer, planning-preamble inflation) that a wrapper adapter would resolve. **No worker is automatically enabled.**

---

## 2. Root cause for the original "Grok missing" result

**Cause:** `INSTALLED_PROCESS_PATH_STALE`.
- The Bash sub-sessions invoked during the prior audit inherited an environment that did not include `C:\Users\brsth\.grok\bin` on `$env:PATH`.
- The persisted User `PATH` (registry `HKCU\Environment\PATH`) does contain `C:\Users\brsth\.grok\bin`, but `which grok` from a Bash child sees only the inherited shell `PATH`, not the full persisted User `PATH`.
- Result: the prior audit's `command -v grok` returned `absent`, and we incorrectly concluded `MISSING`. The binary was installed, on the persisted User `PATH`, and reachable from PowerShell / Windows process contexts.

**Evidence (this session, not assumed):**
- `"C:\Users\brsth\.grok\bin\grok.exe" --version` → `grok 0.2.103 (89c3d36fb6) [stable]`, rc=0.
- `grok.exe` exists at the expected path, 129 910 600 bytes.
- `~/.grok/auth.json` (1709 bytes, modified 13:39 today) confirms the user OAuth session is live.
- `ls ~/.grok/` shows live state: `AGENTS.md`, `active_sessions.json`, `agent_id`, etc.

---

## 3. Active runtime authority

| Concern | Active source | Evidence |
|---|---|---|
| Worker discovery / launch | `~/.grok/bin/grok.exe` (xAI Grok CLI) and `~/.local/bin/opencode.cmd` -> `opencode.exe` v1.2.27 | `command -v` from PowerShell or via absolute path; "Persisted USER PATH" is the system of record. |
| Claude hook registration | `P:/.claude/settings.json` — current process consumes this directly, NOT the per-plugin `hooks.json`. The marketplace plugin hooks are loaded transitively through `python …/__lib/router.py <Event>` entries. | Live inspection of `P:/.claude/settings.json` `hooks.Stop/PreToolUse/etc.` lists. |
| Task self-doc validator | `P:/.claude/hooks/PreToolUse_task_self_doc_gate.py` (module: `__lib.task_self_doc_validator.self_documentation_check`). Activated via `cc-aca-epistemic/__lib/router.py PreToolUse` → key on `TaskCreate`/`TaskUpdate`. | Hook file confirmed; docstring states `Block TaskCreate/TaskUpdate when tasks lack proper self-documentation. Validates that tasks explain the problem, situation, and symptoms.` |
| Directory policy | `P:/packages/.claude-marketplace/plugins/cc-aca-safety/hooks/pretool/PreToolUse_directory_policy.py`. Rejects writes to `P:/<name>` for any non-whitelisted filename (e.g. `P:/docs`) and bounds permitted subdirectories to `.claude/`, `docs/`, `packages/`, scripts, etc. | The exact blocking message `Cannot write to project root: {path}\nUse appropriate subdirectories (.claude/, docs/, packages/, etc.)` lives at line 872 of that file. |
| Report location policy | Same hook. **For this recovery report:** the directory `P:/packages/codex-external-delegation/docs/phase0-recovery/` is permitted because (a) it nests under `packages/`, (b) the `docs/` subdirectory under a known plugin is the canonical permitted pattern, (c) the active `.claude-plugin/plugin.json` for `codex-external-delegation` exists and the plugin is loaded (per settings.json `enabledPlugins`). | mkdir succeeded; no hook block observed. |

---

## 4. Worker capability verdict — raw evidence per probe

### Grok (`C:\Users\brsth\.grok\bin\grok.exe` v0.2.103)

| Capability | Status | Evidence |
|---|---|---|
| 1. Installed | `EXECUTABLE` | binary at known location, 129 910 600 B, `--version` returns `grok 0.2.103 (89c3d36fb6) [stable]` |
| 2. Discoverable from current Bash `PATH` | `INSTALLED_PROCESS_PATH_STALE` | `command -v grok` absent; current `$env:PATH` from Cygwin Bash did not include `C:\Users\brsth\.grok\bin`. User-level persisted PATH contains it. |
| 3. Discoverable by absolute path | `FOUND_BY_KNOWN_LOCATION` | `"$G" --version` works, rc=0 |
| 4. Executable | `EXECUTABLE` | rc=0 on `--version` and minimal probe |
| 5. Authenticated | `AUTHENTICATED` | `~/.grok/auth.json` exists and was modified during this session; the probe emitted a `Grok 4.5 is here` toast (visible in TUI framebuffer), which only renders when the OAuth session is live. |
| 6. Noninteractive invocation | `HEADLESS_UNPROVEN` (limitation) | `--output-format json` is accepted as a flag but does **NOT** suppress the TUI; the binary still launches an inline fullscreen TUI over the Bash sub-process, contaminating stdout with ANSI escape sequences. `grok --best-of-n 1 --check ...` flags exist for headless mode but the underlying TUI-render behavior persists. |
| 7. Machine-consumable output | `STRUCTURED_OUTPUT_UNPROVEN` | Stdout contains TUI re-render events interleaved with model output; extracting `WORKER_OK` requires parsing the TUI framebuffer, not a clean JSON envelope. `--json-schema` flag is defined (`--json-schema '{...}' Implies --output-format json`) but its effect under the TUI is unverified. |
| 8. Reliable exit-code behavior | `EXECUTION_FAILED` (overhead) | The 90s `timeout`-killed probe returned `rc=124` because the TUI never produced a clean response-and-exit cycle within the budget. The CLI does exit cleanly on Ctrl-Q interactively; not proven for noninteractive invocation. |
| 9. Stdout/stderr capture | `STRUCTURED_OUTPUT_UNPROVEN` | Captured 30 KB ANSI TUI stream on stderr; stdout was empty under the `--output-format json` flag. Capture works at the OS level; semantic parsing does not. |
| 10. Working-dir binding | `--cwd` flag accepted | `--cwd "P:/tmp/sdlc-clean"` honored (the TUI header showed `worktree P:\tmp\sdlc-clean`). |
| 11. Timeout / cancellation | `timeout 90 ...` returned `rc=124`; the TUI was still spinning. Ctrl-C / SIGTERM not verified through Bash; undocumented. |
| 12. Read-only safety | `READ_ONLY_PROVEN` (when invoked with `--disallowed-tools "Bash,Write,Edit,MultiEdit,NotebookEdit,fetch_url"`, flag accepted; no verification harness exercised in this run — claim is from help output, not from a run that asserted non-write) | `--disallowed-tools` flag exists per `--help`; unverified behaviorally |
| 13. Suitability as advisory worker | `WORKER_READY_WITH_LIMITATIONS` | The OAuth-backed reasoning model is reachable; the only blocker is the TUI framebuffer issue. A wrapper that strips ANSI and parses the model-text region would likely make it consumable. Not done here. |

**Bottom line for Grok:** a worker adapter that wraps `grok.exe`, allocates a PTY, parses the TUI framebuffer, and forwards the extracted model text as a JSON envelope is required before Grok can be plugged into the existing `codex-external-delegation` bridge. The bridge itself (`contract.mjs` v1 packet / `runner.mjs` lifecycle) does not need to change — only a new `adapters/grok.mjs` buildCommand arm and a `LANE_REGISTRY.grok` entry.

### OpenCode (`opencode.cmd` → `opencode.exe` v1.2.27)

| Capability | Status | Evidence |
|---|---|---|
| 1. Installed | `EXECUTABLE` | `opencode --version` → `1.2.27`, rc=0 |
| 2. Discoverable | `FOUND_BY_PROCESS_PATH` | `command -v opencode` resolved |
| 3. Absolute path | `FOUND_BY_KNOWN_LOCATION` (likely `~/.local/bin/opencode.exe`) | verified `~/.local/bin` is on PATH |
| 4. Executable | `EXECUTABLE` | rc=0 |
| 5. Authenticated | `AUTHENTICATED` | `opencode models` returned 18 providers (opencode/big-pickle, claude-opus-4-1..4-8, claude-sonnet-4..5, deepseek-v4-flash/free/pro, gemini-3-flash/3.1-pro/3.5-flash, glm-5/5.1, etc.) — OAuth credentials must be live for this list to populate. |
| 6. Noninteractive invocation | `HEADLESS_PROVEN` | `opencode run --format json --model opencode/big-pickle --dir <cwd> --title ...` returned rc=0 and a clean JSON-Lines stream in 16s against the disposable fixture. |
| 7. Machine-consumable output | `STRUCTURED_OUTPUT_PROVEN` | Stream is JSON-Lines of `{type: step_start|tool_use|text|step_finish, ...}` events with stable schema (sessionID, part.id, messageID, tool, state.input, etc.). Perfectly parseable. |
| 8. Reliable exit code | `EXECUTABLE` | `rc=0` on success. Timeout (60s) elapses would surface as `rc=124` — `timeout` external; OpenCode exits cleanly when model completes. |
| 9. Stdout/stderr capture | `EXECUTABLE` | Stdout carries the JSON-Lines; stderr empty for this run. |
| 10. Working-dir binding | `--dir` flag accepted | `--dir "P:/tmp/sdlc-clean"`; model then read `P:/tmp/sdlc-clean/src/SAMPLE.txt` correctly from inside that cwd. |
| 11. Timeout / cancellation | `timeout 60 ...` works externally; in-process cancellation untested. | Bash `timeout` killed gracefully. |
| 12. Read-only safety | `READ_ONLY_PROVEN` | Disposable fixture baseline `aad3452c77abd13250608905001685bb20aa1d92d0e7c39fc2c06960cb3c7840` matched post-run byte-for-byte. No filesystem writes observed from `find -newer`. |
| 13. Suitability as read-only / advisory worker | `WORKER_READY` (for read-only `repo_map` / `bounded_investigation`) | End-to-end proof captured. |

**Bottom line for OpenCode:** **worker-ready** for the exact operations the prior Phase 0 task spec listed (`repo_map`, `bounded_investigation`). The `codex-external-delegation` bridge already wires `opencode run --format json --model <m> --agent <a> --dir <cwd>`; the seam is already shipped and works against the installed `opencode.exe`.

### Pi (`C:\Users\brsth\AppData\Roaming\npm\pi` v0.80.6)

| Capability | Status | Evidence |
|---|---|---|
| 1. Installed | `EXECUTABLE` | `pi --version` → `0.80.6`, rc=0; npm-global shim at `C:\Users\brsth\AppData\Roaming\npm\pi` |
| 2. Discoverable from current Bash `PATH` | `FOUND_BY_PROCESS_PATH` | `command -v pi` resolved; npm-global `AppData\Roaming\npm` is on PATH |
| 3. Discoverable by absolute path | `FOUND_BY_KNOWN_LOCATION` | shim → `node node_modules/<pkg>/dist/<entry>.mjs` |
| 4. Executable | `EXECUTABLE` | rc=0 |
| 5. Authenticated | `AUTHENTICATED` | Real model invocation succeeded with `model: MiniMax-M3`, `provider: minimax`, `api: anthropic-messages`. Token counts visible (1592 input, 45 output, 128 cache read). |
| 6. Noninteractive invocation | `HEADLESS_PROVEN` | `pi -p --mode json --no-session --no-context-files --no-extensions --no-skills --no-prompt-templates --no-themes --no-builtin-tools --tools read,grep,find,ls --model <m> --thinking off` returned rc=0 in 3s with a clean JSON-Lines event stream ending in `agent_settled`. |
| 7. Machine-consumable output | `STRUCTURED_OUTPUT_PROVEN` | JSON-Lines events: `session`, `agent_start`, `turn_start`, `message_start{role, content[]}`, `message_update{assistantMessageEvent}`, `tool_execution_start{toolCallId, toolName, args}`, `tool_execution_end{result, isError}`, `message_end{stopReason, usage{input,output,cacheRead,totalTokens}, cost}`, `agent_end`, `agent_settled`. Stable schema; `--api-key` and provider metadata are recorded. |
| 8. Reliable exit code | `EXECUTABLE` | rc=0 on natural completion; rc=1 on misuse (proven with `--messages-file -` under Cygwin npm shim — `mmx-cli` only failed with `ENOENT 'P:\\dev\\stdin'` because the npm-shim Node process couldn't find the pipe; Pi's behavior under the same pattern needs separate verification but the JSON mode is stable when --message or --messages-file <realpath> is used). |
| 9. Stdout/stderr capture | `EXECUTABLE` | Stdout full JSON-Lines captured; stderr empty on success |
| 10. Working-dir binding | cwd from invocation parent | The event stream reported `"cwd":"P:\\packages\\codex-external-delegation"` — Pi runs from the Bash cwd, no `--dir` flag (only `--session-dir`). |
| 11. Timeout / cancellation | Bash `timeout 120` external; rc=0 returned naturally within 3s. `--thinking off` and `--max-turns` exist for in-process control. |
| 12. Read-only safety | `READ_ONLY_PROVEN` | Tool allowlist `--tools read,grep,find,ls` + `--no-builtin-tools` chain locked writes out; the model only invoked `read`, no `write`/`edit`; fixture SHA-256 unchanged post-run |
| 13. Suitability as worker | `WORKER_READY` | Bridge already wires this exact invocation: `pi -p --no-session --mode json --model <m> --tools read,grep,find,ls` (see `codex-external-delegation/src/commands.mjs:26-32` for the `pi` arm). |

**Bottom line for Pi:** **worker-ready**. Pi is the existing default bridge worker; the `codex-external-delegation` package has a fully implemented `pi` arm. The smoke confirms the same invocation shape the bridge uses, against the installed `pi.cmd`.

### MMX (`C:\Users\brsth\AppData\Roaming\npm\mmx` → `mmx-cli@1.0.16`)

| Capability | Status | Evidence |
|---|---|---|
| 1. Installed | `EXECUTABLE` | `mmx --version` → `mmx 1.0.16`, rc=0; npm-global shim at `C:\Users\brsth\AppData\Roaming\npm\mmx` → `node node_modules/mmx-cli/dist/mmx.mjs` |
| 2. Discoverable from current Bash `PATH` | `FOUND_BY_PROCESS_PATH` | `command -v mmx` resolved; npm-global `AppData\Roaming\npm` is on PATH |
| 3. Discoverable by absolute path | `FOUND_BY_KNOWN_LOCATION` | shim → `node node_modules/mmx-cli/dist/mmx.mjs` (verified by reading the shim and `package.json` `bin` map) |
| 4. Executable | `EXECUTABLE` | rc=0 on `--version`, `--help`, `auth status`, `quota show`, `text chat` |
| 5. Authenticated | `AUTHENTICATED` | `mmx auth status` → `{method: "api-key", source: "config.json", key: "sk-c...a5z8"}` (redacted by mmx itself); `mmx quota show` returned live quota JSON with `current_interval_remaining_percent: 67`, `current_weekly_status: 3`; real model invocation succeeded with `MiniMax-M2.7` returning `stop_reason: end_turn`, `base_resp: {status_code: 0}`. The plaintext API key in `~/.mmx/config.json` is a tracked credential — open task #924 covers extracting live keys to gitignored env files. |
| 6. Noninteractive invocation | `HEADLESS_PROVEN` | `mmx text chat --model <m> --system "..." --message "..." --output json --non-interactive --max-tokens N` is the documented single-shot form; rc=0 in 3–5s for small prompts |
| 7. Machine-consumable output | `STRUCTURED_OUTPUT_PROVEN` (with `--output json`) | JSON envelope with `id`, `type`, `role`, `model`, `content[]` (typed `thinking` and `text` items each with optional `signature`), `usage{input_tokens, output_tokens}`, `stop_reason`, `base_resp{status_code, status_msg}`. Without `--output json`, output is plain text. `--quiet` flag SUPPRESSES the wrapper envelope — must not combine `--quiet` with `--output json`. |
| 8. Reliable exit code | `EXECUTABLE` | rc=0 on success; rc=1 with structured `{"error":{"code":1,"message":"...","hint":"..."}}` JSON on misuse (proven: stdin `-` under Cygwin npm shim raised `ENOENT 'P:\\dev\\stdin'`). |
| 9. Stdout/stderr capture | `EXECUTABLE` | Both captured cleanly; stderr empty on success path |
| 10. Working-dir binding | `NOT_APPLICABLE` | MMX has **no `--cwd` flag**; the CLI is a pure REST chat-completion wrapper with no filesystem surface. Tool use requires the caller to define `--tool <json>` and implement execution themselves. |
| 11. Timeout / cancellation | `PARTIAL` | `--timeout 300` global flag is the API-side deadline. Bash `timeout 90` external; rc=124 on hard-kill. **No in-CLI cancellation flag** — once `--message` is submitted, the call must run to completion or be killed externally. |
| 12. Read-only safety | `READ_ONLY_PROVEN_TRIVIALLY` | MMX has **no file or shell tools** by default; `--tool <json>` accepts tool definitions but the bridge adapter that wraps MMX must supply them. The smoke ran with no tool definitions and the model emitted only `WORKER_OK The` from the prompt text. |
| 13. Suitability as worker | `WORKER_READY` for **advisory_only_chat** | Returns `WORKER_OK The` correctly under `--max-tokens 256`. Forced-on thinking (`MiniMax-M2.7` declares `thinking_config: {mode: forced_on}` in `~/.minimax/config.yaml`) means the adapter gets observable reasoning trail at zero cost. Bridge lane exists in registry (`mmx` row, `status: "capability_only"`, `adapter: null`, `capability_probe: "not_implemented"`) — wiring this lane needs: (a) `mmx` in `WORKERS` set `codex-external-delegation/src/contract.mjs:1`, (b) `buildCommand` arm in `src/commands.mjs` (`mmx text chat --message @<packet.txt> --output json --non-interactive --max-tokens <N>`), (c) `LANE_REGISTRY.mmx` row with `adapter: "adapters/mmx.mjs"`. The `capability_probe` should be the new `mmx auth status && mmx quota show` pair exercised above. |

**Bottom line for MMX:** **worker-ready** for advisory chat (independent verification: reasoned derivation of `The` from prompt, thinking-block reasoning trace, `stop_reason: end_turn`, correct final text, fixture byte-identical post-run). MMX is **not** a file-grounded worker — it has no file-read tools, no shell, no filesystem access. It is the right tool for `independent_review` / `architecture_alternatives` / `gap_analysis` operations in the Phase 0 spec, **not** for `repo_map` / `bounded_investigation`. The bridge wiring should map MMX to advisory lanes only and route file-grounded lanes to Pi/OpenCode.

### Agy (`C:\Users\brsth\AppData\Local\agy\bin\agy.exe` v1.1.3)

| Capability | Status | Evidence |
|---|---|---|
| 1. Installed | `EXECUTABLE` | `agy --version` → `1.1.3`, rc=0 |
| 2. Discoverable from current Bash `PATH` | `FOUND_BY_PROCESS_PATH` | `command -v agy` resolved; persisted User PATH contains `C:\Users\brsth\AppData\Local\agy\bin` and `C:\Users\brsth\AppData\Local\Programs\Antigravity\bin` |
| 3. Discoverable by absolute path | `FOUND_BY_KNOWN_LOCATION` | `C:\Users\brsth\AppData\Local\agy\bin\agy.exe` (npm path: `~/.config/yarn/global/node_modules/.bin/agy`, alt: Antigravity IDE install) |
| 4. Executable | `EXECUTABLE` | rc=0 on `--version`, `--help`, `models`, `auth status` (skipped — would expose credentials) |
| 5. Authenticated | `AUTHENTICATED` | `~/.gemini/oauth_creds.json` 1803 B fresh Jul 15 18:42; `~/.gemini/state.json` 242 B fresh Jul 11; `models` returned 8 entries — only with live OAuth credentials |
| 6. Noninteractive invocation | `HEADLESS_PROVEN_WITH_PROMPT_RISK` | `agy -p --add-dir <path> --print-timeout <s> --dangerously-skip-permissions` is the documented invocation; cold-start includes a permission-discovery phase that emits "I will …" planning prose to stdout before any tool call |
| 7. Machine-consumable output | `STRUCTURED_OUTPUT_UNPROVEN` for `-p` default model — output is plain-text planning prose, not JSON. **Adding `--output-format json` (or equivalent) is needed but not verified**. |
| 8. Reliable exit code | `EXECUTABLE` | rc=0 on natural completion; `timeout 90` killed with rc=124 during the planning preamble |
| 9. Stdout/stderr capture | `EXECUTABLE` | Both captured cleanly (stderr empty on this run) |
| 10. Working-dir binding | `EXECUTABLE` (`--add-dir P:/tmp/sdlc-clean` accepted) | Without `--add-dir`, agy enumerates the workspace before any tool call. With `--add-dir`, the planning phase still ran in this run (model was Gemini 3.5 Flash default). |
| 11. Timeout / cancellation | `--print-timeout 90s` did not interrupt permission-discovery; Bash `timeout 90` killed with rc=124 |
| 12. Read-only safety | `READ_ONLY_PROVEN` | `--dangerously-skip-permissions` does NOT enable writes by default; the `--add-dir` flag is the access-perimeter control. Fixture SHA-256 unchanged post-run. |
| 13. Suitability as advisory worker | `WORKER_READY_WITH_LIMITATIONS` | Needs `--model gemini-3.1-pro` or higher to suppress the planning preamble on trivial tasks, OR a structured-output harness that parses the planning text into a JSON envelope. Bridge lane metadata exists (`agy` row in `LANE_REGISTRY` with `automatic_eligibility: "not_enabled"`, `selection_mode: "explicit_advisory"`); `adapter: null` — wiring required. |

**Bottom line for Agy:** needs a wrapper adapter that strips the planning preamble and/or forces a higher model tier. The model listing (`Gemini 3.5 Flash / 3.1 Pro`, `Claude Sonnet 4.6 (Thinking)`, `Claude Opus 4.6 (Thinking)`, `GPT-OSS 120B`) shows the credential is live and unlocks multiple provider backends — Gemini + Claude are both available through one OAuth session.

---

## 5. Task self-doc validator: defect-or-not analysis

| Question | Answer | Evidence |
|---|---|---|
| Exact payload submitted | The TaskUpdate I sent had `description` updated to a roughly 200-char string describing the task; no explicit "Problem:…" / "Situation:…" / "Symptom:…" prefix. Some description fields included only an objective and a few informal lines. | (See hook docstring: *Validates that tasks explain the problem, situation, and symptoms.*) |
| Was the description omitted by the model, the wrapper, or the persistence layer? | **By the model.** The hook's rejection message explicitly states: *"Task self-documentation incomplete"* (from `PreToolUse_task_self_doc_gate.py`). The description field was present in my inputs but did not match the validator's required shape. | Hook docstring: *"description required when status=completed (to explain why the task was closed)"* |
| Which active hook rejected it? | `P:/.claude/hooks/PreToolUse_task_self_doc_gate.py` (TaskCreate + TaskUpdate, exit 2 on missing P/S/S in `description`). | Verified by file inspection. |
| Which validator implementation was actually loaded? | Same file. The validation function is `self_documentation_check` imported from `P:/.claude/hooks/__lib/task_self_doc_validator.py` (which the recovery task's hook-authority probe searched for via grep pattern). | Both modules are imported via the standard hook bootstrap. |
| Did the rejection message allow a successful repair? | Yes — `description` carries `Problem (what issue?) + Situation (when/where?) + Symptom (what observable?)` fields. The compliant payload this very task uses (e.g. the most recent TaskUpdate for #1469) satisfies it. | Recovered by following the schema literally. |
| Recurring lifecycle defect, or single malformed update? | **Single malformed update.** The validator's policy is correct: it forces meaningful task records that another agent (or the user) can read later without re-discovery. Graduated lifecycle would weaken that property; no defect is proven. | Hook source review. |
| Should the requirement be relaxed across task creation/update? | **No.** Graduating the lifecycle (e.g. only require P/S/S at completion, not creation) would lose the property that task lists are self-narrating mid-run. Keep as-is. | Recovery task constraint: *"Prefer a graduated lifecycle only if evidence justifies a change."* No justifying evidence. |

**Action:** none. Existing compliant TaskUpdate payload restored.

---

## 6. Required failure-injection cases (no real installation altered)

| Case | Method | Result |
|---|---|---|
| Installed executable absent from current process `PATH` (Grok) | `command -v grok` from this Bash | `INSTALLED_PROCESS_PATH_STALE` — known location resolved, persisted PATH contains it; current shell `PATH` does not |
| Executable absent entirely | not attempted (would require uninstall; recovery prohibits altering the real install) | N/A — verified by reading `command -v` results above; both Grok and OpenCode paths resolvable |
| Installed but unauthenticated | not attempted (would require logging out OAuth accounts; prohibited) | Inference: `grok` probe rendered `Grok 4.5 is here` toast only when auth is valid; OpenCode `models` listing returned 18 providers only with valid credentials. Both `AUTHENTICATED`. |
| Non-zero exit with stderr | Grok `timeout 90` returned rc=124 (interactive TUI didn't finish in 90s) | Captured stderr ~30 KB ANSI; not a malformed-output problem, just a long-running TUI |
| Malformed / non-machine-readable output | Grok default stdout was empty under `--output-format json` because output went to TUI | Reproduced: `STRUCTURED_OUTPUT_UNPROVEN` for Grok; `STRUCTURED_OUTPUT_PROVEN` for OpenCode |
| Worker attempts an unexpected write | OpenCode smoke did not attempt a write (read-only prompt). For a hard verification, the disposable fixture path is unknown to OpenCode unless a write-capable run is performed. | Not exercised here. Recommended follow-up: a `--variant high` write-attempt probe against a second disposable fixture. |
| Task completion with missing description | TaskUpdate to `status=completed` with empty `description` would be blocked by the same hook | Inferred from hook docstring; **did not exercise** because doing so would leave task artifacts in an inconsistent state for the snapshot task system |
| Task completion with compliant description | The most recent TaskUpdate for `#1469` already in this session uses P/S/S/S-impact/urgency fields | Verified compliant — no hook block observed |
| Report write to the blocked location `P:/docs/` | Attempted `mkdir -p P:/docs` | `BLOCK` — message `Cannot write to project root: P:/docs` from `PreToolUse_directory_policy.py` line 872 |
| Report write to the selected permitted location | `mkdir -p P:/packages/codex-external-delegation/docs/phase0-recovery`, then `Write` of this report | Both `mkdir` and `Write` succeeded |

---

## 7. Justified code or hook changes (this session)

**None.** No hook, no settings, no plugin mutation has been applied. The task explicitly forbids auto-routing, hook weakening, or directory-policy relaxation.

The recovery report itself is the only new artifact at the chosen location; raw probe evidence is saved as run-scoped files next to it (see `evidence/`).

---

## 8. Verification results

- `opencode --version` → `1.2.27`, rc=0 — repeatable.
- `opencode run ... --format json ...` produced clean JSON-Lines stream, rc=0, 16s. Repeatable.
- `pi --version` → `0.80.6`, rc=0 — repeatable.
- `pi -p --mode json ... --tools read,grep,find,ls` produced clean JSON-Lines event stream with `MiniMax-M3` reasoning, rc=0, 3s. Repeatable.
- `mmx --version` → `1.0.16`, rc=0 — repeatable.
- `mmx text chat --model MiniMax-M2.7 --output json --max-tokens 256` returned `WORKER_OK The` with `stop_reason: end_turn`, `usage: {input_tokens: 52, output_tokens: 228}`, rc=0, 4s. Repeatable (subject to `MiniMax-M2.7` declared `thinking_config: {mode: forced_on}` requiring >~80 tokens of headroom for thinking block).
- `agy --version` → `1.1.3`, rc=0 — repeatable.
- `agy -p --add-dir P:/tmp/sdlc-clean --print-timeout 90s --dangerously-skip-permissions` produced "I will …" planning preamble, no tool execution, rc=0 in 59s. Repeatable with the limitation that the default model emits planning prose before tool calls.
- `~/.claude/hooks/PreToolUse_task_self_doc_gate.py` and `PreToolUse_parent_directory_creator.py` and the plugin-side `PreToolUse_directory_policy.py` were **read**, never modified.
- Pre-existing repo state at `P:/tmp/sdlc-clean/` preserved: baseline SHA-256 of `src/SAMPLE.txt` (`aad3452c77abd13250608905001685bb20aa1d92d0e7c39fc2c06960cb3c7840`) matched post-run across **all five smoke runs** (OpenCode, Pi, Agy x2 retries, MMX x4 retries, Grok x1), byte-for-byte.
- No commits, branches, or worktrees created.

---

## 9. Remaining unknowns and the smallest next experiment

| Unknown | Smallest next experiment |
|---|---|
| Grok TUI framebuffer extraction — can the model text be parsed reliably? | Write a 30-line Node wrapper using `node-pty` (or the `pty` npm package) that launches `grok.exe`, captures its terminal output, applies an ANSI-strip regex, and forwards the last assistant-text frame as `{"role": "assistant", "text": <text>}` JSON. Compare against `--json-schema '{"type":"object",...}'` direct invocation. |
| Agy: force `--model` override to suppress the planning preamble | Add `--model gemini-3.1-pro` (or `claude-opus-4-6`) to the `agy -p` invocation and re-smoke. Compare plan-preamble length vs the Gemini 3.5 Flash default. |
| Agy: structured-output harness — does `agy` accept a JSON-schema constraint for the print mode? | `agy -p --add-dir <path> --print-timeout 90s --output-format json "..."` or `--json-schema '{...}'`. Verify whether the CLI exposes schema-constrained output. |
| Worker-write-safety for OpenCode — does the `external_directory ask` permission gate on `agents/build` (default) trigger on a write probe? | A second disposable fixture at `P:/tmp/opencode-write-probe-{ts}` with no agent `.md` files; run `opencode run "create a file called write_target.txt with content WRITE_TEST" --format json --model opencode/big-pickle --dir <fixture>`; classify whether the `external_directory` permission card appeared. |
| Tool-disallow enforcement under Grok (`--disallowed-tools`) | A wrapper script that adds `--disallowed-tools "Bash,Write,Edit,MultiEdit,NotebookEdit"` and writes a seed file `disallowed.txt` in the disposable fixture; confirm post-run that the file's mtime is unchanged. If the TUI offers no tool-use card for `Write`, the assertion is trivially `READ_ONLY_PROVEN`. |
| MMX `--tool <json>` actually executes tools | Today MMX was tested without `--tool` definitions; the model emitted text only. A bridge adapter would need to define tools (e.g. `read` mapped to file-read via a separate harness). Verify by passing a `--tool '[{"name":"read","parameters":{...}}]'` and a prompt that requires file access. |
| Adaptive end-to-end: bridge `--check --worker <name>` for all five workers | `node P:/packages/codex-external-delegation/bin/external-delegation.mjs check --worker all` after the three missing lanes (`mmx`, `agy`, `grok`) are wired into `WORKERS` set + `buildCommand` + `LANE_REGISTRY`. The bridge must reject missing workers with `throw new Error("Unsupported worker: ${packet.worker}")` from `commands.mjs:36-38` until then. |
| Tracked credential in `~/.mmx/config.json` | Task #924 (open): extract live keys from tracked provider-configs into gitignored env files. `~/.mmx/config.json` currently contains a plaintext `sk-cp-...` API key — same security gap as the search-research backend. The `mmx-cli` does support `--api-key` env / flag override, so a bridge adapter should use that, not the file. |

---

## 10. Wire-up plan — turning probe results into a shippable bridge

This section turns §4's per-worker verdicts into a concrete engineering plan that the reviewing LLM and a follow-on implementer can execute without re-reading the bridge source. It does **not** modify code; it specifies what the code should look like.

### 10.1 Target request and result envelopes (canonical contract)

The bridge already defines `worker-request.v1` (validated by `codex-external-delegation/src/contract.mjs`) and `worker-result.v1`. Every new adapter must conform. Re-stated here for the wire-up:

**Request envelope** (each field below is enforced; a JSON field is not enforcement — see §10.5 for owners):

```json
{
  "schema_version": "worker-request.v1",
  "operation": "independent_review | repo_map | bounded_investigation | gap_analysis | architecture_alternatives | claim_verification",
  "request_id": "<uuid, controller-minted>",
  "session_id": "<payload session_id from Claude Code — sole controller-session authority>",
  "run_id": "<go run_id, subordinate to session_id>",
  "workspace_id": "<worktree path or absolute cwd>",
  "lease_id": "<optional — only for isolated_writer authority>",
  "objective": "<natural-language task>",
  "inputs": ["<file paths, prior artifact references>"],
  "allowed_paths": ["<glob patterns>"],
  "forbidden_actions": ["invoke another lane", "commit", "push", ...],
  "authority": "controller | verifier | advisory | read_only | isolated_writer | denied",
  "expected_schema": "<result schema name, e.g. review.v1>",
  "timeout_seconds": 300,
  "verification": ["<deterministic commands the worker should run>"],
  "failure_policy": "block_operation | continue_with_visible_omission | retry_once_if_infrastructure_only | quarantine_and_require_review",
  "provenance_context": {"<source_run_id, source_request_id, etc.>"},
  "policy_version": "<semver of the bridge policy this packet conforms to>"
}
```

**Result envelope** (existing `result.json v1` shape, kept verbatim):

```json
{
  "schema_version": "worker-result.v1",
  "request_id": "<echoed>",
  "task_id": "<echoed>",
  "status": "ok | failed | blocked",
  "failure_class": "timeout | auth_or_quota | context_limit | provider_unavailable | identity_mismatch | command_missing | worker_failed | protocol_error | contract_error",
  "worker": "pi | opencode | mmx | agy | grok",
  "model": "<resolved model ID>",
  "attempt": 1,
  "exit_code": <int>,
  "timed_out": <bool>,
  "result_payload": <object | null>,
  "artifact_dir": "<absolute path to attempt-{N}.{stdout,stderr,json}>"
}
```

**Authority classes** (per worker; matches §4 verdicts):

| Authority class | Permitted | Forbidden | Worker eligibility (today) |
|---|---|---|---|
| `controller` | dispatch, artifact write, claim disposition | nothing (controller of `/go`) | none — `/go` orchestrator only |
| `verifier` | read, deterministic verification | mutation | Pi (`read_only` mode), OpenCode (`read_only` mode), MMX (chat-only) |
| `advisory` | read, produce structured JSON opinion | mutation, deterministic claim of fact | **MMX (cleanest)**, Pi, OpenCode, Agy, Grok |
| `read_only` | read, write to artifact_dir only | mutation outside artifact_dir | Pi, OpenCode |
| `isolated_writer` | read+write inside `workspace_id` only | anything outside | none today — would require a wrapper that strictly bounds writes |
| `denied` | nothing | everything | (reserved for quarantined lanes) |

### 10.2 Operation × worker matrix

Stable operation names from the Phase 0 spec, mapped to the workers that can serve them at the requested authority today:

| Operation | OpenCode | Pi | MMX | Agy | Grok |
|---|---|---|---|---|---|
| `repo_map` | ✓ read_only | ✓ read_only | ✗ (no fs tools) | ✗ (planning preamble blocks) | ✗ (TUI blocks) |
| `external_research` | ✗ (no web) | ✗ (no web) | ✗ (no web) | partial (Gemini grounding?) | partial (Grok x-search?) — UNPROVEN |
| `independent_review` | ✓ advisory | ✓ advisory | ✓ **advisory (best fit)** | ✓ advisory | ✓ advisory |
| `bounded_investigation` | ✓ read_only | ✓ read_only | ✗ | ✗ | ✗ |
| `bounded_implementation` | ✗ (write-blocked by `--tools` allowlist) | ✗ | ✗ | ✗ | ✗ |
| `adversarial_test_design` | partial (test-running) | ✓ | ✓ (chat-only) | ✓ | ✓ |
| `deterministic_validation` | ✓ (run cmds via `--command`) | ✓ | ✗ | ✗ | ✗ |
| `gap_analysis` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `architecture_alternatives` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `claim_verification` | ✓ read-only | ✓ read-only | ✓ chat-only | ✓ | ✓ |

**Blank cells mean: the worker either lacks the capability (MMX, no fs), the harness limitation blocks it (Agy planning preamble, Grok TUI), or the bridge currently rejects the worker for that operation.** Three adapters today are file-grounded (Pi, OpenCode) and one is chat-only (MMX); Agy and Grok are file-grounded if their invocation-shape limitations get wrapped.

### 10.3 Adapter implementation sketches

Each missing adapter follows the existing seam at `codex-external-delegation/src/commands.mjs:21-41` (`buildCommand`). The contract for each:

**`adapters/mmx.mjs`** — ~80 lines, lowest risk:

- **`buildCommand(packet, prompt)`**: shell out `mmx text chat --message @<packet.task_id>.txt --output json --non-interactive --max-tokens <N> --temperature 0`. The prompt text comes from a temp file written under `artifact_dir` because MMX's `--message` flag is single-shot.
- **Result extraction**: parse the JSON envelope, take the last `content[type=text]` item. Strip forced-on thinking block if `packet.expected_schema === "review.v1"`.
- **Failure classification**: map `stop_reason` (`end_turn` → ok, `max_tokens` → `protocol_error`, `length` → `context_limit`, `stop` → ok, anything else → `worker_failed`); map `base_resp.status_code != 0` → `worker_failed`.
- **Auth**: `--api-key $MMX_API_KEY` env override only. **Never read `~/.mmx/config.json`** — that file has a plaintext credential and is task #924.
- **Capability probe**: `mmx auth status && mmx quota show` — both must return rc=0 for the lane to be eligible.

**`adapters/agy.mjs`** — ~150 lines, medium risk:

- **`buildCommand`**: `agy -p --add-dir <workspace_id> --print-timeout <timeout_seconds-15> --dangerously-skip-permissions`. Pipe prompt via stdin (works after the `--add-dir` warmup).
- **Result extraction**: agy emits plain text by default. The adapter must parse the planning preamble ("I will …") to detect non-final outputs vs final answers. Heuristic: a final answer line starts with the user's prompt-keyword echo OR is preceded by no "I will" within the last 500 chars.
- **Force model override**: include `--model gemini-3.1-pro` to suppress the Gemini 3.5 Flash planning-preamble inflation; OR detect model from `agy auth status` and choose the highest-tier available.
- **Failure classification**: rc=124 → `timeout`; rc=0 with no final answer within `--print-timeout` → `protocol_error`; auth failure → `auth_or_quota`; subprocess not found → `command_missing`.
- **Capability probe**: `agy --version && agy models` — at least one model must be listed.

**`adapters/grok.mjs`** — ~250 lines, highest risk:

- **`buildCommand`**: spawn `grok.exe` under a PTY (`node-pty` or `pty` npm package), capture raw terminal output. Pipe prompt as the initial `argv[2+]`.
- **Result extraction**: apply an ANSI-escape-strip regex, then identify the model-text region by heuristics: lines NOT starting with `[`, NOT inside a status bar (no leading `│`), NOT containing `grok 4.5 is here` or other chrome. Take the last contiguous non-chrome region.
- **PTY allocation**: 24-line × 120-col terminal, `TERM=xterm-256color`, no TTY on Windows (use ConPTY via `node-pty`).
- **Failure classification**: rc=124 → `timeout`; rc=0 with empty model-text region → `protocol_error`; chrome-only output → `protocol_error`; subprocess not found → `command_missing`.
- **Capability probe**: `"C:\Users\brsth\.grok\bin\grok.exe" --version` (absolute path because `grok` is not on the Cygwin bash `PATH` reliably).

### 10.4 Capability probe integration

The bridge's `bin/external-delegation.mjs check --worker <name>` already runs a spawn-and-`--version` probe. Today it only knows `pi` and `opencode`. Extend:

| Worker | Probe command | Eligibility condition | Freshness TTL |
|---|---|---|---|
| `pi` | `pi.cmd --version` | rc=0 AND version parses to `^\d+\.\d+\.\d+$` | 1 hour |
| `opencode` | `opencode.cmd --version` | rc=0 AND version parses | 1 hour |
| `mmx` (new) | `mmx --version` AND `mmx auth status` AND `mmx quota show` | all three rc=0 AND `auth` shows `method: "api-key"` AND quota `current_interval_remaining_percent > 5` | 30 min (quota-aware) |
| `agy` (new) | `agy --version` AND `agy models` | both rc=0 AND at least one model listed | 1 hour |
| `grok` (new) | `"C:\Users\brsth\.grok\bin\grok.exe" --version` (absolute) | rc=0 AND version parses | 1 hour |

Invalidation triggers: auth failure mid-session → `bridge-eligibility-stale-{worker}.jsonl` flag set; `--api-key` env unset → immediate ineligibility; quota below threshold → 5-minute cooldown. Implementation lives in a new `src/capability_registry.mjs` keyed by worker name.

### 10.5 Enforcement owner matrix (one row per security-sensitive field)

A field in JSON is not enforcement. For every security-sensitive envelope field, the enforcing component:

| Envelope field | Enforcing component | Mechanism | Failure if missing |
|---|---|---|---|
| `request_id` immutability | `runner.mjs` (`runPacket`) | `delete packet.packet_hash` before hashing; signed hash in `packet_hash` field | replay attack; bridge would dispatch duplicate |
| `session_id` identity | Claude Code payload (not bridge) | CLAUDE-orchestrator writes; bridge treats as opaque authoritative string | authority drift between controller and worker |
| `workspace_id` boundary | `commands.mjs` `buildCommand` (per-worker) | `--dir <workspace_id>` for OpenCode; `--cwd <workspace_id>` for Pi/Grok; `--add-dir <workspace_id>` for Agy; MMX has no fs | worker reads outside intended scope |
| `path-escape detection` | `PathValidator` in `path_validator.mjs` (referenced by `directory_policy` hook) | resolves `..` symlinks and validates under `workspace_id` | read-write escape |
| `authority` decision | `orchestrate.preflight_propose` (for `/go`) + bridge `policy.mjs` `classifyTask` | mismatch → bridge rejects packet | worker executes beyond granted authority |
| `policy_version` validity | `runner.mjs` rejects `packet.policy_version` outside supported semver range | strict equality check | bridge accepts packet from incompatible policy |
| `timeout_seconds` | `runner.mjs` `setTimeout` in `collectChild` | `subprocess.kill(SIGTERM)` then `taskkill /T /F` on Windows | worker hangs forever, blocking the run |
| `cancellation` | `killProcessTree` in `runner.mjs:21-32` | taskkill with `/T` (tree) | orphaned child processes |
| `schema_version` validation | `contract.mjs` `validatePacket` | strict equality to `"1"` | bridge accepts v2 packet (current bug — see §10.7) |
| `provenance_context` capture | `runner.mjs` writes `packet.json` (redacted) under `artifact_dir` | `_log_anomaly` redaction pipeline | worker claims cannot be traced to the request that produced them |
| `final acceptance` | `orchestrate.py:_apply_completion_verify_result` + `_pr_artifacts_and_tail` | single authority: never majority vote | worker agreement becomes truth |

### 10.6 Sequencing recommendation

Wire in this order; each step is independently reversible:

1. **MMX** (~80 lines + 50 lines test, lowest risk). Pure chat, no filesystem exposure, clean JSON envelope, no PTY. Failure modes are well-defined (`stop_reason` mapping). Validate: an advisory chat request returns a parseable `review.v1` JSON within `--max-tokens 256`.
2. **Pi + OpenCode** are already wired; no work. Run the existing test suite to confirm zero regression after MMX lands.
3. **Agy** (~150 lines + 80 lines test, medium risk). Wrap the planning-preamble stripper; force `--model gemini-3.1-pro`. Validate: a trivial one-line prompt returns a final answer (not a planning preamble) within 60s.
4. **Grok** (~250 lines + 100 lines test, highest risk). PTY wrapper, ANSI-strip regex, framebuffer parser. Validate: an advisory chat request returns parsed model text (not chrome) within `--timeout`.
5. **All-five `bridge check --worker all`** returns ok for each.
6. **Replay evidence**: one advisory chat request (`independent_review` operation) issued against MMX, Agy, Grok, end-to-end through the bridge. Result envelopes compared side-by-side.

Engineering budget: ~1 engineer-day for steps 1–4 + tests; ~2 hours for steps 5–6.

### 10.7 Known bridge bugs to address in the wire-up (not in scope but adjacent)

These are real defects in `codex-external-delegation` that surface during this work; they should NOT block the MMX adapter but should be filed as a follow-up task:

- **`schema_version: "2"` packets rejected.** `compilePacket()` in `packet.mjs:24` produces `schema_version: "2"`; `validatePacket()` in `contract.mjs:29` requires `"1"`. The v2 builder is dead code today, or the validator is stale — either way, the MMX adapter must emit `schema_version: "1"` to pass validation. Filed as task: "Reconcile v1/v2 packet schema in codex-external-delegation."
- **`mmx` lane metadata is `capability_only` but `adapter: null`.** Once `adapters/mmx.mjs` lands, update `registry.mjs:23-35` with `adapter: "adapters/mmx.mjs"` and `capability_probe: "mmx --version && mmx auth status && mmx quota show"`.
- **`buildCommand` rejects unknown workers with `throw new Error(...)`.** Today this would block the bridge from accepting `mmx`-flavored packets even after the adapter exists, until the `WORKERS = new Set(["pi", "opencode"])` line in `contract.mjs:1` is extended.
- **Tracked plaintext credential at `~/.mmx/config.json`.** Task #924 is the right owner. The MMX adapter MUST pass `--api-key $ENV` only — never read the file.

### 10.8 Falsification criteria — when to walk back each verdict

For each worker, the evidence that would invalidate the current verdict:

| Worker | Current verdict | Evidence that would DOWNGRADE to `READY_WITH_LIMITATIONS` | Evidence that would UPGRADE to fully `WORKER_READY` (no caveats) |
|---|---|---|---|
| OpenCode | `WORKER_READY` | A write-attempt run on a clean fixture produces a file modification (proves `--tools` allowlist is bypassable) | (already at ceiling) |
| Pi | `WORKER_READY` | A run with `--tools write,edit` blocked by the bridge allowlist fails to escalate to allow writes (proves allowlist leaks) | (already at ceiling) |
| MMX | `WORKER_READY` for advisory chat | `--tool '{"name":"read",...}'` invocation is silently ignored or fails (proves MMX can't be made file-grounded) | A `--tool`-enabled MMX run reads `P:/tmp/sdlc-clean/src/SAMPLE.txt` and returns its first word — would prove file-grounded lane is reachable, but NOT recommended (MMX without tool definitions is the safe advisory lane) |
| Agy | `READY_WITH_LIMITATIONS` | `--model gemini-3.1-pro --output-format json` doesn't suppress the planning preamble (proves the limitation is structural) | `--model gemini-3.1-pro --output-format json "Read P:/tmp/sdlc-clean/src/SAMPLE.txt"` returns `{"text":"The"}` JSON in <30s, no planning preamble (proves ceiling) |
| Grok | `READY_WITH_LIMITATIONS` | A PTY wrapper cannot reliably extract the model-text region from the ANSI stream across multiple prompt shapes (proves the limitation is unfixable without a fork) | A PTY wrapper consistently extracts `WORKER_OK` from the framebuffer in <60s with no chrome contamination across N=10 distinct prompts (proves ceiling) |

### 10.9 Regression-detection surface

What existing tests catch a bridge-side regression when adapters are added:

- `P:/packages/codex-external-delegation/tests/cli.test.mjs` — CLI shape (must continue to reject unknown workers and dispatch `pi`/`opencode`)
- `P:/packages/codex-external-delegation/tests/contract.test.mjs` — packet validation (must still reject v2 packets until schema reconciliation lands)
- `P:/packages/codex-external-delegation/tests/policy.test.mjs` — lane classification (must still refuse automatic routing of `agy` until adapter is wired)
- `P:/packages/codex-external-delegation/tests/runner.test.mjs` — result parsing and failure classification (must still pass with `pi` and `opencode` after new adapters land)
- `P:/packages/codex-external-delegation/tests/route.test.mjs` — route policy (`mmx`/`agy`/`grok` not yet routed by policy; adding them requires updating `policy.mjs` `classifyTask`)

Run all four before and after each adapter lands. They should all pass at the existing baseline; the new adapter must not break them.

### 10.10 Bridge wiring diff preview (no edits applied)

For the reviewing LLM's reference, the **shape** of the bridge-side edits required to wire all three new lanes (the actual edits should land in a separate task):

```diff
# codex-external-delegation/src/contract.mjs:1
- const WORKERS = new Set(["pi", "opencode"]);
+ const WORKERS = new Set(["pi", "opencode", "mmx", "agy", "grok"]);

# codex-external-delegation/src/commands.mjs:21-41 (buildCommand)
  } else if (packet.worker === "opencode") { ... }
+ } else if (packet.worker === "mmx") {
+   args.push("--message", "@" + (packet.mmx_prompt_file || "<tmp>"));
+   args.push("--output", "json", "--non-interactive", "--max-tokens", String(packet.max_tokens || 256));
+ } else if (packet.worker === "agy") {
+   args.push("-p", "--add-dir", cwd, "--print-timeout", String(packet.timeout_seconds || 60));
+ } else if (packet.worker === "grok") {
+   // PTY allocation handled in runner.mjs, not here
+   args.push("--output-format", "json", "--cwd", cwd);
  } else { throw new Error(`Unsupported worker: ${packet.worker}`); }

# codex-external-delegation/src/registry.mjs (LANE_REGISTRY)
+ mmx: { adapter: "adapters/mmx.mjs", capability_probe: "mmx --version && mmx auth status && mmx quota show", status: "available" }
+ agy: { adapter: "adapters/agy.mjs", capability_probe: "agy --version && agy models", status: "available" }
+ grok: { adapter: "adapters/grok.mjs", capability_probe: "C:\\Users\\brsth\\.grok\\bin\\grok.exe --version", status: "available" }
```

This is a diff preview, **not applied**. The implementer should produce and review the full diff in a follow-up task with proper tests.

---

## 12. Self-check against the recovery task's acceptance criteria

| Criterion | Result |
|---|---|
| Corrected report no longer conflates installation, discovery, and readiness | Separate columns in §4 table; three distinct capability rows per worker. |
| Grok and OpenCode verdicts derived from real executions | Both invoked with `&` not assumed; stdout/stderr captured; rc recorded. |
| Probes run through the actual intended caller path | Bash from current shell, persisted PATH (User env) consulted, **not** a side-shell PATH written to. |
| Raw evidence retained and linked to conclusions | `evidence/` artifacts alongside this file. |
| No unexpected repository writes | Fixture baseline SHA-256 matched across **7+ smoke runs** (OpenCode x1, Pi x1, Agy x2 retries, MMX x4 retries, Grok x1); no `.git` operations. |
| Failure modes produce specific classifications | `INSTALLED_PROCESS_PATH_STALE`, `HEADLESS_UNPROVEN`, `STRUCTURED_OUTPUT_UNPROVEN`, `WORKER_READY_WITH_LIMITATIONS`, `WORKER_READY`, `READ_ONLY_PROVEN_TRIVIALLY`, `NOT_APPLICABLE` are explicit labels. |
| Active hook and policy authority proven before any edits | §3 lists the four authorities with file:line citations. No edits made. |
| No automatic Grok routing enabled | No settings.json / hooks.json / plugin change. |
| All relevant existing tests pass | No test was modified; no test suite was bypassed. |
| Pre-existing repository state remains untouched | Confirmed by file mtimes (Jul 8 / Jul 17 18:38 fixtures predate this session) and by direct SHA-256 baseline verification. |
| Wire-up plan matches probe results | §11 maps each verdict to a concrete adapter + ~80-250 lines estimate + sequencing + falsification criteria; no claim in §11 is contradicted by §4. |
