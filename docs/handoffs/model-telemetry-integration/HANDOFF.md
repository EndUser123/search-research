# Handoff: Telemetry integration into dispatch skills

**Created:** 2026-07-24
**Session:** 019f91d3-2741-7f83-af68-211796180474
**Author:** grok
**Status:** Ready for fresh cold start LLM

## Objective

Integrate the `/model-benchmark` telemetry library (`telemetry.py`) into the
fleet's dispatch skills so every `spawn_subagent` and direct API call is logged
to `P:/.artifacts/model-telemetry/usage.jsonl`. This provides the live-usage
data needed for dynamic model selection per the policy at
`P:/.data/wiki/concepts/model-pool-selection-policy-speed-quota-diversity.md`.

## Background

The `/model-benchmark` skill was built this session with three scripts:
- `~/.grok/skills/model-benchmark/scripts/benchmark.py` — one-shot latency benchmark
- `~/.grok/skills/model-benchmark/scripts/telemetry.py` — shared logging library
- `~/.grok/skills/model-benchmark/scripts/analyze.py` — telemetry analysis

The telemetry library exposes `log_call()` and `log_spawn()`. Each skill needs
exactly one import + one `log_spawn()` call per `spawn_subagent` dispatch point.

## Scope (7 skills to integrate)

### Priority 1 — Highest signal (verifiers and dispatchers)

| Skill | File | What to wrap | task_domain tag |
|---|---|---|---|
| `/check` | `P:/.grok/skills/check/SKILL.md` (Step 3 spawn) | Each verifier `spawn_subagent` call | `code-verification` |
| `/go` | `~/.grok/skills/go/SKILL.md` (Step 3 H4 wave) | Each implementation/test/critic subagent | `code-generation` / `mechanical` / `adversarial` |
| `/review` | `~/.grok/skills/review/SKILL.md` | Each specialist subagent | `adversarial` |

### Priority 2 — Research and discovery

| Skill | File | What to wrap | task_domain tag |
|---|---|---|---|
| `/www` | `~/.grok/skills/www/SKILL.md` | Research subagent spawns | `mechanical` (extraction) |
| `/web` | `~/.grok/skills/web/SKILL.md` | Search dispatch + result synthesis | `mechanical` |
| `/wiki` | `~/.grok/skills/wiki/SKILL.md` | Query subagents (if spawned) | `mechanical` |
| `/preflight` | `P:/.agents/skills/preflight/SKILL.md` | Discovery subagents | `mechanical` |

### Priority 3 — Direct API scripts (already partially done)

| Script | Status | What to add |
|---|---|---|
| `P:/.agents/scripts/models/dgemma_read.py` | Already logs to console | Add `log_call()` with `task_domain="extraction"` |
| Any future `extract.py` | Not yet built | Include `log_call()` from the start |

## Integration pattern (per skill)

For each skill, the change is mechanical:

1. **Import the telemetry library at the top of the spawn section:**
```python
import sys
sys.path.insert(0, r"C:\Users\brsth\.grok\skills\model-benchmark\scripts")
from telemetry import log_spawn
```

2. **Wrap each `spawn_subagent` call with timing + logging:**
```python
import time
start = time.monotonic()
result = spawn_subagent(
    description="Verify: ...",
    subagent_type="general-purpose",
    model="zen-deepseek-v4-flash-free",  # or whatever model
    ...
)
elapsed = (time.monotonic() - start) * 1000
log_spawn(
    model="zen-deepseek-v4-flash-free",
    task_domain="code-verification",
    latency_ms=elapsed,
    success=True,  # or False if the verifier returned FAIL/error
    caller="/check verifier",
)
```

3. **For skills that are SKILL.md-only (no Python):** add a note in the skill
   instructing the orchestrating LLM to call `log_spawn()` after each
   `spawn_subagent` returns. The LLM can run it via `run_terminal_command`:

```powershell
python -c "import sys; sys.path.insert(0, r'C:\Users\brsth\.grok\skills\model-benchmark\scripts'); from telemetry import log_spawn; log_spawn(model='zen-deepseek-v4-flash-free', task_domain='code-verification', latency_ms=1234, success=True, caller='/check')"
```

## Acceptance criteria

- [ ] All 7 Priority 1+2 skills have telemetry integration
- [ ] `/check` verifier spawns are logged with `task_domain="code-verification"`
- [ ] `/go` H4 wave spawns are logged with appropriate domain tags
- [ ] `/review` specialist spawns are logged with `task_domain="adversarial"`
- [ ] `P:/.artifacts/model-telemetry/usage.jsonl` accumulates entries from real usage
- [ ] `python analyze.py` produces non-empty per-model stats after 1 day of usage

## Constraints

- Do NOT change model selection logic in the skills — only add telemetry logging
- Do NOT break existing skill behavior — telemetry is additive, best-effort
- If `telemetry.py` import fails (path issue), the skill must continue working
  (wrap in try/except, log a warning, move on)
- Do NOT log file contents, prompts, or responses — only metadata (model,
  domain, latency, success, token counts)

## Related

- Policy: `P:/.data/wiki/concepts/model-pool-selection-policy-speed-quota-diversity.md`
- Firewall architecture: `P:/.data/wiki/concepts/context-firewall-architecture.md`
- Benchmark skill: `~/.grok/skills/model-benchmark/SKILL.md`
- Telemetry library: `~/.grok/skills/model-benchmark/scripts/telemetry.py`
