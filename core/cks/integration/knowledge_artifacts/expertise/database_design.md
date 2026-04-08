# Database Design Expertise

**File**: `cks/integration/knowledge_artifacts/expertise/database_design.md`
**Category**: Database Engineering
**Expertise Level**: Senior/Principal
**Last Updated**: 2025-12-21
**Tags**: `database`, `sql`, `nosql`, `schema-design`, `performance`, `migration`, `orm`
**Task ID**: task-03-03

---

## Overview

This expertise file provides comprehensive database design patterns, best practices, and solutions for both relational (SQL) and non-relational (NoSQL) database systems. It covers data modeling, performance optimization, migration strategies, and modern database management practices for the CSF ecosystem.

---

## Relational Database Design (SQL)

### Core Design Principles

#### Normalization Patterns

```sql
-- First Normal Form (1NF) - Atomic Values
CREATE TABLE users (
    user_id INT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Second Normal Form (2NF) - No Partial Dependencies
CREATE TABLE orders (
    order_id INT PRIMARY KEY,
    user_id INT NOT NULL,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE order_items (
    order_item_id INT PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);
```

#### Database Schema Patterns

**Star Schema for Analytics:**
```sql
-- Fact table
CREATE TABLE sales_facts (
    sale_id BIGINT PRIMARY KEY,
    date_id INT NOT NULL,
    product_id INT NOT NULL,
    store_id INT NOT NULL,
    customer_id INT NOT NULL,
    quantity_sold INT,
    revenue DECIMAL(12,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (date_id) REFERENCES date_dimension(date_id),
    FOREIGN KEY (product_id) REFERENCES product_dimension(product_id),
    FOREIGN KEY (store_id) REFERENCES store_dimension(store_id),
    FOREIGN KEY (customer_id) REFERENCES customer_dimension(customer_id)
);

-- Dimension tables
CREATE TABLE date_dimension (
    date_id INT PRIMARY KEY,
    full_date DATE NOT NULL,
    year INT NOT NULL,
    quarter INT NOT NULL,
    month INT NOT NULL,
    day_of_week INT NOT NULL,
    is_weekend BOOLEAN DEFAULT FALSE
);
```

### Indexing Strategies

#### Composite Index Design
```sql
-- Query pattern: WHERE status = ? AND created_at > ? ORDER BY priority DESC
CREATE INDEX idx_tasks_status_created_priority
ON tasks (status, created_at, priority DESC);

-- Covering index for frequent queries
CREATE INDEX idx_users_email_active
ON users (email, is_active) INCLUDE (user_id, username);

-- Partial indexes for filtered data
CREATE INDEX idx_active_users_last_login
ON users (last_login_at) WHERE is_active = true;
```

#### Function-Based Indexes
```sql
-- Case-insensitive search
CREATE INDEX idx_users_email_lower
ON users (LOWER(email));

-- JSON data indexing (PostgreSQL)
CREATE INDEX idx_products_attributes_category
ON products USING GIN ((attributes->>'category'));

-- Expression indexes for computed columns
CREATE INDEX idx_orders_month
ON orders (EXTRACT(MONTH FROM created_at));
```

### Advanced SQL Patterns

#### Hierarchical Data Management
```sql
-- Recursive CTE for organizational hierarchy
WITH RECURSIVE employee_hierarchy AS (
    -- Base case: top-level managers
    SELECT employee_id, manager_id, name, 1 as level,
           ARRAY[employee_id] as path_ids
    FROM employees
    WHERE manager_id IS NULL

    UNION ALL

    -- Recursive case: subordinates
    SELECT e.employee_id, e.manager_id, e.name, eh.level + 1,
           eh.path_ids || e.employee_id
    FROM employees e
    JOIN employee_hierarchy eh ON e.manager_id = eh.employee_id
)
SELECT
    employee_id,
    name,
    level,
    array_length(path_ids, 1) as depth
FROM employee_hierarchy
ORDER BY level, name;
```

#### JSON Data Handling
```sql
-- PostgreSQL JSON operations
CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    attributes JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- JSON query with index
CREATE INDEX idx_product_attributes_gin
ON products USING GIN (attributes);

-- Efficient JSON queries
SELECT product_id, name
FROM products
WHERE attributes @> '{"category": "electronics", "brand": "Apple"}'
  AND attributes ? 'specifications';
```

---

## NoSQL Database Patterns

### MongoDB Document Design

#### Embedding vs. Referencing
```javascript
// Embedded documents for read performance
{
  _id: ObjectId("64a7b8c9d1e2f3a4b5c6d7e8"),
  title: "Database Design Best Practices",
  content: "Comprehensive guide to database design patterns...",
  author: {
    _id: ObjectId("64a7b8c9d1e2f3a4b5c6d7e9"),
    name: "John Doe",
    email: "john@example.com",
    expertise: ["Database Architecture", "Performance Optimization"]
  },
  tags: ["mongodb", "database", "design", "patterns"],
  metadata: {
    view_count: 1250,
    rating: 4.8,
    last_accessed: ISODate("2025-12-21T10:00:00Z")
  },
  created_at: ISODate("2025-12-21T09:00:00Z"),
  updated_at: ISODate("2025-12-21T09:30:00Z")
}

// Referenced pattern for large related data
{
  _id: ObjectId("64a7b8c9d1e2f3a4b5c6d7ea"),
  title: "CSF Knowledge System",
  category_ids: [ObjectId("cat1"), ObjectId("cat2")],
  expertise_area: "knowledge_management",
  related_documents: [
    ObjectId("64a7b8c9d1e2f3a4b5c6d7e8"),
    ObjectId("64a7b8c9d1e2f3a4b5c6d7eb")
  ],
  access_patterns: {
    read_frequency: "high",
    update_frequency: "low",
    query_patterns: ["by_category", "by_expertise", "by_tags"]
  }
}
```

#### Schema Validation Patterns
```javascript
// MongoDB schema validation
db.createCollection("expertise_files", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["title", "category", "expertise_level", "content"],
      properties: {
        title: {
          bsonType: "string",
          minLength: 1,
          maxLength: 200,
          description: "Title of the expertise file"
        },
        category: {
          enum: ["database", "api_design", "system_architecture", "security"],
          description: "Primary category of expertise"
        },
        expertise_level: {
          enum: ["junior", "intermediate", "senior", "principal"],
          description: "Expertise level classification"
        },
        tags: {
          bsonType: "array",
          maxItems: 15,
          items: {
            bsonType: "string",
            minLength: 1
          },
          description: "Tags for content discovery"
        },
        content: {
          bsonType: "string",
          minLength: 50,
          description: "Main content of the expertise file"
        },
        metadata: {
          bsonType: "object",
          properties: {
            view_count: { bsonType: "int", minimum: 0 },
            rating: { bsonType: "double", minimum: 0, maximum: 5 },
            last_accessed: { bsonType: "date" }
          }
        }
      }
    }
  },
  validationLevel: "strict",
  validationAction: "error"
});
```

### Redis Data Structures

#### Cache Patterns for Knowledge System
```python
import redis
import json
from datetime import timedelta
from typing import Dict, List, Any

class CSFKnowledgeCache:
    def __init__(self, redis_host='localhost', redis_port=6379, db=0):
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=db,
            decode_responses=True
        )

    def cache_expertise_file(self, file_id: str, content: Dict, ttl_hours: int = 24):
        """Cache expertise file with metadata"""
        key = f"expertise:{file_id}"
        content_json = json.dumps(content)

        # Store with expiration
        self.redis_client.setex(
            key,
            timedelta(hours=ttl_hours),
            content_json
        )

        # Add to category index
        category = content.get('category', 'uncategorized')
        self.redis_client.sadd(f"category:{category}", file_id)

        # Add to tag indices
        for tag in content.get('tags', []):
            self.redis_client.sadd(f"tag:{tag}", file_id)

    def get_cached_expertise(self, file_id: str) -> Dict:
        """Retrieve cached expertise file"""
        key = f"expertise:{file_id}"
        cached_content = self.redis_client.get(key)

        if cached_content:
            return json.loads(cached_content)
        return None

    def search_expertise_by_category(self, category: str) -> List[str]:
        """Find expertise files by category"""
        file_ids = self.redis_client.smembers(f"category:{category}")
        return list(file_ids)

    def search_expertise_by_tags(self, tags: List[str]) -> List[str]:
        """Find expertise files with intersection of tags"""
        if not tags:
            return []

        # Get files for each tag
        tag_sets = [
            set(self.redis_client.smembers(f"tag:{tag}"))
            for tag in tags
        ]

        # Find intersection
        result_set = set.intersection(*tag_sets) if tag_sets else set()
        return list(result_set)

    def implement_access_tracking(self, file_id: str, user_id: str):
        """Track file access for analytics"""
        access_key = f"access:{file_id}"

        # Increment access count
        self.redis_client.incr(access_key)

        # Set expiration on access tracking
        self.redis_client.expire(access_key, timedelta(days=30))

        # Track user access pattern
        user_pattern_key = f"user_pattern:{user_id}"
        self.redis_client.lpush(user_pattern_key, file_id)
        self.redis_client.ltrim(user_pattern_key, 0, 99)  # Keep last 100
        self.redis_client.expire(user_pattern_key, timedelta(days=90))

    def cache_query_result(self, query_hash: str, result: List, ttl_minutes: int = 30):
        """Cache expensive search query results"""
        key = f"query_cache:{query_hash}"
        result_json = json.dumps(result)

        self.redis_client.setex(
            key,
            timedelta(minutes=ttl_minutes),
            result_json
        )

    def get_cached_query(self, query_hash: str) -> List:
        """Retrieve cached query result"""
        key = f"query_cache:{query_hash}"
        cached_result = self.redis_client.get(key)

        if cached_result:
            return json.loads(cached_result)
        return None
```

#### Pub/Sub for Real-time Knowledge Updates
```python
class KnowledgeUpdatePublisher:
    def __init__(self, redis_client):
        self.redis_client = redis_client

    def publish_file_update(self, event_type: str, file_id: str, data: Dict):
        """Publish file update events"""
        event = {
            'event_type': event_type,  # created, updated, deleted
            'file_id': file_id,
            'timestamp': datetime.utcnow().isoformat(),
            'data': data
        }

        # Publish to general channel
        self.redis_client.publish('knowledge_updates', json.dumps(event))

        # Publish to specific category channel
        category = data.get('category', 'general')
        self.redis_client.publish(f'category_{category}', json.dumps(event))

class KnowledgeUpdateSubscriber:
    def __init__(self, redis_client):
        self.redis_client = redis_client
        self.pubsub = self.redis_client.pubsub()

    def subscribe_to_updates(self, categories: List[str] = None):
        """Subscribe to knowledge update events"""
        channels = ['knowledge_updates']

        if categories:
            channels.extend([f'category_{cat}' for cat in categories])

        self.pubsub.subscribe(*channels)

    def listen_for_updates(self, callback):
        """Listen for updates and execute callback"""
        for message in self.pubsub.listen():
            if message['type'] == 'message':
                try:
                    event = json.loads(message['data'])
                    callback(event)
                except json.JSONDecodeError:
                    print(f"Invalid JSON in message: {message['data']}")
```

---

## Data Modeling and Schema Design

### Entity-Relationship Patterns for CSF

#### Knowledge System Data Model
```sql
-- Core expertise files table
CREATE TABLE expertise_files (
    file_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(200) NOT NULL,
    category VARCHAR(50) NOT NULL,
    expertise_level VARCHAR(20) NOT NULL CHECK (expertise_level IN ('junior', 'intermediate', 'senior', 'principal')),
    content TEXT NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_hash VARCHAR(64) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    view_count INTEGER DEFAULT 0,
    rating DECIMAL(3,2) DEFAULT 0.00,
    is_active BOOLEAN DEFAULT TRUE
);

-- Tags for flexible categorization
CREATE TABLE expertise_tags (
    tag_id SERIAL PRIMARY KEY,
    tag_name VARCHAR(50) UNIQUE NOT NULL,
    tag_category VARCHAR(50),  -- For tag hierarchy
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Many-to-many relationship between files and tags
CREATE TABLE expertise_file_tags (
    file_id UUID REFERENCES expertise_files(file_id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES expertise_tags(tag_id) ON DELETE CASCADE,
    PRIMARY KEY (file_id, tag_id)
);

-- Knowledge relationships (related files, dependencies, etc.)
CREATE TABLE expertise_relationships (
    relationship_id SERIAL PRIMARY KEY,
    source_file_id UUID REFERENCES expertise_files(file_id),
    target_file_id UUID REFERENCES expertise_files(file_id),
    relationship_type VARCHAR(50) NOT NULL CHECK (relationship_type IN ('related', 'dependency', 'prerequisite', 'supersedes')),
    strength DECIMAL(3,2) DEFAULT 1.0 CHECK (strength >= 0 AND strength <= 1),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_file_id, target_file_id, relationship_type)
);

-- Usage analytics
CREATE TABLE expertise_usage (
    usage_id BIGSERIAL PRIMARY KEY,
    file_id UUID REFERENCES expertise_files(file_id),
    user_id VARCHAR(100),
    access_type VARCHAR(50) NOT NULL CHECK (access_type IN ('view', 'search', 'download', 'reference')),
    query_context TEXT,
    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    session_id VARCHAR(100)
);

-- Indexes for performance
CREATE INDEX idx_expertise_files_category ON expertise_files(category);
CREATE INDEX idx_expertise_files_level ON expertise_files(expertise_level);
CREATE INDEX idx_expertise_files_active ON expertise_files(is_active) WHERE is_active = true;
CREATE INDEX idx_expertise_files_search ON expertise_files USING GIN(to_tsvector('english', title || ' ' || content));

-- Usage analytics indexes
CREATE INDEX idx_expertise_usage_file_time ON expertise_usage(file_id, accessed_at);
CREATE INDEX idx_expertise_usage_user_time ON expertise_usage(user_id, accessed_at);
```

#### Schema Evolution Patterns
```sql
-- Add new columns with backward compatibility
ALTER TABLE expertise_files
ADD COLUMN metadata JSONB DEFAULT '{}';

-- Create trigger for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_expertise_files_updated_at
    BEFORE UPDATE ON expertise_files
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add check constraints for data quality
ALTER TABLE expertise_files
ADD CONSTRAINT chk_expertise_rating
CHECK (rating >= 0 AND rating <= 5);

ALTER TABLE expertise_files
ADD CONSTRAINT chk_expertise_view_count
CHECK (view_count >= 0);

-- Table partitioning for high-volume usage data
CREATE TABLE expertise_usage_partitioned (
    LIKE expertise_usage INCLUDING ALL
) PARTITION BY RANGE (accessed_at);

-- Monthly partitions
CREATE TABLE expertise_usage_2025_12 PARTITION OF expertise_usage_partitioned
    FOR VALUES FROM ('2025-12-01') TO ('2026-01-01');

CREATE TABLE expertise_usage_2026_01 PARTITION OF expertise_usage_partitioned
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
```

---

## Performance Optimization

### Query Optimization Techniques

#### Full-Text Search Implementation
```sql
-- PostgreSQL full-text search setup
ALTER TABLE expertise_files
ADD COLUMN search_vector tsvector;

-- Create trigger for automatic search vector updates
CREATE OR REPLACE FUNCTION expertise_files_search_trigger()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector :=
        setweight(to_tsvector('english', COALESCE(NEW.title, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.content, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(string_agg(t.tag_name, ' '), '')), 'C');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER expertise_files_search_update
    BEFORE INSERT OR UPDATE ON expertise_files
    FOR EACH ROW EXECUTE FUNCTION expertise_files_search_trigger();

-- Search function with ranking
CREATE OR REPLACE FUNCTION search_expertise(
    search_query TEXT,
    category_filter VARCHAR(50) DEFAULT NULL,
    level_filter VARCHAR(20) DEFAULT NULL,
    limit_count INTEGER DEFAULT 10
)
RETURNS TABLE(
    file_id UUID,
    title VARCHAR(200),
    category VARCHAR(50),
    expertise_level VARCHAR(20),
    rank REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ef.file_id,
        ef.title,
        ef.category,
        ef.expertise_level,
        ts_rank(ef.search_vector, plainto_tsquery('english', search_query)) as rank
    FROM expertise_files ef
    WHERE
        ef.search_vector @@ plainto_tsquery('english', search_query)
        AND ef.is_active = true
        AND (category_filter IS NULL OR ef.category = category_filter)
        AND (level_filter IS NULL OR ef.expertise_level = level_filter)
    ORDER BY rank DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;
```

#### Materialized Views for Analytics
```sql
-- Usage analytics materialized view
CREATE MATERIALIZED VIEW expertise_usage_stats AS
SELECT
    ef.file_id,
    ef.title,
    ef.category,
    ef.expertise_level,
    COUNT(eu.usage_id) as total_accesses,
    COUNT(DISTINCT eu.user_id) as unique_users,
    MAX(eu.accessed_at) as last_accessed,
    AVG(eu.rating) as avg_rating  -- If ratings are stored in usage table
FROM expertise_files ef
LEFT JOIN expertise_usage eu ON ef.file_id = eu.file_id
WHERE ef.is_active = true
GROUP BY ef.file_id, ef.title, ef.category, ef.expertise_level
WITH DATA;

-- Create indexes on materialized view
CREATE INDEX idx_expertise_usage_stats_category ON expertise_usage_stats(category);
CREATE INDEX idx_expertise_usage_stats_level ON expertise_usage_stats(expertise_level);
CREATE INDEX idx_expertise_usage_stats_accesses ON expertise_usage_stats(total_accesses DESC);

-- Refresh strategy
CREATE OR REPLACE FUNCTION refresh_expertise_stats()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY expertise_usage_stats;
END;
$$ LANGUAGE plpgsql;

-- Schedule refresh (example with pg_cron)
SELECT cron.schedule('refresh-expertise-stats', '0 */4 * * *', 'SELECT refresh_expertise_stats();');
```

### Connection Pooling and Scaling

#### SQLAlchemy Advanced Configuration
```python
from sqlalchemy import create_engine, event
from sqlalchemy.pool import QueuePool, StaticPool
from sqlalchemy.orm import sessionmaker
import logging

# Production-ready database configuration
def create_database_engine(database_url: str, pool_size: int = 20):
    """Create optimized database engine for CSF knowledge system"""

    engine = create_engine(
        database_url,
        poolclass=QueuePool,
        pool_size=pool_size,
        max_overflow=30,  # Additional connections when pool is full
        pool_pre_ping=True,  # Validate connections before use
        pool_recycle=3600,  # Recycle connections after 1 hour
        echo=False,  # Disable SQL logging in production
        connect_args={
            "application_name": "csf_nip_knowledge_system",
            "connect_timeout": 10,
            "command_timeout": 30
        }
    )

    # Add event listeners for monitoring
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        if 'sqlite' in database_url:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.close()

    @event.listens_for(engine, "before_execute")
    def log_sql(conn, clauseelement, multiparams, params, execution_options):
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            logging.debug(f"SQL: {clauseelement}")

    return engine

# Read-write splitting for scalability
class DatabaseManager:
    def __init__(self, master_url: str, replica_urls: List[str] = None):
        self.master_engine = create_database_engine(master_url)

        # Create replica engines for read operations
        self.replica_engines = []
        if replica_urls:
            for replica_url in replica_urls:
                self.replica_engines.append(create_database_engine(replica_url))

        # Session factories
        self.master_session_factory = sessionmaker(bind=self.master_engine)

        if self.replica_engines:
            self.replica_session_factory = sessionmaker(bind=self.replica_engines[0])
        else:
            self.replica_session_factory = self.master_session_factory

    def get_read_session(self):
        """Get session for read operations (replica if available)"""
        return self.replica_session_factory()

    def get_write_session(self):
        """Get session for write operations (master)"""
        return self.master_session_factory()

    def close_all_connections(self):
        """Close all database connections"""
        self.master_engine.dispose()
        for engine in self.replica_engines:
            engine.dispose()
```

---

## Database Migration Patterns

### Version-Controlled Migrations

#### Alembic Migration Templates
```python
# alembic/versions/002_create_expertise_system.py
"""Create expertise management system

Revision ID: 002
Revises: 001
Create Date: 2025-12-21 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None

def upgrade():
    # Create expertise_files table
    op.create_table('expertise_files',
        sa.Column('file_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('expertise_level', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_hash', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.Column('view_count', sa.Integer(), nullable=True),
        sa.Column('rating', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('file_id'),
        sa.UniqueConstraint('file_hash')
    )

    # Create indexes
    op.create_index('idx_expertise_files_category', 'expertise_files', ['category'])
    op.create_index('idx_expertise_files_level', 'expertise_files', ['expertise_level'])
    op.create_index('idx_expertise_files_active', 'expertise_files', ['is_active'],
                    unique=False, postgresql_where=sa.text('is_active = true'))

def downgrade():
    op.drop_table('expertise_files')
```

#### Zero-Downtime Migration Strategy
```python
# Database migration manager for CSF
class ZeroDowntimeMigrator:
    def __init__(self, database_manager):
        self.db_manager = database_manager
        self.migration_steps = []

    def add_column_with_default(self, table_name: str, column_name: str,
                               column_type, default_value, nullable: bool = True):
        """Add column with default value in stages"""

        # Stage 1: Add column as nullable
        self.migration_steps.append(f"""
            ALTER TABLE {table_name}
            ADD COLUMN {column_name} {column_type} { 'NOT NULL' if not nullable else '' };
        """)

        # Stage 2: Update existing rows in batches
        self.migration_steps.append(f"""
            UPDATE {table_name}
            SET {column_name} = {default_value}
            WHERE {column_name} IS NULL;
        """)

        # Stage 3: Add NOT NULL constraint if needed
        if not nullable:
            self.migration_steps.append(f"""
                ALTER TABLE {table_name}
                ALTER COLUMN {column_name} SET NOT NULL;
            """)

    def execute_migration(self, batch_size: int = 1000):
        """Execute migration steps with proper error handling"""

        with self.db_manager.get_write_session() as session:
            try:
                for step in self.migration_steps:
                    if "UPDATE" in step and "WHERE" in step:
                        # Batch updates for large tables
                        self._execute_batch_update(session, step, batch_size)
                    else:
                        # Direct execution for DDL
                        session.execute(step)
                    session.commit()

            except Exception as e:
                session.rollback()
                raise e

    def _execute_batch_update(self, session, update_query: str, batch_size: int):
        """Execute update in batches to avoid long-running transactions"""

        # Extract table and conditions from query
        # This is simplified - real implementation would parse the query
        table_name = "expertise_files"  # Extract from query
        condition = "new_column IS NULL"  # Extract from query

        while True:
            # Process batch
            batch_query = f"""
                {update_query.split('UPDATE')[1].split('WHERE')[0].strip()}
                WHERE {condition}
                LIMIT {batch_size}
            """

            result = session.execute(batch_query)

            if result.rowcount == 0:
                break

            session.commit()

            # Small delay to prevent overwhelming the database
            time.sleep(0.1)
```

---

## Transaction Management and Consistency

### ACID Compliance Patterns

#### Optimistic Concurrency Control
```python
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from sqlalchemy import orm
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()

class ExpertiseFile(Base):
    __tablename__ = 'expertise_files'

    file_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(200), nullable=False)
    content = Column(String, nullable=False)
    view_count = Column(Integer, default=0)
    version = Column(Integer, nullable=False, default=1)
    updated_at = Column(DateTime, nullable=True)

    __mapper_args__ = {
        "version_id_col": version
    }

class ExpertiseRepository:
    def __init__(self, session: Session):
        self.session = session

    def update_file_with_conflict_detection(self, file_id: uuid.UUID,
                                          title: str = None,
                                          content: str = None) -> bool:
        """Update expertise file with optimistic locking"""

        try:
            expertise_file = self.session.query(ExpertiseFile).filter(
                ExpertiseFile.file_id == file_id
            ).first()

            if not expertise_file:
                return False

            # Update fields if provided
            if title is not None:
                expertise_file.title = title
            if content is not None:
                expertise_file.content = content

            expertise_file.updated_at = datetime.utcnow()

            self.session.commit()
            return True

        except orm.exc.StaleDataError:
            # Handle concurrent modification
            self.session.rollback()
            raise Exception(f"File {file_id} was modified by another process")

        except Exception as e:
            self.session.rollback()
            raise e

    def increment_view_count(self, file_id: uuid.UUID) -> bool:
        """Thread-safe view count increment"""

        try:
            # Use atomic update for better performance
            result = self.session.query(ExpertiseFile).filter(
                ExpertiseFile.file_id == file_id
            ).update({
                ExpertiseFile.view_count: ExpertiseFile.view_count + 1
            })

            self.session.commit()
            return result > 0

        except Exception as e:
            self.session.rollback()
            raise e
```

#### Distributed Transaction Patterns
```python
import asyncio
from typing import List, Callable, Any, Dict
from dataclasses import dataclass
from enum import Enum

class SagaStepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATED = "compensated"

@dataclass
class SagaStep:
    name: str
    execute: Callable
    compensate: Callable
    status: SagaStepStatus = SagaStepStatus.PENDING
    result: Any = None
    error: Exception = None

class KnowledgeSystemSaga:
    """Saga pattern for complex knowledge system operations"""

    def __init__(self):
        self.steps: List[SagaStep] = []
        self.executed_steps: List[SagaStep] = []

    def add_step(self, name: str, execute: Callable, compensate: Callable):
        """Add a step to the saga"""
        self.steps.append(SagaStep(name=name, execute=execute, compensate=compensate))

    async def execute(self) -> bool:
        """Execute all saga steps with compensation on failure"""

        try:
            for step in self.steps:
                step.status = SagaStepStatus.RUNNING

                try:
                    print(f"Executing step: {step.name}")
                    result = await step.execute()
                    step.result = result
                    step.status = SagaStepStatus.COMPLETED
                    self.executed_steps.append(step)

                except Exception as e:
                    step.status = SagaStepStatus.FAILED
                    step.error = e
                    raise e

            return True

        except Exception as e:
            print(f"Saga failed: {e}. Starting compensation...")
            await self.compensate()
            return False

    async def compensate(self):
        """Execute compensation for all executed steps in reverse order"""

        for step in reversed(self.executed_steps):
            if step.status == SagaStepStatus.COMPLETED:
                try:
                    print(f"Compensating step: {step.name}")
                    await step.compensate(step.result)
                    step.status = SagaStepStatus.COMPENSATED

                except Exception as e:
                    print(f"Compensation failed for step {step.name}: {e}")
                    # Log error but continue with other compensations

# Usage example for knowledge file processing
async def process_expertise_file_saga(file_data: Dict):
    """Saga for processing expertise files across multiple systems"""

    saga = KnowledgeSystemSaga()

    # Define saga steps
    async def validate_file(data):
        # Validate file structure and content
        if not data.get('title') or not data.get('content'):
            raise ValueError("Missing required fields")
        return {"validated": True, "data": data}

    async def store_in_database(data):
        # Store in primary database
        # This would interact with the database layer
        return {"db_id": "temp_id", "stored": True}

    async def index_for_search(data):
        # Index for full-text search
        # This would interact with Elasticsearch or similar
        return {"indexed": True}

    async def cache_content(data):
        # Cache in Redis for fast access
        # This would interact with the cache layer
        return {"cached": True}

    # Compensation functions
    async def remove_from_database(data):
        # Remove from database
        pass

    async def remove_from_search_index(data):
        # Remove from search index
        pass

    async def remove_from_cache(data):
        # Remove from cache
        pass

    # Add steps to saga
    saga.add_step("validate", validate_file, lambda x: None)
    saga.add_step("store_db", store_in_database, remove_from_database)
    saga.add_step("index_search", index_for_search, remove_from_search_index)
    saga.add_step("cache", cache_content, remove_from_cache)

    return await saga.execute()
```

---

## ORM Patterns and Best Practices

### SQLAlchemy Advanced Patterns

#### Repository Pattern Implementation
```python
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc

T = TypeVar('T')

class BaseRepository(ABC, Generic[T]):
    """Base repository pattern implementation"""

    def __init__(self, session: Session, model_class: T):
        self.session = session
        self.model_class = model_class

    def create(self, **kwargs) -> T:
        """Create new entity"""
        entity = self.model_class(**kwargs)
        self.session.add(entity)
        self.session.flush()
        return entity

    def get_by_id(self, entity_id) -> Optional[T]:
        """Get entity by ID"""
        return self.session.query(self.model_class).filter(
            self.model_class.id == entity_id
        ).first()

    def get_all(self, limit: int = None, offset: int = None) -> List[T]:
        """Get all entities with pagination"""
        query = self.session.query(self.model_class)

        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)

        return query.all()

    def update(self, entity_id: int, **kwargs) -> Optional[T]:
        """Update entity"""
        entity = self.get_by_id(entity_id)
        if entity:
            for key, value in kwargs.items():
                setattr(entity, key, value)
            self.session.flush()
        return entity

    def delete(self, entity_id: int) -> bool:
        """Delete entity"""
        entity = self.get_by_id(entity_id)
        if entity:
            self.session.delete(entity)
            self.session.flush()
            return True
        return False

class ExpertiseRepository(BaseRepository[ExpertiseFile]):
    """Specialized repository for expertise files"""

    def __init__(self, session: Session):
        super().__init__(session, ExpertiseFile)

    def search_by_content(self, query: str, category: str = None,
                         expertise_level: str = None) -> List[ExpertiseFile]:
        """Search expertise files by content"""

        filters = []

        if category:
            filters.append(ExpertiseFile.category == category)
        if expertise_level:
            filters.append(ExpertiseFile.expertise_level == expertise_level)

        # Full-text search
        if query:
            search_filter = or_(
                ExpertiseFile.title.ilike(f'%{query}%'),
                ExpertiseFile.content.ilike(f'%{query}%')
            )
            filters.append(search_filter)

        return self.session.query(ExpertiseFile).filter(
            and_(*filters)
        ).order_by(desc(ExpertiseFile.view_count)).all()

    def get_related_files(self, file_id: uuid.UUID, limit: int = 5) -> List[ExpertiseFile]:
        """Get related expertise files based on category and tags"""

        source_file = self.get_by_id(file_id)
        if not source_file:
            return []

        # Find files in same category
        query = self.session.query(ExpertiseFile).filter(
            and_(
                ExpertiseFile.category == source_file.category,
                ExpertiseFile.file_id != file_id,
                ExpertiseFile.is_active == True
            )
        )

        # This would be enhanced with tag-based recommendations
        return query.order_by(desc(ExpertiseFile.rating)).limit(limit).all()

    def get_popular_files(self, category: str = None, limit: int = 10) -> List[ExpertiseFile]:
        """Get most popular expertise files"""

        query = self.session.query(ExpertiseFile).filter(
            ExpertiseFile.is_active == True
        )

        if category:
            query = query.filter(ExpertiseFile.category == category)

        return query.order_by(
            desc(ExpertiseFile.view_count),
            desc(ExpertiseFile.rating)
        ).limit(limit).all()
```

#### Database-Agnostic Patterns
```python
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, DateTime, Boolean, String
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class BaseModel(Base):
    """Base model with common fields for all entities"""

    __abstract__ = True

    id = Column(Integer, primary_key=True)
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        server_default=func.now(),
        nullable=False
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        server_default=func.now(),
        nullable=False
    )
    is_active = Column(Boolean, default=True, nullable=False)
    created_by = Column(String(100), nullable=True)

    # Soft delete functionality
    def soft_delete(self):
        """Mark entity as deleted"""
        self.is_active = False
        self.updated_at = datetime.utcnow()

    # Restore from soft delete
    def restore(self):
        """Restore soft-deleted entity"""
        self.is_active = True
        self.updated_at = datetime.utcnow()

    def to_dict(self, exclude_fields: List[str] = None):
        """Convert entity to dictionary"""
        exclude_fields = exclude_fields or []
        result = {}

        for column in self.__table__.columns:
            if column.name not in exclude_fields:
                value = getattr(self, column.name)
                if isinstance(value, datetime):
                    value = value.isoformat()
                result[column.name] = value

        return result

class AuditMixin(Base):
    """Mixin for audit trail functionality"""

    __abstract__ = True

    modified_by = Column(String(100), nullable=True)
    version = Column(Integer, default=1, nullable=False)

    def increment_version(self):
        """Increment version number"""
        self.version += 1

# Usage example
class ExpertiseFile(BaseModel, AuditMixin):
    __tablename__ = 'expertise_files'

    title = Column(String(200), nullable=False)
    content = Column(String, nullable=False)
    category = Column(String(50), nullable=False)
    expertise_level = Column(String(20), nullable=False)
    view_count = Column(Integer, default=0)
    rating = Column(Integer, default=0)
    file_hash = Column(String(64), nullable=False)

    def __repr__(self):
        return f"<ExpertiseFile(id={self.id}, title='{self.title}', category='{self.category}')>"
```

---

## Data Integrity and Validation

### Constraint Implementation

#### Multi-column Constraints
```sql
-- Complex check constraints for expertise files
ALTER TABLE expertise_files
ADD CONSTRAINT chk_expertise_level
CHECK (expertise_level IN ('junior', 'intermediate', 'senior', 'principal'));

ALTER TABLE expertise_files
ADD CONSTRAINT chk_expertise_rating
CHECK (rating >= 0 AND rating <= 5);

ALTER TABLE expertise_files
ADD CONSTRAINT chk_view_count_positive
CHECK (view_count >= 0);

-- Conditional unique constraints
CREATE UNIQUE INDEX idx_unique_active_title_category
ON expertise_files (title, category)
WHERE is_active = true;

-- Exclusion constraints for time-based data (PostgreSQL)
CREATE TABLE expertise_file_versions (
    version_id SERIAL PRIMARY KEY,
    file_id UUID NOT NULL,
    version_number INTEGER NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    is_current BOOLEAN DEFAULT false,
    EXCLUDE USING GIST (
        file_id WITH =,
        version_number WITH =
    )
);
```

#### Data Validation with Triggers
```sql
-- Comprehensive validation trigger for expertise files
CREATE OR REPLACE FUNCTION validate_expertise_file()
RETURNS TRIGGER AS $$
BEGIN
    -- Validate required fields
    IF NEW.title IS NULL OR TRIM(NEW.title) = '' THEN
        RAISE EXCEPTION 'Title cannot be null or empty';
    END IF;

    IF NEW.content IS NULL OR TRIM(NEW.content) = '' THEN
        RAISE EXCEPTION 'Content cannot be null or empty';
    END IF;

    IF NEW.category IS NULL OR TRIM(NEW.category) = '' THEN
        RAISE EXCEPTION 'Category cannot be null or empty';
    END IF;

    -- Validate expertise level
    IF NEW.expertise_level NOT IN ('junior', 'intermediate', 'senior', 'principal') THEN
        RAISE EXCEPTION 'Invalid expertise level: %', NEW.expertise_level;
    END IF;

    -- Validate file hash length (SHA-256)
    IF LENGTH(NEW.file_hash) != 64 THEN
        RAISE EXCEPTION 'Invalid file hash length';
    END IF;

    -- Validate rating range
    IF NEW.rating < 0 OR NEW.rating > 5 THEN
        RAISE EXCEPTION 'Rating must be between 0 and 5';
    END IF;

    -- Validate view count is non-negative
    IF NEW.view_count < 0 THEN
        RAISE EXCEPTION 'View count cannot be negative';
    END IF;

    -- Auto-update timestamp
    NEW.updated_at = CURRENT_TIMESTAMP;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_validate_expertise_file
    BEFORE INSERT OR UPDATE ON expertise_files
    FOR EACH ROW EXECUTE FUNCTION validate_expertise_file();

-- Trigger for usage analytics
CREATE OR REPLACE FUNCTION log_expertise_access()
RETURNS TRIGGER AS $$
BEGIN
    -- Log file access for analytics
    INSERT INTO expertise_usage (file_id, access_type, accessed_at)
    VALUES (NEW.file_id, 'view', CURRENT_TIMESTAMP)
    ON CONFLICT DO NOTHING;

    -- Increment view count
    UPDATE expertise_files
    SET view_count = view_count + 1
    WHERE file_id = NEW.file_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- This would be called by the application layer when a file is accessed
```

---

## Backup and Recovery Strategies

### Automated Backup Solutions

#### PostgreSQL Backup Scripts for CSF
```bash
#!/bin/bash
# backup_csf_nip_database.sh - Comprehensive backup for CSF knowledge system

set -e

# Configuration
DB_NAME="csf_nip_knowledge"
DB_USER="csf_backup_user"
BACKUP_DIR="/backups/csf_nip/database"
RETENTION_DAYS=30
DATE=$(date +%Y%m%d_%H%M%S)
S3_BUCKET="csf-backups"  # Optional cloud storage

# Create backup directory
mkdir -p $BACKUP_DIR/{full,differential,schema}

# Full database backup with compression
echo "Starting full database backup..."
pg_dump -U $DB_USER -h localhost -d $DB_NAME \
    --format=custom \
    --compress=9 \
    --verbose \
    --jobs=4 \
    --file="$BACKUP_DIR/full/csf_nip_full_$DATE.dump"

# Schema-only backup
echo "Creating schema backup..."
pg_dump -U $DB_USER -h localhost -d $DB_NAME \
    --schema-only \
    --file="$BACKUP_DIR/schema/csf_nip_schema_$DATE.sql"

# Critical tables data backup
echo "Backing up critical tables..."
tables=("expertise_files" "expertise_usage" "expertise_tags" "expertise_relationships")

for table in "${tables[@]}"; do
    pg_dump -U $DB_USER -h localhost -d $DB_NAME \
        --data-only \
        --table=$table \
        --file="$BACKUP_DIR/full/${table}_data_$DATE.sql"
done

# Create differential backup (changes since last full backup)
if [ -f "$BACKUP_DIR/full/last_full_backup.txt" ]; then
    last_backup_date=$(cat "$BACKUP_DIR/full/last_full_backup.txt")
    echo "Creating differential backup since $last_backup_date..."

    pg_dump -U $DB_USER -h localhost -d $DB_NAME \
        --format=custom \
        --compress=9 \
        --data-only \
        --file="$BACKUP_DIR/differential/csf_nip_diff_$DATE.dump"
fi

# Backup verification
echo "Verifying backup integrity..."
pg_restore --list "$BACKUP_DIR/full/csf_nip_full_$DATE.dump" > /dev/null
if [ $? -eq 0 ]; then
    echo "✓ Backup verification successful: $DATE"

    # Update last backup timestamp
    echo "$DATE" > "$BACKUP_DIR/full/last_full_backup.txt"
else
    echo "✗ Backup verification failed: $DATE"
    exit 1
fi

# Generate backup report
cat > "$BACKUP_DIR/backup_report_$DATE.txt" << EOF
CSF Database Backup Report
==============================
Date: $(date)
Backup ID: $DATE
Database: $DB_NAME

Backup Files:
- Full: csf_nip_full_$DATE.dump
- Schema: csf_nip_schema_$DATE.sql
- Differential: ${differential_file:-"N/A"}

Backup Sizes:
$(du -h $BACKUP_DIR/full/csf_nip_full_$DATE.dump)
$(du -h $BACKUP_DIR/schema/csf_nip_schema_$DATE.sql)

Verification Status: PASSED
EOF

# Optional: Upload to cloud storage
if command -v aws &> /dev/null && [ ! -z "$S3_BUCKET" ]; then
    echo "Uploading backup to S3..."
    aws s3 cp "$BACKUP_DIR/full/csf_nip_full_$DATE.dump" "s3://$S3_BUCKET/database/full/"
    aws s3 cp "$BACKUP_DIR/schema/csf_nip_schema_$DATE.sql" "s3://$S3_BUCKET/database/schema/"
    aws s3 cp "$BACKUP_DIR/backup_report_$DATE.txt" "s3://$S3_BUCKET/database/reports/"
fi

# Cleanup old backups
echo "Cleaning up old backups..."
find $BACKUP_DIR/full -name "*.dump" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR/differential -name "*.dump" -mtime +7 -delete  # Keep differentials for 7 days
find $BACKUP_DIR/schema -name "*.sql" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR -name "backup_report_*.txt" -mtime +$RETENTION_DAYS -delete

# Log backup completion
echo "$(date): CSF database backup completed successfully" >> $BACKUP_DIR/backup.log

echo "Backup process completed successfully!"
```

#### Point-in-Time Recovery Setup
```sql
-- Enable WAL archiving for point-in-time recovery
-- Add to postgresql.conf:
-- wal_level = replica
-- archive_mode = on
-- archive_command = 'cp %p /backup/wal_archive/%f'
-- max_wal_senders = 3
-- wal_keep_segments = 64

-- Create recovery configuration template
-- recovery.conf.template:
-- restore_command = 'cp /backup/wal_archive/%f %p'
-- recovery_target_time = '2025-12-21 15:30:00'
-- recovery_target_inclusive = true
-- recovery_target_action = 'promote'

-- Function to create restore point
CREATE OR REPLACE FUNCTION create_restore_point(point_name TEXT)
RETURNS TEXT AS $$
DECLARE
    restore_point_name TEXT;
BEGIN
    -- Generate unique restore point name
    restore_point_name := point_name || '_' || to_char(now(), 'YYYY_MM_DD_HH24_MI_SS');

    -- Create restore point
    EXECUTE format('SELECT pg_create_restore_point(%L)', restore_point_name);

    -- Log restore point creation
    INSERT INTO restore_point_log (point_name, created_at, created_by)
    VALUES (restore_point_name, now(), current_user);

    RETURN restore_point_name;
END;
$$ LANGUAGE plpgsql;

-- Table to track restore points
CREATE TABLE restore_point_log (
    id SERIAL PRIMARY KEY,
    point_name TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP NOT NULL,
    created_by TEXT NOT NULL,
    description TEXT
);
```

---

## Query Optimization Techniques

### Advanced Indexing Strategies

#### Specialized Indexes for Knowledge System
```sql
-- Composite index for common search patterns
CREATE INDEX idx_expertise_search_main ON expertise_files
(category, expertise_level, is_active)
INCLUDE (title, rating);

-- Partial index for active files only
CREATE INDEX idx_expertise_active_files ON expertise_files
USING GIN (to_tsvector('english', title || ' ' || content))
WHERE is_active = true;

-- Expression index for title search
CREATE INDEX idx_expertise_title_search ON expertise_files
USING GIN (to_tsvector('english', title));

-- Tag search optimization
CREATE INDEX idx_expertise_file_tags ON expertise_file_tags (tag_id, file_id);

-- Usage analytics optimization
CREATE INDEX idx_expertise_usage_analytics ON expertise_usage
(file_id, accessed_at DESC)
WHERE accessed_at > CURRENT_DATE - INTERVAL '90 days';

-- Create search results materialized view
CREATE MATERIALIZED VIEW popular_expertise_by_category AS
SELECT
    ef.category,
    ef.expertise_level,
    ef.file_id,
    ef.title,
    ef.rating,
    ef.view_count,
    COUNT(eu.usage_id) as recent_accesses,
    AVG(eu.rating) as avg_user_rating
FROM expertise_files ef
LEFT JOIN expertise_usage eu ON ef.file_id = eu.file_id
    AND eu.accessed_at > CURRENT_DATE - INTERVAL '30 days'
WHERE ef.is_active = true
GROUP BY ef.category, ef.expertise_level, ef.file_id, ef.title, ef.rating, ef.view_count
HAVING COUNT(eu.usage_id) > 0 OR ef.view_count > 10
WITH DATA;

-- Index the materialized view
CREATE INDEX idx_popular_expertise_category ON popular_expertise_by_category (category, recent_accesses DESC);
CREATE INDEX idx_popular_expertise_level ON popular_expertise_by_category (expertise_level, rating DESC);
```

#### Query Optimization Examples
```sql
-- Before: Inefficient query with multiple subqueries
SELECT
    ef.file_id,
    ef.title,
    ef.category,
    (SELECT COUNT(*) FROM expertise_usage eu1 WHERE eu1.file_id = ef.file_id) as total_views,
    (SELECT AVG(eu2.rating) FROM expertise_usage eu2 WHERE eu2.file_id = ef.file_id AND eu2.rating IS NOT NULL) as avg_rating
FROM expertise_files ef
WHERE ef.category = 'database' AND ef.is_active = true;

-- After: Optimized with JOINs and aggregation
SELECT
    ef.file_id,
    ef.title,
    ef.category,
    COALESCE(stats.view_count, 0) as total_views,
    COALESCE(stats.avg_rating, 0) as avg_rating
FROM expertise_files ef
LEFT JOIN (
    SELECT
        file_id,
        COUNT(*) as view_count,
        AVG(CASE WHEN rating IS NOT NULL THEN rating END) as avg_rating
    FROM expertise_usage
    GROUP BY file_id
) stats ON ef.file_id = stats.file_id
WHERE ef.category = 'database' AND ef.is_active = true;

-- Advanced search with ranking
WITH search_results AS (
    SELECT
        ef.file_id,
        ef.title,
        ef.category,
        ef.expertise_level,
        ef.rating,
        ef.view_count,
        -- Full-text search rank
        ts_rank(
            to_tsvector('english', ef.title || ' ' || ef.content),
            plainto_tsquery('english', 'database performance')
        ) as search_rank,
        -- Popularity score
        (ef.rating * 0.6 + LOG(ef.view_count + 1) * 0.4) as popularity_score
    FROM expertise_files ef
    WHERE
        ef.is_active = true
        AND to_tsvector('english', ef.title || ' ' || ef.content) @@ plainto_tsquery('english', 'database performance')
)
SELECT *,
    (search_rank * 0.7 + popularity_score * 0.3) as combined_score
FROM search_results
WHERE category = 'database'
ORDER BY combined_score DESC
LIMIT 20;
```

---

## Database Security Best Practices

### Access Control Implementation

#### Row-Level Security for Multi-Tenant System
```sql
-- Enable RLS on expertise_files
ALTER TABLE expertise_files ENABLE ROW LEVEL SECURITY;

-- Policy for users to see their own files and public files
CREATE POLICY user_file_access_policy ON expertise_files
    FOR ALL
    TO application_user
    USING (
        created_by = current_user
        OR is_public = true
    );

-- Policy for editors to update files in their expertise areas
CREATE POLICY editor_update_policy ON expertise_files
    FOR UPDATE
    TO editor_user
    USING (
        category IN (SELECT category FROM user_expertise_areas WHERE user_id = current_user)
    );

-- Policy for admins to have full access
CREATE POLICY admin_full_access_policy ON expertise_files
    FOR ALL
    TO admin_user
    USING (true);

-- Function to set application context
CREATE OR REPLACE FUNCTION set_application_context(user_id TEXT, user_roles TEXT[])
RETURNS void AS $$
BEGIN
    PERFORM set_config('app.current_user_id', user_id, true);
    PERFORM set_config('app.user_roles', array_to_string(user_roles, ','), true);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Enhanced security policy using application context
CREATE POLICY context_based_access ON expertise_files
    FOR ALL
    TO application_user
    USING (
        -- Users can see their own files
        created_by = current_setting('app.current_user_id', true)
        OR
        -- Users can see files in their authorized categories
        category = ANY (
            SELECT category
            FROM user_category_permissions
            WHERE user_id = current_setting('app.current_user_id', true)
        )
        OR
        -- Public files are visible to all
        is_public = true
    );
```

#### Comprehensive Audit Logging
```sql
-- Enhanced audit table
CREATE TABLE comprehensive_audit_log (
    audit_id BIGSERIAL PRIMARY KEY,
    table_name VARCHAR(50) NOT NULL,
    operation VARCHAR(10) NOT NULL,
    user_id VARCHAR(100) NOT NULL,
    session_id VARCHAR(100),
    record_id VARCHAR(100),
    old_values JSONB,
    new_values JSONB,
    changed_fields JSONB,
    ip_address INET,
    user_agent TEXT,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    affected_rows INTEGER,
    transaction_id VARCHAR(100),
    CONSTRAINT chk_operation CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE', 'SELECT'))
);

-- Generic audit trigger function with field-level tracking
CREATE OR REPLACE FUNCTION enhanced_audit_trigger_function()
RETURNS TRIGGER AS $$
DECLARE
    changed_fields JSONB;
    field_value JSONB;
BEGIN
    -- Build changed fields JSON for UPDATE operations
    IF TG_OP = 'UPDATE' THEN
        changed_fields := '{}'::jsonb;

        -- Compare each column
        FOR column_name IN
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = TG_TABLE_NAME
            AND column_name NOT IN ('created_at', 'updated_at')
        LOOP
            -- Use dynamic SQL to compare old and new values
            EXECUTE format('SELECT to_jsonb(OLD.%I), to_jsonb(NEW.%I)', column_name, column_name)
            INTO old_val, new_val;

            IF old_val IS DISTINCT FROM new_val THEN
                changed_fields := jsonb_set(changed_fields,
                    array[column_name],
                    jsonb_build_object('old', old_val, 'new', new_val)
                );
            END IF;
        END LOOP;
    END IF;

    -- Insert audit record
    INSERT INTO comprehensive_audit_log (
        table_name, operation, user_id, session_id, record_id,
        old_values, new_values, changed_fields, ip_address, user_agent,
        affected_rows, transaction_id
    )
    VALUES (
        TG_TABLE_NAME,
        TG_OP,
        current_user,
        current_setting('app.session_id', true),
        CASE
            WHEN TG_OP = 'DELETE' THEN OLD.id::text
            WHEN TG_OP IN ('INSERT', 'UPDATE') THEN NEW.id::text
            ELSE NULL
        END,
        CASE WHEN TG_OP IN ('UPDATE', 'DELETE') THEN row_to_json(OLD) END,
        CASE WHEN TG_OP IN ('INSERT', 'UPDATE') THEN row_to_json(NEW) END,
        changed_fields,
        inet_client_addr(),
        current_setting('app.user_agent', true),
        1,
        current_setting('app.transaction_id', true)
    );

    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Apply enhanced audit trigger
CREATE TRIGGER enhanced_expertise_files_audit
    AFTER INSERT OR UPDATE OR DELETE ON expertise_files
    FOR EACH ROW EXECUTE FUNCTION enhanced_audit_trigger_function();
```

---

## Multi-Database Architectures

### Polyglot Persistence for CSF

#### Database Selection Matrix for Knowledge System

| Use Case | Recommended Database | Key Features | CSF Integration |
|----------|---------------------|--------------|-------------------|
| Core Knowledge Data | PostgreSQL | ACID, JSONB, Full-text Search | Primary storage for expertise files |
| Search Indexing | Elasticsearch | Full-text search, faceting, relevance | Advanced content discovery |
| Session Cache | Redis | In-memory, TTL, Pub/Sub | User sessions, real-time updates |
| Analytics Data | ClickHouse | Columnar, fast aggregations | Usage analytics, reporting |
| File Metadata | MongoDB | Flexible schema, document storage | File versioning, metadata |
| Graph Relationships | Neo4j | Relationship queries, traversals | Knowledge graph, connections |

#### Cross-Database Synchronization Implementation
```python
import asyncio
from typing import Dict, List, Any
import json
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

class DataSyncOperation(Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"

@dataclass
class SyncEvent:
    operation: DataSyncOperation
    entity_type: str
    entity_id: str
    data: Dict[str, Any]
    timestamp: datetime
    source_db: str
    target_dbs: List[str]

class CSFDataSyncManager:
    """Manages data synchronization across multiple databases"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.databases = {}
        self.sync_queue = asyncio.Queue()
        self.setup_databases()

    def setup_databases(self):
        """Initialize database connections"""
        # PostgreSQL (Primary)
        self.databases['postgresql'] = self._setup_postgresql()

        # Elasticsearch (Search)
        self.databases['elasticsearch'] = self._setup_elasticsearch()

        # Redis (Cache)
        self.databases['redis'] = self._setup_redis()

        # MongoDB (Metadata)
        self.databases['mongodb'] = self._setup_mongodb()

    async def sync_expertise_file(self, operation: DataSyncOperation,
                                 file_data: Dict[str, Any]) -> bool:
        """Sync expertise file across all relevant databases"""

        event = SyncEvent(
            operation=operation,
            entity_type="expertise_file",
            entity_id=file_data.get('file_id'),
            data=file_data,
            timestamp=datetime.utcnow(),
            source_db="postgresql",
            target_dbs=["elasticsearch", "redis", "mongodb"]
        )

        return await self._process_sync_event(event)

    async def _process_sync_event(self, event: SyncEvent) -> bool:
        """Process sync event with error handling and retries"""

        success_count = 0
        total_targets = len(event.target_dbs)

        for target_db in event.target_dbs:
            try:
                if target_db == "elasticsearch":
                    await self._sync_to_elasticsearch(event)
                elif target_db == "redis":
                    await self._sync_to_redis(event)
                elif target_db == "mongodb":
                    await self._sync_to_mongodb(event)

                success_count += 1
                print(f"✓ Synced {event.entity_id} to {target_db}")

            except Exception as e:
                print(f"✗ Failed to sync {event.entity_id} to {target_db}: {e}")

                # Add to retry queue
                await self._queue_retry(event, target_db, str(e))

        return success_count == total_targets

    async def _sync_to_elasticsearch(self, event: SyncEvent):
        """Sync to Elasticsearch for search functionality"""

        es_client = self.databases['elasticsearch']
        index_name = "expertise_files"

        if event.operation == DataSyncOperation.DELETE:
            await es_client.delete(
                index=index_name,
                id=event.entity_id
            )
        else:
            # Prepare document for ES
            doc = {
                "title": event.data.get('title'),
                "content": event.data.get('content'),
                "category": event.data.get('category'),
                "expertise_level": event.data.get('expertise_level'),
                "tags": event.data.get('tags', []),
                "rating": event.data.get('rating', 0),
                "view_count": event.data.get('view_count', 0),
                "created_at": event.data.get('created_at'),
                "updated_at": event.data.get('updated_at'),
                "is_active": event.data.get('is_active', True)
            }

            await es_client.index(
                index=index_name,
                id=event.entity_id,
                body=doc
            )

    async def _sync_to_redis(self, event: SyncEvent):
        """Sync to Redis for caching"""

        redis_client = self.databases['redis']

        cache_key = f"expertise:{event.entity_id}"

        if event.operation == DataSyncOperation.DELETE:
            await redis_client.delete(cache_key)
        else:
            # Cache with TTL
            cache_data = {
                "title": event.data.get('title'),
                "category": event.data.get('category'),
                "expertise_level": event.data.get('expertise_level'),
                "rating": event.data.get('rating', 0)
            }

            await redis_client.setex(
                cache_key,
                timedelta(hours=24),
                json.dumps(cache_data)
            )

            # Update category and tag indices
            category = event.data.get('category')
            if category:
                await redis_client.sadd(f"category:{category}", event.entity_id)

            for tag in event.data.get('tags', []):
                await redis_client.sadd(f"tag:{tag}", event.entity_id)

    async def _sync_to_mongodb(self, event: SyncEvent):
        """Sync to MongoDB for metadata and analytics"""

        mongo_client = self.databases['mongodb']
        collection = mongo_client.csf_nip.expertise_metadata

        if event.operation == DataSyncOperation.DELETE:
            await collection.delete_one({"file_id": event.entity_id})
        else:
            # Prepare metadata document
            metadata = {
                "file_id": event.entity_id,
                "title": event.data.get('title'),
                "category": event.data.get('category'),
                "expertise_level": event.data.get('expertise_level'),
                "tags": event.data.get('tags', []),
                "access_patterns": {
                    "daily_views": 0,
                    "weekly_views": 0,
                    "monthly_views": 0
                },
                "search_metrics": {
                    "search_frequency": 0,
                    "avg_search_rank": 0,
                    "click_through_rate": 0
                },
                "created_at": event.data.get('created_at'),
                "updated_at": event.data.get('updated_at'),
                "last_synced": datetime.utcnow()
            }

            await collection.replace_one(
                {"file_id": event.entity_id},
                metadata,
                upsert=True
            )

    async def _queue_retry(self, event: SyncEvent, target_db: str, error: str):
        """Queue failed sync for retry"""

        retry_data = {
            "event": event.__dict__,
            "target_db": target_db,
            "error": error,
            "retry_count": 0,
            "last_attempt": datetime.utcnow()
        }

        # Store in retry queue (could be Redis or database)
        await self.sync_queue.put(retry_data)

    async def process_retry_queue(self):
        """Process failed sync attempts"""

        while True:
            try:
                retry_data = await asyncio.wait_for(
                    self.sync_queue.get(),
                    timeout=60.0
                )

                # Exponential backoff for retries
                retry_count = retry_data.get('retry_count', 0)
                if retry_count < 5:  # Max 5 retries
                    delay = min(300, 2 ** retry_count)  # Max 5 minutes

                    await asyncio.sleep(delay)

                    event = SyncEvent(**retry_data['event'])
                    target_db = retry_data['target_db']

                    success = await self._process_single_sync(event, target_db)

                    if not success:
                        retry_data['retry_count'] += 1
                        retry_data['last_attempt'] = datetime.utcnow()
                        await self.sync_queue.put(retry_data)

            except asyncio.TimeoutError:
                continue  # No items in queue
            except Exception as e:
                print(f"Error in retry queue: {e}")
                await asyncio.sleep(60)  # Wait before retrying
```

---

## Monitoring and Observability

### Database Health Monitoring

#### Comprehensive Health Check System
```python
import asyncio
import time
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import psutil
from sqlalchemy import text
import redis
from pymongo import MongoClient
import elasticsearch

@dataclass
class DatabaseHealthStatus:
    name: str
    status: str  # healthy, degraded, unhealthy
    response_time: float
    error_message: Optional[str]
    metrics: Dict[str, Any]
    timestamp: datetime

class DatabaseHealthMonitor:
    """Comprehensive health monitoring for CSF databases"""

    def __init__(self, database_configs: Dict[str, Dict]):
        self.database_configs = database_configs
        self.alert_thresholds = {
            'response_time_ms': 1000,
            'connection_usage_percent': 80,
            'memory_usage_percent': 85,
            'disk_usage_percent': 90,
            'error_rate_percent': 5
        }
        self.health_history = {}

    async def check_all_databases(self) -> Dict[str, DatabaseHealthStatus]:
        """Check health of all configured databases"""

        health_status = {}
        tasks = []

        # Create tasks for each database check
        for db_name, config in self.database_configs.items():
            task = asyncio.create_task(
                self._check_database_health(db_name, config)
            )
            tasks.append((db_name, task))

        # Wait for all checks to complete
        for db_name, task in tasks:
            try:
                status = await task
                health_status[db_name] = status

                # Store in history
                if db_name not in self.health_history:
                    self.health_history[db_name] = []
                self.health_history[db_name].append(status)

                # Keep only last 100 entries
                if len(self.health_history[db_name]) > 100:
                    self.health_history[db_name] = self.health_history[db_name][-100:]

            except Exception as e:
                health_status[db_name] = DatabaseHealthStatus(
                    name=db_name,
                    status='unhealthy',
                    response_time=0,
                    error_message=str(e),
                    metrics={},
                    timestamp=datetime.utcnow()
                )

        return health_status

    async def _check_database_health(self, db_name: str, config: Dict) -> DatabaseHealthStatus:
        """Check health of a specific database"""

        start_time = time.time()

        try:
            if db_name == 'postgresql':
                return await self._check_postgresql_health(config, start_time)
            elif db_name == 'redis':
                return await self._check_redis_health(config, start_time)
            elif db_name == 'mongodb':
                return await self._check_mongodb_health(config, start_time)
            elif db_name == 'elasticsearch':
                return await self._check_elasticsearch_health(config, start_time)
            else:
                raise ValueError(f"Unknown database type: {db_name}")

        except Exception as e:
            response_time = (time.time() - start_time) * 1000

            return DatabaseHealthStatus(
                name=db_name,
                status='unhealthy',
                response_time=response_time,
                error_message=str(e),
                metrics={},
                timestamp=datetime.utcnow()
            )

    async def _check_postgresql_health(self, config: Dict, start_time: float) -> DatabaseHealthStatus:
        """Check PostgreSQL database health"""

        from sqlalchemy import create_engine

        engine = create_engine(config['connection_string'])

        with engine.connect() as conn:
            # Basic connectivity test
            conn.execute(text('SELECT 1'))

            # Get detailed metrics
            metrics = {}

            # Connection info
            conn_info = conn.execute(text("""
                SELECT
                    count(*) as active_connections,
                    count(*) FILTER (WHERE state = 'active') as active_queries
                FROM pg_stat_activity
            """)).fetchone()

            metrics.update({
                'active_connections': conn_info.active_connections,
                'active_queries': conn_info.active_queries
            })

            # Database size and table counts
            db_info = conn.execute(text("""
                SELECT
                    pg_size_pretty(pg_database_size(current_database())) as db_size,
                    (SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public') as table_count
            """)).fetchone()

            metrics.update({
                'database_size': db_info.db_size,
                'table_count': db_info.table_count
            })

            # Replication status (if applicable)
            try:
                repl_info = conn.execute(text("""
                    SELECT
                        pg_is_in_recovery() as is_replica,
                        pg_last_xact_replay_timestamp() as last_replay
                """)).fetchone()

                metrics.update({
                    'is_replica': repl_info.is_replica,
                    'last_replay': repl_info.last_replay
                })
            except:
                metrics['replication_info'] = 'Not available'

            response_time = (time.time() - start_time) * 1000

            # Determine health status
            status = self._determine_health_status(metrics, response_time)

            return DatabaseHealthStatus(
                name='postgresql',
                status=status,
                response_time=response_time,
                error_message=None,
                metrics=metrics,
                timestamp=datetime.utcnow()
            )

    async def _check_redis_health(self, config: Dict, start_time: float) -> DatabaseHealthStatus:
        """Check Redis health"""

        redis_client = redis.Redis(
            host=config.get('host', 'localhost'),
            port=config.get('port', 6379),
            db=config.get('db', 0),
            socket_connect_timeout=5,
            socket_timeout=5
        )

        # Basic connectivity test
        redis_client.ping()

        # Get Redis info
        info = redis_client.info()

        metrics = {
            'used_memory': info.get('used_memory_human'),
            'used_memory_peak': info.get('used_memory_peak_human'),
            'connected_clients': info.get('connected_clients'),
            'total_commands_processed': info.get('total_commands_processed'),
            'keyspace_hits': info.get('keyspace_hits', 0),
            'keyspace_misses': info.get('keyspace_misses', 0),
            'uptime_in_seconds': info.get('uptime_in_seconds'),
            'redis_version': info.get('redis_version')
        }

        # Calculate hit rate
        hits = metrics['keyspace_hits']
        misses = metrics['keyspace_misses']
        total_requests = hits + misses

        if total_requests > 0:
            metrics['hit_rate'] = (hits / total_requests) * 100
        else:
            metrics['hit_rate'] = 0

        response_time = (time.time() - start_time) * 1000
        status = self._determine_health_status(metrics, response_time)

        return DatabaseHealthStatus(
            name='redis',
            status=status,
            response_time=response_time,
            error_message=None,
            metrics=metrics,
            timestamp=datetime.utcnow()
        )

    def _determine_health_status(self, metrics: Dict, response_time: float) -> str:
        """Determine health status based on metrics"""

        # Check response time
        if response_time > self.alert_thresholds['response_time_ms']:
            return 'unhealthy'

        # Check connection usage
        if 'active_connections' in metrics:
            # This would need max connections config
            pass

        # Check memory usage
        if 'used_memory' in metrics:
            # This would need max memory config
            pass

        # Check hit rate for Redis
        if 'hit_rate' in metrics:
            if metrics['hit_rate'] < 80:
                return 'degraded'

        return 'healthy'

    async def start_continuous_monitoring(self, interval_seconds: int = 60):
        """Start continuous health monitoring"""

        while True:
            try:
                health_status = await self.check_all_databases()

                # Check for alerts
                await self._check_alerts(health_status)

                # Log health status
                await self._log_health_status(health_status)

            except Exception as e:
                print(f"Error in health monitoring: {e}")

            await asyncio.sleep(interval_seconds)

    async def _check_alerts(self, health_status: Dict[str, DatabaseHealthStatus]):
        """Check for alert conditions"""

        for db_name, status in health_status.items():
            if status.status in ['degraded', 'unhealthy']:
                await self._send_alert(
                    f"Database {db_name} is {status.status}",
                    {
                        'database': db_name,
                        'status': status.status,
                        'response_time': status.response_time,
                        'error_message': status.error_message,
                        'metrics': status.metrics
                    }
                )

    async def _send_alert(self, message: str, details: Dict):
        """Send alert to monitoring system"""

        alert_data = {
            'message': message,
            'details': details,
            'severity': 'critical' if details['status'] == 'unhealthy' else 'warning',
            'timestamp': datetime.utcnow().isoformat()
        }

        # Integration with alerting system (Slack, PagerDuty, etc.)
        print(f"ALERT: {message}")
        print(f"Details: {json.dumps(alert_data, indent=2)}")

    async def _log_health_status(self, health_status: Dict[str, DatabaseHealthStatus]):
        """Log health status to database or file"""

        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'databases': {
                db_name: {
                    'status': status.status,
                    'response_time': status.response_time,
                    'metrics': status.metrics
                }
                for db_name, status in health_status.items()
            }
        }

        # Log to file or monitoring system
        print(f"Health Check: {json.dumps(log_entry, indent=2)}")
```

---

## Future Considerations and Trends

### Emerging Database Technologies

#### Vector Databases for AI-Powered Knowledge Discovery
```python
# Example with Weaviate for semantic search in expertise files
import weaviate
from weaviate.client import Client
import numpy as np
from sentence_transformers import SentenceTransformer

class AIEnhancedKnowledgeSystem:
    """AI-powered knowledge discovery using vector databases"""

    def __init__(self, weaviate_url: str, model_name: str = "all-MiniLM-L6-v2"):
        self.client = weaviate.Client(weaviate_url)
        self.encoder = SentenceTransformer(model_name)
        self.setup_schema()

    def setup_schema(self):
        """Setup Weaviate schema for expertise files"""

        schema = {
            "classes": [
                {
                    "class": "ExpertiseFile",
                    "description": "Expertise file with semantic search capabilities",
                    "properties": [
                        {
                            "name": "title",
                            "dataType": ["text"],
                            "description": "Title of the expertise file"
                        },
                        {
                            "name": "content",
                            "dataType": ["text"],
                            "description": "Main content of the expertise file"
                        },
                        {
                            "name": "category",
                            "dataType": ["string"],
                            "description": "Primary category"
                        },
                        {
                            "name": "expertise_level",
                            "dataType": ["string"],
                            "description": "Expertise level classification"
                        },
                        {
                            "name": "tags",
                            "dataType": ["string[]"],
                            "description": "Tags for content discovery"
                        },
                        {
                            "name": "metadata",
                            "dataType": ["object"],
                            "description": "Additional metadata"
                        }
                    ],
                    "vectorizer": "none"  # We'll provide our own vectors
                }
            ]
        }

        # Create schema if it doesn't exist
        try:
            self.client.schema.create(schema)
        except:
            pass  # Schema might already exist

    def index_expertise_file(self, file_data: Dict):
        """Index expertise file for semantic search"""

        # Combine title and content for embedding
        text_to_embed = f"{file_data['title']}\n\n{file_data['content']}"

        # Generate embedding
        embedding = self.encoder.encode(text_to_embed)

        # Prepare data object
        data_object = {
            "title": file_data['title'],
            "content": file_data['content'],
            "category": file_data['category'],
            "expertise_level": file_data['expertise_level'],
            "tags": file_data.get('tags', []),
            "metadata": file_data.get('metadata', {})
        }

        # Add to Weaviate
        self.client.data_object.create(
            data_object=data_object,
            class_name="ExpertiseFile",
            vector=embedding.tolist()
        )

    def semantic_search(self, query: str, category: str = None,
                       expertise_level: str = None, limit: int = 10) -> List[Dict]:
        """Perform semantic search with optional filters"""

        # Generate query embedding
        query_embedding = self.encoder.encode(query).tolist()

        # Build query
        near_vector = {"vector": query_embedding}

        # Add filters if provided
        if category or expertise_level:
            where_filter = {"operator": "And", "operands": []}

            if category:
                where_filter["operands"].append({
                    "path": ["category"],
                    "operator": "Equal",
                    "valueString": category
                })

            if expertise_level:
                where_filter["operands"].append({
                    "path": ["expertise_level"],
                    "operator": "Equal",
                    "valueString": expertise_level
                })

            near_vector["where"] = where_filter

        # Execute search
        result = self.client.query.get(
            "ExpertiseFile",
            ["title", "content", "category", "expertise_level", "tags", "metadata", "_additional {id certainty}"]
        ).with_near_vector(near_vector).with_limit(limit).do()

        return result["data"]["Get"]["ExpertiseFile"]

    def find_similar_files(self, file_id: str, limit: int = 5) -> List[Dict]:
        """Find files similar to a given file"""

        # Get the file's vector
        file_data = self.client.data_object.get_by_id(
            file_id,
            class_name="ExpertiseFile",
            with_vector=True
        )

        if not file_data or "vector" not in file_data:
            return []

        # Search for similar files
        result = self.client.query.get(
            "ExpertiseFile",
            ["title", "content", "category", "expertise_level", "_additional {id certainty}"]
        ).with_near_vector({
            "vector": file_data["vector"],
            "certainty": 0.7  # Minimum similarity threshold
        }).with_limit(limit + 1).do()  # +1 to exclude the original file

        # Filter out the original file
        similar_files = [
            file for file in result["data"]["Get"]["ExpertiseFile"]
            if file["_additional"]["id"] != file_id
        ]

        return similar_files[:limit]
```

#### Time-Series Database for Usage Analytics
```python
# Example with InfluxDB for usage analytics
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime, timedelta
import json

class KnowledgeUsageAnalytics:
    """Usage analytics using time-series database"""

    def __init__(self, influxdb_url: str, token: str, org: str, bucket: str):
        self.client = InfluxDBClient(url=influxdb_url, token=token, org=org)
        self.bucket = bucket
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        self.query_api = self.client.query_api()

    def record_file_access(self, file_id: str, user_id: str,
                          category: str, access_type: str = "view"):
        """Record file access event"""

        point = Point("file_access") \
            .tag("file_id", file_id) \
            .tag("user_id", user_id) \
            .tag("category", category) \
            .tag("access_type", access_type) \
            .field("count", 1) \
            .time(datetime.utcnow())

        self.write_api.write(bucket=self.bucket, record=point)

    def record_search_query(self, user_id: str, query: str,
                           results_count: int, response_time_ms: float):
        """Record search query analytics"""

        point = Point("search_query") \
            .tag("user_id", user_id) \
            .tag("query_hash", str(hash(query))) \
            .field("query", query) \
            .field("results_count", results_count) \
            .field("response_time_ms", response_time_ms) \
            .time(datetime.utcnow())

        self.write_api.write(bucket=self.bucket, record=point)

    def get_usage_trends(self, time_range: str = "-7d") -> Dict:
        """Get usage trends over time"""

        # Query file access trends
        access_query = f'''
        from(bucket: "{self.bucket}")
          |> range(start: {time_range})
          |> filter(fn: (r) => r._measurement == "file_access")
          |> aggregateWindow(every: 1h, fn: count, createEmpty: false)
          |> yield(name: "access_trend")
        '''

        # Query search trends
        search_query = f'''
        from(bucket: "{self.bucket}")
          |> range(start: {time_range})
          |> filter(fn: (r) => r._measurement == "search_query")
          |> aggregateWindow(every: 1h, fn: count, createEmpty: false)
          |> yield(name: "search_trend")
        '''

        # Execute queries
        access_result = self.query_api.query(access_query)
        search_result = self.query_api.query(search_query)

        return {
            "access_trends": self._process_query_result(access_result),
            "search_trends": self._process_query_result(search_result)
        }

    def get_popular_categories(self, time_range: str = "-7d", limit: int = 10) -> List[Dict]:
        """Get most popular categories"""

        query = f'''
        from(bucket: "{self.bucket}")
          |> range(start: {time_range})
          |> filter(fn: (r) => r._measurement == "file_access")
          |> group(columns: ["category"])
          |> count()
          |> sort(columns: ["_value"], desc: true)
          |> limit(n: {limit})
          |> yield(name: "popular_categories")
        '''

        result = self.query_api.query(query)
        return self._process_query_result(result)

    def get_user_engagement(self, user_id: str, time_range: str = "-30d") -> Dict:
        """Get user engagement metrics"""

        # File accesses by user
        access_query = f'''
        from(bucket: "{self.bucket}")
          |> range(start: {time_range})
          |> filter(fn: (r) => r._measurement == "file_access")
          |> filter(fn: (r) => r.user_id == "{user_id}")
          |> count()
        '''

        # Search queries by user
        search_query = f'''
        from(bucket: "{self.bucket}")
          |> range(start: {time_range})
          |> filter(fn: (r) => r._measurement == "search_query")
          |> filter(fn: (r) => r.user_id == "{user_id}")
          |> count()
        '''

        # Average response time for searches
        response_time_query = f'''
        from(bucket: "{self.bucket}")
          |> range(start: {time_range})
          |> filter(fn: (r) => r._measurement == "search_query")
          |> filter(fn: (r) => r.user_id == "{user_id}")
          |> mean(column: "response_time_ms")
        '''

        access_result = self.query_api.query(access_query)
        search_result = self.query_api.query(search_query)
        response_time_result = self.query_api.query(response_time_query)

        return {
            "file_accesses": self._extract_single_value(access_result),
            "search_queries": self._extract_single_value(search_result),
            "avg_search_response_time": self._extract_single_value(response_time_result)
        }

    def _process_query_result(self, result) -> List[Dict]:
        """Process InfluxDB query result into list of dictionaries"""

        processed = []

        for table in result:
            for record in table.records:
                processed.append({
                    "time": record.get_time(),
                    "value": record.get_value(),
                    "field": record.get_field(),
                    "tags": record.values
                })

        return processed

    def _extract_single_value(self, result) -> float:
        """Extract single value from query result"""

        for table in result:
            for record in table.records:
                return record.get_value()
        return 0
```

---

## Conclusion

This database design expertise file provides comprehensive patterns and best practices for the CSF Persistent Learning Agent Ecosystem. The implementation covers:

### Key Areas Covered

1. **Relational Database Design**: Advanced PostgreSQL patterns for knowledge storage
2. **NoSQL Integration**: MongoDB for metadata, Redis for caching, Elasticsearch for search
3. **Data Modeling**: Schema design with evolution and validation
4. **Performance Optimization**: Query tuning, indexing strategies, materialized views
5. **Migration Management**: Zero-downtime migrations with version control
6. **Transaction Management**: ACID compliance and distributed transaction patterns
7. **Security Implementation**: Row-level security, audit logging, access control
8. **Multi-Database Architecture**: Polyglot persistence with synchronization
9. **Monitoring**: Comprehensive health checks and performance monitoring
10. **Future Technologies**: Vector databases for AI, time-series for analytics

### Implementation Highlights

- **ACID-compliant primary storage** with PostgreSQL
- **Full-text search capabilities** using PostgreSQL and Elasticsearch
- **High-performance caching** with Redis
- **Flexible metadata storage** with MongoDB
- **Comprehensive audit logging** and security controls
- **Real-time synchronization** across multiple databases
- **AI-powered semantic search** with vector databases
- **Time-series analytics** for usage insights

### Scalability Considerations

The design supports:
- **Horizontal scaling** through database replication
- **Read/write splitting** for performance optimization
- **Connection pooling** for efficient resource management
- **Partitioning** for large datasets
- **Caching layers** to reduce database load
- **Async processing** for non-blocking operations

### Maintenance and Operations

- **Automated backup and recovery** procedures
- **Health monitoring** with alerting
- **Performance analytics** and optimization
- **Schema evolution** with backward compatibility
- **Zero-downtime deployment** strategies

This expertise file serves as a comprehensive reference for database design and implementation within the CSF ecosystem, ensuring robust, scalable, and maintainable data persistence solutions for the knowledge management system.

---

**Author**: CSF Development Team
**Task ID**: task-03-03
**Version**: 1.0
**Review Cycle**: Quarterly
**Integration**: CKS (Knowledge Management System)
**Related Files**:
- `cks/integration/knowledge_artifacts/expertise/api_design.md`
- `cks/integration/knowledge_artifacts/expertise/system_architecture.md`
- `cks/integration/knowledge_artifacts/expertise/performance_optimization.md`
