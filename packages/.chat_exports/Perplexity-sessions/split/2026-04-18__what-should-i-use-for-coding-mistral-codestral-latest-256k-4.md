---
title: "What should I use for coding?
mistral      codestral-latest                               256K     4.1K     no        no"
date: "2026-04-18"
mode: "COPILOT"
uuid: "ddb075e4-07fd-4f29-b26d-1a68386dd37a"
entry_count: 1
---

## Human

What should I use for coding?
mistral      codestral-latest                               256K     4.1K     no        no
mistral      devstral-2512                                  262.1K   262.1K   no        no
mistral      devstral-medium-2507                           128K     128K     no        no
mistral      devstral-medium-latest                         262.1K   262.1K   no        no
mistral      devstral-small-2505                            128K     128K     no        no
mistral      devstral-small-2507                            128K     128K     no        no
mistral      labs-devstral-small-2512                       256K     256K     no        yes
mistral      magistral-medium-latest                        128K     16.4K    yes       no
mistral      magistral-small                                128K     128K     yes       no
mistral      ministral-3b-latest                            128K     128K     no        no
mistral      ministral-8b-latest                            128K     128K     no        no
mistral      mistral-large-2411                             131.1K   16.4K    no        no
mistral      mistral-large-2512                             262.1K   262.1K   no        yes
mistral      mistral-large-latest                           262.1K   262.1K   no        yes
mistral      mistral-medium-2505                            131.1K   131.1K   no        yes
mistral      mistral-medium-2508                            262.1K   262.1K   no        yes
mistral      mistral-medium-latest                          128K     16.4K    no        yes
mistral      mistral-nemo                                   128K     128K     no        no
mistral      mistral-small-2506                             128K     16.4K    no        yes
mistral      mistral-small-2603                             256K     256K     yes       yes
mistral      mistral-small-latest                           256K     256K     yes       yes
mistral      open-mistral-7b                                8K       8K       no        no
mistral      open-mixtral-8x22b                             64K      64K      no        no
mistral      open-mixtral-8x7b                              32K      32K      no        no
mistral      pixtral-12b                                    128K     128K     no        yes
mistral      pixtral-large-latest                           128K     128K     no        yes

## Assistant

**For coding from this Mistral list, use devstral-2512 (Devstral 2).** It tops agentic coding benchmarks at 72.2% on SWE-bench Verified, handling multi-file edits, tool use, and large codebases with its 256K context.[1][2][3]

## Top Recommendations
- **devstral-2512**: Best overall for complex dev tasks; 123B params, open-weight SOTA for agents, rivals Claude Opus on SWE-bench.[4][1]
- **labs-devstral-small-2512**: Efficient alternative (24B); 68% SWE-bench, vision support ("yes"), runs on consumer GPUs.[3]
- **magistral-medium-latest**: Strong coding index (16.0), reasoning-focused with function calling; good for structured tasks.[5]

## Key Comparison
| Model                  | Context (In/Out) | Function Calling | Vision | SWE-bench Score | Notes |
|------------------------|------------------|------------------|--------|-----------------|-------|
| devstral-2512         | 262K/262K       | no              | no    | 72.2%          | Agentic SOTA [1][2] |
| labs-devstral-small-2512 | 256K/256K     | no              | yes   | ~68%           | Efficient, visual [3] |
| magistral-medium-latest | 128K/16K      | yes             | no    | Top 20 LiveCodeBench | Reasoning/coding [6][5] |
| codestral-latest      | 256K/4K         | no              | no    | HumanEval 86.6% | Fast/lightweight [7] |

Devstral series outperforms Codestral/Magistral on modern agent benchmarks like SWE-bench (real GitHub issues). Data from 2025-2026; assumes OpenRouter-like access (your list format).[8][9][10]

**Next step**: Test devstral-2512 on a SWE-bench sample via OpenRouter CLI: `openrouter --model mistral/devstral-2512 "Fix this GitHub issue: [paste]". Confidence: High (benchmarks consistent across sources).
