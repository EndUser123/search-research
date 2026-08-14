---
title: "z.ai python cookbook"
date: "2025-12-09"
mode: "COPILOT"
uuid: "c79f639c-95b4-4134-b518-5ba4e1c141ea"
entry_count: 7
---

## Human

z.ai python cookbook

## Assistant

The **Z.ai Python Cookbook** provides a collection of practical recipes for interacting with the Z.ai (formerly Zhipu AI) platform, which hosts the **GLM-4** family of models (GLM-4.6, GLM-4.5, and GLM-4V).

### 1. Installation & Setup
The official Python SDK is **`zai-sdk`**. It supports both synchronous and asynchronous usage.

```bash
pip install zai-sdk
```

### 2. Basic Chat Completion
This recipe demonstrates how to initialize the client and generate a simple response using the flagship `glm-4.6` model.[1][2]

```python
from zai import ZaiClient

# Initialize with your API key
client = ZaiClient(api_key="YOUR_API_KEY")

response = client.chat.completions.create(
    model="glm-4.6",  # Or "glm-4.5"
    messages=[
        {"role": "system", "content": "You are a helpful AI assistant."},
        {"role": "user", "content": "Explain quantum entanglement in one sentence."}
    ],
    temperature=0.7
)

print(response.choices[0].message.content)
```

### 3. Streaming Responses
For real-time applications, use the `stream=True` parameter to receive tokens as they are generated.[2]

```python
response = client.chat.completions.create(
    model="glm-4.6",
    messages=[
        {"role": "user", "content": "Write a Python script to parse a CSV file."}
    ],
    stream=True
)

print("Streamed Output:")
for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

### 4. Vision & Multimodal Analysis (GLM-4V)
Z.ai's vision models can analyze images and video frames. You pass image URLs or base64 data within the message content.[3]

```python
response = client.chat.completions.create(
    model="glm-4v",  # Vision-capable model
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "What is unusual about this image?"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://example.com/suspicious-frame.jpg"
                    }
                }
            ]
        }
    ]
)
print(response.choices[0].message.content)
```

### 5. Tool Calling (Function Calling)
GLM-4 models are optimized for agentic workflows and can autonomously decide to call external tools (like search or custom functions).[4][2]

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather for a city",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "City name"},
                    "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
                },
                "required": ["location"]
            }
        }
    }
]

response = client.chat.completions.create(
    model="glm-4.6",
    messages=[{"role": "user", "content": "What's the weather like in Tokyo?"}],
    tools=tools,
    tool_choice="auto"
)

# Check if the model wants to call a function
if response.choices[0].message.tool_calls:
    tool_call = response.choices[0].message.tool_calls[0]
    print(f"Function called: {tool_call.function.name}")
    print(f"Arguments: {tool_call.function.arguments}")
```

### 6. OpenAI Compatibility Layer
If you have existing code built for OpenAI's SDK, you can switch to Z.ai by simply changing the `base_url` and `api_key`.[5][6]

```python
from openai import OpenAI

client = OpenAI(
    api_key="YOUR_ZAI_API_KEY",
    base_url="https://open.bigmodel.cn/api/paas/v4/"
)

response = client.chat.completions.create(
    model="glm-4",
    messages=[{"role": "user", "content": "Hello from OpenAI client!"}]
)
print(response.choices[0].message.content)
```

### 7. Asynchronous Usage
For high-concurrency applications (like your video analysis pipelines), use the `AsyncZaiClient`.[2]

```python
import asyncio
from zai import AsyncZaiClient

async def main():
    client = AsyncZaiClient(api_key="YOUR_API_KEY")
    
    response = await client.chat.completions.create(
        model="glm-4.6",
        messages=[{"role": "user", "content": "Generate 3 variants of a YouTube title."}]
    )
    print(response.choices[0].message.content)

# asyncio.run(main())
```

## Human

Using Z.ai vision models in Python examples

## Assistant

This **Vision Cookbook** focuses on the multimodal capabilities of Z.ai, specifically using the **GLM-4V** and **GLM-4.5V** models. These models can process images, video frames, and visual data for tasks like captioning, analysis, and optical character recognition (OCR).

### 1. Single Image Analysis (URL vs. Base64)
The `glm-4.5v` model accepts images either as a remote URL or a Base64-encoded string.

**Option A: Using an Image URL**
```python
from zai import ZaiClient

client = ZaiClient(api_key="YOUR_API_KEY")

response = client.chat.completions.create(
    model="glm-4.5v",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Describe the architectural style of this building."},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://example.com/architecture.jpg"
                    }
                }
            ]
        }
    ]
)
print(response.choices[0].message.content)
```

**Option B: Using Local Images (Base64)**
For local files, you must encode them before sending.[1]

```python
import base64

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

base64_image = encode_image("local_diagram.png")

response = client.chat.completions.create(
    model="glm-4.5v",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Extract all the text labels from this diagram."},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64_image}"
                    }
                }
            ]
        }
    ]
)
print(response.choices[0].message.content)
```

### 2. Video Content Analysis (Frame Extraction)
Since Z.ai models like GLM-4.5V are optimized for video understanding, you can analyze video by extracting key frames. This script processes a video file and asks the model to summarize the event.[2][3]

```python
import cv2
import base64
from zai import ZaiClient

# Helper to encode specific frame
def encode_frame(frame):
    _, buffer = cv2.imencode(".jpg", frame)
    return base64.b64encode(buffer).decode("utf-8")

# Extract 1 frame every 2 seconds
video = cv2.VideoCapture("security_footage.mp4")
base64Frames = []
fps = video.get(cv2.CAP_PROP_FPS)
frame_interval = int(fps * 2) 

count = 0
while video.isOpened():
    success, frame = video.read()
    if not success:
        break
    if count % frame_interval == 0:
        base64Frames.append(encode_frame(frame))
    count += 1
video.release()

# Construct the message with multiple image frames
content_parts = [{"type": "text", "text": "Analyze these video frames. What suspicious activity is occurring?"}]
for b64_frame in base64Frames[:10]: # Limit frames to avoid context overflow
    content_parts.append({
        "type": "image_url",
        "image_url": {"url": f"data:image/jpeg;base64,{b64_frame}"}
    })

response = client.chat.completions.create(
    model="glm-4.5v",
    messages=[{"role": "user", "content": content_parts}]
)

print(response.choices[0].message.content)
```

### 3. Visual Agent with Tool Calling
GLM-4.5V can "see" an image and then decide to call a tool based on what it sees. This is useful for automated workflows (e.g., "If you see a receipt, save the total to the database").[4][5]

```python
import json

# Define a tool for the model to use
tools = [
    {
        "type": "function",
        "function": {
            "name": "log_maintenance_issue",
            "description": "Log a detected maintenance issue to the system",
            "parameters": {
                "type": "object",
                "properties": {
                    "severity": {"type": "string", "enum": ["low", "high", "critical"]},
                    "issue_type": {"type": "string", "description": "e.g., 'cracked_screen', 'rust', 'leak'"},
                    "description": {"type": "string", "description": "Visual description of the defect"}
                },
                "required": ["severity", "issue_type"]
            }
        }
    }
]

# Provide an image of a broken pipe
base64_image = encode_image("broken_pipe.jpg")

response = client.chat.completions.create(
    model="glm-4.5v",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Inspect this equipment. If there is damage, log a ticket."},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
            ]
        }
    ],
    tools=tools,
    tool_choice="auto"
)

# Process the tool call
tool_calls = response.choices[0].message.tool_calls
if tool_calls:
    for tool_call in tool_calls:
        args = json.loads(tool_call.function.arguments)
        print(f"logging issue: {args['issue_type']} (Severity: {args['severity']})")
```

### 4. GUI & Screen Parsing Agent
GLM-4.5V has specific capabilities for understanding GUI layouts. This recipe asks the model to identify clickable elements in a screenshot.[3][2]

```python
response = client.chat.completions.create(
    model="glm-4.5v",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Identify the bounding box coordinates [x1, y1, x2, y2] for the 'Submit' button in this UI screenshot."},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{screenshot_b64}"}}
            ]
        }
    ]
)
# GLM-4.5V is trained to provide precise grounding/coordinates
print(response.choices[0].message.content)
```

## Human

Example of sending multiple images in one request with Z.ai

## Assistant

### Multi-Image Analysis with Z.ai (GLM-4V)
You can send multiple images in a single request by adding multiple `image_url` objects to the `content` list. This is useful for comparison tasks, storyboarding, or sequential analysis.

**Note:** The model processes images in the order they appear in the list.

```python
from zai import ZaiClient
import base64

# 1. Initialize Client
client = ZaiClient(api_key="YOUR_API_KEY")

# 2. Helper to encode local images
def encode_image(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')

# Prepare images (one from URL, one local)
url_image = "https://example.com/chart_2023.png"
local_b64 = encode_image("chart_2024_local.png")

# 3. Construct Request with Multiple Images
response = client.chat.completions.create(
    model="glm-4.6",  # or glm-4.5v / glm-4v
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text", 
                    "text": "Compare these two charts. What is the key difference in the trend between 2023 and 2024?"
                },
                {
                    "type": "image_url", 
                    "image_url": {"url": url_image}
                },
                {
                    "type": "image_url", 
                    "image_url": {"url": f"data:image/png;base64,{local_b64}"}
                }
            ]
        }
    ]
)

print(response.choices[0].message.content)
```

### Key Constraints[1]
*   **Order Matters:** The model "sees" the images in the sequence you provide them. Refer to them as "the first image" or "the second image" in your prompt for clarity.
*   **Token Usage:** Each image consumes tokens (typically calculated by resolution). Sending many high-res images can quickly deplete context windows.
*   **Limit:** While the exact limit varies by model version, best practices suggest limiting requests to 2-4 images to ensure high-quality attention to detail unless you are doing video frame analysis.

## Human

any z.ai glm examples for deep thinking with web searching / research?

## Assistant

### Deep Thinking with Web Search (Z.ai / GLM-4)

The Z.ai platform provides two distinct ways to handle complex research: **Deep Thinking** (Chain-of-Thought) and **Web Search**. These can be combined or used independently.

Below are three examples for different research workflows.

#### 1. Built-in Web Search (Simplest)
This is the standard approach for "research" tasks. Z.ai has a native `web_search` tool that you can toggle. The model will autonomously search, read results, and synthesize an answer.[1][2]

```python
from zai import ZaiClient

client = ZaiClient(api_key="YOUR_API_KEY")

response = client.chat.completions.create(
    model="glm-4.6",
    messages=[
        {"role": "user", "content": "What are the latest breakthroughs in solid-state batteries as of late 2025?"}
    ],
    tools=[{
        "type": "web_search",
        "web_search": {
            "search_query": "solid state battery breakthroughs late 2025",
            "search_result": True  # Returns sources in the response
        }
    }]
)

print(response.choices[0].message.content)

# Inspect references if available
if hasattr(response, 'web_search'):
    for ref in response.web_search:
        print(f"- {ref['title']}: {ref['link']}")
```

#### 2. "Deep Thinking" Mode (No Search)
Use this when you want the model to reason through a complex problem using its internal knowledge *before* answering. This enables a "Chain of Thought" process.[3][4]

```python
response = client.chat.completions.create(
    model="glm-4.6",
    messages=[
        {"role": "user", "content": "Analyze the potential economic impact of AGI on the insurance industry."}
    ],
    # Enable Deep Thinking via the extra_body parameter or specific SDK field
    extra_body={
        "thinking": {
            "type": "enabled"
        }
    },
    max_tokens=4096
)

# The 'reasoning_content' often arrives in a separate field or delta
print("--- Reasoning Process ---")
# Note: In some SDK versions, reasoning might be part of the 'choices' object directly
# or streamed separately.
print(response.choices[0].message.reasoning_content) 

print("\n--- Final Answer ---")
print(response.choices[0].message.content)
```

#### 3. Agentic Workflow: Deep Thinking + Custom Search Tool
For the most control, define your own search tool and let the model "think" about when to use it. This mimics an agent that plans a research strategy.[5][3]

```python
import json

# Define your custom search tool (mock implementation)
tools = [
    {
        "type": "function",
        "function": {
            "name": "google_search",
            "description": "Search Google for current information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search keywords"}
                },
                "required": ["query"]
            }
        }
    }
]

# 1. Ask the model to research a topic
messages = [
    {"role": "system", "content": "You are a research scientist. Think deeply before searching."},
    {"role": "user", "content": "Investigate the validity of the 'LK-99' superconductor claims from 2023 vs 2025 updates."}
]

response = client.chat.completions.create(
    model="glm-4.6",
    messages=messages,
    tools=tools,
    extra_body={"thinking": {"type": "enabled"}} # Force it to plan first
)

message = response.choices[0].message

# 2. Print the thought process
if hasattr(message, 'reasoning_content'):
    print(f"Thought Process: {message.reasoning_content}")

# 3. Handle Tool Call
if message.tool_calls:
    tool_call = message.tool_calls[0]
    print(f"Decided to search for: {json.loads(tool_call.function.arguments)['query']}")
```

### Key Considerations
*   **Latency:** Enabling `thinking` significantly increases response time because the model generates internal tokens before producing the final output.[3]
*   **Streaming:** For the best user experience with Deep Thinking, use `stream=True` so you can display the "Thinking..." state to the user while the model reasons.[4]
*   **Model Support:** Ensure you are using `glm-4.6` or `glm-4.1v-thinking` (or newer) as older models may not support the explicit `thinking` parameter.[6][7]

## Human

Best practices for prompt design with Deep Thinking and web search

## Assistant

### Best Practices: Prompting for "Deep Thinking" & Research
When using Z.ai's **GLM-4.6** or **GLM-4.1V-Thinking**, you are managing two distinct cognitive processes:
1.  **Deep Thinking (Rumination):** Internal chain-of-thought (CoT) for planning, logic, and self-correction.
2.  **Web Search (Research):** External information retrieval for factual accuracy.

The most effective prompts explicitly coordinate these two. Instead of treating them as automatic, you should act as a "conductor" telling the model *when* to look inward (think) and *when* to look outward (search).

#### 1. The "Think-Then-Act" Protocol
For complex research, models often rush to search without a plan. You can prevent this by enforcing a strict order of operations in your system prompt.

**Why it works:** It forces the model to decompose the user's query into sub-questions *before* wasting tokens on irrelevant searches.

```python
system_prompt = """
You are an advanced research assistant with Deep Thinking capabilities.
You must follow this strictly sequential process for every query:

1. [THOUGHT] Internal Analysis:
   - Break down the user's request into core components.
   - Identify what you ALREADY know vs. what needs external verification.
   - Formulate 3-5 precise search queries targeting the missing information.

2. [ACTION] Web Search:
   - Execute the planned search queries using the 'web_search' tool.
   - Do not search for generic terms; be specific.

3. [SYNTHESIS] Answer Formulation:
   - Synthesize the search results with your internal knowledge.
   - Cite sources using [web:x] format.
"""
```

#### 2. Explicit Constraints for "Rumination"
When `thinking` is enabled via the API, the model generates a hidden chain of thought. However, you can guide the *quality* of this thought process by defining "Thinking Constraints" in your prompt.

*   **Bad Prompt:** "Research quantum computing trends."
*   **Good Prompt:** "Research quantum computing trends. **Thinking Constraint:** Before searching, list the top 3 separate hardware approaches (superconducting, trapped ion, photonic) to ensure you search for updates on *each* specific track rather than generic news."

#### 3. The "Iterative Refinement" Loop
GLM-4 models excel at agentic workflows where they critique their own search results. You can script this behavior by asking the model to evaluate the "sufficiency" of its findings.

**Prompt Pattern:**
> "Conduct a search on [Topic]. After receiving results, enter a 'Reflection Phase'. Ask yourself: 'Do these results fully answer the user's specific question about X?' If no, refine your search query and search again. Only provide the final answer when you have sufficient evidence."

#### 4. Handling "Thinking" vs. "Content"
When using the API, remember that `reasoning_content` (the thinking trace) and `content` (the final answer) are separate.

*   **For Debugging/Transparency:** Print the `reasoning_content` to see *why* the model chose a specific search keyword.
*   **For User Experience:** Only show the `content`.
*   **Prompt Tip:** If the model gets stuck in a "thinking loop" (over-analyzing), add a system instruction: *"Prioritize tangible search actions over prolonged theoretical planning."*

#### 5. Recommended Configuration (Python SDK)
Combine the prompt engineering with the correct API parameters for the best result.

```python
# Best configuration for deep research
response = client.chat.completions.create(
    model="glm-4.6",
    messages=[
        {"role": "system", "content": "You are a critical thinker. Verify every claim with a search result."},
        {"role": "user", "content": "Compare the battery density of the 2025 Tesla model vs BYD Blade."}
    ],
    tools=[{"type": "web_search", "web_search": {"search_result": True}}],
    extra_body={
        "thinking": {
            "type": "enabled",  # Enable the internal reasoning engine
            "max_tokens": 2048  # Give it space to plan
        }
    }
)
```

### Summary Checklist for Prompts
| Feature | Best Practice |
| :--- | :--- |
| **Context** | explicit reasoning steps (Plan → Search → Verify). |
| **Tool Use** | Forbid "blind searching." Require a specific query plan first. |
| **Citations** | Explicitly request inline citations (e.g., "Cite as [1]"). |
| **Fallback** | Tell the model what to do if search fails (e.g., "State clearly if no data is found"). |

## Human

How to structure prompts for multi-step reasoning with Deep Thinking

## Assistant

### Structuring Prompts for Deep Thinking (GLM-4 & GLM-4.1V-Thinking)

When using Z.ai's **Deep Thinking** models (like `glm-4.6` with thinking enabled or `glm-4.1v-thinking`), the model naturally generates a hidden "Chain of Thought" (CoT) before producing an answer.

To maximize the effectiveness of this, you should not just ask a question; you should **structure the reasoning process** using specific constraints.

#### 1. The "Reasoning Constraint" Pattern
Instead of a generic system prompt, use a structure that defines *how* the model should think, not just *what* it should do. This prevents the model from rushing to a conclusion.

**Template:**
```python
messages = [
    {
        "role": "system", 
        "content": """
You are a reasoned problem solver.
RULES FOR THINKING:
1. Deconstruct: Break the user's query into independent variables.
2. Plan: List the logical steps required to solve it BEFORE solving.
3. Self-Correct: If a step relies on an assumption, verify it or state the uncertainty.
4. Output: Provide a clear final answer only after the reasoning phase.
"""
    },
    {
        "role": "user", 
        "content": "Calculate the trajectory of a rocket given [complex variables]..."
    }
]
```

#### 2. Specialized Prompt Structures

##### A. The "Tree of Thoughts" (ToT) Structure
For highly complex scenarios (e.g., strategic planning), force the model to explore multiple possibilities.

**Prompt Example:**
> "I need to increase server reliability by 20%.
> **Thinking Requirement:**
> 1. Generate 3 distinct strategies (e.g., Hardware redundancy, Software failover, Load balancing).
> 2. For EACH strategy, simulate a failure scenario and predict the outcome.
> 3. Compare the trade-offs (Cost vs. Reliability).
> 4. Select the best strategy and justify why."

##### B. The "Validation Loop" (For Math/Coding)
GLM-4.1V-Thinking supports specific formatting tags like `<think>` and `<answer>`. You can enforce strict validation.[1][2]

**Prompt Example:**
> "Write a Python script to sort a list of dictionaries by a specific key.
> **Constraint:** Before writing the code, mentally trace the execution with an example list `[{'id': 2}, {'id': 1}]` to ensure your logic handles edge cases like missing keys.
> **Format:** Output your logic in the reasoning block and the code in the final answer."

#### 3. Deep Thinking + Visual Reasoning (GLM-4.1V-Thinking)
When using the multimodal reasoning model, you must guide it to "look" before it "thinks."

```python
response = client.chat.completions.create(
    model="glm-4.1v-thinking",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Analyze this flowchart and find the bottleneck."},
                {"type": "image_url", "image_url": {"url": "..."}}
            ]
        }
    ],
    # Specific parameter to enable/configure thinking
    extra_body={
        "thinking": {
            "type": "enabled",
            "budget_tokens": 4096  # Reserve capacity for long reasoning
        }
    }
)
```
**Prompt Tip:** "Trace the flow from Start to End. Identify any node with >2 incoming arrows but only 1 outgoing arrow. Explain why this specific node causes a delay."

#### 4. Handling the Output
With Deep Thinking enabled, the response object structure changes slightly depending on the SDK version.

*   **Standard Content:** `response.choices[0].message.content` (The final answer).
*   **Reasoning Trace:** `response.choices[0].message.reasoning_content` (The chain of thought).

**Best Practice:** Always log the `reasoning_content` in your backend for debugging prompt effectiveness, but only show the `content` to the end user unless they request "Show Work".

```python
# Example of parsing
message = response.choices[0].message
if hasattr(message, 'reasoning_content') and message.reasoning_content:
    print(f"[Internal Monologue]:\n{message.reasoning_content[:200]}...\n")
print(f"[Final Answer]:\n{message.content}")
```

## Human

Examples of concise prompt templates for Deep Thinking multi-step tasks

## Assistant

Here are concise, reusable prompt templates designed to force structure on Z.ai's Deep Thinking models (GLM-4.6 / GLM-4.1V-Thinking) without wasting tokens on fluff.

These are formatted as Python strings for direct insertion into your `messages` array.

### 1. The "Architect's Blueprint" (For Coding/Engineering)
**Use Case:** Preventing "spaghetti code" by forcing a design phase before implementation.

```python
PROMPT_ARCHITECT = """
TASK: {user_task}

Thinking Process:
1. [REQUIREMENTS] List explicit and implicit constraints.
2. [EDGE CASES] Identify 3 potential failure points (e.g., null inputs, scale).
3. [DESIGN] Outline the function signature and data structures.
4. [IMPLEMENT] Write the final code based on the above.

Output format: Provide the reasoning first, then the code block.
"""
```

### 2. The "OODA Loop" (For Strategic Analysis)
**Use Case:** Situational analysis, business strategy, or game theory.
*Based on: Observe, Orient, Decide, Act.*

```python
PROMPT_OODA = """
Scenario: {scenario_description}

Execute OODA Loop:
- OBSERVE: List the raw facts visible in the data/prompt.
- ORIENT: Analyze biases, missing data, and relationships.
- DECIDE: Propose 3 possible courses of action.
- ACT: Select the single best action and justify it.
"""
```

### 3. The "Visual Investigator" (For GLM-4V Image Analysis)
**Use Case:** Forensic analysis of an image, detailed inspection.
*Note: Prevents the model from hallucinating details by forcing an inventory step.*

```python
PROMPT_VISION_INVESTIGATOR = """
Analyze the attached image.

Step 1: [INVENTORY] List every distinct object and text element visible.
Step 2: [RELATIONSHIPS] Describe how these objects interact (spatial or functional).
Step 3: [DEDUCTION] Based ONLY on Step 1 & 2, answer: {user_question}

Constraint: Do not assume context not visible in the frame.
"""
```

### 4. The "Devil's Advocate" (For Critical Review)
**Use Case:** Reviewing content, searching for flaws, or refining an argument.

```python
PROMPT_CRITIC = """
Subject: {topic_or_content}

Perform a Critical Review:
1. ARGUMENT: Construct the strongest possible argument FOR the subject.
2. COUNTER: Construct the strongest possible argument AGAINST it.
3. SYNTHESIS: Resolve the conflict and provide a balanced conclusion.
"""
```

### 5. The "Fact-Check Protocol" (For RAG/Search)
**Use Case:** Answering questions where accuracy is paramount, minimizing hallucinations.

```python
PROMPT_FACT_CHECK = """
Question: {user_query}

Verification Protocol:
1. CLAIM EXTRACTION: Identify key claims in the query.
2. EVIDENCE SEARCH: (Internal) What specific facts verify these claims?
3. CONFIDENCE CHECK: If exact data is missing, state "Unknown".
4. ANSWER: Provide the answer with inline citations [Source: X].
"""
```

### Implementation Example
Here is how to drop one of these templates into your Z.ai SDK call:

```python
from zai import ZaiClient

client = ZaiClient(api_key="YOUR_KEY")

# User input
user_req = "Write a Python script to scrape a dynamic website using Selenium."

response = client.chat.completions.create(
    model="glm-4.6",
    messages=[
        {
            "role": "user",
            # Injecting the template dynamically
            "content": PROMPT_ARCHITECT.format(user_task=user_req)
        }
    ],
    extra_body={"thinking": {"type": "enabled"}}
)

print(response.choices[0].message.content)
```
