# Design: LLM-Judge Stop Hook for Proactive Observation Surfacing

**Status:** Design complete (2026-08-02). Phase 0 implemented and live. Phase 1+ gated on measurement.

**Design doc:** `C:\Users\brsth\AppData\Local\Temp\grok-design-2088aada\grok-design-doc-2088aada.md` (~2000 lines, 67 review findings addressed, critical friend PROCEED)
**Wiki concept:** [[measure-first-pattern-for-proactive-mechanism-design]]
**Phase 0 code (live):**
- `~/.grok/hooks/scripts/PostToolUse_tool_log.py` — logs tool calls per session
- `~/.grok/hooks/scripts/Stop_text_log.py` — captures lastAssistantMessage per turn
- `~/.grok/hooks/posttooluse-tool-log.json` + `stop-text-log.json` — registrations
- `P:/.agents/scripts/analysis/phase0_missed_rate.py` — missed-observation rate analyzer

**Kill switch:** `OBSERVATION_TOOL_LOG_DISABLED=1` env var disables both hooks.

---

## Design revision (2026-08-02, post-critical-friend)

The critical friend reframed the approach from "build judge immediately" to "measure first." Phase 0 is now **passive log only** (no judge, no API cost, no additionalContext). The judge (Phase 1) is built ONLY if Phase 0 shows ≥0.5 missed observations per session over 30 days / 50 sessions. See [[measure-first-pattern-for-proactive-mechanism-design]] for the transferable pattern.

**Open questions** (in design doc §16):
- §16.13: Is 0.5 missed obs/session the right Phase 0→1 threshold? Review after 7 days of data.
- §16.12: Does the judge's reduced context limit detection? Falsifier: 20 turns, judge run twice (reduced vs full context).

---

## Objective (original)

Build a Stop hook that uses a two-stage filter (deterministic code → LLM judge) to detect when the agent encountered information worth surfacing but didn't express it, then injects `Maybe:` observations back into the conversation via `additionalContext`.

## Problem

The `/notice` skill has 13 triggers, 8-heuristic motivation scoring, adaptive calibration, and hard-skip patterns — the most sophisticated proactive-surfacing design in the workspace. It has never been observed working because it's a skill, not a hook. Skills require invocation; hooks fire automatically. All that trigger infrastructure sits dormant.

The AGENTS.md `Note:` and `Maybe:` rules are behavioral reminders (~60-70% reliable based on correction frequency this session). Hooks are the only mechanism tier with near-100% reliability on this host.

## Proposed solution: two-stage Stop hook

### Stage 1 — Deterministic code filter (5-10ms, every turn)

Python script reads the transcript/tool-call context and applies hard gates:

- **Skip if:** first turn, acceleration mode, implementation skill active (`/go`, `/refactor`, `/grok-parallel`), already has `Note:`/`Maybe:`/`INFO:` line in output
- **Fire if:** turn used observation-producing tools (`read_file`, `grep`, `list_dir`, `web_search`, `web_fetch`, `evaluate_script`) AND zero observation lines in output AND cooldown expired (max 1 per 3 turns)

If stage 1 returns False: exit immediately, no LLM cost.

### Stage 2 — LLM judge (2-5s, only when stage 1 passes)

Send the agent's last turn (tool calls + results + output) to a different-model-family judge with:

```
You are an observation auditor. Read the agent's last turn below.
The agent used these tools: <list>.
Did the agent encounter information worth surfacing that the operator would want to know, but didn't mention?
Consider: connections to wiki concepts, patterns from prior sessions, contradictions with documented state, workflow automation opportunities, unverified claims, non-obvious techniques.
Score each candidate on relevance, novelty, and information gap (1-5 each).
Only return candidates with average score ≥3.0 and confidence ≥medium.
Reply JSON: {"observations": [{"text": "...", "confidence": "low|medium", "score": N}]}
If nothing missed: {"observations": []}
```

### Injection

If observations found, inject via Stop hook `additionalContext`:
```
System reminder: observation audit found something you may have missed:
Maybe: <observation>. Confidence: <level>. Ignore if not relevant.
```

## Design decisions to make in the design doc

1. **Judge model selection** — DiffusionGemma (free, 256K context, local), free fleet model (zen-deepseek-v4-flash-free via spawn_subagent), or a small model via direct API. Consider: latency, cost, model-family diversity from parent Grok, reliability of tool-grounded prompts.

2. **Transcript packing** — how to efficiently pass the last turn's content to the judge. Options: read `chat_history.jsonl` directly, use `/packet` for content extraction, pass tool results inline. Consider: the judge doesn't need the full conversation — just the last turn's tool calls + results + agent output.

3. **False-positive management** — what prevents the judge from surfacing noise? Options: confidence threshold (medium+), score threshold (3.0+), cooldown (1 per 3 turns), adaptive calibration (track operator response: acknowledged → lower threshold, ignored → raise).

4. **Injection reliability** — the Cursor bug reports show `additionalContext` injection can silently fail. How to verify the injection landed. Options: receipt log, re-check on next turn, structural fallback (if injection fails, append to a file the agent is told to read).

5. **Adaptive calibration** — reuse `/notice`'s calibration state (`~/.grok/state/notice-calibration.json`). Track: acknowledged observations (lower threshold), ignored observations (raise), explicitly dismissed (raise more). Floor at 2.0, ceiling at 5.0.

6. **Trigger taxonomy reuse** — which `/notice` triggers (T1-T13) map to the hook? The most relevant for `Maybe:` surfacing: T7 (connection opportunity), T8 (anticipated need), T11 (undocumented success pattern). The others (T1 error, T6 unverified diagnosis, T10/T13 accumulation) are already partially covered by existing hooks/skills.

7. **Performance budget** — target: ≤5s total per fire (stage 1: <10ms, stage 2: 2-5s). Fires on ~20-30% of turns (only observation-producing turns, not in hard-skip, not on cooldown). Acceptable? What's the operator's tolerance?

8. **Relationship to `/notice` skill** — does this hook replace `/notice`, complement it, or merge with it? The hook fires automatically; the skill fires on invocation. Options: (a) hook replaces skill entirely, (b) skill becomes the design document and manual-trigger path, hook becomes the auto-fire path, (c) skill is deprecated.

## Constraints

- **Must work in Grok Build** — hooks are `command` and `http` type only (no `prompt` or `agent` hook types like Claude Code has). The LLM judge call must happen via Python script that calls an API, not via a native prompt hook.
- **Must use a different model family** from the parent Grok — same-family judges share blind spots. We have DeepSeek (zen-deepseek-v4-flash-free), Qwen, MiniMax available.
- **Must be non-blocking when possible** — if the LLM judge takes >10s, the Stop hook should either timeout gracefully (fail-open, no observation surfaced) or run async.
- **Must not duplicate `/notice`'s trigger design** — reuse, don't reinvent.
- **Must have a kill switch** — operator can disable the hook if false-positive rate is too high.

## Research base

- `/notice` SKILL.md — 13 triggers, 8-heuristic motivation scoring, adaptive calibration (the design to reuse)
- LLM-as-judge research: Luna-2 (3B/8B) achieves 0.88-0.95 accuracy at 97% cost reduction (Zylos 2026)
- Reflexion (Shinn et al., NeurIPS 2023): specific recovery signals beat generic "look again" prompts
- Claude Code Stop hooks: `additionalContext` injection is the documented primitive for surfacing observations
- HaluGate: token-level hallucination detection with 76-162ms overhead — demonstrates feasibility of fast judge hooks
- "Where Facts Go Missing" (arXiv:2607.22448): 73.4% of omission loss comes from deterministic pipeline layers — hooks catch what model cognition misses
- Self-preference bias: judge must be different model family from the generator
- Two-stage filter pattern: rule-based checks first with short-circuiting (Modelmetry, LangChain middleware, AWS Bedrock AgentCore)
- `/tp` protocol.md anti-template voice section — the judge prompt should also resist formulaic output

## File paths

- `/notice` SKILL.md: `~/.grok/skills/notice/SKILL.md`
- Existing calibration state: `~/.grok/state/notice-calibration.json`
- Existing cooldown state: `~/.grok/state/notice-cooldown.json`
- Hook registration: `~/.grok/config.toml` (Stop hooks section)
- DiffusionGemma reader: `P:/.agents/scripts/models/dgemma_read.py`
- Spawn logging: `P:/.agents/scripts/log_spawn.py`

## Acceptance criteria

- [ ] Two-stage filter design documented with data flow diagram
- [ ] Stage 1 deterministic filter implemented and tested (hard-skip, tool-type filter, cooldown)
- [ ] Stage 2 LLM judge prompt designed and tested for false-positive rate
- [ ] Injection mechanism verified (additionalContext lands reliably in Grok Build)
- [ ] Judge model selected based on latency + accuracy + model-family diversity
- [ ] Adaptive calibration reused from `/notice`
- [ ] Kill switch implemented (env var or config flag)
- [ ] Performance budget met: ≤5s per fire, fires on ≤30% of turns
- [ ] False-positive rate measured: target ≤20% of surfaced observations are noise
- [ ] Relationship to `/notice` skill documented (replace, complement, or merge)
---
---
---

## Changelog

| Date | Session | Action |
|------|---------|--------|
| 2026-08-02T16:34 | 019fba58... | claim released |
| 2026-08-02T16:33 | 019fba58... | claimed by grok |
