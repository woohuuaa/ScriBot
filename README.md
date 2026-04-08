# ScriBot

> **RAG-Powered AI Assistant** for KDAI Documentation with chat, agent, and docs widget UI

## What is This?

ScriBot is a **documentation assistant** that uses:
- **RAG (Retrieval-Augmented Generation)** to search and cite 30+ technical documents
- **ReAct Agent Architecture** for multi-step reasoning
- **5 Modular Tools** for knowledge base management (search, list, info, create, delete)
- **Vector Embeddings** with environment-specific providers (Ollama locally, FastEmbed for hosted demos)
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
│  Floating ScriBot widget                                        │
│  - Chat mode (SSE streaming)                                    │
│  - Agent mode (default, with steps + sources)                   │
│  - Provider switcher (Ollama / Groq)                            │
└──────────────────────────────────┬──────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                         FastAPI Backend                         │
│                                                                 │
│  POST /api/chat        ← RAG-enhanced chat                      │
│  POST /api/agent/run   ← ReAct Agent with 5 tools               │
│  POST /api/admin/index-docs      ← Trigger hosted indexing      │
│  GET  /api/admin/index-docs/status ← Check indexing status      │
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

- **Qdrant** for self-hosted semantic search
- **ReAct agent** for transparent multi-step reasoning
- **Environment-specific embeddings**: Ollama locally, FastEmbed on Railway
- **Astro + Starlight widget** to keep the assistant inside the docs site

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
│   │   ├── embedder.py             # Embedding providers (Ollama / FastEmbed)
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
├── Dockerfile.railway              # Hosted backend image (backend + Docs)
├── railway.json                    # Railway deployment command/config
├── Docs/
│   ├── src/components/ScriBotWidget.tsx   # Floating chatbot widget
│   ├── src/lib/scribot.ts                 # Frontend API client
│   ├── src/styles/scribot.css             # Widget styling
│   └── src/content/docs/                  # KDAI documentation source
├── backend/.env.railway.example    # Railway backend env example
├── Docs/.env.railway.example       # Railway frontend env example
└── qdrant_storage/                 # Local Qdrant persistence
```

## RAG Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│ Step 1: Indexing (Offline)                                      │
│                                                                 │
│   MDX Files → Clean (remove frontmatter, imports, mermaid)      │
│            → Chunk (by ## headings)                             │
│            → Embed (Ollama locally / FastEmbed on Railway)      │
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

Local indexing uses `nomic-embed-text` through Ollama (768-dim vectors). Hosted demos on Railway use FastEmbed (`BAAI/bge-small-en-v1.5`, 384-dim vectors). If you change embedding provider or vector dimension, re-index the collection.

## ReAct Agent Architecture

The agent follows a `Thought → Action → Observation → Final Answer` loop, which makes tool use explicit and debuggable. It is used for multi-step questions, source-aware retrieval, and document-management tasks.

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

For Railway demos, deploy the backend with `Dockerfile.railway`, set the hosted environment variables, and trigger indexing via `POST /api/admin/index-docs`.

## Current Status

- Backend chat and agent endpoints are working
- Docs widget is mounted into the Astro + Starlight site
- Chat mode supports SSE streaming
- Agent mode is the default mode and shows steps and source links
- Provider labels expose active model names and availability via `/api/providers`
- The deployed frontend now prefers a usable provider from `/api/providers` instead of always sticking to the initial UI default
- Groq is labeled as `Recommended`, while remote Ollama is shown as `Local only` when unavailable
- Deployed frontend shows a clear Ollama deployment hint instead of a raw DNS error
- Source links stay in-page and preserve widget state via `sessionStorage`
- Ollama is mainly for local development, while Groq is recommended for faster demos
- Hosted indexing can be triggered remotely with `POST /api/admin/index-docs` and monitored via `GET /api/admin/index-docs/status`
- Railway demo deployment is working with `Groq + FastEmbed + Qdrant`

## Deployment Recommendation

### Local Development

- Use `docker compose up -d`
- Keep `EMBEDDING_PROVIDER=ollama`
- Keep `QDRANT_HOST=qdrant`
- Ollama is suitable for local development and fallback testing

### Hosted Demo (Railway)

- **Frontend:** deploy `Docs/` to Vercel
- **Backend provider:** prefer Groq for faster and more reliable live responses
- **Embedding provider:** use FastEmbed on Railway instead of Ollama
- **Backend image:** use `Dockerfile.railway` so both `backend/` and `Docs/` are available in the container
- Set `PUBLIC_SCRIBOT_API_BASE` in the Docs frontend to the deployed backend URL
- Trigger indexing remotely with `POST /api/admin/index-docs` and monitor it via `GET /api/admin/index-docs/status`
- Ollama should be treated as local-only unless you explicitly host a reachable Ollama server and set `OLLAMA_BASE_URL`

## Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Frontend** | Astro + Starlight + React | Documentation site and floating widget UI |
| **Backend** | FastAPI (Python) | Async API server |
| **Vector DB** | Qdrant | Semantic search with cosine similarity |
| **Embeddings** | Ollama / FastEmbed | Ollama for local development, FastEmbed for hosted demos |
| **LLM** | Groq / Ollama / OpenAI | Response generation |
| **Container** | Docker Compose | Multi-service orchestration |
| **Hosted Demo Deploy** | Railway | FastAPI + Qdrant demo deployment |

## Environment Profiles

### Local

```env
DEFAULT_PROVIDER=groq
EMBEDDING_PROVIDER=ollama
GROQ_API_KEY=<your-groq-api-key>
OLLAMA_MODEL=llama3.1:8b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
OLLAMA_KEEP_ALIVE=30m
OLLAMA_NUM_CTX=2048
OLLAMA_NUM_PREDICT=512
QDRANT_HOST=qdrant
QDRANT_PORT=6333
QDRANT_COLLECTION=kdai_docs
```

### Railway

```env
DEFAULT_PROVIDER=groq
EMBEDDING_PROVIDER=fastembed
GROQ_API_KEY=<your-groq-api-key>
FASTEMBED_MODEL=BAAI/bge-small-en-v1.5
FASTEMBED_BATCH_SIZE=4
FASTEMBED_THREADS=1
EMBEDDING_DIMENSION=384
QDRANT_URL=http://<your-qdrant-private-host>:6333
QDRANT_COLLECTION=kdai_docs
ADMIN_TOKEN=<your-admin-token>
```

`OLLAMA_BASE_URL` is optional on Railway and should only be set if you explicitly host a reachable Ollama server. Otherwise, treat Ollama as local-only. In deployed environments, the frontend uses `/api/providers` to surface provider availability and prefers a usable provider by default.

## Hosted Indexing

When running on Railway without shell access, use the admin indexing endpoints:

```bash
curl -X POST https://<your-backend>/api/admin/index-docs \
  -H "Content-Type: application/json" \
  -H "x-admin-token: <your-admin-token>" \
  -d '{"recreate": true}'

curl https://<your-backend>/api/admin/index-docs/status \
  -H "x-admin-token: <your-admin-token>"
```

## Demo Questions

### Chinese

1. `請用一段話介紹 KDAI 是什麼。`（Chat mode）
2. `請把 KDAI 架構分成 Backend、Frontend、Services、Infrastructure 四部分說明。`（Agent mode）
3. `請整理 KDAI quick-start 的最小操作步驟，限制 5 點內。`（Chat mode）
4. `什麼是 WebSocket broadcasting？請用 KDAI 的情境舉例。`（Agent mode）
5. `請先用中文回答 KDAI 是什麼，再切換成英文用一句話重述一次。`（Chat mode）

### English

1. `What is KDAI in one paragraph?`（Chat mode）
2. `Explain the KDAI architecture in four parts: Backend, Frontend, Services, and Infrastructure.`（Agent mode）
3. `Give me the minimum quick-start steps in at most 5 bullet points.`（Chat mode）
4. `What is WebSocket broadcasting, and how is it used in a KDAI scenario?`（Agent mode）
5. `First answer in English, then switch to Chinese and summarize KDAI in one sentence.`（Chat mode）

## Related: KDAI2 Project

This chatbot is built for [KDAI2](https://github.com/W-KDAI/kdai2) documentation. My contributions to KDAI2 include:

- **Built question extraction feature end-to-end** - Backend buffering system, LLM integration, Vue.js frontend
- **Developed context-aware UI** - Shows extracted questions with source transcript references and click-to-navigate
- **Engineered real-time buffering pipeline** - Aggregates streaming transcripts for accurate LLM processing
- **Optimized LLM prompts** - Improved question identification for Dutch parliamentary debates

## License

MIT
