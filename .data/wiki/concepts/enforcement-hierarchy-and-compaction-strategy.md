---
title: "Enforcement hierarchy and compaction strategy for agent instruction files"
created: 2026-07-28
source: session-019fa48a (/www research on compaction best practices + enforcement mechanism selection)
tags: [agents-md, compaction, enforcement, hooks, mcp, progressive-disclosure, decision-framework, lossless, lossy]
host: both
agent: grok
verification: multi-source-verified
sources:
  - "Gilbert et al. — Semantic Compression With LLMs (arXiv:2304.12512)"
  - "LTSC — Lossless Token Sequence Compression (arXiv:2506.00307)"
  - "Liu et al. — Lost in the Middle (arXiv:2307.03172, TACL)"
  - "RAPTOR — Recursive Abstractive Summarization (arXiv:2401.18059)"
  - "Anthropic — Effective context engineering for AI agents (Sep 2025)"
  - "HumanLayer — Writing a good CLAUDE.md (Nov 2025)"
  - "GitHub Blog — How to write a great AGENTS.md (2,500 repos)"
  - "ETH Zurich — Evaluating AGENTS.md (arXiv:2602.11988)"
  - "Tyler Folkman — Stop Compressing Context"
  - "Cui et al. — Automatic Prompt Optimization via Heuristic Search (arXiv:2502.18746)"
relations:
  - target: wiki/concepts/agents-md-construction-best-practices.md
    type: extends
  - target: wiki/concepts/best-practices-enforcement-mechanism-grok-build.md
    type: extends
  - target: wiki/concepts/mechanical-enforcement-over-behavioral-reminder.md
    type: related
  - target: wiki/concepts/code-orchestrates-model-judges-skill-scale.md
    type: related
---

# Enforcement hierarchy and compaction strategy for agent instruction files

## Decision context

**Why this research was needed:** after refactoring `~/.grok/AGENTS.md` from 1,170 → 505 lines
and `P:/AGENTS.md` from 602 → 115 lines (total budget 1,679 → 620 lines), the operator asked:
(1) are "lossless maximal compaction" and "minimal lossy compaction" useful concepts for
the harder cuts? (2) when should something be a hook vs an AGENTS.md entry? (3) when should
something be an MCP server vs a hook vs a CLI vs a prompt instruction?

## Finding 1: Lossless vs lossy compaction IS established terminology and maps cleanly

The terms come from prompt compression research (Gilbert et al. 2023, LTSC 2025). They
map to instruction files as:

| Type | Definition | For AGENTS.md | Example |
|------|-----------|---------------|---------|
| **Lossless** | Perfect reconstruction possible (original recoverable) | Exact commands, schema constraints, forbidden lists, file paths | `git filter-repo` in forbidden list; `encoding='utf-8'` |
| **Lossy** | Meaning/intent preserved, exact wording discarded | Prose rationale, reference incidents, worked examples | "Why this rule exists" paragraphs; 6 worked examples |

**The practical heuristic:** if the content is a *command/exact-string that must not drift*,
it's lossless (keep inline or pointer-replace with `file:line`). If the content is
*pattern-recognition context that helps the model apply a rule*, it's lossy — safe to
compress, summarize, or move to a wiki concept.

**Key disconfirmation (Liu et al. 2307.03172):** "lost in the middle" means pointers
to wiki concepts placed mid-context can be silently ignored by the model. RAPTOR
(arXiv:2401.18059) showed hierarchical summarization outperforms chunk-based retrieval
on multi-hop reasoning. **Implication:** for load-bearing rules, inline lossy compression
(a tight rule statement) can outperform a pointer to a wiki the model never reads. The
optimal is: tight rule inline + wiki exists as fallback for deep lookup. This is what our
refactored AGENTS.md does.

## Finding 2: The enforcement hierarchy (4 levels)

There is a clear progression from "softest" to "hardest" enforcement:

```
Level 0: PROMPT INSTRUCTION (AGENTS.md / system prompt)
  → Probabilistic (~60-80% compliance under pressure)
  → Zero runtime cost
  → Zero maintenance burden
  → Fails by omission (model forgets under closure pressure)

Level 1: HOOK (PreToolUse / PostToolUse / Stop)
  → Near-deterministic WHEN it fires (~100% when matcher hits)
  → Latency cost (5-60s for Stop gates; <5ms for simple regex)
  → Maintenance burden (false positives, stale logic, platform bugs)
  → Fails silently (exit code confusion, HTTP timeouts, disabled on "unhealthy")
  → Best for: binary checks (command regex, file path, secrets)

Level 2: CLI TOOL (standalone executable invoked by model)
  → Deterministic execution, model decides when to invoke
  → Separate process, state management overhead
  → Near-zero schema overhead for the model
  → Best for: inner-loop dev work the model already knows (git, pytest, gh)

Level 3: MCP SERVER (always-available tool with schema in context)
  → Always present in tool list; model invokes on demand
  → Token cost per tool (~500-1500 tokens per tool schema)
  → Runtime infrastructure (auth, SSE/HTTP, secrets, observability)
  → Best for: shared multi-tenant systems needing OAuth, audit trails, cross-client reuse
```

### The promotion ladder (when to move up)

A rule **promotes from prompt → hook** when ALL of:
1. The model repeatedly bypasses the rule despite prompt wording
2. The check is binary/pattern-matchable (command regex, file path, secrets)
3. Failure cost is high (data loss, secret leak, destructive operation)
4. The check is fast (<5ms for PreToolUse; <60s for Stop)

A rule **promotes from hook → CLI** when:
1. The hook needs complex state the hook process can't maintain
2. The check needs multi-step execution (not a single regex/exit-code)
3. The operator wants to invoke it manually too

A capability **promotes from CLI → MCP server** when:
1. Multiple clients need the same tool (Claude, Cursor, VS Code, Grok)
2. The tool needs persistent auth/connection state (database, API)
3. Structured JSON I/O matters (not just stdout text)
4. The tool benefits from always-available discovery (model knows it exists without
   the prompt mentioning it)

### Key counter-evidence: hooks are NOT always more reliable

Hooks have documented silent-failure modes that make a poorly-tuned hook **strictly worse**
than a prompt rule:
- **Exit code confusion:** `exit 1` (conventional error) fails OPEN — only `exit 2` blocks
- **Silent disabling:** "unhealthy" HTTP hooks silently stop firing
- **Platform bugs:** Windows MSIX, subagent hook skipping, matcher parsing bugs
- **Cry-wolf fatigue:** broad hooks generate false-positive noise that masks real errors

**Implication:** a hook is only worth the maintenance burden when the rule fires
*deterministically* with *near-zero false positives* AND *failures are catastrophic*.
For everything else, a well-placed prompt rule + occasional correction is more cost-effective.

## Finding 3: Eval-driven ablation vs heuristic compaction

**The research view (ETH Zurich, Anthropic):** strip and measure. Run your task suite,
remove a rule, measure success-rate delta. Anthropic reportedly removed >80% of Claude
Code's system prompt for newer models with no eval loss.

**The practitioner view:** heuristic compression works fine for most teams. Tools like
`llm-prompt-compress`, Terse, and LangChain reorders ship without eval studies and achieve
40-75% reduction. The survey by Cui et al. (2025) catalogs multiple heuristic methods
(evolutionary, beam, bandit, MCTS) that systematically improve prompts without ablation.

**Our workspace reality:** we don't have a repeatable eval suite for AGENTS.md rules.
Until we do, heuristic compaction (the approach we used) is the right method —
keep rules, cut rationale. The risk is "selective omission" (model forgets rule N
because its pattern-recognition anchor was removed), not "refuses to engage."

## Decision matrix: where does a new rule go?

| Characteristic | AGENTS.md | Hook | CLI skill | MCP server |
|---|---|---|---|---|
| **Determinism needed** | Low (behavioral) | High (binary check) | Medium (invoked on demand) | Medium |
| **Fires every turn** | Yes (always loaded) | Only when matcher hits | Only when model invokes | Schema always loaded |
| **Latency** | 0 | 5ms-60s | Process spawn | Network/IPC |
| **Token cost** | Per-token (every turn) | 0 (hook is separate process) | 0 until invoked | Schema overhead per turn |
| **Maintenance** | Low (text edit) | High (code, tests, false positives) | Medium (CLI code) | High (server, auth, ops) |
| **Failure mode** | Omission under pressure | Silent failure / false positive | Model forgets to invoke | Connection failure |
| **Best for** | Behavioral rules, conventions, context | Safety guards, format checks, verification gates | Complex multi-step tools | Shared infrastructure, live data |

### Anti-pattern: hooking what should be prompted

Don't make a hook for something the model can reasonably decide:
- "Should I use `/tp` here?" → prompt (needs judgment)
- "Is this answer too verbose?" → prompt (contextual)
- "Did I search before proposing?" → prompt (can't mechanically verify intent)

### Anti-pattern: prompting what should be hooked

Don't keep a prompt rule for something deterministic:
- "Never run `git reset --hard`" → hook (binary check, catastrophic failure)
- "Verify file exists before editing" → hook (mechanical check)
- "Commit after each logical unit" → could be either, but hook is more reliable

## What this means for our AGENTS.md refactor

Our current state (620 lines across 2 files) is within the instruction budget. The
remaining content is:
- **Lossless rules** (forbidden lists, exact commands, file paths) — must stay inline
- **Lossy behavioral rules** (thought-partner protocol, per-turn checklist) — inline
  because the model needs them every turn and pointers would be lost-in-middle
- **Dangling wikilinks** — the progressive-disclosure promise is unfulfilled. The wikis
  either need to be created, or the inline rationale restored. Currently neither exists.

The optimal end-state is NOT "smaller AGENTS.md" — it's "every rule has its rationale
available at the right level: inline for load-bearing, wiki for on-demand."

## Falsifier

This framework is wrong if:
- Heuristic compaction produces worse instruction-following than the original bloated file
  (testable via session quality tracking — behavioral correction tracking)
- Hooks we built from this framework cause more false positives than correct catches
- The dangling wikilinks never get filled in, making the refactor a permanent capability loss

## Related

- [[agents-md-construction-best-practices]] — progressive disclosure principle
- [[best-practices-enforcement-mechanism-grok-build]] — enforcement mechanism design
- [[code-orchestrates-model-judges-skill-scale]] — the meso/macro enforcement scales
- [[mechanical-enforcement-over-behavioral-reminder]] — why gates beat prose
- [[mechanical-enforcement-hierarchy]] — the promotion ladder from prompt to code
