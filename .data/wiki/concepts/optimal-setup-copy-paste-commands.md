---
title: "Optimal Setup Copy-Paste Commands"
status: active
source: ~/Downloads/OPTIMAL-SETUP-COPY-PASTE.md
hash: 5f2ce0dd70f68d8e4dfed86a2255b3e3f7c6ddf1095ca1b2e58a8f471dc20ac7
date: 2026-04-26
category: deployment
tags: [plugins, setup, copy-paste, commands]
host: grok
---

# Optimal Setup Copy-Paste Commands

## Step 1: Save Files

Save these 2 files to `P:\packages\.claude-marketplace\`:
- `plugin-audit-and-fix.ps1`
- `claude-plugin-setup.sh`

## Step 2: Run Bash Setup

```bash
cd P:\packages\.claude-marketplace
chmod +x claude-plugin-setup.sh
./claude-plugin-setup.sh
```

## Step 3: Update Marketplace & Install

```bash
/plugin marketplace update local
/plugin install cc-skills-ai-api@local
/plugin install cc-skills-ai-cli@local
/plugin install cc-skills-media@local
/plugin install cc-skills-meta@local
/plugin install cc-skills-sdlc@local
/plugin install cc-skills-utils@local
/plugin install snapshot@local
/plugin list
```

## Step 4: Verify Success

All 7 plugins should show in `/plugin list` with green checkmarks.

## See Also

- [[optimal-solution-complete-setup]] — complete setup guide
- [[deployment-checklist]] — deployment checklist
