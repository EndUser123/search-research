# GitHub Integration for TaskMaster

## Overview

This GitHub integration system provides automated task creation and management for TaskMaster through comprehensive webhook processing. The system analyzes pull requests, commits, and issues to automatically generate tasks with full CWO12 compliance validation.

## Features

### Core Functionality
- **Webhook Server**: Secure GitHub webhook endpoint with signature verification
- **PR Analysis Engine**: Advanced analysis of pull requests for task creation
- **Commit Analyzer**: Commit message analysis for task creation and linking
- **Task Automation Engine**: Rule-based task creation with CWO12 compliance
- **Error Handling**: Comprehensive retry logic and monitoring system

### Key Capabilities
- Automated task creation from GitHub events
- CWO12 constitutional compliance validation
- Evidence collection and verification
- Task linking and status updates
- Performance monitoring and health checks
- Rate limiting and circuit breaker protection

## Architecture

```
GitHub Webhook → Webhook Server → Event Orchestrator
                                      ↓
    ┌─────────────────┬─────────────────┬─────────────────┐
    │                 │                 │                 │
 PR Analysis    Commit Analyzer   Automation Engine  Error Manager
    │                 │                 │                 │
    └─────────────────┴─────────────────┴─────────────────┘
                                      ↓
                              TaskMaster Database
```

## Installation

### Prerequisites
- Python 3.8+
- TaskMaster database setup
- GitHub repository with webhook permissions
- Environment variables configured

### Setup Steps

1. **Clone or copy the integration files to your TaskMaster directory:**
   ```
   P:/.speckit/taskmaster/
   ├── github_webhook_server.py
   ├── pr_analysis_engine.py
   ├── commit_analyzer.py
   ├── task_automation_engine.py
   ├── error_handling_retry.py
   ├── github_integration_main.py
   └── README_GITHUB_INTEGRATION.md
   ```

2. **Install required Python packages:**
   ```bash
   pip install aiohttp asyncio sqlite3
   ```

3. **Configure environment variables:**
   ```bash
   export GITHUB_WEBHOOK_SECRET="your-webhook-secret-key"
   export GITHUB_TOKEN="your-github-personal-access-token"
   export WEBHOOK_HOST="localhost"  # or your server IP
   export WEBHOOK_PORT="8080"       # or your preferred port
   ```

4. **Set up GitHub webhook:**
   - Go to your GitHub repository settings
   - Add webhook pointing to `http://your-server:8080/webhook/github`
   - Set secret key to match `GITHUB_WEBHOOK_SECRET`
   - Select events: Pull requests, Pushes, Issues, Issue comments

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GITHUB_WEBHOOK_SECRET` | Yes | Secret key for webhook signature verification |
| `GITHUB_TOKEN` | Yes | GitHub personal access token with repo permissions |
| `WEBHOOK_HOST` | No | Host address for webhook server (default: localhost) |
| `WEBHOOK_PORT` | No | Port for webhook server (default: 8080) |

### GitHub Token Requirements

The GitHub token needs the following permissions:
- `repo` - Full repository access
- `admin:repo_hook` - Manage webhooks (if setting up via API)
- `read:org` - Organization access (for organization repositories)

## Usage

### Starting the Integration

```bash
cd P:/.speckit/taskmaster
python github_integration_main.py
```

The system will:
1. Initialize all components
2. Start the webhook server
3. Begin processing GitHub events
4. Log statistics and health status

### Webhook Endpoints

- **Main Webhook**: `POST /webhook/github` - Receives GitHub events
- **Health Check**: `GET /health` - Basic health status
- **Status Check**: `GET /status` - Detailed system status

### Event Processing

#### Pull Request Events
- **Opened**: Creates tasks based on PR analysis
- **Ready for Review**: Triggers task creation for review
- **Closed/Merged**: Updates related task status

#### Push Events
- **Commits**: Analyzed for task creation keywords
- **Task Linking**: Links commits to existing tasks
- **Status Updates**: Updates task progress based on commits

#### Issue Events
- **Opened**: Creates tasks from GitHub issues
- **Labels**: Used for task categorization and priority

#### Comment Events
- **Task Triggers**: Processes manual task creation commands
- **Keywords**: Responds to `/task-create`, `TODO:`, etc.

## Task Creation Rules

### Default Automation Rules

1. **PR Opened - Feature Development**
   - Event: `pull_request` with `action=opened`
   - Labels: `feature`, `enhancement`
   - Creates: Development task with testing requirements

2. **PR Opened - Bug Fix**
   - Event: `pull_request` with `action=opened`
   - Labels: `bug`, `fix`
   - Creates: High-priority bug fix task

3. **Security Vulnerability**
   - Event: `pull_request` with security labels
   - Creates: Critical priority security task

4. **Commit with Task Keywords**
   - Event: `push` with task creation keywords
   - Keywords: `task-create`, `tsk.new`, `TODO:`, `FIXME:`
   - Creates: Task based on commit content

### Task Creation Syntax

#### In Commit Messages
```
task-create: Implement user authentication
type: feature
priority: high
phase: development

Add OAuth2 authentication with JWT tokens
```

#### In Issue Comments
```
/task-create Add comprehensive logging system

Type: feature
Priority: medium
Phase: development
Acceptance Criteria:
- All major operations logged
- Log levels implemented
- Log rotation configured
```

## CWO12 Compliance

### Compliance Features

1. **Evidence Collection**
   - Automatic evidence gathering from GitHub events
   - Commit message analysis for completion evidence
   - File change tracking for verification

2. **Constitutional Validation**
   - Automated compliance checking
   - Rule-based validation
   - Evidence completeness verification

3. **Verification Requirements**
   - Acceptance criteria generation
   - Testing requirement analysis
   - Documentation completeness checks

### Compliance Validation

The system validates:
- Evidence requirements are met
- Constitutional rules are followed
- Documentation is complete
- Verification criteria are measurable

## Monitoring and Maintenance

### Health Monitoring

Access `GET /status` for comprehensive health information:
```json
{
  "status": "healthy",
  "components": {
    "webhook_server": "running",
    "pr_analyzer": "running",
    "automation_engine": "running"
  },
  "statistics": {
    "uptime_hours": 24.5,
    "events_processed": 1250,
    "tasks_created": 89,
    "success_rate": 98.4
  }
}
```

### Error Handling

The system includes comprehensive error handling:
- **Retry Logic**: Exponential backoff for transient failures
- **Circuit Breaker**: Prevents cascade failures
- **Rate Limiting**: Protects against overload
- **Error Classification**: Categorizes errors by type and severity

### Logging

Logs are written to:
- Console output (for real-time monitoring)
- File: `P:/.speckit/taskmaster/github_integration.log`

Log levels include:
- `INFO`: Normal operation and statistics
- `WARNING`: Recoverable issues and rate limiting
- `ERROR`: Processing errors and failures
- `CRITICAL`: System-level problems

## Performance Considerations

### Rate Limiting
- GitHub API: 5,000 requests/hour (authenticated)
- Internal: 1,000 requests/5 minutes per operation type
- Webhook processing: No artificial limits

### Scaling
- **Horizontal**: Multiple instances behind load balancer
- **Vertical**: Increase memory and CPU for high-volume repositories
- **Database**: Consider connection pooling for SQLite

### Optimization Tips
1. Use specific event filters to reduce processing
2. Adjust retry configurations for your environment
3. Monitor and tune rate limiting thresholds
4. Regular maintenance of error logs and statistics

## Troubleshooting

### Common Issues

#### Webhook Not Receiving Events
1. Check webhook URL is accessible
2. Verify secret key matches GitHub configuration
3. Check firewall and network connectivity
4. Review GitHub webhook delivery logs

#### Tasks Not Being Created
1. Check automation rules are enabled
2. Verify CWO12 compliance validation isn't blocking
3. Review error logs for specific issues
4. Check GitHub token permissions

#### High Error Rates
1. Review rate limiting settings
2. Check GitHub API token validity
3. Verify database connectivity
4. Monitor system resources

### Debug Mode

Enable debug logging:
```python
logging.getLogger().setLevel(logging.DEBUG)
```

### Health Checks

Regular health monitoring:
```bash
curl http://localhost:8080/health
curl http://localhost:8080/status
```

## Security Considerations

### Webhook Security
- **Signature Verification**: All webhooks verified with HMAC-SHA256
- **Rate Limiting**: Prevents abuse and overload
- **Input Validation**: All GitHub data validated before processing

### GitHub Token Security
- Store token securely (environment variables recommended)
- Use minimal required permissions
- Rotate tokens regularly
- Monitor token usage

### Data Privacy
- No sensitive data stored in logs
- GitHub data processed in memory only
- Compliance with data protection requirements

## API Reference

### Webhook Server

#### GitHubWebhookServer
```python
server = GitHubWebhookServer(
    webhook_secret="secret",
    github_token="token",
    host="localhost",
    port=8080
)

await server.start()
await server.stop()
```

#### Event Handlers
- `handle_pull_request(event)`
- `handle_push(event)`
- `handle_issues(event)`
- `handle_issue_comment(event)`

### Analysis Engines

#### PR Analysis Engine
```python
analyzer = PRAnalysisEngine(github_token)
result = await analyzer.analyze_pr(pr_data, "owner/repo")
```

#### Commit Analyzer
```python
analyzer = CommitAnalyzer(github_token)
result = await analyzer.analyze_commit(commit_data, "owner/repo")
```

### Task Automation

#### Automation Engine
```python
engine = TaskAutomationEngine()
tasks = await engine.process_github_event(event_data)
```

#### Custom Rules
```python
rule = AutomationRule(
    rule_id="custom_rule",
    name="Custom Task Creation",
    event_type="pull_request",
    conditions={"labels_contains": ["custom"]},
    task_template={...}
)
engine.add_automation_rule(rule)
```

## Contributing

### Development Setup
1. Set up development environment
2. Create feature branch
3. Add tests for new functionality
4. Ensure CWO12 compliance
5. Submit pull request

### Testing
- Unit tests for individual components
- Integration tests for webhook processing
- Load testing for high-volume scenarios
- Compliance testing for CWO12 requirements

## Support

### Documentation
- This README
- Inline code documentation
- Error message explanations
- GitHub issues for bug reports

### Getting Help
1. Check this documentation first
2. Review log files for specific errors
3. Check GitHub webhook delivery status
4. Create issue with detailed information

## Version History

### v1.0.0
- Initial release
- Core webhook functionality
- PR and commit analysis
- Task automation engine
- Error handling and monitoring
- CWO12 compliance integration

## License

This integration is part of the TaskMaster system and follows the same licensing terms.

---

**Note**: This integration assumes an existing TaskMaster setup with the database schema already in place. Ensure your TaskMaster installation is properly configured before enabling GitHub integration.
