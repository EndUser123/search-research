---
title: "Do you think the quota and rates for the three pools is trustworthy?  Please research."
date: "2026-07-23"
mode: "COPILOT"
uuid: "7e6af5d1-7841-43ac-8b6e-6f8ab1910e96"
entry_count: 6
---

## Human

Do you think the quota and rates for the three pools is trustworthy?  Please research.

## Assistant

## Short answer

No — trust the **architecture and mechanics** described in the report, but **not the specific numeric quota tables**. The three-pool separation, the proportional/unified Gemini quota pool in Antigravity, the AI-credit overage toggle, and the "billing wipes the free tier" behavior for the Developer API are all corroborated by Google's own documentation. But the exact RPM/TPM/RPD numbers in the Pool 2 table, and any precise weekly/5-hour caps for Pool 1, are not something Google currently publishes — and the third-party sources the report leans on for those numbers actively contradict each other.

## What checks out against primary sources

The core structural claims are verifiable and accurate:

- **Antigravity's plans page** confirms a single baseline quota that refreshes every five hours until a weekly cap is hit for AI Pro users, with third-party models (Claude/GPT-OSS) on a separate fixed limit due to "severe capacity limitations" — exactly what the report describes.[1]
- Google's own **"Changes to Antigravity Plans" post** confirms the unified, proportional-by-API-price Gemini quota pool replacing separate Flash/Pro limits, and that non-Gemini models remain on an independent fixed pool.[2]
- The **Gemini API free-tier billing trap** (enabling billing removes free-tier limits entirely and starts per-token billing immediately) is confirmed by Google's rate-limits doc's tier-qualification table, which shows Free vs. Tier 1+ as mutually exclusive states rather than additive.[3]
- Model names in the report (Gemini 3.6 Flash, 3.5 Flash-Lite, 3.5 Flash, 3.1 Pro) are real and current — confirmed via Google's own blog announcements from May and July 2026.[4][5][6]
- Community reports of a "5-hour sprint + 7-day baseline lockout" structure for Antigravity align with the report's dual-limiter description, though this is forum corroboration, not an official numeric source.[7][8]

## Where the numbers are not trustworthy

Google's own current rate-limits page for the Gemini Developer API is explicit: **"Rate limits depend on a variety of factors... and can be viewed in Google AI Studio,"** and **"Specified rate limits are not guaranteed and actual capacity may vary"**. Google does not publish a static, universal RPM/TPM/RPD table anymore — it tells you to check your live AI Studio project console instead.[3]

Given that, the report's precise numbers (e.g., "Gemini 3 Flash: 10 RPM / 250,000 TPM / 1,500 RPD") are sourced only from third-party blog aggregators, not from ai.google.dev directly. Those third-party sources disagree with each other substantially:

| Source | Free tier RPM | Free tier RPD | Gemini 2.5 Pro RPD |
|---|---|---|---|
| pecollective.com [9] | Not specified | Up to 1,500 (Flash) | 50 |
| help.apiyi.com [10] | 5–15 | 100–250 | ~100 |
| aifreeapi.com (cited in original report) | Similar to above but with different tier boundaries | — | — |

This is a real, unresolved conflict — not a rounding difference. A Reddit thread from r/Bard on new Gemini API rate limits also shows users actively debating whether the Cloud Console quota page itself is even reliable in real time. Additionally, some model IDs in the report's Pool 2 table (e.g. "gemini-3-flash," "gemini-3.1-flash-lite") don't cleanly match the model naming Google uses in its own current batch-limits table (which lists "Gemini 3.6 Flash," "Gemini 3.1 Flash Lite," no plain "Gemini 3 Flash")  — suggesting some model-ID entries were interpolated or hallucinated by the research tool rather than pulled from a live source.[11][3]

## Practical implication for you

- Trust the **qualitative routing logic** (pool separation, telemetry via `/usage`, credit-overage toggle, billing trap) — it's well-grounded.
- Do **not** hardcode the specific RPM/TPM/RPD numbers from that report into any automation or router config. Have your orchestrator query the **live AI Studio quota page** for Pool 2 and the **agy `/usage`/`/quota` JSON telemetry** for Pool 1 at runtime instead of relying on static published values.[1][3]
- Given your interest in cost-effective multi-agent routing, this is exactly the kind of place where a "verified vs. inferred vs. unknown" register (which the report itself attempted) is the right instinct — but that register should have flagged the Pool 2 numeric table as **unknown/unverifiable**, not "verified," since the primary source explicitly declines to publish it.

## Human

How do I query them?  The goal is to give a LLM guidance on what models to use and how frequently we can use them, to determine what roles we should use them in.

## Assistant

Yes — but you should query them **differently for each pool**, because Google does not expose one authoritative API for all three. For your purpose, the right output is not “exact static quotas,” but a **routing registry** with: pool, model, auth method, current availability, live quota source, reset behavior, and a conservative role assignment. The main constraint is that Google explicitly says Gemini API limits **vary by project/tier/account status and should be viewed in AI Studio**, while Antigravity exposes usage through its own UI and status-line telemetry rather than a public quota API.[1][2]

## What to query

You want a normalized record like this for every candidate model:

- Pool: `antigravity`, `gemini_api_project_X`, `gemini_web`
- Product-facing model name: e.g. `Gemini 3.6 Flash`, `Gemini 3.1 Pro`, `Claude Sonnet`
- Auth path: OAuth/session/API key
- Quota owner: account or project
- Meter source: `/usage` or AI Studio page
- Hard dimensions: RPM, TPM, RPD when published or live-visible
- Soft dimensions: 5-hour pooled limit, weekly pooled limit, preview instability, fallback behavior
- Role tags: `interactive`, `batch`, `cheap-router`, `deep-reasoning`, `review`, `multimodal`
- Confidence: `verified`, `observed`, `inferred`, `unknown`

That structure matches Google's own split: Gemini API limits are **per project, not per key**, with RPM/TPM/RPD and midnight-Pacific RPD reset, while Antigravity quota is a **five-hour refresh plus weekly limit** and is correlated to work done rather than a published token denominator.[2][1]

## Pool 1 query path

For **Antigravity**, query the live client, not docs alone. The plans doc says AI Pro gets a high quota refreshed every five hours until a weekly limit is reached, and that overage behavior depends on the AI Credit Overages setting; docs also point to `/usage` and `/quota` as the quota surfaces.[2]

Use a two-part approach:

1. Manual verification in the client:
- Run `/usage` or `/quota`.
- Record the model groups shown, remaining percentages, and reset times.
- Confirm whether Gemini and third-party models appear as separate pools.

2. Machine capture from the status line:
- Antigravity supports a custom status line command, and the docs expose this as the intended integration point for live session metadata.[2]
- In practice, you should wire a script that snapshots every quota update into JSONL.

A practical script target looks like this:

```bash
# statusline.sh
ts=$(date -Is)
cat > "/tmp/agy-status-${ts//:/-}.json"
```

And in settings, point the status-line command at that script. Your router should then parse snapshots into a registry like:

```json
{
  "pool": "antigravity",
  "captured_at": "2026-07-23T14:44:00-06:00",
  "groups": [
    {
      "name": "gemini",
      "remaining_fraction": 0.62,
      "reset_at": "2026-07-23T18:05:00Z",
      "window_type": "5h_or_weekly"
    },
    {
      "name": "third_party",
      "remaining_fraction": 0.41,
      "reset_at": "2026-07-24T02:00:00Z",
      "window_type": "5h_or_weekly"
    }
  ],
  "credits_overage": "never"
}
```

Use this for **eligibility**, not exact throughput forecasting, because Antigravity's own plan page says quota is correlated with amount of work done and can differ prompt to prompt.[2]

## Pool 2 query path

For the **Gemini Developer API**, the authoritative source is the project's live AI Studio quota page, not static docs. Google explicitly says rate limits depend on tier and other factors, that active limits should be viewed in AI Studio, and that specified rate limits are not guaranteed because actual capacity may vary.[1]

You should collect three things:

1. Static metadata from docs:
- Model families available.
- Whether a model is preview/experimental.
- Tiering rules and reset mechanics.
- Batch-specific limits.

2. Live project quota from AI Studio:
- RPM
- TPM
- RPD
- Any model-specific special meters
- Current usage tier
- Whether billing is disabled or active

3. Runtime telemetry from API responses:
- 429 frequency
- Which model fails first under burst
- Latency percentiles
- Retry success rate

Important rules from Google's docs:
- Limits are applied **per project**, not per API key.[1]
- RPD resets at **midnight Pacific time**.[1]
- Free vs Tier 1+ is tied to whether billing is attached and account spend history; moving from Free to paid tier requires setting up billing in AI Studio.[1]

So your registry row for API models should come from the **UI plus runtime observations**, for example:

```json
{
  "pool": "gemini_api_project_alpha",
  "project_id": "alpha",
  "billing_tier": "free",
  "model": "gemini-3.6-flash",
  "limits": {
    "rpm": 10,
    "tpm": 250000,
    "rpd": 1500
  },
  "reset": {
    "rpd_timezone": "America/Los_Angeles",
    "rpd_resets": "midnight"
  },
  "source": "AI Studio quota page",
  "confidence": "verified_live"
}
```

For automated collection, because Google points you to AI Studio rather than documenting a universal quota API, the safest design is:
- Keep a human-maintained or semi-automated **quota manifest** exported from AI Studio.
- Have your runtime read that manifest.
- Update it daily or whenever the project/tier changes.

## Pool 3 query path

For the **Gemini web/mobile app**, you usually cannot query quota programmatically in a supported way. The relevant behavior is product-level: AI Pro gives higher consumer usage limits, but Antigravity and API quotas are separate products and are documented separately.[2][1]

Treat this pool as:
- Manual/interactive only.
- Measured by observed lockouts, model availability, and feature visibility.
- Suitable for research or one-off deep tasks, but **not** as a deterministic backend routing target.

Your registry should therefore use softer fields:

```json
{
  "pool": "gemini_web",
  "model": "Gemini 3.1 Pro",
  "limit_type": "consumer_compute_window",
  "refresh": "observed_5h_like_window",
  "remaining": "manual_only",
  "automation_supported": false,
  "confidence": "observed"
}
```

That keeps the LLM from over-trusting this pool for background orchestration.

## Recommended schema

Use one canonical file that your orchestration layer reads before dispatch:

```json
{
  "captured_at": "2026-07-23T14:44:00-06:00",
  "models": [
    {
      "id": "ag-gemini-3.6-flash",
      "pool": "antigravity",
      "display_name": "Gemini 3.6 Flash",
      "quota_scope": "shared_gemini_group",
      "availability": "enabled",
      "auth": "google_oauth",
      "limits": {
        "type": "shared_percent_pool",
        "five_hour_remaining": 0.62,
        "weekly_remaining": 0.71
      },
      "roles": ["agentic_coding", "fast_synthesis", "default"],
      "privacy": "medium",
      "confidence": "verified_live"
    },
    {
      "id": "api-gemini-3.6-flash",
      "pool": "gemini_api_project_alpha",
      "display_name": "Gemini 3.6 Flash",
      "quota_scope": "per_project",
      "availability": "enabled",
      "auth": "api_key",
      "limits": {
        "rpm": 10,
        "tpm": 250000,
        "rpd": 1500
      },
      "roles": ["batch", "structured_extraction", "cheap_parallel"],
      "privacy": "depends_on_terms",
      "confidence": "verified_live"
    }
  ]
}
```

This is what your planner LLM should consume, not raw docs.

## Routing logic

Use a two-stage decision:

1. **Role fit**
- Deep interactive coding agent: Antigravity Gemini group.
- Cheap parallel extraction/classification: Gemini API Flash-family model.
- Independent critique or final review: Antigravity third-party pool.
- Consumer Deep Research/manual exploration: Gemini web.

2. **Quota fit**
- If API model is below a safety floor, e.g. <20% daily or repeated 429s, reroute to another API model or defer.
- If Antigravity five-hour pool is low, reserve it for high-value tasks only.
- If only web remains, require manual dispatch.

That logic is grounded in the fact that API quotas are project-based numeric rate limits, while Antigravity quotas are work-correlated and pooled over five-hour and weekly windows.[1][2]

## Concrete implementation

A minimal practical system:

- `quota_registry.json`: human/semi-automated truth source.
- `collect_antigravity.ps1` or `.sh`: parses status-line quota payloads into normalized JSON.
- `collect_api_limits.md`: a checklist for copying AI Studio quota values into the registry.
- `route.ts`: selects model by role, privacy class, and remaining quota.

Example TypeScript selector:

```ts
type Role =
  | "default"
  | "agentic_coding"
  | "structured_extraction"
  | "batch"
  | "deep_reasoning"
  | "final_review";

type ModelRecord = {
  id: string;
  pool: string;
  roles: Role[];
  availability: "enabled" | "disabled";
  confidence: "verified_live" | "observed" | "inferred";
  limits?: {
    rpm?: number;
    tpm?: number;
    rpd?: number;
    five_hour_remaining?: number;
    weekly_remaining?: number;
  };
};

export function pickModel(models: ModelRecord[], role: Role): ModelRecord | null {
  const eligible = models.filter(
    m =>
      m.availability === "enabled" &&
      m.roles.includes(role) &&
      (
        (m.limits?.five_hour_remaining ?? 1) > 0.2 &&
        (m.limits?.weekly_remaining ?? 1) > 0.2 &&
        (m.limits?.rpd ?? 1) > 50
      )
  );

  const ranked = eligible.sort((a, b) => {
    const aScore =
      (a.confidence === "verified_live" ? 3 : a.confidence === "observed" ? 2 : 1) +
      ((a.limits?.five_hour_remaining ?? 0.5) * 2) +
      ((a.limits?.weekly_remaining ?? 0.5) * 2) +
      Math.min((a.limits?.rpm ?? 10) / 10, 3);

    const bScore =
      (b.confidence === "verified_live" ? 3 : b.confidence === "observed" ? 2 : 1) +
      ((b.limits?.five_hour_remaining ?? 0.5) * 2) +
      ((b.limits?.weekly_remaining ?? 0.5) * 2) +
      Math.min((b.limits?.rpm ?? 10) / 10, 3);

    return bScore - aScore;
  });

  return ranked[0] ?? null;
}
```

## Guidance to give the LLM

Tell the planner model something like this:

- Treat `quota_registry.json` as the source of truth.
- Prefer records with `confidence = verified_live`.
- Never invent RPM/TPM/RPD for Antigravity.
- For API pools, assume limits are **per project, not per API key**.[1]
- Assume daily API quotas reset at **midnight Pacific**.[1]
- Treat Antigravity usage as **shared pooled work budget**, not message count.[2]
- Do not route confidential data to a pool unless the privacy policy for that pool has been explicitly classified in the registry.
- If no eligible model has enough headroom, return `NEEDS_MANUAL_OVERRIDE` rather than guessing.

## Best next step

Build a **single live quota registry** first, not a full router. Start with:
- one Antigravity collector,
- one manually maintained AI Studio quota snapshot,
- one role taxonomy,
- one selector function.

Then test it on 20–30 real tasks and measure: chosen model, fallback invoked, quota drain, latency, and failure rate. That will give you an evidence-based role map instead of a static model chart.

## Human

Why can't you simply tell me what my expected quota is for each pool for the models?

## Assistant

I can’t simply tell you “your quota is X requests/tokens per model per pool” because Google deliberately **does not publish stable, account‑specific numbers** for all three pools, and the numbers that do exist are **tier‑dependent, region‑dependent, and sometimes in flux**. Instead, Google explicitly tells you to check **your live quota UI** for each pool, and external sources conflict enough that any static table I gave you would be guesswork.

Here’s the breakdown by pool.

## Gemini Developer API (AI Studio) pool

For the **Developer API**, the official rate‑limits doc states:

> “Rate limits depend on a variety of factors (such as your usage tier) and can be viewed in Google AI Studio. As your tier and account status change, your rate limits may change as well.”[1]

Key implications:

- There is **no one set of public RPM/TPM/RPD numbers** that applies to all accounts or projects.
- Limits depend on:
  - Usage tier (Free vs paid tiers; preview vs standard models).[2][1]
  - Whether billing is enabled, and possibly region/account trust.[3][2]
- The **authoritative source** for your project is:
  - The AI Studio “Rate limits” page for that specific project.[4][1]

Third‑party guides (APIYI, Datastudios, etc.) show example free‑tier values (e.g. “Gemini 2.5 Flash: ~10 RPM, ~250 RPD; Flash‑Lite: ~15 RPM, ~1,000 RPD; Pro: ~5 RPM, ~100–250 RPD”) but they explicitly present these as approximate and note that Google has **recently cut quotas and varies limits by tier**. Those numbers:[5][2][3]

- Are **not guaranteed** for your project.
- Sometimes contradict each other and older docs (e.g., RPD ranging from 20 to 250 for similar models).[5][2][3]
- Were measured at specific times and may have changed.

So if I told you “you get exactly 10 RPM and 250 RPD for Gemini 2.5 Flash,” that would be **speculation** for your project, and likely wrong the next time Google adjusts quotas.

## Antigravity / agy pool

For **Antigravity**, the official plans doc states for AI Pro:

- “Users on Google AI Pro receive: High, generous quota, refreshed every five hours until weekly limit reached; Higher weekly rate limit.”[6]
- All plans receive a baseline use of Gemini models, with the multi‑plan split (Free / Pro / Ultra) controlling how generous the quota is.[7][6]

Separately, forum posts show:

- Google has adjusted Antigravity quotas, with some AI Pro users seeing **multi‑day lockouts** instead of the advertised 5‑hour refresh, due to weekly caps overriding the 5‑hour window.[8][9][10]
- Weekly caps are enforced “for all models” and can preempt the shorter window.[10]

But Google does **not** publish:

- A numeric “you get N tokens per five‑hour window” denominator.
- Exact token‑per‑week values.
- Per‑model caps inside the Gemini pool.

The only official guidance is qualitative: “high, generous quota,” “refreshed every five hours until weekly limit reached,” “higher weekly rate limit,” and “quotas that refresh every five hours” for Pro/Ultra, with weekly caps to preserve fairness. That’s enough to say:[6][10][7]

- You have a pooled Gemini quota (Flash + Pro) with:
  - A **rolling five‑hour compute window**, and
  - A **hard weekly limit** that can override five‑hour refresh.[8][10][6]
- But **not enough to translate that into precise tokens or requests** per model.

Because Google explicitly doesn’t expose a denominator (and seems to be tuning it behind the scenes), I cannot give you “Gemini 3.6 Flash in Antigravity = X tokens per week” as a factual number.

## Gemini web/mobile (consumer apps) pool

For the **Gemini apps** (web/mobile), Google’s support page says:

- AI Plus: “2× higher than standard limits.”
- AI Pro: “4× higher than standard limits.”
- AI Ultra: “5× or 20× higher than AI Pro limits depending on subscription.”[11]

It also says:

- Limits are now **compute‑based**: prompt complexity, features used (Deep Research, image/video), and chat length affect usage, rather than simple fixed counts.[12]
- You should view your usage limits in the product:
  - “To view your usage limits: Visit gemini.google.com → Settings → Usage limits.”.[11]

Earlier articles and support docs have cited specific **daily prompt counts** (e.g., free users get 5 Pro prompts per day; AI Pro gets ~100 Pro prompts and higher Deep Research and image caps), but:[13][14]

- These have already changed at least once, as Google moved from pure prompt counts to compute‑based limits.[14][12]
- They’re clearly **plan‑ and time‑specific**, not a hard standard across all times and accounts.

Again, if I told you “as AI Pro you get exactly 100 Pro prompts and 1,500 Thinking prompts per day,” I’d be quoting an **older prompt‑count snapshot** that Google has updated and layered with a compute system, not necessarily what you have right now in July 2026.[12][14]

## Summary of why I can’t give you static numbers

Fact:

- Google’s own docs say **Gemini API rate limits vary by usage tier and account status and must be viewed in AI Studio**; they explicitly warn that specified limits are **not guaranteed**.[1]
- Antigravity’s docs describe **relative generosity and refresh behavior** (5‑hour window + weekly cap) but **do not publish numeric denominators**.[7][6]
- Gemini apps limits are expressed as **multipliers over standard limits** plus a compute model, and you are instructed to view the current numbers in the app’s Usage Limits UI.[11][12]
- Public secondary sources (blogs, forums) show:
  - Substantial **changes over time** (quota cuts of 50–90% for free tier, altered Pro prompt caps).[15][14][5]
  - **Conflicting values** for the same model/tier (RPD and RPM ranges).[2][3][5]

Consensus:

- The only reliable way to know **your** quota for **your** account, region, and project is to query:
  - Antigravity’s `/usage`/`/quota` and status‑line telemetry.
  - AI Studio’s rate‑limit page for each project.
  - Gemini web’s Settings → Usage limits UI.

Speculation (low confidence):

- I could interpolate “typical” free‑tier or Pro values from third‑party tables (e.g., Flash around 10 RPM/250 RPD, Flash‑Lite 15 RPM/1000 RPD, Pro 5 RPM/100–250 RPD; consumer Pro prompts in the ~100 range).[13][14][3][2]
- But these are **approximate, time‑bound, and not guaranteed** for your specific account.

Given your decision standard (no guessing, distinguish fact/consensus/speculation), I would rather say: **we don’t have the data to give your exact per‑model quotas in each pool.** We only have:

- Qualitative behaviors (pools are separate, Antigravity has 5‑hour + weekly compute limits, AI Pro has 4× standard app limits).[6][12][7][11]
- Live UIs that show **current numeric limits** for your specific account, which you can capture and feed to your router.

The right move is to:

- Treat official docs and UIs as **the source of truth**, and
- Build your system around **live, account‑specific readings** rather than static published numbers that may be wrong for your tier or change silently.

Would it be useful if I sketched an explicit “measurement checklist” you can run once per pool (Antigravity, API, web) to extract your current quotas and normalize them into a registry for your LLM?

## Human

Are you deliberately being difficult?  do you think I want an answer to two decimal places?  What can you say and with what confidence?

## Assistant

No, I’m not trying to be difficult. I’m trying to stay inside “evidence‑grounded” instead of giving you a neat looking but fundamentally made‑up quota chart.

You absolutely don’t need two‑decimal‑place precision; what you need is **ballpark guidance with clearly labeled confidence** per pool, per model family. Here’s what I can say, and how sure I am about each claim.

***

## Confidence bands

Let’s use your taxonomy explicitly:

- **FACT (high confidence, backed by primary sources)** – official docs/help pages/product UIs.
- **CONSENSUS (medium confidence)** – multiple independent secondary sources that broadly agree, consistent with docs.
- **SPECULATION (low confidence)** – interpolations, extrapolations, or clearly conflicting sources.

***

## Pool 2 – Gemini Developer API (AI Studio)

### What is solid FACT

- Rate limits are enforced **per project**, not per API key. Multiple keys in one project share the same quota.[1][2]
- Limits are model‑ and tier‑specific, with dimensions like **RPM (requests/minute), TPM (tokens/minute), RPD (requests/day)**.[2][1]
- **RPD resets at midnight Pacific Time**, i.e. per calendar day in PT, not rolling.[1][2]
- **Your actual limits depend on your usage tier and account status**, and may change; Google explicitly states you should **view them in Google AI Studio** rather than rely on static docs.[1]
- Enabling **billing on a project moves it out of pure free‑tier limits** into paid tiers with different quotas and per‑token billing.[2][1]

**Confidence: FACT.** This is exactly what the official Gemini API docs and tier guides say.[2][1]

### Reasonable CONSENSUS ballpark for free tier

Across several third‑party, 2026‑dated sources that all describe the current free tier:

- Flash‑family models (Gemini 2.5 Flash, 3.x Flash):
  - RPM roughly **5–15**.
  - RPD roughly **100–1,500**, depending on model and tier.[3][4][2]
- Pro‑family models (Gemini 2.5 Pro / “Pro Series”):
  - RPM roughly **5–10**.
  - RPD roughly **50–250** (often lower than Flash).[3][2]

They also consistently report that:

- Google has **cut free quotas** substantially vs earlier marketing, sometimes by 50–90%.[4][5]
- Limits can differ **between projects** based on tier, age, and usage.[2]

So if you ask “order‑of‑magnitude free‑tier expectations,” I can say with **CONSENSUS‑level confidence**:

> For a typical non‑billed AI Studio project on the current free tier, you should expect **single‑digit to low‑double‑digit RPM**, and **tens to low‑hundreds of RPD**, with Flash getting more daily calls than Pro‑series models.[4][3][2]

That’s intentionally a **band**, not a precise number.

### Where it becomes SPECULATION

Anything like:

- “You have exactly 10 RPM and 250 RPD for Gemini 3.6 Flash in your project.”
- “Canada free tier projects always get 1,500 RPD for Flash.”

would be **SPECULATION** because:

- Google’s own docs explicitly say limits vary by tier and account and must be viewed in AI Studio.[1]
- Users are reporting very different values for “free” or “trial” projects even within the same timeframe.[5][3][4][2]

***

## Pool 1 – Antigravity / agy (Google AI Pro)

### What is solid FACT

From Antigravity’s official plans and Google’s own Antigravity announcements:

- AI Pro subscribers get **“high, generous quota, refreshed every five hours until weekly limit reached; higher weekly rate limit”** compared to free users.[6][7]
- Quota is enforced via **two windows**:
  - A **rolling 5‑hour window** that “refreshes every five hours” in the sense of capacity sliding out.
  - A **weekly limit** that, once hit, overrides the 5‑hour refresh and causes multi‑day lockouts until the weekly window resets.[7][8][9][6]
- Documentation and community threads consistently say **Gemini models share a pooled budget**, and **third‑party models (Claude, GPT‑OSS) are on separate, tighter fixed limits** due to capacity/cost constraints.[8][9][10][6]

**Confidence: FACT** on “5h + weekly dual limiter” and “pooled Gemini vs separate third‑party pool” for AI Pro Antigravity.[9][10][6][7][8]

### What is reasonable CONSENSUS

From multiple user threads and product posts:

- AI Pro users **rarely hit limits in casual use**; intensive agentic coding or long auto‑loops can hit 5‑hour caps quickly and bump against weekly caps sooner than expected.[8][9]
- Weekly caps on the third‑party pool (Claude/GPT‑OSS) can be **much stricter**, triggering **multi‑day lockouts** despite Antigravity marketing still saying “refreshed every five hours.”[10][8]

So with **CONSENSUS** level confidence:

> For your Antigravity AI Pro Gemini pool, think in terms of “a substantial but opaque shared compute budget over 5 hours, with a larger weekly budget behind it, and a separate, much smaller weekly+5h budget for Claude/GPT‑OSS.”[6][7][9][10][8]

We know the **shape** of the curves, not the denominators.

### Where it’s SPECULATION

- “Gemini 3.6 Flash in Antigravity gives you N tokens per week.”
- “Claude Sonnet has a weekly limit of exactly X calls.”

Those are **not published anywhere**, and community threads show people being surprised by hitting caps earlier than expected, which implies ongoing internal tuning.[9][10][8]

***

## Pool 3 – Gemini web/mobile (consumer apps, AI Pro)

### What is solid FACT

From Google’s own help and news:

- AI Pro is **“4× higher than standard limits”** for Gemini apps; AI Plus is 2×, AI Ultra is 5× or 20× higher depending on subscription.[11]
- Limits are now **compute‑based**, weighting:
  - Model used (Pro vs Flash vs “thinking” variants),
  - Prompt/context length,
  - Features like Deep Research, images, audio/video.[12]
- Earlier explicit daily prompt caps (e.g. “100 daily Pro prompts,” “1,500 Thinking prompts”) have been **adjusted upward** overall but wrapped in this compute system.[13][12]
- You can view your current usage state and limits via **Gemini → Settings → Usage limits**; the UI is the intended source for your specific account.[11][12]

**Confidence: FACT** on “Pro has 4× standard limits, compute‑based, check usage limits in settings.”[12][13][11]

### Reasonable CONSENSUS ballpark

From public announcements around 2025–early 2026:

- Standard/free users had **single‑digit to low‑tens daily Pro prompts** and very few Deep Research calls.[14][13]
- Pro moved that into roughly **low‑hundreds of daily Pro / Thinking prompts** and more Deep Research allowance, before compute weighting.[13][12]
- With 4× multiplier, Pro is clearly “you can work all day interactively without hitting a wall, unless you hammer Deep Research or long Thinking conversations.”

So with **CONSENSUS** level confidence:

> As AI Pro, you can treat Gemini web/mobile as having **enough premium compute for sustained daily interactive use**, with rare hard caps unless you’re doing heavy Deep Research or very long “thinking” chats.[11][12][13]

Again, that’s a qualitative band, not a daily integer.

### Where it’s SPECULATION

- “You currently have exactly 100 Pro prompts and 1,500 Thinking prompts per day.”
- “Your Deep Research cap is exactly N calls/day in July 2026.”

Those numbers have already changed over time, and Google now wraps them behind compute‑based limits and encourages you to view them in the app.[12][13][11]

***

## Direct answer to your frustration

You’re right to push: you don’t want two‑decimal‑place precision; you want actionable guidance. So:

- **I can say:**
  - Developer API free‑tier is roughly “small RPM and RPD per project” – expect single‑digit/low‑double‑digit RPM and tens to low‑hundreds of RPD for Flash; Pro gets fewer RPD. (CONSENSUS)[3][4][2]
  - Antigravity AI Pro gives you a **high pooled Gemini budget over 5h + weekly**, and a **smaller, stricter weekly+5h budget for Claude/GPT‑OSS**. (FACT + CONSENSUS)[7][10][6][8][9]
  - Gemini apps AI Pro gives you **4× standard limits and enough compute for heavy daily use**, gated by compute weighting; hard caps mostly show up under Deep Research or long “thinking” sessions. (FACT + CONSENSUS)[13][11][12]

- **I will not say:**
  - “Your Antigravity Gemini pool is exactly X tokens/week.”
  - “Your AI Studio free tier for project Y is exactly 10 RPM and 250 RPD.”
  - “Your AI Pro app tier is exactly N prompts/day.”
  
  because those would cross from **CONSENSUS bands** into **false precision**, and your own usage tiers and project state may differ.

Given your goal (guide an LLM on **what models to use and how frequently**), the right abstraction is:

- Treat each pool/model family as “small/medium/large budget” and “cheap/expensive per call,” with bands like:
  - API Flash: “cheap, small per‑project budget.”
  - API Pro: “expensive, very small per‑project budget.”
  - Antigravity Gemini: “expensive, medium pooled budget, bounded by weekly caps.”
  - Antigravity Claude/GPT‑OSS: “expensive, small budget.”
  - Gemini web AI Pro: “large interactive budget with compute weighting.”
- And then refine those bands using **your own measured quotas from UIs**.

If you want, I can propose explicit labels like `budget_small`, `budget_medium`, `budget_large` and `cost_low`, `cost_medium`, `cost_high` per model family, and we can treat those as the guidance you give the LLM—grounded in FACT/CONSENSUS rather than pretending to know exact numbers.

## Human

show me in a table.

## Assistant

Here’s a concise table that captures what we **can** say for each pool/model family, with explicit confidence and approximate bands rather than fake precision.

### Quota expectations by pool and model family

| Pool & model family | Typical quota scale (orders of magnitude) | Reset behavior | Cost profile | What this is based on | Confidence |
|---|---|---|---|---|---|
| **Gemini API – Flash family** (Gemini 2.5 Flash, 3.x Flash) | **RPM:** single‑digit to low‑double‑digit (≈5–15). **RPD:** tens to low‑hundreds (≈100–250), sometimes up to ~1,000 for Flash‑Lite in free tier guides. [1][2][3][4][5] | **Per‑project rate limits.** RPD resets at midnight Pacific; RPM/TPM enforced per 10‑minute windows. [6][3] | **Low/medium cost per call.** Designed for prototyping, parallel tasks, and structured extraction on free tier; significantly cheaper than Pro. [3] | Official rate‑limit doc (per‑project tiers, reset rules) plus late‑2025/2026 free‑tier guides showing ~10 RPM / ~250 RPD for Flash models and ~15 RPM / ~1,000 RPD for Flash‑Lite. [6][1][3][4] | **CONSENSUS** (bands are typical, exact numbers vary by project and may change). |
| **Gemini API – Pro family** (Gemini 2.5 Pro, 3.x Pro preview) | **RPM:** low single‑digit (≈5). **RPD:** low‑hundreds or below (≈50–100+), notably tighter than Flash. [1][3][7] | Same as Flash: per‑project; RPD resets at midnight Pacific; limits depend on tier/account. [6][3] | **High cost per call.** Intended for complex reasoning with limited free quota; preview models sometimes stricter. [3][1] | AI Studio free‑tier tables (Gemini 2.5 Pro ≈5 RPM, ≈100 RPD) and forum answers (“around 30 requests/day” for Pro in some builds). [1][3][7] | **CONSENSUS** (ballpark, not exact; varies by tier/project). |
| **Antigravity – Gemini group** (Flash/Pro in CLI/desktop) | **Compute budget:** substantial shared pool for Gemini over a rolling **5‑hour window**, plus a larger weekly cap. Expect enough for heavy daily interactive coding unless you run long, agentic loops constantly. [8][9][10][11] | **Dual limiter:** rolling 5‑hour baseline that “refreshes every five hours until weekly limit reached,” and a **weekly cap** that can override the 5‑hour refresh and cause multi‑day lockouts when hit. [8][12][13][10][11] | **High cost per complex loop, medium per simple calls.** Agentic coding with many sub‑calls can drain the 5‑hour pool quickly; simple prompts are cheap relative to weekly budget. [8][9][10] | Antigravity plans doc (“high, generous quota, refreshed every five hours… higher weekly rate limit”) plus Google/Reddit threads confirming 5‑hour + weekly bars for each bucket and reporting weekly overriding 5‑hour refresh for Pro users. [8][9][10][13][12][11] | **FACT** on structure; **SPECULATION** on exact token/request counts (Google doesn’t publish denominators). |
| **Antigravity – Claude/GPT‑OSS group** | **Compute budget:** much smaller weekly+5‑hour pool than Gemini. Expect to hit weekly caps with relatively modest usage. [13][14][10][15] | Same dual limiter: 5‑hour baseline + weekly cap, but with **tighter weekly limits**, leading to multi‑day lockouts when exhausted. [13][14][10] | **High cost per call.** Third‑party models are constrained due to host capacity and external API costs; best reserved for review/critical checks. [8][14][10][15] | Support threads reporting “baseline quota will refresh after SIX DAYS for Claude and FOUR DAYS for Gemini” and multi‑day lockouts, plus Antigravity posts that describe separate buckets and tighter third‑party constraints. [13][14][10][15] | **FACT** on “separate, stricter pool”; **SPECULATION** on exact volumes. |
| **Gemini apps – AI Pro (web/mobile)** | **Daily capacity:** enough compute for heavy daily interactive use on Pro, with ~4× standard limits. Earlier prompt‑count snapshots show moving from ~single‑digit Pro prompts for free users to ~low‑hundreds of Pro/Thinking prompts for Pro, but now wrapped in compute‑based limits. [16][17][18][19][20][21] | **Compute‑based 5‑hour window + weekly cap.** Usage limit “refreshes every 5 hours until you reach your weekly limit”; caps are computed from prompt complexity, features, and chat length. [16][17][22][21] | **Medium/high cost per heavy Deep Research or thinking session; low cost per short Flash prompt.** Heavy features can burn through the 5‑hour compute window quickly; standard chatting is cheap. [17][19][21] | Gemini help and Antigravity/Gemini product announcements: AI Pro = 4× higher usage than standard, compute‑based usage limits, 5‑hour refresh until weekly cap, and earlier prompt limits (~100 Pro prompts, 1,500 Thinking prompts) that have since been generalized into compute terms. [16][17][19][22][21][20][18] | **FACT** on “compute‑based 5‑hour + weekly, 4× standard” and “view limits in app”; **CONSENSUS** on “low‑hundreds Pro/Thinking prompts” as a rough scale. |

***

### How to read this table for routing

Given this:

- Use **bands**, not integers, in your LLM guidance:
  - API Flash = `budget_small_to_medium`, `cost_low`, good for batch/parallel.
  - API Pro = `budget_small`, `cost_high`, reserve for rare reasoning calls.
  - Antigravity Gemini = `budget_medium`, `cost_medium`, main agentic coding pool.
  - Antigravity Claude/GPT‑OSS = `budget_small`, `cost_high`, review/adversarial only.
  - Gemini apps Pro = `budget_large`, `cost_compute_weighted`, manual deep work.

- Treat anything in the “SPECULATION” zone as **do not hardcode; measure from your UIs** (AI Studio rate‑limit page, Antigravity `/usage`, Gemini app Usage limits).

If you’d like, next step I can map these bands into explicit labels (`budget_small/medium/large`, `cost_low/medium/high`) per model family, ready to drop into your router’s config.

## Human

Where is table not great: 
PoolModels relevant to Flash / Flash-LiteAvailability nowQuota or rate that appliesWhat is actually known
Antigravity Gemini pool (agy)
Gemini 3.6 Flash, Gemini 3.5 Flash, Gemini 3.1 Pro
Flash-Lite unavailable
Shared 5-hour limit plus shared weekly limit for the Gemini group. Consumption is proportional to token cost. No RPM, TPM, RPD, or absolute denominator is published.
Proven from your live agy model selector and quota screen.
Antigravity Claude/GPT pool
Claude Sonnet 4.6, Claude Opus 4.6, GPT-OSS 120B
No Gemini Flash-Lite
Separate shared 5-hour limit plus weekly limit. Token-cost-weighted according to the wording in your live quota screen.
Proven from your live agy quota screen and model selector.
Gemini Developer API free tier
Latest Flash-Lite model available through API, subject to your project’s current model access
Yes, this is the pool where Flash-Lite matters directly
Best available estimate: roughly 15 RPM, 250,000 TPM, and approximately 1,000 RPD, per project. Exact live limits may differ by model and project.
Estimate based on current free-tier patterns; Google AI Pro does not increase this unbilled project quota.
Gemini web/mobile under Google AI Pro
Flash-Lite may be used as a fallback or standard low-cost model, but is not necessarily presented as a selectable named model
Indirectly / product-managed
4× the standard consumer compute allowance, with a 5-hour limit and weekly cap. No defensible requests-per-day conversion exists.
Plan-level entitlement is known; exact Flash-Lite allocation is not published.

## Assistant

The table is useful conceptually, but it overstates certainty in a few places and blurs important distinctions between **“proven for your account”**, **“general product behavior”**, and **“best‑guess numeric estimate.”** Here’s where I’d flag it as “not great,” row by row.

***

## Antigravity Gemini pool (agy)

**Row text:**

> Shared 5-hour limit plus shared weekly limit for the Gemini group. Consumption is proportional to token cost. No RPM, TPM, RPD, or absolute denominator is published.  
> Proven from your live agy model selector and quota screen.

### Issues

- **“Consumption is proportional to token cost” is stronger than the evidence.**  
  Antigravity docs and discussions say the Gemini pool is a shared budget correlated with “amount of work done” and that different models have different relative impacts, but they do **not** formally state a simple proportional formula like “8× cheaper → 8× more quota.” That framing is closer to speculation than fact.[1][2][3]

- **“Proven from your live agy model selector and quota screen” conflates UI observation with product‑wide behavior.**  
  The CLI showing Gemini 3.6 Flash, 3.5 Flash, 3.1 Pro under one bar proves **your current account** has a shared Gemini group, but it doesn’t prove:
  - That this structure never changes,
  - That it’s proportional to public API pricing,
  - That the same holds in other tiers or regions.  
  So “proven” should be narrowed: **proven for your current AI Pro Antigravity subscription**, not globally.

### Better framing

- **FACT:** Gemini models in your Antigravity AI Pro environment share a 5‑hour and weekly quota pool; denominators are not published.[2][4][1]
- **CONSENSUS:** Heavier/expensive models (Gemini Pro, long “thinking” traces) eat more of that pool than cheaper Flash‑family calls.[1][2]
- **SPECULATION:** Simple proportional mapping to public API token pricing.

***

## Antigravity Claude/GPT pool

**Row text:**

> Separate shared 5-hour limit plus weekly limit. Token-cost-weighted according to the wording in your live quota screen.  
> Proven from your live agy quota screen and model selector.

### Issues

- **Token‑cost weighting for third‑party group is murky.**  
  Antigravity docs describe “severe capacity limitations” and much tighter weekly caps for non‑Gemini models, but do **not** clearly state that this pool is proportional to token cost in the same way as Gemini. The primary, well‑documented behavior is “separate buckets, stricter limits,” not “explicit pricing‑based weighting.”[3][5][6][2][1]

- **“Proven” again overstates scope.**  
  You can see that Claude/GPT is a separate bucket with its own bars in your UI, and that it has a weekly cap and 5‑hour baseline. That’s **proven for your account**, but comments about how exactly cost is applied across those models are, at best, inferred.

### Better framing

- **FACT:** Claude/GPT‑OSS models share a separate 5‑hour + weekly pool with significantly tighter limits than Gemini in Antigravity AI Pro; this pool can lock out for days when exhausted.[5][6][2][3]
- **CONSENSUS:** More “expensive” non‑Gemini calls drain this pool quickly.
- **SPECULATION:** Explicit token‑cost weighting formula.

***

## Gemini Developer API free tier

**Row text:**

> Best available estimate: roughly 15 RPM, 250,000 TPM, and approximately 1,000 RPD, per project. Exact live limits may differ by model and project.  
> Estimate based on current free-tier patterns; Google AI Pro does not increase this unbilled project quota.

### Issues

- **Numeric band is too narrow and presented as a single “best estimate.”**  
  Across sources, free‑tier values for Flash/Flash‑Lite and Pro vary a lot:
  - Some tables: Flash ≈10 RPM, 250 RPD; Flash‑Lite ≈15 RPM, 1,000 RPD.[7][8][9]
  - Others show cuts (e.g. “10–50 RPM” or “100–250 RPD”) and warn Google has slashed quotas by 50–92%.[10][11][12]
  - Google’s own doc says **“rate limits depend on a variety of factors… and can be viewed in AI Studio”** and explicitly warns that specified limits are not guaranteed.[13]

  So anchoring on “15 / 250,000 / ~1,000” as **the** estimate risks giving a false sense of stability. The right shape is “RPM in the 5–15 band; RPD in the 100–1,000 band depending on model and project.”

- **“Google AI Pro does not increase this unbilled project quota” is directionally right, but loosely sourced.**  
  Official docs treat consumer AI Pro and Gemini API tiers separately; AI Studio limits are tied to project tier and billing, not to consumer AI Pro. That’s **strong consensus** but not spelled out in one sentence.[11][14][13]
  You’re safe to treat it as “AI Pro doesn’t magically upgrade your free API project,” but it’s better labeled as CONSENSUS.

### Better framing

- **FACT:** Limits are set per project; RPM/TPM/RPD dimensioned; RPD resets at midnight PT; AI Studio shows your exact limits; consumer AI Pro and AI Studio project tier are separate products.[14][15][11][13]
- **CONSENSUS:** Free‑tier Flash/Flash‑Lite sits in **≈5–15 RPM, ≈100–1,000 RPD** range, depending on model and project; Pro is tighter.[8][9][7][10][11]
- **SPECULATION:** “15 RPM / 250,000 TPM / 1,000 RPD” as a single “best estimate” for **your** project.

***

## Gemini web/mobile under Google AI Pro

**Row text:**

> 4× the standard consumer compute allowance, with a 5-hour limit and weekly cap. No defensible requests-per-day conversion exists.  
> Plan-level entitlement is known; exact Flash-Lite allocation is not published.

### Issues

This is actually the **least problematic** row; you’re pretty close to the documented behavior:

- Gemini help explicitly says apps now have **compute‑based usage limits**, that your limit **refreshes every 5 hours until you reach your weekly limit**, and describes AI Pro as “4× higher than standard limits.”[16][17][18]
- 9to5Google and related coverage reiterate the 5‑hour refresh + weekly cap for AI Ultra/Pro plans.[17][19]
- Reddit threads and help comments highlight that earlier prompt counts (12/50/100 uses/day) have been replaced by opaque compute limits; users no longer have clear RPD numbers.[20][21][22]

The only nuance I’d add:

- **“No defensible requests-per-day conversion exists” is accurate.**  
  You could quote older snapshots (e.g. “100 Pro prompts/day for Pro”), but they’ve already changed and are now wrapped in compute.[19][22]
- **“Flash-Lite allocation not published” is also accurate.**  
  Web app doesn’t necessarily expose Flash‑Lite as a named option, and per‑model caps within the compute pool aren’t documented.

So this row is essentially fine; just label the 4× and 5‑hour/weekly limits as **FACT**, and the role of Flash‑Lite in fallback behavior as **CONSENSUS/observed**, not guaranteed.

***

## Overall “not great” points

Across the whole table:

1. **Mixing UI‑specific observations with product‑wide “proven.”**  
   The Antigravity rows should say “proven in your current agy quota screen” rather than implying universal rules.

2. **Treating one numeric guess as “best estimate.”**  
   For the API free tier, the credible thing is a **range** (RPM and RPD bands) with a clear “depends on project/tier” caveat, not a single number that looks precise.

3. **Not labeling FACT vs CONSENSUS vs SPECULATION in the table itself.**  
   Given how much is tier‑dependent and tuning‑dependent, each cell should explicitly carry a confidence tag so you can see at a glance which parts you trust for automation and which parts are just routing hints.

If you’d like, I can rewrite this table with explicit confidence tags per cell (e.g. “FACT”, “CONSENSUS”, “SPECULATION”) and wider bands for the API row, so you can drop it straight into your “verified / inferred / unknown” register.
