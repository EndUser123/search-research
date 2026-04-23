#!/bin/bash
# Bash script to start claude-code-proxy with secure credentials
# Usage: ./start-proxy.sh [terminal-number]
# Example: ./start-proxy.sh 1  (starts Terminal 1 on port 3001)

set -e

# Default terminal
TERMINAL=${1:-1}

# Validate terminal number (1-10)
if ! [[ "$TERMINAL" =~ ^[1-9]$|^10$ ]]; then
    echo "Error: Terminal number must be between 1 and 10"
    echo "Usage: $0 [terminal-number]"
    exit 1
fi

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Config file based on terminal number
CONFIG_FILE="$SCRIPT_DIR/config-terminal${TERMINAL}.yaml"

# Verify config file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Config file not found: $CONFIG_FILE"
    echo "Available terminals: 1-10"
    echo "Create config files using: cp config.yaml.example config-terminal[N].yaml"
    exit 1
fi

# Load credentials from Windows Credential Manager (via Python)
echo "Loading credentials from Windows Credential Manager..."

OPENAI_KEY=$(python "P:/packages/.mcp/claude-code-proxy/credential_manager.py" get OPENAI_API_KEY 2>/dev/null || echo "")
OPENROUTER_KEY=$(python "P:/packages/.mcp/claude-code-proxy/credential_manager.py" get OPENROUTER_API_KEY 2>/dev/null || echo "")
MINIMAX_KEY=$(python "P:/packages/.mcp/claude-code-proxy/credential_manager.py" get MINIMAX_API_KEY 2>/dev/null || echo "")

if [ -n "$OPENAI_KEY" ]; then
    export OPENAI_API_KEY="$OPENAI_KEY"
    echo "  OPENAI_API_KEY loaded"
else
    echo "  Warning: OPENAI_API_KEY not found in credential manager"
fi

if [ -n "$OPENROUTER_KEY" ]; then
    export OPENROUTER_API_KEY="$OPENROUTER_KEY"
    echo "  OPENROUTER_API_KEY loaded"
else
    echo "  Warning: OPENROUTER_API_KEY not found in credential manager"
fi

if [ -n "$MINIMAX_KEY" ]; then
    export MINIMAX_API_KEY="$MINIMAX_KEY"
    echo "  MINIMAX_API_KEY loaded"
else
    echo "  Warning: MINIMAX_API_KEY not found in credential manager"
fi

# Set ANTHROPIC_BASE_URL to route through proxy
# Main orchestrator stays on Anthropic, subagents route to configured providers
export ANTHROPIC_BASE_URL="http://localhost:300${TERMINAL}"

echo ""
echo "Starting claude-code-proxy Terminal ${TERMINAL}..."
echo "  Config: ${CONFIG_FILE}"
echo "  ANTHROPIC_BASE_URL: ${ANTHROPIC_BASE_URL}"
echo ""

# Start the proxy (Go executable)
PROXY_EXE="$SCRIPT_DIR/proxy/claude-code-proxy.exe"

if [ ! -f "$PROXY_EXE" ]; then
    echo "Error: Proxy executable not found: $PROXY_EXE"
    echo "Build the proxy first: cd proxy && go build -o claude-code-proxy.exe ./cmd/proxy"
    exit 1
fi

"$PROXY_EXE" --config "$CONFIG_FILE"
