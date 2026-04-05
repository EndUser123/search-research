# Prompting Toolkit

> A comprehensive prompting ecosystem with real-time enhancement and advanced strategy library

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9+-brightgreen.svg)](https://www.python.org/)
[![Monorepo](https://img.shields.io/badge/structure-monorepo-purple.svg)](#monorepo-structure)

## 📺 Assets & Media

Explainer videos and architecture diagrams are available in the [assets/](./assets/) directory:

- **Explainer Video**: [![Watch Explainer Video](assets/infographics/prompting_toolkit_architecture.png)](assets/videos/prompting-toolkit_explainer_pbs.mp4)
  *Click image to watch PBS-structured explainer video (2:15) - Problem → Behavior → Solution*
- **Architecture Diagram**: See [assets/diagrams/architecture.md](./assets/diagrams/architecture.md) for system design overview
- **Integration Examples**: See [assets/examples/](./assets/examples/) for hook and framework integration patterns

Note: Media assets are generated using NotebookLM and Claude Code's built-in diagramming tools.

## 🎯 Two Installation Modes

This package supports **two installation modes** depending on your Claude Code setup:

### Mode A: Router-Based Installation (Recommended for Advanced Users)

If you use a custom hook router system (like `UserPromptSubmit_router.py`), install via the standard plugin pattern:

```bash
# 1. Clone or copy this package to P:/packages/
git clone <repo-url> P:/packages/prompting-toolkit

# 2. The .claude-plugin directory will be auto-discovered by Claude Code
# 3. Your router (P:/.claude/hooks/UserPromptSubmit_router.py) will handle the hooks
```

**How it works:**
- `.claude-plugin/plugin.json` declares this as a Claude Code plugin
- `hooks.json` routes UserPromptSubmit events to your custom router
- Your router consolidates multiple hooks and manages execution order
- This is the **hybrid approach**: official plugin structure + custom router integration

**Why use this mode:**
- ✅ Centralized hook management in your router
- ✅ Fine-grained control over hook priorities and execution order
- ✅ Easy to debug and test hooks via router
- ✅ Can add custom preprocessing/postprocessing in router

### Mode B: Default Claude Code Installation (Standard Claude Code Users)

If you're using **default Claude Code functionality** without custom routers:

```bash
# 1. Copy the hook package directly to Claude's hooks directory
cp -r P:/packages/prompting-toolkit/packages/hook ~/.claude/hooks/_packages/prompt-hook

# 2. Enable in Claude Code settings.json
claude config set hooks.UserPromptSubmit.prompt-hook.enabled true
```

**Or add to your `~/.claude/settings.json`:**
```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "python ~/.claude/hooks/_packages/prompt-hook/hook/prompt_enhancement.py"
          }
        ]
      }
    ]
  }
}
```

**How it works:**
- Direct hook execution without router layer
- Simpler setup for standard Claude Code installations
- Each hook is registered independently in settings.json

**Why use this mode:**
- ✅ No custom router required
- ✅ Standard Claude Code plugin pattern
- ✅ Easier for users without advanced hook setups
- ✅ Works out-of-the-box with default Claude Code

## 🔧 Configuration

### Environment Variables

Both installation modes support these environment variables:

```bash
# Enable/disable prompt enhancement
export PROMPT_ENHANCEMENT_ENABLED=true

# Enable interactive choice UI (ask user before applying enhancement)
export PROMPT_CHOICE_ENABLED=true

# Debug mode (verbose logging)
export PROMPT_ENHANCEMENT_DEBUG=false
```

Add these to your `P:/.claude/settings.json` under the `"env"` section:

```json
{
  "env": {
    "PROMPT_ENHANCEMENT_ENABLED": "true",
    "PROMPT_CHOICE_ENABLED": "true"
  }
}
```

## 📊 Architecture

This monorepo contains two complementary packages:

### `packages/hook` (formerly `prompt-enhancement`)

**User-facing prompt improver** that runs automatically in Claude Code.

- ✨ **Noise Cleaning** - Removes terminal artifacts automatically
- 🎯 **Complexity Analysis** - Categorizes prompts (simple/moderate/complex/expert)
- 🏷️ **Domain Detection** - Identifies context (security, testing, database, frontend)
- 🔀 **Choice UI** - Interactive approval: enhanced vs. original prompt
- 🔒 **Multi-terminal Safe** - Isolated state per terminal session

**Perfect for:** Claude Code users who want automatic prompt improvement without leaving their workflow.

### `packages/framework` (formerly `prompting-framework`)

**Developer library** with 23+ prompting strategies and optimization algorithms.

- 🧬 **Meta-Prompt Optimization** - Genetic Algorithm (GA) + Differential Evolution (DE)
- 📚 **Multi-Strategy Support** - Chain-of-Verification, Socratic, Self-Refine, Query Fanout
- 🎛️ **Context-Aware Selection** - Automatic technique selection based on query characteristics
- 📊 **Performance Monitoring** - Built-in tracking and optimization
- 🛡️ **Constitutional Compliance** - Safety constraints built into the framework

**Perfect for:** Python developers building sophisticated AI applications.

## 🏗️ Monorepo Structure

```
prompting-toolkit/
├── .claude-plugin/         # Claude Code plugin metadata
│   ├── plugin.json        # Plugin declaration
│   └── hooks.json         # Hook routing configuration
├── packages/
│   ├── hook/              # Claude Code integration
│   │   ├── prompting_toolkit/
│   │   │   ├── __init__.py
│   │   │   └── enhancement.py
│   │   ├── tests/
│   │   └── pyproject.toml
│   │
│   └── framework/         # Python library
│       ├── src/prompting_framework/
│       │   ├── techniques/           # 23+ strategy modules
│       │   ├── meta_prompt_optimizer.py
│       │   ├── prompting_orchestrator.py
│       │   └── context_models.py
│       ├── tests/
│       └── pyproject.toml
│
├── examples/              # Cross-package examples
│   ├── hook_to_framework/  # Using both together
│   └── standalone/         # Individual package usage
│
├── README.md              # This file
├── LICENSE                # MIT
└── OLD_*.md               # Original package docs (preserved)
```

## 🚀 Quick Start

### Using `hook` (Automatic Enhancement)

**Mode A (Router-based):**
```json
// P:/.claude/settings.json
{
  "env": {
    "PROMPT_ENHANCEMENT_ENABLED": "true",
    "PROMPT_CHOICE_ENABLED": "true"
  }
}
```

**Mode B (Default Claude Code):**
```json
// ~/.claude/settings.json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "python ~/.claude/hooks/_packages/prompt-hook/hook/prompt_enhancement.py"
          }
        ]
      }
    ]
  }
}
```

Every prompt is now automatically analyzed and enhanced with your choice to accept or decline.

### Using `framework` (Python Library)

```python
from prompting_framework import PromptingOrchestrator, PromptingContext

orchestrator = PromptingOrchestrator()
context = PromptingContext(
    query="How should I implement this feature?",
    domain="software",
    complexity="medium"
)

# Auto-select best techniques
techniques = await orchestrator.select_applicable_techniques(context)
print(f"Best techniques: {[t.name for t in techniques]}")

# Or optimize prompts with GA/DE
from prompting_framework import MetaPromptOptimizer

optimizer = MetaPromptOptimizer()
result = optimizer.optimize(
    initial_prompt="You are a helpful assistant.",
    evaluator=lambda prompt: evaluate_quality(prompt)
)
print(f"Optimized: {result.best_prompt}")
```

## 💡 Using Both Together

**Example:** Enhanced user prompt → Framework strategy selection

```python
# 1. User types: "implement websocket server"
# 2. hook detects: "security domain, complex"
# 3. hook adds: "Security context: OWASP Top 10 considerations"
# 4. framework selects: Chain-of-Verification + Constitutional Compliance
# 5. Result: Secure-by-design implementation with verification steps
```

See [`examples/hook_to_framework/`](examples/hook_to_framework/) for complete integration examples.

## 📦 Installation Details

### Option A: Local Development (Monorepo)

```bash
git clone https://github.com/csf-dev/prompting-toolkit.git
cd prompting-toolkit

# Install both packages in editable mode
pip install -e packages/hook
pip install -e packages/framework
```

### Option B: Individual Packages

**Router-based installation:**
```bash
# Just the hook (Claude Code integration)
# Copy to P:/packages/ and let .claude-plugin handle discovery
cp -r packages/hook P:/packages/prompting-toolkit
```

**Default Claude Code installation:**
```bash
# Just the hook (direct to Claude hooks directory)
cp -r packages/hook ~/.claude/hooks/_packages/prompt-hook

# Just the framework (Python library)
pip install prompting-framework  # After publishing to PyPI
```

## 🛠️ Development

### Code Quality

```bash
# Format
black packages/

# Lint
ruff check packages/

# Type check
mypy packages/framework/src/
```

### Pre-commit Hooks

```bash
# Install (from package root)
pip install pre-commit
pre-commit install
```

## 🧪 Testing

```bash
# Test hook package
cd packages/hook
pytest

# Test framework package
cd packages/framework
pytest --cov=prompting_framework --cov-report=html

# Test all packages from root
pytest
```

## 📝 Migration from Original Packages

**If you were using:**

- `prompt-enhancement` → Now `packages/hook`
- `prompting-framework` → Now `packages/framework`

**All functionality is preserved.** Update your imports:

```python
# Old
from prompt_enhancement.hook import prompt_enhancement

# New (hook package)
from prompting_toolkit import enhancement

# Old
from prompting_framework import PromptingOrchestrator

# New (framework package - same!)
from prompting_framework import PromptingOrchestrator
```

## 🤝 Contributing

Contributions welcome! Please see:
- `packages/hook/CONTRIBUTING.md` - Hook-specific guidelines
- `packages/framework/CONTRIBUTING.md` - Framework-specific guidelines

## 📄 License

MIT License - see [LICENSE](LICENSE)

## 🗺️ Roadmap

- [ ] PyPI publishing for `prompting-framework`
- [ ] VS Code extension for `hook` functionality
- [ ] Additional techniques in framework (target: 30+)
- [ ] Performance benchmarks and comparison charts
- [ ] Integration tests covering both packages

## 📚 Original Documentation

Preserved for reference:
- [OLD_PROMPT_ENHANCEMENT_README.md](OLD_PROMPT_ENHANCEMENT_README.md) - Original `prompt-enhancement` docs
- [OLD_PROMPTING_FRAMEWORK_README.md](OLD_PROMPTING_FRAMEWORK_README.md) - Original `prompting-framework` docs

## 🌟 Acknowledgments

Built with:
- [Python](https://www.python.org/) - Language and ecosystem
- [Claude Code](https://claude.ai/code) - Hook integration platform
- [DEAP](https://github.com/DEAP/deap) - Optimization algorithm inspiration
- [pytest](https://pytest.org/) - Testing framework

---

**Author:** [Your Name] | **GitHub:** [@csf-dev](https://github.com/csf-dev)
