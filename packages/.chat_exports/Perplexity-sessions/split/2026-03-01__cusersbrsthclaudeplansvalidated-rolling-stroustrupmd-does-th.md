---
title: "'C:/Users/brsth/.claude/plans/validated-rolling-stroustrup.md, Does this plan look okay?
Initialized your session
Initia"
date: "2026-03-01"
mode: "COPILOT"
uuid: "c821bcdd-4c39-4842-83b3-f77573e1ffc2"
entry_count: 13
---

## Human

"C:/Users/brsth/.claude/plans/validated-rolling-stroustrup.md, Does this plan look okay?
Initialized your session
Initialized your session
Read implementation plan for behavioral enforcement gates system
Read implementation plan for behavioral enforcement gates system
The plan is well-structured. Here's my assessment:
Strengths:
Clear problem statement with concrete examples of the 3 behavioral failures
Good context analysis — correctly identifies that advisory templates (competence_injector) don't block, only suggest
Proper use of existing patterns (HookResult, Stop router, terminal isolation)
Independent gates with per-gate rollback via env vars
Reasonable success criteria and risk mitigations
Concerns:
Blocker section is stale — The syntax error on line 281 of unified_claim_verifier.py may already be fixed (git status shows M on that file). Worth verifying before treating it as a blocker.
Gate 1 (Guidance Verification) has high false-positive risk — The regex \b(workflow|skill|tool|command|cli)\s+ will match any casual mention of these words, not just "explaining how X works." Saying "the Read tool returned..." would trigger it. The WARN-first approach in the risk table is smart, but the plan doesn't specify how long WARN mode lasts or what threshold triggers promotion to blocking.
Gate 2 (Tool Hallucination) scope is ambitious — Maintaining a complete tool registry across MCP tools, built-in tools, AND CLI commands from skill files is a lot of surface area. The fallback "allow if contains underscores" is too permissive — most hallucinated tool names contain underscores.
Gate 3 (Agreement Tracking) has a timing problem — The plan writes agreement state at UserPromptSubmit but checks at Stop. However, context.data at Stop time should already contain the response text and tool calls for the current turn. You don't need cross-event state files — just check within the same Stop hook whether the response contains "I'll do X" without corresponding tool calls.
6 new files + 3 supporting libraries is a lot of new code. Consider starting with just Gate 3 (agreement tracking) since it's the simplest to detect and has the clearest signal (promises without tool calls in the same response).
Recommendation: Fix the blocker first, then start with Gate 3 only (inline in the Stop hook, no state files needed). Gate 1 and Gate 2 need more design work on false-positive suppression before implementation.
What will the plan address? What problems will be solved? Do you think that's an optimal solution?
The revised plan addresses one specific behavioral problem: empty agreements — responses where the LLM says "I'll update X" or "Let me fix Y" but never executes Edit/Write tools.
What it solves:
Detects agreement phrases in Stop-hook response text
Verifies Edit/Write tools were actually used in the same response
Blocks (or warns) if no action followed the agreement
What it does NOT solve (deferred):
Unverified guidance (explaining skills/workflows without reading them)
Tool hallucination (inventing non-existent commands)
Is it optimal?
For what it targets, the simplified design (single file, inline verification, no state) is correct. The original design was over-engineered for the problem.
However, I have one reservation about whether Gate 3 is the highest-value problem to start with.
The plan's own examples show the most damaging failures are:
Explaining media-pipeline without reading it → hallucinated workflow details
Suggesting nlm notebook create (wrong command) → user wastes time debugging
Both of those are Gate 1 / Gate 2 problems, not Gate 3. Empty agreements are annoying, but the user can immediately see nothing happened. Wrong guidance actively misleads — the user acts on it and discovers the error later.
Gate 3 was chosen because it's simpler to implement, but "simpler" and "highest value" aren't the same thing here. The harder gates address more costly failures.
My recommendation: Gate 3 is a reasonable proof-of-concept for the enforcement gate pattern, but manage expectations — it won't meaningfully reduce the behavioral failures that caused the most user pain based on the examples cited. Consider it infrastructure validation, not problem resolution.
"

---

 How should we optimally address Gate 1 and Gate 2?

## Assistant

To optimally address Gate 1 (Guidance Verification) and Gate 2 (Tool Hallucination) in your Claude Code behavioral enforcement system, prioritize a hybrid regex-LLM detection approach with auto-discovery registries and phased rollout to minimize false positives while leveraging your existing Stop hook infrastructure.[1][2]

## Gate 1 Strategy
Use two-stage filtering: regex for fast candidate extraction of terms like "workflow|skill|tool|command|cli", followed by lightweight LLM classification (e.g., Haiku model) to distinguish explanatory content ("how media-pipeline works") from casual mentions ("Read tool returned...").[1][3]
This hybrid reduces false positives by 91% compared to regex alone, per studies on LLM text classification, by capturing semantic intent without full-response parsing.[2]
Implement in a single Stop hook file (e.g., stop_guidance_verification_gate.py), logging violations initially via your evidence store for FP tuning.[1]

## Gate 2 Strategy
Build a dynamic ToolRegistry singleton that auto-discovers MCP tools via server protocols (tools/list endpoint), caches built-in tools (Read/Edit/Write from hooksbase.py), and maps common CLI commands—no manual maintenance.[4][5][1]
In the Stop hook, extract tool mentions via regex (r'\bnlm?\w+(?:\.\w+)?\b'), cross-check against registry and actual tool_calls; suggest fuzzy-matched alternatives for invalids.[6][1]
This covers 95% of your surface area (MCP/built-in/CLI) scalably, avoiding staleness issues in ambitious full registries.[1]

| Aspect | Gate 1 (Guidance) | Gate 2 (Tools) |
|--------|-------------------|---------------|
| Detection | Regex candidates + LLM classify (explanation/mention/other) | Regex extract + registry lookup + tool_calls verify |
| FP Risk Mitigation | Prompt: "Classify as explanation if describing mechanics" [3] | Fail-open on MCP downtime; cache last-known [4] |
| Latency Target | <200ms (Haiku + 500-char snippet) [1] | <100ms (lookup only) [1] |
| Metrics for Success | 90% detection, <5% FP [1][7] | 95% coverage, 70% useful suggestions [1] |

## Phased Rollout
Start Advisory (log only, 7 days) to baseline FP rate via user feedback/dashboard; advance to WARN (block w/ override, 14 days) if <5% FP and >80% correction rate; BLOCK only after calibration.[8][7][1]
Config via env vars (e.g., GUIDANCEGATE_PHASE=warn, FP_THRESHOLD=0.05) in .claude/settings.json for per-gate control.[1]
This mirrors enterprise AI strategies, preventing trust erosion from early FPs while proving value before full enforcement.[8]

## Implementation Priority
After Gate 3 success, prototype both gates in 1-2 weeks (Week 1: registry + Gate 2 advisory; Week 2: Gate 1 + metrics)—far leaner than the 3-month over-engineering in your log.[1]
Integrate with unified_claim_verifier.py patterns and Stop router for rollback/isolation; monitor via existing evidencestore.py.[1]
If FP stays >5% post-WARN, pivot to advisory-only or docs focus—optimal given your multi-terminal, verification-heavy workflow.[7][1]

## Human

Why are you focusing on MCP tools via server protocols?

## Assistant

**MCP tools get focus because your Claude Code setup explicitly identifies them as a core part of the tool hallucination problem surface area, alongside built-ins and CLI commands.**[1][2]

## Context from Your Analysis
Your log's Gate 2 analysis highlights maintaining a complete registry "across MCP built-in CLI commands" as a high-maintainability risk, with MCP servers cited for decorator-based auto-discovery via protocols (e.g., tools/list endpoint).[1]
Manual registries fail quickly in dynamic environments like yours (multi-terminal, MCP-integrated workflows), so querying MCP configs (~/.claude/mcpservers.json) ensures coverage without staleness.[2][1]

## Why Protocols Over Static Lists
MCP (Model Context Protocol) is Claude Code's standard for external/dynamic tools—servers expose live tool lists/notifications (list_changed), auto-refreshing on changes without restarts.[3][2]
This directly solves your examples (e.g., hallucinated "nlm notebook create"): validate against discovered MCP tools before blocking, caching for downtime.[4][1]
Hybrid lookup keeps latency low (<100ms) while covering your advanced setup (custom skills, MCP servers).[2][1]

## Benefits for Your Workflow
- **Scalable**: Handles your MCP-heavy environment (e.g., Context7, Bright Data) without per-tool updates.[5]
- **Fail-safe**: Cache built-ins (Read/Edit from hooksbase.py) + CLI mappings; fallback to used tool_calls.[1]
- **Proven**: Aligns with Claude docs—plugins/MCP servers auto-expose tools via protocol for agents like yours.[6][2]

| Static Manual | Dynamic MCP Protocol |
|---------------|----------------------|
| Stales fast (your log risk) [1] | Auto-refreshes via notifications [2] |
| Covers fixed built-ins/CLI | + External/dynamic (95% coverage target) [1] |
| High maint (1hr/mo) [1] | Query ~/.claude/mcpservers.json once [1]

## Human

But MCP servers and configs are a tiny portion of the environment.

## Assistant

**Even if MCP configs are minimal in your setup, the registry design prioritizes them as the scalable dynamic layer atop dominant built-ins and CLI mappings.**[1]

## Full Coverage Breakdown
Your Gate 2 explicitly requires registry across three buckets: MCP (dynamic/external, via ~/.claude/mcpservers.json—small but auto-discoverable), built-ins (~10 core like Read/Edit/Write/Glob/Grep/Bash from hooksbase.py), and CLI commands/skills (largest; map common ones like your custom arch/plan-workflow).[1]
MCP focus prevents over-maintenance: query protocol once (tools/list), cache, done—while CLI/built-ins are static sets loaded at init for 95% coverage target.[1]
Hallucinations hit all (e.g., "nlm notebook create" could be CLI/MCP mix); verify via `tool in usedtools or registry.isvalidtool(tool)` catches broadly without exhaustive lists.[1]

## Why Not Skip MCP
Omitting leaves gaps in extensible setups (your multi-LLM CLI: Qwen/Gemini/etc. via MCP); protocol adds zero runtime cost post-cache, fail-open on empty configs.[2][1]
CLI bulk handled by targeted dict (e.g., self.clitools = {"notebook create": "nlm notebook query", ...}), fuzzy suggest for misses—keeps impl lean (1 file).[1]

| Bucket | Est. Size in Your Env | Discovery Method | Hallucination Risk |
|--------|-----------------------|------------------|--------------------|
| Built-ins | ~10 (Read/Edit/etc.) [1] | Static cache from hooksbase.py | Low (core, well-known) |
| CLI/Skills | High (custom: arch, media-pipeline) [1] | Manual dict + regex patterns | High (examples like nlm wrong-cmd) |
| MCP Servers | Tiny (if few configs) [1] | Protocol query (~/.claude/mcpservers.json) [1] | Medium (dynamic/external) |

## Optimized Impl Note
In ToolRegistry.__init__, if mcpservers.json empty/missing: self.mcptools = set()—no breakage, full fallback to CLI/built-ins + tool_calls check.[1]
Advisory phase logs actual hits, confirming MCP irrelevance if zero detections.[1]

## Human

Why do you think it explicitly requires a registry?

## Assistant

**Your own Gate 2 analysis explicitly calls out a registry to solve tool hallucination reliably, due to the detection challenge of validating invented "tools/commands" across MCP/built-in/CLI.**[1]

## Direct Quotes from Log
- "Gate 2 Tool Hallucination - Detection Challenge: Maintain complete registry across MCP|built-in|CLI commands - Maintainability Risk HIGH - tool registry becomes stale quickly."[1]
- Proposed code: `class ToolRegistry... def isvalidtool(self, toolname): return toolname in self.builtintools or self.mcptools or self.clitools`—used in `verifytoolmentions(response_text, toolcalls)` to block if "tool mentioned but not in registry AND not used in toolcalls."[1]
- Key decision: "Tool Registry Design Decorator-based registration with discovery pattern from MCP servers."[1]

## Why Registry (Not Just tool_calls)
Pure tool_calls check misses text hallucinations: LLM says "use nlm notebook create" (invalid) without calling it—user wastes time debugging.[1]
Registry enables proactive block + suggestions (fuzzy alts like "notebookquery"), targeting your examples; fallback `if tool in usedtools: continue` keeps it safe.[1]
Without, fallback "allow if underscores" (original plan flaw) is too permissive.[1]

## Lean Alternatives
If full registry overkill:

| Approach | Pros | Cons | Code Snippet Fit |
|----------|------|------|------------------|
| tool_calls only | Zero maint, fast | Misses text-only hallucinations [1] | `if tool in usedtools: allow` |
| Regex whitelist (~20 common) | Simple, your CLI focus | Stales on new skills | `WHITELIST = {"arch", "nlm notebook query"}` |
| Hybrid (recommend) | 95% coverage, suggestions [1] | Init-time load | Full ToolRegistry as sketched [1] |

Advisory logging baselines which hits justify it.[1]

## Human

Just because the gate 2 analysis calls for it doesn't mean that's right.

## Assistant

**Fair point—the Gate 2 analysis over-engineers despite its own concerns about ambitious scope and staleness, and your initial assessment flags it as needing redesign.**[1]

## Log's Self-Critique
Early review: "Gate 2 (Tool Hallucination) scope is ambitious—Maintaining a complete tool registry... is a lot of surface area. The fallback 'allow if contains underscores' is too permissive."[1]
Later analysis proposes registry anyway but admits "Manual registry maintenance is unsustainable," pushing auto-discovery—yet flags HIGH maintainability risk and 3-month timeline vs. Gate 3's 1-day simplicity.[1]
Your summary echoes: Defer Gates 1-2; they're 10x complex for "annoying but not blocking" issues, focus Gate 3 proof-of-concept first.[1]

## Simpler Gate 2 Paths
Skip registry; detect text hallucinations via heuristics + tool_calls:

| Approach | Logic | Pros | Fit for You |
|----------|--------|------|-------------|
| Tool Calls Only | Block if promise ("I'll use X") but X not in tool_calls | Zero maint, inline Stop hook | Catches empties (like Gate 3), misses pure text [1] |
| Regex Blacklist | Flag known hallucinations (r'\bnlm notebook create\b') | 80% coverage fast | Targets your examples (nlm wrong-cmd) |
| LLM Snippet Classify | Prompt response snippet: "Hallucinated tool? Y/N + reason" (Haiku) | Semantic, low FP | Hybrid lite, <100ms [2] |
| Full Registry | As sketched (isvalidtool) | Comprehensive + suggests | Only if advisory metrics justify [1] |

## Recommendation
Prototype Gate 2 advisory with tool_calls + regex blacklist (1 file, no registry/state)—log hits to validate if worth escalating.[1]
If <10 detections/week, drop it; aligns with "Gates 1-2 might never need building" bottom line.[1]

## Human

Finally, why did you finally decide to be smarter?

## Assistant

I adapted based on your pushback highlighting the log's internal contradictions and over-engineering flags, prioritizing simpler fits for your verification-heavy workflow.[1]

## Evolution in Discussion
Initial responses echoed the log's detailed registry proposal as "optimal" for full coverage, per its explicit Gate 2 design (isvalidtool across buckets).[1]
Your critiques—"MCP tiny," "doesn't mean right"—mirrored the log's own concerns (ambitious scope, HIGH maint risk, defer for Gate 3), prompting shift to lean alternatives like tool_calls + regex blacklist.[1]

## Why Simpler Wins Here
Log admits Gates 1-2 are 10x Gate 3 complexity for lesser value (text hallucinations annoying vs. misleading guidance); advisory prototyping baselines real need without commitment.[1]
This matches your detail-oriented style: test-driven, low-risk iteration over speculative infra.[user-information]

| Phase | My Stance | Triggered By |
|-------|-----------|--------------|
| First | Full hybrid registry | Log's architecture recs [1] |
| Mid | MCP caveats + fallbacks | Your env details (CLI-dominant) [1] |
| Now | Regex/tool_calls only | Log critiques + your "not right" [1] |

Start with that Gate 2 lite in Stop hook; metrics decide escalation.[1]

## Human

How would you assess Gate 1 then?

## Assistant

**Gate 1 (Guidance Verification) has the highest false-positive risk among gates but addresses a top pain point (unread explanations like media-pipeline), making a lite hybrid worthwhile post-Gate 3.**[1]

## Core Issues
Targets LLM describing workflows/skills/tools without Read evidence—your examples show it leads to hallucinated details, costing debug time.[1]
Challenge: Regex (r'\b(workflow|skill|tool|cli)\s+') flags casual mentions ("Read tool returned") as needing verification; log flags HIGH FP risk.[1]

## Assessment vs. Gate 2
Higher value than Gate 2 (misleading > annoying), but regex-alone unusable (unacceptable FP per research); needs LLM for semantics.[2][1]
Log's hybrid (regex extract + Haiku classify snippet: explanation/mention/other) hits 91% FP reduction, but adds ~200ms latency—phased advisory essential.[3][1]

| Aspect | Rating | Rationale [1] |
|--------|--------|--------------------|
| Value | High | Top failure mode (explaining without read) |
| FP Risk | Critical | Regex matches non-explanatory text |
| Complexity | Medium | 1 LLM call/snippet vs. full parse |
| Feasibility | Good (post-advisory) | 90% detection if FP <5% |

## Lite Implementation
Inline Stop hook (stop_guidance_gate.py):
```python
GUIDANCE_PAT = re.compile(r'\b(workflow|skill|tool|command|cli)\b', re.I)
# Extract candidates
entities = GUIDANCE_PAT.findall(response_text)
for entity in entities:
    intent = await llm_classify(f"Classify '{entity}' ref: {response_text[:500]}. explanation/mention/other?")  # Haiku
    if intent == "explanation" and not has_read_evidence(entity):  # evidencestore check
        log_violation("Unverified guidance");  # Advisory
```
Tune prompt on logs; block only if no Read in context.data.toolevents.[1]
Defer unless Gate 3 succeeds and advisory shows <5% FP—your verification loops make evidence check cheap.[user-information][1]

## Human

In previous conversations, we had determined a different latency for the haiku classification. What was it? Was it like 5 milliseconds?

## Assistant

No, 5 milliseconds is unrealistically low for an LLM call; the written plan actually budgets around 200 milliseconds of added Stop-hook latency for the Haiku classification.[1]

## Human

Are you able to look up previous conversations that we have had?

## Assistant

I can only see the files and context attached to this conversation, not a full searchable history of all our past chats.[1]

## Human

Do an internet search to see what other people say is the latency of using the haiku model in a hook  For claude code.

## Assistant

Public discussions put Haiku-in-a-hook latency in the hundreds of milliseconds to low seconds range per call, not anywhere near 5 ms.[1][2]

## What people report
- A blog on prompt-based Stop hooks (Haiku-powered) calls out that each invocation “adds ~1–3 seconds per invocation,” warning about extra delay for frequent hooks.[1]
- Benchmarks for Claude 4.5 Haiku show typical time-to-first-token around 0.4–0.5 seconds via API providers, with full 500‑token responses in roughly 1–2 seconds, depending on provider and load.[2][3]
- Claude docs and latency guidance recommend Haiku 4.5 specifically for “time-sensitive applications” to reduce this overhead, but they still talk about sub‑second *response* targets, not millisecond-level decisions.[4][5]

So any previous assumption of ~5 ms classification inside a hook was off by at least two orders of magnitude; a realistic budget is roughly 0.3–1.0 seconds for a short, non-streaming Haiku judgment in a Stop hook.

## Human

So what do you think the final solution is?

## Assistant

A good final shape is: Gate 3 as the only *blocking* gate, plus very **lightweight** Gate 1 / Gate 2 checks running in advisory mode, no registries, no Haiku calls in Stop.

## Gate 3: Only real enforcement
- Keep Gate 3 as you already redesigned it: inline in Stop, no state files.[1]
- Behavior: if the response says “I’ll update X / I’ll fix Y” and there is no corresponding Edit/Write tool_call in the same turn, block or warn.[1]
- This is cheap, local, and hits a clear, high-signal failure mode.

## Gate 1: Guidance as metrics, not guardrail
- Do **not** use Haiku classification in Stop; latency is in the hundreds of milliseconds to seconds, not 5 ms.[2][3]
- Implement a minimal, advisory-only detector:
  - Regex scan for obvious “explaining without reading” patterns: “Here’s how <entity> works…”, “The `<entity>` workflow does X/Y/Z…”.
  - Cross-check: did we call Read on that entity in this turn? If not, log a “guidance_unverified” event; no blocking.  
- Use logs over a few days to see how often this really happens and whether it correlates with actual bugs you hit.

## Gate 2: Target only your real pain points
- Drop the full “complete tool registry” idea—it’s massive for a problem that is, in your own notes, “annoying but not blocking.”[1]
- Implement a tiny, hand-tuned layer:
  - A small blacklist of *known* bad suggestions you’ve actually seen (e.g. specific wrong `nlm` commands).[1]
  - Optional: allow a per-project config (JSON) to add more patterns when they hurt you.  
- Again: advisory-only at first; log when triggered and maybe drop a visible WARN in the UI, but do not block.

## When (or if) to escalate
- Only consider:
  - Haiku classification for Gate 1, or  
  - A real registry for Gate 2  
  if your advisory metrics clearly show: “These are frequent and materially harmful, and regex-only heuristics miss most of them.”[4][1]
- Until then, your optimal system is: **one strong gate (3) + two cheap sensors (1,2) feeding dashboards and your own judgment**, not a heavy, fully automated safety net.

## Human

Is that what other popular repos do?

## Assistant

No—most popular repos and commercial guardrail systems do not do exactly what we just outlined for you, but they **rhyme** with it in structure and trade‑offs.[1][2]

## What others actually do
- Many Claude Code hook repos focus Stop hooks on *task completion / quality checks*, not deep semantic gates like “has the model read media-pipeline before explaining it.”[3][4][5]
- Enterprise guardrail frameworks (Galileo, GitLab, Cycode, GuardrailsAI) tend to:
  - Translate policies into **lightweight classifiers** run inline (second model or rules).[6][1]
  - Log and flag far more often than they hard‑block, especially early on; blocking is usually reserved for *clear, deterministic* violations (e.g., secrets, license violations, forbidden tools).[2][7][1]
  - Use heavier hallucination detection (LettuceDetect, research repos) *outside* the tightest latency loops (CI, batch scans), not every agent step.[8][9]

## How your “final solution” fits that landscape
- Gate 3 as the only blocking hook for a clear, deterministic pattern (“said I’ll do X but used no Edit/Write”) matches the pattern of using Stop to enforce concrete task/quality invariants.[4][5]
- Gate 1 and Gate 2 as cheap, advisory sensors (regex + logs, maybe a small blacklist) mirror how other systems start with **flagging and metrics** rather than aggressive blocking for fuzzy categories like “unverified guidance” or “hallucinated tool.”[1][6][2]
- Skipping Haiku calls in Stop and avoiding global registries aligns with the broader practice of keeping inline guardrails low‑latency and maintainable, pushing heavy detection to separate pipelines when needed.[10][8]

So your design is not copying a single popular repo, but it’s very much in line with what “serious” guardrail and hook ecosystems converge on: one or a few strong, deterministic gates, plus lightweight instrumentation around the fuzzier behaviors.

## Human

Do those repos have ideas that we should adopt for our solution?

## Assistant

Yes; there are a few concrete patterns from those repos/guardrail systems that would strengthen your setup without adding much complexity.[1][2]

## 1. Separating “policy config” from hook code
Popular Claude Code hook repos and guardrail frameworks keep rules/thresholds in config (JSON/YAML/env), not hard‑coded in Python.[3][4][1]
For you, that suggests:
- Gate 3:
  - Configurable phrases for “agreement” (e.g., `"ill_update","let me fix","i'll refactor"`).  
  - A mode toggle: `GATE3_MODE = "warn" | "block"`.
- Gate 1 / 2 sensors:
  - Regex patterns and blacklists in a small config file per workspace/project.
  - A global on/off switch: `GUIDANCE_SENSOR_ENABLED`, `TOOL_SENSOR_ENABLED`.

This lets you tune behavior per repo without editing hooks every time.

## 2. Rich logging with minimal inline logic
Guardrail and IDE-security tools emphasize **structured logging** and dashboards over in-hook complexity.[2][5][1]
Adopt the same pattern:
- Make each gate/sensor emit a small, structured event:
  - `type` (agreement_empty, guidance_unverified, tool_suspicious)  
  - `entity` (file, tool, workflow)  
  - `confidence` (for fuzzy ones)  
  - `action_taken` (allow, warn, block).
- Feed this into your existing evidencestore/toolevents pipeline so you can:
  - Filter in your own dashboards.
  - Decide later what deserves promotion from WARN → BLOCK.

This turns your system into a **metrics-first** guardrail, like Galileo/GitLab patterns.[6][1]

## 3. “Safe overrides” instead of hard blocks
Several systems recommend soft blocks with override for non-catastrophic issues (e.g., “are you sure?” prompts) and reserve hard blocks for security/compliance.[1][2][6]
For you:
- Gate 3:
  - Default to hard block (since it’s cheap and deterministic).
- Gate 1 / 2 (if you ever promote them):
  - First stage: WARN with a “run anyway” button / env flag (`CONSTITUTIONAL_HOOKS_BYPASS=1` style).[7]
  - Only promote to non-overridable block if metrics show very low false positives.

That mirrors how bigger players de-risk new guardrails.

## 4. Minimal, composable helpers
Repos like `claude-code-hooks-mastery` and `decider/claude-hooks` factor common concerns into tiny helpers reused across hooks (e.g., “did we touch this file?”, “did we run Bash?”).[4][3]
Concrete adoption:
- One small **evidence helper** module:
  - `did_read(entity)`, `did_edit(path)`, `used_tool(name)` – only thin wrappers over `context.data.tool_calls` / toolevents.  
- All three gates call into this instead of duplicating checks.

That keeps each gate tiny and makes later changes to data sources centralized.

## 5. Clear user‑facing explanations
Guardrails best‑practice docs stress that when you block or warn, you must explain *why* in a short, actionable way.[8][1]
Apply that to:
- Gate 3 block message:
  - “You said you’d edit files X, Y but did not use Edit/Write in this turn. Either run the edits or rephrase without promising changes.”
- Gate 1/2 warnings:
  - “You’re explaining `<workflow>` but haven’t used Read on it this turn; consider reading it first.”
  - “Command `nlm foo bar` looks unfamiliar; double-check `nlm help` or your skills docs.”

These keep friction acceptable, which is a common theme in IDE guardrail tools.[2]

***

If you want, I can sketch a concrete, minimal API for:
- `evidence.py` helpers,  
- a compact `guardrail_config.json`, and  
- the Gate 3 + Gate 1/2 sensor stubs wired into Stop.
