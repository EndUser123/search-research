---
title: "I'm trying to sign up for nvidia developer, but I get this sms problem.  why?"
date: "2026-03-18"
mode: "COPILOT"
uuid: "dd3201ea-6dff-4dec-a9d8-d84eb1a87289"
entry_count: 2
---

## Human

I'm trying to sign up for nvidia developer, but I get this sms problem.  why?

## Assistant

**The "This phone number has exceeded limits" error during NVIDIA NIM (build.nvidia.com) phone verification is a widespread system issue, affecting even first-time attempts across regions including Canada (+1 403 numbers).**[1][2][3]

**It triggers immediately or after one OTP (often received but rejected by UI), blocking API key generation for unlimited requests and GPU sandboxes.**[4][1]

This matches a surge of identical complaints since mid-March 2026, likely due to backend rate-limiting bugs or anti-abuse false positives amid high NIM demand.[2][5]

## Current Status
Ongoing as of March 18, 2026; some cases (e.g., Canada +1 416) resolved by support, but many persist.[1][2]

Canada is supported (worldwide expansion noted in UI), so not a location block.[6]

## Next Steps
Email help@build.nvidia.com with: registered email, phone(s) tried (+1 403 468 378?), error screenshot, and request manual verification/API key activation.[5]

Many users report 24-48h fixes; include your Calgary, AB location if relevant.[3][4]

Wait 24h before retrying, or test alternate +1 numbers (non-VOIP).[2]

## Human

Alternative ways to get NVIDIA developer API key without SMS

## Assistant

**No official alternatives exist to bypass SMS OTP for NVIDIA NIM API keys on build.nvidia.com; phone verification is mandatory for new accounts to generate keys.**[1][2][3]

**Users universally report the "exceeded limits" error blocks access, with no email, NGC, or other verification options documented.**[4][3][5]

## Workarounds
Contact help@build.nvidia.com requesting manual activation—provide account email, phone (+1 403 468 378?), screenshot; many receive keys in 24-48h.[5][6][1]

Existing NGC Personal API keys (from ngc.nvidia.com/setup/api-key) work for some NIM downloads but require separate phone verification there and lack NIM unlimited quotas.[3][7]

## Limitations
VPNs/carrier switches rarely help; avoid VOIP numbers as they're auto-blocked for fraud.[2][8]

No public beta/self-host bypasses grant free unlimited API/GPU access without verification.[3]

What phone carriers have you tried?
