---
title: "How to use opencode headless with chutes and deepseek 3.2?"
date: "2026-01-26"
mode: "COPILOT"
uuid: "2267fd05-33d8-43ee-8e12-ae143877864f"
entry_count: 3
---

## Human

How to use opencode headless with chutes and deepseek 3.2?

## Assistant

Perfect! I found solid documentation and examples. Based on the search results, here's your **step-by-step setup guide**:

## OpenCode Headless + Chutes + DeepSeek 3.2 Integration

### 1. **Install OpenCode CLI**

```powershell
npm install -g opencode-ai
```

Verify installation:
```powershell
opencode --version
```

### 2. **Set Up Chutes.ai Account & API Key**

1. Register at **[chutes.ai](https://chutes.ai/)** (free account, just needs username)
2. Generate API key:
   - Log in to Chutes
   - Click **"API"** in the sidebar
   - Generate a new API key (don't use the default)
   - **Store it securely** - you'll need it for authentication

### 3. **Configure OpenCode for Chutes + DeepSeek**

Create or update your OpenCode configuration to use the Chutes provider:

```bash
opencode configure
```

Or manually configure via environment variables:

```powershell
$env:OPENCODE_MODEL = "provider/model-name"
$env:OPENCODE_API_KEY = "your-chutes-api-key"
```

**For DeepSeek 3.2 specifically:**
- **Model ID:** `deepseek-ai/DeepSeek-V3-0324`
- **Base URL:** `https://llm.chutes.ai/v1/`
- **API Key:** Your Chutes API key

### 4. **Start OpenCode Headless Server**

```bash
# Start headless server for API access
opencode serve --port 4096

# OR start with web interface
opencode web --port 4096
```

### 5. **Use in Your Code Generation Pipeline**

**Option A: Via CLI (Direct)**
```bash
opencode run "Write a Python function to sort an array using quicksort" \
  --model provider/deepseek-ai/DeepSeek-V3-0324 \
  --attach http://localhost:4096
```

**Option B: Via API (For Your Pipeline)**
```python
import requests
import json

OPENCODE_URL = "http://localhost:4096"
CHUTES_API_KEY = "your-api-key"

payload = {
    "messages": [
        {"role": "user", "content": "Write a TypeScript function for debouncing"}
    ],
    "model": "deepseek-ai/DeepSeek-V3-0324",
    "provider": "chutes"
}

headers = {
    "Authorization": f"Bearer {CHUTES_API_KEY}",
    "Content-Type": "application/json"
}

response = requests.post(
    f"{OPENCODE_URL}/v1/chat/completions",
    json=payload,
    headers=headers
)

code = response.json()["choices"][0]["message"]["content"]
print(code)
```

**Option C: Custom OpenAI-Compatible Client**
```python
from openai import OpenAI

client = OpenAI(
    api_key="your-chutes-api-key",
    base_url="https://llm.chutes.ai/v1/"
)

response = client.chat.completions.create(
    model="deepseek-ai/DeepSeek-V3-0324",
    messages=[
        {"role": "user", "content": "Generate a React component"}
    ],
    temperature=0.3  # DeepSeek recommends 0.3 for balanced output, 0.0 for coding
)

print(response.choices[0].message.content)
```

### 6. **Optimization Tips for Code Generation**

**Temperature Settings (DeepSeek Recommendations):**
- **0.0** - Deterministic (best for code generation)
- **0.3** - Balanced (good for mixed tasks)
- **0.6+** - Creative (reasoning tasks)

**Best Practices:**
- Use `temperature=0.0` for deterministic code output
- Use `min_p=0.01` instead of default 0.1 to filter low-probability tokens
- Set timeout to avoid hanging on long generations
- Cache prompts if running repetitive code generation

### 7. **Advanced: Multi-Agent Pipeline**

For orchestrating multiple code agents via OpenCode headless:

```bash
# Terminal 1: Run persistent OpenCode server
opencode serve --port 4096

# Terminal 2: Spawn code generation task
opencode run "Create API endpoint handler" \
  --attach http://localhost:4096 \
  --model provider/deepseek-ai/DeepSeek-V3-0324 \
  --session my-codegen-session

# Terminal 3: Run quality checks on generated code
opencode run "Lint and test the generated code" \
  --attach http://localhost:4096 \
  --session my-codegen-session
```

### Key Configuration File (`.opencode/config.json`)

```json
{
  "provider": "chutes",
  "model": "deepseek-ai/DeepSeek-V3-0324",
  "apiKey": "${CHUTES_API_KEY}",
  "baseUrl": "https://llm.chutes.ai/v1/",
  "temperature": 0.0,
  "maxTokens": 4096,
  "timeout": 30000
}
```

### Troubleshooting

**403 Errors on Chutes.ai?**
- Some EU countries block chutes.ai - use a VPN if needed
- Verify API key is correctly generated (not using default)

**Reasoning blocks not appearing?**
- DeepSeek R1 reasoning requires specific handler (fixed in recent Chutes/OpenCode updates)
- Ensure you're using latest OpenCode version: `npm install -g opencode-ai@latest`

**Cold start delays?**
- Use `opencode serve` to maintain persistent server instead of spawning new process each time
- This eliminates MCP server boot overhead

***

**Want me to create a complete automation script for your code generation pipeline, or help set up specific integrations (like CI/CD, git hooks, etc.)?**

## Human

what about if I wanted to use it from powershell?  so from the terminal command line?

## Assistant

Perfect—I found specific PowerShell guidance and the CLI documentation. Here's your **complete PowerShell terminal workflow**:

## OpenCode + Chutes + DeepSeek 3.2 from PowerShell CLI

### Setup (One-Time)

```powershell
# Install globally
npm install -g opencode-ai

# Verify installation
opencode --version

# Set environment variables
$env:CHUTES_API_KEY = "your-chutes-api-key"
$env:OPENCODE_MODEL = "chutes/deepseek-ai/DeepSeek-V3-0324"
```

### Option 1: Direct CLI Commands (Simplest)

**Single prompt, get code back:**

```powershell
opencode run "Write a function to validate email addresses in TypeScript" `
  -m chutes/deepseek-ai/DeepSeek-V3-0324 `
  --format json
```

**With file attachment:**

```powershell
opencode run "Fix the bugs in this file" `
  -f ./mycode.ts `
  -m chutes/deepseek-ai/DeepSeek-V3-0324
```

**Continue a previous session:**

```powershell
opencode run "Now add error handling" `
  -c `
  -m chutes/deepseek-ai/DeepSeek-V3-0324
```

### Option 2: Persistent Server + Lightweight CLI (Best for Automation)

**Terminal 1 - Start persistent server:**

```powershell
# This keeps the server running between commands
opencode serve --port 4096
```

**Terminal 2 - Send commands without cold boot overhead:**

```powershell
# Each command reuses the existing server
opencode run "Generate a React component for a todo list" `
  --attach http://localhost:4096 `
  -m chutes/deepseek-ai/DeepSeek-V3-0324

# Continue in same session
opencode run "Add dark mode support" `
  --attach http://localhost:4096 `
  --session <previous-session-id> `
  -m chutes/deepseek-ai/DeepSeek-V3-0324
```

### Option 3: Direct API Calls via PowerShell (Most Control)

**Raw HTTP request to OpenCode server:**

```powershell
# Prerequisites: Server running on localhost:4096
$apiUrl = "http://localhost:4096/v1/chat/completions"

$body = @{
    model    = "chutes/deepseek-ai/DeepSeek-V3-0324"
    messages = @(
        @{
            role    = "user"
            content = "Create a Python function to sort a list using merge sort"
        }
    )
    temperature = 0.0  # Deterministic for code
} | ConvertTo-Json

$headers = @{
    "Content-Type"  = "application/json"
    "Authorization" = "Bearer $env:CHUTES_API_KEY"
}

$response = Invoke-WebRequest `
    -Uri $apiUrl `
    -Method POST `
    -Headers $headers `
    -Body $body

$result = $response.Content | ConvertFrom-Json
$generatedCode = $result.choices[0].message.content

Write-Output $generatedCode
```

### Option 4: PowerShell Script for Pipeline Automation

**Save as `codegen.ps1`:**

```powershell
param(
    [Parameter(Mandatory=$true)]
    [string]$Prompt,
    
    [string]$FilePath,
    [string]$OutputFile,
    [string]$SessionId,
    [switch]$Attach,
    [string]$AttachUrl = "http://localhost:4096"
)

$cmd = "opencode run `"$Prompt`""

if ($FilePath -and (Test-Path $FilePath)) {
    $cmd += " -f $FilePath"
}

if ($Attach) {
    $cmd += " --attach $AttachUrl"
}

if ($SessionId) {
    $cmd += " -s $SessionId"
}

$cmd += " -m chutes/deepseek-ai/DeepSeek-V3-0324 --format json"

Write-Host "Executing: $cmd" -ForegroundColor Cyan

$result = Invoke-Expression $cmd | ConvertFrom-Json

$code = $result.choices[0].message.content

if ($OutputFile) {
    $code | Out-File -FilePath $OutputFile -Encoding UTF8
    Write-Host "✓ Code saved to $OutputFile" -ForegroundColor Green
} else {
    Write-Host $code
}

return $code
```

**Usage:**

```powershell
# Single generation
.\codegen.ps1 -Prompt "Create a hash table sorting function" -OutputFile output.ps1

# With file attachment
.\codegen.ps1 `
    -Prompt "Refactor this code for performance" `
    -FilePath .\slowcode.ps1 `
    -OutputFile refactored.ps1 `
    -Attach

# Continue session
.\codegen.ps1 `
    -Prompt "Add logging to this function" `
    -SessionId "abc-123-def" `
    -Attach
```

### Option 5: PowerShell Function (Easy to Use)

**Add to PowerShell profile (`$PROFILE`):**

```powershell
function Generate-Code {
    param(
        [Parameter(Mandatory=$true, ValueFromPipeline=$true)]
        [string]$Prompt,
        
        [alias("f")]
        [string]$File,
        
        [alias("o")]
        [string]$Output,
        
        [alias("a")]
        [switch]$AttachToServer
    )
    
    $args = @("run", $Prompt)
    
    if ($File) { $args += "-f", $File }
    if ($AttachToServer) { $args += "--attach", "http://localhost:4096" }
    
    $args += "-m", "chutes/deepseek-ai/DeepSeek-V3-0324"
    
    $result = & opencode @args --format json | ConvertFrom-Json
    $code = $result.choices[0].message.content
    
    if ($Output) {
        $code | Out-File -FilePath $Output -Encoding UTF8
        Write-Host "✓ Saved to $Output" -ForegroundColor Green
    } else {
        $code
    }
}
```

**Then use it as:**

```powershell
Generate-Code "Write a cmdlet to list all PowerShell processes"

Generate-Code -Prompt "Fix this bug" -File buggy.ps1 -Output fixed.ps1 -AttachToServer
```

### Windows PowerShell Wrapper Fix

If you get the `/bin/sh` error (Windows-specific issue), manually patch it:

```powershell
# Find the wrapper
$wrapperPath = (Get-Command opencode.ps1).Source

# Edit it
$content = Get-Content $wrapperPath

# Replace the problematic line
$content = $content -replace `
    '& "/bin/sh\$exe"', `
    '& "$basedir/node_modules/opencode-ai/node_modules/opencode-windows-x64/bin/opencode.exe"'

Set-Content -Path $wrapperPath -Value $content -Encoding UTF8

Write-Host "✓ OpenCode wrapper fixed" -ForegroundColor Green
```

### Real-World Terminal Example

```powershell
# Start server once
opencode serve --port 4096

# Terminal 2: Batch code generation
$tasks = @(
    "Write a function to parse CSV files",
    "Create a REST API client",
    "Build a file watcher utility"
)

foreach ($task in $tasks) {
    Write-Host "`n[Generating] $task" -ForegroundColor Yellow
    
    opencode run $task `
        --attach http://localhost:4096 `
        -m chutes/deepseek-ai/DeepSeek-V3-0324 `
        --title $task
}
```

### Key PowerShell Advantages

- **No quotes issues:** Use backticks for line continuation (`` ` ``) instead of backslashes
- **Pipeline integration:** Pipe results directly to `Out-File`, `ForEach-Object`, etc.
- **JSON parsing:** `ConvertFrom-Json` for structured output
- **Aliases:** `iwr` instead of `Invoke-WebRequest`, `% instead of `ForEach-Object`
- **Splatting:** Use `@()` for cleaner multi-parameter calls

**Need help setting up the persistent server or want a batch automation script that handles multiple concurrent generations?**

## Human

I don't want to use it as a server

## Assistant

Got it—you want **direct CLI usage without the persistent server**. Here's the stripped-down PowerShell approach:

## OpenCode CLI from PowerShell (No Server)

### Basic Direct Commands

```powershell
# Simple prompt
opencode run "Write a PowerShell function to check disk usage"

# Specify model explicitly
opencode run "Create a TypeScript interface for user data" `
  -m chutes/deepseek-ai/DeepSeek-V3-0324

# Attach a file to analyze
opencode run "Refactor this code for performance" `
  -f ./mycode.ts `
  -m chutes/deepseek-ai/DeepSeek-V3-0324

# Save output to file
opencode run "Generate boilerplate React component" `
  -m chutes/deepseek-ai/DeepSeek-V3-0324 `
  > output.tsx
```

### Environment Variable Setup (One-Time)

```powershell
# Add to PowerShell profile for persistence
Add-Content $PROFILE @"
`$env:CHUTES_API_KEY = "your-api-key"
"@

# Or set it per-session
$env:CHUTES_API_KEY = "your-api-key"
```

### Quick Alias (Optional)

```powershell
# Add to profile for quick access
function oc { opencode run @args -m chutes/deepseek-ai/DeepSeek-V3-0324 }

# Usage:
oc "Write a function to validate URLs"
oc "Fix bugs in this file" -f bug.js > fixed.js
```

That's it—each `opencode run` call is independent, no server running in background. The model boots fresh each time you run it.
