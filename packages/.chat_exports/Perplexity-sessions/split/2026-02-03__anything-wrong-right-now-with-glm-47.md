---
title: "anything wrong right now with glm-4.7?"
date: "2026-02-03"
mode: "COPILOT"
uuid: "81d92b28-8aae-4581-a576-a4aa8423dedc"
entry_count: 2
---

## Human

anything wrong right now with glm-4.7?

## Assistant

**No widespread outages reported for GLM-4.7 right now.**[1][2]

Recent status checks show Z.ai's services, including API components, as fully operational with no active incidents. A Z.ai status page confirms no disruptions today.[2][1]

**User-Reported Issues**
- Some developers note ongoing server overloads causing TPS drops, reduced reasoning, and connection problems, especially during peak times or training periods.[1]
- Rate limiting (e.g., 429 errors) and slowness have been mentioned today on Reddit, potentially due to high load.[3]
- Specific variants like GLM-4.7-Flash face local setup bugs (e.g., loops in llama.cpp), but these are resolvable via clean reinstalls.[4]

These appear intermittent rather than systemic failures, common for high-demand AI services. For your Z.ai coding plan, try off-peak hours or alternative providers like Together AI hosting GLM-4.7.[5]

## Human

Solutions for GLM-4.7 server overload and TPS drops

## Assistant

**GLM-4.7 overloads stem from Z.ai server load, rate limits, and high concurrency on the coding plan.**[1][2]

**Immediate Workarounds**
- Switch to GLM-4.6 temporarily, which handles higher concurrency (up to 12 sessions) without throttling.[3][1]
- Implement retries with delays (5+ seconds between requests) and monitor Z.ai status for maintenance.[4]
- Use direct API connections in Claude Code instead of gateways to bypass overloaded proxies.[1][3]

**Long-Term Fixes**
- Run GLM-4.7-Flash locally via vLLM, SGLang, or Transformers with quantization (e.g., INT4/FP8) for 100+ TPS on capable hardware like 8xH100.[5][6]
- Alternate providers like Together AI or Cerebras for hosted inference without Z.ai limits.[7]
- Optimize prompts: Disable thinking mode for simple queries or set budgets (e.g., 2048 tokens) to reduce load.[6]

These steps align with your multi-terminal Claude Code setup—test direct GLM-4.6 switches first for quick gains.[1]
