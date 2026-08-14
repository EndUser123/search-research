# Pack: model-web

**Files:** 10
**Mode:** file pack

---


## SIGNATURE TOC

### C:\Users\brsth\.grok\skills\model-web\SKILL.md

```markdown
---
name: model-web
description: >
metadata:
argument-hint: "[ask <site> \"<prompt>\" | select | list | ensemble \"<prompt>\"]"
when-to-use: >
user-invocable: true
host: grok
version: "1.3"
depends_on: [chrome-devtools]
consumes: [chrome-devtools-mcp-tools]
provides: [model-web-advisory, browser-llm-bridge, conversation-selection, multi-model-ensemble, sse-response-capture, fusion-portal-orchestration]
domain: browser-automation
# /model-web — browser-based LLM advisory bridge
## Core concept
- receives prompts from Grok
- reasons and responds
- can be consulted for direction, critique, research, or review
- **never directly controls** files, shell, or workstation state
Grok:
- decides what to ask
- sends prompts through the browser adapter
- extracts and verifies responses
- decides what local action (if any) follows
- applies its own hooks, approval gates, and judgment before acting
## Prerequisites
## Invocation patterns
### Default invocation (no args): the launcher page
## Site configurations
### Verified sites
### Community-verified sites (selectors from ParallelChat/AI-Multichat)
### Community-sourced DOM selectors (from ParallelChat, AI-Multichat)
### Input method recipes (per-framework)
### Model / mode / effort selectors
## The adapter protocol
### Step 0: Find and claim the target tab
- Claims auto-expire (no TTL refresh → auto-released)
- `release` returning `{"status":"not_claimed"}` or `{"status":"not_owner"}`
- On Chrome restart, all claims are meaningless (pages no longer exist)
- Conflict (exit code 2) means another session owns it — use a different tab
### Step 0.5: Inject SSE capture shim (MANDATORY GATE — not optional)
provides:
- `getRaw()` — all accumulated SSE data as a string
- `getChunks()` — array of individual chunks (for incremental polling)
- `extractText()` — parsed response text (handles ChatGPT JSON-delta SSE format)
- `isDone()` — true when the stream has ended (`[DONE]` marker or reader closed)
- `clear()` — reset accumulated data (call before each new prompt)
- `info()` — diagnostic JSON for debugging
### Step 1: Take a pre-send snapshot (target via pageId)
### Step 2: Generate nonce and compose prompt
### Step 3: Send the prompt
### Step 3.5: Verify submission (mandatory — prevents silent data loss)
### Step 4: Wait for response completion (adaptive polling — upgraded 2026-08-09)
### Step 5: Extract the response
boundary:
- Elements with uid prefix higher than the pre-send prefix
- Grouped under a generic/article container after the user message
- Containing the nonce (freshness proof)
### Step 6: Record run state
### Step 7: Return to Grok
## Conversation selection protocol
### `/model-web select`
## Ensemble protocol
### `/model-web ensemble "prompt"`
### Ensemble response fusion (from big-AGI Beam)
- "Find the consensus across all responses and produce a unified answer"
- "Identify the best structural elements from each response and combine them"
- "Find contradictions between responses and resolve them with reasoning"
### Post-ensemble routing (mandatory for actionable findings)
### Post-ensemble stats update (mandatory — added 2026-08-02)
- Exceptional insight/novelty: +30 to +50
- Solid contribution: +10 to +20
- Average/useful: -5 to +5
- Weak/unhelpful: -20 to -30
- No response/failed: -10 (slight penalty, not harsh — could be transient)
- The response was purely advisory context consumed immediately (e.g., a
- The response was incorporated into a wiki concept or AGENTS.md rule
## Fusion portal protocol
### Naming convention
- **"the CLI"** or **"the terminal"** = the orchestrator (the terminal LLM)
- **"Grok"** = the grok.com web LLM (one of the 16 ensemble targets)
### Opening the fusion portal
### The blast signal
- `"background"` — tabs open behind the fusion page (default)
- `"visible"` — tabs open in the foreground so the operator can watch each model respond
### Orchestration flow (7 steps)
- **`background`** (default): `new_page(url=<new_chat_url>, background=true)` —
- **`visible`**: `new_page(url=<new_chat_url>, background=false)` — tabs open
- Navigate to `new_chat_url` (fresh composer)
- Inject SSE shim
- Fill + submit per site config
- Verify submission (Step 3.5 of adapter protocol)
- Wait for completion
- Extract response (SSE preferred, DOM fallback)
### Monitoring and recovery
### Cohere limitation
## Run-state management
### State machine
### Why
- Duplicate submission (Grok restarts → did it already send?)
```

### C:\Users\brsth\.grok\skills\model-web\__lib\extract_response.py

```python
extract_via_sse_shim(page_id: int) -> dict | None
extract_from_snapshot_file(snapshot_path: Path, pre_send_prefix: int, nonce: str | None) -> dict
main() -> None
```

### C:\Users\brsth\.grok\skills\model-web\__lib\fusion_orchestrate.py

```python
utc_now() -> str
generate_run_id() -> str
sha256(text: str) -> str
fusion_state_path(run_id: str) -> Path
atomic_write(path: Path, data: dict) -> None
read_fusion_state(run_id: str) -> dict | None
read_file_or_stdin(file_arg: str | None) -> str
js_escape(text: str) -> str
cmd_parse_blast(args: argparse.Namespace) -> None
cmd_map_tabs(args: argparse.Namespace) -> None
cmd_init_run(args: argparse.Namespace) -> None
cmd_record_response(args: argparse.Namespace) -> None
cmd_gen_eval(args: argparse.Namespace) -> None
cmd_status(args: argparse.Namespace) -> None
cmd_list_runs(args: argparse.Namespace) -> None
cmd_model_map(args: argparse.Namespace) -> None
main() -> None
```

### C:\Users\brsth\.grok\skills\model-web\__lib\run_state.py

```python
utc_now() -> str
generate_run_id() -> str
generate_nonce() -> str
sha256(text: str) -> str
state_path(run_id: str) -> Path
atomic_write(path: Path, data: dict) -> None
read_state(run_id: str) -> dict | None
cmd_create(args: argparse.Namespace) -> None
cmd_update(args: argparse.Namespace) -> None
cmd_get(args: argparse.Namespace) -> None
cmd_list(args: argparse.Namespace) -> None
cmd_active(args: argparse.Namespace) -> None
_claim_lock(timeout: float, poll: float)
_load_claims() -> dict
_save_claims(data: dict) -> None
_gc_claims(claims: dict) -> dict
_resolve_sid(args) -> str
cmd_claim(args: argparse.Namespace) -> None
cmd_release(args: argparse.Namespace) -> None
cmd_claims(args: argparse.Namespace) -> None
main() -> None
```

### C:\Users\brsth\.grok\skills\model-web\__lib\sse_shim.js

```javascript
# (no signatures extracted)
```

### C:\Users\brsth\.grok\skills\model-web\fusion2.html

```html
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Model Web — Fusion</title>
<link rel="stylesheet" href="tokens.css">
<style>
<body>
<script src="model-stats.js"></script>
<script>
```

### C:\Users\brsth\.grok\skills\model-web\launcher.html

```html
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Model Web — LLM Launcher</title>
<link rel="stylesheet" href="tokens.css">
<style>
<body>
<script src="model-stats.js"></script>
<script>
```

### C:\Users\brsth\.grok\skills\model-web\model-stats.js

```javascript
# (no signatures extracted)
```

### C:\Users\brsth\.grok\skills\model-web\tests\test_run_state.py

```python
run_cmd(args: list[str]) -> tuple[str, int]
cleanup_all()
clean_state_dir()
class TestCreate
test_create_generates_run_id_and_nonce(self)
test_create_stores_prompt_hash(self)
test_create_no_prompt_leaves_hash_null(self)
class TestUpdate
test_update_state_and_round(self)
test_update_response_hash(self)
test_update_nonexistent_returns_error(self)
test_update_invalid_state_rejected(self)
class TestGet
test_get_returns_full_record(self)
test_get_nonexistent_returns_error(self)
class TestList
test_list_returns_all_records(self)
test_list_empty_returns_empty_array(self)
class TestActive
test_active_excludes_terminal_states(self)
test_active_empty_when_all_terminal(self)
class TestAtomicWrite
test_no_tmp_file_left_after_write(self)
test_json_file_is_valid(self)
```

### C:\Users\brsth\.grok\skills\model-web\tokens.css

```css
# (no signatures extracted)
```
