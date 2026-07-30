---
thread_id: session-observations-20260730
parent_handoff_path: none
current_session_id: 019fb177-e5d5-7520-92f5-0158f87639c9
current_terminal_id: 3c773c60-e09f-490c-a96b-b14fa5208849
produced_at: 2026-07-30T13:00:00Z
status: open
handoff_type: investigation
accurate_as_of_head: 3f2040c
---

# Session observations — 2026-07-30 close-authority + workflow improvements

## Observations

1. **Skill-graph enumeration discipline gap**: the agent enumerated closure skills from context, not catalog. Root cause is structural (no mechanical rule). Fixed with AGENTS.md rule — next session should verify it fires correctly.

2. **Subagents can't access MCP tools**: discovered during /www Phase 2b when the Reddit research subagent couldn't reach the Reddit MCP. Fixed in /www SKILL.md with parent-level execution rule. This likely affects other MCP-dependent skills when delegated to subagents.

3. **Plan-vs-source contradictions are common**: the plan's RESOLVED set differed from the implementation contract. H3 discovery caught it before implementation. This validates the "wiki library query mandatory for ALL code changes" policy added to /go this session.

4. **/tp → /review overlap**: two separate review pipelines ran on the same code. The /tp found framing issues, /review found code bugs. They're complementary, not redundant — but the operator had to invoke both manually. The new /ship profile chains them.

5. **WIKI: marker auto-capture rule is untested**: the rule was added to AGENTS.md but has never fired end-to-end (marker → session boundary → /wiki batch write). Next session should test by producing a wiki-worthy finding and verifying the marker appears and gets captured.

6. **/ship is designed but untested**: the profile exists in go/SKILL.md but has never run against a real branch. Predictable edge cases: stash/merge/restore ordering, specialist in Phase 1 finding real bugs without session context.

7. **Scanner latency is ~20-28s**: measured during live test. The Stop hook will add this to every /close turn. Not a bug — expected latency.

8. **Reddit MCP search endpoint is broken**: `reddit__search_reddit` fails with "Search failed for all subreddits." Only `reddit__browse_subreddit` works (RSS fallback). The search endpoint may need API credentials that aren't configured.
