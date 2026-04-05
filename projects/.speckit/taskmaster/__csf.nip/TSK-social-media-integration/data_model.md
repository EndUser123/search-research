# Social Media Integration Data Model

## Entity Definitions

### SocialMediaProvider
Abstract base class defining the interface for all social media providers.

**Attributes**:
- `provider_id` (string): Unique identifier for the provider
- `provider_name` (string): Human-readable provider name
- `provider_type` (enum): RSS, SCRAPING, API_PROXY, SEARCH_ENGINE
- `base_url` (string): Primary endpoint URL
- `fallback_urls` (array): Alternative endpoints for failover
- `rate_limit` (object): Request rate limiting configuration
- `auth_required` (boolean): Whether authentication is needed
- `status` (enum): ACTIVE, INACTIVE, DEGRADED, ERROR
- `last_health_check` (datetime): Last health monitoring timestamp

**Methods**:
- `search(query: string, limit: int)`: Search for content
- `get_content(item_id: string)`: Retrieve specific content
- `validate_response(response)`: Validate API response format
- `handle_error(error)`: Process and categorize errors

### RedditRSSProvider
RSS-based Reddit content provider for subreddit feeds.

**Attributes**:
- `subreddit_feeds` (array): Configured subreddit RSS URLs
- `feed_cache` (object): Cached feed data with expiration
- `update_frequency` (integer): Minutes between feed updates
- `max_posts_per_feed` (integer): Maximum posts to retrieve per feed
- `supported_post_types` (array): Types of posts to extract (hot, new, top)

**Configuration**:
```json
{
  "provider_id": "reddit_rss",
  "provider_name": "Reddit RSS Feeds",
  "subreddit_feeds": [
    "https://www.reddit.com/r/python.rss",
    "https://www.reddit.com/r/programming.rss",
    "https://www.reddit.com/r/MachineLearning.rss"
  ],
  "update_frequency": 30,
  "max_posts_per_feed": 25
}
```

### InvidiousYouTubeProvider
YouTube content provider using Invidious instances.

**Attributes**:
- `invidious_instances` (array): List of Invidious instance URLs
- `current_instance_index` (integer): Index of active instance
- `instance_health` (object): Health status of each instance
- `search_timeout` (integer): Timeout for search requests (seconds)
- `video_metadata_fields` (array): Fields to extract from video data

**Configuration**:
```json
{
  "provider_id": "youtube_invidious",
  "provider_name": "YouTube via Invidious",
  "invidious_instances": [
    "https://yewtu.be",
    "https://vid.puffyan.us",
    "https://yewtu.be"
  ],
  "search_timeout": 10,
  "video_metadata_fields": [
    "title", "description", "duration", "viewCount",
    "published", "author", "authorId"
  ]
}
```

### RedditScrapingProvider
Web scraping provider for Reddit content as fallback.

**Attributes**:
- `user_agent` (string): User agent string for requests
- `request_delay` (float): Seconds between requests
- `max_retries` (integer): Maximum retry attempts
- `respect_robots_txt` (boolean): Whether to check robots.txt
- `scraping_patterns` (object): Regex patterns for content extraction

**Configuration**:
```json
{
  "provider_id": "reddit_scraping",
  "provider_name": "Reddit Web Scraping",
  "user_agent": "ClaudeCode-Research-Bot/1.0",
  "request_delay": 2.0,
  "max_retries": 3,
  "respect_robots_txt": true
}
```

### SocialMediaContent
Represents content retrieved from social media platforms.

**Attributes**:
- `content_id` (string): Unique content identifier
- `provider_id` (string): Source provider identifier
- `platform` (string): Social media platform name
- `title` (string): Content title
- `content` (text): Full content text
- `author` (string): Content author username
- `author_id` (string): Author's unique identifier
- `url` (string): Original content URL
- `created_at` (datetime): Content creation timestamp
- `retrieved_at` (datetime): When content was retrieved
- `metadata` (object): Platform-specific metadata
- `tags` (array): Content classification tags
- `relevance_score` (float): Algorithmic relevance score (0.0-1.0)

**Platform-Specific Metadata**:

**Reddit**:
```json
{
  "subreddit": "python",
  "post_type": "link",
  "score": 1250,
  "comments": 87,
  "awards": [],
  "flair": "discussion"
}
```

**YouTube**:
```json
{
  "video_id": "dQw4w9WgXcQ",
  "duration": 212,
  "view_count": 1234567890,
  "like_count": 45678901,
  "channel_name": "OfficialChannel",
  "description": "Video description here"
}
```

### ResearchQuery
Represents a research query and its execution context.

**Attributes**:
- `query_id` (string): Unique query identifier
- `query_text` (string): Original search query
- `query_type` (enum): GENERAL, TECHNICAL, NEWS, ACADEMIC
- `sources` (array): Requested source types
- `max_results` (integer): Maximum desired results
- `filters` (object): Query filters and constraints
- `created_at` (datetime): Query creation timestamp
- `execution_time` (float): Total execution time in seconds
- `results_count` (integer): Number of results returned

### SearchResult
Represents a single search result from any provider.

**Attributes**:
- `result_id` (string): Unique result identifier
- `query_id` (string): Associated query identifier
- `provider_id` (string): Source provider
- `content` (SocialMediaContent): Associated content object
- `relevance_score` (float): Relevance to query (0.0-1.0)
- `rank` (integer): Result ranking within query
- `snippet` (string): Highlighted text snippet
- `confidence` (float): Confidence in result accuracy (0.0-1.0)

## Relationships

### Provider-Content Relationship
```
SocialMediaProvider (1) → (N) SocialMediaContent
```
- Each provider can retrieve multiple content items
- Each content item belongs to exactly one provider

### Query-Result Relationship
```
ResearchQuery (1) → (N) SearchResult → (1) SocialMediaContent
```
- Each query generates multiple search results
- Each search result references one content item
- Content can be referenced by multiple queries/queries

### Provider-Query Relationship
```
ResearchQuery (N) → (N) SocialMediaProvider
```
- Queries can specify preferred providers
- Multiple providers can be used for a single query
- Provider selection based on query type and availability

### Health Monitoring Relationship
```
SocialMediaProvider (1) → (N) HealthCheck
```
- Each provider has periodic health checks
- Health checks track provider availability and performance

## Data Integrity

### Primary Keys
- `SocialMediaProvider.provider_id`
- `SocialMediaContent.content_id`
- `ResearchQuery.query_id`
- `SearchResult.result_id`

### Foreign Keys
- `SocialMediaContent.provider_id` → `SocialMediaProvider.provider_id`
- `SearchResult.query_id` → `ResearchQuery.query_id`
- `SearchResult.content_id` → `SocialMediaContent.content_id`

### Unique Constraints
- `(provider_id, content_id)` - Prevent duplicate content from same provider
- `(query_id, provider_id, rank)` - Prevent duplicate rankings

### Not Null Constraints
- All primary key fields
- `SocialMediaContent.title`
- `SocialMediaContent.platform`
- `ResearchQuery.query_text`
- `SearchResult.relevance_score`

## Validation Rules

### Provider Validation
- `provider_id` must match pattern: `^[a-z0-9_]+$`
- `provider_type` must be one of: RSS, SCRAPING, API_PROXY, SEARCH_ENGINE
- `rate_limit` must be positive integer representing requests per hour
- `base_url` must be valid HTTPS URL

### Content Validation
- `content_id` must be unique across all providers
- `platform` must be one of: reddit, youtube, hacker_news, stack_exchange
- `relevance_score` must be between 0.0 and 1.0
- `created_at` must be valid ISO 8601 datetime
- `url` must be valid URL format

### Query Validation
- `query_text` cannot be empty or whitespace only
- `max_results` must be between 1 and 100
- `query_type` must be one of: GENERAL, TECHNICAL, NEWS, ACADEMIC
- `sources` must contain valid provider IDs

### Result Validation
- `relevance_score` must be between 0.0 and 1.0
- `rank` must be positive integer
- `confidence` must be between 0.0 and 1.0
- Foreign key constraints must be satisfied

## Indexes

### Performance Indexes
```sql
-- Content lookup by provider and platform
CREATE INDEX idx_content_provider_platform
ON social_media_content(provider_id, platform);

-- Content search by creation date
CREATE INDEX idx_content_created_at
ON social_media_content(created_at DESC);

-- Query lookup by type and creation date
CREATE INDEX idx_query_type_created
ON research_query(query_type, created_at DESC);

-- Result lookup by query and relevance
CREATE INDEX idx_result_query_relevance
ON search_result(query_id, relevance_score DESC);

-- Provider health monitoring
CREATE INDEX idx_provider_health_check
ON health_check(provider_id, check_time DESC);
```

### Full-Text Search Indexes
```sql
-- Content full-text search
CREATE FULLTEXT INDEX idx_content_fulltext
ON social_media_content(title, content);

-- Query full-text search
CREATE FULLTEXT INDEX idx_query_fulltext
ON research_query(query_text);
```

## Data Formats

### Date/Time Formats
- All datetime fields use ISO 8601 format: `YYYY-MM-DDTHH:MM:SSZ`
- Timezone is always UTC for consistency
- Created timestamps are immutable, updated timestamps are mutable

### JSON Metadata Format
```json
{
  "version": "1.0",
  "generated_at": "2025-12-12T18:13:30Z",
  "provider_specific": {
    "field": "value"
  },
  "processing": {
    "extraction_time": 1.234,
    "cache_hit": false
  }
}
```

### Error Response Format
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests to provider",
    "provider_id": "reddit_scraping",
    "retry_after": 120,
    "timestamp": "2025-12-12T18:13:30Z"
  }
}
```

## Data Migration

### Version 1.0 Schema
- Initial schema with basic provider and content entities
- Support for RSS, scraping, and API proxy providers
- Basic query and result tracking

### Future Schema Evolution
- Add support for additional social platforms
- Implement content deduplication across providers
- Add advanced filtering and search capabilities
- Implement content classification and tagging system

## Security Considerations

### Data Privacy
- No personal user data stored
- Only publicly available social media content
- Content metadata stripped of personally identifiable information

### Access Control
- Provider access controlled through rate limiting
- Scraping respects robots.txt and terms of service
- API proxy usage monitored and logged

### Data Retention
- Content cached for reasonable period (7-30 days)
- Query results retained for analysis and optimization
- Regular cleanup of expired content and queries

---

**Schema Version**: 1.0
**Last Updated**: 2025-12-12
**Compatibility**: UnifiedResearchEngine v2.0+
