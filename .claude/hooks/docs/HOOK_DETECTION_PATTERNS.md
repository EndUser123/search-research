# Hook Detection Patterns & TAV Standard

This document formalizes the seven detection patterns used within the CSF hook ecosystem and defines the **Trigger-Audit-Verdict (TAV)** best practice for honesty and evidence enforcement.

---

## The Seven Detection Patterns

### 1. Deterministic Regex (Syntactic)
*   **Best for**: Hard security gating and fixed CLI patterns.
*   **Example**: "Block `eval()` or `exec()` in Bash commands."
*   **Pros**: Zero latency, 100% deterministic.
*   **Cons**: Brittle; easily bypassed by minor formatting changes.

### 2. Entity Extraction & Intersection
*   **Best for**: Turn-based scope verification.
*   **Example**: "You claimed 'config.yaml has field X' without performing a `Read` on `config.yaml` this turn."
*   **Pros**: Catches "Scope Creep" where the model talks about unobserved files.
*   **Cons**: Prone to false positives if the model uses "nicknames" for files.

### 3. State-Machine Gating (Workflow)
*   **Best for**: Enforcing multi-turn sequences (e.g., TDD).
*   **Example**: "Block editing code because the 'Red' (failing test) phase wasn't recorded in the session state."
*   **Pros**: Enforces logic that spans multiple user interactions.
*   **Cons**: Risks "stuck" states if session context is lost or corrupted.

### 4. Cognitive Self-Correction (Soft Blocking)
*   **Best for**: Behavioral nuance and clinical tone enforcement.
*   **Example**: "Inject a prompt: 'You asked a question without checking docs. Are you sure you shouldn't investigate first?'"
*   **Pros**: Educates the model without breaking the user flow.
*   **Cons**: Does not technically prevent a determined lazy model from proceeding.

### 5. AST / Signature Characterization (Structural)
*   **Best for**: Protecting infrastructure and library integrity.
*   **Example**: "Detect that a code edit removed a function parameter used by other modules."
*   **Pros**: Deep understanding of code impact; catches "silent" breakages.
*   **Cons**: High computation overhead; language-specific (.py, .ts only).

### 6. ML / Embedding-Based (Semantic)
*   **Best for**: Mapping prose to evidence when identities differ.
*   **Example**: "Map the user's mention of 'janitor script' to `SessionStart_janitor.py` in the evidence ledger."
*   **Pros**: Handles paraphrases and loose language better than exact matches.
*   **Cons**: Non-deterministic; harder to debug; requires pre-loaded models (CKS).

### 7. Syntactic-Empirical Hybrid (Trigger-Audit-Verdict)
*   **Best for**: Truth, history, success, and absence claims.
*   **Example**: "You said 'I ran tests earlier' but the ledger shows no test run this session."
*   **Pros**: Highest signal-to-noise; grounds linguistic "tells" in ground-truth reality.
*   **Cons**: Requires a robust, centralized Evidence Ledger.

---

## Best Practice: The TAV Standard

Use the **Trigger-Audit-Verdict (TAV)** pattern for any hook evaluating claims about **external reality** or **past actions**.

### 1. Trigger (Fast Path)
Use lightweight Regex to identify the *intent* to make a claim. If no claim is detected, exit immediately (< 2ms) to minimize latency.

### 2. Audit (Layered Mapping)
If triggered, verify the claim against the **Unified Evidence Ledger** using a layered approach:
1.  **Exact Match**: Check for exact filenames or command strings.
2.  **Heuristic Mapping**: Use proximity or known aliases (e.g., `gh` -> `which gh`).
3.  **ML/Embeddings**: For high-stakes ambiguous cases, use semantic similarity to map prose to ledger items.

### 3. Verdict (Enforcement Path)
*   **Confirmed**: Ledger supports claim → **Allow**.
*   **Silent**: Ledger has no relevant data → **Soft Block** (Self-Eval prompt).
*   **Contradicted**: Ledger proves claim is false → **Hard Block** (Exit 2).

---

## Summary of Use Cases

| Requirement Type | Recommended Pattern |
|------------------|---------------------|
| **Truth / Honesty** | **Hybrid (TAV)** |
| **Security / Safety** | Deterministic Regex |
| **Code Integrity** | AST / Signature |
| **Workflow / Phase** | State-Machine |
| **Tone / Habits** | Cognitive / Soft Block |

**Note**: Keep pure structural/workflow guards in their specialized patterns. Do not force AST or State-Machine logic into TAV unless they require evidence-based cross-verification.
