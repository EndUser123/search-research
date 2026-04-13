# Review Bundle: Reasoning & Cognitive Systems

**Generated**: 2026-04-13
**Scope**: /think skill, /ai-gemini skill, and reasoning/cognitive hooks
**File Count**: 5 skills + ~15 hook modules + tests
**Execution Mode**: Single-agent (small scope)

---

## 1. PROJECT CONTEXT

### Bundle Metadata
- **Skills**: `/think` (v3.0.0), `/ai-gemini` (v1.3.8)
- **Hook modules**: 6 core + supporting infrastructure
- **Test coverage**: Extensive unit/snapshot tests per module

### Domain & Purpose
Reasoning and cognitive infrastructure for Claude Code — a layered system of skills and hooks that:
1. **Auto-detect** reasoning needs from keyword/semantic signals
2. **Inject** contextual frameworks (RCA, tradeoffs, evidence audit, architecture)
3. **Enforce** discovery mandates and reasoning contracts
4. **Route** to appropriate external AI assistants (Gemini CLI)

### Scale Metrics
- **9 reasoning profiles** in `think_trigger.py` (debug_rca, tradeoff_decision, evidence_audit, architecture, pre_commit_risk, security_review, performance_analysis, multi_file_refactor, explicit_think, quick)
- **11 cognitive enhancers** in `cognitive_enhancers.py`
- **4 reasoning modes**: sequential, multi_agent, graph, two_stage
- **4 task paths** in /ai-gemini: RESEARCH (ACG), ENGINEERING (TDD), DESIGN (adversarial), RCA (hypothesis ledger)

### Environment
- **OS**: Windows 11 Pro (bash, PowerShell)
- **Primary language**: Python 3.12+
- **Package managers**: pytest, ruff
- **External services**: Gemini CLI (`@google/gemini-cli`)

---

## 2. ARCHITECTURE OVERVIEW

```
User Prompt
    │
    ├── cognitive_guardrails (priority 2.0) ──── Discovery mandate + generalization check
    ├── cognitive_enhancers (priority 11.0) ── 11 lightweight framework injections
    ├── think_trigger (priority 6.0) ───────── Auto-detect + inject reasoning profile
    ├── reasoning_mode_selector (priority 8.0) ─ Select reasoning mode (sequential/multi_agent/graph/two_stage)
    ├── sequential_thinking (priority 8.5) ─── Multi-phase Generate → Critique → Improve loop
    │
    ▼
Claude Code Response Generation
    │
    ├── /think skill ────────────────────────── Depth ladder, frame chaining, evidence-audit mode
    └── /ai-gemini skill ────────────────────── ACG workflow, TDD, adversarial review, RCA
```

### Data Flow
1. **UserPromptSubmit hooks** analyze prompt for reasoning signals
2. **Injected context** provides framework + contract language
3. **Skills** provide specialized workflows (think, ai-gemini)
4. **Output** is expected to follow reasoning contract (verify, counterexample, falsification)

---

## 3. COMPONENT INVENTORY

### Skills

#### `/think` (P:/.claude/skills/think/SKILL.md)
- **Purpose**: Adaptive reasoning gate — choose depth, chain frames, verify before settling
- **Key features**:
  - Depth ladder: `/truth` → evidence-audit → `/decision-tree` → `/sequential-thinking` → `/think`
  - Open-ended prompt pattern: 3 branches (creative, skeptical, pragmatic) + frame chaining
  - Evidence-audit mode: Verified/Inferred/Unproven claim labeling
  - External challenger policy: `/codex`, `/ai-gemini`, `/ai-qwen` for high-uncertainty decisions
  - Reasoning frames: decision matrix, tree search, causal graph, pre-mortem, challenger debate, first principles, inversion, Bayesian update, systems thinking, Cynefin, causal trace, root-cause analysis

#### `/ai-gemini` (P:/.claude/skills/ai-gemini/SKILL.md)
- **Purpose**: Gemini-powered general-purpose assistant using ACG workflow
- **Key features**:
  - Soft triage: RESEARCH → ACG, ENGINEERING → TDD, DESIGN → adversarial review, RCA → hypothesis ledger
  - Citation enforcement: `[source: file:line]` format, `[UNVERIFIED]`/`[BAD-CITATION]`/`[LOW-CONFIDENCE]` flags
  - Verification pyramid: Tier 1 (Unit) → Tier 2 (Integration) → Tier 3 (E2E)
  - Gemini CLI invocation: `-y -o text --include-directories` for headless use
  - Model pinning: `-m gemini-2.5-flash` for stability

### Hook Modules

#### `reasoning_contract.py` (UserPromptSubmit_modules/)
- **Purpose**: Shared baseline reasoning discipline
- **Contract clauses**: verify before claiming, name counterexample, search existing first, state rollback, falsification condition, comparison axis, pre-mortem check, fix closure check
- **API**: `build_reasoning_contract()`, `append_reasoning_contract()`, `contract_clauses()`
- **Usage**: Imported by think_trigger, cognitive_enhancers, sequential_thinking

#### `think_trigger.py` (UserPromptSubmit_modules/)
- **Purpose**: Auto-detect reasoning profile from keyword signals
- **Profiles**: 9 (debug_rca, tradeoff_decision, evidence_audit, architecture, pre_commit_risk, security_review, performance_analysis, multi_file_refactor, explicit_think, quick)
- **Detection**: strong (1 match) vs weak (2+ matches), code span stripping, stemming
- **Pattern**: Single-source `ThinkProfile` dataclass with invariant check on import
- **Integration**: Reads from unified_detection result, falls back to legacy analyzer

#### `cognitive_guardrails.py` (UserPromptSubmit_modules/)
- **Purpose**: Prevent discovery failure and instance-class confusion
- **Detection**: DESIGN_INTENT_PATTERNS (action verbs + implementation objects, planning framing, explicit skill invocations)
- **Injection**: DISCOVERY MANDATE + GENERALIZATION CHECK
- **Config**: `COGNITIVE_GUARDRAILS_ENABLED` env var (default: true)

#### `cognitive_enhancers.py` (UserPromptSubmit_modules/)
- **Purpose**: 11 lightweight context injections for better reasoning
- **Enhancers**: assumption_surfacing, outcome_anchoring, inversion_prompting, chestertons_fence, calibrated_confidence, named_artifact_discovery, socratic_decomposition, cynefin_classification, hanlons_razor, devils_advocate, comparative_analysis, escape_hatch_gate, assumption_check
- **Intent detection**: implementation, diagnostic, meta_rca, decomposition, implementation_diagnostic, escape_hatch, question
- **Config**: `cognitive_enhancers_config.json`, per-enhancer enable/disable, max_enhancers_per_prompt

#### `reasoning_mode_selector.py` (UserPromptSubmit_modules/)
- **Purpose**: Select optimal reasoning mode (sequential, multi_agent, graph, two_stage)
- **Integration**: Uses unified_detection result, falls back to legacy `Start_reasoning_mode_selector` from P:/packages/reasoning
- **Output**: mode + confidence + systemContext with reasoning contract

#### `sequential_thinking.py` (UserPromptSubmit_modules/)
- **Purpose**: Generate → Critique → Improve loop for enhanced reasoning quality
- **Trigger patterns**: 20+ regex patterns for analysis, evaluation, problem-solving, design decisions, architecture, complex explanation
- **Semantic detection**: Via unified_semantic_daemon (90MB shared RAM), fallback chain: daemon IPC → direct SentenceTransformer → regex-only
- **Modes**: initial, investigation (Layer 2), hypothesis_mode
- **State**: Terminal-scoped JSON files in P:/.claude/state/sequential-thinking/

### External Hooks

#### `PreToolUse_sequential_thinking.py`
- Injects mode-specific system messages based on session state

#### `StopHook_sequential_thinking.py`
- Manages iteration and session completion

#### `reasoning_quality_gate_monitor.py`
- Tracks quality gate statistics from `P:/packages/reasoning/hook_usage.log`
- CLI: `--stats`, `--health`, `--recent`

---

## 4. DESIGN INTENT AND NON-NEGOTIABLES

### Architectural Pillars
1. **Evidence-first**: Verify before claiming absence, breakage, or implementation state
2. **Falsification**: Name counterexample/failure mode before stating conclusion
3. **Discovery mandate**: Search existing implementations before creating new ones
4. **Depth-adaptive**: Pick reasoning depth matching risk/uncertainty/blast radius
5. **Source-grounded**: Gemini outputs must cite sources; unverified claims flagged

### Technology Constraints
- Hooks must use stderr only for errors, stdout for diagnostics
- No external API calls in hooks (no LLM calls during hook execution)
- Terminal isolation via scoped state files (terminal_id prefix)
- Fail-open on errors (hooks should not break prompt processing)

### Things That Must NOT Change
- `reasoning_contract.py` clause order or removal without updating all consumers
- `ThinkProfile` dataclass structure (frozen=True for thread safety)
- Sequential thinking session state schema (terminal_id scoping)
- /ai-gemini citation format `[source: file:line]`

---

## 5. KNOWN ISSUES

| Issue | Impact | Workaround |
|-------|--------|------------|
| ThinPrompt injection causes prompt bloat when multiple enhancers fire | Token overhead | Max 3 enhancers per prompt via config |
| Semantic detection requires ~90MB RAM for SentenceTransformer | Resource usage | Daemon shares model across terminals |
| Cognitive guardrails can over-fire on "build" in non-design contexts | False positives | Explicit opt-out via COGNITIVE_GUARDRAILS_ENABLED=false |
| Gemini CLI `--include-directories` required for file access in headless mode | CLI complexity | SKILL.md documents the pattern |

---

## 6. INTEGRATION POINTS

### Hook Stack Order (UserPromptSubmit)
```
cognitive_guardrails (2.0) → think_trigger (6.0) → reasoning_mode_selector (8.0) → sequential_thinking (8.5) → cognitive_enhancers (11.0)
```

### Skill Invocations
- `/think` → reasoning profile injection + depth ladder
- `/ai-gemini` → Gemini CLI + ACG workflow
- `/sequential-thinking` → sequential_thinking hook activation

### External Dependencies
- `P:/packages/reasoning/` — Start_reasoning_mode_selector, sequential_state
- `P:/packages/reasoning/hooks/` — reasoning hooks package
- `P:/__csf/src/daemons/unified_semantic_daemon.py` — semantic similarity
- Gemini CLI (`@google/gemini-cli`) — external AI assistant

---

## 7. INPUT/OUTPUT CONTRACT

### Per-Hook Data Flow

| Hook | Input | Output | Dependencies |
|------|-------|--------|--------------|
| `think_trigger` | `context.prompt`, `context.data.unified_detection_result` | `HookResult.context.additionalContext` (profile template + contract) | `reasoning_contract`, `unified_detection` |
| `cognitive_guardrails` | `context.prompt` | `HookResult.context.additionalContext` (discovery + generalization) | `reasoning_contract` |
| `cognitive_enhancers` | `context.prompt` | `HookResult` (enhancer injections + tags) | `conflict_arbiter`, `tag_registry`, `observability` |
| `reasoning_mode_selector` | `context.prompt`, `context.data.unified_detection_result` | `HookResult.context.systemContext` + `additionalContext` (mode display) | `Start_reasoning_mode_selector` |
| `sequential_thinking` | `context.prompt`, `context.terminal_id`, `context.data.unified_detection_result` | `HookResult.context.additionalContext` (session ID, mode, instructions) | `sequential_state`, `sequential_thinking_semantic_client`, `tag_emission` |

### Quality Gates
- **Hook priority ordering**: Ensures cognitive_guardrails fires first (discovery mandate before solution design)
- **Max enhancers cap**: Prevents prompt bloat from cognitive_enhancers
- **Invariant check** in `think_trigger.py`: `_PROFILES` and `_COMPILED_STRONG` must have matching keys

---

## 8. KNOWN ISSUES

1. **Prompt bloat**: Multiple hooks can inject significant context; mitigated by max_enhancers=3
2. **False positive risk**: Cognitive guardrails may over-fire; configurable via env var
3. **RAM for semantic detection**: ~90MB shared model; acceptable for desktop use
4. **Gemini CLI availability**: Requires `npm i -g @google/gemini-cli`; filesystem access must be verified per session

---

## 9. VERIFICATION COMMANDS

```bash
# Run reasoning hook tests
pytest P:/.claude/hooks/UserPromptSubmit_modules/tests/test_think_trigger.py -v
pytest P:/.claude/hooks/UserPromptSubmit_modules/tests/test_cognitive_enhancers_*.py -v
pytest P:/.claude/hooks/tests/test_sequential_thinking_hooks.py -v

# Verify reasoning contract clauses
python -c "from UserPromptSubmit_modules.reasoning_contract import contract_clauses; print(contract_clauses())"

# Check think_trigger invariant
python -c "import think_trigger"  # Should pass without AssertionError

# Verify Gemini CLI
gemini --version
gemini -y -o text -p "Say hello"
```

---

## 10. APPENDIX: REASONING PROFILES

| Profile | Trigger Keywords (Strong) | Use Case |
|---------|---------------------------|----------|
| debug_rca | flaky, race condition, root cause, stack trace | 5-Whys root cause analysis |
| tradeoff_decision | option a vs b, pros and cons, trade-off | Quick comparison of 2 options |
| evidence_audit | verify, prove, fact-check, confirm | Evidence-first claim verification |
| architecture | microservices, monolith, domain model | Architecture evaluation |
| pre_commit_risk | about to deploy, before merging, breaking changes | Pre-mortem risk assessment |
| security_review | SQL injection, XSS, OWASP, CVE | Security threat modeling |
| performance_analysis | slow, latency, bottleneck, O(n²) | Performance investigation |
| multi_file_refactor | refactor across multiple files, rename globally | Multi-file refactoring |
| explicit_think | THINK keyword (uppercase) | Deliberate reasoning mode |
| quick | Default when THINK used without profile | Lightweight triage |

---

*End of review bundle*
