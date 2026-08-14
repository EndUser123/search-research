---
title: "what perplexity repos exist that allow me to use perplexity search and deep research?  They provided a $5 credit per mon"
date: "2026-03-11"
mode: "COPILOT"
uuid: "c92c3cc6-9816-4f7f-8b7e-0cd30ff39214"
entry_count: 1
---

## Human

what perplexity repos exist that allow me to use perplexity search and deep research?  They provided a $5 credit per month for api use, but have recently revoked it.

## Assistant

Perplexity AI's official GitHub organization (ppl-ai) has no repositories enabling programmatic use of their search or deep research features; it only contains forks of unrelated projects like icons and devtools.[1][2]

No official open-source repos exist for Perplexity search/deep research integration.[3][2][1]

## Unofficial Repos
Community/third-party GitHub repos provide API wrappers/clients for Perplexity's paid Search API (docs.perplexity.ai) and pplx-api (online LLMs with web access), usable post-$5 Pro credit revocation (confirmed removed ~Feb 2026).[4][5][6][7]

| Repo | Description | Language | Stars (approx) | Usage Notes |
|------|-------------|----------|----------------|-------------|
| [helallao/perplexity-ai](https://github.com/helallao/perplexity-ai) [6] | Unofficial Python wrapper for search (auto/pro/reasoning/deep research modes), supports streaming/follow-ups/files. | Python | N/A | Requires API key; account gen for limits (ethical concerns); incognito mode. |
| Others (e.g., Yusuke710/nanoPerplexityAI) [8] | Open-source Perplexity clones using own search/LLMs (no Perplexity API). | Python | Low | Local/self-hosted; no Perplexity dependency. |

## API Access
Use official Perplexity API (pay-as-you-go, no free tier post-revocation): Generate key at perplexity.ai/settings/api; SDK example (Python): `pip install perplexity; client.search.create(query="...")`.[9][7]

**Next step:** `pip install perplexity` then test with minimal paid credits (~$5 min top-up). Uncertainty: No official OSS confirmed (searched GitHub/org/docs); unofficial may break on API changes.[7]
