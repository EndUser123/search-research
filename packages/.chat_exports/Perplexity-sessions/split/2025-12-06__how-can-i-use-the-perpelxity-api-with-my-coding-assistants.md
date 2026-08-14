---
title: "how can I use the perpelxity api with my coding assistants?"
date: "2025-12-06"
mode: "COPILOT"
uuid: "b2862ca4-c347-4044-a157-991fd8b7d7d9"
entry_count: 3
---

## Human

how can I use the perpelxity api with my coding assistants?

## Assistant

To integrate the Perplexity API (including pplx-api and Sonar APIs) with coding assistants like Claude Code, use its OpenAI-compatible interface for seamless compatibility.[1][2]

## Setup Steps
Access the API via your Perplexity account settings: Navigate to Settings > "</> API" tab, add payment/credits, and generate an API key.[3]
Use the key as a bearer token in requests (e.g., `Authorization: Bearer ${PERPLEXITY_API_KEY}`) or initialize an OpenAI client with `base_url="https://api.perplexity.ai"` and your key.[2]
Available endpoints include `/chat/completions` for Sonar models (e.g., `sonar-pro`) and Search API for web-grounded retrieval.[4]

## Code Example (Python)
```python
from openai import OpenAI

client = OpenAI(api_key="YOUR_API_KEY", base_url="https://api.perplexity.ai")
response = client.chat.completions.create(
    model="sonar-pro",  # Or mistral-7b-instruct, etc.
    messages=[{"role": "user", "content": "Your query here"}]
)
print(response.choices[0].message.content)
```
This works directly in Claude Code or similar assistants by pasting the client setup and adapting prompts for API calls.[2]

## Developer Resources
Full docs, SDKs, and quickstarts are at the API Platform (console.perplexity.ai), supporting Python, TypeScript, and agentic workflows. Monitor usage and models (e.g., Sonar for cited answers) in the same settings tab.[5][3][1][4]

## Human

what are some good implementation ideas that people have done with perplexity api and sdks?

## Assistant

Based on the latest resources, here are some excellent implementation ideas people have done with Perplexity API and SDKs:

## Real-World Use Cases

### **1. Real-Time Customer Support**
Zoom integrated Perplexity Sonar into their AI assistant to provide instant, citation-backed answers without users leaving the platform. You can build similar chatbots that pull live web data to answer support tickets with current information.[1]

### **2. Content Generation & Marketing Intelligence**
- **Trend analysis**: Use Sonar to analyze competitor strategies, market trends, and customer behavior in real-time
- **Marketing campaigns**: Pull trending topics and craft data-driven campaigns from live sources
- **Report generation**: Automate tender reports, market analysis documents with formatted outputs[2]

### **3. Interactive Web Applications**
Build React/Node apps that integrate Sonar for:
- Real-time fact-checking dashboards
- Live research tools with citation tracking
- Knowledge management systems with sourced answers[3]

### **4. Prospect Research & Lead Enrichment**
Use the API to automatically gather and enrich prospect data with current online information for sales teams.[2]

### **5. Interesting Facts Generator**
Simple but practical: Fetch fascinating, sourced facts about topics using the API to power educational content or trivia apps.[4]

### **6. Document Analysis & RAG Systems**
- Feed documents to Sonar with system prompts for custom search behavior
- Configure to prioritize trusted sources (e.g., healthcare orgs using medical sources only)
- Build knowledge bases with citation tracking[1]

### **7. Video Content Intelligence Routing (UVIR)**
*(Relevant to your work!)* Route different video types through specialized prompts using Sonar's search capability to contextualize analysis with current web data on trends, creators, and content performance.[5]

***

## Implementation Patterns

**Python with AsyncPerplexity** (good for integrating with Claude Code):
```python
import asyncio
from perplexity import AsyncPerplexity

client = AsyncPerplexity(api_key="YOUR_KEY")

async def get_citations():
    response = await client.chat.completions.create(
        model="sonar-pro",
        messages=[{"role": "user", "content": "Latest AI developments"}]
    )
    return response
```

**React Integration** (custom hooks for web apps):
```javascript
const usePerplexity = () => {
    const [loading, setLoading] = useState(false);
    const client = new OpenAI({
        apiKey: process.env.REACT_APP_PERPLEXITY_API_KEY,
        baseURL: "https://api.perplexity.ai"
    });
    // Handle streaming, citations, etc.
};
```

**Node/Express Backend**:
```javascript
app.post("/api/generate", async (req, res) => {
    const response = await client.chat.completions.create({
        model: "sonar-pro",
        messages: [{ role: "user", content: req.body.prompt }]
    });
    res.json({ result: response.choices[0].message.content });
});
```

***

## Key Advantages for Your Use Case

✅ **Real-time web grounding** - Perfect for analyzing current video trends and creator data
✅ **Citations included** - Know where facts come from (great for anti-hallucination)
✅ **Cost-effective** - More affordable than Claude + browsing for search-heavy workloads
✅ **OpenAI-compatible interface** - Drop-in replacement if you're already using similar APIs
✅ **Async support** - Great for concurrent video analysis pipelines
✅ **Official cookbook** - Full examples at [docs.perplexity.ai/cookbook](https://docs.perplexity.ai/cookbook)[6]

For your UVIR system, combining Sonar's real-time search with Claude for video classification could create a powerful content intelligence pipeline that understands both current context and detailed visual analysis.

## Human

<q>7. Video Content Intelligence Routing (UVIR)
(Relevant to your work!) Route different video types through specialized prompts using Sonar's search capability to contextualize analysis with current web data on trends, creators, and content performance.</q> Can you show me an example of use for uvir?

## Assistant

Great question! Let me build a concrete UVIR example for you that combines video classification with Perplexity Sonar for context-aware routing.

## UVIR System: Practical Example

**Scenario:** You have a video pipeline that needs to intelligently route and analyze different content types, pulling real-time context about creators, trends, and performance.

### System Architecture

```
Video Input
    ↓
[Extract Metadata & Frames]
    ↓
[Classify Content Type] ← UVIR Router
    ├─ Educational/Tutorial
    ├─ Entertainment/Comedy
    ├─ News/Current Events
    ├─ Creator Interview
    └─ Science Explainer
    ↓
[Route to Specialized Prompt + Sonar Context]
    ↓
[Enrich with Real-time Web Data]
    ↓
[Generate Analysis + Citations]
```

### Code Example (Python)

```python
import asyncio
from openai import AsyncOpenAI
import json

class UVIRSystem:
    def __init__(self, perplexity_api_key):
        self.sonar = AsyncOpenAI(
            api_key=perplexity_api_key,
            base_url="https://api.perplexity.ai"
        )
    
    # Video type classifier (could be Claude, vision model, or ML model)
    async def classify_video(self, video_metadata, frames_sample):
        """Returns: {'type': 'education', 'confidence': 0.95, 'keywords': [...]}"""
        # Your existing classification logic
        return {
            'type': 'education',
            'topic': 'machine learning basics',
            'creator': 'AI Research Lab',
            'confidence': 0.92
        }
    
    # UVIR routing: Select specialized prompt + context enrichment
    def get_routing_config(self, classification):
        """Map content type to specialized prompt + Sonar queries"""
        
        configs = {
            'education': {
                'system_prompt': """You are an expert educational content analyst.
Analyze this video's teaching methodology, clarity, and educational value.
Identify the learning outcomes and compare against similar educational content.""",
                'sonar_query': f"Latest {classification['topic']} courses and tutorials 2025",
                'analysis_focus': ['methodology', 'clarity', 'engagement', 'accuracy']
            },
            'news': {
                'system_prompt': """You are a news content fact-checker and analyst.
Verify claims, identify bias, check against current events, and assess journalistic quality.""",
                'sonar_query': f"Current news about {classification['topic']} today",
                'analysis_focus': ['accuracy', 'bias', 'timeliness', 'sources']
            },
            'entertainment': {
                'system_prompt': """You are an entertainment content analyst.
Assess humor style, production quality, audience appeal, and viral potential.""",
                'sonar_query': f"Trending {classification['topic']} entertainment content",
                'analysis_focus': ['engagement', 'originality', 'production', 'audience_fit']
            },
            'creator_interview': {
                'system_prompt': """You are an influencer/creator analyst.
Evaluate the guest's influence, discuss topics, and compare against creator market trends.""",
                'sonar_query': f"Creator {classification.get('guest_name', 'interview')} 2025",
                'analysis_focus': ['influence', 'authenticity', 'audience', 'relevance']
            },
            'science': {
                'system_prompt': """You are a science communicator analyst.
Evaluate scientific accuracy, complexity level, and explain whether claims are supported.""",
                'sonar_query': f"Recent research {classification['topic']} 2025",
                'analysis_focus': ['accuracy', 'clarity', 'citations', 'complexity']
            }
        }
        
        return configs.get(classification['type'], configs['education'])
    
    async def enrich_with_sonar(self, query):
        """Get real-time context from Sonar with citations"""
        response = await self.sonar.chat.completions.create(
            model="sonar-pro",
            messages=[{
                "role": "user",
                "content": query
            }]
        )
        return {
            'context': response.choices[0].message.content,
            'citations': response.citations if hasattr(response, 'citations') else []
        }
    
    async def analyze_video(self, video_metadata, frames_sample, transcript):
        """Full UVIR pipeline"""
        
        # Step 1: Classify video
        classification = await self.classify_video(video_metadata, frames_sample)
        print(f"✓ Classified as: {classification['type']} (confidence: {classification['confidence']})")
        
        # Step 2: Get routing config
        config = self.get_routing_config(classification)
        print(f"✓ Routed to: {config['system_prompt'][:50]}...")
        
        # Step 3: Enrich with real-time Sonar data
        context = await self.enrich_with_sonar(config['sonar_query'])
        print(f"✓ Enriched with real-time data from {len(context.get('citations', []))} sources")
        
        # Step 4: Analyze with context-aware prompt
        analysis_prompt = f"""
Analyze this video content:

TRANSCRIPT SUMMARY:
{transcript[:500]}...

REAL-TIME CONTEXT:
{context['context'][:800]}...

ANALYSIS FOCUS AREAS: {', '.join(config['analysis_focus'])}

Provide detailed analysis with specific insights and recommendations.
"""
        
        # You could use Claude here for final analysis
        response = await self.sonar.chat.completions.create(
            model="sonar-pro",
            messages=[
                {"role": "system", "content": config['system_prompt']},
                {"role": "user", "content": analysis_prompt}
            ]
        )
        
        return {
            'classification': classification,
            'routing_type': classification['type'],
            'context_sources': context.get('citations', []),
            'analysis': response.choices[0].message.content,
            'focus_areas': config['analysis_focus']
        }


# Usage Example
async def main():
    uvir = UVIRSystem(api_key="YOUR_PERPLEXITY_KEY")
    
    # Simulate video input
    video_metadata = {
        'title': 'How Transformers Work: A Deep Dive',
        'channel': 'AI Research Lab',
        'duration': 1200,
        'views': 50000
    }
    
    frames_sample = ['frame1', 'frame2', 'frame3']  # In practice, actual frame data
    
    transcript = """
    Today we're going to understand transformer architecture. Transformers are neural networks...
    They use attention mechanisms to process sequential data... Unlike RNNs, they can process
    entire sequences in parallel... This makes them incredibly efficient for language models...
    """
    
    result = await uvir.analyze_video(video_metadata, frames_sample, transcript)
    
    print("\n" + "="*60)
    print(f"CLASSIFICATION: {result['classification']['type'].upper()}")
    print(f"CONFIDENCE: {result['classification']['confidence']}")
    print("\nANALYSIS:\n" + result['analysis'])
    print(f"\nSOURCES: {len(result['context_sources'])} citations included")

# Run it
asyncio.run(main())
```

### Real-World UVIR Use Cases

**1. Educational Content Routing**
- Video: "Python for Beginners"
- Sonar Query: "Best Python programming courses 2025"
- Analysis: Compare teaching methodology against trending educational approaches
- Output: Clarity score, learning outcomes, competitive positioning

**2. News Content Routing**
- Video: "Latest AI Regulations Explained"
- Sonar Query: "AI regulation updates December 2025"
- Analysis: Fact-check claims, identify bias, assess timeliness
- Output: Accuracy report, citation sources, bias analysis

**3. Creator Performance Routing**
- Video: "Interview with Hugging Face CEO"
- Sonar Query: "Hugging Face funding trends 2025"
- Analysis: Contextualize guest's relevance, compare guest influence metrics
- Output: Creator impact score, topic relevance, audience alignment

**4. Trending Science Routing**
- Video: "Breakthrough in Quantum Computing"
- Sonar Query: "Recent quantum computing breakthroughs 2025"
- Analysis: Verify against latest research, explain complexity
- Output: Accuracy score, citation sources, education level

### Key Benefits of UVIR + Sonar

✅ **Context-Aware**: Each content type gets specialized analysis  
✅ **Real-Time**: Sonar pulls current trends and creator data  
✅ **Cited**: All analysis includes sources (anti-hallucination)  
✅ **Scalable**: Route thousands of videos with different prompts  
✅ **Flexible**: Easy to add new content types or modify routing logic  

This approach would be perfect for your video intelligence system—you get specialized analysis routing plus real-time context about trends, creators, and content performance, all with proper citations!
