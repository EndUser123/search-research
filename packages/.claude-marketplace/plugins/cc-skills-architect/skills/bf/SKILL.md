---
name: bf
description: >
  Bifrost management and routing workbench. LLM dispatch moved to /ai-api.
  This skill provides: daemon lifecycle (start/restart/shutdown/dashboard/status),
  catalog browsing, route probing/management, and bf_agent library introspection.
version: "3.0.0"
status: stable
enforcement: advisory
category: routing
argument-hint: <command> [args...]
disable-model-invocation: true
triggers:
  - /bf
workflow_steps:
  - 'if first arg is start, restart, shutdown, dashboard, status, or sync: run powershell -File P://.claude/provider-configs/cc-bifrost.ps1 --<arg>'
  - 'if first arg is catalog: run python P://packages/cc-skills-utils/skills/bifrost/scripts/filter_models.py --source local <remaining args>'
  - 'if first arg is routes: import bf_agent, call probe_routes(), format as table'
  - 'if first arg is routes with second arg --new-only: import bf_agent, call list_catalog_models(min_context=128000, free_only=True), format as unrouted list'
  - 'if first arg is list-routes: import bf_agent, call list_routes(), format as table'
  - 'if first arg is add: import bf_agent, parse <model> <provider> <target> from remaining args, call add_route(model, provider, target), report result'
  - 'if first arg is delete: import bf_agent, parse <rule-id> from remaining args, call delete_route(int(rule-id)), report result'
  - 'else: REPLY with redirect instruction — for LLM calls use: /ai-api <mode> <model> <prompt>'
---

# /bf — Bifrost Management & Routing

**Note:** LLM dispatch has moved to `/ai-api`.
- `/ai-api <mode> <model> <prompt>` — direct SDK (fastest)
- `/ai-api bf <mode> <model> <prompt>` — through Bifrost HTTP (governance + fallback)

This skill handles Bifrost daemon lifecycle, catalog browsing, and route management.

## Quick Reference

| Command | Purpose |
|---------|---------|
| `/bf start` | Start Bifrost daemon on port 8080 |
| `/bf restart` | Stop + start + verify routing |
| `/bf shutdown` | Stop the daemon |
| `/bf dashboard` | Open http://localhost:8080 |
| `/bf status` | Health check: rules, keys, live probe |
| `/bf catalog` | Browse model catalog (default: free/subscription >= 128k ctx) |
| `/bf routes` | Probe all routes, measure latency |
| `/bf routes --new-only` | Find catalog models with no route yet |
| `/bf list-routes` | List all routing rules |
| `/bf add <model> <provider> <target>` | Add routing rule |
| `/bf delete <rule-id>` | Delete routing rule |

## Catalog Examples

```bash
/bf catalog --list-providers          # show provider counts
/bf catalog --provider nvidia         # Nvidia models
/bf catalog --provider openrouter --free-only --min-context 131072  # free OR models >= 128k
/bf catalog --mode embed              # embedding models only
/bf catalog --format json             # machine-readable
/bf catalog --list-all                # all models, no filter
```

## Routes Examples

```bash
/bf routes                            # probe all configured routes
/bf routes --new-only                 # find unrouted catalog models
/bf list-routes                       # list all rules
/bf add DSv4-flash deepseek deepseek-ai/deepseek-v4-flash
/bf delete 5
```

## bf_agent Library (introspection)

```python
from bf_agent import probe_routes, list_catalog_models, add_route, delete_route, list_routes
```

| Function | Purpose |
|----------|---------|
| `probe_routes()` | Probe all routes, return {routes[], ok_count, err_count} |
| `list_catalog_models(min_context, free_only)` | Sweep catalog, return model dicts |
| `add_route(model, provider, target)` | Add routing rule, returns {ok, rule_id} |
| `delete_route(rule_id)` | Delete rule, returns {ok} |
| `list_routes()` | List all rules, returns {routes[], count} |

## Failure Modes

**`provider is required` (HTTP 500)**
Rules disabled after startup. Run `/bf status` to check. Run `/bf restart` to re-enable.

**`model should be in provider/model format` (HTTP 400)**
CEL routing not matching. Check `/bf status` — ensure `enabled=1` for the rule.

## Migrated to /ai-api

| Old /bf usage | New /ai-api equivalent |
|---------------|------------------------|
| `/bf brainstorm M27 prompt` | `/ai-api brainstorm M27 prompt` |
| `/bf design DSv4-flash prompt` | `/ai-api design DSv4-flash prompt` |
| `/bf compare M27,GLM-5.1,DSv4-flash prompt` | `/ai-api compare M27,GLM-5.1,DSv4-flash prompt` |
| `/bf code DSv4-flash prompt` | `/ai-api code DSv4-flash prompt` |
| `/bf review M27 prompt` | `/ai-api review M27 prompt` |
| `/bf explore GLM-5.1 prompt` | `/ai-api explore GLM-5.1 prompt` |

## Evidence-First Principles

### E1 — Evidence before claims
Before claiming code is absent, unchanged, or non-existent — search the codebase and verify with tools first. Claims of absence are only valid after confirmed Read/Grep/git failures.

### E4 — Investigate before asking
Do NOT answer without reading relevant source files first. Do not ask the user for information you can obtain yourself via Read, Grep, Bash, git, or available MCP tools.

### E5 — Anti-lazy escape hatch
Prohibited:
- "I assume", "I think", "probably" without tool verification
- Claiming something doesn't exist without confirmed tool failure
- Skipping evidence gathering because the answer seems obvious

## PHASE STRUCTURE

```
PHASE 1: PARSE + ROUTE (Generation) — Identify command, match workflow_steps pattern
    ↓ STOP: Confirm routing decision before execution
PHASE 2: EXECUTE (Generation) — Run the matched command/script
    ↓ STOP: Report result before completion
PHASE 3: REPORT (Validation) — Format and present result to user
```

**STOP conditions:**
- Between PHASE 1 and PHASE 2: STOP after routing decision (confirm correct path)
- Between PHASE 2 and PHASE 3: STOP after execution completes (verify success)
- Between PHASE 3 and end: STOP after result formatted (user sees output)

**Key separation**: Parsing/routing is Generation. Command execution is Generation. Result reporting is Validation.

**For Bifrost HTTP routing:** add `bf` after `/ai-api`:
```bash
/ai-api bf brainstorm M27 prompt  # routes through Bifrost daemon
```