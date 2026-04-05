---
name: pre-mortem
version: 6.4
description: Pre-mortem failure analysis. Imagine "it's 6 months later and this failed — why?" then work backward to find root causes, cascade effects, and specific mitigations. Includes adversarial validation (8-agent multi-perspective analysis), kill criteria for solo dev, AI/LLM failure modes, success theater detection, fix side effects analysis, and operational verification. Use for: failure analysis, risk assessment, project post-mortems, "what could go wrong", stress testing features, identifying second-order effects, cascade analysis, "will this work?", "what's the worst case?", or anytime the user asks about project risks. Auto-integrates with /reflect.
status: stable
category: analysis
enforcement: advisory
hooks:
  Stop:
    - once: true
      hooks:
        - type: command
          command: "python P:/.claude/skills/pre-mortem/hooks/Stop_hook_premortem_quality_gate.py"
          timeout: 30
---

# Pre-Mortem: Comprehensive Failure Analysis

## Why Pre-Mortem > Risk Assessment

**Risk Assessment:** "What MIGHT go wrong?" → Optimism bias filters answers
**Pre-Mortem:** "It's 6 months later. It FAILED. Why?" → Liberates honest analysis

**Research:** Pre-mortems increase problem identification by 30% (Klein, 2007).

## Core Framework (7-Step Process)

**Quick Reference:**
1. **Step 0**: Extract project constraints from CLAUDE.md
2. **Step 0.7**: Define kill criteria (abandonment triggers for solo dev)
3. **Step 1**: Set failure scenario ("It's 6 months later and this failed")
4. **Step 1.5**: Analyze fix side effects (NEW risks from proposed fixes)
5. **Step 2**: Brainstorm causes (10+ from multi-perspective analysis)
6. **Step 2.5**: Trace second-order effects (minimum 3-step cascades)
7. **Step 2.6**: Check AI/LLM-specific failure modes
8. **Step 2.7**: Check temporal failure modes (context overflow, forgotten constraints)
9. **Step 2.8**: Check interruption, handoff, and contract-boundary failure modes
9. **Step 3**: Categorize (People/Process/Tech/External)
10. **Step 3.5**: Apply reference class forecasting (base rates from similar projects)
11. **Step 3.6**: Detect success theater (fake metrics that mask problems)
12. **Step 3.8**: Operational verification (require empirical evidence)
13. **Step 4**: Rate risks (Likelihood × Impact = Risk Score 1-9)
14. **Step 4.5**: Map dependency cascades
15. **Step 5**: Prevent top 3 + map to actions
16. **Step 6**: Monitor warning signs
17. **Step 7**: Adversarial validation (8-agent multi-perspective analysis)

**Detailed documentation**: See `references/` for deep dives on each step.

## Execution Workflow (MANDATORY - When skill is invoked)

When `/pre-mortem` is invoked, execute the following steps in order:

### Auto-Detect Target (if no arguments provided)

Resolve target via semantic intent, not archaeology:

1. **Named outputs**: If user references a named output from conversation (e.g., "pre-mortem on the auth hook we designed") → use that
2. **Active task context**: If `/code` or `/planning` was recently running → the feature/plan they were working on
3. **Conversation semantic**: What were we discussing when `/pre-mortem` was invoked? What problem were we solving?
4. **Recent changes as fallback**: File modifications in last 5-10 turns — but weight by semantic relevance, not recency alone
5. **Only ask if genuinely ambiguous**: When >3 semantically-distinct targets exist with no clear intent signal

State assumption: "Analyzing [X] — assumption based on [signal]. Correct?" Only prompt for confirmation if intent is unclear.

### Execute Framework Steps

For each step, perform the analysis and document findings:

**Step 0**: Read `CLAUDE.md` at project root and extract constraints (constitutional principles, working principles, domain-specific rules)

**Step 0.7**: Define kill criteria (abandonment triggers for solo dev) - e.g., "If > 2 hours without progress, pivot", "If > 3 unrelated failures, abandon approach"

**Step 1**: Set failure scenario - "It's 6 months later and this failed. Why?"

**Step 1.5**: For each proposed fix, ask "What NEW risks does this fix introduce?"

**Step 2**: Brainstorm 10+ failure causes from multiple perspectives (People, Process, Tech, External)

**Step 2 (continued) — Step-Back Prompting**:
Before listing specific failure causes, apply first-principles grounding:
  Ask "What general architectural principles, invariants, or laws apply to this system?"
  For each principle identified, ask "How could this principle be violated or stressed?"
  Then cascade to specific failure manifestations that breach those principles.
Each failure cause must cite the governing principle it violates.

**Step 2.5 — Cascade analysis**: For each risk with likelihood ≥ 2 (medium or high):
  1. Explore 3 cascade paths ("And then what?")
  2. Evaluate each path:
     - "sure": >70% probability of materializing
     - "maybe": 30-70% probability
     - "impossible": <30% probability
  3. Recommend highest-certainty path (highest probability) as primary cascade
  4. Document lower-certainty paths as alternatives with their probability estimates

**Step 2.6**: Check AI/LLM-specific failure modes (see `references/ai-llm-failures.md`)

**Step 2.7**: Check temporal failure modes
- "LLM forgets requirement from 50 turns ago" (or more)
- "Context window exceeded, earlier constraints dropped"
- "AI contradicts earlier decision"
- Warning sign: "what was the requirement again?"

**Step 2.8**: Check interruption, handoff, and contract-boundary failure modes
- "Compaction occurs between producer write and consumer read"
- "Resume artifact is partial but treated as complete"
- "Consumer expects fields never guaranteed by producer"
- "Stale summary outranks transcript/workspace truth"
- "Producer succeeded but consumer handshake never actually worked"
- "Validator exists nowhere, so partial state silently passes through"

**Step 3**: Categorize each cause: People/Process/Tech/External

**Step 3.5**: Apply reference class forecasting - "What do similar projects show?"

**Step 3.6**: Detect success theater (see `references/success-theater.md`)

For stateful or handoff work, success theater must explicitly check for producer-only proof:
- file written
- payload emitted
- hook completed

without proof that the real consumer validated and used it correctly.

**Step 3.8 — Operational Verification** (REQUIRED):
For each critical/high-risk finding, require ONE of:
- Test output showing actual failure mode
- Code review excerpt showing the bug/invariant violation
- Log excerpt demonstrating the problem
- Read of actual file:line proving the issue exists
Claims without empirical evidence are excluded. This is NOT optional — it is the difference between analysis and speculation.

**Step 4**: Rate each risk: Risk Score = Likelihood (1-3) × Impact (1-3)
For each risk, also include: likelihood% (0-100), confidence% (0-100), uncertainty notes

**Step 4.5**: Map dependency cascades between risks (OPTIONAL)
- Ask: "Do any risks CAUSE, BLOCK, or ENABLE other risks?"
- If YES → Add inline annotations (`[causes: ID]`, `[blocks: ID]`, `[caused-by: ID]`)
- If NO → Skip to Step 5
- **See**: `references/dependency-cascades.md` for complete methodology

**Step 5**: Prevent top 3 risks + map each to a specific action (NO orphan priorities)

**Step 6 — Warning Signs** (REQUIRED):
Document specific observable indicators that each risk is materializing. For each top risk, list:
- What to look for (observable symptom)
- How to detect it (monitoring check or test)
- What it means if seen (escalation trigger)
Generic "monitor closely" statements are insufficient. Be specific: "If error rate exceeds X%, then Y" or "If logs show pattern Z, then escalate."

Example:
• RISK-001 (auth token expiry): Warning sign → Logs show `401` spikes in 15-min window → Trigger → Force re-auth flow

**Step 7**: Adversarial validation - Dispatch agents in TWO phases:

**Phase 1 — Parallel dispatch (7 agents)**:
The Agent tool handles subprocess dispatch and error recovery internally. Dispatch all 7 non-critic agents in parallel:

```python
# Phase 1: Dispatch 7 agents in PARALLEL (all run simultaneously)
# CRITICAL: Each agent writes findings to a JSON file. After writing, the agent's response
# must contain ONLY the file path. This prevents context overflow when 7+ agents run in parallel.
Agent(subagent_type="adversarial-compliance", description="Compliance review", prompt="Review pre-mortem at <analysis_path> for specification violations, solo-dev inappropriate patterns, and constitutional violations. Write findings to your designated JSON file. CRITICAL: After writing your findings to the JSON file, your response must contain ONLY the file path. Do NOT include full findings in your response.")
Agent(subagent_type="adversarial-logic", description="Logic review", prompt="Review pre-mortem at <analysis_path> for pure logic errors, race conditions, off-by-one bugs, and implementation gaps. Write findings to your designated JSON file. CRITICAL: After writing your findings to the JSON file, your response must contain ONLY the file path. Do NOT include full findings in your response.")
Agent(subagent_type="adversarial-performance", description="Performance review", prompt="Review pre-mortem at <analysis_path> for performance bottlenecks, timeouts, N+1 patterns, and scalability limits. Write findings to your designated JSON file. CRITICAL: After writing your findings to the JSON file, your response must contain ONLY the file path. Do NOT include full findings in your response.")
Agent(subagent_type="adversarial-security", description="Security review", prompt="Review pre-mortem at <analysis_path> for security vulnerabilities, data leaks, access control gaps, and injection risks. Write findings to your designated JSON file. CRITICAL: After writing your findings to the JSON file, your response must contain ONLY the file path. Do NOT include full findings in your response.")
Agent(subagent_type="adversarial-testing", description="Testing review", prompt="Review pre-mortem at <analysis_path> for testing gaps, missing scenarios, brittle tests, and coverage gaps. Write findings to your designated JSON file. CRITICAL: After writing your findings to the JSON file, your response must contain ONLY the file path. Do NOT include full findings in your response.")
Agent(subagent_type="adversarial-quality", description="Quality review", prompt="Review pre-mortem at <analysis_path> for maintainability risks, tech debt, code smells, and coupling issues. Write findings to your designated JSON file. CRITICAL: After writing your findings to the JSON file, your response must contain ONLY the file path. Do NOT include full findings in your response.")
Agent(subagent_type="adversarial-qa", description="QA review", prompt="Review pre-mortem at <analysis_path> for missing acceptance criteria, untestable requirements, and validation gaps. Write findings to your designated JSON file. CRITICAL: After writing your findings to the JSON file, your response must contain ONLY the file path. Do NOT include full findings in your response.")
```

**Phase 2 — Series dispatch (critic agent + empirical falsification)**:
After Phase 1 agents complete and their findings are available, dispatch the critic agent with a mandatory falsification mandate:

```python
# Phase 2: Dispatch critic agent in SERIES (after all other agents have reported)
# This allows the critic to review the consensus findings and identify blind spots
Agent(subagent_type="adversarial-critic", description="Critic review", prompt=""Meta-analysis of pre-mortem at <analysis_path> - consensus gaps, blind spots, bias patterns, and contradiction detection. Provide confidence calibration on findings.

MANDATORY FALSIFICATION: For each finding rated HIGH severity, attempt to empirically reproduce or falsify it before confirming the rating:
- Race conditions: write a minimal Python script to trigger the race. If it fails 3x, demote to MEDIUM and note 'not reproduced'
- Threshold claims (e.g. '900s timeout', '50ms latency'): read the relevant code path and verify the actual threshold value
- Existence claims (e.g. 'no test for X'): verify the code/filepath actually exists or doesn't using grep/glob
- Collision/ID conflicts: write a minimal reproduction. If it doesn't trigger in 3 attempts, demote

Report falsification test output for each HIGH finding. A finding without a falsification attempt remains UNVERIFIED with confidence ceiling 50%."")
```

**Why the critic runs in series**: The critic's role is to evaluate the consensus from 7 parallel agents AND empirically verify HIGH severity findings. If the critic runs in parallel with them, it cannot see their findings to critique them or attempt falsification. Running in series ensures the critic has all agent outputs available for meta-analysis and empirical testing.

**After Step 7**: Merge adversarial findings into final output. adversarial-critic provides confidence calibration. Store detailed findings to `.evidence/` directory for future reference.

**Evidence-Based Findings Requirement (v5.1 - 2026-04-02)**:
- ONLY include findings verified by adversarial agents with concrete evidence (file:line citations)
- Reject low-quality or speculative findings without proof
- Each recommended next step MUST link to a verified issue from agent findings
- HIGH severity findings MUST have falsification attempt documented in critic JSON (failure to attempt = UNVERIFIED, confidence ceiling 50%)
- Format: "Issue ID → Evidence file:line → Action"

### Output Format

Produce output using the format below. **Only `✅ RECOMMENDED NEXT STEPS` appears by default.** Use `--verbose` or `-v` to include all sections.

## Output Format

### RNS Output Modes

`/pre-mortem` supports three Recommended Next Steps formats:

- no flag or default behavior -> **minimal**
- `--rns=minimal` -> minimal owner/action/proof format
- `--rns=legacy` -> original legacy domain format

If no flag is provided, always use the **minimal** version.

**Default: Next Steps Only** (actionable, no noise)

### Default RNS Format (Optimal)

Use this format by default.

```md
## ✅ RECOMMENDED NEXT STEPS

### BLOCKING BEFORE IMPLEMENTATION

RISK-XXX - Short title
  Type: ROOT-CAUSE FIX | PROOF / CERTIFICATION | SYMPTOM PATCH
  Owner: `/arch` | `/planning` | `/code` | `/verify --contracts` | `/sqa` | `/reflect`
  Blocking: yes | no
  Depends on: `RISK-...` (optional)
  Survives compaction: yes | no
  Why: Why this matters in concrete system terms.
  Prevention action:
  Concrete change that reduces or removes the risk.
  Proof action:
  Concrete verification step that proves the risk is actually controlled.

### BLOCKING BEFORE VERIFIED

RISK-YYY - Short title
  Type: PROOF / CERTIFICATION
  Owner: `/verify --contracts`
  Blocking: yes
  Depends on: `RISK-...`
  Survives compaction: yes
  Why: Why producer-only proof is insufficient.
  Prevention action:
  None. This is a proof obligation, not a design action.
  Proof action:
  Explicit verification of producer fields, consumer validation, stale rejection, and happy path.

### HARDENING / FOLLOW-UP

RISK-ZZZ - Short title
  Type: ROOT-CAUSE FIX | PROOF / CERTIFICATION | SYMPTOM PATCH
  Owner: `/recap` | `/reflect` | `/top-problems`
  Blocking: no
  Survives compaction: yes | no
  Why: Why this should still be addressed.
  Prevention action:
  Hardening or lesson-capture action.
  Proof action:
  How to verify that the hardening actually took effect.

0 - Do ALL Blocking Steps First
```

**Rules for the optimal format:**

- Every top risk gets an owner skill.
- Every top risk gets both a **Prevention action** and a **Proof action**.
- Every item must be classified as `ROOT-CAUSE FIX`, `PROOF / CERTIFICATION`, or `SYMPTOM PATCH`.
- Every item must state whether it is blocking and whether it must survive compaction.
- For stateful/resume/handoff work, at least one action must target `/verify --contracts`.

### Minimal RNS Format (`--rns=minimal`)

Use this when the user wants a lighter version but still wants ownership and proof.

```md
## ✅ RECOMMENDED NEXT STEPS

1 (ARCH) - Close resume-envelope contract ambiguity
  Owner: `/arch`
  Why: Consumer requirements are still implied.
  Action: Define producer, consumer, required fields, freshness authority, and invalidation trigger.
  Proof: `/verify --contracts hook:resume`

2 (CODE) - Add runtime validation for required fields
  Owner: `/code`
  Why: Partial state can proceed too far downstream.
  Action: Add validator so missing required fields fail fast.
  Proof: Test missing, partial, stale, and valid payload cases.

0 - Do ALL Recommended Next Steps
```

### Legacy RNS Format (`--rns=legacy`)

Use this only when explicitly requested or for compatibility with older consumers.

```
## ✅ RECOMMENDED NEXT STEPS

**Evidence-Based Format (legacy)**: Each action MUST link to verified adversarial finding with evidence.

N – Capture lessons and patterns (automatic)
  Na: Auto-invoke `/learn` - Capture failure patterns to CKS
  Nb: Auto-invoke `/reflect {skill_name}` - Document lessons from this analysis

1 (DOMAIN) - Brief description
  Auto-invoke recommended action or manual check based on finding evidence

0 - Do ALL Recommended Next Steps

*Where N = last technical step number + 1. Learning is always the penultimate section, just above "Do ALL."*
```

**Verbose mode (`--verbose` or `-v`): Full analysis with all sections**

```
## 🔴 WHAT'S ACTUALLY BROKEN

**Step 3.8 content — Critical failures with empirical evidence**
Required: Each item must cite test output, code excerpt, or log line proving the issue.
• CRIT-001 | Hook not in dispatch (Risk 8)
  Evidence: `Stop_router.py:47` — not in UNIVERSAL hooks list
  [causes: CRIT-002, CRIT-003]

• CRIT-002 | Hook never executes (Risk 9)
  Evidence: pytest output shows 0 tests collected for `test_hook_x.py`
  [caused-by: CRIT-001]

## 🟠 HIGH-RISK BEHAVIOR

**Step 6 content — Warning signs with escalation triggers**
Required: Each risk must have observable symptom → detection method → trigger.
• RISK-001 | Auth token expiry race (Risk 6)
  Warning sign → Logs show `401` spikes in 15-min window
  Detection → Monitor auth error rate dashboard
  Trigger → If >5% 401s in 5 min, force re-auth flow

• RISK-002 | Context overflow (Risk 7)
  Warning sign → "what was the requirement again?" appears in logs
  Detection → Session length > 200 turns triggers alert
  Trigger → Compact session immediately

**Dependency annotations** (OPTIONAL - from Step 4.5):
- `[causes: ID]` → This risk directly creates another risk
- `[blocks: ID]` → This risk prevents another risk from starting
- `[caused-by: ID]` → This risk is caused by another risk
- `[enables: ID]` → This risk is required for another risk

Only use when structural dependencies exist. Skip if risks are independent.

## 🧠 BLIND SPOTS & CONTRADICTIONS

• Finding with evidence

## 🧪 TESTING & WATCHLIST (OPERATIONAL CHECKLIST)

**Per run**
• [ ] Check item

**Cadence**
• [ ] Recurring check

## 📂 EVIDENCE ARTIFACTS (FOR DEEP DIVE)

Detailed findings stored in `.evidence/` directory

## ✅ RECOMMENDED NEXT STEPS

[same as default above]
```

**Formatting Rules:**
- Section headers: `🔴 WHAT'S ACTUALLY BROKEN`, `🟠 HIGH-RISK BEHAVIOR`, `🧠 BLIND SPOTS`, `🧪 TESTING`, `📂 EVIDENCE`, `✅ NEXT STEPS`
- Finding format: `ID | Title (Risk N)` with indented bullets
- Evidence requirement: Each action MUST cite verified finding with file:line
- Selection: "3" = all actions in domain 3, "3b" = just action 3b, "0" = everything
- CRITICAL: Every CRITICAL failure must have a corresponding next step
- Domain 7 (learning) MUST be included for adaptive self-improvement
- Default RNS mode is **minimal** unless `--rns=optimal` or `--rns=legacy` is specified

## Usage Patterns

### Default Target Detection

When invoked without arguments, `/pre-mortem` auto-detects the target from recent conversation history. See "Auto-Detect Target" in the Execution Workflow section above for details.

### Integration Points

- **/reflect** - Automatic pre-mortem on project completion
- **/code** - Suggests pre-mortem for complex features
- **/refactor** - Suggests pre-mortem for architectural changes
- **/breakdown** - Mini pre-mortem during task planning

### Remaining Items Tracking (MANDATORY)

**Problem**: Pre-mortem action items marked "TODO" or left incomplete get forgotten. "Did we forget anything?" has no systematic answer.

**Protocol**:

1. **At completion**: All unfixed action items (marked ❌ or not marked ✅) are "remaining items"
2. **Evidence file tracking**: Each pre-mortem evidence file MUST have a "REMAINING ITEMS" section listing unfixed items with:
   - Item ID (e.g., "Step 5")
   - What remains
   - Why it wasn't done (deferred, complex, low-priority, etc.)
3. **"Did we forget anything?" trigger**: When this phrase appears OR when continuing work on a pre-mortem target, IMMEDIATELY:
   - Read the pre-mortem evidence file for the target
   - List all remaining items with their status
   - Ask: "Should any of these be addressed now?"

**Evidence file format**:
```markdown
## REMAINING ITEMS

| Step | Status | Gap | Priority |
|------|--------|-----|----------|
| 5 (QUALITY) | ❌ Open | Structured parsing not implemented | Medium |
| 6 (TESTING) | ❌ Open | Worktree integration tests missing | Medium |
| 7 (SECURITY) | ❌ Open | Lock-free pattern deferred | Low |
```

**This is NOT optional.** Every pre-mortem that produces action items MUST track remaining items. Unfixed items don't disappear unless explicitly deferred with rationale.

## Multi-Terminal Isolation

All pre-mortem operations are multi-terminal safe:

**Prediction Storage**
- Filenames include unique timestamps (ISO 8601 with colons replaced by dashes)
- Filenames optionally include terminal_id or process ID (os.getpid()) for additional collision avoidance
- Each terminal writes to separate prediction files without coordination
- Format: `premortem_{project}_{terminal_id/pid}_{timestamp}.md`

**File Operations**
- Write operations are atomic (single write() call per file)
- No read-modify-write patterns that could cause race conditions
- Prediction files use 0o600 permissions (owner read/write only)

**Kill Criteria Checking**
- Kill criteria validation is read-only (examines files, doesn't modify state)
- No shared mutable state between terminals
- Each terminal operates independently

**Evidence Storage**
- `.evidence/` directory stores adversarial agent findings
- Files are named with timestamps to prevent collisions
- Each agent writes to its own file without coordination

## Success Criteria

- 10+ failure modes identified
- Fix side effects analyzed (Step 1.5)
- Adversarially validated (8-agent multi-perspective analysis)
- Cascade depth traced (all risks ≥6 have 3-step minimum)
- AI/LLM risks checked (Step 2.6)
- Temporal failure modes checked (Step 2.7)
- Success theater detected (Step 3.6)
- **Step 3.8: Operational verification — each critical/high-risk finding has empirical evidence (test output, code:line citation, or log excerpt)**
- **Step 6: Warning signs — each top risk has observable symptom → detection method → escalation trigger**
- Kill criteria defined (Step 0.7)
- Dependency cascades mapped if applicable (Step 4.5 - OPTIONAL)
- Top priorities mapped to actions (NO orphan priorities)

## Version History

For detailed version history, see [CHANGELOG.md](./CHANGELOG.md).

Recent versions:
- **v6.4** (2026-04-02): Optimal RNS format is now default
  - Added three RNS output modes: default/optimal, `--rns=minimal`, and `--rns=legacy`
  - Default now assigns owner skill, prevention action, proof action, blocking status, and compaction-survival status
  - Added explicit distinction between root-cause fix, proof/certification, and symptom patch
- **v6.2** (2026-04-01): Default output is now Next Steps Only
  - Changed default output from full 6-section snapshot to just `✅ RECOMMENDED NEXT STEPS`
  - Added `--verbose` flag documentation for full analysis
  - Rationale: Full output is comprehensive but often overkill for simple changes
- **v6.1** (2026-04-01): Critic agent runs in series after other agents
  - Changed Step 7 to TWO phases: 7 agents in parallel, then critic in series
  - Reason: Critic's role is to evaluate consensus from other agents — running in parallel prevents it from critiquing their findings
  - Updated /planning skill with same two-phase pattern (5 agents parallel, then critic)
- **v5.1** (2026-03-22): Added Step 4.5 dependency cascade analysis
  - Added OPTIONAL inter-risk dependency mapping step
  - Created `references/dependency-cascades.md` with keystone risk pattern
  - Added inline annotation format for dependencies ([causes], [blocks], etc.)
  - Distinguishes structural dependencies from categorization (Step 3)
  - Most solo dev pre-mortems skip this step - only for keystone risk patterns
- **v5.0** (2026-03-20): Evidence-based findings requirement with domain-optimized next steps
  - Added evidence-based findings requirement after Step 7
  - Only include VERIFIED findings with concrete evidence (file:line citations)
  - Updated recommended next steps format to include Domain 7 (learning capture)
  - Each action MUST link to verified adversarial finding with evidence
  - Format: "Issue ID → Evidence file:line → Action"
  - Domain 7 captures lessons via /learn and /reflect for adaptive self-improvement
  - Updated success criteria to require evidence citations and Domain 7
  - Reference: Verified findings from GTO skill-based hook implementation
- **v4.9** (2026-03-20): Fixed adversarial agent dispatch to match working implementation
  - Changed from Python loop pattern to explicit Agent() calls (one per line)
  - Fixed agent types: replaced `code-critic` (doesn't exist) with `adversarial-logic`
  - Fixed agent types: replaced `qa-engineer` (doesn't exist) with `adversarial-qa`
  - Added `adversarial-logic` for pure logic errors (matches planning skill)
  - Added file path references to prompts: "Review pre-mortem at <analysis_path>..."
  - Reference: P:\.claude\skills\planning\SKILL.md:205-210
- **v4.8** (2026-03-20): Added 429 API quota error retry logic for adversarial agents (later removed in v4.9)
- **v4.7.2** (2026-03-20): Fixed adversarial agent dispatch pattern to match working implementation
  - Changed from loop-based to explicit Agent() calls (one per line)
  - Brief descriptions ("Compliance review") instead of f-string patterns
  - Removed `model="haiku"` to use default model
  - Reference: P:\.claude\skills\planning\SKILL.md:205-210
- **v4.7.1** (2026-03-20): Fixed Agent tool syntax - added `description` parameter
- **v4.7** (2026-03-20): Added Execution Workflow section - MANDATORY execution instructions with Step 7 adversarial validation
- **v4.6** (2026-03-20): Generic action patterns expanded to 13 + contextual feedback
- **v4.5** (2026-03-20): Agent tool optimization - Removed Python wrapper
- **v4.4** (2026-03-20): Full integration - 5 structural improvements
- **v4.3** (2026-03-20): Priority-to-action mapping enforcement

---

**Reference**: Klein, G. (2007). "Performing a Project Premortem" - HBR
