# CHS - Chat History Search Help

## Detailed Command Options

### Search Command Options

#### Filtering Options
- `--session-filter FILTER`: Filter by session timeframe
  - **Values**: `today`, `yesterday`, `week`, `month`, `all`
  - **Default**: `all`
  - **Example**: `--session-filter today` searches only today's chats

- `--context-filter FILTER`: Filter by conversation context
  - **Values**: `project`, `general`, `technical`
  - **Default**: `all`
  - **Example**: `--context-filter project` focuses on project-related discussions

- `--content-filter FILTER`: Filter by content type
  - **Values**: `user`, `assistant`, `both`
  - **Default**: `both`
  - **Example**: `--content-filter user` searches only your messages

#### Ranking Options
- `--rank-by METHOD`: Result ranking method
  - **Values**: `relevance`, `recency`, `frequency`
  - **Default**: `relevance`
  - **Relevance**: TF-IDF + semantic similarity scoring
  - **Recency**: Recent conversations ranked higher
  - **Frequency**: Frequently mentioned topics prioritized

#### Output Options
- `--limit N`: Maximum number of results
  - **Range**: 1-100
  - **Default**: 20
  - **Example**: `--limit 10` shows top 10 results

- `--format FORMAT`: Output format
  - **Values**: `text`, `json`, `markdown`
  - **Default**: `text`
  - **JSON**: Structured data with metadata
  - **Markdown**: Formatted with headers and bullet points

- `--output FILE`: Save results to file
  - **Example**: `--output results.md`
  - **Auto-detects format from file extension**

### Analyze Command Options

#### Analysis Types
- `--pattern-analysis`: Deep pattern analysis
  - Identifies recurring conversation patterns
  - Detects frequently discussed topics
  - Analyzes question-answer patterns

- `--trend-analysis`: Topic trends over time
  - Tracks conversation themes evolution
  - Identifies trending vs declining topics
  - Shows conversation frequency patterns

- `--topic-modeling`: Automatic topic discovery
  - Uses machine learning to identify main topics
  - Groups related conversations automatically
  - Shows topic distribution and relationships

#### Output Options
- `--output FILE`: Save analysis report
  - **Formats**: Supports text, JSON, CSV
  - **Auto-format**: Detects format from file extension
  - **Example**: `--output analysis_report.json`

### Index Command Options

#### Index Operations
- `--rebuild`: Rebuild entire index from scratch
  - **Time**: 2-5 minutes for 1000+ chats
  - **Use**: When search results seem inaccurate
  - **Note**: Temporary index available during rebuild

- `--incremental`: Update index with new chats only
  - **Time**: 10-30 seconds
  - **Default operation**
  - **Use**: Regular maintenance

- `--optimize`: Optimize existing index
  - **Time**: 1-2 minutes
  - **Benefits**: Faster search, smaller index size
  - **Use**: Weekly maintenance

### Export Command Options

#### Export Types
- `--search-query QUERY`: Export specific search results
  - **Example**: `--search-query "docker issues"`
  - **Combines search and export in one step**

- `--all`: Export all indexed content
  - **Size**: Can be large (10-50MB)
  - **Format**: JSON with full metadata

#### Format Options
- `--format FORMAT`: Export format
  - **JSON**: Full data with metadata, best for backup
  - **CSV**: Tabular data, good for spreadsheets
  - **Markdown**: Formatted documentation
  - **HTML**: Interactive web page

## Troubleshooting

### Common Issues

#### Search Returns No Results
**Possible Causes:**
- Query too specific - try broader terms
- Wrong session filter - check timeframe
- Index needs rebuilding - run `index --rebuild`

**Solutions:**
```bash
# Try broader search terms
python -m src.modules.analysis.chat_search.src.chat_history_search search "docker" --session-filter month

# Rebuild index if search seems inaccurate
python -m src.modules.analysis.chat_search.src.chat_history_search index --rebuild

# Check system status
python -m src.modules.analysis.chat_search.src.chat_history_search status
```

#### Slow Search Performance
**Possible Causes:**
- Index needs optimization
- Large chat history (>2000 entries)
- Complex queries with multiple filters

**Solutions:**
```bash
# Optimize index
python -m src.modules.analysis.chat_search.src.chat_history_search index --optimize

# Use simpler queries
python -m src.modules.analysis.chat_search.src.chat_history_search search "query" --limit 10

# Check performance metrics
python -m src.modules.analysis.chat_search.src.chat_history_search status
```

#### Index Building Errors
**Possible Causes:**
- Corrupted chat history file
- Permission issues with history file
- Disk space insufficient

**Solutions:**
```bash
# Check chat history file exists
ls -la "C:/Users/brsth/.claude/history.jsonl"

# Check available disk space
df -h

# Rebuild from scratch
python -m src.modules.analysis.chat_search.src.chat_history_search index --rebuild
```

#### Export Fails
**Possible Causes:**
- Invalid output path
- Permission issues
- Disk space insufficient

**Solutions:**
```bash
# Use absolute path
python -m src.modules.analysis.chat_search.src.chat_history_search export --output "/full/path/results.json"

# Check directory permissions
ls -la "$(dirname '/path/to/output')"

# Export smaller datasets
python -m src.modules.analysis.chat_search.src.chat_history_search search "query" --export --format json --output small_results.json
```

### Performance Optimization

#### Improve Search Speed
1. **Regular Index Maintenance**:
   ```bash
   # Weekly optimization
   python -m src.modules.analysis.chat_search.src.chat_history_search index --optimize
   ```

2. **Use Appropriate Limits**:
   ```bash
   # Faster searches with reasonable limits
   python -m src.modules.analysis.chat_search.src.chat_history_search search "query" --limit 20
   ```

3. **Optimize Query Structure**:
   ```bash
   # Use specific terms instead of broad concepts
   python -m src.modules.analysis.chat_search.src.chat_history_search search "docker permission denied" --session-filter week
   ```

#### Reduce Memory Usage
1. **Export in Batches**:
   ```bash
   # Export specific time ranges
   python -m src.modules.analysis.chat_search.src.chat_history_search export --search-query "topic" --session-filter month
   ```

2. **Use Efficient Formats**:
   ```bash
   # JSON is more memory-efficient than HTML
   python -m src.modules.analysis.chat_search.src.chat_history_search export --format json
   ```

### System Status Interpretation

#### Understanding Status Output
```bash
python -m src.modules.analysis.chat_search.src.chat_history_search status
```

**Key Metrics:**
- **Chat History Size**: Number of indexed conversations
- **Index Health**: Percentage of properly indexed content
- **Search Performance**: Average response time in milliseconds
- **Storage Usage**: Disk space used by index files

**Status Indicators:**
- 🟢 **Good**: Index health >95%, performance <100ms
- 🟡 **Warning**: Index health 80-95%, performance 100-500ms
- 🔴 **Issue**: Index health <80%, performance >500ms

#### Recommended Actions Based on Status
- **If index health <90%**: Run `index --rebuild`
- **If performance >300ms**: Run `index --optimize`
- **If storage usage >100MB**: Consider export and archive old conversations

### Advanced Usage

#### Complex Search Queries
```bash
# Combine multiple filters
python -m src.modules.analysis.chat_search.src.chat_history_search search "docker error" --session-filter week --context-filter technical --rank-by relevance --limit 15

# Pattern-based searches
python -m src.modules.analysis.chat_search.src.chat_history_search search "authentication.*failed" --rank-by frequency
```

#### Batch Operations
```bash
# Multiple searches in parallel (script)
for query in "docker error" "git conflict" "python import"; do
    python -m src.modules.analysis.chat_search.src.chat_history_search search "$query" --output "${query// /_}_results.json"
done
```

#### Integration Scripts
```bash
# Daily analysis cron job
python -m src.modules.analysis.chat_search.src.chat_history_search analyze --trend-analysis --output "daily_analysis_$(date +%Y%m%d).json"

# Weekly maintenance
python -m src.modules.analysis.chat_search.src.chat_history_search index --optimize
python -m src.modules.analysis.chat_search.src.chat_history_search status > "weekly_status_$(date +%Y%m%d).log"
```

## Technical Details

### Search Algorithm
- **Primary**: TF-IDF (Term Frequency-Inverse Document Frequency)
- **Secondary**: Semantic similarity using sentence embeddings
- **Boosting**: Recency and frequency weighting
- **Ranking**: Combined relevance score (0-100)

### Index Structure
- **Storage**: Compressed JSON format
- **Updates**: Incremental by default
- **Optimization**: Weekly recommended
- **Backup**: Export with `--format json` for full backup

### Performance Characteristics
- **Index Size**: ~10-50MB for 1000+ conversations
- **Search Speed**: 50-200ms typical
- **Index Build**: 2-5 minutes for full rebuild
- **Memory Usage**: 100-500MB during operations
