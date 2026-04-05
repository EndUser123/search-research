# Architectural Review & Design (ARCH)

When performing architectural analysis, you must follow these high-rigor patterns:

## 1. Adversarial Review
Before proposing a solution, act as an "Adversary" and find 3 ways your design could fail:
- Performance bottlenecks (N+1 queries, memory leaks)
- Security gaps (Unauthorized access, data leaks)
- Complexity bloat (Over-engineering, unnecessary abstractions)

## 2. Alternatives Analysis
Always present at least two distinct architectural paths:
- **Approach A (Primary):** The recommended path.
- **Approach B (Alternative):** A valid alternative with different trade-offs.
Explain why A was chosen over B.

## 3. Contract & Schema Audit
- **Return Schemas:** Ensure function outputs match existing API/Hook protocols.
- **Data Integrity:** Verify that new data structures don't conflict with existing database schemas.
- **Guard Integrity:** Ensure 'Enabled' flags and security gates are preserved.

## 4. Design-First Verification
- **Trace the Data:** Step through the logic mentally (AoT) from input to output.
- **Fail Fast:** If a design flaw is detected during tracing, HALT and report. Do not proceed to implementation.
