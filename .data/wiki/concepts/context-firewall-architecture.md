---
title: "Context firewall architecture: 3-layer model dispatch"
created: 2026-07-24
source: session-2026-07-24 (operator question on agent context firewalls)
tags: [models, architecture, context, firewall, agents, optimization, extraction]
summary: >
  Three-layer dispatch pattern that prevents raw file content and search results
  from polluting the orchestrator's context. Layer 1 (extraction pool) reads bulk
  content via script-called completion models. Layer 2 (agent pool) does tool-use
  work in bounded subagents. Layer 3 (orchestrator) sees only summaries and makes
  decisions. The script IS the firewall -- the orchestrator calls a script, gets
  JSON, never touches raw content.
agent: grok
host: grok
cognitive_load: 3
verification: operator-validated-design
relations:
  - target: wiki/concepts/model-pool-selection-policy-speed-quota-diversity
    type: implements
  - target: wiki/concepts/model-fleet-provider-pools
    type: depends-on
  - target: wiki/concepts/diffusiongemma-direct-api-howto
    type: implements-layer-1
  - target: wiki/concepts/llm-handoff-best-practices
    type: complements
---

# Context firewall architecture: 3-layer model dispatch

## External validation (/www research 2026-07-24)

The 3-layer pattern is **structurally standard**. The industry uses different
names but the same architecture. Key external references:

- **Anthropic "Effective context engineering" (Sep 2025):** introduces
  "compaction" (our Layer 1) and "sub-agent architectures" (our Layer 2+3
  split). Quote: "specialized sub-agents can handle focused tasks with clean
  context windows... returns only a condensed, distilled summary (often
  1,000-2,000 tokens)." This is the authoritative public statement of the
  pattern. Source: anthropic.com/engineering/effective-context-engineering-for-ai-agents
- **Anthropic multi-agent research system (Jun 2025):** production
  implementation — 15x token cost vs single-agent, but outperforms on complex
  research. Validates that context isolation is worth the cost.
- **LangChain "Context Engineering" (Jul 2025):** organizes the space into
  write / select / **compress** (Layer 1) / **isolate** (Layer 2+3). Our
  pattern maps cleanly onto their taxonomy.
- **FrugalGPT (2023) / RouteLLM (ICLR 2025):** academic foundation for
  capability-tiered routing (try cheap, score, escalate).
- **3-tier model router (MindStudio, AWS, LeanLM):** industry-standard
  Fast/Smart/Power tiering. Our layers map to these tiers but compose them
  across pipeline stages, not per-request.

### What the term means externally

"Context firewall" is used externally but has two meanings:
- **Meaning A (dominant, ~80%):** security firewall — prompt injection defense,
  PII filtering. We do NOT mean this.
- **Meaning B (minority but validated):** context isolation — Boris Cherny
  (Claude Code creator) coined it; the "Harness Effect" paper references a
  "context-firewall contract"; a Zhihu systems-engineering article labels it
  "Layer C: Sub-Agent Isolation (The Context Firewall)." This IS our meaning.

**When communicating externally:** prefer "context isolation" or "sub-agent
isolation" (Anthropic/LangChain vocabulary) to avoid collision with security
firewalls. Keep "context firewall" as the internal term.

### What's standard vs novel in our approach

**Standard (industry already does this):**
- Sub-agent isolation with own context window (Anthropic, LangChain, CrewAI)
- Map-reduce summarization of bulk content (LangChain, Google Cloud)
- Three-tier model selection (MindStudio, AWS)
- Score-based cascade escalation (FrugalGPT, RouteLLM)

**Novel (our deliberate departures):**
1. **The firewall is a Python script, not an LLM decision.** Most systems let
   the orchestrator LLM decide when to compress. We make the orchestrator call
   a deterministic script. See "Trade-offs" below for why this is both a
   strength and a risk.
2. **Explicit completion-only extraction pool as Layer 1.** Most routing
   systems treat all models as tool-use capable. We separate completion-only
   models (DiffusionGemma) into their own pool that must be script-called.
3. **3-layer composition per pipeline stage, not per-request.** The 3-tier
   router industry pattern selects one tier per user request. Our pattern
   composes tiers across stages of a single request's lifecycle.

## The problem

The orchestrator LLM (parent Grok) has a finite context window. When it reads
raw files, search results, or API responses directly, it consumes context with
content that the downstream decision does not need. A 40KB app.py, a 10K-word
wiki page, 20 search results with full page content -- these pollute context
that should be reserved for reasoning, synthesis, and decision-making.

The naive fix (read everything into context) causes:
- Context pressure -> degraded reasoning quality
- Longer latencies (more tokens to process)
- Lost signal (key facts buried in noise)
- Higher cost (orchestrator-tier tokens burned on reading)

## The pattern: 3 layers with context firewalls

```
Layer 1: EXTRACTION (script-called, completion-only, cheap, fast)
  |  Reads bulk content via direct API script
  |  Returns: extracted facts, summaries, structured data (JSON)
  |  Never touches orchestrator context
  v
Layer 2: AGENT (spawn_subagent, tool-use, mid-tier, bounded scope)
  |  Receives Layer 1 output (or reads files directly with tools)
  |  Iterates: reads files, runs tests, edits code
  |  Returns: structured findings, verdicts, diffs
  |  Firewall: only the summary returns to orchestrator
  v
Layer 3: ORCHESTRATOR (parent LLM, expensive, limited context)
  Receives only Layer 2 summaries + Layer 1 extractions
  Makes decisions, synthesizes, writes final output
  NEVER reads raw files or search results directly
```

**Key invariant:** each layer sees only the output of the layer below, never the
raw input. The orchestrator's context budget is reserved for judgment, not
reading.

## Layer 1: The extraction pool

### What it is

Completion-only models called via **Python scripts**, not `spawn_subagent`.
The script:
1. Reads file(s) from disk
2. Constructs a prompt with the file content
3. Calls the model's API directly (HTTP request)
4. Parses the response
5. Returns structured JSON to the caller

The orchestrator never sees the raw file. It calls `python extract.py <files>`
and gets back JSON.

### Why script-called (not spawn_subagent)

If the orchestrator LLM manages the extraction call (construct prompt, parse
response, decide what to extract), the orchestration overhead pollutes its own
context. The firewall must be a **script call** -- one command, one JSON
response. The script handles everything internally.

`spawn_subagent` is for Layer 2 -- it gives the subagent its own context,
tools, and iteration loop. Layer 1 does not need iteration; it needs speed and
context isolation.

### Pool members

| Member | Provider | Context | Speed | Role |
|---|---|---|---|---|
| `nvidia-diffusiongemma-26b` | NVIDIA | 262K | ~600ms-3.7s | Primary -- fastest, batch, free |
| `gemma-4-31b-it` | Google | 131K | 5094ms | Fallback -- if NVIDIA 429 |
| `gemini-3.5-flash-lite` | Google | 1M | `[UNMEASURED]` | Fallback -- large context |
| `nvidia-nemotron-3-ultra` | NVIDIA | 1M | `[UNMEASURED]` | Fallback -- reasoning-quality extraction |

Defining property: you pass everything in the prompt and get one response. No
tool use, no file access by the model. The script IS the firewall.

### Existing implementation

`P:/.agents/scripts/models/dgemma_read.py` -- modes: single, `--enhanced`
(3-perspective merge), `--batch` (multiple files in one call). This is the
canonical Layer 1 implementation.

### What needs building

A generalized extraction utility that any skill can call:

```powershell
python P:/.agents/scripts/models/extract.py <files...> --prompt "extract all function signatures and their return types" --format json
```

This would:
- Accept N file paths
- Read them, merge into one prompt (respecting context limits)
- Call DiffusionGemma (or fallback if NVIDIA is down)
- Return structured JSON
- Be callable from any skill's orchestrator as one command

This does NOT exist yet -- `dgemma_read.py` does reading/summarization but is
not a general-purpose extraction utility. The build is a follow-up task.

## Layer 2: The agent pool

### What it is

Tool-use models dispatched via `spawn_subagent`. Each subagent has its own
context window, can read files, run commands, and iterate. It returns only its
structured findings to the orchestrator.

### Pool members

Per the domain table in [[model-pool-selection-policy-speed-quota-diversity]]:
- Mechanical / code-reading: `zen-deepseek-v4-flash-free`
- Code generation: `minimax-m3`
- Reasoning / planning: `glm-5-2`
- Multimodal: `minimax-m3`

### How it firewalls

The subagent's full context (file contents, command outputs, reasoning) stays
inside the subagent. Only the structured response crosses the boundary back to
the orchestrator. The orchestrator sees: "PASS, 5 tests passed, no issues
found" -- not the 50KB of file content the subagent read to reach that verdict.

### Skills that already implement this correctly

| Skill | How it firewalls | Status |
|---|---|---|
| `/check` | Verifier subagents do all reading, return PASS/FAIL + issues | GOOD |
| `/go` H4 | Implementation subagents do the work, parent synthesizes | GOOD |
| `/review` | Specialists inspect code, return FINDINGS.md | GOOD |
| `/preflight` | Script-first (`discovery_audit.py`), then synthesis | GOOD (script is Layer 1) |

### Skills that violate the firewall

| Skill | Violation | Fix |
|---|---|---|
| `/web` | Returns raw search results to parent | Add Layer 2 distillation before parent sees results |
| `/www` | Research subagent can dump large content to parent | Ensure research subagent returns distilled findings only |
| `/wiki` | Parent reads large wiki pages directly | Use Layer 1 extraction for pages >5K words |
| `/go` H3 | Discovery can dump file contents into parent | Discovery packet consumed by Layer 2 synthesizer |

## Layer 3: The orchestrator

### What it is

The parent LLM (Grok). Receives only:
- Layer 1 extractions (JSON facts from scripts)
- Layer 2 summaries (structured findings from subagents)
- User messages
- Its own reasoning

### What it should NEVER do

- Read raw files directly when a Layer 1/2 alternative exists
- Receive raw search results (distill first)
- Process more than ~5K words of raw content from any single source

### Exceptions (when direct reading is correct)

- Quick reference checks (read a specific line of a specific file)
- Small files (<500 words) where the overhead of delegation exceeds the benefit
- Decision-critical content the orchestrator must reason about directly (a
  contract, a schema, a specific code block under review)

The principle: **direct reading is fine for small, targeted reads. Bulk reading
should always go through Layer 1 or Layer 2.**

## Integration with model-benchmark telemetry

The `/model-benchmark` telemetry tracks which layer each call operates in:

- `task_domain: "extraction"` -> Layer 1
- `task_domain: "mechanical" / "code-verification" / "code-generation"` -> Layer 2
- `task_domain: "reasoning" / "adversarial"` -> Layer 2 or Layer 3

This allows the analysis script to report per-layer latency and success rates,
validating that the firewall is working as designed.

## When this architecture is wrong (falsifier)

### General falsifiers (apply to any context firewall)

1. **Layer 1 extraction loses critical signal.** If the completion model's
   summary drops the exact detail the decision needs, the firewall caused a
   worse outcome than direct reading. Mitigation: use `--enhanced` mode
   (3-perspective merge) for high-stakes extraction; or escalate to Layer 2
   (agent with tools) when extraction quality is uncertain.

2. **Delegation overhead exceeds the work.** If the file is 200 lines and the
   orchestrator needs one specific function, calling a Layer 1 script to
   "extract" it is slower than just reading the file directly. The firewall
   is for bulk content, not targeted reads.

3. **The orchestrator needs the full context to make the decision.** Some
   decisions (architecture choices, cross-file refactoring) require seeing
   the full picture. In these cases, the orchestrator should read directly --
   the firewall is an optimization, not a constraint.

### Script-firewall trade-offs (our specific design choice)

Our firewall is a **deterministic Python script**, not an LLM-orchestrated
decision. This is a deliberate departure from how most production systems work
(Anthropic, LangChain, CrewAI all let the orchestrator LLM decide when to
compress). The trade-offs:

**Strengths of the script approach:**
- **Determinism.** Same extraction prompt + same file = same result every time.
  An LLM-orchestrated firewall introduces variance — the extraction changes
  each run. For a fleet running the same task across terminals, determinism
  matters.
- **Context isolation is guaranteed.** The orchestrator literally cannot see
  raw content — the script returns JSON. With an LLM firewall, the orchestrator
  sees raw content first, then decides to summarize it, burning context on the
  read before the compression.
- **Cheap to run.** Layer 1 uses DiffusionGemma (free, ~600ms-3.7s). An LLM
  firewall would use orchestrator-tier tokens for every compression decision.

**Risks of the script approach:**

1. **Extract-then-need mismatch (SERIOUS).** The script extracts what it was
   told to extract. But the orchestrator may discover mid-reasoning that it
   needs something different. With an LLM firewall, the orchestrator re-queries
   naturally. With a script firewall, you either: re-run (latency cost),
   extract broadly (losing compression), or give up and read raw (firewall
   failed — raw content enters context anyway, but only after the wasted
   Layer 1 call). **Mitigation:** Layer 2 agents (with tools) can re-read
   files when extraction is insufficient. The script firewall is Layer 1 only;
   Layer 2 is always available as fallback.

2. **Signal loss on novel content (SERIOUS).** A script extracting "function
   signatures" won't surface "this file also has a SQL injection." An LLM
   reading raw content might notice the unexpected. The firewall hides
   anomalies along with noise. **Mitigation:** use Layer 2 agents (with full
   file access) for security review, architecture analysis, and any task where
   "I might find something unexpected" is the point. Layer 1 is for known-shape
   extraction (signatures, metrics, structured data), not exploratory reading.

3. **Cross-file pattern blindness (SERIOUS).** The script extracts each file
   independently. Cross-file patterns ("function A in file X calls function B
   in file Y which has a bug") are lost at Layer 1. An LLM reading raw files
   sees these directly. **Mitigation:** Layer 2 agents can read multiple files
   and correlate. Use Layer 1 for per-file extraction, Layer 2 for cross-file
   analysis.

4. **Rigidity vs adaptivity (moderate).** An LLM firewall adapts its extraction
   to the current question. A script firewall has a fixed prompt per call.
   Mitigation: pass extraction intent as a script parameter
   (`--prompt "extract error handling logic"`). This adds flexibility without
   surrendering determinism.

5. **Maintenance burden (moderate).** Each extraction task needs its own prompt
   template. The script library grows over time. Mitigation: a general-purpose
   `extract.py` with `--prompt` parameter covers most cases without separate
   scripts per task.

6. **Context re-introduction risk (moderate).** If Layer 1 extraction is
   insufficient and the orchestrator escalates to reading raw, the raw content
   enters context — but only after the latency cost of the failed Layer 1 call.
   Net worse than reading directly. **Mitigation:** Layer 1 should extract
   generously when uncertain — return more than the orchestrator thinks it
   needs, not less. The cost of over-extraction is lower than the cost of
   re-introduction.

7. **Overuse trap (manageable).** Once the firewall exists, there's a
   temptation to route everything through it — even small files where direct
   reading is faster. **Mitigation:** explicit threshold — Layer 1 only for
   files >5K words or >500 lines. Below that, the orchestrator reads directly.

**When the script approach is correct:**
- The orchestrator's context budget is the binding constraint (our fleet)
- Reproducibility matters (deterministic extraction = same result each time)
- Extraction tasks are bounded and predictable (file reading, search
  distillation, metric extraction)
- The orchestrator knows what it needs before calling the script

**When the script approach is wrong:**
- The extraction target is unknown until mid-reasoning (use Layer 2 agent)
- Cross-file pattern detection IS the task (use Layer 2 agent with multi-file
  access)
- The content is small enough that direct reading is cheaper than delegation
  (read directly)
- The task is exploratory ("what's interesting in this codebase?") rather than
  extractive ("list all functions that call database.query()")

## Relationship to existing concepts

- **Implements** [[model-pool-selection-policy-speed-quota-diversity]] -- the
  domain table's firewall-layer column is defined here
- **Depends on** [[model-fleet-provider-pools]] -- the extraction pool members
- **Implements Layer 1** via [[diffusiongemma-direct-api-howto]] -- the
  `dgemma_read.py` script pattern
- **Complements** [[llm-handoff-best-practices]] -- handoffs are a form of
  context firewalling across sessions; this concept is intra-session

## Source

Operator question during session 2026-07-24: "Are we optimally structuring /www
/web /wiki /preflight etc, to use agents as context firewalls while still
optimizing quality that gets to the orchestrating LLM?" -- refined with "can we
do this with code so that it doesn't defeat the purpose?" (i.e., the firewall
must be a script, not LLM-managed orchestration).

## Auto-related

- [[model-pool-selection-policy-speed-quota-diversity]]
- [[diffusiongemma-direct-api-howto]]
- [[model-fleet-provider-pools]]
