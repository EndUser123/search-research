# Quota Decision Guide

Detailed guidance for choosing the right query tier to conserve Perplexity quota.

## Cost Model

| Tier | What It Costs | Resets | Typical Pool |
|------|---------------|--------|--------------|
| **Sonar / quick** | FREE — no quota consumed | — | Unlimited |
| **Pro Search** (standard/detailed, pplx_ask, pplx_query, all model-specific tools) | 1 Pro Search query | Weekly | ~300/week |
| **Deep Research** (pplx_deep_research, research intent) | 1 Deep Research query | Monthly | ~5-10/month |

## Intent Selection: Choose the Lowest Sufficient Tier

Ask yourself: **"Can Sonar answer this?"** If yes, use `quick`. Only escalate if the answer is no.

**Use quick (FREE — Sonar)** when the query is:
- A factual lookup: "What is the capital of France?"
- A definition: "What does CORS stand for?"
- A simple current-event check: "Who won the Super Bowl?"
- A quick status/version check: "What is the latest version of React?"
- A straightforward how-to that's well-documented: "How do I create a venv in Python?"
- A single-fact retrieval: "What is the population of Tokyo?"
- A simple translation or conversion: "How many meters in a mile?"

**Use standard (1 Pro Search)** when the query:
- Needs synthesis across multiple web sources: "Compare Next.js and Remix for SSR"
- Requires very current data from multiple sources: "What happened in AI this week?"
- Asks for a how-to with nuance: "Best practices for PostgreSQL indexing in 2026"
- Needs cited sources for credibility: "What are the side effects of metformin?"
- Involves a real comparison or tradeoff analysis

**Use detailed (1 Pro Search, premium model)** when the query:
- Requires complex multi-step reasoning: "Analyze the pros/cons of microservices vs monolith for a 10-person startup"
- Demands deep technical analysis: "Explain the differences between Raft and Paxos consensus algorithms"
- Needs authoritative synthesis with reasoning: "What are the economic implications of the new EU AI Act?"

**Use research (1 Deep Research — scarce)** ONLY when:
- The user explicitly asks for "deep research", "comprehensive report", or similar
- Never use autonomously — always ask the user first
- Falls back to premium Pro Search if research quota is exhausted

## Decision Flowchart

```
You want to query Perplexity...
│
├─ Is this a simple fact, definition, or well-known how-to?
│  └─ YES → intent='quick' (FREE)
│
├─ Does it need multiple current web sources or cited synthesis?
│  └─ YES → intent='standard' (1 Pro)
│
├─ Does it need deep reasoning, complex analysis, or premium model quality?
│  └─ YES → intent='detailed' (1 Pro, premium model)
│
├─ Did the user explicitly request deep research / comprehensive report?
│  └─ YES → intent='research' (1 Deep Research)
│
└─ When in doubt → intent='quick' (FREE, upgrade later if insufficient)
```

## Automatic Quota Protection

The smart router automatically protects you:
- **Healthy quota**: Uses the ideal model for your intent
- **Low quota (<20% pro remaining)**: Response footer warns you to conserve
- **Critical quota (<10% pro remaining)**: Downgrades detailed→auto to conserve
- **Exhausted quota**: Falls back to Sonar for everything except research
- **Research exhausted**: Falls back to premium Pro Search
- Response metadata shows what model was used, why, and remaining quota
