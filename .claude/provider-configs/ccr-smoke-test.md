# CCR Smoke Test — can Claude Code Router replace Bifrost + bespoke shim?

**Decision this test settles:** whether CCR (Node, transformer-native) can be the
*entire* routing layer — replacing both `bifrost_tool_shim.js` and the Bifrost
binary — or whether Bifrost must stay behind it for fallback resilience.

**Criterion:** CCR wins (full replacement) only if it matches Bifrost on BOTH
multi-provider routing AND multi-target fallback chains. The enterprise features
I earlier weighted (governance/RBAC/caching) are NOT in use — the live Bifrost
`governance` block is only `routing_rules` (CEL model→provider maps). So routing +
fallback parity is the whole question.

---

## Prerequisite: upgrade CCR (installed 1.0.72 → latest 2.0.0)

```powershell
ccr stop                                                   # if running (pid file present)
npm install -g @musistudio/claude-code-router@latest       # 1.0.72 is a major version behind
ccr version                                                 # confirm 2.x
```
> 2.0.0 is a major bump; the transformer/routing config below targets 2.x docs.
> Test on 1.0.72 and you may test a stale API.

---

## Part 1 — Multi-LLM routing (proves CCR replaces Bifrost's core job)

Configure 2 real providers you already have keys for (keys live in `P:/.env`).
Use MiniMax (cloud, Anthropic-compatible — also the tool-call-leak target) + one
OpenAI-compatible provider (e.g. an OpenCode/Nvidia/Z.ai route from your Bifrost table).

`~/.claude-code-router/config.json`:
```jsonc
{
  "Providers": [
    {
      "name": "minimax",
      "api_base_url": "https://api.minimax.io/anthropic/v1/messages",
      "api_key": "<MINIMAX_KEY from P:/.env>",
      "models": ["MiniMax-M2.7"]
    },
    {
      "name": "zai",
      "api_base_url": "https://api.z.ai/v1/chat/completions",
      "api_key": "<ZAI_KEY>",
      "models": ["glm-4.7"],
      "transformer": { "use": ["openrouter"] }   // OpenAI->Anthropic shape
    }
  ],
  "Router": { "default": "zai,glm-4.7" }
}
```
```powershell
ccr start
$env:ANTHROPIC_BASE_URL = "http://127.0.0.1:3456"   # confirm CCR's port from `ccr start` output
claude
```
**PASS check 1:** a normal turn answers via `zai`. Then `/model minimax,MiniMax-M2.7`
(or edit Router.default) and confirm a turn answers via MiniMax. Both providers reachable
through CCR = CCR can do Bifrost's core multi-LLM job.

---

## Part 2 — Fallback chain (the make-or-break; Bifrost's one feature CCR may lack)

Add a fallback so the primary is dead and a secondary must take over.
Check CCR 2.x docs for the exact key — candidates: a `fallback` array on the provider,
or a Router-level fallback list. Minimal probe:
```jsonc
{
  "Providers": [
    { "name": "dead",  "api_base_url": "http://127.0.0.1:9/v1/messages", "api_key": "x", "models": ["primary"] },
    { "name": "zai",   "api_base_url": "https://api.z.ai/v1/chat/completions", "api_key": "<ZAI_KEY>", "models": ["glm-4.7"], "transformer": { "use": ["openrouter"] } }
  ],
  "Router": { "default": "dead,primary", "fallback": ["zai,glm-4.7"] }   // verify key name in 2.x docs
}
```
`dead` points at a closed port (127.0.0.1:9) so the primary call fails immediately.

**PASS check 2:** a turn still succeeds — CCR fails over from `dead` to `zai`.
**FAIL:** the turn errors out with no failover.

---

## Decision

| Part 1 | Part 2 | Outcome |
|---|---|---|
| PASS | PASS | **Replace shim + Bifrost with CCR.** Host the MiniMax `<minimax:tool_call>`→`tool_use` normalizer as a `transformResponseOut` plugin in `~/.claude-code-router/plugins/`. Single-layer stack. |
| PASS | FAIL | **Keep Bifrost** as routing/failover backend; put CCR (or UniClaudeProxy) in front *only* for tool-call normalization (one provider = Bifrost passthrough). |
| FAIL | — | CCR can't replace Bifrost; extend the existing shim's response path instead. |

**Rollback:** none of this touches Bifrost or the shim until the decision is made.
To revert at any point: `ccr stop`, unset `ANTHROPIC_BASE_URL` (or run `cc-bf`), Bifrost
path is untouched.

**Known risk / failure mode:** the fallback config key name is unverified for 2.x —
if Part 2 "fails", first confirm you used the correct key from the live 2.x docs before
concluding CCR lacks fallback.
```
