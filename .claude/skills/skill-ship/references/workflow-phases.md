---
type: core
load_when: discovery
priority: mandatory
estimated_lines: 350
---

# Skill Complete - Detailed Workflow Phases

This document contains the detailed phase-by-phase instructions for the skill-ship workflow. See SKILL.md for overview and quick reference.

## Phase 0: Context Awareness

**Goal**: Detect session patterns, user corrections, and learning signals before starting skill work — lightweight, no external tools

**Questions to answer**:
1. Were there user corrections or broken-windows signals in this session related to skills?
2. Are there any active hooks or state that would affect skill execution?
3. Did recent conversation show any recurring patterns about skill quality?

**Actions**:
1. **Scan recent conversation turns** (last 5-10 turns) for correction signals:
   - User said "no, not X" or "stop doing X" → flag as broken window
   - User said "yes exactly" or "perfect" → flag as validated pattern
   - User corrected trigger/output/format → note as quality requirement
2. **Read session state files**:
   - `.claude/hooks/.evidence/gto-state-*/` — GTO outputs from earlier session activity
   - `.evidence/skill-ship-state-{cwd_hash}/workflow-state.json` — **skill-ship's own terminal-scoped evidence** (if exists and fresh, read to detect interrupted workflow)
     - Contains: `target_skill`, `current_phase`, `quality_dimensions`, `workflow_started`
     - Only use if last_updated < 24 hours (stale state is worse than no state)
     - If interrupted workflow detected → surface as "resuming workflow for {target_skill}" before Phase 1
3. **Extract signals** — Map detected patterns to specific skill quality concerns:
   - User corrected trigger accuracy → increase trigger validation rigor in Phase 3b
   - User flagged a missing feature → note as design requirement in Phase 2
   - User corrected output format → enforce template in Phase 4
   - User reported failure mode → add to Phase 3d artifact validation checks

**Output Format**: Embedded in Phase 1 output

```markdown
### Session Correction Signals

| Signal | Location | Skill Quality Concern | Routed To |
|--------|----------|---------------------|-----------|
| [pattern] | turn N | [specific concern] | [phase] |

### Resumed from Evidence (if applicable)
If `.evidence/skill-ship-state-{cwd_hash}/workflow-state.json` was found and fresh (< 24h):
- **Resuming workflow for**: `{target_skill}`
- **Last completed phase**: `{current_phase}`
- **Quality dimensions**: `{quality_dimensions}`
- Surface this as: `→ Resuming skill-ship for {target_skill} — last completed: {current_phase}`

**Skip this phase when**: Fresh session with no prior skill work in the chat

---

## Phase 1: Discovery & Intent

**Goal**: Understand what the user wants to accomplish

**Questions to answer**:
1. What should this skill enable Claude to do?
2. When should this skill trigger? (user phrases/contexts)
3. What's the expected output format?
4. Is this a new skill or improvement to existing?
5. Should we set up test cases for verification?

**Intent Extraction Rules (Critical)**:

**Possessive Repair Phrase Trap:**
When the user says "my skill isn't working" or "this skill is broken", the phrase "my skill" or "this skill" may be incorrectly extracted as a NEW skill name to create. **This is wrong.**

**Correct interpretation:**
- "my skill isn't working right" → REPAIR intent for an EXISTING skill (user wants help fixing a skill they already have)
- "this skill keeps failing" → REPAIR intent (possessive "this" refers to existing skill)
- "create a skill called my-skill" → NEW creation intent (explicit "create a skill called X")

**Rule:** Possessive adjectives ("my", "this") + broken/error/not-working keywords = REPAIR intent. Do NOT treat possessive phrases as skill names to create.

**If no specific skill is named in a repair phrase:** Ask the user "Which skill do you want me to help fix?" before proceeding.

**Python Skill Repair Diagnostic (run before Phase 2 when REPAIR intent + Python skill detected):**

When a Python skill has a `lib/` directory, two failure modes account for most "wrong output / empty results" bugs:

**Failure Mode 1 — Missing `lib/__init__.py` export**

```bash
python "P:/.claude/skills/<SKILL_NAME>/<main_script>.py" --help
```
- If `ImportError: cannot import name 'X' from 'lib'` → find the function: `grep -rn "^def X\|^class X" P:/.claude/skills/<SKILL_NAME>/lib/`
- If found in a `.py` file but absent from `lib/__init__.py` → add `X` to both `__all__` and the import statements
- Re-run `--help` to confirm fix

**Failure Mode 2 — SKILL.md routing to a degraded fallback script**

Read the `## EXECUTE` section of `SKILL.md`. If it lists two scripts (a primary and a "fallback for monorepo/subdirectories"), check the fallback script for disabled detectors (comment blocks with "Re-enable by uncommenting below"). If detectors are commented out:
- Update SKILL.md to remove the fallback routing — use the primary script for all targets
- Mark the fallback script as deprecated in a comment or SKILL.md note

**Verification**: Run the primary script with `--format markdown --no-subagents` on a real target. Confirm health score has dimension breakdown and gap count > 0 (not "Total Gaps: 0" from a script with disabled detectors).

**Actions**:
1. **Extract intent** from conversation if available
2. **CRITICAL**: Before assuming new creation, check for possessive repair phrases (see above)
3. **AUTOMATED CONFLICT DETECTION** (enforced):
   - Invoke `/similarity` skill automatically with skill description/intent
   - If similarity score ≥ 80%:
     - Display conflict table: | Existing Skill | Similarity | Overlapping Features |
     - Ask user: "Continue creating new skill OR enhance existing [skill-name]?"
     - If enhance: **Output feed-forward block** (see below), then route to `/skill-ship` with improvement intent for existing skill
     - If continue: Document overlap rationale and proceed with creation

**Enhance Existing — Feed-Forward Block**:
When user chooses "enhance existing", emit this structured block immediately after the decision:

```markdown
<!-- SKILL-SHIP FEED-FORWARD -->
<!-- TARGET_SKILL: [skill-name] -->
<!-- TARGET_PATH: [absolute path to SKILL.md] -->
<!-- INTENT: enhance -->
<!-- OVERLAP_FEATURES: [comma-separated list of overlapping features from similarity analysis] -->
<!-- USER_CORRECTIONS: [any corrections flagged by user during conflict review] -->
<!-- GTO_SIGNALS: [any Phase 0 signals relevant to this skill] -->
<!-- END FEED-FORWARD -->
```

Phase 2 reads this block as context instead of re-parsing the conversation. Do NOT proceed to Phase 2 creation without first incorporating the feed-forward context from this block.
3. Clarify output format requirements
4. Determine if objective verification is needed

**Output Format**: Use Template 2 (Executive Summary Format)

```markdown
# Discovery Summary

## Intent
[What the skill should do]

## Context
- Triggering phrases: [list]
- Output format: [description]
- Conflict detection: [similarity score / conflicts found / none]
- Test coverage: [yes/no with rationale]

## Similarity Analysis
[If conflicts detected:]
| Existing Skill | Similarity | Overlapping Features | Action |
|----------------|------------|---------------------|---------|
| [skill-name] | [score%] | [features] | [Enhance/Continue/New]

## Recommendation
[Proposed approach with skill type classification]
[If conflicts: Document decision rationale for creating new vs enhancing existing]
```

---

## Phase 1.5: Knowledge Retrieval

**Goal**: Retrieve relevant patterns, lessons, and research before building — with active NotebookLM enhancement scanning

**Questions to answer**:
1. What related patterns exist in CKS?
2. What enforcement mechanisms, hooks, agents, sub-agents, trigger strategies, output formats, and failure modes exist in NotebookLM that could strengthen this skill?
3. What relevant lessons are in memory.md?
4. What do existing skills/plugins teach about the inferred quality dimensions?

**Infer functional quality dimensions FIRST** — Before querying any knowledge source, read the skill description and infer which of these are relevant. These dimensions apply to ALL knowledge sources (CKS, NotebookLM, skills/plugins), not just NotebookLM:

  | Dimension | Trigger signals | What to look for |
  |-----------|----------------|------------------|
  | Robustness | Error handling, edge cases, race conditions mentioned | Failure modes, circuit breakers, retry logic |
  | Computational Efficiency | Large data, loops, repeated operations | N+1 patterns, caching, batch operations |
  | Token Efficiency | Sub-agents, large context, verbose outputs, repeated summaries | File-passing IPC, progressive disclosure, condensed formats (machine RNS), lazy context loading |
  | Safety | State mutations, file operations, shared data | Atomicity, locking, corruption prevention |
  | Observability | Diagnostics, debugging, health monitoring | Logging patterns, trace hooks, metrics |
  | Concurrency | Multi-terminal, shared state, parallel work | Terminal isolation, file locking, race conditions |
  | Recoverability | Undo, rollback, cleanup on failure | Transaction patterns, cleanup hooks, backup |
  | Self-Improvement | Repeated use, feedback signals, evolving requirements, lessons learned | Feedback loops, self-correction hooks, lesson capture to memory/CKS, adaptive thresholds |

**Flagged dimensions become Quality Commitments** — These are explicitly listed in the Phase 2 output and validated in Phase 3b.

**Actions**:
1. **Query CKS** for relevant patterns:
   - Extract key terms from skill intent/description
   - Run `/cks search "<domain>" "<keywords>"` for semantic search
   - Run `/cks search "<pattern_type>"` for hook/pattern/anti-pattern queries
   - **Also query CKS for each flagged quality dimension**: `/cks search "<dimension-name>" "<skill-domain>"` (e.g., `/cks search "concurrent safety" "terminal isolation"`)

2. **Query NotebookLM** (if available) — Intelligent Notebook Discovery:
   - Check `nlm auth status`
   - List notebooks: `nlm notebook list`
   - **Smart relevance selection** (use approach A or B):
     - **Approach A (describe + semantic match)** — Get topic depth:
       1. `nlm notebook describe <id>` on each candidate to get AI-generated topic summary
       2. Score by semantic relevance to skill intent (not just keyword overlap)
       3. Select top 2-3 by intent match, not title substring
     - **Approach B (inverted query — let NotebookLM route)** — Most elegant:
       1. Ask the most broadly-relevant notebook (e.g., "skills & patterns"): `nlm notebook query <id> "I need to build a skill that [skill description]. Which of my other notebooks would be most relevant and why?"`
       2. Use that response to identify 2-3 target notebooks
       3. This leverages NotebookLM's semantic retrieval instead of manual keyword matching
   - Run 5 targeted queries per selected notebook using `nlm notebook query <id> "<question>"`:

     | Query | Purpose | Example Question Template |
     |-------|---------|---------------------------|
     | Q1: Enforcement | Find hooks, quality gates, StopHook patterns | "What enforcement mechanisms or hooks appear in this corpus that could strengthen a skill that [skill description]?" |
     | Q2: Agents/Sub-Agents | Find agent patterns, subagent coordination, capability delegation | "What agent or subagent patterns are described here — e.g. specialized agents, tool orchestration, capability delegation — that could enhance a skill for [skill description]?" |
     | Q3: Triggers | Find trigger phrases, activation contexts, user intent signals | "What trigger phrases or user intents are described that might improve how a skill for [skill description] gets activated?" |
     | Q4: Output/Format | Find templates, formatting patterns, presentation strategies | "What output formats, templates, or presentation patterns appear here that could improve a skill's usability?" |
     | Q5: Gaps/Failure | Find edge cases, failure modes, missing features | "What failure modes, edge cases, or missing features are discussed that a skill for [skill description] should handle?" |

   - Synthesize findings: deduplicate across notebooks, rank by relevance to target skill
   - If a notebook has no relevant results for a query, note "no findings" rather than omitting the row

3. **Scan existing skills/plugins** for reusable patterns:
   - Use `/similarity <target-skill-name>` to find related skills by domain
   - Also scan directly: Glob `skills/*/SKILL.md` and `hooks/**/SKILL.md` for frontmatter `description` matching target domain
   - For each related skill found, read its implementation files (not just SKILL.md — look at `__lib/`, `scripts/`, `references/`)
   - Extract reusable patterns: interesting hooks, CLI patterns, data structures, phase designs
   - Deduplicate against what's already in CKS or NotebookLM findings
   - Rank by specificity and reuse feasibility

4. **Query memory.md**:
   - Read MEMORY.md topic index
   - Read relevant topic files based on keywords
   - Priority files: working_principles.md, discovery_patterns.md, skill_optimization_patterns.md

**Output Format**: Use Template 2 (Executive Summary Format)

```markdown
## Knowledge Retrieval Summary

### CKS Results
[Relevant patterns found in CKS]

### NotebookLM Enhancement Scan

**Notebooks analyzed:** [list of notebook names/aliases]

| Enhancement Vector | Source Notebook | Finding | Applicable Phase |
|--------------------|-----------------|---------|------------------|
| Enforcement pattern | notebook-name | description | phase_3b hooks |
| Agents/Sub-Agents | notebook-name | description | phase_2 design, phase_3c |
| Trigger phrase | notebook-name | description | phase_1 triggers |
| Output format | notebook-name | description | phase_4 formatting |
| Gap/Edge case | notebook-name | description | phase_2 design |
| [new row for each finding] | | | |

**Notebooks with no relevant findings:** [list any notebooks where all 5 queries returned "no findings"]

### Existing Skills/Plugins Patterns
[Reusable patterns extracted from related skills/plugins, including hook patterns, CLI structures, data models, phase designs]

| Source Skill | Pattern | Reuse Feasibility | Applicable Phase |
|-------------|---------|-------------------|-----------------|
| skill-name | description | high/medium/low | phase_2 design |

### Memory.md Results
[Relevant topic files and lessons]

### Recommendations
[What patterns/lessons should be incorporated into the skill — include agents/sub-agents recommendations here]
```

**NotebookLM Query Guidelines**:
- Always substitute `[skill description]` with a concrete 1-2 sentence summary of what the skill does
- If a notebook contains no relevant findings, still include it in the table with "no findings" rather than omitting
- Deduplicate findings that appear across multiple notebooks — combine into a single row listing all source notebooks
- Rank recommendations by: (1) specificity to the skill domain, (2) evidence strength in source, (3) feasibility of implementation

**Skip this phase when**:
- Simple skills (<5 steps, straightforward execution)
- User explicitly declines knowledge retrieval
- Domain has no existing CKS/memory entries

<!--STATE_SAVE: After Phase 1.5 completes (or skips), write to `.evidence/skill-ship-state-{cwd_hash}/workflow-state.json`:
{"target_skill": "<skill_path>", "quality_dimensions": [<dim1>, ...], "current_phase": "1.5_complete", "skip_reason": null | "simple_skill" | "user_declined" | "no_existing_entries", "workflow_started": "<ISO_timestamp>", "last_updated": "<ISO_timestamp>"}
This enables compaction resilience — if session is compacted during Phase 2+, resume from this state.
CRITICAL: skip_reason MUST be set if Phase 1.5 was not executed. Phase 2 gate checks this field.-->

---

## Phase 2: Creation & Structuring

**Goal**: Create or update the skill structure

**⚠️ Phase 1.5 Gate — MUST SATISFY BEFORE PROCEEDING:**

Before beginning Phase 2, verify ONE of the following:
1. **Phase 1.5 output present** — Knowledge Retrieval Summary appears in conversation or workflow state with CKS results, NotebookLM Enhancement Scan table, and Memory.md results
2. **Phase 1.5 skipped with logged reason** — Check workflow state for skip reason matching one of the defined `skip_when` conditions:
   - `simple_skill`: Skill has <5 steps and straightforward execution
   - `user_declined`: User explicitly declined knowledge retrieval
   - `no_existing_entries`: Verified via `/search` that domain has no CKS/memory/notebook entries

**If neither condition is met** — Phase 1.5 was silently skipped. DO NOT proceed to Phase 2. Execute Phase 1.5 now or document the skip reason in workflow state.

**Enforcement rationale**: Phase 1.5 is the knowledge-retrieval safety net — skipping it means building without access to lessons, patterns, and enforcement mechanisms already documented in CKS/NotebookLM. The violation cost is paid in repeated mistakes across skill iterations.

**Skill Coordination**:
- Invoke **skill-creator** for draft creation and test prompt generation
- Invoke **skill-development** for SKILL.md structure and best practices
- Use **display_templates.md** for output formatting guidance

**Actions**:
1. Create SKILL.md with proper YAML frontmatter
2. **Set Degrees of Freedom** (NEW):
   - Add `freedom: high|medium|low` field to YAML frontmatter
   - **High freedom** (text-based instructions): Multiple approaches valid, decisions depend on context
   - **Medium freedom** (pseudocode/scripts with parameters): Preferred pattern exists, some variation acceptable
   - **Low freedom** (specific scripts, few parameters): Operations fragile, consistency critical
3. Apply progressive disclosure pattern (keep under 500 lines)
4. Choose appropriate output format template from display_templates.md:
   - Template 1: Strict Analysis Format (API-like)
   - Template 2: Executive Summary Format (flexible)
   - Template 3: Hypothesis Testing Format
   - Template 4: Comparison Format
   - Template 5: Workflow Progress Format
   - Template 6: Error Analysis Format
   - Template 7: Research Findings Format

**Output Format**: Use Template 1 (Strict Analysis Format)

```markdown
## Skill Structure Analysis

**Confidence:** [Score]% (Tier [1-4])

### Skill Classification
**Type:** [EXECUTION/KNOWLEDGE/PROCEDURE]
**Freedom Level:** [high/medium/low]
**Complexity Score:** [calculated score]
**Hook Recommendation:** [yes/no with rationale]

### Structure
- YAML frontmatter: ✓
- Description quality: [assessment]
- Progressive disclosure: [assessment]
- Output format template: [Template #]

### Evidence
| Aspect | Status | Notes |
|--------|--------|-------|
| Triggers | [status] | [details] |
| Workflow | [status] | [details] |
| Output | [status] | [details] |
| Tests | [status] | [details] |

### Quality Commitments
[List of flagged dimensions from Phase 1.5 that the skill must address — each dimension listed with how the design addresses it]

| Dimension | Commitment | Validation |
|-----------|-----------|-----------|
| [e.g., Token Efficiency] | [e.g., File-passing IPC instead of content passing] | Phase 3b checks for IPC patterns |
```

---

## Phase 3: Quality & Validation

**Goal**: Ensure skill meets quality standards

**Skill Coordination**:
- Invoke **testing-skills** for trigger and execution path validation
- Invoke **av** for hook generation and improvement analysis
- Run test prompts if configured

**Quality Validation Integration**:

1. **Skill Validation** (recommended):
   - Invoke `/testing-skills` with skill path for validation
   - Testing-skills will verify: YAML completeness, trigger accuracy, constitution links
   - Review validation report and address critical issues before proceeding

2. **Manual Verification Checks** (always performed):
   - **YAML frontmatter**: Verify name, description, triggers, category present
   - **Description quality**: Check ≤100 characters (registry constraint)
   - **Trigger phrases**: Test that phrases actually invoke the skill
   - **Constitution links**: Ensure skill declares which PARTs it extends
   - **Execution paths**: Walk through workflow steps to verify they complete
   - **`execution_hint` alignment** (NEW - catches aspirational tool declarations):
     - Parse `execution_hint` for explicit tool declarations (e.g., `Agent tool:`, `Bash tool:`, `Skill tool:`)
     - If `execution_hint` declares a tool, verify the execution flow actually contains that tool's invocation syntax (e.g., `Agent(...)`, `Bash(...)`, `Skill(...)`)
     - Precedent: Integration Verifier catches `suggest:` pointing to non-existent skills — same philosophy applies to tool declarations
     - Failure mode: `execution_hint: "Agent tool:..."` but no `Agent(...)` call in execution flow → gitbatch-style failure where orchestrator waits for instruction instead of executing

3. **Integration Check** (for orchestrated skills):
   - Verify all skills in `suggest:` field actually exist
   - Use `/similarity` to check for redundant/conflicting skills
   - Document any gaps or overlaps

4. **Progressive Disclosure** (enforced for >300 lines):
   - If SKILL.md exceeds 300 lines, move detailed content to references/
   - Keep main workflow in SKILL.md, advanced guides in references/

5. **Isolation Testing** (NEW - critical safety check):
   - Spawn sub-agent with ONLY the test skill
   - Run 2-3 representative tasks in isolated context
   - Verify: No environment mutations, no side effects
   - Check: Skill executes without affecting user's environment

**Actions**:
1. **Skill validation** (recommended):
   - Invoke `/testing-skills` with skill path
   - Review validation report for critical issues
   - Address FAILED checks before proceeding

2. **`execution_hint` alignment check** (NEW - catches aspirational tool declarations):
   - If `execution_hint` contains `Agent tool:`, `Bash tool:`, or `Skill tool:` → verify the execution flow has the corresponding `Agent(...)`, `Bash(...)`, or `Skill(...)` invocation syntax
   - Precedent: Integration Verifier for `suggest:` field
   - Failure mode: gitbatch — `execution_hint: "Agent tool:..."` but Step 3 only prose-described agent spawning without `Agent(...)` call

2. **Integration verification** (if orchestrated):
   - Check all skills in `suggest:` field exist
   - Use `/similarity` to detect redundancy/conflicts
   - Document any integration gaps

3. **Absence claim verification** (if claims present):
   - Use Read/Grep tools to verify absence claims
   - Require Tier 1 or Tier 2 evidence before accepting
   - Flag unverified claims for user correction

4. **Test trigger phrases** (if complex triggering):
   - Manually test trigger phrases
   - Verify skill activates with intended phrases
   - Optimize description if triggering fails

5. **Check progressive disclosure** (if SKILL.md >300 lines):
   - Verify main content in SKILL.md, details in references/
   - If not compliant: Move content to references/ and restructure

6. **Isolation testing** (NEW - critical safety check):
   - Spawn sub-agent with ONLY the test skill
   - Run 2-3 representative tasks
   - Verify: No environment mutations, no side effects
   - Check: Skill executes in isolated context

7. **Generate hooks** (if complexity score ≥ 1):
   - Invoke **av** for hook generation
   - Apply StopHook for multi-phase workflows
   - Apply PreToolUse hooks for execution requirements

**Output Format**: Use Template 3 (Hypothesis Testing Format)

```markdown
## Quality Validation

| Test | Status | Evidence | Fix |
|------|--------|----------|-----|
| YAML completeness | ✓/✗ | [details] | [action if needed] |
| Trigger accuracy | ✓/✗ | [details] | [action if needed] |
| Output consistency | ✓/✗ | [details] | [action if needed] |
| Execution flow | ✓/✗ | [details] | [action if needed] |
| Quality Commitments | ✓/✗ | [details] | [action if needed] |
| Absence claim verification | ✓/✗ | [details] | [action if needed] |
| Isolation testing | ✓/✗ | [details] | [action if needed] |
| Test coverage | ✓/✗ | [details] | [action if needed] |

### Selected Issues
**Priority:** [High/Medium/Low]
**Issue:** [Description]
**Fix:** [Specific action]

### Validation Plan
1. [Validation step 1]
2. [Validation step 2]
3. [Validation step 3]
```

---

## Phase 3d: Artifact Quality Validation (Conditional)

**Goal**: Validate downstream artifact quality when target skill emits durable artifacts

**Activation Check** — Activate Phase 3d if ANY of the following are true (skip if none):

- [ ] `produces_artifact: true` in SKILL.md frontmatter
- [ ] Description contains "produces" or "artifact" keywords (e.g., "Produces plan artifacts", "emits reports")
- [ ] Workflow steps reference file outputs with artifact names (e.g., `plan.md`, `review.findings.json`, `*.report.md`)
- [ ] Skill category is `planning`, `reporting`, or `analysis`

**If none apply → Skip Phase 3d** UNLESS:
- Skill touches state mutations (file writes, shared data, terminal state) even if output is transient — in that case, apply Safety + Concurrency dimension checks from Quality Commitments
- In that case: run only the relevant rubric criteria (Safety, Concurrency), skip the rest

**Actions**:
1. **Load artifact-rubric.md** — the 5-criterion quality bar for artifact-emitting skills
2. **Locate the artifact** — Find the primary output file(s) the skill produces
3. **Apply the 5 checks**:
   - Single-purpose: artifact addresses one goal, not multiple
   - No raw findings: audit logs/review output synthesized, not pasted verbatim
   - No placeholder residue: no `{{TODO}}`, `[UNRESOLVED]`, unresolved markers
   - Contradiction-free: status is internally consistent (e.g., "ACCEPTED" = no P0 blockers)
   - Decision-complete: all P0/P1 findings incorporated or explicitly deferred with rationale
4. **Synthesize findings** — Do not append raw check output; summarize by criterion

**Blocking gate**: Phase 4 is blocked until `ARTIFACT_PASS` (all P0/P1 criteria met).

**Output Format**:
```markdown
## Artifact Quality Validation

| Criterion | Result | Details |
|-----------|--------|---------|
| Single-purpose | ✓/✗ | [details] |
| No raw findings | ✓/✗ | [details] |
| No placeholder residue | ✓/✗ | [details] |
| Contradiction-free | ✓/✗ | [details] |
| Decision-complete | ✓/✗ | [details] |

### Verdict
**ARTIFACT_PASS** or **ARTIFACT_FAIL** — [list failures if any]
```

---

## Phase 3.5: Evaluation & Iteration

**Goal**: Validate skill performance through empirical testing and iteration

**Choose Evaluation Mode** (NEW):

**Trial Mode** (before installing):
- Test-drive skill with 2-3 representative tasks
- Evaluate: Does it help? Clear instructions?
- Decision: keep, pass, or try another
- Use case: "Try before commit" - quick informal testing

**Evaluation Mode** (before publishing):
- Spawn specialized reviewers for structure/safety/usefulness
- Comprehensive quality audit with formal test suite
- Generate recommendations for improvements
- Use case: "Evaluate before publish" - formal quality gate

**Prerequisites**:
- Requires **skill-creator** plugin (from `~/.claude/plugins/cache/claude-plugins-official/skill-creator/`)
- Eval suite structure: Create `evals/evals.json` in skill directory with test prompts
- Eval viewer: Uses `eval-viewer/generate_review.py` for performance reports (skill-creator feature)

**📖 Detailed Guide**: See `references/eval-guide.md` for complete eval suite creation, test categories, performance interpretation, and description optimization.

**Skill Coordination**:
- Invoke **skill-creator** to run eval suite with `evals/evals.json`
- Use eval-viewer to generate performance reports via `eval-viewer/generate_review.py`
- Apply description optimization script if triggering issues detected
- Iterate until satisfaction threshold met

**Actions**:
1. **Choose mode**: Ask user "Trial mode (test-drive) or Evaluation mode (quality audit)?"
2. Create test prompts (2-3 realistic user queries)
3. Save to `evals/evals.json` format
4. Run evaluation suite with skill-creator
5. Generate performance report with variance analysis
6. Review results with user using eval-viewer
7. Apply description optimization if triggering accuracy < 80%
8. Rewrite skill based on empirical feedback
9. Repeat until performance threshold met

**Output Format**: Use Template 1 (Strict Analysis Format)

```markdown
## Evaluation Results

**Confidence:** [Score]% (Tier [1-4])

### Performance Metrics
| Metric | Score | Target | Status |
|--------|-------|--------|--------|
| Trigger accuracy | [%] | ≥80% | ✓/✗ |
| Output consistency | [%] | ≥90% | ✓/✗ |
| Execution success | [%] | ≥95% | ✓/✗ |
| Variance analysis | [score] | Low variance | ✓/✗ |

### Test Results
| Test Prompt | Expected | Actual | Pass/Fail | Notes |
|-------------|----------|--------|-----------|-------|
| [prompt 1] | [expectation] | [result] | ✓/✗ | [notes] |
| [prompt 2] | [expectation] | [result] | ✓/✗ | [notes] |

### Iteration Plan
1. [Issue identified] → [Fix applied]
2. [Issue identified] → [Fix applied]
3. Re-run eval suite after fixes

### Evidence
| Aspect | Evidence Source |
|--------|-----------------|
| Test output | eval-viewer/generate_review.py |
| Performance | evals/evals.json results |
| Variance | Benchmark comparison |
```

**When to skip this phase**:
- Simple skills with objectively verifiable outputs (file transforms, data extraction)
- User explicitly declines evaluation ("just vibe with me")
- Skills with subjective outputs (writing style, art)

---

## Phase 4: Optimization & Enhancement

**Goal**: Improve skill performance and reliability

**Skill Coordination**:
- Invoke **av2** for mechanical continuation enforcement (if multi-phase workflow)
- Invoke **output-style-extractor** to ensure consistent formatting
- Review display_templates.md for format improvements

**Actions**:
1. Analyze workflow for phase enforcement needs
2. Add StopHook if multi-phase workflow detected
3. Optimize description for triggering accuracy (if Phase 3.5 showed issues)
4. Ensure output format matches chosen template
5. Add progressive disclosure if skill > 300 lines
6. **Consistency verification** (flaky test detection):
   - Run skill 3x with identical prompts
   - Measure output variance across runs
   - Flag non-deterministic behavior
   - High variance = requires fixing before deployment

7. **IMPL Pattern Extraction** (do this properly — thoroughness pass):
   - Read `P:/memory/skill_optimization_patterns.md`
   - Read `P:/.claude/.evidence/critique/IMPROVEMENTS.md`
   - If IMPROVEMENTS.md has entries not yet generalized into skill_optimization_patterns.md:
     - Extract the broader principle from each unimplemented IMPL entry
     - Append generalized principle to `skill_optimization_patterns.md` with a one-line changelog entry:
       `- [date]: [principle summary] — from IMPL entry: [original entry name]`
     - Flag remaining IMPL entries that still need generalization as **pending tasks**
   - If no unimplemented IMPL entries exist: note "IMPL entries fully generalized" in output

**Output Format**: Use Template 6 (Error Analysis Format)

```markdown
## Optimization Analysis

### Summary
**Skill:** [skill-name]
**Location:** [file:line or component]
**Optimization Type:** [Continuation/Format/Performance]

### Issues Identified
| Issue | Impact | Fix |
|-------|--------|-----|
| [Issue 1] | [High/Med/Low] | [Solution] |
| [Issue 2] | [High/Med/Low] | [Solution] |

### Resolution
**Continuation Enforcement:** [StopHook added/updated/skipped]
**Format Standardization:** [Template # applied]
**Performance:** [optimizations applied]

### Prevention
[How to prevent future issues]
```

---

## Phase 5: Distribution & Documentation

**Goal**: Prepare skill for sharing or deployment

**Skill Coordination**:
- Invoke **sharing-skills** for GitHub PR workflow
- Invoke **github-public-posting** for pre-publish checklist
- Document output format in skill if not present

**Actions**:
1. Create fork if needed
2. Create feature branch
3. Commit changes with conventional commits
4. Open PR with proper description
5. Ensure output format documented in SKILL.md

**Output Format**: Use Template 5 (Workflow Progress Format)

```markdown
## Distribution Progress

### Phase 1: Preparation
- [x] Skill validated
- [x] Output format documented
- [x ] PR description written

### Phase 2: Git Workflow
- [ ] Fork repository
- [ ] Create feature branch
- [ ] Commit changes
- [ ] Push to remote

### Phase 3: PR Creation
- [ ] Open pull request
- [ ] Add reviewers
- [ ] Link to issues

### Current Status
**Phase:** [Current phase]
**Blockers:** [Any blockers or "None"]
**Next action:** [Specific next step]
```

<!--STATE_CLEAR: On workflow completion (Phase 5 done or user exits early): delete `.evidence/skill-ship-state-{cwd_hash}/workflow-state.json` — workflow is complete, no need to resume. Use Write tool to delete the file. This prevents stale state from confusing future runs.-->

---

## When to Skip Phases

**Skip Phase 3.5 (Evaluation) when:**
- Simple skills with objectively verifiable outputs
- User explicitly declines evaluation
- Skills with subjective outputs (writing style, art)

**Skip Phase 5 (Distribution) when:**
- Local skill improvements
- Plugin skills (use plugin distribution workflow)
- Skills not intended for sharing

## Quick Reference Table

| Phase | Goal | Key Skills | Output Template | Skip When |
|-------|------|------------|-----------------|-----------|
| Phase 1 | Discovery & Intent | similarity | Template 2 | Never |
| Phase 1.5 | Knowledge Retrieval | notebooklm, cks, memory | Template 2 | Simple skills, user declines |
| Phase 2 | Creation & Structuring | skill-creator, skill-development | Template 1 | Never |
| Phase 3 | Quality & Validation | testing-skills, av | Template 3 | Never |
| Phase 3.5 | Evaluation & Iteration | skill-creator (evals) | Template 1 | Simple skills, user declines, subjective outputs |
| Phase 4 | Optimization & Enhancement | av2, output-style-extractor | Template 6 | Multi-phase workflows only |
| Phase 5 | Distribution & Documentation | sharing-skills | Template 5 | Local skills, plugins, not sharing |
