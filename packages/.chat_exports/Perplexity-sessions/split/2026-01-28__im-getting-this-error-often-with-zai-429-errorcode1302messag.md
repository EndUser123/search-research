---
title: "I'm getting this error often with z.ai:
 429 {'error':{'code':'1302','message':'High concurrency usage of this API, plea"
date: "2026-01-28"
mode: "COPILOT"
uuid: "540d099b-f260-4b3e-af08-f54bce6250c5"
entry_count: 1
---

## Human

I'm getting this error often with z.ai:
 429 {"error":{"code":"1302","message":"High concurrency usage of this API, please
     reduce concurrency or contact customer service to increase
     limits"},"request_id":"2026012811081869430d3797894b26"}

## Assistant

Based on the documentation and community reports, error 1302 on Z.ai is a **concurrency limit violation**, not a rate limit or account issue. Here's what you need to know:

## The Problem

Error 1302 means your Z.ai account has hit its **concurrent request limit**—the maximum number of API requests you can initiate simultaneously. This is different from rate limiting (frequency) and applies to parallel execution, which is critical for agent-based workflows like the multi-terminal setups you run.[1]

## Current Context with Your Setup

Given your usage pattern with 5-6 concurrent Claude Code terminal sessions running Z.ai models, you're likely exceeding Z.ai's concurrency quota for your subscription tier. The Z.ai documentation confirms that different users have different concurrency quotas based on their subscription plan.[2]

Community reports show this is a real issue: users on Pro and MAX plans report encountering 1302 errors even with seemingly minimal concurrent requests, suggesting either the limits are strict or the quota system may have anomalies.[3][4]

## Solutions

**Immediate workarounds:**

1. **Reduce simultaneous requests** — Space out your agent launches or limit concurrent terminals. A user reported success by adding 1-2 second delays between rapid successive calls.[4]

2. **Downgrade some agents to lower-tier models** — Instead of running all subagents on GLM-4.7, use GLM-4.5 or lower for agents that don't require peak performance, reducing overall concurrency pressure.[4]

3. **Check your actual quota** — Visit https://z.ai/manage-apikey/rate-limits to verify your subscription's concurrency limit (note: coding plan limits differ from API balance consumption limits).

**Long-term solution:**

Contact Z.ai customer service to **increase your concurrency limit**—this is explicitly offered in their error documentation. Given your Pro subscription and agent-based workflow, they may accommodate a higher concurrent request quota.[1]

The error is legitimate infrastructure-level throttling, not a bug, so spacing out requests is the most reliable immediate fix while you pursue a limit increase with support.
