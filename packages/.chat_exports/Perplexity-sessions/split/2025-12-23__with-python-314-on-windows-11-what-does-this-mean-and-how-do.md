---
title: "with python 3.14 on windows 11, what does this mean, and how do we fix it?
This error originated either by throwing insi"
date: "2025-12-23"
mode: "COPILOT"
uuid: "9e041b8a-e9b3-4527-8907-18558e9289cf"
entry_count: 1
---

## Human

with python 3.14 on windows 11, what does this mean, and how do we fix it?
This error originated either by throwing inside of an async function without a catch block, or by rejecting a promise which was not handled with .catch(). The promise rejected with the reason:

● Web Search("Rich library auto_refresh False Windows Terminal ANSI escape code virtual terminal
            sequence")
  ⎿ Found 10 results for "Rich library auto_refresh False Windows Terminal ANSI escape code virtual
     terminal sequence"

## Assistant

Now I'll provide the comprehensive answer:

***

## What This Error Means

This is an **unhandled promise rejection** occurring in the Node.js layer of your Claude Code environment. The error indicates that a promise (from your web search tool—likely the Perplexity MCP server) was rejected, but the rejection was never caught with a `.catch()` handler or wrapped in a `try-catch` block.[1][2][3]

The specific reference to **`auto_refresh False Windows Terminal ANSI escape code`** tells you two things are happening simultaneously:

1. **The Promise Side**: Your Perplexity web search tool is making an async call that's failing and not being properly caught
2. **The Rich Library Side**: Your Python code is using the Rich library with `auto_refresh=False`, which disables automatic screen refresh for terminal output (particularly relevant on Windows Terminal where ANSI escape sequence handling can be finicky)

These aren't directly related, but they both create environments where error handling becomes fragile—Rich isn't auto-managing the terminal state refresh, and your async web search isn't wrapped in error handling.

***

## How to Fix It

### **Step 1: Wrap Your Web Search Tool Calls with Proper Error Handling**

If you're using a Perplexity MCP server or calling a web search function in your Claude Code, ensure every promise-returning call has error handling:

**Before (causes the error):**
```javascript
// This rejects and has no handler
const result = await performWebSearch("your query");
```

**After (fixed):**
```javascript
// Wrap in try-catch
try {
  const result = await performWebSearch("your query");
  // use result
} catch (error) {
  console.error("Web search failed:", error);
  // handle gracefully or rethrow with context
}
```

Or use `.catch()` explicitly:
```javascript
performWebSearch("your query")
  .catch(error => {
    console.error("Web search failed:", error);
    return null; // or default value
  })
  .then(result => {
    // process result or null
  });
```

### **Step 2: Fix Rich Library ANSI Handling on Windows Terminal**

When creating Rich Console, Live Display, or Progress objects, explicitly configure them for Windows Terminal:[4][5]

**For Console output:**
```python
from rich.console import Console

console = Console(
    force_terminal=True,  # Force ANSI codes even if detection fails
    legacy_windows=False,  # Use modern Windows Terminal, not legacy console
    color_system="truecolor"  # Use full 24-bit color support
)
```

**For Progress bars or Live displays:**
```python
from rich.progress import Progress

with Progress(
    auto_refresh=False,  # You're already using this
    force_terminal=True,
    force_interactive=False,  # Important: CI systems need this
) as progress:
    task = progress.add_task("[cyan]Processing...", total=100)
    for i in range(100):
        # do work
        progress.update(task, advance=1)
        progress.refresh()  # Manually refresh after each update when auto_refresh=False
```

**Key point**: When you set `auto_refresh=False`, you **must** manually call `.refresh()` after updating tasks.[5]

### **Step 3: Enable Windows Terminal Virtual Terminal Support (If Needed)**

On Windows 11, Windows Terminal should have this enabled by default, but if ANSI codes still aren't rendering:

1. Open PowerShell as Administrator
2. Run:
```powershell
New-ItemProperty -Path "HKCU:\Console" -Name "VirtualTerminalLevel" -Value 1 -Force
```

This enables ANSI/VT100 escape sequence support in the console.

### **Step 4: Environmental Control in Claude Code**

Add this at the top of your Python script to help Rich detect your terminal correctly:

```python
import os
os.environ['FORCE_COLOR'] = '1'  # Force color output
os.environ['PYTHONUNBUFFERED'] = '1'  # Unbuffered output
```

***

## Complete Example: Safe Web Search + Rich Output

Here's a pattern that avoids both errors:

```python
# Python side
from rich.progress import Progress
import subprocess
import json

def search_with_error_handling(query: str) -> dict:
    """Safely call Node.js web search with proper error handling."""
    try:
        result = subprocess.run(
            ["node", "search.js", query],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode != 0:
            raise RuntimeError(f"Search failed: {result.stderr}")
        return json.loads(result.stdout)
    except subprocess.TimeoutExpired:
        print("[red]❌ Web search timed out after 30 seconds[/red]")
        return {}
    except json.JSONDecodeError:
        print("[red]❌ Invalid response format from search[/red]")
        return {}
    except Exception as e:
        print(f"[red]❌ Search error: {e}[/red]")
        return {}

# Node.js side (search.js)
const performSearch = async (query) => {
  try {
    // Your Perplexity/web search call
    const result = await perplexityClient.search(query);
    console.log(JSON.stringify(result));
    process.exit(0);
  } catch (error) {
    console.error(JSON.stringify({ error: error.message }));
    process.exit(1);  // Signal failure to Python
  }
};

performSearch(process.argv[2])
  .catch(err => {
    console.error(JSON.stringify({ error: err.message }));
    process.exit(1);
  });
```

Then use Rich safely:

```python
from rich.console import Console

console = Console(force_terminal=True, legacy_windows=False)

with Progress(auto_refresh=False, force_terminal=True) as progress:
    task = progress.add_task("[cyan]Searching...", total=1)
    result = search_with_error_handling("your query")
    progress.update(task, advance=1)
    progress.refresh()
    
    if result:
        console.print("[green]✓ Search successful[/green]")
    else:
        console.print("[yellow]⚠ Search returned empty[/yellow]")
```

***

## Summary

The error is your **web search promise rejecting without a handler**. The Rich/ANSI context shows you're working in a mixed Python-Node.js environment (Claude Code) where async errors can slip through. **Add `.catch()` handlers or `try-catch` blocks around all promise-returning calls**, ensure Rich has manual `.refresh()` calls when `auto_refresh=False`, and configure explicit terminal support for Windows 11.[6][2][4]
