# Vault Log

## --title
Source: agy headless permissions.allow fix for filesystem reads
Agent: --source
Notes: session-019fbf02
Page: --tags

## --title
Source: Grok Build session transcript format: tool call data in updates.jsonl
Agent: --source
Notes: session-019fbf02
Page: --tags

## LLM Context Windows and Map-Reduce Thresholds
Source: www-research-20260801
Agent: grok
Notes: MiniMax 205K, DiffusionGemma 256K, lost-in-middle at 80K tokens, map-reduce with 10% overlap. Applied to fix wiki-yt truncation bug.
Page: wiki/concepts/llm-context-windows-map-reduce-synthesis-thresholds.md

## Ship Phase-Log Enforcement Design
Source: session-20260801
Agent: grok
Notes: Phase-log enforcement for /ship Phase 1 compliance. Agent writes phase-log as it completes phases; ship_receipt.py validates all 4 present with finding counts. Falsifier: escalate to Stop hook after 3 runs if gamed.
Page: wiki/concepts/ship-phase-log-enforcement-design.md

## serde-broken-false-positive-sweep
Source: session-019fb933
Agent: grok
Notes: All 10 serde_broken entries tested and cleared — multi-path model access, mutual exclusivity fix, escalating cooldowns
Page: P:/.data/wiki/concepts/serde-broken-false-positive-sweep-20260801.md

## --title
Source: Literal-vs-intent pattern refinement in agent-failure-modes
Agent: --source
Notes: session-019fbf02
Page: --tags

## --title
Source: AAR always-Deep mode operator directive
Agent: --source
Notes: session-019fbf02
Page: --tags

## Replacement before investigation pattern
Source: session-019fb177
Agent: grok
Notes: Recurring behavioral pattern: agent recommends replacing tools before trying workarounds. 13+ handoffs.
Page: wiki/concepts/replacement-before-investigation-pattern.md

## [2026-08-01] ingest | close-check Phase 4 Finalize: make blocking unnecessary
Source: session-019fb933 (close-check Phase 4 build)
Agent: grok
Notes: Decision: auto-remediate + auto-finalize preferred over mechanical enforcement layers (close_authority.py + Stop hooks). Selection criterion: minimize operator cognitive load at session close. Phase 4 commits artifacts, cleans temp, refreshes index, surfaces only operator-only items.
Page: wiki/concepts/close-check-finalize-phase-make-blocking-unnecessary.md

## [2026-08-01] ingest | Rhai workflow smoke checks validate parse, not function-call validity
Source: session-019fb933 (close-check Phase 4 build, /tp critique)
Agent: grok
Notes: Two Rhai bugs survived smoke checks in close-check: substr() method doesn't exist, inline #[...] array fails inside parallel(). Both parse cleanly, fail at runtime. Lesson: smoke check pass = structural validity only, not behavioral correctness.
Page: wiki/concepts/rhai-workflow-smoke-check-misses-function-call-bugs.md

## [2026-08-01] ingest | VERIFY gate enforcement gap: documentation vs. runtime invocation
Source: session-2026-08-01
Agent: grok
Notes: Verified gap between documented /grok-verify invocation (/go H6 pack) and observable runtime. Operator confirmed 'we never use grok-verify'; transcript scan shows 38 prose mentions in one transcript, no structured invocations. Closes the implementation gap left open by agentic-sdlc-skill-lifecycle-architecture.md
Page: wiki/concepts/verify-gate-enforcement-gap-document-vs-runtime.md

## TP hat selection gate: content-driven hat choice replaces default-all-on
Source: session-019f902a-621d-7711-9436-7c6003c57793
Agent: grok
Notes: Redesigned /tp hat framework from default-all-on + horizon matrix to content-driven hat selection based on operator intent
Page: P:/.data/wiki/concepts/tp-hat-selection-gate-content-driven-hat-choice.md

## Skill catalog scope inconsistency causes cascading read failures
Source: session-019f902a-621d-7711-9436-7c6003c57793
Agent: grok
Notes: Fixed 9 stale path references across 5 files; catalog listed review/refactor at workspace scope but they live at user scope
Page: P:/.data/wiki/concepts/skill-catalog-scope-inconsistency-causes-cascading-read-failures.md

## --concept
Source: narrative-as-signal
Agent: --action
Notes: created
Page: --source

## Lifecycle skill remediation modes
Source: session-019fb937
Agent: grok
Notes: auto-act vs surface-only classification for close-check Phase 3
Page: .data/wiki/concepts/lifecycle-skill-remediation-modes-auto-act-vs-surface-only.md

## Lint as Forward-Looking Research Source
Source: dream-2026-08-01
Agent: grok
Notes: Lint pass generates forward-looking research suggestions (contradictions, evidence gaps, falsifier triggers, stale hubs). Implements Karpathy lint principle. Auto-promoted from dream.
Page: wiki/concepts/lint-as-forward-looking-research-source.md

## Completeness Over Curation in Recommendations
Source: dream-2026-08-01
Agent: grok
Notes: When asked for recommendations, list ALL items with positive ROI. Operator corrected: hiding recommendations is a trust violation. Auto-promoted from dream.
Page: wiki/concepts/completeness-over-curation-recommendation-discipline.md

## Pipeline Default Validation Against Actual Data Distributions
Source: dream-2026-08-01
Agent: grok
Notes: Pipeline defaults guessed at authoring time are 100-1000x too conservative. wiki-yt 1200-char truncation + qmd staleness. Auto-promoted from dream.
Page: wiki/concepts/pipeline-default-validation-against-actual-data-distributions.md

## --title
Source: Scheduled checks in /maintain
Agent: --slug
Notes: scheduled-checks-in-maintain
Page: --tags

## --title
Source: Tool fallbacks (moved to wiki)
Agent: --slug
Notes: tool-fallbacks
Page: --tags

## --title
Source: Multi-LLM aggregator landscape
Agent: --slug
Notes: multi-llm-aggregator-landscape
Page: --tags

## --title
Source: CAPTCHA solving for non-vision LLM agents
Agent: --slug
Notes: captcha-solving-for-non-vision-llm-agents
Page: --tags

## Analysis over action pattern
Source: session-019fb937
Agent: grok
Notes: Workspace optimizes for knowledge capture over application — fixes die in invocation gap
Page: .data/wiki/concepts/analysis-over-action-knowledge-capture-without-application.md

## Karpathy LLM Wiki Gist
Source: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
Agent: grok
Notes: Karpathy's canonical LLM Wiki idea file. The pattern specification for LLM-maintained wikis. Raw gist fetched directly via raw.githubusercontent.com.
Page: sources/gist.github.com/000-karpathy-llm-wiki-gist.md

## Cole Medin AI Knowledge Base
Source: https://github.com/coleam00/cole-medin-knowledge-base
Agent: grok
Notes: OKF knowledge base built from Cole Medin's 200 YouTube videos. Reference implementation of the channel-to-KB pipeline described in video 8JWhwhxWtJw.
Page: wiki/sources/github.com/000-coleam00-cole-medin-knowledge-base.md

## OKF Spec (GoogleCloudPlatform)
Source: https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf
Agent: grok
Notes: Google's official OKF v0.2 spec repository README. Raw README fetched directly (browser crawl captured navigation chrome).
Page: wiki/sources/github.com/000-GoogleCloudPlatform-knowledge-catalog-okf-spec.md

## LLM Synthesis Context Truncation Blind Spot
Source: session-20260801
Agent: grok
Notes: wiki-yt synthesize_subtopics.py truncated transcripts to 1200 chars (3.8% of avg). Fixed: full text by default + map-reduce fallback at 300K char budget. Root cause: default 250x too conservative vs actual 205K-256K token context windows.
Page: wiki/concepts/llm-synthesis-context-truncation-blind-spot.md

## LLM-Based Concept Canonicalization for Knowledge Bases
Source: session-20260801
Agent: grok
Notes: LLM-based semantic concept canonicalization technique: fuzzy-matching surface label variants (PIV loop = plan implement validate = plan build verify) + appears-more-than-once threshold for concept inclusion. Source: Cole Medin YouTube (8JWhwhxWtJw)
Page: wiki/concepts/llm-concept-canonicalization-technique.md

## behavioral-compliance-gap
Source: session-20260801
Agent: grok
Notes: Agent skipped agy lens despite parallel panel instruction — unverified narrative rationalization
Page: P:/.data/wiki/concepts/behavioral-compliance-gap-agent-skips-instructed-steps-without-verifying.md

## Parallel CDP MCP servers OpenChrome upgrade path
Source: session-20260801
Agent: grok
Notes: Landscape of parallel browser MCP servers; OpenChrome connects to real Chrome with 20 lanes
Page: wiki/concepts/parallel-cdp-mcp-servers-openchrome.md

## Browser automation failure modes for LLM chat interfaces
Source: session-20260801
Agent: grok
Notes: 4 failure types + verify-after-submit principle from DEV article + live testing
Page: wiki/concepts/browser-automation-failure-modes-llm-chat.md

## Agent consolidation in parallel workflows
Source: session-2026-07-31
Agent: grok
Notes: Group by capability need not topic; 9 agents to 3
Page: P:/.data/wiki/concepts/agent-consolidation-in-parallel-workflows.md

## Command-wrapper pattern for workflows
Source: session-2026-07-31
Agent: grok
Notes: Resolve dynamic values at command layer; workflows can't access env/filesystem
Page: P:/.data/wiki/concepts/command-wrapper-pattern-for-workflows.md

## Tool fallbacks as index not authority
Source: session-20260731
Agent: grok
Notes: Groq exclusion gap caused 3 failed spawns; restructured tool-fallbacks as wiki-index
Page: wiki/concepts/tool-fallbacks-as-index-not-authority.md

## Chrome autoConnect for authenticated CDP sessions
Source: session-20260731
Agent: grok
Notes: autoConnect decision + persistence + enterprise policy + side panel limitation
Page: wiki/concepts/chrome-autoconnect-for-authenticated-cdp-sessions.md

## phase2-receipt-format-mismatch
Source: session-20260731
Agent: grok
Notes: Stop hook _is_valid_succeeded_receipt required FILES but writer produces CLAIMED_SCOPE — entire receipt system was non-functional
Page: P:/.data/wiki/concepts/phase2-receipt-format-mismatch-stop-hook-rejects-claimed-scope.md

## Overclaiming under exploration-to-recommendation pressure
Source: session-2026-07-31
Agent: grok
Notes: 5 recommendation reversals; check disconfirming evidence before asserting
Page: P:/.data/wiki/concepts/overclaiming-under-exploration-to-recommendation-pressure.md

## Intent-mode-gated auto-composition
Source: session-2026-07-31
Agent: grok
Notes: Auto-route within same intent mode; operator-gate at research->implementation boundary
Page: P:/.data/wiki/concepts/intent-mode-gated-auto-composition.md

## Router and proxy solutions for cross-harness model tool-calling
Source: session-2026-07-31
Agent: grok
Notes: 5 mechanisms for tool-call emission failures; add_function_to_prompt DISCONFIRMED
Page: P:/.data/wiki/concepts/router-proxy-tool-calling-normalization-patterns.md

## Hook timeout root cause resolved + list-before-claim rule
Source: session-019fb937
Agent: grok
Notes: Dirty tree 1388->399 by untracking regenerable stubs. Created list-before-claim rule for destructive proposals.
Page: .data/wiki/concepts/hook-evidence-collection-cost-vs-timeout-tradeoff.md

## Chrome ACP library stack and best practices 2026
Source: session-2026-07-31
Agent: grok
Notes: Research: chrome-acp library stack, 6 Hono CVEs, WXT/CRXJS preferred, ACP ecosystem 80+ clients, installable skills
Page: wiki/concepts/chrome-acp-library-stack-and-best-practices-2026.md

## retrospective-synthesis
Source: session-019fb177
Agent: grok
Notes: What made the /recap-grok output great: causation chains, meta-narrative, quality assessment
Page: P:/.data/wiki/concepts/retrospective-synthesis-in-session-recaps.md

## invisible-cross-reference
Source: session-019fb177
Agent: grok
Notes: Reading data is necessary but not sufficient — cross-referencing must produce visible output to be verifiable
Page: P:/.data/wiki/concepts/invisible-cross-reference-reading-is-not-sufficient.md

## Model routing community implementations comparison
Source: session-20260731
Agent: grok
Notes: 4 community implementations compared: Hermes model-router (5-tier auto-escalation), Hermes issue #5508 (per-skill model frontmatter), Tokenless YC S26 (proxy gateway), Claude Code .claude/rules (behavioral). Our unique differentiator: quota-awareness + serde-broken detection.
Page: P:/.data/wiki/concepts/model-routing-community-implementations-comparison-2026.md

## cross-invocation
Source: session-019fb177
Agent: grok
Notes: Skills proactively suggest complementary skills — /recap↔/handoff first implementation, pattern captured for future integrations
Page: P:/.data/wiki/concepts/cross-invocation-skills-proactively-suggest-complementary-skills.md

## meta-level-proactivity-skill-graph
Source: session-019fb177
Agent: grok
Notes: Three structural fixes for agent proactivity mapped to the skill graph — meta-checkpoint, cold-read audit, wiki marker scanner
Page: P:/.data/wiki/concepts/meta-level-proactivity-three-fixes-skill-graph-mapping.md

## skill-usability-audit
Source: session-019fb177
Agent: grok
Notes: Cold-read critique technique for catching LLM-followability problems in skills — spawn fresh subagent, pass only skill files, ask structured usability questions
Page: P:/.data/wiki/concepts/skill-usability-audit-cold-read-critique.md

## dual-path-hazard
Source: session-019fb177
Agent: grok
Notes: Delete manual instructions when replacing with mechanical generator — dual-path confusion is the dominant usability hazard
Page: P:/.data/wiki/concepts/dual-path-hazard-delete-manual-when-adding-mechanical.md

## Spec file placement: project root convention (Spec Kit + OpenSpec)
Source: session-20260730
Agent: grok
Notes: Spec belongs at the project root of the effort it describes, not in a workspace-wide docs directory. Confirmed by GitHub Spec Kit + OpenSpec.
Page: wiki/concepts/spec-file-placement-project-root-convention.md

## ship-receipt-mechanical-generation
Source: session-019fb177
Agent: grok
Notes: SHIP receipt mechanically generated from per-check results — code-enforced verdict derivation replaces LLM-assembled receipts
Page: P:/.data/wiki/concepts/ship-receipt-mechanical-generation-from-per-check-results.md

## code-review-speed-comes-from-richer-context-not-more-agents
Source: session-019fb49b
Agent: grok
Notes: Speed comes from diff-in-bundle not more agents. BugBot 8-pass ensemble for coverage, single-agent sequential for framing. Applied to /tp and /review.
Page: P:/.data/wiki/concepts/code-review-speed-comes-from-richer-context-not-more-agents.md

## youtube-throttling-returns-429-not-silent-200
Source: session-019fb49b
Agent: grok
Notes: YouTube throttling returns 429 not 200+empty. yt-is circuit breaker handles it correctly. The 200+empty claim was fabricated.
Page: P:/.data/wiki/concepts/youtube-throttling-returns-429-not-silent-200.md

## Asserting runtime behavior from memory — behavioral pattern (operator correction)
Source: session-20260730
Agent: grok
Notes: Agent asserted Chrome reload behavior as fact without testing. Operator: 'we must kill this behavior.' New concept: asserting-runtime-behavior-from-memory-not-testing.
Page: wiki/concepts/asserting-runtime-behavior-from-memory-not-testing.md

## Chrome ACP Patches Update
Source: session-20260730
Agent: grok
Notes: Added P-wd-lock (working directory lock to P:\), IIFE structure docs, CDP debugging section, re-apply procedure, patch placement rules
Page: wiki/concepts/chrome-acp-grok-build-setup-implementation.md

## Chromium CDP WebSocket Origin Restriction
Source: session-20260730
Agent: grok
Notes: Chrome 111+ rejects WebSocket CDP connections with Origin header; suppress_origin=True fix for Python websocket-client; Comet chrome_proxy.exe launch procedure
Page: wiki/concepts/chromium-cdp-websocket-origin-restriction.md

## Delegation decision rule: context-dependency not just quota
Source: session-20260730
Agent: grok
Notes: Delegate when output is self-contained artifact + summarizable + won't inform future turns. Keep on orchestrator when reasoning process must inform next decision or operator needs to see evolution. Over-isolation destroys orchestrator value.
Page: P:/.data/wiki/concepts/delegation-decision-rule-context-dependency.md

## Corrected model-role-assignment concept: dual basis (task-fit + quota isolation)
Source: session-20260730
Agent: grok
Notes: Added dual basis for model selection: task-fit (validated by operator experience, not just benchmarks) + quota isolation (mechanical). Clarified picker is availability checker not selector. Pool contracts remain source of truth. Skill wiring reverted.
Page: P:/.data/wiki/concepts/model-role-assignment-public-vs-custom-benchmarks.md

## MCP media servers installed (Kinocut + OpenCV MCP)
Source: session-20260730
Agent: grok
Notes: Both verified on Windows 11 via stdio handshake + real ops. mcp<2 pin required (SDK 2.0 broke fastmcp import). New concept: mcp-sdk-2-0-fastmcp-breakage.
Page: wiki/concepts/mcp-servers-for-polishing-code-words-images-video.md

## Karpathy's LLM Wiki Method
Source: nlm-sync-2026-07-30
Agent: grok
Notes: Synced from NotebookLM notebook Perplexity: perplexity-videos-tab
Page: wiki/concepts/karpathys-llm-wiki-method.md

## Open Knowledge Format (OKF)
Source: nlm-sync-2026-07-30
Agent: grok
Notes: Synced from NotebookLM notebook Perplexity: perplexity-videos-tab
Page: wiki/concepts/open-knowledge-format-okf.md

## LLM Wiki Knowledge Pattern
Source: nlm-sync-2026-07-30
Agent: grok
Notes: Synced from NotebookLM notebook Perplexity: perplexity-videos-tab
Page: wiki/concepts/llm-wiki-knowledge-pattern.md

## MCP Servers for Polishing Code Words Images Video
Source: session-20260730
Agent: grok
Notes: Research into kinocut, opencv-mcp, mcpolish for fleet media pipeline
Page: P:/.data/wiki/concepts/mcp-servers-for-polishing-code-words-images-video.md

## agreement-as-narrative-fabricating-knowledge-posture-under-pushback
Source: session-019fb49b
Agent: grok
Notes: New sycophancy disguise: fabricating knowledge posture (not just 'can't be done' narratives). Extends plausible-narratives taxonomy.
Page: P:/.data/wiki/concepts/agreement-as-narrative-fabricating-knowledge-posture-under-pushback.md

## youtube-api-search-list-only-endpoint-for-title-to-video-id
Source: session-019fb49b
Agent: grok
Notes: YouTube Data API constraint: search.list is the only endpoint for title→video_id. Documents non-API alternatives (Takeout, yt-dlp).
Page: P:/.data/wiki/concepts/youtube-api-search-list-only-endpoint-for-title-to-video-id.md

## Updated information on agentic harnesses and repo-maps
Source: session-20260730
Agent: grok
Notes: Codebase-Memory MCP graph (10x fewer tokens) and JetBrains Context (68% fewer turns) as repo-map alternatives to Aider. Agentic harness paper: system prompt is only component that regresses alone (-2.3pp), memory most impactful (+5.6pp). Superseded 2 NLM concepts.
Page: P:/.data/wiki/concepts/agentic-harness-seven-components-2026.md

## --slug
Source: two-component-research-winnowing-pattern
Agent: --action
Notes: created
Page: --agent

## --slug
Source: wiki-validator-retroactive-sweep
Agent: --action
Notes: batch_update
Page: --agent

## --slug
Source: fix-nits-when-already-in-file-deferral-is-theater
Agent: --action
Notes: created
Page: --agent

## Wiki improvement opportunities
Source: session-019fb177
Agent: grok
Notes: practitioner evidence for agent knowledge bases
Page: wiki/concepts/wiki-improvement-opportunities-practitioner-evidence.md

## INTG-2 resolved gate-state set
Source: session-019fb177
Agent: grok
Notes: needs_llm_check is a valid terminal state
Page: wiki/concepts/intg2-resolved-gate-state-set-needs-llm-check.md

## research-quality-principle-efficiency-not-censorship
Source: session-019fb189
Agent: grok
Notes: Standing directive.
Page: wiki/concepts/research-quality-principle-efficiency-not-censorship.md

## delegation-optimization-chunking-output-backend-discipline
Source: session-019fb189
Agent: grok
Notes: Updated with external research: RouteLLM, FrugalGPT, cascade break-even math, coordination cost ceiling, task-tier mapping, practitioner failure modes.
Page: wiki/concepts/delegation-optimization-chunking-output-backend-discipline.md

## delegation-optimization-chunking-output-backend-discipline
Source: session-019fb189
Agent: grok
Notes: Reusable delegation optimization rules.
Page: wiki/concepts/delegation-optimization-chunking-output-backend-discipline.md

## Provider quota API reference updated with opencode-quota
Source: session-2026-07-30
Agent: grok
Notes: opencode-quota checks all providers programmatically; earlier 'no API' claim was wrong
Page: wiki/concepts/provider-quota-usage-api-reference.md

## Chrome ACP + Grok Build setup — patches 8-10 (cwd trim, browser rules injection, expanded rules)
Source: session-2026-07-30
Agent: grok
Notes: cwd trim fix, _meta.rules injection pattern, browser-use-inspired default rules, Comet policy patch verified
Page: wiki/concepts/chrome-acp-grok-build-setup-implementation.md

## prompt-preflight-session-context-completeness-check
Source: session-019fb189
Agent: grok
Notes: Prompt preflight: session-context completeness check before dispatching subagent prompts.
Page: wiki/concepts/prompt-preflight-session-context-completeness-check.md

## convergence-gap-rca-symptom-restatement-toulmin-enforcement
Source: session-019fb189
Agent: grok
Notes: Updated: added Hermes systematic-debugging benchmark findings (tight feedback loop, Rule of Three, hypothesis diversification, admit ignorance).
Page: wiki/concepts/convergence-gap-rca-symptom-restatement-toulmin-enforcement.md

## Chrome ACP + Grok Build setup implementation
Source: session-2026-07-29/30
Agent: grok
Notes: Full implementation record: proxy patches (5), extension patch (1), Comet policy patch (1), startup procedure, known limitations
Page: wiki/concepts/chrome-acp-grok-build-setup-implementation.md

## self-reflection-in-llms-fails-without-external-evidence
Source: session-019fb189
Agent: grok
Notes: Self-reflection in LLMs fails without external evidence. Huang, Reflexion ablation, Riddell RCA study. Reflection vs verification distinction.
Page: wiki/concepts/self-reflection-in-llms-fails-without-external-evidence.md

## Provider quota API reference
Source: session-2026-07-30
Agent: grok
Notes: Which API calls work for checking quota per provider
Page: wiki/concepts/provider-quota-usage-api-reference.md

## research-applicability-checking-dont-cite-without-verifying-assumptions
Source: session-019fb189
Agent: grok
Notes: Research applicability checking — don't cite findings without verifying assumptions apply. Martingale worked example.
Page: wiki/concepts/research-applicability-checking-dont-cite-without-verifying-assumptions.md

## convergence-gap-rca-symptom-restatement-toulmin-enforcement
Source: session-019fb189
Agent: grok
Notes: Convergence gap in RCA: symptom-restatement, Toulmin enforcement, Occam/Hickam heuristic.
Page: wiki/concepts/convergence-gap-rca-symptom-restatement-toulmin-enforcement.md

## --agent
Source: grok
Agent: --session
Notes: 019fa5a1
Page: --page

## --concept
Source: test-selection-for-session-verification
Agent: --title
Notes: Test selection for session verification: full suite, not testmon
Page: --tags

## --agent
Source: grok
Agent: --session
Notes: 019fa5a1
Page: --page

## Chrome ACP + Grok Build browser-driven agentic CLIs
Source: session-2026-07-29 /www research
Agent: grok
Notes: ACP maturity, browser-agent security, safe implementation, 6 attack vectors, 2 host invariant violations mitigated
Page: wiki/concepts/chrome-acp-grok-build-browser-driven-agentic-clis.md

## Scheduled tasks wiki concept
Source: session-2026-07-29
Agent: grok
Notes: Wiki-based date-triggered task table for content freshness maintenance
Page: wiki/concepts/scheduled-tasks-wiki-content-maintenance.md

## --concept
Source: test-coverage-gap-detection-structural-fix
Agent: --title
Notes: Test coverage gap detection: structural fix
Page: --tags

## Reusable internals catalog
Source: session-019fa276
Agent: grok
Notes: Catalog of shared utilities across skills. 10 functions in 6 categories. Before reinventing, check the catalog.
Page: .data/wiki/concepts/reusable-internals-catalog.md

## FMEA skill design — AST-based failure analysis
Source: session-019fa276
Agent: grok
Notes: Decision: AST static analysis over LLM reasoning for component-level FMEA. First run caught the exact cluster_transcripts.py contamination boundary.
Page: .data/wiki/concepts/fmea-skill-design-ast-based-failure-analysis.md

## Workspace improvement cycle 6-stage decomposition
Source: session-019fa276
Agent: grok
Notes: Framework: SENSE-REMEMBER-DECIDE-ACT-VERIFY-MEASURE. Layers 1-5 partially built. Layer 6 (MEASURE) doesn't exist. Cross-session scanner implemented to connect SENSE to REMEMBER.
Page: .data/wiki/concepts/workspace-improvement-cycle-6-stage-decomposition.md

## Silently dead hooks PGM fleet monitoring gap
Source: session-019fa48a
Agent: grok
Notes: PGM silently dead since ship; 3 hooks same payload bug
Page: P:/.data/wiki/concepts/silently-dead-hooks-pgm-payload-bug-fleet-monitoring-gap.md

## Multi-subagent workflow failure patterns
Source: session-019fa48a
Agent: grok
Notes: 5 failure modes from /design run d8173a98
Page: P:/.data/wiki/concepts/multi-subagent-orchestration-workflow-failure-patterns.md

## Cross-session transcript mining survey
Source: session-019fa276
Agent: grok
Notes: /www research: surveyed agent-retro, recursive-improve, cass-memory, alpha-loop. Identified 3-layer architecture convergence and our missing pipeline (transcripts→obligations). Wiki concept written.
Page: .data/wiki/concepts/cross-session-transcript-mining-continuous-improvement.md

## decision-transition-auditing-verdict-integrity-controls
Source: session-2026-07-29 (external LLM review of /behave + /www research)
Agent: grok
Notes: Verdict-integrity controls: unsupported claims cannot change design verdicts; 8 control gaps; self-protection pattern detection; McCormick 8-pattern taxonomy; HTC trajectory calibration
Page: P:/.data/wiki/concepts/decision-transition-auditing-verdict-integrity-controls.md

## Research-to-execution-ratio structural fix implemented
Source: session-019fa276
Agent: grok
Notes: Updated concept with implementation receipt: workspace_opportunity_scan.py scan_open_handoffs + /tp explore opportunity scan gate
Page: .data/wiki/concepts/research-to-execution-ratio-self-reinforcing-pattern.md

## --concept
Source: session-start-hooks-cannot-inject-visible-context-grok-build
Agent: --action
Notes: created
Page: --source

## OpenAI subscription models investigation
Source: session-2026-07-29
Agent: grok
Notes: Codex OAuth token scoped to connectors API only; standard API endpoints reject it; GPT-5.6 model details documented
Page: wiki/concepts/openai-subscription-models-in-grok-build.md

## --concept
Source: confidence-scoring-for-static-analysis-fp-suppression
Agent: --title
Notes: Confidence scoring for static analysis FP suppression
Page: --tags

## Model pool contracts created
Source: session-2026-07-29
Agent: grok
Notes: 4 pool contracts: coding, reasoning, mechanical, critic. Coding pool updated with Ling 3.0 Flash. Fleet pools updated with verified models.
Page: wiki/capabilities/

## --concept
Source: wire-before-build
Agent: --action
Notes: created
Page: --source

## --concept
Source: exploration-vs-execution-intent-signals
Agent: --action
Notes: created
Page: --source

## Model role assignment public vs custom benchmarks
Source: session-2026-07-29
Agent: grok
Notes: Decision to use public benchmarks for capability assessment; composite ranking confirms GLM-5.2 as thought partner
Page: wiki/concepts/model-role-assignment-public-vs-custom-benchmarks.md

## --concept
Source: shell-to-python-orchestration-threshold
Agent: --title
Notes: Shell-to-Python orchestration threshold
Page: --tags

## --concept
Source: fix-introduces-regression-by-trading-properties
Agent: --action
Notes: created
Page: --source

## --concept
Source: sdlc-proactive-prevention-techniques-2026
Agent: --title
Notes: SDLC proactive prevention techniques beyond our current pipeline
Page: --tags

## code-verification-pipeline-gaps
Source: session-019fa94d-/www
Agent: grok
Notes: Maps verification tools to bug classes; recommends pylint --errors-only in /check over new /trace skill
Page: concepts/code-verification-pipeline-gaps.md

## cross-workspace-pyright-blind-spot
Source: session-019fa94d-/wiki
Agent: grok
Notes: Files outside P: escape /check pyright scope; _mark_row missing def not caught
Page: concepts/cross-workspace-pyright-blind-spot.md

## persistence-location-decision-rule
Source: session-2026-07-29 (operator caught 2 persistence errors)
Agent: grok
Notes: If output costs API calls/time to reproduce, persist durably — never P:/tmp
Page: P:/.data/wiki/concepts/persistence-location-decision-rule.md

## -e
Source: compat-layer-cargo-cult
Agent: -t
Notes: wiki
Page: -d

## -e
Source: refactor-verification-gap
Agent: -t
Notes: wiki
Page: -d

## textual-settings-persistence-lifecycle
Source: session-019fa94d-/wiki
Agent: grok
Notes: X-button settings trap: save on Input.Changed not on_unmount; strip quotes from pasted paths
Page: concepts/textual-settings-persistence-lifecycle.md

## -e
Source: close-scanner-false-positive
Agent: -t
Notes: wiki
Page: -d

## Capability node architecture
Source: session-2026-07-28
Agent: grok
Notes: Two-layer contract + design notes decision
Page: P:/.data/wiki/concepts/capability-node-architecture.md

## textual-tui-pitfall-checklist
Source: session-019fa94d-/www
Agent: grok
Notes: Checklist of 25+ predictable Textual+Python bugs mapped to KSC findings; pre-flight checklist for any TUI app
Page: concepts/textual-tui-pitfall-checklist.md

## -e
Source: behaviors-and-compaction-research
Agent: -t
Notes: wiki
Page: -d

## io-safety-review-lens
Source: session-019fa94d-tp
Agent: grok
Notes: New review lens: catches delete-before-copy and non-atomic write patterns that 4 standard reviews missed
Page: concepts/io-safety-review-lens.md

## --concept
Source: fleet-wide-friction-taxonomy-20260728
Agent: --action
Notes: created
Page: --source

## fleet-maintenance-skill-design
Source: session-019fa94d-/www
Agent: grok
Notes: Design for /maintain skill: diagnose (workspace-health) + act (cleanup/rotation) + prevent (growth limits). Not a port of Claude main.
Page: concepts/fleet-maintenance-skill-design.md

## --concept
Source: deferred-skill-improvements-registry
Agent: --action
Notes: created
Page: --source

## dead-code: /check Step 0.9 vulture wired advisory
Source: session-019fa94d-/go
Agent: grok
Notes: vulture_precheck.py + SKILL Step 0.9; Textual FP filter; soft-skip if missing
Page: concepts/dead-code-detection-workflow.md

## dead-code-detection-workflow: /check Step 0.9 gap + Textual FP
Source: session-019fa94d-handoff
Agent: grok
Notes: Documented that /check did not run vulture; recommended integration table now includes /check Step 0.9 as not-yet-wired; Textual false-positive note
Page: concepts/dead-code-detection-workflow.md

## model-fit-and-post-hoc-behavioral-detection
Source: session-019fa48a
Agent: grok
Notes: Model fit (Claude best anti-sycophancy) + post-hoc detection (Stop hook pattern matching + intent drift)
Page: wiki/concepts/model-fit-and-post-hoc-behavioral-detection.md

## --concept
Source: spec-driven-development-tools-and-planning-workflows
Agent: --action
Notes: updated
Page: --source

## --concept
Source: held-out-data-already-on-disk-count-artifacts-not-invocations
Agent: --action
Notes: created
Page: --source

## PostToolUse fires on tool-call completion not process completion
Source: session-20260728
Agent: grok
Notes: Auto-backgrounded commands skip receipt capture because PostToolUse fires before process finishes. Fix: pass timeout=180000 to keep foreground.
Page: wiki/concepts/posttooluse-fires-on-tool-call-completion-not-process-completion.md

## --agent
Source: grok
Agent: --session
Notes: 019fa5a1
Page: --page

## Built-in grep tool over shell ripgrep for wiki search
Source: session-20260728
Agent: grok
Notes: Research confirms ripgrep optimal for 380-file wiki. Built-in grep tool used instead of shell rg. qmd removed.
Page: wiki/concepts/built-in-grep-tool-over-shell-ripgrep-for-wiki-search.md

## [2026-07-28] ingest | Test concept — auto-link and post-write pipeline verification
Source: session-2026-07-28
Agent: grok
Notes: integration test: verify auto-linking works after qmd cutover
Page: wiki/concepts/test-auto-link-verification-20260728.md

## --agent
Source: grok
Agent: --session
Notes: 019fa5a1
Page: --page

## Cardiovascular Health Targets and Age-Related Considerations
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook WL: Health (ADHD/Sleep/Cancer)
Page: wiki/concepts/cardiovascular-health-targets-and-age-related-considerations.md

## Beef Price Drivers and Supply Constraints
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook WL: Health (ADHD/Sleep/Cancer)
Page: wiki/concepts/beef-price-drivers-and-supply-constraints.md

## MOTS-C Mitochondrial Peptide
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook WL: Health (ADHD/Sleep/Cancer)
Page: wiki/concepts/mots-c-mitochondrial-peptide.md

## Metabolic Targeting of Cancer Cell Fuel Sources
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook WL: Health (ADHD/Sleep/Cancer)
Page: wiki/concepts/metabolic-targeting-of-cancer-cell-fuel-sources.md

## Dog Reactivity Training Techniques
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook WL: Health (ADHD/Sleep/Cancer)
Page: wiki/concepts/dog-reactivity-training-techniques.md

## Sleep Apnea Non-CPAP Interventions
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook WL: Health (ADHD/Sleep/Cancer)
Page: wiki/concepts/sleep-apnea-non-cpap-interventions.md

## Carnivore Diet Outcomes and Comparative Diet Debates
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook WL: Health (ADHD/Sleep/Cancer)
Page: wiki/concepts/carnivore-diet-outcomes-and-comparative-diet-debates.md

## Metabolic Status as Determinant of Cancer and Dementia Risk
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook WL: Health (ADHD/Sleep/Cancer)
Page: wiki/concepts/metabolic-status-as-determinant-of-cancer-and-dementia-risk.md

## Internal ADHD Experiences and Hidden Manifestations
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook WL: Health (ADHD/Sleep/Cancer)
Page: wiki/concepts/internal-adhd-experiences-and-hidden-manifestations.md

## Custom Skills Overview
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook [INGESTED] - Mastering Claude Skills
Page: wiki/concepts/custom-skills-overview.md

## AI System Evaluation and Security Frameworks
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook [INGESTED] - Mastering Claude Skills
Page: wiki/concepts/ai-system-evaluation-and-security-frameworks.md

## LangGraph Tool Args Validation Middleware
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook [INGESTED] - Mastering Claude Skills
Page: wiki/concepts/langgraph-tool-args-validation-middleware.md

## NVIDIA NeMo Guardrails
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook [INGESTED] - Mastering Claude Skills
Page: wiki/concepts/nvidia-nemo-guardrails.md

## Claude Code Guardrails
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook [INGESTED] - Mastering Claude Skills
Page: wiki/concepts/claude-code-guardrails.md

## Tool Binding and Choice Control
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook [INGESTED] - Mastering Claude Skills
Page: wiki/concepts/tool-binding-and-choice-control.md

## Claude Code Skills Development
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook [INGESTED] - Mastering Claude Skills
Page: wiki/concepts/claude-code-skills-development.md

## LLM Agent Reliability and Testing Patterns
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook [INGESTED] - Mastering Claude Skills
Page: wiki/concepts/llm-agent-reliability-and-testing-patterns.md

## Claude Code Execution Control Patterns
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook [INGESTED] - Mastering Claude Skills
Page: wiki/concepts/claude-code-execution-control-patterns.md

## Claude Code Hooks System
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook [INGESTED] - Mastering Claude Skills
Page: wiki/concepts/claude-code-hooks-system.md

## GDPR Compliance Requirements for AI Systems
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook [INGESTED] - Claude Code - Observability & Logging
Page: wiki/concepts/gdpr-compliance-requirements-for-ai-systems.md

## OpenTelemetry Structured Logging Patterns
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook [INGESTED] - Claude Code - Observability & Logging
Page: wiki/concepts/opentelemetry-structured-logging-patterns.md

## Vibe Coding Tools and Workflows
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook [INGESTED] - ext-Gemini CLI, Jules CLI, and Claude Code
Page: wiki/concepts/vibe-coding-tools-and-workflows.md

## Agent Skills Architecture
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook [INGESTED] - ext-Gemini CLI, Jules CLI, and Claude Code
Page: wiki/concepts/agent-skills-architecture.md

## Agent Skills Documentation Pattern
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook [INGESTED] - ext-Gemini CLI, Jules CLI, and Claude Code
Page: wiki/concepts/agent-skills-documentation-pattern.md

## Vibe-Coding Prompt Template
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook [INGESTED] - ext-Gemini CLI, Jules CLI, and Claude Code
Page: wiki/concepts/vibe-coding-prompt-template.md

## Claude MCP Server Management
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook [INGESTED] - ext-Gemini CLI, Jules CLI, and Claude Code
Page: wiki/concepts/claude-mcp-server-management.md

## CLI-Based AI Coding Agents
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook [INGESTED] - ext-Gemini CLI, Jules CLI, and Claude Code
Page: wiki/concepts/cli-based-ai-coding-agents.md

## Claude Code Extensibility and Configuration
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook [INGESTED] - ext-Gemini CLI, Jules CLI, and Claude Code
Page: wiki/concepts/claude-code-extensibility-and-configuration.md

## Claude Code CLI Tool
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook [INGESTED] - ext-Gemini CLI, Jules CLI, and Claude Code
Page: wiki/concepts/claude-code-cli-tool.md

## Free AI Coding Model Alternatives to Opus
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook [INGESTED] - WL: AI Coding & Tooling
Page: wiki/concepts/free-ai-coding-model-alternatives-to-opus.md

## Parallel Agent Session Management
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook [INGESTED] - WL: AI Coding & Tooling
Page: wiki/concepts/parallel-agent-session-management.md

## AI Tool Integration and Workflow Orchestration
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook [INGESTED] - WL: AI Coding & Tooling
Page: wiki/concepts/ai-tool-integration-and-workflow-orchestration.md

## Local Audio AI Models
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook [INGESTED] - WL: AI Coding & Tooling
Page: wiki/concepts/local-audio-ai-models.md

## Kimi K2.7 Code Mixture-of-Experts Architecture
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook [INGESTED] - WL: AI Coding & Tooling
Page: wiki/concepts/kimi-k27-code-mixture-of-experts-architecture.md

## AI Image Generation Models And Workflows
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook [INGESTED] - WL: AI Coding & Tooling
Page: wiki/concepts/ai-image-generation-models-and-workflows.md

## Automated Model Routing for LLM Coding Tasks
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook [INGESTED] - WL: AI Coding & Tooling
Page: wiki/concepts/automated-model-routing-for-llm-coding-tasks.md

## Open-Source Developer Inventory and Security Tools
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook [INGESTED] - WL: AI Coding & Tooling
Page: wiki/concepts/open-source-developer-inventory-and-security-tools.md

## Free Open Source Self Hosted Tools
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook [INGESTED] - WL: AI Coding & Tooling
Page: wiki/concepts/free-open-source-self-hosted-tools.md

## Free AI Video Generation Tools
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook [INGESTED] - WL: AI Coding & Tooling
Page: wiki/concepts/free-ai-video-generation-tools.md

## CLI Vibe Coding Workflow Techniques
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook ext-Gemini CLI, Jules CLI, and Claude Code
Page: wiki/concepts/cli-vibe-coding-workflow-techniques.md

## Claude Agent Skills
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook ext-Gemini CLI, Jules CLI, and Claude Code
Page: wiki/concepts/claude-agent-skills.md

## Skill Documentation Structure
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook ext-Gemini CLI, Jules CLI, and Claude Code
Page: wiki/concepts/skill-documentation-structure.md

## Vibe-Coding Prompt Templates
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook ext-Gemini CLI, Jules CLI, and Claude Code
Page: wiki/concepts/vibe-coding-prompt-templates.md

## Cookie Handling in AI Agent Web Interactions
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook ext-Gemini CLI, Jules CLI, and Claude Code
Page: wiki/concepts/cookie-handling-in-ai-agent-web-interactions.md

## Open Source CLI AI Coding Agents
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook ext-Gemini CLI, Jules CLI, and Claude Code
Page: wiki/concepts/open-source-cli-ai-coding-agents.md

## Claude Code Configuration and Settings
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook ext-Gemini CLI, Jules CLI, and Claude Code
Page: wiki/concepts/claude-code-configuration-and-settings.md

## AI CLI Tools and Coding Agents
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook ext-Gemini CLI, Jules CLI, and Claude Code
Page: wiki/concepts/ai-cli-tools-and-coding-agents.md

## GDPR Compliance Requirements for AI Agents
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Claude Code - Observability & Logging
Page: wiki/concepts/gdpr-compliance-requirements-for-ai-agents.md

## OpenTelemetry Logging Patterns
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Claude Code - Observability & Logging
Page: wiki/concepts/opentelemetry-logging-patterns.md

## Claude Code Hooks
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Claude Code Skills and Features Reference Guide
Page: wiki/concepts/claude-code-hooks.md

## Antigravity Codes Platform
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Claude Code and QMD: Persistent Knowledge Architecture
Page: wiki/concepts/antigravity-codes-platform.md

## Karpathy-Style Knowledge Base Workflow
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Claude Code and QMD: Persistent Knowledge Architecture
Page: wiki/concepts/karpathy-style-knowledge-base-workflow.md

## CLAUDE.md Configuration Files
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Claude Code and QMD: Persistent Knowledge Architecture
Page: wiki/concepts/claudemd-configuration-files.md

## Claude Code Obsidian Integration Patterns
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Claude Code and QMD: Persistent Knowledge Architecture
Page: wiki/concepts/claude-code-obsidian-integration-patterns.md

## Claude Code External Integration Patterns
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Claude Code and QMD: Persistent Knowledge Architecture
Page: wiki/concepts/claude-code-external-integration-patterns.md

## LLM Wiki Knowledge Pattern
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Claude Code and QMD: Persistent Knowledge Architecture
Page: wiki/concepts/llm-wiki-knowledge-pattern.md

## Claude Code Integration with Obsidian Knowledge Bases
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Claude Code and QMD: Persistent Knowledge Architecture
Page: wiki/concepts/claude-code-integration-with-obsidian-knowledge-bases.md

## Self-Feedback Iterative Refinement
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Iterative AI Refinement and Multi-Agent Debate Frameworks
Page: wiki/concepts/self-feedback-iterative-refinement.md

## Verification Techniques for LLM Reliability
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Iterative AI Refinement and Multi-Agent Debate Frameworks
Page: wiki/concepts/verification-techniques-for-llm-reliability.md

## Iterative Refinement in LLM Code Generation
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Iterative AI Refinement and Multi-Agent Debate Frameworks
Page: wiki/concepts/iterative-refinement-in-llm-code-generation.md

## Multi-Agent Code Review Systems
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Iterative AI Refinement and Multi-Agent Debate Frameworks
Page: wiki/concepts/multi-agent-code-review-systems.md

## AI Agent Schema Standards
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook high-quality GitHub profile landing pages
Page: wiki/concepts/ai-agent-schema-standards.md

## Digital Video Production Fundamentals
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook high-quality GitHub profile landing pages
Page: wiki/concepts/digital-video-production-fundamentals.md

## Self-Regulated Study Loop Systems
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook _2026-01-15
Page: wiki/concepts/self-regulated-study-loop-systems.md

## Multi-Agent Orchestration Patterns
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook _2026-01-15
Page: wiki/concepts/multi-agent-orchestration-patterns.md

## Claude Code Multi-Agent Design Patterns
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Adversarial Analysis Skills: Pre-Mortem and Critique Frameworks
Page: wiki/concepts/claude-code-multi-agent-design-patterns.md

## Multi-Agent System Failure Modes
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Adversarial Analysis Skills: Pre-Mortem and Critique Frameworks
Page: wiki/concepts/multi-agent-system-failure-modes.md

## Multi-Agent Architectures for Autonomous Systems
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Adversarial Analysis Skills: Pre-Mortem and Critique Frameworks
Page: wiki/concepts/multi-agent-architectures-for-autonomous-systems.md

## Adversarial Multi-Agent Code Review
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Adversarial Analysis Skills: Pre-Mortem and Critique Frameworks
Page: wiki/concepts/adversarial-multi-agent-code-review.md

## Multi-Agent Code Orchestration
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Adversarial Analysis Skills: Pre-Mortem and Critique Frameworks
Page: wiki/concepts/multi-agent-code-orchestration.md

## --agent
Source: grok
Agent: --session
Notes: 019fa5a1
Page: --page

## Claude Code Write Restriction Pattern
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Claude Code - Workflow and Logic Inefficiencies
Page: wiki/concepts/claude-code-write-restriction-pattern.md

## Agent Memory Systems
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Claude Code - Workflow and Logic Inefficiencies
Page: wiki/concepts/agent-memory-systems.md

## Failure Taxonomy in Tool-Augmented LLMs
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Claude Code - Workflow and Logic Inefficiencies
Page: wiki/concepts/failure-taxonomy-in-tool-augmented-llms.md

## HTTPS Observability for AI Agents
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Claude Code - Workflow and Logic Inefficiencies
Page: wiki/concepts/https-observability-for-ai-agents.md

## AI Agent Resource Management and Validation
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Claude Code - Workflow and Logic Inefficiencies
Page: wiki/concepts/ai-agent-resource-management-and-validation.md

## Agentic AI Production Considerations
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Claude Code - Workflow and Logic Inefficiencies
Page: wiki/concepts/agentic-ai-production-considerations.md

## Structured Output from LLMs
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Claude Code - Workflow and Logic Inefficiencies
Page: wiki/concepts/structured-output-from-llms.md

## Memory-Augmented Agent Architectures
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Claude Code - Workflow and Logic Inefficiencies
Page: wiki/concepts/memory-augmented-agent-architectures.md

## AI Agent Evaluation and Performance Measurement
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Claude Code - Workflow and Logic Inefficiencies
Page: wiki/concepts/ai-agent-evaluation-and-performance-measurement.md



## [2026-07-28] ingest | FTS5 query-syntax escaping required for MATCH with user input
Source: session-2026-07-28
Agent: grok
Notes: test post-write driver
Page: wiki/concepts/fts5-query-syntax-escaping-required.md

## Claude Code Development Capabilities
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Claude Code - Context Memory and Search
Page: wiki/concepts/claude-code-development-capabilities.md

## Semantic Code Retrieval for Context Management
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Claude Code - Context Memory and Search
Page: wiki/concepts/semantic-code-retrieval-for-context-management.md

## Agentic RAG Architecture
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Claude Code - Context Memory and Search
Page: wiki/concepts/agentic-rag-architecture.md

## Context Management in Claude Code
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Claude Code - Context Memory and Search
Page: wiki/concepts/context-management-in-claude-code.md

## OpenCode Go model auth: Anthropic Messages format
Source: session-20260728
Agent: grok
Notes: Qwen/MiniMax models need x-api-key header not api_key field. Config fix resolved 401. 3 models verified.
Page: wiki/concepts/opencode-go-model-auth-anthropic-vs-openai-format.md

## Phylo Agent Architecture
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Deep Research Prompts, Methods, Examples
Page: wiki/concepts/phylo-agent-architecture.md

## LLM Coding Agent Architecture Patterns
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Deep Research Prompts, Methods, Examples
Page: wiki/concepts/llm-coding-agent-architecture-patterns.md

## OpenClaw Agent Architecture
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Deep Research Prompts, Methods, Examples
Page: wiki/concepts/openclaw-agent-architecture.md

## Sequential Falsification for Hypothesis Validation
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Deep Research Prompts, Methods, Examples
Page: wiki/concepts/sequential-falsification-for-hypothesis-validation.md

## Loop Engineering for Autonomous Agents
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Deep Research Prompts, Methods, Examples
Page: wiki/concepts/loop-engineering-for-autonomous-agents.md

## Self-Correction Reflection Loop
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Deep Research Prompts, Methods, Examples
Page: wiki/concepts/self-correction-reflection-loop.md

## GDPR Compliance Requirements for AI Systems
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Claude Code - Observability & Logging
Page: wiki/concepts/gdpr-compliance-requirements-for-ai-systems.md

## OpenTelemetry Logging
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Claude Code - Observability & Logging
Page: wiki/concepts/opentelemetry-logging.md

## Primal Nutrition for Weight Loss
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Testing Buzz by Block: The Limits of Agent Orchestration
Page: wiki/concepts/primal-nutrition-for-weight-loss.md

## Laguna S 2.1 Local Model Capabilities
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Testing Buzz by Block: The Limits of Agent Orchestration
Page: wiki/concepts/laguna-s-21-local-model-capabilities.md

## Claude Code Extensibility and Ecosystem
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Testing Buzz by Block: The Limits of Agent Orchestration
Page: wiki/concepts/claude-code-extensibility-and-ecosystem.md

## Claude Opus 5 Model Overview
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Testing Buzz by Block: The Limits of Agent Orchestration
Page: wiki/concepts/claude-opus-5-model-overview.md

## Loop Engineering for Claude Code
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Testing Buzz by Block: The Limits of Agent Orchestration
Page: wiki/concepts/loop-engineering-for-claude-code.md

## CLI Vibe Coding Tools and Configuration
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook ext-Gemini CLI, Jules CLI, and Claude Code
Page: wiki/concepts/cli-vibe-coding-tools-and-configuration.md

## Agent Skills
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook ext-Gemini CLI, Jules CLI, and Claude Code
Page: wiki/concepts/agent-skills.md

## Agent Skill Documentation Patterns
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook ext-Gemini CLI, Jules CLI, and Claude Code
Page: wiki/concepts/agent-skill-documentation-patterns.md

## Vibe Prompt Template
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook ext-Gemini CLI, Jules CLI, and Claude Code
Page: wiki/concepts/vibe-prompt-template.md

## Claude Code MCP Server Configuration
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook ext-Gemini CLI, Jules CLI, and Claude Code
Page: wiki/concepts/claude-code-mcp-server-configuration.md

## CLI-Based AI Coding Agents
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook ext-Gemini CLI, Jules CLI, and Claude Code
Page: wiki/concepts/cli-based-ai-coding-agents.md

## Claude Code HTTPS Access and Authentication
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook ext-Gemini CLI, Jules CLI, and Claude Code
Page: wiki/concepts/claude-code-https-access-and-authentication.md

## Claude Code CLI Tool Overview
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook ext-Gemini CLI, Jules CLI, and Claude Code
Page: wiki/concepts/claude-code-cli-tool-overview.md

## AI System Evaluation and Benchmarking Methods
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Engineering the Autonomous Diagnostic: AI Agent Reliability and RCA
Page: wiki/concepts/ai-system-evaluation-and-benchmarking-methods.md

## AI-Generated Code Anti-Patterns
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Engineering the Autonomous Diagnostic: AI Agent Reliability and RCA
Page: wiki/concepts/ai-generated-code-anti-patterns.md

## AI Agent Security and Observability
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Engineering the Autonomous Diagnostic: AI Agent Reliability and RCA
Page: wiki/concepts/ai-agent-security-and-observability.md

## Agent Reliability Patterns and Production Validation
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Engineering the Autonomous Diagnostic: AI Agent Reliability and RCA
Page: wiki/concepts/agent-reliability-patterns-and-production-validation.md

## AI Agent Systems in Software Engineering
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Engineering the Autonomous Diagnostic: AI Agent Reliability and RCA
Page: wiki/concepts/ai-agent-systems-in-software-engineering.md

## Agentic Self-Correction and Context Management
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook AI Architecture and Decision Record Frameworks
Page: wiki/concepts/agentic-self-correction-and-context-management.md

## Architecture Decision Records
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook AI Architecture and Decision Record Frameworks
Page: wiki/concepts/architecture-decision-records.md

## AI Agent Steering and Self-Improvement Patterns
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook AI Architecture and Decision Record Frameworks
Page: wiki/concepts/ai-agent-steering-and-self-improvement-patterns.md

## CLAUDE.md Configuration Practices
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook AI Architecture and Decision Record Frameworks
Page: wiki/concepts/claudemd-configuration-practices.md

## LLM-based Agent Architectures
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook AI Architecture and Decision Record Frameworks
Page: wiki/concepts/llm-based-agent-architectures.md

## Claude Code Project Memory
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook AI Architecture and Decision Record Frameworks
Page: wiki/concepts/claude-code-project-memory.md

## GPU Cloud Rental Specifications
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Maximizing LLM Performance and Context via GPU Memory Optimization
Page: wiki/concepts/gpu-cloud-rental-specifications.md

## Uncensored AI Models
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Maximizing LLM Performance and Context via GPU Memory Optimization
Page: wiki/concepts/uncensored-ai-models.md

## Context Management Trade-offs
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Maximizing LLM Performance and Context via GPU Memory Optimization
Page: wiki/concepts/context-management-trade-offs.md

## Local LLM Inference Optimization
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Maximizing LLM Performance and Context via GPU Memory Optimization
Page: wiki/concepts/local-llm-inference-optimization.md

## Local LLM Inference Engines
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Maximizing LLM Performance and Context via GPU Memory Optimization
Page: wiki/concepts/local-llm-inference-engines.md

## KV Cache Memory Management in LLM Inference
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Maximizing LLM Performance and Context via GPU Memory Optimization
Page: wiki/concepts/kv-cache-memory-management-in-llm-inference.md

## GGUF Quantization for Large Language Models
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Maximizing LLM Performance and Context via GPU Memory Optimization
Page: wiki/concepts/gguf-quantization-for-large-language-models.md

## NVIDIA VRAM Management for Local LLM Inference
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Maximizing LLM Performance and Context via GPU Memory Optimization
Page: wiki/concepts/nvidia-vram-management-for-local-llm-inference.md

## Custom Skills for Claude
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Mastering Claude Skills
Page: wiki/concepts/custom-skills-for-claude.md

## Security and Reliability Evaluation in AI Systems
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Mastering Claude Skills
Page: wiki/concepts/security-and-reliability-evaluation-in-ai-systems.md

## LangGraph Tool Args Validation
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Mastering Claude Skills
Page: wiki/concepts/langgraph-tool-args-validation.md

## NVIDIA NeMo Guardrails Overview
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Mastering Claude Skills
Page: wiki/concepts/nvidia-nemo-guardrails-overview.md

## Cookie Consent Mechanisms in AI Product Webpages
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Mastering Claude Skills
Page: wiki/concepts/cookie-consent-mechanisms-in-ai-product-webpages.md

## Tool Choice Parameter Control
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Mastering Claude Skills
Page: wiki/concepts/tool-choice-parameter-control.md

## Claude Skills
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Mastering Claude Skills
Page: wiki/concepts/claude-skills.md

## LLM Agent Evaluation and Regression Testing
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Mastering Claude Skills
Page: wiki/concepts/llm-agent-evaluation-and-regression-testing.md

## Programmable Behavioral Control in Claude Code
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Mastering Claude Skills
Page: wiki/concepts/programmable-behavioral-control-in-claude-code.md

## Claude Code Hooks
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Mastering Claude Skills
Page: wiki/concepts/claude-code-hooks.md

## React Component Library Ecosystem
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Github Awesome
Page: wiki/concepts/react-component-library-ecosystem.md

## GitHub Trending Video Coverage
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Github Awesome
Page: wiki/concepts/github-trending-video-coverage.md

## Automated Code Quality Enforcement
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Thinking and Reasoning
Page: wiki/concepts/automated-code-quality-enforcement.md

## Claude Code Skills and MCP Integration
Source: nlm-sync-2026-07-28
Agent: grok
Notes: Synced from NotebookLM notebook Thinking and Reasoning
Page: wiki/concepts/claude-code-skills-and-mcp-integration.md

## Brave Browser Privacy Controversies and Container Features
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Model Reviews & Benchmarks
Page: wiki/concepts/brave-browser-privacy-controversies-and-container-features.md

## Windows Customization and Enhancement Approaches
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Model Reviews & Benchmarks
Page: wiki/concepts/windows-customization-and-enhancement-approaches.md

## AI-Enhanced YouTube Video Workflows
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Model Reviews & Benchmarks
Page: wiki/concepts/ai-enhanced-youtube-video-workflows.md

## Smart TV App Installation Techniques
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Model Reviews & Benchmarks
Page: wiki/concepts/smart-tv-app-installation-techniques.md

## Fable 5 Model Capabilities
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Model Reviews & Benchmarks
Page: wiki/concepts/fable-5-model-capabilities.md

## AI-Powered Faceless Shorts Automation
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook Nate Herk | AI Automation
Page: wiki/concepts/ai-powered-faceless-shorts-automation.md

## Days-to-First-Client Acquisition
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook Nate Herk | AI Automation
Page: wiki/concepts/days-to-first-client-acquisition.md

## AI Agent Development and Sales
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook Nate Herk | AI Automation
Page: wiki/concepts/ai-agent-development-and-sales.md

## n8n AI Agent Architecture
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook Nate Herk | AI Automation
Page: wiki/concepts/n8n-ai-agent-architecture.md

## Rate Limiting in Python Web Scraping
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook Video Pipeline
Page: wiki/concepts/rate-limiting-in-python-web-scraping.md

## Video OCR Processing with Python
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook Video Pipeline
Page: wiki/concepts/video-ocr-processing-with-python.md

## YouTube HTTPS Access Errors
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook Video Pipeline
Page: wiki/concepts/youtube-https-access-errors.md

## Circuit Breaker Pattern
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook Video Pipeline
Page: wiki/concepts/circuit-breaker-pattern.md

## Context Caching for Gemini Models
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook Video Pipeline
Page: wiki/concepts/context-caching-for-gemini-models.md

## Python Abstract Base Classes
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook Video Pipeline
Page: wiki/concepts/python-abstract-base-classes.md

## HTTP 429 Errors in Web Scraping
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook Video Pipeline
Page: wiki/concepts/http-429-errors-in-web-scraping.md

## YouTube Transcript Extraction Techniques
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook Video Pipeline
Page: wiki/concepts/youtube-transcript-extraction-techniques.md

## Gemini CLI and API Video Understanding Capabilities
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook Video Pipeline
Page: wiki/concepts/gemini-cli-and-api-video-understanding-capabilities.md

## GitHub-Hosted YouTube Integration Tools
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook Video Pipeline
Page: wiki/concepts/github-hosted-youtube-integration-tools.md

## OpenTelemetry W3C Context Propagation
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook Transcripts and Logs of AI Coding Sessions
Page: wiki/concepts/opentelemetry-w3c-context-propagation.md

## Claude Code Hooks
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook Transcripts and Logs of AI Coding Sessions
Page: wiki/concepts/claude-code-hooks.md

## PreToolUse Approach in Claude Code
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook Transcripts and Logs of AI Coding Sessions
Page: wiki/concepts/pretooluse-approach-in-claude-code.md

## PreToolUse Authorization Gate
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook Transcripts and Logs of AI Coding Sessions
Page: wiki/concepts/pretooluse-authorization-gate.md

## Tick-Borne Disease Risks and Prevention
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Geopolitics (Israel/Islam/Trump)
Page: wiki/concepts/tick-borne-disease-risks-and-prevention.md

## Hidden Mechanisms In Institutional Decision-Making
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Geopolitics (Israel/Islam/Trump)
Page: wiki/concepts/hidden-mechanisms-in-institutional-decision-making.md

## YouTube Content Diversity and Platform Dynamics
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Geopolitics (Israel/Islam/Trump)
Page: wiki/concepts/youtube-content-diversity-and-platform-dynamics.md

## Multi-Source Perspective on Global Geopolitical Shifts
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Geopolitics (Israel/Islam/Trump)
Page: wiki/concepts/multi-source-perspective-on-global-geopolitical-shifts.md

## Post-Dennard Scaling Computing Approaches
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Multi-Agent Orchestration
Page: wiki/concepts/post-dennard-scaling-computing-approaches.md

## Agentic Software Engineering
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Multi-Agent Orchestration
Page: wiki/concepts/agentic-software-engineering.md

## PrismML Bonsai 27B Model
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Multi-Agent Orchestration
Page: wiki/concepts/prismml-bonsai-27b-model.md

## Hermes Agent Free Capabilities
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Multi-Agent Orchestration
Page: wiki/concepts/hermes-agent-free-capabilities.md

## Hermes Agent Configuration System
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Multi-Agent Orchestration
Page: wiki/concepts/hermes-agent-configuration-system.md

## Thought Collapse in LLMs
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook Claude Code - Skills: Agentic Coding and Prompt Engineering
Page: wiki/concepts/thought-collapse-in-llms.md

## Structured Output Validation
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook Claude Code - Skills: Agentic Coding and Prompt Engineering
Page: wiki/concepts/structured-output-validation.md

## MCP Server Design Patterns
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook Claude Code - Skills: Agentic Coding and Prompt Engineering
Page: wiki/concepts/mcp-server-design-patterns.md

## TOON Format for LLM Token Optimization
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook Claude Code - Skills: Agentic Coding and Prompt Engineering
Page: wiki/concepts/toon-format-for-llm-token-optimization.md

## Reddit Prompt Engineering Community Discourse
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook Claude Code - Skills: Agentic Coding and Prompt Engineering
Page: wiki/concepts/reddit-prompt-engineering-community-discourse.md

## Claude Code Extension Patterns
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook Claude Code - Skills: Agentic Coding and Prompt Engineering
Page: wiki/concepts/claude-code-extension-patterns.md

## Deterministic Output Control in Agentic CLI Environments
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook Claude Code - Skills: Agentic Coding and Prompt Engineering
Page: wiki/concepts/deterministic-output-control-in-agentic-cli-environments.md

## Latent Reasoning in Language Models
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook Claude Code - Skills: Agentic Coding and Prompt Engineering
Page: wiki/concepts/latent-reasoning-in-language-models.md

## GitHub Repository File Structures
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook Claude Code - Skills: Agentic Coding and Prompt Engineering
Page: wiki/concepts/github-repository-file-structures.md

## Claude Code CLI Agent Configuration and Workflow Patterns
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook Claude Code - Skills: Agentic Coding and Prompt Engineering
Page: wiki/concepts/claude-code-cli-agent-configuration-and-workflow-patterns.md

## Thought Collapse in LLMs
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook Claude Code - Skills: Agentic Coding and Prompt Engineering
Page: wiki/concepts/thought-collapse-in-llms.md

## Claude API Documentation Resources
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook Claude Code - Skills: Agentic Coding and Prompt Engineering
Page: wiki/concepts/claude-api-documentation-resources.md

## Model Context Protocol Architecture
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook Claude Code - Skills: Agentic Coding and Prompt Engineering
Page: wiki/concepts/model-context-protocol-architecture.md

## TOON Data Format for LLM Token Optimization
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook Claude Code - Skills: Agentic Coding and Prompt Engineering
Page: wiki/concepts/toon-data-format-for-llm-token-optimization.md

## Advanced Prompt Engineering Effectiveness
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook Claude Code - Skills: Agentic Coding and Prompt Engineering
Page: wiki/concepts/advanced-prompt-engineering-effectiveness.md

## Claude Code Customization Patterns
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook Claude Code - Skills: Agentic Coding and Prompt Engineering
Page: wiki/concepts/claude-code-customization-patterns.md

## Deterministic Output Engineering
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook Claude Code - Skills: Agentic Coding and Prompt Engineering
Page: wiki/concepts/deterministic-output-engineering.md

## Latent Chain-of-Thought Reasoning
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook Claude Code - Skills: Agentic Coding and Prompt Engineering
Page: wiki/concepts/latent-chain-of-thought-reasoning.md

## GitHub Repository File Structure Patterns
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook Claude Code - Skills: Agentic Coding and Prompt Engineering
Page: wiki/concepts/github-repository-file-structure-patterns.md

## Claude Code External Tool Integration via MCP
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook Claude Code - Skills: Agentic Coding and Prompt Engineering
Page: wiki/concepts/claude-code-external-tool-integration-via-mcp.md

## --agent
Source: grok
Agent: --session
Notes: 019fa5a1
Page: --page

## AI Trading Integration
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Anthropic & Agent Ecosystem
Page: wiki/concepts/ai-trading-integration.md

## AI-Assisted Writing Workflows
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Anthropic & Agent Ecosystem
Page: wiki/concepts/ai-assisted-writing-workflows.md

## AI Harness Engineering
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Anthropic & Agent Ecosystem
Page: wiki/concepts/ai-harness-engineering.md

## Anthropic's Free Claude Education Platform
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Anthropic & Agent Ecosystem
Page: wiki/concepts/anthropics-free-claude-education-platform.md

## Free AI Skills and Optimization Techniques
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Anthropic & Agent Ecosystem
Page: wiki/concepts/free-ai-skills-and-optimization-techniques.md

## AI Agent Orchestration Patterns
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Anthropic & Agent Ecosystem
Page: wiki/concepts/ai-agent-orchestration-patterns.md

## Loop Engineering in AI Agent Systems
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Anthropic & Agent Ecosystem
Page: wiki/concepts/loop-engineering-in-ai-agent-systems.md

## Knowledge Graph Construction for AI Memory Systems
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Anthropic & Agent Ecosystem
Page: wiki/concepts/knowledge-graph-construction-for-ai-memory-systems.md

## AI Agent Skill Design Patterns
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Anthropic & Agent Ecosystem
Page: wiki/concepts/ai-agent-skill-design-patterns.md

## Multi-Agent Orchestration
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Anthropic & Agent Ecosystem
Page: wiki/concepts/multi-agent-orchestration.md

## Free AI Coding Alternatives
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: AI Coding & Tooling
Page: wiki/concepts/free-ai-coding-alternatives.md

## Parallel Agent Session Management
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: AI Coding & Tooling
Page: wiki/concepts/parallel-agent-session-management.md

## NotebookLM Enhanced Capabilities
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: AI Coding & Tooling
Page: wiki/concepts/notebooklm-enhanced-capabilities.md

## Local Audio Model Capabilities
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: AI Coding & Tooling
Page: wiki/concepts/local-audio-model-capabilities.md

## Kimi K2.7 Code MoE Architecture
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: AI Coding & Tooling
Page: wiki/concepts/kimi-k27-code-moe-architecture.md

## AI Image and Video Generation Workflows
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: AI Coding & Tooling
Page: wiki/concepts/ai-image-and-video-generation-workflows.md

## Automated Model Routing in AI Coding
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: AI Coding & Tooling
Page: wiki/concepts/automated-model-routing-in-ai-coding.md

## Free Open-Source Developer Tools
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: AI Coding & Tooling
Page: wiki/concepts/free-open-source-developer-tools.md

## Free Open-Source Self-Hosted Software Alternatives
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: AI Coding & Tooling
Page: wiki/concepts/free-open-source-self-hosted-software-alternatives.md

## Free Open Source AI Coding Models
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: AI Coding & Tooling
Page: wiki/concepts/free-open-source-ai-coding-models.md

## research-to-execution-ratio-self-reinforcing-pattern
Source: session-019fa48a
Agent: grok
Notes: Cross-session systemic pattern: research artifacts accumulate faster than execution. Self-reinforcing loop. Detection signal: operator confusion after confirmatory research.
Page: wiki/concepts/research-to-execution-ratio-self-reinforcing-pattern.md

## --agent
Source: grok
Agent: --session
Notes: 019fa5a1
Page: --page

## Missing decision frameworks: 9 gaps
Source: wiki-2026-07-28
Agent: grok
Notes: Synthesis of 3 research streams: 9 framework categories workspace lacks, ranked by failure class caught
Page: wiki/concepts/missing-decision-frameworks-9-gaps.md

## Adaptive AI Agent Systems
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook Agentic Engineering Playbook
Page: wiki/concepts/adaptive-ai-agent-systems.md

## Agentic AI System Patterns
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook Agentic Engineering Playbook
Page: wiki/concepts/agentic-ai-system-patterns.md

## Autonomous AI Coding Agents
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook Agentic Engineering Playbook
Page: wiki/concepts/autonomous-ai-coding-agents.md

## Vercel Security Checkpoint
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook Agentic Engineering Playbook
Page: wiki/concepts/vercel-security-checkpoint.md

## Claude Code Platform Configuration and Deployment
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook Agentic Engineering Playbook
Page: wiki/concepts/claude-code-platform-configuration-and-deployment.md

## AI Agent Design in Pydantic AI
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook Agentic Engineering Playbook
Page: wiki/concepts/ai-agent-design-in-pydantic-ai.md

## Claude Agent SDK Concepts
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook Agentic Engineering Playbook
Page: wiki/concepts/claude-agent-sdk-concepts.md

## Deterministic Control Patterns in Agentic Coding Systems
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook Agentic Engineering Playbook
Page: wiki/concepts/deterministic-control-patterns-in-agentic-coding-systems.md

## Claude Code Hook System Patterns
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook Agentic Engineering Playbook
Page: wiki/concepts/claude-code-hook-system-patterns.md

## Claude Code Hooks
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook Agentic Engineering Playbook
Page: wiki/concepts/claude-code-hooks.md

## AI Agent Design Patterns
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook Agentic Engineering Playbook
Page: wiki/concepts/ai-agent-design-patterns.md

## Agentic AI System Architectures
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook Agentic Engineering Playbook
Page: wiki/concepts/agentic-ai-system-architectures.md

## Planning in AI Coding Agents
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook Agentic Engineering Playbook
Page: wiki/concepts/planning-in-ai-coding-agents.md

## Vercel Security Checkpoint
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook Agentic Engineering Playbook
Page: wiki/concepts/vercel-security-checkpoint.md

## Claude Code Shell Integration and Configuration
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook Agentic Engineering Playbook
Page: wiki/concepts/claude-code-shell-integration-and-configuration.md

## Pydantic AI Agent Patterns
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook Agentic Engineering Playbook
Page: wiki/concepts/pydantic-ai-agent-patterns.md

## Claude Agent SDK Architecture
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook Agentic Engineering Playbook
Page: wiki/concepts/claude-agent-sdk-architecture.md

## Context Compaction and Resumption Continuity in Agentic Coding Systems
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook Agentic Engineering Playbook
Page: wiki/concepts/context-compaction-and-resumption-continuity-in-agentic-codi.md

## Claude Code Hook System
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook Agentic Engineering Playbook
Page: wiki/concepts/claude-code-hook-system.md

## Claude Code Hooks
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook Agentic Engineering Playbook
Page: wiki/concepts/claude-code-hooks.md

## workspace-infrastructure-investment-priorities-2026
Source: session-019fa48a
Agent: grok
Notes: /www investigation of 6 system-level tracks. Cross-cutting: thin-layer-over-existing-substrate wins on every track.
Page: wiki/concepts/workspace-infrastructure-investment-priorities-2026.md

## Why source-code citation rule
Source: session-019fa39d /why RCA
Agent: grok
Notes: Decision: /why system-behavior claims must cite source-code location (file:line) that produces the output. [INFERENCE]-first protocol. Root cause: 3/8 findings wrong because narrated from JSON output, not code. Fresh-lens /tp caught all 3 by reading source.
Page: P:/.data/wiki/concepts/why-source-code-citation-rule.md

## [2026-07-27] ingest | Verification claim admissibility: verdict vocabulary, replay realism, and baseline-aware regression
Source: session-2026-07-27
Agent: grok
Notes: Verification claim admissibility rules (O-3/O-4/O-5)
Page: wiki/concepts/verification-claim-admissibility.md

## Queue-of-work pattern for nlm-to-wiki
Source: wiki-2026-07-28
Agent: grok
Notes: Architecture decision: decouple work distribution from execution. Workers start/stop independently. Config hot-reload. No kill needed. endjin: 48h→2h.
Page: wiki/concepts/queue-of-work-pattern-for-nlm-to-wiki.md

## Workspace improvement opportunities (8)
Source: session-019fa39d /tp fresh-lens scan
Agent: grok
Notes: Fresh-lens glm-5-2 scan found 8 improvement opportunities. Keystone: extract wiki-gate into shared __lib (15 skills, divergent criteria). Also: workspace-wide evidence tiers, Step 0.5 hit-rate measurement, scheduler_create for cadence, maintainability review on analytical skills, /debrief consolidation, /close↔/aar contract drift clustering, three-layer enforcement architecture naming.
Page: P:/.data/wiki/concepts/workspace-improvement-opportunities-20260727.md

## Deepseek D-Spark Speculative Decoding
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WebSync: Watch Later - YouTube
Page: wiki/concepts/deepseek-d-spark-speculative-decoding.md

## Skill per Hour
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WebSync: Watch Later - YouTube
Page: wiki/concepts/skill-per-hour.md

## Pharmacologic Interventions for Metabolic Health
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WebSync: Watch Later - YouTube
Page: wiki/concepts/pharmacologic-interventions-for-metabolic-health.md

## YouTube Video Dialogue and Commentary Formats
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WebSync: Watch Later - YouTube
Page: wiki/concepts/youtube-video-dialogue-and-commentary-formats.md

## Generative AI Tool Patterns
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WebSync: Watch Later - YouTube
Page: wiki/concepts/generative-ai-tool-patterns.md

## Niacin and GPR109a Receptor Activation
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WebSync: Watch Later - YouTube
Page: wiki/concepts/niacin-and-gpr109a-receptor-activation.md

## Israel-Palestine Conflict Discourse
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WebSync: Watch Later - YouTube
Page: wiki/concepts/israel-palestine-conflict-discourse.md

## Wellness Optimization Metrics
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WebSync: Watch Later - YouTube
Page: wiki/concepts/wellness-optimization-metrics.md

## Government Debt and Fiscal Policy
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WebSync: Watch Later - YouTube
Page: wiki/concepts/government-debt-and-fiscal-policy.md

## Portable AI Brain Pattern
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WebSync: Watch Later - YouTube
Page: wiki/concepts/portable-ai-brain-pattern.md

## Smart Glasses Phone Connectivity
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: NotebookLM & Google AI
Page: wiki/concepts/smart-glasses-phone-connectivity.md

## Agent Harness Engineering
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: NotebookLM & Google AI
Page: wiki/concepts/agent-harness-engineering.md

## Open-Source Chinese AI Models
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: NotebookLM & Google AI
Page: wiki/concepts/open-source-chinese-ai-models.md

## NotebookLM Gemini Integration
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: NotebookLM & Google AI
Page: wiki/concepts/notebooklm-gemini-integration.md

## Externalized AI Memory Systems
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: NotebookLM & Google AI
Page: wiki/concepts/externalized-ai-memory-systems.md

## Jira Ticket to Pull Request Automation
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Local AI Models & GPU
Page: wiki/concepts/jira-ticket-to-pull-request-automation.md

## Smart Glasses Market Competition
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Local AI Models & GPU
Page: wiki/concepts/smart-glasses-market-competition.md

## Open-Weight Code Models and Tools
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Local AI Models & GPU
Page: wiki/concepts/open-weight-code-models-and-tools.md

## Systematic Trading Approaches
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Local AI Models & GPU
Page: wiki/concepts/systematic-trading-approaches.md

## Quantization and Memory Optimization for Local AI Models
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Local AI Models & GPU
Page: wiki/concepts/quantization-and-memory-optimization-for-local-ai-models.md

## Routine skill improvement cadence
Source: session-019fa39d /www research
Agent: grok
Notes: Scheduled monthly/quarterly skill health checks using existing skill combinations. Key insight: cadence matters more than technique. Novel combinations explored: /design on skills, /packet+cross-model, /www+skill-dev, /tp on skill framing. 3 parallel subagents + disconfirmation.
Page: P:/.data/wiki/concepts/routine-skill-improvement-cadence.md

## Shared-directory contamination pattern
Source: wiki-2026-07-27
Agent: grok
Notes: Bug pattern: accumulating artifacts from multiple runs break per-unit processing when stages don't filter by unit identity
Page: wiki/concepts/shared-directory-contamination-pattern.md

## Claude Code Video Editing Automation
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Claude Code Repos & Tools
Page: wiki/concepts/claude-code-video-editing-automation.md

## Vector Search vs Plain Text Search
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Claude Code Repos & Tools
Page: wiki/concepts/vector-search-vs-plain-text-search.md

## Claude Code Context Management and Steering Patterns
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Claude Code Repos & Tools
Page: wiki/concepts/claude-code-context-management-and-steering-patterns.md

## Codebase Knowledge Graph Mapping
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Claude Code Repos & Tools
Page: wiki/concepts/codebase-knowledge-graph-mapping.md

## Skill-step receipts checked by hooks
Source: wiki-2026-07-27
Agent: grok
Notes: Design analysis: receipt-checking hooks for skill steps. Catches step-skip under closure pressure; doesn't catch quality. 3 proposals ascending complexity.
Page: wiki/concepts/skill-step-receipts-checked-by-hooks.md

## Systematic problem anticipation: methods and existing tools
Source: wiki-2026-07-27
Agent: grok
Notes: Formal methods survey (FMEA, MCTS, LATS, ToT) + skills/repos across our env, Claude marketplace, and internet
Page: wiki/concepts/systematic-problem-anticipation-methods-and-existing-tools.md

## --concept
Source: verification-receipt-systems-design-landscape
Agent: --source
Notes: session-019fa48a /www
Page: --note

## Consumer Product Design Strategies
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Options & Trading
Page: wiki/concepts/consumer-product-design-strategies.md

## Dividend Portfolio Income Strategies
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Options & Trading
Page: wiki/concepts/dividend-portfolio-income-strategies.md

## Tesla Optimus Production Infrastructure
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Options & Trading
Page: wiki/concepts/tesla-optimus-production-infrastructure.md

## MCP Server Architecture and Ecosystem
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Options & Trading
Page: wiki/concepts/mcp-server-architecture-and-ecosystem.md

## Low-Cost Autonomous Drone Systems
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Options & Trading
Page: wiki/concepts/low-cost-autonomous-drone-systems.md

## Going Trump Every
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Options & Trading
Page: wiki/concepts/going-trump-every.md

## Zero DTE Options Trading Approaches
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Options & Trading
Page: wiki/concepts/zero-dte-options-trading-approaches.md

## [2026-07-27] ingest | Assumption-auditing and unknown-unknown discovery: mental models for self-correcting AI agents
Source: session-2026-07-27
Agent: grok
Notes: Assumption-auditing and unknown-unknown discovery mental models
Page: wiki/concepts/assumption-auditing-and-unknown-unknown-discovery.md

## --concept
Source: mechanisms-for-thought-partner-behavior
Agent: --action
Notes: created
Page: --source

## Autistic Social Communication Patterns and Coping Strategies
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Misc (HFY + assorted)
Page: wiki/concepts/autistic-social-communication-patterns-and-coping-strategies.md

## Claude Design Rapid Prototyping
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Misc (HFY + assorted)
Page: wiki/concepts/claude-design-rapid-prototyping.md

## Human Resilience Under Alien Duress
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Misc (HFY + assorted)
Page: wiki/concepts/human-resilience-under-alien-duress.md

## Smart Glasses Display Technology
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Misc (HFY + assorted)
Page: wiki/concepts/smart-glasses-display-technology.md

## Women Attraction Patterns and Preferences
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Misc (HFY + assorted)
Page: wiki/concepts/women-attraction-patterns-and-preferences.md

## Metabolic Approaches for Body Composition Optimization
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Misc (HFY + assorted)
Page: wiki/concepts/metabolic-approaches-for-body-composition-optimization.md

## Carney's Diplomatic Strategy With Trump
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Misc (HFY + assorted)
Page: wiki/concepts/carneys-diplomatic-strategy-with-trump.md

## Multi-Model AI Workflow Patterns
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Misc (HFY + assorted)
Page: wiki/concepts/multi-model-ai-workflow-patterns.md

## Photobiomodulation Wavelengths and Biological Effects
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: GitHub Trending & AI News
Page: wiki/concepts/photobiomodulation-wavelengths-and-biological-effects.md

## Exercise Benefits for ADHD
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: GitHub Trending & AI News
Page: wiki/concepts/exercise-benefits-for-adhd.md

## Adaptive Teaching Skills
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: GitHub Trending & AI News
Page: wiki/concepts/adaptive-teaching-skills.md

## Claude Design Transformation Method
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: GitHub Trending & AI News
Page: wiki/concepts/claude-design-transformation-method.md

## Invisible Workplace Dynamics
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: GitHub Trending & AI News
Page: wiki/concepts/invisible-workplace-dynamics.md

## Smart Glasses Display Technologies and Ecosystem
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: GitHub Trending & AI News
Page: wiki/concepts/smart-glasses-display-technologies-and-ecosystem.md

## Ukraine Russia Drone Warfare Dynamics
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: GitHub Trending & AI News
Page: wiki/concepts/ukraine-russia-drone-warfare-dynamics.md

## Canada's Geopolitical Repositioning Under Carney
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: GitHub Trending & AI News
Page: wiki/concepts/canadas-geopolitical-repositioning-under-carney.md

## Metabolic Health And Visceral Fat Management
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: GitHub Trending & AI News
Page: wiki/concepts/metabolic-health-and-visceral-fat-management.md

## Claude Skills
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: GitHub Trending & AI News
Page: wiki/concepts/claude-skills.md

## Friction in Computing Systems
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Health & Weight Loss
Page: wiki/concepts/friction-in-computing-systems.md

## Light Wavelengths and Biological Effects
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Health & Weight Loss
Page: wiki/concepts/light-wavelengths-and-biological-effects.md

## Gemma 4 QAT and Uncensored Variants
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Health & Weight Loss
Page: wiki/concepts/gemma-4-qat-and-uncensored-variants.md

## COVID-19 Vaccine Controversy and Public Discourse
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Health & Weight Loss
Page: wiki/concepts/covid-19-vaccine-controversy-and-public-discourse.md

## Canadian Retirement Advantage Programs
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Health & Weight Loss
Page: wiki/concepts/canadian-retirement-advantage-programs.md

## Ukraine's Drone Warfare Capabilities
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Health & Weight Loss
Page: wiki/concepts/ukraines-drone-warfare-capabilities.md

## Trading Psychology and Market Behavior
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Health & Weight Loss
Page: wiki/concepts/trading-psychology-and-market-behavior.md

## Canada-US Relations Under Trump and Carney
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Health & Weight Loss
Page: wiki/concepts/canada-us-relations-under-trump-and-carney.md

## Metabolic Health Optimization
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Health & Weight Loss
Page: wiki/concepts/metabolic-health-optimization.md

## Claude Code Multi-Agent Collaboration Patterns
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Health & Weight Loss
Page: wiki/concepts/claude-code-multi-agent-collaboration-patterns.md

## ADHD-Autism Cognitive and Behavioral Contrasts
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Canadian Politics & Trade
Page: wiki/concepts/adhd-autism-cognitive-and-behavioral-contrasts.md

## Henry Noik Case Public Debates
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Canadian Politics & Trade
Page: wiki/concepts/henry-noik-case-public-debates.md

## Gemma Uncensored QAT Models
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Canadian Politics & Trade
Page: wiki/concepts/gemma-uncensored-qat-models.md

## Ampersand Loop Knot for Drawstrings
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Canadian Politics & Trade
Page: wiki/concepts/ampersand-loop-knot-for-drawstrings.md

## New World Screwworm Reintroduction and Containment Failure
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Canadian Politics & Trade
Page: wiki/concepts/new-world-screwworm-reintroduction-and-containment-failure.md

## Ukraine-Russia Drone Warfare Dominance
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Canadian Politics & Trade
Page: wiki/concepts/ukraine-russia-drone-warfare-dominance.md

## Body Composition Optimization Strategies
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Canadian Politics & Trade
Page: wiki/concepts/body-composition-optimization-strategies.md

## Systemic Software Fragility
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Canadian Politics & Trade
Page: wiki/concepts/systemic-software-fragility.md

## Canada-US Tensions Under Carney and Trump
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Canadian Politics & Trade
Page: wiki/concepts/canada-us-tensions-under-carney-and-trump.md

## Claude Code Dynamic Workflows
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL: Canadian Politics & Trade
Page: wiki/concepts/claude-code-dynamic-workflows.md

## [2026-07-27] ingest | Solo-director AI-coder fleet: coordination, isolation, and stale-data immunity best practices
Source: session-2026-07-27
Agent: grok
Notes: Solo-director AI fleet coordination research
Page: wiki/concepts/solo-director-ai-fleet-coordination-isolation-best-practices.md

## --concept
Source: fabricated-fatigue-llm-session-end-recommendations
Agent: --source
Notes: session-019fa48a /wiki
Page: --note

## [2026-07-27] ingest | Handoff fragmentation under recurrence: single-writer-per-file produces N authoritative files for one workstream
Source: session-2026-07-27
Agent: grok
Notes: Handoff fragmentation under recurrence finding
Page: wiki/concepts/handoff-fragmentation-under-recurrence.md

## --concept
Source: handoff-fragmentation-under-recurrence
Agent: --session
Notes: 019fa5a1
Page: --summary

## Agentic SDLC lifecycle validated end-to-end
Source: session-019fa39d AAR Q11
Agent: grok
Notes: Empirical validation: 9-skill cascade (why→www→design→go→check→review→wiki→handoff) chained naturally without manual bridging. /close failure was skill-internal, not lifecycle-level.
Page: P:/.data/wiki/concepts/agentic-sdlc-lifecycle-validated-end-to-end.md

## --concept
Source: agents-md-construction-best-practices
Agent: --source
Notes: session-019fa48a /www
Page: --note

## Terminal visual enhancements for agentic CLIs
Source: wiki-2026-07-27
Agent: grok
Notes: 3 pure-Unicode enhancements (bar chart, sparkline, clickable links) + dual-mode + progressive disclosure
Page: wiki/concepts/terminal-visual-enhancements-for-agentic-clis.md

## --concept
Source: mechanical-enforcement-over-behavioral-reminder
Agent: --source
Notes: session-019fa48a /wiki
Page: --note

## --concept
Source: operator-model-routing-directives
Agent: --source
Notes: session-019fa48a /why capture-failure fix
Page: --note

## --concept
Source: fts5-query-syntax-escaping-required
Agent: --source
Notes: session-019fa48a /why
Page: --note

## Video-to-wiki pipeline report: metrics and framework
Source: wiki-2026-07-27
Agent: grok
Notes: Pilot metrics + 3-tier reporting framework for video-to-knowledge pipelines
Page: wiki/concepts/video-to-wiki-pipeline-report-metrics-and-framework.md

## Claude AI Side Hustle Approaches
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL-Pilot: Claude Skills & Code
Page: wiki/concepts/claude-ai-side-hustle-approaches.md

## Claude Trading System Integration
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL-Pilot: Claude Skills & Code
Page: wiki/concepts/claude-trading-system-integration.md

## Claude Tag Multiplayer Collaboration
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL-Pilot: Claude Skills & Code
Page: wiki/concepts/claude-tag-multiplayer-collaboration.md

## Claude Loop Engineering
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL-Pilot: Claude Skills & Code
Page: wiki/concepts/claude-loop-engineering.md

## Prompt Engineering for Next-Generation AI Models
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL-Pilot: Claude Skills & Code
Page: wiki/concepts/prompt-engineering-for-next-generation-ai-models.md

## Claude Design Skills
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL-Pilot: Claude Skills & Code
Page: wiki/concepts/claude-design-skills.md

## AI Model Performance Benchmarks
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL-Pilot: Claude Skills & Code
Page: wiki/concepts/ai-model-performance-benchmarks.md

## Claude Code Usage Patterns
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL-Pilot: Claude Skills & Code
Page: wiki/concepts/claude-code-usage-patterns.md

## AI-Powered Video Editing Integration
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL-Pilot: Claude Skills & Code
Page: wiki/concepts/ai-powered-video-editing-integration.md

## Claude Skills Overview
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL-Pilot: Claude Skills & Code
Page: wiki/concepts/claude-skills-overview.md

## --concept
Source: conversation-distillation-review-packet-export
Agent: --source
Notes: session-019fa48a
Page: --note

## --concept
Source: compaction-inherited-diagnosis-unverified-propagation
Agent: --action
Notes: created
Page: --source

## Claude AI Side Hustle Implementation
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL-Pilot: Claude Skills & Code
Page: wiki/concepts/claude-ai-side-hustle-implementation.md

## Anthropic Collaborative AI Tools
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL-Pilot: Claude Skills & Code
Page: wiki/concepts/anthropic-collaborative-ai-tools.md

## Claude Loop Engineering
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL-Pilot: Claude Skills & Code
Page: wiki/concepts/claude-loop-engineering.md

## AI Prompting Optimization Techniques
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL-Pilot: Claude Skills & Code
Page: wiki/concepts/ai-prompting-optimization-techniques.md

## Frontier AI Model Benchmarks and Rankings
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL-Pilot: Claude Skills & Code
Page: wiki/concepts/frontier-ai-model-benchmarks-and-rankings.md

## Claude Operational Best Practices
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL-Pilot: Claude Skills & Code
Page: wiki/concepts/claude-operational-best-practices.md

## Claude Skills Overview
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL-Pilot: Claude Skills & Code
Page: wiki/concepts/claude-skills-overview.md

## --concept
Source: skill-management-in-agentic-systems-research-survey
Agent: --action
Notes: created
Page: --source

## --concept
Source: local-config-dataclass-for-circular-import-boundary
Agent: --action
Notes: created
Page: --source

## --concept
Source: cross-module-call-graph-audit-false-negative
Agent: --action
Notes: created
Page: --source

## Handoff: wiki-query-stop-hook-20260727
Source: session-019fa39d
Agent: grok
Notes: Handoff for the wiki-query Stop hook implementation. Design complete (3 rounds + critical friend), 5 units COMMIT_THIS_SESSION ready. Design doc in temp. Shadow mode default. nlm-class reproduction as Unit 7.
Page: P:\docs\handoffs\wiki-query-stop-hook-20260727\HANDOFF.md

## /design speedup: --fast mode + parallel pre-write
Source: session-019f9a3c /go implementation
Agent: grok
Notes: Decision concept: 4 research-backed speedups implemented in /design SKILL.md. --fast mode (2-round default), Step 0.9 (parallel pre-write), parallel review, model cascading. Parallel section drafting rejected. Commits 76b4634, 0d9a41b. /review found 2 interaction gaps (R-001, R-002) accepted as caveats.
Page: P:/.data/wiki/concepts/design-skill-speedup-fast-mode-parallel-prewrite.md

## Skill domain map
Source: session-2026-07-27
Agent: grok
Notes: 13 domains, 60 Grok skills, 50 Claude-only gaps
Page: wiki/concepts/skill-domain-map.md

## LLM synthesis quality and speed techniques
Source: session-019f9a3c /www follow-up
Agent: grok
Notes: /www on synthesis quality, speed, constrained generation, iterative refinement. 4 findings: (1) input diversity + synthesis prompt > technique, (2) prefix caching + cascading + speculative decoding are near-lossless speedups, (3) outline helps but rigid JSON hurts prose, (4) 2-round default sufficient, 3+ overkill. Practical synthesis for /design: 2-round + cascading + parallel pre-write + outline + structured metadata. 4 parallel subagents.
Page: P:/.data/wiki/concepts/llm-synthesis-quality-and-speed-techniques.md

## Claude AI Side Hustles
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL-Pilot: Claude Skills & Code
Page: wiki/concepts/claude-ai-side-hustles.md

## Claude Tag Team Collaboration
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL-Pilot: Claude Skills & Code
Page: wiki/concepts/claude-tag-team-collaboration.md

## AI Model Benchmarking Performance
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL-Pilot: Claude Skills & Code
Page: wiki/concepts/ai-model-benchmarking-performance.md

## Claude Operational Best Practices
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL-Pilot: Claude Skills & Code
Page: wiki/concepts/claude-operational-best-practices.md

## Claude-Powered Video Editing Workflows
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL-Pilot: Claude Skills & Code
Page: wiki/concepts/claude-powered-video-editing-workflows.md

## Claude Skills
Source: nlm-sync-2026-07-27
Agent: grok
Notes: Synced from NotebookLM notebook WL-Pilot: Claude Skills & Code
Page: wiki/concepts/claude-skills.md

## nlm-to-wiki optimization opportunities
Source: wiki-2026-07-27
Agent: grok
Notes: 5 ranked optimizations from live timing data: parallel export (6x), parallel synthesis (5x), embedding cache (60x re-sync)
Page: wiki/concepts/nlm-to-wiki-optimization-opportunities.md

## Stateful skills need a maintenance surface
Source: wiki-2026-07-27
Agent: grok
Notes: Architecture decision: stateful skills that accumulate durable state need audit/fix/prune/disk-report surface
Page: wiki/concepts/stateful-skills-need-maintenance-surface.md

## Parallelizing design-doc generation: what works
Source: session-019f9a3c /www research
Agent: grok
Notes: /www on parallel multi-agent design-doc generation. Operator's proposed pattern (parallel drafters -> merge) is LEAST effective. 3 findings: (1) parallel section drafting rarely beats serial, (2) FusioN beats BoN by up to +55%, (3) parallelism pays at pre-write + post-write layers. Optimal speedup: parallel pre-write + parallel review + --fast mode. 4 parallel subagents + disconfirmation.
Page: P:/.data/wiki/concepts/parallelizing-design-doc-generation-what-works.md

## skip-write-only-computation-over-cache-or-budget + visible-output-contracts-for-behavioral-skill-steps
Source: session-2026-07-27
Agent: grok
Notes: Added 2 decision concepts from hook timeout RCA. Concept 1: skip write-only fields (275x speedup). Concept 2: visible-output receipts for /why Step 0.5.
Page: P:/.data/wiki/concepts/skip-write-only-computation-over-cache-or-budget.md

## Auto-test Stop hooks and property-based testing for AI-generated code
Source: session-2026-07-27 / /www auto-test + mutation/PBT research
Agent: grok
Notes: Auto-test in Stop hook saves turns via additionalContext JSON. PBT (Hypothesis) catches 81% vs 69% for unit tests on AI code — solves tautological-test blind spot. Mutation testing too slow for hooks; use CI. Recommendation: extend quality_gate.py to run tests + emit additionalContext + check stopHookActive.
Page: P:/.data/wiki/concepts/auto-test-stop-hooks-and-property-based-testing.md

## LLM instruction non-compliance activation gap
Source: session-2026-07-27
Agent: grok
Notes: Why agents read skills but don't follow them; CLAUDE.md outperforms skills for always-on rules
Page: wiki/concepts/llm-instruction-non-compliance-activation-gap-2026.md

## Enforcing KB consultation before action: methods
Source: session-019f9a3c /www research
Agent: grok
Notes: /www on how practitioners force agents to check docs before acting. 3 tiers (hard/soft/adaptive); hard preferred. Reflection fails without external grounding. Risk-tiered escalation beats confidence-based. Wiki claims externally corroborated. 4 parallel subagents + disconfirmation pass.
Page: P:/.data/wiki/concepts/enforcing-kb-consultation-before-action-methods.md

## Error-handling loops skip the wiki-query step
Source: session-019f9a3c /why RCA
Agent: grok
Notes: /why on nlm-to-wiki session that declared 'operator must do OAuth' without querying wiki. Distinct trigger from search-before-proposing: error-handling is diagnosis-shaped, not proposal-shaped. Cross-model review (glm-5-2) passed 3/3.
Page: P:/.data/wiki/concepts/error-handling-loops-skip-wiki-query.md

## Grok Build Stop hook patterns and v0.2.107 feedback mechanism
Source: session-2026-07-27 / /www grok build hooks
Agent: grok
Notes: Grok Build v0.2.107 added feedback-to-model mechanism for Stop hooks (not just exit-2 blocking). Community implementations scarce — only dcg + quality_gate.py ship real Grok-native hooks. Key lesson: gate only on risky turns per Snorkel self-critique paradox.
Page: P:/.data/wiki/concepts/grok-build-stop-hook-patterns-and-feedback-mechanism.md

## Fabrication-ceremony tax: compounding cost of structural defenses against lying
Source: dream-2026-07-26-incremental
Agent: grok
Notes: /dream Pass 1 auto-promotion. Meta-pattern: model fabrication triggers structural ceremony (receipts, validators, scanner gates); ceremony is necessary but compounds superlinearly (gate interaction + ceremony-as-vector + triage overhead). 3 sessions: 019f9f4f trust-deficit diagnosis, 019f9b00 /aar skip + pushback, 019f9bfe layer-1 failures. Operator-articulated: 'lies all the time' not 'forgets.' Key insight: ceremony vocabulary becomes new fabrication vector.
Page: wiki/concepts/fabrication-ceremony-tax-compounding-cost.md

## Self-improving agent systems deep-dive
Source: session-2026-07-27 / SI-03 repo research
Agent: grok
Notes: 20 techniques extracted from 4 repos. Lowest-effort: Self-Debug, Dynamic Cheatsheet, CRITIC hook, Self-Correct Loop (all Low ~150-200 lines). Updated wiki concept with findings table.
Page: P:/.data/wiki/concepts/self-improving-agent-systems-techniques-and-workspace-gaps.md

## --concept
Source: single-repo-verification-false-negative-on-multi-repo-workspace
Agent: --action
Notes: created
Page: --source

## Markdown/Mermaid rendering in agentic CLIs + stop-narrative 4x recurrence evidence
Source: wiki (session 019f9f48; web: termaid, glow, cursor.com, grok CLI changelog)
Agent: grok
Notes: New concept markdown-mermaid-rendering-agentic-clis-windows-11.md + updated go-home-narrative with 4x recurrence evidence from session 019f9f48
Page: wiki/concepts/markdown-mermaid-rendering-agentic-clis-windows-11.md

## Self-improving agent systems: techniques, frameworks, and workspace gaps
Source: session-2026-07-26 / /www self-improvement research
Agent: grok
Notes: Workspace already implements Reflexion/Voyager/CRITIC/accumulated-rules. Five gaps: improvement kata, self-evolving skills, proactive anticipation, curiosity-driven exploration, Could-You-Be-Wrong prompt. 59 sourced findings, 4 key repos for deeper investigation.
Page: P:/.data/wiki/concepts/self-improving-agent-systems-techniques-and-workspace-gaps.md

## --concept
Source: dream-pass1-auto-promotion-act-on-high-confidence
Agent: --action
Notes: created
Page: --source

## --concept
Source: validator-script-closure-pressure-backstop
Agent: --action
Notes: created
Page: --source

## --concept
Source: trusted-exit-status-fallacy-pipeline-ground-truth
Agent: --action
Notes: created
Page: --source

## stop-hook-feedback-delivery-authoritative-not-tool-result
Source: session-019f9d1f /www research
Agent: grok
Notes: Stop-hook exit code 2 + stderr delivered as authoritative user_query, not untrusted tool-result. HN thread evidence + session transcript verification.
Page: .data/wiki/concepts/stop-hook-feedback-delivery-authoritative-not-tool-result.md

## 2026-07-26 session findings
Source: session-019f9bfe
Agent: grok
Notes: Scope-matching concept revised (commit 339cdf9): reclassified 5 near-misses as layer-1, REJECTED scope-receipt block as anti-pattern, reframed operator as structural external verifier. nemorton-3-ultra root cause FULLY CONFIRMED via dual cross-transport test (commits 44d83f6, 137e338): Grok Build serde bug, not NVIDIA; OpenCode PASS (88.99s, 6 tools), PI PASS (70.44s, 3 tools). Red-team BLOCK on prose-rule adoption: prose rule is anti-pattern #1 per enforcement wiki line 44; concept line 8 (systematize operator catches) contradicts line 159 (prose rule). Path forward: structural mechanism (AAR Q11 feedback loop) + measurement baseline first + separate directive-non-execution class. Three handoffs: nemotron-spawn-failure-investigation, cross-transport-model-matrix, scope-matching-rule-adoption-post-redteam.
Page: P:/.data/wiki/log.md

## AAR skill install scope: user not workspace
Source: session-20260726
Agent: grok
Notes: AAR lives at user scope ~/.grok/skills/aar/ not P:/.grok/skills/aar/. Path bug fixed in commit 236204c. Complements skill-host-applicability-convention.
Page: wiki/concepts/aar-skill-install-scope-user-not-workspace.md

## model-tool-calling-capability-matrix updated
Source: session-2026-07-26 / empirical nemotron testing
Agent: grok
Notes: Empirically tested all 4 nemotron variants. or-nemotron-ultra-free (OpenRouter) works for both trivial and real tool-grounded prompts. nvidia-nemotron-3-ultra fails on tool prompts even with stream_tool_calls=false. zen variant broken (proxy issue).
Page: P:/.data/wiki/concepts/model-tool-calling-capability-matrix.md

## Theatrical contrition / over-apologetic response patterns (research)
Source: www (web: arxiv 2507.02745 Ashktorab, 2502.08177 SycEval, 2602.23971 AISI, 2607.10411 EGDP, 2509.21305 Vennemeyer; springer Harland/Turner; seangoedecke.com; lesswrong nostalgebraist; turntrout.com; patronus.ai)
Agent: grok
Notes: New concept theatrical-contrition-and-over-apologetic-response-patterns.md consolidates UX-optimization angle: explanatory > empathic > rote apology in technical contexts; EGDP-style structured templates as the structural fix.
Page: wiki/concepts/theatrical-contrition-and-over-apologetic-response-patterns.md

## adaptive-orchestration-task-shape-classification
Source: session-019f9d1f /www research
Agent: grok
Notes: /go ceremony classifier validated by 1074 transcript scan
Page: .data/wiki/concepts/adaptive-orchestration-task-shape-classification.md

## Proactive AI volunteering mechanisms: research base and three-mechanism ladder
Source: session-2026-07-26 / /www proactive AI research
Agent: grok
Notes: Field is mixed-initiative (Horvitz 1999). BEHAVE-AI principles (3 of 8 are proactivity CONSTRAINTS). Harari & Amir 2025: proactive help reduces adoption even when useful. Three-mechanism ladder: (1) end-of-turn observation rule [shipped to AGENTS.md], (2) /notice skill [built], (3) full proactive agent [rejected].
Page: P:/.data/wiki/concepts/proactive-ai-volunteering-mechanisms.md

## Meta-rigor: /why Step 14 self-application (research)
Source: www (wiki: mandatory-step-enforcement-code-over-prose, external-state-cross-check-as-structural-fix, analyst-exhibits-pattern-being-analyzed; web: arxiv 2410.04444 Gödel Agent, brightlume.ai, openai harness-engineering)
Agent: grok
Notes: Refined analyst-exhibits-pattern-being-analyzed.md with fix-set extension. All three claimed novel gaps were already documented in wiki from 2026-07-20/21. Actual gap is one skill-wiring: /why Step 14 does not invoke external-state-cross-check on its own fix set.
Page: wiki/concepts/analyst-exhibits-pattern-being-analyzed.md

## Research vs design vs architect skills + /www self-assessment
Source: session-2026-07-26 / /www meta-run
Agent: grok
Notes: Field taxonomy: 4-stage separation (Research → Architecture → Design → Implementation). /www measured at 585 lines, 9 mandatory rules, 3 enhancement batches, Round 2.5 alone 1181 words — past MindStudio inverted-U inflection. Recommendation: keep disconfirmation + ledger + wait-all gate; pare Round 2.5 ingestion triggers + mid-research contradiction check + example invocation.
Page: P:/.data/wiki/concepts/research-vs-design-vs-architect-skills-and-www-self-assessment.md

## scope-matching-verification-discipline
Source: session-20260726
Agent: grok
Notes: /www: verification ceiling + two-layer defense
Page: P:/.data/wiki/concepts/scope-matching-verification-discipline.md

## Receipt-misattribution sub-pattern (why RCA)
Source: why RCA on session 019f9f48 turn 1
Agent: grok
Notes: Added sub-pattern to causal-mechanism-claims-require-source-receipts-before-durable-write.md: receipt misattribution across neighboring claims (verified discovery, misattributed to deployment recommendation). Cross-model reviewed by glm-5-2 (WRITE-WITH-MODIFICATIONS).
Page: wiki/concepts/causal-mechanism-claims-require-source-receipts-before-durable-write.md

## Hook evidence-collection cost vs timeout tradeoff
Source: session-2026-07-26 / /why Step 15
Agent: grok
Notes: Verification hooks that do synchronous git subprocess fan-out don't scale with workspace size; on 994-file P:\ the receipt hook consumed 5.8s of 10s budget on dirty-set scan alone, causing silent receipt-coverage gaps. Cross-model review passed 3/3. Pattern + architectural fixes captured.
Page: P:/.data/wiki/concepts/hook-evidence-collection-cost-vs-timeout-tradeoff.md

## Junction failure modes for skill discovery (research)
Source: www (web: learn.microsoft.com, gitforwindows.org, docker/for-win#1205, openai/codex#11314, upstash/context7#2361; empirical: test_git_junction.py)
Agent: grok
Notes: Updated agent-config-directory-taxonomy.md with junction-vs-symlink failure-mode table. Junctions work for Grok Build + Node.js (verified) and are safe for recommended layout (junction outside git/sync). Codex/OpenCode junction compatibility UNVERIFIED — prior symlink/path-resolution issues suggest possible failure.
Page: wiki/concepts/agent-config-directory-taxonomy.md

## Parallel subagent wait-all-before-conclude gate
Source: session-2026-07-26
Agent: grok
Notes: Rule: orchestrator skills may not emit durable artifacts or fact-conclusions until all dispatched background subagents return completed or explicitly failed. Fixes the partial-persistence failure from the operator-modeling /www run.
Page: P:/.data/wiki/concepts/parallel-subagent-wait-all-gate.md

## User Modeling for Agentic CLIs (disconfirmation upgrade)
Source: session-2026-07-26 / late subagent merge
Agent: grok
Notes: Late-arriving disconfirmation subagent surfaced 3 stronger peer-reviewed sources (P-DPO OpenReview 132 cit, Qian 2021 66 cit, MIT/Penn State ACM CHI 2026). Upgraded concept: disconfirmation table now has 4 peer-reviewed receipts instead of 1, refines ETH Zurich with documentation-substitution reframe, evidence_gaps note per-user-vs-per-project split is untested directly.
Page: P:/.data/wiki/concepts/user-modeling-for-agentic-clis.md

## User Modeling for Agentic CLIs: research landscape and operator-profile recommendation
Source: session-2026-07-26 / www
Agent: grok
Notes: Predictive operator model concept is real (User Modeling / Personal LLM Agents). Disconfirmation flipped naive answer: ETH Zurich -3% on LLM-written context, Writer.com 25x sycophancy under Mem0. Recommendation: keep existing operator-collaboration-style-and-leverage.md; do not auto-inject; add refresh discipline.
Page: P:/.data/wiki/concepts/user-modeling-for-agentic-clis.md

## Skill dedup behavior across agent CLIs (research)
Source: www (web: anomalyco/opencode#29950,#32202; openai/codex#25324,#8169; vercel-labs/skills#1200; anthropics/claude-code#10115,#46833,#42384; nodejs.org/api/fs.html; forum.cursor.com)
Agent: grok
Notes: Re-refined agent-config-directory-taxonomy.md: NO major agent CLI dedupes by resolved path. Symlink into multiple scan roots of same tool causes duplication (Codex/Copilot/Claude/Grok) or non-deterministic last-writer-wins (OpenCode). Corrected recommendation: source outside scan roots, junction to exactly ONE root per tool.
Page: wiki/concepts/agent-config-directory-taxonomy.md

## receipt-before-write handoff + vocabulary-mismatch sub-pattern
Source: session-20260726
Agent: grok
Notes: Deferred structural hook with trigger; workflow fix adopted
Page: P:/docs/handoffs/receipt-before-write-workflow-and-hook-20260726/HANDOFF.md

## Cross-env skill portability research
Source: www (web: opencode.ai/docs, openai/codex#20637, anthropics/claude-code#66352)
Agent: grok
Notes: Refined agent-config-directory-taxonomy.md: .agents/skills/ natively polled by 4/5 tools (Codex, OpenCode, Grok Build, Copilot). Claude Code lone holdout.
Page: wiki/concepts/agent-config-directory-taxonomy.md

## blind-spot-detection-methods (expanded)
Source: session-20260726
Agent: grok
Notes: 5 techniques with workspace mapping + gaps identified (RCF biggest gap; ACH partial in /why)
Page: P:/.data/wiki/concepts/blind-spot-detection-methods.md

## blind-spot-detection-methods
Source: session-20260726
Agent: grok
Notes: /www research: 5 evidence-backed blind-spot techniques (pre-mortem, devil's advocate, RCF, bias blind spot, ACH); maps to workspace; identifies reference class forecasting as the biggest gap
Page: P:/.data/wiki/concepts/blind-spot-detection-methods.md

## extract-moves-not-conditions-tp-enhancements
Source: session-20260725
Agent: grok
Notes: Decision: /tp 3 enhancements (decomposition/tiered output/uncertainty surfacing); the extract-moves-not-conditions principle
Page: P:/.data/wiki/concepts/extract-moves-not-conditions-tp-enhancements.md

## coupling-inventory-as-mandatory-design-section
Source: session-20260725
Agent: grok
Notes: Decision: /design coupling inventory gate (3-layer writer/reviewer/critical-friend enforcement); refines raising-coding-best-practices
Page: P:/.data/wiki/concepts/coupling-inventory-as-mandatory-design-section.md

## Research: structural enforcement for skipped-under-load rules on Grok Build
Source: session-2026-07-26-www-enforcement
Agent: grok
Notes: Researched 5 enforcement mechanisms for rules that get skipped under generative load, focused on Grok Build (command+http hooks only). Findings: (1) 800-line AGENTS.md is the root cause, not rule wording (39% multi-turn drop from flat rule piles); (2) UserPromptSubmit rule-injection is the canonical just-in-time mechanism; (3) PreToolUse regex for Class C is feasible with two-tier pattern; (4) PostToolUse sequence-marker gate via state files; (5) HTTP hook to cross-model LLM judge is last resort (93% failure rate). Dominant failure mode is route-around (background agents bypass Stop hooks; Reward Hacking Benchmark). Ranked implementation: trim AGENTS.md first, then rule-injection, then per-rule hooks. Synthesizes mandatory-step-enforcement-code-over-prose + best-practices-enforcement-mechanism-grok-build + llm-judgment-hooks. 14 sources, multi-source-verified.
Page: wiki/concepts/structural-enforcement-for-skipped-rules-grok-build-2026.md

## cli-api-drift-in-skill-scripts
Source: session-20260725
Agent: grok
Notes: Cross-model reviewed by go-mimo-v2-5 (PROMOTE); companion to subprocess-as-degradation-boundary
Page: P:/.data/wiki/concepts/cli-api-drift-in-skill-scripts.md

## Testing plan: K3 and Ultra spawn_subagent failures
Source: session-2026-07-26
Agent: grok
Notes: Proper testing plan with /tp review. Phase 0 discriminates the reasoning_content hypothesis via known-working models. Phase 1 splits K3 (OpenCode proxy) and Ultra (NVIDIA direct) as separate tracks. Revised based on review: added T0 discriminator, split tracks, deferred upstream reporting until root cause confirmed.
Page: wiki/concepts/testing-plan-k3-ultra-spawn-failures.md

## subprocess-as-degradation-boundary
Source: session-20260725
Agent: grok
Notes: Isolates the coupling insight from /tp critique; companion to cli-api-drift
Page: P:/.data/wiki/concepts/subprocess-as-degradation-boundary.md

## 3 wiki concepts: decisions + finding from session close
Source: session-019f9a89-close-followup
Agent: grok
Notes: Three concepts captured during close follow-up: (1) nemotron-tp-pool-demote-decision — §4b decision documenting the /tp pool demotion with falsifier; (2) wiki-captures-decisions-by-default — §4b decision documenting the SCHEMA §4 split; (3) verify-against-existing-state-before-defensive-mechanisms — §4a finding codifying the structural fix for over-engineering errors. All pass validate_wiki_entry.py. Plus 2 handoffs: missed-decisions-wiki-capture-investigation and why-skill-adoption-gap.
Page: wiki/concepts/nemotron-tp-pool-demote-decision.md, wiki/concepts/wiki-captures-decisions-by-default.md, wiki/concepts/verify-against-existing-state-before-defensive-mechanisms.md

## VII. Advanced Memory Architectures
Source: nlm-sync-2026-07-25
Agent: grok
Notes: Synced from NotebookLM notebook WL-Pilot: Claude Skills & Code
Page: wiki/concepts/nlm-23bf4931-vii-advanced-memory-architectures.md

## VI. Information Architecture and Prompt Engineering
Source: nlm-sync-2026-07-25
Agent: grok
Notes: Synced from NotebookLM notebook WL-Pilot: Claude Skills & Code
Page: wiki/concepts/nlm-23bf4931-vi-information-architecture-and-prompt-engineering.md

## IV. Enterprise Collaboration and Autonomy
Source: nlm-sync-2026-07-25
Agent: grok
Notes: Synced from NotebookLM notebook WL-Pilot: Claude Skills & Code
Page: wiki/concepts/nlm-23bf4931-iv-enterprise-collaboration-and-autonomy.md

## III. Specialized Workflow Components
Source: nlm-sync-2026-07-25
Agent: grok
Notes: Synced from NotebookLM notebook WL-Pilot: Claude Skills & Code
Page: wiki/concepts/nlm-23bf4931-iii-specialized-workflow-components.md

## I. Foundational Claude Configuration and Capabilities
Source: nlm-sync-2026-07-25
Agent: grok
Notes: Synced from NotebookLM notebook WL-Pilot: Claude Skills & Code
Page: wiki/concepts/nlm-23bf4931-i-foundational-claude-configuration-and.md

## Documented deferral: when documentation substitutes for action
Source: session-2026-07-25 (via /aar Phase 9.5 auto-promotion)
Agent: grok
Notes: Phase 9.5 auto-promoted lesson L1 from AAR of session 019f9b00. Three instances of the agent documenting a diagnosed defect for 'the next session' instead of fixing it in the same turn when the fix was cheap (stale accurate_as_of_head, /aar skip, D1-D3 deferral). Same failure class as narrative-as-signal, applied to agent's own process. Same-turn fix rule + detection-signal phrases. INVESTIGATE lifecycle: needs cross-session evidence before AGENTS.md rule promotion.
Page: wiki/concepts/documented-deferral-substitutes-for-action.md

## Grok workflows: community sentiment + security incident + bcherny quantified wins
Source: session-2026-07-25 (via /www run 3)
Agent: grok
Notes: /www gap-fill run 3 on existing grok-build-workflows-rhai-orchestration concept. Added: community sentiment section (HN + r/ClaudeAI praise patterns: visibility, context-mgmt, long-task correctness; criticisms: cost, primitive-proliferation confusion, token-burn suspicion), two new failure modes (primitive-proliferation confusion, Grok-specific repo-upload security incident Jul 12-16 verified across 5+ sources), bcherny Anthropic-internal quantified wins (SDK startup -61%, CPU/mem 2-10x, false-positive prompts -45%, 10K+ LOC deleted). 434 lines, validator PASS. Run 3 of 3 in /www ledger.
Page: wiki/concepts/grok-build-workflows-rhai-orchestration.md

## [2026-07-25] ingest | Agentic workflows: Grok / Claude Code / Codex orchestration best practices
Source: session-2026-07-25
Agent: grok
Notes: Updated /www run 3: community sentiment + security incident + bcherny quantified wins (session 019f9b00)
Page: wiki/concepts/grok-build-workflows-rhai-orchestration.md

## ADHD parallel-frame divergent ideation integration
Source: session-20260725
Agent: grok
Notes: Refines brainstorming-ideation-with-llms; analyzes UditAkhourii/adhd technique integration with /tp, /design, brainstorming
Page: P:/.data/wiki/concepts/adhd-parallel-frame-divergent-ideation-integration.md

## [2026-07-25] ingest | Documented deferral: when documentation substitutes for action
Source: session-2026-07-25
Agent: grok
Notes: AAR auto-promoted lesson L1 from session 019f9b00
Page: wiki/concepts/documented-deferral-substitutes-for-action.md

## New wiki concept: lexical-vs-semantic-verification-gap
Source: session-019f9a89-why-v3-ab-test
Agent: grok
Notes: Captured the control-plane failure pattern that the /why v3 A/B test surfaced: a gate can fire correctly lexically (exit code 0, file written) while measuring the wrong thing semantically (does the receipt prove completion). Distinct from premature-closure (model-side) and from mutation-receipt (system-side architecture); this is the verification-plane gap that lets the model's false claim pass the gate. Validated by the A/B run: v1 found the underlying measurement gap but bucketed as generic 'Structural'; v3 Step 6 sub-dimension named it as the highest-signal finding. Passes validate_wiki_entry.py with Receipts section.
Page: wiki/concepts/lexical-vs-semantic-verification-gap.md

## Optimal-vs-blanket rule application
Source: session-2026-07-25
Agent: grok
Notes: When a default rule (observe-then-refactor) is applied as a blanket, it often doesn't fit. 3 preconditions to check per-instance: (1) already observed? (2) mechanical check? (3) code layer exists? Worked case from the wiki-save gate split.
Page: wiki/concepts/optimal-vs-blanket-rule-application.md

## [2026-07-25] ingest | Close verification evidence is scope-specific, not a universal stale-read
Source: session-2026-07-25
Agent: grok
Notes: Correct scope-specific /check verification semantics and receipt integration
Page: wiki/concepts/close-scanner-verification-gap-stale-read.md

## Wiki integration added to 7 skills (debrief, wargame, model-benchmark, tp, review, red-team)
Source: session-2026-07-25
Agent: grok
Notes: All 7 skills now have query-at-start + save-at-end wiki integration with mechanical gates. Closes the audit gap from wiki-integrated-skills-query-save-pattern. Commits 1c7fc2b + dae4e9d.
Page: multiple skills

## Causal mechanism claims require source inspection before durable write
Source: session-019f96f5
Agent: grok
Notes: Specific surface form of the receipt rule: before writing 'X happens because <mechanism>' into a durable artifact, read the source. Worked example: the close-scanner concept incident.
Page: P:/.data/wiki/concepts/causal-mechanism-claims-require-source-receipts-before-durable-write.md

## Close scanner verification gap is stale-read when /check verifiers ran
Source: session-019f96f5
Agent: grok
Notes: Scanner can't see into /check subagent transcripts → reports false VERIFICATION_GAP. Cold-start protocol: check for /check run dirs + read check-state.md before treating gap as real.
Page: P:/.data/wiki/concepts/close-scanner-verification-gap-stale-read.md

## Wiki-integrated skills: query-at-start, save-at-end pattern
Source: session-2026-07-25
Agent: grok
Notes: Audit of 36 skills. 7 with proper integration, 6 partial, 2 clear gaps (wargame, model-benchmark). /why is gold standard. Documents the 3-point pattern and refactoring sequence.
Page: wiki/concepts/wiki-integrated-skills-query-save-pattern.md

## /check design: inline-equivalence sub-signal + LangGraph vocabulary note
Source: session-2026-07-25
Agent: grok
Notes: Added 5.2.1 to /check design (PR 1 scope): inline-equivalence detection with EQUIVALENCE_CLAIM_PATTERNS regex. Added architectural vocabulary note mapping detectors→deterministic nodes, verifiers→agentic nodes, routing→conditional edges per LangGraph framing.
Page: P:/docs/designs/2026-07-25-check-orchestrator-design.md

## 3 wiki concepts from /why v3 multi-model synthesis
Source: session-019f9a89-why-v3-synthesis
Agent: grok
Notes: Captured 3 reusable design decisions from the 5-model /why synthesis: (1) multi-producer-cross-model-synthesis methodology pattern (N producers + 1 synthesizer with per-finding verification gate); (2) inline-conditional-over-dispatch principle (for skills with conditional depth, inline triggers fire on evidence; dispatch presupposes reliable Step-0 classification which is itself a closure-pressure failure mode); (3) synchronous-review-direct-write pattern (staging only earns its keep for async review; sync review IS the gate). All three pass validate_wiki_entry.py. /why v3 implementation at commit ddf793d in ~/.grok.
Page: wiki/concepts/multi-producer-cross-model-synthesis.md, wiki/concepts/inline-conditional-over-dispatch-for-skill-design.md, wiki/concepts/synchronous-review-direct-write-pattern.md

## Adaptive expansion: evidence-triggered conditional steps over pre-classification dispatch
Source: session-019f96f5
Agent: grok
Notes: Validates /why v2→v3 refactor. 3 supporting literatures: CAT/IRT, Bayesian adaptive trials, adaptive vs routine expertise. Hybrid form (fixed core + adaptive expansion) is empirically supported.
Page: P:/.data/wiki/concepts/adaptive-expansion-evidence-triggered-conditional-steps.md

## LLM Dreaming — Offline Memory Consolidation for LLM Agents
Source: session-2026-07-25
Agent: grok
Notes: Multi-source /www: 5 subagents (theory/repos/sentiment/discovery/disconfirmation). Dominant 2026 sense = async memory consolidation (Anthropic Dreams May 2026, Letta sleep-time compute, Xiaomi MiMo). Bloat is #1 failure mode. Multi-agent fleet topology (our exact pattern) is unresearched. Proposed /dream meta-skill over existing substrates with anti-bloat + identity-preservation + security gates. Disconfirmation qualified 4/5 Round-1 claims; refuted 'Reflexion plateaus' in strong form.
Page: wiki/concepts/llm-dreaming-memory-consolidation.md

## Handoff: code-orchestrates pattern workstream
Source: session-2026-07-25
Agent: grok
Notes: Bundles /close Fix 4 + /check improvements + 5 skill refactors under one pattern. LangGraph as canonical reference. Tier 1 (tactical), Tier 2 (strategic), Tier 3 (open question).
Page: P:/docs/handoffs/code-orchestrates-pattern-workstream-20260725/HANDOFF.md

## Code-orchestrates-model-judges at the skill scale
Source: session-2026-07-25
Agent: grok
Notes: Update: LangGraph is the canonical implementation. StateGraph + conditional edges map directly to our gate loop. Added LangGraph as 5th term + framework-comparison table.
Page: wiki/concepts/code-orchestrates-model-judges-skill-scale.md

## Code-orchestrates-model-judges at the skill scale
Source: session-2026-07-25
Agent: grok
Notes: /www research: micro-scale complement to macro (workflows) and meso (hooks). MindStudio deterministic+agentic nodes, DevelopersDigest control stack. 4 overlapping names for the same principle.
Page: wiki/concepts/code-orchestrates-model-judges-skill-scale.md

## Nemotron serde unsolved — wiki findability + 2026-07-25 retest
Source: session-019f9a89-nemotron-retest
Agent: grok
Notes: Documented where Nemotron spawn_subagent serialization lives (capability matrix is canonical). Status NOT SOLVED. Retest 2026-07-25 same error null expected u32 col 330 on ~90k-token assignment. Workarounds only; root cause still UNKNOWN.
Page: wiki/concepts/model-tool-calling-capability-matrix.md

## Handoff: close lighter-equivalent loophole (3 ACT_NOW from AAR)
Source: session-2026-07-25
Agent: grok
Notes: Implements the 3 structural fixes from session-019f9488 AAR: close /close self-authorization loophole, extend claims-require-receipts to equivalence claims, resolve-now default for /close gates.
Page: P:/docs/handoffs/close-lighter-equivalent-loophole-20260725/HANDOFF.md

## NotebookLM source limits free vs paid
Source: session-2026-07-25
Agent: grok
Notes: Free=50, Plus=300. Stale training data defaults to 50. Verify with capacity test.
Page: wiki/concepts/notebooklm-source-limits-free-vs-paid.md

## AAR session 019f9488 — /tp rewrite close-out
Source: session-2026-07-25
Agent: grok
Notes: Full /aar run with preprocessor packet (264 events, 108 signals). Critical finding: model self-authorized inline equivalent to skip /aar — recurring closure-pressure pathology. 7 opportunities identified, 3 ACT_NOW.
Page: P:/.artifacts/grok-aar/console_console_83b3323a-a71b-4f55-8a5d-6a41/20260725-close/aar-report.md

## Semantic clustering with bounded size
Source: session-2026-07-25
Agent: grok
Notes: HDBSCAN two-pass + KNN-assign + greedy merge; verified 4116 videos -> 15 clusters
Page: wiki/concepts/semantic-clustering-bounded-size.md

## NotebookLM CLI operational gotchas
Source: session-2026-07-25
Agent: grok
Notes: Auth recovery recipe, bulk add correction, first-URL cosmetic error
Page: wiki/concepts/notebooklm-cli-operational-gotchas.md

## Session 019f9488 retrospective — /tp rewrite, receipt system commit, domain 5 sharpening
Source: session-2026-07-25
Agent: grok
Notes: Inline /close retrospective. Three frictions: defer-to-fresh-session rationalization, dropped header mid-edit, close verdict contradicted deferrals. /tp smoke test passed.
Page: P:/docs/handoffs/session-019f9488-retrospective-20260725/RETROSPECTIVE.md

## Skill rewrite protocol: rename-fallback, cross-reference preservation, filename-collision resolution
Source: session-2026-07-25
Agent: grok
Notes: Reusable rewrite protocol validated on /tp — rename-fallback, split deep content, filename-collision resolution
Page: wiki/concepts/skill-rewrite-preserve-tested-behavior-protocol.md

## Multi-dimensional matrix as skill-design organization pattern
Source: session-2026-07-25
Agent: grok
Notes: 4D matrix pattern from /tp rewrite — lens x horizon x target x posture as organizing principle
Page: wiki/concepts/multi-dimensional-matrix-skill-organization-pattern.md

## Cognitive enforcement patterns for AI coding agents
Source: session-2026-07-25
Agent: grok
Notes: Six-category framework: epistemic checkpoints, pre-mortem, mandatory verification, language precision, destructive action gates, reasoning flaws. Derived from CLAUDE.md + AGENTS.md.
Page: P:/.data/wiki/concepts/cognitive-enforcement-patterns-for-ai-coding-agents.md

## [2026-07-25] ingest | Instruction-to-state closure gap: desired state and obligation ledgers
Source: session-2026-07-25
Agent: grok
Notes: Captured the externally researched trade-offs and selected a narrow desired-state manifest plus session-scoped obligation ledger.
Page: wiki/concepts/instruction-to-state-closure-gap-obligation-ledger.md

## intent-based-routing-for-ai-agent-skills-2026
Source: session-2026-07-25 (/www research)
Agent: grok
Notes: Validates /tp semantic intent classification approach. Industry consensus: LLM-based classification sufficient for <15 categories; cascade (keyword→embedding→SLM→LLM) needed at scale.
Page: wiki/concepts/intent-based-routing-for-ai-agent-skills-2026.md

## ai-agent-verification-orchestration-best-practices-2026
Source: session-2026-07-24/25 (/www research)
Agent: grok
Notes: Created via /www research on /check orchestrator patterns. Synthesizes Addy Osmani, Futurum/Qodo, fbakkensen, AgentGuard, Weights & Biases, and community sources.
Page: wiki/concepts/ai-agent-verification-orchestration-best-practices-2026.md

## [2026-07-24] ingest | Relevance gate before raising issues
Source: session-2026-07-24
Agent: grok
Notes: Relevance gate behavioral rule
Page: wiki/concepts/relevance-gate-before-raising-issues.md

## relevance-gate-before-raising-issues
Source: session 019f96f5
Agent: grok
Notes: Behavioral rule: filter what to raise through decision/risk/trust gate before surfacing. Prevents exhaustive low-impact reporting that creates friction.
Page: concepts/relevance-gate-before-raising-issues.md

## close-auto-invokes-aar
Source: session 019f96f5
Agent: grok
Notes: Decision: /close auto-invokes /aar (the Never-auto rule was a regression). Surfaces dirty_age.py false positive on dirty submodule working trees.
Page: concepts/close-auto-invokes-aar.md

## [2026-07-24] ingest | /close auto-invokes /aar — not optional
Source: session-2026-07-24
Agent: grok
Notes: AAR close-invocation policy reversal decision
Page: wiki/concepts/close-auto-invokes-aar.md

## integrity-authority-not-achievable-single-user
Source: session-2026-07-24
Agent: grok
Notes: Created during /close. 10/10 adversarial write vectors forge authority on single-user Windows.
Page: wiki/concepts/integrity-authority-not-achievable-single-user.md

## host-metadata-not-authoritative-for-identity
Source: session-2026-07-24
Agent: grok
Notes: Created during /close. Proven that summary.json is model-writable and cwd is not always show-toplevel.
Page: wiki/concepts/host-metadata-not-authoritative-for-identity.md

## Updated [[context-firewall-architecture]] with external validation citations (Anthropic, LangChain, FrugalGPT, RouteLLM) and script-firewall trade-offs section (7 risks with mitigations). 3 serious risks: extract-then-need mismatch, signal loss on novel content, cross-file pattern blindness. All mitigated by Layer 2 agent fallback.
Source: session-2026-07-24
Agent: grok
Notes: External research validated 3-layer pattern as standard; 2 novel pieces: script-firewall and extraction pool.
Page: P:/.data/wiki/concepts/context-firewall-architecture.md

## Created [[context-firewall-architecture]]: 3-layer dispatch pattern (extraction pool, agent pool, orchestrator). Updated [[model-pool-selection-policy-speed-quota-diversity]] domain table with tool-use, firewall-layer, and extraction pool dimensions. Added --gaps/--domain/--pool modes to model-benchmark skill. Wrote telemetry integration handoff.
Source: session-2026-07-24
Agent: grok
Notes: Firewall: DiffusionGemma primary extraction, Gemma-4-31b/Gemini-Flash-Lite fallbacks. Telemetry handoff at P:/docs/handoffs/model-telemetry-integration/HANDOFF.md
Page: P:/.data/wiki/concepts/context-firewall-architecture.md

## Updated [[model-pool-selection-policy-speed-quota-diversity]] with first measured latency data (DeepSeek 2900ms fastest vs M3 4056ms vs GLM 6744ms), 9 corrections from /tp critique + /www research, and external literature references (RouteLLM, llm-d, FrugalGPT, OmniRouter, Thompson sampling).
Source: session-2026-07-24
Agent: grok
Notes: Corrections: quality floor as Rule 0, mechanical default DeepSeek not M3, context-fit pre-check, multimodal row, code-gen needs calibration, diversity for resilience, per-provider thresholds, speed-primary is industry inversion, model-pool is our coinage.
Page: P:/.data/wiki/concepts/model-pool-selection-policy-speed-quota-diversity.md

## AI thought-partner landscape and /tp improvements
Source: /www research (minimax-search + web-search-prime, 7 queries)
Agent: grok
Notes: OpenClaw/Hermes have no critical-friend mode. MAD literature validates /tp design (cross-model, verification, single-round). Three improvements: critique memory, pre-critique triage, outcome tracking.
Page: P:/.data/wiki/concepts/ai-thought-partner-landscape-and-tp-improvements-2026.md

## Created model-pool-selection-policy-speed-quota-diversity
Source: session-2026-07-24
Agent: grok
Notes: Three-rule policy: speed+quota over free, except diversity for adversarial review. Corrects free-first default.
Page: P:/.data/wiki/concepts/model-pool-selection-policy-speed-quota-diversity.md

## Multimodal capability: all 46 models researched
Source: web research via /www (minimax-search, 11 queries)
Agent: grok
Notes: Expanded multimodal filter from 4 to all 46 models. 13 multimodal, 9 text-only, 3 conflicting. Key: GLM-5.2 text-only, Nemotron-3-Ultra text-only, MiMo V2.5 omnimodal, Gemma-4-31B accepts images, DeepSeek V4-Pro conflicting.
Page: P:/.data/wiki/concepts/model-fleet-provider-pools.md

## best-practices-enforcement-mechanism-grok-build
Source: session-2026-07-24 (/www research)
Agent: grok
Notes: Created via /www research on enforcement-mechanism design for Grok Build. Synthesizes wiki (external-state-cross-check, mandatory-step-enforcement, grok-pretooluse-deny-contract) + web (fbakkensen Stop-hook quality gates, wandb Yes-Man/correlated-validator, freecodecamp deterministic validator). Refines external-state-cross-check and mandatory-step-enforcement.
Page: wiki/concepts/best-practices-enforcement-mechanism-grok-build.md

## expected-ui-ux-features
Source: session-2026-07-24
Agent: grok
Notes: Tiered UI/UX checklist: table-stakes, good, great, web, TUI. 7 sources + WCAG 2.1. Disconfirmation: no Tier 1/2 features challenged.
Page: P:/.data/wiki/concepts/expected-ui-ux-features.md

## textual-tui-best-practices
Source: session-2026-07-24
Agent: grok
Notes: Textual TUI best practices: workers, reactive, CSS, app structure, version stability
Page: P:/.data/wiki/concepts/textual-tui-best-practices.md

## thought-partner-design-dimensions-beyond-critique
Source: session-2026-07-23
Agent: grok
Notes: Created via /www — Six Thinking Hats analysis of /tp, pattern recognition as master-coach differentiator, three new domains proposed
Page: P:/.data/wiki/concepts/thought-partner-design-dimensions-beyond-critique.md

## skill-auto-invocation-reliability
Source: session-2026-07-23
Agent: grok
Notes: Created via /www — 650-trial data on skill activation reliability, cross-host enforcement comparison
Page: P:/.data/wiki/concepts/skill-auto-invocation-reliability.md

## agentic-sdlc-skill-lifecycle-architecture
Source: session-2026-07-23
Agent: grok
Notes: Created via /www — Agentic SDLC domain classification: our skill lifecycle mapped to industry standard
Page: P:/.data/wiki/concepts/agentic-sdlc-skill-lifecycle-architecture.md

## AI Automated Test Generation Patterns
Source: session-2026-07-22
Agent: grok
Notes: /www: cross-model test generation, IDE tools benchmark, NVIDIA HEPH, Pynguin, CodiumAI, common failure modes, optimal prompts
Page: P:/.data/wiki/concepts/ai-automated-test-generation-patterns.md

## Quality Gate Hook System Implementation
Source: session-2026-07-22
Agent: grok
Notes: /wiki: documents the 4-file hook system (Stop gate + PostToolUse nudge + Session cleanup), through 2 critiques + 1 review, proven catching its own developer mid-session
Page: P:/.data/wiki/concepts/quality-gate-hook-system-implementation.md

## [2026-07-20] ingest | Mental Models for /tp and /brainstorming
Source: session-2026-07-20 (/www research on mental models for tp and brainstorming)
Agent: grok
Notes: /www research on mental models for /tp and /brainstorming. Sources: Costa & Kallick (critical friend), Chiang et al. (devil's advocate LLM), Design Council (Double Diamond), Klein (pre-mortem), Munger/Parrish (second-order thinking), Argyris (double-loop), Rosenbaum/Liu (LLM creativity research). Key findings: 3 models already implemented (critical friend, steelman/devil's advocate, double-loop). 3 missing: Double Diamond (diverge-converge for /brainstorming), pre-mortem (prospective hindsight for /tp), second-order thinking (downstream consequences for /tp).
Page: P:/.data/wiki/concepts/mental-models-for-tp-and-brainstorming.md

## [2026-07-20] ingest | Mental Models for Handoff and AAR
Source: session-2026-07-20 (/www research on mental models for handoff + AAR)
Agent: grok
Notes: /www research on mental models that help handoff and AAR. Sources: Argyris (double-loop learning), Esther Derby (double-loop in retrospectives), Boyd (OODA loop), Dodge et al. (AAR for AI), USAID AAR guide, Wharton, Grinschgl (distributed cognition), progressive disclosure/crystallization. Key finding: 3 models already implemented (progressive disclosure, progressive crystallization, cognitive offloading). 2 missing: double-loop learning (challenges assumptions, not just actions) and OODA loop (faster retrospective cycle for LITE tier). Most impactful change: add double-loop questions to AAR Phase 4.
Page: P:/.data/wiki/concepts/mental-models-for-handoff-and-aar.md

## [2026-07-20] ingest | Parallel-Safe Solution Decomposition: DSM + Critical Path + Completeness Verification
Source: session-2026-07-20 (/www research on parallel decomposition mental models)
Agent: grok
Notes: /www research on mental models for decomposing steps, finding parallelism, and verifying completeness. Sources: DSM (MIT, dsmweb.org, Sookocheff), CPM (Wikipedia), Wardley Mapping, Value Stream Mapping (Atlassian), GitHub Spec Kit. Key finding: DSM + CPM solve decomposition + parallelism; the missing piece is completeness verification — a checklist confirming the decomposed pattern retains all components. Recommendation: implement workflow completeness checks in /design, /go, /red-team.
Page: P:/.data/wiki/concepts/parallel-safe-solution-decomposition.md

## [2026-07-20] ingest | Spec-Driven Development and Harness Engineering: Ecosystem Map
Source: session-2026-07-20 (/www deep investigation of design system repos)
Agent: grok
Notes: Deep /www investigation of spec-driven development and harness engineering repos. Sources: GitHub Spec Kit (full spec-driven.md read), awesome-harness-engineering (326KB README), Addy Osmani, Augment Code, Martin Fowler/Böckeler, Alibaba open-code-review, statewright, lopopolo/harness-engineering, Loop Engineering. Key findings: our patterns validated as industry-standard; 4 techniques worth adopting from Spec Kit (constitutional gates, [NEEDS CLARIFICATION] markers, template-driven quality, specify→plan→tasks chain).
Page: P:/.data/wiki/concepts/spec-driven-development-harness-engineering-ecosystem.md

## [2026-07-20] ingest | Design Doc and Spec System Patterns: External Best Practices
Source: session-2026-07-20 (/www research on design system improvements)
Agent: grok
Notes: /www research on external design-doc/spec-generation systems. Sources: Augment Code (living specs), Addy Osmani (spec-writing guide), GitHub 2,500-repo study, Barnacle multi-agent document writing. Found 5 patterns to adopt: bidirectional spec updates, protected-decision markers, hierarchical spec summaries, cost-aware model tiering, structured decision logs. Validated 6 patterns we already do well.
Page: P:/.data/wiki/concepts/design-doc-spec-system-patterns.md

## [2026-07-22] ingest | Dead code detection workflow: vulture for Python LLM agent pipelines
Source: session-2026-07-22
Agent: grok
Notes: /www: dead code detection workflow (vulture) + Grok Build hook architecture clarification
Page: wiki/concepts/dead-code-detection-workflow.md

## [2026-07-20] ingest | Friction Detection: Operator Pushback as Mechanical Trigger Signal
Source: session-2026-07-20 (/www research on friction trigger reliability)
Agent: grok
Notes: /www research on making the /aar trigger reliable. Sources: arxiv 20,574-session study (pushback = primary misalignment signal, 41% of turns), Latitude.so (6 failure modes with detection methods). Key finding: detect operator pushback in transcript mechanically, not abstract "friction." Resolves the open question from mandatory-step-enforcement-code-over-prose.
Page: P:/.data/wiki/concepts/friction-detection-operator-pushback-as-trigger.md

## TUI Testing Strategy
Source: session-2026-07-22
Agent: grok
Notes: /www research: 4-layer testing stack for Textual TUI apps (unit + property + integration + mutation)
Page: P:/.data/wiki/concepts/tui-testing-strategy-python-textual.md

## [2026-07-20] ingest | Mandatory Step Enforcement: Move Control Flow from Prose to Code
Source: session-2026-07-20 (/www research)
Agent: grok
Notes: /www research on structural enforcement of mandatory steps. Sources: Brightlume (state machines), OpenAI (harness engineering), existing wiki (skill-enforcement-layers, skill-step-downgraded). Key finding: move enforcement from prose (advisory) to code (structural). Three patterns: state-machine guarded transitions, scanner-side gates, linter-promotion.
Page: P:/.data/wiki/concepts/mandatory-step-enforcement-code-over-prose.md

## [2026-07-20] ingest | Skill Step Downgraded from Action to Note Under Context Momentum
Source: session-2026-07-20
Agent: grok
Notes: /close retrospective gate fired correctly but the "ask operator" action was downgraded to "recommend" in summary table. Operator caught it. Same root cause as premature solutioning: prose rules don't bind under context momentum.
Page: P:/.data/wiki/concepts/skill-step-downgraded-from-action-to-note.md

## --source
Source: session-2026-07-22 (/www search tools)
Agent: --agent
Notes: grok
Page: --notes

## --source
Source: session-2026-07-22 (/www deep)
Agent: --agent
Notes: grok
Page: --notes

## TUI Frameworks for Personal Scripts
Source: session-2026-07-22
Agent: grok
Notes: /www research: Python Rich/Textual + PowerShell Terminal.Gui/ConsoleGuiTools comparison
Page: P:/.data/wiki/concepts/tui-frameworks-for-personal-scripts.md

## --source
Source: session-2026-07-22 (/www)
Agent: --agent
Notes: grok
Page: --notes

## [2026-07-22] ingest | Agent config directory taxonomy: .agents vs .grok vs .claude vs .codex
Source: session-2026-07-22
Agent: grok
Notes: /www research: agent config directory taxonomy
Page: wiki/concepts/agent-config-directory-taxonomy.md

## [2026-07-22] ingest | LLM agent token waste: 3 categories, 59% in verification, and what to detect
Source: session-2026-07-22
Agent: grok
Notes: /wiki distill: AgentDiet 3-category taxonomy + Tokenomics 59.4% + Stanford 1000x + amplification model
Page: wiki/concepts/llm-agent-token-waste-categories.md

## [2026-07-22] ingest | /check and /review are complementary, not redundant
Source: session-2026-07-22
Agent: grok
Notes: session 2026-07-21 AAR lesson L2
Page: wiki/concepts/check-vs-review-complementary-not-redundant.md

## [2026-07-22] ingest | Plan skill completeness: what makes LLM plans safe to execute
Source: session-2026-07-22
Agent: grok
Notes: /www research: plan skill completeness (O'Reilly + Plan-and-Act + Tokenomics + AgentDiet)
Page: wiki/concepts/plan-skill-completeness.md

## [2026-07-21] ingest | Git worktree best practices for multi-terminal AI fleets: do's, don'ts, alternatives
Source: session-2026-07-21 (/www compound research)
Agent: grok
Notes: Holistic worktree guide synthesizing 7 external sources (official git docs, GitButler, 5 practitioners incl. 1 large-monorepo skeptic). Confirms worktrees for multi-terminal AI fleets; documents dependency-install bottleneck, 2 conflicts (create-on-demand vs pre-warmed pool; GitButler virtual branches vs worktrees), and alternatives comparison. Fills the gap left by failure-mode-only existing concepts.
Page: wiki/concepts/git-worktree-multi-terminal-best-practices.md

## [2026-07-21] ingest | The analyst exhibits the pattern being analyzed
Source: session-2026-07-21
Agent: grok
Notes: AAR batch promotion: analyst-exhibits-pattern-being-analyzed (from multiple AAR reports)
Page: wiki/concepts/analyst-exhibits-pattern-being-analyzed.md

## [2026-07-21] ingest | Check the data on disk before deferring: calibration data may already exist
Source: session-2026-07-21
Agent: grok
Notes: AAR batch promotion: check-data-before-deferring (from multiple AAR reports)
Page: wiki/concepts/check-data-before-deferring.md

## [2026-07-21] ingest | Writing a discipline doesn't enforce it: the self-referential gap
Source: session-2026-07-21
Agent: grok
Notes: AAR batch promotion: writing-discipline-not-enforced (from multiple AAR reports)
Page: wiki/concepts/writing-discipline-not-enforced.md

## [2026-07-21] ingest | Plan mode is not a security primitive
Source: session-2026-07-21
Agent: grok
Notes: AAR batch promotion: plan-mode-not-security-primitive (from multiple AAR reports)
Page: wiki/concepts/plan-mode-not-security-primitive.md

## [2026-07-21] ingest | Multi-agent destructive git: force-push and reset --hard are categorically wrong on shared repos
Source: session-2026-07-21
Agent: grok
Notes: AAR batch promotion: multi-agent-destructive-git (from multiple AAR reports)
Page: wiki/concepts/multi-agent-destructive-git.md

## [2026-07-21] ingest | Stop_claim_gap_telemetry_probe.py — verified internal structure
Source: session-2026-07-21
Agent: grok
Notes: Verified internal structure of Stop_claim_gap_telemetry_probe.py: 371 total lines (325 non-empty), no env var reads, decision=telemetry hardcoded, dedup key includes marker.
Page: wiki/concepts/stop-claim-gap-telemetry-probe-structure.md

## [2026-07-20] ingest | Design skill's write/review loop misses framing gaps — preflight is the remedy
Source: session-2026-07-20
Agent: grok
Notes: Meta-finding from the /codex + /mmx skill design session. 4 review rounds reached 0 open issues, then a preflight (source-authority-discovery) audit found 6 real gaps: unaddressed cc-skills-ai-api alternative, mmx OAuth auth-method, Windows .cmd shim silent failure, mmx search mode, sandbox_permissions key, host: tag. The design skill should mandate preflight before the first write round. ADR-009 documents the full design; this concept captures the structural finding about the design skill itself.
Page: wiki/concepts/design-skill-preflight-gap.md

## [2026-07-20] ingest | CLI canonical invocation silently does the wrong thing — a failure class
Source: session-2026-07-20
Agent: grok
Notes: Three instances observed during /codex + /mmx skill smoke-testing: (1) codex review inherits danger-full-access from config.toml, (2) mmx --quiet strips JSON wrapper from --output json, (3) bare mmx on Windows fails via .cmd shim. All share the structure: help text suggests invocation X, X looks correct in code review, X silently produces wrong results at runtime. Only runtime smoke-tests catch these. The /mmx PR 3 smoke-test caught 3 bugs that 4 design review rounds missed.
Page: wiki/concepts/cli-canonical-invocation-silent-failure-class.md

## [2026-07-20] ingest | Skill rename propagation checklist
Source: session-2026-07-20
Agent: grok
Notes: 10-step checklist extracted from renaming source-authority-discovery → preflight. Touches: primary skill dir (git mv), plugin mirror (git mv in submodule), SKILL.md frontmatter+body, workspace constitution (CLAUDE.md), plugin constitution, consumer skills (wargame/tp/grok-discovery), consumer scripts (run_discovery.ps1), contract tests, ADR references. Historical artifacts (audit JSONs, session state) intentionally left as point-in-time records. Both contract tests pass after rename.
Page: wiki/concepts/skill-rename-propagation-checklist.md

## [2026-07-21] ingest | Recurring thinking errors: solution-vending, premature convergence, goal-assumption, inference-as-fact, prior-output anchoring
Source: session-2026-07-21
Agent: grok
Notes: operator-directed after multiple thinking errors recurred in a single session. Three of seven overlap with /tp modes 1/4/6; two (#2 premature convergence, #5 prior-output anchoring) are not named elsewhere. Page is operational — each error has a concrete instance, correction, and falsifier. Future sessions should use the 7-point check list in §"How a future session should use this page" before sending multi-option or multi-item responses.
Page: wiki/concepts/recurring-thinking-errors.md

## [2026-07-21] ingest | Skill quick-fit screening: a 30-second triage before skill execution
Source: session-2026-07-21
Agent: grok
Notes: session 2026-07-21 /wiki ingest
Page: wiki/concepts/skill-quick-fit-screening-pattern.md

## [2026-07-21] ingest | Skill path resolution gotcha: Grok skills can live in multiple scopes
Source: session-2026-07-21
Agent: grok
Notes: session 2026-07-21 /wiki ingest
Page: wiki/concepts/skill-path-resolution-gotcha.md

## [2026-07-21] ingest | On Windows Git Bash, git invokes hooks via shebang line — executable bit not required
Source: session-2026-07-21
Agent: grok
Notes: Session 019f8507 distilled: Windows Git Bash invokes hooks via shebang line, not executable bit (refutes ccr-ornith false positive)
Page: wiki/concepts/windows-gitbash-hook-invocation.md

## [2026-07-21] ingest | Tool Use Protocol for Subagent Critical-Friend Critique
Source: session-2026-07-21
Agent: grok
Notes: session 2026-07-21 /wiki ingest
Page: wiki/concepts/tool-use-protocol-subagent-critical-friend.md

## [2026-07-21] ingest | Git mv + search_replace: the 0/0 commit that loses your content changes
Source: session-2026-07-21
Agent: grok
Notes: Session 019f8507 distilled: git mv + search_replace produces 0/0 commit that loses content changes
Page: wiki/concepts/git-mv-search-replace-capture-bug.md

## [2026-07-20] update | Plausible narratives substitute for verification
Source: session-2026-07-20
Agent: grok
Notes: added disguise variants section (4 disguises); merge from session-2026-07-20
Page: wiki/concepts/plausible-narratives-substitute-for-verification.md

## [2026-07-20] ingest | Grok permission deny rules as cross-host protection
Source: session-2026-07-20
Agent: grok
Notes: grok permission deny rules as cross-host protection; config pattern for protecting .claude/ from .grok/
Page: wiki/concepts/grok-permission-deny-rules-cross-host-protection.md

## [2026-07-20] ingest | Evidence-first default: empowerment over prohibition for needless-confirmation
Source: session-2026-07-20
Agent: grok
Notes: evidence-first default: empowerment over prohibition; research synthesis (dev.to + arxiv + Anthropic)
Page: wiki/concepts/evidence-first-default-and-needless-confirmation.md

## [2026-07-20] ingest | Handoff skill v0.1.1: scope-bounds, falsifier-strength, assignment fields
Source: session-2026-07-20
Agent: grok
Notes: handoff skill v0.1.1: 4 validators (scope-bounds, falsifier-strength, assignment-fields, heading-match), fleet-coordination frontmatter
Page: wiki/concepts/handoff-skill-v011-validators.md

## [2026-07-20] ingest | Host-surface boundary: which trees are mine to edit
Source: session-2026-07-20
Agent: grok
Notes: host-surface boundary: which trees are mine to edit; permission deny rules as mechanical guard
Page: wiki/concepts/host-surface-boundary.md

## [2026-07-20] ingest | Wiki Lifecycle State File: Design, Tests, and Gaps
Source: session-2026-07-20
Agent: grok
Notes: lifecycle design + honest gap list
Page: wiki/concepts/wiki-lifecycle-state-file.md

## [2026-07-20] ingest | Verification-Before-Completion: Cross-Host Operator Principle
Source: session-2026-07-20
Agent: grok
Notes: session-2026-07-20 ingest (cross-host content)
Page: wiki/concepts/verification-before-completion-principle.md

## [2026-07-20] ingest | Plan-Then-Execute and Other LLM Agent Design Patterns (Beurer-Kellner et al., 2025)
Source: session-2026-07-20
Agent: grok
Notes: session-2026-07-20 ingest (cross-host content)
Page: wiki/concepts/plan-then-execute-pattern.md

## [2026-07-20] ingest | AI Agent Oversight Without Explainability Is a Rubber Stamp
Source: session-2026-07-20
Agent: grok
Notes: session-2026-07-20 ingest (cross-host content)
Page: wiki/concepts/agent-oversight-rubber-stamping.md

## [2026-07-20] ingest | AI Agent Failure Modes Beyond Hallucination (Saplin, 2026)
Source: session-2026-07-20
Agent: grok
Notes: session-2026-07-20 ingest (cross-host content)
Page: wiki/concepts/agent-failure-modes-2026.md

## [2026-07-20] ingest | Web and Social Research State in 2026: Free Tiers, Maintained Tools
Source: session-2026-07-20
Agent: grok
Notes: session-2026-07-20 ingest
Page: wiki/concepts/web-research-state-2026.md

## [2026-07-20] ingest | Grok Build Compat Layer Does Not Surface Marketplace Plugin-Bundled Skills
Source: session-2026-07-20
Agent: grok
Notes: session-2026-07-20 ingest
Page: wiki/concepts/grok-build-compat-layer-marketplace-plugin-skills.md

## [2026-07-20] ingest | Grok Build's `~/.grok/disabled-hooks` Per-Hook Disable Layer
Source: session-2026-07-20
Agent: grok
Notes: session-2026-07-20 ingest
Page: wiki/concepts/grok-build-disabled-hooks-per-hook-layer.md

## [2026-07-20] ingest | Grok Build cc-aca-* Enforcement Suite IS Active — Verified via Inspect
Source: session-2026-07-20
Agent: grok
Notes: session-2026-07-20 ingest
Page: wiki/concepts/grok-build-cc-aca-actually-enabled.md

## [2026-07-20] ingest | Plan Mode in Grok Build is Structured-Thinking, Not a Security Sandbox
Source: session-2026-07-20
Agent: grok
Notes: session-2026-07-20 ingest
Page: wiki/concepts/grok-build-plan-mode-structured-thinking.md

## [2026-07-19] ingest | Multi-agent review: attack correlated errors, not persona diversity
Source: session-2026-07-19
Agent: grok
Notes: Correlated-errors lens for multi-agent review; frame-diversity + falsifier-gating + orthogonal-model critic
Page: wiki/concepts/multi-agent-correlated-errors.md

## [2026-07-19] ingest | Examples over rules — escape hatch for tacit knowledge that resists encoding
Source: session-2026-07-19
Agent: grok
Notes: Examples-over-rules escape hatch; tacit knowledge technique from Hormozi video review
Page: wiki/concepts/examples-over-rules-escape-hatch.md

## [2026-07-19] ingest | ADR (2026-05-12): Prompt Clarification & Context Augmentation Plugin (Two-Tier)
Source: session-2026-07-19
Agent: grok
Notes: Imported ADR; source=P:/.claude/arch_decisions/2026-05-12_fast_prompt-enhancement-bridge.md
Page: wiki/concepts/prompt-enhancer-clarification-bridge.md

## [2026-07-19] ingest | ADR-008: Concurrent-Session Worktree Isolation
Source: session-2026-07-19
Agent: grok
Notes: Imported ADR; source=P:/docs/adrs/ADR-008-concurrent-session-worktree-isolation.md
Page: wiki/concepts/concurrent-session-worktree-isolation.md

## [2026-07-19] ingest | ADR-007: Pre-Proposal Contract-and-Value Gate for Cross-Component Mechanism Changes
Source: session-2026-07-19
Agent: grok
Notes: Imported ADR; source=P:/docs/adrs/ADR-007-pre-proposal-contract-and-value-gate.md
Page: wiki/concepts/pre-proposal-contract-and-value-gate.md

## [2026-07-19] ingest | ADR-006: Compact Handoff — Add Verbatim Last User Message Field
Source: session-2026-07-19
Agent: grok
Notes: Imported ADR; source=P:/docs/adrs/ADR-006-compact-handoff-verbatim-field.md
Page: wiki/concepts/compact-handoff-verbatim-last-user-message.md

## [2026-07-19] ingest | ADR-004: /recap Handoff-First Path Resolution
Source: session-2026-07-19
Agent: grok
Notes: Imported ADR; source=P:/docs/adrs/ADR-004-recap-path-resolution-strategy.md
Page: wiki/concepts/recap-path-resolution-strategy.md

## [2026-07-19] ingest | ADR-003: Enhance /recap Session Reconstruction — Three-Bug Fix
Source: session-2026-07-19
Agent: grok
Notes: Imported ADR; source=P:/docs/adrs/ADR-003-recap-session-reconstruction.md
Page: wiki/concepts/recap-session-reconstruction-three-fixes.md

## [2026-07-19] ingest | ADR-002: Hybrid Compile-Upfront + RAG Architecture for search-research
Source: session-2026-07-19
Agent: grok
Notes: Imported ADR; source=P:/docs/adrs/ADR-002-search-research-optimal-architecture.md
Page: wiki/concepts/search-research-hybrid-compile-upfront-rag.md

## [2026-07-19] ingest | ADR (2026-04-08): TLDR Summary Data Source — Use Handoff V2 Envelope
Source: session-2026-07-19
Agent: grok
Notes: Imported ADR; source=P:/docs/adrs/20260408_cli_tldr_data_source.md
Page: wiki/concepts/tldr-handoff-data-source.md

## [2026-07-19] ingest | ADR (2026-04-11): Absorb Episodic-Memory into search-research CHS Backend
Source: session-2026-07-19
Agent: grok
Notes: Imported ADR; source=P:/docs/adrs/2026-04-11_fast_episodic-memory-consolidation.md
Page: wiki/concepts/episodic-memory-consolidation-into-search-research.md

## [2026-07-19] ingest | ADR (2026-04-07): Hook-Based Detection for Proposal-Decision Conflation
Source: session-2026-07-19
Agent: grok
Notes: Imported ADR; source=P:/docs/adrs/2026-04-07_fast_proposal-decision-conflation-hook.md
Page: wiki/concepts/proposal-decision-conflation-hook.md

## [2026-07-19] ingest | Parallel worktree config.lock contention (claude-code #34645)
Source: https://github.com/anthropics/claude-code/issues/34645
Agent: grok
Notes: New finding surfaced during multi-terminal git optimization review. Closed-as-not-planned upstream bug: 3+ parallel Agent tool calls with isolation: "worktree" on Windows race for .git/config.lock. Distinguishes config.lock (worktree operations) from index.lock (staging area) covered in git-index-lock-concurrent-access-recovery. Workarounds: pre-create worktrees serially in main thread, cap parallel worktree-isolated agents at ≤2, or flock .git/config.lock. Marks ADR-008's write-lease-gate writeup as adjacent but covering file-level lock, not git-level lock. Host: claude (bug in Claude Code Agent tool).
Page: wiki/concepts/parallel-worktree-config-lock-contention-claude-code-34645.md

## [2026-07-19] ingest | Multi-terminal git coordination primitives (beyond isolation)
Source: session-2026-07-19
Agent: grok
Notes: New finding surfaced during multi-terminal git review. Wiki has strong coverage of *isolation* primitives (per-worktree cwd, terminal-scoped artifacts, grok-safe-git preflight, worktree-root policy hook) but no coverage of *coordination* primitives for integrating parallel work back into shared branches. Closes the gap with three concrete primitives: git rerere enabled true, rebase-each-feature-on-main-before-merge, one-terminal-owns-main convention. Multi-source-verified (Augment guide, Phoenix article, git's own rerere docs, branch-exclusivity invariant). Host: both (primitives are git-level, not platform-specific). EVIDENCE_GAP: rerere scope (per-repo vs global) not measured on P:\ corpus.
Page: wiki/concepts/multi-terminal-git-coordination-primitives.md


## [2026-07-19] ingest | QMD CLI syntax differs by subcommand: update takes positional, search/status take --collection
Source: session-2026-07-19
Agent: grok
Notes: Per-subcommand syntax mismatch in `qmd`. `qmd update --collection wiki` errors with "unrecognized arguments" — correct is `qmd update wiki` (positional). `qmd search` and `qmd status` use `--collection` flag correctly. Three doc instances fixed (two handoffs). Important framing: the corpus-redundancy conclusion from earlier this session was NOT invalidated by this error — the author caught and corrected the syntax before running the test, and this-session re-test with fresh index confirmed auto-link still returns empty. Meta-lesson: verify CLI syntax via `--help` before documenting; also, doc errors do not automatically invalidate downstream tests (require verifying the wrong syntax was actually used in the test).

**[SUPERSEDED 2026-07-25]** The above entry documents `qmd update` as a real command. It does not exist in qmd 0.1.2 — `qmd --help` shows only `search`, `collection`, `document`. The referenced concept `qmd-cli-syntax-differs-by-subcommand.md` was never created. The "positional vs flag" distinction was either against a different qmd version or was a hallucinated command. The current qmd API uses `qmd document add` for indexing (per-document, not bulk `update`). This correction surfaced during session-20260725 /why investigation of crawl4ai qmd integration failures. The corpus-redundancy conclusion noted above stands; only the qmd command documentation was wrong.
Page: wiki/concepts/qmd-cli-syntax-differs-by-subcommand.md (NEVER CREATED — dangling reference)

## [2026-07-19] ingest | Grok Build /export derives filename from session title, not the argument
Source: session-2026-07-19
Agent: grok
Notes: Host-level filename derivation. `/export Web.md` in a session titled "Wiki" produced `Wiki-Web-Red.md`, not `Web.md`. Verified via session `019f7b37` metadata + file inspection. No config knob controls this; workarounds are `/copy`+agent-write or rename session. Answers user's actual question this session.
Page: wiki/concepts/grok-build-export-filename-derives-from-session-title.md

## [2026-07-19] ingest | Gitleaks stdin-scan reports File='' — .gitleaksignore path suppression cannot match
Source: session-2026-07-19
Agent: grok
Notes: Hook at `.githooks/pre-commit` was running `git diff --cached | gitleaks stdin`, producing findings with empty File field. Path-based `.gitleaksignore` cannot match empty path. Fixed by iterating staged files and invoking `gitleaks detect --source <path> --no-git` per file. Verified end-to-end: previously-blocked commit passed after fix. Upstream issue gitleaks#1051 confirms. Both hosts affected (git-level hook).
Page: wiki/concepts/gitleaks-stdin-scan-empty-file-field-breaks-ignore.md

## [2026-07-19] ingest | Schema-as-constitution: single convention source for multi-agent shared wikis
Source: session-2026-07-19
Agent: grok
Notes: Architectural decision to resolve dual-source drift between Grok-side and Claude-side wiki SKILL.md files. Created P:/.data/wiki/SCHEMA.md as single convention source; both SKILL.md files rewritten as thin orchestrators. Boundary: policy in SCHEMA.md, procedure in SKILL.md. First compression was over-aggressive (lost YouTube chain, tier UI, Update phases); critical review caught it, procedure restored.
Page: wiki/concepts/wiki-schema-as-constitution.md

## [2026-07-19] ingest | Subagent silent no-write: agent reports file path without invoking write tool
Source: session-2026-07-19
Agent: grok
Notes: Failure mode observed during /red-team self-review. red-team-failure-modes specialist returned expected file path but never invoked write tool. 6 tool calls, 0 writes. Findings (3 BLOCK + 3 REVISE) recoverable from thinking-transcript only. Orchestrator had no post-dispatch Test-Path verification. Fix documented as Priority 1 in P:/docs/red-team-workflow-reliability-handoff-2026-07-19.md. Incident logged as inc-48fd0ac31fb7.
Page: wiki/concepts/subagent-silent-no-write-failure.md

## [2026-07-19] update | Schema-as-constitution: SCHEMA.md created; both SKILL.md files become thin orchestrators
Source: session-2026-07-19
Agent: grok
Notes: Architectural decision executed. Created P:/.data/wiki/SCHEMA.md (224 lines) as the single source of truth for wiki conventions (page format, frontmatter fields including verification: and cognitive_load, quality gate, link density, log protocol, typed wikilinks, operations overview, recommended cadence, evidence principles, key principles). Both SKILL.md files rewritten as thin per-host orchestrators that reference SCHEMA.md: Grok-side 261→59 lines (-77%), Claude-side 531→170 lines (-68%). Plugin cc-skills-sdlc bumped 1.0.230→1.0.232, cache rebuilt, zero drift confirmed. Resolves the dual-source drift problem identified during red-team self-review (WRF-001). Both hosts now read the same convention source; per-host orchestration (manifest pipeline, signal-extract, /main --fix automation) stays in each SKILL.md.
Pages: P:/.data/wiki/SCHEMA.md (new), ~/.grok/skills/wiki/SKILL.md (rewrite), P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/wiki/SKILL.md (rewrite + plugin-mutation)

## [2026-07-19] update | B-lite session closure — handoff acceptance recorded
Source: session-2026-07-19
Agent: grok
Notes: B-lite execution closed at `~/.grok/skills/wiki/SKILL.md` (3 edits: verification frontmatter convention at L106, link density advisory at L149, recommended cadence at L254) + `P:/.data/wiki/concepts/claude-code-on-windows-moc.md` (MOC + future-session observation hook) + `P:/.data/wiki/qmd-baseline-2026-07-19.json` (top-1 score 0.083 with 1044 docs). Handoff items 4-5 captured as deliverables at `P:/docs/red-team-workflow-reliability-handoff-2026-07-19.md` and `P:/docs/web-search-tools-and-pkm-research-handoff-2026-07-19.md`. Both handoffs contain the planning, decision criteria, and prioritized next-steps for any future session; they are **not pending execution** in this session — they are durable records. Tool-fallbacks.md row added for the `web_search` 429-on-parallel-batches failure observed under MiniMax-M3 (cross-confirms the existing GLM-5.2 row from 2026-07-18; documents the MCP alternatives `minimax-search__web_search` and `web-search-prime__web_search_prime`).

## [2026-07-19] ingest | Claude Code on Windows — Map of Content (MOC) hub page
Source: session-2026-07-19
Agent: grok
Notes: First MOC (Map of Content) in the vault. Hub for 6 cross-cutting Windows + Claude Code pages (claude-code-windows-11-config, claude-code-windows-11-fixes, claude-code-export-drive-root-perm-bug, windows-onedrive-readonly-marker, windows-cross-process-file-locking, openai-codex-windows-11-troubleshooting). Created during wiki discoverability B-lite execution. Wiki auto-link returned empty neighbors (consistent with QMD corpus ceiling at 0.083; baseline fingerprint captured at P:/.data/wiki/qmd-baseline-2026-07-19.json). Per Karpathy LLM-Wiki reviewers, MOCs are the highest-leverage remediation when semantic search degrades — this page is an instance of that pattern.
Page: wiki/concepts/claude-code-on-windows-moc.md

## [2026-07-19] update | OneDrive-EPERM cluster pages — v2.1.163 fix landscape + scope relabel + auto-link corpus reality
Source: session-2026-07-19
Agent: grok
Notes: Disconfirmation search surfaced Claude Code v2.1.163 changelog entry fixing the session-env mkdir path with the OneDrive-ReadOnly pattern. The parent-of-export-target mkdir we reproduced is a DIFFERENT call-site not in the v2.1.163 fix, so the route-around workaround still holds for users on current versions. Updated both pages: added version-specific fix landscape section, expanded GitHub issue set (#30928, #50773, #50886, #62140, #65229 added), explicit scope-note on the OneDrive page that other surfaces (agent-cache, marketplace, Write tool) are inferred not locally reproduced. Auto-link returned empty neighbors four runs in a row; investigation showed QMD max relevance score 0.083 even on known-topic queries ("AGENTS.md hard rules", "plan mode", "slash command") with most hits being unrelated noise from sources/. Auto-link is correctly no-op'ing on a corpus where semantic similarity is below threshold; not a bug, but a corpus-coverage artifact worth noting if wiki discoverability becomes important.
Pages: wiki/concepts/windows-onedrive-readonly-marker.md (update), wiki/concepts/claude-code-export-drive-root-perm-bug.md (update)

## [2026-07-19] ingest | Windows OneDrive Files On-Demand ReadOnly marker — Claude Code mkdir failures and the diagnostic probe
Source: session-2026-07-19
Agent: grok
Notes: New concept page (split out from claude-code-export-drive-root-perm-bug.md because the OneDrive marker class affects /export AND agent-cache AND marketplace installs AND Write-tool). Carries the `attrib` + `(Get-Item).Attributes` diagnostic probe locally verified 2026-07-19 (C:\Users\brsth\Downloads R set; C:\Users\brsth\.claude, P:\, P:\.claude all clean). Pages cross-link both ways.
Page: wiki/concepts/windows-onedrive-readonly-marker.md

## [2026-07-19] update | Claude Code `/export` mkdir failures on Windows — verified workaround + second symptom (EEXIST/OneDrive)
Source: session-2026-07-19
Agent: grok
Notes: Substantial update. EVIDENCE_GAP closed: workaround verified locally — file landed at P:/.claude/exports/2026-07-19-session.md (198,185 bytes, 3,087 lines, mtime 2026-07-19 06:58:05). Added second symptom class (EEXIST on OneDrive-ReadOnly parents), OneDrive Files On-Demand ReadOnly marker as upstream cause, `attrib`/`(Get-Item).Attributes` diagnostic probe, GitHub issues #31030/#31398/#37306/#59622 as sibling evidence, and a diagnostic quick-reference table. Diagnostic probe verified locally: C:\Users\brsth\Downloads attrs=ReadOnly,Directory,Archive; P:\.claude no R flag.
Page: wiki/concepts/claude-code-export-drive-root-perm-bug.md

## [2026-07-19] ingest | Claude Code `/export` fails with EPERM mkdir at drive-root CWD
Source: session-2026-07-19
Agent: grok
Notes: Workaround: pass explicit filename to /export; confirmed via code.claude.com docs + anthropics/claude-code#20139 (closed as not planned). EVIDENCE_GAP: workaround not locally tested; both sources verified by web_fetch this session.
Page: wiki/concepts/claude-code-export-drive-root-perm-bug.md

## [2026-07-18] ingest | Grok marketplace-cache is third-party plugins, not Grok host source
Source: session-2026-07-18
Agent: grok
Notes: `~/.grok/marketplace-cache/<hash>/` is third-party plugin code, not Grok's runtime. `b975999a270027c6` is `thedotmack/claude-mem` v13.11.0. Grok's runtime is closed-source binary at `~/.grok/bin/grok.exe`. Always read `package.json` before citing any file under a cache directory as host authority.

## [2026-07-18] ingest | Source-authority confabulation from cache directories
Source: session-2026-07-18
Agent: grok
Notes: Distinct confabulation subclass — reading cache-dir source with host-matching filenames (`HookResult`, `types.ts`, `adapters/`) and concluding it is host authority when it is a third-party plugin's internal abstraction. Worse than ordinary confabulation because it survives "did you verify?" self-checks. Fix: read `package.json` first to identify the package.

## [2026-07-18] ingest | Grok memory workspace sharing conflicts with multi-terminal isolation
Source: session-2026-07-18
Agent: grok
Notes: Grok workspace memory (`~/.grok/memory/<project-slug>-<hash8>/MEMORY.md`) is shared across all same-project terminals/worktrees (keyed on git origin). Conflicts with the binding multi-terminal isolation invariant on all four properties. Memory is disabled by default as of 2026-07-18; enabling requires override conditions or mitigations (disable `/dream` auto-consolidation, single-writer discipline, etc.).

## [2026-07-18] update | Grok Build Hook Host Ceiling and Mechanics (correction)
Source: session-2026-07-18
Agent: grok
Notes: Corrected prior version that cited `thedotmack/claude-mem` source as "Grok runner." Struck all `marketplace-cache/b975999a270027c6/` citations. Marked passive-surfacing mechanism UNVERIFIED pending probe at `~/.grok/hooks/probe-passive-surface.json`. Added "common mistake #3" (citing marketplace-cache as Grok source). Demoted host-asymmetry table to confidence-graded with Grok passive surfacing as UNVERIFIED.

## [2026-07-16] ingest | Workflow: File-Name-Becomes-Slash-Command
Source: session-2026-07-16
SHA256: none (session-derived)

## [2026-07-16] ingest | Check Duplication: Prior Evidence Reused Without Fresh Execution
Source: session-2026-07-16
SHA256: none (session-derived)

## [2026-07-16] ingest | Hook Types: UserPromptSubmit exists but UserPromptExpansion does not
Source: session-2026-07-16
SHA256: none (session-derived)

## [2026-07-16] ingest | Workflow Pipeline/Parallel Barrier Discipline
Source: session-2026-07-16
SHA256: none (session-derived)

## [2026-07-16] ingest | Check Skill-to-Workflow Naming Collision Resolution
Source: session-2026-07-16
SHA256: none (session-derived)
Content: yt-dlp flat/non-flat playlist export, --playlist-end pagination fix for 4900+ entries, PowerShell + Python API extraction patterns
Page: wiki/concepts/export-youtube-playlist-urls-via-yt-dlp.md

## [2026-05-10] ingest | GitHub Hook Repos
Source: web research
SHA256: newly-created-2026-05-10
Content: disler/claude-code-hooks-mastery, karanb192/claude-code-hooks (368 stars), anipotts/claude-code-tips - practical patterns for hooks
Page: wiki/sources/github/claude-code-hooks-repos.md

## [2026-05-10] ingest | HTTP Hooks + External LLM Integration
Source: web research
SHA256: newly-created-2026-05-10
Content: Python HTTP server pattern for invoking external LLMs (OpenAI, Anthropic) via HTTP hooks - architecture, Flask/FastAPI examples, use cases
Page: wiki/sources/hooks/http-hooks-external-llm.md

## [2026-05-10] ingest | MCP vs HTTP Hooks Comparison
Source: web research
SHA256: newly-created-2026-05-10
Content: Decision framework for when to use MCP tool hooks vs HTTP hooks - latency, reliability, scalability tradeoffs
Page: wiki/sources/hooks/mcp-vs-http-hooks.md

## [2026-05-10] ingest | Code + External LLM via Bifrost
Source: code-analysis
SHA256: newly-created-2026-05-10
Content: Working pattern: Stop_semantic_critic.py uses bf_agent.py for external LLM evaluation via Bifrost proxy - bifrost_call(), provider routing, fail-open error handling
Page: wiki/sources/hooks/code-external-llm-via-bifrost.md

## [2026-05-10] ingest | External LLM Patterns Comparison
Source: code-analysis
SHA256: newly-created-2026-05-10
Content: Three patterns: disler_utils SDK (in-context), Bifrost bf_agent (out-of-context multi-provider), HTTP hooks (separate server) - decision framework, tradeoffs
Page: wiki/sources/hooks/external-llm-patterns-comparison.md

## [2026-05-10] ingest | MiniMax M2.7 Tutorial (Unsloth)
Source: web crawl
SHA256: c95a6f2e8d3b1a4c
Content: MiniMax M2.7 model tutorial on Unsloth - architecture, training, fine-tuning guide
Page: wiki/sources/unsloth.ai/minimax-m27.md

## [2026-05-10] ingest | Groq API Documentation
Source: web crawl
SHA256: a4e8f2c1b3d5a7e9
Content: Groq API docs - LPU inference, model endpoints, API usage, rate limits
Page: wiki/sources/groq.com/docs.md

## [2026-05-10] ingest | GLM-5 GitHub Repository
Source: web crawl
SHA256: 7f2a4e8c1b3d5e9a
Content: GLM-5 open source repository - architecture, API, capabilities
Page: wiki/sources/github.com/zai-org__GLM-5.md

## [2026-05-10] ingest | Mistral AI Cookbook
Source: web crawl
SHA256: 3d8a1e5f7c2b4a9e
Content: Mistral AI cookbook - code examples, fine-tuning, deployment patterns
Page: wiki/sources/github.com/mistralai__cookbook.md

## [2026-05-10] ingest | Cerebras Cookbook
Source: web crawl
SHA256: 9c4e2a7f1b3d5e8a
Content: Cerebras cookbook - fast inference, LLM acceleration patterns
Page: wiki/sources/github.com/buildfastwithai__Cerebras-Cookbook.md

## [2026-05-10] ingest | Google Gemini Cookbook
Source: web crawl
SHA256: 2b7f9a3e5c1d4e8a
Content: Google Gemini cookbook - API usage, multimodal capabilities, code examples
Page: wiki/sources/github.com/google-gemini__cookbook.md

## [2026-05-10] ingest | Bifrost Repository
Source: web crawl
SHA256: 8f2a4e1c3b5d7e9a
Content: Maxim AI Bifrost repository - multi-model orchestration, agent framework
Page: wiki/sources/github.com/maximhq__bifrost.md

## [2026-05-10] ingest | Anthropic Python SDK
Source: web crawl
SHA256: 1a3c5e7f9b2d4e8a
Content: Anthropic Python SDK for Claude API - messages, streaming, async patterns
Page: wiki/sources/github.com/anthropics__anthropic-sdk-python.md

## [2026-05-10] ingest | Mistral Python Client
Source: web crawl
SHA256: 5e8a2c4f6b1d3e7a
Content: Mistral AI Python client - model access, chat completions, async support
Page: wiki/sources/github.com/mistralai__client-python.md

## [2026-05-10] ingest | OpenAI Python SDK
Source: web crawl
SHA256: 9d3a5e7f1b2c4e8a
Content: OpenAI Python SDK - chat completions, assistants, batch processing
Page: wiki/sources/github.com/openai__openai-python.md

## [2026-05-10] ingest | Pydantic AI
Source: web crawl
SHA256: 4e7a1c3f5b2d8e9a
Content: Pydantic AI - type-safe LLM interaction with Pydantic validation
Page: wiki/sources/github.com/pydantic__pydantic-ai.md

## [2026-05-10] ingest | HTTPX
Source: web crawl
SHA256: 2c5e8a1f3b7d4e9a
Content: HTTPX - async HTTP client for Python - API patterns, streaming
Page: wiki/sources/github.com/encode__httpx.md

## [2026-05-10] ingest | LangGraph
Source: web crawl
SHA256: 7f1a3c5e9b2d4e8a
Content: LangGraph - orchestration framework for LLM agents, workflow patterns
Page: wiki/sources/github.com/langchain-ai__langgraph.md

## [2026-05-10] ingest | Claude Code Starters
Source: web crawl
SHA256: 3b5e7a1f4c2d8e9a
Content: Anthropic Claude Code starter projects - hooks, skills, integrations
Page: wiki/sources/github.com/anthropics__claude-code-starters.md

## [2026-05-10] ingest | disler_utils Direct SDK Integration
Source: code-analysis
SHA256: newly-created-2026-05-10
Content: Lightweight Python utilities for direct LLM API calls - anth.py (Anthropic), oai.py (OpenAI), summarizer.py example - currently unused by active hooks
Page: wiki/sources/hooks/disler-utils-direct-sdk.md

## [2026-05-09] ingest | Claude Code Hook Implementations (real-world)
Source: research synthesis from dev.to article + ksred.com
SHA256: 31461da81915aa35bcef74ab4ce944e232e5c781eb53edbb1f4ab48e9cb96844
Content: 5 popular command hooks from 108h autonomous operation — error-gate, no-ask-human, session-start-marker, cdp-safety-check, activity-logger
Page: wiki/concepts/hooks-real-world-impl.md

## [2026-05-09] ingest | Claude Code Hooks Reference (code.claude.com)
Source: https://code.claude.com/docs/en/hooks
SHA256: a1b2c3d4e5f6 (placeholder - compute from actual file)
Content: Official hooks docs — 5 hook types (command, http, mcp_tool, prompt, agent), full event reference, I/O protocol, env vars, async hooks, MCP matching
Page: wiki/sources/code.claude.com/hooks-reference.md

## 2026-05-06
## [2026-05-06] ingest | Claude Code Hooks Reference v3.1
Source: P:/.claude/docs/claude-hooks-v3.1.md
SHA256: 98ba34235c5b029447792a982cbd3a26d69ff7cd6b7f89684cbec31ef98ab16f
Content: Authoritative hooks reference â€” 27 events, 4 hook types, schemas, matchers, exit codes, component-scoped hooks
Page: wiki/sources/hooks/claude-hooks-v3.1.md

## 2026-04-10
- Vault restored from backup
- Obsidian GUI unavailable (indexing hang on Windows 11)
- Wiki structure initialized: wiki/concepts/, wiki/entities/, wiki/comparisons/
- Sources restored from sources.bak

## [2026-04-10] ingest | /learn Skill Scoring Breakdown Fix - Summary

## [2026-04-12] ingest | Claude Code Skill Failure Patterns
Source: Perplexity analysis of yt-channel skill execution failures
Content: Top 10 failure patterns, PVE/SALT frameworks, context degradation mitigation
Page: wiki/concepts/claude-code-skill-failure-patterns.md

## [2026-04-12] ingest | NotebookLM Markdown Exporter
Source: Downloads/notebooklm_exporter.py + USAGE_GUIDE.md
Content: Playwright-based browser automation script for exporting NotebookLM notebooks to Markdown
Page: wiki/entities/notebooklm-exporter.md

## [2026-04-12] ingest | yt-is NotebookLM Pipeline Improvements
Source: Perplexity analysis "Can you think of gaps or opportunities to improve this pipeline"
Content: 6-month roadmap: failure taxonomy, quota-aware behavior, non-Google fallbacks, operational UX
Page: wiki/concepts/yt-is-notebooklm-pipeline-improvements.md

## [2026-04-13] ingest | Are there repos or solutions to claude code getting
## [2026-04-13] ingest | hook to enforce discovery be
## [2026-04-13] ingest | solo operator adr best practices
## [2026-04-13] ingest | Python Behavior Tree Framework for Autonomous LLM Agents
## [2026-04-13] ingest | YouTube restricts History (HL)
## [2026-04-13] ingest | Does it make sense NO My recent changes

## [2026-04-18] ingest | skill-review-failure
Source: ~/Downloads/hooks_implementation_plan 1.md
Content: Claude Code loaded ai-gemini skill but applied ACG framework to own reasoning instead of running Gemini CLI. /truth caught false claim.
Page: wiki/entities/skill-review-failure.md
Hash: 9dc4017ea688c8af1afd6dc1fa01767ddd44c5759f37dfeb9f24d07947d5c585

## [2026-04-18] ingest | hooks-implementation-plan
Source: ~/Downloads/hooks_implementation_plan 0.md
Content: Phase 0-2 plan: reduce PreToolUse latency, consolidate Stop-layer, add UserPromptSubmit helpfulness. Preserves dispatch-chain integrity and fail-open invariants.
Page: wiki/concepts/hooks-implementation-plan.md
Hash: 137a453b5599c5960f36346ba85f3811820c5aa073644457cb7013ba30d9d764

## [2026-04-18] ingest | handoff-pre-co-problems
Source: ~/Downloads/Conversation with claude code about handoff pre-co.md
Content: skill-craft routes to skill-creator via keyword text matching only. skill-creator requires human-authored eval queries and can't run autonomously.
Page: wiki/concepts/handoff-pre-co-problems.md
Hash: 2c9752f0c97f249c5d4f3c5935e637f6d9e17b6f259b691b5558a9b17cdb8884

## [2026-04-18] ingest | skill-enforcement-root-cause
Source: ~/Downloads/Here's a chat with claude code, and codex, about o.md
Content: Layer 1 fails because advisory text can't force tool calls. Structural fixes: inline skill content, native commands, or Superpowers enforcement.
Page: wiki/concepts/skill-enforcement-root-cause.md
Hash: 139dee6605c6e04cde7de577566292b5aa911185b462b761a70f7e16111c498d

## [2026-04-18] ingest | command-path-vs-skill-enforcement
Source: ~/Downloads/Here's a chat with claude code, and codex, about o (1).md
Content: Native commands vs. UserPromptSubmit. Commands expand deterministically before model sees turn. Superpowers uses structural positioning + psychological pressure + TDD on instruction language.
Page: wiki/concepts/command-path-vs-skill-enforcement.md
Hash: 249a63d3853fe055bbf20e1b8186ab2ec3674e273408a7a15b81f36563646bc2

## [2026-04-24] ingest | Handoff Envelope Schema
Source: chs-export session 76b50f85-6b2f-4a73-be58-d04cb15fc9a7
Content: Complete envelope structure for handoff v2 â€” build_envelope() 3 top-level keys + checksum, build_resume_snapshot() 13 required + 8 optional params, schema v2 strict validation. Local marketplace installation details.
Page: wiki/concepts/handoff-envelope-schema.md
Hash: 9ff9ec00ba8e443c0e5ad9f9e45f79e2381d19779b363f0f13b4a73470cb8a04

## 2026-04-29

- **crawl4ai**: [Claude Code Hooks: Complete Guide to All 12 Lifecycle Events](sources/claudefa.st/000-blog-tools-hooks-hooks-guide.md)
  - URL: https://claudefa.st/blog/tools/hooks/hooks-guide
  - SHA256: f2328ca0607c2ead65aaecf097f404f112408696b23bb9547f813abb1f3c7f00
  - Source: crawl-ingest skill (crawl4ai â†’ QMD)
  - Related: hook-discovery, hook-debugging, hook-implementation-plan, rca-go-stop-hooks

## 2026-04-29
- **Claude Code Hooks: Complete Guide to All 12 Lifecycle Events** (P:\.data\wiki\sources\claudefa.st\000-blog-tools-hooks-hooks-guide.md)
  - URL: https://claudefa.st/blog/tools/hooks/hooks-guide
  - SHA256: 87e100778fde89ccd519593b5023342e17dfec5bf1e7f337af10c5d4f6f9c0dd
  - Source: crawl-ingest

## 2026-04-29
- **Example Domain** (P:\.data\wiki\sources\example.com\000-.md)
  - URL: https://example.com
  - SHA256: afbe8ebdfffe8026d9bec5c5b006005661c1f715df2d060fec6cea228b9aa28a
  - Source: crawl-ingest
- [2026-05-08] https://pi.dev/docs/latest SHA256:96bfee635871a68c02b079da6d9a471a499d4d95bf126a6b7138be09d89f6980

## [2026-05-08] ingest | MCP Token Optimizer Spec
Source: P:\.data\wiki\sources\spec-mcp-token-optimizer.md
SHA256: 274cc9dfaf814f349c9c717a30315f2b0eb5bb6704a4b6fbf0ab058a5b235b08
Content: Reduction of MCP token bloat from 150K to 3K tokens via dynamic discovery, sandboxing, and bundling.
Page: wiki/concepts/mcp-token-optimizer.md


## [2026-05-08] ingest | ADR: Terminal ID Detection - Hooks-Aware Directory Traversal
Source: P:\.data\wiki\sources\research\adr-terminal-id-detection-20260309.md
SHA256: 88c188703e1a0982de43529973c1d724a9a7162c12af50e8410f21b30a6bf87d
Content: **Date**: 2026-03-09 **Status**: Accepted **Context**: Handoff System **Related Files**: - `P:\.claude\hooks\terminal_detection.py` (lines 369-488)...
Page: wiki/concepts/adr-terminal-id-detection-20260309.md

## [2026-05-08] ingest | Adversarial Review Session Notes
Source: P:\.data\wiki\sources\research\adversarial-review-session-notes.md
SHA256: 69710676c1e829b6b8e8383e5f119c774660557913dda91624ac6a4b8ec622b1
Content: **Date**: 2026-03-15 **Focus**: /review and /adversarial-review skills integration **Status**: âœ… **ALL ISSUES RESOLVED** (verified 2026-03-16) # ...
Page: wiki/concepts/adversarial-review-session-notes.md

## [2026-05-08] ingest | AST Pattern Detection & Static Analysis Research
Source: P:\.data\wiki\sources\research\ast_pattern_detection_research.md
SHA256: 48843a85c71f4804887c53625392b2d73278256bf1d15f2b0145c3526454fb0a
Content: # This document catalogs AST-based pattern detection techniques for Python code quality analysis, based on research from DPy, PyExamine, Code Craft...
Page: wiki/concepts/ast_pattern_detection_research.md

## [2026-05-08] ingest | c users brsth downloads llm lo 8OdttnJOSZiQBT0W6YV0rA
Source: P:\.data\wiki\sources\research\c-users-brsth-downloads-llm-lo-8OdttnJOSZiQBT0W6YV0rA.md
SHA256: 2f53558ff5a55f3f6f303cbe16cfe6d4e96aeef6070cc7802fc7e3a49a9c9a36
Content: <img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/> efficient or effective. What ar...
Page: wiki/concepts/c-users-brsth-downloads-llm-lo-8OdttnJOSZiQBT0W6YV0rA.md

## [2026-05-08] ingest | Can you give me a deep research prompt that I can (1)
Source: P:\.data\wiki\sources\research\Can-you-give-me-a-deep-research-prompt-that-I-can-(1).md
SHA256: 1fbd48406f03dc4c908c29dce663ede894a6709df479cf2f65a5e66aab1333e0
Content: <img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/> Hereâ€™s a compact, highâ€‘sign...
Page: wiki/concepts/Can-you-give-me-a-deep-research-prompt-that-I-can-(1).md

## [2026-05-08] ingest | check data
Source: P:\.data\wiki\sources\research\check_data.js
SHA256: b84a4a9e6439fe920a2ac80e30c841275fe9cc8df2b6d2ca28a61b8fa16014ef
Content: const TECH_DATA = { "strategy": { "label": "Strategy Branch", "icon": "compass", "color": "indigo", "commands": [], "bullets": [ "@architect", "@cs...
Page: wiki/concepts/check_data.js

## [2026-05-08] ingest | Claude Code Agents Guide
Source: P:\.data\wiki\sources\research\claude-agents-v1.0.md
SHA256: 30c206870ea13a78c8e3655c8ccda5d81ded4f2bacfcf5134622cd95c7254912
Content: **v1.0 | April 2026 | 2.1.63+ | Reference** # 1. [Core Agent Concepts](#core-agent-concepts) 2. [Subagent vs Agent Teams](#subagent-vs-agent-teams)...
Page: wiki/concepts/claude-agents-v1.0.md

## [2026-05-08] ingest | Claude Code MCP Guide
Source: P:\.data\wiki\sources\research\claude-mcp-v1.0.md
SHA256: f0a3e857fcdeb01e232bee669ed0bee442abff0b2307c8931ef83a3db5947b51
Content: **v1.0 | April 2026 | Reference** # 1. [Core MCP Concepts](#core-mcp-concepts) 2. [MCP Server Architecture](#mcp-server-architecture) 3. [Skills as...
Page: wiki/concepts/claude-mcp-v1.0.md

## [2026-05-08] ingest | claude skill v1.0
Source: P:\.data\wiki\sources\research\claude-skill-v1.0.md
SHA256: 2009fea15eb1e9c92df535fe9b15e9d3e1d44c795b246ed3cbc027e1bc0b075b
Content: Standards for writing production-quality Claude Code skills. Applies to all skills in `.claude/skills/`, `skills/`, and plugin skills under `.claud...
Page: wiki/concepts/claude-skill-v1.0.md

## [2026-05-08] ingest | Execution Efficiency Implementation
Source: P:\.data\wiki\sources\research\CLAUDE_md_patch_execution_efficiency.md
SHA256: 23f4e525ffba2ead4602d319a34c7055c667ece8e9f984a8462e4937fef38157
Content: # **Primary mechanism:** Output style (`.claude/output-styles/expert.md`) **Observability:** Style friction detector (`hooks/style_friction_detecto...
Page: wiki/concepts/CLAUDE_md_patch_execution_efficiency.md

## [2026-05-08] ingest | Code Review & Adversarial Analysis: Pattern Comparison
Source: P:\.data\wiki\sources\research\code-review-patterns-comparison.md
SHA256: 920f46937e266670f4c30bcf37c1cec02525f759092f629025bdbdb5e7269ff2
Content: **Date**: 2026-03-16 **Purpose**: Analyze patterns across implementations that informed `/uci` (Unified Code Inspection) # ## ``` User â†’ Main Age...
Page: wiki/concepts/code-review-patterns-comparison.md

## [2026-05-08] ingest | Competence Layer Architecture v2.0 - Complete Implementation Plan
Source: P:\.data\wiki\sources\research\competence_layer_v2_design.md
SHA256: bc81562d8d04092a6646afe54a382354e6d7d76c3faeefdaa9adf18951d446c4
Content: > **Single message for another LLM to execute as implementation roadmap** |--|| | **Over-coupled workflow gate** | TaskUpdate tied to TaskList evid...
Page: wiki/concepts/competence_layer_v2_design.md

## [2026-05-08] ingest | Competence Layer Phase 2: Self-Improvement, Reflection, and Metrics
Source: P:\.data\wiki\sources\research\competence_phase2_self_improvement.md
SHA256: 9b0d1f2fd47eeebf348ed2ded0520ac68967d0d88aca3c8d7f594496bf40c1e2
Content: > **For simpler LLM implementation** - Apply these additions after core competence layer (Phase 1) is implemented. Assume following from Phase 1 al...
Page: wiki/concepts/competence_phase2_self_improvement.md

## [2026-05-08] ingest | Configuration Guide: Intent Validation + Auto-Backup
Source: P:\.data\wiki\sources\research\CONFIGURATION_GUIDE.md
SHA256: 99e537b216049461288d9c898aecbaea3cb77084295bdbf77cde6c649373edc8
Content: # Intent validation is preconfigured with conservative defaults. No action neededâ€”it just works. For advanced tuning, edit `P:\.claude\settings.t...
Page: wiki/concepts/CONFIGURATION_GUIDE.md

## [2026-05-08] ingest | Contract Enforcer Bug Fix - Solution Review
Source: P:\.data\wiki\sources\research\contract_enforcer_bug_fix_review.md
SHA256: 85413cc873e8d0be7401fc794f3d06bb3f775ed433bc8f99d5841ed824c9e7f1
Content: **Date:** 2026-02-02 **Author:** TDD Workflow (Bug Fix) **Reversibility:** R:1 (single function implementation, easily reverted) # ## The `load_con...
Page: wiki/concepts/contract_enforcer_bug_fix_review.md

## [2026-05-08] ingest | Google Gemini
Source: P:\.data\wiki\sources\research\Deep-Research-with-Gemini-CLI.md
SHA256: 3010034541c95e8ffd5feff77825b32c89fa4d2d4a5feeaed9497770dec826e2
Content: [ Gemini ](/app) Deep Research with Gemini-CLI Upgrade [ ](/app) [ My stuff ](mystuff) [ Gems ](/gems/view) Analysis, Dev Forensics Analysis, Dev T...
Page: wiki/concepts/Deep-Research-with-Gemini-CLI.md

## [2026-05-08] ingest | Google Gemini
Source: P:\.data\wiki\sources\research\Deep-Research-with-Gemini-CLIimplementation.md
SHA256: eb9f5a9d8e5b379b1b53582a3b2030ae7240cf5e568802144ba3244c9fcb9eed
Content: [ Gemini ](/app) Deep Research with Gemini-CLI Upgrade [ ](/app) [ My stuff ](mystuff) [ Gems ](/gems/view) Analysis, Dev Forensics Analysis, Dev T...
Page: wiki/concepts/Deep-Research-with-Gemini-CLIimplementation.md

## [2026-05-08] ingest | generate sdlc tech tree data
Source: P:\.data\wiki\sources\research\generate_sdlc_tech_tree_data.py
SHA256: f970c292758ca212f02d66d37f56d15d5b69dc8c78590132d9a92cfdd35f68c0
Content: from __future__ import annotations import json import pathlib import re import sys from typing import Dict, Iterable, List, Optional, Tuple import ...
Page: wiki/concepts/generate_sdlc_tech_tree_data.py

## [2026-05-08] ingest | Handoff System Fix Summary
Source: P:\.data\wiki\sources\research\handoff-system-fix-summary.md
SHA256: afafa6e0c0bbd0f72d420a6835170fece6749348ba4cc2ed862930bb365035b4
Content: # # After conversation compaction events, the handoff system failed to provide adequate task context, causing: 1. **Assistant gets sidetracked** by...
Page: wiki/concepts/handoff-system-fix-summary.md

## [2026-05-08] ingest | Hook Architecture v2.6.0
Source: P:\.data\wiki\sources\research\hook-architecture.md
SHA256: 8b95662cd185b9ebd0dbcb4d41090d329f627b183ce506b4b3966102c8e278f0
Content: > Extracted from settings.json for reference. Not runtime configuration. # **Core Principle:** Structural enforcement beats instruction injection. ...
Page: wiki/concepts/hook-architecture.md

## [2026-05-08] ingest | Id like to give notebooklm a deep research prompt
Source: P:\.data\wiki\sources\research\Id-like-to-give-notebooklm-a-deep-research-prompt.md
SHA256: 319bb60e1fcbdce64c027b2c963c0c566f0b28c6445860952ee2648625e1aa26
Content: <img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/> Please make it great and includ...
Page: wiki/concepts/Id-like-to-give-notebooklm-a-deep-research-prompt.md

## [2026-05-08] ingest | Lesson Capture Ecosystem - Reference
Source: P:\.data\wiki\sources\research\lesson_capture_reference.md
SHA256: db3a5dd3798a6519dd24bced87dfa1e6675a06e4ec5e420dd57537e7851c787b
Content: **Purpose**: Consolidated reference for all lesson capture skills and hooks. **Created**: 2026-02-05 **Status**: Active documentation -| # ## **Pur...
Page: wiki/concepts/lesson_capture_reference.md

## [2026-05-08] ingest | Memory to CKS Integration - COMPLETE
Source: P:\.data\wiki\sources\research\memory_to_cks_integration.md
SHA256: 3a26d919aa44d7d7a6608ffcca997cb65f91c511ba5e945f308878121a187710
Content: **Date**: 2026-03-14 **Status**: âœ… Operational # Memory files from `C:\Users\brsth\.claude\projects\P--\memory\` were not integrated into CKS, ca...
Page: wiki/concepts/memory_to_cks_integration.md

## [2026-05-08] ingest | Meta-Review Production Deployment Guide
Source: P:\.data\wiki\sources\research\meta-review-production-deployment.md
SHA256: 2581bcf508ec0156161827117cdfa1e4b3a0cfa38ae39bbe4f0cd6a5d4977180
Content: **Created**: 2026-03-10 **Status**: PRODUCTION-READY **Version**: 1.0.0 # The Meta-Review System is production-ready and validated against real pac...
Page: wiki/concepts/meta-review-production-deployment.md

## [2026-05-08] ingest | Multi-Terminal Architecture Documentation
Source: P:\.data\wiki\sources\research\multi-terminal-architecture.md
SHA256: 6a642553187502bb206d6dd89c5ffa704d0096a67cb4770c77293f7ac43597bf
Content: **Purpose**: Document how multi-terminal isolation works across the hooks ecosystem, including state management, terminal detection, and known race...
Page: wiki/concepts/multi-terminal-architecture.md

## [2026-05-08] ingest | Google Gemini
Source: P:\.data\wiki\sources\research\page-2026-03-25-04-35-22.md
SHA256: 7624fe8637013aa389e5896dda51e7a3e4ffa5d94e003ad8bae6e5c68f1283cb
Content: [ Gemini ](/app) Model Cascading for Cost Efficiency [ ](/app) [ My stuff ](mystuff) [ Gems ](/gems/view) Analysis, Dev Forensics Analysis, Dev Tes...
Page: wiki/concepts/page-2026-03-25-04-35-22.md

## [2026-05-08] ingest | Google Gemini
Source: P:\.data\wiki\sources\research\page-2026-03-26-13-29-49.md
SHA256: c83f3050c3332364a89b2e70587660f100d28acc1cdd13a1398336c92c5d8a68
Content: [ Gemini ](/app) Stable Terminal ID for Claude Code Upgrade [ ](/app) [ My stuff ](mystuff) [ Gems ](/gems/view) Analysis, Dev Forensics Analysis, ...
Page: wiki/concepts/page-2026-03-26-13-29-49.md

## [2026-05-08] ingest | Implementation Plan: loop-core Package
Source: P:\.data\wiki\sources\research\plan-loop-core.md
SHA256: 024eb10b49909fcec2d437c3fefc29634a702606466a1ffa7e046982c5975ef2
Content: **Created**: 2026-03-14 **Status**: COMPLETE âœ… **Estimated Effort**: 2.5-3 hours # Create `packages/loop-core/` with file-based state management ...
Page: wiki/concepts/plan-loop-core.md

## [2026-05-08] ingest | TASK-005: Per-Terminal State Directories - Remaining Implementation
Source: P:\.data\wiki\sources\research\plan-task-005-remaining.md
SHA256: 5efdb14f6e842737ce37321926097f5cb478416a78ae565dff91f4d21cd8cfae
Content: **Created**: 2026-03-14 **Phase**: Phase 1-3 Completion **Estimated Time**: 2-4 hours # Complete the migration of remaining hooks to use the new te...
Page: wiki/concepts/plan-task-005-remaining.md

## [2026-05-08] ingest | Plan Review Guide - Consolidated Skill Reference
Source: P:\.data\wiki\sources\research\plan_review_guide.md
SHA256: 9bfdaa3755f157d3e2e0bf02bcf75355c279d0f0334d7aafc1f24c7b3cb97fdf
Content: **Version:** 1.0.0 **Created:** 2026-02-05 **Purpose:** Single reference document consolidating all skills for reviewing and improving plans. # ## ...
Page: wiki/concepts/plan_review_guide.md

## [2026-05-08] ingest | Quality Gates Architecture
Source: P:\.data\wiki\sources\research\quality-gates-architecture.md
SHA256: e95ca15440754bf6c60eab315a5ca86aedb7c420e4571f26059a7f23a3d23880
Content: # Two-tier quality system with automatic escalation based on failure severity, plus opportunity tracking. ``` COMMIT â†’ ðŸ”” /r (preventive self-r...
Page: wiki/concepts/quality-gates-architecture.md

## [2026-05-08] ingest | RCA Improvement Implementation Summary
Source: P:\.data\wiki\sources\research\RCA_IMPROVEMENT_IMPLEMENTATION.md
SHA256: 600b35d90841fed007af28638b41fbc7d99082b3e9515a0db27ea400eb86a96b
Content: # This implementation addresses structural gaps in the RCA system to improve outcomes through enforcement rather than instruction. **Principle Appl...
Page: wiki/concepts/RCA_IMPROVEMENT_IMPLEMENTATION.md

## [2026-05-08] ingest | Recovery Guide: Auto-Backup and Intent Validation
Source: P:\.data\wiki\sources\research\RECOVERY_GUIDE.md
SHA256: b80095c4f0465f26b42edc1debdc8a6376b5bf6223561d6fb06bfe8720b49b40
Content: # If a file got deleted or modified unexpectedly, this guide helps you recover it. ## **Layer 1: Prevention (Intent Validation)** - Blocks destruct...
Page: wiki/concepts/RECOVERY_GUIDE.md

## [2026-05-08] ingest | Refactoring Validation Process
Source: P:\.data\wiki\sources\research\refactoring-validation-guide.md
SHA256: d6279f2d3b9d6efa223b42f3795f73797bfee1b4421c9a96434056c3feca24c7
Content: **Purpose**: Prevent syntax errors from propagating through development phases by enforcing immediate validation after batch refactoring operations...
Page: wiki/concepts/refactoring-validation-guide.md

## [2026-05-08] ingest | Repository Visibility Guard - Functional Test Summary
Source: P:\.data\wiki\sources\research\repo-visibility-guard-test-summary.md
SHA256: 254d5b26ea529ea96d444b8cb949cc74bcd67a3c062c2486eced7985da8cd160
Content: **Date**: 2026-03-14 **Status**: âœ… **LIVE & PROTECTING** # ## - **File**: `.claude/hooks/tests/test_repo_visibility_guard.py` - **Result**: 21/21...
Page: wiki/concepts/repo-visibility-guard-test-summary.md

## [2026-05-08] ingest | Repository Visibility Guard Hook
Source: P:\.data\wiki\sources\research\repository-visibility-guard.md
SHA256: 382776ccf0483de7517e68bdef395e69c538336dc67e219d6b3cfdb4ceefb3fc
Content: **Implementation Date**: 2026-03-14 **Purpose**: Prevents accidental public exposure of P:\ drive repositories that may contain API keys or sensiti...
Page: wiki/concepts/repository-visibility-guard.md

## [2026-05-08] ingest | sdlc data injection
Source: P:\.data\wiki\sources\research\sdlc_data_injection.js
SHA256: ca858c15e035d5d242983edee0b471c26cbfd9cf50f95f8f34816c2c8d4954f5
Content: // AUTO-GENERATED BY generate_sdlc_tech_tree_data.py const RELATIONSHIPS = {}; const CLUSTERS = { "strategy": [ { "hub": "/design", "satellites": [...
Page: wiki/concepts/sdlc_data_injection.js

## [2026-05-08] ingest | Session State Tracking - Implementation Summary
Source: P:\.data\wiki\sources\research\session-state-implementation.md
SHA256: a3bbc7132f98ff4977dfa47d0cad465c98a2f60f0ca1e473e38d076dcb4045eb
Content: **Date:** 2025-12-29 **Status:** Implemented **RCA Reference:** yt-fts incident 2025-12-28 # ## **Files:** - `P:/.claude/hooks/session_reversion_ch...
Page: wiki/concepts/session-state-implementation.md

## [2026-05-08] ingest | Skills Index Catalog
Source: P:\.data\wiki\sources\research\SKILLS_INDEX.md
SHA256: a2996576a6d35538609c6c6266af66c75eb8b78c31b6451175a8c3455a01ae0c
Content: **Generated:** 2026-01-16 | **Total Skills:** 193 | **Categories:** 59 # - **AI/LLM**: 1 skills - **Observability**: 1 skills - **Quality**: 1 skil...
Page: wiki/concepts/SKILLS_INDEX.md

## [2026-05-08] ingest | Python Static Analysis Tools Catalog 2025
Source: P:\.data\wiki\sources\research\static_analysis_tools_catalog.md
SHA256: 1bbf15f062658ed266c73872a99d464dbca129b52f8eaf2abff7f7d4db2cc09b
Content: # This document catalogs Python static analysis tools for 2025, covering linters, type checkers, security scanners, and formatters. Tools are evalu...
Page: wiki/concepts/static_analysis_tools_catalog.md

## [2026-05-08] ingest | Statusline System
Source: P:\.data\wiki\sources\research\statusline.md
SHA256: abaececeaf9de0720543311e72def2acdf600f0e4902bf9b52182153d5fba053
Content: Real-time status display for Claude Code terminal sessions. # | Component | Path | Lines | |-|-|-|-| | ðŸŸ¢ | â‰¥150k | Plenty | | ðŸŸ¡ | â‰¥100k |...
Page: wiki/concepts/statusline.md

## [2026-05-08] ingest | TASK-003/004: Terminal ID Standardization - Summary
Source: P:\.data\wiki\sources\research\task-003-004-summary.md
SHA256: 735c436a1d908b2ace7b527369748e667b1d7e57b8ae2a15d3e1d54c82c0195b
Content: **Completed**: 2026-03-14 **Phase**: Phase 1 - Tenant IDs, Hooks, Per-Terminal State # Implemented centralized terminal ID derivation system to pro...
Page: wiki/concepts/task-003-004-summary.md

## [2026-05-08] ingest | TASK-005: Per-Terminal State Directories - COMPLETE âœ…
Source: P:\.data\wiki\sources\research\task-005-foundation-summary.md
SHA256: e13610b100b952afa97881daef30bc309d32b7696c9bf0d9f2ca30dc7053e8bb
Content: **Completed**: 2026-03-14 **Phase**: Full implementation complete (all 5 tasks) **Final Commit**: TBD # Implemented complete per-terminal state iso...
Page: wiki/concepts/task-005-foundation-summary.md

## [2026-05-08] ingest | TDD System Documentation
Source: P:\.data\wiki\sources\research\TDD_SYSTEM.md
SHA256: fbeecce84df993e58c438c5b33f1010e5b44b2883ac3a4693c1ddd48137fa1f4
Content: # The TDD (Test-Driven Development) enforcement system consists of three layers: 1. **Skills** - Documentation and guidance 2. **Hooks** - Actual e...
Page: wiki/concepts/TDD_SYSTEM.md

## [2026-05-08] ingest | temp relationships
Source: P:\.data\wiki\sources\research\temp_relationships.js
SHA256: 48d2dcb048f58099a11ec37b53e360c5a7db34757acc74c18170bb272b985342
Content: const RELATIONSHIPS = { "/analytics": { "next": [ "/refactor", "/optimize", "/fix" ], "prev": [ "/test", "/verify", "/benchmark" ], "capabilities":...
Page: wiki/concepts/temp_relationships.js

## [2026-05-08] ingest | temp rels
Source: P:\.data\wiki\sources\research\temp_rels.js
SHA256: 174a54ccb1a47b983a22e5ad556ea253345b338e2083b1b5d4a24a60d8283b63
Content: const RELATIONSHIPS = { "/analytics": { "capabilities": [ "system analytics and metrics collection\", \"performance monitoring and dashboard\", \"d...
Page: wiki/concepts/temp_rels.js

## [2026-05-08] ingest | Terminal ID Detection - Quick Reference
Source: P:\.data\wiki\sources\research\terminal-id-troubleshooting.md
SHA256: 20435890a47db85c8eda663031cc49357ca1d629e8289fac49866f32ae46a116
Content: **Last Updated**: 2026-03-09 **Status**: Working correctly with hooks-aware directory traversal ## **Symptom**: SessionStart shows error loading ha...
Page: wiki/concepts/terminal-id-troubleshooting.md

## [2026-05-08] ingest | Turn Scoping Design Review - TASK-013a
Source: P:\.data\wiki\sources\research\turn-scoping-design.md
SHA256: 9d90cd200e9c6e7e322e8c35cd467aa6bc08d98697ed5bb5f53a8acd71401d25
Content: # **Root cause**: Loop observability module (TASK-006) was not integrated into the Ralph loop platform - completed as a standalone module without h...
Page: wiki/concepts/turn-scoping-design.md

## [2026-05-08] ingest | User Preferences Scope Clarification
Source: P:\.data\wiki\sources\research\user-preferences-scope-clarification.md
SHA256: 1f656158ab75be65a52dee8e51e50656cf0ec80d760d42bf9fe800452344155d
Content: **Purpose:** Add these clarifications to your user preferences (Settings > Profile) to prevent satisficing. # Without this clarification, "Minimal ...
Page: wiki/concepts/user-preferences-scope-clarification.md

## [2026-05-08] ingest | Verification Hooks Documentation
Source: P:\.data\wiki\sources\research\verification-hooks.md
SHA256: 2ef2fa0893cd4da68895bb4123494b4189b486451332694bf956bc9140b44476
Content: # The verification claim grounding system provides per-terminal, evidence-based validation of claims made by AI responses. This prevents the AI fro...
Page: wiki/concepts/verification-hooks.md

## [2026-05-08] ingest | Verification Claim Grounding Implementation - COMPLETE
Source: P:\.data\wiki\sources\research\verification-implementation-complete.md
SHA256: a92609bcd774505bd9f6b91ead1bd59cd66642f03b44ea3e82a73d94c32c693f
Content: **Date Completed**: 2026-03-15 **Plan**: `plan-20260314-verification-claim-grounding.md` **Status**: âœ… ALL PHASES COMPLETE # Successfully impleme...
Page: wiki/concepts/verification-implementation-complete.md

## [2026-05-08] ingest | /v Skill Review Guide - Sequential Validation Pipeline
Source: P:\.data\wiki\sources\research\v_skill_guide.md
SHA256: 72c30e8ae36aafdf6bfdff63f745444e52ecc154c3e3b5abb49a603b18ae22fa
Content: **Version:** 1.0.0 **Created:** 2026-02-05 **Purpose:** Single reference document for the `/v` (sequential validation pipeline) skill and related v...
Page: wiki/concepts/v_skill_guide.md

## [2026-05-08] ingest | ADR-{timestamp}: Production Telemetry for skill-craft Post-Run Validation
Source: P:\.data\wiki\sources\research\architecture\ADR-skill-craft-telemetry.md
SHA256: e6bf185a947995b7c58089153819e6e1e68633ae5aece5926f5366b334a64ca9
Content: # Proposed # skill-craft runs a 5-phase pipeline (DIAGNOSING â†’ PLANNING â†’ EXECUTING â†’ EVALUATING â†’ GATING) against target skills. After eac...
Page: wiki/concepts/ADR-skill-craft-telemetry.md

## [2026-05-08] ingest | ADR-20260420: Batch Query + Citation Granularity for QMD Wiki Backend
Source: P:\.data\wiki\sources\research\architecture\ADR-SYSTEM-1776662134.md
SHA256: ee9c542eab65a9e38cb42e6e26892844168986c117eafd3db7e12433cf8164f6
Content: # Proposed # The QMD Wiki backend (search-research/core/backends/local/qmd_wiki_backend.py) supports single-query search only. The transcript compa...
Page: wiki/concepts/ADR-SYSTEM-1776662134.md

## [2026-05-08] ingest | ADR-20260420: Batch Query + Line-Number Citation for QMD Wiki Backend
Source: P:\.data\wiki\sources\research\architecture\ADR-SYSTEM-1776662428.md
SHA256: d36f630093b2552862ce90431eba31d4ec301147421c62442aa32d05a6eef6c6
Content: # Proposed # The QMD Wiki backend (search-research/core/backends/local/qmd_wiki_backend.py) supports single-query search only. The transcript compa...
Page: wiki/concepts/ADR-SYSTEM-1776662428.md

## [2026-05-08] ingest | ADR SYSTEM 1776735279
Source: P:\.data\wiki\sources\research\architecture\ADR-SYSTEM-1776735279.md
SHA256: b8017f58cff8ea70ac14671e8af957d5a9032797525f876bfef1806380759a4b
Content: ADR: Fix Context Auto-Detection for Extensionless Directory Paths # Accepted # When /ai-pcli is invoked with a directory path that has no file exte...
Page: wiki/concepts/ADR-SYSTEM-1776735279.md

## [2026-05-08] ingest | Design: Production Telemetry for skill-craft Post-Run Validation
Source: P:\.data\wiki\sources\research\architecture\skill-craft-telemetry-design.md
SHA256: 56f9511c940f76c2d2687df7781e365286c6d81b55c22541dd427bbfbc732e67
Content: # skill-craft cannot currently measure whether a target skill actually improved after running. It only verifies that its own fidelity gates passed....
Page: wiki/concepts/skill-craft-telemetry-design.md

## [2026-05-08] ingest | Extraction Refactoring Pattern
Source: P:\.data\wiki\sources\research\patterns\extraction_refactoring.md
SHA256: be2310cd6b01e1b25bd0ce9e658b7fe930bb71da72fb16bc6e92353172793914
Content: # Reduce cyclomatic complexity by extracting focused helper methods based on single responsibility principle. # - **CC > 15**: Function is too comp...
Page: wiki/concepts/extraction_refactoring.md

## [2026-05-08] ingest | check missing
Source: P:\.data\wiki\sources\research\sdlc_tech_tree\check_missing.py
SHA256: 811e3a6ffb40d6ad3c981078dd7dcd471fea8bdac6658ac7e6cc995ac090f8f1
Content: import os import json import re SKILLS_DIR = r"P:/.claude/skills" TECH_DATA_FILE = r"P:/.claude/docs/sdlc_tech_tree/data/tech_data.js" with open(TE...
Page: wiki/concepts/check_missing.py

## [2026-05-08] ingest | extract skills
Source: P:\.data\wiki\sources\research\sdlc_tech_tree\extract_skills.py
SHA256: 05842a667debfc1b6a22ff1b0f9692ff407006d2832dddb74dfac4239fb95f6e
Content: import json import re import sys from datetime import date, datetime from pathlib import Path hooks_path = Path("P:/.claude/hooks") sys.path.insert...
Page: wiki/concepts/extract_skills.py

## [2026-05-08] ingest | generate similarity
Source: P:\.data\wiki\sources\research\sdlc_tech_tree\generate_similarity.py
SHA256: 950010ca0a92bb12c1542651590a63f8db46db4842ff66a8b5663f4d7ceddb9c
Content: import json import os import re import numpy as np from sklearn.feature_extraction.text import TfidfVectorizer from sklearn.metrics.pairwise import...
Page: wiki/concepts/generate_similarity.py

## [2026-05-08] ingest | refine tech data
Source: P:\.data\wiki\sources\research\sdlc_tech_tree\refine_tech_data.py
SHA256: 28bd92bec4fc81a9695b89796f4cf2fccc7ebf69d24513df158aef2fdde894ee
Content: import json META = { "strategy": {"label": "Strategy Branch", "icon": "compass", "color": "indigo"}, "execution": {"label": "Execution Branch", "ic...
Page: wiki/concepts/refine_tech_data.py

## [2026-05-08] ingest | update clusters
Source: P:\.data\wiki\sources\research\sdlc_tech_tree\update_clusters.py
SHA256: d4f6eb7ef378fa3b2917042601c42992cdd8894bcb5465c9cd2951423d6185af
Content: import re SOURCE_FILE = r"P:/.claude/docs/sdlc_tech_tree/data/relationships.js" NEW_CLUSTERS = """window.CLUSTERS = { "strategy": [ { "hub": "/desi...
Page: wiki/concepts/update_clusters.py

## [2026-05-08] ingest | update clusters final
Source: P:\.data\wiki\sources\research\sdlc_tech_tree\update_clusters_final.py
SHA256: 8656a8f2cac0f1453a08c8e313282e7a556ea847915822e79abc0ffddc45a2c1
Content: import re SOURCE_FILE = r"P:/.claude/docs/sdlc_tech_tree/data/relationships.js" NEW_CLUSTERS = """window.CLUSTERS = { "strategy": [ { "hub": "/heal...
Page: wiki/concepts/update_clusters_final.py

## [2026-05-08] ingest | update tech data final
Source: P:\.data\wiki\sources\research\sdlc_tech_tree\update_tech_data_final.py
SHA256: 34b277580b6f7873b96cac324934ce4946fbf499a427fcdae9bf2723c34100c0
Content: import json META = { "strategy": {"label": "Strategy (Discover & Plan)", "icon": "compass", "color": "indigo"}, "execution": {"label": "Execution (...
Page: wiki/concepts/update_tech_data_final.py

## [2026-05-08] ingest | metadata
Source: P:\.data\wiki\sources\research\sdlc_tech_tree\data\metadata.js
SHA256: 94f7021968bb888dece684bb88f4097cefe18cdac278f1a7f03a56f9082f0a1c
Content: // Auto-extracted data window.COMMAND_METADATA = { "/learn": { "desc": "Central Hub for learning and retrospectives.", "usage": "/learn [insight]",...
Page: wiki/concepts/metadata.js

## [2026-05-08] ingest | relationships
Source: P:\.data\wiki\sources\research\sdlc_tech_tree\data\relationships.js
SHA256: 04a13693685d2a978c905a1e8fd3da3151200215d42c6ad6460f736de05c82c2
Content: // Auto-extracted data window.RELATIONSHIPS = { "/analytics": { "next": [ "/refactor", "/optimize", "/fix" ], "prev": [ "/test", "/verify", "/bench...
Page: wiki/concepts/relationships.js

## [2026-05-08] ingest | similarity
Source: P:\.data\wiki\sources\research\sdlc_tech_tree\data\similarity.js
SHA256: efdc3baf7ea140855cf0e070e062c0fe3a60642e272e199774129d1675025ab1
Content: window.SIMILARITY_DATA = { "/acef": [ { "id": "/command-create", "score": 0.2354 }, { "id": "/command-enhance", "score": 0.1872 }, { "id": "/docs",...
Page: wiki/concepts/similarity.js

## [2026-05-08] ingest | skills metadata
Source: P:\.data\wiki\sources\research\sdlc_tech_tree\data\skills_metadata.js
SHA256: 13d686f719b744df473278d7f985fdfdf18ca67487f26c7e9a970b9c1aab498c
Content: // Auto-generated by extract_skills.py using skill_registry window.SKILLS_METADATA = { "/Master Skill Orchestrator": { "id": "/Master Skill Orchest...
Page: wiki/concepts/skills_metadata.js

## [2026-05-08] ingest | tech data
Source: P:\.data\wiki\sources\research\sdlc_tech_tree\data\tech_data.js
SHA256: 7d9e7e28f94f2d260f969e57b060b8b7284e46781e73c2e9357a4898f524f6ef
Content: // Auto-generated by update_tech_data_final.py window.TECH_DATA = { "strategy": { "label": "Strategy (Discover & Plan)", "icon": "compass", "color"...
Page: wiki/concepts/tech_data.js

## [2026-05-08] ingest | main
Source: P:\.data\wiki\sources\research\sdlc_tech_tree\styles\main.css
SHA256: a978d8593667145ea78f7af6df73d44eb52b713ef8b6ac265f4683bc9f9c239e
Content: body { font-family: "Inter", sans-serif; letter-spacing: -0.01em; } code { font-family: "JetBrains Mono", monospace; } .tech-node { transition: all...
Page: wiki/concepts/main.css

## [2026-05-08] ingest | sdlc tech tree improvements
Source: P:\.data\wiki\sources\research\sdlc_tech_tree\styles\sdlc_tech_tree_improvements.css
SHA256: 05571786b1d376ed232ab7747feb40eca5dc44986d73c7c847071b00d03644e3
Content: /* ============================================ SDLC Tech Tree - Right Pane Improvements ============================================ */ /* 1. ENHA...
Page: wiki/concepts/sdlc_tech_tree_improvements.css

## [2026-05-08] ingest | Skill Execution Enforcement v3.2 - Solution Document
Source: P:\.data\wiki\sources\research\solutions\skill_execution_enforcement_v3.md
SHA256: 3108705845935b099fac8d7f9e2c46310260bd102c0c5dbe98a0605c3ff7576c
Content: # LLM loads skill documentation via Skill tool, then provides its own analysis instead of executing the skill's designated workflow. The skill *app...
Page: wiki/concepts/skill_execution_enforcement_v3.md

## [2026-05-10] ingest | Popular Claude Code Search and Companion Repos
Source: for my claude code llm, what are the most popular.md
SHA256: fe8fa9c01ce037e5d3fc0f8fcbab1f0c93c77c67b1ed312fc89cf412bf6ed8cd
Content: Survey of top Claude Code repos including Repomix, Claude-Mem, mcp-vector-search, and web search integration options with hype-to-reality analysis.
Page: wiki/concepts/popular-claude-code-search-repos.md

## [2026-05-10] ingest | Claude Code Session ID Detection Methods
Source: from claude code_ __what is this session id___.md
SHA256: 3dfd4aa3d20c0168ad40a3a7c6ae6f6d2ba49d980ec12ad44d12a656e328d78b
Content: Methods for deriving session ID in interactive Claude Code sessions on Windows 11 with multi-terminal considerations.
Page: wiki/concepts/session-id-detection-methods.md

## [2026-05-10] ingest | /go Artifact-Pattern Quick Reference
Source: GO-QUICK-REFERENCE.md
SHA256: 1f6fe9196d0ae4389567d96c5f3e66d791240b4126a8e74f50fc40dab75d0baa
Content: File-based state machine with atomic gates for /go skill -- six steps from task definition to PR-ready completion with per-terminal isolation.
Page: wiki/concepts/go-artifact-pattern-quick-reference.md

## [2026-05-10] ingest | Session Chain Across Compaction - Architecture and Solution
Source: Has anyone figured out for claude code, how to cre.md
SHA256: d30cde4cd5514e392aedf28d3f6aa5d1d8514f59e560bc9dbd7542f0ee1821ae
Content: Compaction breaks session chains because JSONL files have no back-pointer. Fix: session_chain array in handoff envelope via PreCompact.
Page: wiki/concepts/session-chain-compaction-problem.md

## [2026-05-10] ingest | Hallucination Detection and Verification for Code Agents
Source: Here's a chat history we've been having.  Please s.md
SHA256: 8927fb360a02abc0a735bdd472d7fefc62266f8704ded4dc7b2f3ccdc0fe87c8
Content: Tool-grounded verification beats scoring for code agents. Pelican pattern, Galileo Luna-2 vs Arthur Shield comparison, RAG+tools integration.
Page: wiki/concepts/hallucination-detection-code-agents.md

## [2026-05-10] ingest | Skill Execution Enforcement: Inline vs Advisory Architecture
Source: Here's a chat with claude code, and codex, about o (2).md
SHA256: be98695523ea31936758d29c883e3105e0e8b26440ba5a9f8d011ec3feb3b75b
Content: UserPromptSubmit achieves only ~50% skill compliance. Inline skill injection via system-reminder eliminates tool-call bypass surface. Stop hook remains necessary as safety net.
Page: wiki/concepts/skill-execution-enforcement-deep-dive.md

## [2026-05-10] ingest | Hooks Optimization: Handoff Prompt and Consolidation Strategy
Source: Here's the end conversation from a previous thread (1).md
SHA256: 5c663555b9fd4f5918007c3e59efa6f763a6bde6f8a80036f375f967a35ce7b0
Content: Stop hook pipeline architecture with telemetry (94.3% allow), behavior_contract.py consolidation absorbing operating_rules/truthfulness_gate/verify_before_claim.
Page: wiki/concepts/hooks-optimization-handoff-prompt.md

## [2026-05-10] ingest | Hooks Consolidation Audit Prompt Design
Source: Here's the end conversation from a previous thread (2).md
SHA256: 5dbb7deb3695e2eb70747a307a38b55806260507166ae1ce70fee70930779dbd
Content: Audit prompt for turn classification, hook overlap analysis, and consolidation verdict. Three-step structure: classify, audit, propose injection.
Page: wiki/concepts/hooks-consolidation-audit-prompt.md

## [2026-05-10] ingest | Hooks Architecture for Dynamic CLAUDE.md Injection
Source: Here's the end conversation from a previous thread.md
SHA256: 8135881a64eca622ea201d86dbd25155e41fb0dcab90a0d51c9f4c80a278f018
Content: Design for hook system that dynamically injects relevant CLAUDE.md segments using turn classification and additionalContext injection.
Page: wiki/concepts/hooks-claude-md-injection-strategy.md

## [2026-05-10] ingest | Hooks Implementation Plan Phase 2
Source: hooks_implementation_plan 2.md
SHA256: 6e29ef00e690d59f033409a9927f886e4ecb9cf6f1f961f98e4f3576801f3566
Content: Phase 2 plan: reduce PreToolUse latency, consolidate Stop-layer, add UserPromptSubmit helpfulness. Preserves dispatch-chain integrity and fail-open invariants.
Page: wiki/concepts/hooks-implementation-plan-phase2.md

## [2026-05-10] ingest | LLM Proactive Helpfulness: Fixing Passive and Literalist Responses
Source: How can I describe the problems with this page to.md
SHA256: 68815b9c8a85bd196f88c05d65089b5477385d0f0964c57401ee506552687ad3
Content: Passive LLM patterns (literalism, withheld diagnoses) fixed via CLAUDE.md rules for proactive behavior plus Stop hook anti-pattern detection.
Page: wiki/concepts/llm-proactive-helpfulness-patterns.md

## [2026-05-10] ingest | Vectorized CLAUDE.md: Dynamic Retrieval of Project Policies
Source: How can we make claude code pay attention to it's.md
SHA256: 6d8ca34a68f4441a9315da132b1e39b9aef38abfdc05b8b8692cf6b23f158312
Content: Hybrid approach: keep short always-on core, retrieve task-relevant micro-rules via policy engine with metadata. Two-stage retrieval at UserPromptSubmit and PostToolBatch.
Page: wiki/concepts/vectorized-claude-md-retrieval.md

## [2026-05-10] ingest | Bifrost AI Gateway Setup for Claude Code Multi-Model Routing
Source: how do I install bifrost to work with claude code_ (1).md
SHA256: 7232e1176ba17de6b1b27c9145d7af08beae84ef5482d947253e2ce4ebed3717
Content: Complete setup for Bifrost gateway routing Claude Code through multiple providers. Install, configure, route, and optional MCP integration.
Page: wiki/concepts/bifrost-gateway-multi-model-setup.md

## [2026-05-10] ingest | Bifrost Setup: Anthropic-Only vs Multi-Provider Routing
Source: how do I install bifrost to work with claude code_.md
SHA256: 5e5247bef10049e7f4afb7e30d2f01461abd6bf27329b3eb668996ce7d77f6e7
Content: Bifrost setup with comparison of Anthropic-only vs Bifrost-first multi-provider routing for mostly-non-Anthropic workflows.
Page: wiki/concepts/bifrost-setup- anthropic-routing.md

## [2026-05-10] ingest | NVIDIA NIM Free API: Model Access and Status Checking
Source: I have a nvidia key.  How can I find out easily (c (1).md
SHA256: 239ef015fec84228b8957c45d2eebb852352c9003c9876f44155948839edbc63
Content: Reference for NVIDIA NIM free API access, PowerShell curl testing, nimping status scan (23/40 coding models UP), DeepSeek V4 availability issues.
Page: wiki/concepts/nvidia-nim-free-models-reference.md


## [2026-05-10] ingest | LLM Self-Critique and Self-Reflection Prompting
Source: LLM self-critique prompting research
SHA256: 16af3864ed809ae33bf4c3a4babfec387d8f15a0305f6e7b1c76271685153ff0
Content: Self-critique prompting patterns and continuous feedback loops for LLM output evaluation.
Page: wiki/concepts/llm-self-critique-prompting.md

## [2026-05-10] ingest | Questions That Force LLMs to Expose Unstated Assumptions
Source: Questions that expose LLM assumptions research
SHA256: 172d5a9a81361b9184197c3ab18169ed6b5404c08c9148e1610d8c60980ffa1a
Content: Scope, constraint, identity, and negative questions that challenge LLM mental models.
Page: wiki/concepts/questions-that-expose-llm-assumptions.md

## [2026-05-10] ingest | /code Skill Pipeline - Optimal Execution Order with External LLM Delegation
Source: Code skill optimal pipeline order research
SHA256: a46a70947a2889b4649306894053bbc0165d35b0c855dd8cff8119b3ffaa183b
Content: /code as orchestration skill. Pipeline: resolve_input to worktree to classify to readiness to plan to delegate to verify.
Page: wiki/concepts/code-skill-optimal-pipeline-order.md

## [2026-05-10] ingest | /code Skill Pipeline Design - Execution Order Analysis
Source: Code skill pipeline design analysis
SHA256: 6db02dda4a26ceea883913a6661f5005f8bfbd4506dbf1ec8092c2cee79fd11c
Content: Dependency chain analysis. Analyze before checklist, conditional explore, scope gating.
Page: wiki/concepts/code-skill-pipeline-design.md

## [2026-05-10] ingest | Model Reasoning Failures That Hooks Cannot Prevent
Source: Model reasoning failures analysis
SHA256: d0a0feb1972b57ca4304a268d1ddf9727593fd36f2d8453482d9d23cfbd8fe29
Content: Three LLM failure modes hooks cannot fix. Hook best practices for v2.1.119.
Page: wiki/concepts/model-reasoning-failures-hooks-cannot-fix.md

## [2026-05-10] ingest | pi CLI NVIDIA Key Requirement Bug
Source: pi CLI bug external review
SHA256: 55bf4336d527f60e91ef28cde87d2d1427752a490347dd840557b76fab6fb275
Content: pi v0.67.68 requires NVIDIA key at startup even for OpenRouter. Bug in provider init.
Page: wiki/concepts/pi-cli-nvidia-key-bug.md

## [2026-05-10] ingest | Plugin Setup - 3 Critical Fixes
Source: Plugin setup action required
SHA256: c1a57f0ce896620bbd84a03626ce88b13b7548cbe2b860c150a40cd083744711
Content: Windows path fix, audit script deployment, plugin-installer optional. 7 plugins working.
Page: wiki/concepts/plugin-setup-action-required.md

## [2026-05-10] ingest | Local Plugin Marketplace Registration for Claude Code
Source: Local plugin marketplace registration guide
SHA256: de04a2011354b59647bafcb006cd349cb9f1d315359fe0cb6b6d73fe2b1347ee
Content: Marketplace setup with marketplace.json, registration commands, schema validation errors.
Page: wiki/concepts/local-plugin-marketplace-registration.md

## [2026-05-10] ingest | yt-is Pipeline and Web Scraping Repository Landscape
Source: yt-is and web scraping repo research
SHA256: 453ceecc0d3d60f0140106e6c05afc9255972fa430d59184c19f91695edd1026
Content: No yt-is clones. Nordstrom scraping via JSON extraction. Playwright migration path.
Page: wiki/concepts/yt-is-pipeline-and-web-scraping-repos.md

## [2026-05-10] ingest | yt-is Pipeline Selenium and DOM Scraping Research
Source: yt-is Selenium scraping research
SHA256: 629dc71cfca548cc418e58f78d94e99227b7047c4bc3b0e4a2a16114af874668
Content: YouTube transcript repos vs yt-is. Multi-key API advantage. Playwright 2-5x faster.
Page: wiki/concepts/yt-is-selenium-scraping-research.md

## [2026-05-10] ingest | /bf Skill - Thin Dispatcher for Bifrost-Backed Orchestration
Source: bf_SKILL.md
SHA256: 1807a9c5255410392f29c965f409ba2638128c7e915738d4976747076c8a9039
Content: Thin dispatcher (v4.0) routing to bf_v3_service.py. Models: M27, GLM-5.1, DSv4-flash.
Page: wiki/concepts/bf-skill-thin-dispatcher.md

## [2026-05-10] ingest | /bf Skill - Multi-Model Bifrost Orchestrator (v2.0)
Source: bf_skill_complete.md
SHA256: cfa138705bfb62d240212abf19bc55f16fddcad5ccc68e42a6c0c355da493b19
Content: Full implementation with httpx async, mode-specific prompts, flexible arg parsing.
Page: wiki/concepts/bf-skill-multi-model-orchestrator.md

## [2026-05-10] ingest | YouTube Channel URL Verification List
Source: YouTube channel URL verification
SHA256: 20626e610a0c6ae6b0670f1cdf89533312e3050a75c5c8a015c424a9866c4fb9
Content: 160+ YouTube handles verified by subscriber count and video volume. Duplicates canonicalized.
Page: wiki/concepts/yt-channel-url-verification-list.md

## [2026-05-10] ingest | Claude Search Plugin Implementation Package
Source: claude-search-implementation-package variant
SHA256: d7aabf33deaf1403dd32921402baf5f47b072f38604b79be42fca0436a70e8e5
Content: Plugin-native search spec: entity types, scope maps, intent classifier, evidence packets.
Page: wiki/concepts/claude-search-plugin-implementation-package.md

## [2026-05-10] ingest | Claude Search Plugin Specification
Source: claude-search-implementation-package
SHA256: 92689f6f7ae258148f1e6aa8c621a4ce2308bb54e580f11df56cafcf023e9594
Content: Deterministic entity resolution, structured evidence packets, mandatory coverage.
Page: wiki/concepts/claude-search-plugin-spec.md

## [2026-05-10] ingest | Claude Search Implementation - Final LLM Prompt
Source: claude-search-implementing-llm-final-prompt
SHA256: 96a10383ed5eec20bf627da9347d1ff82abe7f0b0aa1f323379dd91fc5ca11ab
Content: Async-native bridge with UnifiedAsyncRouter. Required-root enforcement in bridge. Phase Two modules.
Page: wiki/concepts/claude-search-implementation-final-prompt.md

## [2026-05-10] ingest | Session Chaining in Claude Code After Compaction
Source: deep-research-report session chaining
SHA256: 9ad0d1047411f6afb6f582bdebeb57e9b9ccff805276bdf33172fee1d874aec6
Content: No official chain API. PreCompact/PostCompact/SessionStart hooks. Hook-driven SQLite chain store.
Page: wiki/concepts/session-chaining-after-compaction.md

## [2026-05-10] ingest | Hybrid Orchestration of Local Think and External LLM Connectors
Source: deep-research-report hybrid orchestration
SHA256: 68d6a63f0163fa885d5b0de8114dcbe771c0ba1409b4cd6bdaf34f50b97bb55b
Content: Think-first control plane. Six architecture patterns. Selective chaining default.
Page: wiki/concepts/hybrid-orchestration-local-think-external-llm.md

## [2026-05-10] ingest | Programming Fonts for Developers - 2026 Guide
Source: page-2026-04-19-11-13-22.md
SHA256: 211a31a02b2e39d0e9a21d43d2c1371a96b642dfa97bfb7daf864c073b9ea02b
Content: Top 10 programming fonts with evaluation criteria and editor recommendations.
Page: wiki/concepts/programming-fonts-developer-guide-2026.md

## [2026-05-10] ingest | LLM Model Routing Strategy
Source: page-2026-04-28-18-40-39.md
SHA256: f59cb0d42ecd7380a2a1ba4f5b2b13ce34c5ed5ffd9b96cd61afbceefb5b3699
Content: Agent harness as permanent OS with external LLMs as consultants.
Page: wiki/concepts/llm-model-routing-strategy.md

## [2026-05-10] ingest | HAT Framework Gap Analysis
Source: Please analyze this copy-paste article and let me (1).md
SHA256: ca42050d191bfce1e1d41e56abaa3c90c9506bcb9ad8f762836669c889735910
Content: Six gaps in HAT framework.
Page: wiki/concepts/hat-framework-analysis-gaps.md

## [2026-05-10] ingest | Plugin Installer Setup Guide
Source: README-OPTIMAL-SOLUTION.md
SHA256: 0ffa3573f414d153d26995a84b8017e12b98d75a050f799b09da67aff5ac20ae
Content: Three-step setup for 7 dev plugins with PowerShell audit and bash validation.
Page: wiki/concepts/plugin-installer-setup-guide.md

## [2026-05-10] ingest | Skill-to-Page Template Refactor
Source: should we refactor the skill to make it more effic.md
SHA256: 19f81bfab557f31fbf13e575f0cd0b2ed2edafa94d54edd834a384293b6ed7d1
Content: Template skeletons for index.html instead of freeform regeneration.
Page: wiki/concepts/skill-to-page-template-refactor.md

## [2026-05-10] ingest | /go Skill Ralph Loop
Source: SKILL.md
SHA256: 135ed7d6ca4c625dd6c261afe5e6fd0fffb528688e348140ed11d00cff79b002
Content: Local Ralph loop with per-terminal isolation and atomic step gating.
Page: wiki/concepts/go-skill-ralph-loop.md

## [2026-05-10] ingest | Doc-Compiler Refactor Specification
Source: skill_to_page_refactor_prompt.md
SHA256: 4d822a6dccfa530901b259a06034948c32e4240adb72cbcd01abb8b56a2e38ac
Content: Diagram-aware doc compiler with nine stages and template-based emission.
Page: wiki/concepts/doc-compiler-refactor-prompt.md

## [2026-05-10] ingest | Artifact Pattern for Skill Design
Source: SKILL-artifact-pattern.md
SHA256: 92b8847001dd663e286d0ec8c06b276fa554e54048ffe6aa2319df12f9d016e8
Content: Terminal-isolated state with atomic filesystem flags. Reusable across skills.
Page: wiki/concepts/artifact-pattern-skill-design.md

## [2026-05-10] ingest | LLM Reasoning Failures and Hook Boundaries
Source: The diagnosis is correct.md
SHA256: e01dc0d59b563bbf2da8379179ba928e616e8f46496ceae544ff306676f65c86
Content: Literal entity resolution and unincorporated corrections are reasoning failures.
Page: wiki/concepts/llm-reasoning-failures-hook-mitigation.md

## [2026-05-10] ingest | LangGraph Task Routing
Source: the transcript recommends using smaller &amp; chea.md
SHA256: f78eb53c47cd84335aa286ea88e44ee7df426bd0137bc344fd8616ac321fb1ee
Content: AgentFloor A0-E complexity tiers for model routing.
Page: wiki/concepts/langgraph-task-routing-models.md

## [2026-05-10] ingest | Doc-Compiler Pipeline Debugging
Source: These are different conversation about our doc-com.md
SHA256: 6f81762a19d448fc5deb19cfa629e68652bcd27a3c54c6f762c0d30ed65c3a9a
Content: Runtime bugs, upstream modeling gaps, and process gaps in LLM prompting.
Page: wiki/concepts/doc-compiler-pipeline-debugging.md

## [2026-05-10] ingest | Z.AI Bifrost Provider Integration
Source: This is a conversation with a not very good LLM in.md
SHA256: c4904e83906910e108e43a2db789a9c27e4c31529c7d05bb8ea664fd5b56df05
Content: Z.AI coding plan API different base URL. Manual GLM-5.1 declaration.
Page: wiki/concepts/zai-bifrost-provider-integration.md

## [2026-05-10] ingest | Hook False Positive Cascade
Source: This is history from a system we have been working.md
SHA256: 1333a8f4c8c2b24000bd57eeadae6db5d5527385b8383bf3e467a8422ef5d933
Content: Hooks matching surface keywords without semantic understanding.
Page: wiki/concepts/hook-false-positive-cascade.md

## [2026-05-10] ingest | Skill Enforcement Gate Gap
Source: We are having ongoing problems with claude code no.md
SHA256: 045f6ed0de6707ecd89c771c0df14ab880ed311a407bf96c3951a7c1f501c86d
Content: Gate only checks workflow_steps ignoring enforcement field.
Page: wiki/concepts/skill-enforcement-gate-gap.md

## [2026-05-10] ingest | Mermaid Pane Resize Solution
Source: We are trying to resize the mermaid pane so that I.md
SHA256: ed21c12f7a10a3c5610d7aacbd72f30c0bddd413d2e79974f39d3a7b5b159818
Content: Container lacked height constraint. Added resize with drag handle.
Page: wiki/concepts/mermaid-pane-resize-solution.md

## [2026-05-10] ingest | CLAUDE.md Memory Injection Architecture
Source: We had a conversation related to this subject for.md
SHA256: 2592555de7c09788ab0a6afddcf277d029eabb07f61b3e7f1180cae01bf9b7cc
Content: Three-layer design: baseline rules, just-in-time reminders, enforcement.
Page: wiki/concepts/claude-md-memory-injection-architecture.md

## [2026-05-10] ingest | Skill-Creator Plugin Guide
Source: what does the claude code plugin skill-creator do_.md
SHA256: 2ba4ab491f364cb44a50688f75cabe510c1f5f4b7ece41f7566699fcc4e0fce0
Content: Meta-skill for automated skill creation, testing, evaluation.
Page: wiki/concepts/skill-creator-plugin-guide.md

## [2026-05-10] ingest | Tokio Prompt Orchestrator Hooks
Source: what does this mean for claude code_ _Best practic.md
SHA256: b73a117c04ce6cdabbb82b438d906adc85136b02f7738c92e7c37172f4209229
Content: Rust async orchestration with 10 hook points across 5 stages.
Page: wiki/concepts/tokio-prompt-orchestrator-hooks.md

## [2026-05-10] ingest | NSE and Q Skill Decomposition
Source: What domains are being expressed in these decompos.md
SHA256: 64f80c3be5f7bfc3c891ccfc522eb7f61793f9b220d1db7ff79751ae208356cd
Content: 22 components across /nse (7) and /q (15). Gaps in task backlog and RCA documentation.
Page: wiki/concepts/nse-q-skill-decomposition-domains.md

## [2026-05-10] ingest | QMD Web Ingestion Workflow
Source: In claude code qmd ingesting files.md
SHA256: 150d01a098ba8110436041f7adce3cac5b00483ddcee1211c117dffcf5166e14
Content: QMD web ingestion pipeline using Firecrawl/Playwright.
Page: wiki/concepts/qmd-web-ingestion-workflow.md

## [2026-05-10] ingest | Claude Code Stop Hook Claim Enforcement
Source: In claude code we are a little stuck.md
SHA256: f3808ff7a97bf65d2c84a9d03a0c2c42845c4f44ea0ffa783781453a11685472
Content: Stop hook claim verification traps and causal claim gap.
Page: wiki/concepts/claude-code-stop-hook-claim-enforcement.md

## [2026-05-10] ingest | LM Studio RAG Configuration on Windows
Source: in lmstudio on windows.md
SHA256: b48c616a6ac74cbe61380f4dfb8f75b4c21fbb51a7eb9092b289a706b354ce0f
Content: LM Studio built-in RAG and Big RAG plugin setup.
Page: wiki/concepts/lmstudio-rag-setup.md

## [2026-05-10] ingest | TLDR Pages Repository
Source: is there a tldr repo_.md
SHA256: 507147ea8ed01f031c2bfcb535d5e16173c7e56f872c794799dfc1e05136d99e
Content: tldr-pages/tldr canonical repository and clients.
Page: wiki/concepts/tldr-pages-repository.md

## [2026-05-10] ingest | Claude Code Plugin Skill Namespacing
Source: Is there a workaround in claude code.md
SHA256: 7c95aef521d41b62f457cd8b2ee3c68cd152b379eb4121c985936bbe0cac90fa
Content: Plugin skill namespacing and autocomplete bug.
Page: wiki/concepts/claude-code-plugin-skill-namespacing.md

## [2026-05-10] ingest | Browser Session Architecture NotebookLM
Source: Let me know browser automation.md
SHA256: ba5bc8e45558d9f9632b43cc889b64f12066418ed7e79d6432b003de0f71e082
Content: Playwright automation profile for NotebookLM DOM testing.
Page: wiki/concepts/browser-session-architecture-notebooklm.md

## [2026-05-10] ingest | LLM Hallucination in Debugging RCA
Source: LLM_1 says this about LLM_2.md
SHA256: a939fc368f9d46c89a1bf7a65e71ede5225803034978bed3aa51855943cde23d
Content: Cross-model debugging RCA showing fabrication.
Page: wiki/concepts/llm-hallucination-debugging-rca-analysis.md

## [2026-05-10] ingest | Plugin Installer Setup Manifest
Source: MANIFEST.md
SHA256: 19dd16e5d30b0cab3205784e16bcb4b0dcc2190c09a768560a2ed6ec9b95ad8f
Content: Plugin installer deployment manifest.
Page: wiki/concepts/plugin-installer-manifest.md

## [2026-05-10] ingest | Diagram-as-Code Standards Comparison
Source: Mermaid diagrams software architecture.md
SHA256: 2b7ce5bfc6d5f254bed9f65e3407796d7f5c43f8b63f5719924ec69885d98742
Content: Mermaid vs Excalidraw vs D2 vs PlantUML.
Page: wiki/concepts/diagram-standards-comparison.md

## [2026-05-10] ingest | Design Review Reasoning Bookend Rule
Source: My design skill lazy errors think 1.md
SHA256: e0ecb18cba33c8899c4016cdffa1c13fb83fc86e55ea0e83245ac25886ac5200
Content: Premature bug call with bookend rule fix.
Page: wiki/concepts/design-review-reasoning-bookend-rule.md

## [2026-05-10] ingest | LangGraph Skills Orchestration
Source: My design skill lazy errors think 2.md
SHA256: 0650ddf7e13d184b8024f3430af0b29ee7325a17a02549d6189e2d5ec05f0639
Content: Skills with embedded scripts outperform pure LLM.
Page: wiki/concepts/langgraph-skills-orchestration-benchmarks.md

## [2026-05-10] ingest | Design Review Bookend Rule System
Source: My design skill lazy errors think.md
SHA256: 31fb8d0a742ada2f33beab7aa6cd0e13d1ea8f768dc7b806acc6d10afee8f8e9
Content: Operationalizing bookend rule as system guardrail.
Page: wiki/concepts/design-review-bookend-rule-system.md

## [2026-05-10] ingest | LLM CSS Layout Verification Failure
Source: My LLM says this wrong.md
SHA256: 46385a56b5bda6310e4e31a2ef1e8971a522a1bc17108c64f1cd058887176a1d
Content: Skill-to-page self-referential bug cycle.
Page: wiki/concepts/llm-css-layout-verification-failure.md

## [2026-05-10] ingest | NotebookLM YouTube Quality Prompts
Source: notebooklm-youtube-quality-prompts.md
SHA256: d3766899ad9edc9d78e16a280a79465685898f21ef6127ad0016e55b1f1a0c87
Content: Five prompts for YouTube quality scoring.
Page: wiki/concepts/notebooklm-youtube-quality-prompts.md

## [2026-05-10] ingest | NotebookLM YouTube Scam Detection
Source: notebooklm-youtube-scam-prompts.md
SHA256: e9438ef9b24d633415eb31503596f00870232c60f0f3a57c312acbd1a643717d
Content: Five prompts for scam and fake engagement detection.
Page: wiki/concepts/notebooklm-youtube-scam-detection-prompts.md

## [2026-05-10] ingest | NotebookLM yt-dlp Quality Playbook
Source: notebooklm-yt-dlp-quality-playbook.md
SHA256: cb3edac659b21591e7d9c2d389112d890aea8addfe7c991d19cf6a6962a40aa9
Content: Batch YouTube analysis pipeline with yt-dlp.
Page: wiki/concepts/notebooklm-ytdlp-quality-playbook.md

## [2026-05-10] ingest | NotebookLM yt-dlp RedFlags Proxy
Source: notebooklm-ytdlp-redflags-proxy-guide.md
SHA256: e02e1ce99e940088c777538226d18b03dab02cf4502f2c0a5118cc245d7d2c40
Content: Red-flag prompts and proxy rotation scaling.
Page: wiki/concepts/notebooklm-ytdlp-redflags-proxy-guide.md

## [2026-05-10] ingest | Plugin Installer Copy-Paste Setup
Source: OPTIMAL-SETUP-COPY-PASTE.md
SHA256: 5f2ce0dd70f68d8e4dfed86a2255b3e3f7c6ddf1095ca1b2e58a8f471dc20ac7
Content: Quick copy-paste deployment of 7 plugins.
Page: wiki/concepts/plugin-installer-copy-paste-setup.md

## [2026-05-10] ingest | Programming Fonts Comparison
Source: page-2026-04-19-11-13-08.md
SHA256: 29682c1b340692083cfb14d3b6cced80cc494cd7731dcaca32ebff3ac68ed1b3
Content: Free programming font comparison for eye strain.
Page: wiki/concepts/programming-fonts-comparison.md

## [2026-05-10] ingest | Claude Code Memory Plugins
SHA256: b073729ede9b7c53c854378080bdfe01df7e0c9236670b21d315603634446641
Content: remember and claude-mem plugins for persistent context, token efficiency, and common issues.
Page: wiki/concepts/claude-code-memory-plugins-remember-and-claude-mem.md

## [2026-05-10] ingest | GitHub Pull Requests Guide
SHA256: 3e9b9dbe1b37ac384e9db76e953313415381d91c62225b491836beb26cd037a9
Content: Full PR guide covering core components, PR vs MR, solo developer LLM SDLC integration, review best practices.
Page: wiki/concepts/github-pull-requests-guide.md

## [2026-05-10] ingest | GitHub PR Fundamentals
SHA256: ba313f217af0c5449058ee9559454ef4b14178e2a4003910dd6424d5c440b206
Content: PR basics: workflow, advanced features, review process, PR vs merge request.
Page: wiki/concepts/github-pr-fundamentals.md

## [2026-05-10] ingest | Claude Code Focus Mode
SHA256: 9e6911bf362a2e789503cb88880950d8e7f7de1b78d3b9729ef2e81205e934d2
Content: Focus mode as viewMode setting with three modes, configuration via /config, availability caveats on Windows.
Page: wiki/concepts/claude-code-focus-mode.md

## [2026-05-10] ingest | Gemini CLI Integration with Claude Code
SHA256: ed13b8bb6db7ae27fe75044df6e7eb85a0420ca3fb517d717eeebb7b862f4fe1
Content: Public repos wiring Gemini CLI into Claude Code via MCP, integration toolkits, multi-model workflows.
Page: wiki/concepts/gemini-cli-in-claude-code-integration.md

## [2026-05-10] ingest | Git Index Lock and Concurrent Access Recovery
SHA256: 1bdc671dfe8fe9445336551d8ce9a58823735809d8040a7f02b2726084605552
Content: Git index.lock root causes (concurrent access), submodule status codes, safe recovery path for monorepos.
Page: wiki/concepts/git-index-lock-concurrent-access-recovery.md

## [2026-05-10] ingest | Preventing Skill File Deletion Gaps
SHA256: a4a7d799fd2de7ed0222c19a45298942fa5a35f544681dd962e6ef74d30ef872
Content: Prevention layers for skill file deletion: audit scripts, guard skills, pre-commit hooks, two-phase playbooks.
Page: wiki/concepts/skill-file-deletion-prevention-guardrails.md

## [2026-05-10] ingest | Design Reference Template Extraction
SHA256: 734570553aa92dc6c83bdd538f44825556a9193899521e323e59d9e2f23068a8
Content: Prompt engineering for extracting reusable design templates, avoiding shallow mimicry and over-engineering.
Page: wiki/concepts/design-reference-template-extraction.md

## [2026-05-10] ingest | Claude Code /simplify Command
SHA256: 0e3699414e5926ff6ff1751ed708b14df3b155c0aac8815879c05b17745d105c
Content: /simplify as internal command, relationship to public code-simplifier agent, lifecycle domain.
Page: wiki/concepts/claude-code-simplify-command.md

## [2026-05-10] ingest | OpenAI Codex Windows 11 Troubleshooting
SHA256: 96f71b62dd6a82770b752243030a5f6bb71a83bfac81c4203290c3aa84325484
Content: Shell initialization failures, PowerShell conflicts, ripgrep blocking, prioritized fixes for Codex on Win11.
Page: wiki/concepts/openai-codex-windows-11-troubleshooting.md

## [2026-05-10] ingest | LLM Overconfidence and Structural Assessment Failures
SHA256: 6d55b5002353da1b19d6da98fa806a7522c17a9e9adb4a6d0fa6a1a5ec29703f
Content: Three root causes of LLM overconfidence (vocabulary mismatch, dead code, advisory vs enforcement).
Page: wiki/concepts/llm-overconfidence-and-structural-assessment-failures.md

## [2026-05-10] ingest | LangGraph Compare Service with Bifrost
SHA256: ac4bbdba337032f39f56191315ccd636411bd7b4ee9997f91c44480be6846ccb
Content: LangGraph StateGraph for parallel multi-model comparison via Bifrost with fan-out workers and result synthesis.
Page: wiki/concepts/langgraph-compare-service-bifrost.md

## [2026-05-10] ingest | SDLC Skill Stack - /code, /design, /planning, /go
SHA256: a5d6d0f1e77cc927cf1289e3c971aa66a22175a683c57e1e613443a93bb4225f
Content: Four-skill SDLC stack: /go (worktree), /design (CAPs), /planning (plans), /code (TDD orchestrator).
Page: wiki/concepts/sdlc-skill-stack-code-design-planning-go.md

## [2026-05-10] ingest | Producer-Consumer Contract Testing for LLM Handoffs
SHA256: 477289bfa56acb870d682783bed53e05fcdafc256f6aeb7f818ae31673bfe731
Content: Contract Testing (CDC) for LLM session handoffs, preventing missing envelope fields via Pydantic validation.
Page: wiki/concepts/producer-consumer-contract-testing-for-handoffs.md

## [2026-05-10] ingest | Hook Over-Enforcement and Epistemic Gate Refactoring
SHA256: acb9d933e7554d44a4a5f47fe5249038896081d6be033b5b0c605c3fe7ed5317
Content: Epistemic format hooks blocking architecture reasoning, root causes, refactor target.
Page: wiki/concepts/hook-over-enforcement-and-epistemic-gate-refactoring.md

## [2026-05-10] ingest | Hook Refactoring Audit Checklist
SHA256: 4cb2760eb4b388196192c19243a6936c2097c468ef06df042626a3338f10aba5
Content: Audit checklist for hook refactoring: inventory, policy files, runtime overrides, failure corpus.
Page: wiki/concepts/hook-refactoring-audit-checklist.md

## [2026-05-10] ingest | YouTube Ingestion Throughput Bottleneck Analysis
SHA256: 734570553aa92dc6c83bdd538f44825556a9193899521e323e59d9e2f23068a8
Content: NotebookLM ingestion bottleneck in source addition phase (588-1051s), workers sequential despite parallel arch.
Page: wiki/concepts/youtube-ingestion-throughput-bottleneck-analysis.md

## [2026-05-10] ingest | NVIDIA NIM Free Model Access
Source: I have a nvidia key.  How can I find out easily (c.md
SHA256: badf9552cb5d0a26fd0aee9271c22894c05d50f55b5446eaabfe85a158ca8a62
Content: NVIDIA NIM free API key access to 150+ serverless models; nimping CLI for batch checks.
Page: wiki/concepts/nvidia-nim-free-model-access.md

## [2026-05-10] ingest | Iterative LLM Review Automation
Source: I have LLM_A (claude code), and LLM_B (codex).  I.md
SHA256: fff4bec5eb460165069ea9526eb1b2907082a6bc5f2a60624c93453efffed540
Content: Multi-agent review frameworks for Claude/Codex ping-pong; convergence via edit distance.
Page: wiki/concepts/iterative-llm-review-automation.md

## [2026-05-10] ingest | MiniMax M2.7 Bifrost Integration
Source: I want to use my minimax token plan with bifrost a.md
SHA256: ee794d02c59c2bf6e1869aa239087a3bb1ccae2acce05cc7eaf28194ce8564eb
Content: M2.7 on MiniMax platform but missing from Bifrost; manual custom provider workaround.
Page: wiki/concepts/minimax-m27-bifrost-integration.md

## [2026-05-10] ingest | NotebookLM Batch Size Experiment
Source: I am talking to claude code but I do not think it is.md
SHA256: 473ab9dd3b5b0f9b1842408da3411bf125e8cd921f194d638cc03dfac784a7e2
Content: LLM reasoning failure attributing elapsed_s to yt-dlp; 225 per-request limit; hook gap.
Page: wiki/concepts/notebooklm-batch-size-experiment.md

## [2026-05-10] ingest | Hook Noise Reduction Strategy
Source: I am working in claude code and we have hooks that.md
SHA256: abbd63e57fe1439d50bf080c59719692e73345e3cdbd2b8f0239cf19f1ea3294
Content: Treat hooks as alerting system; hard vs soft split; suppression tree; confidence scoring.
Page: wiki/concepts/hook-noise-reduction-strategy.md

## [2026-05-10] ingest | Artifact Pattern Implementation
Source: IMPLEMENTATION-GUIDE.md
SHA256: 2eb3945093eb19a1c8a59bd52c0a7091b42943ce726598bf3cf66ac758e696aa
Content: Artifact state-flag pattern for /go skill; per-terminal isolation; atomic step gating.
Page: wiki/concepts/go-artifact-pattern-implementation.md

## [2026-05-10] ingest | Silent Stop Hook Limitation
Source: in Claude Code Is it really impossible to have sil (1).md
SHA256: d2f9bdbd74f1f1a02cc2396ed0122ea56d3f564774ebc9876e6e83337fb1eae0
Content: Stop hook has no silent-block mode; move formatting to UserPromptSubmit.
Page: wiki/concepts/silent-stop-hook-limitation.md

## [2026-05-10] ingest | Silent Stop Hook Analysis Extended
Source: in Claude Code Is it really impossible to have sil (2).md
SHA256: 8bb9b9a58dbdd14fbf03738eb05e53f702d0b2e59fd2fdbd279e7fb26352cd06
Content: Extended analysis; three enforcement tiers; UserPromptSubmit architecture.
Page: wiki/concepts/silent-stop-hook-analysis-v2.md

## [2026-05-10] ingest | Silent Stop Hook Original Query
Source: in Claude Code Is it really impossible to have sil.md
SHA256: ae092848437a7c4fcd4ed92d2e5f559532cba4fd8cf79389efbd194bb33e2a33
Content: Original query; confirms impossibility; upstream enforcement recommended.
Page: wiki/concepts/silent-stop-hook-original-query.md

## [2026-05-10] ingest | Relative Import Fix skill-guard
Source: in claude code on windows 11 does this proposal m.md
SHA256: f22edd3ad1fd92aa75c13d512b56fff09264f5bd4e34e4b66b2fc52d59507211
Content: ImportError from relative imports in hooks.json; fix is absolute imports.
Page: wiki/concepts/relative-import-fix-skill-guard.md

## [2026-05-10] ingest | OpenCode SQLite Sequential Dispatch
Source: In claude code on windows 11 is this true Su.md
SHA256: 2318fdb7ca5995653d91ac9383810444acdc5f329b994e5b9317c86d83040058
Content: SQD dispatch converted to sequential due to SQLite lock.
Page: wiki/concepts/opencode-sqlite-sequential-dispatch.md

## [2026-05-10] ingest | Windows 11 Silent Edit Failures
Source: In claude code on windows 11 this is a critical p.md
SHA256: f518998e85ad05054d82303fb109abdf93fdb24bf338adea9cbbbc7a867d687c
Content: Silent file write failures on Windows 11; post-edit verification loops.
Page: wiki/concepts/windows-11-silent-edit-failures.md

## [2026-05-10] ingest | Discovering All Hooks Sources
Source: In Claude code they have hooks. They can be global.md
SHA256: bd54dac06160ed0f1e2abe062676bad569e57b36c4661986ff7478cfea6c5a0b
Content: Six hook sources; discovery prompt strategy; 24-26 events.
Page: wiki/concepts/discovering-all-hooks-sources.md

## [2026-05-10] ingest | Skill Self-Verification via Hooks
Source: In claude code how can we solve this skill self-v (1).md
SHA256: bd2920695e49b45040ba7d73aef3c3232e34060be79f96c3ef8110a62afcd495
Content: 4-component self-verification: state file + PreToolUse + PostToolUse + Stop.
Page: wiki/concepts/skill-self-verification-hooks.md

## [2026-05-10] ingest | Auto-Stage and Commit Strategies
Source: in claude code I want to auto-stage and commit A.md
SHA256: fdd8ec715d716583c8e82e39bc255e7c2851d7ddc67a5556a10024b3e536794b
Content: Three approaches: CLAUDE.md, PostToolUse hook, Stop hook.
Page: wiki/concepts/auto-stage-commit-strategies.md

## [2026-05-10] ingest | Prompt Chaining Best Practices
Source: In Claude code I would like to learn about prompt.md
SHA256: 09dfbe40b67a1b79af6caa48dbcd11194a2e3e320c72a03db8a1596f91ede88a
Content: Six design principles; structured handoffs; validation loops; branching.
Page: wiki/concepts/prompt-chaining-best-practices.md

## [2026-05-10] ingest | Context Injection Memory Errors
Source: in claude code I am trying to create a useful cont (1).md
SHA256: 76a752805bb48f704f8caceba4d1d5bec0126b9df1b226ee40d323b84e074eac
Content: Three mistakes about hook API; only command hooks exist; no programmatic routing.
Page: wiki/concepts/context-injection-memory-system-errors.md

## [2026-05-10] ingest | Context Injection GTO Pipeline
Source: in claude code I am trying to create a useful cont.md
SHA256: cc9fa1c0a2664e42b307db046778ef94209f73d85a0d6d1c74830c1afddcdf06
Content: GTO health score 20; schema contradiction; unactioned recommendations.
Page: wiki/concepts/context-injection-gto-pipeline-issues.md

## [2026-05-10] ingest | QMD Web Ingestion Tools
Source: In claude code I am using qmd for ingesting files (1).md
SHA256: a5b634b5a91d74052c5d5704f87beee735abb69f3d91824ac672f6ee04fe786d
Content: QMD web ingestion pipeline; tool stack: curl, Playwright, Firecrawl.
Page: wiki/concepts/qmd-web-ingestion-tools.md
## [2026-05-10] ingest | Artifact Identity Mismatch Remediation
Source: deep-research-report (3).md
SHA256: 00063c0b5a27055ca52168d3ea2da7bd53da2a57207a7e8b6267ada6131c118a
Content: Remediation plan for artifact identity mismatch in Claude Code where broad search returns wrong sibling skill results
Page: wiki/concepts/artifact-identity-mismatch-remediation.md

## [2026-05-10] ingest | yt-is Throughput Bottleneck Diagnosis Prompt Review
Source: deep-research-report.md
SHA256: b64cb064f2e7b7ef34828002ff9a7fa93340987c25b51bb43078399ed54772fd
Content: Analytical review of a diagnostic prompt for yt-is video ingestion pipeline throughput bottleneck
Page: wiki/concepts/yt-is-throughput-bottleneck-diagnosis.md

## [2026-05-10] ingest | NotebookLM Bulk Deletion Automation
Source: delete all notebooks that have the _worker_ in the.md
SHA256: 73fd53abf728b2e4fc5c3186b08cfe5adeeee9f7c8bf3e1da06d96bf5ea34c17
Content: Browser console script and Chrome extension architecture for bulk-deleting NotebookLM notebooks by title filter
Page: wiki/concepts/notebooklm-bulk-deletion-automation.md

## [2026-05-10] ingest | Plugin Installer Deployment Guide
Source: DEPLOYMENT.md
SHA256: 9267d0bf47547b476b560ad7e2f6fabe71aae99bf4d0cd447389d533c122cd47
Content: Three-option deployment guide for creating plugin-installer skill in Claude Code marketplace
Page: wiki/concepts/plugin-installer-deployment-guide.md
## [2026-05-10] ingest | Plugin Installer Deployment Checklist
Source: DEPLOYMENT-CHECKLIST.md
SHA256: f0d6337ab05bf937623f0aea394be098b98f728907317aaf7b17936cefac331a
Content: Pre-flight through post-flight checklist for deploying plugin-installer skill and verifying 7 marketplace plugins
Page: wiki/concepts/plugin-installer-deployment-checklist.md

## [2026-05-10] ingest | Diagnose Skill Complete Implementation Package
Source: diagnose-complete-implementation-package.md
SHA256: 06a6e32604df30d16a6afbd35c211e9ca4faac38e56ffd1093353d2622100438
Content: Implementation spec for diagnose skill as policy-driven orchestrator over Python analyzers agents hooks and machine artifacts
Page: wiki/concepts/diagnose-skill-implementation-package.md

## [2026-05-10] ingest | Intelligence Stream Pipeline Repo Survey
Source: Do repos exist for the _intelligence stream_ descr.md
SHA256: c5526b9d68863846cf18753772d1f8351cdaa8ce60b57b7935cea8ee9a6cfd4c
Content: Survey of existing repos for YouTube intelligence stream pipeline and missing orchestration layer
Page: wiki/concepts/intelligence-stream-repo-survey.md

## [2026-05-10] ingest | Doc-Compiler Skill Specification
Source: do the needful so that we have a full working impl.md
SHA256: 715f6be063515a34befa678dc832f60a56b0be5a30d11b3a2cdf7adb211d2381
Content: Complete spec for doc-compiler skill compiling skills/plugins into interactive diagram-aware HTML documentation
Page: wiki/concepts/doc-compiler-skill-specification.md

## [2026-05-10] ingest | Mermaid SVG Race Condition and Theme Toggle Fix
Source: Do you agree with this result___The skill generate.md
SHA256: 31d4d190114d781eed8ca1f8f414312530f3f91e38949189f31c29aaf6131760
Content: Forensic breakdown of three JS failure points in Mermaid diagram rendering race condition DOM destruction state loss
Page: wiki/concepts/mermaid-svg-race-condition-fix.md
## [2026-05-10] ingest | YouTube Channel Quality Evaluation for Intelligence Stream
Source: Do you think any of these channels are low quality (1).md
SHA256: b3975ccea3d371bea247b2c5201ac34cffaf99c927f930d91eb7c26f9996295a
Content: 94 YouTube channel URLs for quality evaluation as part of intelligence stream content curation pipeline
Page: wiki/concepts/youtube-channel-quality-evaluation.md

## [2026-05-10] ingest | Plugin Loading Failure Root Cause Analysis
Source: Does this make sense_  __  Problem Statement_ reas.md
SHA256: bbbd024d76926ad4048e9e36f2ddf297a3fbd725ab59d379712f76a2f71df8eb
Content: Root cause analysis of reason_openai_v4.0 plugin loading failure registry entry cache location enabled toggle
Page: wiki/concepts/plugin-loading-failure-diagnosis.md

## [2026-05-10] ingest | Reasoning Hygiene Hooks Evaluation
Source: Does this seem like a good idea given the problems (1).md
SHA256: 93f9e8b6d73f9abc62fc51395026299e88f904f7ab7e1e434683daa914cf964f
Content: Evaluation of regex-based Stop hooks for reasoning hygiene and alternatives self-critique local LLM verification
Page: wiki/concepts/reasoning-hygiene-hooks-evaluation.md

## [2026-05-10] ingest | Bifrost MCP Filesystem Setup Plan
Source: exported-assets (4)/script.md
SHA256: a28b115fcb4fc40e809dd69f9784e29930a76bb92d1492ce8abee0cbaaadf6d5
Content: Step-by-step setup plan for Bifrost + MCP filesystem + Claude Code on Windows 11 via WSL2
Page: wiki/concepts/bifrost-mcp-filesystem-setup-plan.md

## [2026-05-10] ingest | BF Dispatcher and V3 Service Implementation
Source: exported-assets (4)/script_1.md
SHA256: f3964756ac7e0034d71b68e7697aec2e0f85a7da44bbc65e25cd74a2fae696d8
Content: Complete implementation of /bf skill dispatcher and bf_v3_service.py FastAPI+LangGraph orchestration service
Page: wiki/concepts/bf-dispatcher-and-v3-service.md
## [2026-05-10] ingest | Bifrost Setup Quick Reference Checklist
Source: exported-assets (7)/bf_files.md
SHA256: 4f2b8db14bbbcd90d04af90957babdd9baff4040869f2e6aa597eab0db71c900
Content: Structured JSON plan and quick-start checklist for Bifrost + MCP Filesystem + Claude Code setup
Page: wiki/concepts/bifrost-setup-checklist.md

## [2026-05-10] ingest | Plugin Install Facts and Reality Gap Analysis
Source: FACTS-AND-REALITY.md
SHA256: 67ed58fb8f98f0be9cfe54a4eeeb5de82cf7623b7c4322cf9660e07a1d1a386e
Content: Gap analysis comparing requested bash plugin installs vs delivered with 3 specific gaps and current plugin status
Page: wiki/concepts/plugin-install-facts-and-reality.md

## [2026-05-10] ingest | NTP TDD Enforcement System v2.0 Changelog
Source: files/CHANGELOG.md
SHA256: b641528a37ce627b07641ab5a88ddfece58807275c6ab9d28179fb74c2bd19bb
Content: 12 fixes for NTP TDD enforcement cross-process env vars HMAC bypass retry corruption validation hardening
Page: wiki/concepts/ntp-tdd-enforcement-v2.0-changelog.md

## [2026-05-10] ingest | NTP TDD Enforcement System v2.1 Changelog
Source: files (1)/CHANGELOG-v2.1.md
SHA256: 223d9285b071cd36c565d75b6e883ec4449c124d1f8cdd8c8bf992254b8177e7
Content: 5 external review fixes preflight session-aware bypass validator-owned test execution per-session HMAC refactor enforcement
Page: wiki/concepts/ntp-tdd-enforcement-v2.1-changelog.md

## [2026-05-10] ingest | NTP TDD Enforcement System v3.1 Review
Source: files (2)/REVIEW-AND-CHANGELOG.md
SHA256: bbf3eb04d3d1c5f0d2df93a35fb80a0dcb2c4d7b66db287bad6c949328fa4790
Content: Review of v3 draft 2 crashes 5 logic bugs 1 security regression HMAC dropped 3 regressions from v2.1
Page: wiki/concepts/ntp-tdd-enforcement-v3.1-review.md

## [2026-05-12] ingest | Bash Security Agentic Safety Model
Source: YouTube — "[CLAUDE CODE] Agentic Bash Security: 5-Level Risk Framework"
SHA256: b25f22f771c16808a78f065310aef8500eb224856b7bb6cbfcc8e010885db17e
Content: 5-level bash execution model: user prompt → system prompt → blacklist → whitelist → no-bash. Risk compounds with runtime.
Page: wiki/sources/spec-bMQ54XHGRdM.md

## [2026-05-12] ingest | Pi Agent TypeScript Extension Guards
Source: YouTube — "[CLAUDE CODE] Pi Agent Sandbox: TypeScript .pie/ Extension"
SHA256: 7f16572f9f391abe2e867fef1f6716d0c3f19db89e9c458bb3580b62ecb48230
Content: TypeScript tool restriction via .pie/ extension guard functions. Guard predicates enforce tool restrictions at runtime.
Page: wiki/sources/spec-1ZsFjM6yZGI.md

## [2026-05-12] ingest | AIOS 5-Tier Cross-Model Failover Architecture
Source: YouTube — "[CLAUDE CODE] AIOS Failover: Cross-Model Resilience Architecture"
SHA256: 0d351d5622accb33c3ffa4732ab246e7a673929317dcb725eded21a4888b2d21
Content: Context → Skills/Agents → MCP/APIs → Interface → Runtime. Cross-model failover testing validates each tier degrades gracefully.
Page: wiki/sources/spec-JBaUXDRtRek.md

## [2026-05-12] ingest | Parallel Worktrees 5-Pillar System
Source: YouTube — "[CLAUDE CODE] Claude Code Parallel Worktrees: 5-Pillar System"
SHA256: 12fb035c5661be68ccf1cf6c2995e338438fba5756852d916784e22513e29687
Content: 5 pillars: Issue-as-Spec, Git Worktree Isolation, Fresh-Context Validation, Multi-Agent Review, Self-Healing Layer.
Page: wiki/sources/spec-rFGlJ4oIlhw.md

## [2026-05-12] ingest | 7-Level Memory Stack
Source: YouTube — "[CLAUDE CODE] 7-Level Memory Stack for AI Agents"
SHA256: 3b43e09ba9e4d741df350a68ab7f0ff198f600b24b4b4743cb4b756f7a7b0bdb
Content: Identity, Critical Context, Working Memory, Long-Term + Episodic, Decay, Promotions, Semantic + Keyword + Entity. Memory Architect skill.
Page: wiki/sources/spec-OMkdlwZxSt8.md

## [2026-05-12] ingest | Karpathy LLM KB Compiler Analogy
Source: YouTube — "[CLAUDE CODE] Karpathy LLM Knowledge Base: Compiler Analogy"
SHA256: b35f5f64cc5d3940672c33278ee6b2b44fa23dbc19be9dc6c6425bc0198a2d80
Content: Raw markdown (source) → LLM (compiler) → executable (wiki). Internal KB: session logs → daily logs → concepts → wiki.
Page: wiki/sources/spec-7huCP6RkcY4.md

## [2026-05-12] ingest | AI Newsroom Telegram Pipeline
Source: YouTube — "[CLAUDE CODE] AI Newsroom: Telegram Pipeline"
SHA256: 2d92cd30932edb7136002333f6cb8b4ec9a6e817c3dd2970238b6fa6b2f2bdfd
Content: 9-component pipeline: CC Claw multi-model, Telegram control, News scanner, Skill + Context separation, Perplexity MCP fact-check, Buffer MCP cross-post.
Page: wiki/sources/spec-C-L0xk7Uuko.md

## [2026-05-12] ingest | Senior Dev AI Workflow
Source: YouTube — "[CLAUDE CODE] Senior Dev AI Workflow"
SHA256: 9ef70aa643de3c99e60585996f9ad6703dc1e9f212690f066790403d6056a3bf
Content: Parallel worktrees + PR review + Karpathy KB. 5 pillars with self-healing layer. Claude Code hooks: SessionStart/PreCompact/SessionEnd.
Page: wiki/sources/spec-t1bWyk9qVa4.md
## [2026-05-24] ingest | YouTube Ingestion Throughput Bottleneck Analysis
Source: C:\Users\brsth\Downloads\YouTube Ingestion Throughput Bottleneck Analysis.md
SHA256: 01016b208ba9cac989bfea5ca7c4da5515af3bc05c08e2abb51a478ae0b0e484
Content: Root cause analysis of yt-is NotebookLM pipeline bottleneck — warm-worker strategy counterproductive, profile contention on Windows, non-linear vector re-indexing, metric aggregation artifacts, ephemeral worker recommendation.
Page: wiki/concepts/youtube-ingestion-throughput-bottleneck.md


## [2026-05-24] ingest | Popular Claude Code Plugins and Skills
Source: C:/Users/brsth/Downloads/what are very popular plugins or skills or repos f.md
SHA256: 6377631270fe8b022d3ab132be293fc1efac77182ed863961095201afa44c26e
Content: Popular Mermaid and diagram plugins/skills for Claude Code -- Mermaid skill (johnlarkin1), Mermaid Tools (daymade), veelenga/claude-mermaid MCP, awesome lists, 6 theme presets, making diagrams attractive guide.
Page: wiki/concepts/popular-plugins-skills-repos.md

## [2026-05-24] ingest | Frustrating Experience RCA
Source: C:\Users\brsth\Downloads\This is an rca about a frustrating experience with.md
SHA256: b8f5b82fdf0f6fb8008247020662aa1a4d9a84c80890edf037d49633bafa35c8
Content: RCA for 11-minute session where LLM fixed intra-section padding without detecting root cause (3-space cross-section indent offset in cc-bifrost.ps1). Root cause: missing reasoning-depth enforcement gate in Stop.py IN_PROCESS_GATES; response_too_short early-return at line 2705 allows shallow micro-turns.
Page: wiki/concepts/frustrating-experience-rca.md

## [2026-05-24] ingest | LLM Inference Providers List
Source: C:\Users\brsth\Downloads\Here's a list of inference providers for LLMs.  Sh.md
SHA256: ba821f33ff191949718f142443fff67eb13033e20087adf394b9f3479696aa4b
Content: Curated list of 19 LLM inference providers with model IDs, SDK docs, cookbooks, and implementation repos. Plus 27 essential SDKs for local knowledge store.
Page: wiki/concepts/llm-inference-providers-list.md

nSource: chain_20260524_115434.mdn

## [2026-06-30] ingest | Coding-Plan Subscription Quota APIs
Source: chat-session 2026-06-30
SHA256: 62ee3c8b6804ce6fc689fac52f606100964bb785b87713804a9da8c977c9bf2f
File: concepts/coding-plan-quota-apis.md

## [2026-06-30] ingest | CDP-Attached Browsers Blocked at Google OAuth Consent
Source: chat-session 2026-06-30
SHA256: d900f4e02bf213e32fa85fe25b6658922d52d1aeb88677e4880ded91cc734fc1
File: concepts/cdp-google-oauth-automation-block.md

## [2026-07-01] ingest | llama.cpp CUDA Build for Blackwell RTX 5070 (sm_120)
Source: session-wiki-ingest-2026-07-01
SHA256: newly-created-2026-07-01
File: concepts/llama-cpp-blackwell-build.md

## [2026-07-01] ingest | llama.cpp --cpu-moe MoE Expert Offloading
Source: session-wiki-ingest-2026-07-01
SHA256: newly-created-2026-07-01
File: concepts/llama-cpp-moe-cpu-offload.md

## [2026-07-01] ingest | Local LLM System RAM Exhaustion on 64GB Windows 11
Source: session-wiki-ingest-2026-07-01
SHA256: newly-created-2026-07-01
File: concepts/local-llm-system-ram-impact.md

## [2026-07-03] ingest | Debrief 2026-07-03 — chs export, plugin-audit, CCR router findings
Source: 2026-07-03 [chs #1060 #1062 · plugin-audit #1061 · docs #1058 · detector #983].md
SHA256: sha256:9e242ff357e0cdbd308e3fccab1c4c09dd5702a8c0aa44e195ee79e9da33aeb1
File: concepts/debrief-2026-07-03-chs-plugin-audit-router.md


## [2026-07-04] ingest | ADR: Derived-Data Location Policy — daemon relocation to P:/.data/daemon
Source: session-2026-07-04-daemon-relocation
SHA256: newly-created-2026-07-04
File: concepts/adr-derived-data-location-policy-20260704.md

## 2026-07-04
- **Claude Code Docs, Guides & Best Practices | ClaudeLog** (P:\.data\wiki\sources\claudelog.com\000-.md)
  - URL: https://claudelog.com/
  - SHA256: 4d12ef6e6aa0f52d12a53863f50d28a7565f168ff25e4678b07f26cdd94a243f
  - Source: crawl-ingest

## 2026-07-04
- **Claude Code Docs, Guides & Best Practices | ClaudeLog** (P:\.data\wiki\sources\claudelog.com\000-.md)
  - URL: https://claudelog.com/
  - SHA256: e4f2890caf2d0ed56e6725cf6e21c4da26fcac1a85681d2d987ab569d0f64dcc
  - Source: crawl-ingest

## 2026-07-04
- **Support ClaudeLog | ClaudeLog** (P:\.data\wiki\sources\claudelog.com\001-support-claudelog.md)
  - URL: https://claudelog.com/support-claudelog
  - SHA256: 8e8289e7e256c8455895a85942f98efd86cd918f9d5c600a7055f2763ab5b970
  - Source: crawl-ingest

## 2026-07-04
- **Install Claude Code | ClaudeLog** (P:\.data\wiki\sources\claudelog.com\002-install-claude-code.md)
  - URL: https://claudelog.com/install-claude-code
  - SHA256: 2e9062c1eab1f80bb901de400214527d1480df9c04df5d0c9086094fc18a7d9d
  - Source: crawl-ingest

## 2026-07-04
- **Tutorial | ClaudeLog** (P:\.data\wiki\sources\claudelog.com\003-claude-code-tutorial.md)
  - URL: https://claudelog.com/claude-code-tutorial
  - SHA256: 634beaebdc29b3df5e76cf0ea011628e4b303175d18033599e687db4f7653621
  - Source: crawl-ingest

## 2026-07-04
- **Claude Code Configuration Guide | ClaudeLog** (P:\.data\wiki\sources\claudelog.com\004-configuration.md)
  - URL: https://claudelog.com/configuration
  - SHA256: 763aa954874ce6099a05f81ae1a5c56daadd15f39357cc43b92cf24e17a37def
  - Source: crawl-ingest

## 2026-07-04
- **Claude Code Pricing | ClaudeLog** (P:\.data\wiki\sources\claudelog.com\005-claude-code-pricing.md)
  - URL: https://claudelog.com/claude-code-pricing
  - SHA256: e0ff4311c663d024a2cbc01c993ef893f08df05c5da3d745662a31f007210386
  - Source: crawl-ingest

## 2026-07-04
- **Claude News | ClaudeLog** (P:\.data\wiki\sources\claudelog.com\006-claude-news.md)
  - URL: https://claudelog.com/claude-news
  - SHA256: c750d53573dcc5815c84d418454f5460eb89cf14fba44fbd7b2aa5047ebbbeba
  - Source: crawl-ingest

## 2026-07-04
- **Claude Code Changelog | ClaudeLog** (P:\.data\wiki\sources\claudelog.com\007-claude-code-changelog.md)
  - URL: https://claudelog.com/claude-code-changelog
  - SHA256: 9af5a69013530408ac7e0a06fc5e006fa25df78866b304dfa51ec55aa410f5b9
  - Source: crawl-ingest

## 2026-07-04
- **Credyt | ClaudeLog** (P:\.data\wiki\sources\claudelog.com\008-credyt.md)
  - URL: https://claudelog.com/credyt
  - SHA256: eb25e09ce2d6dc256564a5774b6e15ecc10adb4fd2ac690eb841274f01bf8b51
  - Source: crawl-ingest

## 2026-07-04
- **You are the Main Thread | ClaudeLog** (P:\.data\wiki\sources\claudelog.com\009-mechanics-you-are-the-main-thread.md)
  - URL: https://claudelog.com/mechanics/you-are-the-main-thread
  - SHA256: 2808416f8beeb915734f56694686871b3fc82c15c322404bdc5a5e50092a915a
  - Source: crawl-ingest

## 2026-07-04
- **Claude Code Docs, Guides & Best Practices | ClaudeLog** (P:\.data\wiki\sources\claudelog.com\000-.md)
  - URL: https://claudelog.com/
  - SHA256: 71c1ee6e7f4fdb2e81c2717c122842457fcdc058163b5553bd34ee94d296b8be
  - Source: crawl-ingest (ingested)

## 2026-07-04
- **Support ClaudeLog | ClaudeLog** (P:\.data\wiki\sources\claudelog.com\001-support-claudelog.md)
  - URL: https://claudelog.com/support-claudelog
  - SHA256: f08cf06b758bbf8318149ab16c4ec7f3b630332ba15867c9542ff852d45c6009
  - Source: crawl-ingest (ingested)

## 2026-07-04
- **Install Claude Code | ClaudeLog** (P:\.data\wiki\sources\claudelog.com\002-install-claude-code.md)
  - URL: https://claudelog.com/install-claude-code
  - SHA256: f5377074307291230ca4bbfa6a189feb75803746db1976457618264465cfd6b5
  - Source: crawl-ingest (ingested)

## 2026-07-04
- **Tutorial | ClaudeLog** (P:\.data\wiki\sources\claudelog.com\003-claude-code-tutorial.md)
  - URL: https://claudelog.com/claude-code-tutorial
  - SHA256: 6257b10b5b2b43bc2683cc5372aba4cb463c4f8300426002382249dbb9e41b10
  - Source: crawl-ingest (ingested)

## 2026-07-04
- **Claude Code Docs, Guides & Best Practices | ClaudeLog** (P:\.data\wiki\sources\claudelog.com\000-.md)
  - URL: https://claudelog.com/
  - SHA256: 458281b72247a95b3176a1210800cfc052c801b6a37efac91971d99a0c2c3623
  - Source: crawl-ingest (revised)

## 2026-07-04
- **Support ClaudeLog | ClaudeLog** (P:\.data\wiki\sources\claudelog.com\001-support-claudelog.md)
  - URL: https://claudelog.com/support-claudelog
  - SHA256: 279e864f0577c7adb6162cdcf5feda9d39ee7554e15f9be5bf74abc4b7a8faae
  - Source: crawl-ingest (revised)

## 2026-07-04
- **Install Claude Code | ClaudeLog** (P:\.data\wiki\sources\claudelog.com\002-install-claude-code.md)
  - URL: https://claudelog.com/install-claude-code
  - SHA256: e185e8a5f17b2bb56132d3ae08ac6bcfc91bb6453ad446ee5a28c9354834a216
  - Source: crawl-ingest (revised)

## 2026-07-04
- **Tutorial | ClaudeLog** (P:\.data\wiki\sources\claudelog.com\003-claude-code-tutorial.md)
  - URL: https://claudelog.com/claude-code-tutorial
  - SHA256: 5a14f82013fd5dc0b1c4f440fd3a19c23f484436a165cf8a96459f50612cf125
  - Source: crawl-ingest (revised)

## 2026-07-04
- **T** (C:\Users\brsth\AppData\Local\Temp\tmp2qj5qt3k\test.example\000-x.md)
  - URL: https://test.example/x
  - SHA256: 9f077ab94fe81c3adeebc85d35320e5eb9633ccee674255763eefebe645ab964
  - Source: crawl-ingest (ingested)

## 2026-07-04
- **T** (000-x.md)
  - URL: https://test.example/x
  - SHA256: 9f077ab94fe81c3adeebc85d35320e5eb9633ccee674255763eefebe645ab964
  - Source: crawl-ingest (skipped)

## [2026-07-04] ingest | Confabulated Ignorance and the Source-Fabrication Stop Gate
Source: session-2026-07-04-research (web + in-repo source verification)
SHA256: newly-created-2026-07-04
Content: Maps confabulation/source-amnesia/sycophantic-false-ignorance failure modes to Claude Code enforcement. Verified StopHook_cross_validator.py::verify_document_claim trigger + quote_exemption gap (Task #1123 FP). Corrects earlier wrong hypothesis (gate never sees user prompt). Confabulated-ignorance detector = named-but-unstudied gap.
Page: wiki/concepts/confabulated-ignorance-and-source-fabrication-gate.md
## [2026-07-05] ingest | DSpark, MTP Speculative Decoding, and Ornith-1.0-9B Benchmarks
Source: wiki-source-dspark-mtp-ornith.txt
SHA256: ff95fcfafda3616fad1a6afe2fd7320c01c14940670d341aa16f78309c0c2e82

## [2026-07-05] ingest | cc-ccr Local Liveness Probe Fix
Source: wiki-source-ccr-probe-fix.txt
SHA256: a23f6d5acf429d323c59942dd09357e50e84ff0b23e7b1e0e55ff69be4fcba9c

## [2026-07-05] ingest | Subagent Model Diversity — Two Independent Levers
Source: session-derived (red-team model-fit review)
SHA256: session-synthesis-no-source-file
Ready. What do you need?nSource: sessionn

## [2026-07-05] ingest | Claude Code Goal Writing Best Practices
Source: session
Transcript: P:/Users/brsth/.claude/projects/P--/2026-07-05.jsonl


## [2026-07-05] ingest | improve-partner novel ideas (preserved from hook deletion)
Source: session
Task: #1052


## 2026-07-06
- **jacob-bd/perplexity-web-mcp** (P:\.data\wiki\sources\github.com\000-jacob-bd-perplexity-web-mcp.md)
  - URL: https://github.com/jacob-bd/perplexity-web-mcp
  - SHA256: 98227681106a73c5a4cb1fe2c7c1e0fad968027a6a4f7c54f5b0b5228f0b1053
  - Source: crawl-ingest (ingested)

## 2026-07-06
- **jacob-bd/perplexity-web-mcp** (000-jacob-bd-perplexity-web-mcp.md)
  - URL: https://github.com/jacob-bd/perplexity-web-mcp
  - SHA256: 98227681106a73c5a4cb1fe2c7c1e0fad968027a6a4f7c54f5b0b5228f0b1053
  - Source: crawl-ingest (skipped)
## [2026-07-05] ingest | search-research Plugin: Provider Stack Fix and Expansion
Source: session
Transcript: session-2026-07-05

## [2026-07-05] ingest | /go Capability-Claim Audit for Consolidation/Deprecation/Routing Tasks
Source: session
Transcript: session-2026-07-05


## [2026-07-06] ingest | ACTIVE_RUNTIME_HOOKS allowlist makes orphan hooks inert
Source: downloads-extract-router-active-runtime-hooks-allowlist-inertness
Source file: C:\Users\brsth\Downloads\ralph.txt

## [2026-07-06] ingest | Windows Git Bash ${HOME} must be overridden for fixed paths
Source: downloads-extract-windows-git-bash-home-path-override
Source file: C:\Users\brsth\Downloads\ACTUAL-ACTION-REQUIRED.md

## [2026-07-06] ingest | Default risk classifier excludes auth from production keywords
Source: downloads-extract-risk-classifier-auth-default-exclusion
Source file: C:\Users\brsth\Downloads\pi-risk-policy-wording-blocks.md

## [2026-07-06] ingest | ROI formula for ranking meta-engineering levers
Source: downloads-extract-meta-engineering-roi-ranking-frame
Source file: C:\Users\brsth\Downloads\meta-planner.md

## [2026-07-06] ingest | Phased rollout meta-planner meta-critic first
Source: downloads-extract-orchestrate-meta-phased-rollout
Source file: C:\Users\brsth\Downloads\IMPLEMENTATION_GUIDE.md

## [2026-07-06] ingest | Claim verifier taxonomy hard vs advisory by tag
Source: downloads-extract-claim-verifier-hard-vs-advisory-routing
Source file: C:\Users\brsth\Downloads\pony_tail_claim_phase0_plan_final.md

## [2026-07-06] ingest | File-anchored memory relevance filtering for PostCompact
Source: downloads-extract-postcompact-memory-relevance-filtering
Source file: C:\Users\brsth\Downloads\memory_md_test_setup.txt

## [2026-07-06] ingest | Detector prompts need structured JSON with signals_for/against
Source: downloads-extract-notebooklm-detector-prompt-template
Source file: C:\Users\brsth\Downloads\notebooklm-youtube-scam-prompts.md

## [2026-07-06] ingest | NLM source relocation via text download + re-upload
Source: downloads-extract-nlm-source-relocation-text-download
Source file: C:\Users\brsth\Downloads\multi-llm llm was wrong about moving sources 0.txt

## [2026-07-06] ingest | SessionStart hooks do NOT fire on intra-session compaction
Source: downloads-extract-sessionstart-vs-compaction-event-fire
Source file: C:\Users\brsth\Downloads\03-22-2025 - bad thinking, bad solutions 0.txt

## [2026-07-06] ingest | Complexity-tier routing A0-E with auto-escalation
Source: downloads-extract-complexity-tier-routing-auto-escalation
Source file: C:\Users\brsth\Downloads\the transcript recommends using smaller &amp;amp; chea.md

## [2026-07-06] ingest | stop-gate artifacts-are-invocation inversion
Source: downloads-extract-stop-gate-invocation-vs-completion-causality
Source file: C:\Users\brsth\Downloads\fix_invocation_detection_prompt.txt

## [2026-07-06] ingest | stop-gate cannot distinguish invoke from mention
Source: downloads-extract-stop-gate-invocation-vs-mention-discriminator
Source file: C:\Users\brsth\Downloads\fix_enforce_gate_prompt.txt

## [2026-07-06] ingest | asyncio.subprocess.SubprocessError does not exist
Source: downloads-extract-asyncio-subprocess-subprocesserror-typo
Source file: C:\Users\brsth\Downloads\edit didn't persist 0.txt

## [2026-07-06] ingest | hook scope cannot solve constitutional-layer pattern
Source: downloads-extract-hook-layer-vs-constitutional-layer-pattern-promotion
Source file: C:\Users\brsth\Downloads\cognitive-enhancers1.txt

## [2026-07-06] ingest | debrief rubric tightening measured numbers
Source: downloads-extract-skill-description-trim-budget-measured
Source file: C:\Users\brsth\Downloads\Fusion - -debrief- is a skill that analysis - Jun 30 7.48pm.md

## [2026-07-06] ingest | phase-1 step-0 gates discrimination-first
Source: downloads-extract-phase-1-step-0-discrimination-gates
Source file: C:\Users\brsth\Downloads\phase-1-implementation-packet-v2-hardened.md

## [2026-07-06] ingest | state file verification before by-design claims
Source: downloads-extract-debugrca-state-file-verification-step
Source file: C:\Users\brsth\Downloads\handoff problem again.txt

## [2026-07-06] ingest | Mutex leak self-detection after zombie cleanup
Source: downloads-extract-daemon-mutex-leak-after-zombie-cleanup
Source file: C:\Users\brsth\Downloads\notebooklm-debug-1776784907263.txt

## [2026-07-06] ingest | yt-dlp Python API path switches when cookies present
Source: downloads-extract-ytdlp-python-api-vs-cli-cookie-divergence
Source file: C:\Users\brsth\Downloads\media-pipeline.txt

## [2026-07-06] ingest | PreToolUse gate has prose-only bypass blind spot
Source: downloads-extract-skill-first-gate-prose-only-bypass
Source file: C:\Users\brsth\Downloads\skill-guard-gto.txt

## [2026-07-06] ingest | Silent exception swallow reproduces the bug it guards
Source: downloads-extract-silent-exception-swallow-bypasses-critical-guard
Source file: C:\Users\brsth\Downloads\think_handoff1.txt

## [2026-07-06] ingest | Always-on priming causes LLM habituation
Source: downloads-extract-hook-always-on-priming-causes-habituation
Source file: C:\Users\brsth\Downloads\review.txt

## [2026-07-06] ingest | Claim-aware gate short-circuit cuts gate fires 80%
Source: downloads-extract-claim-aware-gate-short-circuit-measurement
Source file: C:\Users\brsth\Downloads\claim_aware_validation_corrected.txt

## [2026-07-06] ingest | Brain iron RLS ADHD fatigue cluster
Source: downloads-extract-adhd-fatigue-iron-rls-cluster
Source file: C:\Users\brsth\Downloads\ADHD_Fatigue_1Pager.txt

## [2026-07-06] ingest | Two-stage honesty gate prevents prose violations
Source: downloads-extract-two-stage-honesty-gate-pattern
Source file: C:\Users\brsth\Downloads\honesty.txt

## [2026-07-06] ingest | Detector-level filter beats downstream filter
Source: downloads-extract-filter-at-detector-not-downstream
Source file: C:\Users\brsth\Downloads\ltos 0.txt

## [2026-07-06] ingest | GTO suggests skill based on findings not project type
Source: downloads-extract-gto-finding-driven-skill-suggestions
Source file: C:\Users\brsth\Downloads\not a good thinker LLM 1.txt

## [2026-07-06] ingest | EJS challenge solving needs deno runtime
Source: downloads-extract-ytdlp-ejs-cookie-selenium-fallback-chain
Source file: C:\Users\brsth\Downloads\media-pipeline.txt

## [2026-07-06] ingest | SessionStart PreCompact payload lacks terminalId
Source: downloads-extract-sessionstart-precompact-payload-shape
Source file: C:\Users\brsth\Downloads\handoff major problem..txt

## [2026-07-06] ingest | Stop output schema decision block vs approve
Source: downloads-extract-stop-hook-output-schema
Source file: C:\Users\brsth\Downloads\ccr-fable-routing-architecture-v3.md

## [2026-07-06] ingest | Three-way model tier semantics for gate policy
Source: downloads-extract-three-way-model-tier-gate-policy
Source file: C:\Users\brsth\Downloads\ccr-fable-routing-architecture-v3.md

## [2026-07-06] ingest | Identity contract for Stop hooks session_id only
Source: downloads-extract-stop-hook-identity-contract
Source file: C:\Users\brsth\Downloads\go_reliability_handoff.md

## [2026-07-06] ingest | Coverage means attempt succeeded not hits returned
Source: downloads-extract-search-coverage-attempt-not-hits
Source file: C:\Users\brsth\Downloads\claude-search-implementing-llm-final-prompt.md

## [2026-07-06] ingest | Token cost estimator with hard floor 15
Source: downloads-extract-token-cost-estimator-floor-15
Source file: C:\Users\brsth\Downloads\claude-search-implementing-llm-final-prompt.md

## [2026-07-06] ingest | Ack repetition counter thresholds for escalation
Source: downloads-extract-ack-repetition-counter-thresholds
Source file: C:\Users\brsth\Downloads\prompt_agent_viability_pilot_prompt.txt

## [2026-07-06] ingest | Adjacent-entry contamination detection pattern
Source: downloads-extract-adjacent-entry-contamination-detection
Source file: C:\Users\brsth\Downloads\prompt_agent_viability_pilot_prompt.txt

## [2026-07-06] ingest | Native /goal emits JSON validation error
Source: downloads-extract-native-goal-json-validation-error
Source file: C:\Users\brsth\Downloads\go_reliability_handoff.md

## [2026-07-06] ingest | Reminder injection size caps and dedup rules
Source: downloads-extract-reminder-injection-size-and-dedup
Source file: C:\Users\brsth\Downloads\claude_code_reminder_recovery_implementation_prompt.txt

## [2026-07-06] ingest | In-process gates bypassed on trivial responses
Source: downloads-extract-stoppy-inprocess-gates-bypass-trivial
Source file: C:\Users\brsth\Downloads\This is an rca about a frustrating experience with.md

## [2026-07-06] ingest | Route-class-first CCR routing
Source: downloads-extract-ccr-route-class-first-routing
Source file: C:\Users\brsth\Downloads\ccr-fable-routing-design-doc (1).md

## [2026-07-06] ingest | Diagram-router for documentation compilers
Source: downloads-extract-doc-compiler-diagram-router-stages
Source file: C:\Users\brsth\Downloads\skill_to_page_refactor_prompt.md

## [2026-07-06] ingest | Acknowledgment-loop stop hook pattern
Source: downloads-extract-stop-hook-acknowledgment-loop-blocker
Source file: C:\Users\brsth\Downloads\repetition_prevention_hardening_prompt.txt

## [2026-07-06] ingest | Pre-curated packets beat raw yt-dlp JSON
Source: downloads-extract-nblm-precurated-source-packets
Source file: C:\Users\brsth\Downloads\notebooklm-yt-dlp-quality-playbook.md

## [2026-07-06] ingest | Handoff dir derived from __file__ not cwd
Source: downloads-extract-hook-state-dir-from-__file__
Source file: C:\Users\brsth\Downloads\handoff and lazy problems1.txt

## [2026-07-06] ingest | MiniMax Token Plan endpoints
Source: downloads-extract-minimax-token-plan-endpoints
Source file: C:\Users\brsth\Downloads\I want to use my minimax token plan with bifrost a.md

## [2026-07-06] ingest | is_opportunity must be inlined before use
Source: downloads-extract-loop-derived-bool-inline-not-hoist
Source file: C:\Users\brsth\Downloads\03-21-2025 - bad coding logic 0.txt

## [2026-07-06] ingest | Reusable add_skill_path helper pattern
Source: downloads-extract-skill-pathlib-autopath-helper
Source file: C:\Users\brsth\Downloads\critique.txt

## [2026-07-06] ingest | attnroute reduces 50K-200K tokens to ~2K at 309ms
Source: downloads-extract-attnroute-context-reduction-90pct
Source file: C:\Users\brsth\Downloads\Claude Code Model Routing — Alternatives, Features &amp; Ideas Worth Adopting.md

## [2026-07-06] ingest | Three-question anti-bloat hook invariant
Source: downloads-extract-three-question-anti-bloat-hook-invariants
Source file: C:\Users\brsth\Downloads\crud-operations-redesign-with-interfaces.md

## [2026-07-06] ingest | Control-turn gate bypass prevents hijacking
Source: downloads-extract-control-turn-quality-gate-bypass
Source file: C:\Users\brsth\Downloads\optimal_implementation_prompt.txt

## [2026-07-06] ingest | HIGH_CONFidence_PATTERNS at 54% false positive
Source: downloads-extract-high-confidence-pattern-false-positives
Source file: C:\Users\brsth\Downloads\history1.txt

## [2026-07-06] ingest | Model switching breaks prompt cache
Source: downloads-extract-model-switch-cache-penalty
Source file: C:\Users\brsth\Downloads\Claude Code Model Routing — Alternatives, Features &amp; Ideas Worth Adopting.md

## [2026-07-06] ingest | Proxy-level routing decoupled from hook context
Source: downloads-extract-proxy-router-rejected-for-claude-only
Source file: C:\Users\brsth\Downloads\Claude Code Model Routing — Alternatives, Features &amp; Ideas Worth Adopting.md

## [2026-07-06] ingest | SubagentStart tier injection beats SessionStart
Source: downloads-extract-subagent-start-tier-injection
Source file: C:\Users\brsth\Downloads\Claude Code Model Routing — Alternatives, Features &amp; Ideas Worth Adopting.md

## [2026-07-06] ingest | Version-keyed cache hides source edits
Source: downloads-extract-version-keyed-cache-hides-source-edits
Source file: C:\Users\brsth\Downloads\crud-operations-redesign-with-interfaces.md

## [2026-07-06] ingest | rename to plan-relevant name corrupts intent
Source: downloads-extract-session-name-intent-misread
Source file: C:\Users\brsth\Downloads\handoff rca.txt

## [2026-07-06] ingest | fail-closed verification guard reversed to fail-warn
Source: downloads-extract-fail-closed-to-fail-warn-completion-guard
Source file: C:\Users\brsth\Downloads\implemented without approval, thinking code is for features when it's for all coding.txt

## [2026-07-06] ingest | Hook timeout only logs never kills
Source: downloads-extract-hook-timeout-warning-only-no-kill
Source file: C:\Users\brsth\Downloads\task-hook.txt

## [2026-07-06] ingest | Evidence check matches text not execution
Source: downloads-extract-evidence-check-text-not-execution
Source file: C:\Users\brsth\Downloads\inefficient gto 1.txt

## [2026-07-06] ingest | Discard unverified-edge-case options don't append
Source: downloads-extract-edge-case-filter-not-append
Source file: C:\Users\brsth\Downloads\meta-cognitive.txt

## [2026-07-06] ingest | Clear sys.modules AND pycache on import fix
Source: downloads-extract-sys-modules-pycache-both-required
Source file: C:\Users\brsth\Downloads\03-25-2025 poor thinking &amp; doesn't read skills 0.txt

## [2026-07-06] ingest | Test fixture referenced nonexistent class forever
Source: downloads-extract-broken-import-silent-green-tests
Source file: C:\Users\brsth\Downloads\plan visualizer.txt

## [2026-07-06] ingest | Evidence dir hardcoded to home not project
Source: downloads-extract-evidence-dir-hardcoded-home
Source file: C:\Users\brsth\Downloads\03-27-2025 gto not formatting 0.txt

## [2026-07-06] ingest | Manual override is rule zero
Source: downloads-extract-override-tier-rule-zero
Source file: C:\Users\brsth\Downloads\pi-risk-policy-implementation-spec.md

## [2026-07-06] ingest | Hard-anchor verbatim last user turn
Source: downloads-extract-compact-anchor-last-turn-verbatim
Source file: C:\Users\brsth\Downloads\Conversation with claude code about handoff pre-co.md

## [2026-07-06] ingest | Hooks enforce gaps not reasoning
Source: downloads-extract-hooks-boundary-not-reasoning-fixers
Source file: C:\Users\brsth\Downloads\The diagnosis is correct.md

## [2026-07-06] ingest | Premise propagation cascades across parallel agents
Source: downloads-extract-premise-propagation-parallel-fp
Source file: C:\Users\brsth\Downloads\I don't know what to call this behavior.txt

## [2026-07-06] ingest | Multiple hook emitters concatenate JSON
Source: downloads-extract-multi-hook-stdout-concat-broken-json
Source file: C:\Users\brsth\Downloads\main.txt

## [2026-07-06] ingest | User-directive obligation tracker is missing
Source: downloads-extract-user-directive-obligation-tracker
Source file: C:\Users\brsth\Downloads\blocked phrases.txt

## [2026-07-06] ingest | Terminal registry beats PID fallback
Source: downloads-extract-terminal-registry-over-pid-fallback
Source file: C:\Users\brsth\Downloads\verify0.txt

## [2026-07-06] ingest | PreCompact handoff self-load bug
Source: downloads-extract-precompact-handoff-self-load
Source file: C:\Users\brsth\Downloads\inefficient commitment 0.txt

## [2026-07-06] ingest | Stop router skips close_turn on block
Source: downloads-extract-stop-router-close-turn-on-block
Source file: C:\Users\brsth\Downloads\Implement multi-terminal isolation and data consistency 2.txt

## [2026-07-06] ingest | Phase hooks must read artifacts not strings
Source: downloads-extract-artifact-backed-phase-evidence
Source file: C:\Users\brsth\Downloads\Refactor Skill v2  Design Rationale &amp; Upgrade Guide.md

## [2026-07-06] ingest | SQA layers parallelize with one gate
Source: downloads-extract-sqa-layer-parallelization-with-gate
Source file: C:\Users\brsth\Downloads\sqa.txt

## [2026-07-06] ingest | Hook pattern blind spot for imminent-action
Source: downloads-extract-imminent-action-claim-blind-spot
Source file: C:\Users\brsth\Downloads\03-25-2025 poor thinking and self-imposed constraints 0.txt

## [2026-07-06] ingest | Lazy enumerates one item at a time
Source: downloads-extract-enumerate-all-not-one-at-a-time
Source file: C:\Users\brsth\Downloads\inefficient is 0.txt

## [2026-07-06] ingest | Tool-call evidence trumps skill metadata
Source: downloads-extract-skill-loaded-doesnt-mean-skill-executed
Source file: C:\Users\brsth\Downloads\inefficient commitment 0.txt

## [2026-07-06] ingest | Handoff must store disk state not transcript
Source: downloads-extract-handoff-must-store-disk-state
Source file: C:\Users\brsth\Downloads\✳ Task List.txt

## [2026-07-06] ingest | gitready inline course loses quality
Source: downloads-extract-re-delegate-not-port-for-shared-quality
Source file: C:\Users\brsth\Downloads\hooks_implementation_plan 1.md

## [2026-07-06] ingest | Hook advice layer cannot enforce honesty
Source: downloads-extract-advisory-vs-enforcing-hooks-limits
Source file: C:\Users\brsth\Downloads\Untitled.txt

## [2026-07-06] ingest | Skill execution gate fires mid-response
Source: downloads-extract-stop-hook-timing-mid-response
Source file: C:\Users\brsth\Downloads\Implement multi-terminal isolation and data consistency 2.txt

## [2026-07-06] ingest | Maintainability Index is opaque and gameable
Source: downloads-extract-maintainability-index-not-headline
Source file: C:\Users\brsth\Downloads\page-2026-04-19-11-13-22.md

## [2026-07-07] ingest | directory_policy.json enforces via missing hook filename
Source: downloads-extract-w2-directory-policy-enforcer-filename-mismatch
Source file: C:\Users\brsth\Downloads\PreToolUse0.txt

## [2026-07-07] ingest | Handoff naive string search fails on JSON transcript
Source: downloads-extract-w2-handoff-naive-transcript-search-fails-json
Source file: C:\Users\brsth\Downloads\03-19-2025 - handoff idea 0.txt

## [2026-07-07] ingest | Handoff truncation loses task context
Source: downloads-extract-w2-handoff-truncation-loses-task-context
Source file: C:\Users\brsth\Downloads\handoff and lazy problems3.txt

## [2026-07-07] ingest | Missing EXECUTION DIRECTIVE causes LLM to reformat script output
Source: downloads-extract-w2-skill-missing-exec-directive-llm-reinterpretation
Source file: C:\Users\brsth\Downloads\03-22-2025 - bad thinking, bad solutions 1.txt

## [2026-07-07] ingest | Stop gate false-positive on verified negative existence claims
Source: downloads-extract-w2-stop-gate-false-positive-verified-negative-claim
Source file: C:\Users\brsth\Downloads\conflated two different things.txt

## [2026-07-07] ingest | First-hit confirmation bias bypasses multi-hypothesis gates
Source: downloads-extract-w2-first-hit-confirmation-bias-bypasses-rca-gates
Source file: C:\Users\brsth\Downloads\Prevent First Plausible Explanation Anti-Pattern.txt

## [2026-07-07] ingest | Adversarial agent output directory mismatch causes false missing
Source: downloads-extract-w2-adversarial-agent-output-directory-mismatch
Source file: C:\Users\brsth\Downloads\03-17-2005 - search-research 0.txt

## [2026-07-07] ingest | YouTube CLI URL-as-text mode hangs >90s transcript-only reliable
Source: downloads-extract-w2-youtube-cli-url-mode-hang-transcript-fallback
Source file: C:\Users\brsth\Downloads\⠂ int-stream.txt

## [2026-07-07] ingest | Coverage-before-claims forbids absence without full search
Source: downloads-extract-w2-coverage-before-claims-absence-forbidden
Source file: C:\Users\brsth\Downloads\claude-search-implementation-package (1).md

## [2026-07-07] ingest | Mermaid plugin ecosystem generation extraction live-render tiers
Source: downloads-extract-w2-mermaid-plugin-ecosystem-three-tiers
Source file: C:\Users\brsth\Downloads\what are very popular plugins or skills or repos f.md

## [2026-07-07] ingest | Daemon stale PID accumulation causes cross-terminal hook errors
Source: downloads-extract-w2-daemon-stale-pid-accumulation-cross-terminal-errors
Source file: C:\Users\brsth\Downloads\✳ Terminal Issues.txt

## [2026-07-07] ingest | Derive architecture map don't maintain it
Source: downloads-extract-w2-derive-architecture-map-sessionstart
Source file: C:\Users\brsth\Downloads\chain_20260706_170546.md

## [2026-07-07] ingest | Seven-layer SQA framework Godelian bound
Source: downloads-extract-w2-seven-layer-sqa-godelian-bound
Source file: C:\Users\brsth\Downloads\03-25-2025 sqa 0.txt

## [2026-07-07] ingest | Drift framing wrong verify constraints not change
Source: downloads-extract-w2-architecture-constraint-vs-drift-reframe
Source file: C:\Users\brsth\Downloads\03-25-2025 sqa 0.txt

## [2026-07-07] ingest | Solo-dev rejects git hooks and continuous checks
Source: downloads-extract-w2-solo-dev-rejects-continuous-checks
Source file: C:\Users\brsth\Downloads\03-25-2025 sqa 0.txt

## [2026-07-07] ingest | Cognitive enhancers trigger patterns miss questions
Source: downloads-extract-w2-cognitive-enhancers-miss-question-triggers
Source file: C:\Users\brsth\Downloads\why can't llms think properly  1 ✳ ai-gemini.txt

## [2026-07-07] ingest | CKS relevance-gated injection score > 0.7
Source: downloads-extract-w2-cks-relevance-threshold-injection
Source file: C:\Users\brsth\Downloads\⠂ Document stop-block logging system.txt

## [2026-07-07] ingest | UEEA blanket-grace gap per-evidence linkage needed
Source: downloads-extract-w2-ueea-per-evidence-linkage-gap
Source file: C:\Users\brsth\Downloads\⠐ ltos.txt

## [2026-07-07] ingest | YouTube RSS only gives recent API for full history
Source: downloads-extract-w2-youtube-channel-enumeration-rss-vs-api
Source file: C:\Users\brsth\Downloads\⠐ int-stream.txt

## [2026-07-07] ingest | claudish session-level vs seifghazi subagent-only routing
Source: downloads-extract-w2-claudish-vs-seifghazi-subagent-routing
Source file: C:\Users\brsth\Downloads\03-20-2025 - not smart 4.txt

## [2026-07-07] ingest | Skill inline injection Stop hook is correct safety net
Source: downloads-extract-w2-skill-inline-injection-stop-as-fire-alarm
Source file: C:\Users\brsth\Downloads\Here's a chat with claude code, and codex, about o.md

## [2026-07-07] ingest | Refactor state-machine key mismatch and substring progress detection
Source: downloads-extract-w2-refactor-state-machine-key-mismatch
Source file: C:\Users\brsth\Downloads\deep-research-report (4).md

## [2026-07-07] ingest | Speculative worktree refactor default architecture
Source: downloads-extract-w2-speculative-worktree-refactor-default
Source file: C:\Users\brsth\Downloads\deep-research-report (4).md

## [2026-07-07] ingest | pythonw.exe swallows logger calls silently
Source: downloads-extract-w2-pythonw-swallows-logger-calls
Source file: C:\Users\brsth\Downloads\daemon1.txt

## [2026-07-07] ingest | Prose rules lose to default reflexes
Source: downloads-extract-w2-prose-rules-lose-to-tool-call-gates
Source file: C:\Users\brsth\Downloads\π - .txt

## [2026-07-07] ingest | LLM-suggested npm packages may not exist
Source: downloads-extract-w2-verify-llm-recommended-npm-packages
Source file: C:\Users\brsth\Downloads\π - .txt

## [2026-07-07] ingest | Per-backend validation before migration not after
Source: downloads-extract-w2-per-backend-validation-before-migration
Source file: C:\Users\brsth\Downloads\page-2026-07-07-04-30-28.md

## [2026-07-07] ingest | Subagent merge protocol must be explicit
Source: downloads-extract-w2-explicit-subagent-merge-protocol
Source file: C:\Users\brsth\Downloads\advesarial0-lots of good info.txt

## [2026-07-07] ingest | Memory index tool observations not conversation text
Source: downloads-extract-w2-memory-index-tool-observations-not-conversation
Source file: C:\Users\brsth\Downloads\What is _  ❯ ◯ remember · claude-plugins-official.md

## [2026-07-07] ingest | Mock call-count tests setup before patching
Source: downloads-extract-w2-mock-call-count-setup-before-patch
Source file: C:\Users\brsth\Downloads\⠐ Test Execution2.txt

## [2026-07-07] ingest | Prevention hooks must fire pre-response not post
Source: downloads-extract-w2-prevention-hooks-must-fire-pre-response
Source file: C:\Users\brsth\Downloads\design and discovery didn't find existing solutions ✳ bad-rca.txt

## [2026-07-07] ingest | Prompt hooks inject into current session free
Source: downloads-extract-w2-prompt-hooks-use-session-llm-free
Source file: C:\Users\brsth\Downloads\03-22-2025 - verbose pre-mortem 0.txt

## [2026-07-07] ingest | LLMs fabricate bugs in uncommitted files
Source: downloads-extract-w2-llm-fabricates-bugs-in-uncommitted-files
Source file: C:\Users\brsth\Downloads\LLM_1 says this about LLM_2_ ___● Based on the cha.md

## [2026-07-07] ingest | except-pass hides undefined functions called at 7 sites
Source: downloads-extract-w2-except-pass-hides-undefined-function
Source file: C:\Users\brsth\Downloads\not a good thinker LLM 4 hook loops.txt

## [2026-07-07] ingest | cc-model-router hardcodes Anthropic tier IDs
Source: downloads-extract-w2-cc-model-router-hardcoded-tier-env-override
Source file: C:\Users\brsth\Downloads\✳ claude-router.txt

## [2026-07-07] ingest | AI-API benchmark planning domain saturates 1.0/1.0
Source: downloads-extract-w2-ai-api-benchmark-saturation-stdev-ranking
Source file: C:\Users\brsth\Downloads\✳ Review AI API handoff document.txt

## [2026-07-07] ingest | Skill-first gate has documented design drift
Source: downloads-extract-w2-skill-first-gate-telemetry-comment-drift
Source file: C:\Users\brsth\Downloads\✳ Debug Hook Loop.txt

## [2026-07-07] ingest | Skill-first gate chicken-and-egg deadlock
Source: downloads-extract-w2-skill-first-gate-three-layer-deadlock
Source file: C:\Users\brsth\Downloads\✳ hooking0.txt

## [2026-07-07] ingest | Diagnostic gate block scope discriminating_test only
Source: downloads-extract-w2-diagnostic-gate-block-scope-discriminating-test-only
Source file: C:\Users\brsth\Downloads\✳ Research solutions for Claude Code issues.txt

## [2026-07-07] ingest | /refactor is Python library with CC thresholds
Source: downloads-extract-w2-refactor-python-library-cc-thresholds-not-loc
Source file: C:\Users\brsth\Downloads\✳ adv-review-skill.txt

## [2026-07-07] ingest | UserPromptSubmit can only append 10k overflow
Source: downloads-extract-w2-userpromptsubmit-append-only-10k-overflow
Source file: C:\Users\brsth\Downloads\You are reviewing an architecture decision record.md

## [2026-07-07] ingest | Prose skills have unverifiable routing logic
Source: downloads-extract-w2-prose-skills-unverifiable-routing-needs-decision-spec
Source file: C:\Users\brsth\Downloads\__❯ We're trying to achieve an optimal order for t.md

## [2026-07-07] ingest | transcript field excludes current in-progress turn
Source: downloads-extract-w2-hook-transcript-excludes-current-turn
Source file: C:\Users\brsth\Downloads\✳ hooking0.txt

## [2026-07-07] ingest | Dead code in RCA confidence must drop to 0
Source: downloads-extract-w2-rca-dead-code-hypothesis-confidence-must-drop-zero
Source file: C:\Users\brsth\Downloads\glm multi-terminal isolation and data consistency 2.txt

## [2026-07-07] ingest | Stop.py ORPHAN-imports false positive exemption
Source: downloads-extract-w2-stop-orphan-imports-exemption
Source file: C:\Users\brsth\Downloads\✳ Fix Chrome DevTools MCP response halts.txt

## [2026-07-07] ingest | hook_health.json stale-TTL removal
Source: downloads-extract-w2-hook-health-stale-ttl-removal
Source file: C:\Users\brsth\Downloads\✳ Fix Chrome DevTools MCP response halts.txt

## [2026-07-07] ingest | chs_cli export requires explicit --session-id
Source: downloads-extract-w2-chs-cli-export-requires-explicit-session-id
Source file: C:\Users\brsth\Downloads\✳ Debug LLM session export and context handling.txt

## [2026-07-07] ingest | Document-claim detector scope FP reproduced
Source: downloads-extract-w2-document-claim-detector-scope-fp-reproduced
Source file: C:\Users\brsth\Downloads\✳ Debug LLM session export and context handling.txt

## [2026-07-07] ingest | Source-vs-cache reproduction validity check
Source: downloads-extract-w2-source-vs-cache-reproduction-validity
Source file: C:\Users\brsth\Downloads\✳ Debug LLM session export and context handling.txt

## [2026-07-07] ingest | Worktree isolation via cwd inheritance
Source: downloads-extract-w2-worktree-isolation-via-cwd-inheritance
Source file: C:\Users\brsth\Downloads\__❯ We're trying to achieve an optimal order for t (1).md

## [2026-07-07] ingest | PreCompact hook schema shape
Source: downloads-extract-w2-precompact-hook-schema-shape
Source file: C:\Users\brsth\Downloads\✳ prompt-enhancer.txt

## [2026-07-07] ingest | Overconfidence regex misses structural vocabulary
Source: downloads-extract-w2-overconfidence-structural-vocabulary-blind-spot
Source file: C:\Users\brsth\Downloads\Why You Hate It.md

## [2026-07-07] ingest | Skills bypass PreToolUse gates via subprocess
Source: downloads-extract-w2-skill-subprocess-bypasses-pretooluse-gates
Source file: C:\Users\brsth\Downloads\I don't want the simpliest fix. ⠂ git.txt

## [2026-07-07] ingest | integration_engine.py 7356-line orphan code
Source: downloads-extract-w2-integration-engine-orphan-code-archaeology
Source file: C:\Users\brsth\Downloads\✳ Review ponytail audit findings.txt

## [2026-07-07] ingest | Per-tag evidence requirements for audit claims
Source: downloads-extract-w2-audit-finding-evidence-requirements-by-tag
Source file: C:\Users\brsth\Downloads\✳ Review ponytail audit findings.txt

## [2026-07-07] ingest | Fable behavior via JSONL distillation Mark Kashef method
Source: downloads-extract-w2-fable-behavioral-distillation-from-jsonl-history
Source file: C:\Users\brsth\Downloads\how can I make my current llm act like claude fabl.md

## [2026-07-07] ingest | Skill error loggers must capture stdout JSON not stderr only
Source: downloads-extract-w2-skill-subprocess-stderr-only-error-masking
Source file: C:\Users\brsth\Downloads\error logs.txt

## [2026-07-07] ingest | Question+document disambiguation heuristic
Source: downloads-extract-w2-question-document-role-disambiguation-heuristic
Source file: C:\Users\brsth\Downloads\error logs.txt

## [2026-07-07] ingest | Cognitive enhancer tag codes are display-only
Source: downloads-extract-w2-cognitive-enhancer-tag-codes-display-only
Source file: C:\Users\brsth\Downloads\Here's a chat with claude code.  Any ideas for a s.md

## [2026-07-07] ingest | UserPromptSubmit cannot rewrite user prompt in place
Source: downloads-extract-w2-userpromptsubmit-no-inplace-rewrite-contract
Source file: C:\Users\brsth\Downloads\You are reviewing an architecture decision record (1).md

## [2026-07-07] ingest | Task-contract gate deterministic regex limitations
Source: downloads-extract-w2-task-contract-gate-regex-under-over-fire-limits
Source file: C:\Users\brsth\Downloads\Please review the handoff.____● ---_  FILES_CHANGE.md

## [2026-07-07] ingest | n_1_transcript_path is single-hop overwrites each compaction
Source: downloads-extract-w2-n1-transcript-path-single-hop-overwrite-limit
Source file: C:\Users\brsth\Downloads\Has anyone figured out for claude code, how to cre.md

## [2026-07-07] ingest | Fingerprint parity proves model alias identity
Source: downloads-extract-w2-fingerprint-parity-model-alias-verification
Source file: C:\Users\brsth\Downloads\chain_20260706_173325.md

## [2026-07-07] ingest | Agent tool schema leaks ~1600 tokens per turn
Source: downloads-extract-w2-agent-tool-schema-token-leakage
Source file: C:\Users\brsth\Downloads\✳ Investigate agent tool definition size.txt

## [2026-07-07] ingest | DELEGATION_GATE bypass via env var or --allow-inline
Source: downloads-extract-w2-delegation-gate-env-var-bypass
Source file: C:\Users\brsth\Downloads\✳ Investigate agent tool definition size.txt

## [2026-07-07] ingest | Public /v1/models endpoint masks broken auth headers
Source: downloads-extract-w2-public-models-endpoint-masks-auth-bugs
Source file: C:\Users\brsth\Downloads\✳ claude.txt

## [2026-07-07] ingest | Reasoning models emit reasoning_content not content
Source: downloads-extract-w2-reasoning-models-emit-reasoning-content-key
Source file: C:\Users\brsth\Downloads\✳ claude.txt

## [2026-07-07] ingest | Three-layer cognitive enforcement architecture
Source: downloads-extract-w2-three-layer-cognitive-enforcement-architecture
Source file: C:\Users\brsth\Downloads\✳ Complete wrapper elimination for epistemic and investigation plugins.txt

## [2026-07-07] ingest | Model self-reports of context window are weak evidence
Source: downloads-extract-w2-model-self-report-context-weak-evidence
Source file: C:\Users\brsth\Downloads\chain_20260706_173325.md

## [2026-07-07] ingest | Unverified LLM tier rankings must not become routing rosters
Source: downloads-extract-w2-unverified-llm-rankings-poison-routing-roster
Source file: C:\Users\brsth\Downloads\✳ claude.txt

## [2026-07-07] ingest | Stop hook health alert lists orphan hooks not in router registry
Source: downloads-extract-w2-orphan-hook-health-alert-detection
Source file: C:\Users\brsth\Downloads\✳ Investigate agent tool definition size.txt

## [2026-07-07] ingest | assumption_audit_v2.py is 104KB dead code with zero consumers
Source: downloads-extract-w2-assumption-audit-v2-dead-code-104kb
Source file: C:\Users\brsth\Downloads\✳ Complete wrapper elimination for epistemic and investigation plugins.txt

## [2026-07-07] ingest | Headroom zombie auto-recovery design
Source: downloads-extract-w2-headroom-zombie-port-cmdline-detection
Source file: C:\Users\brsth\Downloads\✳ headroom.txt

## [2026-07-07] ingest | Self-reflection gate noise reduction recipe
Source: downloads-extract-w2-self-reflection-contradiction-dedupe-doc-skip-cap
Source file: C:\Users\brsth\Downloads\✳ epistemic-gate.txt

## [2026-07-07] ingest | Cross-model audit hallucination rate
Source: downloads-extract-w2-cross-model-audit-hallucination-demand-file-evidence
Source file: C:\Users\brsth\Downloads\consolidate hooks maybe and skill-guard.txt

## [2026-07-07] ingest | cc-ccr env-var route override recipe
Source: downloads-extract-w2-cc-ccr-env-var-route-override-per-shell
Source file: C:\Users\brsth\Downloads\✳ headroom.txt

## [2026-07-07] ingest | Shell-pipe stdin conflict in LLM wrappers
Source: downloads-extract-w2-shell-pipe-stdin-conflict-llm-wrapper
Source file: C:\Users\brsth\Downloads\llm defening bad analysis⠐ ai-gemini.txt

## [2026-07-07] ingest | Downloads corpus file-size distribution
Source: downloads-extract-w2-downloads-corpus-file-size-distribution-three-tier
Source file: C:\Users\brsth\Downloads\The attached file is for background info.  Here's.md

## [2026-07-07] ingest | YAML workflow_steps parse fails silently
Source: downloads-extract-w2-yaml-workflow-steps-silent-parse-failure
Source file: C:\Users\brsth\Downloads\temp⠐ skill-audit.txt

## [2026-07-07] ingest | Content-match fallback bypasses target scoping
Source: downloads-extract-w2-content-match-fallback-target-bypass-risk
Source file: C:\Users\brsth\Downloads\llm making stuff up⠐ skill-guard.txt

## [2026-07-07] ingest | CLAIM_PATTERNS misses causal mechanism claims
Source: downloads-extract-w2-causal-claim-patterns-gap-unified-verifier
Source file: C:\Users\brsth\Downloads\In claude code, we are a little stuck.  How can we.md

## [2026-07-07] ingest | Orthogonality check must precede bypass heuristics
Source: downloads-extract-w2-orthogonality-check-ordering-before-bypass
Source file: C:\Users\brsth\Downloads\We are accepting a handoff from another LLM__text.md

## [2026-07-07] ingest | Channel metadata source capability matrix
Source: downloads-extract-w2-youtube-channel-metadata-source-capability-matrix
Source file: C:\Users\brsth\Downloads\⠂ yt-is 0.txt

## [2026-07-07] ingest | skill-craft mixes direct import and subprocess integration
Source: downloads-extract-w2-skill-craft-direct-import-staleness-subprocess
Source file: C:\Users\brsth\Downloads\⠂ skill-craft.txt

## [2026-07-07] ingest | SILENT verdict conflates two distinct causes
Source: downloads-extract-w2-silent-verdict-conflation-filter-by-targets
Source file: C:\Users\brsth\Downloads\bad thinking ⠂ skill-audit.txt

## [2026-07-07] ingest | system_fingerprint proves model alias identity
Source: downloads-extract-w2-system-fingerprint-model-alias-identity-evidence
Source file: C:\Users\brsth\Downloads\Can you validate this information____  opencode-ze.md

## [2026-07-07] ingest | Model self-reported limits are weak evidence
Source: downloads-extract-w2-model-self-reported-limits-weak-evidence
Source file: C:\Users\brsth\Downloads\Can you validate this information____  opencode-ze.md

## [2026-07-07] ingest | Investigator-first prompt pattern for fresh LLM
Source: downloads-extract-w2-investigator-first-prompt-pattern
Source file: C:\Users\brsth\Downloads\The attachment is a previous conversation.  Here's.md

## [2026-07-07] ingest | Source-fabrication gate FP on pasted-context analysis
Source: downloads-extract-w2-source-fabrication-gate-pasted-context-false-positive
Source file: C:\Users\brsth\Downloads\chain_20260704_230335.md

## [2026-07-07] ingest | Rubric scoring breaks for trace-only skills
Source: downloads-extract-w2-rubric-scoring-breaks-for-trace-only-skills
Source file: C:\Users\brsth\Downloads\chain_82946cce.md

## [2026-07-07] signal-extract | The fixes resolved the test failures: Summary of Fixes Root 
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\03-16-2026 handoff.txt
Novelty: 12%

## [2026-07-07] signal-extract | Solution: Add ruff format to the PostToolUse hook so formatt
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\03-17-2005 - auto-formatting.txt
Novelty: 7%

## [2026-07-07] signal-extract | The GitHub provider imports from non-existent research_flash
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\03-17-2005 - openrouter 0.txt
Novelty: 8%

## [2026-07-07] signal-extract | No github.py exists in the providers directory. ● Summary Ta
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\03-17-2005 - openrouter 0.txt
Novelty: 7%

## [2026-07-07] signal-extract | cli.py:1122 imports non-existent research_flash.sources.gith
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\03-17-2005 - openrouter 0.txt
Novelty: 22%

## [2026-07-07] signal-extract | ❌ No named pipe server (SemanticClient/SemanticDaemon classe
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\03-17-2005 - search-research 4.txt
Novelty: 12%

## [2026-07-07] signal-extract | Change Stop hook to run at different point in response lifec
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\03-20-2025 - not smart 0.txt
Novelty: 8%

## [2026-07-07] signal-extract | Implication: The implementation plan must be revised to use 
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\03-20-2025 - not smart 4.txt
Novelty: 7%

## [2026-07-07] signal-extract | Table-formatted implementation details (| file.py |, | Class
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\03-21-2025 - really annoying not using the skills 1.txt
Novelty: 6%

## [2026-07-07] signal-extract | Transient Edit-block on settings.json — root cause never fou
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\2026-07-01 [CHS #917 · dream-cycle #976 · gate #942 · plugin-audit #982 #988 · opportunity #983 #989 #1001 · hooks #986 #987 · model #990 #991 · friction #992 #993 #994].txt
Novelty: 14%

## [2026-07-07] signal-extract | #945 Cleanup: stale hook_ledger.db (485MB) + orphan worktree
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\2026-07-01 [CHS #917 · dream-cycle #976 · gate #942 · plugin-audit #982 #988 · opportunity #983 #989 #1001 · hooks #986 #987 · model #990 #991 · friction #992 #993 #994].txt
Novelty: 11%

## [2026-07-07] signal-extract | The `local` tier now switches to the local llama.cpp model f
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\2026-07-03 [chs #1060 #1062 · plugin-audit #1061 · docs #1058 · detector #983].md
Novelty: 9%

## [2026-07-07] signal-extract | Root cause: PowerShell's `-f` operator tries to parse the Un
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\2026-07-03 [chs #1060 #1062 · plugin-audit #1061 · docs #1058 · detector #983].md
Novelty: 10%

## [2026-07-07] signal-extract | Root cause: line 1130 `key_patterns = ["**/*.py", "**/*.json
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\2026-07-03 [chs #1060 #1062 · plugin-audit #1061 · docs #1058 · detector #983].md
Novelty: 14%

## [2026-07-07] signal-extract | **Export verification**: Confirmed `da9b9573` transcript (13
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\2026-07-03 [chs #1060 #1062 · plugin-audit #1061 · docs #1058 · detector #983].md
Novelty: 8%

## [2026-07-07] signal-extract | Fixed by abandoning delegation and running WebSearch directl
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\2026-07-03 [chs #1060 #1062 · plugin-audit #1061 · docs #1058 · detector #983].md
Novelty: 12%

## [2026-07-07] signal-extract | Fixed by running WebSearch/webReader directly in main contex
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\2026-07-03 [chs #1060 #1062 · plugin-audit #1061 · docs #1058 · detector #983].md
Novelty: 14%

## [2026-07-07] signal-extract | Confirmed `_format_transcript` (non-streaming twin, line 780
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\2026-07-03 [chs #1060 #1062 · plugin-audit #1061 · docs #1058 · detector #983].md
Novelty: 6%

## [2026-07-07] signal-extract | The [dev.to "190 Things Hooks Cannot Enforce"](https://www.d
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\2026-07-03 [go #1067 #1068 #1069 · stop #1066 · telemetry #1070].md
Novelty: 10%

## [2026-07-07] signal-extract | Registry skips Read so it must be inline.", "activeForm": "W
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\2026-07-03 [go #1067 #1068 #1069 · stop #1066 · telemetry #1070].md
Novelty: 23%

## [2026-07-07] signal-extract | The diagnostics are pre-existing in PreToolUse.py (parameter
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\2026-07-03 [go #1067 #1068 #1069 · stop #1066 · telemetry #1070].md
Novelty: 7%

## [2026-07-07] signal-extract | Root cause: it read top-level `session_id` while the real pa
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\2026-07-03 [go #1067 #1068 #1069 · stop #1066 · telemetry #1070].md
Novelty: 6%

## [2026-07-07] signal-extract | The prior session's identified root cause (line 9635): the `
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\2026-07-03 [go #1067 #1068 #1069 · stop #1066 · telemetry #1070].md
Novelty: 14%

## [2026-07-07] signal-extract | The stdin piping approach documented in the fix is the corre
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\ai-gemini questions 1.txt
Novelty: 9%

## [2026-07-07] signal-extract | The local tier now switches to the local llama.cpp model for
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\ccr dashboard redesign.txt
Novelty: 9%

## [2026-07-07] signal-extract | Root cause: `user_prompt` variable undefined at line 4540 of
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260527_151412.md
Novelty: 9%

## [2026-07-07] signal-extract | **Root cause**: During cc-aca-authority migration (task #552
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260527_151412.md
Novelty: 10%

## [2026-07-07] signal-extract | The Stop.py crash is caused by two broken imports (lines 123
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260527_151412.md
Novelty: 17%

## [2026-07-07] signal-extract | Root cause: _run_referent_coverage was removed from Stop.py 
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260527_151412.md
Novelty: 6%

## [2026-07-07] signal-extract | **Asymmetric cleanup removal**: Root cause — `_run_referent_
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260527_151412.md
Novelty: 10%

## [2026-07-07] signal-extract | Never authored by hand — PluginMarketplaceSchema rewrites un
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260527_151412.md
Novelty: 13%

## [2026-07-07] signal-extract | The root cause (snapshot hooks.json disabled, no settings.js
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260527_151412.md
Novelty: 10%

## [2026-07-07] signal-extract | Did the block happen before or after my SessionStart changes
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260529_091750.md
Novelty: 10%

## [2026-07-07] signal-extract | **Director decisions (cannot auto-close)**: OQ-1 (advisory v
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260629_084915.md
Novelty: 6%

## [2026-07-07] signal-extract | + `systemMessage` + `permissionDecisionReason` — so all 8 ho
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260629_084915.md
Novelty: 7%

## [2026-07-07] signal-extract | — standalone, settings.json empty, not in class registry | y
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260629_084915.md
Novelty: 8%

## [2026-07-07] signal-extract | RC#5's V-loop is inert; the fix is a ~10-line port into the 
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260629_084915.md
Novelty: 8%

## [2026-07-07] signal-extract | The registered `InvestigationTracker` calls only `record_exe
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260629_084915.md
Novelty: 10%

## [2026-07-07] signal-extract | (1) REGISTERED `posttooluse/investigation_tracker.py` — clas
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260629_084915.md
Novelty: 17%

## [2026-07-07] signal-extract | The 05:54 run was an orphan fluke — a correctly-orchestrated
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260629_084915.md
Novelty: 25%

## [2026-07-07] signal-extract | (CHANGE-007 verification stamper) after compaction — answer 
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260629_084915.md
Novelty: 5%

## [2026-07-07] signal-extract | SOLVED: Diagnosed root cause, traced origin to commit 634d2a
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260630_160635.md
Novelty: 6%

## [2026-07-07] signal-extract | "The stack frames are separate errors" (user's prior read): 
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260630_160635.md
Novelty: 6%

## [2026-07-07] signal-extract | Root cause restated: `terminal_detection` was loaded under t
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260630_160635.md
Novelty: 7%

## [2026-07-07] signal-extract | (orphaned settings.json vars, wikilink warning) and **Q2 exe
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260704_002157.md
Novelty: 14%

## [2026-07-07] signal-extract | **Q1 orphaned settings.json vars + wikilink warning**: Still
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260704_002157.md
Novelty: 14%

## [2026-07-07] signal-extract | The suspected root cause remains the `claim_gap_telemetry_pr
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260704_002527.md
Novelty: 10%

## [2026-07-07] signal-extract | The two tracebacks are just `mutmut` and `cosmic_ray` not be
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260704_135445.md
Novelty: 36%

## [2026-07-07] signal-extract | COMMITMENT: YES — those tracebacks are `ModuleNotFoundError:
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260704_135445.md
Novelty: 25%

## [2026-07-07] signal-extract | I really want an answer." — I owned that I flagged `owner_sk
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260704_135445.md
Novelty: 11%

## [2026-07-07] signal-extract | The test suite never executes: `tests/conftest.py:20` does `
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260704_135445.md
Novelty: 8%

## [2026-07-07] signal-extract | if `/go` SKILL execution provably always sets CWD to the use
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260704_135445.md
Novelty: 5%

## [2026-07-07] signal-extract | If the SKILL passes `--root-dir <user-repo>` explicitly, the
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260704_135445.md
Novelty: 6%

## [2026-07-07] signal-extract | SELF-IDENTIFIED GAP (via /improve): the fix is partial — orc
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260704_135445.md
Novelty: 8%

## [2026-07-07] signal-extract | had polluted the real `go-sessions/` pointer store — `test_o
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260704_135445.md
Novelty: 6%

## [2026-07-07] signal-extract | The UserPromptSubmit injection could be sharpened: "CRITICAL
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260704_154324.md
Novelty: 8%

## [2026-07-07] signal-extract | The risk is a future `claude plugin update` clobbering it — 
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260704_154324.md
Novelty: 10%

## [2026-07-07] signal-extract | — the fix was to suppress the visible window; the empty Main
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260704_154324.md
Novelty: 8%

## [2026-07-07] signal-extract | Contradiction resolutions: (1) default mode `warn` per code 
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260704_225650.md
Novelty: 5%

## [2026-07-07] signal-extract | Retract proposal item (c) — don't delete shared claim_patter
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260704_225650.md
Novelty: 8%

## [2026-07-07] signal-extract | The tradeoff: red-team is already 8 agents, and `red-team-fa
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260704_231217.md
Novelty: 8%

## [2026-07-07] signal-extract | `P:/.data/wiki/concepts/auto-stage-commit-strategies.md` (20
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260704_231217.md
Novelty: 7%

## [2026-07-07] signal-extract | Plugin specialist done — notable finding PLUGIN-1: the cc-sk
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260704_231217.md
Novelty: 8%

## [2026-07-07] signal-extract | `plugin.json` \u2014 PLUGIN-1 (Path B silently never fires: 
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260704_231217.md
Novelty: 18%

## [2026-07-07] signal-extract | Fix via STATE-1's per-session keying + SessionStart TTL swee
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260704_231217.md
Novelty: 6%

## [2026-07-07] signal-extract | Request size ~794KB. 13 14 **Root Cause:*
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260705_133206.md
Novelty: 20%

## [2026-07-07] signal-extract | No official response from Anthropic is visible in the provid
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260705_133206.md
Novelty: 7%

## [2026-07-07] signal-extract | The reporter found 20+ orphaned subagent processes consuming
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260705_133206.md
Novelty: 12%

## [2026-07-07] signal-extract | semantic_critic escalates software_rca to BLOCK; Option B (b
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260705_133206.md
Novelty: 12%

## [2026-07-07] signal-extract | Root Cause ^ SyntaxError: unterminated string literal (detec
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260705_133206.md
Novelty: 27%

## [2026-07-07] signal-extract | Root Cause\\nThe running...'\n# These have actual newlines i
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260705_133206.md
Novelty: 11%

## [2026-07-07] signal-extract | Orphaned env var (no active hook reads it): PROBLEM_STMT_VER
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260705_192919.md
Novelty: 10%

## [2026-07-07] signal-extract | 20% cap-hit; most loops resolve within budget ⚠️ WIKI [333ms
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260705_192919.md
Novelty: 10%

## [2026-07-07] signal-extract | SessionStart may surface the reclaimable count but must not 
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260705_192919.md
Novelty: 17%

## [2026-07-07] signal-extract | Fixed by using `SimpleNamespace(name='wiki', fixable=[{...}]
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260705_192919.md
Novelty: 17%

## [2026-07-07] signal-extract | both check orphaned junctions (plugin-installer line 231-238
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260705_192919.md
Novelty: 10%

## [2026-07-07] signal-extract | Identity handshake (checks `identity.json` matches session I
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260705_192919.md
Novelty: 7%

## [2026-07-07] signal-extract | gate caught {blocks} premature RCA claim(s); spot-check a bl
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260705_192919.md
Novelty: 27%

## [2026-07-07] signal-extract | 20% cap-hit; most loops resolve within budget ⚠️ WIKI [275ms
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260705_192919.md
Novelty: 10%

## [2026-07-07] signal-extract | Deliberately not next: fixing the ~74 unregistered approve-e
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260706_170541.md
Novelty: 7%

## [2026-07-07] signal-extract | The root cause (PLUGIN_SLASH_EXECUTION_LANE exemption + inte
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260706_170541.md
Novelty: 7%

## [2026-07-07] signal-extract | A static settings list rots. claude-audit already audits set
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260706_170541.md
Novelty: 7%

## [2026-07-07] signal-extract | Gate the ceremony on it: `investigate`/`validate`/`decide` s
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260706_170621.md
Novelty: 6%

## [2026-07-07] signal-extract | **Worker-mode window is semantically wrong**: worker mode sh
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260706_170621.md
Novelty: 5%

## [2026-07-07] signal-extract | The fix is test-only (conftest fixture); the polluter was pr
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260706_170621.md
Novelty: 8%

## [2026-07-07] signal-extract | SessionStart may surface reclaimable count but must not dele
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260706_170621.md
Novelty: 12%

## [2026-07-07] signal-extract | SessionStart may surface the reclaimable count but must not 
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260706_170621.md
Novelty: 22%

## [2026-07-07] signal-extract | Never auto-delete; SessionStart may surface reclaimable coun
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260706_170621.md
Novelty: 12%

## [2026-07-07] signal-extract | SessionStart may surface the reclaimable count but must not 
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260706_170621.md
Novelty: 22%

## [2026-07-07] signal-extract | Mode-invariance bug: both branches of `if is_mutation:` at p
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260706_170621.md
Novelty: 7%

## [2026-07-07] signal-extract | GO_LOCAL_LLM was dead code. scripts\orchestrate.py:1065: # R
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260706_170621.md
Novelty: 12%

## [2026-07-07] signal-extract | Hook script naming convention — `{plugin}_{event}.py` Per `P
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260706_170622.md
Novelty: 7%

## [2026-07-07] signal-extract | The user's observed skips happen on skills that DO declare `
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260706_170622.md
Novelty: 9%

## [2026-07-07] signal-extract | There's a `TestExtractSlashCommand` class with tests for the
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260706_170622.md
Novelty: 5%

## [2026-07-07] signal-extract | Runs BEFORE the run-state check, so\n# it fires even when th
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260706_170622.md
Novelty: 5%

## [2026-07-07] signal-extract | user-authored and must be stripped before directive detectio
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260706_170622.md
Novelty: 9%

## [2026-07-07] signal-extract | `P:\tmp\scan_transcripts.py` → `P:\\tmp\\tmpscan_transcripts
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260706_175856.md
Novelty: 30%

## [2026-07-07] signal-extract | Then non-fatal PermissionError rmtree-ing old 1.0.55 cache `
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_82946cce.md
Novelty: 5%

## [2026-07-07] signal-extract | That means EITHER the state dir is elsewhere, OR the hook ha
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_82946cce.md
Novelty: 6%

## [2026-07-07] signal-extract | The user's "please fix the tests" was specifically about my 
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_82946cce.md
Novelty: 5%

## [2026-07-07] signal-extract | Flagged re.PatternError issue: FIXED (12 tests, root cause =
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_82946cce.md
Novelty: 14%

## [2026-07-07] signal-extract | ## Root cause `chs_cli.py:1172`: ```python session_count = t
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_cache_smoke.md
Novelty: 10%

## [2026-07-07] signal-extract | SessionStart_chs_delta_reindex.py — completely orphaned (not
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\failed to look up documentation⠐ SELF_REFLECTION.txt
Novelty: 12%

## [2026-07-07] signal-extract | [The Real Reason Your OpenClaw Skills Fail... (the fix)
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\filtered-tabs.md
Novelty: 17%

## [2026-07-07] signal-extract | TestSingleRootCauseEscapeHatch — verifies [SINGLE ROOT CAUSE
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\gemini.txt
Novelty: 11%

## [2026-07-07] signal-extract | TestEdgeCases — empty responses, None handling, non-RCA turn
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\gemini.txt
Novelty: 8%

## [2026-07-07] signal-extract | assess_recommendation(claim) -> RecommendationAssessment — c
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\Here's a chat history we've been having.  Please s.md
Novelty: 12%

## [2026-07-07] signal-extract | No current criticals; VSCode extension stalls rare (heap-rel
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\Here's the end conversation from a previous thread (1).md
Novelty: 8%

## [2026-07-07] signal-extract | ``` Root cause: H1 — classifier priority 5.0, fires after 8 
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\Here's the end conversation from a previous thread (1).md
Novelty: 8%

## [2026-07-07] signal-extract | The likely truth is: **late claim_type write is the root cau
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\Here's the end conversation from a previous thread (1).md
Novelty: 6%

## [2026-07-07] signal-extract | ```python # In Stop.py gate_name = "frameguard_stop" # Exact
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\Here's the end conversation from a previous thread (1).md
Novelty: 12%

## [2026-07-07] signal-extract | Prose-only turns: PreToolUse never fires → no receipt → Stop
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\Here's the end conversation from a previous thread (1).md
Novelty: 9%

## [2026-07-07] signal-extract | The visited set fix (line 255-257 in session_chain.py) alrea
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\hook pain 0.txt
Novelty: 8%

## [2026-07-07] signal-extract | ```markdown All setTimeout/setInterval calls must be tracked
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\How can I describe the problems with this page to.md
Novelty: 30%

## [2026-07-07] signal-extract | If `Stop_router.py` contains a second, newer validator unive
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\I'm working in claude code and we have hooks that.md
Novelty: 7%

## [2026-07-07] signal-extract | Exposes a Phase 0 gate (_run_phase0_depends_on_skills_gate) 
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\I'm working in claude code and we have hooks that.md
Novelty: 6%

## [2026-07-07] signal-extract | Stop_router.py is orphaned — delete it, migrate its unique v
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\I'm working in claude code and we have hooks that.md
Novelty: 8%

## [2026-07-07] signal-extract | Result: Stop_router.py is dead code living in a parallel uni
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\I'm working in claude code and we have hooks that.md
Novelty: 12%

## [2026-07-07] signal-extract | Orphan detection script — Fixed ValueError: 'P:\\...' is not
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\I'm working in claude code and we have hooks that.md
Novelty: 10%

## [2026-07-07] signal-extract | Problem: your orphan-detection script raised `ValueError: 'P
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\I'm working in claude code and we have hooks that.md
Novelty: 19%

## [2026-07-07] signal-extract | Here’s why it’s not strange and what they represent: ## What
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\I'm working in claude code and we have hooks that.md
Novelty: 8%

## [2026-07-07] signal-extract | UserPromptSubmit_modules/tests/test_behavior_contract.py:34 
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\I'm working in claude code and we have hooks that.md
Novelty: 8%

## [2026-07-07] signal-extract | The serial part is the veridical gate at line 1197-1205: if 
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\improve-chat-history.md
Novelty: 31%

## [2026-07-07] signal-extract | Only the veridical gate is serial: it runs first and short-c
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\improve-chat-history.md
Novelty: 23%

## [2026-07-07] signal-extract | Dead code in main loop (line 2030) turn_kind = _detect_turn_
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\in Claude Code Is it really impossible to have sil (1).md
Novelty: 8%

## [2026-07-07] signal-extract | CKS write path verified end-to-end (before=16 → after=17, ty
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\in claude code, I'm trying to create a useful cont (1).md
Novelty: 10%

## [2026-07-07] signal-extract | but **cold-start must be solved before default enablement**.
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\in claude code, I'm trying to create a useful cont (1).md
Novelty: 6%

## [2026-07-07] signal-extract | Deduplicate assumption_audit_v2.py line 2519-2520 (goal: eli
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\In claude code, we are a little stuck.  How can we.md
Novelty: 10%

## [2026-07-07] signal-extract | BLOCKER (run() untested) → FIXED via TestRunProtocol (6 test
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\inefficient gto 1.txt
Novelty: 20%

## [2026-07-07] signal-extract | SyntaxError: (unicode error) 'unicodeescape' codec can't dec
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\lazy 0 ⠂ Claude Code.txt
Novelty: 5%

## [2026-07-07] signal-extract | Bug 1 (NameError) → Stop hook crashes on _materialize_snapsh
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\mm multi-terminal isolation and data consistency 1.txt
Novelty: 10%

## [2026-07-07] signal-extract | If any claim is marked `DISPROVEN` or `UNCLEAR`, do not pres
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\My design skill made some lazy errors.  __❯ _think (1).md
Novelty: 11%

## [2026-07-07] signal-extract | Root Cause #3 (Why Errors Are Non-Blocking) The hook_runner.
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\narattion without execution.txt
Novelty: 16%

## [2026-07-07] signal-extract | Root cause (reframed): The guard hook at Stop_deletion_verif
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\not a good thinker LLM 3.txt
Novelty: 11%

## [2026-07-07] signal-extract | Root cause (proven from the code, not guessed) turn_start in
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\npm view @juicesharprpiv-advisor version.txt
Novelty: 6%

## [2026-07-07] signal-extract | The PowerShell profile doesn't have [ha-debug] directly — mu
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\npm view pi-loop-police version.txt
Novelty: 10%

## [2026-07-07] signal-extract | The fix is a procedural heuristic, not code. ● Background co
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\temp oauth ✳ IS.txt
Novelty: 13%

## [2026-07-07] signal-extract | Tradeoff: Router adds single-point maintenance but enables c
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\The attached file is for background info. Here's a (1).md
Novelty: 9%

## [2026-07-07] signal-extract | StopHook_drift_sentinel.py:87 — limit=50 hardcoded at call s
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\the llm is guessing again 0.txt
Novelty: 8%

## [2026-07-07] signal-extract | 4 new TestPhaseAwareApplicability tests: impl contracts sile
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\We are accepting a handoff from another LLM__text.md
Novelty: 7%

## [2026-07-07] signal-extract | Root cause (preliminary): The additionalContext scaffolding 
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\We are working in claude code on windows 11, with (1).md
Novelty: 10%

## [2026-07-07] signal-extract | Root Cause 2: PLAN MODE bypass checks string prefix, not sch
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\We are working in claude code on windows 11, with (1).md
Novelty: 6%

## [2026-07-07] signal-extract | > PreToolUse must be the primary blocking layer for “investi
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\We are working in claude code on windows 11, with (1).md
Novelty: 5%

## [2026-07-07] signal-extract | Policy routing (confirmed from code) at epistemic_validator.
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\We are working in claude code on windows 11, with (1).md
Novelty: 9%

## [2026-07-07] signal-extract | Returns False if response lacks analytical markers (because,
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\You can see towards the end of this conversation, (1).md
Novelty: 6%

## [2026-07-07] signal-extract | Fixed /resume silently dropping sessions when the first mess
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\yt-fts1.txt
Novelty: 11%

## [2026-07-07] signal-extract | (`core/chs/db.py:35`). `INSERT OR IGN +ORE` therefore silent
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\[CHS #917 #918 · pi #914 · go #916 #939 · gate #942 #943 #944 #945].txt
Novelty: 6%

## [2026-07-07] signal-extract | hook ingests `>0` messages on a session who -se transcript h
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\[CHS #917 #918 · pi #914 · go #916 #939 · gate #942 #943 #944 #945].txt
Novelty: 11%

## [2026-07-07] signal-extract | That prevents the classic failure mode where “principles” tu
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\_In claude code, I found this conversation super a.md
Novelty: 12%

## [2026-07-07] signal-extract | Each is engineered to output structured tasks (hypothesis, s
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\__❯ So I need to ask you questions because you can (1).md
Novelty: 6%

## [2026-07-07] signal-extract | When a contract run is active, PreToolUse must treat `allowe
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\__❯ what should skill-guard do___● Skill-guard enf.md
Novelty: 12%

## [2026-07-07] signal-extract | `contract_type` in `ExecutionRun` must be derived from SKILL
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\__❯ what should skill-guard do___● Skill-guard enf.md
Novelty: 8%

## [2026-07-07] signal-extract | With an active ExecutionRun, PreToolUse must treat allowed_t
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\__❯ what should skill-guard do___● Skill-guard enf.md
Novelty: 7%

## [2026-07-07] signal-extract | The Stop hook must be a pure contract checker for an Executi
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\__❯ what should skill-guard do___● Skill-guard enf.md
Novelty: 14%

## [2026-07-07] signal-extract | ExecutionRun.contract_type and ExecutionRun.response_require
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\__❯ what should skill-guard do___● Skill-guard enf.md
Novelty: 7%

## [2026-07-07] signal-extract | However, when writing or reading files that exceed a certain
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\π - .txt
Novelty: 8%

## [2026-07-07] signal-extract | Add a discriminating test (e.g., 'This would be wrong if...'
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\✳ Claude Code.txt
Novelty: 6%

## [2026-07-07] signal-extract | Root cause: During cc-aca-authority migration (task #552-#55
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\✳ Complete wrapper elimination for epistemic and investigation plugins.txt
Novelty: 10%

## [2026-07-07] signal-extract | UNGUARDED INJECTION ROOT CAUSE: Stop.py lines 4968-5005 inje
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\✳ Fix Chrome DevTools MCP response halts.txt
Novelty: 24%

## [2026-07-07] signal-extract | ORPHAN exemption: SessionStart_hook_health_check.py learns S
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\✳ Fix Chrome DevTools MCP response halts.txt
Novelty: 9%

## [2026-07-07] signal-extract | Dead Code Left Behind _classify_error_events() is now dead c
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\✳ Fix Chrome DevTools MCP response halts.txt
Novelty: 15%

## [2026-07-07] signal-extract | The issues are: NullPointerException doesn't match null (dif
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\✳ global-reasoning.txt
Novelty: 12%

## [2026-07-07] signal-extract | **What I did wrong**: Emitted "**Root cause analysis: Primar
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\✳ Improve single-LLM response quality.txt
Novelty: 6%

## [2026-07-07] signal-extract | **Evidence**: 107 > L11834 assistant: "**Root cause analysis
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\✳ Improve single-LLM response quality.txt
Novelty: 10%

## [2026-07-07] signal-extract | StopHook_unverified_stance.py:592 — explicitly catches "Root
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\✳ Research solutions for Claude Code issues.txt
Novelty: 8%

## [2026-07-07] signal-extract | Reconstructing the 3 === Case1-PowerShell-RCA === user_promp
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\✳ Research solutions for Claude Code issues.txt
Novelty: 12%

## [2026-07-07] signal-extract | with pytest.raises(HandoffValidationError, match="must be a 
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\✳ snapshot.txt
Novelty: 20%

## [2026-07-07] signal-extract | with pytest.raises(HandoffValidationError, match="must be a 
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\✳ snapshot.txt
Novelty: 18%

## [2026-07-07] signal-extract | with pytest.raises(HandoffValidationError, match="must be a 
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\✳ snapshot.txt
Novelty: 15%

## [2026-07-07] signal-extract | with pytest.raises(HandoffValidationError, match="missing re
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\✳ snapshot.txt
Novelty: 12%

## [2026-07-07] signal-extract | with pytest.raises(HandoffValidationError, match="resume_sna
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\✳ snapshot.txt
Novelty: 12%

## [2026-07-07] signal-extract | HandoffValidationError, match="decision_register must be a l
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\✳ snapshot.txt
Novelty: 14%

## [2026-07-07] signal-extract | with pytest.raises(HandoffValidationError, match="must be an
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\✳ snapshot.txt
Novelty: 12%

## [2026-07-07] signal-extract | with pytest.raises(HandoffValidationError, match="must be be
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\✳ snapshot.txt
Novelty: 12%

## [2026-07-07] signal-extract | with pytest.raises(HandoffValidationError, match="must be be
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\✳ snapshot.txt
Novelty: 17%

## [2026-07-07] signal-extract | Hypothesis: Recent changes caused this — Rejected because li
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\✳ Solve coding problem.txt
Novelty: 8%

## [2026-07-07] signal-extract | Hypothesis: turn_mode.py suppression is broken — Rejected be
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\✳ Solve coding problem.txt
Novelty: 6%

## [2026-07-07] signal-extract | verified) Root Cause Single root cause: Line 3443 in Stop.py
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\✳ Solve coding problem.txt
Novelty: 14%

## [2026-07-07] signal-extract | "PostToolUse:TaskCreate hook error" from another terminal Ro
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\✳ Terminal Issues.txt
Novelty: 11%

## [2026-07-07] signal-extract | Before I act, I need to find the actual reason rather than g
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\⠐ Install hermes-agent on Windows 11.txt
Novelty: 33%

## [2026-07-07] signal-extract | **Cost**: YouTube Data API has quota limits; must use free a
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\⠐ int-stream.txt
Novelty: 10%

## [2026-07-07] signal-extract | BREADCRUMB_VERIFIER_ENABLED — NOT orphaned: read in cc-aca-i
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\⠐ main.txt
Novelty: 11%

## [2026-07-07] signal-extract | BREADCRUMB_VERIFIER_MODE — NOT orphaned: read in cc-aca-inve
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\⠐ main.txt
Novelty: 11%

## [2026-07-07] signal-extract | The fix and Phase 5 should be decided by the user based on t
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\2026-07-03 [go #1067 #1068 #1069 · stop #1066 · telemetry #1070].md
Novelty: 6%

## [2026-07-07] signal-extract | A prior session's guess ("the fil +e is 2.7 GB", "the root c
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\2026-07-01 [CHS #917 · dream-cycle #976 · gate #942 · plugin-audit #982 #988 · opportunity #983 #989 #1001 · hooks #986 #987 · model #990 #991 · friction #992 #993 #994].txt
Novelty: 10%

## [2026-07-07] signal-extract | For example: # You run in Claude Code: echo "test" # Behind 
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\PreToolUse0.txt
Novelty: 7%

## [2026-07-07] signal-extract | Behavior must not change: all 9 tests pass before AND after.
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\2026-07-03 [go #1067 #1068 #1069 · stop #1066 · telemetry #1070].md
Novelty: 10%

## [2026-07-07] signal-extract | Windows API calls require ctypes (error-prone if misused) Co
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\example of stupid9.txt
Novelty: 10%

## [2026-07-07] signal-extract | Single-file, ~10 lines.\n\n## Falsification\nThis fix is wro
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260706_170622.md
Novelty: 12%

## [2026-07-07] signal-extract | Single-file, ~10 lines. 75 76 ## Falsification 77 This fix i
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260706_170622.md
Novelty: 6%

## [2026-07-07] signal-extract | Confidence: 75% — Evidence basis: Direct code analysis (drea
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\example of stupid9.txt
Novelty: 8%

## [2026-07-07] signal-extract | compression_first_stage: 30007ms is hardcoded in Headroom, n
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\✳ headroom.txt
Novelty: 12%

## [2026-07-07] signal-extract | Root cause: commit `634d2a2` (2026-06-28 14:07:51 MST, "fix(
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260630_160635.md
Novelty: 9%

## [2026-07-07] signal-extract | The root cause was that .PadRight() on .NET strings uses cod
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\✳ cc-bf.txt
Novelty: 6%

## [2026-07-07] signal-extract | Worse: `STOP_CROSS_VALIDATOR_ENABLED` defaults `false` (line
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260704_225650.md
Novelty: 12%

## [2026-07-07] signal-extract | Orphaned env var (no active hook reads it): CLAUDE_CODE_TASK
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260704_002157.md
Novelty: 6%

## [2026-07-07] signal-extract | Orphaned env var (no active hook reads it): CLAUDE_CODE_TASK
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260704_002157.md
Novelty: 11%

## [2026-07-07] signal-extract | (1) REGISTERED `P:/.claude/hooks/posttooluse/investigation_t
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260629_084915.md
Novelty: 15%

## [2026-07-07] signal-extract | 2 name: mcp-config-location-fix 3 description: "MCP servers 
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260704_154324.md
Novelty: 29%

## [2026-07-07] signal-extract | GTO v4.2 — 10 findings | Health: F (20) | Fresh 1 🔧 QUALITY 
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\⠐ Fix GTO PostToolUse hooks.txt
Novelty: 6%

## [2026-07-07] signal-extract | The fix is not to "disable" the hook — it's to satisfy it on
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\2026-07-01 [CHS #917 · dream-cycle #976 · gate #942 · plugin-audit #982 #988 · opportunity #983 #989 #1001 · hooks #986 #987 · model #990 #991 · friction #992 #993 #994].txt
Novelty: 6%

## [2026-07-07] signal-extract | Root cause:F-string contains % character**" 162 > 163 > User
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\✳ Improve single-LLM response quality.txt
Novelty: 9%

## [2026-07-07] signal-extract | Lines 1205-1230 that call them Root cause fix for /yt-channe
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\why did we switch topics ✳ skill-guard.txt
Novelty: 9%

## [2026-07-07] signal-extract | So the fix is adding a guard inside each hook that short-cir
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\✳ rca(g).txt
Novelty: 7%

## [2026-07-07] signal-extract | Worse: STOP_CROSS_VALIDATOR_ENABLED defaults false (line 113
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\✳ Debug LLM session export and context handling.txt
Novelty: 6%

## [2026-07-07] signal-extract | Orphaned env var (no active hook reads it): CLAUDE_CODE_TASK
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260704_002157.md
Novelty: 11%

## [2026-07-07] signal-extract | Orphaned env var (no active hook reads it): CLAUDE_CODE_TASK
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260705_192919.md
Novelty: 11%

## [2026-07-07] signal-extract | ⚠️ Wiki vault: 2 broken wikilink(s); 2 orphan page(s) (100% 
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260705_192919.md
Novelty: 19%

## [2026-07-07] signal-extract | `"the bug is"`, `"the issue is"`, `"root cause"`, `"caused b
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\We are working in claude code on windows 11, with (1).md
Novelty: 8%

## [2026-07-07] signal-extract | Fix 3 — Dead code removal: Removed the unreachable return Ep
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\We are working in claude code on windows 11, with (1).md
Novelty: 21%

## [2026-07-07] signal-extract | Let me check the orphan-detection code in main_health.py and
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260705_192919.md
Novelty: 19%

## [2026-07-07] signal-extract | The accompanying SKILL.md (v4.0.0) 3 is a thin dispatcher th
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\✳ bifrost.txt
Novelty: 7%

## [2026-07-07] signal-extract | WriteError: P:\.claude\provider-configs\test_headroom_zombie
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\✳ headroom.txt
Novelty: 18%

## [2026-07-07] signal-extract | Let me look at what I found after line 9418 — was there a re
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\2026-07-03 [go #1067 #1068 #1069 · stop #1066 · telemetry #1070].md
Novelty: 20%

## [2026-07-07] signal-extract | The _check_skill_first_gate() at line 1227 still runs first 
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\__❯ what should skill-guard do___● Skill-guard enf.md
Novelty: 7%

## [2026-07-07] signal-extract | The fix is to call _detect_critic_profile in the telemetry t
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\I'm working in claude code and we have hooks that.md
Novelty: 9%

## [2026-07-07] signal-extract | The root cause is clear: `_run_referent_coverage` was remove
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260527_151412.md
Novelty: 8%

## [2026-07-07] signal-extract | GO_LOCAL_LLM was dead code. skills\go\scripts\orchestrate.py
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260706_170621.md
Novelty: 12%

## [2026-07-07] signal-extract | # " Root cause: The orthogonal check at line 2437 had if not
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\The attached file is for background info. Here's a (1).md
Novelty: 9%

## [2026-07-07] signal-extract | The root cause is confirmed: line 3443 in Stop.py incorrectl
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\✳ Solve coding problem.txt
Novelty: 8%

## [2026-07-07] signal-extract | A prior session's g -uess ("the file is 2.7 GB", "the root c
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\2026-07-01 [CHS #917 · dream-cycle #976 · gate #942 · plugin-audit #982 #988 · opportunity #983 #989 #1001 · hooks #986 #987 · model #990 #991 · friction #992 #993 #994].txt
Novelty: 12%

## [2026-07-07] signal-extract | Here's what was done: Root cause: Commit 754030b371 added fr
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\Implement multi-terminal isolation and data consistency 1.txt
Novelty: 6%

## [2026-07-07] signal-extract | Root Cause (Layered) Primary: claim_patterns.py has no patte
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\llm can't tell what a task is and maybe a handoff issue ⠂ IS.txt
Novelty: 8%

## [2026-07-07] signal-extract | Root cause: The refactor in commit 754030b371 added from sha
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\mm multi-terminal isolation and data consistency 1.txt
Novelty: 6%

## [2026-07-07] signal-extract | external / not-our-code: native /goal evaluator (#994), glm-
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260704_002527.md
Novelty: 5%

## [2026-07-07] signal-extract | Confirmed root cause in `run_context.py:216-222`: `_resolve_
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260704_135445.md
Novelty: 6%

## [2026-07-07] signal-extract | Root cause is model_router_classify.py:129 hardcoding claude
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\✳ Check plugin docs and GitHub repo.txt
Novelty: 5%

## [2026-07-07] signal-extract | marketplace\plugins\cc-aca-epist emic\hooks\pretool\fact-gua
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\✳ Complete wrapper elimination for epistemic and investigation plugins.txt
Novelty: 14%

## [2026-07-07] signal-extract | Let me check what happened AFTER line 9418 — did I actually 
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\2026-07-03 [go #1067 #1068 #1069 · stop #1066 · telemetry #1070].md
Novelty: 10%

## [2026-07-07] signal-extract | Trade-off noted in the changelog: "may cause some flicker du
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\npm view pi-loop-police version.txt
Novelty: 11%

## [2026-07-07] signal-extract | **Skipped Registration Check**: Real root cause—SessionStart
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\LLM_1 says this about LLM_2_ ___● Based on the cha.md
Novelty: 10%

## [2026-07-07] signal-extract | Actual Root Cause (pre-existing issue) Headroom's compressio
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\✳ Research token cost saving strategies for LLMs.txt
Novelty: 9%

## [2026-07-07] signal-extract | ```json { "file_path": "P:\\.claude\\hooks\\tests\\test_epis
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260706_170720.md
Novelty: 12%

## [2026-07-07] signal-extract | [H3] A complete fix requires storing S_OLD's path BEFORE S_N
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\temp ⠐ ClaudeChainMiner.txt
Novelty: 8%

## [2026-07-07] signal-extract | The key insight is that the proposal mis-attributed the root
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260704_231217.md
Novelty: 10%

## [2026-07-07] signal-extract | This converted newl' Traceback (most recent call last): File
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\✳ Research solutions for Claude Code issues.txt
Novelty: 6%

## [2026-07-07] signal-extract | Let me fix that: ● Update(.claude\skills\design\SKILL.md) ⎿ 
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\⠐ Claude Code2.txt
Novelty: 8%

## [2026-07-07] signal-extract | Turn mode invariant assertion — Stop.py:618-626 File: P:\\.c
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\We are working in claude code on windows 11, with (1).md
Novelty: 6%

## [2026-07-07] signal-extract | Dispatch flows through the local `P:/.claude/hooks/Stop.py` 
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260704_225650.md
Novelty: 6%

## [2026-07-07] signal-extract | ".claude/hooks/Stop_router.py" 2>/dev/null | head -10) ⎿ 52c
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\Implement multi-terminal isolation and data consistency 0.txt
Novelty: 8%

## [2026-07-07] signal-extract | ```json { "taskId": "977", "subject": "Universal skill-first
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260706_170622.md
Novelty: 5%

## [2026-07-07] signal-extract | Let me check what "40 failing hooks" refers to and find the 
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\✳ Fix Chrome DevTools MCP response halts.txt
Novelty: 6%

## [2026-07-07] signal-extract | G4 (go_continuation_gate.py, direct-entry in settings.json) 
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260706_170621.md
Novelty: 8%

## [2026-07-07] signal-extract | The fix is to make PreToolUse Layer 0 universal (block non-`
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260706_170622.md
Novelty: 9%

## [2026-07-07] signal-extract | the proper fix by adding a file handler to logging.basicConf
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\daemon1.txt
Novelty: 11%

## [2026-07-07] signal-extract | P:\\.claude\\hooks\\Stop.py — removed orphaned if anomalies:
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\We are accepting a handoff from another LLM__text.md
Novelty: 12%

## [2026-07-07] signal-extract | Import from search_research.config instead.", DeprecationWar
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\03-19-2025 - sychopath 0.txt
Novelty: 22%

## [2026-07-07] signal-extract | Found the root cause: `Stop._pin_scope_env(data)` at line 15
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\2026-07-03 [go #1067 #1068 #1069 · stop #1066 · telemetry #1070].md
Novelty: 7%

## [2026-07-07] signal-extract | packages\.claude-marketplace\plugins\cc-skills-utils\skills\
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260705_192919.md
Novelty: 5%

## [2026-07-07] signal-extract | This is a systematic schema issue, not plugin-specific.[^8_2
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\and claude code, How do we register a local plugin.md
Novelty: 10%

## [2026-07-07] signal-extract | Both _check_skill_first_gate() (PreToolUse.py:1131) and skil
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\llm doesn't like to check requirements for it's own solutions resulting in garbage solutions that don't work⠐ skill-guard.txt
Novelty: 8%

## [2026-07-07] signal-extract | Correctly identified ModuleNotFoundError: No module named '_
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\narattion without execution.txt
Novelty: 14%

## [2026-07-07] signal-extract | Add it explicitly. ● Bash(powershell.exe -NoProfile -Command
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\⠐ Install hermes-agent on Windows 11.txt
Novelty: 8%

## [2026-07-07] signal-extract | FIXED the root cause of the re.PatternError (12 tests now pa
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_82946cce.md
Novelty: 10%

## [2026-07-07] signal-extract | Orphaned env var (no active hook reads it): STOP_HYPOTHESIS_
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260705_192919.md
Novelty: 12%

## [2026-07-07] signal-extract | User smoke test: Run /reload-plugins, verify recap doesn't t
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\✳ Solve coding problem.txt
Novelty: 6%

## [2026-07-07] signal-extract | ```json { "-A": 3, "-B": 3, "-n": true, "output_mode": "cont
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260704_154324.md
Novelty: 8%

## [2026-07-07] signal-extract | Let me check how Stop.py constructs its config: Searched for
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\Here's a chat with claude code.  Any ideas for a s.md
Novelty: 17%

## [2026-07-07] signal-extract | I halt/bake for extended periods (lines 137, 161, 171, 173, 
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\✳ Fix Chrome DevTools MCP response halts.txt
Novelty: 6%

## [2026-07-07] signal-extract | Thought for 16s, searched for 1 pattern, read 1 file (ctrl+o
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\[CHS #917 #918 · pi #914 · go #916 #939 · gate #942 #943 #944 #945].txt
Novelty: 10%

## [2026-07-07] signal-extract | `/bf compare ...` → LangGraph multi-model fan-out + synthesi
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\how do I install bifrost to work with claude code_ (1).md
Novelty: 8%

## [2026-07-07] signal-extract | Root cause: win32api.CreateMutex doesn't exist in pywin32
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\✳ Terminal Issues.txt
Novelty: 43%

## [2026-07-07] signal-extract | CONVENTION claims must NOT bypass even with hedge words sinc
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\Here's a chat history we've been having.  Please s.md
Novelty: 9%

## [2026-07-07] signal-extract | Line 1428-1430: for MEDIUM/HIGH risk, it checks target_read 
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\✳ Complete wrapper elimination for epistemic and investigation plugins.txt
Novelty: 6%

## [2026-07-07] signal-extract | The root cause is that turn_mode is never passed into Episte
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\We are working in claude code on windows 11, with (1).md
Novelty: 11%

## [2026-07-07] signal-extract | — DEFERRED — not a plugin change ### Proposal restated Add 5
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260705_133206.md
Novelty: 7%

## [2026-07-07] signal-extract | Here's what I found and what I recommend. ## Q2 — root cause
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260704_221306.md
Novelty: 6%

## [2026-07-07] signal-extract | Let me add it properly. ● Update(packages\.claude-marketplac
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\ccr dashboard redesign.txt
Novelty: 6%

## [2026-07-07] signal-extract | Once conversation history exceeds capacity, the oldest 10,00
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\What is _  ❯ ◯ remember · claude-plugins-official.md
Novelty: 5%

## [2026-07-07] signal-extract | Searched for 1 pattern, read 1 file (ctrl+o to expand) ⎿ Pos
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\✳ Check plugin docs and GitHub repo.txt
Novelty: 6%

## [2026-07-07] signal-extract | `task_contract_fit` Stop gate in `P:/.claude/hooks/Stop.py` 
Source: downloads-signal-extract
Source file: C:\Users\brsth\Downloads\chain_20260705_133206.md
Novelty: 6%

## [2026-07-07] ingest | Completion Evidence Contract — typed ledger to prevent overclaiming
Source: session
Transcript: session-2026-07-07

## [2026-07-07] ingest | Affordance-based routing — choose commands by machinery fit, not by quoting docs
Source: session
Transcript: session-2026-07-07

## [2026-07-07] ingest | Discoverable-fact-offloading split — asking the user for discoverable facts = inventing them
Source: session
Transcript: session-2026-07-07

## [2026-07-07] ingest | Skill Enforcement Upstream Constraints
Source: session
Transcript: C:\Users\brsth\.claude\projects\P--\a3a261fd-9218-428a-9986-3ab39794c7f6.jsonl
Content: Upstream CC rejects force-invocation (#15136 closed-not-planned); skill-scoped frontmatter hooks unreliable via plugin (#17688 Open, #30874 closed-not-planned); cc-spex state-file phase gate is the one community-validated ordering pattern. Decision-shaping for #1090 Option 1 vs Option 2.
Page: wiki/concepts/skill-enforcement-upstream-constraints.md

## [2026-07-07] ingest | Reliable Skill Output Consistency: Three Tiers
Source: session
Transcript: C:\Users\brsth\.claude\projects\P--\a3a261fd-9218-428a-9986-3ab39794c7f6.jsonl
Content: Tier A Structured Outputs API (constrained decoding); Tier B synthetic-tool trick (input_schema IS output schema, reuse tool-calling machinery inside Claude Code); Tier C prompt-engineering (format/prefill/examples/retrieval/chain/role). No existing page covered output reliability.
Page: wiki/concepts/reliable-skill-output-consistency.md

## [2026-07-07] ingest | Python Renderer for Skill Output Consistency
Source: session
Transcript: session-2026-07-07-rns
Pattern: code owns format, model owns content. Demonstrated by RNS (drift) vs recap (render_actions).
## [2026-07-08] ingest | Windows cross-process file locking — msvcrt.locking on a 0-byte file
Source: session
Transcript: b8c3e0a4-3c21-4ab7-9fa9-5b8df525d370.jsonl
Page: P:/.data/wiki/concepts/windows-cross-process-file-locking.md
## [2026-07-08] ingest | Background warm-up atomic publish — daemon-thread build vs concurrent read
Source: session
Transcript: b8c3e0a4-3c21-4ab7-9fa9-5b8df525d370.jsonl
Page: P:/.data/wiki/concepts/background-warmup-atomic-publish.md
## [2026-07-08] ingest | Claude Code auto-mode classifier model is NOT independently configurable
Source: session-2026-07-08
Page: P:/.data/wiki/concepts/claude-code-classifier-not-configurable.md
## [2026-07-08] ingest | Windows P/Invoke CreateProcess: console isolation via CREATE_NEW_CONSOLE
Source: session-2026-07-08
Page: P:/.data/wiki/concepts/windows-createprocess-console-isolation.md
## [2026-07-08] ingest | Local model readiness gate: LOADED is enough, don't probe inference
Source: session-2026-07-08
Page: P:/.data/wiki/concepts/local-model-readiness-gate.md
## [2026-07-08] ingest | llama-server orphan-on-give-up + crash-log archival
Source: session-2026-07-08
Page: P:/.data/wiki/concepts/llama-server-orphan-on-give-up.md

## [2026-07-09] ingest | Critique artifacts inherit the failure mode they critique
Source: session
Transcript: C:/Users/brsth/.claude/projects/P--/07d9d135-72e7-4ace-800a-8a10a5caeed4/

## [2026-07-09] ingest | Preference-Without-Enforcement Pattern
Source: session-2026-07-09
Transcript: session be39a5da

## [2026-07-10] ingest | Deliberation Topology & Ultracode Integration
Source: session-2026-07-10
SHA256: e24a85dd35a5d5a514ed57015d891a66a38999461fd7bbbfdcc23fda0a7dc7c4

## [2026-07-11] ingest | ADR: Epistemic Deliberation Architecture
Source: session-2026-07-10-deliberation-design
SHA256: n/a (session-authored)

## [2026-07-09] ingest | Git Submodule Topology for Plugin Monorepo
Source: session-2026-07-09
Transcript: session be39a5da

## [2026-07-17] ingest | Grok Build: env_key falls back to grok.com OIDC when process env is missing → 401 from third-party providers
Source: session-2026-07-17
Transcript: sessions/P%3A%5C/019f6f1e-34e0-7c03-840f-2a1a30683671

## [2026-07-17] ingest | Grok Build two_pass_compaction is prefire+final scheduler, NOT two LLM summarization passes
Source: session-2026-07-17
Transcript: sessions/P%3A%5C/019f6f1e-34e0-7c03-840f-2a1a30683671

## [2026-07-17] ingest | OpenCode Go: hy3-preview appears in /v1/models catalog but is rejected at chat time
Source: session-2026-07-17
Transcript: sessions/P%3A%5C/019f6f1e-34e0-7c03-840f-2a1a30683671

## [2026-07-18] ingest | Plan mode stuck-exit behavioral fix
Source: session-2026-07-18
Agent: grok

## [2026-07-18] ingest | Behavioral rules beat hooks when agent has context
Source: session-2026-07-18
Agent: grok

## [2026-07-18] ingest | Terminal-scoped artifacts isolation pattern
Source: session-2026-07-18
Agent: grok

## [2026-07-18] ingest | Pre-emission verification calibration
Source: session-2026-07-18
Agent: grok

## [2026-07-18] deprecate | Behavioral rules beat hooks (superseded)
Source: session-2026-07-18
Agent: grok

## [2026-07-18] ingest | Grok PreToolUse matcher semantics — Bash vs .* and the read-only fast-path
Source: session-2026-07-18
Agent: grok

## [2026-07-18] ingest | Grok hook diagnostic method — how to tell if hooks are firing
Source: session-2026-07-18
Agent: grok

## [2026-07-18] ingest | Multi-terminal hook state isolation — session-scoped flag files
Source: session-2026-07-18
Agent: grok

## [2026-07-18] correction | Grok PreToolUse matcher semantics (earlier claims retracted)
Source: session-2026-07-18
Agent: grok
Note: TUI annotations proved hooks DO dispatch; failures were path/env-var, not matcher

## [2026-07-18] ingest | Grok hook command env-var pre-flight validation
Source: session-2026-07-18
Agent: grok

## [2026-07-18] ingest | Midea U-shaped AC recall — what Canadian retailers are actually selling
Source: session-2026-07-18
Agent: grok
Notes: Health Canada RA-77547 covers the whole Midea U-shaped family 8K/10K/12K BTU (plus Danby/Frigidaire/Insignia/Perfect Aire rebadges). The two BB.ca SKUs verified in-session (19418425 = MW10MSWBA4RCM, 19421982 = MW10MSWBA5RCM) are on the recall list and sold as 'new' by Midea America (Canada) Corp. The Midea.ca recall-lookup form requires serial number (not model) and renders a literal {{ERROR}} template variable — not a working pre-purchase tool. Reliable workflow is Ctrl-F the model on Health Canada's RA-77547 list, or call 1-888-345-0256.

## [2026-07-18] ingest | MCP browser automation on Canadian retail sites — known gates and missing workarounds
Source: session-2026-07-18
Agent: grok
Notes: Chrome DevTools MCP works for general retail browsing but escalates to Akamai 'Access Denied' on re-navigation in the same session (verified bestbuy.ca — first PDP loaded, subsequent navigations blocked). Walmart.ca serves a PerimeterX 'Press & Hold' HUMAN CHALLENGE unsolvable by MCP (no pressure sensor) — works around with Google search-snippet metadata. Canadian Tire preferred-store binding is via session cookie after a UI click on 'Select this store' on the store locator page; ?postalCode URL params are silently ignored. See cross-link to the Midea recall page for application context.

## [2026-07-18] deletion | midea-u-shaped-ac-recall-canada.md retracted by user
Source: session-2026-07-18
Agent: grok
Notes: Page removed at user request. Cross-link on mcp-browser-canada-retail-gating.md replaced with explanatory note. Underlying recall facts (Health Canada RA-77547, MW-prefix SKU coverage) remain directly verifiable on the Health Canada recall page; they are no longer held in this vault. The original ingest log entry above is preserved as historical record of what was written and when.

## [2026-07-18] ingest | Wiki corpus is Claude-Code-skewed; tag every wiki citation by host provenance
Source: session-2026-07-18
Agent: grok
Notes: New durable rule covering: (1) corpus skew (most pages written under Claude Code); (2) four-tag taxonomy for citations (Grok Build / Claude Code / Cross-host / Host-agnostic); (3) operating pattern for /wiki queries (query QMD, grep slugs, cite with tag, verify before transfer). Mirrored at ~/.grok/AGENTS.md under Hard rules as ### Wiki citation provenance (cross-host tag required). Cross-links to grok-build-hook-host-ceiling, grok-pretooluse-matcher-and-readonly-fastpath, grok-hook-command-env-var-pre-flight-validation.

## [2026-07-18] demotion | Never invent provenance identity (AGENTS.md Hard rule)
Source: AGENTS.md Hard rules demoted 2026-07-18
Agent: grok
Notes: Demoted from ~/.grok/AGENTS.md line 73 (subsection under ## Hard rules). Rule fires only when the assistant would otherwise output a transaction-identity string (rare). Rule text and original "Allowed sources" hierarchy preserved verbatim in the wiki page. Reason: 12 lines + boilerplate, narrow firing, fits clean in wiki where load is on-demand.

## [2026-07-18] demotion | Reviewers do not redefine the goal (AGENTS.md Hard rule)
Source: AGENTS.md Hard rules demoted 2026-07-18
Agent: grok
Notes: Demoted from ~/.grok/AGENTS.md line 110 (subsection under ## Hard rules). 3-line rule, narrow firing condition ("I am in reviewer mode"). Preserved verbatim in the wiki page. Demoted as part of routine trim pass; rule text is recoverable via /wiki query if needed mid-session.

## [2026-07-18] ingest | Skill authoring host-applicability convention
Source: session-2026-07-18
Agent: grok
Notes: Companion rule to wiki-citation-host-provenance -- covers WRITING (SKILL.md frontmatter `host:` field) where the citation rule covers READING. Audit found 884 SKILL.md files, 0 with host tags. Convention applies prospectively. Backfill not recommended -- most live in plugin caches. Mirrored at ~/.grok/AGENTS.md under ## Hard rules as ### Skill authoring host provenance (cross-host tag required). Lint script: P:/tmp/lint_skill_hosts.py.

## [2026-07-18] demotion | Invariants beat environment comfort (AGENTS.md Hard rule)
Source: AGENTS.md Hard rules wikified 2026-07-18
Agent: grok
Notes: Demoted from ~/.grok/AGENTS.md H3 subsection (### Invariants beat environment comfort) under ## Hard rules (predictable error classes). Body preserved verbatim in the wiki page. AGENTS.md now carries a header + wikilink reference pointer only. Part of compression pass targeting 15 KB size goal. Recovers by /wiki query.

## [2026-07-18] demotion | Minimal fix and root cause (not minimal alone) (AGENTS.md Hard rule)
Source: AGENTS.md Hard rules wikified 2026-07-18
Agent: grok
Notes: Demoted from ~/.grok/AGENTS.md H3 subsection (### Minimal fix and root cause (not minimal alone)) under ## Hard rules (predictable error classes). Body preserved verbatim in the wiki page. AGENTS.md now carries a header + wikilink reference pointer only. Part of compression pass targeting 15 KB size goal. Recovers by /wiki query.

## [2026-07-18] demotion | Model-as-orchestrator (AGENTS.md Hard rule)
Source: AGENTS.md Hard rules wikified 2026-07-18
Agent: grok
Notes: Demoted from ~/.grok/AGENTS.md H3 subsection (### Model-as-orchestrator) under ## Hard rules (predictable error classes). Body preserved verbatim in the wiki page. AGENTS.md now carries a header + wikilink reference pointer only. Part of compression pass targeting 15 KB size goal. Recovers by /wiki query.

## [2026-07-18] demotion | Trust over believability (AGENTS.md Hard rule)
Source: AGENTS.md Hard rules wikified 2026-07-18
Agent: grok
Notes: Demoted from ~/.grok/AGENTS.md H3 subsection (### Trust over believability) under ## Hard rules (predictable error classes). Body preserved verbatim in the wiki page. AGENTS.md now carries a header + wikilink reference pointer only. Part of compression pass targeting 15 KB size goal. Recovers by /wiki query.

## [2026-07-18] demotion | Self-review before shipping advice (AGENTS.md Hard rule)
Source: AGENTS.md Hard rules wikified 2026-07-18
Agent: grok
Notes: Demoted from ~/.grok/AGENTS.md H3 subsection (### Self-review before shipping advice) under ## Hard rules (predictable error classes). Body preserved verbatim in the wiki page. AGENTS.md now carries a header + wikilink reference pointer only. Part of compression pass targeting 15 KB size goal. Recovers by /wiki query.

## [2026-07-18] demotion | Edit-then-verify (every edit, no exceptions) (AGENTS.md Hard rule)
Source: AGENTS.md Hard rules wikified 2026-07-18
Agent: grok
Notes: Demoted from ~/.grok/AGENTS.md H3 subsection (### Edit-then-verify (every edit, no exceptions)) under ## Hard rules (predictable error classes). Body preserved verbatim in the wiki page. AGENTS.md now carries a header + wikilink reference pointer only. Part of compression pass targeting 15 KB size goal. Recovers by /wiki query.

## [2026-07-18] demotion | Inference chains, bare numbers, and destructive-write preflight (AGENTS.md Hard rule)
Source: AGENTS.md Hard rules wikified 2026-07-18
Agent: grok
Notes: Demoted from ~/.grok/AGENTS.md H3 subsection (### Inference chains, bare numbers, and destructive-write preflight) under ## Hard rules (predictable error classes). Body preserved verbatim in the wiki page. AGENTS.md now carries a header + wikilink reference pointer only. Part of compression pass targeting 15 KB size goal. Recovers by /wiki query.

## [2026-07-18] demotion | No question theater (do the non-destructive investigation) (AGENTS.md Hard rule)
Source: AGENTS.md Hard rules wikified 2026-07-18
Agent: grok
Notes: Demoted from ~/.grok/AGENTS.md H3 subsection (### No question theater (do the non-destructive investigation)) under ## Hard rules (predictable error classes). Body preserved verbatim in the wiki page. AGENTS.md now carries a header + wikilink reference pointer only. Part of compression pass targeting 15 KB size goal. Recovers by /wiki query.

## [2026-07-18] demotion | Objective triggers (evaluate each; each is falsifiable) (AGENTS.md H3)
Source: AGENTS.md wikified during plan-skill + AGENTS.md compression pass
Agent: grok
Notes: Demoted from ~/.grok/AGENTS.md H3 subsection on 2026-07-18 during a routine compression pass targeting 15 KB size goal. AGENTS.md now carries the header + a wikilink reference pointer only; body loaded on demand via /wiki query. The four plan-mode rules are also mirrored at ~/.grok/skills/plan/SKILL.md for /plan invocation. Body preserved verbatim in the wiki page.

## [2026-07-18] demotion | Fire rule (when plan mode MUST appear as a named option) (AGENTS.md H3)
Source: AGENTS.md wikified during plan-skill + AGENTS.md compression pass
Agent: grok
Notes: Demoted from ~/.grok/AGENTS.md H3 subsection on 2026-07-18 during a routine compression pass targeting 15 KB size goal. AGENTS.md now carries the header + a wikilink reference pointer only; body loaded on demand via /wiki query. The four plan-mode rules are also mirrored at ~/.grok/skills/plan/SKILL.md for /plan invocation. Body preserved verbatim in the wiki page.

## [2026-07-18] demotion | Do NOT surface plan mode when (AGENTS.md H3)
Source: AGENTS.md wikified during plan-skill + AGENTS.md compression pass
Agent: grok
Notes: Demoted from ~/.grok/AGENTS.md H3 subsection on 2026-07-18 during a routine compression pass targeting 15 KB size goal. AGENTS.md now carries the header + a wikilink reference pointer only; body loaded on demand via /wiki query. The four plan-mode rules are also mirrored at ~/.grok/skills/plan/SKILL.md for /plan invocation. Body preserved verbatim in the wiki page.

## [2026-07-18] demotion | Plan mode vs /go (resolve the default) (AGENTS.md H3)
Source: AGENTS.md wikified during plan-skill + AGENTS.md compression pass
Agent: grok
Notes: Demoted from ~/.grok/AGENTS.md H3 subsection on 2026-07-18 during a routine compression pass targeting 15 KB size goal. AGENTS.md now carries the header + a wikilink reference pointer only; body loaded on demand via /wiki query. The four plan-mode rules are also mirrored at ~/.grok/skills/plan/SKILL.md for /plan invocation. Body preserved verbatim in the wiki page.

## [2026-07-18] demotion | Grok Build host authority (don't confabulate across hosts) (AGENTS.md H3)
Source: AGENTS.md wikified during plan-skill + AGENTS.md compression pass
Agent: grok
Notes: Demoted from ~/.grok/AGENTS.md H3 subsection on 2026-07-18 during a routine compression pass targeting 15 KB size goal. AGENTS.md now carries the header + a wikilink reference pointer only; body loaded on demand via /wiki query. The four plan-mode rules are also mirrored at ~/.grok/skills/plan/SKILL.md for /plan invocation. Body preserved verbatim in the wiki page.

## [2026-07-19] update | Grok Build Hook Host Ceiling — passive-surfacing EVIDENCE_GAP resolved
Source: session-2026-07-18
Agent: grok
Note: probe-passive-surface fired; none of 4 channels reached model; passive injection is closed

## [2026-07-19] ingest | Grok PreToolUse deny contract — verified end-to-end (Python)
Source: session-2026-07-18
Agent: grok

## [2026-07-19] ingest | Grok hook script reliability — Python vs bash on Windows
Source: session-2026-07-18
Agent: grok

## [2026-07-19] update | Multi-terminal hook state isolation — empirical confirmation added
Source: session-2026-07-18
Agent: grok

## [2026-07-18] ingest | Grok Build PreToolUse hook harness debug methodology
Source: session-2026-07-18 hook canary investigation
Agent: grok
Notes: Captures the diagnostic pattern that distinguishes harness-side bugs from script-side bugs in Grok Build PreToolUse hook reporting. Today's investigation found (a) the wrapper reports exit 1 even when scripts exit 0, and (b) GROK_HOOK_* env vars are not exported. Both are host-side; the methodology tells future agents how to identify them. Cross-links: grok-build-hook-host-ceiling, grok-pretooluse-matcher-and-readonly-fastpath, wiki-citation-host-provenance.

## [2026-07-18] edit | wiki pages -- host: grok tag added
Source: session-2026-07-18 AGENTS.md compression follow-on
Agent: grok
Notes: Added `host: grok` field to frontmatter of 18 wiki pages created in this session (3 demotions + 8 non-plan rules + 4 plan-mode rules + 1 Grok Build host authority + 2 existing rule pages: skill-host-applicability-convention, wiki-citation-host-provenance). Convention applies prospectively per the Skill authoring rule. Existing 781 wiki pages are pre-convention.

## [2026-07-18] edit | lint_skill_hosts.py relocated to ~/.grok/scripts/
Source: AGENTS.md compression follow-on
Agent: grok
Notes: Lint script moved from P:/tmp/lint_skill_hosts.py to C:\Users\brsth\.grok\scripts\lint_skill_hosts.py -- per the AGENTS.md "no maintained transients in P:/tmp/" rule. Extended with a `description:` frontmatter check (skill without description field can't be auto-loaded).

## [2026-07-19] ingest | Worktree-root policy hook design (2026-07)
Source: session
Transcript: session-2026-07-19

## [2026-07-19] ingest | Claude Code hooks bug landscape (2026-07-19)
Source: session
Transcript: session-2026-07-19

## [2026-07-19] ingest | /verify is a bundled Claude Code skill (slash command), not Skill-tool invocable
Source: session
Transcript: C:\Users\brsth\.claude\projects\P--\45504861-e019-4c69-a420-34761e7d303e.jsonl
Path: P:/.data/wiki/concepts/claude-code-verify-builtin-skill.md

## 2026-07-20

### Added
- concepts/plausible-narratives-substitute-for-verification.md — cognitive pattern where plausible narratives override verification. 5 observed instances from 2026-07-20 session. Structural fix: treat narrative as signal to read docs, not as answer.
- concepts/exemption-logic-as-conflict-signal.md — architectural principle: don't gate what the layer above already gates. Worked example: CCR proxy ceiling (6 commits of failed exemptions → removed). Discriminating test for when upstream gates are justified.
- concepts/grok-build-runtime-docs-divergence.md — the workspace's Claude-Code-flavored docs describe enforcement that doesn't fire under Grok Build (compat.claude.hooks=false, cc-aca-* disabled). Active-surface snapshot bridges the gap. Resolution options tracked.

### Added (late session)
- concepts/qmd-semantic-search-requires-llm-backend.md — root cause of QMD's broken semantic search: CLI didn't pass llm_backend (BM25-only), auto-link timeout too short, default model weak. 3-layer fix documented.

### Added (closing the lanes-vs-roles gap)
- concepts/model-lanes-vs-roles.md — the 2-lane routing framework (Reasoning vs Code), extracted from /go spawn recipe into its own wiki concept. Documents: ccr-ornith capabilities + limitations (65K context, Windows attr false-positives, 956s timeout), DiffusionGemma capabilities + the critical spawn_subagent failure + direct API workaround, Gemini 3.x as new free option, full fleet table (11 models with lane/cost/context), wave table, context-fit formula. Cross-links model-picker, compensating-for-weaker-models, gemini catalog, gemini-api-vs-agy-cli.

## 2026-07-21 — optimality-claims-are-completion-claims

- **Concept:** "Optimal" / "best" / "recommended" claims are structurally equivalent to "done" / "fixed" claims; apply the same verification discipline (name metric, name alternatives, show comparison, state falsifier)
- **Source:** Session 019f8155 — self-referential /www run triggered by "how do you know what you're saying is optimal?"
- **Why durable:** Captures a discipline that's missing from the wiki despite three adjacent concepts (verification-before-completion, plausible-narratives, evidence-first). Closes a specific failure mode where "optimal" framing substitutes for actual comparison. Includes a legitimate escape hatch: when operator policy has eliminated certain alternatives upstream, downstream agents can cite that policy instead of re-comparing.
- **Auto-linked:** wiki/concepts/verification-before-completion-principle (refines), wiki/concepts/plausible-narratives-substitute-for-verification (related)
- **Research ledger:** P:/.data/www-ledger/optimality-claims-verification.md

### Added (/wiki — session distillate)
- concepts/rule-not-fired-vs-rule-doesnt-exist.md — meta-pattern from /tp critique: process failures on this host are overwhelmingly trigger failures (rule exists but doesn't fire), not knowledge gaps (rule doesn't exist). Worked example: the agent had a rule requiring >=2 alternatives for hard-to-reverse decisions, but built the Search MCP from user suggestion without evaluating alternatives. Fix: skill gating (/go architectural profile), not another rule. Includes diagnostic table and cost/benefit for when to add triggers.

## [2026-07-21] ingest | File edit failures: two classes with distinct fixes
Source: session-2026-07-21
Agent: grok
Notes: New concept — the persistence-vs-collision distinction for file edit losses. Class A (persistence failure, OS/tool layer) fixed by atomic write. Class B (sequential collision, agent concurrency) NOT fixed by atomic write; fixed by append-only for logs, conditional write for shared docs. Born from the 2026-07-21 log.md incident where 13 entries were lost to Class B collision misdiagnosed as Class A. v1 file-editing-protocol conflated the two; v2 (P:/tmp/file-editing-protocol-v2-019f819a.md) codifies the distinction.
Page: wiki/concepts/file-edit-failures-two-classes.md

## [2026-07-21] ingest | External reports: silent edit non-persistence and shell quoting failures
Source: session-2026-07-21-www
Agent: grok
Notes: /www research — external prevalence of Class A silent writes (Claude Code #40227/#49805, Cursor buffer-not-disk) and Class C shell quoting (PowerShell @'...'@ in Bash #65162). Confirms industry reports match local protocol. Page: concepts/external-silent-edit-and-shell-quoting-reports.md

## 2026-07-20 — subagent-synthesis-report-gate

- **Page:** wiki/concepts/subagent-synthesis-report-gate.md
- **Why:** the subagent-synthesis→report-gate rule was added to ~/.grok/AGENTS.md (lines 100–125) earlier in this session but never distilled to a wiki concept. The rule has a real reference failure (cc-council incident) and a companion failure mode (storytelling under uncertainty). Wiki page makes the rule discoverable via semantic search; the AGENTS.md entry stays load-bearing for always-loaded behavior.
- **Existing pages checked:** llm-handoff-best-practices, optimal-cross-session-chain-traversal-aar-handoff-grok, handoff-skill-v011-validators, llm-council-and-model-fusion — none cover the subagent-synthesis-specific verification-gate rule.
- **Superseded/contradicted:** none.

### Added + corrected (model pool concept)
- concepts/model-pool-not-chain.md — CORRECTS the chain notation in /go and model-lanes-vs-roles. Models within a lane are a POOL of qualified candidates, not a ranked fallback chain. Any pool member that clears the quality floor is acceptable; selection by situational fit, not fixed ordering. Chain notation led another LLM to propose linear fallback (DGemma -> ccr-ornith -> parent), which is wrong.
- concepts/model-lanes-vs-roles.md — UPDATED: "Primary/Escalate" columns changed to "Free pool members/Escalation tier"; "fallback" labels changed to "pool member"; pool note added linking to model-pool-not-chain.
- /go SKILL.md spawn recipe — UPDATED: wave table changed from chain notation (A -> B -> C) to pool notation ({A, B, C} -> escalate); spawn example updated to show pool selection logic, not chain escalation.

### Added (fleet rationalization)
- concepts/model-fleet-provider-pools.md — full 46-slug fleet across 8 access paths (CCR, NVIDIA, Google, MiniMax, GLM, Zen, go, OR free). Rationalized pool/flow: 6 free providers, subscription is exception not default. zen/go/or pools (16 models) are underused backup capacity. Selection flow: lane -> tier (free first) -> provider (diversity is a feature) -> situational fit. Includes calibration gap list (go-kimi, go-mimo, zen models untested).

## [2026-07-22] ingest | Model selection from the pool: the decision framework
Source: session-2026-07-22-www
Agent: grok
Notes: /www on model-selection strategy. Extends model-pool-not-chain (peers) with a 6-element decision framework (task-novelty, quality-floor, latency, context-fit, cost-regime, quota-strategy) + ordered-filter selection. External: mindstudio, truefoundry, CASTER, SCORE, 2 arxiv surveys. Key: subscription-quota-as-reserve, not budget-to-burn; avoid fail-then-retry cascades on predictable-hard tasks (route directly); monitor cascade escalation rate. Page: concepts/model-selection-from-pool-decision-framework.md

### Corrected (OpenRouter NOT free + selection strategy)
- concepts/model-fleet-provider-pools.md — CORRECTED: OpenRouter go-*/or-* models are NOT free (~.005/1M tokens). Reclassified as exception-only (manual picker). Updated pool tables to remove them from free tier. Added selection strategy: when to use free-fast vs free-slow vs subscription-high-quota. Decision factors ranked (quality floor, cost tier, context fit, latency, volume, quality requirement, provider diversity). Quota arithmetic for MiniMax (16K/mo) and GLM (4.3K/mo). Operator constraint: OpenRouter is manual-exception only.

## [2026-07-22] ingest | DiffusionGemma direct API: reproducible HOW-TO
Source: session-2026-07-22
Agent: grok
Notes: Created because prior DGemma pages asserted "works via direct API" without a recipe - a skeptic correctly flagged this as unsupported. This page provides endpoint, auth, request shape, 3 modes, and a falsification test. Both tests run at creation: smoke 2.0s, batch 1.4s/2 files. Smoke script at P:/tmp/dgemma_smoke.py. Page: concepts/diffusiongemma-direct-api-howto.md

## [2026-07-22] update | DiffusionGemma HOW-TO: 6-skill test found + fixed 2 defects
Source: session-2026-07-22
Agent: grok
Notes: Tested the HOW-TO across 6 real SKILL.md files (4.9-37KB). Found: (1) batch 'name' field used filename stem so all skills showed as 'SKILL' - fixed to use parent dir for generic names; (2) max_file_chars=12000 silently truncated 3/6 skills (tp/go/handoff) - raised to 50000. Re-tested: 6/6 correct names, 0/6 truncated, 7.0s. Script: P:/.data/wiki/scripts/diffusiongemma_read.py. Page updated with receipts.

### Corrected (verified DGemma data + removed unverified claims)
- concepts/model-fleet-provider-pools.md — UPDATED with verified data: DGemma live API tests (867ms-3.7s latency, 5/5 rapid-fire OK), NVIDIA rate limit confirmed ~40 RPM (no daily cap, staff-confirmed), context 262,144 confirmed from NIM docs. Removed fabricated quota arithmetic (was "50 calls/day"; actual is ~170/hr x 5 terminals = ~7% of NVIDIA 40 RPM ceiling). Added [UNMEASURED] labels for Gemini speed/quota and ornith latency. Removed "42x faster" claim (unverified). Added model architecture details (25.2B/3.8B MoE, diffusion block generation, 1100 tok/s spec).

## [2026-07-22] cleanup | Removed meta-narrative anti-pattern from 2 wiki pages
Source: session-2026-07-22
Agent: grok
Notes: Removed author-self-commentary sections that added no operational value to LLMs reading cold. DGemma HOW-TO: removed 'Why this page exists' + 'Why a skeptic was right to doubt' sections, cleaned summary, trimmed 'overclaimed' clause. Model-selection: removed 'What this adds' preamble, stripped 2 conversation-referencing parentheticals. External-reports page verified clean, no edits. Discriminator applied: 'does this tell the reader what to do?'

## [2026-07-22] feat | Dynamic file cap in diffusiongemma_read.py + skill-refactoring handoff
Source: session-2026-07-22
Agent: grok
Notes: (B) Replaced fixed max_file_chars=50000 with dynamic context-derived cap (CONTEXT_CHARS_BUDGET // batch_count). Testing found a latent prompt bug: model non-deterministically stopped at 5/6 summaries. Fixed with count-explicit prompt ("There are EXACTLY N files... ALL N must be covered"). Verified 3/3 runs at 6/6. Also: handoff created for the skill-refactoring program (11 skills >20KB, refactor to /tp-pattern one at a time). Handoff: P:/docs/handoffs/skill-refactoring-program-20260722/HANDOFF.md

### Added (verified model test results)
- concepts/dgemma-gemini-flash-operational-tests-2026-07-22.md — formal test of DGemma + Gemini 3.5 Flash-Lite across 6 task types. Both pass quality floor (7/7 code gen, 3/3 code review, valid JSON, 1.0 extraction recall). Gemini 4x faster (p50=918ms vs 3913ms) and 4x more consistent (p90/p50=1.09x vs 2.6x). DGemma empty-content root cause verified: 256-token diffusion blocks require max_tokens >= 256 (fixed via max_completion_tokens=8192). Full raw results at P:/tmp/model-test-results.json. Test bug disclosed (wrong prompt for handoff answer key, corrected, both scored 1.0 on re-run).

### Added (verified Gemini/Gemma quota and rate limits)
- concepts/gemini-gemma-quota-rate-limits-2026-07-22.md — official Google docs (scraped 2026-07-22): all Flash/Flash-Lite/Pro models confirmed FREE on Free Tier (free input + output). Rate limits per-project (not per-key): ~15 RPM, ~1,500 RPD for Flash-Lite (practitioner-reported; verify in AI Studio). ~50 RPD for Pro (explains our "limit: 0" errors). RPD resets midnight Pacific. agy uses separate subscription quota pool — independent from direct API. NVIDIA DGemma has separate quota (~40 RPM, no daily cap). Fleet usage ~1,360 calls/day = ~91% of Flash-Lite RPD — tight but workable.

### Added (verified billing tiers + actual rate limits from operator dashboard)
- concepts/gemini-billing-tiers-actual-rate-limits-2026-07-22.md — SUPERSEDES the practitioner-estimated limits from the earlier concept. Verified from operator's AI Studio dashboard: both API keys are Free tier (Google One AI Pro subscription does NOT upgrade API project tier). Actual limits: Gemma 4 31B = 14,400 RPD / 30 RPM (best free model by far); Flash-Lite = 500 RPD / 15 RPM; Flash = 20 RPD / 5 RPM; Pro = 0/0. Enabling billing moves ALL models to per-token pricing ( min prepay, stops at ). Cannot have billing and free pricing on same project. Strategy: stay free; Gemma 4 31B as Code lane primary (28x more RPD than Flash-Lite), DGemma (NVIDIA, no daily cap) as overflow.

### Added (agy vs direct API strategy)
- concepts/agy-vs-direct-api-complementary-value.md — answers "maybe we get more value by just using agy?" No: agy (1,500 req/day, Pro sub, agent harness, burns quota faster due to autonomous internal calls) and direct API (14,400 RPD on Gemma 4 alone, raw inference, separate quota pool) serve different purposes. API for mechanical/pool dispatch; agy for harness-heavy work (tools, repo map, Pro model access, second opinions). "Just use agy" trap: would exhaust in ~1hr of fleet work, lose NVIDIA/local models, lose parallelism. Practitioner evidence: Reddit users confirm agy burns quota 5-10x faster than API calls.

### Added (Gemma operationalization guide)
- concepts/operationalizing-gemma-models-2026-07-22.md — practical guide for maximizing value from Gemma 4 31B (Google API: 14,400 RPD, 16K TPM binding constraint, 131K context) and DiffusionGemma 26B (NVIDIA API: no daily cap, 40 RPM, 262K context). Includes: Google's official sampling params (temp=1.0, top_p=0.95, top_k=64), thinking mode via <|think|>, DGemma's 256-token block requirement (max_completion_tokens=8192 fix), TPM pacing strategy (3s for small, 30s for large), verified quality results for all 3 models, when-to-use-which decision table, and remaining test gaps. Combines official docs + our live test data.

### Updated (delegation gate added to fleet pools)
- concepts/model-fleet-provider-pools.md — added "Delegation gate" section adapted from cost-aware-delegation skill. Five-condition hard gate (mechanical, verifiable, bounded, nameable success criteria, savings > overhead), keep-with-parent list, good delegation targets, cost test ("if packet > task, too small to delegate"), delegation packet structure (8 fields), parent verification checklist. Source cited as cost-aware-delegation skill; Codex-specific details (PI worker, LM Studio) excluded; principles mapped to our pool model.

## [2026-07-22] docs | Session-close accounting rule + shipped-work consolidation handoff
Source: session-2026-07-22
Agent: grok
Notes: (1) New rule in P:/AGENTS.md: Session-close accounting + handoff completeness - requires ACCOUNTING block + handoff check before declaring done. Triggered by operator asking 'are you sure there's nothing left open?' when 6 handoffs + 8 shipped items were undocumented. (2) Consolidation handoff: session-2026-07-22-shipped-work captures the .agents/ move, dynamic cap, count-explicit prompt, _display_name fix, model-selection framework, Re-observe-on-rejection rule, meta-narrative cleanup, and commit-hygiene lesson - none of which were in the session's 6 planning handoffs.

## [2026-07-22] ingest | Session close-out skill design: improvements + multi-terminal invariants
Source: session-2026-07-22-www
Agent: grok
Notes: /www on /close skill improvements. 6 external-sourced patterns (Hermes handoff fields, Cognizant idempotency/validation-gates/decision-lock, digitalapplied loop cap, dev.to restart-survival) + 5 host-mandatory multi-terminal/stale-data invariants. Applied to /close skill (Hard constraints section + Steps 0/1/6/7). Page: concepts/session-close-out-skill-design.md

## [2026-07-22] docs | Handoff: /tp model pool (stop degrading to inline on rate-limit)
Source: session-2026-07-22
Agent: grok
Notes: /tp currently spawns fresh subagent with model omitted -> inherits parent -> if parent 429s, falls to inline (same-lens). Happened ~5x this session. Handoff scopes the fix: try a pool of spawn_subagent-compatible models (parent, ccr-ornith, go-mimo-v2-5, + Reasoning-lane probes) before inline fallback. Applies model-pool-not-chain to /tp. Critical constraint: pool must be spawn_subagent-compatible subset (dgemma/deepseek/qwen/mistral excluded per tool-fallbacks). Handoff: tp-model-pool-not-inline-fallback-20260722

## [2026-07-22] feat | /tp model pool + /close test suite + correctness fixes
Source: session-2026-07-22
Agent: grok
Notes: Actioned /tp critique findings on /close (all value-adding ones). (1) /tp Step 2 rewritten to try spawn_subagent model pool [nemotron, ornith, glm, mimo, parent] before inline fallback - verified via 4-model probe (all passed). (2) /close: removed undefined new_finding_from_check flag, added decision-lock contradiction-break rule, replaced fuzzy discoverable-from check, added 10-test suite (all pass), added auto-resolve for clean sessions, extended restart-survival spot-check to close-state.md. tool-fallbacks.md updated with probe data. Handoff tp-model-pool-not-inline-fallback-20260722 closed.

## [2026-07-22] ingest | Model tool-calling capability matrix
Source: session-2026-07-22-www
Agent: grok
Notes: /www on which models support agentic tool use. Key finding: most host-pool models DO support tool calling; dgemma is the exception (thinking-mode conflict with framework parser, NOT missing capability - Google ships function calling for Gemma 4). Failure is transport-specific (spawn_subagent/headless --tools fail; direct API works). Adds 7th element to model-selection framework: tool-call requirement. Nemotron paradox: high leaderboard scores but serialization-fails on real tool tasks on this host. Page: concepts/model-tool-calling-capability-matrix.md

## [2026-07-22] docs | Two root-cause handoffs: test-code drift + API guessing
Source: session-2026-07-22
Agent: grok
Notes: (1) test-code-drift-multi-agent-20260722: /close scanner went 4 versions with zero test coverage because concurrent sessions didn't update tests. Fix: coverage gate (pytest --cov-fail-under=80). (2) api-guessing-without-verification-20260722: agent wrote 24 tests against inferred API (8 failed) because grep function-names felt like a contract. Fix: read signatures before writing; test runner already catches wrong guesses. Both are instances of plausible-narratives-substitute-for-verification.

## [2026-07-22] docs | Handoff: skill location audit + optimization review
Source: session-2026-07-22
Agent: grok
Notes: Audit all 38 non-bundled skills across 4 scope locations (user/project/bundled/.agents) for optimal placement per .agents/ open standard + user-scope convention, plus optimization review (size, tests, portability, stale refs, convention compliance). 3 tasks: location audit (per-skill disposition), optimization review, disposition table. Specific questions: /check at project scope (missed by consolidation?), check-work deprecated (retire?), code-review vs review (duplicate?), .agents/ skills (cross-host or misplaced?). Connects to skill-refactoring-program and test-code-drift handoffs.

## [2026-07-22] docs | Handoff: /close v6 deferred design findings
Source: session-2026-07-22
Agent: grok
Notes: /tp critique of /close v6 (glm-5-2, 9 tool calls) found 9 issues. Items 1-4 (broken tests, stale gate count, wrong --no-loop row, untested functions) being fixed by concurrent session. Items 5-9 (quota gate overhead, session_observations false-positive rate, dead backslash regex, decisions-gate-invalidates-wiki-gate, no pruning mechanism) deferred to handoff for design evaluation. 5 findings, each with decision needed + possible fix + priority.

## [2026-07-22] docs | Handoff: /close scanner architecture + root-cause chain (5 levels)
Source: session-2026-07-22
Agent: grok
Notes: 5-level root-cause analysis of the /close gate resolution failure (LLM said "noting" instead of acting). Level 1: symptoms (RC1-RC5). Level 2: mechanisms. Level 3: common pattern (agents solve immediate problems without system understanding). Level 4: Observe-Before-Propose scope too narrow (fires on structure, not infrastructure). Level 5: LLM optimizes output production over system understanding. Plus non-regex alternatives for scanner (YAML frontmatter parsing vs regex scraping). 7 tasks with dependency order. Task 1 (verify qmd) blocks everything.

## [2026-07-22] ingest | Grok per-hook disable layer — silent suppression of plugin hooks
Source: session-2026-07-22 (via /www)
Agent: grok

## [2026-07-22] ingest | Hook failure mode taxonomy — general, Grok-specific, exec-gate-specific
Source: session-2026-07-22 (via /www)
Agent: grok

## [2026-07-22] ingest | Read-only vs mutating command classification — three solutions for exec-gate friction
Source: session-2026-07-22 (via /www)
Agent: grok

## [2026-07-22] ingest | Exec-gate plugin design rationale and reusable logic (retired)
Source: session-2026-07-22
Agent: grok

## [2026-07-22] ingest | LLM defensiveness under user pushback — skill-level fixes don't work, structural ones do
Source: session-2026-07-22 (via /www)
Agent: grok


## 2026-07-23 — problem-first-systems-decomposition

- **Page:** wiki/concepts/problem-first-systems-decomposition.md
- **Why:** user asked what mental model prevents optimization-without-understanding in LLM agents


## [2026-07-22] ingest | Challenge-triggered verification — actual implementations people are using
Source: session-2026-07-22 (via /www)
Agent: grok

## 2026-07-24
- **Example Domain** (P:\.data\wiki\sources\example.com\000-.md)
  - URL: https://example.com
  - SHA256: fea0da776d1c2e68dfd88bab21228628968e567f744b4b228ed32ac0b3b7e729
  - Source: crawl-ingest (ingested)

## 2026-07-25
- **UditAkhourii/adhd** (P:\.data\wiki\sources\github.com\000-UditAkhourii-adhd.md)
  - URL: https://github.com/UditAkhourii/adhd
  - SHA256: 1a3d51bb130ee804ff3c1d91e39ed68ccb29efafcd72b9f60ba6e859c9c992cf
  - Source: crawl-ingest (ingested)
130ee804ff3c1d91e39ed68ccb29efafcd72b9f60ba6e859c9c992cf
  - Source: crawl-ingest (ingested)
d)

## 2026-08-01
- **coleam00/cole-medin-knowledge-base** (P:\.data\wiki\sources\github.com\000-coleam00-cole-medin-knowledge-base.md)
  - URL: https://github.com/coleam00/cole-medin-knowledge-base
  - SHA256: ba3617c25433c98f925f8033dd40b61546122f062b585a77d5ace5a907839f21
  - Source: crawl-ingest (ingested)

## 2026-08-01
- **knowledge-catalog/okf at main · GoogleCloudPlatform/knowledge-catalog · GitHub** (P:\.data\wiki\sources\github.com\000-GoogleCloudPlatform-knowledge-catalog-tree-main-ok.md)
  - URL: https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf
  - SHA256: 2c7bd0b0023e6c3d20590ef3b64fc9895d2ca9bb4754394addebff3ed65bd84a
  - Source: crawl-ingest (ingested)
(ingested)
