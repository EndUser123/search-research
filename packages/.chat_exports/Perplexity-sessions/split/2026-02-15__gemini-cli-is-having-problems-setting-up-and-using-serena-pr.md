---
title: "gemini cli is having problems setting up and using serena properly.  What does it need to do/"
date: "2026-02-15"
mode: "COPILOT"
uuid: "7b78cc85-d864-4662-aaea-4d0b4dc23197"
entry_count: 2
---

## Human

gemini cli is having problems setting up and using serena properly.  What does it need to do/

## Assistant

Gemini CLI basically just needs Serena running as an MCP server with a sane config, and then you have to register that MCP server in Gemini’s tools config so the model can actually call Serena’s tools.[1][2][3][4][5]

### 1. What Serena itself needs

To be usable from Gemini CLI, Serena must be able to start as an MCP server and see your project.[4][1]

- Install `uv` globally (Serena expects it).[6]
- Clone Serena and enter the repo:  
  - `git clone https://github.com/oraios/serena.git`  
  - `cd serena`[1][6][4]
- (Optional but recommended) copy and adjust the config:  
  - `cp src/serena/resources/serena_config.template.yml serena_config.yml`[6][1]
- Start the MCP server locally (basic form):  
  - `uv run serena start-mcp-server`  
  - or, from elsewhere: `uv run --directory /abs/path/to/serena serena start-mcp-server`[4]

Make sure Serena can see your codebase (via `--project` flag or `.serena/project.yml`) so tools like `find_symbol` and `edit_code` work correctly.[7][1][6]

### 2. What Gemini CLI needs to do with Serena

Gemini CLI must treat Serena as a local MCP server and load its tools.[2][8][3][5]

Conceptually, Gemini CLI will:

- Start Gemini with MCP support enabled.  
- Discover the Serena MCP endpoint (command + args).  
- Fetch and register Serena’s tool schemas.  
- Use those tools inside its ReAct loop for code editing, navigation, etc.[8][3][2]

In practice, that usually means adding a block like this (exact file/path depends on your Gemini CLI install, but the shape is):[2][6][4]

```jsonc
{
  "mcpServers": {
    "serena": {
      "command": "/abs/path/to/uv",
      "args": [
        "run",
        "--directory",
        "/abs/path/to/serena",
        "serena-mcp-server"
      ]
    }
  }
}
```

or, with the newer entry point:[4]

```jsonc
{
  "mcpServers": {
    "serena": {
      "command": "/abs/path/to/uv",
      "args": [
        "run",
        "--directory",
        "/abs/path/to/serena",
        "serena",
        "start-mcp-server"
      ]
    }
  }
}
```

Once that’s in place, restart Gemini CLI; you should see Serena’s tools listed among available MCP tools and the model will start calling them when you ask for code-aware operations.[3][5][2]

### 3. Common “it’s not working” issues

From what people report with Gemini CLI + Serena, most breakages come from:[5][9][10][7][6][4]

- Wrong `command`/`args` (e.g., pointing to Python instead of `uv`, or wrong `--directory`).  
- Serena not in a venv / environment that has its deps installed.  
- Missing `serena_config.yml` or project config so Serena has no project root.  
- Gemini CLI started before you added the MCP config, so it never registered tools.  
- Gemini aggressively preferring its built-ins instead of Serena; you sometimes need to explicitly instruct it to “use Serena tools for navigation/editing.”

If you paste your current Gemini CLI MCP config block and how you’re launching Serena, I can pinpoint what’s off and give you an exact patch.

## Human

✦ The relevant setting from Claude (extracted from the working serena plugin configuration at
  C:\\Users\\brsth\\.claude\\plugins\\cache\\claude-plugins-official\\serena\\2cd88e7947b7\\.mcp.json) is:


    1 {
    2   "serena": {
    3     "command": "uvx",
    4     "args": [
    5       "--from",
    6       "git+https://github.com/oraios/serena",
    7       "serena",
    8       "start-mcp-server"
    9     ]
   10   }
   11 }


  I have updated your global Gemini configuration (C:\\Users\\brsth\\.gemini\\settings.json) to mirror this working setup,
  while keeping --quiet and --project-from-cwd for better CLI compatibility:


    1     "mcpServers": {
    2         "serena": {
    3             "command": "uvx",
    4             "args": [
    5                 "--quiet",
    6                 "--from",
    7                 "git+https://github.com/oraios/serena",
    8                 "serena",
    9                 "start-mcp-server",
   10                 "--project-from-cwd"
   11             ]
   12         }
   13     },

## Assistant

Your Gemini `mcpServers` block for Serena looks structurally fine; the main extra things Gemini usually needs (vs Claude) are scope/allow-listing and sometimes a working directory or trust flag.[1][2][3]

### 1. Validate the Gemini `settings.json` shape

Make sure the Serena block sits at the top level (not nested under some other object) and that JSON is valid, e.g.:

```jsonc
{
  // ...other Gemini settings...

  "mcpServers": {
    "serena": {
      "command": "uvx",
      "args": [
        "--quiet",
        "--from",
        "git+https://github.com/oraios/serena",
        "serena",
        "start-mcp-server",
        "--project-from-cwd"
      ],
      "trust": true
    }
  }
}
```

Gemini CLI uses this exact top-level `mcpServers` object to discover servers and will ignore them if the structure is off.[2][3]

### 2. Check global MCP settings (allowed/excluded)

If you have a top-level `mcp` block, you may need to explicitly allow Serena:[1][2]

```jsonc
"mcp": {
  "allowed": ["serena"],
  "excluded": []
}
```

If `mcp.allowed` exists and does not include `"serena"`, Gemini will never connect even though the `mcpServers` entry is correct.[2][1]

### 3. Confirm Serena actually starts under `uvx` in Gemini’s context

From a regular shell in a project directory where you’re invoking `gemini`, run:

```bash
uvx --quiet --from git+https://github.com/oraios/serena \
  serena start-mcp-server --project-from-cwd
```

If that fails (import error, missing uv, auth to GitHub, etc.), Gemini will also fail silently or just mark the server as DISCONNECTED.[4][5][6]
If it works, you should see Serena start and log that it detected the project directory.

### 4. Optional: add `cwd` so Serena sees the same project as Gemini

Gemini doesn’t automatically change `cwd` for MCP servers; if you’re using a global `~/.gemini/settings.json`, adding `cwd` is recommended:[7][2]

```jsonc
"mcpServers": {
  "serena": {
    "command": "uvx",
    "args": [
      "--quiet",
      "--from",
      "git+https://github.com/oraios/serena",
      "serena",
      "start-mcp-server",
      "--project-from-cwd"
    ],
    "cwd": ".",
    "trust": true
  }
}
```

This lets Serena’s `--project-from-cwd` resolve relative to the directory where you run `gemini` (which matches how you’re used to Claude’s behavior).[4][2]

### 5. How to verify Gemini actually sees Serena

Once config is in place:

1. Restart any long-lived Gemini CLI session.  
2. Run something like: `gemini tools list` (or your equivalent) and confirm `serena` is listed as an MCP server with status CONNECTED.[8][2]
3. In a prompt, explicitly ask: “Use the **Serena** MCP tools to inspect this repository and list top-level Python modules.” If you don’t see any tool calls, Gemini probably still isn’t connecting.

If you paste your full `settings.json` (redact keys) and the exact output of that standalone `uvx ... serena start-mcp-server --project-from-cwd` test, I can tighten this into a minimal working config line-for-line.
