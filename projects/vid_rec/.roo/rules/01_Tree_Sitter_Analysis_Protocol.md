# PROTOCOL: Code Analysis via Tree-Sitter

**Objective:** To ensure all initial code analysis is performed using the structured, reliable `mcp-tree_sitter` tool.

---

### !! CRITICAL MANDATE: `tree-sitter`-first for code analysis !!

Your primary method for understanding code structure is `mcp-tree_sitter`. You **MUST** call all `tree-sitter` tools using the `<use_mcp_tool>` wrapper.

---

### Primary Analysis Workflow

#### Step 1: Register Project (Once Per Session)
Before you can analyze any files, you **MUST** register the project directory. This gives the `tree-sitter` server a short name to reference the project. Use `.` for the path to reference the current workspace directory.

**Correct Invocation:**
```
<use_mcp_tool>
  <server_name>mcp-tree_sitter</server_name>
  <tool_name>register_project_tool</tool_name>
  <arguments>
    {
      "path": ".",
      "name": "YT_Sync"
    }
  </arguments>
</use_mcp_tool>
```
*You will use the `name` you define here (e.g., "YT_Sync") in all subsequent tool calls.*

#### Step 2: Analyze Files
Once the project is registered, you can analyze files using its registered name.

**Example: Get Symbols from a File**
To get a list of functions and classes from `yt_sync/auditing.py`:

**Correct Invocation:**
```
<use_mcp_tool>
  <server_name>mcp-tree_sitter</server_name>
  <tool_name>get_symbols</tool_name>
  <arguments>
    {
      "project": "YT_Sync",
      "file_path": "yt_sync/auditing.py"
    }
  </arguments>
</use_mcp_tool>
```

---

### !! COMMON FAILURE MODES (TO AVOID) !!

1.  **DO NOT** call `tree-sitter` tools directly. This will fail.
    ```
    <!-- INCORRECT: Missing the <use_mcp_tool> wrapper -->
    <get_symbols>
      <path>yt_sync/auditing.py</path>
    </get_symbols>
    ```

2.  **DO NOT** use the full file path as the `project` name. Use the short name you registered in Step 1.
    ```
    <!-- INCORRECT: 'project' argument is the full path -->
    <use_mcp_tool>
      <server_name>mcp-tree_sitter</server_name>
      <tool_name>get_symbols</tool_name>
      <arguments>
        {
          "project": "d:/OneDrive/_Python/_Projects/YT_Sync",
          "file_path": "yt_sync/auditing.py"
        }
      </arguments>
    </use_mcp_tool>
    ```
