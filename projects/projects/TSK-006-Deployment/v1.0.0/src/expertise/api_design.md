# API Design Expertise

**Metadata:**
- **Expertise Domain**: API Design & Architecture
- **Classification**: Development Patterns, Architecture, Integration
- **Tags**: `api-design`, `rest`, `graphql`, `microservices`, `authentication`, `performance`
- **Created**: 2025-12-21
- **CKS Context**: Persistent Learning Agent Ecosystem
- **Priority**: High

## Table of Contents
1. [REST API Design Principles](#rest-api-design-principles)
2. [GraphQL Schema Design Patterns](#graphql-schema-design-patterns)
3. [Microservices Architecture Patterns](#microservices-architecture-patterns)
4. [API Authentication & Authorization](#api-authentication--authorization)
5. [Rate Limiting & Throttling](#rate-limiting--throttling)
6. [API Versioning Strategies](#api-versioning-strategies)
7. [Error Handling & Response Formatting](#error-handling--response-formatting)
8. [Documentation Standards](#documentation-standards)
9. [Performance Optimization](#performance-optimization)
10. [Testing Strategies](#testing-strategies)
11. [Integration Patterns & Webhooks](#integration-patterns--webhooks)

---

## REST API Design Principles

### Core Principles

**1. Resource-Oriented Design**
```yaml
# Good: Clear resource identification
/api/v1/users/{userId}
/api/v1/users/{userId}/orders
/api/v1/products/{productId}/reviews

# Bad: Action-based URLs
/api/v1/getUserDetails
/api/v1/createOrder
/api/v1/processPayment
```

**2. HTTP Method Semantics**
```yaml
GET    /users          # List users
GET    /users/{id}     # Get specific user
POST   /users          # Create new user
PUT    /users/{id}     # Replace entire user
PATCH  /users/{id}     # Partial update
DELETE /users/{id}     # Delete user
```

**3. Status Code Best Practices**
```yaml
# Success Codes
200 OK          # Successful GET, PUT, PATCH
201 Created     # Successful POST
204 No Content  # Successful DELETE

# Client Error Codes
400 Bad Request        # Validation errors
401 Unauthorized       # Authentication required
403 Forbidden          # Permission denied
404 Not Found          # Resource doesn't exist
409 Conflict           # Resource conflict
422 Unprocessable Entity # Validation failed

# Server Error Codes
500 Internal Server Error # Unexpected server error
502 Bad Gateway          # Upstream service error
503 Service Unavailable  # Service temporarily down
```

### Request/Response Patterns

**1. Consistent Response Structure**
```json
{
  "data": {
    // Actual response data
  },
  "meta": {
    "timestamp": "2025-12-21T10:30:00Z",
    "version": "v1",
    "requestId": "req_123456789"
  },
  "links": {
    "self": "/api/v1/users?page=1",
    "next": "/api/v1/users?page=2",
    "prev": null
  }
}
```

**2. Error Response Format**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field": "email",
      "issue": "Invalid email format"
    },
    "timestamp": "2025-12-21T10:30:00Z",
    "requestId": "req_123456789"
  }
}
```

**3. Pagination Patterns**
```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "pageSize": 20,
    "totalItems": 150,
    "totalPages": 8,
    "hasNext": true,
    "hasPrev": false
  }
}
```

---

## GraphQL Schema Design Patterns

### Schema Design Best Practices

**1. Type Organization**
```graphql
# Root types
type Query {
  user(id: ID!): User
  users(filter: UserFilter, first: Int, after: String): UserConnection!
  products(category: String): [Product!]!
}

type Mutation {
  createUser(input: CreateUserInput!): CreateUserPayload!
  updateUser(id: ID!, input: UpdateUserInput!): UpdateUserPayload!
}

type Subscription {
  userCreated: User!
  userUpdated(id: ID!): User!
}

# Core types
type User {
  id: ID!
  email: String!
  profile: UserProfile
  orders(first: Int, after: String): OrderConnection!
  createdAt: DateTime!
  updatedAt: DateTime!
}

# Input types
input CreateUserInput {
  email: String!
  profile: UserProfileInput
}

# Filter types
input UserFilter {
  status: UserStatus
  createdAfter: DateTime
  createdBefore: DateTime
}
```

**2. Relay Specification Compliance**
```graphql
# Connection pattern for pagination
type UserConnection {
  edges: [UserEdge!]!
  pageInfo: PageInfo!
  totalCount: Int!
}

type UserEdge {
  node: User!
  cursor: String!
}

type PageInfo {
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  startCursor: String
  endCursor: String
}
```

**3. Resolver Best Practices**
```python
# Efficient data loading with DataLoader
class UserResolvers:
    def __init__(self):
        self.user_loader = DataLoader(load_users)
        self.order_loader = DataLoader(load_user_orders)

    async def resolve_user(self, parent, info, id):
        return await self.user_loader.load(id)

    async def resolve_orders(self, parent, info, first, after):
        return await self.order_loader.load(parent.id)
```

### GraphQL Performance Patterns

**1. Query Complexity Analysis**
```python
# Query complexity calculation
COMPLEXITY_WEIGHTS = {
    'user': 1,
    'users': 10,
    'orders': 5,
    'nested_queries': 20
}

def calculate_query_complexity(ast):
    complexity = 0
    for field in ast.selection_set.selections:
        complexity += COMPLEXITY_WEIGHTS.get(field.name.value, 1)
    return complexity
```

**2. Query Depth Limiting**
```python
# Prevent deeply nested queries
MAX_QUERY_DEPTH = 7

def validate_query_depth(ast, current_depth=0):
    if current_depth > MAX_QUERY_DEPTH:
        raise QueryDepthError(f"Query depth exceeds maximum of {MAX_QUERY_DEPTH}")

    if hasattr(ast, 'selection_set'):
        for field in ast.selection_set.selections:
            validate_query_depth(field, current_depth + 1)
```

---

## Microservices Architecture Patterns

### Service Communication Patterns

**1. Synchronous Communication**
```yaml
# API Gateway Pattern
api-gateway:
  routes:
    - path: /api/users/**
      service: user-service
      timeout: 5000ms
    - path: /api/orders/**
      service: order-service
      timeout: 10000ms

# Service-to-Service Communication
user-service:
  communication:
    - service: order-service
      protocol: HTTP/REST
      circuit-breaker: true
      retry-policy:
        max-attempts: 3
        backoff: exponential
```

**2. Asynchronous Communication**
```yaml
# Event-Driven Architecture
event-bus:
  type: kafka
  topics:
    - user.created
    - user.updated
    - order.placed
    - payment.processed

# Message Patterns
patterns:
  - command: CreateOrderCommand
    handler: order-service
    retry: 3
  - event: OrderCreatedEvent
    subscribers:
      - payment-service
      - notification-service
      - inventory-service
```

**3. Service Discovery**
```yaml
# Consul Service Registry
consul:
  services:
    user-service:
      port: 8081
      health-check: /health
      tags: [api, v1]
    order-service:
      port: 8082
      health-check: /health
      tags: [api, v1]
```

### Data Management Patterns

**1. Database per Service**
```yaml
services:
  user-service:
    database:
      type: postgresql
      schema: users
      connection-pool: 20

  order-service:
    database:
      type: mongodb
      collection: orders
      sharding: true
```

**2. Saga Pattern for Distributed Transactions**
```python
# Choreography-based Saga
class OrderSaga:
    async def execute(self, order_data):
        try:
            # Step 1: Create order
            order = await self.order_service.create(order_data)

            # Step 2: Process payment
            payment = await self.payment_service.process(
                order.id, order_data.payment
            )

            # Step 3: Update inventory
            await self.inventory_service.reserve(order_data.items)

            # Step 4: Send confirmation
            await self.notification_service.send_confirmation(order.id)

        except Exception as e:
            # Compensating transactions
            await self.compensate(order.id)
            raise e
```

---

## API Authentication & Authorization

### Authentication Strategies

**1. JWT Token-Based Authentication**
```python
# JWT Token Structure
{
  "sub": "user_123",
  "email": "user@example.com",
  "roles": ["user", "admin"],
  "permissions": ["read:orders", "write:orders"],
  "iat": 1640102400,
  "exp": 1640188800,
  "iss": "your-api",
  "aud": "your-client"
}

# Token Validation Middleware
async def authenticate_request(request):
    token = extract_bearer_token(request)
    payload = decode_jwt(token)

    if not validate_token(payload):
        raise AuthenticationError("Invalid token")

    return payload
```

**2. OAuth 2.0 Flows**
```yaml
authorization-server:
  flows:
    authorization-code:
      - PKCE
      - state-parameter
    client-credentials:
      - service-to-service
    refresh-token:
      - rotation
      - reuse-detection
```

**3. API Key Authentication**
```python
# API Key Management
class APIKeyManager:
    def __init__(self):
        self.keys = {}

    def generate_key(self, client_id, permissions):
        key = secrets.token_urlsafe(32)
        self.keys[key] = {
            'client_id': client_id,
            'permissions': permissions,
            'created_at': datetime.utcnow(),
            'last_used': None
        }
        return key
```

### Authorization Patterns

**1. Role-Based Access Control (RBAC)**
```python
# RBAC Implementation
class RBACAuthorizer:
    ROLES = {
        'admin': ['read', 'write', 'delete'],
        'user': ['read', 'write'],
        'guest': ['read']
    }

    def authorize(self, user_role, required_permission):
        user_permissions = self.ROLES.get(user_role, [])
        return required_permission in user_permissions
```

**2. Attribute-Based Access Control (ABAC)**
```python
# ABAC Policy Evaluation
class ABACPolicy:
    def evaluate(self, subject, resource, action, environment):
        policies = self.get_policies(subject, resource, action)

        for policy in policies:
            if self.matches_conditions(policy.conditions, environment):
                return policy.effect

        return 'deny'
```

---

## Rate Limiting & Throttling

### Rate Limiting Strategies

**1. Token Bucket Algorithm**
```python
class TokenBucket:
    def __init__(self, capacity, refill_rate):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate
        self.last_refill = time.time()

    def consume(self, tokens=1):
        self.refill()
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    def refill(self):
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now
```

**2. Sliding Window Counter**
```python
class SlidingWindowCounter:
    def __init__(self, window_size, max_requests):
        self.window_size = window_size
        self.max_requests = max_requests
        self.requests = []

    def is_allowed(self):
        now = time.time()
        # Remove old requests
        self.requests = [req_time for req_time in self.requests
                        if now - req_time < self.window_size]

        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True
        return False
```

**3. Rate Limiting Configuration**
```yaml
rate-limits:
  default:
    requests-per-minute: 60
    burst: 10

  premium-users:
    requests-per-minute: 1000
    burst: 100

  api-keys:
    tier-1:
      requests-per-minute: 10000
      burst: 1000
    tier-2:
      requests-per-minute: 1000
      burst: 100
```

---

## API Versioning Strategies

### Versioning Approaches

**1. URI Path Versioning**
```yaml
# Version in URL path
/api/v1/users
/api/v2/users

# Pros: Clear versioning
# Cons: URL pollution, caching complexity
```

**2. Header-Based Versioning**
```yaml
# Version in header
GET /api/users
Accept: application/vnd.api+json;version=1
API-Version: v1

# Pros: Clean URLs, flexible
# Cons: Less discoverable, tooling support
```

**3. Query Parameter Versioning**
```yaml
# Version as query parameter
GET /api/users?version=v1
GET /api/users?api_version=2

# Pros: Simple implementation
# Cons: Cache complications, less RESTful
```

### Versioning Best Practices

**1. Backward Compatibility**
```python
# Version-specific serializers
class UserSerializerV1:
    fields = ['id', 'email', 'first_name', 'last_name']

class UserSerializerV2:
    fields = ['id', 'email', 'profile']  # Combined name fields

# Version routing
@app.route('/api/v1/users')
def list_users_v1():
    return serialize_users_v1(get_users())

@app.route('/api/v2/users')
def list_users_v2():
    return serialize_users_v2(get_users())
```

**2. Deprecation Strategy**
```yaml
deprecation-policy:
  support-duration: 12 months
  deprecation-notice: 3 months
  sunset-notice: 1 month

headers:
  deprecation: true
  sunset: "2025-06-21"
  link: '</api/v2/users>; rel="successor-version"'
```

---

## Error Handling & Response Formatting

### Error Handling Patterns

**1. Centralized Error Handler**
```python
class APIErrorHandler:
    ERROR_MAP = {
        ValidationError: (400, "VALIDATION_ERROR"),
        AuthenticationError: (401, "AUTHENTICATION_ERROR"),
        AuthorizationError: (403, "AUTHORIZATION_ERROR"),
        NotFoundError: (404, "NOT_FOUND"),
        ConflictError: (409, "CONFLICT"),
    }

    def handle_error(self, error):
        error_type = type(error)
        status, code = self.ERROR_MAP.get(error_type, (500, "INTERNAL_ERROR"))

        return {
            "error": {
                "code": code,
                "message": str(error),
                "timestamp": datetime.utcnow().isoformat(),
                "requestId": get_request_id()
            }
        }, status
```

**2. Validation Error Details**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": {
      "fields": [
        {
          "field": "email",
          "message": "Invalid email format",
          "value": "invalid-email"
        },
        {
          "field": "age",
          "message": "Must be between 18 and 100",
          "value": 15
        }
      ]
    }
  }
}
```

**3. Consistent Response Envelope**
```python
class ResponseEnvelope:
    @staticmethod
    def success(data, meta=None):
        response = {"data": data}
        if meta:
            response["meta"] = meta
        return response

    @staticmethod
    def error(error_code, message, details=None):
        response = {
            "error": {
                "code": error_code,
                "message": message
            }
        }
        if details:
            response["error"]["details"] = details
        return response
```

---

## Documentation Standards

### OpenAPI/Swagger Documentation

**1. API Specification Structure**
```yaml
openapi: 3.0.3
info:
  title: User Management API
  version: 2.0.0
  description: Comprehensive user management system
  contact:
    name: API Team
    email: api@example.com
  license:
    name: MIT
    url: https://opensource.org/licenses/MIT

servers:
  - url: https://api.example.com/v2
    description: Production server
  - url: https://staging-api.example.com/v2
    description: Staging server

paths:
  /users:
    get:
      summary: List users
      parameters:
        - name: page
          in: query
          schema:
            type: integer
            minimum: 1
            default: 1
        - name: limit
          in: query
          schema:
            type: integer
            minimum: 1
            maximum: 100
            default: 20
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    type: array
                    items:
                      $ref: '#/components/schemas/User'
                  pagination:
                    $ref: '#/components/schemas/Pagination'
```

**2. Schema Definitions**
```yaml
components:
  schemas:
    User:
      type: object
      required:
        - id
        - email
      properties:
        id:
          type: string
          format: uuid
          example: "550e8400-e29b-41d4-a716-446655440000"
        email:
          type: string
          format: email
          example: "user@example.com"
        profile:
          $ref: '#/components/schemas/UserProfile'
        created_at:
          type: string
          format: date-time
          example: "2025-12-21T10:30:00Z"

    UserProfile:
      type: object
      properties:
        first_name:
          type: string
          example: "John"
        last_name:
          type: string
          example: "Doe"
        avatar_url:
          type: string
          format: uri
          example: "https://example.com/avatars/user.jpg"
```

**3. API Documentation Best Practices**
```yaml
# Include comprehensive examples
examples:
  user_creation:
    summary: Create a new user
    value:
      email: "newuser@example.com"
      profile:
        first_name: "Jane"
        last_name: "Smith"

# Document authentication schemes
security:
  - BearerAuth: []
  - ApiKeyAuth: []

securitySchemes:
  BearerAuth:
    type: http
    scheme: bearer
    bearerFormat: JWT
  ApiKeyAuth:
    type: apiKey
    in: header
    name: X-API-Key
```

---

## Performance Optimization

### Caching Strategies

**1. HTTP Caching Headers**
```python
# Cache-Control Directives
@app.route('/api/users/{id}')
def get_user(id):
    user = get_user_from_db(id)

    response = jsonify(user)
    # Cache for 5 minutes
    response.cache_control.max_age = 300
    # Allow stale cache for 1 hour
    response.cache_control.stale_if_error = 3600
    # Vary by user role for different data
    response.vary = 'Authorization'

    return response

# ETag Implementation
@app.route('/api/products')
def list_products():
    products = get_products()
    etag = generate_etag(products)

    if request.headers.get('If-None-Match') == etag:
        return '', 304  # Not Modified

    response = jsonify(products)
    response.set_etag(etag)
    return response
```

**2. Redis Caching Layer**
```python
class CacheManager:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.default_ttl = 300  # 5 minutes

    async def get_cached_response(self, key):
        cached = await self.redis.get(key)
        if cached:
            return json.loads(cached)
        return None

    async def cache_response(self, key, data, ttl=None):
        ttl = ttl or self.default_ttl
        await self.redis.setex(key, ttl, json.dumps(data))
```

**3. Database Query Optimization**
```python
# Efficient database queries
def get_users_with_orders_optimized(user_ids):
    # Single query with joins instead of N+1 queries
    query = """
    SELECT u.*, o.id as order_id, o.total as order_total
    FROM users u
    LEFT JOIN orders o ON u.id = o.user_id
    WHERE u.id = ANY(%s)
    ORDER BY u.id, o.created_at
    """
    return execute_query(query, [user_ids])

# Pagination with cursor-based approach
def get_users_cursor(after=None, limit=20):
    if after:
        cursor = decode_cursor(after)
        query = "SELECT * FROM users WHERE id > %s ORDER BY id LIMIT %s"
        return execute_query(query, [cursor, limit])
    else:
        query = "SELECT * FROM users ORDER BY id LIMIT %s"
        return execute_query(query, [limit])
```

### Response Optimization

**1. Response Compression**
```python
# Gzip compression for large responses
from flask_compress import Compress

Compress(app)

# Configure compression levels
app.config['COMPRESS_LEVEL'] = 6
app.config['COMPRESS_MIMETYPES'] = [
    'application/json',
    'application/javascript',
    'text/css',
    'text/html'
]
```

**2. Field Selection and Filtering**
```python
# GraphQL-like field selection for REST APIs
@app.route('/api/users')
def list_users():
    fields = request.args.get('fields', 'id,email').split(',')
    users = get_users_from_db()

    filtered_users = []
    for user in users:
        filtered_user = {field: user[field] for field in fields if field in user}
        filtered_users.append(filtered_user)

    return jsonify(filtered_users)
```

---

## Testing Strategies

### API Testing Framework

**1. Integration Test Structure**
```python
class UserAPITestCase(TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.test_user = create_test_user()

    async def test_get_user_success(self):
        response = await self.client.get(f'/api/users/{self.test_user.id}')

        assert response.status_code == 200
        data = response.json()
        assert data['data']['id'] == self.test_user.id
        assert 'email' in data['data']

    async def test_get_user_not_found(self):
        fake_id = str(uuid.uuid4())
        response = await self.client.get(f'/api/users/{fake_id}')

        assert response.status_code == 404
        error = response.json()['error']
        assert error['code'] == 'NOT_FOUND'

    async def test_create_user_validation_error(self):
        invalid_data = {
            'email': 'invalid-email',
            'profile': {
                'first_name': ''
            }
        }

        response = await self.client.post('/api/users', json=invalid_data)

        assert response.status_code == 400
        error = response.json()['error']
        assert error['code'] == 'VALIDATION_ERROR'
        assert len(error['details']['fields']) > 0
```

**2. Contract Testing**
```python
# Pact contract testing
class UserConsumerContract:
    @pytest.mark.asyncio
    async def test_get_user_contract(self):
        pact = Consumer('user-consumer').has_pact_with(Provider('user-service'))

        pact.given('user exists')\
            .upon_receiving('get user request')\
            .with_request('GET', '/users/123')\
            .will_respond_with(200, body={
                'data': {
                    'id': '123',
                    'email': 'user@example.com',
                    'profile': {
                        'first_name': 'John',
                        'last_name': 'Doe'
                    }
                }
            })

        with pact:
            client = APIClient(pact.uri)
            response = await client.get('/users/123')
            assert response.status_code == 200
```

**3. Load Testing**
```python
# Locust load testing script
class UserAPILoadTest(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def get_user_list(self):
        self.client.get('/api/users?page=1&limit=20')

    @task(2)
    def get_user_details(self):
        user_id = random.choice(self.user_ids)
        self.client.get(f'/api/users/{user_id}')

    @task(1)
    def create_user(self):
        user_data = {
            'email': f'user{random.randint(1000, 9999)}@example.com',
            'profile': {
                'first_name': 'Test',
                'last_name': 'User'
            }
        }
        response = self.client.post('/api/users', json=user_data)
        if response.status_code == 201:
            self.user_ids.append(response.json()['data']['id'])
```

---

## Integration Patterns & Webhooks

### Webhook Implementation

**1. Webhook Delivery System**
```python
class WebhookDelivery:
    def __init__(self, retry_policy):
        self.retry_policy = retry_policy
        self.queue = asyncio.Queue()

    async def deliver_webhook(self, webhook_url, payload, signature):
        headers = {
            'Content-Type': 'application/json',
            'X-Webhook-Signature': signature,
            'X-Webhook-ID': str(uuid.uuid4()),
            'X-Webhook-Timestamp': str(int(time.time()))
        }

        async for attempt in AsyncRetryer(self.retry_policy):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(webhook_url,
                                          json=payload,
                                          headers=headers) as response:
                        if response.status == 200:
                            return True
                        raise WebhookDeliveryError(f"HTTP {response.status}")
            except Exception as e:
                if attempt == self.retry_policy.max_attempts:
                    raise e
                await asyncio.sleep(self.retry_policy.backoff(attempt))
```

**2. Webhook Signature Validation**
```python
class WebhookValidator:
    def __init__(self, secret):
        self.secret = secret

    def generate_signature(self, payload):
        payload_bytes = json.dumps(payload, sort_keys=True).encode()
        return hmac.new(
            self.secret.encode(),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()

    def verify_signature(self, payload, signature):
        expected = self.generate_signature(payload)
        return hmac.compare_digest(expected, signature)
```

**3. Event-Driven Integration**
```python
# Event Sourcing Pattern
class EventStore:
    def __init__(self, db_connection):
        self.db = db_connection

    async def save_event(self, aggregate_id, event_type, event_data):
        event = {
            'id': str(uuid.uuid4()),
            'aggregate_id': aggregate_id,
            'type': event_type,
            'data': json.dumps(event_data),
            'created_at': datetime.utcnow()
        }
        await self.db.execute(
            "INSERT INTO events (id, aggregate_id, type, data, created_at) "
            "VALUES (%(id)s, %(aggregate_id)s, %(type)s, %(data)s, %(created_at)s)",
            event
        )

    async def get_events(self, aggregate_id, from_version=0):
        events = await self.db.fetch(
            "SELECT * FROM events WHERE aggregate_id = %s AND version > %s "
            "ORDER BY created_at ASC",
            aggregate_id, from_version
        )
        return [self._deserialize_event(event) for event in events]
```

### API Gateway Patterns

**1. Request Routing**
```yaml
gateway:
  routes:
    - path: /api/v1/users/**
      upstream: http://user-service:8080
      methods: [GET, POST, PUT, DELETE]
      auth_required: true
      rate_limit: 100/minute

    - path: /api/v1/orders/**
      upstream: http://order-service:8082
      methods: [GET, POST]
      auth_required: true
      rate_limit: 200/minute
      circuit_breaker:
        threshold: 5
        timeout: 30s
```

**2. Request Transformation**
```python
class RequestTransformer:
    def transform_request(self, request, target_service):
        transformed = {
            'method': request.method,
            'path': request.path,
            'headers': self.transform_headers(request.headers, target_service),
            'query_params': request.query_params,
            'body': self.transform_body(request.body, target_service)
        }
        return transformed

    def transform_headers(self, headers, target_service):
        # Remove gateway-specific headers
        transformed = {k: v for k, v in headers.items()
                      if not k.startswith('X-Gateway-')}

        # Add service-specific headers
        transformed['X-Forwarded-For'] = headers.get('X-Real-IP')
        transformed['X-Service-Name'] = target_service

        return transformed
```

---

## Summary

This API Design Expertise file provides comprehensive patterns and best practices for:

1. **REST API Design** with proper HTTP semantics and resource-oriented architecture
2. **GraphQL Schema Design** following Relay specifications and performance optimizations
3. **Microservices Architecture** with communication patterns and data management strategies
4. **Security Patterns** including authentication, authorization, and rate limiting
5. **Versioning Strategies** to ensure backward compatibility and smooth migrations
6. **Error Handling** with consistent response formats and centralized error management
7. **Documentation Standards** using OpenAPI/Swagger for comprehensive API documentation
8. **Performance Optimization** through caching, compression, and query optimization
9. **Testing Strategies** covering integration, contract, and load testing approaches
10. **Integration Patterns** including webhooks and event-driven architectures

These patterns can be applied to design scalable, maintainable, and performant APIs that integrate seamlessly with the Persistent Learning Agent Ecosystem.