# arch Examples

This directory contains usage examples for the `arch` architecture advisor.

## Examples

### `basic_usage.py`
Getting architectural recommendations for a simple web service.

Run:
```bash
cd packages/arch
python examples/basic_usage.py
```

### `pattern_matching.py` (TODO)
Demonstrates pattern matching for different project types.

### `custom_patterns.py` (TODO)
Shows how to add custom architectural patterns.

## Expected Output

For `basic_usage.py`:
```
Recommended Pattern: modular_monolith
Rationale: Team size (3) and traffic (<1000 req/day) make microservices overhead unjustified.
Modular monolith provides clear boundaries while maintaining simplicity.

Suggested Structure:
e-commerce-api/
├── api/           # REST endpoints
├── services/      # Business logic (billing, inventory, orders)
├── models/        # Data models
├── db/            # Database layer
└── auth/          # Authentication

Key Decisions:
  - Use FastAPI for REST framework (async, type-safe)
  - PostgreSQL for data persistence (ACID compliance for orders)
  - Modular structure to enable future microservice extraction
  - JWT-based authentication

Trade-offs:
  - Monolith → Faster development, easier deployment
  - PostgreSQL → Additional operational overhead vs SQLite
  - FastAPI → Smaller ecosystem vs Flask
```
