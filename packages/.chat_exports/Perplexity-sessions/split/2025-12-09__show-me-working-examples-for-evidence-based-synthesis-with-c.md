---
title: "show me working examples for Evidence-Based Synthesis with Citations RAGAS"
date: "2025-12-09"
mode: "COPILOT"
uuid: "de7b460c-c842-431b-99ad-43587b3ce20b"
entry_count: 1
---

## Human

show me working examples for Evidence-Based Synthesis with Citations RAGAS

## Assistant

Perfect! Now let me create one more visual reference document with practical patterns.

Now let me provide you with a comprehensive overview.

## Evidence-Based Synthesis with Citations RAGAS: Working Examples

Evidence-Based Synthesis with Citations using RAGAS is a framework for building RAG systems that produce factually grounded responses with proper source attribution. Here are the key working examples and implementations:[1][2][3][4][5][6]

### Core Concept: The Faithfulness Framework

**Faithfulness** is the foundation metric that measures whether claims in a response can be inferred from retrieved contexts. The process works in three steps:[7]

1. **Claim Extraction** - The LLM breaks down the response into individual, verifiable statements[3]
2. **Claim Verification** - Each claim is checked against the retrieved context to determine if it's supported[3]
3. **Score Calculation** - Faithfulness = (verified_claims) / (total_claims)[7]

**Example:**
- Question: "Where was Einstein born?"
- Context: "Albert Einstein (born 14 March 1879) was a German-born theoretical physicist"
- High Faithfulness Answer: "Einstein was born in Germany on 14th March 1879" (Score: 1.0)[7]
- Low Faithfulness Answer: "Einstein was born in Germany on 20th March 1879" (Score: 0.5)[7]

### Working Example 1: Basic Faithfulness Evaluation[8]

This example demonstrates the simplest form of evidence-based evaluation:

```python
from ragas.dataset_schema import SingleTurnSample
from ragas.metrics import Faithfulness
from langchain_openai import ChatOpenAI
from ragas.llms import LangchainLLMWrapper

llm = ChatOpenAI(model="gpt-3.5-turbo")
wrapped_llm = LangchainLLMWrapper(llm)

sample = SingleTurnSample(
    user_input="When was the first super bowl?",
    response="The first super bowl was held on Jan 15, 1967",
    retrieved_contexts=[
        "The First AFL–NFL World Championship Game was played on January 15, 1967."
    ]
)

scorer = Faithfulness(llm=wrapped_llm)
score = await scorer.single_turn_ascore(sample)
print(f"Faithfulness Score: {score}")  # Output: 1.0
```

### Working Example 2: Citation Synthesis with Claim Extraction

The RAGAS approach extracts claims and maps them directly to source material:[3]

```python
class CitationSynthesizer:
    def extract_claims(self, response: str, llm):
        """Extract individual verifiable claims from response"""
        prompt = f"""Given this answer, create one or more focused statements 
        from each sentence. Break down complex sentences into assertions.
        
        Answer: {response}
        
        Return as JSON list."""
        
        claims = llm.invoke(prompt)
        return claims
    
    def verify_claims_against_context(self, claims: list, contexts: list, llm):
        """Verify each claim against retrieved contexts"""
        verification_results = {}
        
        for claim in claims:
            prompt = f"""Determine if this statement is supported by the context.
            
            Statement: {claim}
            
            Context: {' '.join(contexts)}
            
            Respond: "Yes" / "No" / "Partial" """
            
            result = llm.invoke(prompt)
            verification_results[claim] = result
        
        return verification_results
```

### Working Example 3: RAG Pipeline Evaluation with RAGAS[9][8]

Complete end-to-end evaluation demonstrating the full RAGAS workflow:

```python
from ragas import evaluate
from datasets import Dataset
from ragas.metrics import Faithfulness, ResponseRelevancy, ContextPrecision

# Prepare dataset
eval_dataset = {
    "question": [
        "How to deposit a business cheque?",
        "When was Oppenheimer released?",
    ],
    "contexts": [
        ["To deposit a cheque issued to an associate, open a business account "
         "with the bank. You will need a state-issued 'dba' certificate from "
         "the county clerk's office and an Employer ID Number (EIN)."],
        ["Oppenheimer is a 2023 biographical thriller film written and directed "
         "by Christopher Nolan, starring Cillian Murphy."]
    ],
    "answer": [
        "To deposit a cheque[1], open a business account[1] with the bank "
        "and obtain a 'dba' certificate[1] and an EIN[1].",
        
        "Oppenheimer is a 2023 film[2] directed by Christopher Nolan[2], "
        "starring Cillian Murphy[2]."
    ],
    "ground_truths": [
        ["Open business account with required documents"],
        ["2023 film, directed by Nolan, stars Cillian Murphy"]
    ]
}

dataset = Dataset.from_dict(eval_dataset)

# Evaluate with RAGAS metrics
result = evaluate(
    dataset,
    metrics=[
        Faithfulness(),
        ResponseRelevancy(),
        ContextPrecision()
    ]
)

print(result.to_pandas())
```

### Working Example 4: Citation Map Data Structure

A practical way to maintain claim-to-source mappings:[6]

```python
class CitationMap:
    def __init__(self):
        self.claim_to_sources = {}
        self.source_to_claims = {}
        self.source_metadata = {}
    
    def add_source(self, source_id: str, title: str, url: str = None):
        """Register a source with metadata"""
        self.source_metadata[source_id] = {
            'id': source_id,
            'title': title,
            'url': url
        }
    
    def add_citation(self, claim: str, source_id: str, 
                    confidence: float = 1.0):
        """Map a claim to a source"""
        if claim not in self.claim_to_sources:
            self.claim_to_sources[claim] = []
        
        self.claim_to_sources[claim].append({
            'source_id': source_id,
            'confidence': confidence
        })
        
        if source_id not in self.source_to_claims:
            self.source_to_claims[source_id] = []
        
        self.source_to_claims[source_id].append(claim)
    
    def get_claims_for_source(self, source_id: str) -> list:
        """Retrieve all claims supported by a source"""
        return self.source_to_claims.get(source_id, [])
```

### Key RAGAS Metrics for Citations

| Metric | Purpose | Range | Use Case |
|--------|---------|-------|----------|
| **Faithfulness**[7] | Factual consistency of response vs. context | 0-1 | Prevent hallucinations, validate citations |
| **Answer Relevancy** | How well answer addresses the question | 0-1 | Ensure answer completeness |
| **Context Precision** | Ratio of relevant to total context sentences | 0-1 | Ensure focused, clean context |
| **Context Recall** | Coverage of necessary information | 0-1 | Ensure retrieval completeness |

### Citation Accuracy Evaluation[10]

A practical function to verify citation accuracy:

```python
def citation_accuracy(response: str, citations: list, contexts: list) -> float:
    """Verify that citations actually support the claims"""
    accurate_citations = 0
    total_citations = len(citations)
    
    if total_citations == 0:
        return 1.0
    
    for claim_start, claim_end, source_index in citations:
        claim = response[claim_start:claim_end]
        cited_context = contexts[source_index]
        
        # Calculate word overlap
        claim_words = set(claim.lower().split())
        context_words = set(cited_context.lower().split())
        overlap = len(claim_words & context_words) / len(claim_words)
        
        if overlap > 0.5:  # 50% threshold
            accurate_citations += 1
    
    return accurate_citations / total_citations
```

### Production Implementation: Scholar QA Approach[6]

The Ai2 Scholar QA system demonstrates production-grade evidence-based synthesis with the following workflow:

1. **Quote Extraction** - Extracts verbatim relevant quotes from retrieved passages
2. **Answer Outline & Clustering** - Organizes quotes into thematic sections
3. **Claim Generation** - Generates claims with inline citations
4. **Evaluation** - Uses ALCE (entailment-based) evaluation for citation precision and recall

This approach achieved **48.1% citation precision** and **52.1% citation recall** in evaluation, significantly outperforming comparable systems like OpenScholar (25.9% precision).[6]

### Installation & Setup

```bash
pip install ragas langchain openai datasets

export OPENAI_API_KEY="your-api-key"
```

### Best Practices

1. **Extract claims before mapping** - Break down complex statements into verifiable assertions
2. **Use confidence scores** - Track certainty in claim-source mappings
3. **Maintain source metadata** - Keep title, URL, and publication date with citations
4. **Evaluate iteratively** - Use metrics to identify and improve weak areas
5. **Provide excerpts** - Show exact supporting text for each claim
6. **Flag contradictions** - Mark claims that contradict retrieved context

The comprehensive guide document I've created (code_file:24) contains additional working examples, metric definitions, and practical patterns for implementing evidence-based synthesis in your RAG pipelines.
