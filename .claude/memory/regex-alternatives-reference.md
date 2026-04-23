# Regex Alternatives Reference Guide

**Date:** 2026-04-02
**Source:** NotebookLM research across 22 notebooks + analysis

---

## When Regex Is the Wrong Tool

Regex is brittle for complex text processing because:
- Backtracking causes exponential slowdown on adversarial input (ReDoS)
- No structural awareness — can't distinguish code from comments
- Fragile matching — `rm -rf` in a string matches same as on command line
- Maintenance burden — complex patterns become unreadable

---

## The Alternatives Tier List

### Tier 1: AST & Grammar-Based Parsing (<5ms)

**Use when:** You need to analyze code, shell commands, or structured formats with context awareness.

**Tools:**
- **Tree-sitter** — incremental parsing, used by GitHub, Neovim
- **ast-grep** — AST-based pattern matching for code analysis

**Why it's better:** Builds a hierarchical tree, not a flat string. Each node has type and position — you can distinguish `Executed` commands from `Comment` spans.

**Example from dcg (Destructive Command Guard):**
```
SpanKind Classification:
- Executed     → Command words, MUST check
- InlineCode   → Content inside backticks, MUST check
- Data         → Single-quoted strings, Can skip
- Comment      → Shell comments (#), Skip
- HeredocBody  → Escalated to deeper scanning
```

This eliminates false positives that plague regex. `echo "rm -rf /"` won't trigger a destructive command alert because `"rm -rf /"` is classified as `Data` (quoted string).

---

### Tier 2: Automata & Finite State Machines

**Use when:** You need multi-pattern matching at high throughput.

**Tools:**
- **Aho-Corasick** — matches all keywords in single O(n) pass
- **DFA (Deterministic Finite Automaton)** — compiled regex, no backtracking

**Why it's better:** No backtracking. Scans input once, reports all matches simultaneously. Linear time complexity.

**Example:** Instead of running 50 regex checks sequentially, Aho-Corasick builds an automaton that scans the input once and reports which patterns matched.

---

### Tier 3: SIMD-Accelerated Substring Search

**Use when:** You need fast "quick rejection" before heavier analysis.

**Tools:**
- **memchr crate** (Rust) — uses SSE2, AVX2, NEON vector instructions
- **hyperscan** — Intel's SIMD regex engine

**Why it's better:** Sub-microsecond filtering. Checks if *any* target keyword exists before your expensive pipeline runs. Hardware-level parallelism.

**Typical pipeline:**
1. SIMD quick-reject — does target keyword exist at all?
2. If yes, run Aho-Corasick for multi-pattern match
3. If yes, run structural analysis (AST/SpanKind)
4. If still ambiguous, escalate to LLM

---

### Tier 4: Domain-Specific Query Languages

**Use when:** Working with structured data (especially JSON).

| Language | Tool | Best For |
|----------|------|----------|
| **JSONPath** | jsonpath-rust, go-jsonpath | JSON extraction |
| **JMESPath** | jmespath-py | JSON with filtering |
| **CEL** | cel-go, cel-spec | Policy evaluation, expressions |
| **Rego** | OPA (Open Policy Agent) | Complex policy rules |

**Why it's better:** Operates on structure, not strings. No string escaping issues. Intentionally can't do what regex does — which is the point.

**Rule:** If you're using regex on JSON, you're doing it wrong. Use JSONPath.

---

### Tier 5: Vector & Semantic Matching

**Use when:** You need relevance, not exact matches. Fuzzy matching, concept search.

**Tools:**
- **Pinecone, Chroma, Qdrant, Weaviate** — vector databases
- **FAISS** — Facebook's similarity search

**Why it's better:** Maps queries to concepts. `echo "delete all records"` matches SQL `DROP TABLE` because semantically related — even though the strings are completely different.

**Trade-off:** Requires embedding model + vector store. Higher latency than exact matching. Best for search/ranking, not detection.

---

### Tier 6: LLM Intent Classification

**Use when:** Mechanical rules fail to capture nuance — obfuscation, intent, context-dependence.

**Example:** Shell obfuscation detection. `r\`m -rf /` (backtick escaping) or `$(whoami)` variable substitution — regex can't handle, but an LLM understands the intent.

**Pattern from Claude Code hooks:**
```
Prompt Hook → Send to Claude 3.5 Haiku → Returns {ok: boolean, reason: string}
```

**Why it's better:** Handles edge cases that would require infinite regex rules.

**Trade-off:** Latency (~100ms+), cost, token usage. Use as escalation after structural checks fail.

---

## Word Boundaries: Where They Fit

**Short answer:** Word boundaries (`\b`) are a positional hack that most alternatives replace with structural awareness.

| Approach | Word Boundary Equivalent |
|----------|------------------------|
| Regex `\b` | `(?<![a-zA-Z])(?=([a-zA-Z]+))(?![a-zA-Z])` — fragile |
| Aho-Corasick | Complete keyword match only (no substring) |
| AST/SpanKind | **Stronger than `\b`** — structural context knows if a token is `Executed` vs `Data` vs `Comment` |
| LLM | Understands whether `rm` is being *executed* vs *mentioned* |

**The upgrade path:**
- Replace `\brm\b` with AST matching: match `rm` where SpanKind == `Executed`
- This correctly handles `echo "rm"` (not destructive) vs `rm` (destructive) without any boundary logic

---

## Hybrid Pipeline Pattern

Best-in-class systems layer these approaches:

```
Input Text
    │
    ├── [Tier 3] SIMD Quick-Reject
    │       Does target keyword exist at all?
    │            │ No → Done (fast pass)
    │            │
    │            ▼ Yes
    │       [Tier 2] Aho-Corasick
    │       Which pack's keywords matched?
    │            │
    │            ▼ Yes
    │       [Tier 1] AST/SpanKind
    │       Is keyword in executable position?
    │            │ No → Done (false positive eliminated)
    │            │
    │            │ Yes (but ambiguous)
    │            ▼
    │       [Tier 6] LLM Intent Classification
    │       What's the actual intent?
    │
    └── Final Decision
```

This is how dcg (Destructive Command Guard) works — only ~5ms for shell command analysis, zero false positives on quoted strings.

---

## Quick Decision Guide

| Use case | Recommended approach |
|----------|---------------------|
| Detect specific strings in code | Tree-sitter + SpanKind |
| Multi-pattern keyword search | Aho-Corasick |
| Fast rejection filter | SIMD (memchr) |
| Parse JSON | JSONPath / JMESPath |
| Policy evaluation | CEL or Rego |
| Fuzzy semantic search | Vector embeddings |
| Handle obfuscation/edge cases | LLM (fast model, single turn) |
| Simple substring in trusted input | `in` operator or `memchr` |

---

## Key Principle

> **Use regex only when:** the pattern is truly regular (character classes, simple positions) and you control the input format completely.

> **Use alternatives when:** input is complex, untrusted, or requires context awareness.

---

## Sources

- Destructive Command Guard (dcg) architecture — d66afb5b notebook
- Claude Code hooks system — ceb52be1 notebook
- JSONPath / JMESPath / CEL comparisons — fbb47810, 7aeb565f notebooks
- Vector database landscape — b546fab1, bb96ed7d notebooks
