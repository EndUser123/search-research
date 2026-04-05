# Architecture Decision: Self-Reflection Loop for Phase 1 Reasoning

**Date:** 2026-03-10
**Status:** ACCEPTED
**Decision:** Implement self-reflection loop (Generate → Critique → Improve) for Phase 1 reasoning without external LLMs

## Problem Statement

Current Sequential Mode implementation provides zero value:
- Just wraps prompts in stage prefixes
- No actual reasoning enhancement
- Doesn't make Claude smarter

## Decision

Implement self-reflection pattern with internal critique loop:

```python
class ReflectiveSequentialMode(BaseMode):
    async def process(self, prompt: str, ...) -> ProcessingResult:
        # 1. Generate initial 5-stage reasoning
        initial_chain = self._generate_sequential_thoughts(prompt)

        # 2. Self-critique (internal monologue)
        critique = self._self_critique(initial_chain)

        # 3. Refine based on critique
        refined_chain = self._refine_thoughts(initial_chain, critique)

        # 4. Quality gate (reflection tokens)
        if self._quality_check(refined_chain):
            return ProcessingResult(..., thought_chain=refined_chain)
        else:
            # Loop back (max 2 iterations)
            return await self._process_with_reflection(prompt, attempt=2)
```

## Rationale

### Research Evidence

1. **Self-Refine Pattern** (OpenAI Research)
   - Generate → Critique → Improve loop
   - 20-30% accuracy improvement on complex tasks
   - No external LLM needed

2. **LangGraph-Reflection** (Production Framework)
   - Main agent + critique agent
   - Same model, different modes
   - Proven in production code review

3. **Self-RAG** (University of Washington)
   - Reflection tokens: IsSup, IsRel, IsGr, IsUse
   - Self-correction without external feedback
   - 60% performance gains

### Why No External LLM Needed

**Mode switching** (key insight):
- Generation mode: "Write an answer"
- Analysis mode: "Review for issues"
- Improvement mode: "Fix these issues"

Same model, different prompts = Self-reflection loop

## Architecture

### Phase 1 (Current)
```
ReflectiveSequentialMode:
  ├─ Generate 5-stage thoughts
  ├─ Self-critique (internal monologue)
  ├─ Refine based on critique
  ├─ Quality gate (IsSup, IsRel, IsUse tokens)
  └─ Return if quality passes, else loop (max 2)
```

### Phase 2 (Future)
```
MultiAgentMode:
  ├─ Factual Agent
  ├─ Emotional Agent
  ├─ Critical Agent
  ├─ Optimistic Agent
  ├─ Creative Agent
  └─ Synthesis Agent
```

## Implementation Tasks

1. [ ] Rewrite SequentialMode with self-reflection
2. [ ] Add internal monologue prompts
3. [ ] Implement quality gate checks
4. [ ] Add iteration logic (max 2)
5. [ ] Measure quality improvement

## Alternatives Considered

| Option | Pros | Cons | Decision |
|--------|------|-------|----------|
| A: Current (string templating) | Simple | Zero value | REJECTED |
| B: External LLM multi-agent | Diverse perspectives | Requires API keys | DEFERRED (Phase 2) |
| C: Self-reflection loop | 20-60% improvement, no external deps | 2-3x slower | SELECTED |

## Risk Mitigation

**Risk**: Self-reflection may have blind spots
**Mitigation**: Phase 2 multi-agent mode adds external perspectives

**Risk**: Over-refinement (infinite critique loops)
**Mitigation**: Max 2 iterations, timeout on quality gate

## Success Criteria

- [ ] Sequential Mode shows measurable quality improvement
- [ ] No external LLM dependencies in Phase 1
- [ ] Quality gate prevents low-quality reasoning
- [ ] Performance acceptable (2-3x acceptable for quality gain)

## References

- Self-RAG Paper: Asai et al., University of Washington
- LangGraph-Reflection: https://github.com/langchain-ai/langgraph-reflection
- Self-Refine Pattern: Madaan et al., OpenAI Research
- Reflection Agents Blog: https://blog.langchain.com/reflection-agents/

## Confidence

85% - Strong research evidence, multiple production implementations

## Adversarial Self-Review

**Weakest assumption**: Claude can effectively critique own output without blind spots
**Consequence**: May miss biases that external perspectives would catch
**Mitigation**: Phase 2 multi-agent mode addresses this
