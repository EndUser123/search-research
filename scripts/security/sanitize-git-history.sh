#!/bin/bash
# Git History Sanitization Script
# WARNING: This rewrites git history. Backup first!

set -e

echo "⚠️  GIT HISTORY SANITIZATION"
echo "This will IRREVERSIBLY rewrite git history to remove .env files"
echo ""
read -p "Have you backed up your repository? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Aborted. Please backup first:"
    echo "   git clone --mirror P:/ P:/backup.git"
    exit 1
fi

echo ""
echo "🔒 Step 1: Analyzing what will be removed..."
git log --all --full-history --oneline -- "**/.env" | head -20

echo ""
read -p "Continue with sanitization? (yes/no): " proceed

if [ "$proceed" != "yes" ]; then
    echo "❌ Aborted."
    exit 1
fi

echo ""
echo "🧹 Step 2: Creating backup branch..."
git branch backup-before-sanitization $(git rev-parse HEAD)

echo ""
echo "🔥 Step 3: Removing .env files from history..."
git-filter-repo --invert-paths --path '**/.env' --path '**/*.env' --force

echo ""
echo "✅ Step 4: Cleanup complete!"
echo ""
echo "⚠️  IMPORTANT: Force push required to update remote:"
echo ""
echo "   git push origin --force --all"
echo "   git push origin --force --tags"
echo ""
echo "📋 Notify all collaborators to clone fresh copies:"
echo "   git clone https://github.com/EndUser123/P.git P-clean"
echo ""

read -p "Force push now? (yes/no): " push_confirm

if [ "$push_confirm" = "yes" ]; then
    echo "🚀 Pushing sanitized history..."
    git push origin --force --all
    git push origin --force --tags
    echo "✅ Remote repository sanitized!"
else
    echo "⏸️  Sanitized locally only. Force push when ready."
fi

echo ""
echo "✨ Sanitization complete!"
echo "   Backup branch: backup-before-sanitization"
echo "   Verify: git log --all --full-history -- '**/.env'  (should be empty)"
