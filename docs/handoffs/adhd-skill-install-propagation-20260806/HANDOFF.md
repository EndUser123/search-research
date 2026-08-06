---
thread_id: adhd-skill-20260806
parent_handoff_path: none
current_session_id: 019fd81d-3012-7762-ab3f-71ac0c992a8b
current_terminal_id: grok-adhd-019fd81d
produced_at: 2026-08-06T07:30:00Z
status: open
handoff_type: investigation
accurate_as_of_head: a5b3210d4ec1eb315c33ec50116e8841fec1666f
---

# /adhd skill install + Rule 7 propagation

## Objective

Install and test the i-have-adhd output-style skill on Grok Build, evaluate which of its 10 ADHD-friendly rules are evidence-supported, and propagate the genuinely missing ones into existing skills.

## What now works

- `/adhd` is installed at `~/.grok/skills/adhd/` and invocable next session
- Rule 7 ("make wins visible") is embedded in `/close`, `/handoff`, and `/go`
- SessionStart hook reminds operator that `/adhd` exists
- Clone space convention documented in the wiki

## Status

OPEN — skill installed and 3 skills patched. Testing across live sessions is the remaining work.

## Key decisions

### Decision 1: Opt-in skill, not AGENTS.md or hook

**Choice:** Install as opt-in skill (`/adhd`), not as AGENTS.md rules or a SessionStart hook.

**Selection criterion:** instruction budget compliance.

**Why:** AGENTS.md is already 122K bytes (~30K tokens, ~200+ rules) — past IFScale's "uniform abandonment" threshold (arXiv:2507.11538). Adding rules degrades ALL existing rules. SessionStart hooks are passive on Grok Build (stdout ignored, file:///10-hooks.md:303), so the Claude Code hook-injection pattern doesn't transfer.

**Steelman (rejected):** AGENTS.md always-on block. Stronger per-rule enforcement via system-prompt priority (arXiv:2502.12197). Rejected because every added rule degrades every existing rule in the budget.

**Falsifier:** Grok Build adds a SessionStart context-injection mechanism (not stdout) — hook approach becomes viable and always-on could work.

### Decision 2: Rule 9 rejected

**Choice:** Do not enforce "cap lists at 5 items."

**Why:** ADHD research says working memory is 3-4 items (not 5). And AGENTS.md says "Completeness over curation — list every item with positive ROI." Rule 9 loses on both axes. Resolution: chunk (top 3-4 as "do now"), don't cap.

### Decision 3: Rule 7 propagated to three skills

**Choice:** Only "make wins visible" was propagated. Rules 1 (lead with action), 5 (restate state), 10 (no preamble) were evaluated and found already covered by existing skill output formats.

**Why:** The /tp critique collapsed the 15-edit proposal to 3 edits. Most "ADHD-friendly" rules are already the default output shape (verdict-first, numbered lists, status restated via todo_write).

## Evidence

- IFScale benchmark (arXiv:2507.11538): 20 models tested, best at 68% accuracy at 500 instructions. Our ~200+ rules are in "uniform abandonment" regime.
- Multi-turn decay (arXiv:2505.06120): 39% performance drop across turns. Opt-in injection is less reliable but doesn't compete for system-prompt budget.
- System prompt robustness (arXiv:2502.12197): system prompts have trained priority; user-injected rules don't.
- ADHD rule audit: 5 of 10 rules evidence-supported. Rule 9 contradicted (3-4 items not 5). Rules 8, 10 are style preferences without ADHD-specific evidence.
- AGENTS.md size: 122,727 bytes verified this session via `(Get-Item).Length`.

## Next steps

1. **Test `/adhd` across 3-5 sessions** covering different work types (execution, research, review, planning). Observe which rules actually help vs. feel forced.
2. **After testing, evaluate:** does the operator notice when `/adhd` is active? Do the rules that help match the 5 the research validated (1, 2, 4, 5, 6)?
3. **If Rule 5 (restate state) proves valuable**, consider adding it to `/go` phase progress lines (currently shows phase name only — could add "step X of Y" explicitly).
4. **Wiki concept** at `[[i-have-adhd-skill-implementation-research]]` is the durable reference. Update it after testing.

## Files touched

- `~/.grok/skills/adhd/SKILL.md` (installed)
- `~/.grok/hooks/adhd-skill-reminder.json` (SessionStart reminder)
- `~/.grok/skills/close/SKILL.md` (Rule 7: "What now works" in Completed section)
- `~/.grok/skills/handoff/SKILL.md` (Rule 7: "Lead the body with what now works")
- `~/.grok/skills/go/SKILL.md` (Rule 7: phase lines show what each wave produced)
- `P:/packages/.github_repos/i-have-adhd/` (cloned reference)
- `P:/.data/wiki/concepts/external-repo-clone-space-convention.md` (new)
- `P:/.data/wiki/concepts/i-have-adhd-skill-implementation-research.md` (new, validated)

## Commits

- `~/.grok`: `f7c57bd` — feat: install /adhd skill + add 'make wins visible'
- `P:/`: `c683e9f` — wiki: update /adhd implementation decision

## Suggested skills

- `/check` after next `/adhd` invocation to verify rule compliance
- `/tp` after testing to challenge which rules actually helped
- `/wiki` to update the implementation concept after testing results come in
