---
title: "Awesome Claude Skills Collections"
date: "2026-01-13"
mode: "COPILOT"
uuid: "03cffb0b-c3f7-40ab-900b-3ddec77abbff"
entry_count: 1
---

## Human

Awesome Claude Skills Collections

## Assistant

“Awesome Claude Skills Collections” usually refers to curated lists of high‑quality Claude Skills repos plus a few standout “production packs” that are worth cloning directly.[1][2][3][4][5]

## Core collections to bookmark

- **Anthropic official Skills** – canonical source of spec, folder structure, SKILL.md patterns, and high‑quality exemplars across creative, document, and dev workflows.[5]
- **Awesome Claude Skills lists (GitHub + articles)** – multiple “awesome‑claude‑skills” repos and writeups that categorize skills by domain (research, coding, media, agents, etc.).[2][6][7][8][1]
- **Community skills aggregators** – repos that explicitly position themselves as “Claude Skills collections” and track both official and community skills with tags and usage notes.[9][10][3]

## Production‑grade dev / agent packs

- **levnikolaevich/claude-code-skills** – opinionated, end‑to‑end dev workflow automation pack (planning → docs → coding → QA → audits) with a lot of patterns you can adapt directly to your own `/qa` and multi‑phase flows.[4][11]
- **Linear / project‑workflow oriented skills** – within that repo and related marketplace entries, there are skills that coordinate epics, stories, execution, refactors, and audits in a way that maps well to your multi‑phase QA + bisect + RCA style.[12][4]

## What to copy for your own skills

- **Use Anthropic’s repo for spec + patterns**: SKILL.md layout, metadata fields, hooks, and how they separate instructions from code and assets.[5]
- **Use “awesome” repos for discovery**: clone or fork skills in categories you care about (testing, subagents, media, research, knowledge mgmt) and mine them for concrete patterns (tool wiring, decision trees, retry strategies).[8][1][2]
- **Use `claude-code-skills` for architecture**: copy its ideas around coordinator vs worker skills, phased workflows, and parallel sub‑skills to tighten your own SANITY/E2E/CHAOS/REPORT orchestration.[4]

If you say what categories you want (e.g., “testing + agents + media”), a tailored mini‑collection with 10–15 must‑install skills can be suggested next.
