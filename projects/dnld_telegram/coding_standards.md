# Coding Standards: Async/Await Patterns

## Overview
This document establishes coding standards for async/await patterns in the dnld_telegram project, based on fixes applied during RCA investigation.

## Critical Rule: Async Function Calls Must Be Awaited

### Problem Pattern (INCORRECT)
```python
# WRONG: Calling async function without await
downloaded_files = load_downloaded_files(channel_name)
# Results in: RuntimeWarning: coroutine 'load_downloaded_files' was never awaited
```

### Correct Pattern (REQUIRED)
```python
# CORRECT: Always await async function calls
downloaded_files = await load_downloaded_files(channel_name)
```

## Async/Await Standards

### 1. Function Definition Standards
- Mark functions as `async def` when they perform I/O operations or call other async functions
- Use descriptive function names that indicate async nature when appropriate

### 2. Function Call Standards
- **MANDATORY**: All calls to async functions MUST use the `await` keyword
- Never call async functions without `await` - this creates unresolved coroutines
- Add inline comments explaining async requirements at critical call sites

### 3. Error Prevention
- Use linting tools (mypy, pylint) to catch missing `await` keywords
- Review all function calls in async contexts during code review
- Test async code paths thoroughly to catch runtime warnings

## Implementation Examples

### Fixed Locations in download.py

#### Location 1: Line 715 - download_media_from_message()
```python
# ASYNC REQUIREMENT: load_downloaded_files() is async and MUST be awaited
# Fixed: Added await to prevent "RuntimeWarning: coroutine never awaited"
downloaded_files = await load_downloaded_files(channel_name)
```

#### Location 2: Line 1408 - _prepare_download_session()
```python
# ASYNC REQUIREMENT: load_downloaded_files() is async and MUST be awaited
# Fixed: Added await to prevent "RuntimeWarning: coroutine never awaited"
downloaded_files = await load_downloaded_files(channel_name)
```

#### Location 3: Line 1457 - _try_offline_download_session()
```python
# ASYNC REQUIREMENT: load_downloaded_files() returns a coroutine that must be awaited
downloaded_files = await load_downloaded_files(channel_name)
```

## Common Async Patterns in This Project

### 1. Storage Operations
```python
# All storage operations are async
await save_downloaded_files(channel_name, downloaded_files)
await load_downloaded_files(channel_name)
await save_enumerated_files(channel_name, enumerated_files, chat_id)
```

### 2. Telegram API Operations
```python
# Telethon operations are async
entity = await client.get_entity(chat_id)
message = await client.get_messages(entity, ids=message_id)
downloaded_file = await client.download_media(message, file=path)
```

### 3. Database Operations
```python
# Database operations in async context
async with get_connection(channel_name) as conn:
    cursor = conn.execute(query, params)
    result = cursor.fetchall()
```

## Debugging Async Issues

### Common Warning Signs
1. `RuntimeWarning: coroutine 'function_name' was never awaited`
2. Functions returning `<coroutine object>` instead of expected values
3. Infinite loops or hanging behavior in async code

### Debugging Steps
1. Check all async function calls have `await` keyword
2. Verify function definitions are marked `async def` when needed
3. Ensure proper exception handling in async contexts
4. Use `asyncio.create_task()` for concurrent operations

## Testing Standards

### 1. Async Test Functions
- Use `pytest-asyncio` for testing async functions
- Mark test functions with `@pytest.mark.asyncio`

### 2. Mock Async Functions
```python
# When mocking async functions
@pytest.fixture
def mock_load_downloaded_files():
    async def _mock_load(channel_name):
        return {}
    return _mock_load
```

## Code Review Checklist

- [ ] All async function calls use `await` keyword
- [ ] Functions performing I/O are marked `async def`
- [ ] No coroutine warnings in test output
- [ ] Proper exception handling in async contexts
- [ ] Inline comments explain async requirements at critical locations

## Library-Specific Patterns

### Telethon Library
- All Telethon client operations are async
- Use proper session management with async context managers
- Handle network timeouts and connection errors appropriately

### SQLite with aiosqlite
- Use `async with` for database connections
- Await all cursor operations
- Properly handle database transaction rollbacks

---

*Last Updated: Based on RCA fixes applied 2025-01-21*
*Next Review: When adding new async functionality*
