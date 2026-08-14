---
title: "https://www.youtube.com/watch?v=8JWhwhxWtJw

Find other videos like this."
date: "2026-07-30"
mode: "COPILOT"
uuid: "11047b61-943f-4d01-b9b2-2e834bd93c02"
entry_count: 3
---

## Human

[https://www.youtube.com/watch?v=8JWhwhxWtJw](https://www.youtube.com/watch?v=8JWhwhxWtJw)

Find other videos like this.

## Assistant

Other videos “like this” fall into a few clusters: more OKF / second‑brain content from Cole, general OKF explainer videos, and adjacent “AI second brain / YouTube → knowledge base” tutorials from others.[1][2][3][4][5]

Below are concrete suggestions with why they’re similar and how they differ, so you can choose what to watch next.

## More from Cole on OKF & second brains

These are the closest in spirit: same creator, same stack (Claude Code, OKF, AI agents), and focused on turning messy content into structured knowledge.[2][6][1]

- **“This New Google Format Gives Your AI Agent a Second Brain” – Cole Medin**  
  Focuses specifically on what OKF is, why Google created it, and how it formalizes the LLM‑wiki pattern into a shareable, agent‑readable format. This is effectively the conceptual precursor to the video you linked.[4][1]

- **“Google’s OKF (Open Knowledge Format) Just Added Trust …” – Cole Medin**  
  Dives deeper into OKF’s design, metadata, and trust / provenance angle, and how agents can rely on curated knowledge bundles. It complements the “turn a channel into a KB” video by focusing more on spec details and governance.[3][4]

- **“Full Guide – Build Your Own AI Second Brain with Claude Code” – Cole Medin**  
  Broader end‑to‑end second‑brain workflow (file systems, agents, Claude Code skills), with OKF or LLM‑wiki ideas as one piece of the system. This is worth watching if you’re thinking about integrating multiple OKF bundles into a larger personal knowledge architecture.[2]

You’ll find all of these on Cole’s channel page alongside the video you linked.[6]

## Other OKF / LLM‑wiki tutorials

If you care more about OKF and shared knowledge bundles than specifically about YouTube transcripts, these are close matches conceptually.[5][4]

- **Google Cloud – “How the Open Knowledge Format can improve data sharing” (blog, sometimes mirrored in talks)**  
  Explains OKF v0.1 as a directory of markdown files with YAML front matter, concepts as files, and graph‑style linking via markdown links. This is the primary, authoritative description of the format that Cole is building on.[4]

- **“This New Google Format Gives Your AI Agent a Second Brain” (non‑Cole channels, e.g., Marie Haynes et al.)**  
  Several creators have made OKF intros that show how to use bundles with agents and RAG‑style systems, often demoing navigation via index.md and concept/entity links. These overlap heavily with the ideas in Cole’s video but show different stacks and use‑cases (e.g., enterprise documentation, analytics).[1][5]

- **“How to Build an OKF Knowledge Bundle: Share Your AI …” (MindStudio / similar)**  
  Walks through constructing OKF bundles and importing them into agent frameworks as shareable second‑brain modules. It mirrors the “bundle as GitHub repo + index + concept/entity files” pattern that Cole uses.[7][5][4]

## YouTube channel → knowledge base workflows

These videos are not all explicitly branded as OKF, but they address the same core pattern: scrape YouTube transcripts, structure them, and use LLMs to canonicalize into a KB you can query.[8][9][10]

- **“Unlock YouTube’s Hidden AI Brain” (Stork.ai blog + associated demos)**  
  Builds almost the same pipeline: extract transcripts for a channel, turn them into a text corpus, then use LLMs to identify recurring concepts and consolidate them into a graph-like knowledge base. It references Cole’s work explicitly and shows alternative tooling for similar goals.[9]

- **“How to Get Your Data Ready for AI Agents (Docs, PDFs …)” – Cole Medin**  
  Broader than YouTube, but covers knowledge‑extraction pipelines and optimization strategies for agent‑friendly corpora, including turning arbitrary files into structured LLM knowledge. The same techniques apply to transcripts.[10]

- On “AI second brain” / “YouTube to Obsidian” / “YouTube to knowledge base” search terms, you’ll find multiple creator tutorials walking through:  
  - Using tools like `yt-dlp` or transcript APIs to bulk‑download transcripts.  
  - Converting them to markdown and importing into Obsidian.  
  - Layering RAG or agentic querying on top.[8][9]

## How to systematically find more like this

Given your profile, you probably want to filter to content that’s (a) OKF/LLM‑wiki aware, and (b) focused on agentic use, not just “note‑taking.” Here’s a quick pattern you can use on YouTube and the web:[9][1][4]

- Use these search phrases:  
  - `OKF second brain`  
  - `Open Knowledge Format knowledge bundle`  
  - `LLM wiki YouTube channel`  
  - `YouTube transcripts AI knowledge base`  
  - `agentic knowledge base Obsidian OKF`  

- Prioritize videos or repos that mention:  
  - OKF or “LLM wiki” explicitly.[4]
  - Concepts/entities markdown directories, `index.md`, YAML front matter, and link graphs.  
  - Canonicalization of recurring concepts across many videos (not just “dump transcripts”).[9]

- Cross‑check descriptions for:  
  - GitHub repos with OKF bundles or skills (like Cole’s `cole-medin-knowledge-base`).[7][9]
  - Explicit second‑brain / agent integration (Claude Code, MCP, etc.).[5][2]

If you tell me which aspect you liked most—OKF itself, the canonicalization pipeline, or the Claude Code skills—I can narrow this down to a small, high‑leverage watch list and complementary repos.  

## Human

Please do:
Compare OKF-based knowledge building to RAG/VectorDB methods — latency, setup complexity, and agent-query accuracy for personal brains
​
How to build an automated RAG pipeline for YouTube channels

Comparing OKF to standard Markdown for knowledge management

Best practices for structuring AI-readable documentation

## Assistant

For a **personal brain**, OKF and RAG solve different problems, and the best system is usually hybrid: use OKF/structured markdown as the canonical, inspectable knowledge layer, and add vector retrieval only when corpus size or query style makes direct file traversal too slow or incomplete. If you have to choose one first, OKF is usually the better starting point for accuracy, maintainability, and agent transparency; RAG becomes valuable once recall and scale start to dominate.[1][2][3][4]

## OKF vs RAG

OKF represents knowledge as markdown files with YAML frontmatter, stable paths, cross-links, optional index/log files, and explicit provenance / trust / freshness metadata in the spec’s newer versions. Standard RAG pipelines instead ingest raw documents, chunk them, embed them, store vectors plus metadata, and retrieve semantically similar chunks at query time.[5][2][3][1]

| Dimension | OKF-based knowledge | RAG / VectorDB |
|---|---|---|
| Core unit | One concept per markdown file with frontmatter and links.[2][3] | Chunks of text plus embeddings and metadata.[1] |
| Latency | Often lower for small/medium personal corpora because an agent can navigate `index.md`, filenames, links, and grep-like search without embedding lookup overhead.[2][3] | Often better recall on large unstructured corpora, but every query pays retrieval + reranking + prompt assembly cost.[1][5] |
| Setup complexity | Lower initial complexity: files, naming, frontmatter, directory structure, and git are enough to start.[2][3] | Higher: ingestion, cleaning, chunking, embeddings, vector store, metadata filters, refresh jobs, and evaluation loops.[1] |
| Accuracy for personal brains | Higher when the corpus is curated and canonicalized because concepts are already merged, named, and linked before query time.[2][3][6] | Higher on messy or massive raw corpora, but more sensitive to chunk boundaries, duplicate passages, and weak metadata.[1][5] |
| Explainability | Strong: the agent can cite files, sections, links, and frontmatter provenance directly.[2] | Weaker by default: you usually know which chunks were retrieved, but not whether chunking distorted the concept.[1] |
| Freshness / trust | First-class in OKF v0.2 via `sources`, `generated`, `verified`, `status`, and `stale_after` fields.[2] | Possible, but you must design metadata schemas and enforcement yourself.[1] |

**FACT:** OKF was designed to be human-readable, parseable by agents, diffable in version control, portable across tools, and minimally opinionated, with markdown plus YAML frontmatter as the interoperability surface. **CONSENSUS:** RAG is stronger when the source corpus is large, uncurated, and primarily unstructured, because semantic retrieval can find relevant passages humans would not pre-organize well.[2][3][5][1]

### Practical tradeoffs

For a personal knowledge base, query accuracy usually depends less on raw retrieval math and more on whether your notes have already been **canonicalized** into stable concepts like “PIV loop,” “OKF bundle design,” or “YouTube transcript ingestion,” instead of existing as dozens of overlapping notes. That is why the Cole Medin pattern feels strong: it does extraction first, then concept consolidation, then graph linkage, which removes a large class of retrieval ambiguity before the agent ever answers.[6][2]

A pure vector DB often stores many near-duplicate transcript chunks, so the model must infer at answer time that “plan build verify” and “PIV loop” are the same idea. OKF-style concept files move that disambiguation to build time, which usually improves answer consistency for recurring themes in personal brains.[6][1][2]

## YouTube RAG pipeline

For YouTube channels, the automated RAG pipeline should separate **ingestion**, **canonicalization**, and **retrieval**, rather than jumping straight from transcript to embeddings. That separation is the main architectural difference between a toy demo and a durable system.[1][2]

A strong pipeline looks like this:

1. **Collect channel inventory** — resolve channel URL / handle, enumerate videos, store video ID, title, publish date, description, duration, and playlist memberships as metadata.[2]
2. **Extract transcripts** — pull captions or transcript API output, keep timestamps, and normalize into markdown or JSON documents per video.[2]
3. **Clean and segment** — remove sponsor blocks if desired, fix transcript artifacts, split into semantic sections instead of only fixed token windows.[1][2]
4. **Canonicalize recurring concepts** — use an LLM to cluster repeated ideas, tools, workflows, and entities across videos into stable concept pages.[2]
5. **Store dual outputs** — keep raw transcripts in one store and curated concept docs in another; do not throw away the raw layer.[2]
6. **Index for retrieval** — embed both transcript segments and concept pages, but weight concept pages higher for synthesis questions.[1]
7. **Answer with routing** — factual “what did this creator say in video X?” queries go to transcript retrieval; conceptual “what is their workflow for Y?” queries go to canonicalized concepts first.[2]
8. **Refresh incrementally** — poll for new uploads, transcribe only deltas, re-run concept clustering only for affected topics, then rebuild impacted embeddings.[1]

### Minimal architecture

For a production-minded personal system, I would use:

- **Raw store:** markdown/JSON transcript files in git or object storage.
- **Canonical store:** OKF-like concept/entity docs in markdown.
- **Vector index:** embeddings for both transcript chunks and concept docs.
- **Metadata DB:** SQLite or Postgres for channel/video/topic mappings.
- **Retriever router:** choose between concept-first, transcript-first, or hybrid retrieval depending on query intent.
- **Evaluator:** a regression set of 30–100 real questions from your own usage patterns.[1][2]

**SPECULATION, medium confidence:** For your workflow, a hybrid store will outperform pure RAG because you care about traceability, reusable abstractions, and agent behavior more than bare semantic search convenience. That matches your emphasis on validation, inspectability, and minimal unnecessary complexity.

## OKF vs plain Markdown

OKF is not a replacement for markdown; it is a stricter convention for organizing markdown into interoperable knowledge bundles. Plain markdown is flexible and lightweight, but it does not by itself tell an agent what a file represents, how current it is, whether it was verified, or how it relates to other files.[3][2]

| Aspect | OKF | Standard Markdown |
|---|---|---|
| Structure | Requires a concept document with YAML frontmatter; `type` is required.[2] | No required schema; can be anything from a scratch note to a full article. |
| Navigation | Supports `index.md` for progressive disclosure and normal markdown links for graph traversal.[2][3] | Navigation is whatever folder structure and links you manually create. |
| Trust metadata | Built-in fields for provenance, verification, status, and staleness in v0.2.[2] | Must be invented ad hoc or omitted. |
| Interoperability | Designed so different producers and consumers can exchange bundles without translation.[3] | Human-friendly, but not reliably machine-interpretable across teams or tools. |
| Best use | Canonical knowledge assets, shared agent-readable corpora, curated personal brains.[2][3] | Draft notes, essays, meeting notes, rough research capture. |

The biggest practical difference is that OKF pushes you toward **one concept per file** with explicit metadata and stable identities, while standard markdown often becomes document-centric and drifts into long mixed-topic notes. For AI use, mixed-topic notes are usually worse because chunkers and retrievers must reconstruct conceptual boundaries after the fact.[4][6][1][2]

## AI-readable docs

Best practices for AI-readable documentation are converging around the same themes across OKF, llms.txt-style guidance, and markdown-first docs systems: stable plain-text access, explicit structure, low ambiguity, and rich metadata.[7][4][2]

Use these rules:

- **Prefer markdown or plain-text canonical exports** over JS-heavy rendered docs, because agents parse text more reliably than interactive UI layers.[7][4]
- **Use clear heading hierarchy** so each section maps to a single intent or task.[4][2]
- **Keep sections self-contained** and avoid burying one procedure across multiple tabs or accordions.[4]
- **Separate code from prose** with fenced code blocks and language labels.[4][2]
- **Use YAML frontmatter or equivalent metadata** for title, description, tags, version, ownership, freshness, and trust signals.[4][2]
- **Maintain terminology consistency**; do not rename the same concept across pages unless you add aliases explicitly.[4]
- **Minimize vague pronouns** and refer to the exact noun again when precision matters.[4]
- **Provide stable paths and explicit links** so an agent can traverse related concepts deterministically.[2]
- **Expose a machine-oriented entry point** like `llms.txt`, `skill.md`, bundle `index.md`, or a corpus manifest.[7][2]
- **Preserve provenance** by linking claims to sources or including source metadata in frontmatter.[2]

### Recommended personal-brain pattern

For your use case, I’d structure it in three layers:

- **Layer 1: Raw captures** — transcripts, PDFs, exported chats, bookmarks, meeting notes.
- **Layer 2: Canonical concepts** — OKF-like markdown files for recurring entities, workflows, tools, and principles.
- **Layer 3: Retrieval services** — vector index, lexical search, and graph traversal over layers 1 and 2.[1][2]

That gives you the low-friction ingestion of RAG, the inspectability of markdown, and the higher conceptual accuracy of OKF-style canonicalization.[3][1][2]

## Recommendation

If the goal is “personal brain that answers well,” start with **markdown-first canonicalization**, not embeddings-first retrieval. Then add RAG as an acceleration and recall layer over the canonical corpus plus raw sources, instead of making the vector DB your source of truth.[3][1][2]

**Concrete next step:** design one pilot around a single YouTube channel with this layout: `raw/` transcripts, `concepts/`, `entities/`, bundle `index.md`, and a small vector index over both raw segments and canonical pages. Then evaluate 20 real questions across latency, citation quality, and conceptual consistency before scaling to more channels.[1][2]

Confidence: **high** on the OKF / markdown / AI-readable-docs comparison, because the OKF spec and Google’s design goals are explicit. Confidence: **medium** on latency and agent-query accuracy comparisons, because those depend heavily on corpus size, retriever quality, and whether you canonicalize concepts before retrieval.[5][3][1][2]

## Human

please explain:
Recommended LLM agent patterns for markdown-based graphs
Best practices for YouTube transcript ingestion and chunking

## Assistant

Recommended patterns for LLM agents over markdown graphs and YouTube transcripts both boil down to the same idea: **use structure and semantics as much as possible, and let embeddings be a safety net rather than the primary navigation method**. For markdown graphs, that means graph-aware agents over concept/entity files; for YouTube, that means semantic segmentation into “chapters” plus smart metadata, not naïve fixed-size chunks.[1][2][3][4][5]

***

## Agent patterns for markdown-based graphs

A markdown-based graph is just: directories of .md files, one concept per file where possible, linked with normal markdown links and enriched with frontmatter. OKF formalizes this into a portable bundle, but the patterns below apply equally to your own note graph.[6][7][1]

### Core agent loop

**FACT:** OKF and similar markdown-graph approaches assume an agent that can: read the index, select candidate nodes, follow links, and accumulate context before answering.[8][7][1]

A strong default loop for an “OKF-style” agent is:

1. **Entry-point selection**  
   - Start at an `index.md` or manifest file that lists themes, concepts, and entities.[7][1]
   - Use simple rules (tags, section names) to choose a small set of candidate concept/entity files before touching any embeddings.[5][1]

2. **Concept-first retrieval**  
   - For a conceptual query (“How does PIV loop work?”), read the concept file whose title or aliases best match the query, not raw notes.[6][5]
   - For task queries (“How do I configure X?”), load “skill files” or procedural docs first.[5]

3. **Graph traversal**  
   - Follow outgoing links to related concepts, entities, policies, or procedures, depth-limited (e.g., 1–2 hops).[1][7]
   - Use link text, headings, and local context to decide which edges are actually relevant.[8][1]

4. **Progressive injection**  
   - Inject only a small set of relevant files into the context window; if during reasoning the model realizes it needs more, let it call a tool to fetch another linked file.[8][5]
   - This matches the “progressive tool-based injection” pattern: rule-based selection → embedding-based fallbacks → on-demand file pulls.[5]

5. **Answer with citations**  
   - Include inline citations referencing specific markdown files and headings, since each file is a stable node in the graph.[1][6][5]

**CONSENSUS:** Markdown graphs work best when you enforce **one clear purpose per file** (concept, entity, skill/instruction, policy) and don’t treat large mixed-topic docs as single nodes. That keeps traversal and selection simple and makes causal reasoning across edges more reliable.[6][5]

### Common agent patterns

From OKF, markdown-graph writeups, and “markdown as a knowledge base for agents”, you get a few patterns that compose well:

- **Skill-file agents**  
  - Agent loads a task-specific `skill.md` (how to do X) before acting, then uses tools and context.[5]
  - Good for code-generation skills, deployment procedures, or “how to query this brain” docs.[5]

- **Entity-centric agents**  
  - Each entity (client, system, channel, service) has its own file.  
  - Agent first loads the relevant entity file based on the query, then optionally links to related policies or skills.[9][5]

- **Graph-walking research agents**  
  - Given a question, select a small set of starting nodes (via heuristics + embeddings) and then run a loop: read → expand via links → summarize partial findings → stop when confidence passes a threshold.[2][7]
  - Very effective for “explain how all of my notes about X fit together” style questions.

- **Security/visibility-aware traversal**  
  - In shared graphs, you restrict which nodes the agent can see or traverse based on security labels in frontmatter or directory path.[10][9]
  - The traversal logic enforces “only follow links to nodes you have clearance to see”.[10]

**SPECULATION (high confidence):** For your personal brain, the biggest win is rule-based routing to a small set of markdown files (skills, entities, core concepts) and then allowing graph traversal, with embedding retrieval as a fallback only when the graph does not have an obvious entry node.[2][7][5]

***

## Best practices for YouTube transcript ingestion

YouTube transcripts are noisy, long, and often multi-topic. Good ingestion makes later chunking and RAG far easier.[11][3][4]

### Ingestion pipeline

At a minimum:

1. **Collect metadata**  
   - Save video ID, title, channel, publish date, duration, description, playlist, and URL.[3]
   - Store this once in a machine-readable format (JSON, frontmatter).

2. **Get full transcripts with timestamps**  
   - Use caption API, transcript services, or tools like `yt-dlp` plus transcript extractors; preserve timestamps at sentence or phrase level.[11][3]
   - Keep language info and any “auto vs manual captions” quality signal if available.[3]

3. **Normalize into a structured representation**  
   - Convert into JSON like `[ { start, end, text, speaker? } ]` or markdown with `{ts:…}` markers (as in your attached transcript).[12][3]
   - Clean common artifacts (line breaks mid-sentence, repeated phrases, URL fragments, filler) but avoid “over-cleaning” that removes meaningful cues.[3]

4. **Align with chapter markers if present**  
   - Many videos have chapter timestamps; map transcript timestamps to those segments.[3]
   - Use chapters as initial semantic “super-chunks” for later finer splitting.

5. **Store raw and processed forms**  
   - Keep a “raw” transcript layer plus a “processed” layer (chapters, cleaned text) so you can debug and reprocess without re-downloading.[12][3]

**CONSENSUS:** Good ingestion preserves timestamps, metadata, and structural hints (chapters, sections), because those are extremely helpful later for building concept graphs, quoting, and linking back to precise moments.[11][3]

***

## Best practices for YouTube transcript chunking

For RAG and knowledge extraction, **semantic chunking** beats fixed windowing, especially for spoken content with topic shifts.[4][13][11][3]

### 1. Chunk at semantic boundaries, not fixed sizes

- Semantic chunking = break content where the topic or subtopic changes, often aligned to natural sections like “intro”, “setup”, “demo step 1”, “Q&A”.[11][3]
- Approaches:  
  - Use existing chapters as top-level boundaries and only split further when segments are too long.[3]
  - Use an LLM to tag each transcript line or short span with a topic label and split when the topic label changes or after a minimum length.[11][3]
  - For high scale, train a domain-specific “chaptering” or segmenter model as described in the video summarizer series (input: transcript; output: chapter boundaries).[11][3]

### 2. Choose chunk sizes based on use-case

From RAG chunking guides and semantic chunking best-practices:[13][4]

- For **fact lookup** (“what did they say about tool X?”):  
  - Prefer smaller chunks, often around 64–128 tokens, to get precise retrieval and less noise.[4][13]
- For **workflow or conceptual questions** (“what is their full PIV loop?”):  
  - Use larger semantic chunks, 512–1024 tokens, or full chapter-sized segments so the model sees a complete thought.[13][4]
- In both cases, use semantic boundaries first, then enforce min/max sizes (e.g., merge segments until ≥64 tokens; split long segments >1024 tokens, ideally at sentence boundaries).[4][13]

### 3. Add overlap carefully

- Use overlapping windows so information that straddles boundaries isn’t lost; 1–3 sentences of overlap is common for narrative content.[13][4]
- For spoken transcripts, overlaps around 10–20 seconds or 1–2 short paragraphs are usually enough; more overlap means more duplication in the index.[4]

### 4. Attach rich metadata to chunks

Every chunk should carry:

- Video ID, title, channel, publish date.[3]
- Absolute timestamps `[start, end]` and maybe original `{ts:}` markers for exact citation.[12][3]
- Chapter name / section if available.[3]
- High-level tags: topic, tools mentioned, series name, difficulty level, etc., if you can infer or compute them.[11][3]

This metadata enables:

- Filtering (e.g., “only from 2025+ videos”, “only from RAG series”).[3]
- Better ranking (boost chunks from highly relevant series or fresher content).[4]
- Deep linking to the exact video moment.[12][3]

### 5. Domain-appropriate embeddings and thresholds

Semantic chunking guidance emphasizes that good RAG depends on **domain-tuned embeddings** and thresholds:[13][4]

- Use general-purpose sentence embeddings for mixed technical + narrative content, but test with your corpus.[4]
- Tune similarity thresholds:  
  - Higher (0.7–0.8) for transcripts with frequent topic jumps to avoid pulling unrelated segments.[4]
  - Lower (0.5–0.6) for more narrative, slow-changing videos so you keep enough context.[4]
- Evaluate on real queries; adjust chunk sizes and thresholds based on retrieval precision and answer quality.[13][4]

***

## How these two topics fit together

A good personal system for YouTube + markdown graphs will typically:

- Ingest transcripts → semantic chunks with metadata (and keep full raw transcripts).[12][3][4]
- Build OKF-like **concept/entity files** that aggregate across videos (e.g., “PIV loop”, “OKF bundle design”), each linking back to source videos and timestamps.[1][6][12]
- Treat those concept/entity markdown files as the primary nodes in a knowledge graph, with the agent using **graph traversal** and skill-file patterns to answer most questions, and falling back to chunk-level RAG only when necessary.[7][2][5][4]

If you share a bit about how you’re currently storing transcripts (files in git, a DB, Obsidian vault, etc.), I can sketch a concrete agent architecture and data model tailored to your stack.
