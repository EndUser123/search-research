# E-Commerce Order API API Data Model
**Task ID**: TSK-20251127-001
**Date**: 2025-11-28
**Status**: PLANNING
**Project Type**: API Development

## Data Model Overview

The E-Commerce Order API API data model represents the core entities and relationships required for the RESTful API system. The model follows a relational database design with proper normalization, indexing strategies, and scalability considerations.

## Core Entity Definitions

### User Entity
Represents system users who can authenticate and interact with the API.

**Properties**:
- `id`: Integer primary key (auto-increment)
- `uuid`: UUIDv4 string for external references
- `email`: String, unique email address for authentication
- `username`: String, unique username for login
- `password_hash`: String, bcrypt-hashed password
- `first_name`: String, user's first name
- `last_name`: String, user's last name
- `phone_number`: String, optional phone number
- `avatar_url`: String, URL to profile avatar
- `email_verified`: Boolean, email verification status
- `phone_verified`: Boolean, phone verification status
- `is_active`: Boolean, account active status
- `last_login_at`: Timestamp, last login time
- `created_at`: Timestamp, account creation time
- `updated_at`: Timestamp, last modification time

**Schema**:
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid UUID DEFAULT (random()) NOT NULL,
    email TEXT NOT NULL UNIQUE,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    phone_number TEXT,
    avatar_url TEXT,
    email_verified BOOLEAN DEFAULT FALSE NOT NULL,
    phone_verified BOOLEAN DEFAULT FALSE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    last_login_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,

    CONSTRAINT users_email_check CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    CONSTRAINT users_username_check CHECK (length(username) >= 3 AND length(username) <= 50),
    CONSTRAINT users_password_hash_check CHECK (length(password_hash) >= 60)
);
```

**Python Model**:
```python
@dataclass
class User:
    id: Optional[int] = None
    uuid: str = ""
    email: str = ""
    username: str = ""
    password_hash: str = ""
    first_name: str = ""
    last_name: str = ""
    phone_number: Optional[str] = None
    avatar_url: Optional[str] = None
    email_verified: bool = False
    phone_verified: bool = False
    is_active: bool = True
    last_login_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
```

### Role Entity
Represents user roles for authorization and access control.

**Properties**:
- `id`: Integer primary key (auto-increment)
- `name`: String, unique role name (e.g., "admin", "user", "moderator")
- `description`: Text, role description and purpose
- `is_system`: Boolean, indicates if role is system-managed
- `permissions`: JSON array of permission strings
- `created_at`: Timestamp, role creation time
- `updated_at`: Timestamp, last modification time

**Role Types**:
- `admin`: Full system access
- `user`: Standard user access
- `moderator`: Content moderation access
- `viewer`: Read-only access
- `api_client`: Service account access

**Schema**:
```sql
CREATE TABLE roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    is_system BOOLEAN DEFAULT FALSE NOT NULL,
    permissions JSON DEFAULT '[]' NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);
```

**Python Model**:
```python
@dataclass
class Role:
    id: Optional[int] = None
    name: str = ""
    description: Optional[str] = None
    is_system: bool = False
    permissions: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
```

### UserRole Entity (Many-to-Many)
Represents the relationship between users and roles.

**Properties**:
- `user_id`: Integer, foreign key to users table
- `role_id`: Integer, foreign key to roles table
- `assigned_by`: Integer, foreign key to users table (who assigned)
- `assigned_at`: Timestamp, when role was assigned
- `expires_at`: Timestamp, optional role expiration

**Schema**:
```sql
CREATE TABLE user_roles (
    user_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    assigned_by INTEGER NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    expires_at TIMESTAMP,

    PRIMARY KEY (user_id, role_id),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles (id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_by) REFERENCES users (id),
    CONSTRAINT user_roles_expires_check CHECK (expires_at IS NULL OR expires_at > assigned_at)
);
```

### Primary Resource Entity
Represents the main business entity for the API (customize based on project needs).

**Properties**:
- `id`: Integer primary key (auto-increment)
- `uuid`: UUIDv4 string for external references
- `name`: String, resource name
- `description`: Text, detailed description
- `owner_id`: Integer, foreign key to users table
- `status`: String, resource status (enum: active, inactive, archived, draft)
- `type`: String, resource type (enum: type1, type2, type3)
- `metadata`: JSON, flexible metadata storage
- `tags`: JSON array, categorization tags
- `created_at`: Timestamp, creation time
- `updated_at`: Timestamp, last modification time

**Schema**:
```sql
CREATE TABLE resources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid UUID DEFAULT (random()) NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    owner_id INTEGER NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('active', 'inactive', 'archived', 'draft')),
    type TEXT NOT NULL,
    metadata JSON DEFAULT '{}' NOT NULL,
    tags JSON DEFAULT '[]' NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,

    FOREIGN KEY (owner_id) REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT resources_name_check CHECK (length(name) >= 1 AND length(name) <= 255)
);
```

**Python Model**:
```python
@dataclass
class Resource:
    id: Optional[int] = None
    uuid: str = ""
    name: str = ""
    description: Optional[str] = None
    owner_id: int = 0
    status: str = "active"
    type: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
```

### Audit Log Entity
Tracks all important actions for auditing and compliance.

**Properties**:
- `id`: Integer primary key (auto-increment)
- `user_id`: Integer, foreign key to users table (nullable for system actions)
- `action`: String, action type (enum: create, update, delete, login, logout)
- `resource_type`: String, type of resource affected
- `resource_id`: String, ID of affected resource
- `old_values`: JSON, previous values for updates
- `new_values`: JSON, new values for updates
- `ip_address`: String, client IP address
- `user_agent`: String, client user agent string
- `created_at`: Timestamp, audit entry creation time

**Schema**:
```sql
CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action TEXT NOT NULL CHECK (action IN ('create', 'update', 'delete', 'login', 'logout', 'view')),
    resource_type TEXT NOT NULL,
    resource_id TEXT NOT NULL,
    old_values JSON,
    new_values JSON,
    ip_address TEXT,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,

    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
);
```

## Relationships

### User Relationships
- **One-to-Many**: User → Resources (owner relationship)
- **Many-to-Many**: User ↔ Roles (via user_roles table)
- **One-to-Many**: User → Audit Logs (user actions)

### Role Relationships
- **Many-to-Many**: Role ↔ Users (via user_roles table)

### Resource Relationships
- **Many-to-One**: Resource → User (owner relationship)
- **One-to-Many**: Resource → Audit Logs (resource actions)

## Indexes for Performance

### Primary Indexes
- Primary keys on all tables for efficient lookup
- Unique constraints on email and username for users table

### Search Indexes
```sql
-- User search indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_active ON users(is_active);
CREATE INDEX idx_users_created_at ON users(created_at);

-- Role indexes
CREATE INDEX idx_roles_name ON roles(name);
CREATE INDEX idx_roles_system ON roles(is_system);

-- User role indexes
CREATE INDEX idx_user_roles_user_id ON user_roles(user_id);
CREATE INDEX idx_user_roles_role_id ON user_roles(role_id);
CREATE INDEX idx_user_roles_expires_at ON user_roles(expires_at);

-- Resource indexes
CREATE INDEX idx_resources_owner_id ON resources(owner_id);
CREATE INDEX idx_resources_status ON resources(status);
CREATE INDEX idx_resources_type ON resources(type);
CREATE INDEX idx_resources_created_at ON resources(created_at);
CREATE INDEX idx_resources_name ON resources(name);

-- Full-text search for resources
CREATE VIRTUAL TABLE resource_fts USING fts5(
    name,
    description,
    tags,
    content='resources',
    content_rowid='id'
);

-- Audit log indexes
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_resource_type ON audit_logs(resource_type);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
```

## JSON Schema Definitions

### Metadata JSON Schema
```json
{
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "priority": {
            "type": "string",
            "enum": ["low", "medium", "high", "critical"]
        },
        "category": {
            "type": "string",
            "minLength": 1,
            "maxLength": 100
        },
        "settings": {
            "type": "object",
            "properties": {
                "is_public": {
                    "type": "boolean"
                },
                "allow_comments": {
                    "type": "boolean"
                },
                "enable_notifications": {
                    "type": "boolean"
                }
            }
        },
        "custom_fields": {
            "type": "object",
            "additionalProperties": {
                "type": ["string", "number", "boolean", "array", "object"]
            }
        }
    }
}
```

### Permissions JSON Schema
```json
{
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "array",
    "items": {
        "type": "string",
        "pattern": "^[a-z_]+:[a-z_]+$",
        "enum": [
            "users:read", "users:write", "users:delete",
            "resources:read", "resources:write", "resources:delete",
            "roles:read", "roles:write", "roles:delete",
            "audit:read", "system:admin"
        ]
    },
    "uniqueItems": true
}
```

### Tags JSON Schema
```json
{
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "array",
    "items": {
        "type": "string",
        "pattern": "^[a-z0-9_-]+$",
        "minLength": 1,
        "maxLength": 50
    },
    "uniqueItems": true,
    "maxItems": 20
}
```

## Data Integrity Constraints

### Foreign Key Constraints
- All foreign keys have appropriate ON DELETE/ON UPDATE actions
- Prevent orphaned records in related tables
- Maintain referential integrity across the database

### Check Constraints
- Email format validation using regex
- Username length and character constraints
- Password hash minimum length validation
- Role and resource status enum constraints
- Timestamp relationship validation (created_at <= updated_at)

### Unique Constraints
- User emails must be unique
- Usernames must be unique
- Role names must be unique
- User-role combinations must be unique
- Resource UUIDs must be unique

## Data Migration Strategy

### Version 1.0 Schema
- Initial implementation with core entities
- Basic user management and authentication
- Role-based access control
- Resource management
- Comprehensive audit logging

### Future Extensions
- **Version 1.1**: Resource versioning and history tracking
- **Version 1.2**: Advanced permission system with resource-level permissions
- **Version 2.0**: Multi-tenancy support with organization entities
- **Version 2.1**: Advanced analytics and reporting entities

### Migration Process
1. **Schema Version Tracking**: `schema_version` table with migration metadata
2. **Incremental Migrations**: Version-specific migration scripts with rollback capability
3. **Data Validation**: Post-migration data integrity checks
4. **Performance Optimization**: Index creation and analysis after migrations

## Query Patterns

### User Management Queries
```sql
-- Get user with roles and permissions
SELECT u.*, r.name as role_name, r.permissions
FROM users u
LEFT JOIN user_roles ur ON u.id = ur.user_id
LEFT JOIN roles r ON ur.role_id = r.id
WHERE u.id = ? AND ur.expires_at IS NULL OR ur.expires_at > CURRENT_TIMESTAMP;

-- Check user permissions
SELECT COUNT(*) as has_permission
FROM users u
JOIN user_roles ur ON u.id = ur.user_id
JOIN roles r ON ur.role_id = r.id
WHERE u.id = ? AND
      (r.permissions::jsonb ?| ARRAY[?] OR r.is_system = TRUE) AND
      (ur.expires_at IS NULL OR ur.expires_at > CURRENT_TIMESTAMP);
```

### Resource Management Queries
```sql
-- Get resources with pagination and filtering
SELECT r.*, u.username as owner_username
FROM resources r
JOIN users u ON r.owner_id = u.id
WHERE r.status = ?
  AND r.type = ?
  AND (r.name ILIKE ? OR r.description ILIKE ?)
ORDER BY r.created_at DESC
LIMIT ? OFFSET ?;

-- Full-text search for resources
SELECT r.*, u.username as owner_username,
       rank
FROM resources r
JOIN users u ON r.owner_id = u.id
JOIN resource_fts fts ON r.id = fts.rowid
WHERE resource_fts MATCH ?
ORDER BY rank, r.created_at DESC;
```

### Audit Logging Queries
```sql
-- Get user activity logs
SELECT al.*, u.username as action_user
FROM audit_logs al
LEFT JOIN users u ON al.user_id = u.id
WHERE al.user_id = ?
  AND al.created_at >= ?
  AND al.created_at <= ?
ORDER BY al.created_at DESC;

-- Get resource audit history
SELECT al.*, u.username as action_user
FROM audit_logs al
LEFT JOIN users u ON al.user_id = u.id
WHERE al.resource_type = ?
  AND al.resource_id = ?
ORDER BY al.created_at DESC;
```

## Performance Considerations

### Database Size Estimates
- **Small Applications** (< 1,000 users): < 50MB
- **Medium Applications** (1,000-10,000 users): 50-500MB
- **Large Applications** (> 10,000 users): 500MB+

### Query Performance Targets
- **User Authentication**: <10ms with proper indexing
- **Resource Listing**: <50ms with pagination and filtering
- **Full-Text Search**: <100ms with FTS5
- **Audit Log Queries**: <100ms with time-based filtering

### Optimization Strategies
- **Connection Pooling**: Efficient database connection management
- **Query Caching**: Cache frequently accessed user sessions and permissions
- **Read Replicas**: Separate read replicas for reporting and analytics
- **Partitioning**: Time-based partitioning for audit logs and large tables

## Security Considerations

### Data Encryption
- **Password Storage**: Bcrypt with work factor >= 12
- **Sensitive Data**: Application-level encryption for PII
- **Transport Security**: TLS 1.2+ for all database connections
- **Backup Security**: Encrypted backups with access controls

### Access Controls
- **Row-Level Security**: Users can only access their own resources
- **Column-Level Security**: Sensitive columns protected by roles
- **Audit Trail**: Complete audit logging for all data modifications
- **Data Retention**: Configurable retention policies for audit logs

### Privacy Compliance
- **Data Minimization**: Only collect necessary user information
- **Right to Deletion**: Complete user data deletion capability
- **Data Portability**: Export functionality for user data
- **Consent Management**: Track and manage user consents

## Backup and Recovery

### Backup Strategy
- **Automated Backups**: Daily full backups with hourly incrementals
- **Point-in-Time Recovery**: 15-minute recovery point objective
- **Cross-Region Replication**: Backup replication to secondary regions
- **Backup Verification**: Regular restore testing and validation

### Recovery Procedures
- **Failover Planning**: Automated failover to standby systems
- **Data Consistency**: Transaction log replay for consistency
- **Rollback Capability**: Ability to rollback to previous states
- **Recovery Testing**: Monthly disaster recovery drills

## Conclusion

This data model provides a solid foundation for building a secure, scalable, and maintainable RESTful API. The design emphasizes:

- **Security**: Comprehensive authentication, authorization, and audit capabilities
- **Performance**: Optimized queries, proper indexing, and caching strategies
- **Scalability**: Normalized design that can handle growth and multi-tenancy
- **Maintainability**: Clear structure, proper constraints, and migration support
- **Compliance**: Audit trails, data protection, and privacy features

The model follows database design best practices and provides the flexibility needed for future enhancements while maintaining data integrity and performance requirements.

**Status**: Ready for implementation
**Next Phase**: Database migration script creation and API development
