# "Next Steps" Pattern Research - CSF NIP Skills

**Date:** 2026-02-08
**Researcher:** Claude (with user guidance)
**Context:** User observed duplicate "Next Steps" sections in my output, triggering investigation into actual patterns used across skills.

---

## Executive Summary

**Finding:** The CSF NIP skill ecosystem uses **6 distinct "Next Steps" patterns** depending on workflow context. No unified auto-suggest system exists - `next_command_suggester.py` is a disabled no-op stub.

**Key Design Principles:**
1. No laundry lists (max 4-5 options)
2. Context labels guide decisions (`[Ready to Ship]`)
3. "Or" provides escape hatch
4. Exact commands preferred
5. State-dependent routing (HALT vs COMPLETE)
6. Progressive disclosure over overwhelming menus

---

## Research Methodology

**Tools Used:**
- Grep across 100+ SKILL.md files for pattern detection
- Read verification of build, tdd, v, design, debug, plan skills
- Pattern extraction from actual skill documentation

**Evidence Base:**
- Tier 1: Direct file reads (SKILL.md files)
- Tier 2: Grep pattern matching across codebase
- Confidence: 95% (direct observation)

---

## The Six Patterns

### Pattern 1: "pick one" with Context Labels

**Used in:** `/build`, `/design`, `/analysis-logs`, `/analysis-audit`

**Template:**
```
**Next Steps** (pick one):

1. [Ready to Ship] `/qa` (Certify feature)
2. [Needs Refactoring] `/evolve` (Clean up debt)

Reply with a number, or describe what you need.
```

**Characteristics:**
- 2-4 options only (not overwhelming)
- Labels in brackets provide context for decision
- "Reply with a number" prompt for user interaction
- Used when: Clear branching paths with different outcomes

**Evidence locations:**
- `P:\.claude\skills\build\SKILL.md:346-359`
- `P:\.claude\skills\design\SKILL.md:281-295`
- `P:\.claude\skills\analysis-logs\SKILL.md:113-121`

---

### Pattern 2: Alphanumeric with "Or" Alternative

**Used in:** `/tdd`

**Template:**
```
## Next Steps

1 - Fix QUAL-XXX: [specific action required]
2 - Address PERF-XXX: [specific action required]
3 - Run full regression: pytest tests/ -v
4 - Or: Proceed with deployment/usage
```

**Characteristics:**
- 4+ items showing remaining work
- "Or:" option provides escape hatch
- Specific commands included
- Used when: Multiple remaining tasks, linear progression possible

**Evidence location:**
- `P:\.claude\skills\tdd\SKILL.md:588-628`

---

### Pattern 3: Context-Dependent (HALT vs COMPLETE)

**Used in:** `/v` (validation pipeline)

**Template (HALT):**
```
## Next Steps

1 - /tdd Fix {specific_finding_id} only
2 - /tdd Fix CRITICAL findings
3 - /tdd Fix HIGH findings
4 - /tdd Fix all filtered findings
x - /tdd All findings
```

**Template (COMPLETE):**
```
## Next Steps

1 - Format code: ruff format <target>
2 - Add docstrings: /refactor <target>
3 - Address remaining MEDIUM findings
4 - Or: Proceed with deployment/usage
```

**Characteristics:**
- Different options based on pipeline state
- HALT: prioritized fix options (specific → all)
- COMPLETE: optional cleanup + proceed option
- Used when: Multi-stage pipeline with different outcomes

**Evidence location:**
- `P:\.claude\skills\v\SKILL.md:669-718`

---

### Pattern 4: Conditional Sections

**Used in:** `/analysis-logs`, `/docs`

**Template:**
```
## Next Steps

**If logs found the issue:**
**Next Steps** (pick one):
1. [Found Error] `/debug`
2. [Security Issue] `/audit`

**If no logs found:**
[Suggest /search or other alternatives]
```

**Characteristics:**
- Nested conditions based on results
- Different paths for different outcomes
- Used when: Tool has multiple possible result states

**Evidence location:**
- `P:\.claude\skills\analysis-logs\SKILL.md:113-123`
- `P:\.claude\skills\docs\SKILL.md:310-315`

---

### Pattern 5: Inline "Next Action" (Not a Section)

**Used in:** `/v`, `/plan`, `/validate_spec`

**Template:**
```
# /v: Every finding MUST include a concrete Next Action
# (exact fix command or edit location)

# /plan: Each Next Action must be copy-pasteable
1. Search existing code: `/search "[feature]"`
2. Run /duf for pre-mortem: `/duf --plan <plan.md>`
```

**Characteristics:**
- "Next Action" is per-item, not a section
- Exact commands provided
- Used when: Continuous flow, not end-of-workflow summary

**Evidence locations:**
- `P:\.claude\skills\v\SKILL.md:108` (rule), `613` (Layer 4)
- `P:\.claude\skills\plan\SKILL.md:408-467` (Next Actions section)

---

### Pattern 6: Table Format

**Used in:** `/debug`

**Template:**
```
## Next Steps Table

| Step | Tool | Purpose |
| ---- | ---- | ---- |
| 0 | Reproduce | Confirm bug exists |
| 1 | /logs | First triage |
```

**Characteristics:**
- Tabular reference, not interactive
- Tool + purpose mapping
- Used when: Reference guide for multi-step debugging

**Evidence location:**
- `P:\.claude\skills\debug\SKILL.md:510-520`

---

## Pattern Selection Matrix

| Context | Recommended Pattern | Options Count | Example Skills |
|---------|---------------------|---------------|----------------|
| **End of workflow, 2 clear paths** | Pattern 1: "pick one" with labels | 2-3 | /build, /design |
| **Multiple remaining tasks** | Pattern 2: Alphanumeric with "Or" | 4+ | /tdd |
| **Multi-stage pipeline** | Pattern 3: Context-dependent | Varies | /v |
| **Conditional results** | Pattern 4: Conditional sections | 2-3 | /analysis-logs |
| **Per-item actions** | Pattern 5: Inline "Next Action" | N/A | /v findings |
| **Reference guide** | Pattern 6: Table format | N/A | /debug |

---

## Original Issue Documented

**User Observation:** Duplicate "Next Steps" sections in my output

**What happened:**
1. I created bulleted summary of next steps
2. Then added "Next Action (pick one)" section
3. This was redundant and violated skill patterns

**Correct pattern (from /build):**
```
**Next Steps** (pick one):

1. [Ready to Ship] `/qa` (Certify feature)
2. [Needs Refactoring] `/evolve` (Clean up debt)

Reply with a number, or describe what you need.
```

**Lesson:** Use a single section, not multiple formats for the same information.

---

## Current State of Auto-Suggestion

**Finding:** No working auto-suggest system exists.

**Evidence:**
- `P:\.claude\hooks\next_command_suggester.py` is a disabled no-op stub
- Contains only: `pass  # No-op - hook disabled`
- Each skill manually defines its "Next Steps" in SKILL.md

**Implication:** Workflow guidance is manual, not automated. Each skill author must include appropriate next steps in their skill documentation.

---

## Design Principles Extracted

1. **No laundry lists** - Maximum 4-5 options presented at once
2. **Context labels matter** - `[Ready to Ship]` > just `/qa`
3. **"Or" provides escape** - Always give user an out
4. **Exact commands preferred** - `pytest tests/ -v` > "run tests"
5. **State-dependent routing** - Different options for HALT vs COMPLETE
6. **Conditional branching** - Different paths for different outcomes
7. **Copy-pasteable actions** - Commands should be ready to execute
8. **Progressive disclosure** - Show immediate next step, mention what comes after

---

## Industry Research: External Validation (2026-02-08)

**Research Method:** Multi-source web research using Serper, Exa, Tavily, and GLM-4.7
**Query:** CLI next step suggestions workflow patterns progressive disclosure
**Sources:** 4 providers, 10+ articles/documentation pages

### Key External Findings

#### 1. Progressive Disclosure is Universal Practice

**From multiple sources:**
- "One-Flag Happy Path, Then Progressive Disclosure" - Make common cases simple, save knobs for later
- "Defers advanced features to secondary UI components, reducing cognitive load"
- "Terminal interfaces naturally support progressive disclosure, loading only context needed"

**Validation:** Our Pattern 1 ("pick one" with 2-3 options) aligns with this principle.

#### 2. Context-Aware Suggestions Are Expected

**From GLM-4.7 research:**
"The workflow for 'Next Command Suggestions'...typically follows five stages:
1. **The Trigger** - Command execution completion or user pause
2. **Context Analysis** - Git status, test results, recent commands
3. **Suggestion Generation** - Based on current state
4. **Presentation** - Ranked by relevance
5. **User Selection** - Accept, modify, or dismiss"

**Validation:** Our Pattern 3 (HALT vs COMPLETE) and Pattern 4 (Conditional Sections) implement state-aware routing.

#### 3. Labels and Descriptors Reduce Cognitive Load

**From IxDF (Interaction Design Foundation):**
"Progressive disclosure...ensure each subsequent step builds on the previous step in both consistency, user goal, and value"

**Validation:** Our `[Ready to Ship]`, `[Needs Refactoring]` labels provide consistency and goal clarity.

#### 4. Escape Hatches Are Standard Practice

**From CLI UX sources:**
- Always provide an "Other" or custom input option
- Don't lock users into predetermined paths

**Validation:** Our "Or:" escape pattern in Patterns 1, 2, 3 matches this standard.

#### 5. State-Dependent Routing is Critical

**From GitHub Actions/Terminal research:**
- Different actions based on workflow status (pass/fail, running/completed)
- Terminal UI shows different options based on run state

**Validation:** Our Pattern 3 (HALT vs COMPLETE) implements this directly.

### What's Missing from Our Implementation

| Gap | Industry Practice | Our Current State |
|-----|-------------------|-------------------|
| **Progressive Disclosure Mechanism** | Show 1-2 primary, reveal more on request | Show all options (2-4) at once |
| **Learning/Adaptation** | AI-powered suggestions that learn from patterns | Fixed suggestions per skill |
| **Ranking/Relevance Scoring** | Rank by likelihood, recent usage, context | Static order |
| **Auto-Detection of "Obvious" Steps** | Auto-execute clear next steps | User must always select |

### Recommendations (by Reversibility)

#### Short Term [R:1] - Low Risk
1. **Add progressive disclosure to existing patterns**
   - Show 1-2 primary options by default
   - Add "Show more options..." to reveal additional items
   - Maintain current escape hatch pattern

2. **Standardize label format across skills**
   - `[Adjective + Noun]` format for consistency
   - Examples: `[Ship Ready]`, `[Tests Failing]`, `[Needs Review]`

3. **Add "auto-proceed" option for common workflows**
   - After `/build` success: Auto-suggest `/qa` with "Press Enter to accept"
   - After test failure: Auto-suggest `/debug` with confirmation

#### Medium Term [R:2] - Moderate Risk
4. **Implement suggestion ranking**
   - Track user selection patterns
   - Rank options by frequency
   - Boost contextually relevant options

5. **Add hybrid auto/interactive mode**
   - Detect "obvious" next steps (single clear path)
   - Auto-execute with --auto flag
   - Fall back to interactive for ambiguous cases

#### Long Term [R:3] - Significant Investment
6. **Re-enable `next_command_suggester.py` with ML**
   - Use semantic search over skill registry
   - Rank by context similarity
   - Learn from user workflows

7. **Create unified suggestion engine**
   - Centralize all "next step" logic
   - Provide consistent API for skills
   - Enable cross-skill workflow awareness

### External Sources

- [10 CLI UX Patterns That Users Will Brag About](https://www.nickis.ninja/2019/11/cli-ux-patterns/) - Serper
- [What is Progressive Disclosure? | IxDF](https://www.interaction-design.org/literature/topics/progressive-disclosure) - Serper
- [Skill authoring best practices - Claude API Docs](https://docs.anthropic.com/claude/docs/skill-authoring-best-practices) - Serper
- [GitHub CLI: Work with GitHub Actions in your terminal](https://cli.github.com/manual/gh_run) - Tavily
- [GLM-4.7 Analysis: Developer tools command completion workflow](https://api.z.ai) - GLM

---

## Answer to Original Question

**Question:** "what's a good way to present options to the user?"

**Evidence-based answer:**
1. Use **Pattern 1** ("pick one" with labels) for 2-3 clear branching paths at workflow end
2. Use **Pattern 2** (alphanumeric with "Or") for 4+ remaining tasks
3. Use **Pattern 3** (context-dependent) for multi-stage workflows
4. Never show 10+ options at once - use progressive disclosure instead
5. Include context labels in brackets to guide decision-making
6. Always provide an "Or:" option for escape
7. Make commands copy-pasteable (no placeholders)

---

## Future Work

### Completed (2026-02-08)
- ✅ Documented 6 patterns across CSF NIP skills
- ✅ Validated against industry best practices
- ✅ Identified gaps and improvement opportunities

### Short Term [R:1] - Ready to Implement
1. Add progressive disclosure to existing patterns
   - Show 1-2 primary options by default
   - Add "Show more options..." to reveal additional items
2. Standardize label format across skills (`[Adjective + Noun]`)
3. Add "auto-proceed" option for common workflows

### Medium Term [R:2] - Requires Planning
4. Implement suggestion ranking (track user patterns)
5. Add hybrid auto/interactive mode (detect obvious steps)

### Long Term [R:3] - Significant Investment
6. Re-enable `next_command_suggester.py` with ML-based semantic search
7. Create unified suggestion engine for cross-skill workflows

**Decision point:** Which short-term improvement to tackle first?

---

## Verification Commands

To re-verify these patterns:

```bash
# Search for "pick one" pattern
grep -r "pick one" P:\.claude\skills\*/SKILL.md

# Search for conditional next steps
grep -r "Next Steps" P:\.claude\skills\*/SKILL.md -A 5

# Check specific skills
cat P:\.claude\skills\build\SKILL.md | grep -A 10 "Next Steps"
cat P:\.claude\skills\tdd\SKILL.md | grep -A 10 "Next Steps"
cat P:\.claude\skills\v\SKILL.md | grep -A 10 "Next Steps"
```

---

## Related Files

- `P:\.claude\hooks\next_command_suggester.py` - Disabled stub
- `P:\.claude\skills\build\SKILL.md` - Lines 346-359
- `P:\.claude\skills\tdd\SKILL.md` - Lines 588-628
- `P:\.claude\skills\v\SKILL.md` - Lines 669-718
- `P:\.claude\skills\design\SKILL.md` - Lines 281-295
- `P:\.claude\skills\plan\SKILL.md` - Lines 408-467

---

**Research Complete:** 2026-02-08
**Last Updated:** 2026-02-08 (Added industry research findings)
**Status:** Ready for implementation - Prioritized recommendations by reversibility
