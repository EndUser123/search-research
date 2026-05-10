# Vault Log

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
