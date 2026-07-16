# Prospect Digest — ChatGPT-Claude Code Bridge

## Trigger
Proposal references CDP (Chrome DevTools Protocol) automation of a web service (chatgpt.com). The project has a wiki prior proving Google blocks CDP-attached browsers at OAuth consent — same protocol, different target. Also references `claude_agent_sdk` (external package v0.1.61, installed and importable).

## Sources

### Wiki: `P:/.data/wiki/concepts/cdp-google-oauth-automation-block.md`

**Takeaway**: Google's "Couldn't sign you in" guard fires on CDP attachment itself, not on JS-level fingerprints (`navigator.webdriver`, `window.chrome`, plugins/languages normalization). JS stealth passed the email-identifier page but failed at OAuth consent. GitHub OAuth was more permissive and succeeded.

**Bearing on**:
- **security** (primary): The ChromeEndpoint component depends on CDP attachment being undetected by chatgpt.com. If ChatGPT (or its underlying auth provider) uses the same CDP-detection mechanism as Google OAuth, the bridge fails entirely. This is the highest-risk unknown in the proposal — no live test against chatgpt.com is referenced.
- **testing**: Methodology from this prior can be reused to probe chatgpt.com's CDP tolerance before writing any bridge code.
- **failure-modes**: Even if CDP is currently tolerated, future ChatGPT anti-automation additions could break the bridge without code changes on this side.

### Installed package: `claude-agent-sdk v0.1.61`

**Takeaway**: The SDK is installed and exposes `query()` (async, returns `ResultMessage`), `list_sessions()`, `get_session_messages()`, and `fork_session()`. The `query()` function is a full Claude Code invocation — it can execute tools, think, and consume significant context/tokens. Each `query()` call starts a new conversation unless a session ID is provided.

**Bearing on**:
- **workflow-reviewer**: `query()` is expensive (full model invocation) and async. At 1s polling frequency, a single ChatGPT message arriving while `query()` is processing a previous one could queue or be lost.
- **state**: SDK sessions have file_size / token usage tracked server-side. Repeated `query()` calls without session management could accumulate unbounded context.
- **gate-reviewer**: The SDK `query()` bypasses all Claude Code hooks (it's an SDK call, not a terminal session). Any hook-based guard on Claude's output (tool-use logging, content filtering, directory policy) is invisible to SDK queries.

### Architecture doc: `P:/docs/architecture.md` line 51

**Takeaway**: "Browser automation, ChatGPT upload, correction loops" are explicitly marked **OUT OF SCOPE** for the ai_lane_controller project.

**Bearing on**:
- All angles: The proposal builds exactly what was scoped out. Significant reset or scope expansion decision is needed before implementation.
