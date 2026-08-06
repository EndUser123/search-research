---
title: "Grok Build weekly quota: gRPC-web billing endpoint"
created: 2026-08-06
source: session-20260806
tags: [quota, grok-build, grpc-web, billing, protobuf, reverse-engineering, xai]
summary: >
  Grok Build's weekly subscription quota (shared across Chat, Imagine, Voice,
  Build, and API) is queryable via a reverse-engineered gRPC-web endpoint at
  grok.com using the bearer token from ~/.grok/auth.json. No official API
  exists for this; the technique was documented by CodexBar and OmniRoute
  before this workspace adopted it. Returns credit_usage_percent and reset
  timestamp from a protobuf response.
agent: grok
host: grok
cognitive_load: 3
verification: empirically-tested
sources:
  - https://github.com/steipete/CodexBar/blob/main/docs/grok.md (CodexBar, accessed 2026-08-06)
  - https://github.com/diegosouzapw/OmniRoute/issues/6844 (OmniRoute, opened 2026-07-11)
  - https://docs.x.ai/grok/faq (xAI FAQ, accessed 2026-08-06)
  - https://docs.x.ai/developers/rate-limits (xAI API rate limits, accessed 2026-08-06)
relations:
  - target: wiki/concepts/provider-quota-usage-api-reference.md
    type: extends
  - target: wiki/concepts/execution-path-based-model-routing-grok-build.md
    type: complements
  - target: wiki/concepts/model-quota-contention-coordination-fleet-rate-limiting.md
    type: related
---

# Grok Build weekly quota: gRPC-web billing endpoint

## Decision context

The fleet quota dashboard (`fleet_quota.py`) tracks all external providers —
z.ai, MiniMax, OpenCode Go, Google Antigravity, OpenRouter, etc. — but Grok
Build (the host platform) was absent. The operator asked why, and initial
research incorrectly concluded that xAI had no metered quota (confusing the
public API's tier-based RPS/TPM ceilings with the consumer subscription's
weekly metered pool). The operator corrected this: "except that there is a
quota per week."

The real question: **can the weekly pool be queried programmatically** the way
opencode-quota queries z.ai and MiniMax? The answer required distinguishing
three separate xAI quota surfaces and finding the undocumented billing
endpoint that the community (CodexBar, OmniRoute) had already reverse-engineered.

## Three xAI quota surfaces (don't conflate them)

| Surface | What it is | Quota model | Queryable? |
|---|---|---|---|
| **xAI public developer API** (`api.x.ai`) | Pay-per-token API with API keys | Tier-based RPS/TPM ceilings — throughput limits, not metered | Console only (`console.x.ai/rate-limits`) |
| **Grok consumer app** (grok.com, iOS, Android) | Chat, Imagine, Voice | Shared weekly metered pool (percentage-based) | Settings → Usage UI only |
| **Grok Build** (CLI/TUI) | This host platform | Same shared weekly pool as consumer app | **gRPC-web endpoint** (this technique) |

The shared weekly pool (since June 2026) is the key: Grok Build draws from the
**same** metered bucket as Chat, Imagine, and Voice. Burning Grok Imagine
credits in the morning reduces Build quota in the afternoon. The pool is
measured as a percentage used, not token counts.

## The gRPC-web billing endpoint

**Endpoint:** `POST https://grok.com/grok_api_v2.GrokBuildBilling/GetGrokCreditsConfig`

**Authentication:** Bearer token from `~/.grok/auth.json` (the JWT the CLI
stores after `grok login`). Token expires after ~7 days; the CLI refreshes
automatically but `fleet_quota.py` does not — it skips on expiry.

**Request body:** 5 zero bytes (empty gRPC-web frame: 1 byte flags + 4 bytes
BE length = 0).

**Response:** gRPC-web framed protobuf containing:
- **Field 1** (float32 inside embedded message): `credit_usage_percent` —
  the percentage of the weekly pool already consumed
- **Field 5** (nested message → field 1 varint): Unix timestamp of the next
  reset

### Required request headers

- `Content-Type: application/grpc-web+proto`
- `X-Grpc-Web: 1`
- `Authorization: Bearer <token>`
- Browser-like `User-Agent` (Cloudflare blocks default Python urllib)
- **IPv4 forcing** (Cloudflare returns error 1010 on IPv6)

### Protobuf parsing (no protobuf library needed)

The response is small enough to parse manually with `struct.unpack`:

1. Strip 5-byte gRPC-web frame header (flags + BE uint32 length)
2. Walk the top-level protobuf to find field 1 (embedded message)
3. Inside the embedded message, find field 1 (float32 = used %) and
   field 5 (nested message with reset timestamp)

Proto3 omits zero values: an omitted `credit_usage_percent` field means 0%
used (not an error). This is a gotcha for parsers — treat absence as 0%, not
None.

### Alternative: ACP JSON-RPC `x.ai/billing`

`grok agent stdio` exposes an ACP extension method `x.ai/billing` that
returns structured JSON with monthlyLimit, usage, and billing cycle. This is
cleaner than protobuf parsing — but as of grok CLI ~0.1.210, it returns
`-32601 Method not found` on the agent-stdio surface (only wired in the
interactive TUI). When xAI enables it, this becomes the preferred path.

## What this means for our workspace

`check_grok()` in `fleet_quota.py` implements the gRPC-web approach. It runs
alongside the other provider checkers in the unified `quota` dashboard:

```
grok             [weekly]
                 quota  [████████░░] 80% (pool: 20% used)  resets  2h 30m · Thu 08:24
```

The 20% used reflects all Grok products (Chat, Imagine, Voice, Build, API)
drawing from the same pool — not just Build usage. This is correct: the pool
is shared.

### Implementation notes

- **Socket monkey-patch for IPv4:** the current implementation patches
  `socket.getaddrinfo` globally. This is not thread-safe — see SEC-1 in the
  /review findings. Acceptable while `fleet_quota.py` runs single-threaded,
  but needs a lock or custom HTTPS handler if hooks call it concurrently.
- **Email prefix in display:** the dashboard shows the account email prefix
  (e.g., "Grok Build (a.hominidae)") to distinguish accounts if multiple
  OIDC entries exist in auth.json.
- **Token expiry:** expired tokens return a graceful "token expired" message
  rather than sending invalid credentials.

## Prior art

- **CodexBar** (steipete/CodexBar): macOS menu-bar app that was first to
  document both billing sources (gRPC-web + ACP JSON-RPC), the protobuf
  parsing, the IPv4 requirement, and the auth.json structure. Their docs at
  `docs/grok.md` are the canonical reference.
- **OmniRoute** (diegosouzapw/OmniRoute): multi-model router that filed a
  detailed feature request (issue #6844, closed via PR #7714) for Grok Build
  quota tracking, documenting the shared weekly pool model and the
  limitations of static rate-limit plans.

## Falsifier

This technique breaks if:
1. xAI exposes an official billing API endpoint (then switch to it)
2. xAI changes the gRPC-web protobuf schema (field numbers or wire types change)
3. xAI adds the `x.ai/billing` ACP method to the agent-stdio surface (then
   switch to JSON-RPC — cleaner than protobuf parsing)
4. Cloudflare tightens bot detection beyond what browser-like headers can
   bypass (then need actual browser cookies via Chrome CDP)
5. The weekly pool model changes back to per-product daily limits (then the
   percentage-based approach no longer applies)

## Sources

- [CodexBar Grok provider docs](https://github.com/steipete/CodexBar/blob/main/docs/grok.md) (steipete, accessed 2026-08-06) — canonical implementation reference; documents both billing sources, parsing quirks, auth.json structure
- [OmniRoute issue #6844](https://github.com/diegosouzapw/OmniRoute/issues/6844) (steveepreston, 2026-07-11) — detailed feature request with endpoint, protobuf field semantics, IPv4 requirement, acceptance criteria
- [xAI FAQ: Usage & Limits](https://docs.x.ai/grok/faq) (xAI, accessed 2026-08-06) — confirms shared weekly pool model, percentage measurement, per-product breakdown
- [xAI API Rate Limits](https://docs.x.ai/developers/rate-limits) (xAI, accessed 2026-08-06) — the *public API* tier system (distinct from the consumer weekly pool)
