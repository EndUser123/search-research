#!/bin/bash
# Generate next task ID in TSK-### format
set -euo pipefail

# Default values
JSON_OUTPUT=false
INCREMENT=false
SHOW_HELP=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --json)
            JSON_OUTPUT=true
            shift
            ;;
        --increment)
            INCREMENT=true
            shift
            ;;
        --help|-h)
            SHOW_HELP=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Show help if requested
if [[ "$SHOW_HELP" == "true" ]]; then
    echo "Usage: ./generate-task-id.sh [--json] [--increment]"
    echo ""
    echo "Options:"
    echo "  --json       Output in JSON format"
    echo "  --increment  Increment the global counter"
    echo "  --help, -h   Show this help message"
    exit 0
fi

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_PATH="$(dirname "$(dirname "$SCRIPT_DIR")")/config/speckit_config.json"

# Check if config exists
if [[ ! -f "$CONFIG_PATH" ]]; then
    echo "Error: Configuration file not found: $CONFIG_PATH" >&2
    exit 1
fi

# Read configuration
CURRENT_ID=$(jq -r '.task_management.global_counter.current_id' "$CONFIG_PATH")
PREFIX=$(jq -r '.task_management.global_counter.prefix' "$CONFIG_PATH")
FORMAT=$(jq -r '.task_management.global_counter.format' "$CONFIG_PATH")

# Generate task ID
TASK_ID=$(printf "$FORMAT" "$CURRENT_ID")

# Increment counter if requested
if [[ "$INCREMENT" == "true" ]]; then
    NEW_ID=$((CURRENT_ID + 1))
    jq ".task_management.global_counter.current_id = $NEW_ID" "$CONFIG_PATH" > "${CONFIG_PATH}.tmp"
    mv "${CONFIG_PATH}.tmp" "$CONFIG_PATH"
fi

# Output result
if [[ "$JSON_OUTPUT" == "true" ]]; then
    jq -n \
        --arg task_id "$TASK_ID" \
        --arg current_id "$CURRENT_ID" \
        --arg incremented "$INCREMENT" \
        --arg prefix "$PREFIX" \
        --arg format "$FORMAT" \
        '{
            task_id: $task_id,
            current_id: ($current_id | tonumber),
            incremented: ($incremented == "true"),
            prefix: $prefix,
            format: $format
        }'
else
    echo "$TASK_ID"
fi
