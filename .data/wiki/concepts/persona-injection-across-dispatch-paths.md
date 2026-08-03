---
title: "Persona injection across dispatch paths: eliminating performative reasoning via prompt-level format constraints"
created: 2026-08-03
source: session-2026-08-03 (web-page trace analysis → persona investigation → PI validation test)
tags: [personas, prompt-engineering, model-dispatch, performative-reasoning, output-format, cross-model, pi, opencode]
summary: >
  LLMs spend reasoning budget on output-format decisions when the format is
  unspecified — 7 of 9 reasoning steps in a web-page-improvement trace were
  format narration, not analysis. Prepending format-constraining instructions
  (personas) to the prompt eliminates this. Validated across three dispatch
  paths: Grok native subagent (platform persona injection as <system-reminder>),
  PI harness (prompt prepending), and OpenCode (prompt prepending or --agent).
  PI test showed 43% latency reduction and zero unsolicited extras with persona
  vs. without. The pattern: personas consumed by skills with their own format
  provide behavioral defaults only; personas consumed by ad-hoc spawns provide
  both behavior and format.
agent: grok
host: grok
cognitive_load: 2
verification: observed
sources:
  - Session 019fc5eb (2026-08-03) — PI A/B test, persona creation, tp_dispatch wiring
  - Grok Build docs 16-subagents.md — persona resolution mechanism
relations:
  - target: wiki/concepts/prompting-patterns-for-ai-agent-control.md
    type: extends
  - target: wiki/concepts/narrative-sufficiency-is-not-verification.md
    type: related
  - target: wiki/concepts/reactive-pattern-matching-and-closure-pressure.md
    type: related
  - target: wiki/concepts/mandatory-step-enforcement-code-over-prose.md
    type: complements
---

# Persona injection across dispatch paths: eliminating performative reasoning via prompt-level format constraints

## Decision context

**Why this research was needed:** the operator showed a reasoning trace where
a model spent 9 steps "improving a web page" — but 7 of those steps were the
model narrating its own output plan ("Structuring the Response," "Writing the
Code Snippets," "Final Polish"). The actual analysis was done in 2 steps. The
operator asked: "To me that implies some sort of template or prompt enhancement."

This led to investigating how to structurally prevent the model from spending
reasoning budget on format decisions, and discovering that the platform already
had the mechanism (personas) but it was underutilized and unvalidated for
external CLI dispatch.

## Key findings

### 1. Performative reasoning is a structural property of open-ended prompts

When a model receives "analyze X and report findings" without an output format
constraint, it must decide: table or prose? Sections or bullets? How many
findings? Should I add recommendations? This decision-making consumes reasoning
budget that should go to analysis. The result is longer latency, more tokens,
and often unsolicited extras (recommendations nobody asked for, "Logic Soundness
Assessment" tables that pad the output).

This is the same class as [[narrative-sufficiency-is-not-verification]] — the
model constructs a plausible analytical narrative that *feels* sufficient (the
9-step trace looks like expert work) but is mostly restatement. The trace's
internal coherence makes it *feel* like real thinking rather than what it
mostly is: the model organizing its output.

### 2. Format-constraining instructions eliminate the problem

Prepending output-format instructions to the prompt removes the format-decision
surface entirely. The model's reasoning goes to analysis, not to "how should I
structure my response?" The evidence from the PI A/B test:

| Metric | BARE (no persona) | PERSONA (file-analyzer) |
|---|---|---|
| Latency | 107s | 61s (**43% faster**) |
| Findings | ~15 + 8 unsolicited recommendations | 19 in mandated table |
| Format | Self-invented (5 sections) | Exact mandated table |
| Unsolicited extras | 8-item "Recommendations" section | Zero |
| Ending | Narrative summary | `FILES_ANALYZED: 1, FINDINGS: 19` |

Same model (nemotron-3-ultra), same file, same task. The only variable was the
persona instructions prepended to the prompt.

### 3. The mechanism works across all dispatch paths

| Dispatch path | How persona is applied | Validated? |
|---|---|---|
| **Grok native subagent** (`spawn_subagent`) | Platform resolution: instructions injected as `<system-reminder>` via persona files in `~/.grok/personas/*.toml` | ✅ (Grok docs 16-subagents.md line 72) |
| **PI harness** (`pi -p --model <m> "<prompt>"`) | Prepend persona instructions to prompt string, or use `--append-system-prompt` | ✅ (A/B test 2026-08-03) |
| **OpenCode** (`opencode run "<prompt>"`) | Prepend persona instructions to prompt, or create OpenCode agent with persona-equivalent system prompt | [INFERENCE] — same mechanism as PI; not separately tested |
| **Direct HTTP** (benchmark.py, fleet_quota.py) | Prepend persona instructions to the messages array | [INFERENCE] — same mechanism; not tested |
| **Cross-model CLI** (/agy, /codex, /mmx) | `tp_dispatch.py --persona <name>` prepends to packed context file | ✅ (code wired + smoke-tested 2026-08-03) |

The pattern is universal: **prompt-level format constraints work regardless of
the transport.** The platform persona system is a convenience for native
subagents; for everything else, prepending the instructions to the prompt string
achieves the same effect.

### 4. The behavioral/format split (critical design principle)

Personas consumed by skills with their own output format (like `/review`'s JSON
schema or `/plan`'s plan format) must provide **behavioral defaults only** —
not output format. A persona that says "output as a table" conflicts with a
skill prompt that says "output as JSON to this path."

Personas consumed by ad-hoc spawns (no skill-provided format) provide **both
behavior and format** — this is where the anti-performative-reasoning benefit
is strongest.

| Persona | Consumer | Who owns format? | Correct? |
|---|---|---|---|
| `sdlc-critic` | `/review` (has JSON schema) | The skill | ✅ (fixed after initial conflict) |
| `sdlc-plan` | `/plan`, `/go` (have plan formats) | The skill | ✅ (fixed after initial conflict) |
| `sdlc-code` | `/go` (implementation) | The skill | ✅ (no format directive) |
| `sdlc-debug` | Ad-hoc | The persona | ✅ |
| `file-analyzer` | Ad-hoc | The persona | ✅ |
| `critique-lens` | Ad-hoc / `tp_dispatch.py` | The persona | ✅ |
| `extractor` | Ad-hoc | The persona | ✅ |

## What this means for our workspace

### What was built

| Component | What it does | Files |
|---|---|---|
| 10 persona files | Behavioral defaults + format constraints for common task types | `~/.grok/personas/*.toml` |
| `tp_dispatch.py --persona` flag | Prepends persona instructions to packed context for cross-model dispatch | `~/.grok/skills/tp/__lib/tp_dispatch.py` |
| `/review` persona prepending | Already existed — auto-applies `sdlc-critic.toml` to specialists | `/review` SKILL.md line 665 |

**What should be updated going forward:**
- When creating new skills that dispatch subagents, specify which persona to prepend (or create a new one if none fits)
- When dispatching via PI/OpenCode/direct HTTP, prepend the appropriate persona instructions to the prompt
- When a skill has its own output format, the persona provides behavioral defaults only (no format)

### The persona inventory (as of 2026-08-03)

| Persona | Purpose | Format owner |
|---|---|---|
| `sdlc-critic` | Adversarial code review | Skill (`/review`) |
| `sdlc-code` | Implementation | Skill (`/go`) |
| `sdlc-debug` | Debugging with hypothesis tree | Persona |
| `sdlc-plan` | Architecture planning | Skill (`/plan`) |
| `sdlc-discover` | Codebase discovery | Skill (`/preflight`) |
| `design-doc-writer` | Design document writing | Persona (references `/design` sections) |
| `design-doc-reviewer` | Design document review | Persona (F-NN format) |
| `file-analyzer` | Ad-hoc file analysis | Persona (finding table) |
| `critique-lens` | Quick critique dispatch | Persona (claims table + verdict) |
| `extractor` | Data/wiki extraction | Persona (JSON array) |

## Falsifier

1. If a future test shows persona'd prompts producing *lower quality* analysis
   than bare prompts (the format constraint suppresses serendipitous findings),
   the format-constraining personas should be loosened to behavioral-only.
2. If external CLIs add native persona support (PI `--append-system-prompt` is
   already close), the prompt-prepending approach becomes unnecessary for that
   path and should migrate to the native mechanism.
3. If the performative-reasoning pattern is shown to be model-specific (some
   models don't narrate their output plan), personas are less valuable for
   those models and the complexity of maintaining them may not be justified.

## Receipts

- PI A/B test: `P:/tmp/test_persona_pi.py` (bare 107s vs persona 61s, 2026-08-03)
- Grok subagent test: persona'd subagent produced clean table output with zero
  format-planning steps in thinking block (subagent 019fc7c1, 2026-08-03)
- `tp_dispatch.py --persona` smoke test: packed context correctly includes
  persona instructions section (2026-08-03)
- Persona conflict discovery: `sdlc-critic` initially specified markdown table
  format that conflicted with `/review`'s JSON schema; fixed by stripping format
  directive, keeping behavioral defaults only
- Persona validation: `P:/tmp/validate_personas.py` confirms all 10 files parse
  as valid TOML with required fields

## Sources

- [Grok Build Subagents and Personas](file:///C:/Users/brsth/.grok/docs/user-guide/16-subagents.md) (Grok Build, 2026) — persona resolution mechanism, `<system-reminder>` injection
- [PI CLI --append-system-prompt](file:///C:/Users/brsth/.grok/skills/tp/SKILL.md) (PI help output, 2026-08-03) — native persona-like flag
- [[prompting-patterns-for-ai-agent-control]] — existing pattern taxonomy; this concept adds pattern #11 (output-format-constraining templates)
- [[mandatory-step-enforcement-code-over-prose]] — why structural enforcement beats prose rules; personas are structural (injected mechanically), not behavioral (remembered)

## Auto-related

- [[user-modeling-for-agentic-clis]]
- [[skill-graph]]
- [[skill-catalog]]
- [[inline-conditional-over-dispatch-for-skill-design]]
- [[llm-based-agent-architectures]]

