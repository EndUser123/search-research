---
thread_id: session-observations-019fa94a-20260728
parent_handoff_path: none
current_session_id: 019fa94a-6738-7ec0-a516-335604633cf6
current_terminal_id: grok-build-primary
produced_at: 2026-07-28T17:10:00Z
status: CLOSED
handoff_type: observation
accurate_as_of_head: HEAD
---

# Session observations — 019fa94a

## Observations

1. **The /tp two-lens process caught a real conflation error.** The handoff marked wiki improvement #6 as "already applied" because the review loop structure existed. The subagent (glm-5-2, 13 tool calls) found that the reviewer prompt had 7 bug-focused dimensions and zero over-engineering dimensions — the loop existed but the function it was supposed to carry was absent. This is the "structure-vs-function conflation" pattern, now documented in [[held-out-data-already-on-disk-count-artifacts-not-invocations]]. The fix was 1 line (dimension 8). The 4 other proposed improvements were dropped/rejected/deferred after the held-out data (24 plans on disk) showed their failure modes had zero observed instances.

2. **Held-out data was already on disk.** Both the subagent and the orchestrator claimed "zero held-out sessions exist." Both were wrong: we counted plan-writer-brand invocations (1) instead of plan artifacts (24 on disk). The 23 pre-consolidation plans are valid held-out data because plan-writer inherited `/plan`'s logic wholesale. A 30-line Python scan answered validation questions that would have been deferred indefinitely. The operator's question "can't we test this idea on our transcripts?" was the catalyst — it reframed the problem from "wait for future sessions" to "scan what's already there."

3. **Ripgrep false negative on gitignored skill directories.** Two separate greps for `name: brainstorming` across `~/.grok` both returned zero matches because `installed-plugins/` is gitignored. The skill existed and was in both the session catalog and `skill-catalog.md` the entire time. This is a structural trap: the old Anti-Forgetting Checklist *recommended* the exact action that failed (step 3: "Grep SKILL.md files"). Fixed in both `~/.grok/AGENTS.md` and `P:/.claude/rules/skill-protocol.md` — catalog-first, grep-not-allowed for skill existence.

4. **Operator rejected plan length budgets decisively.** "I really don't care about plan length, it should be as long as it needs to be. Using an arbitrary plan length looks like a footgun." This is a clear preference: quality is the target, not length. Arbitrary thresholds become targets (Goodhart's law). The plan-writer skill should never impose line limits.

5. **The Verschlimmbesserung pattern applied to the improvement process itself.** The 4 proposed improvements were designed to prevent over-engineering, but adding 4 checks to a 640-line skill IS the accretion pattern. The skill that prevents bloat was itself bloating. The resolution: 1 of 6 improvements had positive ROI (dimension 8); the other 5 were dropped. The skill was then reduced from 640 to 466 lines by offloading provenance prose to `reference/provenance.md`.

6. **/tp on the improved plan-writer found 4 more issues — 1 false positive.** The false positive (dead `/brainstorming` reference) propagated from subagent to orchestrator to almost being acted on. Caught only by direct `read_file` of the skill file during implementation. Receipt rule lesson: a grep returning "no matches" is not proof of absence when the search path is gitignored. The catalog is the authoritative registry.

## Meta-observations

- The session was a focused skill-improvement arc: /tp review → decisions → implementation → /tp review of the implementation → root-cause fix. No context-window compaction. Dense but linear.
- The operator's corrections were consistently about root-cause depth: "can't we test this on transcripts?" and "we need to fix the root cause of this" — each pushed from symptom to structural fix.
- The session produced 2 wiki concepts (1 new, 1 updated), 4 commits in ~/.grok, 6 commits in P:/, and root-cause fixes in 2 authority files.

## Open items

- ~~`/aar` not yet run~~ — **DONE**: AAR finalized at `20260728-171500/aar-report.md`
- No background tasks orphaned (both /tp subagents completed cleanly)

## Post-AAR work (session continuation)

After the AAR, the session continued with:

1. **Deferred-improvements-registry** created (`P:/.data/wiki/concepts/deferred-skill-improvements-registry.md`) — fleet-wide tracking of deferred/rejected skill improvements, analogous to `tool-fallbacks.md`.
2. **Corpus mining** — 20 AARs + 193 handoffs scanned for friction patterns. Fleet-wide friction taxonomy written (`fleet-wide-friction-taxonomy-20260728.md`). Finding: closure-pressure dominates (118 hits/43 files); 9 of 10 friction classes already documented; finding velocity exceeds resolution velocity.
3. **Handoff-cleanup sweep** executed — 80% open rate is velocity, not hygiene (zero stale handoffs). ~30 early-session items reviewable.
4. **Removal protocol** ported from Claude Code to Grok Build (`~/.grok/docs/removal-protocol.md`), summary inlined in AGENTS.md.
5. **Active-surface reading** confirmed `P:/.claude/hooks/` (280 files) is entirely dead on Grok Build (`compat.claude.hooks: OFF`). Cleanup handed off as fresh-session task.
6. **Hook-timeout deferral** removed from registry — concept already exists at `hook-evidence-collection-cost-vs-timeout-tradeoff.md`.
