---
title: "Claude Plugin Marketplace Dashboard"
date: "2026-03-24"
mode: "ASI"
uuid: "df3e3476-2706-404a-bb30-8c40cbad2e85"
entry_count: 1
---

## Human

Build an interactive comparison dashboard for Claude plugin marketplaces including claude-plugins-official, claudemarketplaces.com, claude-plugins.dev, skillsdirectory.org, and ComposioHQ/awesome-claude-skills with plugin counts, ratings, and category filters

## Assistant

The dashboard is live. Here's what's inside:

## Marketplace Coverage

All 5 sources researched and compared:

| Marketplace | Type | Listings | Differentiator |
|---|---|---|---|
| claude-plugins-official[1] | Official | 118 plugins | Anthropic-reviewed, 13 categories, 14.4k stars |
| claudemarketplaces.com[6] | Aggregator | 3,180 | 2,315 skills + 770 MCP servers + 95 marketplace repos |
| claude-plugins.dev[11] | CLI Registry | ~200 | `npx` one-command install, shows per-plugin install counts |
| skillsdirectory.com[3] | Security-First | 9,205 | A/B/C/D/F security grading, 36,109 total scanned |
| ComposioHQ/awesome-claude-skills[5] | Curated List | 147 | 78 SaaS automation skills, 34.5k stars |

Note: skillsdirectory.org doesn't exist — the actual domain is skillsdirectory.com.

## Dashboard Features

- KPI cards with animated counters for total listings, official plugin count, security-scanned skills, and combined GitHub stars
- Sortable marketplace comparison table with type tags and security indicators
- Bar chart (listings by marketplace) and doughnut chart (official plugin category distribution)
- Category Explorer with marketplace and category dropdown filters — shows per-category counts across all 5 sources
- Top Plugins table with search, sorting, pagination, and install counts where available
- Security Grade Distribution panel showing skillsdirectory.com's A–F breakdown (94% Grade A)
- Full light/dark mode with system preference detection
- Methodology section citing all primary data sources
