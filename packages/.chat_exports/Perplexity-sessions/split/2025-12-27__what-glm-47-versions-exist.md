---
title: "what glm 4.7 versions exist?"
date: "2025-12-27"
mode: "COPILOT"
uuid: "9df95071-8173-4f67-8b0e-7b881e5b8e9a"
entry_count: 2
---

## Human

what glm 4.7 versions exist?

## Assistant

GLM-4.7 was released on December 22, 2025, by Zhipu AI (Z.ai) as a major upgrade to the GLM-4.6 model, primarily focused on state-of-the-art coding and agentic reasoning.[1][2][3]

The primary version of the model is the flagship **GLM-4.7**, which is available through API providers like Z.ai and OpenRouter, as well as open-sourced via Hugging Face and ModelScope. While a specific "Exacto" variant has been mentioned by community members as a potential future release for more precise agentic tasks, it is not yet officially confirmed as a separate model version.[4][5][6][7]

### Key Technical Features
The GLM-4.7 model introduces specific operational modes that define how the version functions in production environments:
- **Interleaved Thinking**: Enables the model to perform per-response and per-tool call reasoning to improve instruction following.[2][8]
- **Preserved Thinking**: A mode that automatically retains thinking blocks across multiple conversation turns to prevent context loss.[8][2]
- **Turn-level Thinking**: Allows users to enable or disable reasoning on a per-turn basis to balance speed and accuracy.[2]

### Model Comparison
The following table highlights the differences between GLM-4.7 and its immediate predecessor, GLM-4.6:

| Feature | GLM-4.6 (Nov 2024) | GLM-4.7 (Dec 2025) |
| :--- | :--- | :--- |
| **HLE Score** | 30.4% [9] | 42.8% [2][9] |
| **SWE-bench (Coding)** | 68.0% [9] | 73.8% [9][10] |
| **Context Window** | 128K [11] | 128K (High Stability) [11] |
| **Thinking Modes** | Standard reasoning | Interleaved, Preserved, Turn-level [2] |
| **Primary Strength** | General coding [9] | Agentic execution and UI generation [10][3] |

### Accessibility and Pricing
- **Commercial API**: Available through Z.ai starting at $0.60 per million input tokens and $2.20 per million output tokens.[1]
- **Open Source**: The weights are available for local deployment and are compatible with inference frameworks such as vLLM and SGLang.[11]
- **Developer Tools**: It has been integrated as a default reasoning powerhouse for tools like Claude Code, Cline, and OpenCode.[12][4]

## Human

is there a V or Flash version?

## Assistant

As of December 27, 2025, there is no official **GLM-4.7-V** or **GLM-4.7-Flash** version currently released. The **GLM-4.7** flagship model is presently a text-only reasoning and coding model.[1][2]

However, the "V" (Vision) and "Flash" designations were previously introduced with the **GLM-4.6** series in early December 2025. It is common for Zhipu AI to release specialized multimodal or lightweight variants shortly after a major flagship launch.[3][4][5]

### GLM-4.6 Series Variants
Since GLM-4.7 is focused on text and coding, users requiring vision or low-latency versions typically use the following models from the immediately preceding generation:

- **GLM-4.6V**: A multimodal flagship with 106 billion parameters, designed for high-performance visual understanding, OCR, and video analysis.[6][3]
- **GLM-4.6V-Flash**: A lightweight 9B parameter version of the vision model optimized for speed, low-latency, and local deployment.[3][6]
- **GLM-4.6-Flash**: A fast, text-only version aimed at real-time applications and high-throughput processing.[1]

### Version Availability Table
| Model Series | Flagship (Text) | Vision (V) | Lightweight (Flash) |
| :--- | :--- | :--- | :--- |
| **GLM-4.5** | GLM-4.5 [1] | GLM-4.5V [1] | GLM-4.5-Air (Similar to Flash) [1] |
| **GLM-4.6** | GLM-4.6 [1] | GLM-4.6V [3] | GLM-4.6V-Flash / GLM-4.6-Flash [3] |
| **GLM-4.7** | **GLM-4.7** [2] | *Not Yet Released* | *Not Yet Released* |

### Recent Developments
While GLM-4.7 is text-only, it features improved performance for **front-end artifacts** and **document generation**, which partially bridges the gap for visual tasks by creating structured UI code that renders visually. For actual image-to-text or video-to-text analysis, **GLM-4.6V** remains the recommended current-generation tool.[7][5][3][1]
