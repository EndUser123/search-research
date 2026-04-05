#!/bin/bash
set -e
REPO_DIR="/c/Users/brsth/AppData/Local/Temp/gitingest_mbzuai-oryx_Video-LLaVA"  # pragma: allowlist secret
NOTEBOOKLM_DIR="$REPO_DIR/notebooklm"
mkdir -p "$NOTEBOOKLM_DIR"
cd "$REPO_DIR"
git ls-files -z | grep -zEv '(\.png$|\.jpg$|\.lock$|\.bin$|\.pyc$|__pycache__|\.pytest_cache|node_modules|\.git)' | grep -zv '/\.' | sort > "$NOTEBOOKLM_DIR/file-list.txt"
echo "File count: $(wc -l < $NOTEBOOKLM_DIR/file-list.txt)"
echo "Sample files:" && head -20 "$NOTEBOOKLM_DIR/file-list.txt"
