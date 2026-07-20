# /handoff tests

Behavior and mutation tests for the `/handoff` skill validators.

## What's tested

### `test_behavior.py` — behavior tests

Verify the validators accept well-formed handoffs and reject malformed ones at the behavior level. Uses complete handoff documents (not snippets) to exercise the end-to-end validation pipeline.

Each test corresponds to a contract behavior:
- Valid handoff passes with zero errors
- Missing required header field is an error
- Malformed UUID in header is an error
- Missing body section is an error
- Task packet missing falsifier is an error
- Trivial falsifier is a warning (not blocking)
- Bad verification level is an error
- Paraphrased user message fails verbatim check
- Bad status / type / timestamp rejected
- Parsers handle quotes, comments, missing frontmatter

### `test_mutation.py` — mutation tests

Verify each validator catches its **specific** failure mode. For each validator, apply a mutation that the validator is supposed to catch and assert a matching error is raised. Guards against silent regressions where a validator becomes a no-op.

Mutation discipline:
- Each test mutates exactly one thing
- Each test asserts the specific validator catches it (not just "some error")
- Each test asserts the correct severity (error vs warning)

Coverage:
- `validate_header` — each required field, UUID format, timestamp format, status/type enums, parent path absoluteness
- `validate_body_sections` — each required section, case-insensitive matching
- `validate_task_packets` — each required sub-field, verification level enum, trivial-falsifier warning
- `validate_verbatim_message` — no quote, empty quote, short quote, valid quote
- `validate_streams_section_format` — absent section, empty section, bullet without status, valid bullets
- End-to-end integration — removing any required section, corrupting any header field, removing any packet sub-field

## Running

```bash
cd P:\.grok\skills\handoff
python -m pytest tests/ -v
```

The `conftest.py` adds `__lib/` to `sys.path` so imports work from anywhere.

## Adding new tests

1. **For a new validator:** add at least one behavior test (accepts valid, rejects invalid) and one mutation test per failure mode the validator is supposed to catch.
2. **For a new contract requirement:** add a mutation test that fails if the requirement is silently dropped (e.g., a new required field that gets removed).
3. **For v0.2 features:** add tests alongside the feature; do not break v0.1 tests.

## What's NOT tested (v0.1 scope)

- Filesystem operations (validators are pure functions; filesystem wrapper tested separately when added)
- Cross-session chain traversal (v0.2)
- Multi-writer status replay (v0.2)
- Revision append behavior (v0.2)
- Type-specific optional blocks (v0.2)
