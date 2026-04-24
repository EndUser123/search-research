# Claude Code Isolated Terminal System

[![PowerShell](https://img.shields.io/badge/PowerShell-5.1+-blue.svg)](https://docs.microsoft.com/en-us/powershell/)
[![Claude Code](https://img.shields.io/badge/Claude_Code-Enabled-green.svg)](https://docs.claude.ai/)

This system provides complete configuration isolation for multiple Claude Code terminal instances, allowing you to use different LLM models simultaneously without interference.

## 📋 Table of Contents

- [🚀 Quick Start](#-quick-start)
- [📁 Available Terminals](#-available-terminals)
- [🔒 How Isolation Works](#-how-isolation-works)
- [🛠 Advanced Usage](#-advanced-usage)
- [🔍 Troubleshooting](#-troubleshooting)
- [📚 Technical Details](#-technical-details)

---

## 🚀 Quick Start

### Prerequisites
- PowerShell 5.1 or higher
- Claude Code CLI installed
- LiteLLM proxy running on configured ports

### 1. Initial Setup

Navigate to the isolated terminals directory:
```powershell
cd P:\.claude\proxy\Isolated-Terminals
```

### 2. Create Isolated Configurations

Run the setup script to create all terminal configurations:
```powershell
.\setup-isolated-terminals.ps1
```

**Or manually create configurations:**

```powershell
# Create configuration directories
mkdir "$env:USERPROFILE\.claude\terminal-2"
mkdir "$env:USERPROFILE\.claude\terminal-3"
mkdir "$env:USERPROFILE\.claude\terminal-4"
mkdir "$env:USERPROFILE\.claude\terminal-5"
mkdir "$env:USERPROFILE\.claude\terminal-6"
```

### 3. Launch Terminals

**Launch individual terminals:**
```powershell
.\launch-terminal-2.ps1  # Xiaomi MIMO v2 Flash
.\launch-terminal-3.ps1  # Qwen 3 Coder
.\launch-terminal-4.ps1  # Kat Coder Pro
.\launch-terminal-5.ps1  # Devstral 2512
.\launch-terminal-6.ps1  # Nemotron Nano
```

**Launch all terminals at once:**
```powershell
.\launch-all-isolated-terminals.ps1
```

### 4. Verify Setup

```powershell
# Verify isolation is working
.\verify-isolation.ps1
```

---

## 📁 Available Terminals

| Terminal | Model | Provider | Port | Status |
|----------|-------|----------|------|--------|
| **Terminal 2** | Xiaomi MIMO v2 Flash | OpenRouter | 8787 | ✅ Shared Proxy |
| **Terminal 3** | Qwen 3 Coder | OpenRouter | 8788 | ✅ Dedicated Proxy |
| **Terminal 4** | Kat Coder Pro | OpenRouter | 8789 | ✅ Dedicated Proxy |
| **Terminal 5** | Devstral 2512 | OpenRouter | 8790 | ✅ Dedicated Proxy |
| **Terminal 6** | Nemotron Nano | OpenRouter | 8791 | ✅ Dedicated Proxy |

**Legend:**
- 🔵 **Shared Proxy**: Uses port 8787 with other terminals
- 🟢 **Dedicated Proxy**: Has its own proxy port

---

## 🔒 How Isolation Works

### 🗂️ Configuration Isolation

Each terminal maintains completely separate:
- **Settings File**: `%USERPROFILE%\.claude\terminal-X\settings.json`
- **Session Directory**: `%USERPROFILE%\.claude\terminal-X\sessions\`
- **Profile Name**: Unique `terminal-X` identifier

### 🌍 Environment Variables

Each terminal sets its own environment:
```powershell
$env:CLAUDE_SETTINGS_PATH = "$env:USERPROFILE\.claude\terminal-X\settings.json"
$env:CLAUDE_SESSION_DIR = "$env:USERPROFILE\.claude\terminal-X\sessions\"
$env:CLAUDE_PROFILE = "terminal-X"
$env:ANTHROPIC_BASE_URL = "http://localhost:PORT"
$env:ANTHROPIC_MODEL = "model-name"
```

### 🌐 Network Isolation

- **Shared Proxy**: Terminal 2 uses port 8787
- **Dedicated Proxies**: Terminals 3-6 each have unique ports (8788-8791)
- **No Interference**: Model changes in one terminal don't affect others

---

## 🛠 Advanced Usage

### ⚙️ Custom Terminal Configuration

Edit a terminal's configuration:
```powershell
# Edit terminal 2's settings
code "$env:USERPROFILE\.claude\terminal-2\settings.json"
```

Example settings.json structure:
```json
{
  "env": {
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "your-model-name",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "your-model-name",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "your-model-name"
  }
}
```

### ➕ Adding New Terminals

1. **Create Directory:**
   ```powershell
   mkdir "$env:USERPROFILE\.claude\terminal-7"
   ```

2. **Create Settings:**
   ```powershell
   $settings = @{
     env = @{
       ANTHROPIC_DEFAULT_HAIKU_MODEL = "new-model";
       ANTHROPIC_DEFAULT_SONNET_MODEL = "new-model";
       ANTHROPIC_DEFAULT_OPUS_MODEL = "new-model"
     }
   } | ConvertTo-Json -Depth 10
   $settings | Out-File "$env:USERPROFILE\.claude\terminal-7\settings.json" -Encoding UTF8
   ```

3. **Create Launch Script:**
   Copy and modify an existing `launch-terminal-X.ps1` script.

### 💾 Session Management

Each terminal maintains independent:
- ✅ Conversation history
- ✅ File contexts and associations
- ✅ Project-specific configurations
- ✅ Hook settings and customizations

---

## 🔍 Troubleshooting

### 🚨 Common Issues & Solutions

#### Port Conflicts
```powershell
# Check what's using the ports
netstat -an | findstr ":878"

# Kill process using port 8787
Stop-Process -Id (Get-NetTCPConnection -LocalPort 8787).OwningProcess -Force
```

#### Configuration Not Isolated
```powershell
# Re-run setup
.\setup-isolated-terminals.ps1

# Verify isolation
.\verify-isolation.ps1
```

#### LiteLLM Proxy Issues
- Ensure LiteLLM proxy is running on required ports
- Check proxy configuration matches terminal settings
- Verify API keys are properly configured

### 🧪 Verification Steps

```powershell
# 1. Check configurations exist
Get-ChildItem "$env:USERPROFILE\.claude\terminal-*" -Directory

# 2. Launch terminals and verify models
.\launch-terminal-2.ps1
# In terminal: claude "What model are you using?"

.\launch-terminal-3.ps1
# In terminal: claude "What model are you using?"
# Should show different models
```

---

## 📚 Technical Details

### 🛡️ Isolation Mechanisms

1. **File System Isolation**
   - Separate configuration directories per terminal
   - Independent session storage locations

2. **Environment Isolation**
   - Terminal-specific environment variables
   - No cross-contamination between instances

3. **Process Isolation**
   - Each terminal runs in separate PowerShell process
   - Independent memory and execution contexts

4. **Network Isolation**
   - Dedicated proxy ports prevent interference
   - Separate API endpoints when needed

### 📂 File Structure

```
P:\.claude\proxy\Isolated-Terminals\
├── setup-isolated-terminals.ps1
├── launch-all-isolated-terminals.ps1
├── verify-isolation.ps1
├── launch-terminal-2.ps1
├── launch-terminal-3.ps1
├── launch-terminal-4.ps1
├── launch-terminal-5.ps1
├── launch-terminal-6.ps1
└── README.md

%USERPROFILE%\.claude\
├── terminal-2\
│   ├── settings.json
│   └── sessions\
├── terminal-3\
│   ├── settings.json
│   └── sessions\
└── ...
```

### 🔗 LiteLLM Integration

- **OpenRouter Models**: Access to various LLM providers through OpenRouter API
- **Proxy Configuration**: Configurable endpoints per terminal
- **Fallback Support**: Automatic model fallback on failures

### ⚡ Performance Benefits

- **Zero Interference**: Model changes don't affect other terminals
- **Resource Isolation**: Each terminal manages its own resources
- **Concurrent Usage**: Run multiple models simultaneously
- **Session Persistence**: Independent conversation histories

---

## 📞 Support

For issues or questions:
1. Check the [Troubleshooting](#-troubleshooting) section
2. Run `.\verify-isolation.ps1` to diagnose problems
3. Ensure all prerequisites are installed
4. Check LiteLLM proxy status on configured ports

---

*This system ensures true multi-model isolation, allowing you to work with different AI models simultaneously without any configuration conflicts.*
