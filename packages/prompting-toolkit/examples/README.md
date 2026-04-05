# Prompting Toolkit Examples

This directory contains examples demonstrating how to use the **Prompting Toolkit** ecosystem.

## Directory Structure

```
examples/
├── hook_to_framework/     # Using both packages together
│   └── integrated_workflow.py
├── standalone/            # Using packages individually
│   ├── hook_only.py
│   └── framework_only.py
└── README.md             # This file
```

## Examples

### `hook_to_framework/integrated_workflow.py`

**Best for:** Understanding how both packages work together

Shows:
- How hook automatically enhances user prompts
- How framework provides programmatic control
- Integrated workflow from UX to library
- When to use each package

**Run this first** to understand the full ecosystem.

### `standalone/hook_only.py`

**Best for:** Claude Code users who want automatic enhancement

Shows:
- Setup and configuration
- Environment variables
- Complexity thresholds
- Domain detection
- Multi-terminal safety

No Python code required in production - just configuration!

### `standalone/framework_only.py`

**Best for:** Python developers building AI applications

Shows:
- Basic usage (orchestrator, context)
- Meta-prompt optimization (GA/DE)
- Using specific techniques
- Context-aware selection
- Performance tracking
- Custom techniques

Full programmatic control for sophisticated applications.

## Quick Start

```bash
# 1. Explore the integrated workflow
cat examples/hook_to_framework/integrated_workflow.py

# 2. Try hook-only (configuration based)
cat examples/standalone/hook_only.py

# 3. Try framework-only (Python library)
cat examples/standalone/framework_only.py

# 4. Run framework examples
cd examples/standalone
python framework_only.py
```

## Which Example Should I Start With?

| Your Goal | Start With |
|-----------|------------|
| Understand the full ecosystem | `hook_to_framework/integrated_workflow.py` |
| Improve my Claude Code prompts | `standalone/hook_only.py` |
| Build AI-powered features | `standalone/framework_only.py` |
| See how they work together | `hook_to_framework/integrated_workflow.py` |

## Key Concepts

### `hook` (Automatic Enhancement)

- **Runs automatically** in Claude Code
- **No code required** - just configuration
- **Interactive choice** - accept or decline enhancements
- **Multi-terminal safe** - isolated state per session

**Perfect for:** Day-to-day Claude Code usage

### `framework` (Python Library)

- **Programmatic control** - full Python API
- **23+ techniques** - Chain-of-Verification, Socratic, Self-Refine, etc.
- **GA/DE optimization** - meta-prompt tuning
- **Performance tracking** - metrics and monitoring

**Perfect for:** Building AI applications

### Combined (Full Ecosystem)

- **hook** improves user prompts automatically
- **framework** provides advanced strategies
- **Seamless integration** - both understand complexity, domain, security
- **Flexible upgrade** - start with hook, add framework when needed

**Perfect for:** Complete prompt optimization solution

## Running Examples

### Hook Examples (Configuration-Based)

```bash
# Just read the example - no execution needed
cat examples/standalone/hook_only.py

# Apply configuration to enable hook
# Edit P:/.claude/settings.json:
{
  "env": {
    "PROMPT_ENHANCEMENT_ENABLED": "true",
    "PROMPT_CHOICE_ENABLED": "true"
  }
}

# Restart Claude Code - hook is now active!
```

### Framework Examples (Python Code)

```bash
# Navigate to examples
cd examples/standalone

# Run framework examples
python framework_only.py

# Or run specific sections
python -c "from prompting_framework import PromptingOrchestrator; ..."
```

## Common Workflows

### Workflow 1: Automatic Enhancement (Hook Only)

1. User types prompt in Claude Code
2. Hook analyzes complexity and domain
3. Hook presents enhanced version
4. User accepts or declines
5. Enhanced prompt sent to Claude

**No code needed** - just enable in settings!

### Workflow 2: Programmatic Control (Framework Only)

1. Python application receives query
2. Framework selects best techniques
3. Framework executes strategies
4. Application uses optimized output

**Full control** - build AI-powered features!

### Workflow 3: Combined Ecosystem (Both)

1. User types prompt in Claude Code
2. Hook enhances automatically (UX layer)
3. Framework provides advanced strategies (library layer)
4. Best of both: automatic + programmatic

**Complete solution** - end-to-end optimization!

## Tips for Learning

1. **Start with `integrated_workflow.py`** - Understand the big picture
2. **Read before running** - Examples are heavily documented
3. **Experiment with settings** - Try different configurations
4. **Check the original docs** - `OLD_*.md` files have detailed info
5. **Look at the source** - `packages/hook/` and `packages/framework/`

## Troubleshooting

**Hook not running?**
- Check `PROMPT_ENHANCEMENT_ENABLED="true"` in settings.json
- Verify package is in `P:/packages/` or `~/.claude/hooks/_packages/`

**Framework import errors?**
- Install with `pip install -e packages/framework/`
- Check Python version >= 3.9

**Examples not working?**
- Ensure you're in the correct directory
- Check all dependencies are installed
- Try running with `python -v` for verbose output

## Next Steps

After exploring examples:

1. **Enable hook** in your Claude Code setup
2. **Install framework** locally: `pip install -e packages/framework/`
3. **Build your first application** using framework
4. **Contribute** new techniques or improvements

## Additional Resources

- [Main README](../README.md) - Complete ecosystem overview
- [OLD_PROMPT_ENHANCEMENT_README.md](../OLD_PROMPT_ENHANCEMENT_README.md) - Original hook docs
- [OLD_PROMPTING_FRAMEWORK_README.md](../OLD_PROMPTING_FRAMEWORK_README.md) - Original framework docs
- [packages/hook/](../packages/hook/) - Hook source code
- [packages/framework/](../packages/framework/) - Framework source code

---

**Happy prompting!** 🚀
