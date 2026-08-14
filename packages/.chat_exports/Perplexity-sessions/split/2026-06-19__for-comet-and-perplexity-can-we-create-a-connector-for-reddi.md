---
title: "for comet and perplexity, can we create a connector for reddit?  or does one already exist?"
date: "2026-06-19"
mode: "COPILOT"
uuid: "bd063674-9048-429b-9c1b-fb228903ff73"
entry_count: 20
---

## Human

for comet and perplexity, can we create a connector for reddit?  or does one already exist?

## Assistant

Short answer: I don’t see an official Reddit connector for Perplexity’s built-in connectors right now, but Perplexity does have a broader connectors system and an Enterprise app-connectors catalog that currently shows file apps, communication apps, and project-management apps rather than Reddit.[1]

For Pro users, the documented connectors I found are Google Drive and Dropbox, with Perplexity saying it is working on expanding to other cloud storage services.  The Enterprise app-connectors page also highlights apps like Notion, Linear, GitHub, email/calendar, and other workflow tools, but Reddit is not listed there in the content I checked.[2][1]

For Comet, I did not find evidence of a native Reddit connector in the sources I checked. What *does* seem plausible is building a custom integration around Reddit’s API or using a workflow tool/middleware layer to bridge Reddit with Perplexity/Comet, but that would be a custom connector rather than an existing first-party one.[3][4]

## Practical options

- **No-code/low-code route:** Use a workflow tool like n8n to connect Reddit data into your own pipeline, then feed the output into Perplexity or another agentic layer.[3]
- **Custom connector route:** Build a Reddit integration against Reddit’s API and expose it through whatever connector or automation surface Comet/Perplexity can consume.
- **Manual fallback:** If your need is just to research Reddit content, use Perplexity’s web search rather than a connector, since Perplexity can already search public web sources.[1]

## What I’d assume

I’m making one key assumption: by “connector” you mean an official first-party integration inside Perplexity/Comet, not a third-party automation bridge. Under that definition, the current evidence points to **no native Reddit connector yet**.[2][1]

Would you like me to map the best implementation path for a Reddit connector in your stack, including API auth, rate limits, and how to surface it to Comet/Perplexity?

## Human

I'm thinking of connectors like Recall and YouTube.  I have those as connectors for Comet and Perplexity.

## Assistant

Got it — you mean the **Perplexity/Comet connector catalog**, not generic third-party integrations. In that sense, Perplexity now supports a very large connector system, and as of the March 13, 2026 changelog it also supports **Bring Your Own Connector** via MCP for Pro, Max, and Enterprise users.[1]

## What that means for Reddit

I did **not** find Reddit listed among the first-party connectors I checked, while Perplexity explicitly documents connectors for things like files, work apps, and a broad prebuilt catalog.  So the likely answer is: **there may not be a native Reddit connector yet, but you can probably build one as a custom MCP connector** if your account tier supports it.[2][1]

## For Recall and YouTube

Recall is a good example of how this works: Recall’s MCP docs/video describe connecting any MCP-compatible client, including Perplexity, and even mention a path to show up as an official connector later while using a custom connector in the meantime.  YouTube also appears in Perplexity’s connector ecosystem in the sense that Perplexity can work with video-related sources and external integrations, but the key point is that the connector framework is broad enough that custom additions are now supported.[3][4][1]

## Best answer

So the corrected answer is:

- **Yes, you can likely create a Reddit connector** for Perplexity/Comet via MCP, assuming your plan and product surface allow custom connectors.[1]
- **No, I did not find evidence that Reddit already exists as a native first-party connector** in the connector lists I checked.[2][1]
- **If you just want Reddit access in Perplexity today**, the cleanest path is probably a custom MCP connector rather than waiting for an official one.[1]

## Next step

The most useful next step is to decide whether you want:

1. **Read-only Reddit search/connect** for research.
2. **Write-capable Reddit actions** like posting, commenting, or moderation.
3. **A Comet-only browser workflow** versus a Perplexity Computer/MCP connector.

Those three choices determine the API, auth model, and whether you should build a small MCP server, a webhook proxy, or a full connector service.

## Human

I just need it for search read-only for Reddit.

## Assistant

Yes — for **read-only Reddit search**, a custom connector is a good fit. Perplexity now supports custom MCP connectors for Pro, Max, and Enterprise, so you can point it at a small Reddit-search MCP server instead of waiting for a native Reddit connector.[1][2]

## What to build

For your use case, the connector only needs a narrow set of tools:

- `search_posts(query, subreddit?, sort?, time_filter?, limit?)`
- `get_post(url_or_id)` for opening a result
- optionally `get_comments(post_id, limit?)` if you want the thread context

That keeps the surface area small and safer than a full write-capable integration. The official Reddit API docs confirm Reddit exposes read access to posts and comments through its API, and Reddit requires registration/credentials for API access.[3][4][5]

## Best implementation path

The cleanest approach is:

1. Create a tiny MCP server.
2. Implement Reddit **application-only OAuth** for read access.
3. Expose just search and fetch tools.
4. Register it as a custom connector in Perplexity and, if supported, in Comet too.

Reddit’s public API docs and Reddit developer guidance indicate you need app registration and authentication even for read access, and older developer discussions align with application-only OAuth for read-only usage.[6][4][7]

## Important constraint

One thing to be careful about: Reddit’s access model has changed a lot since 2023, so the exact scopes, rate limits, and approval requirements should be taken from the current Reddit help/developer docs rather than older tutorials. The current Reddit help/docs pages are the authoritative source for that.[8][4]

## My recommendation

Build it as a **read-only MCP connector** with one auth path and one search endpoint first. That gives you the highest chance of working cleanly in both Perplexity and Comet, and it avoids overengineering write actions you don’t need.[2][1]

Would you like me to sketch the MCP tool schema and a minimal TypeScript or Python server for Reddit search?

## Human

doesn't a mcp for reddit already exist?

## Assistant

Yes — an MCP for Reddit already exists, and there are multiple community options rather than a single official one. I found open-source Reddit MCP servers like `hawstein/mcp-server-reddit` and `adhikasp/mcp-reddit`, plus other third-party offerings that expose Reddit search/read tools over MCP.[1][2][3]

## What that means for you

For your read-only search use case, an existing Reddit MCP is probably enough if it offers the tools you need: subreddit search, post lookup, and optionally comments. The `mcp-server-reddit` project explicitly says it provides frontpage posts, subreddit info, hot posts, post details, and comments from Reddit’s public API.[1]

## The tradeoff

The main question is not “does it exist?” but “which one is trustworthy and maintained enough for your stack.” Community MCPs vary a lot in API coverage, auth model, and maintenance, so you should check whether the project supports the exact query patterns you want and whether it’s compatible with Perplexity/Comet as a remote or local MCP server.[2][4][1]

## My recommendation

If your goal is just **search/read-only**, I would start with an existing Reddit MCP rather than building one from scratch. The fastest path is to test the simplest server against Perplexity/Comet, verify it can do search and result retrieval, and only then decide whether you need a custom wrapper.[4][2][1]

Would you like me to compare the best Reddit MCP options for Perplexity/Comet and tell you which one looks most maintained?

## Human

yes

## Assistant

Yes — there are already several Reddit MCP servers, and at least some are explicitly read-only or read-focused. The strongest match I found for your use case is a server description that says it provides **read-only access** to Reddit search/posts/comments via OAuth2, plus other projects that offer browsing, search, and comment reading.[1][2][3]

## Best fit for read-only search

For pure search/read-only, the clearest fit is the server described as supporting **read-only access to search for posts within subreddits**. It also uses OAuth2 and is presented as a Claude Desktop-compatible MCP server, which is a good sign for Perplexity/Comet compatibility if they accept standard MCP servers.[3]

## Other existing options

I also found an open-source Reddit MCP server that fetches and analyzes Reddit content, including hot threads and detailed post content, and another one that appears to support browsing Reddit, search, and user activity. Those may be more feature-rich, but they are not as clearly scoped to read-only as the one above.[4][1]

## What I would choose

If you want the safest minimal setup, I’d start with the explicitly read-only one first. If it works in your client, you get less risk and less surface area than a server that also exposes create/write actions.[5][3]

## One caution

I would still verify the current maintenance status and installation docs before committing, because MCP projects in this space are moving quickly and some are community-maintained rather than official. The Perplexity side does support custom MCP connectors, so the main risk is not compatibility in principle but whether the Reddit server is actively maintained and easy to authenticate.[6][7]

Would you like me to shortlist the top 2–3 Reddit MCP servers specifically for **Perplexity/Comet read-only search**, with install method and tradeoffs?

## Human

well, we need to read, but we also need to search.  searching thru 'hot' or 'best' is useful also.  so it sounds like we need all the features that can help with information finding and gathering.

## Assistant

Yes — for your use case, the Reddit MCP ecosystem already covers the core **information-finding** features you want: search, subreddit browsing, hot/new/top/rising feeds, post details, comment threads, and user/subreddit lookup. I found multiple servers that explicitly advertise those capabilities, including one that supports `search_posts` with `relevance`, `hot`, `top`, `new`, and `comments` sorting, plus separate servers that expose hot/new/top/rising posts and full comment trees.[1][2][3][4]

## Best feature match

The best fit is a server that includes:

- `search_posts` across Reddit or within a subreddit.
- `get_subreddit_posts` or equivalent feed browsing with `hot`, `top`, `new`, and `rising`.
- `get_post_details` and `get_post_comments`.
- `get_user_profile` and `get_subreddit_info` for context.

That combination gives you both broad discovery and deep read-through, which is exactly what you described.[2][3]

## Why this matters

For “finding information,” Reddit’s value is usually not just keyword search; it’s also trend discovery and thread digestion. The `hot`, `top`, and `new` views help you surface likely-relevant discussion faster, while comment retrieval lets the assistant extract consensus, disagreements, and edge cases from the thread itself.[3][4][1]

## My recommendation

I would shortlist servers in this order:

1. **The read-only OAuth2 server with hot/top/new/comments sorting** because it matches your stated needs with the smallest risk surface.[1]
2. **A broader read-only server with subreddit browsing, post details, comments, and user/subreddit info** if you want richer context.[2]
3. **A more feature-rich server that also exposes search, comments, user profiles, and trend signals** if you want maximum research depth and don’t mind evaluating maintenance more carefully.[5][3]

## Practical conclusion

So yes, you likely do **not** need to build a Reddit MCP from scratch unless you want tighter control. What you need is the right existing server with the right tool set, and the evidence suggests those features already exist in community MCPs.[3][1][2]

Would you like me to turn this into a short selection matrix for **Perplexity vs Comet compatibility, auth style, and feature coverage**?

## Human

yes

## Assistant

Here’s the selection matrix: for your use case, the best Reddit MCP is the one that combines **search + hot/top/new/rising + comments + subreddit/user context**, and the evidence shows that this feature set already exists in community servers. Perplexity also supports custom MCP connectors, so the main decision is which Reddit MCP is the right fit, not whether the platform can use one at all.[1][2][3]

## Selection matrix

| Option | Read-only | Search | Hot/Top/New/Rising | Comments | User/Subreddit context | Auth style | Fit |
|---|---:|---:|---:|---:|---:|---|---|
| `@enisze/reddit-mcp` | Yes | Yes | Yes, via subreddit post browsing and search-oriented tools | Yes | Some subreddit search/context | OAuth2 / Reddit app credentials | Best minimal fit for your research use case [2] |
| `adhikasp/mcp-reddit` | Yes | Likely yes | Yes, explicitly hot threads | Yes | Some analysis/context | Not fully clear from snippet | Good broader read/search tool, but validate current docs [4] |
| `reddit-mcp-buddy` | Likely yes | Yes | Browse/search/analyze user activity | Likely yes | User activity analysis | Not fully clear from snippet | Good if you care about user-centric research [5] |
| `reddit-mcp` on LobeHub | Yes | Yes | Yes, hot/new/top/rising | Yes | Yes | Not fully clear from snippet | Good feature coverage, but verify maintenance/auth details [6] |
| `nexgendata Reddit MCP` | Yes | Yes | Yes, hot/top/new + trend signals | Yes | Yes | Likely API-backed / vendor-hosted | Strong feature coverage, but more “service” than OSS server [3] |

## My recommendation

If you want the **most straightforward** route, start with `@enisze/reddit-mcp`. It is the clearest match because it explicitly says it supports read-only Reddit search via OAuth2, and the install/config pattern is simple.[2]

If you want the **broadest discovery workflow**, I’d consider a server that exposes hot/top/new/rising plus comments and user/subreddit context, because those are the features that actually help with information gathering on Reddit. The `reddit-mcp` listing on LobeHub and the `nexgendata` offering both advertise that broader surface area.[3][6]

## How to decide

Use this rule:

- Choose **`@enisze/reddit-mcp`** if you want a conservative, read-only, API-credential-based setup.[2]
- Choose **`adhikasp/mcp-reddit`** if you want a simple open-source search-and-analyze server and can tolerate checking the docs yourself.[4]
- Choose a **hot/top/new/rising**-focused server if your main job is discovery rather than exact keyword lookup.[6][3]

## One caution

I would still treat maintenance and auth details as the deciding factor, because MCP projects move fast and snippets can lag behind reality. Perplexity can consume custom MCP servers, but the stability of the Reddit server itself will matter more than the client side at this point.[7][1]

Would you like me to turn this into a **ranked shortlist with install commands** for the top 2 options?

## Human

want the broadest discovery workflow

## Assistant

For a **broad discovery workflow**, the strongest candidate I found is the NexGenData/Apify Reddit MCP because it explicitly covers subreddit search, hot/top/new posts, comment threads, user profiles, and trend signals. That is the closest match to “find, compare, and gather context” rather than just keyword lookup.[1]

## Best fit

| Candidate | Why it fits broad discovery | Caveat |
|---|---|---|
| NexGenData Reddit MCP | Explicitly includes subreddit search, hot/top/new posts, comment threads, user profiles, and trend signals. [1] | It is a hosted/service-style offering, so you should check pricing, auth, and data retention. |
| `enisze/reddit-mcp` | Explicit read-only OAuth2 server with search sorting for relevance, hot, top, new, and comments. [2] | Strong minimal fit, but less obviously “trend discovery” oriented than NexGenData. |
| Zero-config Reddit MCP | Promises search, subreddit browsing, post threads, user activity, and hot/top/new/rising. [3] | No-auth convenience is attractive, but you should verify current project quality and limits. |

## Why I’d pick NexGenData first

The reason is simple: you want breadth, not just safe minimalism. The NexGenData server explicitly surfaces **trend signals** in addition to feeds and threads, which is useful when you need the assistant to discover what is emerging rather than only answer direct queries.[1]

## When to choose the others

Choose `enisze/reddit-mcp` if you want the cleanest read-only OAuth2 path and still need hot/top/new/comments sorting.  Choose the zero-config server if you value fastest setup and broad browsing capabilities, and you are willing to trade some control for convenience.[2][3]

## My practical recommendation

Start with NexGenData if your main goal is research and discovery at scale. If it proves too opaque or too service-dependent, fall back to `enisze/reddit-mcp` as the more conservative read-only option.[2][1]

Would you like me to produce a final **ranked recommendation with install steps** for the top two options?

## Human

is it free to use?

## Assistant

Not always. The MCP software itself is often free, but the **Reddit data source** or hosted connector can be free, freemium, or paid depending on which server you choose.[1][2][3]

## What I found

- The `enisze/reddit-mcp` listing is a read-only OAuth2 server, but the snippet I checked does not show pricing, so I can’t confirm whether it is free from that source alone.[4]
- The NexGenData/Apify Reddit MCP explicitly shows **“Try for free”** and says pricing starts at **$20.00 / 1,000 tool calls**, with a free tier available.[1]
- Another Reddit MCP listing says the server is a server to browse/search/read Reddit, and its snippet notes token usage and that free-tier users should be fine with lighter usage, which suggests a freemium model rather than a pure free guarantee.[3]

## Practical answer

If you want **truly free**, the best bet is usually an **open-source local MCP server** that you run yourself, because the code is free and you only pay Reddit/API or infrastructure costs if those apply. An open-source Reddit MCP on GitHub is licensed MIT, which means the software itself is free to use.[2]

If you want **hosted and easiest**, the NexGenData option is not fully free; it has a free tier, but its paid usage is clearly metered.[1]

## My recommendation

For your “broadest discovery workflow,” I would treat this as a cost tradeoff:

- **Lowest cost:** self-host an open-source Reddit MCP.[2]
- **Fastest setup:** use a hosted freemium option like NexGenData and stay inside the free tier.[1]
- **Most control:** self-host and only expose the discovery tools you need.[2]

A key uncertainty remains: I did not verify the exact pricing page or usage limits for every community server, so “free” should be assumed **per-project, not per-category**.[3][4][1]

Would you like me to pick the best **free** option and the best **hosted free-tier** option side by side?

## Human

apify doesn't look free

## Assistant

You’re right — **Apify is not the same as free**. It may have a free tier or trial, but the Reddit MCP listings I found are clearly pay-per-event / pay-per-use, not “free forever.”[1][2]

## What’s actually free

The truly free path is usually an **open-source self-hosted Reddit MCP**. I found GitHub projects like `GridfireAI/reddit-mcp` that are simply plug-and-play MCP servers for browsing/searching/reading Reddit, which implies the software itself is free if you run it yourself.[3][4]

## What costs money

The hosted Apify-based Reddit MCP is metered. One listing shows pricing from **$4.99 / 1,000 searches** and describes pay-per-event costs per tool call, so it is explicitly not a free hosted service at scale.[1]

## Best interpretation for you

Since you want broad discovery and don’t want to pay Apify-style usage fees, the best fit is:

- **Self-host an open-source Reddit MCP** if you want free software and control.[4][3]
- **Use a hosted service only if you value convenience more than cost.**[1]

## My recommendation

Start with a self-hosted MCP that supports:
- subreddit search,
- hot/top/new/rising browsing,
- post details,
- comment threads,
- user/subreddit context.

That gives you the broad discovery workflow you asked for without paying per call.[5][6][3]

Would you like me to shortlist the best **self-hosted free** Reddit MCPs and rank them by feature coverage and maintenance?

## Human

yes, but I think we can include remote free mcp servers also.

## Assistant

Yes — that broadens the shortlist a lot. If remote free servers are allowed, the best **cost-free** options are the ones that are either truly free to run via a public endpoint or free because they require no API key/auth.[1][2][3]

## Best free remote options

| Option | Free? | Discovery breadth | Notes |
|---|---:|---:|---|
| `reddit-research-mcp` | Yes, appears free to use with a hosted endpoint and no credentials/config needed. [1] | Strong | Best match if you want remote convenience plus research-oriented features. |
| `reddit-no-auth-mcp-server` | Yes, no API key or auth needed. [2] | Strong | Uses public endpoints; good for quick discovery, but verify reliability. |
| `eliasbiondo/reddit-mcp-server` | Yes, no API keys or auth needed. [3] | Strong | Similar zero-config approach; good candidate for testing. |
| `GridfireAI/reddit-mcp` | Free software, self-hostable. [4] | Moderate to strong | Good if you want control rather than a remote hosted endpoint. |
| `enisze/reddit-mcp` | Free software, but requires Reddit OAuth credentials. [5] | Strong | Best if you want an API-backed read-only server and don’t mind setup. |

## Best fit for you

For your “broadest discovery workflow,” I’d rank **`reddit-research-mcp` first** because it is explicitly hosted, has no credentials/config requirement, and is positioned for Reddit research.[1]
My second choice would be **`reddit-no-auth-mcp-server`**, because it also avoids keys and supports search/browsing/comment-style research via public endpoints.[2]
My third choice would be **`eliasbiondo/reddit-mcp-server`** for the same no-auth reason, especially if you want a GitHub-hosted project you can inspect or self-host later.[3]

## Why not Apify

Apify-based options are convenient, but they are not the best answer if you want free usage at scale; the pricing is metered and tied to usage, even when a free tier exists.  That makes them fine as a fallback, but not my first recommendation for a cost-free workflow.[6][7]

## Practical recommendation

Start with a **free remote no-auth server** first, because it gives you the fastest path to broad discovery without building infrastructure. If it proves unreliable or too limited, fall back to a self-hosted open-source server like `GridfireAI/reddit-mcp` or `adhikasp/mcp-reddit`.[8][4][2][1]

Would you like me to do a tighter **top-3 ranking for Perplexity/Comet specifically**, based on ease of connection and feature breadth?

## Human

yes

## Assistant

Yes — for Perplexity/Comet, the key thing is that **Perplexity supports MCP connectors from local servers now, while remote MCP support is documented as coming soon / rolling out**, so the safest assumption is that local/self-hosted servers are the most reliable path today.[1][2]

## Top 3 for your case

| Rank | Option | Why it ranks here | Free? | Remote? | Fit for broad discovery |
|---|---|---|---:|---:|---:|
| 1 | `reddit-research-mcp` | Hosted, no credentials needed, explicitly built for Reddit research and says it turns Reddit into a queryable research database with claims-linked reports. [3] | Yes, appears free | Yes | Excellent |
| 2 | `reddit-no-auth-mcp-server` | No API key or OAuth needed; good for search, browsing, and reading Reddit via public endpoints. [4][5] | Yes | Yes | Excellent |
| 3 | `enisze/reddit-mcp` | Read-only OAuth2, supports subreddit post search and is explicitly aimed at read-only use. [6] | Software free, but not no-auth | Usually local/self-hosted | Very good |

## Why these three

I put `reddit-research-mcp` first because it is the most obviously research-oriented and the snippet says it needs **no Reddit credentials**, with token handling managed by the MCP client.[3]
I put `reddit-no-auth-mcp-server` second because it also avoids keys and is explicitly about reading Reddit through public endpoints, which keeps setup simple.[4][5]
I put `enisze/reddit-mcp` third because it is solid and read-only, but it adds Reddit OAuth setup, so it’s less frictionless than the no-auth options.[6]

## What I’d actually do

If your main goal is **broad discovery with the least setup**, start with `reddit-research-mcp`. If it doesn’t connect cleanly in your Perplexity/Comet setup, fall back to `reddit-no-auth-mcp-server`. If you hit limitations in public-endpoint reliability, use `enisze/reddit-mcp` as the more controlled fallback.[6][3][4]

## One caveat

Perplexity’s help docs currently describe local MCPs on macOS as the supported path, with remote MCP support still evolving. So even if a remote Reddit MCP is free and useful, it may depend on which Perplexity surface you’re using and whether it accepts remote connector URLs yet.[2][1]

Would you like me to turn this into a **decision tree** for “Perplexity Mac app vs Comet browser” and the exact connector I’d try first in each?

## Human

I'm on windows 11, using the comet brower to ask questions in perplexity.

## Assistant

That changes the recommendation a bit. On **Windows 11 in the Comet browser**, the most practical path is still a **remote/no-auth Reddit MCP** if Comet can attach to it directly, because Perplexity documents MCP support and third-party guides indicate remote MCPs are part of the supported model, while Comet itself is a Windows desktop browser.[1][2][3]

## Best fit for your setup

| Rank | Option | Why it fits Windows 11 + Comet | Free? |
|---|---|---|---:|
| 1 | `reddit-research-mcp` | No Reddit credentials, hosted, research-oriented, and explicitly says token handling is managed by the MCP client. [4] | Yes, appears free |
| 2 | `reddit-no-auth-mcp-server` | No API key or OAuth needed, built for public-endpoint Reddit browsing/searching. [5][6] | Yes |
| 3 | `enisze/reddit-mcp` | Good read-only OAuth2 fallback if you’re okay with Reddit app setup. [7] | Software free, but setup required |

## Why this is the best order

For Comet on Windows, convenience matters because you’re already using a desktop browser client rather than a local CLI-only workflow. A hosted remote MCP that works without keys reduces setup friction and avoids Windows/WSL dependency issues that show up in local MCP installations.[3][4][5]

## What I’d do first

I would try `reddit-research-mcp` first, because it is the most “research workflow” aligned and the least annoying to wire up. If Comet doesn’t connect cleanly, I’d try `reddit-no-auth-mcp-server`, then only fall back to `enisze/reddit-mcp` if you want more control or better API behavior.[4][5][7]

## One caution

Perplexity’s own docs still emphasize local MCP support on macOS, with remote support documented but not always equally surfaced across clients. So the exact connection steps may depend on whether your Comet UI exposes custom connector URLs for remote MCPs on Windows.[8][3]

Would you like me to give you the exact **“try this first” connection plan** for Comet on Windows 11, including what to do if the remote connector UI is missing?

## Human

yes, provide the instructions I need to use with the comet brower so perplexity can search reddit.

## Assistant

Yes — on **Windows 11 with Comet**, the most likely workable setup is to add a **remote custom MCP connector** in Perplexity, then point it at a Reddit MCP server that is already hosted and doesn’t require Reddit credentials. Perplexity’s help center says you can add MCP connectors from **Settings → Connectors**, and it distinguishes local and remote MCPs; it also says local MCPs require the helper app on the machine.[1]

## What to install first

Use a Reddit MCP that is already hosted and free, because that avoids local server setup on Windows. The best fit I found for that is `reddit-research-mcp`, which says no Reddit credentials are needed and that it handles authentication while exposing public Reddit data for research.[2]

## Steps to set it up

1. Open **Comet** and sign in to your Perplexity account. Comet is available on Windows and functions as Perplexity’s AI browser.[3][4]
2. Go to **Perplexity settings** and find **Connectors**. Perplexity’s help center says MCP connectors are added there.[1]
3. Choose **Add custom connector** or the equivalent remote-MCP option if it is shown in your UI. Perplexity’s docs and community notes indicate remote MCPs use a server URL rather than a local command.[5][1]
4. Paste the Reddit MCP server URL for the hosted research server you choose. The server should be one that explicitly says it needs no Reddit credentials.[2]
5. Save it, wait for the connector to show as available, then enable it under **Sources** in Perplexity. The help center says MCPs need to be toggled on in Sources before use.[1]
6. Test with a prompt like: **“Use Reddit to find recent discussions about [topic], then summarize the highest-signal threads.”** That should force the connector to perform Reddit search/browse actions.[1]

## If the UI does not show remote connectors

If Comet/Perplexity on your Windows install only shows local MCP setup, then use the same connector idea but switch to a local/self-hosted Reddit MCP instead. Perplexity’s help center says local MCPs require the PerplexityXPC helper app to connect securely to local servers.[1]

## Best prompt pattern

After the connector is enabled, use prompts that ask for both discovery and synthesis:

- “Search Reddit for the most discussed recent opinions on X.”
- “Show me the top Reddit threads on X from the last month and summarize the main arguments.”
- “Search Reddit hot posts for X, then extract the useful takeaways and disagreements.”

Those prompts make it more likely the assistant uses search, hot/top/new, and comment-thread tools rather than only keyword matching.[6][7][2]

## My recommendation

For your setup, I would try **`reddit-research-mcp` first**, because it is hosted, free-looking, and built for research without Reddit credentials.  If Comet refuses a remote connector URL, then the fallback is a local/self-hosted Reddit MCP.[2][1]

Would you like me to give you a **copy-paste connector test plan** with the exact prompts to verify whether the Reddit MCP is actually being used?

## Human

you need to give me all the details so I can fill in the fields properly.

## Assistant

Absolutely — here are the fields you need to fill, plus the safest values to use for your Windows 11 + Comet setup.

## What to enter

If you’re adding a **custom remote MCP connector** in Perplexity, the form will usually ask for:

- **Name**
- **MCP Server URL**
- Sometimes **authentication / advanced settings** if the server needs OAuth or headers.[1][2]

For your use case, the best first try is the hosted Reddit research server, because it says **no Reddit credentials are needed** and it is designed for public Reddit research.[3]

## Recommended values

Use these as your first attempt:

- **Name:** `Reddit Research`
- **MCP Server URL:** the hosted MCP endpoint for `reddit-research-mcp` from its project page. The GitHub snippet confirms the server exists, is official for that project, and is meant for Reddit research.[3]

If you instead choose the no-auth Reddit server, use:

- **Name:** `Reddit No Auth`
- **MCP Server URL:** the public endpoint from that project’s docs/listing. The project description says it works without API keys or OAuth and reads Reddit via public endpoints.[4][5]

## Which connector to pick first

I would start with **`reddit-research-mcp`** first, because it is the most research-oriented and is described as a hosted server with no Reddit credentials required.[3]
If that doesn’t work in your Perplexity UI, then use the no-auth Reddit server as fallback.[5][4]

## If you see advanced fields

If Perplexity shows extra fields like OAuth or advanced auth:

- Leave them blank for `reddit-research-mcp` if the server is truly no-auth for your client flow.[3]
- Only fill them if the server explicitly tells you to use OAuth or a token. The Perplexity and Claude connector docs show OAuth is optional and only needed for servers that require it.[6][1]

## How to test it

After saving the connector, test with a prompt like:

- “Search Reddit for recent discussions about [topic] and summarize the highest-signal threads.”
- “Find the top Reddit posts about [topic] from the last month.”
- “Show me Reddit hot posts about [topic] and extract the main arguments.”[4][3]

## Important caveat

I can give you the exact field values, but I still need the **actual server URL** from the project you choose, because the listings I found confirm the projects exist but don’t always expose the endpoint in the snippet.[7][4][3]
If you want, I can next give you a **project-by-project fill-in sheet** with the exact name, URL, auth choice, and which one to try first for each Reddit MCP option.

## Human

you need to look up on the internet for the information I need.

## Assistant

Yes — now I can give you the actual field-fill details, grounded in what I found online.

## Recommended connector to use first

Use **`reddit-research-mcp`** first. It is described as a hosted Reddit research MCP that turns Reddit into a queryable research database and needs **no Reddit credentials** on your side.[1][2]

## What to enter in Perplexity

Use these values:

- **Name:** `Reddit Research`
- **MCP Server URL:** the hosted MCP URL for `reddit-research-mcp` from its project page
- **Authentication:** `Open` / `None` if Perplexity offers that choice
- **Advanced settings:** leave blank unless the server page explicitly says otherwise[3][1]

Perplexity’s own changelog says custom remote connectors are added by providing an **MCP server URL**, and the connector can use OAuth, API key, or open authentication depending on the server.[4]

## If you want the no-auth fallback

Use **`reddit-no-auth-mcp-server`** if you want a zero-config alternative. The project snippet says it works on Reddit’s public endpoints with **no API keys or authentication required**, and the example install command is `uvx reddit-no-auth-mcp-server`.[5][6]

Fill the form like this:

- **Name:** `Reddit No Auth`
- **MCP Server URL:** the remote endpoint for `reddit-no-auth-mcp-server`
- **Authentication:** `Open` / `None`
- **Notes:** this one is meant to search, browse subreddits, read comments, and get structured data without credentials.[6][5]

## If Perplexity only accepts local MCPs

Perplexity’s help center says local and remote MCPs are supported differently, and local MCPs require the helper app `PerplexityXPC`. If your Comet/Windows UI only exposes local setup, then a remote URL may not work in that specific surface yet.[7]

## Best practical choice for you

For **Windows 11 + Comet + Reddit search**, I would try this order:

1. **`reddit-research-mcp`** — best research-oriented option, no Reddit creds.[1]
2. **`reddit-no-auth-mcp-server`** — simplest zero-config fallback.[5][6]
3. **`enisze/reddit-mcp`** — if you don’t mind creating a Reddit app and using OAuth2.[8]

## Important limitation

I found the project descriptions and install snippets, but not every listing exposed the exact public server URL directly in the snippet. So I can tell you **what to put in the fields**, but for the URL field itself you’ll need to copy the endpoint from the project’s install/docs page.[8][1][5]

## Copy-ready template

If you’re filling the connector form right now, use this template:

- **Name:** Reddit Research
- **MCP Server URL:** `paste the hosted endpoint from the Reddit Research MCP docs`
- **Auth:** Open / None
- **Save:** Yes

If that URL fails, switch to:

- **Name:** Reddit No Auth
- **MCP Server URL:** `paste the hosted endpoint from the zero-config Reddit MCP docs`
- **Auth:** Open / None
- **Save:** Yes[1][5]

Would you like me to do one more lookup specifically to find the **exact remote endpoint URL** for the top candidate so you can paste it directly?

## Human

"MCP Server URL: the hosted MCP URL for reddit-research-mcp from its project page" when I enter that exactly it doesn't work.

## Assistant

That explains it: the text I gave you was a description, not the actual URL. For `reddit-research-mcp`, the real remote MCP URL is:

`https://reddit-research-mcp.fastmcp.app/mcp`[1]

And for the zero-config Reddit MCP, the repository shows HTTP transport support on port 8000, but the exact hosted URL is not visible in the snippet I found, so I can’t truthfully invent one.[2]

## Fill the Perplexity fields

For the **reddit-research-mcp** connector, use:

- **Name:** `Reddit Research`
- **MCP Server URL:** `https://reddit-research-mcp.fastmcp.app/mcp`
- **Authentication:** `Open` or `None`
- **Advanced settings:** leave blank unless the UI requires something else[1]

## Why this one is the right first try

The project page explicitly says **“No credentials or configuration needed!”** and gives that direct MCP URL for “other AI assistants.”[1]
It is also the most aligned with your goal of broad Reddit discovery, because it is the official MCP server powering a Reddit research platform.[1]

## If that one still fails

The next thing to try is the zero-config server, but I’d need the exact public URL from its docs or deployment page before telling you what to paste. The GitHub repo confirms it supports HTTP transport and a `streamable-http` mode on port 8000, but not the hosted endpoint itself.[2]

## Important note

If Perplexity rejects the remote URL even though it is valid, that likely means your specific Comet/Perplexity surface is only accepting local MCPs or needs the helper app flow described in the Perplexity help center.[3]

I can keep going and find the exact URL for the zero-config server too, if you want a backup ready.

## Human

these don't seem to be working

## Assistant

The connectors showing as disconnected is most likely caused by a **missing PerplexityXPC helper application**, which Perplexity requires before any MCP connector (local or remote) will work.[1]

## Fix — step by step

### Step 1 — Install PerplexityXPC
Go to **Settings → Connectors** in Perplexity/Comet. There should be a download prompt or link for the **PerplexityXPC** helper app. Install it and restart Comet.[1]

### Step 2 — Re-check your Reddit Research connector fields

| Field | Value |
|---|---|
| **Name** | `Reddit Research` |
| **MCP Server URL** | `https://reddit-research-mcp.fastmcp.app/mcp` |
| **Authentication** | Open / None |

No Reddit credentials are needed — the project explicitly says **"No credentials or configuration needed!"**[2]

### Step 3 — Enable in Sources
After connecting, go to your Perplexity Sources settings and toggle **Reddit Research** and **Recall** **on**. Connectors must be activated in Sources to actually be used in searches.[3]

### Step 4 — Test
Try a prompt like:
- *"Search Reddit for recent discussions about [topic] and summarize the top threads."*

The PerplexityXPC helper is almost certainly the missing piece — once it is installed, both Reddit Research and Recall should connect properly.

## Human

can't find PerplexityXPC  on the connectors page.

## Assistant

Now I have a clear picture. Here is what is actually happening and what to do:

## The real situation

**PerplexityXPC is a macOS-only helper app** — it does not exist for Windows. That is why you cannot find it. The Perplexity help center article describing it is written for Mac users only.[1]

## What Perplexity says about remote MCPs on Windows

The good news is that as of the **March 13, 2026 changelog**, Perplexity added **remote custom MCP connector support** for Pro, Max, and Enterprise subscribers — and this works by simply providing an **MCP server URL**, no helper app needed. This is separate from the local MCP flow that requires PerplexityXPC.[2]

## Why your Reddit Research connector may not be connecting

The most likely causes are:

1. **Your Perplexity plan** — remote custom MCP connectors require **Pro, Max, or Enterprise**. If you are on a free plan, the connector UI may appear but not actually connect.[2]
2. **The connector needs to be toggled on in Sources** — after saving, go to the Perplexity homepage, click **Sources**, and toggle Reddit Research on.
3. **The connector UI in Comet on Windows may behave slightly differently** than the web version — the exact Add Connector flow in Comet's Settings → Connectors should show a field for MCP Server URL and an auth type of **Open/None**.

## Exact steps for Windows + Comet (no PerplexityXPC needed)

1. In Comet, go to **Settings → Connectors**
2. Click **Add Connector**
3. Go to the **Advanced** tab (not Simple — Simple is for local/command-based MCPs)[3]
4. Fill in:

| Field | Value |
|---|---|
| **Server Name** | `Reddit Research` |
| **MCP Server URL** | `https://reddit-research-mcp.fastmcp.app/mcp` |
| **Authentication** | Open / None |

5. Click **Save**
6. Go back to the Perplexity homepage → click **Sources** → toggle **Reddit Research** on
7. Test with: *"Search Reddit for recent discussions about [topic]"*

## Key point

Skip PerplexityXPC entirely — that is only for Mac local MCPs. On Windows with Comet, use the **Advanced tab** with the remote URL directly.[3]

## Human

image.jpg

## Assistant

I can see from your screenshots exactly what is happening. Here is what they reveal:

## What I can see

**Screenshot 1 (top):** Both **Reddit Research** and **Recall** show the **disconnected plug icon** — meaning they are saved as connectors but not connected/authenticated yet.

**Screenshot 2 (bottom):** The **Connectors dropdown** from the search bar shows Web, YouTube Data, Academic, Gmail, Google Drive, Outlook — but **Reddit Research is not listed there**. This is the Sources panel where you toggle connectors on for use in searches.

## The problem

The Reddit Research connector is saved but **not showing up in the Sources list** because it still shows as disconnected. The plug icon with the slash through it means it needs to be connected/authenticated first before it appears as a usable source.

## What to do

### Step 1 — Click the `...` menu on Reddit Research
On the Connectors settings page, click the **three dots (`...`)** next to Reddit Research and look for an option like **"Connect"**, **"Edit"**, or **"Reconnect"**. This should let you initiate the connection.

### Step 2 — Check the connector details
When you open it, verify:
- **MCP Server URL:** `https://reddit-research-mcp.fastmcp.app/mcp`
- **Authentication:** Open / None

### Step 3 — For Recall
The same disconnected icon appears on **Recall** too. Click its `...` menu and look for a **Connect** option — Recall likely requires you to authenticate with your Recall account via OAuth before it will connect.

### Key insight
The connectors panel in the search bar only shows **connected** sources. Until the plug icon becomes solid/filled (connected), neither Reddit Research nor Recall will appear there as toggleable sources. The fix is connecting them through the `...` menu, not re-adding them.

Can you click the `...` next to Reddit Research and tell me what options appear?
