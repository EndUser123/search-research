#!/bin/bash
# Verification script for Ralph Loop + Git Worktrees workflow
# This script demonstrates the complete workflow end-to-end

set -e

echo "=================================="
echo "Ralph Loop Worktree Workflow Demo"
echo "=================================="
echo

# Check prerequisites
echo "1. Checking prerequisites..."
if ! command -v git &> /dev/null; then
    echo "❌ Git not found. Please install Git 2.17+"
    exit 1
fi

GIT_VERSION=$(git --version | grep -oE '[0-9]+\.[0-9]+' | head -1)
if [ $(echo "$GIT_VERSION < 2.17" | bc) -eq 1 ]; then
    echo "❌ Git version $GIT_VERSION is too old. Please upgrade to 2.17+"
    exit 1
fi

echo "✅ Git version: $(git --version)"
echo "✅ Prerequisites met"
echo

# Create demo repository
echo "2. Creating demo repository..."
DEMO_DIR="/tmp/ralph-worktree-demo-$$"
mkdir -p "$DEMO_DIR"
cd "$DEMO_DIR"
git init
echo "# Ralph Loop Demo" > README.md
git add README.md
git commit -m "Initial commit"
echo "✅ Created demo repository: $DEMO_DIR"
echo

# Create branches
echo "3. Creating feature branches..."
git checkout -b feature/auth-loop
git checkout -b feature/api-loop
git checkout main
echo "✅ Created branches: feature/auth-loop, feature/api-loop"
echo

# Create worktrees
echo "4. Creating git worktrees..."
git worktree add ../demo-auth feature/auth-loop
git worktree add ../demo-api feature/api-loop
echo "✅ Created worktrees"
git worktree list
echo

# Create terminal-specific plans
echo "5. Creating terminal-specific plans..."

# Plan for auth worktree
cat > ../demo-auth/plan.console_auth.md << 'EOF'
# Feature: Authentication System

## RALPH_STATUS

- EXIT_SIGNAL: false
- completion_indicators: 0
- current_task: TASK-001

## Tasks

- [ ] TASK-001 Design user schema and migration
- [ ] TASK-002 Implement password hashing
- [ ] TASK-003 Create login endpoint
- [ ] TASK-004 Add JWT token handling
- [ ] TASK-005 Write integration tests
- [ ] TASK-006 Verify all tests pass
EOF

# Plan for API worktree
cat > ../demo-api/plan.console_api.md << 'EOF'
# Feature: REST API v2

## RALPH_STATUS

- EXIT_SIGNAL: false
- completion_indicators: 0
- current_task: TASK-001

## Tasks

- [ ] TASK-001 Design API endpoints
- [ ] TASK-002 Implement request validation
- [ ] TASK-003 Add rate limiting
- [ ] TASK-004 Write API tests
- [ ] TASK-005 Verify documentation
EOF

echo "✅ Created plans:"
echo "   - ../demo-auth/plan.console_auth.md"
echo "   - ../demo-api/plan.console_api.md"
echo

# Show directory structure
echo "6. Directory structure:"
tree -L 2 .. || ls -la .. | grep demo
echo

# Explain next steps
echo "7. Next steps:"
echo
echo "   To run loops in parallel:"
echo
echo "   # Terminal 1:"
echo "   cd ../demo-auth"
echo "   export CLAUDE_TERMINAL_ID=console_auth"
echo "   /ralph-loop"
echo
echo "   # Terminal 2:"
echo "   cd ../demo-api"
echo "   export CLAUDE_TERMINAL_ID=console_api"
echo "   /ralph-loop"
echo
echo "   After loops complete, merge branches:"
echo
echo "   cd $DEMO_DIR"
echo "   git merge feature/auth-loop --no-ff -m 'feat: Add authentication (ralph-loop)'"
echo "   git merge feature/api-loop --no-ff -m 'feat: Add API v2 (ralph-loop)'"
echo
echo "   Clean up:"
echo "   git worktree remove ../demo-auth"
echo "   git worktree remove ../demo-api"
echo

# Offer to keep or delete demo
echo "8. Demo setup complete!"
echo
echo "Demo repository: $DEMO_DIR"
echo
echo "Keep for testing or delete with:"
echo "   rm -rf $DEMO_DIR"
echo "   rm -rf ../demo-auth ../demo-api"
echo

read -p "Press Enter to run plan resolution test or Ctrl+C to exit..."

# Test plan resolution
echo
echo "9. Testing plan resolution..."
echo

# Test auth worktree
cd ../demo-auth
echo "Testing auth worktree:"
echo "  Terminal ID: console_auth"
echo "  Plan file: plan.console_auth.md"
if [ -f "plan.console_auth.md" ]; then
    echo "  ✅ Plan file found"
    echo "  Tasks:"
    grep -E "^- \[ \] TASK-" plan.console_auth.md | head -3
    echo "  ..."
else
    echo "  ❌ Plan file not found"
fi
echo

# Test API worktree
cd ../demo-api
echo "Testing API worktree:"
echo "  Terminal ID: console_api"
echo "  Plan file: plan.console_api.md"
if [ -f "plan.console_api.md" ]; then
    echo "  ✅ Plan file found"
    echo "  Tasks:"
    grep -E "^- \[ \] TASK-" plan.console_api.md | head -3
    echo "  ..."
else
    echo "  ❌ Plan file not found"
fi
echo

echo "=================================="
echo "Verification complete!"
echo "=================================="
echo
echo "Summary:"
echo "  ✅ Git worktrees created"
echo "  ✅ Terminal-specific plans created"
echo "  ✅ Plan resolution verified"
echo
echo "Ready to run /ralph-loop in parallel terminals!"
