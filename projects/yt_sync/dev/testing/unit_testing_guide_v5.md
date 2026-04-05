# **Ultimate Python Testing Guide 2025: For Humans & AI**

## **🤖 AI Assistant Instructions**

<ai-instructions>
When writing Python tests, you MUST follow this guide's principles. Key rules:
1. **Always use pytest** (not unittest) for new tests
2. **Mock external dependencies** - Never hit real APIs, databases, or filesystems in unit tests
3. **Use AI tools** like Qodo for test generation, then refine manually
4. **Follow AAA pattern** - Arrange, Act, Assert in every test
5. **One behavior per test** - Each test should verify exactly one thing
6. **Use type hints** and validate with pyright/mypy
7. **Generate edge cases** with Hypothesis for comprehensive coverage
</ai-instructions>

---

## **📋 Quick Reference Card**

### **Essential Commands**
```bash
# Run tests with coverage
pytest --cov=myapp --cov-report=html

# Run tests in parallel (faster)
pytest -n auto

# Run only marked tests
pytest -m "not slow"

# Generate AI tests with Qodo
qodo generate tests/

# Type check before testing
pyright && pytest
```

### **Must-Have Dependencies**
```toml
[tool.poetry.dev-dependencies]
pytest = "^8.3"
pytest-asyncio = "^0.24"
pytest-cov = "^5.0"
pytest-xdist = "^3.6"
pytest-mock = "^3.14"
hypothesis = "^6.100"
syrupy = "^4.7"  # Snapshot testing
factory-boy = "^3.3"
faker = "^28.0"
pyright = "^1.1.380"
```

---

## **🎯 The Philosophy of Great Testing**

### **The Timeless Core Philosophy**
Before adopting modern tools, internalize these foundational goals:
- **A Unit Test Verifies a Single Behavior:** It answers one question, like "Does this function correctly calculate a discount?" It does not test the entire checkout process.
- **A Unit Test is Fast and Isolated:** It must not touch the network, the filesystem, or a real database. This ensures tests run in milliseconds and are 100% reliable. This is the key distinction between a **unit test** and an **integration test**.
- **Test the Behavior, Not the Implementation:** Your test should not care *how* a function gets the right answer, only that it *does*. If you refactor the internal logic of a function without changing its public contract, the test should still pass.

### **Testing Philosophy for 2025**
1. **AI-First Development**: Use AI tools to generate initial tests, then refine
2. **Type Safety**: Every test should be type-checked
3. **Speed Matters**: Tests must run in milliseconds, not seconds
4. **Edge Case Coverage**: Use property-based testing to find bugs humans miss

### **The Testing Pyramid**
- **Unit Tests**: Test single functions/classes in isolation (~80% of tests)
- **Integration Tests**: Test component interactions (~15% of tests)
- **E2E Tests**: Test complete user workflows (~5%, minimize these)

---

## **📚 Table of Contents**

### **Part 1: Foundations**
1. [Project Setup & Configuration](#1-project-setup--configuration)
2. [Test Organization & Naming](#2-test-organization--naming)
3. [AI-Powered Test Generation](#3-ai-powered-test-generation)
4. [Common Anti-Patterns to Avoid](#4-common-anti-patterns-to-avoid)

### **Part 2: Unit Testing**
5. [Writing Perfect Unit Tests](#5-writing-perfect-unit-tests)
6. [Mocking Mastery](#6-mocking-mastery)
7. [Async Testing Patterns](#7-async-testing-patterns)
8. [Testing with Type Safety](#8-testing-with-type-safety)

### **Part 3: Advanced Patterns**
9. [Factory Patterns & Test Data](#9-factory-patterns--test-data)
10. [Property-Based Testing](#10-property-based-testing)
11. [Snapshot Testing](#11-snapshot-testing)

### **Part 4: Integration Testing**
12. [Integration Test Patterns](#12-integration-test-patterns)
13. [Testing Microservices](#13-testing-microservices)
14. [Cloud-Native Testing](#14-cloud-native-testing)

### **Part 5: Specialized Testing**
15. [Testing ML/AI Code](#15-testing-mlai-code)
16. [Performance Testing](#16-performance-testing)
17. [Security Testing](#17-security-testing)

---

## **1. Project Setup & Configuration**

### **Modern pytest Configuration (pyproject.toml)**
```toml
[tool.pytest.ini_options]
minversion = "8.0"
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "-ra",
    "--strict-markers",
    "--cov=src",
    "--cov-branch",
    "--cov-report=term-missing:skip-covered",
    "--cov-report=html",
    "--cov-report=xml",
    "--cov-fail-under=80",
]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests",
]
asyncio_mode = "auto"  # Auto-detect async tests

[tool.coverage.run]
branch = true
source = ["src"]
omit = ["*/tests/*", "*/migrations/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if TYPE_CHECKING:",
]
```

### **Essential Fixtures (conftest.py)**
```python
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from faker import Faker
from factory import Factory

# Global fixtures available to all tests
@pytest.fixture
def faker():
    """Provides Faker instance for test data generation."""
    return Faker()

@pytest.fixture
def mock_async():
    """Factory for creating AsyncMock with proper cleanup."""
    mocks = []
    def _create_mock(**kwargs):
        mock = AsyncMock(**kwargs)
        mocks.append(mock)
        return mock
    yield _create_mock
    # Cleanup
    for mock in mocks:
        mock.reset_mock()

@pytest.fixture(autouse=True)
def fast_tests(monkeypatch):
    """Make all tests fast by default."""
    # Patch sleep functions to return immediately
    monkeypatch.setattr("time.sleep", lambda x: None)
    monkeypatch.setattr("asyncio.sleep", AsyncMock())
```

---

## **2. Test Organization & Naming**

### **Directory Structure**
```
project/
├── src/
│   └── myapp/
│       ├── models.py
│       ├── services.py
│       └── api.py
├── tests/
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_models.py
│   │   └── test_services.py
│   ├── integration/
│   │   └── test_api.py
│   └── factories/
│       └── user_factory.py
```

### **Naming Conventions**
```python
# ✅ GOOD: Descriptive test names that read like sentences
def test_user_creation_fails_when_email_is_invalid():
    """Test that user creation raises ValidationError for invalid emails."""

def test_calculate_discount_returns_zero_when_user_is_not_premium():
    """Test discount calculation for non-premium users."""

# ❌ BAD: Vague or implementation-focused names
def test_user()  # Too vague
def test_email_regex()  # Implementation detail
```

---

## **3. AI-Powered Test Generation**

### **Using Qodo (formerly CodiumAI)**
```python
# Step 1: Install Qodo
# pip install qodo-ai

# Step 2: Generate tests for a module
# qodo generate src/myapp/services.py

# Step 3: Review and enhance generated tests
# Original generated test:
def test_calculate_total_basic():
    result = calculate_total([10, 20, 30])
    assert result == 60

# Enhanced with edge cases and better assertions:
@pytest.mark.parametrize("items,expected", [
    ([], 0),  # Empty list
    ([10, 20, 30], 60),  # Normal case
    ([0.1, 0.2], 0.3),  # Floats
    ([-10, 20], 10),  # Negative numbers
    ([Decimal('0.1'), Decimal('0.2')], Decimal('0.3')),  # Decimals
])
def test_calculate_total_handles_various_inputs(items, expected):
    """Test calculate_total with various input types and edge cases."""
    result = calculate_total(items)
    assert result == expected
```

### **AI Test Generation Best Practices**
1. **Always review AI output** - AI can miss edge cases or business logic
2. **Add domain context** - AI doesn't know your business rules
3. **Enhance with property tests** - Combine AI with Hypothesis
4. **Validate type safety** - Ensure generated tests pass type checking

---

## **4. Common Anti-Patterns to Avoid**

Knowing what *not* to do is as important as knowing what to do. Avoid these common pitfalls.

- **Testing Implementation Details:** A test that asserts `self.my_internal_list.append()` was called is brittle. Instead, assert the public-facing outcome (e.g., `assert my_object.item_count == 1`). This allows you to refactor internals without breaking tests.
- **Inter-dependent Tests:** Test A should **never** rely on Test B running first. Each test must be able to run independently and in any order. Use `pytest` fixtures to guarantee a clean state for every test.
- **Non-Deterministic Tests:** Avoid using functions like `datetime.now()` or `random.random()` directly in your code under test. Instead, inject them as dependencies so you can mock them and control their output.
- **Overly Complex Mocks (`Mock-hell`):** If a test requires mocking five different objects with complex `side_effect` and `return_value` chains, it's a strong signal that the code under test is doing too much (violating the Single Responsibility Principle). Refactor the code to be simpler and have fewer dependencies.
- **Testing Your Mocks:** Do not write assertions against the configuration of your mock itself (e.g., `assert mock_obj.return_value == 5`). Instead, assert the *effect* that the mock's return value had on your code's behavior.

---

## **5. Writing Perfect Unit Tests**

### **The AAA Pattern**
Structure every test logically with Arrange-Act-Assert for maximum clarity.
- **Arrange**: Set up all test data, mocks, and object instances.
- **Act**: Execute the single function or method you are testing.
- **Assert**: Verify the results and side effects.

```python
def test_user_service_creates_user_with_hashed_password():
    # ARRANGE: Set up test data and mocks
    user_data = {"email": "test@example.com", "password": "secret123"}
    mock_repo = MagicMock(spec=UserRepository)
    mock_repo.save.return_value = User(id=1, email=user_data["email"])
    service = UserService(repository=mock_repo)

    # ACT: Execute the code under test
    user = service.create_user(**user_data)

    # ASSERT: Verify the results
    assert user.id == 1
    assert user.email == user_data["email"]
    # Verify password was hashed (not stored as plaintext)
    saved_user = mock_repo.save.call_args[0][0]
    assert saved_user.password != "secret123"
    assert saved_user.password.startswith("$2b$")  # bcrypt hash
```

### **Testing Exceptions**
```python
def test_withdrawal_fails_when_insufficient_funds():
    """Test that withdrawal raises InsufficientFundsError."""
    account = BankAccount(balance=100)

    with pytest.raises(InsufficientFundsError) as exc_info:
        account.withdraw(150)

    # Verify exception details
    assert exc_info.value.requested_amount == 150
    assert exc_info.value.available_balance == 100
    assert "Insufficient funds" in str(exc_info.value)
```

---

## **6. Mocking Mastery**

### **Essential Mocking Rules**

#### **Rule 1: Always Use `spec` or `autospec`**
This ensures your mock has the same API as the real object. It prevents "mock drift," where your tests pass but your application breaks because a method was renamed. `autospec=True` is even stricter and recommended.

```python
# ✅ GOOD: Will fail if the real object's API changes
mock_service = MagicMock(spec=PaymentService)
mock_service.process_payment(amount=100)  # OK
mock_service.nonexistent_method()  # AttributeError!

# ❌ BAD: Allows any method call, creating a false sense of security
mock_service = MagicMock()
mock_service.anything_goes()  # No error, hiding potential bugs
```

#### **Rule 2: Patch Where Used, Not Where Defined**
You must patch the object in the namespace where it is *imported and used*, not where it is originally defined. This is the most common mocking mistake.

```python
# app/services.py
from app.email import send_email

def notify_user(user_id):
    send_email(user_id)

# ✅ GOOD: Patch where it's used
@patch('app.services.send_email')
def test_notify_user(mock_send):
    notify_user(123)
    mock_send.assert_called_once_with(123)

# ❌ BAD: Patching where it's defined won't work because app.services
# already has its own reference to the original function.
@patch('app.email.send_email')
```

#### **Rule 3: Mock External Dependencies Only**
The purpose of mocking is to isolate your code from external systems (databases, APIs, filesystem) or complex internal components. Do not mock simple, pure functions or your own business logic.

```python
# ✅ GOOD: Mock external service
@patch('requests.post')
def test_api_client_sends_data(mock_post):
    mock_post.return_value.json.return_value = {"status": "ok"}
    client = APIClient()
    result = client.send_data({"key": "value"})
    assert result["status"] == "ok"

# ❌ BAD: Don't mock your own simple logic
# Don't mock: math operations, string manipulation, pure functions
```

### **Advanced Mocking Patterns**

#### **Context Manager Mocking**
```python
def test_file_processor_handles_large_file():
    mock_file = MagicMock()
    mock_file.__enter__.return_value = mock_file
    mock_file.read.return_value = "test content"

    with patch('builtins.open', return_value=mock_file):
        result = process_file('large.txt')
        assert result == "PROCESSED: test content"
```

#### **Sequential Return Values**
```python
def test_retry_mechanism():
    mock_api = MagicMock()
    # First two calls fail, third succeeds
    mock_api.call.side_effect = [
        ConnectionError("Network error"),
        ConnectionError("Network error"),
        {"status": "success"}
    ]

    with patch('app.external_api', mock_api):
        result = retry_api_call(max_retries=3)
        assert result["status"] == "success"
        assert mock_api.call.call_count == 3
```

---

## **7. Async Testing Patterns**

### **Basic Async Testing**
```python
@pytest.mark.asyncio
async def test_async_user_fetcher():
    # Mock async dependencies
    mock_client = AsyncMock(spec=HTTPClient)
    mock_client.get.return_value = {"id": 1, "name": "Alice"}

    fetcher = UserFetcher(client=mock_client)
    user = await fetcher.fetch_user(1)

    assert user.name == "Alice"
    mock_client.get.assert_awaited_once_with("/users/1")
```

### **Testing Async Context Managers**
```python
@pytest.mark.asyncio
async def test_database_connection():
    mock_conn = AsyncMock()
    mock_conn.__aenter__.return_value = mock_conn
    mock_conn.execute.return_value = [{"id": 1}]

    async with mock_conn as conn:
        result = await conn.execute("SELECT * FROM users")
        assert len(result) == 1
```

### **Concurrent Testing**
```python
@pytest.mark.asyncio
async def test_concurrent_operations():
    async def slow_operation(n):
        await asyncio.sleep(0.1)
        return n * 2

    # Patch sleep to make test fast
    with patch('asyncio.sleep', new_callable=AsyncMock):
        results = await asyncio.gather(
            slow_operation(1),
            slow_operation(2),
            slow_operation(3)
        )
        assert results == [2, 4, 6]
```

---

## **8. Testing with Type Safety**

### **Type-Safe Test Setup**
```python
from typing import Protocol
import pytest
from myapp.models import User
from myapp.repositories import UserRepository

class MockUserRepository(Protocol):
    """Type-safe mock interface."""
    async def get(self, user_id: int) -> User | None: ...
    async def save(self, user: User) -> User: ...

@pytest.fixture
def mock_user_repo() -> MockUserRepository:
    """Provides type-safe mock repository."""
    repo = AsyncMock(spec=UserRepository)
    # Type annotations ensure correct usage
    repo.get.return_value = User(id=1, name="Test")
    return repo
```

### **Testing Type Behavior**
```python
def test_type_inference_with_generics():
    """Test that generic types are properly inferred."""
    from typing import TypeVar, Generic

    T = TypeVar('T')

    class Container(Generic[T]):
        def __init__(self, value: T) -> None:
            self.value = value

        def get(self) -> T:
            return self.value

    # Test type inference
    int_container = Container(42)
    assert isinstance(int_container.get(), int)

    str_container = Container("hello")
    assert isinstance(str_container.get(), str)
```

---

## **9. Factory Patterns & Test Data**

### **Using Factory Boy**
```python
# factories/user_factory.py
import factory
from factory import fuzzy
from myapp.models import User

class UserFactory(factory.Factory):
    class Meta:
        model = User

    id = factory.Sequence(lambda n: n)
    email = factory.LazyAttribute(lambda obj: f"user{obj.id}@example.com")
    username = factory.Faker('user_name')
    age = fuzzy.FuzzyInteger(18, 80)
    is_premium = factory.Faker('boolean', chance_of_getting_true=25)
    created_at = factory.Faker('date_time_this_year')

    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        if not create or not extracted:
            return
        self.tags.add(*extracted)

# Using the factory in tests
def test_premium_user_gets_discount():
    user = UserFactory(is_premium=True, age=30)
    discount = calculate_discount(user)
    assert discount == 0.2  # 20% discount

def test_bulk_user_creation():
    users = UserFactory.create_batch(10, is_premium=True)
    assert all(u.is_premium for u in users)
    assert len(set(u.email for u in users)) == 10  # All unique
```

### **Dynamic Test Data with Faker**
```python
@pytest.fixture
def fake_user_data(faker):
    """Generate realistic user data."""
    return {
        'first_name': faker.first_name(),
        'last_name': faker.last_name(),
        'email': faker.email(),
        'phone': faker.phone_number(),
        'address': {
            'street': faker.street_address(),
            'city': faker.city(),
            'country': faker.country(),
            'postal_code': faker.postcode()
        },
        'credit_card': faker.credit_card_number(),
        'bio': faker.text(max_nb_chars=200)
    }

def test_user_registration_with_realistic_data(fake_user_data):
    response = register_user(fake_user_data)
    assert response.status_code == 201
    assert response.json()['email'] == fake_user_data['email']
```

---

## **10. Property-Based Testing**

### **Hypothesis Fundamentals**
```python
from hypothesis import given, strategies as st, assume

@given(st.lists(st.integers()))
def test_sorting_properties(input_list):
    """Test that sorting maintains essential properties."""
    sorted_list = sorted(input_list)

    # Property 1: Length is preserved
    assert len(sorted_list) == len(input_list)

    # Property 2: Elements are preserved
    assert set(sorted_list) == set(input_list)

    # Property 3: Result is ordered
    for i in range(len(sorted_list) - 1):
        assert sorted_list[i] <= sorted_list[i + 1]

@given(st.text(min_size=1))
def test_string_sanitization_never_produces_empty(input_str):
    """Test that sanitization never produces empty strings."""
    assume(input_str.strip())  # Skip empty/whitespace-only

    sanitized = sanitize_username(input_str)
    assert len(sanitized) > 0
    assert all(c.isalnum() or c == '_' for c in sanitized)
```

### **Advanced Property Testing**
```python
# Custom strategies for domain objects
@st.composite
def user_strategy(draw):
    return User(
        id=draw(st.integers(min_value=1)),
        email=draw(st.emails()),
        age=draw(st.integers(min_value=0, max_value=150)),
        balance=draw(st.decimals(min_value=0, max_value=1000000, places=2))
    )

@given(user_strategy())
def test_account_operations_maintain_invariants(user):
    """Test that account operations maintain business invariants."""
    initial_balance = user.balance

    # Property: Balance never goes negative
    if initial_balance >= 100:
        user.withdraw(100)
        assert user.balance == initial_balance - 100
    else:
        with pytest.raises(InsufficientFundsError):
            user.withdraw(100)

    # Property: Deposits always increase balance
    deposit_amount = Decimal('50.00')
    user.deposit(deposit_amount)
    assert user.balance > initial_balance
```

---

## **11. Snapshot Testing**

### **Using Syrupy**
```python
def test_api_response_structure(snapshot):
    """Test that API response matches expected structure."""
    response = get_user_profile(user_id=123)

    # Snapshot will be created on first run
    assert response == snapshot

def test_rendered_html_output(snapshot):
    """Test that HTML rendering is consistent."""
    user = User(name="Alice", role="admin")
    html = render_user_card(user)

    assert html == snapshot

# Update snapshots when needed:
# pytest --snapshot-update
```

### **Snapshot Testing Best Practices**
```python
def test_complex_calculation_output(snapshot):
    """Test complex calculations with snapshots."""
    # Exclude volatile fields
    result = perform_complex_calculation()

    # Remove timestamps and random IDs before snapshot
    sanitized_result = {
        **result,
        'timestamp': 'TIMESTAMP',
        'request_id': 'REQUEST_ID'
    }

    assert sanitized_result == snapshot
```

---

## **12. Integration Test Patterns**

### **Database Integration Tests**
```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture(scope="function")
def test_db():
    """Provide clean test database for each test."""
    # Use in-memory SQLite for speed
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    yield session

    session.close()
    Base.metadata.drop_all(engine)

def test_user_repository_integration(test_db):
    """Test real database operations."""
    repo = UserRepository(test_db)

    # Create user
    user = repo.create(email="test@example.com", name="Test User")
    assert user.id is not None

    # Fetch user
    fetched = repo.get(user.id)
    assert fetched.email == "test@example.com"

    # Update user
    repo.update(user.id, name="Updated Name")
    updated = repo.get(user.id)
    assert updated.name == "Updated Name"
```

### **API Integration Tests**
```python
@pytest.fixture
def test_client():
    """Provide test client for API testing."""
    from myapp import create_app
    app = create_app(config="testing")

    with app.test_client() as client:
        yield client

def test_api_user_workflow(test_client, test_db):
    """Test complete user workflow through API."""
    # Register user
    register_response = test_client.post('/api/register', json={
        'email': 'newuser@example.com',
        'password': 'secure123'
    })
    assert register_response.status_code == 201
    user_id = register_response.json['id']

    # Login
    login_response = test_client.post('/api/login', json={
        'email': 'newuser@example.com',
        'password': 'secure123'
    })
    assert login_response.status_code == 200
    token = login_response.json['token']

    # Access protected endpoint
    profile_response = test_client.get(
        f'/api/users/{user_id}',
        headers={'Authorization': f'Bearer {token}'}
    )
    assert profile_response.status_code == 200
    assert profile_response.json['email'] == 'newuser@example.com'
```

---

## **13. Testing Microservices**

### **Using Testcontainers**
```python
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer
from testcontainers.kafka import KafkaContainer

@pytest.fixture(scope="session")
def postgres_container():
    """Provide PostgreSQL container for tests."""
    with PostgresContainer("postgres:15") as postgres:
        yield postgres

@pytest.fixture(scope="session")
def redis_container():
    """Provide Redis container for tests."""
    with RedisContainer("redis:7") as redis:
        yield redis

def test_service_with_real_dependencies(postgres_container, redis_container):
    """Test service with real PostgreSQL and Redis."""
    # Get connection URLs
    postgres_url = postgres_container.get_connection_url()
    redis_url = redis_container.get_connection_url()

    # Initialize service with real dependencies
    service = MyService(
        db_url=postgres_url,
        cache_url=redis_url
    )

    # Test with real infrastructure
    result = service.process_data({"key": "value"})
    assert result['status'] == 'processed'

    # Verify data was cached
    cached = service.get_from_cache("key")
    assert cached == "value"
```

### **Contract Testing with Pact**
```python
from pact import Consumer, Provider

def test_user_service_contract():
    """Test contract between services."""
    pact = Consumer('OrderService').has_pact_with(
        Provider('UserService'),
        host_name='localhost',
        port=1234
    )

    expected_user = {
        'id': 123,
        'name': 'Alice',
        'email': 'alice@example.com'
    }

    (pact
     .given('User 123 exists')
     .upon_receiving('a request for user 123')
     .with_request('GET', '/users/123')
     .will_respond_with(200, body=expected_user))

    with pact:
        # Test consumer code
        user = get_user_from_service(123)
        assert user['name'] == 'Alice'
```

---

## **14. Cloud-Native Testing**

### **Testing AWS Services with Moto**
```python
import boto3
from moto import mock_s3, mock_dynamodb

@mock_s3
def test_s3_operations():
    """Test S3 operations with mocked AWS."""
    # Create mock S3 bucket
    s3 = boto3.client('s3', region_name='us-east-1')
    s3.create_bucket(Bucket='test-bucket')

    # Test upload
    s3.put_object(
        Bucket='test-bucket',
        Key='test.txt',
        Body=b'Hello World'
    )

    # Test download
    response = s3.get_object(Bucket='test-bucket', Key='test.txt')
    assert response['Body'].read() == b'Hello World'

@mock_dynamodb
def test_dynamodb_operations():
    """Test DynamoDB operations."""
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

    # Create table
    table = dynamodb.create_table(
        TableName='users',
        KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
        BillingMode='PAY_PER_REQUEST'
    )

    # Test operations
    table.put_item(Item={'id': '123', 'name': 'Alice'})
    response = table.get_item(Key={'id': '123'})
    assert response['Item']['name'] == 'Alice'
```

### **Kubernetes Testing**
```python
from kubernetes import client, config
import pytest

@pytest.fixture
def k8s_client():
    """Provide Kubernetes client for testing."""
    # Use in-cluster config or local kubeconfig
    try:
        config.load_incluster_config()
    except:
        config.load_kube_config()

    return client.CoreV1Api()

def test_pod_creation(k8s_client):
    """Test creating pods in Kubernetes."""
    pod_manifest = {
        'apiVersion': 'v1',
        'kind': 'Pod',
        'metadata': {'name': 'test-pod'},
        'spec': {
            'containers': [{
                'name': 'test-container',
                'image': 'nginx:latest'
            }]
        }
    }

    # Create pod
    k8s_client.create_namespaced_pod(
        namespace='default',
        body=pod_manifest
    )

    # Verify pod exists
    pods = k8s_client.list_namespaced_pod(namespace='default')
    pod_names = [p.metadata.name for p in pods.items]
    assert 'test-pod' in pod_names
```

---

## **15. Testing ML/AI Code**

### **Testing LLM Applications**
```python
from deepeval import assert_test
from deepeval.metrics import AnswerRelevancyMetric, HallucinationMetric
from deepeval.test_case import LLMTestCase

def test_llm_response_quality():
    """Test LLM response quality metrics."""
    test_case = LLMTestCase(
        input="What is the capital of France?",
        actual_output="The capital of France is Paris.",
        expected_output="Paris is the capital of France.",
        context=["France is a country in Europe", "Paris is the capital city of France"]
    )

    # Test relevancy
    relevancy_metric = AnswerRelevancyMetric(threshold=0.8)
    assert_test(test_case, [relevancy_metric])

    # Test for hallucinations
    hallucination_metric = HallucinationMetric(threshold=0.1)
    assert_test(test_case, [hallucination_metric])

def test_model_predictions():
    """Test ML model predictions."""
    import numpy as np
    from sklearn.metrics import accuracy_score

    # Load test data
    X_test = np.array([[1, 2], [3, 4], [5, 6]])
    y_true = np.array([0, 1, 0])

    # Get predictions
    model = load_model('model.pkl')
    y_pred = model.predict(X_test)

    # Test accuracy threshold
    accuracy = accuracy_score(y_true, y_pred)
    assert accuracy >= 0.95  # 95% accuracy requirement

    # Test prediction invariants
    assert all(pred in [0, 1] for pred in y_pred)  # Binary classification
    assert len(y_pred) == len(X_test)
```

### **Data Pipeline Testing**
```python
import pandas as pd
import pytest
from deepchecks.tabular import Dataset
from deepchecks.tabular.checks import DataDuplicates, MixedNulls

def test_data_pipeline_quality():
    """Test data pipeline output quality."""
    # Process data through pipeline
    raw_data = pd.read_csv('raw_data.csv')
    processed_data = data_pipeline.process(raw_data)

    # Create Deepchecks dataset
    ds = Dataset(processed_data, label='target')

    # Check for duplicates
    duplicate_check = DataDuplicates()
    result = duplicate_check.run(ds)
    assert result.passed(), "Pipeline produced duplicate records"

    # Check for mixed nulls
    null_check = MixedNulls()
    result = null_check.run(ds)
    assert result.passed(), "Pipeline has inconsistent null handling"

    # Check output schema
    expected_columns = ['id', 'feature1', 'feature2', 'target']
    assert list(processed_data.columns) == expected_columns
```

---

## **16. Performance Testing**

### **Benchmark Testing**
```python
import pytest
from pytest_benchmark.plugin import benchmark

def fibonacci(n):
    if n < 2:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

def test_fibonacci_performance(benchmark):
    """Test fibonacci performance."""
    result = benchmark(fibonacci, 10)
    assert result == 55

    # Benchmark automatically measures:
    # - min, max, mean, stddev
    # - iterations and rounds
    # Can set thresholds in pytest.ini

@pytest.mark.benchmark(
    group="sorting",
    min_rounds=100,
    max_time=1.0,
    timer=time.perf_counter
)
def test_sorting_algorithms(benchmark):
    """Compare sorting algorithm performance."""
    data = list(range(1000, 0, -1))

    def run_sort():
        return sorted(data.copy())

    result = benchmark(run_sort)
    assert result == list(range(1, 1001))
```

### **Load Testing with Locust**
```python
from locust import HttpUser, task, between

class WebsiteUser(HttpUser):
    wait_time = between(1, 5)  # Wait 1-5 seconds between tasks

    @task
    def index_page(self):
        self.client.get("/")

    @task(3)  # 3x more likely than other tasks
    def view_products(self):
        self.client.get("/products")

    @task
    def create_order(self):
        self.client.post("/orders", json={
            "product_id": 123,
            "quantity": 1
        })

    def on_start(self):
        # Login when user starts
        self.client.post("/login", json={
            "username": "testuser",
            "password": "password"
        })
```

---

## **17. Security Testing**

### **Input Validation Testing**
```python
import pytest
from hypothesis import given, strategies as st

# Common attack patterns
SQL_INJECTION_PAYLOADS = [
    "' OR '1'='1",
    "'; DROP TABLE users; --",
    "1' UNION SELECT * FROM passwords; --"
]

XSS_PAYLOADS = [
    "<script>alert('XSS')</script>",
    "<img src=x onerror=alert('XSS')>",
    "javascript:alert('XSS')"
]

@pytest.mark.parametrize("payload", SQL_INJECTION_PAYLOADS)
def test_sql_injection_prevention(payload):
    """Test that SQL injection attempts are blocked."""
    with pytest.raises(ValidationError):
        search_users(payload)

@pytest.mark.parametrize("payload", XSS_PAYLOADS)
def test_xss_prevention(payload):
    """Test that XSS attempts are sanitized."""
    result = render_user_input(payload)
    assert "<script>" not in result
    assert "javascript:" not in result
    # Ensure proper HTML escaping
    assert "&lt;script&gt;" in result or result == ""
```

### **Authentication Testing**
```python
def test_password_requirements():
    """Test password security requirements."""
    weak_passwords = [
        "123456",  # Too simple
        "password",  # Common password
        "short",  # Too short
        "alllowercase",  # No complexity
    ]

    for password in weak_passwords:
        with pytest.raises(WeakPasswordError):
            validate_password(password)

    # Strong password should pass
    strong_password = "MyStr0ng!P@ssw0rd"
    assert validate_password(strong_password) is True

def test_authentication_rate_limiting():
    """Test that authentication has rate limiting."""
    # Attempt multiple failed logins
    for i in range(5):
        response = login("user@example.com", "wrongpassword")
        assert response.status_code == 401

    # 6th attempt should be rate limited
    response = login("user@example.com", "wrongpassword")
    assert response.status_code == 429  # Too Many Requests
    assert "Rate limit exceeded" in response.json()["error"]
```

---

## **🚀 Quick Start Checklist**

### **For New Projects**
- [ ] Set up `pyproject.toml` with pytest configuration
- [ ] Install essential testing dependencies
- [ ] Create `tests/` directory structure
- [ ] Write `conftest.py` with common fixtures
- [ ] Set up CI/CD with test automation
- [ ] Configure coverage requirements (80%+)
- [ ] Add pre-commit hooks for tests

### **For Each New Feature**
- [ ] Write tests first (TDD) or immediately after
- [ ] Use AI tools to generate initial test cases
- [ ] Add property-based tests for complex logic
- [ ] Mock all external dependencies
- [ ] Test error cases and edge conditions
- [ ] Run with coverage to find gaps
- [ ] Ensure all tests are fast (<100ms each)

### **Before Each Commit**
- [ ] Run full test suite locally
- [ ] Check coverage hasn't decreased
- [ ] Verify no tests are skipped
- [ ] Update snapshots if needed
- [ ] Run type checker (pyright/mypy)
- [ ] Fix any flaky tests

---

## **📝 Common Testing Patterns Reference**

### **Testing Async Generators**
```python
@pytest.mark.asyncio
async def test_async_generator():
    async def count_to_three():
        for i in range(1, 4):
            await asyncio.sleep(0.1)
            yield i

    with patch('asyncio.sleep', new_callable=AsyncMock):
        results = [i async for i in count_to_three()]
        assert results == [1, 2, 3]
```

### **Testing Decorators**
```python
def test_cache_decorator():
    call_count = 0

    @cache_result(ttl=60)
    def expensive_function(x):
        nonlocal call_count
        call_count += 1
        return x * 2

    # First call
    assert expensive_function(5) == 10
    assert call_count == 1

    # Second call should use cache
    assert expensive_function(5) == 10
    assert call_count == 1  # Not incremented
```

### **Testing Context Managers**
```python
from contextlib import contextmanager

def test_custom_context_manager():
    resource_closed = False

    @contextmanager
    def managed_resource():
        resource = {"open": True}
        try:
            yield resource
        finally:
            resource["open"] = False
            nonlocal resource_closed
            resource_closed = True

    with managed_resource() as res:
        assert res["open"] is True

    assert resource_closed is True
```

---

## **🎯 Final Best Practices**

1. **Speed is Critical**: Every test should run in <100ms. Mock anything slow.
2. **Clarity Over Cleverness**: Write tests that junior devs can understand.
3. **Test Behaviors, Not Implementation**: Focus on public APIs and outcomes.
4. **Fail Fast, Fail Clear**: Test failures should immediately reveal the problem.
5. **Embrace AI, But Verify**: Use AI tools to generate tests, but always review.
6. **Type Safety Throughout**: Use type hints and validate with type checkers.
7. **Property Tests Find Bugs**: Use Hypothesis for complex logic testing.
8. **Integration Tests Sparingly**: Most tests should be unit tests.
9. **Mock External Only**: Never mock your own simple business logic.
10. **Continuous Improvement**: Regularly refactor tests like production code.

Remember: **Great tests enable fearless refactoring and catch bugs before users do.**
