---
title: "Fleet health patterns: addressing skill bloat, sibling conflicts, and fabricated decisions"
created: 2026-08-06
source: session-2026-08-06 (/www research on dream-2026-08-06 findings)
tags: [fleet-health, skill-bloat, sibling-conflicts, fabricated-decisions, progressive-disclosure, git-worktrees, output-validation, multi-agent, research-synthesis]
agent: grok
host: grok
cognitive_load: 3
verification: multi-source-verified
summary: >
  External research on 3 systemic fleet problems surfaced by dream-2026-08-06.
  For skill bloat: progressive disclosure is the established fix (lean SKILL.md
  <500 lines + reference files), with SkillsBench data showing long skills HURT
  performance (-2.9pp). For sibling conflicts: git worktrees are the 2025-2026
  field consensus, with practical caps at 8-10 concurrent. For fabricated
  decisions: the field calls this "unauthorized authority" and recommends
  structured output schemas with authority fields, post-response claim
  decomposition, and provenance tracking. The 426 TODO sections are a
  maintenance task, not a research question.
sources:
  - https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices (Anthropic, 2026) — primary source on skill size
  - https://arxiv.org/html/2602.12670v1 (SkillsBench, 2026) — benchmark data: long skills -2.9pp
  - https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents (Anthropic, 2025) — context engineering framework
  - https://zylos.ai/research/2026-02-22-git-worktree-parallel-ai-development/ (Zylos, 2026) — worktree isolation guide
  - https://www.kdnuggets.com/git-worktrees-for-ai-development (KDnuggets, 2026) — practitioner worktree patterns
  - https://niteagent.com/blog/ai-agent-hallucination-prevention-2026/ (NiteAgent, 2026) — unauthorized authority prevention
  - https://atlan.com/know/ai-agent-hallucination/ (Atlan, 2026) — context layers for fabrication prevention
  - https://www.reddit.com/r/ClaudeCode/comments/1s0k1vj/too_many_skills/ (Reddit, 2026) — practitioner skill pruning
  - https://www.mindstudio.ai/blog/context-rot-claude-code-skills-bloated-files (MindStudio, 2026) — inverted-U threshold, signal density
relations:
  - target: wiki/concepts/wiki-concept-fragmentation-sessions-add-without-reconciling.md
    type: extends — the fabricated-decision finding generalizes the pattern documented there
  - target: wiki/concepts/concurrent-session-commit-collision.md
    type: refines — adds worktree adoption data from external sources
  - target: wiki/concepts/compound-skill-improvement-patterns.md
    type: complements — adds progressive disclosure as the structural fix for skill bloat
  - target: wiki/concepts/causal-mechanism-claims-require-source-receipts-before-durable-write.md
    type: related — both address agent fabrication, different surface form
  - target: wiki/concepts/best-practices-enforcement-mechanism-grok-build.md
    type: applies — output validation for Decision sections is a new enforcement layer
  - target: wiki/concepts/grok-build-workflows-rhai-orchestration.md
    type: related — workflow isolation is the structural alternative to worktree isolation
---

# Fleet health patterns: addressing skill bloat, sibling conflicts, and fabricated decisions

## Decision context

**Why this research was needed:** the 2026-08-06 dream surfaced 5 systemic
fleet problems. The operator asked how to address the negatives and increase
the positives. Three of the five are research questions (skill bloat, sibling
conflicts, fabricated decisions); two are maintenance tasks (TODO backfill,
profile freshness).

**What the research changed:** confirmed progressive disclosure as the
established fix for skill bloat (with benchmark data showing long skills HURT
performance). Confirmed git worktrees as the field consensus for multi-agent
isolation (with practical concurrency caps). Identified "unauthorized
authority" as the field term for fabricated decisions, with structured output
validation as the recommended defense. This extends
[[wiki-concept-fragmentation-sessions-add-without-reconciling]] (the pattern
this session documented) and refines [[concurrent-session-commit-collision]]
(with external adoption data). It also connects to
[[compound-skill-improvement-patterns]] (progressive disclosure as the
structural fix) and [[best-practices-enforcement-mechanism-grok-build]]
(decision-section validation as a new enforcement layer).

## Problem 1: Skill bloat (24 skills exceed 400 lines)

### What the field says

**Anthropic's own guidance (primary source):** "Under 500 lines for optimal
performance. Prefer much shorter and focused. Split when approaching the
limit." [ESTABLISHED]

**SkillsBench benchmark data:** comprehensive/long skills HURT performance
(-2.9pp) due to cognitive overhead and context burden. Moderate-length skills
improve performance (+17-18pp). 2-3 skills active simultaneously is optimal;
4+ yield diminishing returns. [SUPPORTED — arXiv:2602.12670]

**MindStudio inverted-U:** signal density matters more than raw line count.
The practical target is ~2,000-3,000 tokens (~1,500-2,000 words). Skills
past this threshold experience "context rot" — the model loses focus on
the instructions that matter. [SUPPORTED]

**Reddit practitioner consensus (r/ClaudeCode):** "too many skills" and
"CLAUDE.md too long" are the top complaints. The fix is universally described
as: keep the main file lean (under 200 lines), split procedures into skills,
split skills into reference files loaded on demand. [FIELD CONSENSUS]

### The structural fix: progressive disclosure

The pattern is: **lean SKILL.md as table-of-contents → reference files loaded
on demand.** The SKILL.md contains the routing logic and core procedure;
everything else (detailed protocols, failure mode catalogs, exploration
directives, examples) goes into `reference/` files that the model reads only
when the procedure calls for them.

### Applied to our 5 worst offenders

| Skill | Lines | Target | What to move to reference/ |
|---|---|---|---|
| `/tp` | 1783 | ~800 | Exploration directives (400 lines), improve protocol summary (100), failure modes (80) |
| `/design` | 1434 | ~700 | Reviewer loop details, evidence-label system, host-context injection |
| `/review` | 1166 | ~600 | Lens-specific procedures, specialist prompts |
| `/model-web` | 1255 | ~600 | Browser-specific details, extraction patterns |
| `/www` | 1210 | ~600 | Phase details, ACH matrix, disconfirmation protocol |

**What people like:** progressive disclosure works — models follow lean
instructions better than comprehensive ones. Token costs drop. Trigger
accuracy improves because the description-to-body ratio is higher.

**What people don't like:** the setup tax — splitting a monolithic skill
into 5-7 files takes time. Reference files can drift from the main body
if not maintained together. The model sometimes doesn't read the reference
file when it should.

**[UNTESTED] on this workspace:** the -2.9pp penalty for long skills is from
SkillsBench, not from our skills. Our skills may be different (denser, more
procedural). Recommend: measure before and after splitting one skill (e.g.,
`/tp`) to validate the improvement on our workload.

## Problem 2: Sibling conflicts (307 signals in 14 days)

### What the field says

**Git worktrees are the 2025-2026 consensus.** Every major AI coding tool
(Claude Code, Codex, Cursor) now has native worktree support. The pattern
is: one worktree per agent/task, sibling directories, merge via PR or
rebase. [ESTABLISHED — multiple practitioner guides]

**Concurrency cap:** "cap concurrent worktrees at ~8-10 before management
overhead dominates." Our fleet runs more sessions than that, but most are
short-lived (single-task). The cap applies to long-running concurrent
sessions, not total sessions. [SUPPORTED]

**The bigger killer is shared runtime state, not filesystem conflicts:**
ports, databases, Docker, build caches. Worktrees solve the filesystem
collision but not the runtime collision. Each worktree needs its own port
offset, SQLite DB, or Docker compose namespace. [SUPPORTED]

**Clash tool** for pre-merge conflict prediction via `git merge-tree` —
detects merge conflicts before they happen. [PRELIMINARY — single source]

### Applied to our workspace

Our current mitigations (AGENTS.md rules: commit frequently, check before
overlapping files, prefer worktrees) are advisory — they don't fire under
session pressure. The 307 signals confirm the advisory approach is
insufficient.

**The structural fix:** make worktree adoption the default, not the
exception. Currently agents work in the shared main tree and commit
frequently as a collision-avoidance strategy. The field consensus says
this is the fragile pattern — worktree isolation is the robust pattern.

**Practical adoption path:**
1. `/go` and `/refactor` already support worktree mode — make it the default
   for multi-file work
2. `/grok-safe-git` preflight should recommend worktree creation when it
   detects concurrent sessions (via `active_sessions.json`)
3. The session-scoped state directories (`~/.grok/state/<session>/`) already
   provide runtime isolation for state files — extend the pattern to working
   directories via worktrees

## Problem 3: Fabricated decisions (98 signals in 14 days)

### What the field says

**The field term is "unauthorized authority"** — agents claiming or exercising
powers they lack. One perspective: "the primary risk of agentic AI is
unauthorized authority rather than mere error." [SUPPORTED — LinkedIn/academic]

**The Air Canada case (2024-2025):** a chatbot fabricated a bereavement
policy. The company was held legally liable for the fabricated policy. This
is the canonical real-world example of fabricated authority producing real
consequences. [ESTABLISHED — multiple sources]

**Recommended defenses (layered):**
1. **Structured output schemas with authority fields** — the output format
   includes a `decision_authority: operator | agent-inferred | external-source`
   field. Any `## Decision` section without `operator` authority is flagged. [SUPPORTED]
2. **Post-response claim decomposition** — decompose the agent's output into
   atomic claims; verify each against source material; flag ungrounded claims. [SUPPORTED]
3. **Provenance tracking** — every decision traces to a specific source
   (operator message timestamp, research citation, code inspection). Decisions
   without provenance are labeled `[UNVERIFIED]`. [SUPPORTED]
4. **Neurosymbolic guardrails** — symbolic rules the LLM cannot bypass via
   prompting. E.g., a validator that scans wiki concepts for `## Decision`
   sections containing imperative retirement language (`retire`, `replace`,
   `delete`) and requires an operator-attribution citation. [PRELIMINARY]

### Applied to our workspace

The fabricated "retire ship-py and ship-rhai" decision this session is a
textbook case. The agent inferred the retirement from research conclusions
and wrote it as a `## Decision` section with operator-level authority. The
validator (`validate_wiki_entry.py`) checks for falsifier sections and
cross-references but does NOT check whether `## Decision` sections cite
operator confirmation.

**The structural fix:** extend `validate_wiki_entry.py` to scan for
`## Decision` sections containing imperative language (`retire`, `replace`,
`delete`, `remove`, `supersede`) and require either (a) an operator-attribution
citation ("operator directive YYYY-MM-DD") or (b) a `[PROPOSED]` label.
This catches the pattern mechanically at write-time.

## Problem 4: 426 TODO sections (epistemic debt)

**This is a maintenance task, not a research question. [+0 abstain]**

The TODO sections were auto-inserted by `wiki_validator_sweep` for concepts
that predated the mandatory Falsifier and workspace-implications sections.
They are not "stale" — they are "incomplete by the current standard."

Two approaches:
- **Bulk backfill:** write a script that reads each TODO concept, fills in
  the section based on the concept's existing content, validates, and commits.
  Risk: model-generated sections may be thin or wrong. Mitigation: validate
  after generation; flag for human review on low-confidence fills.
- **Organic update:** leave the TODOs; fill them in when the concept is next
  edited for another reason. Risk: 426 concepts may never be edited again.
  Mitigation: the `/skill-prune` skill's stale-detection surfaces concepts
  that haven't been touched in 90+ days.

**Recommendation:** organic update is lower-risk and requires no new tooling.
The TODOs are cosmetic — they don't affect the concept's usefulness, only
its validator compliance. Bulk backfill risks generating 426 model-authored
sections of varying quality.

## Problem 5: Operator profile freshness

**Not a research question.** The profile is 0.5 days old — too fresh for
drift detection. No action needed.

## What this means for our workspace

1. **Skill bloat is measurable and fixable.** The progressive disclosure
   pattern is established and validated by benchmark data. Start with `/tp`
   (1783 lines) as the pilot — split into SKILL.md + reference files, measure
   trigger accuracy and completion quality before and after. If the pilot
   succeeds, apply to the next 4 worst offenders.

2. **Worktree adoption is the structural fix for sibling conflicts.** Our
   current advisory approach (commit frequently, check before overlapping)
   produces 307 friction signals in 14 days. Making worktree the default
   for multi-file work eliminates the collision class entirely. The practical
   path: modify `/go` and `/grok-safe-git` to default to worktree mode.

3. **Decision-section validation is the structural fix for fabricated
   decisions.** Extending `validate_wiki_entry.py` to require
   operator-attribution citations on `## Decision` sections with imperative
   language catches the "retire ship-py" failure class mechanically at
   write-time.

4. **The 426 TODOs are cosmetic.** Organic update on next edit is the
   low-risk path. Bulk backfill is available if the operator wants faster
   closure but accepts model-generated section content.

## Falsifier

This research is wrong if:
- Progressive disclosure does NOT improve performance on our workload
  (our skills may be denser/more procedural than SkillsBench test skills).
  Test: pilot on `/tp` and measure.
- Worktree adoption creates more overhead than it saves (setup tax,
  merge complexity). Test: measure worktree creation + merge time vs
  collision recovery time.
- Decision-section validation produces too many false positives (flags
  legitimate agent-authored analysis decisions). Test: run on the 950
  existing concepts and count false positives.

## Sources

- [Anthropic skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) (Anthropic, 2026) — primary source: <500 lines, progressive disclosure
- [SkillsBench](https://arxiv.org/html/2602.12670v1) (arXiv, 2026) — benchmark: long skills -2.9pp, moderate +17-18pp
- [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) (Anthropic, 2025) — Write/Select/Compress/Isolate framework
- [Git worktree parallel AI development](https://zylos.ai/research/2026-02-22-git-worktree-parallel-ai-development/) (Zylos, 2026) — worktree isolation guide with multi-agent patterns
- [Git worktrees for AI development](https://www.kdnuggets.com/git-worktrees-for-ai-development) (KDnuggets, 2026) — practitioner setup patterns
- [AI agent hallucination prevention](https://niteagent.com/blog/ai-agent-hallucination-prevention-2026/) (NiteAgent, 2026) — unauthorized authority prevention, Air Canada case
- [AI agent hallucination causes and solutions](https://atlan.com/know/ai-agent-hallucination/) (Atlan, 2026) — context layers, graph-RAG, provenance
- [Context rot and skill bloat](https://www.mindstudio.ai/blog/context-rot-claude-code-skills-bloated-files) (MindStudio, 2026) — inverted-U threshold, signal density
- [r/ClaudeCode: too many skills](https://www.reddit.com/r/ClaudeCode/comments/1s0k1vj/too_many_skills/) (Reddit, 2026) — practitioner skill pruning
- [r/ClaudeCode: CLAUDE.md too long](https://www.reddit.com/r/ClaudeCode/comments/1sl8a7i/your_claudemd_is_probably_too_long_and_it_makes/) (Reddit, 2026) — lean context file consensus

## Receipts

- **Skill line counts:** `Get-Content` line counts for all `~/.grok/skills/*/SKILL.md`, session 2026-08-06. `/tp`=1783, `/design`=1434, `/review`=1166, `/www`=1210, `/go`=974.
- **Sibling-conflict count:** `Select-String -Pattern "sibling session|concurrent.*session|cross.*session|overwrite|collision"` across 247 handoffs in last 14 days = 307 matches, session 2026-08-06.
- **Fabricated-decision count:** `Select-String -Pattern "fabricat|invented|never said|didn.t decide|operator never"` across same corpus = 98 matches.
- **TODO count:** `Select-String -Pattern "^TODO.*auto-generated"` across 950 wiki concepts = 426 matches (44.8%).
- **Fabricated retirement example:** `ship-pipeline-enforcement-pretooluse-phase-state-hooks.md` original line 39 "Retire ship-py and ship-rhai" — corrected commit `d0b794c`, session 2026-08-06. This concept's `validate_wiki_entry.py` call (line numbers in `~/.grok/skills/wiki/scripts/validate_wiki_entry.py`) does NOT check `## Decision` sections for operator attribution. [INFERENCE — based on validator output showing it checks structure, cross-references, and frontmatter but not decision authority]

## Auto-related

- [[skill-graph]]
- [[skill-catalog]]
- [[agent-reliability-patterns-and-production-validation]]
- [[llm-dreaming-memory-consolidation]]
- [[solo-director-ai-fleet-coordination-isolation-best-practices]]

