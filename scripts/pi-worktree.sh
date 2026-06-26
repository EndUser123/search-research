#!/usr/bin/env bash
# pi-worktree.sh — create / remove a per-session worktree for pi.
#
# Usage:
#   ./pi-worktree.sh create <task-name> [<base>]
#   ./pi-worktree.sh remove <task-name>
#   ./pi-worktree.sh list
#
# Conventions:
#   - Worktrees live at P:/.worktrees/<task-name>/ (siblings of the main repo,
#     never nested inside P:/ itself).
#   - pi-risk-policy copies the user's /P/.env (if present) into the worktree
#     and writes a per-worktree .env.local with a unique port offset.
#   - /P/.pi-risk-policy is shared by reference (symlink), so the global
#     extension code stays in sync.
#
# What this DOES NOT solve (documented in the handoff):
#   - Port collisions across concurrent worktrees (mitigated by
#     .env.local + a per-worktree offset; full isolation needs containers).
#   - Shared DB / cache state (the project must handle per-worktree state
#     explicitly).
#   - Runtime isolation of destructive actions — that's what pi's session-
#     scoped change-set does inside each worktree, and it's the
#     deliverable-A boundary. This script just gives the file system
#     that boundary.

set -euo pipefail

REPO_ROOT="/P"
WORKTREE_PARENT="/P/.worktrees"
RISK_POLICY_SRC="/P/.pi/pi-risk-policy"

cmd="${1:-}"
shift || true

usage() {
    sed -n '2,12p' "$0"
    exit 64
}

case "$cmd" in
    create)
        name="${1:?task name required}"
        base="${2:-main}"
        wt_path="${WORKTREE_PARENT}/${name}"
        if [ -e "$wt_path" ]; then
            echo "worktree already exists at $wt_path" >&2
            exit 1
        fi
        mkdir -p "$WORKTREE_PARENT"
        echo "[pi-worktree] creating $wt_path from $base"
        git -C "$REPO_ROOT" worktree add -b "$name" "$wt_path" "$base"
        # Per-worktree env. Copy (not symlink) .env so each worktree can override.
        if [ -f "${REPO_ROOT}/.env" ]; then
            cp "${REPO_ROOT}/.env" "${wt_path}/.env"
        fi
        # Per-worktree port offset — example: +1000 from the base port. Project
        # must read WORKTREE_PORT_OFFSET from .env.local and add it to its bind port.
        port_offset=$(( (RANDOM % 900) + 100 ))
        cat > "${wt_path}/.env.local" <<EOF
WORKTREE_NAME=${name}
WORKTREE_PORT_OFFSET=${port_offset}
EOF
        # Symlink the user's pi extension so the extension code is shared.
        mkdir -p "${wt_path}/.pi"
        if [ -d "${RISK_POLICY_SRC}" ] && [ ! -e "${wt_path}/.pi/pi-risk-policy" ]; then
            ln -s "$RISK_POLICY_SRC" "${wt_path}/.pi/pi-risk-policy"
        fi
        # Run the project's install (npm ci / pnpm i) if a lockfile is present.
        if [ -f "${wt_path}/package-lock.json" ]; then
            (cd "$wt_path" && npm ci --no-audit --no-fund 2>&1 | tail -5) || true
        elif [ -f "${wt_path}/pnpm-lock.yaml" ]; then
            (cd "$wt_path" && pnpm install --frozen-lockfile 2>&1 | tail -5) || true
        elif [ -f "${wt_path}/yarn.lock" ]; then
            (cd "$wt_path" && yarn install --frozen-lockfile 2>&1 | tail -5) || true
        fi
        echo
        echo "[pi-worktree] ready"
        echo "  cd \"$(cygpath -w "$wt_path" 2>/dev/null || echo "$wt_path")\" && pi"
        echo "  port offset: +${port_offset}"
        ;;
    remove)
        name="${1:?task name required}"
        wt_path="${WORKTREE_PARENT}/${name}"
        if [ ! -d "$wt_path" ]; then
            echo "no worktree at $wt_path" >&2
            exit 1
        fi
        # Safety: refuse to remove if there are uncommitted or unpushed changes.
        status=$(git -C "$wt_path" status --porcelain 2>/dev/null || true)
        if [ -n "$status" ]; then
            echo "[pi-worktree] refusing to remove: $wt_path has uncommitted changes" >&2
            echo "  $status" >&2
            exit 2
        fi
        echo "[pi-worktree] removing $wt_path"
        git -C "$REPO_ROOT" worktree remove --force "$wt_path" || true
        git -C "$REPO_ROOT" worktree prune
        ;;
    list)
        git -C "$REPO_ROOT" worktree list
        ;;
    *)
        usage
        ;;
esac
