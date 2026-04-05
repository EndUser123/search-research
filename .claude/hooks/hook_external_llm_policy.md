# Hook External LLM API Policy

**Rule:** Hooks MUST NOT make external API calls, HTTP requests, or spawn network-dependent subprocesses.

**Rationale:**
1. **Silent degradation**: Network failure during a hook event (PreCompact, SessionStart, etc.) silently degrades output quality or blocks user workflow with no clear error
2. **Latency injection**: Every hook event gains network round-trip overhead — PreCompact hooks that call an LLM add 1–5 seconds to every compaction
3. **Credential complexity**: Hooks run in the framework event loop; managing API keys there adds surface area for leaks and auth failures
4. **Circular dependency**: Claude Code hooks that call the Claude API create a dependency loop — if the API is down, hooks fail, which may prevent the session from starting or compacting

**Red flags (always wrong in hook files):**
```python
# ❌ LLM call inside a hook
llm = get_llm_client()
summary = llm.messages.create(...)

# ❌ HTTP request inside a hook
import requests
response = requests.get("https://api.example.com/...")

# ❌ "Graceful degradation" that silently drops captured data
try:
    summary = call_external_api(transcript)
except Exception:
    summary = None  # NOT graceful — you just lost the data
```

**Correct pattern** — use already-captured local artifacts:
```python
# ✅ Read from transcript (already in handoff envelope) at restore-time
transcript_entries = parse_transcript(snapshot["transcript_path"])
recent_messages = extract_recent_user_messages(transcript_entries, n=15)
```

**If semantic/embedding analysis is needed:** Use the built-in prompt mechanism (`type: 'prompt'`) rather than external HTTP calls to third-party LLM APIs. This keeps the LLM call within Claude Code's infrastructure.

**Decision rule:** If a hook design requires external data, restructure so the data is read from a local artifact at restore/start time rather than fetched at capture/compaction time. The `transcript_path` is already in the handoff envelope — use it.

**Counter-example:** `scanners/strawberry_validator.py` uses `httpx` to call `api.zai.ai` directly, violating all four principles above. Even with 50+ tests, it's unwired (not in `ACTIVE_RUNTIME_HOOKS`) because of this policy violation.
