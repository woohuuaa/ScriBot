# KDAI Docs Chatbot - Side Project Plan

## Goal
Build a RAG chatbot for the KDAI docs website that can be embedded as a side project

## Timeline
**4 weeks**

---

## Tech Stack

| Component | Choice | Reason |
|-----------|--------|--------|
| Backend | FastAPI (Python) | Know Python, great AI ecosystem |
| Frontend | Vue.js widget | Consistent with KDAI |
| LLM | Ollama (llama3.2:3b / llama3.1:8b) | Consistent with KDAI, runs locally |
| Embedding | nomic-embed-text | Ollama recommended |
| Vector DB | Qdrant | Industry standard for AI |
| Search | RAG (hand-written) | Semantic search, industry standard |
| Streaming | SSE | ChatGPT-style streaming |
| Testing | pytest + Vitest | API + Component tests |
| CI/CD | GitHub Actions | Automation |
| Deployment | Docker Compose | Consistent with KDAI |

---

## Model Configuration

| Environment | Model | VRAM |
|-------------|-------|------|
| Laptop Dev | `llama3.2:3b` | ~2GB |
| Laptop Prod | `llama3.1:8b` | ~5GB |
| School GPU | `mistral-nemo:12b` | ~8GB |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 Vue.js Chat Widget (SSE)                    │
│                     (Embedded in Docs)                      │
└────────────────────────────┬────────────────────────────────┘
                             │ SSE Stream
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI RAG Service                      │
│                                                             │
│  POST /api/index      ← Index docs (33 MDX files)          │
│  POST /api/chat       ← SSE streaming response             │
│  GET  /api/health     ← Health check                       │
└─────────────────────────┬───────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
┌─────────────┐   ┌───────────────┐   ┌──────────────┐
│   Ollama    │   │    Qdrant    │   │  .mdx files  │
│ LLM + Emb  │   │  (Vector DB) │   │ (33 files)   │
└─────────────┘   └───────────────┘   └──────────────┘
```

---

## RAG Pipeline (Hand-written)

```
Step 1: Index
  33 MDX → Parse → Chunk (500 tokens) → nomic-embed-text → Store in Qdrant

Step 2: Search
  Question → Embed → Qdrant cosine similarity → Top-3 chunks

Step 3: Generate
  Question + chunks → Prompt → Ollama → SSE streaming response
```

---

## 4-Week Timeline

### Week 1: Environment Setup + RAG Pipeline

| Day | Task | Deliverable |
|-----|------|-------------|
| 1 | FastAPI scaffold, Docker Compose, Qdrant | Runnable project |
| 2 | Qdrant collection setup, client connection | Qdrant connected |
| 3 | MDX parser, chunking logic | Parser complete |
| 4-5 | Ollama embedding (nomic-embed-text) + store in Qdrant | Embedding pipeline |
| 6-7 | `/api/index` endpoint | CLI can index all docs |

**Deliverable**: `python scripts/index_docs.py`

---

### Week 2: RAG API + Semantic Search

| Day | Task | Deliverable |
|-----|------|-------------|
| 1-2 | Semantic search (cosine similarity, top-k) | Search working |
| 3-4 | `/api/chat` endpoint, prompt building, RAG integration | Basic RAG API |
| 5-6 | Error handling, retry, fallback | Robust API |
| 7 | Test RAG quality | Quality verified |

**Deliverable**: API can receive questions and return RAG answers

---

### Week 3: SSE Streaming + Vue.js Widget

| Day | Task | Deliverable |
|-----|------|-------------|
| 1-2 | FastAPI SSE streaming implementation | Streaming API |
| 3-4 | Vue.js widget init, basic UI | Chat box UI |
| 5-6 | SSE client connection, word-by-word display | Streaming UI |
| 7 | Loading, error UI, styling | Complete UI |

**Deliverable**: Embeddable chatbot widget

---

### Week 4: Testing + CI/CD + Documentation

| Day | Task | Deliverable |
|-----|------|-------------|
| 1-2 | pytest: API tests | Backend tests |
| 3 | Vitest: Widget tests | Frontend tests |
| 4 | GitHub Actions CI workflow | Auto testing |
| 5 | Docker Compose + CD pipeline | Auto deployment |
| 6-7 | README, architecture diagram, debug | Complete docs |

**Deliverable**: Production-ready, resume-worthy

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|------------|
| POST | `/api/index` | Index all .mdx files |
| POST | `/api/chat` | SSE streaming response |
| GET | `/api/health` | Health check |

---

## Project Structure

```
kadai-chatbot/
├── docker-compose.yml
├── Dockerfile
├── .github/
│   └── workflows/
│       └── ci.yml
├── rag_service/
│   ├── main.py
│   ├── routers/
│   │   └── chat.py
│   ├── services/
│   │   ├── embedder.py
│   │   ├── searcher.py
│   │   └── generator.py
│   ├── models/
│   │   └── schemas.py
│   └── scripts/
│       └── index_docs.py
├── chatbot_widget/
│   ├── src/
│   │   ├── ChatWidget.vue
│   │   └── ...
│   └── tests/
│       └── ChatWidget.test.ts
├── tests/
│   └── test_api.py
├── docs/
│   └── ARCHITECTURE.md
└── README.md
```

---

## Resume Description

```
KDAI Docs Chatbot (Side Project)
- RAG-based Q&A chatbot for internal documentation with SSE streaming
- FastAPI REST API + Vue.js embedded widget
- Ollama local LLM (llama3.1/llama3.2) + Qdrant vector database
- Semantic search using cosine similarity (nomic-embed-text)
- GitHub Actions CI/CD pipeline with Docker Compose deployment
```

---

## Interview Talking Points (Connecting to KDAI)

1. Referenced KDAI's Docker Compose microservices architecture
2. Ollama local LLM consistent with KDAI's implementation
3. Addresses KDAI's missing semantic search functionality
4. Uses same Python microservices pattern as KDAI ATTS services
