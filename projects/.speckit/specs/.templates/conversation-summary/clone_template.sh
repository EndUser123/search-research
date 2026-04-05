#!/bin/bash

# Clone Template Script for Conversation Summary Task Specifications
# Usage: ./clone_template.sh
# Required Environment Variables:
#   TASK_ID - Task identifier (e.g., TSK-TEST-001)
#   TASK_NAME - Human-readable task name (e.g., test-conversation-summary)
#   DATE - Task creation date (e.g., 2025-11-04)
#   SESSION_ID - Session identifier (e.g., test)
#   COMPLEXITY - Complexity level (1-5)
#   PRIORITY - Priority level (Low/Medium/High/Critical)

set -e  # Exit on error
set -u  # Exit on undefined variable

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Validate required environment variables
validate_variables() {
    local missing_vars=()

    if [ -z "${TASK_ID:-}" ]; then
        missing_vars+=("TASK_ID")
    fi

    if [ -z "${TASK_NAME:-}" ]; then
        missing_vars+=("TASK_NAME")
    fi

    if [ -z "${DATE:-}" ]; then
        missing_vars+=("DATE")
    fi

    if [ -z "${SESSION_ID:-}" ]; then
        missing_vars+=("SESSION_ID")
    fi

    if [ -z "${COMPLEXITY:-}" ]; then
        missing_vars+=("COMPLEXITY")
    fi

    if [ -z "${PRIORITY:-}" ]; then
        missing_vars+=("PRIORITY")
    fi

    if [ ${#missing_vars[@]} -gt 0 ]; then
        print_error "Missing required environment variables:"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
        echo ""
        echo "Usage example:"
        echo "  TASK_ID=TSK-TEST-001 \\"
        echo "  TASK_NAME=test-conversation-summary \\"
        echo "  DATE=2025-11-04 \\"
        echo "  SESSION_ID=test \\"
        echo "  COMPLEXITY=3 \\"
        echo "  PRIORITY=High \\"
        echo "  ./clone_template.sh"
        exit 1
    fi

    # Validate COMPLEXITY is a number between 1-5
    if ! [[ "$COMPLEXITY" =~ ^[1-5]$ ]]; then
        print_error "COMPLEXITY must be a number between 1-5"
        exit 1
    fi

    # Validate PRIORITY is one of the allowed values
    if [[ ! "$PRIORITY" =~ ^(Low|Medium|High|Critical)$ ]]; then
        print_error "PRIORITY must be one of: Low, Medium, High, Critical"
        exit 1
    fi
}

# Function to perform placeholder substitution
substitute_placeholders() {
    local source_file="$1"
    local target_file="$2"

    print_info "Processing: $(basename "$source_file")"

    # Use sed to apply all substitutions with [PLACEHOLDER] format
    sed "s/\[TASK_ID\]/$TASK_ID/g; s/\[TASK_NAME\]/$TASK_NAME/g; s/\[DATE\]/$DATE/g; s/\[SESSION_ID\]/$SESSION_ID/g; s/\[COMPLEXITY\]/$COMPLEXITY/g; s/\[PRIORITY\]/$PRIORITY/g" "$source_file" > "$target_file"

    if [ $? -eq 0 ]; then
        print_info "✓ Created: $(basename "$target_file")"
    else
        print_error "✗ Failed to create: $(basename "$target_file")"
        exit 1
    fi
}

# Main cloning logic
clone_templates() {
    # Set default values using SCRIPT_DIR for absolute paths
    TEMPLATE_DIR="${TEMPLATE_DIR:-$SCRIPT_DIR}"

    # Calculate output directory: go up 4 levels from templates to project root, then down to .speckit/specs/
    OUTPUT_DIR="${OUTPUT_DIR:-$SCRIPT_DIR/../../../../.speckit/specs/$TASK_ID-$TASK_NAME}"

    # Resolve to absolute paths
    TEMPLATE_DIR="$(realpath "$TEMPLATE_DIR")"
    OUTPUT_DIR="$(realpath "$OUTPUT_DIR")"

    # Validate template directory exists
    if [ ! -d "$TEMPLATE_DIR" ]; then
        print_error "Template directory not found: $TEMPLATE_DIR"
        exit 1
    fi

    print_info "Template directory: $TEMPLATE_DIR"
    print_info "Output directory: $OUTPUT_DIR"

    # Create output directory structure
    if mkdir -p "$OUTPUT_DIR"; then
        print_info "✓ Created output directory"
    else
        print_error "✗ Failed to create output directory"
        exit 1
    fi

    # Process all template files except README.md and clone_template.sh itself
    for template_file in "$TEMPLATE_DIR"/*.md; do
        # Skip README.md and clone_template.sh
        if [[ "$(basename "$template_file")" == "README.md" ]] || \
           [[ "$(basename "$template_file")" == "clone_template.sh" ]]; then
            continue
        fi

        # Determine target filename
        local target_filename=$(basename "$template_file")
        local target_file="$OUTPUT_DIR/$target_filename"

        # Perform placeholder substitution
        substitute_placeholders "$template_file" "$target_file"
    done

    # Create .metadata file with task information
    local metadata_file="$OUTPUT_DIR/.metadata"
    cat > "$metadata_file" << EOF
# Task Metadata
TASK_ID=$TASK_ID
TASK_NAME=$TASK_NAME
DATE=$DATE
SESSION_ID=$SESSION_ID
COMPLEXITY=$COMPLEXITY
PRIORITY=$PRIORITY
CREATED_AT=$(date -u +"%Y-%m-%d %H:%M:%S UTC")
EOF

    if [ $? -eq 0 ]; then
        print_info "✓ Created .metadata file"
    else
        print_error "✗ Failed to create metadata file"
        exit 1
    fi

    # Create output directory listing
    echo ""
    print_info "Created files:"
    ls -lh "$OUTPUT_DIR" | grep -v "^total" | awk '{print "  - " $9 " (" $5 ")"}'
}

# Validate script is being run from correct location
validate_location() {
    # Check if we're in a git repository and have .speckit directory
    if [ ! -d ".speckit" ]; then
        print_warning "Running from non-standard location (no .speckit directory found)"
        print_warning "Script may not work correctly"
    fi
}

# Main execution
main() {
    print_info "Starting template cloning process..."
    echo ""

    # Validate script location
    validate_location

    # Validate all required variables
    validate_variables

    # Display variables being used
    print_info "Using the following variables:"
    echo "  TASK_ID:      $TASK_ID"
    echo "  TASK_NAME:    $TASK_NAME"
    echo "  DATE:         $DATE"
    echo "  SESSION_ID:   $SESSION_ID"
    echo "  COMPLEXITY:   $COMPLEXITY"
    echo "  PRIORITY:     $PRIORITY"
    echo ""

    # Perform the cloning
    clone_templates

    echo ""
    print_info "✓ Template cloning completed successfully!"
    # Get relative path from current directory for display
    local display_path="$OUTPUT_DIR"
    if [[ "$OUTPUT_DIR" == $(realpath .)/* ]]; then
        display_path="./${OUTPUT_DIR#$(realpath .)/}"
    fi
    print_info "Output directory: $display_path"
}

# Run main function
main "$@"
