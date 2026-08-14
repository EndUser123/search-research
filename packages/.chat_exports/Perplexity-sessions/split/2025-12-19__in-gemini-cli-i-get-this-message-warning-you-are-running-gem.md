---
title: "In gemini cli I get this message:

╭──────────────────────────────────────────────────────────────────────────╮
│ Warn"
date: "2025-12-19"
mode: "COPILOT"
uuid: "61a78c2e-1b14-4569-b76c-85cf2481f9ab"
entry_count: 2
---

## Human

In gemini cli I get this message:

╭──────────────────────────────────────────────────────────────────────────╮
│ Warning: You are running Gemini CLI in the root directory. Your entire   │
│ folder structure will be used for context. It is strongly recommended to │
│ run in a project-specific directory.                                     │
╰──────────────────────────────────────────────────────────────────────────╯


It's really annoying.  Is there an option to get rid of it?

## Assistant

## Disabling the Root Directory Warning in Gemini CLI

The warning you're seeing is by design—Gemini CLI warns you when running in the root directory because it includes your entire folder structure in the context, which can be inefficient. However, there's no built-in configuration option to directly suppress this specific warning.[1]

Here are your practical alternatives to eliminate the warning:

**Run from a project-specific directory instead of root**

The most straightforward solution is to change directories to a project-specific folder before running Gemini CLI. This is the recommended approach because it also improves performance by limiting the context to only the relevant files you need.[2][3]

```bash
cd /path/to/your/specific/project
gemini
```

**Create a workaround directory structure**

If you need to work across multiple projects, you could create a dedicated workspace directory and organize your projects inside it, then always run Gemini CLI from within those project subdirectories rather than the system root.

**Use sandboxing as a containment measure**

While it won't suppress the warning itself, you could enable sandbox mode using the `--sandbox` flag or setting it in your `settings.json` file. This at least contains the scope of operations:[4]

```bash
gemini --sandbox
```

**Feature request consideration**

The warning exists for good reasons—running Gemini CLI in the root directory can cause performance issues and accidentally expose unintended files to the AI. Rather than suppressing the warning, Google's recommendation is to respect it and organize your work into project-specific directories.[3]

If you believe there's a legitimate use case for suppressing this warning, you could file a feature request on the [Gemini CLI GitHub repository](https://github.com/google-gemini/gemini-cli/), where maintainers have addressed similar concerns about documentation and warnings.[1]

## Human

except that the drive I created is only for software projects.

## Assistant

In that case, you're already following the best practice that Gemini CLI recommends. Since your drive is dedicated to software projects, running Gemini CLI from within specific project subdirectories (rather than the root of that drive) is the ideal approach.

You could organize your workflow like this:

```bash
# Instead of running from:
cd D:\  # or wherever your software projects drive is
gemini

# Run from within a specific project:
cd D:\MyProject
gemini
```

This way, you get the added benefits of:

- **Eliminating the warning** by not running from the root directory
- **Improved performance** since only your current project files are included in the context
- **Better isolation** so Gemini CLI doesn't accidentally include unrelated projects in its context window

If you have multiple projects on that drive, this is the standard workflow pattern that Gemini CLI users follow. The warning disappears naturally once you're in a project-specific directory, and you'll have a cleaner, more focused context for Gemini to work with.
