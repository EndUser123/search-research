# Skill Discovery Report
## Executive summary
I analyzed the local Codex transcript corpus conservatively and found three high-confidence skills worth creating now: `codex-transcript-recovery`, `plugin-hook-source-of-truth-audit`, and `review-packet-runner`. Several other recurring workflows are real, but the evidence points to strengthening existing skills rather than creating new standalone skills: YT-IS/NotebookLM operations, AI API benchmarking, planning command governance, handoff restore audits, and companion-guide document review.
Top recommendation: create fewer skills with stronger triggers. The corpus already has many overlapping skills, so new skills should only cover repeated workflows that have clear failure modes and are not already handled by existing frontmatter.
## Methodology
- Inputs: `C:/Users/brsth/.codex/sessions/**/*.jsonl`, existing skill folders under `P:/packages/.claude-marketplace/plugins`, `P:/.claude/skills`, `C:/Users/brsth/.codex/skills`, and `C:/Users/brsth/.agents/skills`.
- Corpus size: 491 rollout JSONL files, about 1.2 GB.
- Extraction: full streaming pass over all transcript files, filtering system/developer scaffolding and environment-only records. This produced 6711 user task records across 473 session files.
- Clustering: regex-assisted grouping of repeated task language, followed by manual consolidation against examples and the existing skill inventory.
- Ranking: frequency, severity, cross-project reuse, and workflow clarity.
- Copyright/privacy handling: examples are short paraphrases or brief snippets, not long transcript quotations.
## Ranked candidate skills
### 1. codex-transcript-recovery
- Why it exists: Recover and analyze prior Codex session transcripts from local rollout JSONL logs without guessing from memory or the newest file.
- Trigger conditions: User asks for a previous conversation; User gives a Codex rollout path; User asks to find what happened in an earlier session; User references a project-specific prior discussion.
- Evidence from transcripts: 499 filtered task hits across 11 sessions using strict recovery phrases; broader transcript/session language appears in 171 sessions but includes noise.
- Failure modes it should prevent: Searching the whole session tree without narrowing by project/topic; Assuming the newest transcript is the target; Summarizing from recollection instead of transcript evidence; Missing the distinction between Claude transcript paths and Codex rollout paths.
- Standalone or broader section: standalone skill.
- Existing overlap: search-research/chs searches chat history; snapshot/id reports Claude Code identity.
- Confidence: high.
- Recommended action: create now.
- Supporting examples:
  - `rollout-2026-04-29T08-28-28-019dd9a4-2c3c-7a31-a0a2-52c6ec32ef2a.jsonl`: User corrected the agent that the prior conversation was about YT-IS testing plans, not a generic path-error chat.
  - `rollout-2026-04-29T08-33-35-019dd9a8-dc39-7e31-b633-73ab6db27cb7.jsonl`: Follow-up identified the relevant prior YT-IS NotebookLM worker-load/testing transcript and handoff.
  - `rollout-2026-05-04T15-53-11-019df4fb-1e8f-71f1-bb16-3b39fa28d841.jsonl`: User supplied a specific rollout JSONL and asked to find a failed trial run at the end of the transcript.
### 2. plugin-hook-source-of-truth-audit
- Why it exists: Trace live Claude/Codex hook and plugin behavior back to package-owned source files, cache installs, and registry settings before editing.
- Trigger conditions: User asks what hooks/plugins are currently implemented; Hook path or plugin cache looks stale; A package-owned plugin needs a durable fix; Settings and package manifests disagree.
- Evidence from transcripts: 126 strict hits across 81 sessions for source-of-truth, hook manifest, cache, plugin audit, and installed-plugin language; broad hook/plugin terms appear in 195 sessions.
- Failure modes it should prevent: Editing local cache copies instead of package source; Treating settings.json as the only authority; Leaving stale hook filenames or duplicate registrations; Fixing symptoms without running plugin audit/cache refresh.
- Standalone or broader section: standalone skill or strong section under plugin-doctor/plugin-installer.
- Existing overlap: cc-skills-utils/plugin-doctor; cc-skills-utils/plugin-installer; skill-guard/migrate_skill_ef.
- Confidence: high.
- Recommended action: create now.
- Supporting examples:
  - `rollout-2026-01-26T08-26-30-019bfae9-e302-7f20-b4f5-b25f2c59cde8.jsonl`: Assumption-audit hook replacement required distinguishing hook behavior from regex false positives.
  - `rollout-2026-02-07T14-08-49-019c39ef-98f6-7bf3-ac75-250b335a593f.jsonl`: Stop hook loop blocked a fix repeatedly after already-verified path evidence, requiring root-cause tracing of hook logic.
  - `rollout-2026-01-17T11-00-25-019bcd1d-8ef2-7c80-ae2f-8076601f264c.jsonl`: Damage-control hook blocked git-lock cleanup and forced inspection of hook patterns and protected paths.
### 3. review-packet-runner
- Why it exists: Convert critiques, model feedback, and review requests into evidence-grounded audit packets with facts, inferences, open questions, and next actions.
- Trigger conditions: User asks for review, critique, gaps, opportunities, or assessment; User asks to turn critique into an operating model; User wants an audit packet rather than a narrative; Another LLM produced findings that must be verified.
- Evidence from transcripts: 332 strict hits across 133 sessions for critic, findings, review packet, audit packet, premortem, and gap/opportunity language; broad planning/review language appears in 252 sessions.
- Failure modes it should prevent: Narrative agreement without verification; Mixing facts with interpretation; Accepting another model's findings without local evidence; No severity/risk/action fields for follow-up.
- Standalone or broader section: standalone skill if used across domains; otherwise merge into pre-mortem/skeptic/review skills.
- Existing overlap: cc-skills-sdlc/pre-mortem; cc-skills-thinking/skeptic; quickstop/audit; agent-performance-analyzer.
- Confidence: high.
- Recommended action: create now.
- Supporting examples:
  - `rollout-2025-11-28T12-50-37-019acc04-7af3-7d90-a06e-688fe0d2bd24.jsonl`: User asked for gaps and opportunities against plan/task/data-model artifacts.
  - `rollout-2026-01-05T09-51-01-019b8f11-b6ea-75a2-8925-3aa414e5b846.jsonl`: User requested review of a yt-fts refactoring plan with critical findings and questions.
  - `rollout-2026-01-17T11-00-25-019bcd1d-8ef2-7c80-ae2f-8076601f264c.jsonl`: User asked to assess another LLM's implementation and distinguish what was done well from what broke.
### 4. yt-is-notebooklm-benchmark-ops
- Why it exists: Run and document YT-IS NotebookLM/caption/Whisper fetch, canary, routing, and worker-load experiments with explicit evidence capture.
- Trigger conditions: User mentions yt-is canary/fetch/routing; NotebookLM worker-load comparison; Transcript fallback/no captions/live stream routing; Whisper no-speech classification.
- Evidence from transcripts: 983 strict hits across 77 sessions for yt-is, NotebookLM, canary, transcript routing, Whisper, and related media terms.
- Failure modes it should prevent: Changing routing without stopping canary; Comparing worker load on different samples; Over-trusting summaries instead of live traces/logs; Losing benchmark requirements and evidence fields.
- Standalone or broader section: section inside existing yt-is or yt-nlm skill.
- Existing overlap: cc-skills-media/yt-is; cc-skills-media/yt-nlm; cc-skills-media/nlm; local nlm-skill.
- Confidence: high.
- Recommended action: merge into another skill.
- Supporting examples:
  - `rollout-2026-04-29T08-33-35-019dd9a8-dc39-7e31-b633-73ab6db27cb7.jsonl`: Prior YT-IS testing conversation included back-to-back worker-load comparison and canary restart instructions.
  - `rollout-2026-01-07T22-32-46-019b9c17-d698-7833-85b1-8c65f0a92780.jsonl`: Work involved Whisper transcript engine behavior and transcript schema handling.
  - `rollout-2026-01-13T23-47-07-019bbb42-103b-74b0-ab6a-c8c1fce9c9ee.jsonl`: NotebookLM/Gemini/YouTube tooling context appeared alongside operational channel processing questions.
### 5. ai-api-model-benchmarking
- Why it exists: Run controlled multi-provider model comparisons and summarize cost, routing, timeouts, answer fidelity, and failure modes.
- Trigger conditions: User asks to compare OpenRouter/NVIDIA/NIM/Kimi/Qwen/Gemini/Claude models; AI API live comparison JSON files are present; Router/quota/model selection behavior is under review.
- Evidence from transcripts: Strict model/API terms appeared heavily, though some hits include YouTube channel names such as NVIDIA; root-level ai_api comparison artifacts corroborate this workflow.
- Failure modes it should prevent: Uncontrolled provider comparisons; Timeout fixes not validated live; Mixing budget and budgetless runs; No structured answer fidelity fields.
- Standalone or broader section: section inside existing ai-probe-benchmark/ai-api skills.
- Existing overlap: cc-skills-ai-api/ai-api; cc-skills-ai-api/ai-probe-benchmark; cc-skills-ai-api/ai-probe-router.
- Confidence: medium.
- Recommended action: merge into another skill.
- Supporting examples:
  - `workspace artifacts`: Root contains many ai_api_live_compare, ai_api_all_models_direct_compare, ai_api_openrouter_models_compare, and related JSON benchmark outputs.
  - `skill inventory`: Existing skills include ai-api, ai-cli, ai-models, ai-probe-benchmark, ai-probe-nim, ai-probe-openrouter, and ai-probe-router.
### 6. planning-command-surface-governance
- Why it exists: Keep slash-command behavior, plan artifacts, and execution gates aligned across /task, /plan, /planning, /code, /think, and related command surfaces.
- Trigger conditions: User asks whether command docs and implementation agree; Planning metadata/routing behavior differs from canonical command; User asks for implementation gates or review packets.
- Evidence from transcripts: 697 strict hits across 131 sessions for command-surface and planning terms; broad review/planning language appears in 252 sessions.
- Failure modes it should prevent: Command docs drifting from implementation; Plan artifacts saved in root or wrong project scope; Routing metadata mistaken for user-facing behavior; Implementation starts before readiness gates.
- Standalone or broader section: section inside planning/code skills.
- Existing overlap: cc-skills-sdlc/planning; cc-skills-sdlc/code; superpowers writing-plans/executing-plans.
- Confidence: medium.
- Recommended action: merge into another skill.
- Supporting examples:
  - `rollout-2025-11-29T06-39-28-019acfd7-0b76-7ae0-99ae-8142a0995e00.jsonl`: User described /task, /plan, and /exec as custom command entrypoints and asked where task databases and triplets should live.
  - `memory-backed prior work`: Prior work involved /planning canonical command guards, suggest/follow-up metadata, and review packet separation.
### 7. handoff-restore-state-audit
- Why it exists: Audit session handoff, restore, snapshot, terminal-scoped state, and cleanup behavior across compaction and new sessions.
- Trigger conditions: User mentions handoff restore; SessionStart/SessionEnd hooks; snapshot or compaction state; terminal-scoped state or stale restore data.
- Evidence from transcripts: 168 strict hits across 82 sessions for handoff/restore/snapshot/SessionStart/SessionEnd terms.
- Failure modes it should prevent: Restoring stale state; Writing runtime state into package source; Confusing terminal IDs or session IDs; Leaving legacy state paths active.
- Standalone or broader section: section inside snapshot/handoff/recover skills.
- Existing overlap: snapshot/snapshot; snapshot/id; cc-skills-utils/recover.
- Confidence: medium.
- Recommended action: hold.
- Supporting examples:
  - `rollout-2026-01-29T14-54-03-019c0bbf-c602-7621-96ab-1bf0d5ed2848.jsonl`: User asked for review of multi-terminal safe enhancements involving TaskCreate persistence across sessions and compaction.
  - `memory-backed prior work`: Prior handoff work covered SessionStart restore formatting, state path organization, terminal-scoped state, and cleanup.
### 8. doc-review-against-companion-guide
- Why it exists: Review draft docs against a stronger companion guide to find omissions, authority conflicts, and missing operational patterns.
- Trigger conditions: User asks to compare a draft guide to another guide; Review needs omission-based gaps rather than prose cleanup; Docs involve MCP, agents, hooks, skills, commands, lifecycle, or error handling.
- Evidence from transcripts: Only one strict transcript hit in this corpus plus memory corroboration; useful but thin as a standalone skill.
- Failure modes it should prevent: Reviewing a draft in isolation; Missing omitted lifecycle/error-handling sections; Confusing configuration authority; No file:line evidence.
- Standalone or broader section: section inside docs/review-packet-runner.
- Existing overlap: cc-skills-sdlc/docs; review-packet-runner candidate.
- Confidence: low.
- Recommended action: hold.
- Supporting examples:
  - `rollout-2026-04-21T22-19-24-019db36a-0bc1-7b63-990d-9259c9b8a6d9.jsonl`: Search-research draft review in P:/packages/search-research asked for gaps/opportunities/questions.
  - `memory-backed prior work`: Memory notes document claude-mcp-v1.0.md review against claude-agents-v1.0.md for lifecycle/error-handling gaps.
## Evidence table
| Candidate | Evidence strength | Existing coverage | Action |
|---|---:|---|---|
| `codex-transcript-recovery` | high; 499 filtered task hits across 11 sessions using strict recovery phrases; broader transcript/session language appears in 171 sessions but includes noise. | search-research/chs searches chat history, snapshot/id reports Claude Code identity | create now |
| `plugin-hook-source-of-truth-audit` | high; 126 strict hits across 81 sessions for source-of-truth, hook manifest, cache, plugin audit, and installed-plugin language; broad hook/plugin terms appear in 195 sessions. | cc-skills-utils/plugin-doctor, cc-skills-utils/plugin-installer, skill-guard/migrate_skill_ef | create now |
| `review-packet-runner` | high; 332 strict hits across 133 sessions for critic, findings, review packet, audit packet, premortem, and gap/opportunity language; broad planning/review language appears in 252 sessions. | cc-skills-sdlc/pre-mortem, cc-skills-thinking/skeptic, quickstop/audit | create now |
| `yt-is-notebooklm-benchmark-ops` | high; 983 strict hits across 77 sessions for yt-is, NotebookLM, canary, transcript routing, Whisper, and related media terms. | cc-skills-media/yt-is, cc-skills-media/yt-nlm, cc-skills-media/nlm | merge into another skill |
| `ai-api-model-benchmarking` | medium; Strict model/API terms appeared heavily, though some hits include YouTube channel names such as NVIDIA; root-level ai_api comparison artifacts corroborate this workflow. | cc-skills-ai-api/ai-api, cc-skills-ai-api/ai-probe-benchmark, cc-skills-ai-api/ai-probe-router | merge into another skill |
| `planning-command-surface-governance` | medium; 697 strict hits across 131 sessions for command-surface and planning terms; broad review/planning language appears in 252 sessions. | cc-skills-sdlc/planning, cc-skills-sdlc/code, superpowers writing-plans/executing-plans | merge into another skill |
| `handoff-restore-state-audit` | medium; 168 strict hits across 82 sessions for handoff/restore/snapshot/SessionStart/SessionEnd terms. | snapshot/snapshot, snapshot/id, cc-skills-utils/recover | hold |
| `doc-review-against-companion-guide` | low; Only one strict transcript hit in this corpus plus memory corroboration; useful but thin as a standalone skill. | cc-skills-sdlc/docs, review-packet-runner candidate | hold |
## Facts grounded in transcript evidence
- 491 rollout JSONL files were found under C:/Users/brsth/.codex/sessions.
- A streaming extraction found 6711 non-scaffold user task records across 473 session files.
- 235 SKILL.md files were found across package marketplace plugins, P:/.claude/skills, C:/Users/brsth/.codex/skills, and C:/Users/brsth/.agents/skills.
- Existing skills already cover many broad domains: plugin-doctor/plugin-installer, chs/search, ai-api/probe, yt-is/yt-nlm/nlm, planning/code, snapshot/id, pre-mortem/skeptic/audit.
## Inferences
- The highest-value new Codex skill is transcript recovery because it has a clear workflow and is not fully covered by Claude-oriented chat-history or snapshot skills.
- Plugin/hook source-of-truth work deserves standalone treatment if Codex is expected to edit P:/packages safely; otherwise it should be a strong section in plugin-doctor/plugin-installer.
- YT-IS and AI API benchmarking are frequent but already have domain skills, so the safer action is to merge stricter operations sections rather than create new standalone skills.
## Open questions / missing data
- Should these skills target Codex only, Claude Code only, or a harness-neutral format with per-harness adapters?
- Should existing package skills be consolidated before adding new ones to reduce duplicate trigger surfaces?
- Which transcript corpus should be treated as authoritative long term: Codex sessions, Claude project transcripts, or both?
## Codex vs Claude Code harness differences
- Codex transcript recovery uses `C:/Users/brsth/.codex/sessions/**/rollout-*.jsonl`; Claude Code transcript examples use project transcript paths under `C:/Users/brsth/.claude/projects/...`. A skill should branch by harness instead of assuming one transcript schema.
- Claude Code plugin behavior depends on `.claude-plugin/plugin.json`, `hooks/hooks.json`, live `.claude` settings, and versioned plugin cache refresh. Codex skills in this environment also live under `C:/Users/brsth/.codex/skills` and plugin cache paths, so source-of-truth checks must name the active harness.
- NotebookLM/NLM guidance appears in AGENTS-style instructions and installed skills; generation/delete commands need CLI confirmation rules, while transcript analysis does not require NotebookLM authentication.
## Recommended next steps
1. Create `codex-transcript-recovery` first. It has the clearest gap, highest severity, and strongest reusable workflow.
2. Create `plugin-hook-source-of-truth-audit` second, or fold it into `plugin-doctor` only if that skill gets explicit source/cache/settings routing gates.
3. Create `review-packet-runner` third, focused on facts/inferences/open questions/action tables, not generic review prose.
4. Do not create standalone YT-IS, AI API benchmark, planning governance, handoff restore, or companion-guide review skills yet; merge those into existing domain skills after review.
## Top 3 skills to create first
1. `codex-transcript-recovery`: prevents repeated wrong-session recovery and has a crisp evidence-first workflow.
2. `plugin-hook-source-of-truth-audit`: prevents high-cost edits to stale paths, cache copies, or the wrong hook authority.
3. `review-packet-runner`: converts a very common review/critique pattern into a structured deliverable with verification gates.
