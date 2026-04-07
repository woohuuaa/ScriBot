# ScriBot

> **RAG-Powered AI Assistant** for KDAI Documentation with chat, agent, and docs widget UI

## What is This?

ScriBot is a **documentation assistant** that uses:
- **RAG (Retrieval-Augmented Generation)** to search and cite 30+ technical documents
- **ReAct Agent Architecture** for multi-step reasoning
- **5 Modular Tools** for knowledge base management (search, list, info, create, delete)
- **Vector Embeddings** (Qdrant + nomic-embed-text) for semantic search
- **Multiple LLM Providers** (Ollama/Groq/OpenAI)
- **Astro + Starlight widget UI** with floating launcher, streaming chat, agent steps, and source links
- **Session-persistent widget state** so source navigation keeps the conversation open

```
User: "List all documents, then create a new guide about testing"

Agent:
┌────────────────────────────────────────────────────────────┐
│ Thought: User wants to see documents and create a new one. │
│          First, let me list all documents.                 │
│ Action: list_docs                                          │
│                                                            │
│ Observation: Found 33 documents: index.mdx, architecture...│
│                                                            │
│ Thought: Now I'll create the new testing guide.            │
│ Action: create_doc                                         │
│ Action Input: {"filename": "testing-guide.mdx", ...}       │
│                                                            │
│ Observation: Document created and indexed successfully!    │
│                                                            │
│ Thought: Tasks completed. I can provide a summary.         │
│ Final Answer: I found 33 documents and created a new       │
│               testing-guide.mdx with 5 chunks indexed.     │
│                                                            │
│ Sources: testing-guide.mdx                                 │
└────────────────────────────────────────────────────────────┘
```

## 5 Agent Tools

| Tool | Description | Use Case |
|------|-------------|----------|
| `search_docs` | Semantic search across all documents | "What is KDAI's architecture?" |
| `list_docs` | List all indexed documents | "What documents are available?" |
| `get_doc_info` | Get details about a specific document | "Tell me about architecture.mdx" |
| `create_doc` | Create new document + auto-index | "Create a guide about deployment" |
| `delete_doc` | Delete document + remove from index | "Remove the old-guide.mdx" |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  Astro + Starlight Docs Frontend                │
│                                                                 │
│  Floating ScriBot widget                                         │
│  - Chat mode (SSE streaming)                                     │
│  - Agent mode (default, with steps + sources)                    │
│  - Provider switcher (Ollama / Groq)                             │
└──────────────────────────────────┬──────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                         FastAPI Backend                         │
│                                                                 │
│  POST /api/chat        ← RAG-enhanced chat                      │
│  POST /api/agent/run   ← ReAct Agent with 5 tools               │
│  GET  /api/providers   ← Provider/model metadata                │
│  GET  /api/health      ← Health check                           │
└──────────────────────────────────┬──────────────────────────────┘
                                   │
        ┌──────────────────────────┼──────────────────────────────┐
        ▼                          ▼                              ▼
┌───────────────┐          ┌───────────────┐              ┌───────────────┐
│    Qdrant     │          │    Ollama     │              │  Groq/OpenAI  │
│  Vector DB    │          │  Local LLM    │              │  Cloud LLMs   │
│  + Search     │          │ + Embeddings  │              │               │
└───────────────┘          └───────────────┘              └───────────────┘
```

## Key Technical Decisions

| Decision | Why |
|----------|-----|
| **Qdrant** (not Pinecone/Chroma) | Open-source, self-hosted, production-ready REST API |
| **Cosine Similarity** (not Euclidean) | Compares semantic "direction" not magnitude - ideal for text embeddings |
| **ReAct Agent** (not simple RAG) | Multi-step reasoning, transparent thought process, extensible tool system |
| **5 Modular Tools** (not hardcoded) | Easy to extend - just add new Tool class |
| **Hand-written Pipeline** (not LangChain) | Full control, no abstraction overhead, interview-ready code |
| **Docs Widget in Starlight** | Keeps the assistant embedded inside the documentation site |

## Project Structure

```
ScriBot/
├── docker-compose.yml              # Ollama + Backend + Qdrant (local dev)
├── backend/
│   ├── main.py                     # FastAPI endpoints
│   ├── config.py                   # Settings (embedding dim, top-k, etc.)
│   ├── .env                        # Backend-specific local settings
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
│   │   │       ├── search_docs.py  # Semantic search tool
│   │   │       ├── list_docs.py    # List all documents
│   │   │       ├── get_doc_info.py # Get document details
│   │   │       ├── create_doc.py   # Create + auto-index document
│   │   │       └── delete_doc.py   # Delete + remove from index
│   │   │
│   │   └── llm_providers/          # LLM abstraction
│   │       ├── base.py             # Abstract base class
│   │       ├── ollama.py           # Local LLM
│   │       ├── groq.py             # Cloud LLM (free tier)
│   │       └── openai.py           # Cloud LLM (paid)
│   │
│   └── scripts/
│       └── index_docs.py           # Index docs into Qdrant
│
├── Docs/
│   ├── src/components/ScriBotWidget.tsx   # Floating chatbot widget
│   ├── src/lib/scribot.ts                 # Frontend API client
│   ├── src/styles/scribot.css             # Widget styling
│   └── src/content/docs/                  # KDAI documentation source
└── qdrant_storage/                 # Local Qdrant persistence
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
- Knowledge base management (create/delete documents dynamically)

## Quick Start

```bash
# 1. Start all services
docker compose up -d

# 2. Index documentation (first time only)
docker compose exec backend python scripts/index_docs.py

# 3. Test RAG chat
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What is KDAI?", "provider": "ollama"}'

# 4. Test Agent with search
curl -X POST http://localhost:8000/api/agent/run \
  -H "Content-Type: application/json" \
  -d '{"message": "Explain KDAI architecture and how to install it", "provider": "groq"}'

# 5. Test Agent with document management
curl -X POST http://localhost:8000/api/agent/run \
  -H "Content-Type: application/json" \
  -d '{"message": "List all documents, then create a new guide about testing"}'
```

## Current Status

- Backend chat and agent endpoints are working
- Docs widget is mounted into the Astro + Starlight site
- Chat mode supports SSE streaming
- Agent mode is the default mode and shows steps and source links
- Provider labels expose the active model name via `/api/providers`
- Source links stay in-page and preserve widget state via `sessionStorage`
- Ollama is mainly for local development, while Groq is recommended for faster demos

## Deployment Recommendation

- **Frontend:** deploy `Docs/` to Vercel
- **Backend provider for demos:** prefer Groq for faster and more reliable live responses
- **Backend hosting:** Railway is the fastest short-term demo path; EC2 is better for longer-lived infrastructure and full control
- **Ollama:** use mainly for local development, not public demos, unless you control the machine and accept slower first-token latency
- Set `PUBLIC_SCRIBOT_API_BASE` in the Docs frontend to point at the deployed backend URL
- Ensure `Docs/src/content/docs` is available to the backend before running `python scripts/index_docs.py`

## Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Frontend** | Astro + Starlight + React | Documentation site and floating widget UI |
| **Backend** | FastAPI (Python) | Async API server |
| **Vector DB** | Qdrant | Semantic search with cosine similarity |
| **Embeddings** | Ollama (nomic-embed-text) | 768-dim text embeddings |
| **LLM** | Groq / Ollama / OpenAI | Response generation |
| **Container** | Docker Compose | Multi-service orchestration |

## What I Learned

1. **RAG Pipeline Design** - Chunking strategy matters (by headings > fixed size)
2. **Vector Search** - Cosine similarity for semantic meaning, not just keywords
3. **Agent Architecture** - ReAct pattern for transparent multi-step reasoning
4. **Tool System Design** - Abstract base class + modular tools for extensibility
5. **Prompt Engineering** - Structured output format for reliable parsing
6. **Async Python** - httpx + asyncio for concurrent embedding requests

## Related: KDAI Project

This chatbot is built for [KDAI](https://github.com/example/kdai) documentation. My contributions to KDAI include:

- **Built question extraction feature end-to-end** - Backend buffering system, LLM integration, Vue.js frontend
- **Developed context-aware UI** - Shows extracted questions with source transcript references and click-to-navigate
- **Engineered real-time buffering pipeline** - Aggregates streaming transcripts for accurate LLM processing
- **Optimized LLM prompts** - Improved question identification for Dutch parliamentary debates

## License

MIT
