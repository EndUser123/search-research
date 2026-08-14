---
title: "for github gh cli, how can I use it in an automated way (non-interactive), and what can I use it for?"
date: "2025-12-31"
mode: "COPILOT"
uuid: "66ffc953-24aa-4a71-9cfd-bfa76882ea24"
entry_count: 3
---

## Human

for github gh cli, how can I use it in an automated way (non-interactive), and what can I use it for?

## Assistant

Perfect. I have comprehensive information. Let me compile this into a detailed report.

## GitHub CLI (`gh`) for Non-Interactive Automation

GitHub CLI is fundamentally designed for automation and can operate in fully non-interactive mode when properly configured. Here's how to leverage it effectively for scripted workflows.

### Authentication for Automation

Non-interactive authentication is the foundation of automated `gh` usage. There are two primary methods:

**Environment Variable Method (Recommended)**

Set the `GH_TOKEN` environment variable with a Personal Access Token (PAT) before running any `gh` commands:[1]

```powershell
$env:GH_TOKEN = "ghp_your_token_here"
gh auth status
```

This is the cleanest approach for CI/CD, scheduled tasks, or containerized environments. The token is automatically detected and used without any prompts.[1]

**Token via stdin**

For one-off automation:

```powershell
"ghp_your_token_here" | gh auth login --with-token
```

**Token Scopes Required**

Ensure your PAT has these minimum scopes:[1]
- `repo` (full repository access)
- `read:org` (read organization data)
- `gist` (gist management)

For fine-grained PATs, consider using environment variables rather than stdin to avoid scoping issues.[1]

### Non-Interactive Mode Behavior

When `gh` detects non-interactive execution (piped output, no terminal), it automatically:[2]
- Disables all interactive prompts
- Outputs tab-delimited format for machine readability
- Removes text truncation
- Strips color codes and escape sequences
- Supports pagination with `--paginate` flag

**Key Pattern**: Provide explicit flags to eliminate prompts. For example:[3]

```powershell
# Interactive: prompts for merge method
gh pr merge 123

# Non-interactive: explicit flags prevent prompts
gh pr merge 123 --merge
```

Common flag patterns:
- `--merge`, `--rebase`, `--squash` (merge strategy)
- `--delete-branch` (remove after merge)
- `--yes` (skip confirmation)
- `-y` (shorthand)

### Core Automation Use Cases

**Repository Management**

Bulk operations across multiple repositories:[4]

```powershell
# List all repos
gh repo list $owner --limit 1000 --json nameWithOwner --jq '.[].nameWithOwner'

# Delete multiple repos
gh repo list $owner | cut -f1 | xargs -I {} gh repo delete {} --yes

# Change visibility across repos
$repos | ForEach-Object {
    gh repo edit $_ --visibility private
}
```

**Pull Request Automation**

```powershell
# Create PR with auto-merge enabled
gh pr create --title "Automated PR" --body "Content" --auto-merge

# List and process PRs programmatically
gh pr list --state open --json number,title --jq '.[] | "\(.number): \(.title)"'

# Merge all PRs meeting criteria
gh pr list --state open | Where-Object { $_ -match "ready" } | ForEach-Object {
    gh pr merge (($_ -split '\s+')[0]) --squash
}
```

**Issue and Project Management**

```powershell
# Bulk label issues
gh issue list --state open --label "needs-review" --json number | 
  ForEach-Object { gh issue edit $_ --add-label "urgent" }

# Add issues to projects
$project_id = gh project view 5 --owner $org --format json | jq -r '.id'
gh project item-add $project_id --id $issue_id
```

**GitHub Actions Orchestration**

Trigger and monitor workflows:[5]

```powershell
# Trigger workflow manually
gh workflow run "build.yml" -f environment=production

# List workflow runs
gh run list --json databaseId,status,conclusion

# Monitor and retrieve artifacts
gh run view $run_id --json jobs
gh run download $run_id --dir ./artifacts
```

**Bulk Artifact Cleanup**

A practical example combining multiple capabilities:[6]

```powershell
# Get all repos with access, delete artifacts
$repos = gh api "/user/repos?affiliation=owner,collaborator" --paginate |
  jq -r '.[] | select(.permissions.push == true) | .full_name'

foreach ($repo in $repos) {
    $artifacts = gh api "/repos/$repo/actions/artifacts" --paginate | 
      jq -r '.artifacts[].id'
    
    $artifacts | ForEach-Object {
        gh api -X DELETE "/repos/$repo/actions/artifacts/$_"
        Start-Sleep -Seconds 1  # Rate limiting
    }
}
```

### JSON Output and Data Processing

The `gh api` command provides raw, structured output ideal for scripting:[2]

```powershell
# Query GraphQL with jq filtering
gh api graphql -f query='
  query($owner: String!, $name: String!) {
    repository(owner: $owner, name: $name) {
      issues(states:OPEN) { totalCount }
    }
  }
' -F owner=myorg -F name=myrepo --jq '.data.repository.issues.totalCount'

# Pagination with caching
gh api -X GET 'orgs/myorg/teams/myteam/members' \
  -F per_page=100 --paginate --cache 1h --jq '.[].login'
```

Key flags for data manipulation:[7]
- `--jq '<filter>'` - Apply jq expressions to transform JSON
- `--paginate` - Automatically handle pagination
- `--cache <duration>` - Cache responses (e.g., `1h`, `10m`)
- `-f <field>=<value>` - Pass JSON fields
- `-F <field>=<value>` - Pass variables

### Integration with GitHub Actions

`gh` is pre-installed in Actions environments and works with automatic token injection:[8][9]

```yaml
jobs:
  automate:
    runs-on: ubuntu-latest
    steps:
      - name: Enable auto-merge for PRs
        run: gh pr merge --auto --merge "${{ github.event.pull_request.html_url }}"
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Report issues using GraphQL
        run: |
          numOpenIssues=$(gh api graphql -f owner=$OWNER -f name=$REPO \
            -f query='query($owner: String!, $name: String!) {
              repository(owner: $owner, name: $name) {
                issues(states:OPEN) { totalCount }
              }
            }' --jq '.data.repository.issues.totalCount')
          echo "Open issues: $numOpenIssues"
```

### PowerShell-Specific Patterns

Given your Windows 11 + PowerShell expertise, here are optimized patterns:[4]

```powershell
# Batch processing with concurrency
$repos | ForEach-Object -Parallel {
    gh repo edit $_ --visibility private
} -ThrottleLimit 5

# Error handling
try {
    $result = gh pr merge 123 --squash --error-handling continue
    if ($LASTEXITCODE -ne 0) {
        Write-Error "PR merge failed: $result"
    }
} catch {
    Write-Error "Exception: $_"
}

# Output to CSV for audit trails
gh api "/user/repos" --paginate | 
  jq '.[] | {name: .name, visibility: .visibility, updated_at: .updated_at}' |
  ConvertFrom-Json |
  Export-Csv "repos.csv" -NoTypeInformation
```

### Rate Limiting and Performance

For bulk operations:[6]

- Add `Start-Sleep -Milliseconds 100` between requests to stay within rate limits (5,000 requests/hour for authenticated users)
- Use `--cache` on repeated queries
- Batch operations with `xargs` or `ForEach-Object -Parallel`
- Use GraphQL instead of REST where possible (more efficient)

### Safety Guardrails

For automation contexts with AI agents or scheduled tasks:[10]
- Never auto-merge without approval checks
- Require confirmation for destructive operations (delete, force-push)
- Log all executed commands before running
- Use read-only tokens when possible
- Implement approval gates for critical repositories

The GitHub CLI transforms repository management from manual browser-based work into scalable, programmatic workflows—particularly powerful when combined with PowerShell's scripting capabilities for multi-step operations across repositories.

## Human

what are some popular uses with working examples?

## Assistant

Perfect. Now I have comprehensive working examples. Let me compile this into a detailed practical guide with working code examples.

## Popular `gh` Use Cases with Working Examples

Based on your PowerShell + Windows 11 workflow, here are the most practical automation scenarios with fully functional examples you can adapt immediately.

### 1. Bulk Delete Old Repositories

This is the most common cleanup task. The script reads a file with repo names and deletes them all without interactive prompts.[1][2]

**Setup:**
```powershell
# Generate list of repos to delete (review manually first!)
gh repo list myuser --public --json name --jq '.[].name' -L 9999 > repos_to_delete.txt

# Edit repos_to_delete.txt to remove any repos you want to keep
notepad repos_to_delete.txt
```

**PowerShell deletion script:**
```powershell
# delete_repos.ps1
param([string]$RepoFile = "repos_to_delete.txt")

if (-not (Test-Path $RepoFile)) {
    Write-Error "File $RepoFile not found"
    exit 1
}

Write-Host "Starting deletion process. This is IRREVERSIBLE!" -ForegroundColor Red
@"
⚠️  WARNING: Deleting repositories permanently.
⚠️  This cannot be undone.
⚠️  Last chance to cancel (Ctrl+C in next 10 seconds)...
"@ | Write-Host -ForegroundColor Yellow

Start-Sleep -Seconds 10

$repos = Get-Content $RepoFile | Where-Object { $_ -ne "" }
$deleted = 0
$failed = 0

foreach ($repo in $repos) {
    Write-Host "Deleting $repo..." -ForegroundColor Cyan
    
    try {
        gh repo delete $repo --confirm
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Deleted $repo" -ForegroundColor Green
            $deleted++
        } else {
            Write-Host "❌ Failed to delete $repo" -ForegroundColor Red
            $failed++
        }
    } catch {
        Write-Host "❌ Exception deleting $repo: $_" -ForegroundColor Red
        $failed++
    }
    
    Start-Sleep -Milliseconds 500  # Rate limiting
}

Write-Host "`nSummary: $deleted deleted, $failed failed" -ForegroundColor Cyan
```

Run with: `.\delete_repos.ps1`[1]

***

### 2. Bulk Delete GitHub Actions Artifacts

Free GitHub accounts get only 500MB storage—artifacts accumulate fast. This cleans them all.[3]

```powershell
# Get all repos with write access
$repos = gh api "/user/repos?affiliation=owner,collaborator" --paginate | 
    ConvertFrom-Json | 
    Where-Object { $_.permissions.push -eq $true } | 
    Select-Object -ExpandProperty full_name

foreach ($repo in $repos) {
    Write-Host "Processing $repo..." -ForegroundColor Cyan
    
    # Get artifact IDs
    $artifacts = gh api "/repos/$repo/actions/artifacts" --paginate | 
        ConvertFrom-Json | 
        Select-Object -ExpandProperty artifacts
    
    if ($artifacts.Count -eq 0) {
        Write-Host "  No artifacts"
        continue
    }
    
    Write-Host "  Found $($artifacts.Count) artifacts, deleting..."
    
    foreach ($artifact in $artifacts) {
        gh api -X DELETE "/repos/$repo/actions/artifacts/$($artifact.id)"
        Start-Sleep -Milliseconds 100
    }
}

Write-Host "Artifact cleanup complete" -ForegroundColor Green
```

This deletes artifacts across all your repos automatically.[4][3]

***

### 3. Automated Release Creation with Generated Notes

Create releases on every tag push with auto-generated changelogs from PR titles and commits.[5][6]

**GitHub Actions workflow (.github/workflows/release.yml):**
```yaml
name: Create Release

on:
  push:
    tags:
      - v*

permissions:
  contents: write

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - name: Create release with auto-generated notes
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          TAG: ${{ github.ref_name }}
        run: |
          gh release create "$TAG" \
            --repo="$GITHUB_REPOSITORY" \
            --title="${GITHUB_REPOSITORY#*/} $TAG" \
            --generate-notes
```

Push a tag and the release auto-generates from commit history:[7][5]
```powershell
git tag v1.2.3
git push origin v1.2.3
# Release automatically created!
```

**Manual release with pre-built artifacts:**
```powershell
# Generate release notes first
$notes = gh api repos/myuser/myrepo/releases/generate-notes `
    -f tag_name=v1.2.3 --jq '.body'

# Create release with assets
gh release create v1.2.3 `
    --title "Version 1.2.3" `
    --notes "$notes" `
    ./dist/*.zip
```

***

### 4. Auto-Merge PRs After CI Passes

Automatically merge PRs once tests pass—perfect for Dependabot or automated workflows.[8][9][10]

**GitHub Actions workflow:**
```yaml
name: Auto-Merge PR

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  auto-merge:
    runs-on: ubuntu-latest
    steps:
      - name: Enable auto-merge if checks pass
        if: github.event.pull_request.draft == false
        run: |
          gh pr merge --auto --squash \
            "${{ github.event.pull_request.html_url }}"
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

Or from the CLI directly:[11][10]
```powershell
# Merge PR #42 once all checks pass (squash commits)
gh pr merge 42 --auto --squash --delete-branch

# Alternative: merge immediately with rebase
gh pr merge 42 --rebase --delete-branch
```

**Real-world example—auto-merge Dependabot patches:**
```yaml
name: Dependabot Auto-Merge

on: pull_request

jobs:
  auto-merge:
    if: github.event.pull_request.user.login == 'dependabot[bot]'
    runs-on: ubuntu-latest
    steps:
      - name: Enable auto-merge for patch updates
        run: |
          gh pr merge --auto --squash \
            "${{ github.event.pull_request.html_url }}"
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

***

### 5. Bulk Add Labels to Issues/PRs

Loop through filtered items and apply labels programmatically.[12]

```powershell
# Add 'urgent' label to all open issues with 'bug' label
$issues = gh issue list --state open --label "bug" --json number | 
    ConvertFrom-Json

foreach ($issue in $issues) {
    Write-Host "Adding label to issue #$($issue.number)..."
    gh issue edit $issue.number --add-label "urgent"
    Start-Sleep -Milliseconds 200
}

# Or with PRs
gh pr list --state open --json number | ConvertFrom-Json | ForEach-Object {
    gh pr edit $_.number --add-label "needs-review"
}
```

***

### 6. Sync Fork with Upstream

Keep your fork up-to-date with the original repo in one command.[13][14]

```powershell
# Sync fork's main branch with upstream
gh repo sync owner/cli-fork -b main

# Or with --force to overwrite conflicting branches
gh repo sync owner/cli-fork -b main --force
```

This is much simpler than managing git remotes manually.[13]

***

### 7. Clean Up Old Workflow Runs

Delete old CI/CD runs to free storage and declutter the UI.[15]

```powershell
# Delete all workflow runs from a repo
$runs = gh run list --json databaseId -q '.[].databaseId'

foreach ($run in $runs) {
    gh api -X DELETE "repos/$(gh repo view --json nameWithOwner -q .nameWithOwner)/actions/runs/$run"
    Start-Sleep -Milliseconds 100
}

# Or filter by status before deleting
gh run list --status failure --json databaseId -q '.[].databaseId' |
    ForEach-Object {
        gh api -X DELETE "repos/myuser/myrepo/actions/runs/$_"
    }
```

***

### 8. Prune Old Actions Cache

Delete cached builds older than a specific date.[16]

```powershell
# Delete all caches last accessed before 2024-12-01
$caches = gh cache list -R myuser/myrepo | 
    Where-Object { $_[4] -lt "2024-12-01" }

$caches | ForEach-Object {
    $cacheId = ($_ -split '\s+')[1]
    gh cache delete -R myuser/myrepo $cacheId
}
```

Or use the built-in alias approach:[16]
```powershell
# Set alias (one-time)
gh alias set --shell 'cache prune' 'gh cache list -R "$1" | Where-Object { $_.Split()[4] -lt "$2" } | ForEach-Object { gh cache delete -R "$1" $_.Split()[1] }'

# Use it
gh cache prune myuser/myrepo 2024-12-01
```

***

### 9. List and Checkout PRs from Forks

Review external contributor PRs locally without adding remotes.[17]

```powershell
# List all open PRs (including forks)
gh pr list --state open --json number,author,title

# Checkout PR #15 locally (even from a fork!)
gh pr checkout 15

# Make comments or test locally, then switch back
git checkout main
```

***

### 10. Generate Bulk Reports with `gh api`

Query GitHub GraphQL for custom reporting.[18][19]

```powershell
# Get all open issues across repos with their labels
$query = @'
query($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    issues(states: OPEN, first: 100) {
      nodes {
        number
        title
        labels(first: 5) {
          nodes {
            name
          }
        }
      }
    }
  }
}
'@

$result = gh api graphql -f owner="myuser" -f name="myrepo" -f query="$query"
$result | ConvertFrom-Json | 
    Select-Object -ExpandProperty data | 
    Select-Object -ExpandProperty repository | 
    Select-Object -ExpandProperty issues | 
    Select-Object -ExpandProperty nodes | 
    ConvertTo-Json | 
    Out-File "issues_report.json"
```

***

### Key Patterns for Your Setup

Given your multi-terminal workflow with Claude instances, these patterns work well in scripts:

**Error handling & logging:**
```powershell
$ErrorActionPreference = "Continue"
$logfile = "gh-automation-$(Get-Date -Format 'yyyyMMdd-HHmmss').log"

function Log-Op($message) {
    $msg = "$(Get-Date -Format 'HH:mm:ss') - $message"
    Write-Host $msg
    Add-Content $logfile $msg
}

Log-Op "Starting bulk operations..."
try {
    # gh operations here
} catch {
    Log-Op "ERROR: $_"
}
```

**Parallel execution (safe for read operations):**
```powershell
# Get repos in parallel (respects rate limits)
$repos | ForEach-Object -Parallel {
    gh repo view $_ --json nameWithOwner,isArchived
} -ThrottleLimit 5
```

**Rate limiting protection:**
```powershell
$delay_ms = 100  # Adjust based on API limits
$rate_limit = gh api rate_limit --jq '.rate.remaining'
if ($rate_limit -lt 100) {
    Write-Warning "Approaching rate limit: $rate_limit requests remaining"
    Start-Sleep -Seconds 60
}
```

These examples directly integrate with your Claude Code workflows—you can save them as `.ps1` scripts and invoke them from your multi-agent system with full token access and error tracking.[10][20][5][7]

## Human

Can it do research or bug fixing or feature implementation?

## Assistant

## GitHub CLI for Research, Bug Fixing, and Feature Implementation

Short answer: **`gh` alone cannot generate code, but it excels as an orchestration layer that can be integrated with AI/LLM tools for end-to-end automation.**

### What `gh` Can Do on Its Own

**Research & Code Discovery**

`gh` provides powerful search and querying capabilities for investigating codebases:[1][2]

```powershell
# Search code across GitHub for patterns
gh search code "TODO" --repo myorg/myrepo --limit 100

# Search with regex and filters
gh api -X GET search/code -f 'q=repo:cli/cli path:internal/' -F per_page=100 | 
  ConvertFrom-Json | 
  Select-Object -ExpandProperty items |
  Select-Object name, path, @{N="repo";E={$_.repository.name}}

# Find all instances of deprecated patterns
gh search code "deprecated_function" --owner myorg --language python
```

These capabilities let you identify code that needs fixing, find usage patterns, and analyze architectural decisions—all programmatically.[2][3][1]

**GraphQL for Deep Analysis**

Query repositories, issues, and PRs to understand code health and history:[4][5][6]

```powershell
# Find all issues created in the last month with specific labels
$query = @'
query {
  search(query: "repo:myorg/myrepo created:>2025-11-30 label:bug", type: ISSUE, first: 50) {
    edges {
      node {
        ... on Issue {
          number
          title
          createdAt
          labels(first: 5) { nodes { name } }
        }
      }
    }
  }
}
'@

gh api graphql -f query="$query" | ConvertFrom-Json
```

This lets you research bug patterns, understand dependency issues, and identify refactoring candidates.[7]

### What `gh` Cannot Do (Requires External Tools)

`gh` fundamentally **cannot**:[8][9][10][11]
- Generate new code or fixes
- Modify files directly
- Implement features autonomously
- Apply patches without external tools

It's designed for workflow automation and repository management, not code generation.[9][10]

***

### The Hybrid Approach: `gh` + AI for Automation

The real power emerges when combining `gh` with LLM systems. Here's how:

**1. GitHub Copilot CLI** (Public Preview, Sept 2025)[12][13][9]

```powershell
# Install and authenticate
gh extension install copilot/cli
copilot auth login

# Ask Copilot to fix a specific issue
copilot "Fix the failing tests in tests/"

# Or delegate a full task
copilot "Refactor the authentication module to use OAuth2"
```

Copilot CLI has agentic capabilities built-in:[9]
- Reads your local repo context
- Modifies multiple files simultaneously
- Runs git commands and commits changes
- Creates PRs and responds to review feedback
- All done from the terminal

**2. Claude Code Integration** (Complementary Approach)

Claude Code works alongside `gh` to enable full development workflows:[11]

```powershell
# Initialize Claude Code on your repo
claude code init

# Delegate a feature implementation
claude code run "Implement async/await support for database queries"

# Create PR with changes
claude code pr --title "Add async support" --body "Implements async DB queries"
```

Then use `gh` to manage the resulting PRs:

```powershell
# Merge the PR once CI passes
gh pr merge <pr_number> --auto --squash

# Check CI status
gh run view --repo myorg/myrepo <run_id>

# Monitor deployment
gh environment list -R myorg/myrepo
```

**3. Custom AI Agent Loop** (For Full Automation)[14][15]

Build a PowerShell agent that orchestrates the entire workflow:

```powershell
# Find issues needing fixes
$issues = gh issue list --state open --label "bug" --json number,title | 
    ConvertFrom-Json

foreach ($issue in $issues) {
    Write-Host "Analyzing issue #$($issue.number): $($issue.title)"
    
    # Use Claude Code or Copilot to generate fix
    $fix = Invoke-LLMAgent -Issue $issue -Action "GenerateFix"
    
    # Create branch and apply changes
    git checkout -b "fix/$($issue.number)"
    
    # Apply AI-generated patch
    Apply-Patch -Patch $fix -Repository .
    
    # Create PR
    gh pr create --title "Fix #$($issue.number)" `
        --body "Automated fix: $($issue.title)" `
        --draft
    
    Write-Host "PR created for issue #$($issue.number)"
}
```

This pattern mirrors your multi-agent architecture with Claude instances—each agent specializes in a task, and `gh` coordinates the GitHub side.[15][14]

***

### Real-World Use Cases

**Bug Triage & Auto-Fix**

1. Use `gh search code` to find instances of a known bug pattern[3]
2. Feed search results to Claude Code to generate fixes[11]
3. Use `gh pr create` with the generated patch[16]
4. Automatically merge with `gh pr merge --auto` once CI passes[17][18]

**Release Automation**

```powershell
# Fetch all commits since last release
$commits = gh api repos/$owner/$repo/commits --paginate | 
    ConvertFrom-Json

# Send to Claude for release notes generation
$releaseNotes = Invoke-LLMAgent -Commits $commits -Action "GenerateReleaseNotes"

# Create release with auto-generated notes
gh release create v1.0.0 --notes "$releaseNotes"
```

GitHub also has built-in AI release notes:[19][20]
```powershell
gh release create v1.0.0 --generate-notes
```

**Code Quality Scanning**

```powershell
# Search for problematic patterns
$results = gh search code "eval(" --repo myorg --language python

# Feed to LLM for analysis
$recommendations = Invoke-LLMAgent -CodeResults $results -Action "SecurityReview"

# Create issues automatically
$recommendations | ForEach-Object {
    gh issue create --title $_.title --body $_.description --label security
}
```

**Dependency Updates**

```powershell
# Monitor failing tests related to dependencies
gh run list --status failure | 
    Where-Object { $_ -match "deps|dependency" } |
    ForEach-Object {
        # Analyze failure with LLM
        $failure_log = gh run view $_.number --log
        $fix = Invoke-LLMAgent -Log $failure_log -Action "FixDependencyConflict"
        
        # Generate and PR the fix
        git checkout -b "fix/$($_.number)"
        Apply-Patch $fix
        gh pr create --auto-merge
    }
```

***

### Power User Pattern: Agentic Workflows with PowerShell

Since you work with multi-agent systems and Claude Code, here's how to integrate `gh` with your agent infrastructure:[15]

```powershell
# Wrap gh commands as LLM-callable tools
function Invoke-GHSearchCode {
    param([string]$Query)
    gh search code $Query --json name,path,url --limit 50 | ConvertFrom-Json
}

function Invoke-GHCreatePR {
    param([string]$Title, [string]$Body, [string]$Branch)
    gh pr create --title $Title --body $Body --head $Branch
}

# Expose to LLM as function definitions
$tools = @(
    @{
        name = "search_code"
        description = "Search GitHub repositories for code patterns"
        parameters = @{
            type = "object"
            properties = @{
                query = @{ type = "string"; description = "Search query with GitHub syntax" }
            }
            required = @("query")
        }
    },
    @{
        name = "create_pull_request"
        description = "Create a new pull request for code changes"
        parameters = @{
            type = "object"
            properties = @{
                title = @{ type = "string" }
                body = @{ type = "string" }
                branch = @{ type = "string" }
            }
            required = @("title", "body", "branch")
        }
    }
)

# Agent loop: LLM decides which tools to use
while ($taskPending) {
    $response = Invoke-LLMAgent -Tools $tools -CurrentContext $context
    
    if ($response.tool_call -eq "search_code") {
        $results = Invoke-GHSearchCode -Query $response.parameters.query
        $context += $results
    }
    elseif ($response.tool_call -eq "create_pull_request") {
        Invoke-GHCreatePR @response.parameters
    }
}
```

This pattern lets Claude Code (or your own agents) orchestrate `gh` commands without leaving the CLI—perfect for long-running research and implementation tasks.[14][15]

***

### Key Takeaway

**`gh` is the conductor; LLMs are the performers.** Use `gh` to:
- Search and analyze code[1][2][3]
- Query repository metadata[5][4][7]
- Create and manage PRs[21][16]
- Monitor CI/CD and auto-merge[18][17]
- Orchestrate multi-step workflows[14][15]

Pair it with **Copilot CLI, Claude Code, or custom agents** to handle the actual code generation, bug fixes, and feature implementation. For your multi-agent workflow, this means exposing `gh` commands as tools in your agent's function library—letting Claude decide when and how to use them while maintaining full observability and control.[15][14]
