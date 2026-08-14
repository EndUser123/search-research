---
title: "For each of the configured providers in this list, can you record their configurations so that we can restore it later i"
date: "2026-05-14"
mode: "COPILOT"
uuid: "5cc60ad6-fc0e-4298-a3ce-3aaf31c727ed"
entry_count: 2
---

## Human

For each of the configured providers in this list, can you record their configurations so that we can restore it later if we need to?

## Assistant

Here is the complete configuration record for all 8 configured providers in Bifrost (v1.5.2):[1]

***

## Bifrost Provider Configuration Snapshot

### 1. Cerebras[2]
| Field | Value |
|---|---|
| Type | Standard |
| API Key Env Var | `Cerebras_API_KEY` |
| Weight | 1 |
| Enabled | OFF |
| Base URL | *(default)* |

***

### 2. Gemini[3]
| Field | Value |
|---|---|
| Type | Standard |
| API Key Env Var | `Gemini_API_KEY` |
| Weight | 1 |
| Enabled | OFF |
| Base URL | *(default)* |

***

### 3. Groq[4]
| Field | Value |
|---|---|
| Type | Standard |
| API Key Env Var | `Groq_API_KEY` |
| Weight | 1 |
| Enabled | OFF |
| Base URL | *(default)* |

***

### 4. Minimax — CUSTOM[5]
| Field | Value |
|---|---|
| Type | Custom |
| API Key Env Var | `Minimax_API_KEY` |
| Weight | 1 |
| Enabled | OFF |
| Base URL | `https://api.minimax.io/anthropic` |
| Base Provider Type | Anthropic |
| Is Keyless | No |

**Allowed Request Types (enabled):**
- List Models ✅
- Chat Completion ✅
- Chat Completion Stream ✅
- Responses ✅
- Responses Stream ✅
- Count Tokens ✅
- All others: OFF

***

### 5. Mistral AI[6]
| Field | Value |
|---|---|
| Type | Standard |
| API Key Env Var | `Mistral_API_KEY` |
| Weight | 1 |
| Enabled | OFF |
| Base URL | *(default)* |

***

### 6. Nvidia — CUSTOM[7]
| Field | Value |
|---|---|
| Type | Custom |
| API Key Env Var | `Nvidia_API_KEY` |
| Weight | 1 |
| Enabled | OFF |
| Base URL | `https://integrate.api.nvidia.com/` |
| Base Provider Type | OpenAI |
| Is Keyless | No |

**Allowed Request Types (enabled):**
- List Models ✅
- Text Completion ✅
- Text Completion Stream ✅
- Chat Completion ✅
- Chat Completion Stream ✅
- Responses ✅
- Responses Stream ✅
- Embedding ✅
- Speech ✅
- All image/transcription/count tokens: OFF

***

### 7. OpenRouter[8]
| Field | Value |
|---|---|
| Type | Standard |
| API Key Env Var | `OpenRouter_API_KEY` |
| Weight | 1 |
| Enabled | OFF |
| Base URL | *(default)* |

***

### 8. Z.AI — CUSTOM[1]
| Field | Value |
|---|---|
| Type | Custom |
| API Key Env Var | `ZAI_API_KEY` |
| Weight | 1 |
| Enabled | OFF |
| Base URL | `https://api.z.ai/api/coding` |
| Base Provider Type | OpenAI |
| Is Keyless | No |

**Allowed Request Types (enabled):**
- List Models ✅
- Text Completion ✅
- Text Completion Stream ✅
- Chat Completion ✅
- Chat Completion Stream ✅
- Responses ✅
- Responses Stream ✅
- Embedding ✅
- Speech ✅
- All image/transcription/count tokens: OFF

***

### Common Network Defaults (all providers)
All providers share identical network settings unless overridden:
- Timeout: **30 seconds**
- Stream Idle Timeout: **60 seconds**
- Max Retries: **0**
- Initial Backoff: **500ms**
- Max Backoff: **5000ms**
- Max Connections Per Host: **5000**
- Enforce HTTP/2: OFF
- Skip TLS Verification: OFF
- Extra Headers: none
- CA Certificate: none

All providers are currently **disabled** (Enabled toggle = OFF). The three CUSTOM providers (Minimax, Nvidia, Z.AI) each have their own base URLs and API structure configurations as documented above.

## Human

They don't look off to me. They look like enabled on.

## Assistant

You're correct — my apologies for the error. All 8 providers have their Enabled toggle set to **ON**. I was misreading the dark-themed toggles visually. The DOM confirms `checked` for every single one.

Here is the corrected configuration record:

***

## Bifrost Provider Configuration Snapshot (Corrected)

### 1. Cerebras
| Field | Value |
|---|---|
| Type | Standard |
| API Key Env Var | `Cerebras_API_KEY` |
| Weight | 1 |
| **Enabled** | **ON** |
| Base URL | *(default)* |

### 2. Gemini
| Field | Value |
|---|---|
| Type | Standard |
| API Key Env Var | `Gemini_API_KEY` |
| Weight | 1 |
| **Enabled** | **ON** |
| Base URL | *(default)* |

### 3. Groq
| Field | Value |
|---|---|
| Type | Standard |
| API Key Env Var | `Groq_API_KEY` |
| Weight | 1 |
| **Enabled** | **ON** |
| Base URL | *(default)* |

### 4. Minimax — CUSTOM
| Field | Value |
|---|---|
| Type | Custom |
| API Key Env Var | `Minimax_API_KEY` |
| Weight | 1 |
| **Enabled** | **ON** |
| Base URL | `https://api.minimax.io/anthropic` |
| Base Provider Type | Anthropic |
| Is Keyless | No |
| Allowed Request Types (enabled) | List Models, Chat Completion, Chat Completion Stream, Responses, Responses Stream, Count Tokens |

### 5. Mistral AI
| Field | Value |
|---|---|
| Type | Standard |
| API Key Env Var | `Mistral_API_KEY` |
| Weight | 1 |
| **Enabled** | **ON** |
| Base URL | *(default)* |

### 6. Nvidia — CUSTOM
| Field | Value |
|---|---|
| Type | Custom |
| API Key Env Var | `Nvidia_API_KEY` |
| Weight | 1 |
| **Enabled** | **ON** |
| Base URL | `https://integrate.api.nvidia.com/` |
| Base Provider Type | OpenAI |
| Is Keyless | No |
| Allowed Request Types (enabled) | List Models, Text Completion, Text Completion Stream, Chat Completion, Chat Completion Stream, Responses, Responses Stream, Embedding, Speech |

### 7. OpenRouter
| Field | Value |
|---|---|
| Type | Standard |
| API Key Env Var | `OpenRouter_API_KEY` |
| Weight | 1 |
| **Enabled** | **ON** |
| Base URL | *(default)* |

### 8. Z.AI — CUSTOM
| Field | Value |
|---|---|
| Type | Custom |
| API Key Env Var | `ZAI_API_KEY` |
| Weight | 1 |
| **Enabled** | **ON** |
| Base URL | `https://api.z.ai/api/coding` |
| Base Provider Type | OpenAI |
| Is Keyless | No |
| Allowed Request Types (enabled) | List Models, Text Completion, Text Completion Stream, Chat Completion, Chat Completion Stream, Responses, Responses Stream, Embedding, Speech |

***

### Common Network Defaults (all providers)
- Timeout: 30s | Stream Idle Timeout: 60s | Max Retries: 0
- Initial Backoff: 500ms | Max Backoff: 5000ms
- Max Connections Per Host: 5000
- Enforce HTTP/2: OFF | Skip TLS: OFF | Extra Headers: none | CA Cert: none
