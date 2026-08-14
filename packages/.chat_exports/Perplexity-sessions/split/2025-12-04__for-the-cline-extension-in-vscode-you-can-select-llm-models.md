---
title: "For the cline extension in vscode, you can select LLM models to use.  How can I use those models in claude code cli?"
date: "2025-12-04"
mode: "COPILOT"
uuid: "6babfe0f-e7f2-42b3-8500-132be103857b"
entry_count: 2
---

## Human

For the cline extension in vscode, you can select LLM models to use.  How can I use those models in claude code cli?

## Assistant

Now I have the information I need. Let me provide a comprehensive answer to the user.

## Using Cline Extension Models with Claude Code CLI

The short answer is: **Currently, there's no direct integration between the models you select in Cline and Claude Code CLI.** These are two separate systems with independent model configurations. However, you can use Claude models in both tools separately.

### Understanding the Separation

Cline is a **VSCode extension** that works with various LLM providers (Anthropic, OpenAI, OpenRouter, Ollama, etc.) and lets you select which model to use within the IDE. Claude Code CLI, on the other hand, is a command-line interface that specifically uses **Anthropic's Claude models** and has its own model configuration system.[1][2]

### Configuring Claude Code CLI Models

For Claude Code CLI, you configure models directly through these methods:[2]

**Model Aliases** - Use convenient shortcuts like:
- `opus` - Latest Opus model for complex reasoning
- `sonnet` - Latest Sonnet model for daily coding tasks
- `haiku` - Fast and efficient for simple tasks
- `opusplan` - Automatically uses Opus for planning, then switches to Sonnet for execution

**Setting models** via command line:
```bash
claude --model opus
```

Or switch during a session:
```
/model sonnet
```

Or configure permanently in your settings file:
```json
"model": "opus"
```

You can also use environment variables like `ANTHROPIC_MODEL` to control which model is used.[2]

### Using Claude with Cline

If you want to use Claude models in Cline, you can:[1]

1. Open Cline settings (click the gear icon ⚙️)
2. Select **Anthropic** as your API Provider
3. Add your Anthropic API key
4. Choose your preferred Claude model from the dropdown

This gives you Claude access within your VSCode IDE through Cline, but it's still a separate configuration from your Claude Code CLI setup.

### Key Difference

The fundamental difference is that **Cline models are IDE-based** (VSCode extension), while **Claude Code CLI models are terminal-based**. Each has its own configuration and they don't share settings or state. If you want consistency across both tools, you'll need to manually configure the same models in each tool's respective settings.

## Human

what about by using an open source repo or tool as a router?

## Assistant

Perfect! Now I have comprehensive information about using open-source routers. Let me provide a detailed answer.

## Using Open-Source Routers to Bridge Cline and Claude Code CLI

Yes, there are several excellent **open-source router tools** that can bridge your Cline extension and Claude Code CLI by acting as a proxy layer. This approach gives you unified control over LLM model selection across both environments.

### Primary Option: Claude Code Router (CCR)

**Claude Code Router** is the most comprehensive and actively maintained solution. It's specifically designed to route Claude Code requests to different models based on configurable rules, and it works perfectly for your use case.[1]

#### Key Features[1]

**Model Routing**: Routes requests to different models based on task type (background tasks, reasoning, long context, web search, images). This means you can configure Cline to use specific models for certain scenarios while Claude Code CLI uses others—all managed through a single configuration.

**Multi-Provider Support**: Supports OpenRouter, DeepSeek, Ollama, Gemini, Volcengine, SiliconFlow, and other providers. This lets you use any model available through these providers with Claude Code CLI.[1]

**Dynamic Model Switching**: Switch models on-the-fly using the `/model` command within Claude Code. For example: `/model openrouter,google/gemini-2.5-pro-preview`[1]

**Request/Response Transformation**: Custom transformers adapt requests/responses for different provider APIs, ensuring compatibility.[1]

#### Installation & Setup[1]

```bash
# Install Claude Code (if not already installed)
npm install -g @anthropic-ai/claude-code

# Install Claude Code Router
npm install -g @musistudio/claude-code-router
```

Create your configuration file at `~/.claude-code-router/config.json`:[1]

```json
{
  "PROXY_URL": "http://127.0.0.1:7890",
  "LOG": true,
  "LOG_LEVEL": "debug",
  "Providers": [
    {
      "name": "openrouter",
      "api_base_url": "https://openrouter.ai/api/v1/chat/completions",
      "api_key": "$OPENROUTER_API_KEY",
      "models": [
        "anthropic/claude-3.5-sonnet",
        "google/gemini-2.5-pro-preview",
        "deepseek/deepseek-chat"
      ],
      "transformer": {
        "use": ["openrouter"]
      }
    },
    {
      "name": "ollama",
      "api_base_url": "http://localhost:11434/v1/chat/completions",
      "api_key": "ollama",
      "models": ["qwen2.5-coder:latest"]
    }
  ],
  "Router": {
    "default": "openrouter,anthropic/claude-3.5-sonnet",
    "background": "ollama,qwen2.5-coder:latest",
    "think": "openrouter,anthropic/claude-opus-4-20250514",
    "longContext": "openrouter,google/gemini-2.5-pro-preview",
    "longContextThreshold": 60000
  }
}
```

The key configuration section is the **Router** object: which lets you specify which model handles different task types. This creates your unified model selection system.[1]

#### Running Claude Code with the Router[1]

```bash
# Start Claude Code through the router
ccr code

# Or use the UI for configuration
ccr ui

# Dynamically switch models during a session
/model openrouter,anthropic/claude-3.5-sonnet
```

#### Environment Variable Support[1]

For security, use environment variable interpolation in your config:

```json
{
  "OPENAI_API_KEY": "$OPENAI_API_KEY",
  "Providers": [
    {
      "name": "openai",
      "api_key": "$OPENAI_API_KEY"
    }
  ]
}
```

### Alternative: Bifrost Gateway

**Bifrost Gateway** is another open-source option that acts as an API gateway compatible with Anthropic, OpenAI, and Gemini APIs. By routing Claude Code through Bifrost, you intercept API calls at the transport layer, enabling model switching and tool injection without modifying the Claude Code binary.[2]

Configuration benefits of Bifrost:[2]

- Routes requests to GPT-4, Gemini, different Claude variants, or custom/local models
- Model selection handled in Bifrost's configuration
- Keeps Claude Code client setup simple and consistent

### How This Solves Your Problem

With a router like Claude Code Router:

1. **Unified Configuration**: Define all your LLM models in one `config.json` file
2. **Cline Integration**: Cline continues working as normal within VSCode with its own model selection
3. **Claude Code CLI Enhancement**: Claude Code CLI traffic flows through the router proxy, giving you access to all configured models
4. **Dynamic Switching**: Use `/model provider,model-name` to switch models during Claude Code sessions
5. **Task-Based Routing**: Automatically route different task types to different models based on your configuration

This approach is particularly powerful for your workflow since you can configure intelligent routing rules—for example, routing long-context tasks to Gemini, reasoning tasks to DeepSeek, and everyday coding to Claude Sonnet.[3]
