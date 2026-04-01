# ScriBot

> **RAG-Powered AI Agent** for KDAI Documentation with ReAct Architecture

## What is This?

ScriBot is a **documentation assistant** that uses:
- **RAG (Retrieval-Augmented Generation)** to search and cite 30+ technical documents
- **ReAct Agent Architecture** for multi-step reasoning
- **Vector Embeddings** (Qdrant + nomic-embed-text) for semantic search
- **Multiple LLM Providers** (Ollama/Groq/OpenAI) with automatic fallback

```
User: "How do I deploy KDAI with Docker?"

Agent:
┌────────────────────────────────────────────────────────────┐
│ Thought: User wants deployment instructions. Let me search │
│ Action: search_docs                                        │
│ Action Input: {"query": "KDAI Docker deployment setup"}    │
│                                                            │
│ Observation: Found relevant docs in install.mdx...         │
│                                                            │
│ Thought: I have enough information to answer.              │
│ Final Answer: To deploy KDAI with Docker:                  │
│   1. Clone the repository                                  │
│   2. Run `docker compose up -d`                            │
│   ...                                                      │
│                                                            │
│ Sources: install.mdx, docker-setup.mdx                     │
└────────────────────────────────────────────────────────────┘
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FastAPI Backend                         │
│                                                                 │
│  POST /api/chat        ← RAG-enhanced chat                      │
│  POST /api/agent/run   ← ReAct Agent with multi-step reasoning  │
│  GET  /api/health      ← Health check                           │
└──────────────────────────────┬──────────────────────────────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        ▼                      ▼                      ▼
┌───────────────┐      ┌───────────────┐      ┌───────────────┐
│    Qdrant     │      │    Ollama     │      │     Groq      │
│  Vector DB    │      │  Embeddings   │      │     LLM       │
│  (Semantic    │      │  + Local LLM  │      │  (Cloud LLM)  │
│   Search)     │      │               │      │               │
└───────────────┘      └───────────────┘      └───────────────┘
```

## Key Technical Decisions

| Decision | Why |
|----------|-----|
| **Qdrant** (not Pinecone/Chroma) | Open-source, self-hosted, production-ready REST API |
| **Cosine Similarity** (not Euclidean) | Compares semantic "direction" not magnitude - ideal for text embeddings |
| **ReAct Agent** (not simple RAG) | Multi-step reasoning, transparent thought process, extensible tool system |
| **Hand-written Pipeline** (not LangChain) | Full control, no abstraction overhead, interview-ready code |

## Project Structure

```
ScriBot/
├── docker-compose.yml              # Ollama + Backend + Qdrant
├── backend/
│   ├── main.py                     # FastAPI endpoints
│   ├── config.py                   # Settings (embedding dim, top-k, etc.)
│   │
│   ├── services/
│   │   ├── embedder.py             # Ollama embedding (nomic-embed-text)
│   │   ├── qdrant_client.py        # Vector DB operations
│   │   ├── chunker.py              # MDX parsing + text chunking
│   │   ├── rag.py                  # RAG pipeline (retrieve + context)
│   │   │
│   │   ├── agent/                  # ReAct Agent
│   │   │   ├── agent.py            # Agent loop (Thought → Action → Observation)
│   │   │   ├── prompts.py          # System prompts
│   │   │   └── tools/
│   │   │       ├── base.py         # Tool abstract base class
│   │   │       └── search_docs.py  # RAG as a tool
│   │   │
│   │   └── llm_providers/          # LLM abstraction
│   │       ├── base.py             # Abstract base class
│   │       ├── ollama.py           # Local LLM
│   │       ├── groq.py             # Cloud LLM (free tier)
│   │       └── openai.py           # Cloud LLM (paid)
│   │
│   └── scripts/
│       └── index_docs.py           # Index 30+ MDX files into Qdrant
│
└── Docs/src/content/docs/          # KDAI documentation (30+ MDX files)
```

## RAG Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│ Step 1: Indexing (Offline)                                      │
│                                                                 │
│   MDX Files → Clean (remove frontmatter, imports, mermaid)      │
│            → Chunk (by ## headings)                             │
│            → Embed (nomic-embed-text → 768-dim vectors)         │
│            → Store (Qdrant with payload: source, title, content)│
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ Step 2: Query (Online)                                          │
│                                                                 │
│   User Question → Embed → Cosine Search (top-3)                 │
│                → Build Context → LLM Prompt → Response          │
│                                                                 │
│   Returns: Answer + Source Citations                            │
└─────────────────────────────────────────────────────────────────┘
```

## ReAct Agent Architecture

The agent uses **Reasoning + Acting** pattern:

```python
# Simplified agent loop
while not done:
    # 1. LLM generates thought + action
    response = llm.generate(messages)
    
    # 2. Parse response
    thought, action, action_input = parse(response)
    
    # 3. Execute tool
    observation = tools[action].execute(**action_input)
    
    # 4. Add observation to context
    messages.append(f"Observation: {observation}")
    
    # 5. Check for final answer
    if "Final Answer" in response:
        return extract_final_answer(response)
```

**Why ReAct?**
- Transparent reasoning (can debug/explain each step)
- Modular tool system (easy to add new capabilities)
- Multi-step problem solving (not just single-shot Q&A)

## Quick Start

```bash
# 1. Start all services
docker compose up -d

# 2. Index documentation (first time only)
docker compose exec backend python -m scripts.index_docs

# 3. Test RAG chat
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is KDAI?"}'

# 4. Test Agent
curl -X POST http://localhost:8000/api/agent/run \
  -H "Content-Type: application/json" \
  -d '{"message": "Explain KDAI architecture and how to install it"}'
```

## Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Backend** | FastAPI (Python) | Async API server |
| **Vector DB** | Qdrant | Semantic search with cosine similarity |
| **Embeddings** | Ollama (nomic-embed-text) | 768-dim text embeddings |
| **LLM** | Groq / Ollama / OpenAI | Response generation |
| **Container** | Docker Compose | Multi-service orchestration |

## What I Learned

1. **RAG Pipeline Design** - Chunking strategy matters (by headings > fixed size)
2. **Vector Search** - Cosine similarity for semantic meaning, not just keywords
3. **Agent Architecture** - ReAct pattern for transparent multi-step reasoning
4. **Prompt Engineering** - Structured output format for reliable parsing
5. **Async Python** - httpx + asyncio for concurrent embedding requests

## Related: KDAI Project

This chatbot is built for [KDAI](https://github.com/example/kdai) documentation. My contributions to KDAI include:

- **Built question extraction feature end-to-end** - Backend buffering system, LLM integration, Vue.js frontend
- **Developed context-aware UI** - Shows extracted questions with source transcript references and click-to-navigate
- **Engineered real-time buffering pipeline** - Aggregates streaming transcripts for accurate LLM processing
- **Optimized LLM prompts** - Improved question identification for Dutch parliamentary debates

## License

MIT
