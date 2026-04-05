#!/bin/bash
set -e
NOTEBOOK_ID="bdfca419-7312-4e21-bc2d-32aab929557f"
REPOS=(
    "DAMO-NLP-SG:Video-LLaMA:https://github.com/DAMO-NLP-SG/Video-LLaMA"
    "microsoft:autogen:https://github.com/microsoft/autogen"
    "langchain-ai:langchain:https://github.com/langchain-ai/langchain"
    "EdgeFirstAI:videostream:https://github.com/EdgeFirstAI/videostream"
    "RustCV:RustCV:https://github.com/RustCV/RustCV"
    "hybridgroup:gocv:https://github.com/hybridgroup/gocv"
)

clone_and_upload() {
    OWNER="$1"
    REPO="$2"
    URL="$3"
    SANITIZED="${OWNER}_${REPO}"
    TEMP_DIR="/c/Users/brsth/AppData/Local/Temp/gitingest_${SANITIZED}"
    NOTEBOOKLM_DIR="$TEMP_DIR/notebooklm"

    echo "=== Processing $OWNER/$REPO ==="

    # Clone
    if [ -d "$TEMP_DIR" ]; then
        echo "Already cloned, skipping"
    else
        git clone --depth=1 --filter=blob:none "$URL" "$TEMP_DIR" 2>&1
    fi

    # Build file list
    mkdir -p "$NOTEBOOKLM_DIR"
    cd "$TEMP_DIR"
    git ls-files -z | grep -zEv '(\.png$|\.jpg$|\.lock$|\.bin$|\.pyc$|__pycache__|\.pytest_cache|node_modules|\.git)' | grep -zv '/\.' | sort > "$NOTEBOOKLM_DIR/file-list.txt"
    FILE_COUNT=$(git ls-files | grep -vE '(\.png$|\.jpg$|\.lock$|\.bin$|\.pyc$|__pycache__|\.pytest_cache|node_modules)' | wc -l)
    echo "Files: $FILE_COUNT"

    # Generate slice
    SLICE="$NOTEBOOKLM_DIR/repo-index-part-1.md"
    cat > "$SLICE" << SLICE_EOF
# $REPO — Repository Index ($OWNER/$REPO)

## Overview
TODO: Add repo-specific description from README.

## Key Files
TODO: List main source files and their purposes.

## Architecture
TODO: Describe key architectural components.

## Full File Inventory ($FILE_COUNT files)
SLICE_EOF
    git ls-files | grep -vE '(\.png$|\.jpg$|\.lock$|\.bin$|\.pyc$|__pycache__|\.pytest_cache|node_modules)' | sort >> "$SLICE"
    echo "" >> "$SLICE"
    echo "---" >> "$SLICE"
    echo "Slice generated from $OWNER/$REPO | $FILE_COUNT files" >> "$SLICE"

    LINES=$(wc -l < "$SLICE")
    echo "Slice: $LINES lines"

    # Upload
    nlm source add "$NOTEBOOK_ID" --file "$SLICE" --wait 2>&1
    echo ""
}

for entry in "${REPOS[@]}"; do
    IFS=':' read -r OWNER REPO URL <<< "$entry"
    clone_and_upload "$OWNER" "$REPO" "$URL" 2>&1
done

echo "=== ALL DONE ==="
