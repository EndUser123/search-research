---
title: "for factory droid, I'm using my own key from z.ai.  How do I set that up in droid?"
date: "2025-12-10"
mode: "COPILOT"
uuid: "1fc2c304-4252-48d3-a8a1-fffe0d4ca7bf"
entry_count: 2
---

## Human

for factory droid, I'm using my own key from z.ai.  How do I set that up in droid?

## Assistant

You configure it via Factory’s BYOK custom models in the Droid config file, pointing at Z.AI’s endpoint with your own key.[1][2]

## Edit the Factory config

Factory keeps its CLI/Droid config in a JSON file:[1]

- macOS/Linux: `~/.factory/config.json`.[1]
- Windows: `%USERPROFILE%\.factory\config.json`.[1]

Open that file in your editor.

## Add your Z.AI model

Inside `config.json`, add or extend a `custom_models` array with an entry for GLM using your Z.AI key. For a standard Z.AI API plan, the shape should look like:[2][1]

```json
{
  "custom_models": [
    {
      "model_display_name": "GLM-4.6 [Z.AI]",
      "model": "glm-4.6",
      "base_url": "https://api.z.ai/api/paas/v4",
      "api_key": "YOUR_ZAI_API_KEY",
      "provider": "generic-chat-completion-api",
      "max_tokens": 131072
    }
  ]
}
```

- If you are on the GLM Coding Plan, use `https://api.z.ai/api/coding/paas/v4` instead as the `base_url`.[3][1]
- Replace `YOUR_ZAI_API_KEY` with your actual key from the Z.AI console; it stays local and is not uploaded to Factory.[4][1]

## Use it inside Droid

Once saved:[5][1]

- Run `droid` in your project directory as usual.  
- In the Droid UI, use `/model` and pick your Z.AI GLM entry under the “Custom models” section.[5][1]

From that point, all Droid actions in that session will use your Z.AI key for the selected model.[2][1]

## Human

Exact config file path and JSON format for custom_models entry

## Assistant

Factory looks for a single JSON config at a fixed path, and the `custom_models` entry is a top-level array of model objects in that file.[1][2]

## Config file path

- macOS / Linux: `~/.factory/config.json`.[2][1]
- Windows: `%USERPROFILE%\.factory\config.json`.[3][1]

If the file does not exist, create it with a minimal valid JSON object.

## Minimal JSON structure

For a single BYOK model (adapt for Z.AI, OpenRouter, etc.), the config file can be exactly:

```json
{
  "custom_models": [
    {
      "model_display_name": "GLM-4.6 [Z.AI]",
      "model": "glm-4.6",
      "base_url": "https://api.z.ai/api/paas/v4",
      "api_key": "YOUR_ZAI_API_KEY",
      "provider": "generic-chat-completion-api",
      "max_tokens": 131072
    }
  ]
}
```

- `model_display_name`: How Droid shows it in the `/model` picker.[4][2]
- `model`: The model id passed to the provider (e.g., `glm-4.6`).[5][1]
- `base_url`: Provider’s chat/completions endpoint root (change to `https://api.z.ai/api/coding/paas/v4` for the GLM Coding Plan).[1][5]
- `api_key`: Your secret key; stays local in this file.[6][1]
- `provider`: Always `"generic-chat-completion-api"` for OpenAI-compatible HTTP APIs.[7][2]
- `max_tokens`: Upper token limit Droid can request from that model.[8][2]

If you add more models, just append additional objects to the `custom_models` array, keeping the rest of the file valid JSON.
