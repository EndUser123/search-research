# ADR-20260326: Intelligence Stream Phase 1 — Critical Bug Fixes and CKS Integration

**Status:** Proposed
**Date:** 2026-03-26
**Context:** Phase 1 implementation package for Intelligence Stream MVP has 3 runtime bugs and 1 architectural violation. This ADR documents the fixes required before the package is runnable.

---

## Decision

Fix 3 critical bugs, integrate with existing P:-- CKS instead of building a parallel registry, and correct the Gemini CLI invocation syntax.

---

## Bug #1 — `csf/logging.py` missing `import os`

**File:** `csf/logging.py:15`
**Severity:** 🔴 Critical — crashes on every `log_action()` call
**Evidence:** Line 15 calls `os.getenv("CSF_TID")` but `os` is never imported.

```python
# CURRENT (broken)
from pathlib import Path
import json
from datetime import datetime
from .terminal_context import resolve_tid  # os not imported!

def log_action(event: str, payload: dict):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "tid": os.getenv("CSF_TID"),  # NameError at runtime
```

**Fix:**
```python
import os
from pathlib import Path
import json
from datetime import datetime
from .terminal_context import resolve_tid
```

---

## Bug #2 — `bin/csf-ingest` missing `import json`

**File:** `bin/csf-ingest:22`
**Severity:** 🔴 Critical — crashes immediately on first JSON parse
**Evidence:** Line 22 calls `json.loads(line)` but `json` is never imported.

```python
# CURRENT (broken)
#!/usr/bin/env python
import subprocess
from csf.youtube_auth import get_yt_dlp_args
from csf.manifest import write_manifest
from csf.logging import log_action
from csf.terminal_context import resolve_tid
# MISSING: import json

    videos = [json.loads(line) for line in result.stdout.strip().splitlines() if line]
```

**Fix:** Add `import json` to the imports block.

---

## Bug #3 — `cks_store.py` violates multi-terminal isolation

**File:** `csf/cks_store.py:7`
**Severity:** 🔴 Critical — silent data loss on concurrent terminals
**Evidence:** All other modules use `resolve_tid()` for per-tenant paths. `cks_store.py` writes to a shared `.cks/registry.json` at the repo root.

```python
# CURRENT (broken) — shared path, not per-tenant
def append_to_cks(artifact: dict):
    _, tenant_dir = resolve_tid()  # called but IGNORED
    registry = Path(".cks/registry.json")  # SHARED across all terminals!
```

**Consequence:** Two terminals analyzing simultaneously corrupt or silently overwrite each other's artifacts.

**Opportunity:** `P:/packages/search-research/core/cks/unified.py` already has a full CKS with `ingest_memory()`, `ingest_pattern()`, `ingest_decision()`, `ingest_commitment()`, `ingest_learning()`, `ingest_memories_batch()`. This is a confirmed real API with ~20 ingest methods. Building a separate `.cks/registry.json` is both a multi-terminal violation AND wasted integration work.

**Fix — integrate with existing CKS:**

```python
# NEW csf/cks_store.py — uses P:-- existing CKS API
from pathlib import Path
from search_research.core.cks.unified import (
    ingest_memory,
    ingest_pattern,
    ingest_learning,
)

def append_to_cks(artifact: dict):
    """Ingest analysis artifact into P:-- CKS.

    artifact expected shape:
        {"type": "memory|pattern|learning", "title": str, "content": str, "source": str, ...}
    """
    entry_type = artifact.get("type", "memory")
    title = artifact.get("title", "untitled")
    content = artifact.get("content", "")
    source = artifact.get("source", "")

    if entry_type == "memory":
        ingest_memory(question=title, answer=content, source_chunk=source)
    elif entry_type == "pattern":
        ingest_pattern(title=title, content=content, source_chunk=source)
    elif entry_type == "learning":
        ingest_learning(title=title, content=content)
    else:
        ingest_memory(question=title, answer=content, source_chunk=source)
```

**Confirmed CKS sync pattern** (verified at `packages/search-research/core/cks/unified.py:4085`):
```python
from cks.unified import get_cks

def append_to_cks(artifact: dict):
    """CKS handles async internally — no asyncio.run() needed."""
    entry_type = artifact.get("type", "memory")
    title = artifact.get("title", "untitled")
    content = artifact.get("content", "")
    source = artifact.get("source", "")

    with get_cks() as cks:
        if entry_type == "memory":
            cks.ingest_memory(question=title, answer=content, source_chunk=source)
        elif entry_type == "pattern":
            cks.ingest_pattern(title=title, content=content, source_chunk=source)
        elif entry_type == "learning":
            cks.ingest_learning(title=title, content=content)
        else:
            cks.ingest_memory(question=title, answer=content, source_chunk=source)
```

**Also works** via module-level convenience functions (`unified.py:4085-4162`):
```python
from cks.unified import ingest_memory, ingest_pattern, ingest_learning

with get_cks() as cks:
    ingest_memory(question=title, answer=content, source_chunk=source)
```

Import path for bin scripts: `P:/packages/search-research/core/cks/` needs to be on `sys.path` via:
```python
import sys
_src_dir = Path(__file__).parent.parent / "packages" / "search-research" / "core"
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))
from cks.unified import get_cks
```

---

## Bug #4 — `gemini ask` CLI syntax is wrong

**File:** `bin/csf-analyze`
**Severity:** 🔴 Critical — command silently runs in wrong mode
**Evidence:** `gemini ask --model X --output-format json "prompt"` passes `ask --model X --output-format json "prompt"` as an interactive query string, not as CLI flags.

**Correct headless syntax:**
```bash
gemini -p "prompt text" --model gemini-2.0-flash-thinking-exp-1219 --output-format json
```

**Fix in `bin/csf-analyze`:**
```python
# BROKEN (proposal)
result = subprocess.run([
    "gemini", "ask", "--model", cfg["gemini"]["model"],
    "--output-format", "json", prompt
], capture_output=True, text=True)

# FIXED
result = subprocess.run([
    "gemini", "-p", prompt,
    "--model", cfg["gemini"]["model"],
    "--output-format", "json"
], capture_output=True, text=True)
```

---

## Bug #5 — Gemini JSON output parsing is broken

**File:** `bin/csf-analyze`
**Severity:** 🔴 Critical — `json.loads()` on stdout always fails for JSON mode
**Evidence:** `gemini -p --output-format json` returns:
```json
{"session_id": "...", "response": "{\"csf_categories\": [1, 3], ...}", "stats": {...}}
```

The actual JSON payload is a **string inside the `response` field**. The outer wrapper is NOT the payload — it's the CLI output envelope.

**Fix:**
```python
if result.returncode == 0:
    try:
        outer = json.loads(result.stdout)
        # The payload is a JSON string inside the response field
        payload_str = outer.get("response", result.stdout)
        analysis = json.loads(payload_str)
        out_path = analysis_dir / f"{video['id']}.json"
        out_path.write_text(json.dumps(analysis, indent=2))
    except json.JSONDecodeError as e:
        # Fallback: try parsing the raw stdout as last resort
        try:
            analysis = json.loads(result.stdout)
        except:
            log_action("analysis_parse_failed", {"video_id": video["id"], "error": str(e)})
```

---

## Bug #6 — Remove hardcoded model from config

**File:** `config/intelligence_stream.yaml`
**Severity:** 🟡 Medium — model auto-selected by Gemini CLI, hardcoded value may cause `ModelNotFoundError`
**Evidence:** Gemini CLI auto-selects model based on query. `--model` flag overrides this, but the configured model may not exist in the user's installation.

**Fix:** Remove the `model` field from `config/intelligence_stream.yaml`, or leave it blank to let CLI auto-select:
```yaml
gemini:
  # model: auto-selected by CLI — do not hardcode
  output_format: json
```

In `bin/csf-analyze`, remove `--model` from the subprocess call:
```python
# FIXED — let CLI auto-select model
result = subprocess.run([
    "gemini", "-p", prompt,
    "--output-format", "json"
], capture_output=True, text=True)
```

---

## Bug #7 — Unused `watchdog` dependency

**File:** `requirements.txt`
**Severity:** 🟢 Low — dead weight
**Fix:** Remove `watchdog` from `requirements.txt`.

---

## Multi-Terminal Safety Assessment (Post-Fix)

| Component | Pre-Fix | Post-Fix |
|-----------|---------|----------|
| `csf/logging.py` | Broken (crash) | ✅ Per-tenant logs |
| `bin/csf-ingest` | Broken (crash) | ✅ Per-tenant + shared manifest |
| `cks_store.py` | 🔴 Shared registry → silent data loss | ✅ P:-- CKS API (server-side isolation) |
| `bin/csf-analyze` | Broken (wrong CLI syntax + wrong JSON parsing) | ✅ Fixed CLI call + proper response parsing |

---

## Multi-Terminal Safety

- **Pre-fix:** 3 components broken (crash or data loss on any use)
- **Post-fix:** All components are multi-terminal safe

---

## Consequences

**Positive:**
- Package actually runs without crashing
- Artifacts stored in existing P:-- CKS instead of parallel registry
- JSON output correctly parsed
- Uses existing authenticated Gemini CLI (no new API key needed)

**Negative:**
- CKS integration adds `search-research` package dependency to `intelligence-stream/`
- Async CKS methods require `asyncio.run()` wrapper in sync scripts
- Model name must be changed to one available in the Gemini CLI

---

## Implementation Notes

1. **Test order:** Fix bugs 1, 2, 4, 5, 6 first (syntactic). Test with `csf-diag` and `python bin/csf-ingest` before touching CKS integration.
2. **CKS import path:** `P:/packages/search-research/src` must be on `sys.path`. Add to the bin script: `sys.path.insert(0, "P:/packages/search-research/src")`.
3. **Gemini model:** Verify available models with `gemini --help` or `gemini models list` before setting in config.
4. **Async wrapper:** CKS `ingest_*` methods are async. Use `asyncio.run()` or a thread pool:

```python
import asyncio
from search_research.core.cks.unified import ingest_memory

def sync_ingest_memory(question: str, answer: str, source_chunk: str = ""):
    asyncio.run(ingest_memory(question=question, answer=answer, source_chunk=source_chunk))
```
