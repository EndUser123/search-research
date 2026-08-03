---
thread_id: session-observations-019f9a3c-20260729
parent_handoff_path: none
current_session_id: 019f9a3c-a088-7230-97c3-7959e8bae1cd
current_terminal_id: console_1faf8be6-6283-4495-939e-9252
produced_at: 2026-07-29T23:00:00Z
status: CLOSED
handoff_type: observations
---

# Session observations — 2026-07-29

## Observations

1. **close_runner.py treats `needs_attention` as a hard failure (exit 1), hiding gate states.** The runner validates gates and exits non-zero when ANY gate is `needs_attention`, producing "CLOSE INCOMPLETE — scanner unavailable" even though the scanner ran successfully. The full gate states ARE in the evidence ledger JSON (per-session file in the close-evidence artifacts dir) but the runner's error template hides them. Consider: either the runner should render gate states for needs_attention (allowing the LLM to resolve them), or the SKILL.md should document that exit 1 + needs_attention is the expected flow (resolve → re-run). Source: this session's `/close` attempts.

2. **Compaction loses write-path attribution.** The close scanner uses `chat_history.jsonl` to attribute file writes to the session. After compaction, early tool calls are in `compaction/segment_*.md` files, not `chat_history.jsonl`. This causes `session_write_paths: []` even when 100+ files were written. The scanner then can't auto-commit. Workaround: manually identify and commit session files. Source: this session's git_state gate showed `session_write_paths: []` despite 152 verification receipts.

3. **Skill non-compliance is the dominant friction pattern.** 4+ operator corrections this session were caused by the agent not following skill SKILL.md instructions (compressing to mental summary + applying general heuristic). The AGENTS.md meta-rule added this session is the behavioral fix; O1 in the AAR proposes a structural (hook) fix. Monitor whether the meta-rule alone reduces the pattern.
