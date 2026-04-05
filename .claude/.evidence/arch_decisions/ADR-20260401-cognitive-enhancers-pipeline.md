# ADR-20260401: Cognitive Enhancers Pipeline Architecture

**Status:** Accepted
**Date:** 2026-04-01

## Context

The cognitive enhancers pipeline is one of the most complex subsystems in the hook architecture, spanning 8+ modules across configs, registries, tag systems, and observability. Despite its maturity (evolved from a monolithic 660-line file through multiple ADRs and refactors), no single ADR documents the full pipeline architecture.

## Decision

Document the pipeline as the canonical architecture reference. This ADR covers execution flow, components, configuration, intent detection, tag system, conflict resolution, and observability.

## Architecture Overview

### Data Flow

```
User Prompt
    |
    v
registry.run_hooks() -- priority-sorted execution
    |
    v (priority 8.0)
operating_rules -- suppresses old individual enhancers, injects hard directives
    |
    v (priority 11.0)
cognitive_enhancers(context)
    |-- _load_config() -- merge defaults with cognitive_enhancers_config.json
    |-- _is_actionable_prompt() -- skip short/operational prompts
    |-- _detect_intent() -- regex-based topic classification
    |   |-- implementation, diagnostic, meta_rca, decomposition, implementation_diagnostic
    |   +-- Mode overrides: #rca, #deep, #fast
    |-- _select_enhancers() -- topic->enhancer routing, per-topic limits
    |-- resolve_conflict() -- arbiter: fast mode cap, token budget, confidence override
    |-- _build_injection() -- tag emission + rationale + framework text
    |   |-- tag_registry: validate & lookup tags
    |   |-- tag_emission: format [TAG] strings
    |   +-- observability: log tag emission telemetry
    +-- return HookResult(context=injection, tokens=N)
```

### Pipeline Components (execution order)

| Component | File | Priority | Role |
|-----------|------|----------|------|
| **Registry** | `UserPromptSubmit_modules/registry.py` | N/A | Hook discovery, registration, priority-sorted execution |
| **Operating Rules** | `UserPromptSubmit_modules/operating_rules.py` | 8.0 | Hard directives (verify before claiming, be decisive, etc.) |
| **Config Loader** | `UserPromptSubmit_modules/config_loader.py` | N/A | Unified `CognitiveReasoningConfig` dataclass |
| **Cognitive Enhancers** | `UserPromptSubmit_modules/cognitive_enhancers.py` | 11.0 | 11 framework injections, intent detection, topic routing |
| **Conflict Arbiter** | `UserPromptSubmit_modules/conflict_arbiter.py` | N/A | Precedence rules (fast mode, token budget, confidence override) |
| **Tag Registry** | `UserPromptSubmit_modules/tag_registry.py` | N/A | Canonical tag definitions, validation, deprecation |
| **Tag Emission** | `UserPromptSubmit_modules/tag_emission.py` | N/A | Tag formatting, collection, backward compatibility |
| **Observability** | `UserPromptSubmit_modules/observability.py` | N/A | JSONL metrics logging for selections, modes, tags |

## Component Details

### Registry (`registry.py`)

Central hook discovery and execution engine. Uses `@register_hook()` decorator pattern with priority-sorted execution. Supports hook suppression (one hook can suppress others via `suppress` key in result context).

Key functions:
- `register_hook(name, priority)` -- decorator for hook registration
- `run_hooks(data, prompt)` -- priority-sorted execution with suppression
- `_try_import_hook()` -- lazy loading with fail-open on ImportError

### Operating Rules (`operating_rules.py`)

Priority 8.0 hook that fires before cognitive_enhancers (11.0). Injects 4 hard directives and suppresses verbose individual enhancer hooks that were replaced by the unified system.

### Cognitive Enhancers (`cognitive_enhancers.py`)

The main unified hook at priority 11.0. Replaces 9+ separate hooks with a single config-driven router.

Key functions:
- `_load_config()` -- merge `_DEFAULT_CONFIG` with `cognitive_enhancers_config.json`
- `_is_actionable_prompt()` -- skip short/operational prompts, handle slash commands
- `_detect_intent()` -- regex-based topic classification (5 topics)
- `_select_enhancers()` -- topic-to-enhancer routing with per-topic limits
- `_build_injection()` -- tag emission + rationale + framework text assembly
- `cognitive_enhancers(context)` -- registered hook entry point

Uses frozen `Enhancer` dataclass for each framework definition (name, injection text, topics).

### Config Loader (`config_loader.py`)

Unified `CognitiveReasoningConfig` dataclass that loads from `cognitive_reasoning_config.json`. Provides per-framework, per-mode, and per-profile getters with caching.

### Conflict Arbiter (`conflict_arbiter.py`)

Three precedence rules:
1. **Fast mode cap** -- `#fast` caps enhancers to lightweight-only
2. **Token budget** -- caps total injection tokens (default 500)
3. **Confidence override** -- high-confidence reasoning overrides cognitive enhancers

Returns `ArbiterResult` with adjusted enhancer list and metadata.

### Tag Registry (`tag_registry.py`)

Canonical source of truth for all framework tags. Prevents LLM tag hallucination by validating tags at emission time.

Tags: `ASUM`, `ANCH`, `INV`, `FENC`, `CAL`, `DISC`, `SOC`, `CYNE`, `RAZR`, `DADV`

Uses `__debug__` invariant checks on import to ensure registry consistency.

### Tag Emission (`tag_emission.py`)

`Tag` and `TagCollection` dataclasses for formatting, collection, and backward compatibility. Functions:
- `emit_tag()` -- single tag emission
- `emit_tags()` -- multiple tag emission
- `emit_detection_tags()` -- unified detection integration

### Observability (`observability.py`)

JSONL metrics logging to `.claude/data/reasoning_metrics.jsonl`. Three logging functions:
- `log_cognitive_selection()` -- enhancer selections with intent and rationale
- `log_reasoning_mode()` -- reasoning mode activations
- `log_tag_emission()` -- tag emission telemetry with validation status

## Configuration

### Config Files

| Config | Purpose |
|--------|---------|
| `cognitive_enhancers_config.json` | Per-enhancer toggles, topic routing, modes, skill blacklist |
| `cognitive_reasoning_config.json` | Unified config: frameworks, reasoning modes, think profiles, questioning patterns, performance |

### Config Schema (`cognitive_enhancers_config.json`)

```json
{
  "enabled": true,
  "topics": {
    "implementation": true,
    "diagnostic": true,
    "meta_rca": true,
    "decomposition": true,
    "implementation_diagnostic": true
  },
  "enhancers": {
    "assumption_surfacing": true,
    "outcome_anchoring": true,
    "inversion_prompting": true,
    "chestertons_fence": true,
    "calibrated_confidence": true,
    "named_artifact_discovery": true,
    "socratic_decomposition": true,
    "cynefin_classification": true,
    "hanlons_razor": true,
    "devils_advocate": true,
    "comparative_analysis": true
  },
  "max_enhancers_per_prompt": 3,
  "max_enhancers_by_topic": {
    "implementation": 3,
    "diagnostic": 5,
    "meta_rca": 2,
    "decomposition": 4,
    "implementation_diagnostic": 5
  },
  "socratic_min_length": 200,
  "min_prompt_length": 30,
  "enhance_skills": true,
  "skip_skills": ["commit", "push", "search", "help", ...],
  "modes": {
    "rca": {"topic": "meta_rca"},
    "deep": {"topic": "implementation"},
    "fast": {"disable_all": true}
  }
}
```

### Fail-Open Behavior

All config loading fails open. JSON parse errors, missing files, and schema violations emit warnings to stdout but never break hook execution. Defaults are hardcoded in `_DEFAULT_CONFIG`.

## Intent Detection

### Regex-Based Topic Classification

Five topics detected via compiled regex patterns:

| Topic | Detection Pattern | Example Triggers |
|-------|-------------------|------------------|
| `implementation` | `_IMPL_RE`, `_OUTCOME_RE` | "build", "create", "implement", "refactor", "fix" |
| `diagnostic` | `_DIAGNOSTIC_RE` | "debug", "investigate", "diagnose", "why does" |
| `meta_rca` | FAP gate (separate module) | Root cause analysis mode |
| `decomposition` | `_DECOMPOSITION_RE`, length heuristic | "break down", "decompose", or long vague prompts (>200 chars) |
| `implementation_diagnostic` | Combo detection | Both implementation AND diagnostic detected |

### Negation Handling

`_NEGATION_IMPL_RE` prevents false implementation detection on phrases like "don't implement" while allowing quality guidance like "don't forget to test".

### Mode Overrides

User can force topic via `#mode` in prompt:
- `#rca` -- forces `meta_rca` topic
- `#deep` -- forces `implementation` topic
- `#fast` -- disables all enhancers (handled by conflict arbiter)

### Slash Command Handling

Skills get cognitive enhancement by default unless blacklisted in `skip_skills`. New implementation-oriented skills automatically benefit without configuration.

## 11 Cognitive Frameworks

| Framework | Tag | Topics | Injection Purpose |
|-----------|-----|--------|-------------------|
| assumption_surfacing | ASUM | implementation, implementation_diagnostic | Surface unstated assumptions before work begins |
| outcome_anchoring | ANCH | implementation | Define "done" before starting, work backward from goal |
| inversion_prompting | INV | implementation | What would make this change fail? Name one concrete risk |
| chestertons_fence | FENC | implementation | Understand WHY code exists before changing it |
| calibrated_confidence | CAL | diagnostic, implementation_diagnostic | Force HIGH/MEDIUM/LOW confidence labeling on claims |
| named_artifact_discovery | DISC | diagnostic | Find named systems before analyzing; recency != authority |
| socratic_decomposition | SOC | decomposition | Break vague prompts into 2-4 concrete sub-questions |
| cynefin_classification | CYNE | diagnostic, meta_rca | Classify problem domain: Clear/Complicated/Complex/Chaotic |
| hanlons_razor | RAZR | diagnostic | Bugs before blame; simpler explanations before malice |
| devils_advocate | DADV | implementation | Stress-test proposals with counterarguments |
| comparative_analysis | COG (legacy) | implementation, decision_analysis | Search->Evaluate->Implement; compare before committing |

### Tag Emission

Active frameworks emit `[TAG]` strings prepended to the injection. Tags serve dual purpose:
1. **Visibility** -- user and hooks can see which frameworks are active
2. **Validation** -- tag registry prevents hallucination of non-existent tags

Example output header:
```
[ASUM] [ANCH] [INV]
Why: implementation intent detected

**TAG EMISSION REQUIRED**: Begin your response with the framework tags above.
Active frameworks: Assumption Surfacing, Outcome Anchoring, Inversion Prompting
```

## Conflict Resolution

The conflict arbiter (`conflict_arbiter.py`) applies three rules in order:

1. **Fast mode** (`#fast` in prompt): Caps to lightweight enhancers only, reduces token budget
2. **Token budget** (default 500): Removes lowest-priority enhancers if combined injection exceeds budget
3. **Confidence override**: High-confidence reasoning mode can suppress cognitive enhancers

Returns `ArbiterResult(dataclass)` with:
- `enhancers`: adjusted list
- `conflicts_resolved`: count of removals
- `rationale`: human-readable explanation

## Observability

All cognitive enhancer activity logged to `.claude/data/reasoning_metrics.jsonl` via three functions:

| Function | What It Logs |
|----------|-------------|
| `log_cognitive_selection()` | Selected enhancers, detected intent, token count, rationale |
| `log_reasoning_mode()` | Reasoning mode activations with confidence scores |
| `log_tag_emission()` | Tag type, category, validation status, deprecation warnings |

Log entries include session_id and terminal_id for multi-terminal isolation.

## Design Decisions

### DD-1: Regex-Only Intent Detection (No Embeddings)

**Decision**: Use compiled regex patterns for topic classification instead of sentence-transformers embeddings.

**Rationale**: Previous embedding-based system caused 56-second timeout on every UserPromptSubmit event. Regex patterns provide <10ms classification with acceptable accuracy for the 5-topic space.

**Trade-off**: Cannot detect semantic similarity (e.g., "make it better" ~= "improve"), but the explicit verb patterns cover the vast majority of real prompts.

**Reference**: `plan-20260303-cognitive-enhancers-hybrid.md`

### DD-2: Config-Driven Routing

**Decision**: Topics map to enhancers via config, with per-topic limits on max enhancers.

**Rationale**: Replaces hardcoded priority-based individual hooks with a single router that can be reconfigured without code changes. Adding a new enhancer requires only config + one `Enhancer` dataclass.

**Trade-off**: Config schema complexity. Mitigated by fail-open loading and `_DEFAULT_CONFIG` as safety net.

### DD-3: Tag Registry as Source of Truth

**Decision**: All framework tags defined in `tag_registry.py` with `__debug__` invariant checks.

**Rationale**: LLMs were hallucinating tags that didn't exist (e.g., `[STRAT]`, `[PLAN]`). Central registry with import-time validation prevents this class of error.

**Trade-off**: Adding new tags requires editing the registry module. Acceptable given low frequency of tag changes.

### DD-4: Fail-Open Config Loading

**Decision**: All config errors emit warnings but never break hook execution.

**Rationale**: Hooks run on every UserPromptSubmit event. A broken config should not block the user's entire workflow. Hardcoded defaults in `_DEFAULT_CONFIG` ensure the system always has valid configuration.

### DD-5: Operating Rules Suppression

**Decision**: `operating_rules.py` at priority 8.0 fires before `cognitive_enhancers.py` at 11.0, suppressing old verbose individual enhancers.

**Rationale**: Migration from 9 separate hooks to a unified hook left old hooks registered. Rather than deleting them (risky), operating_rules suppresses their output while the unified system handles all routing.

### DD-6: Frozen Dataclass for Framework Definitions

**Decision**: Each framework defined as `Enhancer(name=..., injection=..., topics=[...])` frozen dataclass.

**Rationale**: Prevents accidental mutation of framework definitions. Single-source definition eliminates the bug class where pattern dictionaries and template dictionaries drift apart.

## Historical Context

| Date | Event | Driver |
|------|-------|--------|
| Pre-2026-03-03 | Monolithic 660-line file with sentence-transformers embeddings | Initial implementation |
| 2026-03-03 | Split into hybrid architecture, eliminated 56s timeout | `plan-20260303-cognitive-enhancers-hybrid.md` |
| Post-split | Config-driven routing replaced priority-based individual hooks | Architecture refactor |
| 2026-03-12 | Tag registry added to prevent LLM tag hallucination | Observed hallucination in production |
| 2026-03-14 | Security improvements (prompt injection sanitization) | `COGNITIVE_ENHANCERS_SECURITY_IMPROVEMENTS.md` |
| 2026-03-22 | Additional enhancers added (cynefin, hanlons_razor, devils_advocate) | Framework expansion |
| 2026-03-25 | Context followup detector added for follow-up queries | Cross-turn context continuity |
| 2026-04-01 | Multi-topic selection fix: `max(topic_limits)` replaces `detected_topics[0]` | User asked "why is it only 3?" — diagnostic capped at 3 of 5 candidates |
| 2026-04-01 | Config consolidation: deleted orphaned `cognitive_reasoning_config.json`, cleaned stale entries from `cognitive_enhancers_config.json` | Two-config confusion, stale enhancer names (`failure_analysis_soft`, `analysis_protocol_gate`) |
| 2026-04-01 | Docstring updated: "Nine" → "11" to reflect actual framework count | Stale after framework expansion |

## Related Documents

- `P:/.claude/hooks/plan-20260303-cognitive-enhancers-hybrid.md` -- Original split plan
- `P:/.claude/arch_decisions/COGNITIVE_ENHANCERS_SECURITY_IMPROVEMENTS.md` -- Security fixes
- `P:/.claude/arch_decisions/2025-03-14_fast_cognitive-reasoning-cross-category-triggers.md` -- Cross-category compatibility
