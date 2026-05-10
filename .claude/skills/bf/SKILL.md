---
name: bf
description: >
  Bifrost workbench — direct Python import of bf_agent library.
  Routes to bf_agent.run_simple() for stateless modes, run_compare() for fan-out,
  run_code() for multi-turn code agent with tool loop.
version: "2.0.0"
status: experimental
enforcement: advisory
category: routing
argument-hint: <mode> <model> <prompt...>
disable-model-invocation: true
triggers:
  - /bf
workflow_steps:
  - 'if first arg is start, restart, shutdown, dashboard, status, or sync: run powershell -File P:\\\\\\.claude/provider-configs/cc-bifrost.ps1 --<arg>'
  - 'if first arg is catalog: run python .claude/skills/bifrost/scripts/filter_models.py --source local <remaining args>'
  - 'if first arg is routes: import bf_agent, call probe_routes(), format as table'
  - 'if first arg is routes with second arg --new-only: import bf_agent, call list_catalog_models(min_context=128000, free_only=True), format as unrouted list'
  - 'if first arg is list-routes: import bf_agent, call list_routes(), format as table'
  - 'if first arg is add: import bf_agent, parse <model> <provider> <target> from remaining args, call add_route(model, provider, target), report result'
  - 'if first arg is delete: import bf_agent, parse <rule-id> from remaining args, call delete_route(int(rule-id)), report result'
  - 'else: import bf_agent, call run_simple / run_compare / run_code, report result'
---

You are a Bifrost workbench controller.

## bf_agent library

All work is done by importing and calling the bf_agent library:

```python
from bf_agent import run_simple, run_compare, run_code
```

No HTTP, no curl, no subprocess. Just Python in-process.

## bf_agent API

**run_simple(mode, prompt, model)** — stateless one-shot
- Modes: brainstorm, design, plan, review, explore
- Model: any model Bifrost can route (default: DSv4-flash) — no pre-validation
- Returns: {ok, mode, model, text, error, metrics{ttfb_ms, total_ms, status, error_type}}

**run_compare(prompt, models)** — parallel fan-out with LangGraph synthesis
- Models: any list of models Bifrost can route, default [M27, GLM-5.1, DSv4-flash]
- Returns: {ok, mode, models, results[], synthesis, metrics{wall_time_ms, timed_out_models}}

**run_code(prompt, model, max_turns)** — multi-turn tool loop agent
- Model: any model Bifrost can route (default: DSv4-flash)
- max_turns: optional override (default from BF_CODE_MAX_TURNS env, fallback 6)
- Returns: {ok, mode, model, answer, turns[], completed_via}
- Tool actions: read_file, list_dir, glob, write_file, final_answer
- Tool results fed back to model each turn until final_answer or max_turns

**list_catalog_models(min_context, free_only)** — sweep Bifrost's model catalog
- Returns list of {id, provider, model_id, context_length, label} dicts
- `min_context`: skip models below this context length (default 0 = all)
- `free_only`: skip paid models — only ':free' suffixed or $0 price (default False)
- Hits `GET /v1/models` — no quota burn, just catalog enumeration

**probe_model(model)** — live probe a single model through Bifrost
- Sends 1-token completion via `/v1/chat/completions`, reads back `extra_fields.provider` + latency
- Returns {ok, provider, latency_ms, model_requested, error}
- No route pre-existence required — Bifrost routes and reports at runtime

**probe_routes()** — probe all configured routes (DB + runtime)
- Returns {routes[], ok_count, err_count, summary}
- Each route: {priority, model, target, provider, latency_ms, probe_ok, probe_error}
- Combines `routes_probe.py` logic into the library — available without PowerShell handoff

**add_route(model, provider, target, name, priority, enabled)** — add a routing rule to config.db
- Inserts into `routing_rules` + `routing_targets` in one transaction
- CEL expression auto-generated as `model == "<model>"`
- Returns `{ok: True, rule_id}` or `{ok: False, error: "..."}`
- Idempotent: rejects duplicate CEL expressions with the existing rule id

**delete_route(rule_id)** — delete a routing rule by id
- Deletes from `routing_targets` then `routing_rules` (foreign key order)
- Returns `{ok: True}` or `{ok: False, error: "..."}`

**list_routes()** — list all rules (enabled and disabled)
- Returns `{routes[], count}` with full rule details including enabled/disabled state

## Management Commands

These invoke `cc-bifrost.ps1` for process lifecycle control:

- `/bf start` — start bifrost-http daemon on port 8080
- `/bf restart` — stop + start + auto-verify routing chain
- `/bf shutdown` — stop the daemon
- `/bf dashboard` — open `http://localhost:<port>` in default browser
- `/bf catalog` — query local shadow catalog DB. Pass `--help` for all filter flags. Default: free/subscription chat models >= 128k ctx
- `/bf catalog --list-providers` — show provider counts in local DB
- `/bf catalog --provider nvidia --free-only` — filter by provider, show only free models
- `/bf catalog --provider openrouter --free-only --min-context 131072` — OpenRouter free models >= 128k ctx
- `/bf catalog --mode embed` — embedding models only
- `/bf catalog --format json` — machine-readable output
- `/bf catalog --latest-gen-only` — drop known old-generation models from OpenRouter output (e.g. gpt-4, deepseek-v2, glm-4); free-key and subscription providers are always authoritative. Default: enabled when no `--provider` specified.
- `/bf catalog --list-all` — all models in DB without taxonomy filter
- `/bf catalog --free-tier` — show free-tier context limits instead of paid-tier (useful for Cerebras where free and paid tiers differ)

**Example — agentic work (coding/architecture/reasoning, >= 128k ctx):**
```bash
/bf catalog --latest-gen-only --min-context 128000
```
Produces ~280 models covering latest generation per vendor.

## Local Catalog DB (--source local)

The local shadow catalog at `.claude/skills/bifrost/catalog.db` is populated by `sync_catalog.py`. It replaces the Bifrost governance DB for model discovery and filtering when the Bifrost daemon is not running.

**Taxonomy rules (applied automatically):**
- FREE-KEY providers (cerebras, groq, mistral, nvidia): API key covers all models — no context or cost filter
- SUBSCRIPTION providers (minimax, z.ai): covered by subscription — no cost filter
- OPENROUTER: only models with `input_cost_per_token = 0 AND output_cost_per_token = 0` are free (excludes moonshotai, minimax, z.ai, bytedance)
- `/bf status` — health check: rule count/enabled, provider key alignment, live probe
- `/bf list-routes` — list all routing rules (enabled and disabled)
- `/bf add <model> <provider> <target>` — add a routing rule: model alias, provider name, target model-id
- `/bf delete <rule-id>` — delete a routing rule by its numeric rule id (use `/bf list-routes` to find the id)

## Failure Modes

**`provider is required` (HTTP 500)**
Bifrost sets all routing rules to `enabled=0` on startup. If the re-enable step in `cc-bifrost.ps1 --restart` fails (e.g. python inline script error), rules stay disabled and Bifrost can't route any request — resulting in "provider is required". Run `cc-bf --status` to check if rules are enabled. Run `cc-bf --restart` to re-enable.

**`model should be in provider/model format` (HTTP 400)**
The probe sends the Bifrost routing alias (e.g. `DSv4-flash`) but Bifrost's internal validation requires the actual catalog model ID (`deepseek-ai/deepseek-v4-flash`). This means the CEL routing engine is not matching before validation. Check that the rule exists in `cc-bf --status` and that `enabled=1`.

## Routes Probe (/bf routes)

**`/bf routes`**: Calls `probe_routes()` from bf_agent — combines DB layer + runtime layer in one Python call:

- **DB layer**: `SELECT routing_rules + routing_targets WHERE enabled=1`
- **Runtime layer**: For each routed model, sends a 1-token completion via `probe_model()`, reads `extra_fields.provider` and `latency`
- Output: table with Priority | Model | Target | Provider | Latency | Status

**`/bf routes --new-only`**: Calls `list_catalog_models(min_context=128000, free_only=True)`, diffs against configured CEL expressions, shows catalog models with no route yet.

**No quota burn**: One 1-token completion per routed model. New-model sweep uses `/v1/models` list only — no completions.

## Invocation

  /bf <mode> <model> <prompt...>
  /bf start|restart|shutdown|dashboard|status|catalog|catalog --<args>|routes|routes --new-only|list-routes|add|delete|sync

Argument semantics:
- `$0` = mode
- `$1` = model alias
- remaining text = task prompt

Defaults:
- If mode missing: `brainstorm`
- If model missing (non-compare): `M27`
- In compare mode, if models missing: `M27,GLM-5.1,DSv4-flash` (all three)

Modes:
- `brainstorm`: generate multiple ideas, directions, and variations
- `design`: focus on architecture, interfaces, contracts, tradeoffs
- `plan`: ordered steps with risks and checkpoints
- `review`: critique, find weaknesses, suggest improvements
- `explore`: open-ended investigation and hypothesis generation
- `code`: multi-turn tool loop — read files, write edits, final_answer
- `compare`: fan out across models in parallel, synthesize via LangGraph

Allowed model values:
  Any model Bifrost can route. The library validates at runtime via Bifrost, not ahead-of-time.

## Implementation

### Simple modes (brainstorm/design/plan/review/explore)

```python
from bf_agent import run_simple

result = run_simple("$0", "<prompt>", model="$1")
print(result["text"] or f"ERROR: {result['error']}")
```

### Compare mode

```python
from bf_agent import run_compare

result = run_compare("<prompt>", models=["M27", "GLM-5.1", "DSv4-flash"])
for r in result["results"]:
    print(f"## {r['model']}\n{r['text']}\n")
print("## Synthesis\n" + result["synthesis"])
```

### Code mode

```python
from bf_agent import run_code

result = run_code("<prompt>", model="DSv4-flash")
print(result["answer"])
print(f"(completed via: {result['completed_via']}, turns: {len(result['turns'])})")
```

## Constraints

- BF_ALLOWED_ROOT defaults to P:\\\\\\
- File reads limited to BF_FILE_CHAR_LIMIT (default 12000 chars)
- Directory listing capped at BF_DIR_ITEM_LIMIT (default 200 items)
- Glob capped at BF_GLOB_LIMIT (default 100 matches)
- Code agent max turns: BF_CODE_MAX_TURNS env or 6
- Timeout per model call: BF_TIMEOUT_MS env or 120000ms

## Examples

- /bf brainstorm M27 ideas for a repo-local memory system
- /bf design DSv4-flash plugin architecture for MCP-heavy workflows
- /bf plan GLM-5.1 migration from Python to TypeScript
- /bf review M27 this plugin architecture for brittleness
- /bf compare M27,GLM-5.1,DSv4-flash best architecture for multi-model planning in Claude Code
- /bf code DSv4-flash read P:\\\\\\README.md and propose a refactor
- /bf explore GLM-5.1 what would a pre-mortem skill look like in Claude Code
- /bf routes — probe all configured routes and measure latency
- /bf routes --new-only — find catalog models with no routing rule yet
- /bf list-routes — list all routing rules (enabled and disabled)
- /bf add DSv4-flash deepseek deepseek-ai/deepseek-v4-flash — add a new route
- /bf delete 5 — delete routing rule #5