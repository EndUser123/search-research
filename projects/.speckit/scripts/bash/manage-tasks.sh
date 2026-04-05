#!/bin/bash
# Task management utility for speckit framework
set -euo pipefail

# Default values
ACTION=""
TITLE=""
DESCRIPTION=""
TASK_ID=""
JSON_OUTPUT=false
SHOW_HELP=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --list|-l)
            ACTION="list"
            shift
            ;;
        --add|-a)
            ACTION="add"
            TITLE="$2"
            shift 2
            ;;
        --complete|-c)
            ACTION="complete"
            TASK_ID="$2"
            shift 2
            ;;
        --show|-s)
            ACTION="show"
            TASK_ID="$2"
            shift 2
            ;;
        --json)
            JSON_OUTPUT=true
            shift
            ;;
        --help|-h)
            SHOW_HELP=true
            shift
            ;;
        *)
            if [[ "$ACTION" == "add" && -n "$TITLE" ]]; then
                DESCRIPTION="$DESCRIPTION $1"
            fi
            shift
            ;;
    esac
done

# Show help if requested
if [[ "$SHOW_HELP" == "true" || -z "$ACTION" ]]; then
    echo "Usage: ./manage-tasks.sh [ACTION] [OPTIONS]"
    echo ""
    echo "Actions:"
    echo "  --list, -l                 List all active tasks"
    echo "  --add, -a <title>          Add new task (following arguments become description)"
    echo "  --complete, -c <task-id>   Mark task as completed"
    echo "  --show, -s <task-id>       Show task details"
    echo ""
    echo "Options:"
    echo "  --json                     Output in JSON format"
    echo "  --help, -h                 Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./manage-tasks.sh --list"
    echo "  ./manage-tasks.sh --add 'Implement user auth' 'Add OAuth2 integration'"
    echo "  ./manage-tasks.sh --complete TSK-001"
    exit 0
fi

# Get script directory and paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
ACTIVE_TASKS_PATH="$BASE_DIR/cache/active_tasks.json"
COMPLETED_TASKS_PATH="$BASE_DIR/cache/completed_tasks.json"

# Function to read tasks
get_tasks() {
    local path="$1"
    if [[ -f "$path" ]]; then
        jq -r '.active_tasks // .completed_tasks // []' "$path"
    else
        echo "[]"
    fi
}

# Function to save tasks
save_tasks() {
    local path="$1"
    local tasks="$2"
    local type="$3"

    local data=$(jq -n \
        --argjson tasks "$tasks" \
        --arg type "${type}_tasks" \
        --arg created "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
        --arg version "2.0.0" \
        '{
            ($type): $tasks,
            metadata: {
                created: $created,
                last_updated: $created,
                version: $version,
                total_tasks: ($tasks | length)
            }
        }')
    echo "$data" > "$path"
}

# List tasks
if [[ "$ACTION" == "list" ]]; then
    tasks=$(get_tasks "$ACTIVE_TASKS_PATH")

    if [[ "$JSON_OUTPUT" == "true" ]]; then
        echo "$tasks"
    else
        count=$(echo "$tasks" | jq 'length')
        if [[ "$count" -eq 0 ]]; then
            echo "No active tasks found."
        else
            echo "Active Tasks:"
            echo "$tasks" | jq -r '.[] | "  \(.id): \(.title)"' | while IFS= read -r line; do
                echo "$line"
            done
        fi
    fi
    exit 0
fi

# Add task
if [[ "$ACTION" == "add" ]]; then
    if [[ -z "$TITLE" ]]; then
        echo "Error: Title is required for add action" >&2
        exit 1
    fi

    # Generate new task ID
    generate_script="$SCRIPT_DIR/generate-task-id.sh"
    task_id_result=$("$generate_script" --increment --json)
    task_id=$(echo "$task_id_result" | jq -r '.task_id')

    # Create task object
    task=$(jq -n \
        --arg id "$task_id" \
        --arg title "$TITLE" \
        --arg description "${DESCRIPTION## }" \
        --arg created "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
        '{
            id: $id,
            title: $title,
            description: $description,
            status: "active",
            created: $created,
            updated: $created
        }')

    # Load existing tasks
    existing_tasks=$(get_tasks "$ACTIVE_TASKS_PATH")
    updated_tasks=$(echo "$existing_tasks" | jq ". + [$task]")

    # Save tasks
    save_tasks "$ACTIVE_TASKS_PATH" "$updated_tasks" "active"

    if [[ "$JSON_OUTPUT" == "true" ]]; then
        echo "$task"
    else
        id=$(echo "$task" | jq -r '.id')
        title=$(echo "$task" | jq -r '.title')
        echo "Task created: $id - $title"
    fi
    exit 0
fi

# Complete task
if [[ "$ACTION" == "complete" ]]; then
    if [[ -z "$TASK_ID" ]]; then
        echo "Error: Task ID is required for complete action" >&2
        exit 1
    fi

    active_tasks=$(get_tasks "$ACTIVE_TASKS_PATH")
    task_to_complete=$(echo "$active_tasks" | jq ".[] | select(.id == \"$TASK_ID\")")

    if [[ -z "$task_to_complete" || "$task_to_complete" == "null" ]]; then
        echo "Error: Task not found: $TASK_ID" >&2
        exit 1
    fi

    # Remove from active tasks
    updated_active_tasks=$(echo "$active_tasks" | jq ".[] | select(.id != \"$TASK_ID\")")
    save_tasks "$ACTIVE_TASKS_PATH" "$updated_active_tasks" "active"

    # Add to completed tasks
    completed_task=$(echo "$task_to_complete" | jq \
        --arg completed "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
        '.status = "completed" | .completed = $completed | .updated = $completed')

    completed_tasks=$(get_tasks "$COMPLETED_TASKS_PATH")
    updated_completed_tasks=$(echo "$completed_tasks" | jq ". + [$completed_task]")
    save_tasks "$COMPLETED_TASKS_PATH" "$updated_completed_tasks" "completed"

    if [[ "$JSON_OUTPUT" == "true" ]]; then
        echo "$completed_task"
    else
        id=$(echo "$completed_task" | jq -r '.id')
        title=$(echo "$completed_task" | jq -r '.title')
        echo "Task completed: $id - $title"
    fi
    exit 0
fi

# Show task details
if [[ "$ACTION" == "show" ]]; then
    if [[ -z "$TASK_ID" ]]; then
        echo "Error: Task ID is required for show action" >&2
        exit 1
    fi

    active_tasks=$(get_tasks "$ACTIVE_TASKS_PATH")
    completed_tasks=$(get_tasks "$COMPLETED_TASKS_PATH")
    all_tasks=$(echo "$active_tasks $completed_tasks" | jq -s 'add')
    task=$(echo "$all_tasks" | jq ".[] | select(.id == \"$TASK_ID\")")

    if [[ -z "$task" || "$task" == "null" ]]; then
        echo "Error: Task not found: $TASK_ID" >&2
        exit 1
    fi

    if [[ "$JSON_OUTPUT" == "true" ]]; then
        echo "$task"
    else
        echo "Task: $(echo "$task" | jq -r '.id')"
        echo "Title: $(echo "$task" | jq -r '.title')"
        description=$(echo "$task" | jq -r '.description')
        if [[ "$description" != "null" && "$description" != "" ]]; then
            echo "Description: $description"
        fi
        echo "Status: $(echo "$task" | jq -r '.status')"
        echo "Created: $(echo "$task" | jq -r '.created')"
        completed=$(echo "$task" | jq -r '.completed // empty')
        if [[ "$completed" != "" ]]; then
            echo "Completed: $completed"
        fi
    fi
    exit 0
fi

echo "Error: Invalid action" >&2
exit 1
