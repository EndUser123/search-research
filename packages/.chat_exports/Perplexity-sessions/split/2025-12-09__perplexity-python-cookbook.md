---
title: "perplexity python cookbook"
date: "2025-12-09"
mode: "COPILOT"
uuid: "d7980f9d-52b0-4756-b558-06ec10de454e"
entry_count: 3
---

## Human

perplexity python cookbook

## Assistant

The Perplexity Python cookbook lives in the official docs and a companion GitHub repo, both with multiple end‑to‑end examples in Python.[1][2]

## Official cookbook (docs)

- Main cookbook index with all examples: https://docs.perplexity.ai/cookbook.[1]
- Each example has its own README and Python code, e.g.:
  - Daily Knowledge Bot (scheduled Python script).[3][4]
  - Disease Information App (browser app backed by Python/Perplexity API).[5]
  - Persistent chat memory with LlamaIndex and Sonar API.[6]
  - Discord bot using discord.py and Sonar.[7]

## GitHub repo with Python projects

- GitHub: https://github.com/ppl-ai/api-cookbook.[2]
- Contains fully working projects; you clone the repo, `cd` into an example, install `requirements.txt`, set `PERPLEXITY_API_KEY`, and run the Python scripts as described in each README.[3][2]

## Python SDK and quickstarts

- Python SDK quickstart: https://docs.perplexity.ai/guides/perplexity-sdk.[8]
- General getting‑started + API key setup: https://docs.perplexity.ai/getting-started/quickstart and https://docs.perplexity.ai/getting-started/overview.[9][10]

If you say what you want to build (CLI tool, research agent, Discord bot, etc.), a specific cookbook pattern can be pointed out or adapted into a minimal Python template.

## Human

Perplexity API cookbook examples for Python projects

## Assistant

Perplexity’s API cookbook includes several ready-to-run Python projects covering CLI tools, bots, and small apps.[1][2]

## Core Python examples

From the official cookbook repo, these examples are designed to be run and customized in Python projects:[2]

- Fact Checker CLI – command-line tool that sends claims or article snippets to the Sonar API and returns verification-style responses.[2]
- Daily Knowledge Bot – scheduled script that calls the API once per day and delivers an interesting fact or insight, suitable for cron or serverless jobs.[2]
- Disease Information App – interactive app that queries medical information via the API and presents user-friendly answers, typically backed by a small Python web stack.[2]
- Financial News Tracker – script/app that pulls finance news and uses the API for analysis and summarization.[2]
- Academic Research Finder – helper that searches literature and summarizes or extracts key points using the API.[2]
- Discord Bot – Discord integration (using discord.py) that forwards channel messages to Sonar and posts responses.[2]

## How these map to Python project patterns

These examples cover several common Python patterns:[1][2]

- CLI utilities: Fact Checker CLI, possibly Academic Research Finder, using `argparse`/`click` plus simple API calls.  
- Background jobs and automations: Daily Knowledge Bot and Financial News Tracker as cron/serverless workers driven by the Perplexity API.[2]
- Web or interactive apps: Disease Information App and some showcase apps that combine a Python backend with a browser UI.[1][2]
- Chat/bot integrations: Discord Bot and similar patterns that connect messaging platforms to Perplexity.

## Where to browse the code

- Cookbook documentation overview (descriptions and setup guidance): https://docs.perplexity.ai/cookbook.[1]
- Full Python implementations and project folders: https://github.com/ppl-ai/api-cookbook (each example has its own directory and README with install/run steps and the environment variable `PPLX_API_KEY`).[2]

If you share what you are building (CLI tool, research assistant, Discord bot, SaaS backend), a minimal Python skeleton inspired by one of these examples can be sketched out.

## Human

what are some popular repos built using the perpelxity api.

## Assistant

Several open source and official repositories showcase popular ways developers are using the Perplexity API.[1][2]

## Official Perplexity repos

- **api-cookbook (Perplexity)** – Canonical collection of real-world examples: Fact Checker CLI, Daily Knowledge Bot, Disease Information App, Financial News Tracker, Academic Research Finder, Discord bot, plus advanced integration guides (memory, multimodal, agents).[1]
- **Perplexity AI org on GitHub** – Organization account listing around a couple dozen public projects, with `api-cookbook` as the flagship API example repo.[2]

## Third‑party API clients and wrappers

- **helallao/perplexity-ai** – Unofficial Python wrapper that automates account handling and exposes a simple `search` interface with sync and async usage.[3]
- **nathanrchn/perplexityai** – Lightweight Python API client intended to call Perplexity programmatically from scripts and apps.[4]
- **sgaunet/perplexity-go** – Go client library implementing a `CreateCompletion` interface around Perplexity’s chat completion endpoint.[5]

## Project roundups and integrations

- **Openalternative “best projects using Perplexity AI” list** – Curated roundup of open source tools that embed Perplexity, including search assistants, browser extensions, and educational tools.[6]
- **Instructor integration example** – Guide and sample code showing how to pair Perplexity Sonar models with the Instructor library for structured JSON outputs.[7]

If you share the stack you care about (Python backend, Discord, browser extensions, etc.), more targeted repos that match that pattern can be highlighted.
