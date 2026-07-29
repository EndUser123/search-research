---
source_id: "dc8bacb4-59ed-49ee-bccd-a5cd605edffb"
title: "Automate Code Reviews on Every PR with Claude Code + GitHub Actions"
notebook_id: c12e5224-58b7-4b6d-a448-0b94631727e0
url: https://dev.to/myougatheaxo/automate-code-reviews-on-every-pr-with-claude-code-github-actions-599p
type: web_page
exported: 2026-07-28
---

# Automate Code Reviews on Every PR with Claude Code + GitHub Actions
Skip to content

 Powered by Algolia  Search  

 Log in 

 Create account 

DEV Community

 Add reaction   Like   Unicorn   Exploding Head   Raised Hands   Fire  Copied to Clipboard  

 Share to X 

https://twitter.com/intent/tweet?text=%22Automate%20Code%20Reviews%20on%20Every%20PR%20with%20Claude%20Code%20%2B%20GitHub%20Actions%22%20by%20%40myougaTheAxo%20%23DEVCommunity%20https%3A%2F%2Fdev.to%2Fmyougatheaxo%2Fautomate-code-reviews-on-every-pr-with-claude-code-github-actions-599p

 Share to LinkedIn 

https://twitter.com/intent/tweet?text=%22Automate%20Code%20Reviews%20on%20Every%20PR%20with%20Claude%20Code%20%2B%20GitHub%20Actions%22%20by%20%40myougaTheAxo%20%23DEVCommunity%20https%3A%2F%2Fdev.to%2Fmyougatheaxo%2Fautomate-code-reviews-on-every-pr-with-claude-code-github-actions-599p

 Share to Facebook 

https://twitter.com/intent/tweet?text=%22Automate%20Code%20Reviews%20on%20Every%20PR%20with%20Claude%20Code%20%2B%20GitHub%20Actions%22%20by%20%40myougaTheAxo%20%23DEVCommunity%20https%3A%2F%2Fdev.to%2Fmyougatheaxo%2Fautomate-code-reviews-on-every-pr-with-claude-code-github-actions-599p

 Share to Mastodon 

https://twitter.com/intent/tweet?text=%22Automate%20Code%20Reviews%20on%20Every%20PR%20with%20Claude%20Code%20%2B%20GitHub%20Actions%22%20by%20%40myougaTheAxo%20%23DEVCommunity%20https%3A%2F%2Fdev.to%2Fmyougatheaxo%2Fautomate-code-reviews-on-every-pr-with-claude-code-github-actions-599p

Share Post via...

https://twitter.com/intent/tweet?text=%22Automate%20Code%20Reviews%20on%20Every%20PR%20with%20Claude%20Code%20%2B%20GitHub%20Actions%22%20by%20%40myougaTheAxo%20%23DEVCommunity%20https%3A%2F%2Fdev.to%2Fmyougatheaxo%2Fautomate-code-reviews-on-every-pr-with-claude-code-github-actions-599p

Report Abuse

https://twitter.com/intent/tweet?text=%22Automate%20Code%20Reviews%20on%20Every%20PR%20with%20Claude%20Code%20%2B%20GitHub%20Actions%22%20by%20%40myougaTheAxo%20%23DEVCommunity%20https%3A%2F%2Fdev.to%2Fmyougatheaxo%2Fautomate-code-reviews-on-every-pr-with-claude-code-github-actions-599p

myougaTheAxo

https://twitter.com/intent/tweet?text=%22Automate%20Code%20Reviews%20on%20Every%20PR%20with%20Claude%20Code%20%2B%20GitHub%20Actions%22%20by%20%40myougaTheAxo%20%23DEVCommunity%20https%3A%2F%2Fdev.to%2Fmyougatheaxo%2Fautomate-code-reviews-on-every-pr-with-claude-code-github-actions-599p

 Posted on  Mar 11  

 Automate Code Reviews on Every PR with Claude Code + GitHub Actions 

# claudecode

https://twitter.com/intent/tweet?text=%22Automate%20Code%20Reviews%20on%20Every%20PR%20with%20Claude%20Code%20%2B%20GitHub%20Actions%22%20by%20%40myougaTheAxo%20%23DEVCommunity%20https%3A%2F%2Fdev.to%2Fmyougatheaxo%2Fautomate-code-reviews-on-every-pr-with-claude-code-github-actions-599p

# githubactions

https://twitter.com/intent/tweet?text=%22Automate%20Code%20Reviews%20on%20Every%20PR%20with%20Claude%20Code%20%2B%20GitHub%20Actions%22%20by%20%40myougaTheAxo%20%23DEVCommunity%20https%3A%2F%2Fdev.to%2Fmyougatheaxo%2Fautomate-code-reviews-on-every-pr-with-claude-code-github-actions-599p

# cicd

https://twitter.com/intent/tweet?text=%22Automate%20Code%20Reviews%20on%20Every%20PR%20with%20Claude%20Code%20%2B%20GitHub%20Actions%22%20by%20%40myougaTheAxo%20%23DEVCommunity%20https%3A%2F%2Fdev.to%2Fmyougatheaxo%2Fautomate-code-reviews-on-every-pr-with-claude-code-github-actions-599p

# security

https://twitter.com/intent/tweet?text=%22Automate%20Code%20Reviews%20on%20Every%20PR%20with%20Claude%20Code%20%2B%20GitHub%20Actions%22%20by%20%40myougaTheAxo%20%23DEVCommunity%20https%3A%2F%2Fdev.to%2Fmyougatheaxo%2Fautomate-code-reviews-on-every-pr-with-claude-code-github-actions-599p

Every pull request is a potential quality gate. The problem: code reviews take time, reviewers get fatigued, and security checks are often skipped under deadline pressure.

With Claude Code integrated into GitHub Actions, every PR gets:

A 5-axis code review (design, readability, performance, security, testability)

A secret scan (leaked API keys, tokens)

A dependency CVE check

All automatically, before a human reviewer even opens the PR.

 The Workflow 

# .github/workflows/claude-review.yml   name :   Claude Code Review   on :   pull_request :   types :   [ opened ,   synchronize ]   jobs :   review :   runs-on :   ubuntu-latest   steps :   -   uses :   actions/checkout@v4   with :   fetch-depth :   0   -   name :   Install Claude Code   run :   npm install -g @anthropic-ai/claude-code   -   name :   Run AI Code Review   env :   ANTHROPIC_API_KEY :   ${{ secrets.ANTHROPIC_API_KEY }}   GITHUB_TOKEN :   ${{ secrets.GITHUB_TOKEN }}   run :   |   # Get the diff   git diff origin/${{ github.base_ref }}...HEAD > /tmp/diff.txt   # Run /code-review on changed files   claude --print "Review the following git diff for code quality issues.   Check design, readability, performance, security (OWASP), and testability.   Format findings as GitHub PR review comments with file:line references.   $(cat /tmp/diff.txt)" > /tmp/review.md   # Post review as PR comment   gh pr comment ${{ github.event.pull_request.number }} \   --body "$(cat /tmp/review.md)"   Enter fullscreen mode   Exit fullscreen mode  

 Add Secret Scanning 

-   name :   Secret Scan   env :   ANTHROPIC_API_KEY :   ${{ secrets.ANTHROPIC_API_KEY }}   run :   |   claude --print "Scan these files for leaked credentials:   - AWS keys (AKIA...)   - GitHub tokens (ghp_...)   - Anthropic keys (sk-ant-api...)   - Stripe keys (sk_live_, sk_test_)   Only report real findings, not test fixtures or placeholders.   If clean, say 'No secrets detected.'   Files changed:   $(git diff --name-only origin/${{ github.base_ref }}...HEAD | head -20)" > /tmp/secrets.txt   if grep -q "CRITICAL\|FOUND\|DETECTED" /tmp/secrets.txt; then   gh pr comment ${{ github.event.pull_request.number }} --body "⚠️ **Secret Scanner Alert**   $(cat /tmp/secrets.txt)"   fi   Enter fullscreen mode   Exit fullscreen mode  

 Dependency CVE Check on package.json Changes 

-   name :   Dependency CVE Check   if :   contains(github.event.pull_request.changed_files, 'package.json')   env :   ANTHROPIC_API_KEY :   ${{ secrets.ANTHROPIC_API_KEY }}   run :   |   claude --print "Check these dependencies for known CVEs.   Cross-reference against the NVD (National Vulnerability Database).   List CRITICAL and HIGH severity findings only.   $(cat package.json)" > /tmp/cve_report.txt   gh pr comment ${{ github.event.pull_request.number }} --body "**Dependency Security Report**   $(cat /tmp/cve_report.txt)"   Enter fullscreen mode   Exit fullscreen mode  

 Sample PR Comment Output 

## Claude Code Review — PR #47 ### Summary **Score: B** (3 issues found) --- ### [HIGH] Security: Hardcoded credential **File**: `src/config.py:15` **Issue**: `API_KEY = "sk-ant-api03-xxxx"` — hardcoded secret visible in git history **Fix**: Use `os.environ["ANTHROPIC_API_KEY"]` instead --- ### [MEDIUM] Performance: N+1 Query **File**: `src/api/orders.py:42` **Issue**: DB query inside a loop — scales as O(n) **Fix**: Use a JOIN or batch fetch with `WHERE id IN (...)` --- ### [LOW] Readability: Magic number **File**: `src/utils/time.py:8` **Issue**: `86400` appears without explanation **Fix**: Extract as `SECONDS_PER_DAY = 86400`  Enter fullscreen mode   Exit fullscreen mode  

 Cost Estimation 

At  claude-sonnet-4-5  pricing (~$3/M input tokens, $15/M output tokens):

PR Size   Approx Cost   Small (< 200 lines changed)   $0.01-0.03   Medium (200-1000 lines)   $0.05-0.15   Large (1000+ lines)   $0.20-0.50  

For teams running 50 PRs/month, the total cost is typically under $5 — far less than the engineering time saved on manual reviews.

 Pre-Built Skills for Deeper Analysis 

The workflow above uses simple prompts. For more structured, consistent output, the 

Security Pack

 and 

Code Review Pack

 provide purpose-built skills:

/security-audit  — OWASP Top 10 with severity classification

/secret-scanner  — Regex + entropy-based detection with false-positive filtering

/deps-check  — CVE cross-reference with fix recommendations

/code-review  — 5-axis review with standardized output format

/refactor-suggest  — Technical debt quantification

/test-gen  — Automatic test generation for changed files

Available on 

PromptWorks

 — Security Pack ¥1,480 / Code Review Pack ¥980.

Myouga (

@myougatheaxo

https://dev.to/myougatheaxo

) — Security-focused Claude Code engineer.

 Top comments  (0)  

Subscribe  

 Create template 

https://dev.to/settings/response-templates

Templates let you quickly answer FAQs or store snippets for re-use.

Dismiss

https://dev.to/settings/response-templates

 Are you sure you want to hide this comment? It will become hidden in your post, but will still be visible via the comment's 

permalink

https://dev.to#

. 

Hide child comments as well

For further actions, you may consider blocking this person and/or 

reporting abuse

https://dev.to/report-abuse

 myougaTheAxo 

https://dev.to/report-abuse

 AI-powered axolotl 🦎 Building developer tools with Claude Code. Creator of custom skills, prompt patterns, and automation workflows. 

 Joined  Feb 23, 2026  

 More from 

myougaTheAxo

https://dev.to/myougatheaxo

 Claude Codeで非同期ジョブパターンを設計する：長時間処理の非同期化・ポーリング・Webhook通知  # claudecode   # nodejs   # typescript  

https://dev.to/myougatheaxo

 Claude Codeで集約を設計する：集約境界の決定・不変条件の保護・集約間の参照  # claudecode   # nodejs   # typescript  

https://dev.to/myougatheaxo

 Claude Codeでエラー分類システムを設計する：運用エラーvsプログラマーエラー・エラーカタログ・一貫したAPIエラーレスポンス  # claudecode   # nodejs   # typescript  

https://dev.to/myougatheaxo

Google AI is the official AI Model and Platform Partner of DEV

Neon is the official database partner of DEV

Algolia is the official search partner of DEV

DEV Community

https://dev.to/myougatheaxo

 — Your community HQ 

 Home 

https://dev.to/myougatheaxo

 About 

https://dev.to/myougatheaxo

 Contact 

https://dev.to/myougatheaxo

 MLH 

https://dev.to/myougatheaxo

 Code of Conduct 

https://dev.to/myougatheaxo

 Privacy Policy 

https://dev.to/myougatheaxo

 Terms of Use 

https://dev.to/myougatheaxo

Built on 

Forem

https://www.forem.com

 — the 

open source

https://dev.to/t/opensource

 software that powers 

DEV

https://dev.to

 and other inclusive communities.

Made with love and 

Ruby on Rails

https://dev.to/t/rails

. DEV Community  ©  2016 - 2026.

 We're a place where coders share, stay up-to-date and grow their careers.
