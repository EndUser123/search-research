# CHS - Chat History Search Examples

## Quick Start Examples

### Basic Search
```bash
# Search for any topic
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search search "docker"

# Search with quotes for exact phrases
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search search "permission denied"

# Limit results
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search search "python" --limit 5
```

### System Status
```bash
# Check system health
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search status

# Expected output shows:
# - Chat history size
# - Index health percentage
# - Search performance metrics
# - Storage usage
```

## Real-World Scenarios

### 🐛 Debugging Scenarios

#### Scenario 1: Docker Permission Issues
```bash
# Find all docker permission discussions
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search search "docker permission denied" --session-filter month

# Focus on technical context
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search search "docker permission denied" --context-filter technical --rank-by relevance

# Export solutions for reference
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search export --search-query "docker permission denied" --format markdown --output docker_solutions.md
```

#### Scenario 2: Python Import Errors
```bash
# Search for import error patterns
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search search "module import error" --rank-by frequency

# Recent solutions only
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search search "import error" --session-filter week

# Find virtual environment discussions
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search search "virtual environment import" --context-filter technical
```

#### Scenario 3: Git Merge Conflicts
```bash
# All merge conflict discussions
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search search "merge conflict" --limit 10

# Specific merge strategies
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search search "git merge strategy" --rank-by relevance

# Recent git troubleshooting
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search search "git troubleshooting" --session-filter month --format json
```

### 🏗️ Development Scenarios

#### Scenario 4: API Development Patterns
```bash
# Find API design discussions
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search search "API design patterns" --context-filter technical

# REST API implementations
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search search "REST API implementation" --rank-by frequency

# Authentication approaches
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search search "authentication API" --session-filter month --limit 15
```

#### Scenario 5: Testing Strategies
```bash
# Testing best practices
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search search "testing best practices" --context-filter technical

# Unit testing patterns
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search search "unit testing patterns" --rank-by relevance

# Test-driven development
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search search "TDD approach" --session-filter week
```

#### Scenario 6: Code Refactoring
```bash
# Refactoring discussions
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search search "code refactoring" --limit 10

# Specific refactoring patterns
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search search "extract method refactoring" --context-filter technical

# Refactoring tools and techniques
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search search "refactoring tools" --rank-by frequency
```

### 📚 Learning Scenarios

#### Scenario 7: New Technology Learning
```bash
# Track learning progress for React
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search search "react learning" --session-filter month --rank-by recency

# Find React best practices
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search search "react best practices" --context-filter technical

# React component patterns
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search search "react component patterns" --limit 15
```

#### Scenario 8: Algorithm Study
```bash
# Algorithm discussions
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search search "algorithm implementation" --rank-by relevance

# Specific algorithms
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search search "sorting algorithms" --context-filter technical

# Data structure implementations
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search search "data structure patterns" --session-filter week
```

#### Scenario 9: Security Learning
```bash
# Security concepts
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search search "security best practices" --rank-by frequency

# Authentication patterns
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search search "authentication patterns" --context-filter technical

# Common vulnerabilities
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search search "security vulnerabilities" --session-filter month
```

### 📊 Analysis Examples

#### Scenario 10: Weekly Progress Analysis
```bash
# Analyze weekly chat patterns
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search analyze --trend-analysis --session-filter week

# Pattern discovery for problem-solving
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search analyze --pattern-analysis --search-query "problem solving"

# Topic modeling for project discussions
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search analyze --topic-modeling --context-filter project
```

#### Scenario 11: Learning Pattern Analysis
```bash
# How you learn new technologies
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search analyze --pattern-analysis --search-query "learning new"

# Track knowledge retention
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search analyze --trend-analysis --session-filter month

# Discover your main topics
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search analyze --topic-modeling --output monthly_topics.json
```

### 🔧 Integration Examples

#### Scenario 12: TaskMaster Integration
```bash
# Before starting a new task
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search search "task planning" --session-filter day

# Find related previous tasks
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search search "similar task" --context-filter project

# Store task insights
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search export --search-query "task insights" --format json --output task_context.json
```

#### Scenario 13: Validation System Research
```bash
# Find validation discussions
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search search "code validation" --rank-by relevance

# Quality standards discussions
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search search "quality standards" --context-filter technical

# Best practices for validation
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search search "validation best practices" --session-filter week
```

#### Scenario 14: Health Check Context
```bash
# System performance discussions
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search search "system performance" --rank-by frequency

# Health monitoring approaches
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search search "health monitoring" --context-filter technical

# Performance optimization patterns
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search search "performance optimization" --session-filter month
```

## Advanced Usage Examples

### 🔍 Complex Search Queries

#### Multi-Filter Searches
```bash
# Recent technical discussions about authentication
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search search "authentication" --session-filter week --context-filter technical --rank-by relevance

# All Docker discussions from last month, ranked by frequency
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search search "docker" --session-filter month --rank-by frequency --limit 20

# Project-related API discussions from this week
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search search "API" --session-filter week --context-filter project --rank-by recency
```

#### Export-Oriented Searches
```bash
# Export all React discussions
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search export --search-query "react" --format json --output react_discussions.json

# Export recent debugging sessions
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search export --search-query "debugging" --session-filter month --format markdown --output debugging_log.md

# Export all project discussions
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search export --context-filter project --format csv --output project_discussions.csv
```

### 📈 Analysis Workflows

#### Comprehensive Research Workflow
```bash
# Step 1: Broad topic search
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search search "machine learning" --limit 30 --format json > ml_search.json

# Step 2: Pattern analysis
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search analyze --pattern-analysis --search-query "machine learning" > ml_patterns.json

# Step 3: Trend analysis
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search analyze --trend-analysis --search-query "machine learning" --session-filter month > ml_trends.json

# Step 4: Export comprehensive results
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search export --search-query "machine learning" --format markdown --output ml_research.md
```

#### Learning Progress Tracking
```bash
# Daily learning check
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search analyze --session-filter day --pattern-analysis > daily_learning.json

# Weekly progress summary
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search analyze --session-filter week --trend-analysis > weekly_progress.json

# Monthly knowledge consolidation
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search analyze --session-filter month --topic-modeling --output monthly_knowledge.json
```

### 🛠️ Maintenance Examples

#### System Maintenance
```bash
# Check system status
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search status

# Optimize index (weekly)
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search index --optimize

# Rebuild index (monthly or when needed)
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search index --rebuild

# Backup important findings
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search export --all --format json --output chat_backup_$(date +%Y%m%d).json
```

#### Performance Monitoring
```bash
# Check search performance
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search status

# Test search speed
time python -m src.modules.analysis.chat_search.src.chat_history_search search "test query" --limit 10

# Monitor index size growth
cd "C:/_Python/_Projects/__csf.nip" && python -m src.modules.analysis.chat_search.src.chat_history_search status | grep "Storage"
```

## Script Examples

### 📜 Batch Processing Scripts

#### Multi-Topic Research Script
```bash
#!/bin/bash
# research_multiple_topics.sh

TOPICS=("docker" "kubernetes" "python" "react" "security")
cd "C:/_Python/_Projects/__csf.nip"

for topic in "${TOPICS[@]}"; do
    echo "Researching $topic..."
    python -m src.modules.analysis.chat_search.src.chat_history_search search "$topic" \
        --limit 20 \
        --format json \
        --output "${topic}_research.json"

    python -m src.modules.analysis.chat_search.src.chat_history_search analyze \
        --search-query "$topic" \
        --pattern-analysis \
        --output "${topic}_patterns.json"
done

echo "Research complete. Results saved to *_research.json and *_patterns.json"
```

#### Weekly Analysis Script
```bash
#!/bin/bash
# weekly_analysis.sh

cd "C:/_Python/_Projects/__csf.nip"
DATE=$(date +%Y%m%d)

# System status
python -m src.modules.analysis.chat_search.src.chat_history_search status > "weekly_status_$DATE.log"

# Learning analysis
python -m src.modules.analysis.chat_search.src.chat_history_search analyze \
    --session-filter week \
    --pattern-analysis \
    --output "weekly_learning_$DATE.json"

# Trend analysis
python -m src.modules.analysis.chat_search.src.chat_history_search analyze \
    --session-filter week \
    --trend-analysis \
    --output "weekly_trends_$DATE.json"

# Project discussions
python -m src.modules.analysis.chat_search.src.chat_history_search export \
    --context-filter project \
    --session-filter week \
    --format markdown \
    --output "weekly_project_$DATE.md"

echo "Weekly analysis complete. Files saved with prefix weekly_*_$DATE"
```

#### Knowledge Backup Script
```bash
#!/bin/bash
# backup_knowledge.sh

cd "C:/_Python/_Projects/__csf.nip"
DATE=$(date +%Y%m%d)

# Create backup directory
mkdir -p "backups/$DATE"

# Full backup
python -m src.modules.analysis.chat_search.src.chat_history_search export \
    --all \
    --format json \
    --output "backups/$DATE/full_chat_backup.json"

# Important topics backup
IMPORTANT_TOPICS=("best practices" "lessons learned" "solutions" "insights")

for topic in "${IMPORTANT_TOPICS[@]}"; do
    python -m src.modules.analysis.chat_search.src.chat_history_search export \
        --search-query "$topic" \
        --format markdown \
        --output "backups/$DATE/${topic// /_}.md"
done

echo "Knowledge backup complete in backups/$DATE/"
```

### 🔧 Integration Scripts

#### Task Planning Integration
```bash
#!/bin/bash
# task_planning_helper.sh

TASK_TOPIC="$1"
cd "C:/_Python/_Projects/__csf.nip"

if [ -z "$TASK_TOPIC" ]; then
    echo "Usage: $0 <task_topic>"
    exit 1
fi

echo "Planning task: $TASK_TOPIC"
echo "=========================="

# Find related previous work
echo "1. Previous related work:"
python -m src.modules.analysis.chat_search.src.chat_history_search search "$TASK_TOPIC" \
    --session-filter month \
    --limit 5 \
    --format text

echo ""

# Find similar solutions
echo "2. Similar solutions:"
python -m src.modules.analysis.chat_search.src.chat_history_search search "$TASK_TOPIC" \
    --context-filter technical \
    --rank-by relevance \
    --limit 3

echo ""

# Export context for task
echo "3. Exporting task context..."
python -m src.modules.analysis.chat_search.src.chat_history_search export \
    --search-query "$TASK_TOPIC" \
    --format json \
    --output "task_context_${TASK_TOPIC// /_}.json"

echo "Task context exported to task_context_${TASK_TOPIC// /_}.json"
```

#### Learning Session Helper
```bash
#!/bin/bash
# learning_session.sh

LEARNING_TOPIC="$1"
cd "C:/_Python/_Projects/__csf.nip"

if [ -z "$LEARNING_TOPIC" ]; then
    echo "Usage: $0 <learning_topic>"
    exit 1
fi

echo "Learning session: $LEARNING_TOPIC"
echo "==============================="

# Current knowledge
echo "1. Current knowledge on $LEARNING_TOPIC:"
python -m src.modules.analysis.chat_search.src.chat_history_search search "$LEARNING_TOPIC" \
    --rank-by recency \
    --limit 10

echo ""

# Learning patterns
echo "2. How you learn about $LEARNING_TOPIC:"
python -m src.modules.analysis.chat_search.src.chat_history_search analyze \
    --search-query "learning $LEARNING_TOPIC" \
    --pattern-analysis

echo ""

# Related topics
echo "3. Related topics:"
python -m src.modules.analysis.chat_search.src.chat_history_search search "$LEARNING_TOPIC" \
    --limit 20 \
    --format json | jq -r '.[].content' | grep -i "$LEARNING_TOPIC" | head -10

echo ""

# Export for study
echo "4. Exporting learning material..."
python -m src.modules.analysis.chat_search.src.chat_history_search export \
    --search-query "$LEARNING_TOPIC" \
    --format markdown \
    --output "learning_${LEARNING_TOPIC// /_}.md"

echo "Learning material exported to learning_${LEARNING_TOPIC// /_}.md"
```

## Output Examples

### Search Output Examples

#### Text Format Output
```
[2024-10-15 14:30:22] You: How do I fix docker permission denied errors?
[2024-10-15 14:30:45] Assistant: The permission denied error typically occurs when...
[2024-10-15 14:31:12] You: I tried adding user to docker group but still getting errors
[2024-10-15 14:31:35] Assistant: Let me help you troubleshoot this step by step...

Relevance Score: 95
Session: Technical troubleshooting
Context: Docker configuration
```

#### JSON Format Output
```json
{
  "results": [
    {
      "timestamp": "2024-10-15T14:30:22Z",
      "speaker": "user",
      "content": "How do I fix docker permission denied errors?",
      "relevance_score": 95,
      "session_type": "technical",
      "context_tags": ["docker", "permissions", "troubleshooting"]
    }
  ],
  "total_results": 15,
  "search_time": 0.045,
  "query": "docker permission denied"
}
```

### Analysis Output Examples

#### Pattern Analysis Output
```json
{
  "patterns": [
    {
      "pattern": "Problem-solving approach",
      "frequency": 23,
      "contexts": ["docker", "python", "git"],
      "evolution": "Increasingly systematic over time"
    }
  ],
  "insights": [
    "You tend to search for solutions before asking for help",
    "Learning patterns show progressive complexity"
  ]
}
```

These examples demonstrate the full range of Chat History Search capabilities and how to integrate it into various workflows.
