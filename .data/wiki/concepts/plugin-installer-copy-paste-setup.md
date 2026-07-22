---
title: Plugin Installer Copy-Paste Setup Commands
source: OPTIMAL-SETUP-COPY-PASTE.md
date: 2026-05-10
tags: [claude-code, plugins, setup, copy-paste, deployment, marketplace]
sha256: 5f2ce0dd70f68d8e4dfed86a2255b3e3f7c6ddf1095ca1b2e58a8f471dc20ac7
host: both
---

# Plugin Installer Copy-Paste Setup Commands

## Summary

Quick copy-paste commands for deploying 7 development plugins via the plugin-installer system. A streamlined four-step process: save files, run bash setup, install via Claude Code, verify.

## Key Insights

**Four Steps**: (1) Save audit/setup scripts to marketplace directory. (2) Run bash setup script. (3) Update marketplace and install each plugin via `/plugin install name@local`. (4) Verify with `/plugin list`.

**7 Plugins**: cc-skills-ai-api, cc-skills-ai-cli, cc-skills-media, cc-skills-meta, cc-skills-sdlc, cc-skills-utils, snapshot.

**Skill Invocation**: Use namespaced format: `/cc-skills-ai-api:ai-api [query]`, `/cc-skills-utils:uuid generate`, `/snapshot:track session`.

**Recovery**: Re-run PowerShell auditor with `-AutoFix -DeleteHooks`, re-run bash setup, or validate specific plugins individually.
