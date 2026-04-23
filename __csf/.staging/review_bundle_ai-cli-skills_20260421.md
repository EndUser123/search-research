# Review Bundle: AI CLI Skills
**Generated**: 2026-04-21
**Scope**: /think, /ai-pcli, /ai-cli-gemini, /ai-pi-mm-m27
**File Count**: 4 skills, ~18 files total
**Execution Mode**: Single-agent (all < 10 files per skill)

---

## 1. PROJECT CONTEXT

### Bundle Metadata
- **Generated**: 2026-04-21
- **Scope**: AI CLI skills for parallel multi-LLM orchestration and reasoning
- **File Count**: 4 skills
  - `/think`: 1 file (SKILL.md)
  - `/ai-pcli`: ~15 files (Python modules + SKILL.md)
  - `/ai-cli-gemini`: 1 file (SKILL.md)
  - `/ai-pi-mm-m27`: 1 file (SKILL.md)

### Domain & Purpose
These skills provide complementary AI reasoning capabilities:
- **/think**: Single-model iterative self-critique reasoning
- **/ai-pcli**: Parallel multi-LLM orchestration (gemini, pi-m27, pi-glm, codex)
- **/ai-cli-gemini**: Gemini CLI wrapper with ACG (Analyze-Challenge-Gap) workflow
- **/ai-pi-mm-m27**: MiniMax M2.7 adversarial review via pi agent

### Scale Metrics
- LOC: ~3000+ (ai-pcli alone has 3500+ lines in ai_cli.py)
- All skills are lightweight wrappers around external CLI tools
- No persistent state; stateless execution

---

## 2. ARCHITECTURE OVERVIEW

```
User Input
    │
    ├─► /think ──────────────────► Internal reasoning loop (Generate→Critique→Improve)
    │                                    No external CLI calls
    │
    ├─► /ai-pcli ─────────────────► ai_cli.py
    │     │                              ├─► task_classifier.py (classify task type)
    │     │                              ├─► prompt_templates.py (build enhanced prompts)
    │     │                              ├─► file_context.py (context extraction)
    │     │                              └─► Runs multiple CLIs in parallel:
    │     │                                   - gemini (Google)
    │     │                                   - pi --model minimax/MiniMax-M2.7
    │     │                                   - pi --model z-ai/glm-5.1
    │     │                                   - codex (OpenAI)
    │
    ├─► /ai-cli-gemini ────────────► Gemini CLI wrapper
    │                                     ├─► RESEARCH path: ACG workflow
    │                                     ├─► ENGINEERING path: TDD lite
    │                                     ├─► DESIGN path: adversarial review
    │                                     └─► RCA path: hypothesis ledger
    │
    └─► /ai-pi-mm-m27 ──────────────► pi CLI wrapper (MiniMax M2.7)
                                          └─► Adversarial code review
```

---

## 3. EXECUTION AND DATA FLOW

### /think Execution
1. User invokes `/think [query]`
2. Internal 3-phase loop:
   - Generate: Produce best answer
   - Critique: Identify gaps/weaknesses
   - Improve: Synthesize refined answer
3. Frame selection (decision-tree, investigation, evidence-audit, etc.)
4. Output: Compact recommendation with tradeoffs

### /ai-pcli Execution
1. Parse query and options
2. Classify task type (code_review, planning, brainstorm, etc.)
3. Build context from `--context` or auto-detect
4. Apply prompt enhancement (built-in templates or prompting-toolkit)
5. Run parallel LLM CLIs (waits for ALL to complete)
6. Aggregate outputs
7. Run ai-cli-critic for meta-critique

### /ai-cli-gemini Execution
1. Soft triage (RESEARCH/ENGINEERING/DESIGN/RCA)
2. Route to appropriate workflow
3. Execute Gemini CLI with `-y -o text` flags
4. Apply ACG or other workflow to output

### /ai-pi-mm-m27 Execution
1. User invokes with file path
2. Run `pi --model minimax/MiniMax-M2.7` against file
3. Return JSON with score, summary, issues

---

## 4. COMPONENT INVENTORY

### /think
| Component | Path | Responsibility |
|-----------|------|----------------|
| SKILL.md | P:/.claude/skills/think/SKILL.md | Single-file skill; reasoning depth selection, frame chaining, evidence-audit |

### /ai-pcli
| Component | Path | Responsibility |
|-----------|------|----------------|
| ai_cli.py | P:/packages/cc-skills-ai-cli/skills/ai-pcli/ai_cli.py | Main orchestrator; CLI parsing, parallel execution, aggregation |
| task_classifier.py | P:/packages/cc-skills-ai-cli/skills/ai-pcli/task_classifier.py | Keyword-based task type classification |
| prompt_templates.py | P:/packages/cc-skills-ai-cli/skills/ai-pcli/prompt_templates.py | Task-specific prompt templates |
| file_context.py | P:/packages/cc-skills-ai-cli/skills/ai-pcli/file_context.py | Context extraction from files |
| performance_logger.py | P:/packages/cc-skills-ai-cli/skills/ai-pcli/performance_logger.py | Performance tracking |
| structured_response.py | P:/packages/cc-skills-ai-cli/skills/ai-pcli/structured_response.py | Structured output handling |
| SKILL.md | P:/packages/cc-skills-ai-cli/skills/ai-pcli/SKILL.md | Skill definition |

### /ai-cli-gemini
| Component | Path | Responsibility |
|-----------|------|----------------|
| SKILL.md | P:/.claude/skills/ai-cli-gemini/SKILL.md | Gemini CLI wrapper with ACG workflow |

### /ai-pi-mm-m27
| Component | Path | Responsibility |
|-----------|------|----------------|
| SKILL.md | P:/.claude/skills/ai-pi-mm-m27/SKILL.md | pi + MiniMax M2.7 adversarial review |

---

## 5. DESIGN INTENT AND NON-NEGOTIABLES

### /think
- **Goal**: Adaptive reasoning depth matching problem complexity
- **Non-negotiables**:
  - Evidence-labeling (Verified/Inferred/Unproven)
  - Frame chaining only when it changes the answer
  - Smallest discriminating check before concluding
  - External challenger escalation when internal critique is insufficient

### /ai-pcli
- **Goal**: Parallel multi-model perspective aggregation
- **Non-negotiables**:
  - All CLIs must complete (no partial results)
  - Task-type specific prompt templates
  - Conceptual queries without files → BRAINSTORM template (not PLANNING)
  - ai-cli-critic meta-critique phase
  - Extensionless directory paths detected as directories (not ignored)

### /ai-cli-gemini
- **Goal**: Source-grounded Gemini responses with ACG workflow
- **Non-negotiables**:
  - Citation enforcement (file:line references)
  - Source Fidelity Rule: no claims without reading files first
  - Soft routing (no hard phase gates)
  - Model pinning via `-m` flag for stability

### /ai-pi-mm-m27
- **Goal**: MiniMax M2.7 adversarial code review
- **Non-negotiables**:
  - Score + summary + issues JSON output
  - File must be read (first-line verification)

---

## 6. KNOWN ISSUES

### Historical Issues (Resolved)
1. **Pattern 3 for extensionless paths** (ai-pcli)
   - Problem: Regex required file extension; `yt-is` (directory) was ignored
   - Fix: Added directory detection in `_extract_file_paths_from_query`
   - File: ai_cli.py lines ~2191-2200

2. **Conceptual query → PLANNING template** (ai-pcli)
   - Problem: "what ideas come from..." classified as PLANNING → asked for project
   - Fix: Override to BRAINSTORM when no context AND conceptual starters detected
   - File: ai_cli.py lines ~3507-3522

### Current Potential Issues
1. **gemini-cli crashes on Windows** with `AttachConsole failed` error
   - Affects: /ai-pcli when gemini is selected
   - Workaround: Use `--gemini-only` with caution

2. **Task classifier tiebreaker** (ai-pcli)
   - Problem: PLANNING and BRAINSTORM both score 20% → PLANNING wins (first in enum)
   - Current fix: Conceptual override when no context
   - Residual: Queries with both "ideas" AND "architecture" keywords still ambiguous

---

## 7. INTEGRATION POINTS

### /think → External Challengers
- Can dispatch to `/ai-cli` for multi-LLM challenge when SDLC_MULTI_LLM=1
- Provider selection: `--codex-only`, `--gemini-only`, `--qwen-only`

### /ai-pcli → Task Classifier
- Input: User query
- Output: TaskType (code_review, planning, brainstorm, research, debug, refactor, general)
- Confidence scoring: 0.2 per keyword match, max 1.0

### /ai-pcli → Prompt Templates
- Maps TaskType → prompt template
- Templates: CODE_REVIEW, PLANNING, BRAINSTORM, RESEARCH, DEBUG, REFACTOR, GENERAL
- Solo-dev constraints appended to all templates

### /ai-cli-gemini → Verification Rituals
- Stage 1: `gemini --help` flag verification
- Stage 2: Filesystem access test via `--include-directories`

---

## 8. INPUT/OUTPUT CONTRACT

### /think
| Input | Process | Output |
|-------|---------|--------|
| User query | Internal reasoning loop | Compact recommendation |

### /ai-pcli
| Input | Process | Output |
|-------|---------|--------|
| Query + options | Classify → Context → Enhance → Run CLIs → Aggregate | Aggregated LLM outputs + ai-cli-critic |

| Phase | Reads | Writes |
|-------|-------|--------|
| Classification | query | TaskType enum |
| Context building | _smart_auto_context(), _build_query_context() | context string |
| Prompt enhancement | query + context + task_type | Enhanced query |
| CLI execution | External CLIs (gemini, pi, codex) | stdout/stderr |
| Aggregation | All CLI outputs | Combined text |
| Meta-critique | Combined text | ai-cli-critic findings |

### /ai-cli-gemini
| Input | Process | Output |
|-------|---------|--------|
| Query | Soft triage → ACG or other workflow | Structured findings |

### /ai-pi-mm-m27
| Input | Process | Output |
|-------|---------|--------|
| File path | pi --model minimax/MiniMax-M2.7 | JSON: {score, summary, issues} |

---

## 9. AGENT DISPATCH DEFINITIONS

### /think
- **Dispatch type**: None (single-agent internal reasoning)
- **Reasoning loop**: Generate → Critique → Improve (internal)

### /ai-pcli
- **Dispatch type**: Parallel external CLI processes
- **Agents**: gemini, pi-m27, pi-glm, codex (simultaneous)
- **Post-processing**: ai-cli-critic subagent (sequential after aggregation)
- **Read sources**: 
  - Analysis = aggregated CLI outputs
  - Source = not directly accessed (CLIs read files)

### /ai-cli-gemini
- **Dispatch type**: Single Gemini CLI process
- **Workflow**: ACG (Analyze → Challenge → Gap)

### /ai-pi-mm-m27
- **Dispatch type**: Single pi CLI process
- **Output**: Structured JSON

---

## 10. FAILURE SCENARIOS

### Failure: gemini-cli AttachConsole crash
- **Trigger**: Running `/ai-pcli` with gemini on Windows
- **Symptom**: Multiple `[WARN] Skipping unreadable directory: p:\System Volume Information` followed by `Error: AttachConsole failed`
- **Detection**: stderr contains `AttachConsole failed`
- **Impact**: gemini output empty or error, other CLIs still succeed
- **Mitigation**: Use `--pi-m27-only --pi-glm-only` to avoid gemini

### Failure: Conceptual query → PLANNING template
- **Trigger**: `/ai-pcli "what ideas come from parallel multi-LLM..."` (no file context)
- **Symptom**: LLM asks "what project should I plan?" instead of engaging
- **Root cause**: Task classifier scores PLANNING and BRAINSTORM equally (20%), enum order wins
- **Fix applied**: Override to BRAINSTORM when no context AND conceptual starters detected
- **File**: ai_cli.py conceptual override logic

### Failure: Extensionless directory path ignored
- **Trigger**: `/ai-pcli "review P:/packages/yt-is"` (directory, no extension)
- **Symptom**: CLIs get wrong context (git status from P:\ root) or no context
- **Root cause**: Regex `r"\.\w{2,4}$"` requires extension; fallback to git status
- **Fix applied**: Pattern 3 for extensionless directory paths + conceptual keyword skip
- **File**: ai_cli.py _extract_file_paths_from_query()

### Failure: pi 429 rate limit
- **Trigger**: /ai-pi-mm-m27 or /ai-pcli with pi when rate limited
- **Symptom**: `429 status code` error
- **Workaround**: Wait 30s and retry

### Failure: Empty Gemini output
- **Trigger**: Gemini CLI returns 0 bytes
- **Symptom**: Empty response
- **Handling**: Flag as `[EMPTY_OUTPUT]` and retry up to 3 times

---

## COMPARISON TABLE

| Feature | /think | /ai-pcli | /ai-cli-gemini | /ai-pi-mm-m27 |
|---------|--------|----------|-----------------|----------------|
| Multi-model | No | Yes (4 CLIs) | No | No |
| Iterative critique | Yes (3-phase) | No | ACG (3-step) | No |
| Task templates | No | Yes (7 types) | Soft routing | No |
| Aggregation | No | Yes | No | No |
| Meta-critique | No | Yes (Phase 2) | No | No |
| File context | No | Yes (auto + manual) | Yes (via CLI) | Yes (file read) |
| Citation enforcement | Via labels | No | Yes (file:line) | No |
| External CLI | No | Yes (gemini, pi, codex) | Yes (gemini) | Yes (pi) |
| Confidence scoring | Verified/Inferred/Unproven | Per-task templates | Via ACG | JSON score |
| Solo-dev framing | Yes | Yes | Yes | No |
